"""Substitutions and term/formula unification algorithms."""

from __future__ import annotations
from typing import Dict, Set, Optional, Union, Callable, cast

from logic.core.ast import (
    Term,
    Variable,
    Constant,
    FunctionApp,
    Formula,
    PredicateApp,
    Equality,
    Forall,
    Exists,
    free_variables,
    bound_variables,
)
from logic.core.sorts import is_compatible, sort_of_term
from logic.core.visitors import ASTTransformer
from logic.core.exceptions import UnificationError, SortMismatchError


class SubstitutionTransformer(ASTTransformer):
    """AST transformer for capture-avoiding variable substitution."""

    mapping: Dict[Variable, Term]
    scope_bound_vars: Set[Variable]

    def __init__(self, mapping: Dict[Variable, Term]) -> None:
        """Initializes a SubstitutionTransformer instance with mapping."""
        super().__init__()
        self.mapping = mapping
        self.scope_bound_vars = set()

    def visit_variable(self, node: Variable) -> Term:
        if node in self.mapping:
            return self.mapping[node]
        return node

    def visit_constant(self, node: Constant) -> Term:
        return node

    def visit_function_app(self, node: FunctionApp) -> FunctionApp:
        new_args = tuple(self.visit(arg) for arg in node.args)
        return FunctionApp(
            func=node.func,
            arity=node.arity,
            args=tuple(cast(Term, arg) for arg in new_args),
            return_sort=node.return_sort,
        )

    def visit_predicate_app(self, node: PredicateApp) -> PredicateApp:
        new_args = tuple(self.visit(arg) for arg in node.args)
        return PredicateApp(
            pred=node.pred,
            arity=node.arity,
            args=tuple(cast(Term, arg) for arg in new_args),
        )

    def visit_equality(self, node: Equality) -> Equality:
        new_left = self.visit(node.left)
        new_right = self.visit(node.right)
        assert isinstance(new_left, Term) and isinstance(new_right, Term)
        return Equality(left=new_left, right=new_right)

    def visit_forall(self, node: Forall) -> Formula:
        return self._handle_quantifier(node.variable, node.body, Forall)

    def visit_exists(self, node: Exists) -> Formula:
        return self._handle_quantifier(node.variable, node.body, Exists)

    def _handle_quantifier(
        self,
        bound_var: Variable,
        body: Formula,
        constructor: Callable[[Variable, Formula], Formula],
    ) -> Formula:
        # 1. Shadowing: remove bound_var from active mapping for inner scope
        old_mapping_val = self.mapping.pop(bound_var, None)

        # 2. Check if bound_var would capture any free variable in replacement terms
        # Collect free variables of all replacement terms for variables free in body
        body_free_vars = free_variables(body)
        relevant_replacements = [
            self.mapping[var] for var in body_free_vars if var in self.mapping
        ]
        replacement_free_vars: Set[Variable] = set()
        for repl in relevant_replacements:
            replacement_free_vars.update(free_variables(repl))

        # Capture occurs if bound_var is in replacement_free_vars
        if bound_var in replacement_free_vars:
            # 3. Generate a fresh variable that doesn't conflict
            fresh_var = self._generate_fresh_variable(
                base_var=bound_var,
                forbidden=body_free_vars
                | replacement_free_vars
                | bound_variables(body)
                | self.scope_bound_vars,
            )
            # Rename bound_var to fresh_var in body before substitution
            body = self._rename_bound_variable(body, bound_var, fresh_var)
            target_var = fresh_var
        else:
            target_var = bound_var

        # 4. Process body recursively
        self.scope_bound_vars.add(target_var)
        res_body = self.visit(body)
        self.scope_bound_vars.remove(target_var)
        assert isinstance(res_body, Formula)

        # Restore shadowed mapping entry
        if old_mapping_val is not None:
            self.mapping[bound_var] = old_mapping_val

        return constructor(target_var, res_body)

    def _generate_fresh_variable(
        self, base_var: Variable, forbidden: Set[Variable]
    ) -> Variable:
        forbidden_ids = {v.id for v in forbidden}
        new_id = base_var.id
        while new_id in forbidden_ids:
            new_id += 1
        return Variable(id=new_id, sort=base_var.sort, kind=base_var.kind)

    def _rename_bound_variable(
        self, formula: Formula, old_var: Variable, new_var: Variable
    ) -> Formula:
        renamer = SubstitutionTransformer({old_var: new_var})
        res = renamer.visit(formula)
        assert isinstance(res, Formula)
        return res


