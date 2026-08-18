"""Foundational Theory abstraction and global theory registry."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from logic_prover.core.ast import Formula
from logic_prover.core.signature import Signature
from logic_prover.core.sorts import Sort
from logic_prover.core.validator import validate_formula, ValidationError
from logic_prover.config import SolverConfig

if TYPE_CHECKING:
    from logic_prover.prover.engine import TheoremProver
    from logic_prover.prover.proof import ProofDAG


@dataclass
class Theory:
    """Represents a formal mathematical theory consisting of sorts, a signature, and a set of axioms.

    Attributes:
        name (str): The unique canonical name of the mathematical theory.
        description (str): Human-readable summary of the theory and its domain.
        sorts (Dict[str, Sort]): Dictionary mapping sort names to their Sort instances.
        signature (Signature): The logical signature containing function, predicate, and constant declarations.
        axioms (Dict[str, Formula]): Dictionary mapping axiom identifiers to their Formula AST representations.
    """

    name: str
    description: str
    sorts: Dict[str, Sort] = field(default_factory=dict)
    signature: Signature = field(default_factory=Signature)
    axioms: Dict[str, Formula] = field(default_factory=dict)

    def get_signature(self) -> Signature:
        """Retrieves the logical signature of this theory.

        Returns:
            Signature: The theory's logical signature.

        Example:
            >>> theory = Theory(name="sample", description="sample theory")
            >>> isinstance(theory.get_signature(), Signature)
            True
        """
        return self.signature

    def get_axioms(self) -> List[Tuple[str, Formula]]:
        """Retrieves all axioms of this theory as a list of (name, formula) pairs.

        Returns:
            List[Tuple[str, Formula]]: List containing (axiom_name, axiom_formula) tuples.

        Example:
            >>> theory = Theory(name="sample", description="sample theory")
            >>> theory.get_axioms()
            []
        """
        return list(self.axioms.items())

    def get_axioms_list(self) -> List[Formula]:
        """Retrieves the list of axiom formulas without their names, suitable as prover premises.

        Returns:
            List[Formula]: The list of Formula instances corresponding to all axioms in the theory.

        Example:
            >>> theory = Theory(name="sample", description="sample theory")
            >>> theory.get_axioms_list()
            []
        """
        return list(self.axioms.values())

    def get_axiom(self, name: str) -> Optional[Formula]:
        """Retrieves a specific axiom formula by its registered name.

        Args:
            name (str): The name identifier of the axiom to retrieve.

        Returns:
            Optional[Formula]: The Formula instance if found, None otherwise.

        Example:
            >>> theory = Theory(name="sample", description="sample theory")
            >>> theory.get_axiom("nonexistent") is None
            True
        """
        return self.axioms.get(name)

    def validate(self) -> List[ValidationError]:
        """Validates all axioms in this theory against the theory's signature.

        Returns:
            List[ValidationError]: A list of validation errors found across all axioms (empty if valid).

        Example:
            >>> theory = Theory(name="sample", description="sample theory")
            >>> theory.validate()
            []
        """
        errors: List[ValidationError] = []
        for ax_name, ax_formula in self.axioms.items():
            ax_errors = validate_formula(ax_formula, self.signature)
            for err in ax_errors:
                errors.append(ValidationError(f"[{self.name}:{ax_name}] {err.message}"))
        return errors

    def create_prover(self, config: Optional[SolverConfig] = None) -> TheoremProver:
        """Instantiates a TheoremProver configured with this theory's logical signature.

        Args:
            config (Optional[SolverConfig], optional): Optional solver limits and configuration. Defaults to None.

        Returns:
            TheoremProver: A TheoremProver instance ready for proof search over this theory.

        Example:
            >>> theory = Theory(name="sample", description="sample theory")
            >>> prover = theory.create_prover()
            >>> prover.signature == theory.signature
            True
        """
        from logic_prover.prover.engine import TheoremProver
        return TheoremProver(signature=self.signature, config=config)

    def prove(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
        include_theory_axioms: bool = True,
        max_steps: Optional[int] = None,
        timeout_sec: Optional[float] = None,
    ) -> ProofDAG:
        """Attempts to prove a target formula within this theory, combining optional premises and theory axioms.

        Args:
            target (Formula): The target goal formula to prove.
            premises (Optional[List[Formula]], optional): Additional user-provided premise formulas. Defaults to None.
            include_theory_axioms (bool, optional): Whether to automatically prepend all theory axioms as premises. Defaults to True.
            max_steps (Optional[int], optional): Maximum resolution steps allowed. Defaults to None.
            timeout_sec (Optional[float], optional): Timeout limit in seconds. Defaults to None.

        Returns:
            ProofDAG: A reconstructed natural deduction proof DAG of the target formula.

        Example:
            >>> from logic_prover.core.ast import Variable, Equality, Forall
            >>> from logic_prover.core.sorts import Ind
            >>> v = Variable(0, sort=Ind)
            >>> goal = Forall(v, Equality(v, v))
            >>> theory = Theory(name="sample", description="sample theory")
            >>> proof = theory.prove(target=goal, timeout_sec=2.0)
            >>> proof.is_valid()
            True
        """
        all_premises: List[Formula] = []
        if include_theory_axioms:
            all_premises.extend(self.get_axioms_list())
        if premises:
            all_premises.extend(premises)

        prover = self.create_prover()
        return prover.prove(
            target=target,
            premises=all_premises,
            max_steps=max_steps,
            timeout_sec=timeout_sec,
        )


_THEORY_REGISTRY: Dict[str, Theory] = {}


def register_theory(theory: Theory) -> None:
    """Registers a Theory instance into the global theory registry.

    Args:
        theory (Theory): The Theory object to register.

    Returns:
        None: Does not return a value.

    Example:
        >>> th = Theory(name="dummy_theory", description="A test theory")
        >>> register_theory(th)
        >>> get_theory("dummy_theory").name
        'dummy_theory'
    """
    _THEORY_REGISTRY[theory.name] = theory


def get_theory(name: str) -> Optional[Theory]:
    """Retrieves a registered Theory by its name.

    Args:
        name (str): The name identifier of the theory.

    Returns:
        Optional[Theory]: The registered Theory instance if found, None otherwise.

    Example:
        >>> th = Theory(name="sample_get", description="test get")
        >>> register_theory(th)
        >>> get_theory("sample_get") is not None
        True
        >>> get_theory("nonexistent_theory_xyz") is None
        True
    """
    return _THEORY_REGISTRY.get(name)


def list_theories() -> List[str]:
    """Returns a sorted list of all registered theory names.

    Returns:
        List[str]: List of string names for all registered theories.

    Example:
        >>> theories = list_theories()
        >>> isinstance(theories, list)
        True
    """
    return sorted(list(_THEORY_REGISTRY.keys()))


def get_all_theories() -> Dict[str, Theory]:
    """Returns a copy of the dictionary containing all registered theories.

    Returns:
        Dict[str, Theory]: Mapping of theory names to their Theory instances.

    Example:
        >>> all_th = get_all_theories()
        >>> isinstance(all_th, dict)
        True
    """
    return dict(_THEORY_REGISTRY)
