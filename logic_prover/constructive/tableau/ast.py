"""Abstract syntax, node structures, and proof trees for Semantic Tableaux in Intuitionistic Logic."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any

from logic_prover.core.ast import Formula
from logic_prover.core.parser import to_string
from logic_prover.constructive.common import _is_falsum, _is_verum
from logic_prover.constructive.kripke import World, KripkeModel


class Sign(str, Enum):
    """Truth sign in labelled semantic tableaux.

    T denotes assertion of truth / forcing at a world (w |= A).
    F denotes assertion of falsity / non-forcing at a world (w |/= A).
    """

    TRUE = "T"
    FALSE = "F"

    def __str__(self) -> str:
        """Returns the single-character string representation of the sign.

        Returns:
            str: 'T' or 'F'.

        Example:
            >>> from logic_prover.constructive.tableau.ast import Sign
            >>> str(Sign.TRUE)
            'T'
        """
        return self.value


@dataclass(frozen=True)
class SignedFormula:
    """A formula paired with a truth sign and world location in a Kripke frame.

    Args:
        sign (Sign): Truth assertion (Sign.TRUE or Sign.FALSE).
        formula (Formula): The formula AST.
        world (World): The Kripke world where the formula is signed.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.kripke import World
        >>> from logic_prover.constructive.tableau.ast import SignedFormula, Sign
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> sf = SignedFormula(sign=Sign.TRUE, formula=p, world=World(0, "w0"))
        >>> sf.to_string()
        'T(P, w0)'
    """

    sign: Sign
    formula: Formula
    world: World

    def to_string(self, notation: str = "infix") -> str:
        """Formats the signed formula as a human-readable string.

        Args:
            notation (str, default='infix'): String formatting notation ('infix' or 'latex').

        Returns:
            str: Formatted signed formula string.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau.ast import SignedFormula, Sign
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> sf = SignedFormula(sign=Sign.FALSE, formula=p, world=World(0, "w0"))
            >>> sf.to_string()
            'F(P, w0)'
        """
        f_str = "\\bot" if (_is_falsum(self.formula) and notation == "latex") else (
            "_bot" if _is_falsum(self.formula) else (
                "\\top" if (_is_verum(self.formula) and notation == "latex") else (
                    "_top" if _is_verum(self.formula) else to_string(self.formula, notation=notation)
                )
            )
        )
        return f"{self.sign.value}({f_str}, {self.world.name})"

    def __str__(self) -> str:
        """Returns the default infix string representation.

        Returns:
            str: Signed formula representation.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau.ast import SignedFormula, Sign
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> str(SignedFormula(Sign.TRUE, p, World(0, "w0")))
            'T(P, w0)'
        """
        return self.to_string(notation="infix")


@dataclass
class TableauNode:
    """A node in a semantic tableau derivation tree.

    Args:
        id (int): Unique node integer ID.
        signed_formula (Optional[SignedFormula], default=None): The signed formula introduced or decomposed.
        rule (str, default=''): The name of the tableau rule applied at this node.
        world (Optional[World], default=None): Associated Kripke world.
        children (List[TableauNode], default_factory=list): Child premise nodes in the derivation.
        is_closed (bool, default=False): Whether all branches under this node are closed.
        clash_details (Optional[str], default=None): Explanation of clash if closed directly here.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.tableau.ast import TableauNode, SignedFormula, Sign
        >>> from logic_prover.constructive.kripke import World
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> sf = SignedFormula(Sign.TRUE, p, World(0, "w0"))
        >>> node = TableauNode(id=1, signed_formula=sf, rule="Init")
        >>> node.is_leaf()
        True
    """

    id: int
    signed_formula: Optional[SignedFormula] = None
    rule: str = ""
    world: Optional[World] = None
    children: List[TableauNode] = field(default_factory=list)
    is_closed: bool = False
    clash_details: Optional[str] = None

    def is_leaf(self) -> bool:
        """Checks whether this node is a leaf in the tableau tree.

        Returns:
            bool: True if the node has no children, False otherwise.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode
            >>> node = TableauNode(id=1)
            >>> node.is_leaf()
            True
        """
        return len(self.children) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the tableau node and its children into a dictionary.

        Returns:
            Dict[str, Any]: Dictionary structure of the node.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode
            >>> node = TableauNode(id=1, rule="Init", is_closed=True)
            >>> node.to_dict()["rule"]
            'Init'
        """
        return {
            "id": self.id,
            "signed_formula": self.signed_formula.to_string() if self.signed_formula else None,
            "rule": self.rule,
            "world": self.world.name if self.world else None,
            "is_closed": self.is_closed,
            "clash_details": self.clash_details,
            "children": [c.to_dict() for c in self.children],
        }

    def to_string(self, prefix: str = "", is_last: bool = True) -> str:
        """Renders the node and its sub-branches in ASCII tree format.

        Args:
            prefix (str, default=''): Current indentation prefix.
            is_last (bool, default=True): Whether this child is the last among its siblings.

        Returns:
            str: Multi-line ASCII tree.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode
            >>> node = TableauNode(id=1, rule="Ax", is_closed=True)
            >>> "Ax" in node.to_string()
            True
        """
        connector = "+-- " if is_last else "|-- "
        status = "[CLOSED]" if self.is_closed else "[OPEN]"
        sf_str = f" : {self.signed_formula.to_string()}" if self.signed_formula else ""
        clash_str = f" ({self.clash_details})" if self.clash_details else ""
        lines = [f"{prefix}{connector}{self.rule}{sf_str} {status}{clash_str}"]

        child_prefix = prefix + ("    " if is_last else "|   ")
        for i, child in enumerate(self.children):
            child_is_last = (i == len(self.children) - 1)
            lines.append(child.to_string(prefix=child_prefix, is_last=child_is_last))

        return "\n".join(lines)

    def __str__(self) -> str:
        """Returns the ASCII tree representation of the node.

        Returns:
            str: Multi-line tree string.
        """
        return self.to_string()


