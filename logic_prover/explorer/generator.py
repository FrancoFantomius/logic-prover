"""Formula generator engine implementing diverse candidate exploration strategies."""

from __future__ import annotations
import random
from typing import List, Dict, Set, Optional, Tuple, Any
from logic_prover.config import SolverConfig
from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists,
    free_variables, bound_variables, canonicalize_bound_variables, formula_depth
)
from logic_prover.core.sorts import Sort, Ind
from logic_prover.core.signature import Signature
from logic_prover.core.validator import is_well_formed, validate_formula
from logic_prover.core.substitutions import substitute_formula, substitute_term
from logic_prover.core.database import KnowledgeDatabase, _dict_to_formula
from logic_prover.core.rewriter import RewriteRule, rewrite_all
from logic_prover.prover.engine import TheoremProver
from logic_prover.prover.proof import ProofDAG, ProofStep
from logic_prover.prover.clausifier import to_cnf, Clause, Literal
from logic_prover.prover.rules import get_resolution_rules, resolve_clauses, paramodulate, factor_clause
from logic_prover.explorer.heuristics import (
    calculate_diversity_scores, composite_interestingness, is_redundant_structure, DiversityMetrics
)
from logic_prover.explorer.filter import FormulaFilter


# --- First-Order Anti-Unification Helper Functions ---

def anti_unify_terms(
    t1: Term,
    t2: Term,
    bindings: Dict[Tuple[Term, Term], Variable],
    var_counter: List[int]
) -> Term:
    """
    Computes Most Specific Generalization (MSG) of two terms t1 and t2:
    - If t1 == t2: returns t1
    - If t1 = f(s1...sk) and t2 = f(u1...uk) with same func symbol: returns f(anti_unify(s1, u1)...)
    - Otherwise: assigns or reuses fresh Variable for pair (t1, t2)
    """
    if t1 == t2:
        return t1

    if (
        isinstance(t1, FunctionApp) and isinstance(t2, FunctionApp)
        and t1.func == t2.func and t1.arity == t2.arity
    ):
        new_args = tuple(
            anti_unify_terms(a1, a2, bindings, var_counter)
            for a1, a2 in zip(t1.args, t2.args)
        )
        return FunctionApp(func=t1.func, arity=t1.arity, args=new_args, return_sort=t1.return_sort)

    pair = (t1, t2)
    if pair not in bindings:
        v_id = var_counter[0]
        var_counter[0] += 1
        sort = getattr(t1, 'sort', Ind)
        bindings[pair] = Variable(id=v_id, sort=sort)

    return bindings[pair]


