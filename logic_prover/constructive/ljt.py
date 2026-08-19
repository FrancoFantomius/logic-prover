"""Roy Dyckhoff's Contraction-Free Sequent Calculus (LJT / G4ip) for Intuitionistic Logic.

This module implements the contraction-free sequent calculus LJT (Dyckhoff 1992)
extended with first-order quantifier rules for Intuitionistic First-Order Logic (IQC / iFOL).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Set, Iterable

from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists, free_variables
)
from logic_prover.core.parser import to_string
from logic_prover.core.substitutions import substitute_formula
from logic_prover.core.equality import equality_substitution
from logic_prover.constructive.common import (
    FALSUM,
    VERUM,
    _is_falsum,
    _is_verum,
    _is_atomic,
    kbo_compare,
    normalize_formula,
    _formula_weight,
    fresh_constant,
    ground_terms,
)


def _collect_constants_and_functions(
    formulas: Iterable[Formula]
) -> Tuple[Set[Constant], Set[Tuple[str, int]]]:
    """Extracts all constants and function signature declarations occurring in given formulas.

    Args:
        formulas (Iterable[Formula]): Collection of formula AST nodes.

    Returns:
        Tuple[Set[Constant], Set[Tuple[str, int]]]: Set of constants and set of (func_name, arity) pairs.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Constant
        >>> from logic_prover.constructive.ljt import _collect_constants_and_functions
        >>> c = Constant("c0")
        >>> p = PredicateApp("P", 1, (c,))
        >>> consts, fns = _collect_constants_and_functions([p])
        >>> c in consts
        True
    """
    constants: Set[Constant] = set()
    functions: Set[Tuple[str, int]] = set()

    def _traverse_term(t: Term) -> None:
        if isinstance(t, Constant):
            constants.add(t)
        elif isinstance(t, FunctionApp):
            if isinstance(t.func, str):
                functions.add((t.func, t.arity))
            for arg in t.args:
                _traverse_term(arg)

    def _traverse_formula(f: Formula) -> None:
        if isinstance(f, PredicateApp):
            for arg in f.args:
                _traverse_term(arg)
        elif isinstance(f, Equality):
            _traverse_term(f.left)
            _traverse_term(f.right)
        elif isinstance(f, Not):
            _traverse_formula(f.operand)
        elif isinstance(f, (And, Or, Implies, Iff)):
            _traverse_formula(f.left)
            _traverse_formula(f.right)
        elif isinstance(f, (Forall, Exists)):
            _traverse_formula(f.body)

    for form in formulas:
        _traverse_formula(form)

    return constants, functions


@dataclass(frozen=True)
class Sequent:
    """Represents a single-conclusion intuitionistic sequent Gamma => G.

    Args:
        antecedents (Tuple[Formula, ...], default=()): Tuple of antecedent hypothesis formulas.
        succedent (Formula, default=FALSUM): Goal succedent formula.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.ljt import Sequent
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> seq = Sequent(antecedents=(p,), succedent=p)
        >>> len(seq.antecedents)
        1
    """

    antecedents: Tuple[Formula, ...] = field(default_factory=tuple)
    succedent: Formula = field(default=FALSUM)

    def __post_init__(self) -> None:
        """Ensures antecedents are stored as a tuple."""
        if not isinstance(self.antecedents, tuple):
            object.__setattr__(self, "antecedents", tuple(self.antecedents))

    def to_string(self, notation: str = "infix") -> str:
        """Formats the sequent as a human-readable string.

        Args:
            notation (str, default='infix'): String notation ('infix' or 'latex').

        Returns:
            str: String representation of the sequent.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ljt import Sequent
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> seq = Sequent(antecedents=(p,), succedent=p)
            >>> seq.to_string()
            'P ==> P'
        """
        def fmt(f: Formula) -> str:
            if _is_falsum(f):
                return "\\bot" if notation == "latex" else "_bot"
            if _is_verum(f):
                return "\\top" if notation == "latex" else "_top"
            return to_string(f, notation=notation)

        ant_str = ", ".join(fmt(a) for a in self.antecedents)
        succ_str = fmt(self.succedent)
        turnstile = " \\vdash " if notation == "latex" else " ==> "
        return f"{ant_str}{turnstile}{succ_str}"

    def __str__(self) -> str:
        """Returns the default infix string representation of the sequent."""
        return self.to_string(notation="infix")


@dataclass(frozen=True)
class LJTProofNode:
    """Represents a node in an LJT derivation tree.

    Args:
        sequent (Sequent): The sequent established at this derivation node.
        rule (str): The name of the deduction rule applied.
        premises (Tuple[LJTProofNode, ...], default=()): Child premise proof nodes.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.ljt import Sequent, LJTProofNode
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> node = LJTProofNode(sequent=Sequent((p,), p), rule="Ax")
        >>> node.rule
        'Ax'
    """

    sequent: Sequent
    rule: str
    premises: Tuple[LJTProofNode, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the proof node and its subtree to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary structure of the proof tree.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ljt import Sequent, LJTProofNode
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> node = LJTProofNode(sequent=Sequent((p,), p), rule="Ax")
            >>> node.to_dict()["rule"]
            'Ax'
        """
        return {
            "sequent": self.sequent.to_string(),
            "rule": self.rule,
            "premises": [p.to_dict() for p in self.premises],
        }


