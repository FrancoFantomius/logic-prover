"""Sort system hierarchy for primitive, parameterized, and function sorts."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, TYPE_CHECKING

from solver.core.exceptions import InvalidFormulaError

if TYPE_CHECKING:
    from solver.core.ast import Term


@dataclass(frozen=True)
class Sort(ABC):
    """Abstract Base Class for logical sorts."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the canonical string representation of the sort."""
        pass

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class PrimitiveSort(Sort):
    """Represents an atomic sort (e.g. Ind, Nat, Bool)."""

    sort_name: str

    def __post_init__(self) -> None:
        if not self.sort_name or not isinstance(self.sort_name, str):
            raise InvalidFormulaError("PrimitiveSort name must be a non-empty string.")

    @property
    def name(self) -> str:
        return self.sort_name


@dataclass(frozen=True)
class ParameterizedSort(Sort):
    """Represents a composite parameterized sort (e.g., Set(Nat), Pair(Nat, Bool))."""

    constructor: str
    args: Tuple[Sort, ...]

    def __post_init__(self) -> None:
        if not self.constructor or not isinstance(self.constructor, str):
            raise InvalidFormulaError("ParameterizedSort constructor cannot be empty.")
        if not self.args:
            raise InvalidFormulaError("ParameterizedSort must have at least one argument sort.")

    @property
    def name(self) -> str:
        args_str = ", ".join(arg.name for arg in self.args)
        return f"{self.constructor}({args_str})"


@dataclass(frozen=True)
class FunctionSort(Sort):
    """Represents a function sort (domain sorts -> codomain sort). Reserved for SOL extensions."""

    arg_sorts: Tuple[Sort, ...]
    return_sort: Sort

    @property
    def name(self) -> str:
        args_str = ", ".join(arg.name for arg in self.arg_sorts)
        return f"({args_str}) -> {self.return_sort.name}"


# Atomic primitive sorts
Ind: PrimitiveSort = PrimitiveSort("Ind")
Nat: PrimitiveSort = PrimitiveSort("Nat")
Bool: PrimitiveSort = PrimitiveSort("Bool")


# Helper constructors for parameterized sorts
def SetSort(element_sort: Sort) -> ParameterizedSort:
    """Helper constructing a Set parameterized sort for element_sort."""
    return ParameterizedSort("Set", (element_sort,))


def ListSort(element_sort: Sort) -> ParameterizedSort:
    """Helper constructing a List parameterized sort for element_sort."""
    return ParameterizedSort("List", (element_sort,))


def PairSort(sort_a: Sort, sort_b: Sort) -> ParameterizedSort:
    """Helper constructing a Pair parameterized sort for sort_a and sort_b."""
    return ParameterizedSort("Pair", (sort_a, sort_b))


def is_compatible(s1: Sort, s2: Sort) -> bool:
    """Determines if two sorts are compatible for unification and term assignment.

    Rules:
    1. Identity: If s1 == s2, returns True.
    2. Wildcard: Ind is compatible with all individual primitive and parameterized sorts.
    3. Primitive: Two PrimitiveSorts must match names or involve Ind.
    4. Parameterized: Same constructor, same arity, and recursively compatible arguments.
    5. FunctionSort: Same argument arity, recursively compatible argument sorts and return sorts.
    """
    if s1 == s2:
        return True

    # Generic individual sort wildcard rule
    if (s1 == Ind or s2 == Ind) and not isinstance(s1, FunctionSort) and not isinstance(s2, FunctionSort):
        return True

    if isinstance(s1, PrimitiveSort) and isinstance(s2, PrimitiveSort):
        return s1.sort_name == s2.sort_name

    if isinstance(s1, ParameterizedSort) and isinstance(s2, ParameterizedSort):
        if s1.constructor != s2.constructor or len(s1.args) != len(s2.args):
            return False
        return all(is_compatible(a1, a2) for a1, a2 in zip(s1.args, s2.args))

    if isinstance(s1, FunctionSort) and isinstance(s2, FunctionSort):
        if len(s1.arg_sorts) != len(s2.arg_sorts):
            return False
        if not is_compatible(s1.return_sort, s2.return_sort):
            return False
        return all(is_compatible(a1, a2) for a1, a2 in zip(s1.arg_sorts, s2.arg_sorts))

    return False


def sort_of_term(term: Term, context: Optional[Dict[str, Sort]] = None) -> Sort:
    """Infers the sort of a Term node.

    - Variable: term.sort
    - Constant: term.sort or lookup in context if context provided
    - FunctionApp: term.return_sort or lookup function return sort in context
    """
    from solver.core.ast import Variable, Constant, FunctionApp

    if isinstance(term, Variable):
        return term.sort
    elif isinstance(term, Constant):
        if context and term.name in context:
            return context[term.name]
        return term.sort
    elif isinstance(term, FunctionApp):
        if context and term.func in context:
            func_sort = context[term.func]
            if isinstance(func_sort, FunctionSort):
                return func_sort.return_sort
        return term.return_sort
    else:
        raise InvalidFormulaError(f"Cannot infer sort for unknown term type: {type(term)}")
