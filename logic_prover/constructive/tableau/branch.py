"""Branch state and frame management for intuitionistic semantic tableaux."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Set

from logic_prover.core.ast import Formula, Term, Equality
from logic_prover.constructive.kripke import World


@dataclass
class _BranchState:
    """Internal container for the state of a single tableau branch.

    Args:
        worlds (List[World], default_factory=list): List of worlds active in this branch.
        relations (Dict[World, Set[World]], default_factory=dict): Accessibility relation edges.
        t_formulas (Dict[World, Set[Formula]], default_factory=dict): Signed true formulas per world.
        f_formulas (Dict[World, Set[Formula]], default_factory=dict): Signed false formulas per world.
        domains (Dict[World, Set[Term]], default_factory=dict): Per-world domain ground terms.
        equalities (Dict[World, Set[Equality]], default_factory=dict): Per-world positive equalities.
        applied_rules (Set[Tuple[Any, ...]], default_factory=set): Set of rule signature tuples already applied.

    Example:
        >>> from logic_prover.constructive.kripke import World
        >>> from logic_prover.constructive.tableau.branch import _BranchState
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
    domains: Dict[World, Set[Term]] = field(default_factory=dict)
    equalities: Dict[World, Set[Equality]] = field(default_factory=dict)
    applied_rules: Set[Tuple[Any, ...]] = field(default_factory=set)

    def copy(self) -> _BranchState:
        """Creates an independent deep copy of the branch state.

        Returns:
            _BranchState: Cloned branch state.

        Example:
            >>> from logic_prover.constructive.tableau.branch import _BranchState
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
            domains={w: set(terms) for w, terms in self.domains.items()},
            equalities={w: set(eqs) for w, eqs in self.equalities.items()},
            applied_rules=set(self.applied_rules),
        )

    def add_world(self, world: World) -> None:
        """Registers a world in this branch state ensuring reflexivity.

        Args:
            world (World): The world node to register.

        Returns:
            None: Modifies branch state in-place.

        Example:
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau.branch import _BranchState
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
        self.domains.setdefault(world, set())
        self.equalities.setdefault(world, set())

    def add_relation(self, source: World, target: World) -> None:
        """Adds accessibility relation source <= target with transitive closure and monotonicity.

        Args:
            source (World): Source world node.
            target (World): Target world node.

        Returns:
            None: Modifies branch state in-place.

        Example:
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau.branch import _BranchState
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

        # Propagate T-formulas, domains, and equalities from predecessors to target
        for u in self.worlds:
            if target in self.relations.get(u, set()) and u != target:
                for f in self.t_formulas.get(u, set()):
                    self.t_formulas[target].add(f)
                for t in self.domains.get(u, set()):
                    self.domains[target].add(t)
                for eq in self.equalities.get(u, set()):
                    self.equalities[target].add(eq)

    def add_t_formula(self, world: World, formula: Formula) -> None:
        """Adds a true formula at world and propagates along accessibility relation.

        Args:
            world (World): World node where formula is asserted true.
            formula (Formula): Formula AST asserted true.

        Returns:
            None: Modifies branch state in-place.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau.branch import _BranchState
            >>> s = _BranchState()
            >>> w0 = World(0, "w0")
            >>> p = PredicateApp("P", 0, ())
            >>> s.add_t_formula(w0, p)
            >>> p in s.t_formulas[w0]
            True
        """
        self.add_world(world)
        self.t_formulas[world].add(formula)
        if isinstance(formula, Equality):
            self.add_equality(world, formula)
        for succ in self.relations.get(world, set()):
            self.t_formulas.setdefault(succ, set()).add(formula)

    def add_f_formula(self, world: World, formula: Formula) -> None:
        """Adds a false formula at world.

        Args:
            world (World): World node where formula is asserted false.
            formula (Formula): Formula AST asserted false.

        Returns:
            None: Modifies branch state in-place.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau.branch import _BranchState
            >>> s = _BranchState()
            >>> w0 = World(0, "w0")
            >>> p = PredicateApp("P", 0, ())
            >>> s.add_f_formula(w0, p)
            >>> p in s.f_formulas[w0]
            True
        """
        self.add_world(world)
        self.f_formulas[world].add(formula)

    def add_domain_element(self, world: World, term: Term) -> None:
        """Adds a domain ground term at world and propagates along accessibility relations.

        Args:
            world (World): World node where domain element is added.
            term (Term): Ground term added to D(world).

        Returns:
            None: Modifies branch state in-place.

        Example:
            >>> from logic_prover.core.ast import Constant
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau.branch import _BranchState
            >>> s = _BranchState()
            >>> w0 = World(0, "w0")
            >>> c = Constant("c0")
            >>> s.add_domain_element(w0, c)
            >>> c in s.domains[w0]
            True
        """
        self.add_world(world)
        self.domains[world].add(term)
        for succ in self.relations.get(world, set()):
            self.domains.setdefault(succ, set()).add(term)

    def add_equality(self, world: World, eq: Equality) -> None:
        """Adds a positive equality assertion at world and propagates along accessibility relations.

        Args:
            world (World): World node where equality holds.
            eq (Equality): Equality AST asserting term equivalence.

        Returns:
            None: Modifies branch state in-place.

        Example:
            >>> from logic_prover.core.ast import Constant, Equality
            >>> from logic_prover.constructive.kripke import World
            >>> from logic_prover.constructive.tableau.branch import _BranchState
            >>> s = _BranchState()
            >>> w0 = World(0, "w0")
            >>> eq = Equality(Constant("a"), Constant("b"))
            >>> s.add_equality(w0, eq)
            >>> eq in s.equalities[w0]
            True
        """
        self.add_world(world)
        self.equalities[world].add(eq)
        for succ in self.relations.get(world, set()):
            self.equalities.setdefault(succ, set()).add(eq)


__all__ = ["_BranchState"]
