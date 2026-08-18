# API Reference: `axioms`

# Module `logic_prover.axioms.analysis`

Real analysis, ordered fields, and metric space axioms, signatures, and Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_analysis_signature() -> Signature`

Constructs the signature for Real Analysis (ordered fields and metric spaces).

Registers constants 'real_zero', 'real_one', arithmetic functions 'real_add', 'real_mul',
'real_neg', 'real_inv', metric functions 'abs_val', 'dist', and order predicates 'le', 'lt', 'ge', 'gt'.

**Returns:** `Signature` — The initialized real analysis Signature instance.

### `def get_analysis_axioms() -> List[Tuple[str, Formula]]`

Generates the fundamental First-Order Axioms for Real Analysis.

Includes:
- Field operations (addition & multiplication assoc, comm, id, inv, distrib, non-triviality)
- Ordered field properties (reflexivity, antisymmetry, transitivity, totality, compatibility)
- Metric and absolute value properties (positivity, symmetry, triangle inequalities)

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for real analysis.


---

# Module `logic_prover.axioms.base`

Foundational Theory abstraction and global theory registry.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class Theory`

Represents a formal mathematical theory consisting of sorts, a signature, and a set of axioms.

#### Methods

##### `def get_signature(self) -> Signature`

Retrieves the logical signature of this theory.

**Returns:** `Signature` — The theory's logical signature.

##### `def get_axioms(self) -> List[Tuple[str, Formula]]`

Retrieves all axioms of this theory as a list of (name, formula) pairs.

**Returns:** `List[Tuple[str, Formula]]` — List containing (axiom_name, axiom_formula) tuples.

##### `def get_axioms_list(self) -> List[Formula]`

Retrieves the list of axiom formulas without their names, suitable as prover premises.

**Returns:** `List[Formula]` — The list of Formula instances corresponding to all axioms in the theory.

##### `def get_axiom(self, name: str) -> Optional[Formula]`

Retrieves a specific axiom formula by its registered name.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | The name identifier of the axiom to retrieve. |

**Returns:** `Optional[Formula]` — The Formula instance if found, None otherwise.

##### `def validate(self) -> List[ValidationError]`

Validates all axioms in this theory against the theory's signature.

**Returns:** `List[ValidationError]` — A list of validation errors found across all axioms (empty if valid).

##### `def create_prover(self, config: Optional[SolverConfig]) -> TheoremProver`

Instantiates a TheoremProver configured with this theory's logical signature.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `config` | `Optional[SolverConfig], optional` | Optional solver limits and configuration. Defaults to None. |

**Returns:** `TheoremProver` — A TheoremProver instance ready for proof search over this theory.

##### `def prove(self, target: Formula, premises: Optional[List[Formula]], include_theory_axioms: bool, max_steps: Optional[int], timeout_sec: Optional[float]) -> ProofDAG`

Attempts to prove a target formula within this theory, combining optional premises and theory axioms.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | The target goal formula to prove. |
| `premises` | `Optional[List[Formula]], optional` | Additional user-provided premise formulas. Defaults to None. |
| `include_theory_axioms` | `bool, optional` | Whether to automatically prepend all theory axioms as premises. Defaults to True. |
| `max_steps` | `Optional[int], optional` | Maximum resolution steps allowed. Defaults to None. |
| `timeout_sec` | `Optional[float], optional` | Timeout limit in seconds. Defaults to None. |

**Returns:** `ProofDAG` — A reconstructed natural deduction proof DAG of the target formula.

---

## Functions

### `def register_theory(theory: Theory) -> None`

Registers a Theory instance into the global theory registry.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `theory` | `Theory` | The Theory object to register. |

**Returns:** `None` — Does not return a value.

### `def get_theory(name: str) -> Optional[Theory]`

Retrieves a registered Theory by its name.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | The name identifier of the theory. |

**Returns:** `Optional[Theory]` — The registered Theory instance if found, None otherwise.

### `def list_theories() -> List[str]`

Returns a sorted list of all registered theory names.

**Returns:** `List[str]` — List of string names for all registered theories.

### `def get_all_theories() -> Dict[str, Theory]`

Returns a copy of the dictionary containing all registered theories.

**Returns:** `Dict[str, Theory]` — Mapping of theory names to their Theory instances.


---

# Module `logic_prover.axioms.boolean_algebra`

