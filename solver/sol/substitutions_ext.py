"""Higher-order pattern unification and beta-reduction algorithms for SOL."""

from __future__ import annotations
from typing import Dict, Tuple, Set, Optional, Union, Any

from solver.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists, free_variables
)
from solver.sol.ast_ext import (
    PredicateVariable, FunctionVariable,
    ForallPred, ExistsPred, ForallFunc, ExistsFunc,
    free_predicate_variables, free_function_variables
)
from solver.core.substitutions import substitute_formula, substitute_term, unify_terms, unify_formulas
from solver.core.exceptions import UnificationError
from solver.core.sorts import Ind


def is_ho_pattern(
    app: Union[PredicateApp, FunctionApp],
    bound_vars: Optional[Set[Variable]] = None
) -> bool:
    """
    Checks if an application node is a valid Miller-Pfenning higher-order pattern:
    1. The head symbol is a PredicateVariable or FunctionVariable.
    2. All argument expressions are individual Variable instances.
    3. The argument variables are pairwise distinct.
    4. All argument variables belong to the current bound_vars scope (if specified).
    """
    head = app.pred if isinstance(app, PredicateApp) else app.func
    if not isinstance(head, (PredicateVariable, FunctionVariable)):
        return False

    arg_vars: List[Variable] = []
    for arg in app.args:
        if not isinstance(arg, Variable):
            return False
        if bound_vars is not None and len(bound_vars) > 0 and arg not in bound_vars:
            return False
        if arg in arg_vars:
            return False  # Arguments must be pairwise distinct
        arg_vars.append(arg)

    return True


def beta_reduce_predicate(
    template: Formula,
    params: Tuple[Variable, ...],
    args: Tuple[Term, ...]
) -> Formula:
    """
    Applies arguments to a predicate formula template φ(x_1, ..., x_k).
    Performs parameter substitution [x_i ↦ t_i] with full capture avoidance.
    """
    if len(params) != len(args):
        raise UnificationError(
            f"Beta reduction parameter count mismatch: expected {len(params)}, got {len(args)}"
        )
    mapping = {params[i]: args[i] for i in range(len(params))}
    return substitute_formula(template, mapping)


def beta_reduce_function(
    template: Term,
    params: Tuple[Variable, ...],
    args: Tuple[Term, ...]
) -> Term:
    """
    Applies arguments to a function term template t(x_1, ..., x_k).
    Performs parameter substitution [x_i ↦ t_i] with full capture avoidance.
    """
    if len(params) != len(args):
        raise UnificationError(
            f"Beta reduction parameter count mismatch: expected {len(params)}, got {len(args)}"
        )
    mapping = {params[i]: args[i] for i in range(len(params))}
    return substitute_term(template, mapping)


