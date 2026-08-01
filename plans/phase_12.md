# Phase 12 — Extended Knowledge Base Implementation Plan

> **Phase Goal**: Extend the library's axiom library beyond core logic and Peano arithmetic to cover fundamental algebraic and set-theoretic structures: Group Theory, Binary Relations, Partial and Total Orders, Minimal Set Theory, and Function Concepts. Verify that all axioms are well-sorted, parseable, valid in the Signature, and that the resolution prover can derive non-trivial theorems within each domain.

---

## 1. Overview & Architecture Strategy

Phase 12 expands the formal domain knowledge of the `solver` library by providing rich, reusable axiom modules for higher mathematical domains. Building upon the core logic and arithmetic introduced in Phase 6, and leveraging the Second-Order Logic (SOL) extensions from Phase 11, Phase 12 equips the solver with formalizations of:

1. **Group Theory** (`solver/kb/groups.py`): Monoid and group structures with binary operation, identity element, and inverse operation over `GroupElem` sort.
2. **Binary Relations** (`solver/kb/relations.py`): Properties of relations (reflexivity, symmetry, transitivity, anti-symmetry, irreflexivity, asymmetry) and equivalence relation definitions over `RelElem` sort.
3. **Order Theory** (`solver/kb/orders.py`): Non-strict and strict partial orders, total orders, trichotomy, and duality properties over `OrderElem` sort.
4. **Minimal Set Theory** (`solver/kb/sets.py`): Membership ($\in$), subset ($\subseteq$), union ($\cup$), intersection ($\cap$), set difference ($\setminus$), empty set ($\emptyset$), powerset ($\mathcal{P}$), and singleton sets over parameterized sort `Set(Elem)`.
5. **Function Concepts** (`solver/kb/functions.py`): Function application, function composition, domain/codomain restrictions, injectivity, surjectivity, and bijectivity over domain `Dom`, codomain `Codom`, and function representation sorts.

Each module exposes two standard builder functions:
- `get_<domain>_signature() -> Signature`: Declares all sorts, constants, function symbols, and predicate symbols needed for the domain.
- `get_<domain>_axioms() -> List[Tuple[str, Formula]]`: Returns a list of `(axiom_name, axiom_formula)` pairs, fully constructed as validated AST nodes.

The aggregated knowledge base in `solver/kb/__init__.py` is updated to include all extended domains alongside the foundational equality, logic, and Peano arithmetic modules.

---

## 2. Prerequisites

Before beginning Phase 12, the following phases must be fully implemented and verified:

1. **Phase 1 — AST & Sort System** (`solver/core/ast.py`, `solver/core/sorts.py`): `Sort`, `PrimitiveSort`, `ParameterizedSort`, `Term`, `Formula`, variable indexing, and canonical bound variable renaming.
2. **Phase 2 — Signature & Validator** (`solver/core/signature.py`, `solver/core/validator.py`): `Signature`, symbol lookup, and AST well-formedness validation.
3. **Phase 3 — Visitor Framework & Parser** (`solver/core/parser.py`): String parsing and formatting.
4. **Phase 4 — Substitution & Unification** (`solver/core/substitutions.py`): First-order unification and capture-avoiding substitution.
5. **Phase 6 — Foundational Knowledge Base & Database** (`solver/kb/`, `solver/core/database.py`): `KnowledgeDatabase` storage, axiom registration, and SQLite indexing.
6. **Phase 7 — Prover Engine** (`solver/prover/`): `TheoremProver`, resolution engine, Skolemization, and `ProofDAG` reconstruction.
7. **Phase 11 — Second-Order Logic Extension** (`solver/sol/`): Higher-order patterns and comprehension schema (used for set theory axioms).

---

## 3. Files to Create / Modify

| File Path | Action | Description |
| :--- | :--- | :--- |
| `solver/kb/groups.py` | Create | Group theory signature and axioms (closure, associativity, identity, inverse) |
| `solver/kb/relations.py` | Create | Relation signature and axioms (reflexivity, symmetry, transitivity, anti-symmetry, irreflexivity) |
| `solver/kb/orders.py` | Create | Order theory signature and axioms (partial order, total order, strict order, trichotomy) |
| `solver/kb/sets.py` | Create | Set theory signature and axioms (extensionality, membership, subset, union, inter, diff, empty, powerset) |
| `solver/kb/functions.py` | Create | Function concepts signature and axioms (composition, injectivity, surjectivity, bijectivity, identity) |
| `solver/kb/__init__.py` | Modify | Update package exports to aggregate extended signatures and axiom collections |
| `tests/test_extended_kb.py` | Create | Comprehensive unit tests for AST validation, database registration, and prover theorem derivations across all extended domains |

