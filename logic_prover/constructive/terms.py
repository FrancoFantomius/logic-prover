"""Simply-typed lambda calculus with Curry-Howard proof-term AST, type checker, normalizer, and BHK witness extraction.

This module provides the intermediate typed functional representation of constructive proofs
under the Curry-Howard / BHK isomorphism, supporting sums, products, unit, void, dependent
existential witnesses, universal abstractions, and primitive recursion.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Set, Tuple, List, Union, Sequence

from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.parser import to_string


# ============================================================================
# Type AST
# ============================================================================

class ProofType(ABC):
    """Abstract base class for typed lambda calculus types representing propositions under Curry-Howard."""

    @abstractmethod
    def to_string(self) -> str:
        """Formats the type as a human-readable string.

        Returns:
            str: String representation of the type.
        """
        pass

    def __str__(self) -> str:
        """Returns the default string representation of the type."""
        return self.to_string()


@dataclass(frozen=True)
class AtomType(ProofType):
    """Represents an atomic proposition type (e.g. P, Q, P(c)).

    Args:
        name (str): The name or identifier of the atomic proposition.

    Example:
        >>> from logic_prover.constructive.terms import AtomType
        >>> t = AtomType("P")
        >>> t.to_string()
        'P'
    """

    name: str

    def to_string(self) -> str:
        """Formats the atomic type as a string.

        Returns:
            str: The name of the atomic proposition.
        """
        return self.name


@dataclass(frozen=True)
class ArrowType(ProofType):
    """Represents a function type A -> B (implication A => B).

    Args:
        left (ProofType): Domain argument type.
        right (ProofType): Codomain result type.

    Example:
        >>> from logic_prover.constructive.terms import AtomType, ArrowType
        >>> t = ArrowType(AtomType("P"), AtomType("Q"))
        >>> t.to_string()
        '(P -> Q)'
    """

    left: ProofType
    right: ProofType

    def to_string(self) -> str:
        """Formats the arrow type as a string.

        Returns:
            str: String in the format '(A -> B)'.
        """
        return f"({self.left.to_string()} -> {self.right.to_string()})"


@dataclass(frozen=True)
class ProdType(ProofType):
    """Represents a product type A * B (conjunction A & B).

    Args:
        left (ProofType): Left component type.
        right (ProofType): Right component type.

    Example:
        >>> from logic_prover.constructive.terms import AtomType, ProdType
        >>> t = ProdType(AtomType("P"), AtomType("Q"))
        >>> t.to_string()
        '(P * Q)'
    """

    left: ProofType
    right: ProofType

    def to_string(self) -> str:
        """Formats the product type as a string.

        Returns:
            str: String in the format '(A * B)'.
        """
        return f"({self.left.to_string()} * {self.right.to_string()})"


@dataclass(frozen=True)
class SumType(ProofType):
    """Represents a disjoint sum / coproduct type A + B (disjunction A | B).

    Args:
        left (ProofType): Left alternative type.
        right (ProofType): Right alternative type.

    Example:
        >>> from logic_prover.constructive.terms import AtomType, SumType
        >>> t = SumType(AtomType("P"), AtomType("Q"))
        >>> t.to_string()
        '(P + Q)'
    """

    left: ProofType
    right: ProofType

    def to_string(self) -> str:
        """Formats the sum type as a string.

        Returns:
            str: String in the format '(A + B)'.
        """
        return f"({self.left.to_string()} + {self.right.to_string()})"


@dataclass(frozen=True)
class UnitType(ProofType):
    """Represents the unit type Unit (truth / Verum).

    Example:
        >>> from logic_prover.constructive.terms import UnitType
        >>> t = UnitType()
        >>> t.to_string()
        'Unit'
    """

    def to_string(self) -> str:
        """Formats the unit type as a string.

        Returns:
            str: Constant string 'Unit'.
        """
        return "Unit"


@dataclass(frozen=True)
class VoidType(ProofType):
    """Represents the empty / bottom type Void (falsity / Falsum).

    Example:
        >>> from logic_prover.constructive.terms import VoidType
        >>> t = VoidType()
        >>> t.to_string()
        'Void'
    """

    def to_string(self) -> str:
        """Formats the void type as a string.

        Returns:
            str: Constant string 'Void'.
        """
        return "Void"


@dataclass(frozen=True)
class ForallType(ProofType):
    """Represents a universal dependent product type Pi x:D. B(x).

    Args:
        var (str): The bound variable identifier.
        body (ProofType): The parameterized body type.

    Example:
        >>> from logic_prover.constructive.terms import AtomType, ForallType
        >>> t = ForallType("x", AtomType("P(x)"))
        >>> t.to_string()
        '(forall x. P(x))'
    """

    var: str
    body: ProofType

    def to_string(self) -> str:
        """Formats the universal type as a string.

        Returns:
            str: Formatted forall string.
        """
        return f"(forall {self.var}. {self.body.to_string()})"


@dataclass(frozen=True)
class ExistsType(ProofType):
    """Represents an existential dependent sum type Sigma x:D. B(x).

    Args:
        var (str): The bound variable identifier.
        body (ProofType): The parameterized body type.

    Example:
        >>> from logic_prover.constructive.terms import AtomType, ExistsType
        >>> t = ExistsType("x", AtomType("P(x)"))
        >>> t.to_string()
        '(exists x. P(x))'
    """

    var: str
    body: ProofType

    def to_string(self) -> str:
        """Formats the existential type as a string.

        Returns:
            str: Formatted exists string.
        """
        return f"(exists {self.var}. {self.body.to_string()})"


@dataclass(frozen=True)
class EqType(ProofType):
    """Represents an equality proposition type t1 = t2.

    Args:
        left (Any): Left term expression.
        right (Any): Right term expression.

    Example:
        >>> from logic_prover.constructive.terms import EqType
        >>> t = EqType("a", "b")
        >>> t.to_string()
        '(a = b)'
    """

    left: Any
    right: Any

    def to_string(self) -> str:
        """Formats the equality type as a string.

        Returns:
            str: Formatted equality equation string.
        """
        l_str = self.left.to_string() if hasattr(self.left, "to_string") else str(self.left)
        r_str = self.right.to_string() if hasattr(self.right, "to_string") else str(self.right)
        return f"({l_str} = {r_str})"


def formula_to_type(f: Formula) -> ProofType:
    """Translates a logic Formula AST node into its corresponding Curry-Howard ProofType.

    Args:
        f (Formula): The source logic formula to convert.

    Returns:
        ProofType: The corresponding constructive lambda type.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.terms import formula_to_type
        >>> p = PredicateApp("P", 0, ())
        >>> t = formula_to_type(Implies(p, p))
        >>> t.to_string()
        '(P -> P)'
    """
    from logic_prover.constructive.common import _is_falsum, _is_verum

    if _is_falsum(f):
        return VoidType()
    if _is_verum(f):
        return UnitType()
    if isinstance(f, Equality):
        return EqType(f.left, f.right)
    if isinstance(f, PredicateApp):
        return AtomType(to_string(f))
    if isinstance(f, Not):
        return ArrowType(formula_to_type(f.operand), VoidType())
    if isinstance(f, And):
        return ProdType(formula_to_type(f.left), formula_to_type(f.right))
    if isinstance(f, Or):
        return SumType(formula_to_type(f.left), formula_to_type(f.right))
    if isinstance(f, Implies):
        return ArrowType(formula_to_type(f.left), formula_to_type(f.right))
    if isinstance(f, Iff):
        left_type = formula_to_type(f.left)
        right_type = formula_to_type(f.right)
        return ProdType(ArrowType(left_type, right_type), ArrowType(right_type, left_type))
    if isinstance(f, Forall):
        v_name = f.variable.name if hasattr(f.variable, "name") else f"v{f.variable.id}"
        return ForallType(v_name, formula_to_type(f.body))
    if isinstance(f, Exists):
        v_name = f.variable.name if hasattr(f.variable, "name") else f"v{f.variable.id}"
        return ExistsType(v_name, formula_to_type(f.body))
    return AtomType(to_string(f))


# ============================================================================
# Proof-Term AST
# ============================================================================

class ProofTerm(ABC):
    """Abstract base class for Curry-Howard proof terms in simply-typed lambda calculus."""

    @abstractmethod
    def to_string(self) -> str:
        """Formats the proof term as a readable string.

        Returns:
            str: String representation of the term.
        """
        pass

    def __str__(self) -> str:
        """Returns the default string representation of the proof term."""
        return self.to_string()


@dataclass(frozen=True)
class Var(ProofTerm):
    """Represents a term variable (proof hypothesis or parameter).

    Args:
        name (str): Variable identifier.
        type (Optional[ProofType], default=None): Optional annotated type.

    Example:
        >>> from logic_prover.constructive.terms import Var
        >>> x = Var("x")
        >>> x.to_string()
        'x'
    """

    name: str
    type: Optional[ProofType] = None

    def to_string(self) -> str:
        """Formats the variable as a string.

        Returns:
            str: Variable name.
        """
        return self.name


@dataclass(frozen=True)
class Abs(ProofTerm):
    """Represents a lambda abstraction λ(var: var_type). body.

    Args:
        var (str): Parameter variable name.
        var_type (Optional[ProofType]): Parameter type annotation.
        body (ProofTerm): Abstraction body proof term.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, AtomType
        >>> term = Abs("x", AtomType("P"), Var("x"))
        >>> term.to_string()
        '(lambda x: P. x)'
    """

    var: str
    var_type: Optional[ProofType]
    body: ProofTerm

    def to_string(self) -> str:
        """Formats the lambda abstraction as a string.

        Returns:
            str: Lambda expression string.
        """
        type_str = f": {self.var_type.to_string()}" if self.var_type is not None else ""
        return f"(lambda {self.var}{type_str}. {self.body.to_string()})"


@dataclass(frozen=True)
class App(ProofTerm):
    """Represents a function application (fn arg).

    Args:
        fn (ProofTerm): The function term being applied.
        arg (ProofTerm): The argument term passed to the function.

    Example:
        >>> from logic_prover.constructive.terms import Var, App
        >>> term = App(Var("f"), Var("x"))
        >>> term.to_string()
        '(f x)'
    """

    fn: ProofTerm
    arg: ProofTerm

    def to_string(self) -> str:
        """Formats the application as a string.

        Returns:
            str: Application expression string.
        """
        return f"({self.fn.to_string()} {self.arg.to_string()})"


@dataclass(frozen=True)
class Pair(ProofTerm):
    """Represents a pair ⟨left, right⟩ (conjunction introduction).

    Args:
        left (ProofTerm): Left component term.
        right (ProofTerm): Right component term.

    Example:
        >>> from logic_prover.constructive.terms import Var, Pair
        >>> term = Pair(Var("a"), Var("b"))
        >>> term.to_string()
        '⟨a, b⟩'
    """

    left: ProofTerm
    right: ProofTerm

    def to_string(self) -> str:
        """Formats the pair as a string.

        Returns:
            str: Pair expression string.
        """
        return f"⟨{self.left.to_string()}, {self.right.to_string()}⟩"


@dataclass(frozen=True)
class Fst(ProofTerm):
    """Represents the first projection fst(term) of a product pair.

    Args:
        term (ProofTerm): Pair term to project.

    Example:
        >>> from logic_prover.constructive.terms import Var, Fst
        >>> term = Fst(Var("p"))
        >>> term.to_string()
        'fst(p)'
    """

    term: ProofTerm

    def to_string(self) -> str:
        """Formats first projection as a string.

        Returns:
            str: First projection expression.
        """
        return f"fst({self.term.to_string()})"


@dataclass(frozen=True)
class Snd(ProofTerm):
    """Represents the second projection snd(term) of a product pair.

    Args:
        term (ProofTerm): Pair term to project.

    Example:
        >>> from logic_prover.constructive.terms import Var, Snd
        >>> term = Snd(Var("p"))
        >>> term.to_string()
        'snd(p)'
    """

    term: ProofTerm

    def to_string(self) -> str:
        """Formats second projection as a string.

        Returns:
            str: Second projection expression.
        """
        return f"snd({self.term.to_string()})"


@dataclass(frozen=True)
class Inl(ProofTerm):
    """Represents left injection inl(term) into a disjoint sum (disjunction left introduction).

    Args:
        term (ProofTerm): Proof term for the left alternative.
        sum_type (Optional[SumType], default=None): Target sum type annotation.

    Example:
        >>> from logic_prover.constructive.terms import Var, Inl
        >>> term = Inl(Var("a"))
        >>> term.to_string()
        'inl(a)'
    """

    term: ProofTerm
    sum_type: Optional[SumType] = None

    def to_string(self) -> str:
        """Formats left injection as a string.

        Returns:
            str: Left injection expression.
        """
        return f"inl({self.term.to_string()})"


@dataclass(frozen=True)
class Inr(ProofTerm):
    """Represents right injection inr(term) into a disjoint sum (disjunction right introduction).

    Args:
        term (ProofTerm): Proof term for the right alternative.
        sum_type (Optional[SumType], default=None): Target sum type annotation.

    Example:
        >>> from logic_prover.constructive.terms import Var, Inr
        >>> term = Inr(Var("b"))
        >>> term.to_string()
        'inr(b)'
    """

    term: ProofTerm
    sum_type: Optional[SumType] = None

    def to_string(self) -> str:
        """Formats right injection as a string.

        Returns:
            str: Right injection expression.
        """
        return f"inr({self.term.to_string()})"


@dataclass(frozen=True)
class Case(ProofTerm):
    """Represents case analysis over a disjoint sum: case s of inl(x) => l_body | inr(y) => r_body.

    Args:
        scrutinee (ProofTerm): Sum term being inspected.
        left_var (str): Variable binding for left alternative.
        left_body (ProofTerm): Expression evaluating when left alternative matches.
        right_var (str): Variable binding for right alternative.
        right_body (ProofTerm): Expression evaluating when right alternative matches.

    Example:
        >>> from logic_prover.constructive.terms import Var, Case
        >>> term = Case(Var("s"), "x", Var("x"), "y", Var("y"))
        >>> "case s of" in term.to_string()
        True
    """

    scrutinee: ProofTerm
    left_var: str
    left_body: ProofTerm
    right_var: str
    right_body: ProofTerm

    def to_string(self) -> str:
        """Formats case analysis as a string.

        Returns:
            str: Case expression string.
        """
        return (
            f"case {self.scrutinee.to_string()} of "
            f"inl({self.left_var}) => {self.left_body.to_string()} | "
            f"inr({self.right_var}) => {self.right_body.to_string()}"
        )


@dataclass(frozen=True)
class Unit(ProofTerm):
    """Represents the canonical unit value () (proof of Verum).

    Example:
        >>> from logic_prover.constructive.terms import Unit
        >>> u = Unit()
        >>> u.to_string()
        '()'
    """

    def to_string(self) -> str:
        """Formats unit as a string.

        Returns:
            str: Constant string '()'.
        """
        return "()"


@dataclass(frozen=True)
class Abort(ProofTerm):
    """Represents ex falso quodlibet: abort(target_type, term) from a proof of Void.

    Args:
        target_type (ProofType): Target type being derived.
        term (ProofTerm): Subterm proving Void / Falsum.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abort, AtomType
        >>> term = Abort(AtomType("P"), Var("f"))
        >>> term.to_string()
        'abort(P, f)'
    """

    target_type: ProofType
    term: ProofTerm

    def to_string(self) -> str:
        """Formats abort as a string.

        Returns:
            str: Abort expression string.
        """
        return f"abort({self.target_type.to_string()}, {self.term.to_string()})"


@dataclass(frozen=True)
class Refl(ProofTerm):
    """Represents identity / reflexivity proof term refl(t) for equality t = t.

    Args:
        term (Any): The term expression that is equal to itself.

    Example:
        >>> from logic_prover.constructive.terms import Refl
        >>> r = Refl("a")
        >>> r.to_string()
        'refl(a)'
    """

    term: Any

    def to_string(self) -> str:
        """Formats reflexivity as a string.

        Returns:
            str: Reflexivity expression string.
        """
        t_str = self.term.to_string() if hasattr(self.term, "to_string") else str(self.term)
        return f"refl({t_str})"


@dataclass(frozen=True)
class Subst(ProofTerm):
    """Represents equality substitution / rewrite plumbing term subst(eq_proof, term).

    Args:
        eq_proof (ProofTerm): Proof term establishing equality.
        term (ProofTerm): Proof term to rewrite across equality.

    Example:
        >>> from logic_prover.constructive.terms import Var, Subst
        >>> s = Subst(Var("eq"), Var("p"))
        >>> s.to_string()
        'subst(eq, p)'
    """

    eq_proof: ProofTerm
    term: ProofTerm

    def to_string(self) -> str:
        """Formats substitution as a string.

        Returns:
            str: Substitution expression string.
        """
        return f"subst({self.eq_proof.to_string()}, {self.term.to_string()})"


@dataclass(frozen=True)
class ExistsIntro(ProofTerm):
    """Represents an existential package ⟨witness, proof⟩ proving exists x. P(x).

    Args:
        witness (Any): Concrete witness term.
        proof (ProofTerm): Proof term establishing P(witness).
        exists_type (Optional[ExistsType], default=None): Target existential type.

    Example:
        >>> from logic_prover.constructive.terms import Var, ExistsIntro
        >>> term = ExistsIntro("c", Var("p"))
        >>> term.to_string()
        '⟨c, p⟩'
    """

    witness: Any
    proof: ProofTerm
    exists_type: Optional[ExistsType] = None

    def to_string(self) -> str:
        """Formats existential introduction as a string.

        Returns:
            str: Pair expression ⟨witness, proof⟩.
        """
        w_str = self.witness.to_string() if hasattr(self.witness, "to_string") else str(self.witness)
        return f"⟨{w_str}, {self.proof.to_string()}⟩"


@dataclass(frozen=True)
class ExistsElim(ProofTerm):
    """Represents existential elimination / unpacking: unpack scrutinee as ⟨witness_var, proof_var⟩ in body.

    Args:
        scrutinee (ProofTerm): Existential package to unpack.
        witness_var (str): Variable binding for the witness term.
        proof_var (str): Variable binding for the witness proof.
        body (ProofTerm): Resulting proof term using the unpacked witness and proof.

    Example:
        >>> from logic_prover.constructive.terms import Var, ExistsElim
        >>> term = ExistsElim(Var("e"), "w", "p", Var("p"))
        >>> "unpack" in term.to_string()
        True
    """

    scrutinee: ProofTerm
    witness_var: str
    proof_var: str
    body: ProofTerm

    def to_string(self) -> str:
        """Formats existential elimination as a string.

        Returns:
            str: Unpack expression string.
        """
        return (
            f"unpack {self.scrutinee.to_string()} as ⟨{self.witness_var}, {self.proof_var}⟩ "
            f"in {self.body.to_string()}"
        )


@dataclass(frozen=True)
class NatRec(ProofTerm):
    """Represents primitive recursion over natural numbers: natrec(zero_case, n. ih. succ_case, target).

    Args:
        zero_case (ProofTerm): Proof term for the base case (0).
        succ_var_n (str): Bound variable for the predecessor number.
        succ_var_ih (str): Bound variable for the inductive hypothesis proof.
        succ_case (ProofTerm): Proof term for the successor step case.
        target (ProofTerm): The target natural number term on which induction is performed.

    Example:
        >>> from logic_prover.constructive.terms import Var, NatRec
        >>> term = NatRec(Var("z"), "n", "ih", Var("ih"), Var("k"))
        >>> "natrec" in term.to_string()
        True
    """

    zero_case: ProofTerm
    succ_var_n: str
    succ_var_ih: str
    succ_case: ProofTerm
    target: ProofTerm

    def to_string(self) -> str:
        """Formats primitive recursion as a string.

        Returns:
            str: NatRec expression string.
        """
        return (
            f"natrec({self.zero_case.to_string()}, "
            f"λ{self.succ_var_n} {self.succ_var_ih}. {self.succ_case.to_string()}, "
            f"{self.target.to_string()})"
        )


# ============================================================================
# Free Variables and Capture-Avoiding Substitution
# ============================================================================

def free_vars(term: ProofTerm) -> Set[str]:
    """Computes the set of free term variable identifiers occurring within a ProofTerm.

    Args:
        term (ProofTerm): The proof term to inspect.

    Returns:
        Set[str]: Set of free variable names.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, free_vars
        >>> t = Abs("x", None, Var("y"))
        >>> free_vars(t) == {"y"}
        True
    """
    if isinstance(term, Var):
        return {term.name}
    elif isinstance(term, Abs):
        return free_vars(term.body) - {term.var}
    elif isinstance(term, App):
        return free_vars(term.fn) | free_vars(term.arg)
    elif isinstance(term, Pair):
        return free_vars(term.left) | free_vars(term.right)
    elif isinstance(term, (Fst, Snd)):
        return free_vars(term.term)
    elif isinstance(term, (Inl, Inr)):
        return free_vars(term.term)
    elif isinstance(term, Case):
        fv = free_vars(term.scrutinee)
        fv |= free_vars(term.left_body) - {term.left_var}
        fv |= free_vars(term.right_body) - {term.right_var}
        return fv
    elif isinstance(term, Unit):
        return set()
    elif isinstance(term, Abort):
        return free_vars(term.term)
    elif isinstance(term, Refl):
        return set()
    elif isinstance(term, Subst):
        return free_vars(term.eq_proof) | free_vars(term.term)
    elif isinstance(term, ExistsIntro):
        return free_vars(term.proof)
    elif isinstance(term, ExistsElim):
        fv = free_vars(term.scrutinee)
        fv |= free_vars(term.body) - {term.witness_var, term.proof_var}
        return fv
    elif isinstance(term, NatRec):
        fv = free_vars(term.zero_case) | free_vars(term.target)
        fv |= free_vars(term.succ_case) - {term.succ_var_n, term.succ_var_ih}
        return fv
    return set()


def _fresh_name(base: str, avoid: Set[str]) -> str:
    """Generates a fresh variable name based on base not occurring in avoid.

    Args:
        base (str): Base prefix identifier.
        avoid (Set[str]): Collection of occupied variable names.

    Returns:
        str: Guaranteed fresh identifier.
    """
    candidate = base
    counter = 1
    while candidate in avoid:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def substitute_term(term: ProofTerm, var_name: str, replacement: ProofTerm) -> ProofTerm:
    """Performs capture-avoiding substitution term[replacement / var_name].

    Args:
        term (ProofTerm): Target proof term to undergo substitution.
        var_name (str): Identifier of the variable redex being replaced.
        replacement (ProofTerm): Contractum term to substitute in.

    Returns:
        ProofTerm: The substituted proof term.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, substitute_term
        >>> body = Var("x")
        >>> subst = substitute_term(body, "x", Var("y"))
        >>> subst.to_string()
        'y'
    """
    repl_fv = free_vars(replacement)

    def _sub(t: ProofTerm) -> ProofTerm:
        if isinstance(t, Var):
            return replacement if t.name == var_name else t
        elif isinstance(t, Abs):
            if t.var == var_name:
                return t
            if t.var in repl_fv:
                avoid = repl_fv | free_vars(t.body) | {var_name}
                new_var = _fresh_name(t.var, avoid)
                renamed_body = substitute_term(t.body, t.var, Var(new_var))
                return Abs(new_var, t.var_type, _sub(renamed_body))
            return Abs(t.var, t.var_type, _sub(t.body))
        elif isinstance(t, App):
            return App(_sub(t.fn), _sub(t.arg))
        elif isinstance(t, Pair):
            return Pair(_sub(t.left), _sub(t.right))
        elif isinstance(t, Fst):
            return Fst(_sub(t.term))
        elif isinstance(t, Snd):
            return Snd(_sub(t.term))
        elif isinstance(t, Inl):
            return Inl(_sub(t.term), t.sum_type)
        elif isinstance(t, Inr):
            return Inr(_sub(t.term), t.sum_type)
        elif isinstance(t, Case):
            new_scrutinee = _sub(t.scrutinee)
            # Left branch
            left_v = t.left_var
            left_b = t.left_body
            if left_v == var_name:
                pass
            elif left_v in repl_fv:
                avoid = repl_fv | free_vars(left_b) | {var_name}
                new_left_v = _fresh_name(left_v, avoid)
                left_b = substitute_term(left_b, left_v, Var(new_left_v))
                left_v = new_left_v
                left_b = substitute_term(left_b, var_name, replacement)
            else:
                left_b = substitute_term(left_b, var_name, replacement)

            # Right branch
            right_v = t.right_var
            right_b = t.right_body
            if right_v == var_name:
                pass
            elif right_v in repl_fv:
                avoid = repl_fv | free_vars(right_b) | {var_name}
                new_right_v = _fresh_name(right_v, avoid)
                right_b = substitute_term(right_b, right_v, Var(new_right_v))
                right_v = new_right_v
                right_b = substitute_term(right_b, var_name, replacement)
            else:
                right_b = substitute_term(right_b, var_name, replacement)

            return Case(new_scrutinee, left_v, left_b, right_v, right_b)
        elif isinstance(t, Unit):
            return t
        elif isinstance(t, Abort):
            return Abort(t.target_type, _sub(t.term))
        elif isinstance(t, Refl):
            return t
        elif isinstance(t, Subst):
            return Subst(_sub(t.eq_proof), _sub(t.term))
        elif isinstance(t, ExistsIntro):
            return ExistsIntro(t.witness, _sub(t.proof), t.exists_type)
        elif isinstance(t, ExistsElim):
            new_scrutinee = _sub(t.scrutinee)
            wv = t.witness_var
            pv = t.proof_var
            body = t.body
            if var_name in (wv, pv):
                return ExistsElim(new_scrutinee, wv, pv, body)
            avoid = repl_fv | free_vars(body) | {var_name}
            new_wv = wv
            new_pv = pv
            if wv in repl_fv:
                new_wv = _fresh_name(wv, avoid)
                avoid.add(new_wv)
                body = substitute_term(body, wv, Var(new_wv))
            if pv in repl_fv:
                new_pv = _fresh_name(pv, avoid)
                body = substitute_term(body, pv, Var(new_pv))
            return ExistsElim(new_scrutinee, new_wv, new_pv, substitute_term(body, var_name, replacement))
        elif isinstance(t, NatRec):
            new_zero = _sub(t.zero_case)
            new_target = _sub(t.target)
            vn = t.succ_var_n
            vih = t.succ_var_ih
            sc = t.succ_case
            if var_name in (vn, vih):
                return NatRec(new_zero, vn, vih, sc, new_target)
            avoid = repl_fv | free_vars(sc) | {var_name}
            new_vn = vn
            new_vih = vih
            if vn in repl_fv:
                new_vn = _fresh_name(vn, avoid)
                avoid.add(new_vn)
                sc = substitute_term(sc, vn, Var(new_vn))
            if vih in repl_fv:
                new_vih = _fresh_name(vih, avoid)
                sc = substitute_term(sc, vih, Var(new_vih))
            return NatRec(new_zero, new_vn, new_vih, substitute_term(sc, var_name, replacement), new_target)
        return t

    return _sub(term)


# ============================================================================
# Type Inference and Type Checking
# ============================================================================

def infer_type(term: ProofTerm, ctx: Optional[Dict[str, ProofType]] = None) -> ProofType:
    """Infers the Curry-Howard ProofType of a given ProofTerm under typing context ctx.

    Args:
        term (ProofTerm): The term whose type is to be deduced.
        ctx (Optional[Dict[str, ProofType]], default=None): Variable typing context mapping names to ProofTypes.

    Returns:
        ProofType: The inferred type of the term.

    Raises:
        TypeError: If the term is ill-typed or contains unbound variables.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, infer_type, AtomType
        >>> p = AtomType("P")
        >>> term = Abs("x", p, Var("x"))
        >>> infer_type(term).to_string()
        '(P -> P)'
    """
    if ctx is None:
        ctx = {}

    if isinstance(term, Var):
        if term.name in ctx:
            return ctx[term.name]
        if term.type is not None:
            return term.type
        raise TypeError(f"Unbound variable '{term.name}' not found in typing context {list(ctx.keys())}")

    elif isinstance(term, Abs):
        if term.var_type is None:
            raise TypeError(f"Cannot infer type for unannotated lambda parameter '{term.var}'")
        new_ctx = dict(ctx)
        new_ctx[term.var] = term.var_type
        body_type = infer_type(term.body, new_ctx)
        return ArrowType(term.var_type, body_type)

    elif isinstance(term, App):
        fn_type = infer_type(term.fn, ctx)
        if isinstance(fn_type, ArrowType):
            arg_type = infer_type(term.arg, ctx)
            if arg_type != fn_type.left:
                raise TypeError(
                    f"Type mismatch in function application: function expects {fn_type.left}, "
                    f"but argument has type {arg_type}"
                )
            return fn_type.right
        elif isinstance(fn_type, ForallType):
            return fn_type.body
        else:
            raise TypeError(f"Cannot apply non-function term of type {fn_type}")

    elif isinstance(term, Pair):
        left_type = infer_type(term.left, ctx)
        right_type = infer_type(term.right, ctx)
        return ProdType(left_type, right_type)

    elif isinstance(term, Fst):
        p_type = infer_type(term.term, ctx)
        if not isinstance(p_type, ProdType):
            raise TypeError(f"fst expected product type, got {p_type}")
        return p_type.left

    elif isinstance(term, Snd):
        p_type = infer_type(term.term, ctx)
        if not isinstance(p_type, ProdType):
            raise TypeError(f"snd expected product type, got {p_type}")
        return p_type.right

    elif isinstance(term, Inl):
        inner_type = infer_type(term.term, ctx)
        if term.sum_type is not None:
            if inner_type != term.sum_type.left:
                raise TypeError(
                    f"inl type mismatch: expected left type {term.sum_type.left}, got {inner_type}"
                )
            return term.sum_type
        return SumType(inner_type, AtomType("?"))

    elif isinstance(term, Inr):
        inner_type = infer_type(term.term, ctx)
        if term.sum_type is not None:
            if inner_type != term.sum_type.right:
                raise TypeError(
                    f"inr type mismatch: expected right type {term.sum_type.right}, got {inner_type}"
                )
            return term.sum_type
        return SumType(AtomType("?"), inner_type)

    elif isinstance(term, Case):
        s_type = infer_type(term.scrutinee, ctx)
        if not isinstance(s_type, SumType):
            raise TypeError(f"case scrutinee must have sum type, got {s_type}")
        left_ctx = dict(ctx)
        left_ctx[term.left_var] = s_type.left
        left_res = infer_type(term.left_body, left_ctx)

        right_ctx = dict(ctx)
        right_ctx[term.right_var] = s_type.right
        right_res = infer_type(term.right_body, right_ctx)

        if left_res != right_res:
            raise TypeError(
                f"Branch type mismatch in case: left branch produces {left_res}, "
                f"right branch produces {right_res}"
            )
        return left_res

    elif isinstance(term, Unit):
        return UnitType()

    elif isinstance(term, Abort):
        t_type = infer_type(term.term, ctx)
        if not isinstance(t_type, VoidType):
            raise TypeError(f"abort requires term of type Void, got {t_type}")
        return term.target_type

    elif isinstance(term, Refl):
        return EqType(term.term, term.term)

    elif isinstance(term, Subst):
        eq_type = infer_type(term.eq_proof, ctx)
        if not isinstance(eq_type, EqType):
            raise TypeError(f"subst requires equality proof, got {eq_type}")
        return infer_type(term.term, ctx)

    elif isinstance(term, ExistsIntro):
        p_type = infer_type(term.proof, ctx)
        if term.exists_type is not None:
            return term.exists_type
        w_name = term.witness.name if hasattr(term.witness, "name") else str(term.witness)
        return ExistsType(w_name, p_type)

    elif isinstance(term, ExistsElim):
        s_type = infer_type(term.scrutinee, ctx)
        if not isinstance(s_type, ExistsType):
            raise TypeError(f"unpack requires existential type, got {s_type}")
        body_ctx = dict(ctx)
        body_ctx[term.proof_var] = s_type.body
        return infer_type(term.body, body_ctx)

    elif isinstance(term, NatRec):
        z_type = infer_type(term.zero_case, ctx)
        succ_ctx = dict(ctx)
        succ_ctx[term.succ_var_n] = AtomType("Nat")
        succ_ctx[term.succ_var_ih] = z_type
        step_type = infer_type(term.succ_case, succ_ctx)
        if step_type != z_type:
            raise TypeError(f"natrec step case type {step_type} does not match base type {z_type}")
        return z_type

    raise TypeError(f"Unknown proof term node: {type(term)}")


# ============================================================================
# Beta Normalization
# ============================================================================

def beta_normalize(term: ProofTerm, max_steps: int = 1000) -> ProofTerm:
    """Reduces a ProofTerm to its beta-normal form using capture-avoiding substitution.

    Evaluates lambda applications (App of Abs), pair projections (Fst/Snd of Pair),
    case analyses over injections (Case of Inl/Inr), existential unpacks (ExistsElim of ExistsIntro),
    and primitive recursions (NatRec).

    Args:
        term (ProofTerm): Proof term to normalize.
        max_steps (int, default=1000): Maximum reduction evaluation step limit.

    Returns:
        ProofTerm: Beta-normalized proof term.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, App, AtomType, beta_normalize
        >>> p = AtomType("P")
        >>> id_fn = Abs("x", p, Var("x"))
        >>> redex = App(id_fn, Var("y"))
        >>> norm = beta_normalize(redex)
        >>> norm.to_string()
        'y'
    """
    current = term
    for _ in range(max_steps):
        changed, next_term = _step_normalize(current)
        if not changed:
            return current
        current = next_term
    return current


def _step_normalize(term: ProofTerm) -> Tuple[bool, ProofTerm]:
    """Attempts a single head reduction step on the term.

    Args:
        term (ProofTerm): The term to step.

    Returns:
        Tuple[bool, ProofTerm]: Pair (did_step, new_term).
    """
    if isinstance(term, App):
        # 1. Lambda application redex: (λx. body) arg -> body[arg/x]
        if isinstance(term.fn, Abs):
            return True, substitute_term(term.fn.body, term.fn.var, term.arg)
        # Try reducing function
        c, new_fn = _step_normalize(term.fn)
        if c:
            return True, App(new_fn, term.arg)
        # Try reducing argument
        c, new_arg = _step_normalize(term.arg)
        if c:
            return True, App(term.fn, new_arg)

    elif isinstance(term, Fst):
        if isinstance(term.term, Pair):
            return True, term.term.left
        c, new_t = _step_normalize(term.term)
        if c:
            return True, Fst(new_t)

    elif isinstance(term, Snd):
        if isinstance(term.term, Pair):
            return True, term.term.right
        c, new_t = _step_normalize(term.term)
        if c:
            return True, Snd(new_t)

    elif isinstance(term, Case):
        if isinstance(term.scrutinee, Inl):
            return True, substitute_term(term.left_body, term.left_var, term.scrutinee.term)
        if isinstance(term.scrutinee, Inr):
            return True, substitute_term(term.right_body, term.right_var, term.scrutinee.term)
        c, new_s = _step_normalize(term.scrutinee)
        if c:
            return True, Case(new_s, term.left_var, term.left_body, term.right_var, term.right_body)

    elif isinstance(term, ExistsElim):
        if isinstance(term.scrutinee, ExistsIntro):
            step1 = substitute_term(term.body, term.witness_var, Var(str(term.scrutinee.witness)))
            step2 = substitute_term(step1, term.proof_var, term.scrutinee.proof)
            return True, step2
        c, new_s = _step_normalize(term.scrutinee)
        if c:
            return True, ExistsElim(new_s, term.witness_var, term.proof_var, term.body)

    elif isinstance(term, NatRec):
        t_str = term.target.to_string() if hasattr(term.target, "to_string") else str(term.target)
        if t_str in ("0", "zero", "Constant('zero')"):
            return True, term.zero_case
        c, new_tgt = _step_normalize(term.target)
        if c:
            return True, NatRec(term.zero_case, term.succ_var_n, term.succ_var_ih, term.succ_case, new_tgt)

    elif isinstance(term, Abs):
        c, new_b = _step_normalize(term.body)
        if c:
            return True, Abs(term.var, term.var_type, new_b)

    elif isinstance(term, Pair):
        c, new_l = _step_normalize(term.left)
        if c:
            return True, Pair(new_l, term.right)
        c, new_r = _step_normalize(term.right)
        if c:
            return True, Pair(term.left, new_r)

    elif isinstance(term, Inl):
        c, new_t = _step_normalize(term.term)
        if c:
            return True, Inl(new_t, term.sum_type)

    elif isinstance(term, Inr):
        c, new_t = _step_normalize(term.term)
        if c:
            return True, Inr(new_t, term.sum_type)

    return False, term


# ============================================================================
# Pretty Printers: String, LaTeX, Lean 4
# ============================================================================

def term_to_string(term: ProofTerm) -> str:
    """Formats a ProofTerm as a human-readable lambda calculus expression string.

    Args:
        term (ProofTerm): The term to format.

    Returns:
        str: String representation of the term.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, term_to_string
        >>> term_to_string(Abs("x", None, Var("x")))
        '(lambda x. x)'
    """
    return term.to_string()


def type_to_string(typ: ProofType) -> str:
    """Formats a ProofType as a string.

    Args:
        typ (ProofType): Target type.

    Returns:
        str: String representation of the type.

    Example:
        >>> from logic_prover.constructive.terms import AtomType, type_to_string
        >>> type_to_string(AtomType("P"))
        'P'
    """
    return typ.to_string()


def term_to_latex(term: ProofTerm) -> str:
    """Formats a ProofTerm into LaTeX mathematical notation.

    Args:
        term (ProofTerm): Proof term to translate.

    Returns:
        str: LaTeX code snippet.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, term_to_latex
        >>> term_to_latex(Abs("x", None, Var("x")))
        '(\\\\lambda x. x)'
    """
    if isinstance(term, Var):
        return term.name
    elif isinstance(term, Abs):
        return f"(\\lambda {term.var}. {term_to_latex(term.body)})"
    elif isinstance(term, App):
        return f"({term_to_latex(term.fn)}\\, {term_to_latex(term.arg)})"
    elif isinstance(term, Pair):
        return f"\\langle {term_to_latex(term.left)}, {term_to_latex(term.right)} \\rangle"
    elif isinstance(term, Fst):
        return f"\\pi_1({term_to_latex(term.term)})"
    elif isinstance(term, Snd):
        return f"\\pi_2({term_to_latex(term.term)})"
    elif isinstance(term, Inl):
        return f"\\mathrm{{inl}}({term_to_latex(term.term)})"
    elif isinstance(term, Inr):
        return f"\\mathrm{{inr}}({term_to_latex(term.term)})"
    elif isinstance(term, Case):
        return (
            f"\\mathbf{{case}}\\; {term_to_latex(term.scrutinee)}\\; \\mathbf{{of}}\\; "
            f"\\mathrm{{inl}}({term.left_var}) \\Rightarrow {term_to_latex(term.left_body)} \\mid "
            f"\\mathrm{{inr}}({term.right_var}) \\Rightarrow {term_to_latex(term.right_body)}"
        )
    elif isinstance(term, Unit):
        return "()"
    elif isinstance(term, Abort):
        return f"\\mathrm{{abort}}({term_to_latex(term.term)})"
    elif isinstance(term, Refl):
        return f"\\mathrm{{refl}}({term.term})"
    elif isinstance(term, Subst):
        return f"\\mathrm{{subst}}({term_to_latex(term.eq_proof)}, {term_to_latex(term.term)})"
    elif isinstance(term, ExistsIntro):
        return f"\\langle {term.witness}, {term_to_latex(term.proof)} \\rangle"
    elif isinstance(term, ExistsElim):
        return (
            f"\\mathbf{{unpack}}\\; {term_to_latex(term.scrutinee)}\\; \\mathbf{{as}}\\; "
            f"\\langle {term.witness_var}, {term.proof_var} \\rangle\\; \\mathbf{{in}}\\; "
            f"{term_to_latex(term.body)}"
        )
    elif isinstance(term, NatRec):
        return (
            f"\\mathrm{{natrec}}({term_to_latex(term.zero_case)}, "
            f"\\lambda {term.succ_var_n}\\, {term.succ_var_ih}. {term_to_latex(term.succ_case)}, "
            f"{term_to_latex(term.target)})"
        )
    return str(term)


def type_to_latex(typ: ProofType) -> str:
    """Formats a ProofType into LaTeX mathematical notation.

    Args:
        typ (ProofType): Target type.

    Returns:
        str: LaTeX code snippet.

    Example:
        >>> from logic_prover.constructive.terms import AtomType, ArrowType, type_to_latex
        >>> type_to_latex(ArrowType(AtomType("P"), AtomType("Q")))
        '(P \\\\to Q)'
    """
    if isinstance(typ, AtomType):
        return typ.name
    elif isinstance(typ, ArrowType):
        return f"({type_to_latex(typ.left)} \\to {type_to_latex(typ.right)})"
    elif isinstance(typ, ProdType):
        return f"({type_to_latex(typ.left)} \\times {type_to_latex(typ.right)})"
    elif isinstance(typ, SumType):
        return f"({type_to_latex(typ.left)} \\oplus {type_to_latex(typ.right)})"
    elif isinstance(typ, UnitType):
        return "\\top"
    elif isinstance(typ, VoidType):
        return "\\bot"
    elif isinstance(typ, ForallType):
        return f"(\\forall {typ.var}.\\; {type_to_latex(typ.body)})"
    elif isinstance(typ, ExistsType):
        return f"(\\exists {typ.var}.\\; {type_to_latex(typ.body)})"
    elif isinstance(typ, EqType):
        return f"({typ.left} = {typ.right})"
    return str(typ)


def term_to_lean(term: ProofTerm) -> str:
    """Translates a ProofTerm into valid Lean 4 syntax.

    Args:
        term (ProofTerm): Target proof term.

    Returns:
        str: Lean 4 term expression string.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, term_to_lean
        >>> term_to_lean(Abs("x", None, Var("x")))
        '(fun x => x)'
    """
    if isinstance(term, Var):
        return term.name
    elif isinstance(term, Abs):
        type_str = f" : {type_to_lean(term.var_type)}" if term.var_type is not None else ""
        return f"(fun ({term.var}{type_str}) => {term_to_lean(term.body)})"
    elif isinstance(term, App):
        return f"({term_to_lean(term.fn)} {term_to_lean(term.arg)})"
    elif isinstance(term, Pair):
        return f"({term_to_lean(term.left)}, {term_to_lean(term.right)})"
    elif isinstance(term, Fst):
        return f"({term_to_lean(term.term)}).1"
    elif isinstance(term, Snd):
        return f"({term_to_lean(term.term)}).2"
    elif isinstance(term, Inl):
        return f"(Sum.inl {term_to_lean(term.term)})"
    elif isinstance(term, Inr):
        return f"(Sum.inr {term_to_lean(term.term)})"
    elif isinstance(term, Case):
        return (
            f"(match {term_to_lean(term.scrutinee)} with "
            f"| Sum.inl {term.left_var} => {term_to_lean(term.left_body)} "
            f"| Sum.inr {term.right_var} => {term_to_lean(term.right_body)})"
        )
    elif isinstance(term, Unit):
        return "()"
    elif isinstance(term, Abort):
        return f"(nomatch {term_to_lean(term.term)})"
    elif isinstance(term, Refl):
        return "rfl"
    elif isinstance(term, Subst):
        return f"({term_to_lean(term.eq_proof)} ▸ {term_to_lean(term.term)})"
    elif isinstance(term, ExistsIntro):
        w_str = term.witness.to_string() if hasattr(term.witness, "to_string") else str(term.witness)
        return f"⟨{w_str}, {term_to_lean(term.proof)}⟩"
    elif isinstance(term, ExistsElim):
        return (
            f"(let ⟨{term.witness_var}, {term.proof_var}⟩ := {term_to_lean(term.scrutinee)}; "
            f"{term_to_lean(term.body)})"
        )
    elif isinstance(term, NatRec):
        return (
            f"(Nat.rec {term_to_lean(term.zero_case)} "
            f"(fun {term.succ_var_n} {term.succ_var_ih} => {term_to_lean(term.succ_case)}) "
            f"{term_to_lean(term.target)})"
        )
    return str(term)


def type_to_lean(typ: ProofType) -> str:
    """Translates a ProofType into Lean 4 type syntax.

    Args:
        typ (ProofType): Target type.

    Returns:
        str: Lean 4 type string.

    Example:
        >>> from logic_prover.constructive.terms import AtomType, ArrowType, type_to_lean
        >>> type_to_lean(ArrowType(AtomType("P"), AtomType("Q")))
        '(P → Q)'
    """
    if isinstance(typ, AtomType):
        return typ.name
    elif isinstance(typ, ArrowType):
        return f"({type_to_lean(typ.left)} → {type_to_lean(typ.right)})"
    elif isinstance(typ, ProdType):
        return f"({type_to_lean(typ.left)} × {type_to_lean(typ.right)})"
    elif isinstance(typ, SumType):
        return f"({type_to_lean(typ.left)} ⊕ {type_to_lean(typ.right)})"
    elif isinstance(typ, UnitType):
        return "Unit"
    elif isinstance(typ, VoidType):
        return "Empty"
    elif isinstance(typ, ForallType):
        return f"(∀ ({typ.var} : _), {type_to_lean(typ.body)})"
    elif isinstance(typ, ExistsType):
        return f"(∃ ({typ.var} : _), {type_to_lean(typ.body)})"
    elif isinstance(typ, EqType):
        return f"({typ.left} = {typ.right})"
    return str(typ)


# ============================================================================
# BHK Witness Extraction Container & Functions
# ============================================================================

@dataclass
class Witness:
    """Container holding extracted constructive witness information from a proof.

    Args:
        kind (str): The kind of witness ('existential' or 'disjunction').
        branch (Optional[int], default=None): Disjunction branch choice (1 for left, 2 for right).
        witness_term (Optional[Any], default=None): Concrete instantiated witness term for exists.
        proof_term (Optional[ProofTerm], default=None): Accompanying proof term.

    Example:
        >>> from logic_prover.constructive.terms import Witness, Var
        >>> w = Witness(kind="disjunction", branch=1, proof_term=Var("p"))
        >>> w.kind
        'disjunction'
    """

    kind: str
    branch: Optional[int] = None
    witness_term: Optional[Any] = None
    proof_term: Optional[ProofTerm] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes witness data to a dictionary.

        Returns:
            Dict[str, Any]: Structured dictionary representation.

        Example:
            >>> from logic_prover.constructive.terms import Witness
            >>> w = Witness(kind="existential", witness_term="c0")
            >>> w.to_dict()["kind"]
            'existential'
        """
        w_str = None
        if self.witness_term is not None:
            w_str = self.witness_term.to_string() if hasattr(self.witness_term, "to_string") else str(self.witness_term)
        p_str = term_to_string(self.proof_term) if self.proof_term is not None else None
        return {
            "kind": self.kind,
            "branch": self.branch,
            "witness_term": w_str,
            "proof_term": p_str,
        }

    def to_string(self) -> str:
        """Formats the witness as a human-readable summary.

        Returns:
            str: Description of extracted witness.

        Example:
            >>> from logic_prover.constructive.terms import Witness
            >>> w = Witness(kind="existential", witness_term="c0")
            >>> "witness" in w.to_string()
            True
        """
        if self.kind == "existential":
            w_str = self.witness_term.to_string() if hasattr(self.witness_term, "to_string") else str(self.witness_term)
            return f"Existential witness: {w_str}"
        elif self.kind == "disjunction":
            return f"Disjunction branch: {self.branch} ({'left' if self.branch == 1 else 'right'})"
        return f"Witness({self.kind})"

    def __str__(self) -> str:
        """Returns string representation of the witness."""
        return self.to_string()


