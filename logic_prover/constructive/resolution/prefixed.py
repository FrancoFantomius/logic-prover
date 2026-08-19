"""Prefixed resolution prover and clausal inference rules over Kripke T-strings for Intuitionistic Logic."""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Sequence

from logic_prover.core.ast import (
    Formula,
    Term,
    Variable,
    Equality,
)
from logic_prover.core.exceptions import UnificationError
from logic_prover.core.substitutions import unify_formulas, unify_terms
from logic_prover.core.equality import equality_substitution
from logic_prover.constructive.common import (
    _is_falsum,
    kbo_compare,
    normalize_formula,
)
from logic_prover.constructive.prefix import (
    PrefixSubstitution,
    unify_prefixes,
    is_admissible,
)
from logic_prover.constructive.matrix import (
    FormulaTree,
)
from logic_prover.constructive.resolution.clauses import (
    PrefixedLiteral,
    PrefixedClause,
    PrefixedResolutionStep,
    PrefixedResolutionProofResult,
    clausify_prefixed,
)


def _try_unify_formulas(f1: Formula, f2: Formula) -> Optional[Dict[Variable, Term]]:
    """Attempts to unify two atomic formulas, returning the MGU or None if ununifiable.

    Supports symmetric equality unification for Equality formulas.

    Args:
        f1 (Formula): First atomic formula.
        f2 (Formula): Second atomic formula.

    Returns:
        Optional[Dict[Variable, Term]]: MGU substitution dictionary or None.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.resolution.prefixed import _try_unify_formulas
        >>> p = PredicateApp("P", 0, ())
        >>> _try_unify_formulas(p, p)
        {}
    """
    if f1 == f2:
        return {}
    try:
        return unify_formulas(f1, f2)
    except UnificationError:
        if isinstance(f1, Equality) and isinstance(f2, Equality):
            try:
                subst = unify_terms(f1.left, f2.right)
                subst = unify_terms(f1.right, f2.left, subst)
                return subst
            except UnificationError:
                return None
        return None


def resolve_prefixed_clauses(
    c1: PrefixedClause,
    c2: PrefixedClause,
    subst: Optional[PrefixSubstitution] = None,
    tree: Optional[FormulaTree] = None,
) -> List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
    """Computes all possible binary resolvents between two prefixed clauses under admissible prefix unifiers and term unification.

    Args:
        c1 (PrefixedClause): First parent clause.
        c2 (PrefixedClause): Second parent clause.
        subst (Optional[PrefixSubstitution], default=None): Current accumulated prefix substitution.
        tree (Optional[FormulaTree], default=None): Formula tree used for reduction ordering admissibility.

    Returns:
        List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
            List of (resolvent_clause, new_substitution, lit1, lit2) tuples.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant, PrefixVariable
        >>> from logic_prover.constructive.resolution.clauses import PrefixedClause, PrefixedLiteral
        >>> from logic_prover.constructive.resolution.prefixed import resolve_prefixed_clauses
        >>> p = PredicateApp("P", 0, ())
        >>> c0 = PrefixConstant("c0")
        >>> v1 = PrefixVariable("V1")
        >>> l1 = PrefixedLiteral(Prefix((c0, v1)), 1, p)
        >>> l2 = PrefixedLiteral(Prefix((c0, c0)), 0, p)
        >>> cl1 = PrefixedClause(frozenset([l1]))
        >>> cl2 = PrefixedClause(frozenset([l2]))
        >>> res = resolve_prefixed_clauses(cl1, cl2)
        >>> len(res)
        1
        >>> res[0][0].is_empty()
        True
    """
    initial_subst = subst.copy() if subst is not None else PrefixSubstitution()
    results: List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]] = []

    for l1 in c1.literals:
        # Check complementary literal in c2
        for l2 in c2.literals:
            if l1.polarity != l2.polarity:
                term_unif = _try_unify_formulas(l1.atom, l2.atom)
                if term_unif is not None:
                    unifs = unify_prefixes(l1.prefix, l2.prefix, initial_subst)
                    for unif in unifs:
                        if tree is None or is_admissible(tree, unif):
                            # Construct resolvent: (c1 \ {l1}) U (c2 \ {l2}) instantiated by unif and term_unif
                            rem1 = set(c1.literals) - {l1}
                            rem2 = set(c2.literals) - {l2}
                            combined = rem1 | rem2
                            resolvent = PrefixedClause(frozenset(lit.substitute(unif).substitute_terms(term_unif) for lit in combined))
                            results.append((resolvent, unif, l1, l2))

    return results


