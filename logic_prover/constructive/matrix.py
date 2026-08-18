"""Matrix decomposition, position trees, and connections for Wallen's method."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any, Set

from logic_prover.core.ast import (
    Formula, PredicateApp, Not, And, Or, Implies
)
from logic_prover.core.parser import to_string
from logic_prover.constructive.common import (
    normalize_formula, _is_atomic, _is_falsum, _is_verum, FALSUM
)
from logic_prover.constructive.prefix import (
    PrefixSymbol, PrefixConstant, PrefixVariable, Prefix
)


class PositionType(str, Enum):
    """Wallen primary types for positions in intuitionistic logic.

    Members:
        ALPHA: Non-branching propositional conjunction/disjunction position.
        BETA: Branching propositional position.
        PHI: Intuitionistic dynamic universal/implication premise position introducing prefix variables.
        PSI: Intuitionistic static existential/implication goal position introducing prefix constants.
        ATOM: Atomic proposition leaf position.

    Example:
        >>> from logic_prover.constructive.matrix import PositionType
        >>> PositionType.ALPHA.value
        'ALPHA'
    """

    ALPHA = "ALPHA"
    BETA = "BETA"
    PHI = "PHI"
    PSI = "PSI"
    ATOM = "ATOM"


@dataclass
class Position:
    """A node in the polar decomposition tree with prefix annotations.

    Args:
        id (int): Unique position integer ID.
        formula (Formula): Formula AST at this node.
        polarity (int): Polar value (0 = false / goal, 1 = true / premise).
        pos_type (PositionType): Wallen primary type.
        prefix (Prefix): Kripke world prefix.
        parent (Optional[Position], default=None): Parent position node.
        children (Tuple[Position, ...], default=()): Child positions.
        symbol (Optional[PrefixSymbol], default=None): Introduced prefix symbol.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.matrix import Position, PositionType
        >>> from logic_prover.constructive.prefix import Prefix
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> pos = Position(id=1, formula=p, polarity=0, pos_type=PositionType.ATOM, prefix=Prefix())
        >>> pos.polarity
        0
    """

    id: int
    formula: Formula
    polarity: int
    pos_type: PositionType
    prefix: Prefix
    parent: Optional[Position] = None
    children: Tuple[Position, ...] = field(default_factory=tuple)
    symbol: Optional[PrefixSymbol] = None

    def is_leaf(self) -> bool:
        """Checks if this position is a leaf (atomic proposition).

        Returns:
            bool: True if ATOM type, False otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.matrix import Position, PositionType
            >>> from logic_prover.constructive.prefix import Prefix
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> pos = Position(id=1, formula=p, polarity=0, pos_type=PositionType.ATOM, prefix=Prefix())
            >>> pos.is_leaf()
            True
        """
        return self.pos_type == PositionType.ATOM

    def to_string(self) -> str:
        """Returns a string representation of the signed position.

        Returns:
            str: Formatted position label.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.matrix import Position, PositionType
            >>> from logic_prover.constructive.prefix import Prefix
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> pos = Position(id=1, formula=p, polarity=1, pos_type=PositionType.ATOM, prefix=Prefix())
            >>> "P^1" in pos.to_string()
            True
        """
        f_str = to_string(self.formula) if not _is_falsum(self.formula) else "_bot"
        return f"{f_str}^{self.polarity}:{self.prefix}"

    def __str__(self) -> str:
        """Returns the default string representation of the position."""
        return self.to_string()


class FormulaTree:
    """Constructs and manages the polar decomposition tree and paths for Wallen's method.

    Args:
        target (Formula): Goal formula to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis formulas.
        multiplicity (int, default=1): Multiplicity for phi-node duplications.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.matrix import FormulaTree
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> tree = FormulaTree(target=Implies(p, p))
        >>> len(tree.leaves)
        2
    """

    target: Formula
    premises: Tuple[Formula, ...]
    multiplicity: int
    root: Position
    positions: List[Position]
    leaves: List[Position]
    tree_order: Dict[PrefixSymbol, Set[PrefixSymbol]]
    _counter: int
    _const_counter: int
    _var_counter: int

    def __init__(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
        multiplicity: int = 1,
    ) -> None:
        """Initializes and decomposes the formula tree.

        Args:
            target (Formula): Goal formula AST to decompose.
            premises (Optional[List[Formula]], default=None): Optional hypothesis formulas.
            multiplicity (int, default=1): Multiplicity bound for phi-node duplications.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.matrix import FormulaTree
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> tree = FormulaTree(target=Implies(p, p))
            >>> len(tree.positions) > 0
            True
        """
        self.target = normalize_formula(target)
        self.premises = tuple(normalize_formula(p) for p in (premises or []))
        self.multiplicity = max(1, multiplicity)
        self.positions = []
        self.leaves = []
        self.tree_order = {}
        self._counter = 0
        self._const_counter = 0
        self._var_counter = 0

        # Build initial root prefix c0
        initial_const = PrefixConstant("c0")
        self._add_tree_symbol(initial_const)
        initial_prefix = Prefix((initial_const,))

        if self.premises:
            root_positions: List[Position] = []
            for prem in self.premises:
                prem_pos = self._decompose(prem, polarity=1, prefix=initial_prefix, parent=None)
                root_positions.append(prem_pos)
            target_pos = self._decompose(self.target, polarity=0, prefix=initial_prefix, parent=None)
            root_positions.append(target_pos)

            self._counter += 1
            self.root = Position(
                id=self._counter,
                formula=self.target,
                polarity=0,
                pos_type=PositionType.BETA,
                prefix=initial_prefix,
                children=tuple(root_positions),
            )
            self.positions.append(self.root)
        else:
            self.root = self._decompose(self.target, polarity=0, prefix=initial_prefix, parent=None)

    def _next_id(self) -> int:
        """Generates the next unique integer node ID.

        Returns:
            int: Next ID.
        """
        self._counter += 1
        return self._counter

    def _next_constant(self) -> PrefixConstant:
        """Generates the next unique prefix constant.

        Returns:
            PrefixConstant: New prefix constant.
        """
        self._const_counter += 1
        c = PrefixConstant(f"c{self._const_counter}")
        self._add_tree_symbol(c)
        return c

    def _next_variable(self) -> PrefixVariable:
        """Generates the next unique prefix variable.

        Returns:
            PrefixVariable: New prefix variable.
        """
        self._var_counter += 1
        v = PrefixVariable(f"V{self._var_counter}")
        self._add_tree_symbol(v)
        return v

    def _add_tree_symbol(self, sym: PrefixSymbol) -> None:
        """Registers a symbol in the tree ordering dictionary.

        Args:
            sym (PrefixSymbol): Symbol to add.
        """
        if sym not in self.tree_order:
            self.tree_order[sym] = set()

    def _add_order_edge(self, parent: PrefixSymbol, child: PrefixSymbol) -> None:
        """Adds a directed tree-ordering edge parent <_0 child.

        Args:
            parent (PrefixSymbol): Dominating prefix symbol.
            child (PrefixSymbol): Dominated prefix symbol.
        """
        self._add_tree_symbol(parent)
        self._add_tree_symbol(child)
        self.tree_order[parent].add(child)

    def _decompose(
        self,
        f: Formula,
        polarity: int,
        prefix: Prefix,
        parent: Optional[Position],
    ) -> Position:
        """Recursively decomposes a formula AST into Wallen position nodes.

        Args:
            f (Formula): Normalized formula AST.
            polarity (int): 0 for false/goal, 1 for true/premise.
            prefix (Prefix): Current Kripke world prefix.
            parent (Optional[Position]): Parent position.

        Returns:
            Position: Created root position of this subtree.
        """
        pos_id = self._next_id()

        # Atomic proposition / Falsum / Verum
        if _is_atomic(f):
            leaf_prefix = prefix
            sym: Optional[PrefixSymbol] = None
            if polarity == 1 and not _is_falsum(f) and not _is_verum(f):
                var = self._next_variable()
                if prefix.symbols:
                    self._add_order_edge(prefix.symbols[-1], var)
                leaf_prefix = prefix.append(var)
                sym = var

            pos = Position(
                id=pos_id,
                formula=f,
                polarity=polarity,
                pos_type=PositionType.ATOM,
                prefix=leaf_prefix,
                parent=parent,
                symbol=sym,
            )
            self.positions.append(pos)
            self.leaves.append(pos)
            return pos

        # Conjunction: (A & B)
        if isinstance(f, And):
            if polarity == 0:
                pos = Position(
                    id=pos_id,
                    formula=f,
                    polarity=polarity,
                    pos_type=PositionType.ALPHA,
                    prefix=prefix,
                    parent=parent,
                )
                c1 = self._decompose(f.left, polarity=0, prefix=prefix, parent=pos)
                c2 = self._decompose(f.right, polarity=0, prefix=prefix, parent=pos)
                pos.children = (c1, c2)
            else:
                pos = Position(
                    id=pos_id,
                    formula=f,
                    polarity=polarity,
                    pos_type=PositionType.BETA,
                    prefix=prefix,
                    parent=parent,
                )
                c1 = self._decompose(f.left, polarity=1, prefix=prefix, parent=pos)
                c2 = self._decompose(f.right, polarity=1, prefix=prefix, parent=pos)
                pos.children = (c1, c2)
            self.positions.append(pos)
            return pos

        # Disjunction: (A | B)
        if isinstance(f, Or):
            if polarity == 0:
                pos = Position(
                    id=pos_id,
                    formula=f,
                    polarity=polarity,
                    pos_type=PositionType.BETA,
                    prefix=prefix,
                    parent=parent,
                )
                c1 = self._decompose(f.left, polarity=0, prefix=prefix, parent=pos)
                c2 = self._decompose(f.right, polarity=0, prefix=prefix, parent=pos)
                pos.children = (c1, c2)
            else:
                pos = Position(
                    id=pos_id,
                    formula=f,
                    polarity=polarity,
                    pos_type=PositionType.ALPHA,
                    prefix=prefix,
                    parent=parent,
                )
                c1 = self._decompose(f.left, polarity=1, prefix=prefix, parent=pos)
                c2 = self._decompose(f.right, polarity=1, prefix=prefix, parent=pos)
                pos.children = (c1, c2)
            self.positions.append(pos)
            return pos

        # Implication: (A => B)
        if isinstance(f, Implies):
            if polarity == 0:
                const = self._next_constant()
                if prefix.symbols:
                    self._add_order_edge(prefix.symbols[-1], const)
                new_prefix = prefix.append(const)

                pos = Position(
                    id=pos_id,
                    formula=f,
                    polarity=polarity,
                    pos_type=PositionType.PSI,
                    prefix=new_prefix,
                    parent=parent,
                    symbol=const,
                )
                c1 = self._decompose(f.left, polarity=1, prefix=new_prefix, parent=pos)
                c2 = self._decompose(f.right, polarity=0, prefix=new_prefix, parent=pos)
                pos.children = (c1, c2)
                self.positions.append(pos)
                return pos
            else:
                children_list: List[Position] = []
                pos = Position(
                    id=pos_id,
                    formula=f,
                    polarity=polarity,
                    pos_type=PositionType.PHI,
                    prefix=prefix,
                    parent=parent,
                )
                for _ in range(self.multiplicity):
                    var = self._next_variable()
                    if prefix.symbols:
                        self._add_order_edge(prefix.symbols[-1], var)
                    phi_prefix = prefix.append(var)

                    c1 = self._decompose(f.left, polarity=0, prefix=phi_prefix, parent=pos)
                    c2 = self._decompose(f.right, polarity=1, prefix=phi_prefix, parent=pos)
                    children_list.extend([c1, c2])

                pos.children = tuple(children_list)
                self.positions.append(pos)
                return pos

        pos = Position(
            id=pos_id,
            formula=f,
            polarity=polarity,
            pos_type=PositionType.ATOM,
            prefix=prefix,
            parent=parent,
        )
        self.positions.append(pos)
        self.leaves.append(pos)
        return pos

    def get_paths(self) -> List[List[Position]]:
        """Extracts all vertical paths (sets of atomic leaves) through the matrix.

        Returns:
            List[List[Position]]: List of paths, where each path is a list of leaf positions.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.matrix import FormulaTree
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> tree = FormulaTree(target=Implies(p, p))
            >>> paths = tree.get_paths()
            >>> len(paths)
            1
            >>> len(paths[0])
            2
        """
        def _collect(pos: Position) -> List[List[Position]]:
            if pos.is_leaf():
                return [[pos]]

            if pos.pos_type == PositionType.ALPHA:
                res: List[List[Position]] = []
                for child in pos.children:
                    res.extend(_collect(child))
                return res if res else [[]]

            elif pos.pos_type in (PositionType.BETA, PositionType.PSI):
                child_paths = [_collect(child) for child in pos.children]
                if not child_paths:
                    return [[]]
                comb: List[List[Position]] = child_paths[0]
                for next_paths in child_paths[1:]:
                    new_comb: List[List[Position]] = []
                    for p1 in comb:
                        for p2 in next_paths:
                            new_comb.append(p1 + p2)
                    comb = new_comb
                return comb

            elif pos.pos_type == PositionType.PHI:
                pairs: List[Tuple[Position, Position]] = []
                for i in range(0, len(pos.children), 2):
                    if i + 1 < len(pos.children):
                        pairs.append((pos.children[i], pos.children[i + 1]))

                if not pairs:
                    return [[]]

                comb_res: List[List[Position]] = [[]]
                for c1, c2 in pairs:
                    paths_c1 = _collect(c1)
                    paths_c2 = _collect(c2)
                    branch_paths = paths_c1 + paths_c2
                    new_comb_res: List[List[Position]] = []
                    for existing in comb_res:
                        for b in branch_paths:
                            new_comb_res.append(existing + b)
                    comb_res = new_comb_res
                return comb_res

            return [[]]

        return _collect(self.root)


@dataclass(frozen=True)
class Connection:
    """A complementary pair of atomic leaf positions (u^0, v^1) with identical predicate.

    Args:
        positive (Position): Positive leaf position (premise / true).
        negative (Position): Negative leaf position (goal / false).

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.matrix import Position, PositionType, Connection
        >>> from logic_prover.constructive.prefix import Prefix
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> p1 = Position(1, p, 1, PositionType.ATOM, Prefix())
        >>> p0 = Position(2, p, 0, PositionType.ATOM, Prefix())
        >>> conn = Connection(positive=p1, negative=p0)
        >>> conn.positive.polarity
        1
    """

    positive: Position
    negative: Position

    def to_string(self) -> str:
        """Formats the connection as a string showing leaves and prefixes.

        Returns:
            str: Human-readable connection representation.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.matrix import Position, PositionType, Connection
            >>> from logic_prover.constructive.prefix import Prefix
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> p1 = Position(1, p, 1, PositionType.ATOM, Prefix())
            >>> p0 = Position(2, p, 0, PositionType.ATOM, Prefix())
            >>> conn = Connection(positive=p1, negative=p0)
            >>> "{" in conn.to_string()
            True
        """
        return f"{{{self.positive.to_string()} <-> {self.negative.to_string()}}}"

    def __str__(self) -> str:
        """Returns the default string representation of the connection."""
        return self.to_string()


__all__ = [
    "PositionType",
    "Position",
    "FormulaTree",
    "Connection",
]
