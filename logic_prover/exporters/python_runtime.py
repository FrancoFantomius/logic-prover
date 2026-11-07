"""Runtime support primitives and type mapping for Python code generated from Curry-Howard proofs.

Provides tagged union wrappers Left and Right for intuitionistic disjunction,
primitive recursion helpers for Heyting arithmetic, and type translators mapping
ProofType AST nodes to Python typing annotations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, Callable, Tuple, Union, NoReturn

from logic_prover.constructive.terms import (
    ProofType, AtomType, ArrowType, ProdType, SumType, UnitType, VoidType,
    ForallType, ExistsType, EqType
)

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class Left(Generic[T]):
    """Tagged union wrapper representing the left alternative of a disjunction (A | B).

    Args:
        value (T): The value associated with the left alternative.

    Example:
        >>> from logic_prover.exporters.python_runtime import Left
        >>> l = Left(42)
        >>> l.value
        42
    """

    value: T

    def __repr__(self) -> str:
        """Returns string representation of Left."""
        return f"Left({self.value!r})"


@dataclass(frozen=True)
class Right(Generic[U]):
    """Tagged union wrapper representing the right alternative of a disjunction (A | B).

    Args:
        value (U): The value associated with the right alternative.

    Example:
        >>> from logic_prover.exporters.python_runtime import Right
        >>> r = Right("hello")
        >>> r.value
        'hello'
    """

    value: U

    def __repr__(self) -> str:
        """Returns string representation of Right."""
        return f"Right({self.value!r})"


def nat_rec(zero_val: Any, step_fn: Callable[[int, Any], Any], n: int) -> Any:
    """Executes primitive recursion over natural numbers: f(0) = zero_val; f(n+1) = step_fn(n, f(n)).

    Args:
        zero_val (Any): Base case value for 0.
        step_fn (Callable[[int, Any], Any]): Step function taking predecessor index k and accumulator acc.
        n (int): Target natural number iteration count.

    Returns:
        Any: Result of the primitive recursion.

    Raises:
        ValueError: If n is negative.

    Example:
        >>> from logic_prover.exporters.python_runtime import nat_rec
        >>> # Factorial: f(0) = 1; f(n+1) = (n+1) * f(n)
        >>> nat_rec(1, lambda k, acc: (k + 1) * acc, 5)
        120
    """
    if n < 0:
        raise ValueError(f"Natural number argument must be non-negative, got {n}")
    acc = zero_val
    for k in range(n):
        acc = step_fn(k, acc)
    return acc


def _abort() -> NoReturn:
    """Raises a RuntimeError representing an unreachable branch under ex falso quodlibet.

    Returns:
        NoReturn: Always raises RuntimeError.

    Raises:
        RuntimeError: Always raised when executed.

    Example:
        >>> from logic_prover.exporters.python_runtime import _abort
        >>> try:
        ...     _abort()
        ... except RuntimeError as e:
        ...     "unreachable" in str(e).lower()
        True
    """
    raise RuntimeError("Unreachable: ex falso quodlibet branch executed.")


def type_to_python_annotation(typ: ProofType) -> str:
    """Translates a Curry-Howard ProofType into a valid Python typing annotation string.

    Args:
        typ (ProofType): The constructive proof type to translate.

    Returns:
        str: Python typing annotation expression (e.g. 'Callable[[int], int]', 'Tuple[Any, Any]').

    Example:
        >>> from logic_prover.constructive.terms import AtomType, ArrowType
        >>> from logic_prover.exporters.python_runtime import type_to_python_annotation
        >>> t = ArrowType(AtomType("int"), AtomType("int"))
        >>> type_to_python_annotation(t)
        'Callable[[int], int]'
    """
    if isinstance(typ, AtomType):
        name = typ.name.strip()
        if name in ("Nat", "nat", "int", "integer"):
            return "int"
        elif name in ("Bool", "bool", "boolean"):
            return "bool"
        elif name in ("str", "string"):
            return "str"
        return "Any"
    elif isinstance(typ, ArrowType):
        left_ann = type_to_python_annotation(typ.left)
        right_ann = type_to_python_annotation(typ.right)
        return f"Callable[[{left_ann}], {right_ann}]"
    elif isinstance(typ, ProdType):
        left_ann = type_to_python_annotation(typ.left)
        right_ann = type_to_python_annotation(typ.right)
        return f"Tuple[{left_ann}, {right_ann}]"
    elif isinstance(typ, SumType):
        left_ann = type_to_python_annotation(typ.left)
        right_ann = type_to_python_annotation(typ.right)
        return f"Union[Left[{left_ann}], Right[{right_ann}]]"
    elif isinstance(typ, UnitType):
        return "None"
    elif isinstance(typ, VoidType):
        return "NoReturn"
    elif isinstance(typ, ForallType):
        body_ann = type_to_python_annotation(typ.body)
        return f"Callable[[Any], {body_ann}]"
    elif isinstance(typ, ExistsType):
        body_ann = type_to_python_annotation(typ.body)
        return f"Tuple[Any, {body_ann}]"
    elif isinstance(typ, EqType):
        return "Any"
    return "Any"


__all__ = [
    "Left",
    "Right",
    "nat_rec",
    "_abort",
    "type_to_python_annotation",
]
