"""Unified constructive resolution theorem prover supporting prefixed and relational translation methods."""

from __future__ import annotations
from typing import List, Optional, Sequence, Union

from logic_prover.core.ast import Formula
from logic_prover.constructive.resolution.clauses import (
    PrefixedResolutionProofResult,
)
from logic_prover.constructive.resolution.prefixed import (
    PrefixedResolutionProver,
)
from logic_prover.constructive.resolution.translation import (
    TranslationResolutionResult,
    TranslationResolutionProver,
)


class ConstructiveResolutionProver:
    """Unified resolution theorem prover supporting both Prefixed and Translation methods for IPC.

    Args:
        method (str, default='prefixed'): Proof search strategy ('prefixed', 'translation', or 'auto').
        max_multiplicity (int, default=3): Multiplicity bound for prefixed resolution.
        max_steps (int, default=1000): Maximum search iterations.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.prover import ConstructiveResolutionProver
        >>> p = PredicateApp("P", 0, ())
        >>> prover = ConstructiveResolutionProver(method="prefixed")
        >>> res = prover.prove(Implies(p, p))
        >>> res is not None and res.is_valid
        True
    """

    method: str
    max_multiplicity: int
    max_steps: int
    timeout_sec: float

    def __init__(
        self,
        method: str = "prefixed",
        max_multiplicity: int = 3,
        max_steps: int = 1000,
        timeout_sec: float = 10.0,
    ) -> None:
        """Initializes the unified constructive resolution prover.

        Args:
            method (str, default='prefixed'): Resolution method ('prefixed', 'translation', 'auto').
            max_multiplicity (int, default=3): Multiplicity limit for prefixed resolution.
            max_steps (int, default=1000): Maximum resolution steps limit.
            timeout_sec (float, default=10.0): Wall-clock timeout limit in seconds.

        Example:
            >>> from logic_prover.constructive.resolution.prover import ConstructiveResolutionProver
            >>> prover = ConstructiveResolutionProver(method="auto")
            >>> prover.method
            'auto'
        """
        self.method = method.lower()
        self.max_multiplicity = max(1, max_multiplicity)
        self.max_steps = max(1, max_steps)
        self.timeout_sec = max(0.1, timeout_sec)

    def prove(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]:
        """Attempts to prove an IPC formula using the configured resolution strategy.

        Args:
            target (Formula): Formula AST to prove.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis premises.

        Returns:
            Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]:
                Proof result if valid, None otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution.prover import ConstructiveResolutionProver
            >>> p = PredicateApp("P", 0, ())
            >>> prover = ConstructiveResolutionProver()
            >>> res = prover.prove(Implies(p, p))
            >>> res is not None and res.is_valid
            True
        """
        if self.method == "prefixed":
            p_prover = PrefixedResolutionProver(
                max_multiplicity=self.max_multiplicity,
                max_steps=self.max_steps,
            )
            return p_prover.prove(target=target, premises=premises)

        elif self.method == "translation":
            t_prover = TranslationResolutionProver(
                max_steps=self.max_steps,
                timeout_sec=self.timeout_sec,
            )
            return t_prover.prove(target=target, premises=premises)

        elif self.method == "auto":
            # Try prefixed resolution first
            p_prover = PrefixedResolutionProver(
                max_multiplicity=self.max_multiplicity,
                max_steps=self.max_steps,
            )
            p_res = p_prover.prove(target=target, premises=premises)
            if p_res is not None:
                return p_res

            # Fall back to translation resolution
            t_prover = TranslationResolutionProver(
                max_steps=self.max_steps,
                timeout_sec=self.timeout_sec,
            )
            return t_prover.prove(target=target, premises=premises)

        else:
            raise ValueError(f"Unknown constructive resolution method: {self.method}")


def prove_resolution(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    method: str = "prefixed",
    max_multiplicity: int = 3,
    max_steps: int = 1000,
    timeout_sec: float = 10.0,
) -> Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]:
    """Proves an intuitionistic propositional formula using resolution (prefixed or translation).

    Args:
        formula (Formula): Formula AST to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis premises.
        method (str, default='prefixed'): Resolution method ('prefixed', 'translation', 'auto').
        max_multiplicity (int, default=3): Maximum multiplicity limit for prefixed resolution.
        max_steps (int, default=1000): Maximum search iterations.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Returns:
        Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]:
            Proof result if valid, None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.prover import prove_resolution
        >>> p = PredicateApp("P", 0, ())
        >>> proof = prove_resolution(Implies(p, p), method="prefixed")
        >>> proof is not None and proof.is_valid
        True
    """
    prover = ConstructiveResolutionProver(
        method=method,
        max_multiplicity=max_multiplicity,
        max_steps=max_steps,
        timeout_sec=timeout_sec,
    )
    return prover.prove(target=formula, premises=premises)


__all__ = [
    "ConstructiveResolutionProver",
    "prove_resolution",
]
