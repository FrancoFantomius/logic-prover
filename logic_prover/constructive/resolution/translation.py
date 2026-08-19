"""Relational S4 translation embedding Intuitionistic Propositional Logic into classical First-Order Logic."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Set, Sequence, Union

from logic_prover.core.ast import (
    Formula,
    Term,
    Variable,
    Constant,
    PredicateApp,
    Equality,
    Not,
    And,
    Or,
    Implies,
    Iff,
    Forall,
    Exists,
)
from logic_prover.core.parser import to_string
from logic_prover.core.sorts import Ind
from logic_prover.core.signature import Signature
from logic_prover.config import SolverConfig
from logic_prover.constructive.common import (
    FALSUM,
    VERUM,
    _is_falsum,
    _is_verum,
    _is_atomic,
    normalize_formula,
)
from logic_prover.constructive.ljt import _collect_constants_and_functions
from logic_prover.prover.engine import TheoremProver
from logic_prover.prover.proof import ProofDAG


def translate_ipc_to_fol(
    formula: Formula,
    world_term: Optional[Term] = None,
    var_counter: Optional[List[int]] = None,
) -> Formula:
    """Translates an Intuitionistic Propositional Logic formula into a First-Order Logic formula.

    Implements the standard relational translation (embedding IPC into modal S4 and FOL):
    - tau(P, w) = P(w)
    - tau(_bot, w) = _bot
    - tau(_top, w) = _top
    - tau(~A, w) = forall w'. (R(w, w') => ~tau(A, w'))
    - tau(A & B, w) = tau(A, w) & tau(B, w)
    - tau(A | B, w) = tau(A, w) | tau(B, w)
    - tau(A => B, w) = forall w'. ((R(w, w') & tau(A, w')) => tau(B, w'))

    Args:
        formula (Formula): The IPC formula AST to translate.
        world_term (Optional[Term], default=None): World parameter term (defaults to Constant('w0')).
        var_counter (Optional[List[int]], default=None): Mutable integer counter for unique world variables.

    Returns:
        Formula: The translated First-Order Logic formula AST.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.translation import translate_ipc_to_fol
        >>> p = PredicateApp("P", 0, ())
        >>> fol_f = translate_ipc_to_fol(Implies(p, p))
        >>> type(fol_f).__name__
        'Forall'
    """
    if world_term is None:
        world_term = Constant(name="w0", sort=Ind)
    if var_counter is None:
        var_counter = [1]

    if _is_falsum(formula):
        return FALSUM
    if _is_verum(formula):
        return VERUM

    if _is_atomic(formula):
        if isinstance(formula, PredicateApp):
            return PredicateApp(pred=formula.pred, arity=formula.arity + 1, args=(world_term,) + formula.args)
        elif isinstance(formula, Equality):
            return formula
        return formula

    if isinstance(formula, Not):
        w_var = Variable(id=var_counter[0], sort=Ind)
        var_counter[0] += 1
        r_rel = PredicateApp(pred="R", arity=2, args=(world_term, w_var))
        tau_op = translate_ipc_to_fol(formula.operand, world_term=w_var, var_counter=var_counter)
        return Forall(variable=w_var, body=Implies(left=r_rel, right=Not(operand=tau_op)))

    if isinstance(formula, And):
        return And(
            left=translate_ipc_to_fol(formula.left, world_term=world_term, var_counter=var_counter),
            right=translate_ipc_to_fol(formula.right, world_term=world_term, var_counter=var_counter),
        )

    if isinstance(formula, Or):
        return Or(
            left=translate_ipc_to_fol(formula.left, world_term=world_term, var_counter=var_counter),
            right=translate_ipc_to_fol(formula.right, world_term=world_term, var_counter=var_counter),
        )

    if isinstance(formula, Implies):
        w_var = Variable(id=var_counter[0], sort=Ind)
        var_counter[0] += 1
        r_rel = PredicateApp(pred="R", arity=2, args=(world_term, w_var))
        tau_left = translate_ipc_to_fol(formula.left, world_term=w_var, var_counter=var_counter)
        tau_right = translate_ipc_to_fol(formula.right, world_term=w_var, var_counter=var_counter)
        antecedent = And(left=r_rel, right=tau_left)
        return Forall(variable=w_var, body=Implies(left=antecedent, right=tau_right))

    if isinstance(formula, Iff):
        norm = normalize_formula(formula)
        return translate_ipc_to_fol(norm, world_term=world_term, var_counter=var_counter)

    if isinstance(formula, Forall):
        w_var = Variable(id=var_counter[0], sort=Ind)
        var_counter[0] += 1
        r_rel = PredicateApp(pred="R", arity=2, args=(world_term, w_var))
        tau_body = translate_ipc_to_fol(formula.body, world_term=w_var, var_counter=var_counter)
        return Forall(
            variable=w_var,
            body=Implies(
                left=r_rel,
                right=Forall(variable=formula.variable, body=tau_body),
            ),
        )

    if isinstance(formula, Exists):
        tau_body = translate_ipc_to_fol(formula.body, world_term=world_term, var_counter=var_counter)
        return Exists(variable=formula.variable, body=tau_body)

    return formula


def get_frame_axioms(atomic_predicates: Sequence[Union[str, Tuple[str, int]]]) -> List[Formula]:
    """Generates the Kripke frame reflexivity, transitivity, and monotonicity axioms in FOL.

    Args:
        atomic_predicates (Sequence[Union[str, Tuple[str, int]]]): List of proposition names or (name, arity) tuples.

    Returns:
        List[Formula]: Frame and monotonicity axioms in FOL.

    Example:
        >>> from logic_prover.constructive.resolution.translation import get_frame_axioms
        >>> axioms = get_frame_axioms(["P"])
        >>> len(axioms)
        3
    """
    x = Variable(id=1, sort=Ind)
    y = Variable(id=2, sort=Ind)
    z = Variable(id=3, sort=Ind)

    # 1. Reflexivity: forall x. R(x, x)
    refl = Forall(variable=x, body=PredicateApp(pred="R", arity=2, args=(x, x)))

    # 2. Transitivity: forall x y z. ((R(x, y) & R(y, z)) => R(x, z))
    r_xy = PredicateApp(pred="R", arity=2, args=(x, y))
    r_yz = PredicateApp(pred="R", arity=2, args=(y, z))
    r_xz = PredicateApp(pred="R", arity=2, args=(x, z))
    trans = Forall(
        variable=x,
        body=Forall(
            variable=y,
            body=Forall(
                variable=z,
                body=Implies(left=And(left=r_xy, right=r_yz), right=r_xz),
            ),
        ),
    )

    axioms: List[Formula] = [refl, trans]

    # 3. Monotonicity for atomic predicates:
    parsed_preds: List[Tuple[str, int]] = []
    for item in atomic_predicates:
        if isinstance(item, str):
            if item not in ("R", "_bot", "_top"):
                parsed_preds.append((item, 0))
        elif isinstance(item, tuple) and len(item) == 2:
            if item[0] not in ("R", "_bot", "_top"):
                parsed_preds.append(item)

    for pred, arity in sorted(set(parsed_preds)):
        ind_vars = [Variable(id=10 + i, sort=Ind) for i in range(arity)]
        p_x = PredicateApp(pred=pred, arity=arity + 1, args=(x,) + tuple(ind_vars))
        p_y = PredicateApp(pred=pred, arity=arity + 1, args=(y,) + tuple(ind_vars))
        mono_body: Formula = Implies(left=And(left=p_x, right=r_xy), right=p_y)
        for var in reversed(ind_vars):
            mono_body = Forall(variable=var, body=mono_body)
        mono = Forall(
            variable=x,
            body=Forall(
                variable=y,
                body=mono_body,
            ),
        )
        axioms.append(mono)

    return axioms


def _extract_predicate_declarations(formula: Formula) -> Set[Tuple[str, int]]:
    """Recursively collects all predicate symbols and their IPC arities in a formula AST.

    Args:
        formula (Formula): Formula to inspect.

    Returns:
        Set[Tuple[str, int]]: Set of (predicate_name, arity) tuples.

    Example:
        >>> from logic_prover.core.ast import PredicateApp
        >>> from logic_prover.constructive.resolution.translation import _extract_predicate_declarations
        >>> p = PredicateApp("P", 0, ())
        >>> _extract_predicate_declarations(p)
        {('P', 0)}
    """
    preds: Set[Tuple[str, int]] = set()
    if isinstance(formula, PredicateApp):
        if formula.pred not in ("_bot", "_top", "R"):
            preds.add((formula.pred, formula.arity))
    elif isinstance(formula, Not):
        preds.update(_extract_predicate_declarations(formula.operand))
    elif isinstance(formula, (And, Or, Implies, Iff)):
        preds.update(_extract_predicate_declarations(formula.left))
        preds.update(_extract_predicate_declarations(formula.right))
    elif isinstance(formula, (Forall, Exists)):
        preds.update(_extract_predicate_declarations(formula.body))
    return preds


def _extract_predicate_names(formula: Formula) -> Set[str]:
    """Recursively collects all atomic proposition names in a formula AST.

    Args:
        formula (Formula): Formula to inspect.

    Returns:
        Set[str]: Set of predicate names.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.translation import _extract_predicate_names
        >>> p = PredicateApp("P", 0, ())
        >>> q = PredicateApp("Q", 0, ())
        >>> _extract_predicate_names(Implies(p, q)) == {"P", "Q"}
        True
    """
    return {name for name, _ in _extract_predicate_declarations(formula)}


@dataclass
class TranslationResolutionResult:
    """Container for the derivation results of Translation-based Resolution.

    Args:
        is_valid (bool): Whether the formula was proven valid in IPC.
        target_ipc (Formula): Original IPC goal formula.
        premises_ipc (Tuple[Formula, ...]): Original IPC hypothesis premises.
        target_fol (Formula): Translated First-Order Logic goal formula.
        premises_fol (Tuple[Formula, ...]): Translated premises including frame axioms.
        frame_axioms (Tuple[Formula, ...]): Generated reflexivity, transitivity, and monotonicity axioms.
        proof_dag (Optional[ProofDAG]): Reconstructed natural deduction / resolution proof DAG.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.translation import TranslationResolutionResult
        >>> p = PredicateApp("P", 0, ())
        >>> res = TranslationResolutionResult(True, Implies(p, p), (), Implies(p, p), (), (), None)
        >>> res.is_valid
        True
    """

    is_valid: bool
    target_ipc: Formula
    premises_ipc: Tuple[Formula, ...]
    target_fol: Formula
    premises_fol: Tuple[Formula, ...]
    frame_axioms: Tuple[Formula, ...]
    proof_dag: Optional[ProofDAG]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the translation resolution result to a JSON dictionary.

        Returns:
            Dict[str, Any]: Serialized result dictionary.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution.translation import TranslationResolutionResult
            >>> p = PredicateApp("P", 0, ())
            >>> res = TranslationResolutionResult(True, Implies(p, p), (), Implies(p, p), (), (), None)
            >>> res.to_dict()["is_valid"]
            True
        """
        return {
            "is_valid": self.is_valid,
            "target_ipc": to_string(self.target_ipc),
            "premises_ipc": [to_string(p) for p in self.premises_ipc],
            "target_fol": to_string(self.target_fol),
            "premises_fol": [to_string(p) for p in self.premises_fol],
            "frame_axioms": [to_string(a) for a in self.frame_axioms],
            "has_proof_dag": self.proof_dag is not None,
        }

    def to_string(self) -> str:
        """Formats the translation proof result as a multi-line report.

        Returns:
            str: Multi-line description of the translation proof.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution.translation import TranslationResolutionResult
            >>> p = PredicateApp("P", 0, ())
            >>> res = TranslationResolutionResult(True, Implies(p, p), (), Implies(p, p), (), (), None)
            >>> "Translation Resolution Proof" in res.to_string()
            True
        """
        lines: List[str] = []
        lines.append("=== Relational Translation Resolution Proof (IPC -> FOL) ===")
        lines.append(f"Target (IPC): {to_string(self.target_ipc)}")
        if self.premises_ipc:
            lines.append(f"Premises (IPC): {', '.join(to_string(p) for p in self.premises_ipc)}")
        lines.append(f"Target (FOL): {to_string(self.target_fol)}")
        lines.append(f"Status: {'VALID (Proven via FOL Superposition/Resolution)' if self.is_valid else 'UNPROVABLE'}")
        lines.append(f"Frame Axioms Count: {len(self.frame_axioms)}")
        if self.proof_dag is not None:
            lines.append(f"Reconstructed Proof Steps: {len(self.proof_dag.steps)}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Returns the default string representation.

        Returns:
            str: Formatted report string.
        """
        return self.to_string()


class TranslationResolutionProver:
    """Resolution prover utilizing Relational S4 Translation to First-Order Logic.

    Args:
        max_steps (int, default=1000): Maximum given-clause loop iterations in the FOL prover.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.translation import TranslationResolutionProver
        >>> p = PredicateApp("P", 0, ())
        >>> prover = TranslationResolutionProver()
        >>> res = prover.prove(Implies(p, p))
        >>> res is not None and res.is_valid
        True
    """

    max_steps: int
    timeout_sec: float

    def __init__(self, max_steps: int = 1000, timeout_sec: float = 10.0) -> None:
        """Initializes the TranslationResolutionProver with limits.

        Args:
            max_steps (int, default=1000): Maximum search steps.
            timeout_sec (float, default=10.0): Search timeout in seconds.
        """
        self.max_steps = max(1, max_steps)
        self.timeout_sec = max(0.1, timeout_sec)

    def prove(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> Optional[TranslationResolutionResult]:
        """Attempts to prove an IPC formula by translating to FOL and running the First-Order resolution prover.

        Args:
            target (Formula): The IPC formula AST to prove.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis premises.

        Returns:
            Optional[TranslationResolutionResult]: Proof result if proven valid, None if unprovable.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.resolution.translation import TranslationResolutionProver
            >>> p = PredicateApp("P", 0, ())
            >>> prover = TranslationResolutionProver()
            >>> res = prover.prove(Implies(p, p))
            >>> res is not None and res.is_valid
            True
        """
        norm_target = normalize_formula(target)
        norm_premises = tuple(normalize_formula(p) for p in (premises or []))

        # Collect atomic predicate declarations
        preds: Set[Tuple[str, int]] = set()
        preds.update(_extract_predicate_declarations(norm_target))
        for p in norm_premises:
            preds.update(_extract_predicate_declarations(p))

        consts, fns = _collect_constants_and_functions(list(norm_premises) + [norm_target])

        # Build Signature
        sig = Signature()
        sig.register_predicate("R", 2, (Ind, Ind))
        for pred, arity in sorted(preds):
            sig.register_predicate(pred, arity + 1, (Ind,) * (arity + 1))
        sig.register_constant("w0", Ind)
        for c in consts:
            if c.name != "w0":
                sig.register_constant(c.name, Ind)
        for f_name, f_arity in fns:
            sig.register_function(f_name, f_arity, (Ind,) * f_arity, Ind)

        w0 = Constant("w0", sort=Ind)
        target_fol = translate_ipc_to_fol(norm_target, world_term=w0)
        premises_fol_list = [translate_ipc_to_fol(p, world_term=w0) for p in norm_premises]

        frame_axioms = get_frame_axioms(sorted(preds))
        all_fol_premises = frame_axioms + premises_fol_list

        config = SolverConfig(
            prover_max_steps=self.max_steps,
            prover_timeout_sec=self.timeout_sec,
        )
        fol_prover = TheoremProver(signature=sig, config=config)

        try:
            proof_dag = fol_prover.prove(
                target=target_fol,
                premises=all_fol_premises,
                max_steps=self.max_steps,
                timeout_sec=self.timeout_sec,
            )
            return TranslationResolutionResult(
                is_valid=True,
                target_ipc=norm_target,
                premises_ipc=norm_premises,
                target_fol=target_fol,
                premises_fol=tuple(all_fol_premises),
                frame_axioms=tuple(frame_axioms),
                proof_dag=proof_dag,
            )
        except Exception:
            return None


def prove_translation_resolution(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_steps: int = 1000,
    timeout_sec: float = 10.0,
) -> Optional[TranslationResolutionResult]:
    """Proves an intuitionistic propositional formula using Relational S4 Translation Resolution.

    Args:
        formula (Formula): Goal formula to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis premises.
        max_steps (int, default=1000): Maximum resolution steps in the FOL prover.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Returns:
        Optional[TranslationResolutionResult]: Proof result if valid, None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.resolution.translation import prove_translation_resolution
        >>> p = PredicateApp("P", 0, ())
        >>> proof = prove_translation_resolution(Implies(p, p))
        >>> proof is not None and proof.is_valid
        True
    """
    prover = TranslationResolutionProver(
        max_steps=max_steps,
        timeout_sec=timeout_sec,
    )
    return prover.prove(target=formula, premises=premises)


__all__ = [
    "translate_ipc_to_fol",
    "get_frame_axioms",
    "_extract_predicate_declarations",
    "_extract_predicate_names",
    "TranslationResolutionResult",
    "TranslationResolutionProver",
    "prove_translation_resolution",
]
