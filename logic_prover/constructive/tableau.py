"""Semantic Tableaux with Kripke Semantics for Intuitionistic Propositional Logic (IPC).

This module implements a labelled/prefixed semantic tableau calculus for intuitionistic
propositional logic (Fitting 1969, 1983; Goré 1999). Proof search decomposes signed
formulas across explicit Kripke worlds. When a formula is intuitionistically valid,
all tableau branches close. When a formula is unprovable (e.g. classical tautologies
such as excluded middle or double negation elimination), an open saturated branch
is used to construct an explicit finite Kripke countermodel (W, <=, V) falsifying
the target.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any, Set

from logic_prover.core.ast import (
    Formula, PredicateApp, Not, And, Or, Implies, Iff
)
from logic_prover.core.parser import to_string
from logic_prover.constructive.common import (
    FALSUM,
    VERUM,
    _is_falsum,
    _is_verum,
    _is_atomic,
)
from logic_prover.constructive.kripke import (
    World,
    KripkeModel,
)


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
            >>> from logic_prover.constructive.tableau import Sign
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
        >>> from logic_prover.constructive.tableau import SignedFormula, Sign
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
            >>> from logic_prover.constructive.tableau import SignedFormula, Sign
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
            >>> from logic_prover.constructive.tableau import SignedFormula, Sign
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
        >>> from logic_prover.constructive.tableau import TableauNode, SignedFormula, Sign, World
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
            >>> from logic_prover.constructive.tableau import TableauNode
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
            >>> from logic_prover.constructive.tableau import TableauNode
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
            >>> from logic_prover.constructive.tableau import TableauNode
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
        """Returns the ASCII tree representation of the node."""
        return self.to_string()


class TableauProofTree:
    """Container and visualization manager for a semantic tableau derivation tree.

    Args:
        root (TableauNode): The root node of the derivation tree.

    Example:
        >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree
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
        """Returns the default ASCII rendering."""
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
        >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree, TableauProofResult
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree, TableauProofResult
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
            >>> from logic_prover.constructive.tableau import TableauNode, TableauProofTree, TableauProofResult
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
        """Returns the default string representation."""
        return self.to_string()


@dataclass
class _BranchState:
    """Internal container for the state of a single tableau branch.

    Args:
        worlds (List[World], default_factory=list): List of worlds active in this branch.
        relations (Dict[World, Set[World]], default_factory=dict): Accessibility relation edges.
        t_formulas (Dict[World, Set[Formula]], default_factory=dict): Signed true formulas per world.
        f_formulas (Dict[World, Set[Formula]], default_factory=dict): Signed false formulas per world.
        applied_rules (Set[Tuple[Any, ...]], default_factory=set): Set of rule signature tuples already applied.

    Example:
        >>> from logic_prover.constructive.kripke import World
        >>> from logic_prover.constructive.tableau import _BranchState
        >>> state = _BranchState()
        >>> w0 = World(0, "w0")
        >>> state.add_world(w0)
        >>> w0 in state.worlds
        True
    """

    worlds: List[World] = field(default_factory=list)
    relations: Dict[World, Set[World]] = field(default_factory=dict)
    t_formulas: Dict[World, Set[Formula]] = field(default_factory=dict)
    f_formulas: Dict[World, Set[Formula]] = field(default_factory=dict)
    applied_rules: Set[Tuple[Any, ...]] = field(default_factory=set)

    def copy(self) -> _BranchState:
        """Creates an independent deep copy of the branch state.

        Returns:
            _BranchState: Cloned branch state.

        Example:
            >>> from logic_prover.constructive.tableau import _BranchState
            >>> s = _BranchState()
            >>> s_copy = s.copy()
            >>> len(s_copy.worlds)
            0
        """
        return _BranchState(
            worlds=list(self.worlds),
            relations={w: set(succs) for w, succs in self.relations.items()},
            t_formulas={w: set(forms) for w, forms in self.t_formulas.items()},
            f_formulas={w: set(forms) for w, forms in self.f_formulas.items()},
            applied_rules=set(self.applied_rules),
        )

    def add_world(self, world: World) -> None:
        """Registers a world in this branch state ensuring reflexivity.

        Args:
            world (World): The world node to register.

        Example:
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau import _BranchState
            >>> s = _BranchState()
            >>> s.add_world(World(0, "w0"))
            >>> len(s.worlds)
            1
        """
        if world not in self.worlds:
            self.worlds.append(world)
        self.relations.setdefault(world, {world})
        self.t_formulas.setdefault(world, set())
        self.f_formulas.setdefault(world, set())

    def add_relation(self, source: World, target: World) -> None:
        """Adds accessibility relation source <= target with transitive closure and monotonicity.

        Args:
            source (World): Source world node.
            target (World): Target world node.

        Example:
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau import _BranchState
            >>> s = _BranchState()
            >>> w0, w1 = World(0, "w0"), World(1, "w1")
            >>> s.add_relation(w0, w1)
            >>> w1 in s.relations[w0]
            True
        """
        self.add_world(source)
        self.add_world(target)
        self.relations[source].add(target)

        # Transitive closure
        for u in self.worlds:
            if source in self.relations.get(u, set()):
                self.relations[u].add(target)

        # Propagate T-formulas from predecessors to target
        for u in self.worlds:
            if target in self.relations.get(u, set()) and u != target:
                for f in self.t_formulas.get(u, set()):
                    self.t_formulas[target].add(f)

    def add_t_formula(self, world: World, formula: Formula) -> None:
        """Adds a true formula at world and propagates along accessibility relation.

        Args:
            world (World): World node where formula is asserted true.
            formula (Formula): Formula AST asserted true.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau import _BranchState
            >>> s = _BranchState()
            >>> w0 = World(0, "w0")
            >>> p = PredicateApp("P", 0, ())
            >>> s.add_t_formula(w0, p)
            >>> p in s.t_formulas[w0]
            True
        """
        self.add_world(world)
        self.t_formulas[world].add(formula)
        for succ in self.relations.get(world, set()):
            self.t_formulas.setdefault(succ, set()).add(formula)

    def add_f_formula(self, world: World, formula: Formula) -> None:
        """Adds a false formula at world.

        Args:
            world (World): World node where formula is asserted false.
            formula (Formula): Formula AST asserted false.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau import _BranchState
            >>> s = _BranchState()
            >>> w0 = World(0, "w0")
            >>> p = PredicateApp("P", 0, ())
            >>> s.add_f_formula(w0, p)
            >>> p in s.f_formulas[w0]
            True
        """
        self.add_world(world)
        self.f_formulas[world].add(formula)