---

## 4. Detailed Implementation Guide

### 4.1 `solver/kb/groups.py` — Group Theory Axioms

#### 4.1.1 Overview & Sorts
Group theory operates over an atomic sort `GroupElem = PrimitiveSort("GroupElem")`.
The signature declares:
- Constant `e`: identity element of sort `GroupElem`.
- Function `op`: binary group operation `(GroupElem, GroupElem) -> GroupElem`.
- Function `inv`: unary inverse operation `GroupElem -> GroupElem`.

#### 4.1.2 Module API Signatures
```python
from typing import List, Tuple
from solver.core.ast import Formula, Variable, Constant, FunctionApp, Equality, Forall, Implies, And
from solver.core.sorts import PrimitiveSort, Sort
from solver.core.signature import Signature

GroupElem: PrimitiveSort = PrimitiveSort("GroupElem")

def get_group_signature() -> Signature:
    """Returns the signature for group theory symbols (op, inv, e)."""
    ...

def get_group_axioms() -> List[Tuple[str, Formula]]:
    """Returns group theory axioms: associativity, left/right identity, left/right inverse."""
    ...
```

#### 4.1.3 Axiom Definitions

1. `group_assoc`: $\forall x \forall y \forall z, \text{op}(\text{op}(x, y), z) = \text{op}(x, \text{op}(y, z))$
   ```python
   Forall(v0, Forall(v1, Forall(v2, Equality(
       FunctionApp("op", 2, (FunctionApp("op", 2, (v0, v1), GroupElem), v2), GroupElem),
       FunctionApp("op", 2, (v0, FunctionApp("op", 2, (v1, v2), GroupElem)), GroupElem)
   ))))
   ```
2. `group_identity_left`: $\forall x, \text{op}(e, x) = x$
3. `group_identity_right`: $\forall x, \text{op}(x, e) = x$
4. `group_inverse_left`: $\forall x, \text{op}(\text{inv}(x), x) = e$
5. `group_inverse_right`: $\forall x, \text{op}(x, \text{inv}(x)) = e$

#### 4.1.4 Example Provable Theorems
- **Involution of Inverse** (`group_inv_inv`): $\forall x : \text{GroupElem}, \text{inv}(\text{inv}(x)) = x$
- **Left Cancellation Law** (`group_left_cancel`): $\forall a \forall x \forall y, (\text{op}(a, x) = \text{op}(a, y) \implies x = y)$
- **Uniqueness of Identity** (`group_unique_identity`): $\forall i, (\forall x, \text{op}(i, x) = x) \implies i = e$

---

### 4.2 `solver/kb/relations.py` — Relation Axioms

#### 4.2.1 Overview & Sorts
Relation theory operates over individual elements of sort `RelElem = PrimitiveSort("RelElem")`.
The signature declares:
- Predicate `R`: generic binary relation `(RelElem, RelElem)`.
- Predicate `EqRel`: equivalence predicate representing binary relation `(RelElem, RelElem)`.

#### 4.2.2 Module API Signatures
```python
from typing import List, Tuple
from solver.core.ast import Formula, Variable, PredicateApp, Equality, Forall, Implies, And, Or, Not, Iff
from solver.core.sorts import PrimitiveSort
from solver.core.signature import Signature

RelElem: PrimitiveSort = PrimitiveSort("RelElem")

def get_relation_signature() -> Signature:
    """Returns the signature declaring binary relation predicate R."""
    ...

def get_relation_axioms() -> List[Tuple[str, Formula]]:
    """Returns relation property axioms: reflexivity, symmetry, transitivity, anti-symmetry, irreflexivity, asymmetry."""
    ...
```

#### 4.2.3 Axiom Definitions

