import sqlite3
import json
import os
import contextlib

class TheoryDatabase:
    def __init__(self, db_path="theory.db"):
        self.db_path = db_path
        self.init_db()

    @contextlib.contextmanager
    def connection_scope(self):
        """Context manager for managing and properly closing SQLite database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        with self.connection_scope() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS axioms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                formula_str TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS theorems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                thesis_str TEXT NOT NULL,
                lean_code TEXT,
                is_verified INTEGER NOT NULL CHECK(is_verified IN (0, 1))
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS theorem_hypotheses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theorem_id INTEGER NOT NULL REFERENCES theorems(id) ON DELETE CASCADE,
                hypothesis_idx INTEGER NOT NULL,
                formula_str TEXT NOT NULL,
                UNIQUE(theorem_id, hypothesis_idx)
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS theorem_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theorem_id INTEGER NOT NULL REFERENCES theorems(id) ON DELETE CASCADE,
                step_idx INTEGER NOT NULL,
                formula_str TEXT NOT NULL,
                justification_type TEXT NOT NULL CHECK(justification_type IN ('Axiom', 'Hypothesis', 'MP', 'Lemma')),
                arg1 INTEGER,
                arg2 INTEGER,
                ref_name TEXT,
                substitution_json TEXT,
                UNIQUE(theorem_id, step_idx),
                CHECK(justification_type != 'MP' OR (arg1 IS NOT NULL AND arg2 IS NOT NULL)),
                CHECK(justification_type != 'Axiom' OR ref_name IS NOT NULL),
                CHECK(justification_type != 'Lemma' OR ref_name IS NOT NULL)
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS dependencies (
                theorem_id INTEGER NOT NULL REFERENCES theorems(id) ON DELETE CASCADE,
                depends_on_theorem_id INTEGER NOT NULL REFERENCES theorems(id) ON DELETE CASCADE,
                PRIMARY KEY (theorem_id, depends_on_theorem_id)
            );
            """)
            conn.commit()

    def add_axiom(self, name, formula_str):
        with self.connection_scope() as conn:
            try:
                conn.execute(
                    "INSERT INTO axioms (name, formula_str) VALUES (?, ?);",
                    (name, formula_str)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # If axiom already exists, do nothing
                pass

    def get_axiom(self, name):
        with self.connection_scope() as conn:
            cursor = conn.execute("SELECT formula_str FROM axioms WHERE name = ?;", (name,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_all_axioms(self):
        with self.connection_scope() as conn:
            cursor = conn.execute("SELECT name, formula_str FROM axioms;")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_theorem(self, name):
        with self.connection_scope() as conn:
            cursor = conn.execute(
                "SELECT id, name, thesis_str, lean_code, is_verified FROM theorems WHERE name = ?;",
                (name,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            thm_id, thm_name, thesis_str, lean_code, is_verified = row
            
            # Load hypotheses
            cursor = conn.execute(
                "SELECT formula_str FROM theorem_hypotheses WHERE theorem_id = ? ORDER BY hypothesis_idx;",
                (thm_id,)
            )
            hypotheses = [r[0] for r in cursor.fetchall()]
            
            # Load steps
            cursor = conn.execute(
                "SELECT step_idx, formula_str, justification_type, arg1, arg2, ref_name, substitution_json "
                "FROM theorem_steps WHERE theorem_id = ? ORDER BY step_idx;",
                (thm_id,)
            )
            steps = []
            for r in cursor.fetchall():
                steps.append({
                    'step_idx': r[0],
                    'formula_str': r[1],
                    'justification_type': r[2],
                    'arg1': r[3],
                    'arg2': r[4],
                    'ref_name': r[5],
                    'substitution_json': json.loads(r[6]) if r[6] else None
                })
                
            return {
                'id': thm_id,
                'name': thm_name,
                'thesis_str': thesis_str,
                'lean_code': lean_code,
                'is_verified': is_verified,
                'hypotheses': hypotheses,
                'steps': steps
            }

    def save_theorem(self, name, thesis_str, hypotheses, steps, dependencies=None, lean_code=None, is_verified=0):
        # Validate MP step indices
        for step in steps:
            step_idx = step['step_idx']
            if step['justification_type'] == 'MP':
                arg1 = step['arg1']
                arg2 = step['arg2']
                if arg1 >= step_idx or arg2 >= step_idx:
                    raise ValueError(
                        f"In step {step_idx}: MP arguments ({arg1}, {arg2}) must be less than step_idx."
                    )

        with self.connection_scope() as conn:
            # Remove previous versions to ensure cleanliness
            conn.execute("DELETE FROM theorems WHERE name = ?;", (name,))
            
            cursor = conn.execute(
                "INSERT INTO theorems (name, thesis_str, lean_code, is_verified) VALUES (?, ?, ?, ?);",
                (name, thesis_str, lean_code, is_verified)
            )
            thm_id = cursor.lastrowid
            
            for idx, hyp_str in enumerate(hypotheses):
                conn.execute(
                    "INSERT INTO theorem_hypotheses (theorem_id, hypothesis_idx, formula_str) VALUES (?, ?, ?);",
                    (thm_id, idx, hyp_str)
                )
                
            for step in steps:
                sub_json = json.dumps(step.get('substitution_json')) if step.get('substitution_json') is not None else None
                conn.execute(
                    "INSERT INTO theorem_steps (theorem_id, step_idx, formula_str, justification_type, arg1, arg2, ref_name, substitution_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                    (thm_id, step['step_idx'], step['formula_str'], step['justification_type'], step.get('arg1'), step.get('arg2'), step.get('ref_name'), sub_json)
                )
                
            if dependencies:
                for dep_name in dependencies:
                    dep_cursor = conn.execute("SELECT id FROM theorems WHERE name = ?;", (dep_name,))
                    dep_row = dep_cursor.fetchone()
                    if dep_row:
                        conn.execute(
                            "INSERT OR IGNORE INTO dependencies (theorem_id, depends_on_theorem_id) VALUES (?, ?);",
                            (thm_id, dep_row[0])
                        )
            conn.commit()

    def get_dependencies_recursive(self, theorem_name):
        """
        Returns the dependency tree in topological order (independent lemmas come first).
        """
        with self.connection_scope() as conn:
            cursor = conn.execute("SELECT id, name FROM theorems;")
            id_to_name = {row[0]: row[1] for row in cursor.fetchall()}
            name_to_id = {v: k for k, v in id_to_name.items()}
            
            if theorem_name not in name_to_id:
                return []
                
            target_id = name_to_id[theorem_name]
            
            cursor = conn.execute("SELECT theorem_id, depends_on_theorem_id FROM dependencies;")
            adj = {}
            for t_id, dep_id in cursor.fetchall():
                if t_id not in adj:
                    adj[t_id] = []
                adj[t_id].append(dep_id)
                
            visited = set()
            rec_stack = set()
            result = []
            
            def dfs(node_id):
                if node_id in rec_stack:
                    return
                if node_id in visited:
                    return
                rec_stack.add(node_id)
                deps = adj.get(node_id, [])
                for d in deps:
                    dfs(d)
                rec_stack.remove(node_id)
                visited.add(node_id)
                if node_id != target_id:
                    result.append(id_to_name[node_id])
                    
            dfs(target_id)
            return result