def _validate_mapping_sorts(mapping: Dict[Variable, Term]) -> None:
    """Validates that for all (v -> t) in mapping, is_compatible(v.sort, sort_of_term(t)) holds."""
    for var, term in mapping.items():
        term_sort = sort_of_term(term)
        if not is_compatible(var.sort, term_sort):
            raise SortMismatchError(
                f"Sort mismatch in substitution: variable v{var.id} has sort {var.sort}, "
                f"but replacement term has sort {term_sort}.",
                expected_sort=var.sort,
                actual_sort=term_sort,
            )


def substitute_term(term: Term, mapping: Dict[Variable, Term]) -> Term:
    """Replaces variables in a term according to mapping.

    Args:
        term: Target Term AST node.
        mapping: Dictionary mapping variables to replacement terms.

    Returns:
        New Term node with variables substituted.

    Raises:
        SortMismatchError: If any mapped term sort is incompatible with variable sort.
    """
    _validate_mapping_sorts(mapping)
    if not mapping:
        return term
    transformer = SubstitutionTransformer(mapping)
    res = transformer.visit(term)
    assert isinstance(res, Term)
    return res


def substitute_formula(formula: Formula, mapping: Dict[Variable, Term]) -> Formula:
    """Replaces free variables in a formula while preventing variable capture.

    Args:
        formula: Target Formula AST node.
        mapping: Dictionary mapping free variables to replacement terms.

    Returns:
        New Formula node with capture-avoiding substitution applied.

    Raises:
        SortMismatchError: If any mapped term sort is incompatible with variable sort.
    """
    _validate_mapping_sorts(mapping)
    if not mapping:
        return formula
    transformer = SubstitutionTransformer(mapping)
    res = transformer.visit(formula)
    assert isinstance(res, Formula)
    return res


def apply_substitution(subst: Dict[Variable, Term], term: Term) -> Term:
    """Applies a substitution mapping to a term (idempotent helper wrapper).

    Args:
        subst: Substitution dictionary.
        term: Target term.

    Returns:
        Substituted term.
    """
    return substitute_term(term, subst)


def compose_substitutions(
    s1: Dict[Variable, Term], s2: Dict[Variable, Term]
) -> Dict[Variable, Term]:
    """Composes two substitutions s1 and s2 such that:
    apply_substitution(compose_substitutions(s1, s2), t) == apply_substitution(s1, apply_substitution(s2, t))

    Mathematical Definition: (s1 o s2)(x) = s1(s2(x))

    Args:
        s1: First substitution applied (outer substitution).
        s2: Second substitution applied (inner substitution).

    Returns:
        Composed substitution dictionary.
    """
    _validate_mapping_sorts(s1)
    _validate_mapping_sorts(s2)

    result: Dict[Variable, Term] = {}

    for x, t_x in s2.items():
        t_x_prime = substitute_term(t_x, s1)
        if x != t_x_prime:
            result[x] = t_x_prime

    for y, t_y in s1.items():
        if y not in s2 and y != t_y:
            result[y] = t_y

    return result


