# Phase 6 Implementation Plan: Knowledge Base & Database

## 1. Phase Title, Goal, and Overview

### Title
**Phase 6 — Knowledge Base & Database**

### Goal
Implement foundational axiom sets (Equality, First-Order Logic, Peano Arithmetic) and persistent SQLite-backed storage (`KnowledgeDatabase`) for terms, formulas, axioms, proved theorems, and proof DAGs, along with configuration management (`SolverConfig`) and the CLI database initialization command (`python -m solver init`).

### Overview
Automated theorem provers and formal logic explorers depend on two foundational capabilities:
1. Standard, well-sorted axiom systems that serve as the baseline premises for reasoning.
2. Fast, persistent storage for terms, formulas, axioms, and proved theorems across execution runs.

Phase 6 provides these core capabilities. The `solver.kb` package establishes formal axiom sets for Equality, First-Order Logic (FOL), and Peano Arithmetic using multi-domain sorts (`Ind`, `Nat`, `Bool`). The `solver.core.database` module introduces `KnowledgeDatabase`, an SQLite-backed storage system optimized for logical operations. To support fast structural queries and instant duplicate detection, stored formulas are canonicalized using de Bruijn bound variable renaming (`canonicalize_bound_variables`) and indexed across key structural properties:
- `ast_hash`: SHA-256 hash of the canonical JSON representation (stable across Python sessions/versions).
- `canonical_string`: Formatted canonical text string.
- `free_variables`: JSON list of free variables.
- `predicate_names`: JSON list of predicate symbols.
- `function_names`: JSON list of function symbols.
- `depth`: Maximum AST depth.
- `size`: Total AST node count.

Additionally, this phase introduces `solver/config.py` (`SolverConfig`) to manage library settings and extends `solver/__main__.py` with the CLI `init` command to populate the database with default axioms.

---

## 2. Prerequisites

Before starting Phase 6, the following previous phases must be complete and fully verified:

1. **Phase 1 — AST & Sort System** (`solver/core/ast.py`, `solver/core/sorts.py`, `solver/core/exceptions.py`):
   - AST node definitions: `Term`, `Variable`, `Constant`, `FunctionApp`, `Formula`, `PredicateApp`, `Equality`, `Not`, `And`, `Or`, `Implies`, `Iff`, `Forall`, `Exists`.
   - Structural helpers: `canonicalize_bound_variables()`, `free_variables()`, `formula_depth()`, `formula_size()`.
   - Sort system: `Sort`, `PrimitiveSort("Ind")`, `PrimitiveSort("Nat")`, `PrimitiveSort("Bool")`.
2. **Phase 2 — Signature & Validator** (`solver/core/signature.py`, `solver/core/validator.py`):
   - Symbol registration and lookup via `Signature`.
   - Structural and sort validation via `validate_formula()`.
3. **Phase 3 — Parser & Visitor Framework** (`solver/core/parser.py`, `solver/core/visitors.py`):
   - Text formula parsing via `parse_formula()` and string formatting via `to_string()`.
4. **Phase 4 — Substitution & Unification** (`solver/core/substitutions.py`):
   - Variable substitution `substitute_formula()` and FOL unification.

---

## 3. Files to Create / Modify

| File Path | Action | Description |
| :--- | :--- | :--- |
| `solver/config.py` | Create | Central configuration dataclass (`SolverConfig`) and configuration file parser |
| `solver/kb/__init__.py` | Create | Knowledge base package exports (`get_all_axioms`, `get_combined_signature`) |
| `solver/kb/equality.py` | Create | Equality axiom generators (Reflexivity, Symmetry, Transitivity, Congruence) |
| `solver/kb/logic.py` | Create | FOL axiom generators (Propositional schemata & Quantifier laws) |
| `solver/kb/numbers.py` | Create | Peano Arithmetic axiom generators for natural numbers (`Nat` sort) |
| `solver/core/database.py` | Create | SQLite persistent database manager (`KnowledgeDatabase`), JSON AST serializer, indexed queries |
| `solver/__main__.py` | Create / Update | CLI entry point with `init` command implementation |
| `tests/test_database.py` | Create | Unit and integration test suite for database persistence, indexing, alpha-equivalence, recovery, and CLI |

---

