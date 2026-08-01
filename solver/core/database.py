"""SQLite database persistence engine for solver formulas, axioms, and theorems."""

from __future__ import annotations
import sqlite3
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union, Set

from solver.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists, VariableKind,
    canonicalize_bound_variables, free_variables, formula_depth, formula_size
)
from solver.core.sorts import Sort, PrimitiveSort, ParameterizedSort, FunctionSort, Ind
from solver.core.parser import to_string
from solver.core.exceptions import DatabaseError

# Type hint alias for ProofDAG until prover module is created
ProofDAG = Any


def _sort_to_dict(sort: Sort) -> Dict[str, Any]:
    if isinstance(sort, PrimitiveSort):
        return {"sort_type": "PrimitiveSort", "name": sort.sort_name}
    elif isinstance(sort, ParameterizedSort):
        return {
            "sort_type": "ParameterizedSort",
            "constructor": sort.constructor,
            "args": [_sort_to_dict(a) for a in sort.args]
        }
    elif isinstance(sort, FunctionSort):
        return {
            "sort_type": "FunctionSort",
            "arg_sorts": [_sort_to_dict(a) for a in sort.arg_sorts],
            "return_sort": _sort_to_dict(sort.return_sort)
        }
    else:
        raise DatabaseError(f"Unsupported sort type for serialization: {type(sort)}")


def _dict_to_sort(d: Dict[str, Any]) -> Sort:
    stype = d.get("sort_type")
    if stype == "PrimitiveSort":
        return PrimitiveSort(d["name"])
    elif stype == "ParameterizedSort":
        return ParameterizedSort(d["constructor"], tuple(_dict_to_sort(a) for a in d["args"]))
    elif stype == "FunctionSort":
        return FunctionSort(tuple(_dict_to_sort(a) for a in d["arg_sorts"]), _dict_to_sort(d["return_sort"]))
    else:
        raise DatabaseError(f"Invalid sort dictionary structure: {d}")


from solver.sol.ast_ext import (
    PredicateVariable, FunctionVariable,
    ForallPred, ExistsPred, ForallFunc, ExistsFunc
)


def _term_to_dict(term: Term) -> Dict[str, Any]:
    if isinstance(term, Variable):
        return {
            "node_type": "Variable",
            "id": term.id,
            "kind": term.kind.value,
            "sort": _sort_to_dict(term.sort)
        }
    elif isinstance(term, Constant):
        return {
            "node_type": "Constant",
            "name": term.name,
            "sort": _sort_to_dict(term.sort)
        }
    elif isinstance(term, FunctionApp):
        func_repr = {
            "node_type": "FunctionVariable",
            "index": term.func.index,
            "arity": term.func.arity,
            "arg_sorts": [_sort_to_dict(s) for s in term.func.arg_sorts],
            "return_sort": _sort_to_dict(term.func.return_sort)
        } if isinstance(term.func, FunctionVariable) else term.func
        return {
            "node_type": "FunctionApp",
            "func": func_repr,
            "arity": term.arity,
            "args": [_term_to_dict(arg) for arg in term.args],
            "return_sort": _sort_to_dict(term.return_sort)
        }
    else:
        raise DatabaseError(f"Unsupported term node type for serialization: {type(term)}")


def _dict_to_term(d: Dict[str, Any]) -> Term:
    ntype = d.get("node_type")
    if ntype == "Variable":
        return Variable(id=d["id"], kind=VariableKind(d["kind"]), sort=_dict_to_sort(d["sort"]))
    elif ntype == "Constant":
        return Constant(name=d["name"], sort=_dict_to_sort(d["sort"]))
    elif ntype == "FunctionApp":
        func_raw = d["func"]
        if isinstance(func_raw, dict) and func_raw.get("node_type") == "FunctionVariable":
            func = FunctionVariable(
                index=func_raw["index"],
                arity=func_raw["arity"],
                arg_sorts=tuple(_dict_to_sort(s) for s in func_raw["arg_sorts"]),
                return_sort=_dict_to_sort(func_raw["return_sort"])
            )
        else:
            func = func_raw
        args = tuple(_dict_to_term(arg) for arg in d["args"])
        return FunctionApp(func=func, arity=d["arity"], args=args, return_sort=_dict_to_sort(d["return_sort"]))
    else:
        raise DatabaseError(f"Invalid term dictionary structure: {d}")


