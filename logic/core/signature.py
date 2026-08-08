"""Logical signature definition module for declaring function, predicate, and constant symbols."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Set

from logic.core.exceptions import ValidationError
from logic.core.sorts import Sort, Ind


@dataclass(frozen=True)
class FunctionDecl:
    """Declaration of a function symbol in a logical signature.

    Attributes:
        name: Unique string name of the function.
        arity: Number of arguments expected (>= 0).
        arg_sorts: Tuple of expected argument sorts.
        return_sort: Sort of the returned term (defaults to Ind).
    """

    name: str
    arity: int
    arg_sorts: Tuple[Sort, ...]
    return_sort: Sort = Ind

    def __post_init__(self) -> None:
        if self.arity < 0:
            raise ValueError(f"Function arity cannot be negative: {self.arity}")
        if len(self.arg_sorts) != self.arity:
            raise ValueError(
                f"Function '{self.name}' arity {self.arity} does not match arg_sorts length {len(self.arg_sorts)}"
            )


@dataclass(frozen=True)
class PredicateDecl:
    """Declaration of a predicate symbol in a logical signature."""

    name: str
    arity: int
    arg_sorts: Tuple[Sort, ...]

    def __post_init__(self) -> None:
        if self.arity < 0:
            raise ValueError(f"Predicate arity cannot be negative: {self.arity}")
        if len(self.arg_sorts) != self.arity:
            raise ValueError(
                f"Predicate '{self.name}' arity {self.arity} does not match arg_sorts length {len(self.arg_sorts)}"
            )


class Signature:
    """Declares available functions, predicates, constants, and sort constructors in a logical context."""

    def __init__(
        self,
        functions: Optional[Dict[str, FunctionDecl]] = None,
        predicates: Optional[Dict[str, PredicateDecl]] = None,
        constants: Optional[Dict[str, Sort]] = None,
        sort_constructors: Optional[Dict[str, int]] = None,
    ) -> None:
        """Initializes a new Signature instance with optional predefined declarations."""
        self.functions: Dict[str, FunctionDecl] = dict(functions) if functions else {}
        self.predicates: Dict[str, PredicateDecl] = dict(predicates) if predicates else {}
        self.constants: Dict[str, Sort] = dict(constants) if constants else {}
        self.sort_constructors: Dict[str, int] = dict(sort_constructors) if sort_constructors else {}

    def register_function(
        self,
        name: str,
        arity: int,
        arg_sorts: Tuple[Sort, ...],
        return_sort: Sort = Ind,
    ) -> None:
        """Register a function symbol in the signature.

        Raises:
            ValidationError: If symbol name collides with another predicate/constant or incompatible function decl.
        """
        if name in self.predicates or name in self.constants:
            raise ValidationError(f"Symbol '{name}' is already declared as a predicate or constant.")

        new_decl = FunctionDecl(name=name, arity=arity, arg_sorts=arg_sorts, return_sort=return_sort)
        if name in self.functions:
            existing = self.functions[name]
            if existing != new_decl:
                raise ValidationError(
                    f"Symbol '{name}' already registered as function with different declaration: "
                    f"{existing} vs {new_decl}"
                )
            return

        self.functions[name] = new_decl

    def register_predicate(
        self,
        name: str,
        arity: int,
        arg_sorts: Tuple[Sort, ...],
    ) -> None:
        """Register a predicate symbol in the signature.

        Raises:
            ValidationError: If symbol name collides with another function/constant or incompatible predicate decl.
        """
        if name in self.functions or name in self.constants:
            raise ValidationError(f"Symbol '{name}' is already declared as a function or constant.")

        new_decl = PredicateDecl(name=name, arity=arity, arg_sorts=arg_sorts)
        if name in self.predicates:
            existing = self.predicates[name]
            if existing != new_decl:
                raise ValidationError(
                    f"Symbol '{name}' already registered as predicate with different declaration: "
                    f"{existing} vs {new_decl}"
                )
            return

        self.predicates[name] = new_decl

    def register_constant(self, name: str, sort: Sort = Ind) -> None:
        """Register a constant symbol in the signature.

        Raises:
            ValidationError: If symbol name collides with a function/predicate or incompatible constant declaration.
        """
        if name in self.functions or name in self.predicates:
            raise ValidationError(f"Symbol '{name}' is already declared as a function or predicate.")

        if name in self.constants:
            existing_sort = self.constants[name]
            if existing_sort != sort:
                raise ValidationError(
                    f"Symbol '{name}' already registered as constant with different sort: "
                    f"{existing_sort} vs {sort}"
                )
            return

        self.constants[name] = sort

    def register_sort_constructor(self, name: str, arity: int) -> None:
        """Register a parameterized sort constructor (e.g. Set -> 1, Pair -> 2)."""
        if arity < 0:
            raise ValueError(f"Sort constructor arity cannot be negative: {arity}")
        if name in self.sort_constructors:
            existing_arity = self.sort_constructors[name]
            if existing_arity != arity:
                raise ValidationError(
                    f"Sort constructor '{name}' already registered with arity {existing_arity}, got {arity}"
                )
            return

        self.sort_constructors[name] = arity

    def lookup_function(self, name: str) -> Optional[FunctionDecl]:
        """Retrieve function declaration by name."""
        return self.functions.get(name)

    def lookup_predicate(self, name: str) -> Optional[PredicateDecl]:
        """Retrieve predicate declaration by name."""
        return self.predicates.get(name)

    def lookup_constant(self, name: str) -> Optional[Sort]:
        """Retrieve constant sort by name."""
        return self.constants.get(name)

    def lookup_sort_constructor(self, name: str) -> Optional[int]:
        """Retrieve sort constructor arity by name."""
        return self.sort_constructors.get(name)

    def has_symbol(self, name: str) -> bool:
        """Check if symbol name is declared as constant, function, or predicate."""
        return (name in self.functions) or (name in self.predicates) or (name in self.constants)

    def merge(self, other: Signature) -> Signature:
        """Merge two signatures into a new combined Signature.

        Raises:
            ValidationError: If there is a declaration conflict between the two signatures.
        """
        new_sig = self.clone()
        for func_decl in other.functions.values():
            new_sig.register_function(
                func_decl.name, func_decl.arity, func_decl.arg_sorts, func_decl.return_sort
            )
        for pred_decl in other.predicates.values():
            new_sig.register_predicate(pred_decl.name, pred_decl.arity, pred_decl.arg_sorts)
        for const_name, const_sort in other.constants.items():
            new_sig.register_constant(const_name, const_sort)
        for constructor_name, constructor_arity in other.sort_constructors.items():
            new_sig.register_sort_constructor(constructor_name, constructor_arity)
        return new_sig

    def clone(self) -> Signature:
        """Create a deep copy of the signature."""
        return Signature(
            functions=dict(self.functions),
            predicates=dict(self.predicates),
            constants=dict(self.constants),
            sort_constructors=dict(self.sort_constructors),
        )

    @classmethod
    def empty(cls) -> Signature:
        """Create an empty signature instance."""
        return cls()
