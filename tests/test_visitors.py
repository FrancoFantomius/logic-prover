import unittest
from typing import Dict

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.core.visitors import (
    ASTVisitor, ASTTransformer, DepthVisitor, SizeVisitor,
    FreeVariableCollector, SubstitutionTransformer, ExportVisitor
)


class CountingVisitor(ASTVisitor[int]):
    """Test visitor that counts occurrences of each AST node type."""

    def __init__(self) -> None:
        self.counts: Dict[str, int] = {
            "Variable": 0, "Constant": 0, "FunctionApp": 0, "PredicateApp": 0,
            "Equality": 0, "Not": 0, "And": 0, "Or": 0, "Implies": 0, "Iff": 0,
            "Forall": 0, "Exists": 0
        }

    def visit_variable(self, node: Variable) -> int:
        self.counts["Variable"] += 1
        return 1

    def visit_constant(self, node: Constant) -> int:
        self.counts["Constant"] += 1
        return 1

    def visit_function_app(self, node: FunctionApp) -> int:
        self.counts["FunctionApp"] += 1
        return 1 + sum(self.visit(arg) for arg in node.args)

    def visit_predicate_app(self, node: PredicateApp) -> int:
        self.counts["PredicateApp"] += 1
        return 1 + sum(self.visit(arg) for arg in node.args)

    def visit_equality(self, node: Equality) -> int:
        self.counts["Equality"] += 1
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_not(self, node: Not) -> int:
        self.counts["Not"] += 1
        return 1 + self.visit(node.operand)

    def visit_and(self, node: And) -> int:
        self.counts["And"] += 1
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_or(self, node: Or) -> int:
        self.counts["Or"] += 1
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_implies(self, node: Implies) -> int:
        self.counts["Implies"] += 1
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_iff(self, node: Iff) -> int:
        self.counts["Iff"] += 1
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_forall(self, node: Forall) -> int:
        self.counts["Forall"] += 1
        return 1 + self.visit(node.variable) + self.visit(node.body)

    def visit_exists(self, node: Exists) -> int:
        self.counts["Exists"] += 1
        return 1 + self.visit(node.variable) + self.visit(node.body)


class TestVisitors(unittest.TestCase):

    def test_visitor_dispatching_all_12_node_types(self) -> None:
        v0 = Variable(id=0, sort=Ind)
        v1 = Variable(id=1, sort=Ind)
        c = Constant(name="c", sort=Ind)
        f_app = FunctionApp(func="f", arity=1, args=(v0,), return_sort=Ind)
        pred_app = PredicateApp(pred="P", arity=1, args=(f_app,))
        eq = Equality(left=v0, right=c)
        not_node = Not(operand=eq)
        and_node = And(left=pred_app, right=not_node)
        or_node = Or(left=and_node, right=pred_app)
        implies_node = Implies(left=or_node, right=and_node)
        iff_node = Iff(left=implies_node, right=or_node)
        forall_node = Forall(variable=v0, body=iff_node)
        exists_node = Exists(variable=v1, body=forall_node)

        visitor = CountingVisitor()
        visitor.visit(exists_node)

        self.assertEqual(visitor.counts["Exists"], 1)
        self.assertEqual(visitor.counts["Forall"], 1)
        self.assertEqual(visitor.counts["Iff"], 1)
        self.assertEqual(visitor.counts["Implies"], 1)
        self.assertEqual(visitor.counts["Or"], 2)
        self.assertEqual(visitor.counts["And"], 3)
        self.assertEqual(visitor.counts["Not"], 3)
        self.assertEqual(visitor.counts["Equality"], 3)
        self.assertEqual(visitor.counts["PredicateApp"], 5)
        self.assertEqual(visitor.counts["FunctionApp"], 5)
        self.assertEqual(visitor.counts["Constant"], 3)
        self.assertGreater(visitor.counts["Variable"], 0)

    def test_depth_and_size_visitors(self) -> None:
        v0 = Variable(id=0, sort=Ind)
        v1 = Variable(id=1, sort=Ind)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        q_v1 = PredicateApp(pred="Q", arity=1, args=(v1,))
        formula = And(left=p_v0, right=q_v1)

        self.assertEqual(DepthVisitor().visit(v0), 1)
        self.assertEqual(DepthVisitor().visit(formula), 3)
        # Size of P(v0) & Q(v1): And (1) + P(v0) (2: P, v0) + Q(v1) (2: Q, v1) = 5
        self.assertEqual(SizeVisitor().visit(formula), 5)

    def test_free_variable_collector(self) -> None:
        v0 = Variable(id=0, sort=Ind)
        v1 = Variable(id=1, sort=Ind)
        eq = Equality(left=v0, right=v1)
        self.assertEqual(FreeVariableCollector().visit(eq), {v0, v1})

        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        q_v1 = PredicateApp(pred="Q", arity=1, args=(v1,))
        and_node = And(left=p_v0, right=q_v1)
        forall_node = Forall(variable=v0, body=and_node)
        self.assertEqual(FreeVariableCollector().visit(forall_node), {v1})

    def test_substitution_transformer_and_capture_avoidance(self) -> None:
        v0 = Variable(id=0, sort=Ind)
        v1 = Variable(id=1, sort=Ind)
        v2 = Variable(id=2, sort=Ind)
        f_v1 = FunctionApp(func="f", arity=1, args=(v1,), return_sort=Ind)
        p_v0_v1 = PredicateApp(pred="P", arity=2, args=(v0, v1))

        # forall v1: Ind, P(v0, v1)
        formula = Forall(variable=v1, body=p_v0_v1)

        # Substitute v0 -> f(v1)
        transformer = SubstitutionTransformer({v0: f_v1})
        result = transformer.visit(formula)

        self.assertIsInstance(result, Forall)
        assert isinstance(result, Forall)
        # bound variable v1 should be renamed to fresh var v2 to avoid capturing free v1 in f(v1)
        self.assertNotEqual(result.variable, v1)
        self.assertEqual(result.variable, v2)
        expected_body = PredicateApp(pred="P", arity=2, args=(f_v1, v2))
        self.assertEqual(result.body, expected_body)

    def test_export_visitor_notations(self) -> None:
        v0 = Variable(id=0, sort=Ind)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        q_v0 = PredicateApp(pred="Q", arity=1, args=(v0,))
        implies_node = Implies(left=p_v0, right=q_v0)
        forall_node = Forall(variable=v0, body=implies_node)

        # Infix
        infix_str = ExportVisitor("infix").visit(forall_node)
        self.assertEqual(infix_str, "forall v0 : Ind, (P(v0) => Q(v0))")

        # Prefix
        prefix_str = ExportVisitor("prefix").visit(forall_node)
        self.assertEqual(prefix_str, "(forall (v0 : Ind) (=> (P v0) (Q v0)))")

        # LaTeX
        latex_str = ExportVisitor("latex").visit(forall_node)
        self.assertEqual(latex_str, "\\forall v_{0} : Ind, (P(v_{0}) \\implies Q(v_{0}))")


if __name__ == "__main__":
    unittest.main()