def extract_witness(term: ProofTerm, formula: Formula) -> Optional[Witness]:
    """Extracts a BHK computational witness for an existential or disjunctive goal from its proof term.

    Args:
        term (ProofTerm): The extracted proof term.
        formula (Formula): The theorem formula that was proven.

    Returns:
        Optional[Witness]: Extracted Witness container if formula is existential or disjunctive, None otherwise.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Constant, Exists, Variable
        >>> from logic_prover.core.sorts import Ind
        >>> from logic_prover.constructive.terms import ExistsIntro, Var, extract_witness
        >>> x = Variable(1, sort=Ind)
        >>> c = Constant("c0", sort=Ind)
        >>> goal = Exists(x, PredicateApp("P", 1, (x,)))
        >>> term = ExistsIntro(c, Var("p"))
        >>> wit = extract_witness(term, goal)
        >>> wit is not None and wit.witness_term == c
        True
    """
    norm_term = beta_normalize(term)

    if isinstance(formula, Exists):
        if isinstance(norm_term, ExistsIntro):
            return Witness(
                kind="existential",
                witness_term=norm_term.witness,
                proof_term=norm_term.proof,
            )
        # Search inside nested expressions
        if isinstance(norm_term, Abs):
            sub_w = extract_witness(norm_term.body, formula)
            if sub_w is not None:
                return sub_w

    elif isinstance(formula, Or):
        if isinstance(norm_term, Inl):
            return Witness(
                kind="disjunction",
                branch=1,
                proof_term=norm_term.term,
            )
        elif isinstance(norm_term, Inr):
            return Witness(
                kind="disjunction",
                branch=2,
                proof_term=norm_term.term,
            )

    return None