## 4. Detailed Implementation Guide

### 4.1 `solver/config.py`

Central configuration management for database path, search parameters, prover timeouts, and export settings.

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json

@dataclass
class SolverConfig:
    db_path: str = "solver_data.db"
    explorer_max_depth: int = 4
    explorer_batch_size: int = 50
    explorer_top_k: int = 10
    explorer_strategy: str = "mixed"
    prover_max_steps: int = 1000
    prover_timeout_sec: float = 10.0
    log_level: str = "INFO"
    lean_mathlib_version: str = "latest"

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "SolverConfig":
        """Loads configuration settings from a JSON or TOML file."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Converts configuration to a dictionary."""
        ...

    def save(self, path: Union[str, Path]) -> None:
        """Saves configuration settings to a JSON file."""
        ...
```

#### Implementation Notes & Edge Cases
- `from_file`: Checks file extension (`.json` or `.toml`). Uses standard library `tomllib` (Python 3.11+) or `json` module. Handles missing file gracefully by raising `FileNotFoundError` or `SolverError`.
- Unknown key handling: Filters dictionary keys to match dataclass fields before instantiation to prevent `TypeError`.

---

### 4.2 `solver/kb/equality.py`

Defines equality axioms for First-Order Logic with sorts.

```python
from typing import List, Tuple
from solver.core.ast import Formula, Variable, Equality, Implies, And, Forall
from solver.core.sorts import Ind
from solver.core.signature import Signature

def get_equality_signature() -> Signature:
    """Returns signature declaring generic equality operations."""
    ...

def get_equality_axioms() -> List[Tuple[str, Formula]]:
    """Returns fundamental equality axioms: reflexivity, symmetry, transitivity, and congruence schemata."""
    ...
```

#### Axiom Definitions & Identifiers
1. `eq_reflexive`: $\forall x, x = x$
2. `eq_symmetric`: $\forall x \forall y, (x = y \implies y = x)$
3. `eq_transitive`: $\forall x \forall y \forall z, ((x = y \land y = z) \implies x = z)$
4. `eq_congruence_unary_func`: $\forall x \forall y, (x = y \implies f(x) = f(y))$
5. `eq_congruence_binary_func`: $\forall x_1 \forall x_2 \forall y_1 \forall y_2, ((x_1 = y_1 \land x_2 = y_2) \implies f(x_1, x_2) = f(y_1, y_2))$
6. `eq_congruence_unary_pred`: $\forall x \forall y, ((x = y \land P(x)) \implies P(y))$

---

### 4.3 `solver/kb/logic.py`

Defines core First-Order Logic propositional schemata and quantifier laws.

```python
from typing import List, Tuple
from solver.core.ast import Formula
from solver.core.signature import Signature

def get_fol_signature() -> Signature:
    """Returns signature declaring sample predicate symbols for FOL schemata."""
    ...

def get_fol_axioms() -> List[Tuple[str, Formula]]:
    """Returns First-Order Logic axioms: propositional schemata and quantifier laws."""
    ...
```

#### Axiom Definitions & Identifiers
1. `prop_impl_self`: $\forall x, P(x) \implies P(x)$
2. `prop_and_elim_left`: $\forall x, (P(x) \land Q(x)) \implies P(x)$
3. `prop_and_elim_right`: $\forall x, (P(x) \land Q(x)) \implies Q(x)$
4. `prop_or_intro_left`: $\forall x, P(x) \implies (P(x) \lor Q(x))$
5. `prop_double_negation`: $\forall x, \neg\neg P(x) \implies P(x)$
6. `quant_forall_elim`: $\forall x, P(x) \implies P(x)$
7. `quant_exists_intro`: $\forall x, (P(x) \implies \exists y, P(y))$
8. `quant_de_morgan_1`: $\forall x, (\neg \exists y, P(y) \iff \forall y, \neg P(y))$

---

### 4.4 `solver/kb/numbers.py`

Defines Peano arithmetic axioms for natural numbers.

```python
from typing import List, Tuple
from solver.core.ast import Formula
from solver.core.sorts import PrimitiveSort
from solver.core.signature import Signature

Nat = PrimitiveSort("Nat")

def get_peano_signature() -> Signature:
    """Returns signature declaring Peano arithmetic symbols (0, S, +, *, <=)."""
    ...

