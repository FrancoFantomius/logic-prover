"""Unit and integration test suite for Python code generation from Curry-Howard proofs.

Tests runtime support primitives, AST translation, type annotation mapping, module synthesis,
and dynamic Python code execution with exec().
"""

from __future__ import annotations
import ast
import argparse
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from logic_prover.core.ast import (
    PredicateApp, Constant, Variable, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.constructive.terms import (
    ProofType, AtomType, ArrowType, ProdType, SumType, UnitType, VoidType,
    Var, Abs, App, Pair, Fst, Snd, Inl, Inr, Case,
    Unit, Abort, Refl, Subst, ExistsIntro, ExistsElim, NatRec,
    formula_to_type
)
from logic_prover.constructive.ljt import prove_ljt, extract_ljt_term
from logic_prover.exporters.python_runtime import (
    Left, Right, nat_rec, _abort, type_to_python_annotation
)
from logic_prover.exporters.python_exporter import (
    PythonExporter, export_function, export_module
)
from logic_prover.__main__ import cmd_prove_intuitionistic
from logic_prover.config import SolverConfig


class TestPythonRuntime(unittest.TestCase):
    """Tests for Python runtime support primitives and type translation."""

    def test_left_and_right_tagged_unions(self) -> None:
        """Tests Left and Right container properties, equality, and repr."""
        l = Left(42)
        r = Right("abc")
        self.assertEqual(l.value, 42)
        self.assertEqual(r.value, "abc")
        self.assertEqual(repr(l), "Left(42)")
        self.assertEqual(repr(r), "Right('abc')")
        self.assertNotEqual(l, r)
        self.assertEqual(Left(42), Left(42))

    def test_nat_rec_primitive_recursion(self) -> None:
        """Tests nat_rec iteration for base case and recursive step."""
        # 0 iterations -> base case
        self.assertEqual(nat_rec("base", lambda k, acc: f"{acc}_{k}", 0), "base")

        # Sum 0 + 1 + ... + n: f(0)=0; f(k+1) = acc + (k+1)
        sum_10 = nat_rec(0, lambda k, acc: acc + (k + 1), 10)
        self.assertEqual(sum_10, 55)

        # Factorial 5! = 120
        fact_5 = nat_rec(1, lambda k, acc: (k + 1) * acc, 5)
        self.assertEqual(fact_5, 120)

        # Negative n raises ValueError
        with self.assertRaises(ValueError):
            nat_rec(0, lambda k, acc: acc, -1)

    def test_abort_raises_runtime_error(self) -> None:
        """Tests that _abort raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            _abort()

    def test_type_to_python_annotation(self) -> None:
        """Tests mapping of ProofType to Python typing annotation strings."""
        p = AtomType("P")
        nat_type = AtomType("Nat")
        arrow = ArrowType(nat_type, nat_type)
        prod = ProdType(p, nat_type)
        sm = SumType(p, nat_type)
        u = UnitType()
        v = VoidType()

        self.assertEqual(type_to_python_annotation(nat_type), "int")
        self.assertEqual(type_to_python_annotation(arrow), "Callable[[int], int]")
        self.assertEqual(type_to_python_annotation(prod), "Tuple[Any, int]")
        self.assertEqual(type_to_python_annotation(sm), "Union[Left[Any], Right[int]]")
        self.assertEqual(type_to_python_annotation(u), "None")
        self.assertEqual(type_to_python_annotation(v), "NoReturn")


class TestPythonExporterAST(unittest.TestCase):
    """Tests AST synthesis for all ProofTerm variants."""

    def setUp(self) -> None:
        self.exporter = PythonExporter()
        self.p_type = AtomType("int")

    def test_term_to_ast_basic(self) -> None:
        """Tests AST generation for variables, abstractions, applications, pairs, and projections."""
        v = Var("x")
        ast_v = self.exporter.term_to_ast(v)
        self.assertIsInstance(ast_v, ast.Name)
        self.assertEqual(ast.unparse(ast_v), "x")

        # Lambda: \x. x
        lam = Abs("x", self.p_type, v)
        ast_lam = self.exporter.term_to_ast(lam)
        self.assertIsInstance(ast_lam, ast.Lambda)
        self.assertEqual(ast.unparse(ast_lam), "lambda x: x")

        # Call: (\x. x) y
        app = App(lam, Var("y"))
        ast_app = self.exporter.term_to_ast(app)
        self.assertIsInstance(ast_app, ast.Call)
        self.assertEqual(ast.unparse(ast_app), "(lambda x: x)(y)")

        # Pair & Projections
        pair = Pair(Var("a"), Var("b"))
        self.assertEqual(ast.unparse(self.exporter.term_to_ast(pair)), "(a, b)")
        self.assertEqual(ast.unparse(self.exporter.term_to_ast(Fst(pair))), "(a, b)[0]")
        self.assertEqual(ast.unparse(self.exporter.term_to_ast(Snd(pair))), "(a, b)[1]")

    def test_term_to_ast_sums_and_case(self) -> None:
        """Tests AST generation for Left, Right, and Case expressions."""
        inl = Inl(Var("a"))
        inr = Inr(Var("b"))
        self.assertEqual(ast.unparse(self.exporter.term_to_ast(inl)), "Left(a)")
        self.assertEqual(ast.unparse(self.exporter.term_to_ast(inr)), "Right(b)")

        cs = Case(Var("s"), "x", Var("x"), "y", Var("y"))
        cs_ast = self.exporter.term_to_ast(cs)
        code = ast.unparse(cs_ast)
        self.assertIn("isinstance(_s, Left)", code)
        self.assertIn("_s.value", code)

    def test_term_to_ast_nat_rec(self) -> None:
        """Tests AST generation for nat_rec recursion."""
        rec = NatRec(Var("z"), "k", "ih", Var("ih"), Var("n"))
        rec_ast = self.exporter.term_to_ast(rec)
        code = ast.unparse(rec_ast)
        self.assertIn("nat_rec(z, lambda k, ih: ih, n)", code)

    def test_export_function_uncurrying(self) -> None:
        """Tests uncurrying of nested lambda abstractions into multi-argument function definitions."""
        # \x. \y. x
        term = Abs("x", AtomType("int"), Abs("y", AtomType("str"), Var("x")))
        code = self.exporter.export_function(term, name="const_k", formula_type=ArrowType(AtomType("int"), ArrowType(AtomType("str"), AtomType("int"))))
        self.assertIn("def const_k(x: int, y: str) -> int:", code)
        self.assertIn("return x", code)


class TestPythonExecution(unittest.TestCase):
    """Executes generated Python functions using exec() and verifies computational behavior."""

    def setUp(self) -> None:
        self.exporter = PythonExporter()
        self.p = PredicateApp("P", 0, ())
        self.q = PredicateApp("Q", 0, ())
        self.r = PredicateApp("R", 0, ())

    def _exec_function(self, code: str, fn_name: str) -> Any:
        """Helper executing function code in a sandbox namespace with runtime prelude."""
        ns = {
            "Left": Left,
            "Right": Right,
            "nat_rec": nat_rec,
            "_abort": _abort,
        }
        exec(code, ns)
        return ns[fn_name]

    def test_exec_identity_proof(self) -> None:
        """Proves P => P, synthesizes Python function, and executes it."""
        goal = Implies(self.p, self.p)
        proof = prove_ljt(goal)
        assert proof is not None
        term = extract_ljt_term(proof)

        code = self.exporter.export_function(term, name="identity", formula_type=formula_to_type(goal))
        fn = self._exec_function(code, "identity")

        self.assertEqual(fn(123), 123)
        self.assertEqual(fn("hello"), "hello")
        self.assertEqual(fn([1, 2]), [1, 2])

    def test_exec_conjunction_swap(self) -> None:
        """Proves (P & Q) => (Q & P), synthesizes function, and verifies pair swap execution."""
        goal = Implies(And(self.p, self.q), And(self.q, self.p))
        proof = prove_ljt(goal)
        assert proof is not None
        term = extract_ljt_term(proof)

        code = self.exporter.export_function(term, name="swap_pair", formula_type=formula_to_type(goal))
        fn = self._exec_function(code, "swap_pair")

        res = fn((1, "two"))
        self.assertEqual(res, ("two", 1))

    def test_exec_disjunction_swap(self) -> None:
        """Proves (P | Q) => (Q | P), synthesizes function, and verifies tagged union swap."""
        goal = Implies(Or(self.p, self.q), Or(self.q, self.p))
        proof = prove_ljt(goal)
        assert proof is not None
        term = extract_ljt_term(proof)

        code = self.exporter.export_function(term, name="swap_coprod", formula_type=formula_to_type(goal))
        fn = self._exec_function(code, "swap_coprod")

        self.assertEqual(fn(Left("a")), Right("a"))
        self.assertEqual(fn(Right(99)), Left(99))

    def test_exec_s_combinator(self) -> None:
        """Proves S combinator: (P => (Q => R)) => ((P => Q) => (P => R)) and executes it."""
        goal = Implies(
            Implies(self.p, Implies(self.q, self.r)),
            Implies(Implies(self.p, self.q), Implies(self.p, self.r))
        )
        proof = prove_ljt(goal)
        assert proof is not None
        term = extract_ljt_term(proof)

        code = self.exporter.export_function(term, name="s_comb", formula_type=formula_to_type(goal))
        s_fn = self._exec_function(code, "s_comb")

        # Test: f = (x -> y -> x + y), g = (x -> x * 2), x = 10
        # s_comb(f, g, 10) = f(10, g(10)) = 10 + 20 = 30
        res = s_fn(lambda x: lambda y: x + y, lambda x: x * 2, 10)
        self.assertEqual(res, 30)

    def test_exec_first_order_quantifiers(self) -> None:
        """Proves forall x. P(x) => exists x. P(x) and verifies execution."""
        x = Variable(1, sort=Ind)
        px = PredicateApp("P", 1, (x,))
        goal = Implies(Forall(x, px), Exists(x, px))
        proof = prove_ljt(goal)
        assert proof is not None
        term = extract_ljt_term(proof)

        code = self.exporter.export_function(term, name="forall_to_exists", formula_type=formula_to_type(goal))
        fn = self._exec_function(code, "forall_to_exists")

        # Pass a predicate function
        res = fn(lambda arg: f"proven_{arg}")
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 2)

    def test_export_module_complete(self) -> None:
        """Tests that export_module synthesizes a valid, standalone Python file that compiles."""
        goal1 = Implies(self.p, self.p)
        proof1 = prove_ljt(goal1)
        assert proof1 is not None
        term1 = extract_ljt_term(proof1)

        goal2 = Implies(And(self.p, self.q), And(self.q, self.p))
        proof2 = prove_ljt(goal2)
        assert proof2 is not None
        term2 = extract_ljt_term(proof2)

        theorems = [
            ("id_func", term1, formula_to_type(goal1)),
            ("swap_func", term2, formula_to_type(goal2)),
        ]
        module_text = export_module(theorems, module_docstring="Generated logic module.")

        # Ensure valid Python syntax
        compiled = compile(module_text, "<string>", "exec")
        self.assertIsNotNone(compiled)

        # Execute module namespace
        ns: dict[str, Any] = {}
        exec(compiled, ns)
        self.assertEqual(ns["id_func"](42), 42)
        self.assertEqual(ns["swap_func"]((1, 2)), (2, 1))


class TestCLIWithPythonFormat(unittest.TestCase):
    """Tests CLI command prove-intuitionistic with --term-format python."""

    def test_cli_export_python_output_file(self) -> None:
        """Verifies CLI synthesizes Python code and writes it to disk when --output is provided."""
        with TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "output_program.py"
            config = SolverConfig()
            args = argparse.Namespace(
                command="prove-intuitionistic",
                target="P => P",
                target_pos=None,
                premises=[],
                method="ljt",
                max_term_depth=2,
                max_ind_depth=3,
                timeout=10.0,
                max_steps=1000,
                theory=None,
                extract_term=True,
                term_format="python",
                output=str(out_file),
            )
            ret = cmd_prove_intuitionistic(args, config)
            self.assertEqual(ret, 0)
            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("def synthesized_program(x", content)


if __name__ == "__main__":
    unittest.main()