def extract_program(
    proof_result: Any,
    target: Formula,
    premises: Optional[Sequence[Formula]] = None
) -> Tuple[ProofTerm, Optional[Witness]]:
    """Extracts the executable lambda proof term and its BHK witness from any constructive proof result.

    Args:
        proof_result (Any): Prover result object (e.g. LJTProofTree, TableauProofResult, WallenProofResult).
        target (Formula): Proved theorem goal formula.
        premises (Optional[Sequence[Formula]], default=None): Hypotheses used in proof.

    Returns:
        Tuple[ProofTerm, Optional[Witness]]: Pair of extracted proof term and optional witness.

    Raises:
        ValueError: If no constructive proof term could be extracted.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.ljt import prove_ljt
        >>> from logic_prover.constructive.terms import extract_program
        >>> p = PredicateApp("P", 0, ())
        >>> goal = Implies(p, p)
        >>> proof = prove_ljt(goal)
        >>> term, wit = extract_program(proof, goal)
        >>> term is not None
        True
    """
    term = extract_term(proof_result, target=target, premises=premises)
    if term is None:
        raise ValueError("Could not extract proof term from proof result.")
    witness = extract_witness(term, target)
    return term, witness


def extract_term(
    result: Any,
    target: Optional[Formula] = None,
    premises: Optional[Sequence[Formula]] = None
) -> Optional[ProofTerm]:
    """Universal dispatcher extracting a ProofTerm from any constructive prover result.

    If result is an LJTProofTree, its root term is returned directly. For refutation provers
    (Tableau, Wallen, Prefixed Resolution, IK), the goal is re-proved via LJT to obtain
    its natural constructive proof term.

    Args:
        result (Any): Proof derivation or proof result container.
        target (Optional[Formula], default=None): Target goal formula if re-proving is needed.
        premises (Optional[Sequence[Formula]], default=None): Hypothesis formulas if re-proving is needed.

    Returns:
        Optional[ProofTerm]: Extracted proof term, or None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.ljt import prove_ljt
        >>> from logic_prover.constructive.terms import extract_term
        >>> p = PredicateApp("P", 0, ())
        >>> goal = Implies(p, p)
        >>> proof = prove_ljt(goal)
        >>> term = extract_term(proof)
        >>> term is not None
        True
    """
    # 1. Direct LJTProofTree extraction
    if hasattr(result, "root") and hasattr(result.root, "term"):
        if result.root.term is not None:
            return result.root.term

    # 2. Re-proving translation fallback for other constructive provers
    goal = target
    if goal is None and hasattr(result, "target"):
        goal = getattr(result, "target")
    if goal is None and hasattr(result, "formula"):
        goal = getattr(result, "formula")

    hyps = premises
    if hyps is None and hasattr(result, "premises"):
        hyps = getattr(result, "premises")

    hyps_list: Optional[List[Formula]] = list(hyps) if hyps is not None else None

    if goal is not None:
        from logic_prover.constructive.ljt import LJTProver
        prover = LJTProver()
        ljt_proof = prover.prove(target=goal, premises=hyps_list)
        if ljt_proof is not None and ljt_proof.root.term is not None:
            return ljt_proof.root.term

    return None


__all__ = [
    # Types
    "ProofType",
    "AtomType",
    "ArrowType",
    "ProdType",
    "SumType",
    "UnitType",
    "VoidType",
    "ForallType",
    "ExistsType",
    "EqType",
    "formula_to_type",
    # Terms
    "ProofTerm",
    "Var",
    "Abs",
    "App",
    "Pair",
    "Fst",
    "Snd",
    "Inl",
    "Inr",
    "Case",
    "Unit",
    "Abort",
    "Refl",
    "Subst",
    "ExistsIntro",
    "ExistsElim",
    "NatRec",
    # Functions
    "free_vars",
    "substitute_term",
    "infer_type",
    "beta_normalize",
    "term_to_string",
    "type_to_string",
    "term_to_latex",
    "type_to_latex",
    "term_to_lean",
    "type_to_lean",
    # BHK Witness Extraction
    "Witness",
    "extract_witness",
    "extract_program",
    "extract_term",
]