1. `rel_reflexive`: $\forall x, R(x, x)$
2. `rel_symmetric`: $\forall x \forall y, (R(x, y) \implies R(y, x))$
3. `rel_transitive`: $\forall x \forall y \forall z, ((R(x, y) \land R(y, z)) \implies R(x, z))$
4. `rel_antisymmetric`: $\forall x \forall y, ((R(x, y) \land R(y, x)) \implies x = y)$
5. `rel_irreflexive`: $\forall x, \neg R(x, x)$
6. `rel_asymmetric`: $\forall x \forall y, (R(x, y) \implies \neg R(y, x))$

#### 4.2.4 Example Provable Theorems
- **Irreflexive + Transitive implies Asymmetric** (`rel_irref_trans_implies_asymm`):
  Premises: `rel_irreflexive`, `rel_transitive`.
  Target: $\forall x \forall y, (R(x, y) \implies \neg R(y, x))$
- **Symmetric + Transitive implies Reflexive on Related Domain** (`rel_symm_trans_ref_domain`):
  Premises: `rel_symmetric`, `rel_transitive`.
  Target: $\forall x \forall y, (R(x, y) \implies R(x, x))$

---

### 4.3 `solver/kb/orders.py` — Partial and Total Order Axioms

#### 4.3.1 Overview & Sorts
Order theory operates over sort `OrderElem = PrimitiveSort("OrderElem")`.
The signature declares:
- Predicate `le`: non-strict order relation $\le$ `(OrderElem, OrderElem)`.
- Predicate `lt`: strict order relation $<$ `(OrderElem, OrderElem)`.
- Predicate `ge`: converse relation $\ge$ `(OrderElem, OrderElem)`.

#### 4.3.2 Module API Signatures
```python
from typing import List, Tuple
from solver.core.ast import Formula, Variable, PredicateApp, Equality, Forall, Implies, And, Or, Not, Iff
from solver.core.sorts import PrimitiveSort
from solver.core.signature import Signature

OrderElem: PrimitiveSort = PrimitiveSort("OrderElem")

def get_order_signature() -> Signature:
    """Returns the signature for order relations (le, lt, ge)."""
    ...

def get_partial_order_axioms() -> List[Tuple[str, Formula]]:
    """Returns partial order axioms: reflexivity, anti-symmetry, transitivity, strict order definition."""
    ...

def get_total_order_axioms() -> List[Tuple[str, Formula]]:
    """Returns total order axioms: partial order axioms + totality (or trichotomy)."""
    ...
```

#### 4.3.3 Axiom Definitions

**Partial Order Axioms (`get_partial_order_axioms`):**
1. `po_reflexive`: $\forall x, \text{le}(x, x)$
2. `po_antisymmetric`: $\forall x \forall y, ((\text{le}(x, y) \land \text{le}(y, x)) \implies x = y)$
3. `po_transitive`: $\forall x \forall y \forall z, ((\text{le}(x, y) \land \text{le}(y, z)) \implies \text{le}(x, z))$
4. `po_lt_def`: $\forall x \forall y, (\text{lt}(x, y) \iff (\text{le}(x, y) \land \neg(x = y)))$

**Total Order Axioms (`get_total_order_axioms`):**
Includes all partial order axioms plus:
5. `to_totality`: $\forall x \forall y, (\text{le}(x, y) \lor \text{le}(y, x))$
6. `to_trichotomy`: $\forall x \forall y, (\text{lt}(x, y) \lor x = y \lor \text{lt}(y, x))$

#### 4.3.4 Example Provable Theorems
- **Strict Order Transitivity** (`po_lt_transitive`):
  Premises: `po_transitive`, `po_antisymmetric`, `po_lt_def`.
  Target: $\forall x \forall y \forall z, ((\text{lt}(x, y) \land \text{lt}(y, z)) \implies \text{lt}(x, z))$
- **Strict Order Irreflexivity** (`po_lt_irreflexive`):
  Premises: `po_lt_def`.
  Target: $\forall x, \neg \text{lt}(x, x)$
- **Negation of Strict Order is Converse Order in Total Order** (`to_not_lt_is_ge`):
  Premises: `get_total_order_axioms()`.
  Target: $\forall x \forall y, (\neg \text{lt}(x, y) \iff \text{le}(y, x))$

---

### 4.4 `solver/kb/sets.py` — Minimal Set Theory Axioms