Boolean algebra axioms, signature, and Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_boolean_algebra_signature() -> Signature`

Constructs the signature declaring Boolean Algebra operations and bounds.

Registers constants 'bot', 'top', binary operations 'bmeet', 'bjoin', and unary complement 'bneg'.

**Returns:** `Signature` — The initialized Boolean Algebra Signature instance.

### `def get_boolean_algebra_axioms() -> List[Tuple[str, Formula]]`

Generates the First-Order Boolean Algebra axioms.

Includes:
- Commutativity and associativity of meet and join
- Distributivity of meet over join and join over meet
- Identity laws for top and bot
- Complementation laws
- De Morgan's dual laws

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for boolean algebra.


---

# Module `logic_prover.axioms.equality`

Equality axioms and congruence signature definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_equality_signature() -> Signature`

Constructs the signature declaring generic equality operations and symbols for congruence schemata.

Registers unary function 'f', binary function 'f_bin', and unary predicate 'P'.

**Returns:** `Signature` — The initialized equality Signature instance.

### `def get_equality_axioms() -> List[Tuple[str, Formula]]`

Generates the fundamental First-Order Logic equality axioms and congruence schemata.

Includes:
- eq_reflexive: ∀x. x = x
- eq_symmetric: ∀x, y. (x = y ⇒ y = x)
- eq_transitive: ∀x, y, z. ((x = y ∧ y = z) ⇒ x = z)
- eq_congruence_unary_func: ∀x, y. (x = y ⇒ f(x) = f(y))
- eq_congruence_binary_func: ∀x1, x2, y1, y2. ((x1 = y1 ∧ x2 = y2) ⇒ f_bin(x1, x2) = f_bin(y1, y2))
- eq_congruence_unary_pred: ∀x, y. ((x = y ∧ P(x)) ⇒ P(y))

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for equality theory.


---

# Module `logic_prover.axioms.functions`

Function theory axioms, signatures, and formal Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_function_signature() -> Signature`

Constructs the signature declaring function theory constants, operations, and predicates.

Registers binary functions 'apply' and 'comp', constant 'id_func', and unary
predicates 'is_injective', 'is_surjective', 'is_bijective'.

**Returns:** `Signature` — The initialized function theory Signature instance.

### `def get_function_axioms() -> List[Tuple[str, Formula]]`

Generates the fundamental First-Order Function Theory axioms.

Includes:
- func_well_defined: ∀f, x, y. (x = y ⇒ apply(f, x) = apply(f, y))
- func_comp_def: ∀f, g, x. apply(comp(f, g), x) = apply(f, apply(g, x))
- func_injective_def: ∀f. (is_injective(f) ⇔ ∀x, y. (apply(f, x) = apply(f, y) ⇒ x = y))
- func_surjective_def: ∀f. (is_surjective(f) ⇔ ∀z. ∃x. apply(f, x) = z)
- func_bijective_def: ∀f. (is_bijective(f) ⇔ (is_injective(f) ∧ is_surjective(f)))
- func_id_def: ∀x. apply(id_func, x) = x

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for function theory.


---

# Module `logic_prover.axioms.group_theory`

Group theory axioms, signatures, and formal Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_group_signature() -> Signature`

Constructs the logical signature for First-Order Group Theory.

Registers constant identity 'e', binary operation 'op', and unary inverse 'inv'
over sort GroupElem.

**Returns:** `Signature` — The initialized group theory Signature instance.

### `def get_group_theory_signature() -> Signature`

Alias for get_group_signature constructing the group theory signature.

**Returns:** `Signature` — The initialized group theory Signature instance.

### `def get_group_axioms() -> List[Tuple[str, Formula]]`

Generates the fundamental First-Order Group Theory axioms.

Axioms:
- group_assoc: ∀x, y, z. op(op(x, y), z) = op(x, op(y, z))
- group_identity_left: ∀x. op(e, x) = x
- group_identity_right: ∀x. op(x, e) = x
- group_inverse_left: ∀x. op(inv(x), x) = e
- group_inverse_right: ∀x. op(x, inv(x)) = e

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for group theory.

### `def get_abelian_group_axioms() -> List[Tuple[str, Formula]]`

Generates the Abelian (Commutative) Group Theory axioms.

Extends basic group axioms with commutativity:
- group_commutative: ∀x, y. op(x, y) = op(y, x)

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for abelian groups.


---

# Module `logic_prover.axioms.linear_algebra`

