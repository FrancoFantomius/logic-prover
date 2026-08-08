import unittest
from logic.core.ast import PredicateApp, Not
from logic.prover.clausifier import Clause, Literal
from logic.prover.engine import ResolutionStep
from logic.prover.proof import ProofStep, ProofDAG
from logic.prover.reconstruction import reconstruct_proof, simplify_proof

class TestReconstruction(unittest.TestCase):

    def test_proof_dag_serialization_and_validity(self):
        p = PredicateApp(pred="P", arity=0, args=())

        step1 = ProofStep(id="s1", rule="Axiom", premise_ids=[], conclusion=p)
        step2 = ProofStep(id="s2", rule="NegatedGoal", premise_ids=[], conclusion=Not(p))
        step3 = ProofStep(id="s3", rule="Contradiction", premise_ids=["s1", "s2"], conclusion=PredicateApp(pred="False", arity=0, args=()))
        step4 = ProofStep(id="s4", rule="DoubleNegationElimination", premise_ids=["s3", "s2"], conclusion=p)

        dag = ProofDAG(
            steps={"s1": step1, "s2": step2, "s3": step3, "s4": step4},
            root_id="s4",
            axiom_ids={"s1"}
        )

        self.assertTrue(dag.is_valid())

        # Roundtrip dict serialization
        serialized = dag.to_dict()
        deserialized = ProofDAG.from_dict(serialized)
        self.assertTrue(deserialized.is_valid())
        self.assertEqual(deserialized.root_id, "s4")
        self.assertEqual(len(deserialized.steps), 4)

    def test_simplify_proof(self):
        p = PredicateApp(pred="P", arity=0, args=())
        q = PredicateApp(pred="Q", arity=0, args=())

        step1 = ProofStep(id="s1", rule="Axiom", premise_ids=[], conclusion=p)
        step_dead = ProofStep(id="dead", rule="Axiom", premise_ids=[], conclusion=q)
        step2 = ProofStep(id="s2", rule="DoubleNegationElimination", premise_ids=["s1"], conclusion=p)

        dag = ProofDAG(
            steps={"s1": step1, "dead": step_dead, "s2": step2},
            root_id="s2",
            axiom_ids={"s1", "dead"}
        )

        self.assertEqual(len(dag.steps), 3)
        simplified = simplify_proof(dag)
        self.assertEqual(len(simplified.steps), 2)
        self.assertNotIn("dead", simplified.steps)

    def test_reconstruct_proof_trace(self):
        p = PredicateApp(pred="P", arity=0, args=())
        lit_p = Literal(atom=p, positive=True)
        lit_not_p = Literal(atom=p, positive=False)

        c1 = Clause(frozenset([lit_p]))
        c2 = Clause(frozenset([lit_not_p]))
        c_empty = Clause(frozenset())

        rstep1 = ResolutionStep(id="res_0", rule_name="axiom", premise_ids=[], clause=c1, original_formula=p)
        rstep2 = ResolutionStep(id="res_1", rule_name="negated_goal", premise_ids=[], clause=c2, original_formula=p)
        rstep3 = ResolutionStep(id="res_2", rule_name="resolution", premise_ids=["res_0", "res_1"], clause=c_empty)

        trace = [rstep1, rstep2, rstep3]
        dag = reconstruct_proof(trace, original_target=p, premises=[p])
        self.assertTrue(dag.is_valid())
        self.assertEqual(dag.root_id, "final_conclusion")


if __name__ == "__main__":
    unittest.main()
