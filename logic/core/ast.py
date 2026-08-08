"""Abstract Syntax Tree (AST) definitions for First-Order Logic terms and formulas."""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Set, Union, Dict, Optional, Any

from logic.core.sorts import Sort, Ind
from logic.core.exceptions import InvalidFormulaError


class VariableKind(Enum):
    """Distinguishes variable usage in logic expressions."""

    INDIVIDUAL = "INDIVIDUAL"
    PREDICATE = "PREDICATE"
    FUNCTION = "FUNCTION"


@dataclass(frozen=True)
class Term(ABC):
    """Abstract Base Class for all term AST nodes."""

    sort: Sort = field(default=Ind, kw_only=True)


@dataclass(frozen=True)
class Formula(ABC):
    """Abstract Base Class for all formula AST nodes."""

    pass


@dataclass(frozen=True)
class Variable(Term):
    """Represents an individual variable v_id with an integer index, sort, and kind."""

    id: int
    kind: VariableKind = VariableKind.INDIVIDUAL

    def __post_init__(self) -> None:
        if self.id < 0:
            raise InvalidFormulaError(f"Variable ID must be non-negative, got {self.id}.")


@dataclass(frozen=True)
class Constant(Term):
    """Represents a constant symbol c_name with a sort annotation."""

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise InvalidFormulaError("Constant name cannot be empty.")


@dataclass(frozen=True)
class FunctionApp(Term):
    """Represents function application f(t_1, ..., t_k)."""

    func: Union[str, Any]
    arity: int
    args: Tuple[Term, ...]
    return_sort: Sort = Ind

    def __post_init__(self) -> None:
        if isinstance(self.func, str):
            if not self.func:
                raise InvalidFormulaError("Function name cannot be empty.")
        elif hasattr(self.func, "index") and hasattr(self.func, "arity"):
            pass
        else:
            raise InvalidFormulaError(f"Function symbol must be str or FunctionVariable, got {type(self.func)}.")
        if self.arity < 0:
            raise InvalidFormulaError(f"Function arity must be non-negative, got {self.arity}.")
        if len(self.args) != self.arity:
            raise InvalidFormulaError(
                f"FunctionApp '{self.func}' expected arity {self.arity}, got {len(self.args)} arguments."
            )
        # Ensure underlying term sort matches return_sort
        object.__setattr__(self, "sort", self.return_sort)


@dataclass(frozen=True)
class PredicateApp(Formula):
    """Represents predicate application P(t_1, ..., t_k)."""

    pred: Union[str, Any]
    arity: int
    args: Tuple[Term, ...]

    def __post_init__(self) -> None:
        if isinstance(self.pred, str):
            if not self.pred:
                raise InvalidFormulaError("Predicate name cannot be empty.")
        elif hasattr(self.pred, "index") and hasattr(self.pred, "arity"):
            pass
        else:
            raise InvalidFormulaError(f"Predicate symbol must be str or PredicateVariable, got {type(self.pred)}.")
        if self.arity < 0:
            raise InvalidFormulaError(f"Predicate arity must be non-negative, got {self.arity}.")
        if len(self.args) != self.arity:
            raise InvalidFormulaError(
                f"PredicateApp '{self.pred}' expected arity {self.arity}, got {len(self.args)} arguments."
            )


@dataclass(frozen=True)
class Equality(Formula):
    """Represents term equality t_1 = t_2."""

    left: Term
    right: Term


@dataclass(frozen=True)
class Not(Formula):
    """Represents logical negation ~operand."""

    operand: Formula


@dataclass(frozen=True)
class And(Formula):
    """Represents logical conjunction left & right."""

    left: Formula
    right: Formula


@dataclass(frozen=True)
class Or(Formula):
    """Represents logical disjunction left | right."""

    left: Formula
    right: Formula


@dataclass(frozen=True)
class Implies(Formula):
    """Represents logical implication left => right."""

    left: Formula
    right: Formula


