"""Unit and integration test suite for Curry-Howard Proof-Term Extraction and BHK witness extraction.

Tests typed lambda term construction, bidirectional type inference, beta-normalization,
LJT extraction, multi-prover extraction dispatcher, and BHK witness extraction.
"""

from __future__ import annotations
import unittest
import argparse

from logic_prover.core.ast import (
    PredicateApp, Constant, Variable, Not, And, Or, Implies, Iff, Forall, Exists, Equality
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.constructive.common import FALSUM, VERUM
from logic_prover.constructive.terms import (
    ProofType, AtomType, ArrowType, ProdType, SumType, UnitType, VoidType,
    ForallType, ExistsType, EqType, formula_to_type,
    ProofTerm, Var, Abs, App, Pair, Fst, Snd, Inl, Inr, Case,
    Unit, Abort, Refl, Subst, ExistsIntro, ExistsElim, NatRec,
    free_vars, substitute_term, infer_type, beta_normalize,
    term_to_string, type_to_string, term_to_latex, type_to_latex,
    term_to_lean, type_to_lean, Witness, extract_witness, extract_program, extract_term
)
from logic_prover.constructive.ljt import LJTProver, prove_ljt, extract_ljt_term, prove_ljt_checked
from logic_prover.constructive.tableau import TableauProver
from logic_prover.constructive.wallen import WallenProver
from logic_prover.exporters.lean_exporter import LeanExporter
from logic_prover.__main__ import cmd_prove_intuitionistic
from logic_prover.config import SolverConfig


class TestCurryHowardASTAndTypes(unittest.TestCase):
    """Tests for lambda calculus term AST nodes, ProofType representations, and printers."""

    def setUp(self) -> None:
        self.p = AtomType("P")
        self.q = AtomType("Q")

    def test_type_string_and_printers(self) -> None:
        """Tests string, LaTeX, and Lean 4 pretty printers for types."""
        arrow = ArrowType(self.p, self.q)
        prod = ProdType(self.p, self.q)
        sm = SumType(self.p, self.q)
        u = UnitType()
        v = VoidType()
        fa = ForallType("x", self.p)
        ex = ExistsType("x", self.p)
        eq = EqType("a", "b")

        self.assertEqual(type_to_string(arrow), "(P -> Q)")
        self.assertEqual(type_to_string(prod), "(P * Q)")
        self.assertEqual(type_to_string(sm), "(P + Q)")
        self.assertEqual(type_to_string(u), "Unit")
        self.assertEqual(type_to_string(v), "Void")
        self.assertIn("forall x", type_to_string(fa))
        self.assertIn("exists x", type_to_string(ex))
        self.assertEqual(type_to_string(eq), "(a = b)")

        self.assertIn("\\to", type_to_latex(arrow))
        self.assertIn("\\times", type_to_latex(prod))
        self.assertIn("\\oplus", type_to_latex(sm))
        self.assertEqual(type_to_latex(u), "\\top")
        self.assertEqual(type_to_latex(v), "\\bot")

        self.assertIn("→", type_to_lean(arrow))
        self.assertIn("×", type_to_lean(prod))
        self.assertIn("⊕", type_to_lean(sm))

    def test_term_string_and_printers(self) -> None:
        """Tests term printers for lambda calculus nodes."""
        x = Var("x")
        lam = Abs("x", self.p, x)
        app = App(lam, Var("y"))
        pair = Pair(Var("a"), Var("b"))
        fst = Fst(pair)
        snd = Snd(pair)
        inl = Inl(Var("a"))
        inr = Inr(Var("b"))
        cs = Case(inl, "u", Var("u"), "v", Var("v"))
        abort = Abort(self.p, Var("f"))
        refl = Refl("c")
        subst = Subst(Var("eq"), Var("t"))
        ex_in = ExistsIntro("c", Var("p"))
        ex_el = ExistsElim(ex_in, "w", "pr", Var("pr"))

        self.assertIn("lambda x", term_to_string(lam))
        self.assertIn("fst", term_to_string(fst))
        self.assertIn("snd", term_to_string(snd))
        self.assertIn("inl", term_to_string(inl))
        self.assertIn("inr", term_to_string(inr))
        self.assertIn("case", term_to_string(cs))
        self.assertIn("abort", term_to_string(abort))
        self.assertIn("refl", term_to_string(refl))
        self.assertIn("subst", term_to_string(subst))
        self.assertIn("unpack", term_to_string(ex_el))

        # Lean 4 printer
        self.assertIn("fun (x : P) =>", term_to_lean(lam))
        self.assertIn(".1", term_to_lean(fst))
        self.assertIn(".2", term_to_lean(snd))
        self.assertIn("Sum.inl", term_to_lean(inl))
        self.assertIn("Sum.inr", term_to_lean(inr))
        self.assertIn("match", term_to_lean(cs))
        self.assertIn("rfl", term_to_lean(refl))

    def test_formula_to_type(self) -> None:
        """Tests translation of logic Formula AST nodes into ProofTypes."""
        p = PredicateApp("P", 0, ())
        q = PredicateApp("Q", 0, ())
        x = Variable(1, sort=Ind)
        px = PredicateApp("P", 1, (x,))

        self.assertIsInstance(formula_to_type(VERUM), UnitType)
        self.assertIsInstance(formula_to_type(FALSUM), VoidType)
        self.assertIsInstance(formula_to_type(And(p, q)), ProdType)
        self.assertIsInstance(formula_to_type(Or(p, q)), SumType)
        self.assertIsInstance(formula_to_type(Implies(p, q)), ArrowType)
        self.assertIsInstance(formula_to_type(Not(p)), ArrowType)
        self.assertIsInstance(formula_to_type(Iff(p, q)), ProdType)
        self.assertIsInstance(formula_to_type(Forall(x, px)), ForallType)
        self.assertIsInstance(formula_to_type(Exists(x, px)), ExistsType)


class TestTypeCheckerAndNormalizer(unittest.TestCase):
    """Tests for bidirectional type inference and beta-normalization."""

    def setUp(self) -> None:
        self.p = AtomType("P")
        self.q = AtomType("Q")
        self.r = AtomType("R")

    def test_infer_type_basic(self) -> None:
        """Tests type inference for fundamental combinators."""
        # Identity: \x:P. x  =>  P -> P
        id_term = Abs("x", self.p, Var("x"))
        self.assertEqual(infer_type(id_term), ArrowType(self.p, self.p))

        # Application: (\x:P. x) y  with y:P  =>  P
        app_term = App(id_term, Var("y", self.p))
        self.assertEqual(infer_type(app_term, {"y": self.p}), self.p)

        # Pair: <x, y>  =>  P * Q
        pair_term = Pair(Var("x", self.p), Var("y", self.q))
        self.assertEqual(infer_type(pair_term, {"x": self.p, "y": self.q}), ProdType(self.p, self.q))

        # Fst and Snd
        self.assertEqual(infer_type(Fst(pair_term), {"x": self.p, "y": self.q}), self.p)
        self.assertEqual(infer_type(Snd(pair_term), {"x": self.p, "y": self.q}), self.q)

    def test_infer_type_sums_and_case(self) -> None:
        """Tests type inference for sum injections and case analysis."""
        sum_pq = SumType(self.p, self.q)
        inl_term = Inl(Var("x", self.p), sum_type=sum_pq)
        inr_term = Inr(Var("y", self.q), sum_type=sum_pq)
        self.assertEqual(infer_type(inl_term, {"x": self.p}), sum_pq)
        self.assertEqual(infer_type(inr_term, {"y": self.q}), sum_pq)

        # Case swap: case s of inl(x) => inr(x) | inr(y) => inl(y)
        sum_qp = SumType(self.q, self.p)
        swap_case = Case(
            Var("s"),
            "x", Inr(Var("x"), sum_type=sum_qp),
            "y", Inl(Var("y"), sum_type=sum_qp),
        )
        self.assertEqual(infer_type(swap_case, {"s": sum_pq}), sum_qp)

    def test_infer_type_errors(self) -> None:
        """Tests that ill-typed terms raise TypeError."""
        # Unbound variable
        with self.assertRaises(TypeError):
            infer_type(Var("unbound"))

        # Non-function application
        with self.assertRaises(TypeError):
            infer_type(App(Var("x", self.p), Var("y", self.p)), {"x": self.p, "y": self.p})

        # Argument type mismatch
        id_p = Abs("x", self.p, Var("x"))
        with self.assertRaises(TypeError):
            infer_type(App(id_p, Var("y", self.q)), {"y": self.q})

        # Case branch type mismatch
        bad_case = Case(
            Var("s"),
            "x", Var("x"),  # type P
            "y", Var("y"),  # type Q
        )
        with self.assertRaises(TypeError):
            infer_type(bad_case, {"s": SumType(self.p, self.q)})

    def test_beta_normalize_reductions(self) -> None:
        """Tests capture-avoiding beta reductions."""
        # (λx. x) y -> y
        id_fn = Abs("x", self.p, Var("x"))
        self.assertEqual(beta_normalize(App(id_fn, Var("y"))), Var("y"))

        # fst ⟨a, b⟩ -> a
        pair = Pair(Var("a"), Var("b"))
        self.assertEqual(beta_normalize(Fst(pair)), Var("a"))
        self.assertEqual(beta_normalize(Snd(pair)), Var("b"))

        # case inl(a) of inl(x) => x | inr(y) => y  ->  a
        cs = Case(Inl(Var("a")), "x", Var("x"), "y", Var("y"))
        self.assertEqual(beta_normalize(cs), Var("a"))

        # unpack ⟨w, p⟩ as ⟨x, y⟩ in y -> p
        ex = ExistsIntro("w0", Var("proof0"))
        unpack = ExistsElim(ex, "x", "y", Var("y"))
        self.assertEqual(beta_normalize(unpack), Var("proof0"))


class TestLJTProofTermExtraction(unittest.TestCase):
    """Tests Curry-Howard proof term extraction across LJT derivations."""

    def setUp(self) -> None:
        self.p = PredicateApp("P", 0, ())
        self.q = PredicateApp("Q", 0, ())
        self.r = PredicateApp("R", 0, ())
        self.prover = LJTProver()

    def test_identity_and_k_combinator(self) -> None:
        """Tests extraction of I and K combinators."""
        # P => P
        goal_i = Implies(self.p, self.p)
        tree_i, term_i, typ_i = prove_ljt_checked(goal_i)
        self.assertIsNotNone(term_i)
        self.assertEqual(typ_i, ArrowType(AtomType("P"), AtomType("P")))

        # P => (Q => P)
        goal_k = Implies(self.p, Implies(self.q, self.p))
        tree_k, term_k, typ_k = prove_ljt_checked(goal_k)
        self.assertIsNotNone(term_k)
        expected_k_type = ArrowType(AtomType("P"), ArrowType(AtomType("Q"), AtomType("P")))
        self.assertEqual(typ_k, expected_k_type)

    def test_s_combinator(self) -> None:
        """Tests extraction of S combinator: (P => (Q => R)) => ((P => Q) => (P => R))."""
        p_q_r = Implies(self.p, Implies(self.q, self.r))
        p_q = Implies(self.p, self.q)
        p_r = Implies(self.p, self.r)
        goal_s = Implies(p_q_r, Implies(p_q, p_r))

        tree_s, term_s, typ_s = prove_ljt_checked(goal_s)
        self.assertIsNotNone(term_s)
        self.assertEqual(typ_s, formula_to_type(goal_s))

    def test_conjunction_swap(self) -> None:
        """Tests extraction for pair swap: (P & Q) => (Q & P)."""
        goal = Implies(And(self.p, self.q), And(self.q, self.p))
        tree, term, typ = prove_ljt_checked(goal)
        self.assertIsNotNone(term)
        self.assertEqual(typ, formula_to_type(goal))

    def test_disjunction_introduction_and_swap(self) -> None:
        """Tests extraction for inl/inr and case analysis: P => (P | Q) and (P | Q) => (Q | P)."""
        # P => (P | Q)
        goal_inl = Implies(self.p, Or(self.p, self.q))
        tree_inl, term_inl, typ_inl = prove_ljt_checked(goal_inl)
        self.assertIsNotNone(term_inl)
        self.assertEqual(typ_inl, formula_to_type(goal_inl))

        # (P | Q) => (Q | P)
        goal_swap = Implies(Or(self.p, self.q), Or(self.q, self.p))
        tree_swap, term_swap, typ_swap = prove_ljt_checked(goal_swap)
        self.assertIsNotNone(term_swap)
        self.assertEqual(typ_swap, formula_to_type(goal_swap))

    def test_double_negation_introduction(self) -> None:
        """Tests extraction for double negation introduction: P => ~~P."""
        goal = Implies(self.p, Not(Not(self.p)))
        tree, term, typ = prove_ljt_checked(goal)
        self.assertIsNotNone(term)
        self.assertEqual(typ, formula_to_type(goal))

    def test_ex_falso_quodlibet(self) -> None:
        """Tests extraction for falsum elimination: _bot => P."""
        goal = Implies(FALSUM, self.p)
        tree, term, typ = prove_ljt_checked(goal)
        self.assertIsNotNone(term)
        self.assertEqual(typ, formula_to_type(goal))

    def test_first_order_quantifier_extraction(self) -> None:
        """Tests extraction for forall x. P(x) => exists x. P(x)."""
        x = Variable(1, sort=Ind)
        px = PredicateApp("P", 1, (x,))
        goal = Implies(Forall(x, px), Exists(x, px))

        tree, term, typ = prove_ljt_checked(goal)
        self.assertIsNotNone(term)
        self.assertIsInstance(term, Abs)

    def test_classical_unprovability(self) -> None:
        """Tests that non-constructive formulas (P | ~P) yield no proof term."""
        lem = Or(self.p, Not(self.p))
        proof = self.prover.prove(lem)
        self.assertIsNone(proof)
        with self.assertRaises(Exception):
            prove_ljt_checked(lem)


class TestBHKWitnessExtraction(unittest.TestCase):
    """Tests BHK computational witness extraction for exists and or goals."""

    def setUp(self) -> None:
        self.p = PredicateApp("P", 0, ())
        self.q = PredicateApp("Q", 0, ())
        self.c = Constant("c0", sort=Ind)
        self.x = Variable(1, sort=Ind)

    def test_disjunction_witness_left_and_right(self) -> None:
        """Tests witness extraction from disjunction proofs."""
        # Goal: P | Q  proved from premise P
        proof_l = prove_ljt(Or(self.p, self.q), premises=[self.p])
        self.assertIsNotNone(proof_l)
        term_l = extract_ljt_term(proof_l)
        wit_l = extract_witness(term_l, Or(self.p, self.q))
        self.assertIsNotNone(wit_l)
        assert wit_l is not None
        self.assertEqual(wit_l.kind, "disjunction")
        self.assertEqual(wit_l.branch, 1)

        # Goal: P | Q  proved from premise Q
        proof_r = prove_ljt(Or(self.p, self.q), premises=[self.q])
        self.assertIsNotNone(proof_r)
        term_r = extract_ljt_term(proof_r)
        wit_r = extract_witness(term_r, Or(self.p, self.q))
        self.assertIsNotNone(wit_r)
        assert wit_r is not None
        self.assertEqual(wit_r.kind, "disjunction")
        self.assertEqual(wit_r.branch, 2)

    def test_existential_witness_extraction(self) -> None:
        """Tests extraction of concrete ground term witness for exists x. P(x)."""
        px = PredicateApp("P", 1, (self.x,))
        pc = PredicateApp("P", 1, (self.c,))
        goal = Exists(self.x, px)

        proof = prove_ljt(goal, premises=[pc])
        self.assertIsNotNone(proof)
        term = extract_ljt_term(proof)
        wit = extract_witness(term, goal)
        self.assertIsNotNone(wit)
        assert wit is not None
        self.assertEqual(wit.kind, "existential")
        self.assertEqual(wit.witness_term, self.c)

    def test_extract_program_api(self) -> None:
        """Tests the unified extract_program entrypoint."""
        pc = PredicateApp("P", 1, (self.c,))
        goal = Exists(self.x, PredicateApp("P", 1, (self.x,)))
        proof = prove_ljt(goal, premises=[pc])
        term, wit = extract_program(proof, target=goal, premises=[pc])
        self.assertIsNotNone(term)
        self.assertIsNotNone(wit)
        assert wit is not None
        self.assertEqual(wit.witness_term, self.c)


class TestMultiProverDispatcherAndExporters(unittest.TestCase):
    """Tests term extraction from Tableau and Wallen provers and export to Lean 4."""

    def setUp(self) -> None:
        self.p = PredicateApp("P", 0, ())
        self.q = PredicateApp("Q", 0, ())

    def test_extract_term_from_tableau(self) -> None:
        """Tests extraction dispatcher from a TableauProofResult."""
        goal = Implies(self.p, self.p)
        tab_prover = TableauProver()
        tab_res = tab_prover.prove(goal)
        self.assertTrue(tab_res.is_valid)

        term = extract_term(tab_res, target=goal)
        self.assertIsNotNone(term)
        assert term is not None
        self.assertEqual(infer_type(term), ArrowType(AtomType("P"), AtomType("P")))

    def test_extract_term_from_wallen(self) -> None:
        """Tests extraction dispatcher from a WallenProofResult."""
        goal = Implies(self.p, self.p)
        wal_prover = WallenProver()
        wal_res = wal_prover.prove(goal)
        self.assertTrue(wal_res.is_valid)

        term = extract_term(wal_res, target=goal)
        self.assertIsNotNone(term)
        assert term is not None
        self.assertEqual(infer_type(term), ArrowType(AtomType("P"), AtomType("P")))

    def test_lean_export_proof_term(self) -> None:
        """Tests LeanExporter.export_proof_term generates valid Lean 4 syntax."""
        exp = LeanExporter()
        term = Abs("x", AtomType("P"), Var("x"))
        code = exp.export_proof_term(term, name="id_p")
        self.assertIn("def id_p : (P → P) :=", code)
        self.assertIn("fun (x : P) => x", code)


class TestCLIProofTermFlag(unittest.TestCase):
    """Tests CLI prove-intuitionistic command with --extract-term flag."""

    def test_cli_extract_term_string(self) -> None:
        """Tests CLI extraction with default string format."""
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
            term_format="string",
        )
        ret = cmd_prove_intuitionistic(args, config)
        self.assertEqual(ret, 0)

    def test_cli_extract_term_lean(self) -> None:
        """Tests CLI extraction with Lean format."""
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
            term_format="lean",
        )
        ret = cmd_prove_intuitionistic(args, config)
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
