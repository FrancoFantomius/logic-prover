"""Custom exception hierarchy for the logic library."""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from logic.core.sorts import Sort


class SolverError(Exception):
    """Base exception for all errors raised by the logic library."""

    def __init__(self, message: str) -> None:
        """Initializes a SolverError exception instance."""
        super().__init__(message)
        self.message = message


class ParseError(SolverError):
    """Raised when parsing formula or term text fails due to syntax or token errors."""

    pass


class UnificationError(SolverError):
    """Raised when term or formula unification fails."""

    pass


class SortMismatchError(UnificationError):
    """Raised when terms or expressions of incompatible sorts are combined or unified."""

    def __init__(
        self,
        message: str,
        expected_sort: Optional[Sort] = None,
        actual_sort: Optional[Sort] = None,
    ) -> None:
        """Initializes a SortMismatchError exception instance."""
        super().__init__(message)
        self.expected_sort = expected_sort
        self.actual_sort = actual_sort


class ProofTimeoutError(SolverError):
    """Raised when automated proof search exceeds the allocated time limit."""

    pass


class ProofSearchExhaustedError(SolverError):
    """Raised when proof search completes without finding a proof or refutation."""

    pass


class InvalidFormulaError(SolverError):
    """Raised when constructing an ill-formed AST node (e.g. arity mismatch, invalid ID)."""

    pass


class ValidationError(SolverError):
    """Raised when AST validation checks fail (e.g., sort mismatch, unbound index)."""

    pass


class DatabaseError(SolverError):
    """Raised when persistence operations (SQLite I/O, schema errors, serialization) fail."""

    pass


class RewriteDivergenceError(SolverError):
    """Raised when formula normalization fails to reach a fixed point within max_steps."""

    pass