def substitute_predicate(
    formula: Formula,
    mapping: Dict[PredicateVariable, Union[Formula, Tuple[Tuple[Variable, ...], Formula]]],
    params_mapping: Optional[Dict[PredicateVariable, Tuple[Variable, ...]]] = None
) -> Formula:
    """
    Substitutes occurrences of PredicateApp(pred=P, args=(t1, ..., tk)) where P in mapping
    with the corresponding formula template φ, performing beta-reduction [x_i ↦ t_i].
    """
    if isinstance(formula, PredicateApp):
        new_args = tuple(
            substitute_function(arg, {}) if isinstance(arg, Term) else arg
            for arg in formula.args
        )
        if formula.pred in mapping:
            val = mapping[formula.pred]
            if isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], tuple):
                params, template = val
            elif params_mapping and formula.pred in params_mapping:
                params = params_mapping[formula.pred]
                template = val
            else:
                params = tuple(Variable(id=i, sort=Ind) for i in range(formula.pred.arity))
                template = val
            return beta_reduce_predicate(template, params, new_args)
        return PredicateApp(pred=formula.pred, arity=formula.arity, args=new_args)

    elif isinstance(formula, Equality):
        return Equality(left=formula.left, right=formula.right)

    elif isinstance(formula, Not):
        return Not(operand=substitute_predicate(formula.operand, mapping, params_mapping))

    elif isinstance(formula, And):
        return And(
            left=substitute_predicate(formula.left, mapping, params_mapping),
            right=substitute_predicate(formula.right, mapping, params_mapping)
        )

    elif isinstance(formula, Or):
        return Or(
            left=substitute_predicate(formula.left, mapping, params_mapping),
            right=substitute_predicate(formula.right, mapping, params_mapping)
        )

    elif isinstance(formula, Implies):
        return Implies(
            left=substitute_predicate(formula.left, mapping, params_mapping),
            right=substitute_predicate(formula.right, mapping, params_mapping)
        )

    elif isinstance(formula, Iff):
        return Iff(
            left=substitute_predicate(formula.left, mapping, params_mapping),
            right=substitute_predicate(formula.right, mapping, params_mapping)
        )

    elif isinstance(formula, Forall):
        return Forall(variable=formula.variable, body=substitute_predicate(formula.body, mapping, params_mapping))

    elif isinstance(formula, Exists):
        return Exists(variable=formula.variable, body=substitute_predicate(formula.body, mapping, params_mapping))

    elif isinstance(formula, ForallPred):
        if formula.variable in mapping:
            sub_map = {k: v for k, v in mapping.items() if k != formula.variable}
            return ForallPred(variable=formula.variable, body=substitute_predicate(formula.body, sub_map, params_mapping))
        return ForallPred(variable=formula.variable, body=substitute_predicate(formula.body, mapping, params_mapping))

    elif isinstance(formula, ExistsPred):
        if formula.variable in mapping:
            sub_map = {k: v for k, v in mapping.items() if k != formula.variable}
            return ExistsPred(variable=formula.variable, body=substitute_predicate(formula.body, sub_map, params_mapping))
        return ExistsPred(variable=formula.variable, body=substitute_predicate(formula.body, mapping, params_mapping))

    elif isinstance(formula, (ForallFunc, ExistsFunc)):
        return type(formula)(variable=formula.variable, body=substitute_predicate(formula.body, mapping, params_mapping))

    return formula


def substitute_function(
    node: Union[Formula, Term],
    mapping: Dict[FunctionVariable, Union[Term, Tuple[Tuple[Variable, ...], Term]]],
    params_mapping: Optional[Dict[FunctionVariable, Tuple[Variable, ...]]] = None
) -> Union[Formula, Term]:
    """
    Substitutes occurrences of FunctionApp(func=F, args=(t1, ..., tk)) where F in mapping
    with the corresponding term template t, performing beta-reduction [x_i ↦ t_i].
    """
    if isinstance(node, FunctionApp):
        new_args = tuple(
            substitute_function(arg, mapping, params_mapping) for arg in node.args
        )
        if node.func in mapping:
            val = mapping[node.func]
            if isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], tuple):
                params, template = val
            elif params_mapping and node.func in params_mapping:
                params = params_mapping[node.func]
                template = val
            else:
                params = tuple(Variable(id=i, sort=Ind) for i in range(node.func.arity))
                template = val
            return beta_reduce_function(template, params, new_args)
        return FunctionApp(func=node.func, arity=node.arity, args=new_args, return_sort=node.return_sort)

    elif isinstance(node, (Variable, Constant)):
        return node

    elif isinstance(node, PredicateApp):
        new_args = tuple(
            substitute_function(arg, mapping, params_mapping) for arg in node.args
        )
        return PredicateApp(pred=node.pred, arity=node.arity, args=new_args)

    elif isinstance(node, Equality):
        return Equality(
            left=substitute_function(node.left, mapping, params_mapping),
            right=substitute_function(node.right, mapping, params_mapping)
        )

    elif isinstance(node, Not):
        return Not(operand=substitute_function(node.operand, mapping, params_mapping))

    elif isinstance(node, (And, Or, Implies, Iff)):
        return type(node)(
            left=substitute_function(node.left, mapping, params_mapping),
            right=substitute_function(node.right, mapping, params_mapping)
        )

    elif isinstance(node, (Forall, Exists)):
        return type(node)(
            variable=node.variable,
            body=substitute_function(node.body, mapping, params_mapping)
        )

    elif isinstance(node, (ForallPred, ExistsPred)):
        return type(node)(
            variable=node.variable,
            body=substitute_function(node.body, mapping, params_mapping)
        )

    elif isinstance(node, (ForallFunc, ExistsFunc)):
        if node.variable in mapping:
            sub_map = {k: v for k, v in mapping.items() if k != node.variable}
            return type(node)(variable=node.variable, body=substitute_function(node.body, sub_map, params_mapping))
        return type(node)(variable=node.variable, body=substitute_function(node.body, mapping, params_mapping))

    return node