def _formula_to_dict(formula: Formula) -> Dict[str, Any]:
    if isinstance(formula, PredicateApp):
        pred_repr = {
            "node_type": "PredicateVariable",
            "index": formula.pred.index,
            "arity": formula.pred.arity
        } if isinstance(formula.pred, PredicateVariable) else formula.pred
        return {
            "node_type": "PredicateApp",
            "pred": pred_repr,
            "arity": formula.arity,
            "args": [_term_to_dict(arg) for arg in formula.args]
        }
    elif isinstance(formula, Equality):
        return {
            "node_type": "Equality",
            "left": _term_to_dict(formula.left),
            "right": _term_to_dict(formula.right)
        }
    elif isinstance(formula, Not):
        return {
            "node_type": "Not",
            "operand": _formula_to_dict(formula.operand)
        }
    elif isinstance(formula, And):
        return {
            "node_type": "And",
            "left": _formula_to_dict(formula.left),
            "right": _formula_to_dict(formula.right)
        }
    elif isinstance(formula, Or):
        return {
            "node_type": "Or",
            "left": _formula_to_dict(formula.left),
            "right": _formula_to_dict(formula.right)
        }
    elif isinstance(formula, Implies):
        return {
            "node_type": "Implies",
            "left": _formula_to_dict(formula.left),
            "right": _formula_to_dict(formula.right)
        }
    elif isinstance(formula, Iff):
        return {
            "node_type": "Iff",
            "left": _formula_to_dict(formula.left),
            "right": _formula_to_dict(formula.right)
        }
    elif isinstance(formula, Forall):
        return {
            "node_type": "Forall",
            "variable": _term_to_dict(formula.variable),
            "body": _formula_to_dict(formula.body)
        }
    elif isinstance(formula, Exists):
        return {
            "node_type": "Exists",
            "variable": _term_to_dict(formula.variable),
            "body": _formula_to_dict(formula.body)
        }
    elif isinstance(formula, (ForallPred, ExistsPred)):
        return {
            "node_type": type(formula).__name__,
            "variable": {
                "node_type": "PredicateVariable",
                "index": formula.variable.index,
                "arity": formula.variable.arity
            },
            "body": _formula_to_dict(formula.body)
        }
    elif isinstance(formula, (ForallFunc, ExistsFunc)):
        return {
            "node_type": type(formula).__name__,
            "variable": {
                "node_type": "FunctionVariable",
                "index": formula.variable.index,
                "arity": formula.variable.arity,
                "arg_sorts": [_sort_to_dict(s) for s in formula.variable.arg_sorts],
                "return_sort": _sort_to_dict(formula.variable.return_sort)
            },
            "body": _formula_to_dict(formula.body)
        }
    else:
        raise DatabaseError(f"Unsupported formula node type for serialization: {type(formula)}")