class TableauProofTree:
    """Container and visualization manager for a semantic tableau derivation tree.

    Args:
        root (TableauNode): The root node of the derivation tree.

    Example:
        >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree
        >>> tree = TableauProofTree(TableauNode(id=1, rule="Init", is_closed=True))
        >>> tree.is_closed()
        True
    """

    root: TableauNode

    def __init__(self, root: TableauNode) -> None:
        """Initializes the tableau proof tree.

        Args:
            root (TableauNode): The root node.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree
            >>> tree = TableauProofTree(TableauNode(1, is_closed=True))
            >>> tree.get_size()
            1
        """
        self.root = root

    def is_closed(self) -> bool:
        """Determines if the entire tableau is closed (valid proof).

        Returns:
            bool: True if root node is closed, False otherwise.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree
            >>> tree = TableauProofTree(TableauNode(1, is_closed=True))
            >>> tree.is_closed()
            True
        """
        return self.root.is_closed

    def get_depth(self) -> int:
        """Computes the maximum depth of the tableau tree.

        Returns:
            int: Height of the tree.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree
            >>> tree = TableauProofTree(TableauNode(1))
            >>> tree.get_depth()
            1
        """
        def _calc(node: TableauNode) -> int:
            if not node.children:
                return 1
            return 1 + max(_calc(c) for c in node.children)
        return _calc(self.root)

    def get_size(self) -> int:
        """Computes the total number of nodes in the tableau derivation.

        Returns:
            int: Total node count.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree
            >>> tree = TableauProofTree(TableauNode(1))
            >>> tree.get_size()
            1
        """
        def _count(node: TableauNode) -> int:
            return 1 + sum(_count(c) for c in node.children)
        return _count(self.root)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the tableau tree into a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: Serialized dictionary.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree
            >>> tree = TableauProofTree(TableauNode(1, is_closed=True))
            >>> tree.to_dict()["is_closed"]
            True
        """
        return {
            "is_closed": self.is_closed(),
            "depth": self.get_depth(),
            "size": self.get_size(),
            "tree": self.root.to_dict(),
        }

    def to_string(self) -> str:
        """Renders the entire derivation tree as an ASCII diagram.

        Returns:
            str: Multi-line ASCII tree.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree
            >>> tree = TableauProofTree(TableauNode(1, rule="Root", is_closed=True))
            >>> "Root" in tree.to_string()
            True
        """
        return self.root.to_string(prefix="", is_last=True)

    def to_latex(self) -> str:
        """Generates LaTeX forest / prooftrees markup for the derivation.

        Returns:
            str: LaTeX formatted string.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree
            >>> tree = TableauProofTree(TableauNode(1, rule="Init", is_closed=True))
            >>> "\\begin{forest}" in tree.to_latex()
            True
        """
        lines = ["\\begin{forest}", "  for tree={math content, parent anchor=south, child anchor=north}"]

        def _rec(node: TableauNode, indent: str = "  ") -> None:
            sf_label = node.signed_formula.to_string(notation="latex") if node.signed_formula else ""
            rule_label = f"[{node.rule}]" if node.rule else ""
            status = " \\times" if node.is_closed and not node.children else ""
            label = f"{sf_label} \\; {rule_label}{status}".strip()
            lines.append(f"{indent}[{label}")
            for child in node.children:
                _rec(child, indent + "  ")
            lines.append(f"{indent}]")

        _rec(self.root, "  ")
        lines.append("\\end{forest}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Returns the default ASCII rendering.

        Returns:
            str: ASCII derivation tree string.
        """
        return self.to_string()


