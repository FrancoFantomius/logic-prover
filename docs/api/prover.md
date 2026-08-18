# API Reference: `prover`

# Module `logic_prover.prover.reconstruction`

Natural deduction proof reconstruction from resolution trace logs.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def reconstruct_proof(resolution_trace: List[ResolutionStep], original_target: Formula, premises: Optional[List[Formula]]) -> ProofDAG`

Converts a resolution refutation trace (proving ⊥ from premises ∧ ¬target) into a valid Natural Deduction ProofDAG for original_target.

Pipeline:
1. Map initial 'axiom' steps to ND premises.
2. Map initial 'negated_goal' step to assumption ¬original_target.
3. Convert resolution steps into ND inferences (Modus Ponens, Or Elimination, ResolutionTraceStep).
4. Derive contradiction ⊥ at empty clause root step.
5. Apply Double Negation Elimination / Proof by Contradiction to yield original_target as root.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `resolution_trace` | `List[ResolutionStep]` | Ordered list of ResolutionStep records from the prover. |
| `original_target` | `Formula` | The formula the prover was asked to prove. |
| `premises` | `Optional[List[Formula]]` | Optional list of premise Formulas used by the prover. |

**Returns:** `ProofDAG` — A simplified ProofDAG reconstructing the target's natural deduction proof.

### `def simplify_proof(proof: ProofDAG) -> ProofDAG`

Optimizes ProofDAG by: 1. Pruning dead/unreachable steps not leading to root_id. 2. Collapsing identity and redundant single-premise steps.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `proof` | `ProofDAG` | The ProofDAG to simplify. |

**Returns:** `ProofDAG` — A pruned ProofDAG containing only steps reachable from the root.


---
