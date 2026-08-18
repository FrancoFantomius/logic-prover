# API Reference: `deducer`

# Module `logic_prover.deducer.analyzer`

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
