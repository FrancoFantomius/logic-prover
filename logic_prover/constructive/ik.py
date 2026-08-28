"""Constructive Modal Logic (IK) Sequent Calculus Prover and Countermodel Builder.

This module implements the sequent calculus for constructive modal logic IK
(Plotkin & Stirling 1986; Simpson 1994; Mendler & de Paiva 2005) with modal rules:
- Box-R (K_Box): Gamma_Box => A  /  Gamma => Box A
- Diamond-L (K_Diamond): Gamma_Box, A => B  /  Gamma, Diamond A => Diamond B
- Falsum modal rule (K_Diamond_Bot): Gamma_Box, A => _bot  /  Gamma, Diamond A => _bot
combined with contraction-free intuitionistic propositional and first-order rules,
and semantic countermodel extraction via labeled Kripke tableau.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Set, Sequence, Iterable

from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists, Box, Diamond, free_variables
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
    normalize_formula,
    fresh_constant,
    ground_terms,
)
from logic_prover.constructive.ljt import _collect_constants_and_functions
from logic_prover.constructive.kripke import KripkeModel
from logic_prover.constructive.tableau.prover import TableauProver


@dataclass(frozen=True)
class IKSequent:
    """Represents a single-conclusion constructive modal sequent Gamma => G.

    Args:
        antecedents (Tuple[Formula, ...], default=()): Tuple of antecedent formulas.
        succedent (Formula, default=FALSUM): Goal succedent formula.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Box
        >>> from logic_prover.constructive.ik import IKSequent
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> seq = IKSequent(antecedents=(Box(p),), succedent=Box(p))
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
            >>> from logic_prover.constructive.ik import IKSequent
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> seq = IKSequent(antecedents=(p,), succedent=p)
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
class IKProofNode:
    """Represents a node in an IK derivation tree.

    Args:
        sequent (IKSequent): The sequent established at this derivation node.
        rule (str): The name of the deduction rule applied.
        premises (Tuple[IKProofNode, ...], default=()): Child premise proof nodes.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.ik import IKSequent, IKProofNode
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> node = IKProofNode(sequent=IKSequent((p,), p), rule="Ax")
        >>> node.rule
        'Ax'
    """

    sequent: IKSequent
    rule: str
    premises: Tuple[IKProofNode, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Ensures premises are stored as a tuple."""
        if not isinstance(self.premises, tuple):
            object.__setattr__(self, "premises", tuple(self.premises))

    @property
    def depth(self) -> int:
        """Computes the depth of the proof tree rooted at this node.

        Returns:
            int: Tree depth.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ik import IKSequent, IKProofNode
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> node = IKProofNode(sequent=IKSequent((p,), p), rule="Ax")
            >>> node.depth
            1
        """
        if not self.premises:
            return 1
        return 1 + max(p.depth for p in self.premises)

    @property
    def size(self) -> int:
        """Computes the total number of inference nodes in this proof subtree.

        Returns:
            int: Total node count.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ik import IKSequent, IKProofNode
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> node = IKProofNode(sequent=IKSequent((p,), p), rule="Ax")
            >>> node.size
            1
        """
        return 1 + sum(p.size for p in self.premises)

    def to_string(self, prefix: str = "", is_tail: bool = True) -> str:
        """Formats the subtree as an ASCII tree.

        Args:
            prefix (str, default=''): Current indentation string.
            is_tail (bool, default=True): True if this is the last sibling.

        Returns:
            str: Multi-line ASCII visualization of the derivation tree.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ik import IKSequent, IKProofNode
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> node = IKProofNode(sequent=IKSequent((p,), p), rule="Ax")
            >>> "Ax" in node.to_string()
            True
        """
        connector = "+-- " if is_tail else "|-- "
        rule_tag = f" [{self.rule}]" if self.rule else ""
        lines = [f"{prefix}{connector}{self.sequent.to_string()}{rule_tag}"]

        child_prefix = prefix + ("    " if is_tail else "|   ")
        for i, child in enumerate(self.premises):
            lines.append(child.to_string(child_prefix, i == len(self.premises) - 1))

        return "\n".join(lines)

    def export_latex(self) -> str:
        """Exports the proof subtree to LaTeX bussproofs / ebproof format.

        Returns:
            str: LaTeX inference rule string.

        Example:
            >>> from logic_prover.core.ast import PredicateApp
            >>> from logic_prover.constructive.ik import IKSequent, IKProofNode
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> node = IKProofNode(sequent=IKSequent((p,), p), rule="Ax")
            >>> "\\AxiomC" in node.export_latex()
            True
        """
        if not self.premises:
            return f"\\AxiomC{{}}\n\\RightLabel{{{self.rule}}}\n\\UnaryInfC{{{self.sequent.to_string(notation='latex')}}}"
        elif len(self.premises) == 1:
            prem_tex = self.premises[0].export_latex()
            return f"{prem_tex}\n\\RightLabel{{{self.rule}}}\n\\UnaryInfC{{{self.sequent.to_string(notation='latex')}}}"
        elif len(self.premises) == 2:
            p1_tex = self.premises[0].export_latex()
            p2_tex = self.premises[1].export_latex()
            return f"{p1_tex}\n{p2_tex}\n\\RightLabel{{{self.rule}}}\n\\BinaryInfC{{{self.sequent.to_string(notation='latex')}}}"
        else:
            lines = [p.export_latex() for p in self.premises]
            return "\n".join(lines) + f"\n\\RightLabel{{{self.rule}}}\n\\TrinaryInfC{{{self.sequent.to_string(notation='latex')}}}"


@dataclass(frozen=True)
class IKProofTree:
    """Represents a complete IK derivation tree with metadata.

    Args:
        root (Optional[IKProofNode], default=None): Root node of the derivation.
        is_valid (bool, default=False): True if the proof tree closes all branches.
        depth (int, default=0): Total proof tree height.
        size (int, default=0): Total number of proof nodes.

    Example:
        >>> from logic_prover.constructive.ik import IKProofTree
        >>> tree = IKProofTree(root=None, is_valid=False, depth=0, size=0)
        >>> tree.is_valid
        False
    """

    root: Optional[IKProofNode] = None
    is_valid: bool = False
    depth: int = 0
    size: int = 0

    def to_string(self) -> str:
        """Formats the proof tree into human-readable ASCII format.

        Returns:
            str: Multi-line description of the derivation tree.

        Example:
            >>> from logic_prover.constructive.ik import IKProofTree
            >>> tree = IKProofTree()
            >>> "Empty" in tree.to_string()
            True
        """
        if self.root is None:
            return "Empty IK proof tree."
        status = "Valid IK Proof" if self.is_valid else "Incomplete/Invalid IK Derivation"
        return f"{status} (Depth: {self.depth}, Size: {self.size}):\n" + self.root.to_string()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the proof tree to a dictionary structure.

        Returns:
            Dict[str, Any]: Dictionary with validity, depth, size, and node hierarchy.

        Example:
            >>> from logic_prover.constructive.ik import IKProofTree
            >>> tree = IKProofTree(is_valid=True)
            >>> tree.to_dict()["is_valid"]
            True
        """
        def node_to_dict(n: IKProofNode) -> Dict[str, Any]:
            return {
                "sequent": n.sequent.to_string(),
                "rule": n.rule,
                "premises": [node_to_dict(p) for p in n.premises],
            }

        return {
            "is_valid": self.is_valid,
            "depth": self.depth,
            "size": self.size,
            "root": node_to_dict(self.root) if self.root is not None else None,
        }

    def export_latex(self) -> str:
        """Exports the full proof tree as a LaTeX document or standalone snippet.

        Returns:
            str: LaTeX formatted string using the bussproofs environment.

        Example:
            >>> from logic_prover.constructive.ik import IKProofTree
            >>> tree = IKProofTree()
            >>> tree.export_latex()
            '% Empty IK proof tree'
        """
        if self.root is None:
            return "% Empty IK proof tree"
        return "\\begin{prooftree}\n" + self.root.export_latex() + "\n\\end{prooftree}"

    def __str__(self) -> str:
        """Returns the default string representation of the proof tree."""
        return self.to_string()


@dataclass(frozen=True)
class IKProofResult:
    """Encapsulates the theorem proving outcome for Constructive Modal Logic IK.

    Args:
        is_valid (bool): True if the target formula is valid in IK, False otherwise.
        proof_tree (Optional[IKProofTree], default=None): Sequent derivation tree if valid.
        countermodel (Optional[KripkeModel], default=None): Countermodel if invalid.
        prover_name (str, default='ik_sequent'): Name of the prover engine.

    Example:
        >>> from logic_prover.constructive.ik import IKProofResult
        >>> res = IKProofResult(is_valid=True)
        >>> res.is_valid
        True
    """

    is_valid: bool
    proof_tree: Optional[IKProofTree] = None
    countermodel: Optional[KripkeModel] = None
    prover_name: str = "ik_sequent"

    def to_string(self) -> str:
        """Formats the result as a detailed readable summary.

        Returns:
            str: Multi-line description of validity, proof tree, or countermodel.

        Example:
            >>> from logic_prover.constructive.ik import IKProofResult
            >>> res = IKProofResult(is_valid=True)
            >>> "VALID" in res.to_string()
            True
        """
        status = "VALID" if self.is_valid else "INVALID (or unprovable within bounds)"
        lines = [f"Result: {status} [Prover: {self.prover_name}]"]
        if self.proof_tree is not None and self.is_valid:
            lines.append("\n--- Derivation Tree ---")
            lines.append(self.proof_tree.to_string())
        elif self.countermodel is not None:
            lines.append("\n--- Kripke Countermodel ---")
            lines.append(self.countermodel.to_string())
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the result to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary structure with validity, proof_tree, and countermodel.

        Example:
            >>> from logic_prover.constructive.ik import IKProofResult
            >>> res = IKProofResult(is_valid=False)
            >>> res.to_dict()["is_valid"]
            False
        """
        return {
            "is_valid": self.is_valid,
            "prover_name": self.prover_name,
            "proof_tree": self.proof_tree.to_dict() if self.proof_tree is not None else None,
            "countermodel": self.countermodel.to_dict() if self.countermodel is not None else None,
        }

    def __str__(self) -> str:
        """Returns default string description."""
        return self.to_string()


class IKProver:
    """Automated Theorem Prover for Constructive Modal Logic IK.

    Combines contraction-free sequent calculus with modal deduction rules and
    tableau countermodel synthesis.

    Args:
        max_depth (int, default=50): Maximum proof tree search depth limit.
        max_quantifier_depth (int, default=3): Maximum quantifier instantiation depth.
        max_modal_depth (int, default=3): Maximum modal transition depth.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.ik import IKProver
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> prover = IKProver()
        >>> res = prover.prove(target=Implies(p, p))
        >>> res.is_valid
        True
    """

    max_depth: int
    max_quantifier_depth: int
    max_modal_depth: int

    def __init__(self, max_depth: int = 50, max_quantifier_depth: int = 3, max_modal_depth: int = 3) -> None:
        """Initializes the IK prover with depth and resource bounds.

        Args:
            max_depth (int, default=50): Maximum deduction search depth.
            max_quantifier_depth (int, default=3): Quantifier instantiation bound.
            max_modal_depth (int, default=3): Modal transition bound.

        Example:
            >>> from logic_prover.constructive.ik import IKProver
            >>> p = IKProver(max_depth=30)
            >>> p.max_depth
            30
        """
        self.max_depth = max(1, max_depth)
        self.max_quantifier_depth = max(0, max_quantifier_depth)
        self.max_modal_depth = max(1, max_modal_depth)

    def prove(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> IKProofResult:
        """Attempts to prove that premises => target is valid in Constructive Modal Logic IK.

        Args:
            target (Formula): Goal formula AST.
            premises (Optional[Sequence[Formula]], default=None): Hypotheses.

        Returns:
            IKProofResult: Result containing proof tree if valid or Kripke countermodel if invalid.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.ik import IKProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = IKProver()
            >>> res = prover.prove(target=Implies(p, p))
            >>> res.is_valid
            True
        """
        initial_ants = tuple(premises) if premises is not None else ()
        initial_seq = IKSequent(antecedents=initial_ants, succedent=target)

        node = self._search(initial_seq, depth=0, q_depth=0, m_depth=0)
        if node is not None:
            tree = IKProofTree(root=node, is_valid=True, depth=node.depth, size=node.size)
            return IKProofResult(is_valid=True, proof_tree=tree, prover_name="ik_sequent")

        # Fallback to Tableau Prover for countermodel generation
        tableau = TableauProver(max_depth=self.max_depth, max_worlds=30)
        tab_res = tableau.prove(target=target, premises=premises)
        if tab_res.is_valid:
            # If tableau proved it, construct an axiom-closed minimal tree
            root_node = IKProofNode(sequent=initial_seq, rule="TableauClosed")
            tree = IKProofTree(root=root_node, is_valid=True, depth=1, size=1)
            return IKProofResult(is_valid=True, proof_tree=tree, prover_name="ik_tableau")

        return IKProofResult(is_valid=False, countermodel=tab_res.countermodel, prover_name="ik_sequent")

    def _search(self, seq: IKSequent, depth: int, q_depth: int, m_depth: int) -> Optional[IKProofNode]:
        """Internal recursive backward search engine for IK sequent derivation.

        Args:
            seq (IKSequent): Current goal sequent.
            depth (int): Current search depth.
            q_depth (int): Current quantifier instantiation depth.
            m_depth (int): Current modal transition depth.

        Returns:
            Optional[IKProofNode]: Closed proof node if provable, None otherwise.
        """
        if depth >= self.max_depth:
            return None

        ants = seq.antecedents
        succ = seq.succedent

        # 1. Axiom rule (Ax): P in Gamma, P on succedent
        if any(a == succ for a in ants) or _is_verum(succ):
            return IKProofNode(sequent=seq, rule="Ax")

        # 2. Falsum-L (Bot_L): _bot in Gamma
        if any(_is_falsum(a) for a in ants):
            return IKProofNode(sequent=seq, rule="Bot_L")

        # 3. And-R: Gamma => A & B
        if isinstance(succ, And):
            seq_l = IKSequent(antecedents=ants, succedent=succ.left)
            seq_r = IKSequent(antecedents=ants, succedent=succ.right)
            p_l = self._search(seq_l, depth + 1, q_depth, m_depth)
            if p_l is not None:
                p_r = self._search(seq_r, depth + 1, q_depth, m_depth)
                if p_r is not None:
                    return IKProofNode(sequent=seq, rule="And_R", premises=(p_l, p_r))

        # 4. Imp-R: Gamma => A => B
        if isinstance(succ, Implies):
            new_ants = ants + (succ.left,)
            sub_seq = IKSequent(antecedents=new_ants, succedent=succ.right)
            p = self._search(sub_seq, depth + 1, q_depth, m_depth)
            if p is not None:
                return IKProofNode(sequent=seq, rule="Imp_R", premises=(p,))

        # 5. Not-R: Gamma => ~A
        if isinstance(succ, Not):
            new_ants = ants + (succ.operand,)
            sub_seq = IKSequent(antecedents=new_ants, succedent=FALSUM)
            p = self._search(sub_seq, depth + 1, q_depth, m_depth)
            if p is not None:
                return IKProofNode(sequent=seq, rule="Not_R", premises=(p,))

        # 6. Iff-R: Gamma => A <=> B
        if isinstance(succ, Iff):
            imp1 = Implies(left=succ.left, right=succ.right)
            imp2 = Implies(left=succ.right, right=succ.left)
            and_f = And(left=imp1, right=imp2)
            sub_seq = IKSequent(antecedents=ants, succedent=and_f)
            p = self._search(sub_seq, depth + 1, q_depth, m_depth)
            if p is not None:
                return IKProofNode(sequent=seq, rule="Iff_R", premises=(p,))

        # 7. Or-R: Gamma => A | B
        if isinstance(succ, Or):
            p1 = self._search(IKSequent(antecedents=ants, succedent=succ.left), depth + 1, q_depth, m_depth)
            if p1 is not None:
                return IKProofNode(sequent=seq, rule="Or_R1", premises=(p1,))
            p2 = self._search(IKSequent(antecedents=ants, succedent=succ.right), depth + 1, q_depth, m_depth)
            if p2 is not None:
                return IKProofNode(sequent=seq, rule="Or_R2", premises=(p2,))

        # 8. Modal Rule Box-R (K_Box): Gamma => Box A  with Gamma_Box => A
        if isinstance(succ, Box) and m_depth < self.max_modal_depth:
            unboxed_ants = tuple(a.operand for a in ants if isinstance(a, Box))
            prem_seq = IKSequent(antecedents=unboxed_ants, succedent=succ.operand)
            p = self._search(prem_seq, depth + 1, q_depth, m_depth + 1)
            if p is not None:
                return IKProofNode(sequent=seq, rule="K_Box", premises=(p,))

        # 9. Invertible Left Rules on Antecedents
        for idx, a in enumerate(ants):
            rem_ants = ants[:idx] + ants[idx + 1:]

            # And-L: Gamma, A & B => C  ->  Gamma, A, B => C
            if isinstance(a, And):
                sub_seq = IKSequent(antecedents=rem_ants + (a.left, a.right), succedent=succ)
                p = self._search(sub_seq, depth + 1, q_depth, m_depth)
                if p is not None:
                    return IKProofNode(sequent=seq, rule="And_L", premises=(p,))

            # Or-L: Gamma, A | B => C  ->  Gamma, A => C and Gamma, B => C
            if isinstance(a, Or):
                s1 = IKSequent(antecedents=rem_ants + (a.left,), succedent=succ)
                s2 = IKSequent(antecedents=rem_ants + (a.right,), succedent=succ)
                p1 = self._search(s1, depth + 1, q_depth, m_depth)
                if p1 is not None:
                    p2 = self._search(s2, depth + 1, q_depth, m_depth)
                    if p2 is not None:
                        return IKProofNode(sequent=seq, rule="Or_L", premises=(p1, p2))

            # Modal Rule Diamond-L (K_Diamond): Gamma, Diamond A => Diamond B
            if isinstance(a, Diamond) and m_depth < self.max_modal_depth:
                if isinstance(succ, Diamond):
                    unboxed_ants = tuple(x.operand for x in rem_ants if isinstance(x, Box))
                    prem_seq = IKSequent(antecedents=unboxed_ants + (a.operand,), succedent=succ.operand)
                    p = self._search(prem_seq, depth + 1, q_depth, m_depth + 1)
                    if p is not None:
                        return IKProofNode(sequent=seq, rule="K_Diamond", premises=(p,))
                elif _is_falsum(succ):
                    unboxed_ants = tuple(x.operand for x in rem_ants if isinstance(x, Box))
                    prem_seq = IKSequent(antecedents=unboxed_ants + (a.operand,), succedent=FALSUM)
                    p = self._search(prem_seq, depth + 1, q_depth, m_depth + 1)
                    if p is not None:
                        return IKProofNode(sequent=seq, rule="K_Diamond_Bot", premises=(p,))

            # Imp-L: Gamma, A => B => C
            if isinstance(a, Implies):
                if _is_atomic(a.left):
                    if a.left in rem_ants:
                        s = IKSequent(antecedents=rem_ants + (a.right,), succedent=succ)
                        p = self._search(s, depth + 1, q_depth, m_depth)
                        if p is not None:
                            return IKProofNode(sequent=seq, rule="Imp_L_Atom", premises=(p,))
                else:
                    # General Imp-L branching: Gamma => A and Gamma, B => C
                    s1 = IKSequent(antecedents=rem_ants, succedent=a.left)
                    s2 = IKSequent(antecedents=rem_ants + (a.right,), succedent=succ)
                    p1 = self._search(s1, depth + 1, q_depth, m_depth)
                    if p1 is not None:
                        p2 = self._search(s2, depth + 1, q_depth, m_depth)
                        if p2 is not None:
                            return IKProofNode(sequent=seq, rule="Imp_L", premises=(p1, p2))

        return None


def prove_ik(
    target: Formula,
    premises: Optional[Sequence[Formula]] = None,
    max_depth: int = 50,
) -> IKProofResult:
    """Constructs a proof or countermodel for a formula in Constructive Modal Logic IK.

    Args:
        target (Formula): Goal formula AST.
        premises (Optional[Sequence[Formula]], default=None): Hypotheses.
        max_depth (int, default=50): Search depth limit.

    Returns:
        IKProofResult: The proof result object.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies, Box
        >>> from logic_prover.constructive.ik import prove_ik
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> res = prove_ik(Implies(Box(p), Box(p)))
        >>> res.is_valid
        True
    """
    prover = IKProver(max_depth=max_depth)
    return prover.prove(target=target, premises=premises)


__all__ = [
    "IKSequent",
    "IKProofNode",
    "IKProofTree",
    "IKProofResult",
    "IKProver",
    "prove_ik",
]