def factor_prefixed_clause(
    clause: PrefixedClause,
    subst: Optional[PrefixSubstitution] = None,
    tree: Optional[FormulaTree] = None,
) -> List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
    """Computes all possible factors of a prefixed clause by unifying identical literals under prefix and term unification.

    Args:
        clause (PrefixedClause): The clause to factor.
        subst (Optional[PrefixSubstitution], default=None): Accumulated prefix substitution.
        tree (Optional[FormulaTree], default=None): Formula tree for admissibility validation.

    Returns:
        List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
            List of (factored_clause, new_substitution, lit1, lit2) tuples.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant, PrefixVariable
        >>> from logic_prover.constructive.resolution.clauses import PrefixedClause, PrefixedLiteral
        >>> from logic_prover.constructive.resolution.prefixed import factor_prefixed_clause
        >>> p = PredicateApp("P", 0, ())
        >>> c0 = PrefixConstant("c0")
        >>> v1 = PrefixVariable("V1")
        >>> l1 = PrefixedLiteral(Prefix((c0, v1)), 1, p)
        >>> l2 = PrefixedLiteral(Prefix((c0, c0)), 1, p)
        >>> cl = PrefixedClause(frozenset([l1, l2]))
        >>> factors = factor_prefixed_clause(cl)
        >>> len(factors)
        1
        >>> len(factors[0][0])
        1
    """
    initial_subst = subst.copy() if subst is not None else PrefixSubstitution()
    results: List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]] = []
    lits = list(clause.literals)

    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            l1, l2 = lits[i], lits[j]
            if l1.polarity == l2.polarity:
                term_unif = _try_unify_formulas(l1.atom, l2.atom)
                if term_unif is not None:
                    unifs = unify_prefixes(l1.prefix, l2.prefix, initial_subst)
                    for unif in unifs:
                        if tree is None or is_admissible(tree, unif):
                            rem = set(lits) - {l2}
                            factored = PrefixedClause(frozenset(lit.substitute(unif).substitute_terms(term_unif) for lit in rem))
                            results.append((factored, unif, l1, l2))

    return results


def _paramodulate_clauses(
    c1: PrefixedClause,
    c2: PrefixedClause,
    subst: Optional[PrefixSubstitution] = None,
    tree: Optional[FormulaTree] = None,
) -> List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
    """Derives paramodulants between a positive equality literal in c1 and a target literal in c2.

    Applies first-order paramodulation (subterm replacement under term unification)
    oriented by Knuth-Bendix Ordering (KBO).

    Args:
        c1 (PrefixedClause): Left parent clause containing a positive equality literal.
        c2 (PrefixedClause): Right parent clause containing a target literal.
        subst (Optional[PrefixSubstitution], default=None): Accumulated prefix substitution.
        tree (Optional[FormulaTree], default=None): Formula tree for prefix admissibility.

    Returns:
        List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]:
            List of (paramodulant_clause, new_substitution, eq_lit, target_lit) tuples.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Constant, Equality
        >>> from logic_prover.constructive.prefix import Prefix, PrefixConstant
        >>> from logic_prover.constructive.resolution.clauses import PrefixedClause, PrefixedLiteral
        >>> from logic_prover.constructive.resolution.prefixed import _paramodulate_clauses
        >>> a, b = Constant("a"), Constant("b")
        >>> c0 = PrefixConstant("c0")
        >>> l_eq = PrefixedLiteral(Prefix((c0,)), 1, Equality(a, b))
        >>> l_p = PrefixedLiteral(Prefix((c0,)), 1, PredicateApp("P", 1, (a,)))
        >>> c1 = PrefixedClause(frozenset([l_eq]))
        >>> c2 = PrefixedClause(frozenset([l_p]))
        >>> paramods = _paramodulate_clauses(c1, c2)
        >>> len(paramods) >= 1
        True
    """
    initial_subst = subst.copy() if subst is not None else PrefixSubstitution()
    results: List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]] = []

    for l_eq in c1.literals:
        if isinstance(l_eq.atom, Equality) and l_eq.polarity == 1:
            eq = l_eq.atom
            cmp_res = kbo_compare(eq.left, eq.right)
            orientations: List[Tuple[Term, Term]] = []
            if cmp_res == "gt":
                orientations.append((eq.left, eq.right))
            elif cmp_res == "lt":
                orientations.append((eq.right, eq.left))
            else:
                orientations.append((eq.left, eq.right))
                orientations.append((eq.right, eq.left))

            for l_target in c2.literals:
                unifs = unify_prefixes(l_eq.prefix, l_target.prefix, initial_subst)
                for unif in unifs:
                    if tree is None or is_admissible(tree, unif):
                        for src, dst in orientations:
                            variants = equality_substitution(Equality(src, dst), l_target.atom)
                            for v_atom in variants:
                                if v_atom != l_target.atom:
                                    paramod_lit = PrefixedLiteral(
                                        prefix=l_target.prefix,
                                        polarity=l_target.polarity,
                                        atom=v_atom,
                                    )
                                    rem1 = set(c1.literals) - {l_eq}
                                    rem2 = set(c2.literals) - {l_target}
                                    combined = (rem1 | rem2) | {paramod_lit}
                                    paramodulant = PrefixedClause(frozenset(lit.substitute(unif) for lit in combined))
                                    results.append((paramodulant, unif, l_eq, l_target))

    return results