def _dict_to_formula(d: Dict[str, Any]) -> Formula:
    ntype = d.get("node_type")
    if ntype == "PredicateApp":
        pred_raw = d["pred"]
        if isinstance(pred_raw, dict) and pred_raw.get("node_type") == "PredicateVariable":
            pred = PredicateVariable(index=pred_raw["index"], arity=pred_raw["arity"])
        else:
            pred = pred_raw
        args = tuple(_dict_to_term(arg) for arg in d["args"])
        return PredicateApp(pred=pred, arity=d["arity"], args=args)
    elif ntype == "Equality":
        return Equality(left=_dict_to_term(d["left"]), right=_dict_to_term(d["right"]))
    elif ntype == "Not":
        return Not(operand=_dict_to_formula(d["operand"]))
    elif ntype == "And":
        return And(left=_dict_to_formula(d["left"]), right=_dict_to_formula(d["right"]))
    elif ntype == "Or":
        return Or(left=_dict_to_formula(d["left"]), right=_dict_to_formula(d["right"]))
    elif ntype == "Implies":
        return Implies(left=_dict_to_formula(d["left"]), right=_dict_to_formula(d["right"]))
    elif ntype == "Iff":
        return Iff(left=_dict_to_formula(d["left"]), right=_dict_to_formula(d["right"]))
    elif ntype == "Forall":
        var = _dict_to_term(d["variable"])
        if not isinstance(var, Variable):
            raise DatabaseError("Quantifier variable must be a Variable instance.")
        return Forall(variable=var, body=_dict_to_formula(d["body"]))
    elif ntype == "Exists":
        var = _dict_to_term(d["variable"])
        if not isinstance(var, Variable):
            raise DatabaseError("Quantifier variable must be a Variable instance.")
        return Exists(variable=var, body=_dict_to_formula(d["body"]))
    elif ntype in ("ForallPred", "ExistsPred"):
        v_dict = d["variable"]
        pred_var = PredicateVariable(index=v_dict["index"], arity=v_dict["arity"])
        cls = ForallPred if ntype == "ForallPred" else ExistsPred
        return cls(variable=pred_var, body=_dict_to_formula(d["body"]))
    elif ntype in ("ForallFunc", "ExistsFunc"):
        v_dict = d["variable"]
        func_var = FunctionVariable(
            index=v_dict["index"],
            arity=v_dict["arity"],
            arg_sorts=tuple(_dict_to_sort(s) for s in v_dict["arg_sorts"]),
            return_sort=_dict_to_sort(v_dict["return_sort"])
        )
        cls = ForallFunc if ntype == "ForallFunc" else ExistsFunc
        return cls(variable=func_var, body=_dict_to_formula(d["body"]))
    else:
        raise DatabaseError(f"Invalid formula dictionary structure: {d}")


def extract_predicates(formula: Formula) -> Set[str]:
    """Extracts all predicate symbol names from a formula."""
    preds: Set[str] = set()
    if isinstance(formula, PredicateApp):
        preds.add(formula.pred.name if isinstance(formula.pred, PredicateVariable) else str(formula.pred))
    elif isinstance(formula, Not):
        preds.update(extract_predicates(formula.operand))
    elif isinstance(formula, (And, Or, Implies, Iff)):
        preds.update(extract_predicates(formula.left))
        preds.update(extract_predicates(formula.right))
    elif isinstance(formula, (Forall, Exists)):
        preds.update(extract_predicates(formula.body))
    elif type(formula).__name__ in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
        preds.update(extract_predicates(getattr(formula, "body")))
    return preds


def extract_functions(node: Union[Formula, Term]) -> Set[str]:
    """Extracts all function symbol names from a formula or term."""
    funcs: Set[str] = set()
    if isinstance(node, FunctionApp):
        funcs.add(node.func.name if isinstance(node.func, FunctionVariable) else str(node.func))
        for arg in node.args:
            funcs.update(extract_functions(arg))
    elif isinstance(node, PredicateApp):
        for arg in node.args:
            funcs.update(extract_functions(arg))
    elif isinstance(node, Equality):
        funcs.update(extract_functions(node.left))
        funcs.update(extract_functions(node.right))
    elif isinstance(node, Not):
        funcs.update(extract_functions(node.operand))
    elif isinstance(node, (And, Or, Implies, Iff)):
        funcs.update(extract_functions(node.left))
        funcs.update(extract_functions(node.right))
    elif isinstance(node, (Forall, Exists)):
        funcs.update(extract_functions(node.body))
    elif type(node).__name__ in ("ForallPred", "ExistsPred", "ForallFunc", "ExistsFunc"):
        funcs.update(extract_functions(getattr(node, "body")))
    return funcs