def get_peano_axioms() -> List[Tuple[str, Formula]]:
    """Returns Peano arithmetic axioms for natural numbers."""
    ...
```

#### Signature Symbols
- Constant: `zero` (`0`): sort `Nat`
- Function: `succ` (`S`): arity 1, arg `(Nat,)`, return `Nat`
- Function: `add` (`+`): arity 2, args `(Nat, Nat)`, return `Nat`
- Function: `mul` (`*`): arity 2, args `(Nat, Nat)`, return `Nat`
- Predicate: `le` (`<=`): arity 2, args `(Nat, Nat)`
- Predicate: `eq` (`=`): arity 2, args `(Nat, Nat)`

#### Axiom Definitions & Identifiers
1. `peano_zero_not_succ`: $\forall n : \text{Nat}, \neg (S(n) = 0)$
2. `peano_succ_injective`: $\forall m : \text{Nat} \forall n : \text{Nat}, (S(m) = S(n) \implies m = n)$
3. `peano_add_zero`: $\forall n : \text{Nat}, n + 0 = n$
4. `peano_add_succ`: $\forall m : \text{Nat} \forall n : \text{Nat}, m + S(n) = S(m + n)$
5. `peano_mul_zero`: $\forall n : \text{Nat}, n \cdot 0 = 0$
6. `peano_mul_succ`: $\forall m : \text{Nat} \forall n : \text{Nat}, m \cdot S(n) = (m \cdot n) + m$
7. `peano_le_def`: $\forall m : \text{Nat} \forall n : \text{Nat}, (m \le n \iff \exists k : \text{Nat}, m + k = n)$

---

### 4.5 `solver/kb/__init__.py`

Aggregates all foundational axiom sets and signatures into a unified knowledge base interface.

```python
from typing import List, Tuple
from solver.core.ast import Formula
from solver.core.signature import Signature
from solver.kb.equality import get_equality_axioms, get_equality_signature
from solver.kb.logic import get_fol_axioms, get_fol_signature
from solver.kb.numbers import get_peano_axioms, get_peano_signature

def get_all_axioms() -> List[Tuple[str, Formula, str]]:
    """Returns all foundational axioms as (name, formula, category) tuples."""
    ...

def get_combined_signature() -> Signature:
    """Merges signatures across equality, logic, and peano arithmetic."""
    ...
```

---

### 4.6 `solver/core/database.py`

Persistent storage layer using SQLite.

```python
import sqlite3
import json
import hashlib
from typing import List, Tuple, Optional, Dict, Any, Union
from pathlib import Path
from solver.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists,
    canonicalize_bound_variables, free_variables, formula_depth, formula_size
)
from solver.core.parser import to_string
from solver.core.exceptions import DatabaseError
from solver.prover.proof import ProofDAG

