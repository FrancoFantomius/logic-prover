import unittest

from logic_prover.core.exceptions import ValidationError
from logic_prover.core.sorts import Ind, Nat, Bool
from logic_prover.core.signature import Signature, FunctionDecl, PredicateDecl


class TestSignature(unittest.TestCase):
    def test_registration_and_retrieval(self) -> None:
        sig = Signature.empty()

        # Function
        sig.register_function("f", 1, (Nat,), return_sort=Nat)
        f_decl = sig.lookup_function("f")
        self.assertIsNotNone(f_decl)
        self.assertEqual(f_decl, FunctionDecl("f", 1, (Nat,), return_sort=Nat))

        # Predicate
        sig.register_predicate("P", 2, (Nat, Bool))
        p_decl = sig.lookup_predicate("P")
        self.assertIsNotNone(p_decl)
        self.assertEqual(p_decl, PredicateDecl("P", 2, (Nat, Bool)))

        # Constant
        sig.register_constant("c", Nat)
        c_sort = sig.lookup_constant("c")
        self.assertEqual(c_sort, Nat)

        # Sort constructor
        sig.register_sort_constructor("Set", 1)
        set_arity = sig.lookup_sort_constructor("Set")
        self.assertEqual(set_arity, 1)

        # Non-existent
        self.assertIsNone(sig.lookup_function("unknown"))
        self.assertIsNone(sig.lookup_predicate("unknown"))
        self.assertIsNone(sig.lookup_constant("unknown"))
        self.assertIsNone(sig.lookup_sort_constructor("unknown"))

        # Has symbol
        self.assertTrue(sig.has_symbol("f"))
        self.assertTrue(sig.has_symbol("P"))
        self.assertTrue(sig.has_symbol("c"))
        self.assertFalse(sig.has_symbol("Set"))
        self.assertFalse(sig.has_symbol("unknown"))

    def test_idempotent_registration(self) -> None:
        sig = Signature.empty()
        sig.register_function("f", 1, (Nat,), return_sort=Nat)
        # Re-registering identical function declaration should not error
        sig.register_function("f", 1, (Nat,), return_sort=Nat)

        sig.register_predicate("P", 1, (Bool,))
        sig.register_predicate("P", 1, (Bool,))

        sig.register_constant("c", Nat)
        sig.register_constant("c", Nat)

        sig.register_sort_constructor("Set", 1)
        sig.register_sort_constructor("Set", 1)

    def test_conflict_prevention_cross_type(self) -> None:
        sig = Signature.empty()
        sig.register_function("foo", 1, (Nat,))

        with self.assertRaises(ValidationError):
            sig.register_predicate("foo", 1, (Nat,))

        with self.assertRaises(ValidationError):
            sig.register_constant("foo", Nat)

        sig2 = Signature.empty()
        sig2.register_constant("bar", Nat)

        with self.assertRaises(ValidationError):
            sig2.register_function("bar", 0, ())

        with self.assertRaises(ValidationError):
            sig2.register_predicate("bar", 0, ())

    def test_conflict_prevention_same_type_different_signature(self) -> None:
        sig = Signature.empty()
        sig.register_function("f", 1, (Nat,))

        with self.assertRaises(ValidationError):
            sig.register_function("f", 2, (Nat, Nat))

        with self.assertRaises(ValidationError):
            sig.register_function("f", 1, (Bool,))

        with self.assertRaises(ValidationError):
            sig.register_function("f", 1, (Nat,), return_sort=Bool)

    def test_invalid_declaration_values(self) -> None:
        with self.assertRaises(ValueError):
            FunctionDecl("f", -1, ())

        with self.assertRaises(ValueError):
            FunctionDecl("f", 2, (Nat,))

        with self.assertRaises(ValueError):
            PredicateDecl("P", -1, ())

        with self.assertRaises(ValueError):
            PredicateDecl("P", 1, (Nat, Bool))

        sig = Signature.empty()
        with self.assertRaises(ValueError):
            sig.register_sort_constructor("List", -1)

    def test_merge_signatures(self) -> None:
        sig1 = Signature.empty()
        sig1.register_function("f", 1, (Nat,), return_sort=Nat)
        sig1.register_constant("c1", Nat)

        sig2 = Signature.empty()
        sig2.register_predicate("P", 1, (Nat,))
        sig2.register_constant("c2", Bool)

        merged = sig1.merge(sig2)
        self.assertTrue(merged.has_symbol("f"))
        self.assertTrue(merged.has_symbol("c1"))
        self.assertTrue(merged.has_symbol("P"))
        self.assertTrue(merged.has_symbol("c2"))

    def test_merge_conflict(self) -> None:
        sig1 = Signature.empty()
        sig1.register_function("f", 1, (Nat,))

        sig2 = Signature.empty()
        sig2.register_predicate("f", 1, (Nat,))

        with self.assertRaises(ValidationError):
            sig1.merge(sig2)

    def test_clone(self) -> None:
        sig = Signature.empty()
        sig.register_function("f", 1, (Nat,))
        cloned = sig.clone()
        cloned.register_constant("c", Nat)

        self.assertTrue(cloned.has_symbol("c"))
        self.assertFalse(sig.has_symbol("c"))


if __name__ == "__main__":
    unittest.main()
