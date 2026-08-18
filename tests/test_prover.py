import unittest
import time
from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.core.signature import Signature
from logic_prover.core.exceptions import ProofTimeoutError, ProofSearchExhaustedError
from logic_prover.prover.engine import TheoremProver
from logic_prover.axioms.peano import get_peano_signature, get_peano_axioms
from logic_prover.constructive.common import FALSUM
from logic_prover.constructive.tableau import TableauProver
from logic_prover.constructive.ljt import LJTProver
from logic_prover.constructive.wallen import WallenProver
from logic_prover.constructive.resolution import (
    PrefixedResolutionProver,
    TranslationResolutionProver,
    ConstructiveResolutionProver,
)

class TestProver(unittest.TestCase):

    def setUp(self):
        self.sig = Signature()
        self.sig.register_predicate("P", 1, (Ind,))
        self.sig.register_predicate("Q", 1, (Ind,))
        self.sig.register_predicate("R", 2, (Ind, Ind))
        self.sig.register_predicate("PropP", 0, ())
        self.sig.register_predicate("PropQ", 0, ())
        self.sig.register_constant("a", Ind)
        self.sig.register_constant("b", Ind)
        self.sig.register_function("f", 1, (Ind,), Ind)
        self.prover = TheoremProver(signature=self.sig)

    def test_propositional_tautology_p_or_not_p(self):
        p = PredicateApp(pred="PropP", arity=0, args=())
        target = Or(left=p, right=Not(operand=p))
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_propositional_modus_ponens(self):
        p = PredicateApp(pred="PropP", arity=0, args=())
        q = PredicateApp(pred="PropQ", arity=0, args=())
        premise = And(left=Implies(left=p, right=q), right=p)
        target = q
        proof = self.prover.prove(target=target, premises=[premise])
        self.assertTrue(proof.is_valid())

    def test_peirces_law(self):
        p = PredicateApp(pred="PropP", arity=0, args=())
        q = PredicateApp(pred="PropQ", arity=0, args=())
        # ((P => Q) => P) => P
        target = Implies(
            left=Implies(left=Implies(left=p, right=q), right=p),
            right=p
        )
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_fol_forall_implies_exists(self):
        x = Variable(id=0, sort=Ind)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        # (forall x, P(x)) => (exists x, P(x))
        target = Implies(
            left=Forall(variable=x, body=p_x),
            right=Exists(variable=x, body=p_x)
        )
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_fol_forall_and_distributivity(self):
        x = Variable(id=0, sort=Ind)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        q_x = PredicateApp(pred="Q", arity=1, args=(x,))
        # forall x (P(x) & Q(x)) => (forall x P(x) & forall x Q(x))
        target = Implies(
            left=Forall(variable=x, body=And(left=p_x, right=q_x)),
            right=And(
                left=Forall(variable=x, body=p_x),
                right=Forall(variable=x, body=q_x)
            )
        )
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_fol_exists_forall_implies_forall_exists(self):
        x = Variable(id=0, sort=Ind)
        y = Variable(id=1, sort=Ind)
        r_xy = PredicateApp(pred="R", arity=2, args=(x, y))
        # (exists x forall y R(x, y)) => (forall y exists x R(x, y))
        target = Implies(
            left=Exists(variable=x, body=Forall(variable=y, body=r_xy)),
            right=Forall(variable=y, body=Exists(variable=x, body=r_xy))
        )
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_peano_theorem_add_zero(self):
        peano_sig = get_peano_signature()
        peano_axioms = [formula for _, formula in get_peano_axioms()]
        prover = TheoremProver(signature=peano_sig)

        zero = Constant("zero", sort=Nat)
        add_0_0 = FunctionApp("add", 2, (zero, zero), return_sort=Nat)
        target = Equality(left=add_0_0, right=zero)

        proof = prover.prove(target=target, premises=peano_axioms)
        self.assertTrue(proof.is_valid())

    def test_proof_timeout_exception(self):
        x = Variable(id=0, sort=Ind)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        p_fx = PredicateApp(pred="P", arity=1, args=(FunctionApp("f", 1, (x,), return_sort=Ind),))
        premise1 = Forall(variable=x, body=Implies(left=p_x, right=p_fx))
        premise2 = PredicateApp(pred="P", arity=1, args=(Constant("a", sort=Ind),))
        target = PredicateApp(pred="Q", arity=1, args=(Constant("a", sort=Ind),))

        with self.assertRaises(ProofTimeoutError):
            self.prover.prove(target=target, premises=[premise1, premise2], timeout_sec=0.01, max_steps=1000000)

    def test_proof_search_exhausted_exception(self):
        p = PredicateApp(pred="P", arity=1, args=(Constant("a", sort=Ind),))
        with self.assertRaises(ProofSearchExhaustedError):
            self.prover.prove(target=p, premises=[], max_steps=5, timeout_sec=5.0)

    def test_contradiction_rejected(self) -> None:
        """Verifies that TheoremProver does not accept contradictions.

        Tests propositional contradictions (P & ~P, P <=> ~P) and first-order
        contradictions (forall x P(x) & exists x ~P(x)) to ensure that
        ProofSearchExhaustedError is raised when proof search fails.

        Args:
            None

        Returns:
            None: Asserts that attempting to prove contradictions fails.

        Example:
            >>> self.test_contradiction_rejected()
        """
        p = PredicateApp(pred="PropP", arity=0, args=())
        contradiction_prop = And(left=p, right=Not(operand=p))
        with self.assertRaises(ProofSearchExhaustedError):
            self.prover.prove(target=contradiction_prop)

        contradiction_iff = Iff(left=p, right=Not(operand=p))
        with self.assertRaises(ProofSearchExhaustedError):
            self.prover.prove(target=contradiction_iff)

        x = Variable(id=0, sort=Ind)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        not_p_x = Not(operand=p_x)
        fol_contradiction = And(
            left=Forall(variable=x, body=p_x),
            right=Exists(variable=x, body=not_p_x)
        )
        with self.assertRaises(ProofSearchExhaustedError):
            self.prover.prove(target=fol_contradiction)

    def test_all_provers_reject_contradictions(self) -> None:
        """Verifies that all provers across the library do not accept contradictions.

        Checks TheoremProver, TableauProver, LJTProver, WallenProver,
        PrefixedResolutionProver, TranslationResolutionProver, and
        ConstructiveResolutionProver with contradictory propositional formulas.

        Args:
            None

        Returns:
            None: Asserts that every prover rejects contradiction targets.

        Example:
            >>> self.test_all_provers_reject_contradictions()
        """
        p = PredicateApp(pred="PropP", arity=0, args=())
        contradiction = And(left=p, right=Not(operand=p))
        iff_contradiction = Iff(left=p, right=Not(operand=p))

        # 1. Classical First-Order Resolution Prover
        with self.assertRaises(ProofSearchExhaustedError):
            self.prover.prove(target=contradiction)
        with self.assertRaises(ProofSearchExhaustedError):
            self.prover.prove(target=iff_contradiction)

        # 2. Intuitionistic Semantic Tableau Prover
        tableau_prover = TableauProver()
        res_tab1 = tableau_prover.prove(target=contradiction)
        self.assertFalse(res_tab1.is_valid)
        res_tab2 = tableau_prover.prove(target=FALSUM)
        self.assertFalse(res_tab2.is_valid)
        res_tab3 = tableau_prover.prove(target=iff_contradiction)
        self.assertFalse(res_tab3.is_valid)

        # 3. Intuitionistic Sequent Calculus (LJT) Prover
        ljt_prover = LJTProver()
        self.assertIsNone(ljt_prover.prove(target=contradiction))
        self.assertFalse(ljt_prover.is_provable(target=contradiction))
        self.assertIsNone(ljt_prover.prove(target=FALSUM))
        self.assertFalse(ljt_prover.is_provable(target=FALSUM))
        self.assertIsNone(ljt_prover.prove(target=iff_contradiction))
        self.assertFalse(ljt_prover.is_provable(target=iff_contradiction))

        # 4. Intuitionistic Wallen Matrix Prover
        wallen_prover = WallenProver()
        self.assertIsNone(wallen_prover.prove(target=contradiction))
        self.assertIsNone(wallen_prover.prove(target=FALSUM))
        self.assertIsNone(wallen_prover.prove(target=iff_contradiction))

        # 5. Prefixed Resolution Prover
        prefixed_prover = PrefixedResolutionProver()
        self.assertIsNone(prefixed_prover.prove(target=contradiction))
        self.assertIsNone(prefixed_prover.prove(target=FALSUM))
        self.assertIsNone(prefixed_prover.prove(target=iff_contradiction))

        # 6. Translation Resolution Prover
        translation_prover = TranslationResolutionProver()
        self.assertIsNone(translation_prover.prove(target=contradiction))
        self.assertIsNone(translation_prover.prove(target=FALSUM))
        self.assertIsNone(translation_prover.prove(target=iff_contradiction))

        # 7. Unified Constructive Resolution Prover
        constructive_prover = ConstructiveResolutionProver()
        self.assertIsNone(constructive_prover.prove(target=contradiction))
        self.assertIsNone(constructive_prover.prove(target=FALSUM))
        self.assertIsNone(constructive_prover.prove(target=iff_contradiction))


if __name__ == "__main__":
    unittest.main()
