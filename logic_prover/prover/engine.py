"""Resolution theorem prover engine implementing given-clause resolution and superposition loops."""

from __future__ import annotations
import heapq
import time
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, DefaultDict
from collections import defaultdict

from logic_prover.core.ast import Formula, Variable, Term, Not, Equality, Forall, free_variables, formula_size
from logic_prover.core.sorts import Ind
from logic_prover.core.substitutions import unify_formulas, UnificationError
from logic_prover.config import SolverConfig
from logic_prover.core.exceptions import ProofTimeoutError, ProofSearchExhaustedError, SolverError
from logic_prover.prover.clausifier import Clause, Literal, to_cnf, negate_and_clausify, PredicateApp
from logic_prover.prover.rules import resolve_clauses, factor_clause, paramodulate
from logic_prover.prover.proof import ProofDAG, ProofStep
from logic_prover.prover.reconstruction import reconstruct_proof


@dataclass(frozen=True)
class ResolutionStep:
    """Represents a single step in a resolution proof search trace."""
    id: str
    rule_name: str  # "axiom", "negated_goal", "resolution", "factoring", "paramodulation"
    premise_ids: List[str]
    clause: Clause
    substitution: Dict[Variable, Term] = field(default_factory=dict)
    parent_literals: Optional[Tuple[Literal, Literal]] = None
    original_formula: Optional[Formula] = None


def _clause_predicate_key(clause: Clause) -> frozenset:
    """Extracts a predicate signature key for indexing (set of (pred_name, positive) pairs)."""
    key_parts: Set[Tuple] = set()
    for lit in clause.literals:
        if isinstance(lit.atom, PredicateApp):
            pred_id = lit.atom.pred if isinstance(lit.atom.pred, str) else str(lit.atom.pred)
            key_parts.add((pred_id, lit.positive))
        elif isinstance(lit.atom, Equality):
            key_parts.add(("=", lit.positive))
    return frozenset(key_parts)


def _clause_structural_weight(c: Clause) -> int:
    """Computes clause priority weight using AST size (no string formatting)."""
    weight = len(c.literals) * 10
    for lit in c.literals:
        weight += formula_size(lit.atom)
    if c.is_unit:
        weight -= 5
    return weight