Linear algebra, vector spaces, and inner product spaces axioms, signatures, and Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_linear_algebra_signature() -> Signature`

Constructs the signature for Linear Algebra (vector spaces and inner products).

Registers sorts Vector and Scalar, constants 'vzero', 'szero', 'sone', vector operations
'vadd', 'vneg', 'smul_v', scalar operations 'sadd', 'smul', 'sneg', inner product 'dot',
'norm_sq', and predicate 'orthogonal'.

**Returns:** `Signature` — The initialized linear algebra Signature instance.

### `def get_linear_algebra_axioms() -> List[Tuple[str, Formula]]`

Generates the fundamental First-Order Axioms of Linear Algebra.

Includes:
- Vector space abelian group axioms (vadd assoc, comm, identity vzero, inverse vneg)
- Scalar multiplication axioms (associativity, identity sone, vector/scalar distributivity)
- Inner product axioms (symmetry, bilinearity, zero vector dot product, orthogonality)

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for linear algebra.


---

# Module `logic_prover.axioms.logic`

First-Order Logic foundational axioms and tautologies.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_fol_signature() -> Signature`

Constructs the signature declaring standard unary predicate symbols 'P' and 'Q' for FOL schemata.

**Returns:** `Signature` — The initialized first-order logic Signature instance.

### `def get_fol_axioms() -> List[Tuple[str, Formula]]`

Generates the foundational First-Order Logic propositional and quantifier axioms.

Includes:
- prop_impl_self: ∀x. P(x) ⇒ P(x)
- prop_and_elim_left: ∀x. (P(x) ∧ Q(x)) ⇒ P(x)
- prop_and_elim_right: ∀x. (P(x) ∧ Q(x)) ⇒ Q(x)
- prop_or_intro_left: ∀x. P(x) ⇒ (P(x) ∨ Q(x))
- prop_double_negation: ∀x. ¬¬P(x) ⇒ P(x)
- quant_forall_elim: ∀x. P(x) ⇒ P(x)
- quant_exists_intro: ∀x. P(x) ⇒ ∃y. P(y)
- quant_de_morgan_1: ∀x. (¬∃y. P(y) ⇔ ∀y. ¬P(y))

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs.


---

# Module `logic_prover.axioms.order_theory`

Order theory and lattice axioms, signatures, and Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_order_signature() -> Signature`

Constructs the signature declaring order relation predicates and lattice operations.

Registers predicates 'le', 'lt', 'ge' and binary lattice operations 'meet', 'join'.

**Returns:** `Signature` — The initialized order theory Signature instance.

### `def get_partial_order_axioms() -> List[Tuple[str, Formula]]`

Generates the fundamental Partial Order theory axioms.

Includes:
- po_reflexive: ∀x. x ≤ x
- po_antisymmetric: ∀x, y. ((x ≤ y ∧ y ≤ x) ⇒ x = y)
- po_transitive: ∀x, y, z. ((x ≤ y ∧ y ≤ z) ⇒ x ≤ z)
- po_lt_def: ∀x, y. (x < y ⇔ (x ≤ y ∧ ¬(x = y)))

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for partial orders.

### `def get_total_order_axioms() -> List[Tuple[str, Formula]]`

Generates Total Order axioms combining partial order axioms with totality and trichotomy.

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for total orders.

### `def get_lattice_axioms() -> List[Tuple[str, Formula]]`

Generates the algebraic Lattice Theory axioms (meet, join, commutativity, associativity, absorption).

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for lattices.


---

# Module `logic_prover.axioms.peano`

Peano arithmetic axioms, signature, and formal Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_peano_signature() -> Signature`

Constructs the logical signature declaring Peano arithmetic constants, functions, and relations.

Registers constant 'zero', unary function 'succ', binary functions 'add' and 'mul',
and binary relations 'le' and 'eq'.

**Returns:** `Signature` — The initialized Peano arithmetic Signature instance.

### `def get_peano_axioms() -> List[Tuple[str, Formula]]`

Generates the First-Order Peano arithmetic axioms for natural numbers.

Axioms:
- peano_zero_not_succ: ∀n:Nat. ¬(S(n) = 0)
- peano_succ_injective: ∀m, n:Nat. (S(m) = S(n) ⇒ m = n)
- peano_add_zero: ∀n:Nat. n + 0 = n
- peano_add_succ: ∀m, n:Nat. m + S(n) = S(m + n)
- peano_mul_zero: ∀n:Nat. n * 0 = 0
- peano_mul_succ: ∀m, n:Nat. m * S(n) = (m * n) + m
- peano_le_def: ∀m, n:Nat. (m ≤ n ⇔ ∃k. m + k = n)

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for Peano arithmetic.


