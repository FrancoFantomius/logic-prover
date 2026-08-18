"""Kripke frames, possible worlds, and semantic models for Intuitionistic Logic.

This module provides Kripke semantics structures for intuitionistic propositional
logic (Fitting 1969; Chagrov & Zakharyaschev 1997). In intuitionistic Kripke semantics,
a model M = (W, <=, V) consists of a non-empty set of worlds W, a reflexive-transitive
preorder <=, and a monotone valuation V where u <= v implies V(u) <= V(v).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Set

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


@dataclass(frozen=True, slots=True)
class World:
    """Represents a possible world node in a Kripke frame.

    Args:
        id (int): Unique non-negative integer identifier of the world.
        name (str): Human-readable name of the world (e.g., 'w0', 'w1').

    Example:
        >>> from logic_prover.constructive.kripke import World
        >>> w = World(id=0, name="w0")
        >>> w.name
        'w0'
    """

    id: int
    name: str

    def __str__(self) -> str:
        """Returns the world name.

        Returns:
            str: Name of the world.

        Example:
            >>> from logic_prover.constructive.kripke import World
            >>> str(World(id=1, name="w1"))
            'w1'
        """
        return self.name

    def __repr__(self) -> str:
        """Returns the detailed representation of the world.

        Returns:
            str: Representation string.

        Example:
            >>> from logic_prover.constructive.kripke import World
            >>> repr(World(id=0, name="w0"))
            'World(id=0, name=w0)'
        """
        return f"World(id={self.id}, name={self.name})"


class KripkeModel:
    """A finite Kripke Model (W, <=, V) for Intuitionistic Propositional Logic.

    In intuitionistic Kripke semantics:
    - W is a non-empty set of possible worlds.
    - <= is a preorder (reflexive, transitive accessibility relation).
    - V maps each world w in W to a set of true atomic propositions such that
      if w <= w' then V(w) <= V(w') (monotonicity / persistence / heredity).

    Args:
        worlds (Optional[List[World]], default=None): List of worlds in the model.
        relations (Optional[Dict[World, Set[World]]], default=None): Accessibility map.
        valuations (Optional[Dict[World, Set[Formula]]], default=None): Atomic valuation map.

    Example:
        >>> from logic_prover.constructive.kripke import KripkeModel, World
        >>> model = KripkeModel()
        >>> w0 = World(0, "w0")
        >>> model.add_world(w0)
        >>> w0 in model.worlds
        True
    """

    worlds: List[World]
    relations: Dict[World, Set[World]]
    valuations: Dict[World, Set[Formula]]

    def __init__(
        self,
        worlds: Optional[List[World]] = None,
        relations: Optional[Dict[World, Set[World]]] = None,
        valuations: Optional[Dict[World, Set[Formula]]] = None,
    ) -> None:
        """Initializes a Kripke model with worlds, relations, and valuations.

        Args:
            worlds (Optional[List[World]], default=None): Initial list of worlds.
            relations (Optional[Dict[World, Set[World]]], default=None): Initial accessibility edges.
            valuations (Optional[Dict[World, Set[Formula]]], default=None): Initial truth assignments.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel
            >>> m = KripkeModel()
            >>> len(m.worlds)
            0
        """
        self.worlds = list(worlds) if worlds is not None else []
        self.relations = {w: set(targets) for w, targets in relations.items()} if relations is not None else {}
        self.valuations = {w: set(atoms) for w, atoms in valuations.items()} if valuations is not None else {}

    def add_world(self, world: World) -> None:
        """Adds a world to the model, ensuring reflexivity in the accessibility relation.

        Args:
            world (World): The world to add.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> m.add_world(World(0, "w0"))
            >>> len(m.worlds)
            1
        """
        if world not in self.worlds:
            self.worlds.append(world)
        if world not in self.relations:
            self.relations[world] = {world}
        else:
            self.relations[world].add(world)
        if world not in self.valuations:
            self.valuations[world] = set()

    def add_relation(self, source: World, target: World) -> None:
        """Adds an accessibility edge source <= target and maintains transitive closure.

        Args:
            source (World): The starting world.
            target (World): The accessible world.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> w0, w1 = World(0, "w0"), World(1, "w1")
            >>> m.add_world(w0)
            >>> m.add_world(w1)
            >>> m.add_relation(w0, w1)
            >>> m.is_accessible(w0, w1)
            True
        """
        self.add_world(source)
        self.add_world(target)
        self.relations[source].add(target)
        self._compute_transitive_closure()
        self._enforce_monotonicity()

    def _compute_transitive_closure(self) -> None:
        """Recomputes reflexive-transitive closure across all world relations."""
        for w in self.worlds:
            self.relations.setdefault(w, set()).add(w)

        changed = True
        while changed:
            changed = False
            for u in self.worlds:
                for v in list(self.relations.get(u, set())):
                    for w in self.relations.get(v, set()):
                        if w not in self.relations[u]:
                            self.relations[u].add(w)
                            changed = True

    def _enforce_monotonicity(self) -> None:
        """Enforces monotonicity: if u <= v then V(u) <= V(v)."""
        changed = True
        while changed:
            changed = False
            for u in self.worlds:
                for v in self.relations.get(u, set()):
                    if u != v:
                        for atom in self.valuations.get(u, set()):
                            if atom not in self.valuations.get(v, set()):
                                self.valuations.setdefault(v, set()).add(atom)
                                changed = True

    def add_valuation(self, world: World, formula: Formula) -> None:
        """Assigns truth to an atomic proposition at a world, propagating along accessible worlds.

        Args:
            world (World): World where formula is true.
            formula (Formula): Atomic formula to set true.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> w0 = World(0, "w0")
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> m.add_valuation(w0, p)
            >>> m.evaluate(p, w0)
            True
        """
        self.add_world(world)
        self.valuations[world].add(formula)
        for succ in self.accessible_worlds(world):
            self.valuations.setdefault(succ, set()).add(formula)

    def is_accessible(self, source: World, target: World) -> bool:
        """Tests whether target is reachable from source (source <= target).

        Args:
            source (World): Source world.
            target (World): Target world.

        Returns:
            bool: True if source <= target, False otherwise.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> w0 = World(0, "w0")
            >>> m.add_world(w0)
            >>> m.is_accessible(w0, w0)
            True
        """
        return target in self.relations.get(source, set())

    def accessible_worlds(self, world: World) -> Set[World]:
        """Returns the set of all worlds accessible from the given world.

        Args:
            world (World): Starting world.

        Returns:
            Set[World]: Set of accessible worlds {w' | world <= w'}.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> w0 = World(0, "w0")
            >>> m.add_world(w0)
            >>> len(m.accessible_worlds(w0))
            1
        """
        return set(self.relations.get(world, {world}))

    def evaluate(self, formula: Formula, world: World) -> bool:
        """Evaluates whether an intuitionistic formula is forced at a world: (M, world |= formula).

        Args:
            formula (Formula): The formula AST to evaluate.
            world (World): The evaluation world in W.

        Returns:
            bool: True if world forces formula, False otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> w0 = World(0, "w0")
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> m.evaluate(Implies(p, p), w0)
            True
        """
        if _is_falsum(formula):
            return False
        if _is_verum(formula):
            return True

        if _is_atomic(formula):
            return formula in self.valuations.get(world, set())

        if isinstance(formula, Not):
            return all(not self.evaluate(formula.operand, succ) for succ in self.accessible_worlds(world))

        if isinstance(formula, And):
            return self.evaluate(formula.left, world) and self.evaluate(formula.right, world)

        if isinstance(formula, Or):
            return self.evaluate(formula.left, world) or self.evaluate(formula.right, world)

        if isinstance(formula, Implies):
            for succ in self.accessible_worlds(world):
                if self.evaluate(formula.left, succ) and not self.evaluate(formula.right, succ):
                    return False
            return True

        if isinstance(formula, Iff):
            left_imp = Implies(left=formula.left, right=formula.right)
            right_imp = Implies(left=formula.right, right=formula.left)
            return self.evaluate(left_imp, world) and self.evaluate(right_imp, world)

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Kripke model structure to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary structure with worlds, relations, and valuations.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> m.add_world(World(0, "w0"))
            >>> "worlds" in m.to_dict()
            True
        """
        return {
            "worlds": [w.name for w in self.worlds],
            "relations": {
                w.name: sorted([succ.name for succ in self.relations.get(w, set())])
                for w in self.worlds
            },
            "valuations": {
                w.name: sorted([to_string(f) for f in self.valuations.get(w, set())])
                for w in self.worlds
            },
        }

    def to_string(self) -> str:
        """Formats the Kripke model as a readable multi-line description.

        Returns:
            str: Description of worlds, accessibility relation, and atomic valuations.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> m.add_world(World(0, "w0"))
            >>> "Kripke Model" in m.to_string()
            True
        """
        lines: List[str] = ["Kripke Model (W, <=, V):"]
        lines.append(f"  Worlds: {', '.join(w.name for w in self.worlds) if self.worlds else 'empty'}")
        lines.append("  Accessibility Relation (<=):")
        for w in self.worlds:
            succs = sorted([s.name for s in self.relations.get(w, set())])
            lines.append(f"    {w.name} <= {{{', '.join(succs)}}}")
        lines.append("  Valuations V(w):")
        for w in self.worlds:
            atoms = sorted([to_string(f) for f in self.valuations.get(w, set())])
            atoms_str = ", ".join(atoms) if atoms else "empty"
            lines.append(f"    V({w.name}) = {{{atoms_str}}}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Returns the default string representation of the model."""
        return self.to_string()


__all__ = [
    "World",
    "KripkeModel",
]