def apply_subst(node: Union[Formula, Term], subst: Dict[Any, Any]) -> Union[Formula, Term]:
    """Applies a combined substitution mapping (Variable, PredicateVariable, FunctionVariable)."""
    res = node
    pred_subst = {k: v for k, v in subst.items() if isinstance(k, PredicateVariable)}
    if pred_subst and isinstance(res, Formula):
        res = substitute_predicate(res, pred_subst)
    func_subst = {k: v for k, v in subst.items() if isinstance(k, FunctionVariable)}
    if func_subst:
        res = substitute_function(res, func_subst)
    var_subst = {k: v for k, v in subst.items() if isinstance(k, Variable)}
    if var_subst:
        if isinstance(res, Formula):
            res = substitute_formula(res, var_subst)
        elif isinstance(res, Term):
            res = substitute_term(res, var_subst)
    return res


def compose_subst(subst1: Dict[Any, Any], subst2: Dict[Any, Any]) -> Dict[Any, Any]:
    """Composes two substitution dictionaries: subst1 o subst2."""
    res = {}
    for k, v in subst1.items():
        if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], tuple):
            params, template = v
            res[k] = (params, apply_subst(template, subst2))
        else:
            res[k] = apply_subst(v, subst2)
    for k, v in subst2.items():
        if k not in res:
            res[k] = v
    return res