def unify_terms(
    t1: Term, t2: Term, subst: Optional[Dict[Variable, Term]] = None
) -> Dict[Variable, Term]:
    """Implements Robinson's unification algorithm on first-order terms with occur-check
    and sort compatibility checking.

    Args:
        t1: First term.
        t2: Second term.
        subst: Accumulated substitution context (optional).

    Returns:
        Most General Unifier (MGU) as a dictionary mapping variables to terms.

    Raises:
        UnificationError: If terms cannot be unified (e.g. constant mismatch, arity mismatch, occur-check failure).
        SortMismatchError: If term sorts are incompatible during variable binding.
    """
    if subst is None:
        subst = {}
    else:
        subst = dict(subst)

    def deref(t: Term, s: Dict[Variable, Term]) -> Term:
        while isinstance(t, Variable) and t in s:
            t = s[t]
        return t

    t1 = deref(t1, subst)
    t2 = deref(t2, subst)

    if t1 == t2:
        return subst

    if isinstance(t1, Variable):
        t2 = substitute_term(t2, subst)
        if t1 == t2:
            return subst
        if t1 in free_variables(t2):
            raise UnificationError(f"Occur-check failed: variable v{t1.id} occurs in {t2}")
        t2_sort = sort_of_term(t2)
        if not is_compatible(t1.sort, t2_sort):
            raise SortMismatchError(
                f"Sort mismatch unifying v{t1.id} ({t1.sort}) with term ({t2_sort})",
                expected_sort=t1.sort,
                actual_sort=t2_sort,
            )
        subst[t1] = t2
        for v, val in list(subst.items()):
            if v != t1:
                subst[v] = substitute_term(val, {t1: t2})
        return subst

    if isinstance(t2, Variable):
        return unify_terms(t2, t1, subst)

    if isinstance(t1, Constant) and isinstance(t2, Constant):
        if t1.name != t2.name:
            raise UnificationError(f"Constant mismatch: '{t1.name}' vs '{t2.name}'")
        if not is_compatible(t1.sort, t2.sort):
            raise SortMismatchError(
                f"Sort mismatch unifying constant '{t1.name}' ({t1.sort}) with ({t2.sort})",
                expected_sort=t1.sort,
                actual_sort=t2.sort,
            )
        return subst

    if isinstance(t1, FunctionApp) and isinstance(t2, FunctionApp):
        if t1.func != t2.func or t1.arity != t2.arity:
            raise UnificationError(
                f"Function symbol/arity mismatch: '{t1.func}/{t1.arity}' vs '{t2.func}/{t2.arity}'"
            )
        if not is_compatible(t1.return_sort, t2.return_sort):
            raise SortMismatchError(
                f"Return sort mismatch in function unification: {t1.return_sort} vs {t2.return_sort}",
                expected_sort=t1.return_sort,
                actual_sort=t2.return_sort,
            )
        curr_subst = subst
        for a1, a2 in zip(t1.args, t2.args):
            curr_subst = unify_terms(a1, a2, curr_subst)
        return curr_subst

    raise UnificationError(
        f"Cannot unify incompatible term structures: {type(t1).__name__} and {type(t2).__name__}"
    )


def unify_formulas(f1: Formula, f2: Formula) -> Dict[Variable, Term]:
    """Unifies atomic predicate expressions (first-order only).

    Args:
        f1: First atomic formula (PredicateApp or Equality).
        f2: Second atomic formula (PredicateApp or Equality).

    Returns:
        MGU substitution dictionary.

    Raises:
        UnificationError: If formulas are non-atomic or predicates/arities mismatch.
    """
    if isinstance(f1, PredicateApp) and isinstance(f2, PredicateApp):
        if f1.pred != f2.pred or f1.arity != f2.arity:
            raise UnificationError(
                f"Predicate symbol/arity mismatch: '{f1.pred}/{f1.arity}' vs '{f2.pred}/{f2.arity}'"
            )
        curr_subst: Dict[Variable, Term] = {}
        for a1, a2 in zip(f1.args, f2.args):
            curr_subst = unify_terms(a1, a2, curr_subst)
        return curr_subst

    if isinstance(f1, Equality) and isinstance(f2, Equality):
        curr_subst = unify_terms(f1.left, f2.left)
        curr_subst = unify_terms(f1.right, f2.right, curr_subst)
        return curr_subst

    raise UnificationError("Unification is strictly restricted to first-order atomic formulas.")
