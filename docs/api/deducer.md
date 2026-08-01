# API Reference: `deducer`

# Module `solver.deducer.analyzer`

Network dependency analyzer and minimal hypothesis deduction algorithms.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def analyze_dependencies(formulas: List[Tuple[str, Formula]], prover: TheoremProver, pairwise: bool) -> DependencyGraph`

Builds a DependencyGraph across a collection of named formulas.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formulas` | `List[Tuple[str, Formula]]` | List of (name, formula) tuples. |
| `prover` | `TheoremProver` | TheoremProver instance configured with timeout and search settings. |
| `pairwise` | `bool` | If True, attempts all O(n^2) pairwise implication proofs. If False (default), builds graph incrementally from existing node formulas. |

**Returns:** `DependencyGraph` — DependencyGraph populated with nodes and proved implication/equivalence edges.

### `def find_minimal_hypotheses(target: Formula, available_hypotheses: List[Formula], prover: TheoremProver) -> List[Formula]`

Extracts a minimal sufficient subset of hypotheses for proving the target formula.

Uses a greedy elimination algorithm: tests whether target remains provable when removing
each hypothesis one by one. If provable without h, h is discarded.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | Target conclusion formula. |
| `available_hypotheses` | `List[Formula]` | Initial candidate list of hypothesis formulas. |
| `prover` | `TheoremProver` | TheoremProver instance. |

**Returns:** `List[Formula]` — A minimal subset of hypotheses sufficient to prove target.

**Raises:**
- `ValueError`: If target is not provable from available_hypotheses.

### `def detect_redundant_hypotheses(hypotheses: List[Formula], target: Formula, prover: TheoremProver) -> List[Formula]`

Identifies all redundant hypotheses in a premise set for a target formula.

A hypothesis h is redundant if (hypotheses \ {h}) is sufficient to prove target.
Unlike find_minimal_hypotheses (which returns a single minimal subset), this function
tests each hypothesis independently against the full remaining set.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `hypotheses` | `List[Formula]` | Candidate list of hypothesis formulas. |
| `target` | `Formula` | Target conclusion formula. |
| `prover` | `TheoremProver` | TheoremProver instance. |

**Returns:** `List[Formula]` — List of hypotheses that can be individually removed without losing provability.

**Raises:**
- `ValueError`: If target is not provable from hypotheses.

### `def compute_equivalence_classes(formulas: List[Tuple[str, Formula]], prover: TheoremProver) -> List[Set[str]]`

Groups formula names into logical equivalence classes where formulas mutually imply each other (A <=> B).

Fast-paths syntactic alpha-equivalence via canonicalize_bound_variables, then invokes
bidirectional prover calls for remaining pairs.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formulas` | `List[Tuple[str, Formula]]` | List of (name, formula) tuples. |
| `prover` | `TheoremProver` | TheoremProver instance. |

**Returns:** `List[Set[str]]` — List of sets of formula names, where each set contains mutually equivalent formulas.


---

# Module `solver.deducer.graph`

Dependency graph data structure for formula dependency networks.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class DependencyGraph`

Represents a network-level graph of implication, dependency, and equivalence relationships among named formulas.

#### Methods

##### `def add_node(self, name: str, formula: Formula) -> None`

Adds a named formula node to the graph.

**Returns:** `None`

##### `def add_edge(self, source: str, target: str, relationship: str) -> None`

Adds a directed edge between source and target nodes with a specified relationship.

**Returns:** `None`

##### `def register_proof(self, proof: ProofDAG, theorem_name: str) -> None`

Incrementally updates the dependency graph from a completed proof DAG.

**Returns:** `None`

##### `def predecessors(self, name: str) -> List[str]`

Returns a list of direct predecessor node names (nodes that point to `name`).

**Returns:** `List[str]`

##### `def successors(self, name: str) -> List[str]`

Returns a list of direct successor node names (nodes that `name` points to).

**Returns:** `List[str]`

##### `def transitive_closure(self, name: str) -> Set[str]`

Computes the set of all node names reachable from the given node via directed edges.

**Returns:** `Set[str]`

##### `def is_acyclic_modulo_equivalence(self) -> bool`

Returns True if the graph has no directed cycles other than those within "equivalent" components.

**Returns:** `bool`

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the graph into a dictionary suitable for JSON export and visualization.

**Returns:** `Dict[str, Any]`


---
