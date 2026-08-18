"""Unit and regression tests for Constructive Resolution (Prefixed and Translation) for IPC."""

from __future__ import annotations
import unittest

from logic_prover.core.ast import (
    PredicateApp, Equality, Not, And, Or, Implies, Iff
)
from logic_prover.constructive.prefix import (
    Prefix, PrefixConstant, PrefixVariable, PrefixSubstitution
)
from logic_prover.constructive.common import FALSUM
from logic_prover.constructive.resolution import (
    PrefixedLiteral,
    PrefixedClause,
    PrefixedResolutionStep,
    PrefixedResolutionProofResult,
    clausify_prefixed,
    resolve_prefixed_clauses,
    factor_prefixed_clause,
    PrefixedResolutionProver,
    prove_prefixed_resolution,
    translate_ipc_to_fol,
    get_frame_axioms,
    TranslationResolutionResult,
    TranslationResolutionProver,
    prove_translation_resolution,
    ConstructiveResolutionProver,
    prove_resolution,
)


class TestConstructiveResolution(unittest.TestCase):
    """Test suite for constructive resolution theorem proving in intuitionistic propositional logic."""

    def setUp(self) -> None:
        """Initializes atomic propositions and provers."""
        self.p = PredicateApp(pred="P", arity=0, args=())
        self.q = PredicateApp(pred="Q", arity=0, args=())
        self.r = PredicateApp(pred="R", arity=0, args=())
        self.prefixed_prover = PrefixedResolutionProver(max_multiplicity=3)
        self.translation_prover = TranslationResolutionProver(max_steps=500, timeout_sec=5.0)

    # --- PREFIXED DATA STRUCTURE TESTS ---

    def test_prefixed_literal_operations(self) -> None:
        """Tests PrefixedLiteral creation, negation, substitution, and string formatting."""
        c0 = PrefixConstant("c0")
        v1 = PrefixVariable("V1")
        lit = PrefixedLiteral(prefix=Prefix((c0, v1)), polarity=1, atom=self.p)
        self.assertEqual(lit.polarity, 1)
        self.assertEqual(lit.atom, self.p)
        self.assertEqual(lit.to_string(), "P^1:c0.V1")

        neg = lit.negate()
        self.assertEqual(neg.polarity, 0)
        self.assertEqual(neg.prefix, lit.prefix)

        c1 = PrefixConstant("c1")
        subst = PrefixSubstitution().bind(v1, (c1,))
        inst = lit.substitute(subst)
        self.assertEqual(inst.prefix.symbols, (c0, c1))
        self.assertEqual(inst.constants(), {c0, c1})
        self.assertEqual(inst.variables(), set())

    def test_prefixed_clause_operations(self) -> None:
        """Tests PrefixedClause creation, empty check, substitution, and string formatting."""
        c0 = PrefixConstant("c0")
        l1 = PrefixedLiteral(prefix=Prefix((c0,)), polarity=1, atom=self.p)
        l2 = PrefixedLiteral(prefix=Prefix((c0,)), polarity=0, atom=self.q)
        clause = PrefixedClause(frozenset([l1, l2]))

        self.assertEqual(len(clause), 2)
        self.assertFalse(clause.is_empty())
        self.assertIn("P^1:c0", clause.to_string())
        self.assertIn("Q^0:c0", clause.to_string())

        empty_c = PrefixedClause()
        self.assertEqual(len(empty_c), 0)
        self.assertTrue(empty_c.is_empty())
        self.assertEqual(empty_c.to_string(), "[]")

    def test_prefixed_resolution_and_factoring_rules(self) -> None:
        """Tests resolve_prefixed_clauses and factor_prefixed_clause inference functions."""
        c0 = PrefixConstant("c0")
        c1 = PrefixConstant("c1")
        v1 = PrefixVariable("V1")

        l1 = PrefixedLiteral(prefix=Prefix((c0, v1)), polarity=1, atom=self.p)
        l2 = PrefixedLiteral(prefix=Prefix((c0, c1)), polarity=0, atom=self.p)
        c_left = PrefixedClause(frozenset([l1]))
        c_right = PrefixedClause(frozenset([l2]))

        resolvents = resolve_prefixed_clauses(c_left, c_right)
        self.assertEqual(len(resolvents), 1)
        res_clause, res_subst, _, _ = resolvents[0]
        self.assertTrue(res_clause.is_empty())
        self.assertEqual(res_subst.get(v1), (c1,))

        # Factoring test
        l3 = PrefixedLiteral(prefix=Prefix((c0, c1)), polarity=1, atom=self.p)
        c_fact = PrefixedClause(frozenset([l1, l3]))
        factors = factor_prefixed_clause(c_fact)
        self.assertEqual(len(factors), 1)
        fact_clause, fact_subst, _, _ = factors[0]
        self.assertEqual(len(fact_clause), 1)
        self.assertEqual(fact_subst.get(v1), (c1,))

    # --- PREFIXED RESOLUTION VALIDITY TESTS ---

    def test_prefixed_identity_axiom(self) -> None:
        """Tests identity sequent P ==> P."""
        proof = self.prefixed_prover.prove(target=self.p, premises=[self.p])
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_prefixed_self_implication(self) -> None:
        """Tests self-implication P => P."""
        target = Implies(left=self.p, right=self.p)
        proof = self.prefixed_prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_prefixed_modus_ponens(self) -> None:
        """Tests Modus Ponens: P => Q, P ==> Q."""
        p_imp_q = Implies(left=self.p, right=self.q)
        proof = self.prefixed_prover.prove(target=self.q, premises=[p_imp_q, self.p])
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_prefixed_hypothetical_syllogism(self) -> None:
        """Tests hypothetical syllogism (P => Q) => ((Q => R) => (P => R))."""
        p_imp_q = Implies(left=self.p, right=self.q)
        q_imp_r = Implies(left=self.q, right=self.r)
        p_imp_r = Implies(left=self.p, right=self.r)
        target = Implies(left=p_imp_q, right=Implies(left=q_imp_r, right=p_imp_r))
        proof = self.prefixed_prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_prefixed_conjunction_and_disjunction(self) -> None:
        """Tests conjunction and disjunction introduction / elimination."""
        # P & Q => P
        target1 = Implies(left=And(left=self.p, right=self.q), right=self.p)
        proof1 = self.prefixed_prover.prove(target=target1)
        self.assertIsNotNone(proof1)
        assert proof1 is not None
        self.assertTrue(proof1.is_valid)

        # P => P | Q
        target2 = Implies(left=self.p, right=Or(left=self.p, right=self.q))
        proof2 = self.prefixed_prover.prove(target=target2)
        self.assertIsNotNone(proof2)
        assert proof2 is not None
        self.assertTrue(proof2.is_valid)

    def test_prefixed_currying(self) -> None:
        """Tests currying equivalence (P & Q => R) <=> (P => (Q => R))."""
        target = Iff(
            left=Implies(left=And(left=self.p, right=self.q), right=self.r),
            right=Implies(left=self.p, right=Implies(left=self.q, right=self.r)),
        )
        proof = self.prefixed_prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_prefixed_contraposition(self) -> None:
        """Tests constructive contraposition (P => Q) => (~Q => ~P)."""
        target = Implies(
            left=Implies(left=self.p, right=self.q),
            right=Implies(left=Not(operand=self.q), right=Not(operand=self.p)),
        )
        proof = self.prefixed_prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_prefixed_double_negation_excluded_middle(self) -> None:
        """Tests Glivenko theorem: ~~ (P | ~P) is intuitionistically valid."""
        em = Or(left=self.p, right=Not(operand=self.p))
        target = Not(operand=Not(operand=em))
        proof = self.prefixed_prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_prefixed_falsum_elimination(self) -> None:
        """Tests ex falso quodlibet _bot ==> P."""
        proof = self.prefixed_prover.prove(target=self.p, premises=[FALSUM])
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    # --- PREFIXED RESOLUTION UNPROVABLE THEOREMS (SOUNDNESS) ---

    def test_prefixed_excluded_middle_fails(self) -> None:
        """Verifies classical Excluded Middle P | ~P fails intuitionistically."""
        target = Or(left=self.p, right=Not(operand=self.p))
        proof = self.prefixed_prover.prove(target=target)
        self.assertIsNone(proof)

    def test_prefixed_double_negation_elimination_fails(self) -> None:
        """Verifies classical Double Negation Elimination ~~P => P fails in IPC."""
        target = Implies(left=Not(operand=Not(operand=self.p)), right=self.p)
        proof = self.prefixed_prover.prove(target=target)
        self.assertIsNone(proof)

    def test_prefixed_peirce_law_fails(self) -> None:
        """Verifies Peirce's Law ((P => Q) => P) => P fails in IPC."""
        target = Implies(
            left=Implies(left=Implies(left=self.p, right=self.q), right=self.p),
            right=self.p,
        )
        proof = self.prefixed_prover.prove(target=target)
        self.assertIsNone(proof)

    # --- RELATIONAL TRANSLATION RESOLUTION TESTS ---

    def test_relational_translation_ast(self) -> None:
        """Tests structure of translate_ipc_to_fol and get_frame_axioms."""
        fol_f = translate_ipc_to_fol(Implies(left=self.p, right=self.q))
        self.assertEqual(type(fol_f).__name__, "Forall")

        axioms = get_frame_axioms(["P", "Q"])
        self.assertEqual(len(axioms), 4)  # refl + trans + mono(P) + mono(Q)

    def test_translation_self_implication(self) -> None:
        """Tests proving P => P via FOL relational translation."""
        proof = self.translation_prover.prove(target=Implies(left=self.p, right=self.p))
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)
        self.assertIsNotNone(proof.proof_dag)

    def test_translation_modus_ponens(self) -> None:
        """Tests proving Modus Ponens via FOL relational translation."""
        p_imp_q = Implies(left=self.p, right=self.q)
        proof = self.translation_prover.prove(target=self.q, premises=[p_imp_q, self.p])
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_translation_excluded_middle_fails(self) -> None:
        """Verifies Excluded Middle P | ~P is not provable via translation."""
        target = Or(left=self.p, right=Not(operand=self.p))
        proof = self.translation_prover.prove(target=target)
        self.assertIsNone(proof)

    # --- UNIFIED API & SERIALIZATION TESTS ---

    def test_unified_constructive_prover_api(self) -> None:
        """Tests ConstructiveResolutionProver and convenience helper prove_resolution."""
        target = Implies(left=self.p, right=self.p)

        # Prefixed mode
        res1 = prove_resolution(target, method="prefixed")
        self.assertIsNotNone(res1)
        assert res1 is not None
        self.assertTrue(res1.is_valid)
        self.assertIn("target", res1.to_dict())
        self.assertIn("Prefixed Resolution Proof", res1.to_string())

        # Translation mode
        res2 = prove_resolution(target, method="translation")
        self.assertIsNotNone(res2)
        assert res2 is not None
        self.assertTrue(res2.is_valid)
        self.assertIn("target_ipc", res2.to_dict())
        self.assertIn("Relational Translation Resolution Proof", res2.to_string())

        # Auto mode
        prover_auto = ConstructiveResolutionProver(method="auto")
        res3 = prover_auto.prove(target)
        self.assertIsNotNone(res3)
        assert res3 is not None
        self.assertTrue(res3.is_valid)

    def test_invalid_method_raises(self) -> None:
        """Tests that an unsupported method raises ValueError."""
        prover = ConstructiveResolutionProver(method="unsupported")
        with self.assertRaises(ValueError):
            prover.prove(self.p)

    def test_contradictions_rejected(self) -> None:
        """Verifies that constructive resolution provers do not accept contradictions.

        Tests PrefixedResolutionProver, TranslationResolutionProver, and
        ConstructiveResolutionProver with P & ~P, FALSUM, and P <=> ~P.

        Args:
            None

        Returns:
            None: Asserts that all constructive resolution provers reject contradictions.

        Example:
            >>> self.test_contradictions_rejected()
        """
        contradiction = And(left=self.p, right=Not(operand=self.p))
        iff_contra = Iff(left=self.p, right=Not(operand=self.p))

        # Prefixed resolution
        self.assertIsNone(self.prefixed_prover.prove(target=contradiction))
        self.assertIsNone(self.prefixed_prover.prove(target=FALSUM))
        self.assertIsNone(self.prefixed_prover.prove(target=iff_contra))

        # Relational translation resolution
        self.assertIsNone(self.translation_prover.prove(target=contradiction))
        self.assertIsNone(self.translation_prover.prove(target=FALSUM))
        self.assertIsNone(self.translation_prover.prove(target=iff_contra))

        # Unified constructive resolution prover
        unified = ConstructiveResolutionProver()
        self.assertIsNone(unified.prove(target=contradiction))
        self.assertIsNone(unified.prove(target=FALSUM))
        self.assertIsNone(unified.prove(target=iff_contra))


if __name__ == "__main__":
    unittest.main()