class LJTProofTree:
    """Container and visualization manager for an LJT deduction tree."""

    root: LJTProofNode

    def __init__(self, root: LJTProofNode) -> None:
        """Initializes the proof tree.

        Args:
            root (LJTProofNode): The root node of the derivation.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ljt import Sequent, LJTProofNode, LJTProofTree
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> tree = LJTProofTree(LJTProofNode(Sequent((p,), p), "Ax"))
            >>> tree.is_valid()
            True
        """
        self.root = root

    @property
    def depth(self) -> int:
        """Computes the height of the proof derivation tree.

        Returns:
            int: The maximum depth of the derivation tree.
        """
        def _get_depth(node: LJTProofNode) -> int:
            if not node.premises:
                return 1
            return 1 + max(_get_depth(p) for p in node.premises)

        return _get_depth(self.root)

    @property
    def size(self) -> int:
        """Computes the total number of deduction steps in the proof tree.

        Returns:
            int: Total node count in the derivation.
        """
        def _get_size(node: LJTProofNode) -> int:
            return 1 + sum(_get_size(p) for p in node.premises)

        return _get_size(self.root)

    def is_valid(self) -> bool:
        """Validates that all leaves in the derivation tree are closed axioms.

        Returns:
            bool: True if every leaf is an established axiom, False otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ljt import Sequent, LJTProofNode, LJTProofTree
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> tree = LJTProofTree(LJTProofNode(Sequent((p,), p), "Ax"))
            >>> tree.is_valid()
            True
        """
        axiom_rules = {"Ax", "L_Bot", "R_Top", "R_Refl"}

        def _check(node: LJTProofNode) -> bool:
            if not node.premises:
                return node.rule in axiom_rules
            return all(_check(p) for p in node.premises)

        return _check(self.root)

    def to_ascii(self) -> str:
        """Generates an ASCII visualization of the sequent calculus proof tree.

        Returns:
            str: Multi-line string showing the formatted deduction tree.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ljt import Sequent, LJTProofNode, LJTProofTree
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> tree = LJTProofTree(LJTProofNode(Sequent((p,), p), "Ax"))
            >>> "Ax" in tree.to_ascii()
            True
        """
        lines: List[str] = []

        def _render(node: LJTProofNode, prefix: str = "", is_last: bool = True) -> None:
            branch = "`-- " if is_last else "|-- "
            lines.append(f"{prefix}{branch}[{node.rule}] {node.sequent}")
            next_prefix = prefix + ("    " if is_last else "|   ")
            for i, p in enumerate(node.premises):
                _render(p, next_prefix, i == len(node.premises) - 1)

        lines.append(f"[{self.root.rule}] {self.root.sequent}")
        for i, p in enumerate(self.root.premises):
            _render(p, "", i == len(self.root.premises) - 1)
        return "\n".join(lines)

    def to_latex(self) -> str:
        """Exports the proof tree into LaTeX bussproofs format.

        Returns:
            str: LaTeX code snippet utilizing the bussproofs package.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ljt import Sequent, LJTProofNode, LJTProofTree
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> tree = LJTProofTree(LJTProofNode(Sequent((p,), p), "Ax"))
            >>> "\\\\AxiomC" in tree.to_latex()
            True
        """
        lines: List[str] = ["\\begin{prooftree}"]

        def _rec(node: LJTProofNode) -> None:
            if not node.premises:
                lines.append(f"  \\AxiomC{{}}")
                lines.append(f"  \\RightLabel{{{node.rule}}}")
                lines.append(f"  \\UnaryInfC{{{node.sequent.to_string(notation='latex')}}}")
            else:
                for p in node.premises:
                    _rec(p)
                label = f"  \\RightLabel{{{node.rule}}}"
                lines.append(label)
                if len(node.premises) == 1:
                    lines.append(f"  \\UnaryInfC{{{node.sequent.to_string(notation='latex')}}}")
                elif len(node.premises) == 2:
                    lines.append(f"  \\BinaryInfC{{{node.sequent.to_string(notation='latex')}}}")
                elif len(node.premises) == 3:
                    lines.append(f"  \\TrinaryInfC{{{node.sequent.to_string(notation='latex')}}}")
                else:
                    lines.append(f"  \\QuaternaryInfC{{{node.sequent.to_string(notation='latex')}}}")

        _rec(self.root)
        lines.append("\\end{prooftree}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the proof tree to a structured dictionary.

        Returns:
            Dict[str, Any]: Structured tree data.
        """
        return {
            "root": self.root.to_dict(),
            "depth": self.depth,
            "size": self.size,
            "is_valid": self.is_valid(),
        }

    def __str__(self) -> str:
        """Returns the ASCII representation of the proof tree."""
        return self.to_ascii()


class LJTProver:
    """Automated Theorem Prover for Intuitionistic First-Order Logic with Equality (iFOL=) using LJT / G4ip calculus.

    Args:
        max_term_depth (int, default=2): Maximum function nesting depth for ground term enumeration.
        max_depth (int, default=100): Maximum search derivation depth bound.
        eq_subst_max (int, default=5): Maximum depth/count for equality substitution steps per branch.
    """

    max_term_depth: int
    max_depth: int
    eq_subst_max: int

    def __init__(self, max_term_depth: int = 2, max_depth: int = 100, eq_subst_max: int = 5) -> None:
        """Initializes the LJT theorem prover instance.

        Args:
            max_term_depth (int, default=2): Maximum term nesting depth for quantifier instantiation.
            max_depth (int, default=100): Search recursion depth limit.
            eq_subst_max (int, default=5): Maximum number of equality substitution applications.

        Example:
            >>> from logic_prover.constructive.ljt import LJTProver
            >>> prover = LJTProver(max_term_depth=2)
            >>> isinstance(prover, LJTProver)
            True
        """
        self.max_term_depth = max(0, max_term_depth)
        self.max_depth = max(1, max_depth)
        self.eq_subst_max = max(0, eq_subst_max)

    def _get_ground_terms(self, gamma: Sequence[Formula], goal: Formula) -> List[Term]:
        """Computes available ground terms for quantifier instantiation from sequent formulas.

        Args:
            gamma (Sequence[Formula]): Current antecedent hypothesis formulas.
            goal (Formula): Current goal succedent formula.

        Returns:
            List[Term]: Ground terms up to max_term_depth.
        """
        all_forms = list(gamma) + [goal]
        consts, fns = _collect_constants_and_functions(all_forms)
        return ground_terms(constants=list(consts), functions=list(fns), max_depth=self.max_term_depth)

    def prove(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None
    ) -> Optional[LJTProofTree]:
        """Attempts to construct an intuitionistic LJT proof tree for target from premises.

        Args:
            target (Formula): The goal formula to be proved.
            premises (Optional[List[Formula]], default=None): Optional list of hypothesis formulas.

        Returns:
            Optional[LJTProofTree]: Complete derivation tree if provable, or None if unprovable.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.ljt import LJTProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = LJTProver()
            >>> proof = prover.prove(target=Implies(left=p, right=p))
            >>> proof is not None
            True
        """
        norm_target = normalize_formula(target)
        norm_premises = [normalize_formula(p) for p in (premises or [])]
        initial_sequent = Sequent(antecedents=tuple(norm_premises), succedent=norm_target)
        proof_node = self._search(initial_sequent, depth=0, instantiated_universals=frozenset(), eq_subst_count=0)
        if proof_node is not None:
            return LJTProofTree(root=proof_node)
        return None

    def is_provable(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None
    ) -> bool:
        """Checks whether a formula is intuitionistically valid in LJT calculus.

        Args:
            target (Formula): The goal formula to test.
            premises (Optional[List[Formula]], default=None): Optional list of hypotheses.

        Returns:
            bool: True if provable intuitionistically, False otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.ljt import LJTProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = LJTProver()
            >>> prover.is_provable(Implies(left=p, right=p))
            True
        """
        return self.prove(target=target, premises=premises) is not None

    def _search(
        self,
        seq: Sequent,
        depth: int = 0,
        instantiated_universals: frozenset[Tuple[Formula, Term]] = frozenset(),
        eq_subst_count: int = 0,
    ) -> Optional[LJTProofNode]:
        """Main recursive search procedure implementing Dyckhoff's LJT reduction rules for IQC.

        Invertible rules are executed deterministically first, followed by backtracking
        on non-invertible choices.

        Args:
            seq (Sequent): The current sequent to reduce.
            depth (int, default=0): Current search recursion depth.
            instantiated_universals (frozenset[Tuple[Formula, Term]], default=frozenset()): Tracked (universal, term) instantiations.
            eq_subst_count (int, default=0): Number of equality substitution steps performed on this branch.

        Returns:
            Optional[LJTProofNode]: The derivation node if provable, None otherwise.
        """
        if depth > self.max_depth:
            return None

        gamma = list(seq.antecedents)
        goal = seq.succedent

        # --- 1. AXIOM CHECKS ---
        # Right Verum
        if _is_verum(goal):
            return LJTProofNode(sequent=seq, rule="R_Top", premises=())

        # Left Falsum (Ex Falso Quodlibet)
        if any(_is_falsum(a) for a in gamma):
            return LJTProofNode(sequent=seq, rule="L_Bot", premises=())

        # Identity / Ax: Goal in Antecedents
        if goal in gamma:
            return LJTProofNode(sequent=seq, rule="Ax", premises=())

        # Right Reflexivity (Equality t = t on Right)
        if isinstance(goal, Equality) and goal.left == goal.right:
            return LJTProofNode(sequent=seq, rule="R_Refl", premises=())

        # --- 2. INVERTIBLE RIGHT RULES ---
        # (R =>): Implication on Right
        if isinstance(goal, Implies):
            prem_seq = Sequent(antecedents=tuple(gamma + [goal.left]), succedent=goal.right)
            prem_node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
            if prem_node is not None:
                return LJTProofNode(sequent=seq, rule="R_Imp", premises=(prem_node,))
            return None

        # (R &): Conjunction on Right
        if isinstance(goal, And):
            seq1 = Sequent(antecedents=tuple(gamma), succedent=goal.left)
            node1 = self._search(seq1, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
            if node1 is not None:
                seq2 = Sequent(antecedents=tuple(gamma), succedent=goal.right)
                node2 = self._search(seq2, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if node2 is not None:
                    return LJTProofNode(sequent=seq, rule="R_And", premises=(node1, node2))
            return None

        # (R Forall): Universal Quantifier on Right (Eigenvariable rule)
        if isinstance(goal, Forall):
            consts, _ = _collect_constants_and_functions(gamma + [goal])
            c = fresh_constant(prefix="c", existing_constants=consts)
            sub_body = normalize_formula(substitute_formula(goal.body, {goal.variable: c}))
            prem_seq = Sequent(antecedents=tuple(gamma), succedent=sub_body)
            prem_node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
            if prem_node is not None:
                return LJTProofNode(sequent=seq, rule="R_Forall", premises=(prem_node,))
            return None

        # --- 3. INVERTIBLE LEFT RULES ---
        # (L Refl): t = t on Left (delete reflexivity)
        for i, a in enumerate(gamma):
            if isinstance(a, Equality) and a.left == a.right:
                rest = gamma[:i] + gamma[i + 1:]
                prem_seq = Sequent(antecedents=tuple(rest), succedent=goal)
                prem_node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if prem_node is not None:
                    return LJTProofNode(sequent=seq, rule="L_Refl", premises=(prem_node,))
                return None

        # (L &): Conjunction on Left
        for i, a in enumerate(gamma):
            if isinstance(a, And):
                rest = gamma[:i] + gamma[i + 1:]
                prem_seq = Sequent(antecedents=tuple(rest + [a.left, a.right]), succedent=goal)
                prem_node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if prem_node is not None:
                    return LJTProofNode(sequent=seq, rule="L_And", premises=(prem_node,))
                return None

        # (L |): Disjunction on Left
        for i, a in enumerate(gamma):
            if isinstance(a, Or):
                rest = gamma[:i] + gamma[i + 1:]
                seq1 = Sequent(antecedents=tuple(rest + [a.left]), succedent=goal)
                node1 = self._search(seq1, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if node1 is not None:
                    seq2 = Sequent(antecedents=tuple(rest + [a.right]), succedent=goal)
                    node2 = self._search(seq2, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                    if node2 is not None:
                        return LJTProofNode(sequent=seq, rule="L_Or", premises=(node1, node2))
                return None

        # (L Exists): Existential Quantifier on Left (Eigenvariable rule)
        for i, a in enumerate(gamma):
            if isinstance(a, Exists):
                rest = gamma[:i] + gamma[i + 1:]
                consts, _ = _collect_constants_and_functions(gamma + [goal])
                c = fresh_constant(prefix="c", existing_constants=consts)
                sub_body = normalize_formula(substitute_formula(a.body, {a.variable: c}))
                prem_seq = Sequent(antecedents=tuple(rest + [sub_body]), succedent=goal)
                prem_node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if prem_node is not None:
                    return LJTProofNode(sequent=seq, rule="L_Exists", premises=(prem_node,))
                return None

        # (L => 1): Atom => B on Left when Atom in Gamma
        for i, a in enumerate(gamma):
            if isinstance(a, Implies) and _is_atomic(a.left):
                atom = a.left
                if atom in gamma:
                    rest = gamma[:i] + gamma[i + 1:]
                    prem_seq = Sequent(antecedents=tuple(rest + [a.right]), succedent=goal)
                    prem_node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                    if prem_node is not None:
                        return LJTProofNode(sequent=seq, rule="L_Imp_Atom", premises=(prem_node,))
                    return None

        # (L => 2): (C & D) => B on Left
        for i, a in enumerate(gamma):
            if isinstance(a, Implies) and isinstance(a.left, And):
                c = a.left.left
                d = a.left.right
                b = a.right
                decomp = Implies(left=c, right=Implies(left=d, right=b))
                rest = gamma[:i] + gamma[i + 1:]
                prem_seq = Sequent(antecedents=tuple(rest + [decomp]), succedent=goal)
                prem_node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if prem_node is not None:
                    return LJTProofNode(sequent=seq, rule="L_Imp_And", premises=(prem_node,))
                return None

        # (L => 3): (C | D) => B on Left
        for i, a in enumerate(gamma):
            if isinstance(a, Implies) and isinstance(a.left, Or):
                c = a.left.left
                d = a.left.right
                b = a.right
                decomp1 = Implies(left=c, right=b)
                decomp2 = Implies(left=d, right=b)
                rest = gamma[:i] + gamma[i + 1:]
                prem_seq = Sequent(antecedents=tuple(rest + [decomp1, decomp2]), succedent=goal)
                prem_node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if prem_node is not None:
                    return LJTProofNode(sequent=seq, rule="L_Imp_Or", premises=(prem_node,))
                return None

        # --- 4. NON-INVERTIBLE RULES (BACKTRACKING) ---
        # (R | 1, R | 2): Disjunction on Right
        if isinstance(goal, Or):
            seq1 = Sequent(antecedents=tuple(gamma), succedent=goal.left)
            node1 = self._search(seq1, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
            if node1 is not None:
                return LJTProofNode(sequent=seq, rule="R_Or1", premises=(node1,))

            seq2 = Sequent(antecedents=tuple(gamma), succedent=goal.right)
            node2 = self._search(seq2, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
            if node2 is not None:
                return LJTProofNode(sequent=seq, rule="R_Or2", premises=(node2,))

        # (R Exists): Existential Quantifier on Right (Witness term search)
        if isinstance(goal, Exists):
            candidate_terms = self._get_ground_terms(gamma, goal)
            for t in candidate_terms:
                inst = normalize_formula(substitute_formula(goal.body, {goal.variable: t}))
                prem_seq = Sequent(antecedents=tuple(gamma), succedent=inst)
                node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if node is not None:
                    return LJTProofNode(sequent=seq, rule="R_Exists", premises=(node,))

        # (L Forall): Universal Quantifier on Left (Instantiation with ground terms)
        for i, a in enumerate(gamma):
            if isinstance(a, Forall):
                candidate_terms = self._get_ground_terms(gamma, goal)
                for t in candidate_terms:
                    sig = (a, t)
                    if sig in instantiated_universals:
                        continue
                    inst = normalize_formula(substitute_formula(a.body, {a.variable: t}))
                    if inst in gamma:
                        continue
                    next_inst = instantiated_universals | {sig}
                    prem_seq = Sequent(antecedents=tuple(gamma + [inst]), succedent=goal)
                    node = self._search(prem_seq, depth=depth + 1, instantiated_universals=next_inst, eq_subst_count=eq_subst_count)
                    if node is not None:
                        return LJTProofNode(sequent=seq, rule="L_Forall", premises=(node,))

        # (L Eq Subst): Equality Substitution on Left oriented by KBO
        if eq_subst_count < self.eq_subst_max:
            for i, a in enumerate(gamma):
                if isinstance(a, Equality) and a.left != a.right:
                    cmp_res = kbo_compare(a.left, a.right)
                    # Determine directed rewrite orientations
                    orientations: List[Tuple[Term, Term]] = []
                    if cmp_res == "gt":
                        orientations.append((a.left, a.right))
                    elif cmp_res == "lt":
                        orientations.append((a.right, a.left))
                    else:
                        orientations.append((a.left, a.right))
                        orientations.append((a.right, a.left))

                    for src, dst in orientations:
                        eq_rule = Equality(src, dst)
                        # Substitute in goal
                        goal_vars = equality_substitution(eq_rule, goal)
                        for g_sub in goal_vars:
                            if g_sub != goal:
                                prem_seq = Sequent(antecedents=tuple(gamma), succedent=g_sub)
                                node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count + 1)
                                if node is not None:
                                    return LJTProofNode(sequent=seq, rule="L_Eq_Subst", premises=(node,))

                        # Substitute in hypotheses
                        for j, hyp in enumerate(gamma):
                            if j != i:
                                hyp_vars = equality_substitution(eq_rule, hyp)
                                for h_sub in hyp_vars:
                                    if h_sub != hyp and h_sub not in gamma:
                                        new_gamma = list(gamma) + [h_sub]
                                        prem_seq = Sequent(antecedents=tuple(new_gamma), succedent=goal)
                                        node = self._search(prem_seq, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count + 1)
                                        if node is not None:
                                            return LJTProofNode(sequent=seq, rule="L_Eq_Subst", premises=(node,))

        # (L => 4): (C => D) => B on Left
        for i, a in enumerate(gamma):
            if isinstance(a, Implies) and isinstance(a.left, Implies):
                c = a.left.left
                d = a.left.right
                b = a.right
                rest = gamma[:i] + gamma[i + 1:]

                d_imp_b = Implies(left=d, right=b)
                seq1 = Sequent(antecedents=tuple(rest + [d_imp_b, c]), succedent=d)
                node1 = self._search(seq1, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                if node1 is not None:
                    seq2 = Sequent(antecedents=tuple(rest + [b]), succedent=goal)
                    node2 = self._search(seq2, depth=depth + 1, instantiated_universals=instantiated_universals, eq_subst_count=eq_subst_count)
                    if node2 is not None:
                        return LJTProofNode(sequent=seq, rule="L_Imp_Imp", premises=(node1, node2))

        return None


def prove_ljt(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_term_depth: int = 2,
    eq_subst_max: int = 5
) -> Optional[LJTProofTree]:
    """Top-level convenience function to prove a formula using the LJT calculus with equality.

    Args:
        formula (Formula): The formula to prove.
        premises (Optional[List[Formula]], default=None): Optional list of hypothesis premises.
        max_term_depth (int, default=2): Maximum term depth for quantifier instantiation.
        eq_subst_max (int, default=5): Maximum number of equality substitution applications.

    Returns:
        Optional[LJTProofTree]: The derivation proof tree if valid, None if not provable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.ljt import prove_ljt
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> proof = prove_ljt(Implies(left=p, right=p))
        >>> proof is not None
        True
    """
    prover = LJTProver(max_term_depth=max_term_depth, eq_subst_max=eq_subst_max)
    return prover.prove(target=formula, premises=premises)


__all__ = [
    # Common symbols re-exported
    "FALSUM",
    "VERUM",
    "_is_falsum",
    "_is_verum",
    "_is_atomic",
    "normalize_formula",
    "_formula_weight",
    # LJT specific symbols
    "_collect_constants_and_functions",
    "Sequent",
    "LJTProofNode",
    "LJTProofTree",
    "LJTProver",
    "prove_ljt",
]