def ho_pattern_unify(
    node1: Union[Formula, Term],
    node2: Union[Formula, Term],
    bound_vars: Optional[Set[Variable]] = None
) -> Optional[Dict[Union[PredicateVariable, FunctionVariable, Variable], Any]]:
    """
    Miller-Pfenning Higher-Order Pattern Unification algorithm.
    Restricted to higher-order patterns: P(x_1, ..., x_k) where x_i are distinct bound variables.

    Returns a unified substitution dictionary mapping:
    - PredicateVariable -> Tuple[Tuple[Variable, ...], Formula] (params, formula_template)
    - FunctionVariable -> Tuple[Tuple[Variable, ...], Term] (params, term_template)
    - Variable -> Term

    Returns None if unification fails or nodes are not in pattern form.
    """
    b_vars = set(bound_vars) if bound_vars is not None else set()

    if node1 == node2:
        return {}

    # Case 1: PredicateApp with PredicateVariable head (Pattern vs Target)
    if isinstance(node1, PredicateApp) and isinstance(node1.pred, PredicateVariable):
        if is_ho_pattern(node1, b_vars):
            if node1.pred in free_predicate_variables(node2):
                return None  # Occurrences check failure
            pattern_args = set(node1.args)
            for y in free_variables(node2):
                if b_vars and y in b_vars and y not in pattern_args:
                    return None  # Scope check failure
            assert isinstance(node2, Formula)
            params = tuple(arg for arg in node1.args if isinstance(arg, Variable))
            return {node1.pred: (params, node2)}
        return None

    # Case 2: Target vs PredicateApp (Symmetric)
    if isinstance(node2, PredicateApp) and isinstance(node2.pred, PredicateVariable):
        if is_ho_pattern(node2, b_vars):
            if node2.pred in free_predicate_variables(node1):
                return None  # Occurrences check failure
            pattern_args = set(node2.args)
            for y in free_variables(node1):
                if b_vars and y in b_vars and y not in pattern_args:
                    return None  # Scope check failure
            assert isinstance(node1, Formula)
            params = tuple(arg for arg in node2.args if isinstance(arg, Variable))
            return {node2.pred: (params, node1)}
        return None

    # Case 3: FunctionApp with FunctionVariable head (Pattern vs Target)
    if isinstance(node1, FunctionApp) and isinstance(node1.func, FunctionVariable):
        if is_ho_pattern(node1, b_vars):
            if node1.func in free_function_variables(node2):
                return None  # Occurrences check failure
            pattern_args = set(node1.args)
            for y in free_variables(node2):
                if b_vars and y in b_vars and y not in pattern_args:
                    return None  # Scope check failure
            assert isinstance(node2, Term)
            params = tuple(arg for arg in node1.args if isinstance(arg, Variable))
            return {node1.func: (params, node2)}
        return None

    # Case 4: Target vs FunctionApp (Symmetric)
    if isinstance(node2, FunctionApp) and isinstance(node2.func, FunctionVariable):
        if is_ho_pattern(node2, b_vars):
            if node2.func in free_function_variables(node1):
                return None  # Occurrences check failure
            pattern_args = set(node2.args)
            for y in free_variables(node1):
                if b_vars and y in b_vars and y not in pattern_args:
                    return None  # Scope check failure
            assert isinstance(node1, Term)
            params = tuple(arg for arg in node2.args if isinstance(arg, Variable))
            return {node2.func: (params, node1)}
        return None

    # Case 5: First-Order Variable vs Term/Formula
    if isinstance(node1, Variable):
        if node1 in free_variables(node2):
            return None
        return {node1: node2}

    if isinstance(node2, Variable):
        if node2 in free_variables(node1):
            return None
        return {node2: node1}

    # Case 6: Binary Formula Operators (And, Or, Implies, Iff)
    if type(node1) is type(node2) and isinstance(node1, (And, Or, Implies, Iff)):
        assert isinstance(node2, (And, Or, Implies, Iff))
        s1 = ho_pattern_unify(node1.left, node2.left, b_vars)
        if s1 is None:
            return None
        r1_sub = apply_subst(node1.right, s1)
        r2_sub = apply_subst(node2.right, s1)
        s2 = ho_pattern_unify(r1_sub, r2_sub, b_vars)
        if s2 is None:
            return None
        return compose_subst(s1, s2)

    # Case 7: Equality
    if isinstance(node1, Equality) and isinstance(node2, Equality):
        s1 = ho_pattern_unify(node1.left, node2.left, b_vars)
        if s1 is None:
            return None
        r1_sub = apply_subst(node1.right, s1)
        r2_sub = apply_subst(node2.right, s1)
        s2 = ho_pattern_unify(r1_sub, r2_sub, b_vars)
        if s2 is None:
            return None
        return compose_subst(s1, s2)

    # Case 8: Not
    if isinstance(node1, Not) and isinstance(node2, Not):
        return ho_pattern_unify(node1.operand, node2.operand, b_vars)

    # Case 9: Quantifiers (Forall, Exists)
    if type(node1) is type(node2) and isinstance(node1, (Forall, Exists)):
        assert isinstance(node2, (Forall, Exists))
        v1, v2 = node1.variable, node2.variable
        b1 = node1.body
        b2 = substitute_formula(node2.body, {v2: v1}) if v1 != v2 else node2.body
        return ho_pattern_unify(b1, b2, b_vars | {v1})

    # Case 10: SOL Quantifiers (ForallPred, ExistsPred, ForallFunc, ExistsFunc)
    if type(node1) is type(node2) and isinstance(node1, (ForallPred, ExistsPred, ForallFunc, ExistsFunc)):
        if getattr(node1, "variable") == getattr(node2, "variable"):
            return ho_pattern_unify(node1.body, node2.body, b_vars)
        return None

    # Case 11: Rigid-Rigid Application Matching (PredicateApp or FunctionApp with identical string heads)
    if type(node1) is type(node2) and isinstance(node1, PredicateApp):
        assert isinstance(node2, PredicateApp)
        if node1.pred == node2.pred and len(node1.args) == len(node2.args):
            current_subst: Dict[Any, Any] = {}
            for a1, a2 in zip(node1.args, node2.args):
                a1_sub = apply_subst(a1, current_subst)
                a2_sub = apply_subst(a2, current_subst)
                sub = ho_pattern_unify(a1_sub, a2_sub, b_vars)
                if sub is None:
                    return None
                current_subst = compose_subst(current_subst, sub)
            return current_subst
        return None

    if type(node1) is type(node2) and isinstance(node1, FunctionApp):
        assert isinstance(node2, FunctionApp)
        if node1.func == node2.func and len(node1.args) == len(node2.args):
            current_subst: Dict[Any, Any] = {}
            for a1, a2 in zip(node1.args, node2.args):
                a1_sub = apply_subst(a1, current_subst)
                a2_sub = apply_subst(a2, current_subst)
                sub = ho_pattern_unify(a1_sub, a2_sub, b_vars)
                if sub is None:
                    return None
                current_subst = compose_subst(current_subst, sub)
            return current_subst
        return None

    return None