---

# Module `logic_prover.axioms.relations`

Binary relation theory axioms, signatures, and Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_relation_signature() -> Signature`

Constructs the signature declaring binary relation predicates 'R' and 'EqRel' over RelElem.

**Returns:** `Signature` — The initialized binary relation Signature instance.

### `def get_relation_axioms() -> List[Tuple[str, Formula]]`

Generates the fundamental binary relation property axioms.

Includes:
- rel_reflexive: ∀x. R(x, x)
- rel_symmetric: ∀x, y. (R(x, y) ⇒ R(y, x))
- rel_transitive: ∀x, y, z. ((R(x, y) ∧ R(y, z)) ⇒ R(x, z))
- rel_antisymmetric: ∀x, y. ((R(x, y) ∧ R(y, x)) ⇒ x = y)
- rel_irreflexive: ∀x. ¬R(x, x)
- rel_asymmetric: ∀x, y. (R(x, y) ⇒ ¬R(y, x))

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for relation properties.

### `def get_equivalence_relation_axioms() -> List[Tuple[str, Formula]]`

Generates the Equivalence Relation axioms (reflexivity, symmetry, transitivity).

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for equivalence relations.


---

# Module `logic_prover.axioms.ring_theory`

Ring and field theory axioms, signatures, and Theory definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_ring_signature() -> Signature`

Constructs the signature for algebraic Ring and Field theories.

Registers constants 'rzero', 'rone', addition 'radd', negation 'rneg',
multiplication 'rmul', and inverse 'rinv'.

**Returns:** `Signature` — The initialized ring theory Signature instance.

### `def get_ring_axioms() -> List[Tuple[str, Formula]]`

Generates the fundamental First-Order Axioms for a Ring with unity.

Includes:
- Abelian group for addition (assoc, comm, zero, additive inverse)
- Monoid for multiplication (assoc, left/right unity)
- Distributivity (left and right)

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for ring theory.

### `def get_field_axioms() -> List[Tuple[str, Formula]]`

Generates the Field Theory axioms extending commutative ring axioms with non-triviality and multiplicative inverse.

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for field theory.


---

# Module `logic_prover.axioms.zfc`

Zermelo-Fraenkel Set Theory with Choice (ZFC) axioms, signature, and Theory definition.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_zfc_signature() -> Signature`

Constructs the signature declaring ZFC axiomatic set theory symbols.

Registers sort constructor 'Set', binary relations 'in_set', 'subset',
constant 'empty_set', and operations 'union', 'inter', 'diff', 'singleton',
'pair', 'powerset', and 'choice'.

**Returns:** `Signature` — The initialized ZFC Set Theory Signature instance.

### `def get_set_signature() -> Signature`

Constructs signature for set theory.

**Returns:** `Signature` — The initialized set theory Signature instance.

### `def get_zfc_axioms() -> List[Tuple[str, Formula]]`

Generates the foundational First-Order Axioms of ZFC Set Theory.

Axioms:
- zfc_extensionality: ∀A, B. (A = B ⇔ ∀x. (x ∈ A ⇔ x ∈ B))
- zfc_subset_def: ∀A, B. (A ⊆ B ⇔ ∀x. (x ∈ A ⇒ x ∈ B))
- zfc_empty_set: ∀x. ¬(x ∈ ∅)
- zfc_pairing: ∀x, y, z. (z ∈ pair(x, y) ⇔ (z = x ∨ z = y))
- zfc_singleton: ∀x, y. (y ∈ singleton(x) ⇔ y = x)
- zfc_union_def: ∀A, B, x. (x ∈ (A ∪ B) ⇔ (x ∈ A ∨ x ∈ B))
- zfc_inter_def: ∀A, B, x. (x ∈ (A ∩ B) ⇔ (x ∈ A ∧ x ∈ B))
- zfc_diff_def: ∀A, B, x. (x ∈ (A \ B) ⇔ (x ∈ A ∧ ¬(x ∈ B)))
- zfc_powerset_def: ∀A, B. (B ∈ 𝒫(A) ⇔ B ⊆ A)
- zfc_choice_axiom: ∀A. (¬(A = ∅) ⇒ choice(A) ∈ A)

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for ZFC set theory.

### `def get_set_theory_axioms() -> List[Tuple[str, Formula]]`

Generates foundational Set Theory axioms.

**Returns:** `List[Tuple[str, Formula]]` — List of (axiom_name, formula) pairs for set theory.


---