class KnowledgeDatabase:
    """SQLite persistent storage engine for AST formulas, axioms, proved theorems, and proof DAGs."""

    def __init__(self, db_path: Union[str, Path] = "solver_data.db") -> None:
        """Initializes the database connection and schema tables."""
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self.db_path, timeout=30.0)
        self._init_db()

    def __enter__(self) -> KnowledgeDatabase:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Closes the underlying SQLite connection."""
        if getattr(self, "_conn", None) is not None:
            self._conn.close()
            self._conn = None

    def _init_db(self) -> None:
        """Creates tables, pragmas, and indexes if they do not exist."""
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")

        cursor.executescript("""
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

            CREATE TABLE IF NOT EXISTS proofs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theorem_name TEXT UNIQUE NOT NULL,
                proof_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS theorems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                formula_id INTEGER NOT NULL REFERENCES formulas(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                proof_id INTEGER REFERENCES proofs(id) ON DELETE SET NULL
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
        """)
        self._conn.commit()

    def _formula_to_json(self, formula: Formula) -> str:
        """Serializes Formula AST to deterministic canonical JSON string."""
        d = _formula_to_dict(formula)
        return json.dumps(d, sort_keys=True)

    def _json_to_formula(self, json_str: str) -> Formula:
        """Deserializes JSON string back into Formula AST."""
        d = json.loads(json_str)
        return _dict_to_formula(d)

    def _compute_ast_hash(self, formula: Formula) -> str:
        """Computes deterministic SHA-256 hash of canonicalized formula."""
        canonical = canonicalize_bound_variables(formula)
        json_str = self._formula_to_json(canonical)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def _get_or_insert_formula(self, formula: Formula) -> int:
        """Inserts formula record into `formulas` table if absent; returns formula_id."""
        canonical = canonicalize_bound_variables(formula)
        ast_hash = self._compute_ast_hash(canonical)

        cursor = self._conn.cursor()
        cursor.execute("SELECT id FROM formulas WHERE ast_hash = ?", (ast_hash,))
        row = cursor.fetchone()
        if row is not None:
            return row[0]

        canonical_str = to_string(canonical)
        json_repr = self._formula_to_json(canonical)
        free_vars = json.dumps(sorted([f"v_{v.id}" for v in free_variables(formula)]))
        preds = json.dumps(sorted(list(extract_predicates(formula))))
        funcs = json.dumps(sorted(list(extract_functions(formula))))
        depth = formula_depth(formula)
        size = formula_size(formula)

        cursor.execute(
            """
            INSERT INTO formulas (ast_hash, canonical_string, json_repr, free_variables, predicate_names, function_names, depth, size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ast_hash, canonical_str, json_repr, free_vars, preds, funcs, depth, size)
        )
        return cursor.lastrowid

    def add_axiom(self, name: str, formula: Formula, category: str = "general") -> None:
        """Registers a named axiom in database. Raises DatabaseError on duplicate name."""
        if self._conn is None:
            raise DatabaseError("Database connection is closed.")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT id FROM axioms WHERE name = ?", (name,))
            if cursor.fetchone() is not None:
                raise DatabaseError(f"Axiom with name '{name}' already exists.")

            formula_id = self._get_or_insert_formula(formula)
            cursor.execute(
                "INSERT INTO axioms (name, formula_id, category) VALUES (?, ?, ?)",
                (name, formula_id, category)
            )
            self._conn.commit()
        except Exception as e:
            if self._conn is not None:
                self._conn.rollback()
            if not isinstance(e, DatabaseError):
                raise DatabaseError(f"Failed to add axiom '{name}': {e}") from e
            raise

    def add_theorem(
        self,
        name: str,
        formula: Formula,
        proof: Optional[ProofDAG] = None,
        category: str = "general"
    ) -> None:
        """Registers a proved theorem and optional proof DAG."""
        if self._conn is None:
            raise DatabaseError("Database connection is closed.")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT id FROM theorems WHERE name = ?", (name,))
            if cursor.fetchone() is not None:
                raise DatabaseError(f"Theorem with name '{name}' already exists.")

            proof_id = None
            if proof is not None:
                if hasattr(proof, "to_dict"):
                    proof_data = proof.to_dict()
                elif isinstance(proof, dict):
                    proof_data = proof
                elif isinstance(proof, str):
                    proof_data = proof
                else:
                    proof_data = str(proof)

                proof_json = json.dumps(proof_data) if not isinstance(proof_data, str) else proof_data

                cursor.execute("SELECT id FROM proofs WHERE theorem_name = ?", (name,))
                existing = cursor.fetchone()
                if existing is not None:
                    proof_id = existing[0]
                else:
                    cursor.execute(
                        "INSERT INTO proofs (theorem_name, proof_json) VALUES (?, ?)",
                        (name, proof_json)
                    )
                    proof_id = cursor.lastrowid

            formula_id = self._get_or_insert_formula(formula)
            cursor.execute(
                "INSERT INTO theorems (name, formula_id, category, proof_id) VALUES (?, ?, ?, ?)",
                (name, formula_id, category, proof_id)
            )
            self._conn.commit()
        except Exception as e:
            if self._conn is not None:
                self._conn.rollback()
            if not isinstance(e, DatabaseError):
                raise DatabaseError(f"Failed to add theorem '{name}': {e}") from e
            raise

    def get_axioms(self, category: Optional[str] = None) -> List[Tuple[str, Formula]]:
        """Retrieves axioms, optionally filtered by category."""
        if self._conn is None:
            raise DatabaseError("Database connection is closed.")

        cursor = self._conn.cursor()
        if category is None:
            cursor.execute(
                "SELECT a.name, f.json_repr FROM axioms a JOIN formulas f ON a.formula_id = f.id ORDER BY a.id"
            )
        else:
            cursor.execute(
                "SELECT a.name, f.json_repr FROM axioms a JOIN formulas f ON a.formula_id = f.id WHERE a.category = ? ORDER BY a.id",
                (category,)
            )

        rows = cursor.fetchall()
        return [(name, self._json_to_formula(json_str)) for name, json_str in rows]

    def get_theorems(self, category: Optional[str] = None) -> List[Tuple[str, Formula]]:
        """Retrieves theorems, optionally filtered by category."""
        if self._conn is None:
            raise DatabaseError("Database connection is closed.")

        cursor = self._conn.cursor()
        if category is None:
            cursor.execute(
                "SELECT t.name, f.json_repr FROM theorems t JOIN formulas f ON t.formula_id = f.id ORDER BY t.id"
            )
        else:
            cursor.execute(
                "SELECT t.name, f.json_repr FROM theorems t JOIN formulas f ON t.formula_id = f.id WHERE t.category = ? ORDER BY t.id",
                (category,)
            )

        rows = cursor.fetchall()
        return [(name, self._json_to_formula(json_str)) for name, json_str in rows]

    def get_proof(self, theorem_name: str) -> Optional[ProofDAG]:
        """Retrieves proof DAG for named theorem."""
        if self._conn is None:
            raise DatabaseError("Database connection is closed.")

        cursor = self._conn.cursor()
        cursor.execute("SELECT proof_json FROM proofs WHERE theorem_name = ?", (theorem_name,))
        row = cursor.fetchone()
        if row is None or row[0] is None:
            return None

        proof_json = row[0]
        try:
            data = json.loads(proof_json)
        except Exception:
            return proof_json

        try:
            from solver.prover.proof import ProofDAG as RealProofDAG
            if hasattr(RealProofDAG, "from_dict") and isinstance(data, dict):
                return RealProofDAG.from_dict(data)
        except Exception:
            pass

        return data

    def contains_formula(self, formula: Formula) -> bool:
        """Checks if formula (or an alpha-equivalent variant) exists in database."""
        if self._conn is None:
            raise DatabaseError("Database connection is closed.")

        ast_hash = self._compute_ast_hash(formula)
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM formulas WHERE ast_hash = ?", (ast_hash,))
        return cursor.fetchone() is not None

    def search_formulas(
        self,
        predicate_name: Optional[str] = None,
        max_depth: Optional[int] = None,
        max_size: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[Formula]:
        """Queries formulas using indexed structural attributes."""
        if self._conn is None:
            raise DatabaseError("Database connection is closed.")

        query = ["SELECT DISTINCT f.json_repr FROM formulas f"]
        conditions = []
        params: List[Any] = []

        if category is not None:
            query.append("LEFT JOIN axioms a ON a.formula_id = f.id LEFT JOIN theorems t ON t.formula_id = f.id")
            conditions.append("(a.category = ? OR t.category = ?)")
            params.extend([category, category])

        if max_depth is not None:
            conditions.append("f.depth <= ?")
            params.append(max_depth)

        if max_size is not None:
            conditions.append("f.size <= ?")
            params.append(max_size)

        if predicate_name is not None:
            conditions.append("f.predicate_names LIKE ?")
            params.append(f'%"{predicate_name}"%')

        if conditions:
            query.append("WHERE " + " AND ".join(conditions))

        sql = " ".join(query)
        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        return [self._json_to_formula(json_str) for (json_str,) in rows]