@dataclass
class TableauProofResult:
    """Result of an intuitionistic semantic tableau proof search.

    Args:
        is_valid (bool): True if formula is intuitionistically provable (all branches closed).
        tree (TableauProofTree): The generated semantic tableau derivation tree.
        countermodel (Optional[KripkeModel], default=None): Falsifying Kripke countermodel if unprovable.
        target (Optional[Formula], default=None): Target formula AST.
        premises (Tuple[Formula, ...], default_factory=tuple): Premises tuple.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree, TableauProofResult
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> tree = TableauProofTree(TableauNode(1, is_closed=True))
        >>> res = TableauProofResult(is_valid=True, tree=tree, target=p)
        >>> res.is_valid
        True
    """

    is_valid: bool
    tree: TableauProofTree
    countermodel: Optional[KripkeModel] = None
    target: Optional[Formula] = None
    premises: Tuple[Formula, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the proof result to a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: Dictionary structure of the result.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree, TableauProofResult
            >>> res = TableauProofResult(is_valid=True, tree=TableauProofTree(TableauNode(1, is_closed=True)))
            >>> res.to_dict()["is_valid"]
            True
        """
        return {
            "is_valid": self.is_valid,
            "target": to_string(self.target) if self.target else None,
            "premises": [to_string(p) for p in self.premises],
            "tree": self.tree.to_dict(),
            "countermodel": self.countermodel.to_dict() if self.countermodel else None,
        }

    def to_string(self) -> str:
        """Formats the proof result as a comprehensive multi-line report.

        Returns:
            str: Human-readable proof summary.

        Example:
            >>> from logic_prover.constructive.tableau.ast import TableauNode, TableauProofTree, TableauProofResult
            >>> res = TableauProofResult(is_valid=True, tree=TableauProofTree(TableauNode(1, is_closed=True)))
            >>> "Tableau Proof" in res.to_string()
            True
        """
        lines: List[str] = ["=== Intuitionistic Kripke Tableau Proof (IPC) ==="]
        if self.target:
            lines.append(f"Target: {to_string(self.target)}")
        if self.premises:
            lines.append(f"Premises: {', '.join(to_string(p) for p in self.premises)}")
        lines.append(f"Status: {'VALID (Intuitionistically Proven)' if self.is_valid else 'UNPROVABLE (Countermodel Found)'}")
        lines.append(f"Tree Size: {self.tree.get_size()} nodes, Depth: {self.tree.get_depth()}")
        lines.append("\n--- Derivation Tree ---")
        lines.append(self.tree.to_string())
        if self.countermodel:
            lines.append("\n--- Falsifying Kripke Countermodel ---")
            lines.append(self.countermodel.to_string())
        return "\n".join(lines)

    def __str__(self) -> str:
        """Returns the default string representation.

        Returns:
            str: Formatted proof result string.
        """
        return self.to_string()


__all__ = [
    "Sign",
    "SignedFormula",
    "TableauNode",
    "TableauProofTree",
    "TableauProofResult",
]