class PrefixedResolutionProver:
    """Resolution theorem prover operating directly on prefixed clauses for IPC.

    Args:
        max_multiplicity (int, default=3): Maximum multiplicity bound for phi-node duplications.
        max_steps (int, default=1000): Maximum search iterations per multiplicity level.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.prefixed import PrefixedResolutionProver
        >>> p = PredicateApp("P", 0, ())
        >>> prover = PrefixedResolutionProver()
        >>> res = prover.prove(Implies(p, p))
        >>> res is not None and res.is_valid
        True
    """

    max_multiplicity: int
    max_steps: int

    def __init__(self, max_multiplicity: int = 3, max_steps: int = 1000) -> None:
        """Initializes the PrefixedResolutionProver with search bounds.

        Args:
            max_multiplicity (int, default=3): Maximum multiplicity limit.
            max_steps (int, default=1000): Maximum search iteration limit.
        """
        self.max_multiplicity = max(1, max_multiplicity)
        self.max_steps = max(1, max_steps)

    def prove(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> Optional[PrefixedResolutionProofResult]:
        """Attempts to prove a formula in Intuitionistic Propositional Logic using Prefixed Resolution.

        Args:
            target (Formula): Goal formula AST to prove.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis premises.

        Returns:
            Optional[PrefixedResolutionProofResult]: Proof result if proven valid, None otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution.prefixed import PrefixedResolutionProver
            >>> p = PredicateApp("P", 0, ())
            >>> prover = PrefixedResolutionProver()
            >>> proof = prover.prove(Implies(p, p))
            >>> proof is not None and proof.is_valid
            True
        """
        norm_target = normalize_formula(target)
        norm_premises = tuple(normalize_formula(p) for p in (premises or []))

        for mult in range(1, self.max_multiplicity + 1):
            initial_clauses, tree = clausify_prefixed(
                target=norm_target,
                premises=norm_premises,
                multiplicity=mult,
            )

            if not initial_clauses:
                continue

            proof = self._search_refutation(
                target=norm_target,
                premises=norm_premises,
                initial_clauses=initial_clauses,
                tree=tree,
                multiplicity=mult,
            )
            if proof is not None:
                return proof

        return None

    def _search_refutation(
        self,
        target: Formula,
        premises: Tuple[Formula, ...],
        initial_clauses: List[PrefixedClause],
        tree: FormulaTree,
        multiplicity: int,
    ) -> Optional[PrefixedResolutionProofResult]:
        """Conducts a resolution refutation search closing all initial matrix clauses.

        Args:
            target (Formula): Goal formula.
            premises (Tuple[Formula, ...]): Hypothesis premises.
            initial_clauses (List[PrefixedClause]): Initial decomposed clauses.
            tree (FormulaTree): Decomposition tree for admissibility.
            multiplicity (int): Current multiplicity level.

        Returns:
            Optional[PrefixedResolutionProofResult]: Derived refutation proof or None.
        """
        initial_steps: List[PrefixedResolutionStep] = []
        for i, c in enumerate(initial_clauses, 1):
            initial_steps.append(
                PrefixedResolutionStep(
                    id=f"init_{i}",
                    rule_name="initial",
                    premise_ids=(),
                    clause=c,
                    substitution=PrefixSubstitution(),
                )
            )

        def _find_clause_candidates(
            clause: PrefixedClause,
        ) -> List[Tuple[str, Optional[Tuple[PrefixedLiteral, PrefixedLiteral]], PrefixedLiteral]]:
            candidates = []
            lits = list(clause.literals)
            for i, l1 in enumerate(lits):
                if _is_falsum(l1.atom) and l1.polarity == 1:
                    candidates.append(("falsum_elimination", None, l1))
                if isinstance(l1.atom, Equality) and l1.atom.left == l1.atom.right and l1.polarity == 0:
                    candidates.append(("reflexivity_elimination", None, l1))
                for j in range(i + 1, len(lits)):
                    l2 = lits[j]
                    if l1.polarity != l2.polarity:
                        if _try_unify_formulas(l1.atom, l2.atom) is not None:
                            pos = l1 if l1.polarity == 1 else l2
                            neg = l2 if l1.polarity == 1 else l1
                            candidates.append(("resolution", (pos, neg), pos))

            # Intra-clause equality rewriting: T(s = t) rewrites F(u = v) or other literals
            for l_eq in lits:
                if isinstance(l_eq.atom, Equality) and l_eq.polarity == 1:
                    eq = l_eq.atom
                    orientations = [(eq.left, eq.right), (eq.right, eq.left)]
                    for l_target in lits:
                        if l_target != l_eq:
                            for src, dst in orientations:
                                variants = equality_substitution(Equality(src, dst), l_target.atom)
                                for v in variants:
                                    if v != l_target.atom:
                                        if l_target.polarity == 0 and isinstance(v, Equality) and v.left == v.right:
                                            # Rewrote to F(t = t), a reflexivity clash
                                            candidates.append(("reflexivity_elimination", (l_eq, l_target), l_target))
                                        # Check if rewritten v is complementary to another literal in clause
                                        for l_other in lits:
                                            if l_other != l_target and l_other.polarity != l_target.polarity:
                                                if _try_unify_formulas(v, l_other.atom) is not None:
                                                    pos = l_other if l_other.polarity == 1 else l_target
                                                    neg = l_target if l_other.polarity == 1 else l_other
                                                    candidates.append(("resolution", (pos, neg), pos))
            return candidates

        def _backtrack(
            remaining: List[Tuple[PrefixedClause, str]],
            current_subst: PrefixSubstitution,
            accum_steps: List[PrefixedResolutionStep],
            step_count: int,
        ) -> Optional[Tuple[List[PrefixedResolutionStep], str, PrefixSubstitution]]:
            # Filter already closed clauses
            unclosed: List[Tuple[PrefixedClause, str]] = []
            for clause, init_id in remaining:
                c_inst = clause.substitute(current_subst)
                # Check if this clause is already closed under current substitution
                closed = False
                c_lits = list(c_inst.literals)
                for i, l1 in enumerate(c_lits):
                    if _is_falsum(l1.atom) and l1.polarity == 1:
                        closed = True
                        break
                    if isinstance(l1.atom, Equality) and l1.atom.left == l1.atom.right and l1.polarity == 0:
                        closed = True
                        break
                    for j in range(i + 1, len(c_lits)):
                        l2 = c_lits[j]
                        if l1.polarity != l2.polarity and l1.prefix == l2.prefix and _try_unify_formulas(l1.atom, l2.atom) is not None:
                            closed = True
                            break
                    if closed:
                        break
                if not closed:
                    unclosed.append((clause, init_id))

            if not unclosed:
                if is_admissible(tree, current_subst):
                    empty_id = f"s{step_count + 1}"
                    empty_step = PrefixedResolutionStep(
                        id=empty_id,
                        rule_name="empty_clause",
                        premise_ids=tuple(s.id for s in accum_steps[-2:]) if accum_steps else (),
                        clause=PrefixedClause(),
                        substitution=current_subst,
                    )
                    return accum_steps + [empty_step], empty_id, current_subst
                return None

            unclosed.sort(key=lambda item: len(_find_clause_candidates(item[0])))
            target_clause, init_id = unclosed[0]
            rest = unclosed[1:]

            candidates = _find_clause_candidates(target_clause)
            if not candidates:
                return None

            for rule_name, pair, main_lit in candidates:
                if rule_name == "falsum_elimination":
                    step_count += 1
                    s_id = f"s{step_count}"
                    step = PrefixedResolutionStep(
                        id=s_id,
                        rule_name="falsum_elimination",
                        premise_ids=(init_id,),
                        clause=PrefixedClause(),
                        substitution=current_subst,
                        parent_literals=(main_lit, main_lit),
                    )
                    res = _backtrack(rest, current_subst, accum_steps + [step], step_count)
                    if res is not None:
                        return res
                elif rule_name == "reflexivity_elimination":
                    step_count += 1
                    s_id = f"s{step_count}"
                    step = PrefixedResolutionStep(
                        id=s_id,
                        rule_name="reflexivity_elimination",
                        premise_ids=(init_id,),
                        clause=PrefixedClause(),
                        substitution=current_subst,
                        parent_literals=(main_lit, main_lit),
                    )
                    res = _backtrack(rest, current_subst, accum_steps + [step], step_count)
                    if res is not None:
                        return res
                elif rule_name == "resolution" and pair is not None:
                    pos_lit, neg_lit = pair
                    unifs = unify_prefixes(pos_lit.prefix, neg_lit.prefix, current_subst)
                    for unif in unifs:
                        if is_admissible(tree, unif):
                            step_count += 1
                            s_id = f"s{step_count}"
                            step = PrefixedResolutionStep(
                                id=s_id,
                                rule_name="resolution",
                                premise_ids=(init_id,),
                                clause=PrefixedClause(),
                                substitution=unif,
                                parent_literals=pair,
                            )
                            res = _backtrack(rest, unif, accum_steps + [step], step_count)
                            if res is not None:
                                return res

            return None

        indexed_clauses = [(c, f"init_{i}") for i, c in enumerate(initial_clauses, 1)]
        refute_res = _backtrack(
            remaining=indexed_clauses,
            current_subst=PrefixSubstitution(),
            accum_steps=initial_steps,
            step_count=len(initial_clauses),
        )

        if refute_res is not None:
            all_steps, empty_id, final_subst = refute_res
            return PrefixedResolutionProofResult(
                is_valid=True,
                target=target,
                premises=premises,
                steps=tuple(all_steps),
                empty_clause_id=empty_id,
                substitution=final_subst,
                multiplicity=multiplicity,
            )

        return None


def prove_prefixed_resolution(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_multiplicity: int = 3,
    max_steps: int = 1000,
) -> Optional[PrefixedResolutionProofResult]:
    """Proves an intuitionistic propositional formula using Prefixed Resolution.

    Args:
        formula (Formula): Goal formula to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis premises.
        max_multiplicity (int, default=3): Multiplicity bound for phi-node duplications.
        max_steps (int, default=1000): Maximum search iterations.

    Returns:
        Optional[PrefixedResolutionProofResult]: Derivation proof result if valid, None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.prefixed import prove_prefixed_resolution
        >>> p = PredicateApp("P", 0, ())
        >>> proof = prove_prefixed_resolution(Implies(p, p))
        >>> proof is not None and proof.is_valid
        True
    """
    prover = PrefixedResolutionProver(
        max_multiplicity=max_multiplicity,
        max_steps=max_steps,
    )
    return prover.prove(target=formula, premises=premises)


__all__ = [
    "_try_unify_formulas",
    "resolve_prefixed_clauses",
    "factor_prefixed_clause",
    "_paramodulate_clauses",
    "PrefixedResolutionProver",
    "prove_prefixed_resolution",
]
