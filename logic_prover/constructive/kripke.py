"""Kripke frames, possible worlds, and semantic models for Intuitionistic First-Order Logic.

This module provides Kripke semantics structures for intuitionistic logic
(Fitting 1969; Chagrov & Zakharyaschev 1997). In intuitionistic first-order Kripke semantics,
a model M = (W, <=, D, V) consists of a non-empty set of worlds W, a reflexive-transitive
preorder <=, expanding domain assignment D where u <= v implies D(u) <= D(v), and a monotone
valuation V where u <= v implies V(u) <= V(v).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Set

from logic_prover.core.ast import (
    Formula, Term, PredicateApp, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.parser import to_string
from logic_prover.core.substitutions import substitute_formula
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
    """A finite Kripke Model (W, <=, D, V) for Intuitionistic First-Order Logic (IQC).

    In intuitionistic Kripke semantics:
    - W is a non-empty set of possible worlds.
    - <= is a preorder (reflexive, transitive accessibility relation).
    - D maps each world w in W to a non-empty set of domain terms such that
      if w <= w' then D(w) <= D(w') (expanding domain monotonicity).
    - V maps each world w in W to a set of true atomic propositions such that
      if w <= w' then V(w) <= V(w') (monotonicity / persistence / heredity).

    Args:
        worlds (Optional[List[World]], default=None): List of worlds in the model.
        relations (Optional[Dict[World, Set[World]]], default=None): Accessibility map.
        valuations (Optional[Dict[World, Set[Formula]]], default=None): Atomic valuation map.
        domains (Optional[Dict[World, Set[Term]]], default=None): Per-world domain elements map.

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
    domains: Dict[World, Set[Term]]

    def __init__(
        self,
        worlds: Optional[List[World]] = None,
        relations: Optional[Dict[World, Set[World]]] = None,
        valuations: Optional[Dict[World, Set[Formula]]] = None,
        domains: Optional[Dict[World, Set[Term]]] = None,
    ) -> None:
        """Initializes a Kripke model with worlds, relations, valuations, and domains.

        Args:
            worlds (Optional[List[World]], default=None): Initial list of worlds.
            relations (Optional[Dict[World, Set[World]]], default=None): Initial accessibility edges.
            valuations (Optional[Dict[World, Set[Formula]]], default=None): Initial truth assignments.
            domains (Optional[Dict[World, Set[Term]]], default=None): Initial domain elements per world.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel
            >>> m = KripkeModel()
            >>> len(m.worlds)
            0
        """
        self.worlds = list(worlds) if worlds is not None else []
        self.relations = {w: set(targets) for w, targets in relations.items()} if relations is not None else {}
        self.valuations = {w: set(atoms) for w, atoms in valuations.items()} if valuations is not None else {}
        self.domains = {w: set(terms) for w, terms in domains.items()} if domains is not None else {}

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
        if world not in self.domains:
            self.domains[world] = set()

    def add_relation(self, source: World, target: World) -> None:
        """Adds an accessibility edge source <= target and maintains transitive closure and monotonicity.

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
        """Enforces valuation and domain monotonicity: if u <= v then V(u) <= V(v) and D(u) <= D(v)."""
        changed = True
        while changed:
            changed = False
            for u in self.worlds:
                for v in self.relations.get(u, set()):
                    if u != v:
                        # Valuation monotonicity
                        for atom in self.valuations.get(u, set()):
                            if atom not in self.valuations.get(v, set()):
                                self.valuations.setdefault(v, set()).add(atom)
                                changed = True
                        # Domain monotonicity
                        for term in self.domains.get(u, set()):
                            if term not in self.domains.get(v, set()):
                                self.domains.setdefault(v, set()).add(term)
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

    def add_domain_element(self, world: World, term: Term) -> None:
        """Adds a domain element term at world, propagating along accessible worlds.

        Args:
            world (World): World where domain element is added.
            term (Term): Ground term element to add to D(world).

        Example:
            >>> from logic_prover.core.ast import Constant
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> w0 = World(0, "w0")
            >>> c = Constant("c0")
            >>> m.add_domain_element(w0, c)
            >>> c in m.domains[w0]
            True
        """
        self.add_world(world)
        self.domains[world].add(term)
        for succ in self.accessible_worlds(world):
            self.domains.setdefault(succ, set()).add(term)

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
        """Evaluates whether an intuitionistic first-order formula is forced at a world: (M, world |= formula).

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

        if isinstance(formula, Forall):
            for succ in self.accessible_worlds(world):
                domain_elems = self.domains.get(succ, set())
                for t in domain_elems:
                    sub_f = substitute_formula(formula.body, {formula.variable: t})
                    if not self.evaluate(sub_f, succ):
                        return False
            return True

        if isinstance(formula, Exists):
            domain_elems = self.domains.get(world, set())
            for t in domain_elems:
                sub_f = substitute_formula(formula.body, {formula.variable: t})
                if self.evaluate(sub_f, world):
                    return True
            return False

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Kripke model structure to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary structure with worlds, relations, valuations, and domains.

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
            "domains": {
                w.name: sorted([to_string(t) for t in self.domains.get(w, set())])
                for w in self.worlds
            },
        }

    def to_string(self) -> str:
        """Formats the Kripke model as a readable multi-line description.

        Returns:
            str: Description of worlds, accessibility relation, atomic valuations, and domains.

        Example:
            >>> from logic_prover.constructive.kripke import KripkeModel, World
            >>> m = KripkeModel()
            >>> m.add_world(World(0, "w0"))
            >>> "Kripke Model" in m.to_string()
            True
        """
        lines: List[str] = ["Kripke Model (W, <=, D, V):"]
        lines.append(f"  Worlds: {', '.join(w.name for w in self.worlds) if self.worlds else 'empty'}")
        lines.append("  Accessibility Relation (<=):")
        for w in self.worlds:
            succs = sorted([s.name for s in self.relations.get(w, set())])
            lines.append(f"    {w.name} <= {{{', '.join(succs)}}}")
        lines.append("  Domains D(w):")
        for w in self.worlds:
            terms = sorted([to_string(t) for t in self.domains.get(w, set())])
            terms_str = ", ".join(terms) if terms else "empty"
            lines.append(f"    D({w.name}) = {{{terms_str}}}")
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

