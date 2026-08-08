"""AST extensions for Second-Order Logic (predicate/function variables and quantifiers)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Set, Union

from logic.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic.core.sorts import Sort, Ind
from logic.core.exceptions import InvalidFormulaError


@dataclass(frozen=True)
class PredicateVariable:
    """Quantifiable predicate variable P_index with a fixed arity."""

    index: int
    arity: int

    def __post_init__(self) -> None:
        if self.index < 0:
            raise InvalidFormulaError(f"PredicateVariable index must be >= 0, got {self.index}.")
        if self.arity < 0:
            raise InvalidFormulaError(f"PredicateVariable arity must be >= 0, got {self.arity}.")

    @property
    def name(self) -> str:
        return f"P_{self.index}"


@dataclass(frozen=True)
class FunctionVariable:
    """Quantifiable function variable F_index with argument sorts and return sort."""

    index: int
    arity: int
    arg_sorts: Tuple[Sort, ...]
    return_sort: Sort = Ind

    def __post_init__(self) -> None:
        if self.index < 0:
            raise InvalidFormulaError(f"FunctionVariable index must be >= 0, got {self.index}.")
        if self.arity < 0:
            raise InvalidFormulaError(f"FunctionVariable arity must be >= 0, got {self.arity}.")
        if len(self.arg_sorts) != self.arity:
            raise InvalidFormulaError(
                f"FunctionVariable arity {self.arity} does not match arg_sorts count {len(self.arg_sorts)}."
            )

    @property
    def name(self) -> str:
        return f"F_{self.index}"


@dataclass(frozen=True)
class ForallPred(Formula):
    """Universal quantification over a predicate variable: ∀P. φ"""

    variable: PredicateVariable
    body: Formula


@dataclass(frozen=True)
class ExistsPred(Formula):
    """Existential quantification over a predicate variable: ∃P. φ"""

    variable: PredicateVariable
    body: Formula


@dataclass(frozen=True)
class ForallFunc(Formula):
    """Universal quantification over a function variable: ∀F. φ"""

    variable: FunctionVariable
    body: Formula


@dataclass(frozen=True)
class ExistsFunc(Formula):
    """Existential quantification over a function variable: ∃F. φ"""

    variable: FunctionVariable
    body: Formula


def free_predicate_variables(node: Union[Formula, Term]) -> Set[PredicateVariable]:
    """Returns all unquantified PredicateVariable instances in a formula or term."""
    if isinstance(node, PredicateApp):
        res: Set[PredicateVariable] = set()
        if isinstance(node.pred, PredicateVariable):
            res.add(node.pred)
        for arg in node.args:
            res.update(free_predicate_variables(arg))
        return res
    elif isinstance(node, FunctionApp):
        res = set()
        for arg in node.args:
            res.update(free_predicate_variables(arg))
        return res
    elif isinstance(node, Equality):
        return free_predicate_variables(node.left) | free_predicate_variables(node.right)
    elif isinstance(node, Not):
        return free_predicate_variables(node.operand)
    elif isinstance(node, (And, Or, Implies, Iff)):
        return free_predicate_variables(node.left) | free_predicate_variables(node.right)
    elif isinstance(node, (Forall, Exists)):
        return free_predicate_variables(node.body)
    elif isinstance(node, (ForallPred, ExistsPred)):
        return free_predicate_variables(node.body) - {node.variable}
    elif isinstance(node, (ForallFunc, ExistsFunc)):
        return free_predicate_variables(node.body)
    else:
        return set()


def bound_predicate_variables(node: Union[Formula, Term]) -> Set[PredicateVariable]:
    """Returns all quantified PredicateVariable instances in a formula."""
    if isinstance(node, (ForallPred, ExistsPred)):
        return {node.variable} | bound_predicate_variables(node.body)
    elif isinstance(node, (ForallFunc, ExistsFunc, Forall, Exists)):
        return bound_predicate_variables(node.body)
    elif isinstance(node, Not):
        return bound_predicate_variables(node.operand)
    elif isinstance(node, (And, Or, Implies, Iff)):
        return bound_predicate_variables(node.left) | bound_predicate_variables(node.right)
    elif isinstance(node, (PredicateApp, FunctionApp)):
        res: Set[PredicateVariable] = set()
        for arg in node.args:
            res.update(bound_predicate_variables(arg))
        return res
    elif isinstance(node, Equality):
        return bound_predicate_variables(node.left) | bound_predicate_variables(node.right)
    else:
        return set()


def free_function_variables(node: Union[Formula, Term]) -> Set[FunctionVariable]:
    """Returns all unquantified FunctionVariable instances in a formula or term."""
    if isinstance(node, FunctionApp):
        res: Set[FunctionVariable] = set()
        if isinstance(node.func, FunctionVariable):
            res.add(node.func)
        for arg in node.args:
            res.update(free_function_variables(arg))
        return res
    elif isinstance(node, PredicateApp):
        res = set()
        for arg in node.args:
            res.update(free_function_variables(arg))
        return res
    elif isinstance(node, Equality):
        return free_function_variables(node.left) | free_function_variables(node.right)
    elif isinstance(node, Not):
        return free_function_variables(node.operand)
    elif isinstance(node, (And, Or, Implies, Iff)):
        return free_function_variables(node.left) | free_function_variables(node.right)
    elif isinstance(node, (Forall, Exists)):
        return free_function_variables(node.body)
    elif isinstance(node, (ForallPred, ExistsPred)):
        return free_function_variables(node.body)
    elif isinstance(node, (ForallFunc, ExistsFunc)):
        return free_function_variables(node.body) - {node.variable}
    else:
        return set()


def bound_function_variables(node: Union[Formula, Term]) -> Set[FunctionVariable]:
    """Returns all quantified FunctionVariable instances in a formula."""
    if isinstance(node, (ForallFunc, ExistsFunc)):
        return {node.variable} | bound_function_variables(node.body)
    elif isinstance(node, (ForallPred, ExistsPred, Forall, Exists)):
        return bound_function_variables(node.body)
    elif isinstance(node, Not):
        return bound_function_variables(node.operand)
    elif isinstance(node, (And, Or, Implies, Iff)):
        return bound_function_variables(node.left) | bound_function_variables(node.right)
    elif isinstance(node, (FunctionApp, PredicateApp)):
        res: Set[FunctionVariable] = set()
        for arg in node.args:
            res.update(bound_function_variables(arg))
        return res
    elif isinstance(node, Equality):
        return bound_function_variables(node.left) | bound_function_variables(node.right)
    else:
        return set()
