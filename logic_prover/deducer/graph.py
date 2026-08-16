"""Dependency graph data structure for formula dependency networks."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
import json

from logic_prover.core.ast import Formula
from logic_prover.core.parser import to_string
from logic_prover.prover.proof import ProofDAG


@dataclass
class DependencyGraph:
    """Represents a network-level graph of implication, dependency, and equivalence relationships among named formulas."""

    nodes: Dict[str, Formula] = field(default_factory=dict)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)

    # Internal adjacency structures for fast lookup
    _adj_out: Dict[str, Set[Tuple[str, str]]] = field(default_factory=dict, repr=False)
    _adj_in: Dict[str, Set[Tuple[str, str]]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """Ensures internal adjacency lookup maps are populated on initialization."""
        for name in self.nodes:
            if name not in self._adj_out:
                self._adj_out[name] = set()
            if name not in self._adj_in:
                self._adj_in[name] = set()
        for src, tgt, rel in self.edges:
            if src in self._adj_out:
                self._adj_out[src].add((tgt, rel))
            if tgt in self._adj_in:
                self._adj_in[tgt].add((source, rel)) if False else self._adj_in[tgt].add((src, rel))

    def add_node(self, name: str, formula: Formula) -> None:
        """Adds a named formula node to the graph.

        If a node with the same name exists with an identical formula, this operation is idempotent.
        If the formula differs for an existing name, raises ValueError.

        Args:
            name: Unique name for the node.
            formula: The Formula associated with the node.

        Raises:
            ValueError: If a node with the same name already holds a different formula.
        """
        if name in self.nodes:
            if self.nodes[name] != formula:
                raise ValueError(f"Node '{name}' already exists with a different formula.")
            return
        self.nodes[name] = formula
        if name not in self._adj_out:
            self._adj_out[name] = set()
        if name not in self._adj_in:
            self._adj_in[name] = set()

    def add_edge(self, source: str, target: str, relationship: str) -> None:
        """Adds a directed edge between source and target nodes with a specified relationship.

        Valid relationship strings: "implies", "equivalent", "depends".

        Args:
            source: Name of the source node.
            target: Name of the target node.
            relationship: One of 'implies', 'equivalent', or 'depends'.

        Raises:
            KeyError: If source or target node is not registered.
            ValueError: If relationship string is invalid.
        """
        valid_rels = {"implies", "equivalent", "depends"}
        if relationship not in valid_rels:
            raise ValueError(f"Invalid relationship '{relationship}'. Must be one of {valid_rels}.")
        if source not in self.nodes:
            raise KeyError(f"Source node '{source}' does not exist in graph.")
        if target not in self.nodes:
            raise KeyError(f"Target node '{target}' does not exist in graph.")

        edge = (source, target, relationship)
        if edge not in self.edges:
            self.edges.append(edge)
            self._adj_out[source].add((target, relationship))
            self._adj_in[target].add((source, relationship))

    def register_proof(self, proof: ProofDAG, theorem_name: str) -> None:
        """Incrementally updates the dependency graph from a completed proof DAG.

        Registers the conclusion (theorem_name) and adds directed "implies" edges
        from each premise in proof.premises to theorem_name.

        Args:
            proof: The completed ProofDAG whose premises feed the theorem.
            theorem_name: Name of the theorem node to register.
        """
        # Register conclusion
        self.add_node(theorem_name, proof.conclusion)

        # Ingest premises
        for idx, premise_formula in enumerate(proof.premises):
            premise_name = f"premise_{idx}"
            # Check if premise formula matches an existing node
            found_name = None
            for existing_name, existing_formula in self.nodes.items():
                if existing_formula == premise_formula:
                    found_name = existing_name
                    break

            if found_name is not None:
                premise_name = found_name
            else:
                if premise_name in self.nodes and self.nodes[premise_name] != premise_formula:
                    counter = 1
                    while f"premise_{idx}_{counter}" in self.nodes and self.nodes[f"premise_{idx}_{counter}"] != premise_formula:
                        counter += 1
                    premise_name = f"premise_{idx}_{counter}"

            self.add_node(premise_name, premise_formula)
            self.add_edge(premise_name, theorem_name, "implies")

    def predecessors(self, name: str) -> List[str]:
        """Returns a list of direct predecessor node names (nodes that point to `name`).

        Args:
            name: The node whose predecessors to return.

        Returns:
            Sorted list of direct predecessor names.

        Raises:
            KeyError: If the node does not exist in the graph.
        """
        if name not in self.nodes:
            raise KeyError(f"Node '{name}' does not exist in graph.")
        return sorted([src for src, _ in self._adj_in.get(name, set())])

    def successors(self, name: str) -> List[str]:
        """Returns a list of direct successor node names (nodes that `name` points to).

        Args:
            name: The node whose successors to return.

        Returns:
            Sorted list of direct successor names.

        Raises:
            KeyError: If the node does not exist in the graph.
        """
        if name not in self.nodes:
            raise KeyError(f"Node '{name}' does not exist in graph.")
        return sorted([tgt for tgt, _ in self._adj_out.get(name, set())])

    def transitive_closure(self, name: str) -> Set[str]:
        """Computes the set of all node names reachable from the given node via directed edges.

        Uses Breadth-First Search (BFS) to traverse outward dependencies.

        Args:
            name: The starting node name.

        Returns:
            Set of node names reachable from name (excluding name itself).

        Raises:
            KeyError: If the node does not exist in the graph.
        """
        if name not in self.nodes:
            raise KeyError(f"Node '{name}' does not exist in graph.")

        visited: Set[str] = set()
        queue: List[str] = [name]
        while queue:
            curr = queue.pop(0)
            for succ in self.successors(curr):
                if succ not in visited and succ != name:
                    visited.add(succ)
                    queue.append(succ)
        return visited

    def is_acyclic_modulo_equivalence(self) -> bool:
        """Returns True if the graph has no directed cycles other than those within "equivalent" components."""
        non_eq_edges = [(src, tgt) for src, tgt, rel in self.edges if rel != "equivalent"]
        adj: Dict[str, List[str]] = {node: [] for node in self.nodes}
        for src, tgt in non_eq_edges:
            adj[src].append(tgt)

        visited: Dict[str, int] = {node: 0 for node in self.nodes}  # 0=unvisited, 1=visiting, 2=visited

        def dfs(u: str) -> bool:
            """Recursively detects a cycle in the non-equivalence subgraph.

            Args:
                u: The node currently being visited.

            Returns:
                True if a cycle is found, False otherwise.
            """
            visited[u] = 1
            for v in adj.get(u, []):
                if visited[v] == 1:
                    return True  # Cycle found
                if visited[v] == 0:
                    if dfs(v):
                        return True
            visited[u] = 2
            return False

        for node in self.nodes:
            if visited[node] == 0:
                if dfs(node):
                    return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph into a dictionary suitable for JSON export and visualization."""
        return {
            "nodes": [
                {
                    "id": name,
                    "label": name,
                    "formula": to_string(formula)
                }
                for name, formula in self.nodes.items()
            ],
            "edges": [
                {
                    "source": src,
                    "target": tgt,
                    "relationship": rel
                }
                for src, tgt, rel in self.edges
            ]
        }
