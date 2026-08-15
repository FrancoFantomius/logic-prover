"""Validation engine for checking AST sort and signature consistency."""

from __future__ import annotations
from typing import List, Set, Union, Optional

from logic.core.ast import (
    Term, Formula, Variable, Constant, FunctionApp,
    PredicateApp, Equality, Not, And, Or, Implies, Iff,
    Forall, Exists, VariableKind
)
from logic.core.sorts import Sort, Ind, is_compatible
from logic.core.signature import Signature
from logic.core.exceptions import ValidationError


from logic.sol.ast_ext import (
    PredicateVariable, FunctionVariable,
    ForallPred, ExistsPred, ForallFunc, ExistsFunc
)


def _get_term_sort(term: Term, signature: Signature) -> Sort:
    """Infer sort of term considering signature declarations."""
    if isinstance(term, Variable):
        return term.sort
    elif isinstance(term, Constant):
        decl_sort = signature.lookup_constant(term.name)
        return decl_sort if decl_sort is not None else term.sort
    elif isinstance(term, FunctionApp):
        if isinstance(term.func, FunctionVariable):
            return term.func.return_sort
        decl = signature.lookup_function(term.func)
        return decl.return_sort if decl is not None else term.return_sort
    else:
        return getattr(term, "sort", Ind)


def validate_term(
    term: Term,
    signature: Signature,
    scope: Optional[Set[Variable]] = None
) -> List[ValidationError]:
    """Validate a term AST node for symbol registration, arity, and sort correctness.

    Args:
        term: The term node to validate.
        signature: The logical signature context.
        scope: Set of currently bound variables in outer scopes.

    Returns:
        A list of validation errors found in the term (empty if well-formed).
    """
    errors: List[ValidationError] = []

    if isinstance(term, Variable):
        if term.kind != VariableKind.INDIVIDUAL:
            errors.append(
                ValidationError(
                    f"Variable v_{term.id} must be of INDIVIDUAL kind in First-Order Logic, got {term.kind}."
                )
            )
        if term.id < 0:
            errors.append(ValidationError(f"Variable ID must be non-negative, got {term.id}."))

    elif isinstance(term, Constant):
        decl_sort = signature.lookup_constant(term.name)
        if decl_sort is None:
            errors.append(ValidationError(f"Unregistered constant symbol '{term.name}'."))
        else:
            if not is_compatible(term.sort, decl_sort):
                errors.append(
                    ValidationError(
                        f"Constant '{term.name}' sort {term.sort} incompatible with registered sort {decl_sort}."
                    )
                )

    elif isinstance(term, FunctionApp):
        if isinstance(term.func, FunctionVariable):
            if term.arity != term.func.arity or len(term.args) != term.func.arity:
                errors.append(
                    ValidationError(
                        f"FunctionVariable '{term.func.name}' arity mismatch: expected {term.func.arity}, got {term.arity}."
                    )
                )
            if not is_compatible(term.return_sort, term.func.return_sort):
                errors.append(
                    ValidationError(
                        f"FunctionApp '{term.func.name}' return sort {term.return_sort} incompatible with {term.func.return_sort}."
                    )
                )
            for i, arg in enumerate(term.args):
                errors.extend(validate_term(arg, signature, scope))
                if i < len(term.func.arg_sorts):
                    arg_sort = _get_term_sort(arg, signature)
                    expected_sort = term.func.arg_sorts[i]
                    if not is_compatible(arg_sort, expected_sort):
                        errors.append(
                            ValidationError(
                                f"FunctionVariable '{term.func.name}' argument {i} sort mismatch: expected {expected_sort}, got {arg_sort}."
                            )
                        )
        else:
            decl = signature.lookup_function(term.func)
            if decl is None:
                errors.append(ValidationError(f"Unregistered function symbol '{term.func}'."))
            else:
                if term.arity != decl.arity or len(term.args) != decl.arity:
                    errors.append(
                        ValidationError(
                            f"Function '{term.func}' arity mismatch: expected {decl.arity}, got {term.arity}."
                        )
                    )
                if not is_compatible(term.return_sort, decl.return_sort):
                    errors.append(
                        ValidationError(
                            f"FunctionApp '{term.func}' return sort {term.return_sort} incompatible with registered return sort {decl.return_sort}."
                        )
                    )

            # Recursively validate argument terms and check argument sort compatibility
            for i, arg in enumerate(term.args):
                errors.extend(validate_term(arg, signature, scope))
                if decl is not None and i < len(decl.arg_sorts):
                    arg_sort = _get_term_sort(arg, signature)
                    expected_sort = decl.arg_sorts[i]
                    if not is_compatible(arg_sort, expected_sort):
                        errors.append(
                            ValidationError(
                                f"Function '{term.func}' argument {i} sort mismatch: expected {expected_sort}, got {arg_sort}."
                            )
                        )

    else:
        errors.append(ValidationError(f"Unsupported term node type: {type(term)}."))

    return errors