#### 4.4.1 Overview & Sorts
Set theory operates over element sort `ElemSort = PrimitiveSort("Elem")` and parameterized set sort `SetSort(ElemSort)` (i.e., `ParameterizedSort("Set", (ElemSort,))`).
The signature declares:
- Predicate `in_set` ($\in$): `(ElemSort, Set(ElemSort))`.
- Predicate `subset` ($\subseteq$): `(Set(ElemSort), Set(ElemSort))`.
- Function `empty_set` ($\emptyset$): constant of sort `Set(ElemSort)`.
- Function `union` ($\cup$): `(Set(ElemSort), Set(ElemSort)) -> Set(ElemSort)`.
- Function `inter` ($\cap$): `(Set(ElemSort), Set(ElemSort)) -> Set(ElemSort)`.
- Function `diff` ($\setminus$): `(Set(ElemSort), Set(ElemSort)) -> Set(ElemSort)`.
- Function `singleton`: `(ElemSort) -> Set(ElemSort)`.
- Function `powerset` ($\mathcal{P}$): `(Set(ElemSort)) -> Set(Set(ElemSort))`.

#### 4.4.2 Module API Signatures
```python
from typing import List, Tuple
from solver.core.ast import Formula, Variable, Constant, FunctionApp, PredicateApp, Equality, Forall, Exists, Implies, And, Or, Not, Iff
from solver.core.sorts import PrimitiveSort, ParameterizedSort, SetSort
from solver.core.signature import Signature

ElemSort: PrimitiveSort = PrimitiveSort("Elem")
SetType: ParameterizedSort = SetSort(ElemSort)

def get_set_signature() -> Signature:
    """Returns signature for minimal set theory symbols."""
    ...

def get_set_theory_axioms() -> List[Tuple[str, Formula]]:
    """Returns minimal set theory axioms: extensionality, subset, empty set, union, inter, diff, singleton, powerset."""
    ...
```

#### 4.4.3 Axiom Definitions

1. `set_extensionality`: $\forall A : \text{Set} \forall B : \text{Set}, (A = B \iff \forall x : \text{Elem}, (x \in A \iff x \in B))$
2. `set_subset_def`: $\forall A : \text{Set} \forall B : \text{Set}, (A \subseteq B \iff \forall x : \text{Elem}, (x \in A \implies x \in B))$
3. `set_empty_def`: $\forall x : \text{Elem}, \neg(x \in \text{empty\_set})$
4. `set_union_def`: $\forall A \forall B \forall x, (x \in \text{union}(A, B) \iff (x \in A \lor x \in B))$
5. `set_inter_def`: $\forall A \forall B \forall x, (x \in \text{inter}(A, B) \iff (x \in A \land x \in B))$
6. `set_diff_def`: $\forall A \forall B \forall x, (x \in \text{diff}(A, B) \iff (x \in A \land \neg(x \in B)))$
7. `set_singleton_def`: $\forall x : \text{Elem} \forall y : \text{Elem}, (y \in \text{singleton}(x) \iff y = x)$
8. `set_powerset_def`: $\forall A : \text{Set} \forall B : \text{Set}, (B \in \text{powerset}(A) \iff B \subseteq A)$

#### 4.4.4 Example Provable Theorems
- **Reflexivity of Subset** (`set_subset_refl`): $\forall A : \text{Set}, A \subseteq A$
- **Transitivity of Subset** (`set_subset_trans`): $\forall A \forall B \forall C, ((A \subseteq B \land B \subseteq C) \implies A \subseteq C)$
- **Empty Set is Subset of All Sets** (`set_empty_subset_all`): $\forall A : \text{Set}, \text{empty\_set} \subseteq A$
- **Intersection Idempotence** (`set_inter_idempotent`): $\forall A, \text{inter}(A, A) = A$

---

### 4.5 `solver/kb/functions.py` — Function Concepts Axioms

#### 4.5.1 Overview & Sorts
Function concepts operate over domain sort `Dom = PrimitiveSort("Dom")`, codomain sort `Codom = PrimitiveSort("Codom")`, and function representation sort `FuncSort = PrimitiveSort("Func")`.
The signature declares:
- Function `apply`: $f(x)$ evaluation `(FuncSort, Dom) -> Codom`.
- Function `comp`: composition $g \circ f$ `(FuncSort, FuncSort) -> FuncSort`.
- Constant `id_func`: identity function of sort `FuncSort`.
- Predicate `is_injective`: `(FuncSort)`.
- Predicate `is_surjective`: `(FuncSort)`.
- Predicate `is_bijective`: `(FuncSort)`.