@dataclass(frozen=True)
class Iff(Formula):
    """Represents logical equivalence left <=> right."""

    left: Formula
    right: Formula


@dataclass(frozen=True)
class Forall(Formula):
    """Represents universal quantification forall variable. body."""

    variable: Variable
    body: Formula


@dataclass(frozen=True)
class Exists(Formula):
    """Represents existential quantification exists variable. body."""

    variable: Variable
    body: Formula


def free_variables(node: Union[Term, Formula]) -> Set[Variable]:
    """Returns the set of free individual variables present in a term or formula AST node."""
    if isinstance(node, Variable):
        return {node}
    elif isinstance(node, Constant):
        return set()
    elif isinstance(node, FunctionApp):
        res: Set[Variable] = set()
        for arg in node.args:
            res.update(free_variables(arg))
        return res
    elif isinstance(node, PredicateApp):
        res = set()
        for arg in node.args:
            res.update(free_variables(arg))
        return res
    elif isinstance(node, Equality):
        return free_variables(node.left) | free_variables(node.right)
    elif isinstance(node, Not):
        return free_variables(node.operand)
    elif isinstance(node, (And, Or, Implies, Iff)):
        return free_variables(node.left) | free_variables(node.right)
    elif isinstance(node, (Forall, Exists)):
        return free_variables(node.body) - {node.variable}
    elif type(node).__name__ in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
        return free_variables(getattr(node, "body"))
    else:
        raise InvalidFormulaError(f"Unsupported AST node type: {type(node)}")


def bound_variables(node: Union[Term, Formula]) -> Set[Variable]:
    """Returns the set of bound variables introduced by quantifiers in a formula AST node."""
    if isinstance(node, (Variable, Constant, FunctionApp, PredicateApp, Equality)):
        return set()
    elif isinstance(node, Not):
        return bound_variables(node.operand)
    elif isinstance(node, (And, Or, Implies, Iff)):
        return bound_variables(node.left) | bound_variables(node.right)
    elif isinstance(node, (Forall, Exists)):
        return {node.variable} | bound_variables(node.body)
    elif type(node).__name__ in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
        return bound_variables(getattr(node, "body"))
    else:
        raise InvalidFormulaError(f"Unsupported AST node type: {type(node)}")


def formula_depth(formula: Formula) -> int:
    """Computes the maximum height/depth of the formula AST.

    Leaf formula nodes (PredicateApp, Equality) have depth 1.
    """
    if isinstance(formula, (PredicateApp, Equality)):
        return 1
    elif isinstance(formula, Not):
        return 1 + formula_depth(formula.operand)
    elif isinstance(formula, (And, Or, Implies, Iff)):
        return 1 + max(formula_depth(formula.left), formula_depth(formula.right))
    elif isinstance(formula, (Forall, Exists)):
        return 1 + formula_depth(formula.body)
    elif type(formula).__name__ in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
        return 1 + formula_depth(getattr(formula, "body"))
    else:
        raise InvalidFormulaError(f"Expected Formula, got {type(formula)}")


def formula_size(formula: Formula) -> int:
    """Computes the total number of AST nodes (both Formula and Term nodes) in a formula tree."""

    def _term_size(term: Term) -> int:
        if isinstance(term, (Variable, Constant)):
            return 1
        elif isinstance(term, FunctionApp):
            return 1 + sum(_term_size(arg) for arg in term.args)
        else:
            raise InvalidFormulaError(f"Expected Term, got {type(term)}")

    if isinstance(formula, PredicateApp):
        return 1 + sum(_term_size(arg) for arg in formula.args)
    elif isinstance(formula, Equality):
        return 1 + _term_size(formula.left) + _term_size(formula.right)
    elif isinstance(formula, Not):
        return 1 + formula_size(formula.operand)
    elif isinstance(formula, (And, Or, Implies, Iff)):
        return 1 + formula_size(formula.left) + formula_size(formula.right)
    elif isinstance(formula, (Forall, Exists)):
        return 1 + _term_size(formula.variable) + formula_size(formula.body)
    elif type(formula).__name__ in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
        return 1 + formula_size(getattr(formula, "body"))
    else:
        raise InvalidFormulaError(f"Expected Formula, got {type(formula)}")


