import unittest
from dataclasses import FrozenInstanceError

from logic.core.exceptions import InvalidFormulaError
from logic.core.sorts import (
    Sort,
    PrimitiveSort,
    ParameterizedSort,
    FunctionSort,
    Ind,
    Nat,
    Bool,
    SetSort,
    ListSort,
    PairSort,
    is_compatible,
    sort_of_term,
)
from logic.core.ast import Variable, Constant, FunctionApp


class TestSorts(unittest.TestCase):

    def test_primitive_sorts(self) -> None:
        self.assertEqual(Ind.name, "Ind")
        self.assertEqual(str(Ind), "Ind")
        self.assertEqual(Nat.name, "Nat")
        self.assertEqual(str(Nat), "Nat")
        self.assertEqual(Bool.name, "Bool")
        self.assertEqual(str(Bool), "Bool")

        # Immutability check
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            Ind.sort_name = "Other"  # type: ignore

        # Validation check
        with self.assertRaises(InvalidFormulaError):
            PrimitiveSort("")

    def test_parameterized_sorts(self) -> None:
        set_nat = SetSort(Nat)
        self.assertEqual(set_nat.name, "Set(Nat)")
        self.assertEqual(str(set_nat), "Set(Nat)")

        list_bool = ListSort(Bool)
        self.assertEqual(list_bool.name, "List(Bool)")

        pair_nat_ind = PairSort(Nat, Ind)
        self.assertEqual(pair_nat_ind.name, "Pair(Nat, Ind)")

        nested_set = SetSort(SetSort(Nat))
        self.assertEqual(nested_set.name, "Set(Set(Nat))")

        with self.assertRaises(InvalidFormulaError):
            ParameterizedSort("", (Nat,))

        with self.assertRaises(InvalidFormulaError):
            ParameterizedSort("Set", ())

    def test_function_sorts(self) -> None:
        func_sort = FunctionSort((Nat, Bool), Ind)
        self.assertEqual(func_sort.name, "(Nat, Bool) -> Ind")
        self.assertEqual(str(func_sort), "(Nat, Bool) -> Ind")

    def test_sort_compatibility(self) -> None:
        # Identity
        self.assertTrue(is_compatible(Nat, Nat))
        self.assertTrue(is_compatible(Ind, Ind))

        # Primitive mismatch
        self.assertFalse(is_compatible(Nat, Bool))

        # Wildcard Ind matching primitive & parameterized
        self.assertTrue(is_compatible(Ind, Nat))
        self.assertTrue(is_compatible(Nat, Ind))
        self.assertTrue(is_compatible(Ind, SetSort(Nat)))
        self.assertTrue(is_compatible(SetSort(Nat), Ind))

        # Wildcard Ind matching FunctionSort should be False
        func_sort = FunctionSort((Nat,), Bool)
        self.assertFalse(is_compatible(Ind, func_sort))
        self.assertFalse(is_compatible(func_sort, Ind))

        # Parameterized compatibility
        self.assertTrue(is_compatible(SetSort(Nat), SetSort(Nat)))
        self.assertFalse(is_compatible(SetSort(Nat), SetSort(Bool)))
        self.assertTrue(is_compatible(SetSort(Ind), SetSort(Nat)))
        self.assertTrue(is_compatible(SetSort(Nat), SetSort(Ind)))
        self.assertFalse(is_compatible(SetSort(Nat), ListSort(Nat)))
        self.assertFalse(is_compatible(PairSort(Nat, Bool), PairSort(Nat, Nat)))

        # FunctionSort compatibility
        f1 = FunctionSort((Nat,), Bool)
        f2 = FunctionSort((Nat,), Bool)
        f3 = FunctionSort((Ind,), Bool)
        f4 = FunctionSort((Nat, Nat), Bool)
        self.assertTrue(is_compatible(f1, f2))
        self.assertTrue(is_compatible(f1, f3))
        self.assertFalse(is_compatible(f1, f4))

    def test_sort_of_term(self) -> None:
        v = Variable(id=0, sort=Nat)
        self.assertEqual(sort_of_term(v), Nat)

        c = Constant(name="c", sort=Bool)
        self.assertEqual(sort_of_term(c), Bool)

        c_ctx = Constant(name="c_ctx", sort=Ind)
        self.assertEqual(sort_of_term(c_ctx, context={"c_ctx": Nat}), Nat)

        f_app = FunctionApp(func="f", arity=1, args=(v,), return_sort=Nat)
        self.assertEqual(sort_of_term(f_app), Nat)

        f_app_ctx = FunctionApp(func="f_ctx", arity=1, args=(v,), return_sort=Ind)
        func_sort = FunctionSort((Nat,), Bool)
        self.assertEqual(sort_of_term(f_app_ctx, context={"f_ctx": func_sort}), Bool)

        with self.assertRaises(InvalidFormulaError):
            sort_of_term("not_a_term")  # type: ignore


if __name__ == "__main__":
    unittest.main()