class TableauProver:
    """Automated Theorem Prover and Countermodel Builder for Intuitionistic Logic.

    Implements labelled semantic tableaux with explicit Kripke frame semantics.

    Args:
        max_depth (int, default=100): Maximum branch depth limit.
        max_worlds (int, default=50): Maximum number of Kripke worlds allowed.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.tableau import TableauProver
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> prover = TableauProver()
        >>> res = prover.prove(target=Implies(p, p))
        >>> res.is_valid
        True
    """

    max_depth: int
    max_worlds: int
    _node_counter: int

    def __init__(self, max_depth: int = 100, max_worlds: int = 50) -> None:
        """Initializes the tableau prover with depth and world bounds.

        Args:
            max_depth (int, default=100): Maximum search depth.
            max_worlds (int, default=50): Maximum number of generated worlds.

        Example:
            >>> from logic_prover.constructive.tableau import TableauProver
            >>> prover = TableauProver(max_depth=50)
            >>> prover.max_depth
            50
        """
        self.max_depth = max(1, max_depth)
        self.max_worlds = max(1, max_worlds)
        self._node_counter = 0

    def _next_node_id(self) -> int:
        """Generates a unique node identifier.

        Returns:
            int: Next integer ID.
        """
        self._node_counter += 1
        return self._node_counter

    def _check_clash(self, state: _BranchState) -> Optional[Tuple[World, Formula, str]]:
        """Checks if a branch contains an immediate semantic contradiction.

        Args:
            state (_BranchState): Current branch state.

        Returns:
            Optional[Tuple[World, Formula, str]]: Clash info (world, formula, explanation) or None.
        """
        for w in state.worlds:
            # 1. Falsum asserted true: w |= _bot
            for f in state.t_formulas.get(w, set()):
                if _is_falsum(f):
                    return (w, f, f"Falsum bot asserted TRUE at {w.name}")

            # 2. Verum asserted false: w |/= _top
            for f in state.f_formulas.get(w, set()):
                if _is_verum(f):
                    return (w, f, f"Verum top asserted FALSE at {w.name}")

            # 3. Direct complementary clash: w |= A and w |/= A
            t_set = state.t_formulas.get(w, set())
            f_set = state.f_formulas.get(w, set())
            common = t_set.intersection(f_set)
            if common:
                clash_formula = next(iter(common))
                return (w, clash_formula, f"Complementary clash on {to_string(clash_formula)} at {w.name}")

        return None

    def _extract_countermodel(self, state: _BranchState) -> KripkeModel:
        """Constructs an explicit Kripke countermodel from an open saturated branch.

        Args:
            state (_BranchState): Saturated open branch.

        Returns:
            KripkeModel: The constructed Kripke model (W, <=, V).
        """
        model = KripkeModel()
        for w in state.worlds:
            model.add_world(w)
        for u in state.worlds:
            for v in state.relations.get(u, set()):
                model.add_relation(u, v)
        for w in state.worlds:
            for f in state.t_formulas.get(w, set()):
                if _is_atomic(f) and not _is_falsum(f) and not _is_verum(f):
                    model.add_valuation(w, f)
        return model

    def prove(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
    ) -> TableauProofResult:
        """Attempts to prove an intuitionistic propositional formula or find a Kripke countermodel.

        Args:
            target (Formula): The target formula to prove.
            premises (Optional[List[Formula]], default=None): Optional list of hypothesis premises.

        Returns:
            TableauProofResult: Complete derivation result with validity status and tree.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.tableau import TableauProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = TableauProver()
            >>> res = prover.prove(target=Implies(p, p))
            >>> res.is_valid
            True
        """
        self._node_counter = 0
        premise_list = tuple(premises or [])

        w0 = World(id=0, name="w0")
        initial_state = _BranchState()
        initial_state.add_world(w0)

        for p in premise_list:
            initial_state.add_t_formula(w0, p)
        initial_state.add_f_formula(w0, target)

        root_node = TableauNode(
            id=self._next_node_id(),
            signed_formula=SignedFormula(Sign.FALSE, target, w0),
            rule="Target",
            world=w0,
        )

        is_closed, open_state = self._expand_branch(state=initial_state, node=root_node, depth=1)
        root_node.is_closed = is_closed

        tree = TableauProofTree(root=root_node)
        countermodel: Optional[KripkeModel] = None
        if not is_closed and open_state is not None:
            countermodel = self._extract_countermodel(open_state)

        return TableauProofResult(
            is_valid=is_closed,
            tree=tree,
            countermodel=countermodel,
            target=target,
            premises=premise_list,
        )

    def _expand_branch(
        self,
        state: _BranchState,
        node: TableauNode,
        depth: int,
    ) -> Tuple[bool, Optional[_BranchState]]:
        """Recursively expands a tableau branch applying semantic rules.

        Args:
            state (_BranchState): Current branch state.
            node (TableauNode): Current tree node.
            depth (int): Current tree depth.

        Returns:
            Tuple[bool, Optional[_BranchState]]: (is_closed, open_branch_state).
        """
        # Step 1: Check for contradiction / clash
        clash = self._check_clash(state)
        if clash is not None:
            w, f, desc = clash
            node.is_closed = True
            node.clash_details = desc
            return True, None

        if depth >= self.max_depth or len(state.worlds) > self.max_worlds:
            # Depth bound reached: treat as open branch
            node.is_closed = False
            return False, state

        # Step 2: Apply Non-Branching Rules
        # 2a. T(And): T(A & B, w) -> T(A, w), T(B, w)
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, And):
                    sig = ("T_And", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f, w),
                            rule="T_And",
                            world=w,
                        )
                        node.children.append(child)
                        state.add_t_formula(w, f.left)
                        state.add_t_formula(w, f.right)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 2b. F(Or): F(A | B, w) -> F(A, w), F(B, w)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, Or):
                    sig = ("F_Or", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f, w),
                            rule="F_Or",
                            world=w,
                        )
                        node.children.append(child)
                        state.add_f_formula(w, f.left)
                        state.add_f_formula(w, f.right)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 2c. T(Not): T(~A, w) -> F(A, w') for all accessible w'
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Not):
                    for w_prime in list(state.relations.get(w, set())):
                        sig = ("T_Not", f, w, w_prime)
                        if sig not in state.applied_rules:
                            state.applied_rules.add(sig)
                            child = TableauNode(
                                id=self._next_node_id(),
                                signed_formula=SignedFormula(Sign.TRUE, f, w),
                                rule="T_Not",
                                world=w_prime,
                            )
                            node.children.append(child)
                            state.add_f_formula(w_prime, f.operand)
                            is_closed, open_b = self._expand_branch(state, child, depth + 1)
                            node.is_closed = is_closed
                            return is_closed, open_b

        # Step 3: Apply World-Creating Rules (Kripke World Transitions)
        # 3a. F(Implies): F(A => B, w) -> creates w_new >= w with T(A, w_new), F(B, w_new)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, Implies) and not (_is_falsum(f.right)):
                    sig = ("F_Imp", f, w)
                    if sig not in state.applied_rules and len(state.worlds) < self.max_worlds:
                        state.applied_rules.add(sig)
                        new_world_id = len(state.worlds)
                        w_new = World(id=new_world_id, name=f"w{new_world_id}")
                        state.add_world(w_new)
                        state.add_relation(w, w_new)
                        state.add_t_formula(w_new, f.left)
                        state.add_f_formula(w_new, f.right)

                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f, w),
                            rule=f"F_Imp ({w.name} <= {w_new.name})",
                            world=w_new,
                        )
                        node.children.append(child)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 3b. F(Not) or F(A => _bot): F(~A, w) -> creates w_new >= w with T(A, w_new), F(_bot, w_new)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                is_neg = isinstance(f, Not)
                is_imp_bot = isinstance(f, Implies) and _is_falsum(f.right)
                if is_neg or is_imp_bot:
                    sig = ("F_Not", f, w)
                    if sig not in state.applied_rules and len(state.worlds) < self.max_worlds:
                        state.applied_rules.add(sig)
                        operand = f.operand if is_neg else f.left
                        new_world_id = len(state.worlds)
                        w_new = World(id=new_world_id, name=f"w{new_world_id}")
                        state.add_world(w_new)
                        state.add_relation(w, w_new)
                        state.add_t_formula(w_new, operand)
                        state.add_f_formula(w_new, FALSUM)

                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f, w),
                            rule=f"F_Not ({w.name} <= {w_new.name})",
                            world=w_new,
                        )
                        node.children.append(child)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # Step 4: Apply Branching Rules
        # 4a. F(And): F(A & B, w) -> F(A, w) | F(B, w)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, And):
                    sig = ("F_And", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)

                        # Left branch: F(A, w)
                        state_l = state.copy()
                        state_l.add_f_formula(w, f.left)
                        child_l = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f.left, w),
                            rule="F_And_L",
                            world=w,
                        )
                        node.children.append(child_l)
                        closed_l, open_l = self._expand_branch(state_l, child_l, depth + 1)

                        if not closed_l:
                            node.is_closed = False
                            return False, open_l

                        # Right branch: F(B, w)
                        state_r = state.copy()
                        state_r.add_f_formula(w, f.right)
                        child_r = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f.right, w),
                            rule="F_And_R",
                            world=w,
                        )
                        node.children.append(child_r)
                        closed_r, open_r = self._expand_branch(state_r, child_r, depth + 1)

                        node.is_closed = closed_l and closed_r
                        return node.is_closed, open_r if not closed_r else None

        # 4b. T(Or): T(A | B, w) -> T(A, w) | T(B, w)
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Or):
                    sig = ("T_Or", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)

                        # Left branch: T(A, w)
                        state_l = state.copy()
                        state_l.add_t_formula(w, f.left)
                        child_l = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f.left, w),
                            rule="T_Or_L",
                            world=w,
                        )
                        node.children.append(child_l)
                        closed_l, open_l = self._expand_branch(state_l, child_l, depth + 1)

                        if not closed_l:
                            node.is_closed = False
                            return False, open_l

                        # Right branch: T(B, w)
                        state_r = state.copy()
                        state_r.add_t_formula(w, f.right)
                        child_r = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f.right, w),
                            rule="T_Or_R",
                            world=w,
                        )
                        node.children.append(child_r)
                        closed_r, open_r = self._expand_branch(state_r, child_r, depth + 1)

                        node.is_closed = closed_l and closed_r
                        return node.is_closed, open_r if not closed_r else None

        # 4c. T(Implies): T(A => B, w) -> for all accessible w' >= w, F(A, w') | T(B, w')
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Implies) and not _is_falsum(f.right):
                    for w_prime in list(state.relations.get(w, set())):
                        sig = ("T_Imp", f, w, w_prime)
                        if sig not in state.applied_rules:
                            state.applied_rules.add(sig)

                            # Left branch: F(A, w')
                            state_l = state.copy()
                            state_l.add_f_formula(w_prime, f.left)
                            child_l = TableauNode(
                                id=self._next_node_id(),
                                signed_formula=SignedFormula(Sign.FALSE, f.left, w_prime),
                                rule=f"T_Imp_F ({w_prime.name})",
                                world=w_prime,
                            )
                            node.children.append(child_l)
                            closed_l, open_l = self._expand_branch(state_l, child_l, depth + 1)

                            if not closed_l:
                                node.is_closed = False
                                return False, open_l

                            # Right branch: T(B, w')
                            state_r = state.copy()
                            state_r.add_t_formula(w_prime, f.right)
                            child_r = TableauNode(
                                id=self._next_node_id(),
                                signed_formula=SignedFormula(Sign.TRUE, f.right, w_prime),
                                rule=f"T_Imp_T ({w_prime.name})",
                                world=w_prime,
                            )
                            node.children.append(child_r)
                            closed_r, open_r = self._expand_branch(state_r, child_r, depth + 1)

                            node.is_closed = closed_l and closed_r
                            return node.is_closed, open_r if not closed_r else None

        # 4d. T(Iff): T(A <=> B, w) -> T(A => B, w), T(B => A, w)
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Iff):
                    sig = ("T_Iff", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        imp1 = Implies(left=f.left, right=f.right)
                        imp2 = Implies(left=f.right, right=f.left)
                        state.add_t_formula(w, imp1)
                        state.add_t_formula(w, imp2)
                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f, w),
                            rule="T_Iff",
                            world=w,
                        )
                        node.children.append(child)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 4e. F(Iff): F(A <=> B, w) -> F(A => B, w) | F(B => A, w)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, Iff):
                    sig = ("F_Iff", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        imp1 = Implies(left=f.left, right=f.right)
                        imp2 = Implies(left=f.right, right=f.left)

                        # Left branch: F(A => B, w)
                        state_l = state.copy()
                        state_l.add_f_formula(w, imp1)
                        child_l = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, imp1, w),
                            rule="F_Iff_L",
                            world=w,
                        )
                        node.children.append(child_l)
                        closed_l, open_l = self._expand_branch(state_l, child_l, depth + 1)

                        if not closed_l:
                            node.is_closed = False
                            return False, open_l

                        # Right branch: F(B => A, w)
                        state_r = state.copy()
                        state_r.add_f_formula(w, imp2)
                        child_r = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, imp2, w),
                            rule="F_Iff_R",
                            world=w,
                        )
                        node.children.append(child_r)
                        closed_r, open_r = self._expand_branch(state_r, child_r, depth + 1)

                        node.is_closed = closed_l and closed_r
                        return node.is_closed, open_r if not closed_r else None

        # Step 5: Saturated branch with no further rules applicable and no clash
        node.is_closed = False
        return False, state

    def is_valid(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
    ) -> bool:
        """Checks whether a formula is intuitionistically valid using semantic tableaux.

        Args:
            target (Formula): Formula AST to test.
            premises (Optional[List[Formula]], default=None): Optional hypothesis formulas.

        Returns:
            bool: True if intuitionistically provable, False otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.tableau import TableauProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = TableauProver()
            >>> prover.is_valid(Implies(p, p))
            True
        """
        result = self.prove(target=target, premises=premises)
        return result.is_valid

    def countermodel(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
    ) -> Optional[KripkeModel]:
        """Extracts a Kripke countermodel falsifying the formula if it is not valid.

        Args:
            target (Formula): Formula AST to check.
            premises (Optional[List[Formula]], default=None): Optional hypothesis formulas.

        Returns:
            Optional[KripkeModel]: Falsifying Kripke countermodel if unprovable, None if valid.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Or, Not
            >>> from logic_prover.constructive.tableau import TableauProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = TableauProver()
            >>> cm = prover.countermodel(Or(p, Not(p)))
            >>> cm is not None
            True
        """
        result = self.prove(target=target, premises=premises)
        return result.countermodel


def prove_tableau(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_depth: int = 100,
    max_worlds: int = 50,
) -> TableauProofResult:
    """Proves an intuitionistic formula or extracts a Kripke countermodel via semantic tableaux.

    Args:
        formula (Formula): Target formula AST to prove.
        premises (Optional[List[Formula]], default=None): Optional list of hypothesis formulas.
        max_depth (int, default=100): Maximum search depth bound.
        max_worlds (int, default=50): Maximum number of possible worlds to construct.

    Returns:
        TableauProofResult: Complete derivation result container with tree and countermodel.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.tableau import prove_tableau
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> res = prove_tableau(Implies(p, p))
        >>> res.is_valid
        True
    """
    prover = TableauProver(max_depth=max_depth, max_worlds=max_worlds)
    return prover.prove(target=formula, premises=premises)


__all__ = [
    "FALSUM",
    "VERUM",
    "Sign",
    "World",
    "SignedFormula",
    "KripkeModel",
    "TableauNode",
    "TableauProofTree",
    "TableauProofResult",
    "TableauProver",
    "prove_tableau",
]