#### 4.5.2 Module API Signatures
```python
from typing import List, Tuple
from solver.core.ast import Formula, Variable, Constant, FunctionApp, PredicateApp, Equality, Forall, Exists, Implies, And, Iff
from solver.core.sorts import PrimitiveSort
from solver.core.signature import Signature

Dom: PrimitiveSort = PrimitiveSort("Dom")
Codom: PrimitiveSort = PrimitiveSort("Codom")
FuncSort: PrimitiveSort = PrimitiveSort("Func")

def get_function_signature() -> Signature:
    """Returns signature declaring function concepts (apply, comp, id_func, is_injective, etc.)."""
    ...

def get_function_axioms() -> List[Tuple[str, Formula]]:
    """Returns function concept axioms: composition, injectivity, surjectivity, bijectivity, identity function."""
    ...
```

#### 4.5.3 Axiom Definitions

1. `func_well_defined`: $\forall f : \text{Func} \forall x : \text{Dom} \forall y : \text{Dom}, (x = y \implies \text{apply}(f, x) = \text{apply}(f, y))$
2. `func_comp_def`: $\forall g : \text{Func} \forall f : \text{Func} \forall x : \text{Dom}, \text{apply}(\text{comp}(g, f), x) = \text{apply}(g, \text{apply}(f, x))$
3. `func_injective_def`: $\forall f : \text{Func}, (\text{is\_injective}(f) \iff \forall x \forall y, (\text{apply}(f, x) = \text{apply}(f, y) \implies x = y))$
4. `func_surjective_def`: $\forall f : \text{Func}, (\text{is\_surjective}(f) \iff \forall z : \text{Codom}, \exists x : \text{Dom}, \text{apply}(f, x) = z)$
5. `func_bijective_def`: $\forall f : \text{Func}, (\text{is\_bijective}(f) \iff (\text{is\_injective}(f) \land \text{is\_surjective}(f)))$
6. `func_id_def`: $\forall x : \text{Dom}, \text{apply}(\text{id\_func}, x) = x$

#### 4.5.4 Example Provable Theorems
- **Composition of Injective Functions is Injective** (`func_comp_injective`):
  Premises: `func_injective_def`, `func_comp_def`.
  Target: $\forall f \forall g, ((\text{is\_injective}(f) \land \text{is\_injective}(g)) \implies \text{is\_injective}(\text{comp}(g, f)))$
- **Identity Function is Injective** (`func_id_injective`):
  Premises: `func_injective_def`, `func_id_def`.
  Target: $\text{is\_injective}(\text{id\_func})$
- **Bijective implies Injective** (`func_bij_implies_inj`):
  Premises: `func_bijective_def`.
  Target: $\forall f, (\text{is\_bijective}(f) \implies \text{is\_injective}(f))$

---

### 4.6 `solver/kb/__init__.py` — Aggregated Knowledge Base

Modifies package initialization to re-export all foundational and extended axiom generators and signatures.

```python
from typing import List, Tuple
from solver.core.ast import Formula
from solver.core.signature import Signature
from solver.kb.equality import get_equality_axioms, get_equality_signature
from solver.kb.logic import get_fol_axioms, get_fol_signature
from solver.kb.numbers import get_peano_axioms, get_peano_signature
from solver.kb.groups import get_group_axioms, get_group_signature
from solver.kb.relations import get_relation_axioms, get_relation_signature
from solver.kb.orders import get_partial_order_axioms, get_total_order_axioms, get_order_signature
from solver.kb.sets import get_set_theory_axioms, get_set_signature
from solver.kb.functions import get_function_axioms, get_function_signature

def get_extended_axioms() -> List[Tuple[str, Formula, str]]:
    """Returns all extended axioms with category tags ('groups', 'relations', 'orders', 'sets', 'functions')."""
    ...

def get_all_axioms() -> List[Tuple[str, Formula, str]]:
    """Returns complete library axiom set combining foundational and extended domains."""
    ...

def get_combined_signature() -> Signature:
    """Merges signatures across all foundational and extended axiom domains."""
    ...
```

---

## 5. Step-by-Step Implementation Order

1. **Step 1: Group Theory Module (`solver/kb/groups.py`)**
   - Implement `get_group_signature()` and `get_group_axioms()`.
   - Verify sort correctness (`GroupElem`) and signature registration.