class KnowledgeDatabase:
    def __init__(self, db_path: Union[str, Path] = "solver_data.db"):
        ...

    def __enter__(self) -> "KnowledgeDatabase":
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    def close(self) -> None:
        ...

    def _init_db(self) -> None:
        """Creates tables, pragmas, and indexes if they do not exist."""
        ...

    def _formula_to_json(self, formula: Formula) -> str:
        """Serializes Formula AST to deterministic canonical JSON string."""
        ...

    def _json_to_formula(self, json_str: str) -> Formula:
        """Deserializes JSON string back into Formula AST."""
        ...

    def _compute_ast_hash(self, formula: Formula) -> str:
        """Computes deterministic SHA-256 hash of canonicalized formula."""
        ...

    def _get_or_insert_formula(self, formula: Formula) -> int:
        """Inserts formula record into `formulas` table if absent; returns formula_id."""
        ...

    def add_axiom(self, name: str, formula: Formula, category: str = "general") -> None:
        """Registers a named axiom in database. Raises DatabaseError on duplicate name."""
        ...

    def add_theorem(self, name: str, formula: Formula, proof: Optional[ProofDAG] = None, category: str = "general") -> None:
        """Registers a proved theorem and optional proof DAG."""
        ...

    def get_axioms(self, category: Optional[str] = None) -> List[Tuple[str, Formula]]:
        """Retrieves axioms, optionally filtered by category."""
        ...

    def get_theorems(self, category: Optional[str] = None) -> List[Tuple[str, Formula]]:
        """Retrieves theorems, optionally filtered by category."""
        ...

    def get_proof(self, theorem_name: str) -> Optional[ProofDAG]:
        """Retrieves proof DAG for named theorem."""
        ...

    def contains_formula(self, formula: Formula) -> bool:
        """Checks if formula (or an alpha-equivalent variant) exists in database."""
        ...

    def search_formulas(
        self,
        predicate_name: Optional[str] = None,
        max_depth: Optional[int] = None,
        max_size: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[Formula]:
        """Queries formulas using indexed structural attributes."""
        ...
```

#### SQLite Schema Specification

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS formulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ast_hash TEXT UNIQUE NOT NULL,
    canonical_string TEXT NOT NULL,
    json_repr TEXT NOT NULL,
    free_variables TEXT NOT NULL,
    predicate_names TEXT NOT NULL,
    function_names TEXT NOT NULL,
    depth INTEGER NOT NULL,
    size INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS axioms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    formula_id INTEGER NOT NULL REFERENCES formulas(id) ON DELETE CASCADE,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS theorems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    formula_id INTEGER NOT NULL REFERENCES formulas(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    proof_id INTEGER REFERENCES proofs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theorem_name TEXT UNIQUE NOT NULL,
    proof_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_formulas_ast_hash ON formulas(ast_hash);
CREATE INDEX IF NOT EXISTS idx_formulas_depth ON formulas(depth);
CREATE INDEX IF NOT EXISTS idx_formulas_size ON formulas(size);
CREATE INDEX IF NOT EXISTS idx_axioms_category ON axioms(category);
CREATE INDEX IF NOT EXISTS idx_theorems_category ON theorems(category);
```

#### JSON AST Serialization Rules
- **AST Serialization**: Converts AST nodes to typed JSON dictionaries:
  - `{"type": "Forall", "variable": {"id": 0, "sort": "Nat"}, "body": ...}`
  - `{"type": "Equality", "left": ..., "right": ...}`
- **Hash Stability Algorithm**:
  1. `canonical = canonicalize_bound_variables(formula)`
  2. `json_str = _formula_to_json(canonical)` (using `json.dumps(..., sort_keys=True)`)
  3. `ast_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()`
- **Alpha-Equivalence Matching**: Since `ast_hash` is computed on `canonicalize_bound_variables(formula)`, any formula $\alpha$-equivalent to an existing entry produces the exact same `ast_hash`, enabling instant $O(1)$ duplicate detection via `contains_formula()`.

---

### 4.7 `solver/__main__.py`

CLI entry point using `argparse`.

```python
import sys
import argparse
from pathlib import Path
from solver.config import SolverConfig
from solver.core.database import KnowledgeDatabase
from solver.kb import get_all_axioms

def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="solver", description="Formal Logic Explorer & Theorem Prover CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize database with foundational axioms")
    init_parser.add_argument("--db-path", type=str, default=None, help="Path to SQLite database file")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing database if present")

    return parser

def main() -> None:
    parser = build_cli_parser()
    args = parser.parse_args()

    if args.command == "init":
        config = SolverConfig()
        db_path = args.db_path or config.db_path

        if args.force and Path(db_path).exists():
            Path(db_path).unlink()

        db = KnowledgeDatabase(db_path)
        axioms = get_all_axioms()
        added_count = 0
        for name, formula, category in axioms:
            try:
                db.add_axiom(name, formula, category)
                added_count += 1
            except Exception as e:
                print(f"Skipping duplicate/invalid axiom {name}: {e}")

        db.close()
        print(f"Successfully initialized database at '{db_path}' with {added_count} axioms.")

if __name__ == "__main__":
    main()
```

---

## 5. Step-by-Step Implementation Order

1. **Step 1: Configuration Management (`solver/config.py`)**
   - Implement `SolverConfig` dataclass and JSON/TOML parser.
   - Unit test configuration defaults and file loading.

2. **Step 2: Axiom Modules (`solver/kb/equality.py`, `solver/kb/logic.py`, `solver/kb/numbers.py`, `solver/kb/__init__.py`)**
   - Implement signatures and formula builders for Equality, FOL, and Peano axioms.
   - Verify all formulas parse, construct cleanly, and pass AST validation.

3. **Step 3: Database Engine (`solver/core/database.py`)**
   - Implement SQLite schema initialization, table creation, pragmas, and indexes.
   - Implement AST JSON serializer/deserializer and SHA-256 hash generator.
   - Implement `add_axiom`, `add_theorem`, `get_axioms`, `get_theorems`, `contains_formula`, and `search_formulas`.
   - Implement context manager protocol (`__enter__`, `__exit__`).

4. **Step 4: CLI Command (`solver/__main__.py`)**
   - Implement `init` command handling in `__main__.py`.

5. **Step 5: Testing & Verification (`tests/test_database.py`)**
   - Write comprehensive unit and integration tests covering persistence, indexing, alpha-equivalence, recovery, and CLI execution.

---

## 6. Testing Requirements

All tests are placed in `tests/test_database.py` and run via `pytest`.

### Required Test Cases
1. **Database Schema & Creation (`test_database_creation`)**:
   - Verify SQLite file is created and tables (`formulas`, `axioms`, `theorems`, `proofs`, `metadata`) exist.
2. **Axiom Insertion & Retrieval (`test_add_and_get_axioms`)**:
   - Add axioms across categories (`equality`, `logic`, `peano`). Retrieve by category and verify formula equality.
3. **Persistence Across Restart (`test_persistence_across_restarts`)**:
   - Insert axioms/theorems, close database connection, instantiate new `KnowledgeDatabase` instance pointing to the same file, and verify data persists.
4. **Alpha-Equivalence Querying (`test_contains_formula_alpha_equivalence`)**:
   - Insert formula $\forall x : \text{Ind}, P(x)$. Verify `contains_formula` returns `True` when checked against $\forall y : \text{Ind}, P(y)$.
5. **Deterministic Hash Stability (`test_hash_stability`)**:
   - Assert SHA-256 canonical `ast_hash` matches fixed expected values across multiple Python invocations.
6. **Indexed Formula Search (`test_search_formulas_indexing`)**:
   - Insert formulas with varying depths, sizes, and predicate symbols.
   - Query by `predicate_name`, `max_depth`, and `max_size`. Assert SQL query filtering returns exact matches.
7. **Duplicate Name Handling (`test_duplicate_axiom_error`)**:
   - Assert `add_axiom` with duplicate name raises `DatabaseError`.
8. **Corruption Recovery & Rollback (`test_transaction_rollback`)**:
   - Simulate exception during multi-step write; verify transaction rolls back and database remains uncorrupted.
9. **Context Manager Protocol (`test_context_manager`)**:
   - Verify `with KnowledgeDatabase(...) as db:` opens and automatically closes connection upon block exit.
10. **CLI `init` Integration Test (`test_cli_init`)**:
    - Run `python -m solver init --db-path test_init.db` via subprocess or direct function invocation; verify DB is created and populated with foundational axioms.

---

## 7. Acceptance Criteria

- [ ] All foundational axioms (Equality, FOL, Peano) construct cleanly, validate against signatures, and pass well-formedness checks.
- [ ] Database persists axioms and proved theorems across process restarts.
- [ ] `contains_formula` identifies alpha-equivalent formulas via de Bruijn canonical hashing ($O(1)$ lookup).
- [ ] Formula searches using indexed columns (`ast_hash`, `depth`, `size`, `predicate_names`) return accurate results efficiently.
- [ ] CLI command `python -m solver init` creates database file and populates it with all foundational axioms.
- [ ] `pytest tests/test_database.py` passes with 100% test success rate.

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Python built-in `hash()` instability** | Hash values differ between Python runs, breaking persistence indexing | Use SHA-256 hashing over de Bruijn canonicalized AST JSON strings |
| **SQLite database locking under concurrent access** | File locks cause `OperationalError` during writes | Enable Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) and set explicit busy timeout |
| **JSON serialization recursion limit for deep ASTs** | Stack overflow or truncation on complex formulas | Use iterative AST traversals or standard JSON serializer with depth limits |
| **Schema migration issues for future phases** | Database breaks when new tables are added in later phases | Include a `metadata` table tracking `schema_version` to support incremental migrations |