def anti_unify_formulas(
    f1: Formula,
    f2: Formula,
    bindings: Optional[Dict[Tuple[Term, Term], Variable]] = None,
    var_counter: Optional[List[int]] = None
) -> Optional[Formula]:
    """
    Computes Most Specific Generalization (MSG) of two formulas f1 and f2:
    - If structural connectives/predicates match: anti-unifies recursively.
    - Universally quantifies all fresh generalization variables introduced.
    Returns generalized closed formula, or None if structural mismatch is irreconcilable.
    """
    if bindings is None:
        bindings = {}
    if var_counter is None:
        all_vars = free_variables(f1) | bound_variables(f1) | free_variables(f2) | bound_variables(f2)
        max_id = max((v.id for v in all_vars), default=-1)
        var_counter = [max_id + 1]

    def recurse(g1: Formula, g2: Formula) -> Optional[Formula]:
        if isinstance(g1, PredicateApp) and isinstance(g2, PredicateApp):
            if g1.pred == g2.pred and g1.arity == g2.arity:
                gen_args = tuple(
                    anti_unify_terms(a1, a2, bindings, var_counter)
                    for a1, a2 in zip(g1.args, g2.args)
                )
                return PredicateApp(pred=g1.pred, arity=g1.arity, args=gen_args)
            return None

        if isinstance(g1, Equality) and isinstance(g2, Equality):
            gen_left = anti_unify_terms(g1.left, g2.left, bindings, var_counter)
            gen_right = anti_unify_terms(g1.right, g2.right, bindings, var_counter)
            return Equality(left=gen_left, right=gen_right)

        if isinstance(g1, Not) and isinstance(g2, Not):
            inner = recurse(g1.operand, g2.operand)
            return Not(inner) if inner else None

        if isinstance(g1, And) and isinstance(g2, And):
            l = recurse(g1.left, g2.left)
            r = recurse(g1.right, g2.right)
            return And(l, r) if (l and r) else None

        if isinstance(g1, Or) and isinstance(g2, Or):
            l = recurse(g1.left, g2.left)
            r = recurse(g1.right, g2.right)
            return Or(l, r) if (l and r) else None

        if isinstance(g1, Implies) and isinstance(g2, Implies):
            l = recurse(g1.left, g2.left)
            r = recurse(g1.right, g2.right)
            return Implies(l, r) if (l and r) else None

        if isinstance(g1, Iff) and isinstance(g2, Iff):
            l = recurse(g1.left, g2.left)
            r = recurse(g1.right, g2.right)
            return Iff(l, r) if (l and r) else None

        if isinstance(g1, Forall) and isinstance(g2, Forall):
            var_pair = (g1.variable, g2.variable)
            if g1.variable == g2.variable:
                bound_v = g1.variable
            else:
                if var_pair not in bindings:
                    v_id = var_counter[0]
                    var_counter[0] += 1
                    bindings[var_pair] = Variable(id=v_id, sort=g1.variable.sort)
                bound_v = bindings[var_pair]
            inner = recurse(g1.body, g2.body)
            return Forall(variable=bound_v, body=inner) if inner else None

        if isinstance(g1, Exists) and isinstance(g2, Exists):
            var_pair = (g1.variable, g2.variable)
            if g1.variable == g2.variable:
                bound_v = g1.variable
            else:
                if var_pair not in bindings:
                    v_id = var_counter[0]
                    var_counter[0] += 1
                    bindings[var_pair] = Variable(id=v_id, sort=g1.variable.sort)
                bound_v = bindings[var_pair]
            inner = recurse(g1.body, g2.body)
            return Exists(variable=bound_v, body=inner) if inner else None

        return None

    raw_gen = recurse(f1, f2)
    if not raw_gen:
        return None

    # Universally quantify newly introduced generalization variables that are free
    gen_vars = set(bindings.values()) & free_variables(raw_gen)
    result = raw_gen
    for gv in sorted(gen_vars, key=lambda v: v.id, reverse=True):
        result = Forall(variable=gv, body=result)

    return result