class TheoremProver:
    """Automated resolution theorem prover for First-Order Logic formulas."""

    signature: Signature
    config: SolverConfig

    def __init__(
        self,
        signature: Signature,
        config: Optional[SolverConfig] = None
    ) -> None:
        """Initializes TheoremProver with signature and configuration.

        Args:
            signature: The logical signature context for symbol resolution.
            config: Optional SolverConfig overriding prover limits (defaults to SolverConfig()).
        """
        self.signature = signature
        self.config = config or SolverConfig()

    def prove(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
        max_steps: Optional[int] = None,
        timeout_sec: Optional[float] = None
    ) -> ProofDAG:
        """
        Attempts to prove target from premises using resolution refutation search.
        1. Clausifies premises and negated target into CNF.
        2. Executes Otter given-clause loop with forward subsumption.
        3. On empty clause derivation, extracts resolution trace.
        4. Reconstructs natural deduction ProofDAG.

        Args:
            target: The Formula to prove.
            premises: Optional list of premise Formulas to use.
            max_steps: Optional cap on the number of given-clause loop iterations.
            timeout_sec: Optional wall-clock timeout in seconds.

        Returns:
            A ProofDAG object reconstructing the proof of target from premises.

        Raises:
            ProofTimeoutError: If the search exceeds the time limit.
            ProofSearchExhaustedError: If the search space is exhausted without a contradiction.
        """
        max_steps = max_steps if max_steps is not None else self.config.prover_max_steps
        timeout_sec = timeout_sec if timeout_sec is not None else self.config.prover_timeout_sec

        start_time = time.monotonic()
        premises = premises or []

        step_counter = 0
        trace_records: Dict[str, ResolutionStep] = {}
        clause_to_step_id: Dict[Clause, str] = {}

        # Heap-based priority queue: (weight, insertion_order, clause)
        passive_heap: List[Tuple[int, int, Clause]] = []
        insert_counter = 0

        active_clauses: List[Clause] = []
        active_clause_set: Set[Clause] = set()
        # Predicate signature index for faster subsumption candidate lookup
        active_index: DefaultDict[frozenset, List[Clause]] = defaultdict(list)

        def add_initial_step(clause: Clause, rule_name: str, orig_fmt: Optional[Formula]) -> None:
            """Registers an initial (axiom or negated goal) clause as a trace step.

            Args:
                clause: The clause to register.
                rule_name: Rule label for the step (e.g. 'axiom', 'negated_goal').
                orig_fmt: Original formula associated with the step, if any.
            """
            nonlocal step_counter, insert_counter
            step_id = f"res_{step_counter}"
            step_counter += 1
            step = ResolutionStep(
                id=step_id,
                rule_name=rule_name,
                premise_ids=[],
                clause=clause,
                original_formula=orig_fmt
            )
            trace_records[step_id] = step
            clause_to_step_id[clause] = step_id
            weight = _clause_structural_weight(clause)
            heapq.heappush(passive_heap, (weight, insert_counter, clause))
            insert_counter += 1

        def add_derived_step(clause: Clause, rule_name: str, premise_ids: List[str],
                             subst: Dict[Variable, Term] = None,
                             parent_lits: Optional[Tuple[Literal, Literal]] = None) -> Optional[str]:
            """Add a derived clause step.

            Args:
                clause: The derived clause to register.
                rule_name: Inference rule used ('resolution', 'factoring', 'paramodulation').
                premise_ids: List of step ids that served as premises.
                subst: Substitution used by the inference.
                parent_lits: Pair of literals resolved/paramodulated upon, if any.

            Returns:
                step_id if added, None if the clause is a duplicate or tautology.
            """
            nonlocal step_counter, insert_counter
            if clause in clause_to_step_id or clause.is_tautology:
                return None
            step_id = f"res_{step_counter}"
            step_counter += 1
            res_step = ResolutionStep(
                id=step_id,
                rule_name=rule_name,
                premise_ids=premise_ids,
                clause=clause,
                substitution=subst or {},
                parent_literals=parent_lits
            )
            trace_records[step_id] = res_step
            clause_to_step_id[clause] = step_id
            weight = _clause_structural_weight(clause)
            heapq.heappush(passive_heap, (weight, insert_counter, clause))
            insert_counter += 1
            return step_id

        # Always include reflexivity of equality as an initial axiom step
        v_refl = Variable(999, sort=Ind)
        refl_clause = Clause(frozenset([Literal(atom=Equality(left=v_refl, right=v_refl), positive=True)]))
        add_initial_step(refl_clause, "axiom", Forall(variable=v_refl, body=Equality(left=v_refl, right=v_refl)))

        # Clausify Premises
        from logic_prover.sol.ast_ext import ForallPred, ExistsPred, ForallFunc, ExistsFunc
        from logic_prover.sol.kb_ext import get_sol_axioms
        from logic_prover.prover.rules import SOLInstantiateRule

        sol_rule = SOLInstantiateRule()
        all_sol_candidates = list(premises) + [fmt for _, fmt in get_sol_axioms()]
        for sol_f in all_sol_candidates:
            if type(sol_f).__name__ in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
                inst_clauses = sol_rule.match_and_instantiate(sol_f, target, signature=self.signature)
                for c in inst_clauses:
                    if not c.is_tautology and c not in clause_to_step_id:
                        add_initial_step(c, "axiom", None)

        for prem in premises:
            if type(prem).__name__ not in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
                cnf_clauses = to_cnf(prem, signature=self.signature)
                for c in cnf_clauses:
                    if not c.is_tautology and c not in clause_to_step_id:
                        add_initial_step(c, "axiom", prem)

        # Clausify Negated Target
        target_clauses = negate_and_clausify(target, signature=self.signature)
        for c in target_clauses:
            if not c.is_tautology and c not in clause_to_step_id:
                add_initial_step(c, "negated_goal", target)

        empty_clause_step_id: Optional[str] = None

        # Check if an initial clause is already empty
        for _, _, c in passive_heap:
            if c.is_empty:
                empty_clause_step_id = clause_to_step_id[c]
                break

        step_count = 0
        while passive_heap and not empty_clause_step_id:
            if time.monotonic() - start_time > timeout_sec:
                raise ProofTimeoutError(
                    f"Theorem prover timed out after {timeout_sec:.4f}s ({step_count} steps)."
                )

            if step_count >= max_steps:
                raise ProofSearchExhaustedError(
                    f"Theorem prover search exhausted after max_steps={max_steps} steps."
                )

            step_count += 1

            _, _, given_clause = heapq.heappop(passive_heap)

            if given_clause.is_empty:
                empty_clause_step_id = clause_to_step_id[given_clause]
                break

            if self._is_subsumed(given_clause, active_clauses, active_index):
                continue

            active_clauses.append(given_clause)
            active_clause_set.add(given_clause)
            pred_key = _clause_predicate_key(given_clause)
            active_index[pred_key].append(given_clause)
            given_step_id = clause_to_step_id[given_clause]

            # Generate Factoring Inferences
            for factored_c, subst in factor_clause(given_clause):
                if time.monotonic() - start_time > timeout_sec:
                    raise ProofTimeoutError(f"Theorem prover timed out after {timeout_sec:.4f}s.")
                sid = add_derived_step(factored_c, "factoring", [given_step_id], subst)
                if sid and factored_c.is_empty:
                    empty_clause_step_id = sid
                    break

            if empty_clause_step_id:
                break

            # Generate Resolution & Paramodulation Inferences with Active Clauses
            for active_c in active_clauses:
                if time.monotonic() - start_time > timeout_sec:
                    raise ProofTimeoutError(f"Theorem prover timed out after {timeout_sec:.4f}s.")

                active_step_id = clause_to_step_id[active_c]

                # Binary Resolution
                for resolvent_c, subst, (l1, l2) in resolve_clauses(given_clause, active_c):
                    sid = add_derived_step(resolvent_c, "resolution",
                                           [given_step_id, active_step_id], subst, (l1, l2))
                    if sid and resolvent_c.is_empty:
                        empty_clause_step_id = sid
                        break
                if empty_clause_step_id:
                    break

                # Paramodulation
                for param_c, subst in paramodulate(given_clause, active_c):
                    sid = add_derived_step(param_c, "paramodulation",
                                           [given_step_id, active_step_id], subst)
                    if sid and param_c.is_empty:
                        empty_clause_step_id = sid
                        break
                if empty_clause_step_id:
                    break

        if not empty_clause_step_id:
            raise ProofSearchExhaustedError(
                f"Prover search space exhausted without deriving contradiction ({step_count} steps)."
            )

        needed_ids: Set[str] = set()

        def collect_trace(sid: str) -> None:
            """Recursively marks all steps reachable from a given step as needed.

            Args:
                sid: The step id to start collecting from.
            """
            if sid in needed_ids:
                return
            needed_ids.add(sid)
            for pid in trace_records[sid].premise_ids:
                if pid in trace_records:
                    collect_trace(pid)

        collect_trace(empty_clause_step_id)
        resolution_trace = [trace_records[sid] for sid in sorted(needed_ids, key=lambda x: int(x.split("_")[1]))]

        return reconstruct_proof(resolution_trace, original_target=target, premises=premises)

    def _is_subsumed(self, c: Clause, active_clauses: List[Clause],
                     active_index: DefaultDict[frozenset, List[Clause]]) -> bool:
        """True if c is subsumed by an existing active clause."""
        for active_c in active_clauses:
            if len(active_c.literals) > len(c.literals):
                continue
            if self._clause_subsumes(active_c, c):
                return True
        return False

    def _clause_subsumes(self, c1: Clause, c2: Clause) -> bool:
        if c1.is_empty:
            return True
        if not c1.literals:
            return True
        lits1 = list(c1.literals)
        lits2 = list(c2.literals)

        def match_literals(idx: int, current_subst: Dict[Variable, Term]) -> bool:
            """Backtracking search matching each literal of c1 to a literal of c2.

            Args:
                idx: Current index into the c1 literal list.
                current_subst: Accumulated substitution from matched literals.

            Returns:
                True if all literals of c1 can be matched to literals of c2.
            """
            if idx == len(lits1):
                return True
            lit1 = lits1[idx]
            for lit2 in lits2:
                if lit1.positive == lit2.positive:
                    try:
                        new_subst = unify_formulas(lit1.atom, lit2.atom)
                        lit2_vars = lit2.free_variables()
                        if any(v in lit2_vars for v in new_subst.keys()):
                            continue
                        combined = dict(current_subst)
                        combined.update(new_subst)
                        if match_literals(idx + 1, combined):
                            return True
                    except UnificationError:
                        continue
            return False

        return match_literals(0, {})