2. **Step 2: Relation Axioms Module (`solver/kb/relations.py`)**
   - Implement `get_relation_signature()` and `get_relation_axioms()`.
   - Verify predicate arity and variable sorts (`RelElem`).
3. **Step 3: Order Theory Module (`solver/kb/orders.py`)**
   - Implement `get_order_signature()`, `get_partial_order_axioms()`, and `get_total_order_axioms()`.
   - Verify strict vs non-strict order formulations and trichotomy.
4. **Step 4: Minimal Set Theory Module (`solver/kb/sets.py`)**
   - Implement `get_set_signature()` and `get_set_theory_axioms()`.
   - Verify parameterized sort `Set(Elem)` and binary operators ($\cup, \cap, \setminus, \in, \subseteq$).
5. **Step 5: Function Concepts Module (`solver/kb/functions.py`)**
   - Implement `get_function_signature()` and `get_function_axioms()`.
   - Verify function application, composition, injectivity, surjectivity, and bijectivity.
6. **Step 6: Aggregate Package Exports (`solver/kb/__init__.py`)**
   - Update `get_all_axioms()`, `get_extended_axioms()`, and `get_combined_signature()`.
7. **Step 7: Test Suite & Prover Derivations (`tests/test_extended_kb.py`)**
   - Write comprehensive tests asserting AST validation, SQLite database insertion, and prover theorem derivations across all 5 new domains.

---

## 6. Testing Requirements

All tests are placed in `tests/test_extended_kb.py`.

### 6.1 Unit & AST Invariant Tests
- **Signature Well-Formedness**: Verify that every signature (`get_group_signature`, `get_relation_signature`, `get_order_signature`, `get_set_signature`, `get_function_signature`) passes lookup and arity checks.
- **Axiom AST Validation**: Run `validate_formula()` on every axiom across all extended domains to ensure zero `ValidationError` exceptions.
- **Database Integration**: Insert all extended axioms into `KnowledgeDatabase` and query by category (`"groups"`, `"relations"`, `"orders"`, `"sets"`, `"functions"`). Confirm retrieval fidelity.

### 6.2 Prover Derivation Tests (Non-Trivial Theorems)
The test suite must execute `TheoremProver.prove()` to establish at least one non-trivial theorem in each domain:

1. **Groups**: Prove `group_left_cancel` ($\text{op}(a, x) = \text{op}(a, y) \implies x = y$) from group axioms.
2. **Relations**: Prove `rel_irref_trans_implies_asymm` (Irreflexive + Transitive $\implies$ Asymmetric).
3. **Orders**: Prove `po_lt_transitive` (Strict partial order transitivity) from partial order axioms.
4. **Sets**: Prove `set_subset_trans` (Subset transitivity $A \subseteq B \land B \subseteq C \implies A \subseteq C$) from set axioms.
5. **Functions**: Prove `func_comp_injective` (Composition of injective functions is injective) from function axioms.

---

## 7. Acceptance Criteria

1. **Completeness**: All 5 new modules (`groups.py`, `relations.py`, `orders.py`, `sets.py`, `functions.py`) are created with clean signatures, detailed docstrings, and complete Python type hints.
2. **AST Well-Formedness**: 100% of defined axioms pass `validate_formula()` against their respective signatures.
3. **Database Population**: `python -m solver init` correctly loads all extended axioms into the database without error.
4. **Prover Verification**: The resolution prover successfully derives the required non-trivial theorem for every single new domain, producing a valid `ProofDAG` (`is_valid() == True`).
5. **Test Coverage**: `pytest tests/test_extended_kb.py` passes with 100% assertion pass rate.

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| Resolution prover performance explosion on large set theory axiom sets | Prover timeout during test suite execution | Pass only relevant minimal subsets of domain axioms to `TheoremProver.prove()` for specific theorem targets rather than dumping all KB axioms at once. |
| Sort mismatch between parameterized set sorts `Set(Elem)` and primitive element sorts `Elem` | AST `ValidationError` or unification failure | Rigorously check that `in_set` takes `(Elem, Set(Elem))` and `subset` takes `(Set(Elem), Set(Elem))`. |
| Variable collision in quantifiers during CNF Skolemization | Invalid resolution step in prover | Ensure all axioms use standard canonical variable indices ($v_0, v_1, v_2, \dots$) and rely on `canonicalize_bound_variables` before clausification. |
