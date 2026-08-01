# API Reference: `kb`

# Module `solver.kb.equality`

Equality axioms and congruence signature definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_equality_signature() -> Signature`

Returns signature declaring generic equality operations and sample symbols for schemata.

**Returns:** `Signature`

### `def get_equality_axioms() -> List[Tuple[str, Formula]]`

Returns fundamental equality axioms: reflexivity, symmetry, transitivity, and congruence schemata.

**Returns:** `List[Tuple[str, Formula]]`


---

# Module `solver.kb.functions`

Function theory axioms (injective, surjective, bijective, identity).

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_function_signature() -> Signature`

Returns signature declaring function concepts (apply, comp, id_func, is_injective, etc.).

**Returns:** `Signature`

### `def get_function_axioms() -> List[Tuple[str, Formula]]`

Returns function concept axioms: composition, injectivity, surjectivity, bijectivity, identity function.

**Returns:** `List[Tuple[str, Formula]]`


---

# Module `solver.kb.groups`

Group theory axioms (associativity, identity, inverse, commutativity).

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_group_signature() -> Signature`

Returns the signature for group theory symbols (op, inv, e).

**Returns:** `Signature`

### `def get_group_axioms() -> List[Tuple[str, Formula]]`

Returns group theory axioms: associativity, left/right identity, left/right inverse.

**Returns:** `List[Tuple[str, Formula]]`


---

# Module `solver.kb.logic`

First-Order Logic foundational axioms and tautologies.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_fol_signature() -> Signature`

Returns signature declaring sample predicate symbols for FOL schemata.

**Returns:** `Signature`

### `def get_fol_axioms() -> List[Tuple[str, Formula]]`

Returns First-Order Logic axioms: propositional schemata and quantifier laws.

**Returns:** `List[Tuple[str, Formula]]`


---

# Module `solver.kb.numbers`

Peano arithmetic axioms and natural number signature definitions.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_peano_signature() -> Signature`

Returns signature declaring Peano arithmetic symbols (zero, succ, add, mul, le, eq).

**Returns:** `Signature`

### `def get_peano_axioms() -> List[Tuple[str, Formula]]`

Returns Peano arithmetic axioms for natural numbers.

**Returns:** `List[Tuple[str, Formula]]`


---

# Module `solver.kb.orders`

Order theory axioms (partial orders, total orders, strict orders).

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_order_signature() -> Signature`

Returns the signature for order relations (le, lt, ge).

**Returns:** `Signature`

### `def get_partial_order_axioms() -> List[Tuple[str, Formula]]`

Returns partial order axioms: reflexivity, anti-symmetry, transitivity, strict order definition.

**Returns:** `List[Tuple[str, Formula]]`

### `def get_total_order_axioms() -> List[Tuple[str, Formula]]`

Returns total order axioms: partial order axioms + totality and trichotomy.

**Returns:** `List[Tuple[str, Formula]]`


---

# Module `solver.kb.relations`

Binary relation theory axioms (reflexivity, symmetry, transitivity, irreflexivity).

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_relation_signature() -> Signature`

Returns the signature declaring binary relation predicate R and EqRel.

**Returns:** `Signature`

### `def get_relation_axioms() -> List[Tuple[str, Formula]]`

Returns relation property axioms: reflexivity, symmetry, transitivity, anti-symmetry, irreflexivity, asymmetry.

**Returns:** `List[Tuple[str, Formula]]`


---

# Module `solver.kb.sets`

Naive set theory axioms (extensionality, subset, union, intersection, empty set).

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_set_signature() -> Signature`

Returns signature for minimal set theory symbols.

**Returns:** `Signature`

### `def get_set_theory_axioms() -> List[Tuple[str, Formula]]`

Returns minimal set theory axioms: extensionality, subset, empty set, union, inter, diff, singleton, powerset.

**Returns:** `List[Tuple[str, Formula]]`


---