def canonicalize_bound_variables(formula: Formula) -> Formula:
    """Performs canonical alpha-conversion of bound variables in a formula.

    Free variables retain their original IDs and sorts.
    Bound variables are renamed sequentially (v_0, v_1, ...) skipping free variable IDs.

    Guarantees:
    1. Idempotency: canonicalize(canonicalize(f)) == canonicalize(f)
    2. Alpha-equivalence: If f1 and f2 are alpha-equivalent, canonicalize(f1) == canonicalize(f2)
    3. Free variable preservation: free_variables(canonicalize(f)) == free_variables(f)
    """
    free_vars = free_variables(formula)
    free_ids = {v.id for v in free_vars}

    class IndexGenerator:

        def __init__(self, reserved: Set[int]) -> None:
            self.reserved = reserved
            self.current = 0

        def get_next(self) -> int:
            while self.current in self.reserved:
                self.current += 1
            idx = self.current
            self.current += 1
            return idx

    gen = IndexGenerator(free_ids)

    def _canonicalize_term(t: Term, env: Dict[Variable, Variable]) -> Term:
        if isinstance(t, Variable):
            return env.get(t, t)
        elif isinstance(t, Constant):
            return t
        elif isinstance(t, FunctionApp):
            new_args = tuple(_canonicalize_term(arg, env) for arg in t.args)
            return FunctionApp(func=t.func, arity=t.arity, args=new_args, return_sort=t.return_sort)
        return t

    def _canonicalize_formula(f: Formula, env: Dict[Variable, Variable]) -> Formula:
        if isinstance(f, PredicateApp):
            new_args = tuple(_canonicalize_term(arg, env) for arg in f.args)
            return PredicateApp(pred=f.pred, arity=f.arity, args=new_args)
        elif isinstance(f, Equality):
            return Equality(left=_canonicalize_term(f.left, env), right=_canonicalize_term(f.right, env))
        elif isinstance(f, Not):
            return Not(operand=_canonicalize_formula(f.operand, env))
        elif isinstance(f, And):
            return And(left=_canonicalize_formula(f.left, env), right=_canonicalize_formula(f.right, env))
        elif isinstance(f, Or):
            return Or(left=_canonicalize_formula(f.left, env), right=_canonicalize_formula(f.right, env))
        elif isinstance(f, Implies):
            return Implies(left=_canonicalize_formula(f.left, env), right=_canonicalize_formula(f.right, env))
        elif isinstance(f, Iff):
            return Iff(left=_canonicalize_formula(f.left, env), right=_canonicalize_formula(f.right, env))
        elif isinstance(f, Forall):
            new_id = gen.get_next()
            canon_var = Variable(id=new_id, sort=f.variable.sort, kind=f.variable.kind)
            new_env = dict(env)
            new_env[f.variable] = canon_var
            return Forall(variable=canon_var, body=_canonicalize_formula(f.body, new_env))
        elif isinstance(f, Exists):
            new_id = gen.get_next()
            canon_var = Variable(id=new_id, sort=f.variable.sort, kind=f.variable.kind)
            new_env = dict(env)
            new_env[f.variable] = canon_var
            return Exists(variable=canon_var, body=_canonicalize_formula(f.body, new_env))
        elif type(f).__name__ in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
            new_body = _canonicalize_formula(getattr(f, "body"), env)
            return type(f)(variable=getattr(f, "variable"), body=new_body)
        else:
            raise InvalidFormulaError(f"Unsupported Formula node: {type(f)}")

    return _canonicalize_formula(formula, {})