class FormulaExplorer:
    """
    Semantically-guided Formula Explorer engine.
    Generates, evaluates, ranks, and filters candidate conjectures.
    """

    def __init__(
        self,
        db: KnowledgeDatabase,
        signature: Signature,
        config: SolverConfig,
        prover: Optional[TheoremProver] = None,
        filter_path: Optional[str] = None
    ) -> None:
        """Initializes the candidate formula explorer with database, signature, config, and prover components."""
        self.db = db
        self.signature = signature
        self.config = config
        self.prover = prover or TheoremProver(signature=signature, config=config)
        self.filter = FormulaFilter(storage_path=filter_path or config.db_path + ".filter.json")
        self.rewrite_rules: List[RewriteRule] = []

    def generate_candidates(
        self,
        strategy: str = "mixed",
        max_depth: Optional[int] = None,
        count: Optional[int] = None
    ) -> List[Formula]:
        """
        Generates candidate formulas using specified semantic strategy:
        - 'axiom_rewrite': Rewriting & instantiating known axioms.
        - 'proof_frontier': Extracting & generalizing intermediate proof steps.
        - 'anti_unification': Computing MSG generalization of theorem pairs.
        - 'saturation': Bounded resolution/paramodulation inference on seed axioms.
        - 'lemma_combination': Linking lemmas via implication, conjunction, quantifiers.
        - 'mixed': Proportionally mixes all strategies.
        """
        depth_limit = max_depth or self.config.explorer_max_depth
        target_count = count or self.config.explorer_batch_size

        candidates: List[Formula] = []

        if strategy == "axiom_rewrite":
            candidates = self._generate_axiom_rewrite(depth_limit, target_count)
        elif strategy == "proof_frontier":
            candidates = self._generate_proof_frontier(depth_limit, target_count)
        elif strategy == "anti_unification":
            candidates = self._generate_anti_unification(depth_limit, target_count)
        elif strategy == "saturation":
            candidates = self._generate_saturation(depth_limit, target_count)
        elif strategy == "lemma_combination":
            candidates = self._generate_lemma_combination(depth_limit, target_count)
        elif strategy == "mixed":
            per_strategy = max(1, target_count // 5)
            candidates.extend(self._generate_axiom_rewrite(depth_limit, per_strategy))
            candidates.extend(self._generate_proof_frontier(depth_limit, per_strategy))
            candidates.extend(self._generate_anti_unification(depth_limit, per_strategy))
            candidates.extend(self._generate_saturation(depth_limit, per_strategy))
            candidates.extend(self._generate_lemma_combination(depth_limit, per_strategy))
        else:
            raise ValueError(f"Unknown generation strategy: '{strategy}'")

        # Filter out ill-formed, oversized, or redundant formulas
        valid_candidates: List[Formula] = []
        for f in candidates:
            if formula_depth(f) > depth_limit:
                continue
            if not is_well_formed(f, self.signature):
                continue
            if is_redundant_structure(f):
                continue
            valid_candidates.append(canonicalize_bound_variables(f))

        return valid_candidates

    def rank_and_select(
        self,
        candidates: List[Formula],
        top_k: Optional[int] = None
    ) -> List[Formula]:
        """
        Ranks candidate formulas by multi-metric diversity scores and composite
        interestingness, filtering out previously seen formulas from FormulaFilter.
        Adds selected top candidates to the filter state.
        """
        k = top_k or self.config.explorer_top_k
        unseen_candidates: List[Formula] = []

        for f in candidates:
            if not self.filter.is_seen(f):
                unseen_candidates.append(f)

        scored_candidates: List[Tuple[float, Formula]] = []
        for f in unseen_candidates:
            metrics = calculate_diversity_scores(f)
            score = composite_interestingness(metrics)
            scored_candidates.append((score, f))

        scored_candidates.sort(key=lambda item: item[0], reverse=True)

        selected = [f for score, f in scored_candidates[:k]]
        for f in selected:
            self.filter.add(f)

        return selected

    # --- Strategy Implementations ---

    def _generate_axiom_rewrite(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 1: Rewrite and instantiate existing KB axioms."""
        axioms = [form for name, form in self.db.get_axioms()]
        if not axioms:
            return []

        results: List[Formula] = []
        attempts = 0
        max_attempts = count * 5

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            ax = random.choice(axioms)
            norm = rewrite_all(ax, self.rewrite_rules) if self.rewrite_rules else ax
            
            # Unwrap outer quantifiers to access body variables
            body = norm
            while isinstance(body, (Forall, Exists)):
                body = body.body

            free_vars = list(free_variables(body))
            if free_vars:
                subst: Dict[Variable, Term] = {}
                for v in free_vars:
                    matching_consts = [
                        Constant(c, sort=s) for c, s in self.signature.constants.items()
                        if s == v.sort
                    ]
                    if matching_consts:
                        subst[v] = random.choice(matching_consts)
                if subst:
                    instantiated = substitute_formula(body, subst)
                    rem_free = free_variables(instantiated)
                    for v in sorted(rem_free, key=lambda x: x.id, reverse=True):
                        instantiated = Forall(variable=v, body=instantiated)
                    results.append(instantiated)
                else:
                    results.append(norm)
            else:
                results.append(norm)

        return results

    def _generate_proof_frontier(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 2: Extract and generalize intermediate lemmas from proof DAGs."""
        theorems = self.db.get_theorems()
        results: List[Formula] = []

        for name, thm_formula in theorems:
            if len(results) >= count:
                break
            proof_dag = self.db.get_proof(name)
            if not proof_dag:
                continue

            if isinstance(proof_dag, ProofDAG):
                steps = list(proof_dag.steps.values())
            elif isinstance(proof_dag, dict) and "steps" in proof_dag:
                steps = list(proof_dag["steps"].values())
            else:
                steps = []

            for step in steps:
                if len(results) >= count:
                    break
                if isinstance(step, ProofStep):
                    rule = step.rule
                    conc = step.conclusion
                elif isinstance(step, dict):
                    rule = step.get("rule", "")
                    conc_dict = step.get("conclusion")
                    conc = _dict_to_formula(conc_dict) if conc_dict else None
                else:
                    continue

                if rule and conc and rule not in ("Axiom", "Hypothesis", "NegatedGoal", "DoubleNegationElimination"):
                    if not is_redundant_structure(conc):
                        results.append(conc)

        return results

    def _generate_anti_unification(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 3: Compute Most Specific Generalization of theorem/axiom pairs."""
        formulas = [f for n, f in self.db.get_axioms()] + [f for n, f in self.db.get_theorems()]
        if len(formulas) < 2:
            return []

        results: List[Formula] = []
        for i in range(len(formulas)):
            for j in range(i + 1, len(formulas)):
                if len(results) >= count:
                    break
                gen = anti_unify_formulas(formulas[i], formulas[j])
                if gen and not is_redundant_structure(gen):
                    results.append(gen)

        return results

    def _generate_saturation(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 4: Exhaustive inference on small seed axiom sets via resolution/paramodulation."""
        axioms = [f for n, f in self.db.get_axioms()]
        if not axioms:
            return []

        seeds = axioms[:min(3, len(axioms))]
        clauses: List[Clause] = []
        for s in seeds:
            clauses.extend(to_cnf(s, signature=self.signature))

        derived_clauses: List[Clause] = list(clauses)
        for i in range(len(clauses)):
            for j in range(i + 1, len(clauses)):
                if len(derived_clauses) >= count + len(clauses):
                    break
                res_out = resolve_clauses(clauses[i], clauses[j])
                for r_clause, subst, lits in res_out:
                    if not r_clause.is_empty and not r_clause.is_tautology:
                        derived_clauses.append(r_clause)

        # Also paramodulate if needed
        if len(derived_clauses) < count + len(clauses):
            for i in range(len(clauses)):
                for j in range(len(clauses)):
                    if len(derived_clauses) >= count + len(clauses):
                        break
                    p_out = paramodulate(clauses[i], clauses[j])
                    for p_clause, subst in p_out:
                        if not p_clause.is_empty and not p_clause.is_tautology:
                            derived_clauses.append(p_clause)

        results: List[Formula] = []
        for c in derived_clauses[len(clauses):]:
            if c.is_empty:
                continue
            if c.is_unit:
                lit = list(c.literals)[0]
                f = lit.atom if lit.positive else Not(lit.atom)
            else:
                lits = list(c.literals)
                f = lits[0].atom if lits[0].positive else Not(lits[0].atom)
                for l in lits[1:]:
                    atom_f = l.atom if l.positive else Not(l.atom)
                    f = Or(f, atom_f)

            # Close free variables with Forall
            for v in sorted(free_variables(f), key=lambda x: x.id, reverse=True):
                f = Forall(variable=v, body=f)

            results.append(f)

        return results

    def _generate_lemma_combination(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 5: Combine existing lemmas via implications, conjunctions, quantifiers."""
        formulas = [f for n, f in self.db.get_axioms()] + [f for n, f in self.db.get_theorems()]
        if not formulas:
            return []

        results: List[Formula] = []
        for i in range(len(formulas)):
            for j in range(len(formulas)):
                if i == j or len(results) >= count:
                    continue
                f1, f2 = formulas[i], formulas[j]

                # Combination 1: Implication f1 => f2
                results.append(Implies(left=f1, right=f2))
                if len(results) >= count:
                    break

                # Combination 2: Conjunction f1 ∧ f2
                results.append(And(left=f1, right=f2))
                if len(results) >= count:
                    break

                # Combination 3: Equivalence f1 <=> f2
                results.append(Iff(left=f1, right=f2))
                if len(results) >= count:
                    break

        return results
