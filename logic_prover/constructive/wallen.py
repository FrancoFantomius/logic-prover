"""Lincoln Wallen's Matrix and Connection Method for Intuitionistic Propositional Logic (IPC).

This module implements Wallen's prefix-based matrix characterization and connection
method for intuitionistic propositional logic (Wallen 1990; Otten & Kreitz 1996).
Formulas are decomposed into signed formula trees with Kripke world prefixes,
and theoremhood is established via path-spanning matings with admissible T-string
prefix unification.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any

from logic_prover.core.ast import Formula
from logic_prover.core.parser import to_string
from logic_prover.constructive.common import (
    FALSUM,
    _is_falsum,
    normalize_formula,
)
from logic_prover.constructive.prefix import (
    PrefixSymbol,
    PrefixConstant,
    PrefixVariable,
    Prefix,
    PrefixSubstitution,
    unify_prefixes,
    is_admissible,
)
from logic_prover.constructive.matrix import (
    PositionType,
    Position,
    FormulaTree,
    Connection,
)


@dataclass
class WallenProofResult:
    """Container for Wallen matrix proof derivation results.

    Args:
        is_valid (bool): Whether the formula is intuitionistically valid.
        tree (FormulaTree): The formula decomposition tree.
        connections (Tuple[Connection, ...]): Spanning mating of connections.
        substitution (PrefixSubstitution): Admissible unifying prefix substitution.
        multiplicity (int): Multiplicity level at which proof was found.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.matrix import FormulaTree
        >>> from logic_prover.constructive.prefix import PrefixSubstitution
        >>> from logic_prover.constructive.wallen import WallenProofResult
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> tree = FormulaTree(target=Implies(p, p))
        >>> res = WallenProofResult(True, tree, (), PrefixSubstitution(), 1)
        >>> res.is_valid
        True
    """

    is_valid: bool
    tree: FormulaTree
    connections: Tuple[Connection, ...]
    substitution: PrefixSubstitution
    multiplicity: int

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the proof result to a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: Dictionary structure of the proof.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.matrix import FormulaTree
            >>> from logic_prover.constructive.prefix import PrefixSubstitution
            >>> from logic_prover.constructive.wallen import WallenProofResult
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> tree = FormulaTree(target=Implies(p, p))
            >>> res = WallenProofResult(True, tree, (), PrefixSubstitution(), 1)
            >>> res.to_dict()["is_valid"]
            True
        """
        return {
            "is_valid": self.is_valid,
            "target": to_string(self.tree.target),
            "premises": [to_string(p) for p in self.tree.premises],
            "multiplicity": self.multiplicity,
            "connections": [c.to_string() for c in self.connections],
            "substitution": self.substitution.to_dict(),
        }

    def to_string(self) -> str:
        """Formats the proof result as a multi-line report.

        Returns:
            str: Multi-line proof summary.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.matrix import FormulaTree
            >>> from logic_prover.constructive.prefix import PrefixSubstitution
            >>> from logic_prover.constructive.wallen import WallenProofResult
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> tree = FormulaTree(target=Implies(p, p))
            >>> res = WallenProofResult(True, tree, (), PrefixSubstitution(), 1)
            >>> "VALID" in res.to_string()
            True
        """
        lines: List[str] = []
        lines.append("=== Wallen Matrix Proof (IPC) ===")
        lines.append(f"Target: {to_string(self.tree.target)}")
        if self.tree.premises:
            lines.append(f"Premises: {', '.join(to_string(p) for p in self.tree.premises)}")
        lines.append(f"Status: {'VALID (Intuitionistically Proven)' if self.is_valid else 'UNPROVABLE'}")
        lines.append(f"Multiplicity: {self.multiplicity}")
        if self.connections:
            lines.append("Spanning Connections:")
            for i, c in enumerate(self.connections, 1):
                lines.append(f"  [{i}] {c.to_string()}")
        if self.substitution.mapping:
            lines.append("Prefix Substitution:")
            for k, v in self.substitution.mapping.items():
                lines.append(f"  sigma({k.name}) = {'.'.join(s.name for s in v)}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Returns the default string representation."""
        return self.to_string()


class WallenProver:
    """Matrix / Connection Proof Searcher for Intuitionistic Propositional Logic.

    Args:
        max_multiplicity (int, default=3): Maximum multiplicity bound for phi-node duplications.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.wallen import WallenProver
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> prover = WallenProver()
        >>> res = prover.prove(Implies(p, p))
        >>> res is not None and res.is_valid
        True
    """

    max_multiplicity: int

    def __init__(self, max_multiplicity: int = 3) -> None:
        """Initializes the Wallen prover with maximum multiplicity limit.

        Args:
            max_multiplicity (int, default=3): Maximum multiplicity bound for phi-node duplications.

        Example:
            >>> from logic_prover.constructive.wallen import WallenProver
            >>> prover = WallenProver(max_multiplicity=4)
            >>> prover.max_multiplicity
            4
        """
        self.max_multiplicity = max(1, max_multiplicity)

    def _find_connections_in_path(self, path: List[Position]) -> List[Connection]:
        """Finds all candidate complementary connections in a single matrix path.

        Args:
            path (List[Position]): List of atomic leaf positions in a path.

        Returns:
            List[Connection]: All complementary connections in this path.
        """
        connections: List[Connection] = []
        for i, p1 in enumerate(path):
            if _is_falsum(p1.formula) and p1.polarity == 1:
                dummy_falsum = Position(
                    id=0,
                    formula=FALSUM,
                    polarity=0,
                    pos_type=PositionType.ATOM,
                    prefix=p1.prefix,
                )
                connections.append(Connection(positive=p1, negative=dummy_falsum))

            for j in range(i + 1, len(path)):
                p2 = path[j]
                if p1.formula == p2.formula and p1.polarity != p2.polarity:
                    pos = p1 if p1.polarity == 1 else p2
                    neg = p2 if p1.polarity == 1 else p1
                    connections.append(Connection(positive=pos, negative=neg))
        return connections

    def prove(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
    ) -> Optional[WallenProofResult]:
        """Attempts to prove a formula in Intuitionistic Propositional Logic using Wallen's method.

        Args:
            target (Formula): Formula AST to prove.
            premises (Optional[List[Formula]], default=None): Optional list of hypothesis formulas.

        Returns:
            Optional[WallenProofResult]: Proof result if valid, None if not provable within bounds.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.wallen import WallenProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = WallenProver()
            >>> res = prover.prove(target=Implies(p, p))
            >>> res is not None
            True
        """
        norm_target = normalize_formula(target)
        norm_premises = [normalize_formula(p) for p in (premises or [])]

        for mult in range(1, self.max_multiplicity + 1):
            tree = FormulaTree(target=norm_target, premises=norm_premises, multiplicity=mult)
            paths = tree.get_paths()

            if not paths:
                continue

            mating = self._search_mating(
                tree=tree,
                remaining_paths=paths,
                current_connections=[],
                current_subst=PrefixSubstitution(),
            )

            if mating is not None:
                spanning_conns, final_subst = mating
                return WallenProofResult(
                    is_valid=True,
                    tree=tree,
                    connections=tuple(spanning_conns),
                    substitution=final_subst,
                    multiplicity=mult,
                )

        return None

    def _search_mating(
        self,
        tree: FormulaTree,
        remaining_paths: List[List[Position]],
        current_connections: List[Connection],
        current_subst: PrefixSubstitution,
    ) -> Optional[Tuple[List[Connection], PrefixSubstitution]]:
        """Backtracking search for a path-spanning mating with an admissible unifier.

        Args:
            tree (FormulaTree): Decomposition tree.
            remaining_paths (List[List[Position]]): Unclosed paths.
            current_connections (List[Connection]): Chosen connections so far.
            current_subst (PrefixSubstitution): Accumulated prefix substitution.

        Returns:
            Optional[Tuple[List[Connection], PrefixSubstitution]]: Spanning mating and substitution.
        """
        unclosed: List[List[Position]] = []
        for p in remaining_paths:
            closed = False
            for conn in current_connections:
                if conn.positive in p and conn.negative in p:
                    closed = True
                    break
            if not closed:
                unclosed.append(p)

        if not unclosed:
            if is_admissible(tree, current_subst):
                return current_connections, current_subst
            return None

        unclosed.sort(key=lambda p: len(self._find_connections_in_path(p)))
        path = unclosed[0]
        rest_paths = unclosed[1:]

        candidates = self._find_connections_in_path(path)
        if not candidates:
            return None

        for conn in candidates:
            unifs = unify_prefixes(conn.positive.prefix, conn.negative.prefix, current_subst)
            for unif in unifs:
                if is_admissible(tree, unif):
                    res = self._search_mating(
                        tree=tree,
                        remaining_paths=rest_paths,
                        current_connections=current_connections + [conn],
                        current_subst=unif,
                    )
                    if res is not None:
                        return res

        return None


def prove_wallen(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_multiplicity: int = 3,
) -> Optional[WallenProofResult]:
    """Proves an intuitionistic propositional formula using Wallen's matrix method.

    Args:
        formula (Formula): The formula to prove.
        premises (Optional[List[Formula]], default=None): Optional list of hypothesis premises.
        max_multiplicity (int, default=3): Maximum multiplicity for phi-node duplications.

    Returns:
        Optional[WallenProofResult]: Derivation proof result if valid, None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.wallen import prove_wallen
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> proof = prove_wallen(Implies(left=p, right=p))
        >>> proof is not None and proof.is_valid
        True
    """
    prover = WallenProver(max_multiplicity=max_multiplicity)
    return prover.prove(target=formula, premises=premises)


__all__ = [
    # Re-exported prefix symbols
    "PrefixSymbol",
    "PrefixConstant",
    "PrefixVariable",
    "Prefix",
    "PrefixSubstitution",
    "unify_prefixes",
    "is_admissible",
    # Re-exported matrix symbols
    "PositionType",
    "Position",
    "FormulaTree",
    "Connection",
    # Wallen prover symbols
    "WallenProofResult",
    "WallenProver",
    "prove_wallen",
]