def validate_formula(
    formula: Formula,
    signature: Signature,
    scope: Optional[Set[Variable]] = None
) -> List[ValidationError]:
    """Validate a formula AST node for arity, sorts, binder scoping, and quantifier well-formedness.

    Args:
        formula: The formula node to validate.
        signature: The logical signature context.
        scope: Set of currently bound variables in outer scopes.

    Returns:
        A list of validation errors found in the formula (empty if well-formed).
    """
    errors: List[ValidationError] = []

    if isinstance(formula, PredicateApp):
        if isinstance(formula.pred, PredicateVariable):
            if formula.arity != formula.pred.arity or len(formula.args) != formula.pred.arity:
                errors.append(
                    ValidationError(
                        f"PredicateVariable '{formula.pred.name}' arity mismatch: expected {formula.pred.arity}, got {formula.arity}."
                    )
                )
            for arg in formula.args:
                errors.extend(validate_term(arg, signature, scope))
        else:
            decl = signature.lookup_predicate(formula.pred)
            if decl is None:
                errors.append(ValidationError(f"Unregistered predicate symbol '{formula.pred}'."))
            else:
                if formula.arity != decl.arity or len(formula.args) != decl.arity:
                    errors.append(
                        ValidationError(
                            f"Predicate '{formula.pred}' arity mismatch: expected {decl.arity}, got {formula.arity}."
                        )
                    )

            for i, arg in enumerate(formula.args):
                errors.extend(validate_term(arg, signature, scope))
                if decl is not None and i < len(decl.arg_sorts):
                    arg_sort = _get_term_sort(arg, signature)
                    expected_sort = decl.arg_sorts[i]
                    if not is_compatible(arg_sort, expected_sort):
                        errors.append(
                            ValidationError(
                                f"Predicate '{formula.pred}' argument {i} sort mismatch: expected {expected_sort}, got {arg_sort}."
                            )
                        )

    elif isinstance(formula, Equality):
        errors.extend(validate_term(formula.left, signature, scope))
        errors.extend(validate_term(formula.right, signature, scope))
        left_sort = _get_term_sort(formula.left, signature)
        right_sort = _get_term_sort(formula.right, signature)
        if not is_compatible(left_sort, right_sort):
            errors.append(
                ValidationError(
                    f"Equality sort mismatch: left sort {left_sort} vs right sort {right_sort}."
                )
            )

    elif isinstance(formula, Not):
        errors.extend(validate_formula(formula.operand, signature, scope))

    elif isinstance(formula, (And, Or, Implies, Iff)):
        errors.extend(validate_formula(formula.left, signature, scope))
        errors.extend(validate_formula(formula.right, signature, scope))

    elif isinstance(formula, (Forall, Exists)):
        var = formula.variable
        if var.kind != VariableKind.INDIVIDUAL:
            errors.append(
                ValidationError(
                    f"Quantifier variable v_{var.id} must be of INDIVIDUAL kind in First-Order Logic, got {var.kind}."
                )
            )
        if var.id < 0:
            errors.append(ValidationError(f"Variable ID must be non-negative, got {var.id}."))

        scope_set = set(scope) if scope is not None else set()
        if any(v.id == var.id for v in scope_set):
            errors.append(ValidationError(f"Duplicate binder in scope: variable {var.id}."))

        new_scope = scope_set | {var}
        errors.extend(validate_formula(formula.body, signature, new_scope))

    elif isinstance(formula, (ForallPred, ExistsPred)):
        if formula.variable.index < 0 or formula.variable.arity < 0:
            errors.append(ValidationError(f"Invalid PredicateVariable {formula.variable}."))
        errors.extend(validate_formula(formula.body, signature, scope))

    elif isinstance(formula, (ForallFunc, ExistsFunc)):
        if formula.variable.index < 0 or formula.variable.arity < 0:
            errors.append(ValidationError(f"Invalid FunctionVariable {formula.variable}."))
        errors.extend(validate_formula(formula.body, signature, scope))

    else:
        errors.append(ValidationError(f"Unsupported formula node type: {type(formula)}."))

    return errors


def is_well_formed(node: Union[Term, Formula], signature: Signature) -> bool:
    """Convenience wrapper returning True if the AST node has zero validation errors."""
    if isinstance(node, Term):
        return len(validate_term(node, signature)) == 0
    elif isinstance(node, Formula):
        return len(validate_formula(node, signature)) == 0
    else:
        return False
