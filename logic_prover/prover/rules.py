"""Inference rules for resolution, factoring, paramodulation, and SOL instantiation."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Callable, Any, Set, Union

from logic_prover.core.ast import (
    Term, Variable, FunctionApp, Formula, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists, free_variables
)
from logic_prover.core.substitutions import (
    unify_formulas, unify_terms, UnificationError, substitute_formula, substitute_term
)
from logic_prover.prover.clausifier import Clause, Literal


@dataclass(frozen=True, slots=True)
class InferenceRule:
    name: str
    description: str
    rule_type: str  # "resolution" or "reconstruction"
    apply: Callable[..., List[Any]]


def standardize_clause_variables(c1: Clause, c2: Clause) -> Tuple[Clause, Clause, Dict[Variable, Variable]]:
    """
    Renames free variables in c2 so their variable IDs do not overlap with c1.

    Args:
        c1: First clause (kept unchanged).
        c2: Second clause, whose variables may be renamed.

    Returns:
        Tuple (c1, renamed_c2, variable_renaming_map).
    """
    c1_vars = c1.free_variables()
    c2_vars = c2.free_variables()
    common_vars = c1_vars & c2_vars
    if not common_vars and not (c1_vars and c2_vars):
        return c1, c2, {}

    max_id1 = max([v.id for v in c1_vars], default=0)
    max_id2 = max([v.id for v in c2_vars], default=0)
    offset = max(max_id1, max_id2) + 1

    renaming: Dict[Variable, Term] = {}
    var_map: Dict[Variable, Variable] = {}
    for v in c2_vars:
        new_v = Variable(id=v.id + offset, sort=v.sort, kind=v.kind)
        renaming[v] = new_v
        var_map[v] = new_v

    c2_std = c2.substitute(renaming)
    return c1, c2_std, var_map


def resolve_clauses(
    c1: Clause,
    c2: Clause
) -> List[Tuple[Clause, Dict[Variable, Term], Tuple[Literal, Literal]]]:
    """
    Binary Resolution Rule:
    Given c1 containing L1 and c2 containing L2 where L1.positive != L2.positive:
    Standardizes variables apart, unifies L1.atom and L2.atom with MGU σ.

    Args:
        c1: First input clause.
        c2: Second input clause.

    Returns:
        List of tuples (resolvent_clause, MGU_substitution, (L1, L2)).
    """
    c1_std, c2_std, _ = standardize_clause_variables(c1, c2)
    results: List[Tuple[Clause, Dict[Variable, Term], Tuple[Literal, Literal]]] = []
    seen: Set[Clause] = set()

    for l1 in c1_std.literals:
        for l2 in c2_std.literals:
            if l1.positive != l2.positive:
                try:
                    mgu = unify_formulas(l1.atom, l2.atom)
                    rem_c1 = {l for l in c1_std.literals if l != l1}
                    rem_c2 = {l for l in c2_std.literals if l != l2}
                    resolvent = Clause(frozenset(rem_c1 | rem_c2)).substitute(mgu)
                    if resolvent not in seen:
                        seen.add(resolvent)
                        results.append((resolvent, mgu, (l1, l2)))
                except UnificationError:
                    continue
    return results


def factor_clause(
    c: Clause
) -> List[Tuple[Clause, Dict[Variable, Term]]]:
    """
    Factoring Rule:
    Given c containing L1 and L2 with same polarity:
    Unifies L1.atom and L2.atom with MGU σ.

    Args:
        c: The clause to factor.

    Returns:
        List of tuples (factored_clause, MGU_substitution).
    """
    results: List[Tuple[Clause, Dict[Variable, Term]]] = []
    seen: Set[Clause] = set()
    lits = list(c.literals)
    n = len(lits)
    for i in range(n):
        for j in range(i + 1, n):
            l1, l2 = lits[i], lits[j]
            if l1.positive == l2.positive:
                try:
                    mgu = unify_formulas(l1.atom, l2.atom)
                    factored = c.substitute(mgu)
                    if len(factored.literals) < len(c.literals) and factored not in seen:
                        seen.add(factored)
                        results.append((factored, mgu))
                except UnificationError:
                    continue
    return results


def extract_subterms(term: Term) -> List[Term]:
    """Recursively collects all subterms of a term.

    Args:
        term: The term to traverse.

    Returns:
        List of all subterms including the term itself.
    """
    subterms = [term]
    if isinstance(term, FunctionApp):
        for arg in term.args:
            subterms.extend(extract_subterms(arg))
    return subterms


def extract_atom_subterms(atom: Union[PredicateApp, Equality]) -> List[Term]:
    """Collects all term subterms from a predicate application or equality atom.

    Args:
        atom: The atom to traverse.

    Returns:
        List of all term subterms found in the atom.
    """
    subterms: List[Term] = []
    if isinstance(atom, PredicateApp):
        for arg in atom.args:
            subterms.extend(extract_subterms(arg))
    elif isinstance(atom, Equality):
        subterms.extend(extract_subterms(atom.left))
        subterms.extend(extract_subterms(atom.right))
    return subterms


def replace_subterm(term: Term, target: Term, replacement: Term) -> List[Term]:
    """Replaces occurrences of target subterm with replacement in term.

    Args:
        term: The term in which to replace subterms.
        target: The subterm to locate.
        replacement: The term to substitute in place of target.

    Returns:
        List of distinct terms obtained by replacing one occurrence of target.
    """
    results: List[Term] = []
    if term == target:
        results.append(replacement)
    if isinstance(term, FunctionApp):
        for i, arg in enumerate(term.args):
            for new_arg in replace_subterm(arg, target, replacement):
                new_args = list(term.args)
                new_args[i] = new_arg
                results.append(FunctionApp(func=term.func, arity=term.arity, args=tuple(new_args), return_sort=term.return_sort))
    return results


def replace_atom_subterm(atom: Union[PredicateApp, Equality], target: Term, replacement: Term) -> List[Union[PredicateApp, Equality]]:
    """Replaces occurrences of target subterm with replacement in atom.

    Args:
        atom: The atom in which to replace subterms.
        target: The subterm to locate.
        replacement: The term to substitute in place of target.

    Returns:
        List of distinct atoms obtained by replacing one occurrence of target.
    """
    results: List[Union[PredicateApp, Equality]] = []
    if isinstance(atom, PredicateApp):
        for i, arg in enumerate(atom.args):
            for new_arg in replace_subterm(arg, target, replacement):
                new_args = list(atom.args)
                new_args[i] = new_arg
                results.append(PredicateApp(pred=atom.pred, arity=atom.arity, args=tuple(new_args)))
    elif isinstance(atom, Equality):
        for new_left in replace_subterm(atom.left, target, replacement):
            results.append(Equality(left=new_left, right=atom.right))
        for new_right in replace_subterm(atom.right, target, replacement):
            results.append(Equality(left=atom.left, right=new_right))
    return results


def paramodulate(
    c1: Clause,
    c2: Clause
) -> List[Tuple[Clause, Dict[Variable, Term]]]:
    r"""
    Paramodulation Rule (Equality Rewriting):
    Given c1 containing positive equality literal (t1 = t2) [or (t2 = t1)],
    and c2 containing literal L[s] with subterm s unifiable with t1 via MGU σ:
    Derives paramodulant σ((c1 \ {t1=t2}) ∪ (c2 with s replaced by t2)).

    Args:
        c1: First clause (source of equality literal).
        c2: Second clause (target of rewriting).

    Returns:
        List of tuples (paramodulant_clause, MGU_substitution).
    """
    results: List[Tuple[Clause, Dict[Variable, Term]]] = []
    seen: Set[Clause] = set()

    def _param_ordered(cla: Clause, clb: Clause) -> None:
        cla_std, clb_std, _ = standardize_clause_variables(cla, clb)
        for l_eq in cla_std.literals:
            if l_eq.positive and isinstance(l_eq.atom, Equality):
                t1, t2 = l_eq.atom.left, l_eq.atom.right
                orientations = [(t1, t2), (t2, t1)]
                for lhs, rhs in orientations:
                    for l_target in clb_std.literals:
                        subterms = extract_atom_subterms(l_target.atom)
                        for s in subterms:
                            if isinstance(s, Variable):
                                continue
                            try:
                                mgu = unify_terms(s, lhs)
                                s_subst = substitute_term(s, mgu)
                                rhs_subst = substitute_term(rhs, mgu)
                                for new_atom in replace_atom_subterm(l_target.atom, s, rhs):
                                    new_lit = Literal(atom=new_atom, positive=l_target.positive)
                                    rem_cla = {l for l in cla_std.literals if l != l_eq}
                                    rem_clb = {l for l in clb_std.literals if l != l_target}
                                    paramodulant = Clause(frozenset(rem_cla | rem_clb | {new_lit})).substitute(mgu)
                                    if paramodulant not in seen:
                                        seen.add(paramodulant)
                                        results.append((paramodulant, mgu))
                            except UnificationError:
                                continue

    _param_ordered(c1, c2)
    _param_ordered(c2, c1)
    return results


def get_resolution_rules() -> List[InferenceRule]:
    """Returns the set of core CNF resolution rules."""
    return [
        InferenceRule("BinaryResolution", "Resolve complementary literals", "resolution", resolve_clauses),
        InferenceRule("Factoring", "Merge unifiable literals in same clause", "resolution", factor_clause),
        InferenceRule("Paramodulation", "Equality subterm rewriting", "resolution", paramodulate),
    ]


def get_reconstruction_rules() -> List[InferenceRule]:
    """Returns standard Natural Deduction inference rules used in ProofDAG."""
    return [
        InferenceRule("Axiom", "Premise or hypothesis assumption", "reconstruction", lambda *args: []),
        InferenceRule("NegatedGoal", "Clausified negation of target theorem", "reconstruction", lambda *args: []),
        InferenceRule("ModusPonens", "A, A ⟹ B  ⊢  B", "reconstruction", lambda *args: []),
        InferenceRule("UniversalInstantiation", "∀x P(x)  ⊢  P(t)", "reconstruction", lambda *args: []),
        InferenceRule("ExistentialIntroduction", "P(t)  ⊢  ∃x P(x)", "reconstruction", lambda *args: []),
        InferenceRule("AndIntroduction", "A, B  ⊢  A ∧ B", "reconstruction", lambda *args: []),
        InferenceRule("AndElimination", "A ∧ B  ⊢  A (or B)", "reconstruction", lambda *args: []),
        InferenceRule("OrIntroduction", "A  ⊢  A ∨ B", "reconstruction", lambda *args: []),
        InferenceRule("OrElimination", "A ∨ B, A ⟹ C, B ⟹ C  ⊢  C", "reconstruction", lambda *args: []),
        InferenceRule("DoubleNegationElimination", "¬¬A  ⊢  A", "reconstruction", lambda *args: []),
        InferenceRule("Contradiction", "A, ¬A  ⊢  ⊥", "reconstruction", lambda *args: []),
        InferenceRule("ResolutionTraceStep", "CNF trace resolution inference", "reconstruction", lambda *args: []),
    ]


class SOLInstantiateRule(InferenceRule):
    """
    Inference rule that attempts to instantiate SOL quantified axioms (e.g. Peano Induction)
    against target goal clauses or formulas using higher-order pattern matching.
    Generates ground FOL clauses for the CNF resolution solver.
    """

    def __init__(self) -> None:
        """Constructs the SOL instantiation rule with its metadata and apply function."""
        super().__init__(
            name="SOLInstantiate",
            description="Second-order logic template instantiation via higher-order pattern matching",
            rule_type="resolution",
            apply=self.match_and_instantiate
        )

    def match_and_instantiate(
        self,
        sol_axiom: Formula,
        target_goal: Formula,
        signature: Any = None
    ) -> List[Clause]:
        """Matches second-order logic templates against target goals and instantiates clauses.

        Args:
            sol_axiom: The SOL quantified axiom to instantiate.
            target_goal: The target formula to match the template against.
            signature: Optional Signature for validating instantiated clauses.

        Returns:
            List of Clause objects derived by instantiating the axiom.
        """
        from logic_prover.sol.ast_ext import ForallPred, ExistsPred, PredicateVariable
        from logic_prover.sol.substitutions_ext import ho_pattern_unify, substitute_predicate
        from logic_prover.sol.kb_ext import instantiate_induction
        from logic_prover.prover.clausifier import to_cnf

        clauses: List[Clause] = []

        if isinstance(sol_axiom, ForallPred):
            p_var = sol_axiom.variable
            body = sol_axiom.body

            conc = body.right if isinstance(body, Implies) else body

            subst = None
            if isinstance(conc, Forall) and isinstance(target_goal, Forall):
                subst = ho_pattern_unify(conc.body, target_goal.body, bound_vars={conc.variable})
                if subst and p_var in subst:
                    # Parameter for P is conc.variable
                    param_var = conc.variable
                    prop_template = subst[p_var][1] if isinstance(subst[p_var], tuple) else subst[p_var]
                    # Inductive instantiation
                    fol_instance = substitute_predicate(body, {p_var: ( (param_var,), prop_template )})
                    clauses.extend(to_cnf(fol_instance, signature=signature))
                    return clauses

            subst = ho_pattern_unify(conc, target_goal)
            if subst and p_var in subst:
                fol_instance = substitute_predicate(body, {p_var: subst[p_var]})
                clauses.extend(to_cnf(fol_instance, signature=signature))
                return clauses

        if isinstance(target_goal, Forall):
            fol_instance = instantiate_induction(target_goal.body, target_goal.variable)
            clauses.extend(to_cnf(fol_instance, signature=signature))

        return clauses


def apply_rule(
    rule: InferenceRule,
    premises: List[Any],
    context: Optional[Dict[str, Any]] = None
) -> List[Any]:
    """Applies an inference rule to premises with optional context parameters.

    Args:
        rule: The inference rule to apply.
        premises: Positional arguments passed to the rule's apply function.
        context: Optional keyword arguments passed to the rule's apply function.

    Returns:
        List of results produced by the rule's apply function.
    """
    return rule.apply(*premises, **(context or {}))
