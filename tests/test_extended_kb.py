from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality, Forall, Implies, And, Not, Iff
)
from logic_prover.core.sorts import PrimitiveSort, SetSort, Ind
from logic_prover.core.validator import validate_formula
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.prover.engine import TheoremProver
from logic_prover.kb import (
    get_all_axioms,
    get_extended_axioms,
    get_combined_signature,
    get_group_signature,
    get_group_axioms,
    get_relation_signature,
    get_relation_axioms,
    get_order_signature,
    get_partial_order_axioms,
    get_total_order_axioms,
    get_set_signature,
    get_set_theory_axioms,
    get_function_signature,
    get_function_axioms,
)
from logic_prover.kb.groups import GroupElem
from logic_prover.kb.relations import RelElem
from logic_prover.kb.orders import OrderElem
from logic_prover.kb.sets import ElemSort, SetType
from logic_prover.kb.functions import Dom, Codom, FuncSort


class TestExtendedKB(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_extended.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # --- 1. Signature Well-Formedness Tests ---

    def test_group_signature_well_formed(self) -> None:
        sig = get_group_signature()
        self.assertTrue(sig.has_symbol("e"))
        self.assertTrue(sig.has_symbol("op"))
        self.assertTrue(sig.has_symbol("inv"))

        op_decl = sig.lookup_function("op")
        self.assertIsNotNone(op_decl)
        self.assertEqual(op_decl.arity, 2)
        self.assertEqual(op_decl.arg_sorts, (GroupElem, GroupElem))
        self.assertEqual(op_decl.return_sort, GroupElem)

        inv_decl = sig.lookup_function("inv")
        self.assertIsNotNone(inv_decl)
        self.assertEqual(inv_decl.arity, 1)
        self.assertEqual(inv_decl.arg_sorts, (GroupElem,))
        self.assertEqual(inv_decl.return_sort, GroupElem)

        e_sort = sig.lookup_constant("e")
        self.assertEqual(e_sort, GroupElem)

    def test_relation_signature_well_formed(self) -> None:
        sig = get_relation_signature()
        self.assertTrue(sig.has_symbol("R"))
        self.assertTrue(sig.has_symbol("EqRel"))

        r_decl = sig.lookup_predicate("R")
        self.assertIsNotNone(r_decl)
        self.assertEqual(r_decl.arity, 2)
        self.assertEqual(r_decl.arg_sorts, (RelElem, RelElem))

    def test_order_signature_well_formed(self) -> None:
        sig = get_order_signature()
        self.assertTrue(sig.has_symbol("le"))
        self.assertTrue(sig.has_symbol("lt"))
        self.assertTrue(sig.has_symbol("ge"))

        le_decl = sig.lookup_predicate("le")
        self.assertIsNotNone(le_decl)
        self.assertEqual(le_decl.arity, 2)
        self.assertEqual(le_decl.arg_sorts, (Ind, Ind))

        lt_decl = sig.lookup_predicate("lt")
        self.assertIsNotNone(lt_decl)
        self.assertEqual(lt_decl.arity, 2)
        self.assertEqual(lt_decl.arg_sorts, (Ind, Ind))

    def test_set_signature_well_formed(self) -> None:
        sig = get_set_signature()
        self.assertTrue(sig.has_symbol("in_set"))
        self.assertTrue(sig.has_symbol("subset"))
        self.assertTrue(sig.has_symbol("empty_set"))
        self.assertTrue(sig.has_symbol("union"))
        self.assertTrue(sig.has_symbol("inter"))
        self.assertTrue(sig.has_symbol("diff"))
        self.assertTrue(sig.has_symbol("singleton"))
        self.assertTrue(sig.has_symbol("powerset"))
        self.assertEqual(sig.lookup_sort_constructor("Set"), 1)

    def test_function_signature_well_formed(self) -> None:
        sig = get_function_signature()
        self.assertTrue(sig.has_symbol("apply"))
        self.assertTrue(sig.has_symbol("comp"))
        self.assertTrue(sig.has_symbol("id_func"))
        self.assertTrue(sig.has_symbol("is_injective"))
        self.assertTrue(sig.has_symbol("is_surjective"))
        self.assertTrue(sig.has_symbol("is_bijective"))

    def test_combined_signature_well_formed(self) -> None:
        combined = get_combined_signature()
        self.assertTrue(combined.has_symbol("op"))
        self.assertTrue(combined.has_symbol("R"))
        self.assertTrue(combined.has_symbol("le"))
        self.assertTrue(combined.has_symbol("in_set"))
        self.assertTrue(combined.has_symbol("apply"))
        self.assertTrue(combined.has_symbol("zero"))

    # --- 2. AST Validation Tests ---

    def test_group_axioms_validation(self) -> None:
        sig = get_group_signature()
        for name, formula in get_group_axioms():
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"Group axiom '{name}' failed validation: {errors}")

    def test_relation_axioms_validation(self) -> None:
        sig = get_relation_signature()
        for name, formula in get_relation_axioms():
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"Relation axiom '{name}' failed validation: {errors}")

    def test_order_axioms_validation(self) -> None:
        sig = get_order_signature()
        for name, formula in get_partial_order_axioms():
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"Partial order axiom '{name}' failed validation: {errors}")

        for name, formula in get_total_order_axioms():
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"Total order axiom '{name}' failed validation: {errors}")

    def test_set_axioms_validation(self) -> None:
        sig = get_set_signature()
        for name, formula in get_set_theory_axioms():
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"Set theory axiom '{name}' failed validation: {errors}")

    def test_function_axioms_validation(self) -> None:
        sig = get_function_signature()
        for name, formula in get_function_axioms():
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"Function axiom '{name}' failed validation: {errors}")

    def test_get_extended_axioms_validation(self) -> None:
        sig = get_combined_signature()
        extended = get_extended_axioms()
        self.assertGreater(len(extended), 0)
        for name, formula, category in extended:
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"Extended axiom '{name}' ({category}) failed validation: {errors}")

    def test_get_all_axioms_validation(self) -> None:
        sig = get_combined_signature()
        all_axioms = get_all_axioms()
        self.assertGreater(len(all_axioms), 20)
        for name, formula, category in all_axioms:
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"All axioms entry '{name}' ({category}) failed validation: {errors}")

    # --- 3. Database Integration Tests ---

    def test_database_extended_axioms_population(self) -> None:
        db = KnowledgeDatabase(self.db_path)
        all_axioms = get_all_axioms()

        for name, formula, category in all_axioms:
            db.add_axiom(name, formula, category)

        group_axioms = db.get_axioms("groups")
        relation_axioms = db.get_axioms("relations")
        order_axioms = db.get_axioms("orders")
        set_axioms = db.get_axioms("sets")
        func_axioms = db.get_axioms("functions")

        self.assertEqual(len(group_axioms), len(get_group_axioms()))
        self.assertEqual(len(relation_axioms), len(get_relation_axioms()))
        self.assertEqual(len(order_axioms), len(get_total_order_axioms()))
        self.assertEqual(len(set_axioms), len(get_set_theory_axioms()))
        self.assertEqual(len(func_axioms), len(get_function_axioms()))
        db.close()

    # --- 4. Prover Derivation Tests Across Extended Domains ---

    def test_group_prover_derivation(self) -> None:
        sig = get_group_signature()
        v0 = Variable(0, sort=GroupElem)
        e = Constant("e", sort=GroupElem)
        i = Variable(0, sort=GroupElem)
        x = Variable(1, sort=GroupElem)

        id_right = Forall(v0, Equality(FunctionApp("op", 2, (v0, e), return_sort=GroupElem), v0))
        op_i_x = FunctionApp("op", 2, (i, x), return_sort=GroupElem)
        target = Forall(i, Implies(Forall(x, Equality(op_i_x, x)), Equality(i, e)))

        prover = TheoremProver(signature=sig)
        proof = prover.prove(target=target, premises=[id_right], timeout_sec=5.0)
        self.assertTrue(proof.is_valid())

    def test_relation_prover_derivation(self) -> None:
        sig = get_relation_signature()
        x = Variable(0, sort=RelElem)
        y = Variable(1, sort=RelElem)
        z = Variable(2, sort=RelElem)

        r_xx = PredicateApp("R", 2, (x, x))
        r_xy = PredicateApp("R", 2, (x, y))
        r_yz = PredicateApp("R", 2, (y, z))
        r_xz = PredicateApp("R", 2, (x, z))
        r_yx = PredicateApp("R", 2, (y, x))

        rel_irreflexive = Forall(x, Not(r_xx))
        rel_transitive = Forall(x, Forall(y, Forall(z, Implies(And(r_xy, r_yz), r_xz))))
        target = Forall(x, Forall(y, Implies(r_xy, Not(r_yx))))

        prover = TheoremProver(signature=sig)
        proof = prover.prove(target=target, premises=[rel_irreflexive, rel_transitive], timeout_sec=5.0)
        self.assertTrue(proof.is_valid())

    def test_order_prover_derivation(self) -> None:
        sig = get_order_signature()
        x = Variable(0, sort=OrderElem)
        y = Variable(1, sort=OrderElem)

        le_xy = PredicateApp("le", 2, (x, y))
        lt_xy = PredicateApp("lt", 2, (x, y))
        lt_xx = PredicateApp("lt", 2, (x, x))

        po_lt_def = Forall(x, Forall(y, Iff(lt_xy, And(le_xy, Not(Equality(x, y))))))
        target = Forall(x, Not(lt_xx))

        prover = TheoremProver(signature=sig)
        proof = prover.prove(target=target, premises=[po_lt_def], timeout_sec=5.0)
        self.assertTrue(proof.is_valid())

    def test_set_prover_derivation(self) -> None:
        sig = get_set_signature()
        A = Variable(0, sort=SetType)
        B = Variable(1, sort=SetType)
        C = Variable(2, sort=SetType)
        x = Variable(3, sort=ElemSort)

        in_xA = PredicateApp("in_set", 2, (x, A))
        in_xB = PredicateApp("in_set", 2, (x, B))

        sub_AB = PredicateApp("subset", 2, (A, B))
        sub_BC = PredicateApp("subset", 2, (B, C))
        sub_AC = PredicateApp("subset", 2, (A, C))

        set_subset_def = Forall(A, Forall(B, Iff(sub_AB, Forall(x, Implies(in_xA, in_xB)))))
        target = Forall(A, Forall(B, Forall(C, Implies(And(sub_AB, sub_BC), sub_AC))))

        prover = TheoremProver(signature=sig)
        proof = prover.prove(target=target, premises=[set_subset_def], timeout_sec=5.0)
        self.assertTrue(proof.is_valid())

    def test_function_prover_derivation(self) -> None:
        sig = get_function_signature()
        f = Variable(0, sort=FuncSort)

        bij_f = PredicateApp("is_bijective", 1, (f,))
        inj_f = PredicateApp("is_injective", 1, (f,))
        surj_f = PredicateApp("is_surjective", 1, (f,))

        func_bijective_def = Forall(f, Iff(bij_f, And(inj_f, surj_f)))
        target = Forall(f, Implies(bij_f, inj_f))

        prover = TheoremProver(signature=sig)
        proof = prover.prove(target=target, premises=[func_bijective_def], timeout_sec=5.0)
        self.assertTrue(proof.is_valid())


if __name__ == "__main__":
    unittest.main()
