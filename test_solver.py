import unittest
import os
from formula import parse_formula, Var, Not, Implies
from database import TheoryDatabase
from prover import prove
from verifier import verify_and_save, verify_proof_local
from explorer import generate_candidates, explore_consequences

class TestFormula(unittest.TestCase):
    def test_parsing(self):
        f = parse_formula("p -> (q -> p)")
        self.assertEqual(str(f), "(p -> (q -> p))")
        self.assertIsInstance(f, Implies)
        self.assertIsInstance(f.left, Var)
        self.assertEqual(f.left.name, "p")
        
        f2 = parse_formula("~p -> q")
        self.assertEqual(str(f2), "(~p -> q)")
        
    def test_operators(self):
        p = Var("p")
        q = Var("q")
        f = p >> (q >> p)
        self.assertEqual(str(f), "(p -> (q -> p))")
        
        f2 = ~p >> q
        self.assertEqual(str(f2), "(~p -> q)")
        
    def test_free_variables(self):
        f = parse_formula("(p -> q) -> (~r -> p)")
        self.assertEqual(f.free_variables(), {"p", "q", "r"})
        
    def test_match_schema(self):
        schema = parse_formula("A -> (B -> A)")
        f = parse_formula("p -> (q -> p)")
        bindings = f.match_schema(schema)
        self.assertIsNotNone(bindings)
        self.assertEqual(bindings, {"A": Var("p"), "B": Var("q")})
        
        # Caso di matching incoerente (A mappa a due formule diverse)
        f_bad = parse_formula("p -> (q -> r)")
        self.assertIsNone(f_bad.match_schema(schema))
        
        f_bad2 = parse_formula("p -> (p -> q)")
        # A -> (B -> A) con p -> (p -> q).
        # A deve mappare sia a p che a q -> match fallito
        self.assertIsNone(f_bad2.match_schema(schema))
        
class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_theory.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = TheoryDatabase(self.db_path)
        
    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
            
    def test_axioms(self):
        self.db.add_axiom("ax1", "A -> (B -> A)")
        self.assertEqual(self.db.get_axiom("ax1"), "A -> (B -> A)")
        
    def test_theorems_and_dependencies(self):
        # Aggiunge assioma
        self.db.add_axiom("ax1", "A -> (B -> A)")
        
        # Salva teorema 1 (lemma)
        steps1 = [
            {'step_idx': 0, 'formula_str': 'p -> (p -> p)', 'justification_type': 'Axiom', 'ref_name': 'ax1', 'substitution_json': {'A': 'p', 'B': 'p'}}
        ]
        self.db.save_theorem("thm1", "p -> (p -> p)", [], steps1, is_verified=1)
        
        # Salva teorema 2 che dipende da thm1
        steps2 = [
            {'step_idx': 0, 'formula_str': 'p -> (p -> p)', 'justification_type': 'Lemma', 'ref_name': 'thm1', 'substitution_json': {'p': 'p'}, 'arg1': None}
        ]
        self.db.save_theorem("thm2", "p -> (p -> p)", [], steps2, dependencies=["thm1"], is_verified=1)
        
        deps = self.db.get_dependencies_recursive("thm2")
        self.assertEqual(deps, ["thm1"])
        
class TestVerifier(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_verifier.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = TheoryDatabase(self.db_path)
        self.db.add_axiom("ax1", "A -> (B -> A)")
        self.db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")
        self.db.add_axiom("ax3", "(~A -> ~B) -> (B -> A)")
        
    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
            
    def test_local_verification(self):
        # Dimostrazione valida (p -> p)
        proof = prove("p -> p", [], self.db)
        thm = {
            'name': 'identity',
            'thesis_str': 'p -> p',
            'hypotheses': [],
            'steps': proof
        }
        ok, err = verify_proof_local(thm, self.db)
        self.assertTrue(ok)
        self.assertIsNone(err)
        
        # Dimostrazione non valida per tesi non corrispondente
        thm_invalid = {
            'name': 'identity_invalid',
            'thesis_str': 'p -> q',
            'hypotheses': [],
            'steps': proof  # l'ultimo passo è p -> p, ma la tesi attesa è p -> q
        }
        ok, err = verify_proof_local(thm_invalid, self.db)
        self.assertFalse(ok)
        self.assertIn("non coincide con la tesi", err)

class TestExplorer(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_explorer.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = TheoryDatabase(self.db_path)
        self.db.add_axiom("ax1", "A -> (B -> A)")
        self.db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")
        self.db.add_axiom("ax3", "(~A -> ~B) -> (B -> A)")
        
    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
                
    def test_candidate_generation(self):
        candidates = generate_candidates(['p'], 1)
        self.assertEqual(len(candidates), 3)
        self.assertIn(Var('p'), candidates)
        self.assertIn(Not(Var('p')), candidates)
        self.assertIn(Implies(Var('p'), Var('p')), candidates)
        
    def test_exploration(self):
        count = explore_consequences(self.db, basic_vars=['p'], max_depth=2, max_theorems=2)
        self.assertGreaterEqual(count, 1)
        
        # Recupera il primo teorema trovato (dovrebbe essere p -> p)
        thm = self.db.get_theorem("thm_1")
        self.assertIsNotNone(thm)
        self.assertEqual(thm['is_verified'], 1)

if __name__ == "__main__":
    from explorer import generate_candidates, explore_consequences
    unittest.main()
