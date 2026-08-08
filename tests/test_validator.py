import unittest

from logic.core.exceptions import ValidationError
from logic.core.sorts import Ind, Nat, Bool, SetSort
from logic.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists, VariableKind
)
from logic.core.signature import Signature
from logic.core.validator import validate_term, validate_formula, is_well_formed


class TestValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.sig = Signature.empty()
        self.sig.register_constant("c_nat", Nat)
        self.sig.register_constant("c_bool", Bool)
        self.sig.register_constant("c_ind", Ind)
        self.sig.register_function("f_nat", 1, (Nat,), return_sort=Nat)
        self.sig.register_function("add", 2, (Nat, Nat), return_sort=Nat)
        self.sig.register_predicate("P_nat", 1, (Nat,))
        self.sig.register_predicate("Q_two", 2, (Nat, Bool))

    def test_valid_terms_and_formulas(self) -> None:
        v0 = Variable(0, sort=Nat)
        v1 = Variable(1, sort=Bool)

        # Valid term
        term = FunctionApp("add", 2, (v0, Constant("c_nat", sort=Nat)), return_sort=Nat)
        errors = validate_term(term, self.sig)
        self.assertEqual(len(errors), 0)
        self.assertTrue(is_well_formed(term, self.sig))

        # Valid formula
        formula = Forall(
            v0,
            Exists(
                v1,
                And(
                    PredicateApp("P_nat", 1, (v0,)),
                    PredicateApp("Q_two", 2, (v0, v1)),
                ),
            ),
        )
        errors = validate_formula(formula, self.sig)
        self.assertEqual(len(errors), 0)
        self.assertTrue(is_well_formed(formula, self.sig))

    def test_unregistered_symbols(self) -> None:
        # Unregistered constant
        const_unreg = Constant("unknown_const", sort=Nat)
        errors = validate_term(const_unreg, self.sig)
        self.assertEqual(len(errors), 1)
        self.assertFalse(is_well_formed(const_unreg, self.sig))

        # Unregistered function
        func_unreg = FunctionApp("unknown_func", 1, (Constant("c_nat", sort=Nat),))
        errors = validate_term(func_unreg, self.sig)
        self.assertEqual(len(errors), 1)

        # Unregistered predicate
        pred_unreg = PredicateApp("unknown_pred", 1, (Constant("c_nat", sort=Nat),))
        errors = validate_formula(pred_unreg, self.sig)
        self.assertEqual(len(errors), 1)

    def test_arity_mismatches(self) -> None:
        # Function declared with arity 1, applied with arity 2 in AST (with arity field=2)
        func_arity_mismatch = FunctionApp("f_nat", 2, (Constant("c_nat", sort=Nat), Constant("c_nat", sort=Nat)))
        errors = validate_term(func_arity_mismatch, self.sig)
        self.assertTrue(any("arity mismatch" in str(e) for e in errors))

        # Predicate declared with arity 2, applied with arity 1
        pred_arity_mismatch = PredicateApp("Q_two", 1, (Constant("c_nat", sort=Nat),))
        errors = validate_formula(pred_arity_mismatch, self.sig)
        self.assertTrue(any("arity mismatch" in str(e) for e in errors))

    def test_sort_mismatches(self) -> None:
        # Function expected Nat argument, got Bool
        func_sort_err = FunctionApp("f_nat", 1, (Constant("c_bool", sort=Bool),))
        errors = validate_term(func_sort_err, self.sig)
        self.assertTrue(any("sort mismatch" in str(e) for e in errors))

        # Equality of incompatible sorts Nat vs Bool
        eq_err = Equality(Constant("c_nat", sort=Nat), Constant("c_bool", sort=Bool))
        errors = validate_formula(eq_err, self.sig)
        self.assertTrue(any("Equality sort mismatch" in str(e) for e in errors))

        # Parameterized sort mismatch: Set(Nat) vs Set(Bool)
        set_nat = SetSort(Nat)
        set_bool = SetSort(Bool)
        self.sig.register_constant("s_nat", set_nat)
        self.sig.register_constant("s_bool", set_bool)
        eq_set_err = Equality(Constant("s_nat", sort=set_nat), Constant("s_bool", sort=set_bool))
        errors = validate_formula(eq_set_err, self.sig)
        self.assertTrue(any("Equality sort mismatch" in str(e) for e in errors))

    def test_ind_compatibility(self) -> None:
        # Ind is compatible with Nat
        v_ind = Variable(0, sort=Ind)
        term = FunctionApp("f_nat", 1, (v_ind,), return_sort=Nat)
        errors = validate_term(term, self.sig)
        self.assertEqual(len(errors), 0)

        eq_ind = Equality(Constant("c_nat", sort=Nat), Constant("c_ind", sort=Ind))
        errors = validate_formula(eq_ind, self.sig)
        self.assertEqual(len(errors), 0)

    def test_quantifier_and_scoping_validation(self) -> None:
        v0 = Variable(0, sort=Nat)

        # Duplicate/shadowed binder v0 in nested quantifier
        dup_quant = Forall(v0, Forall(v0, PredicateApp("P_nat", 1, (v0,))))
        errors = validate_formula(dup_quant, self.sig)
        self.assertTrue(any("Duplicate binder in scope" in str(e) for e in errors))
        self.assertFalse(is_well_formed(dup_quant, self.sig))

        # Non-INDIVIDUAL variable kind in FOL validator
        v_pred = Variable(0, sort=Nat, kind=VariableKind.PREDICATE)
        fol_kind_err = Exists(v_pred, PredicateApp("P_nat", 1, (v0,)))
        errors = validate_formula(fol_kind_err, self.sig)
        self.assertTrue(any("INDIVIDUAL kind" in str(e) for e in errors))

    def test_nested_boolean_formulas(self) -> None:
        v0 = Variable(0, sort=Nat)
        v1 = Variable(1, sort=Bool)

        p = PredicateApp("P_nat", 1, (v0,))
        q = PredicateApp("Q_two", 2, (v0, v1))

        # Not, Or, Implies, Iff
        formula = Iff(
            Implies(p, q),
            Or(Not(p), q)
        )
        self.assertTrue(is_well_formed(formula, self.sig))


if __name__ == "__main__":
    unittest.main()
