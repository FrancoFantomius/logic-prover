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
    Box,
    Diamond,
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
    elif isinstance(formula, (Not, Box, Diamond)):
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


def translate_ik_to_fol(
    formula: Formula,
    world_term: Optional[Term] = None,
    var_counter: Optional[List[int]] = None,
) -> Formula:
    """Translates a Constructive Modal Logic IK formula into a First-Order Logic formula.

    Implements the standard relational bi-frame translation for IK:
    - tau_ik(P, w) = P(w)
    - tau_ik(_bot, w) = _bot
    - tau_ik(_top, w) = _top
    - tau_ik(~A, w) = forall w'. (Leq(w, w') => ~tau_ik(A, w'))
    - tau_ik(A & B, w) = tau_ik(A, w) & tau_ik(B, w)
    - tau_ik(A | B, w) = tau_ik(A, w) | tau_ik(B, w)
    - tau_ik(A => B, w) = forall w'. ((Leq(w, w') & tau_ik(A, w')) => tau_ik(B, w'))
    - tau_ik(Box(A), w) = forall w'. forall v. ((Leq(w, w') & R_mod(w', v)) => tau_ik(A, v))
    - tau_ik(Diamond(A), w) = exists v. (R_mod(w, v) & tau_ik(A, v))

    Args:
        formula (Formula): The IK formula AST to translate.
        world_term (Optional[Term], default=None): World parameter term (defaults to Constant('w0')).
        var_counter (Optional[List[int]], default=None): Mutable integer counter for unique world variables.

    Returns:
        Formula: The translated First-Order Logic formula AST.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Box
        >>> from logic_prover.constructive.resolution.translation import translate_ik_to_fol
        >>> p = PredicateApp("P", 0, ())
        >>> fol_f = translate_ik_to_fol(Box(p))
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
        leq_rel = PredicateApp(pred="Leq", arity=2, args=(world_term, w_var))
        tau_op = translate_ik_to_fol(formula.operand, world_term=w_var, var_counter=var_counter)
        return Forall(variable=w_var, body=Implies(left=leq_rel, right=Not(operand=tau_op)))

    if isinstance(formula, And):
        return And(
            left=translate_ik_to_fol(formula.left, world_term=world_term, var_counter=var_counter),
            right=translate_ik_to_fol(formula.right, world_term=world_term, var_counter=var_counter),
        )

    if isinstance(formula, Or):
        return Or(
            left=translate_ik_to_fol(formula.left, world_term=world_term, var_counter=var_counter),
            right=translate_ik_to_fol(formula.right, world_term=world_term, var_counter=var_counter),
        )

    if isinstance(formula, Implies):
        w_var = Variable(id=var_counter[0], sort=Ind)
        var_counter[0] += 1
        leq_rel = PredicateApp(pred="Leq", arity=2, args=(world_term, w_var))
        tau_l = translate_ik_to_fol(formula.left, world_term=w_var, var_counter=var_counter)
        tau_r = translate_ik_to_fol(formula.right, world_term=w_var, var_counter=var_counter)
        return Forall(
            variable=w_var,
            body=Implies(
                left=And(left=leq_rel, right=tau_l),
                right=tau_r,
            ),
        )

    if isinstance(formula, Iff):
        left_imp = Implies(left=formula.left, right=formula.right)
        right_imp = Implies(left=formula.right, right=formula.left)
        return translate_ik_to_fol(And(left=left_imp, right=right_imp), world_term=world_term, var_counter=var_counter)

    if isinstance(formula, Box):
        w_var = Variable(id=var_counter[0], sort=Ind)
        v_var = Variable(id=var_counter[0] + 1, sort=Ind)
        var_counter[0] += 2
        leq_rel = PredicateApp(pred="Leq", arity=2, args=(world_term, w_var))
        rmod_rel = PredicateApp(pred="R_mod", arity=2, args=(w_var, v_var))
        tau_op = translate_ik_to_fol(formula.operand, world_term=v_var, var_counter=var_counter)
        return Forall(
            variable=w_var,
            body=Forall(
                variable=v_var,
                body=Implies(
                    left=And(left=leq_rel, right=rmod_rel),
                    right=tau_op,
                ),
            ),
        )

    if isinstance(formula, Diamond):
        v_var = Variable(id=var_counter[0], sort=Ind)
        var_counter[0] += 1
        rmod_rel = PredicateApp(pred="R_mod", arity=2, args=(world_term, v_var))
        tau_op = translate_ik_to_fol(formula.operand, world_term=v_var, var_counter=var_counter)
        return Exists(
            variable=v_var,
            body=And(left=rmod_rel, right=tau_op),
        )

    if isinstance(formula, Forall):
        w_var = Variable(id=var_counter[0], sort=Ind)
        var_counter[0] += 1
        leq_rel = PredicateApp(pred="Leq", arity=2, args=(world_term, w_var))
        tau_body = translate_ik_to_fol(formula.body, world_term=w_var, var_counter=var_counter)
        return Forall(
            variable=w_var,
            body=Implies(
                left=leq_rel,
                right=Forall(variable=formula.variable, body=tau_body),
            ),
        )

    if isinstance(formula, Exists):
        return Exists(
            variable=formula.variable,
            body=translate_ik_to_fol(formula.body, world_term=world_term, var_counter=var_counter),
        )

    return formula


def get_ik_frame_axioms(
    pred_declarations: Sequence[Union[str, Tuple[str, int]]]
) -> List[Formula]:
    """Generates the first-order frame axioms for Constructive Modal Logic IK.

    Axioms:
    1. Reflexivity of Leq: forall w. Leq(w, w)
    2. Transitivity of Leq: forall u, v, w. ((Leq(u, v) & Leq(v, w)) => Leq(u, w))
    3. Monotonicity/Heredity: forall u, v, x... ((Leq(u, v) & P(u, x...)) => P(v, x...))
    4. IK Commutation: forall w, w_prime, v. ((Leq(w, w_prime) & R_mod(w, v)) => exists v_prime. (R_mod(w_prime, v_prime) & Leq(v, v_prime)))

    Args:
        pred_declarations (Sequence[Union[str, Tuple[str, int]]]): Predicate names or (name, arity) declarations.

    Returns:
        List[Formula]: The generated FOL frame axioms.

    Example:
        >>> from logic_prover.constructive.resolution.translation import get_ik_frame_axioms
        >>> axioms = get_ik_frame_axioms([("P", 0)])
        >>> len(axioms) >= 4
        True
    """
    axioms: List[Formula] = []

    w = Variable(id=1, sort=Ind)
    u = Variable(id=2, sort=Ind)
    v = Variable(id=3, sort=Ind)
    w_p = Variable(id=4, sort=Ind)
    v_p = Variable(id=5, sort=Ind)

    # 1. Reflexivity of Leq: forall w. Leq(w, w)
    axioms.append(
        Forall(
            variable=w,
            body=PredicateApp(pred="Leq", arity=2, args=(w, w)),
        )
    )

    # 2. Transitivity of Leq: forall u, v, w. ((Leq(u, v) & Leq(v, w)) => Leq(u, w))
    axioms.append(
        Forall(
            variable=u,
            body=Forall(
                variable=v,
                body=Forall(
                    variable=w,
                    body=Implies(
                        left=And(
                            left=PredicateApp(pred="Leq", arity=2, args=(u, v)),
                            right=PredicateApp(pred="Leq", arity=2, args=(v, w)),
                        ),
                        right=PredicateApp(pred="Leq", arity=2, args=(u, w)),
                    ),
                ),
            ),
        )
    )

    # 3. Monotonicity / Heredity for each predicate symbol
    parsed_preds: List[Tuple[str, int]] = []
    for item in pred_declarations:
        if isinstance(item, tuple):
            parsed_preds.append(item)
        else:
            parsed_preds.append((item, 0))

    leq_uv = PredicateApp(pred="Leq", arity=2, args=(u, v))
    for pred, arity in sorted(set(parsed_preds)):
        if pred in ("Leq", "R_mod", "_bot", "_top"):
            continue
        ind_vars = [Variable(id=10 + i, sort=Ind) for i in range(arity)]
        p_u = PredicateApp(pred=pred, arity=arity + 1, args=(u,) + tuple(ind_vars))
        p_v = PredicateApp(pred=pred, arity=arity + 1, args=(v,) + tuple(ind_vars))
        mono_body: Formula = Implies(left=And(left=p_u, right=leq_uv), right=p_v)
        for var in reversed(ind_vars):
            mono_body = Forall(variable=var, body=mono_body)
        mono = Forall(
            variable=u,
            body=Forall(
                variable=v,
                body=mono_body,
            ),
        )
        axioms.append(mono)

    # 4. Commutation: forall w, w_p, v. ((Leq(w, w_p) & R_mod(w, v)) => exists v_p. (R_mod(w_p, v_p) & Leq(v, v_p)))
    comm_premise = And(
        left=PredicateApp(pred="Leq", arity=2, args=(w, w_p)),
        right=PredicateApp(pred="R_mod", arity=2, args=(w, v)),
    )
    comm_conclusion = Exists(
        variable=v_p,
        body=And(
            left=PredicateApp(pred="R_mod", arity=2, args=(w_p, v_p)),
            right=PredicateApp(pred="Leq", arity=2, args=(v, v_p)),
        ),
    )
    comm_axiom = Forall(
        variable=w,
        body=Forall(
            variable=w_p,
            body=Forall(
                variable=v,
                body=Implies(left=comm_premise, right=comm_conclusion),
            ),
        ),
    )
    axioms.append(comm_axiom)

    return axioms


class IKTranslationResolutionProver:
    """Theorem Prover for Constructive Modal Logic IK via Relational Translation into First-Order Logic Resolution.

    Args:
        max_steps (int, default=1000): Maximum given-clause loop iterations in the FOL prover.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies, Box
        >>> from logic_prover.constructive.resolution.translation import IKTranslationResolutionProver
        >>> p = PredicateApp("P", 0, ())
        >>> prover = IKTranslationResolutionProver()
        >>> res = prover.prove(Implies(Box(p), Box(p)))
        >>> res is not None and res.is_valid
        True
    """

    max_steps: int
    timeout_sec: float

    def __init__(self, max_steps: int = 1000, timeout_sec: float = 10.0) -> None:
        """Initializes the IKTranslationResolutionProver with search bounds.

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
        """Attempts to prove an IK formula by translating to FOL and running the First-Order resolution prover.

        Args:
            target (Formula): The IK formula AST to prove.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis premises.

        Returns:
            Optional[TranslationResolutionResult]: Proof result if proven valid, None if unprovable.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies, Box
            >>> from logic_prover.constructive.resolution.translation import IKTranslationResolutionProver
            >>> p = PredicateApp("P", 0, ())
            >>> prover = IKTranslationResolutionProver()
            >>> res = prover.prove(Implies(Box(p), Box(p)))
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
        sig.register_predicate("Leq", 2, (Ind, Ind))
        sig.register_predicate("R_mod", 2, (Ind, Ind))
        for pred, arity in sorted(preds):
            sig.register_predicate(pred, arity + 1, (Ind,) * (arity + 1))
        sig.register_constant("w0", Ind)
        for c in consts:
            if c.name != "w0":
                sig.register_constant(c.name, Ind)
        for f_name, f_arity in fns:
            sig.register_function(f_name, f_arity, (Ind,) * f_arity, Ind)

        w0 = Constant("w0", sort=Ind)
        target_fol = translate_ik_to_fol(norm_target, world_term=w0)
        premises_fol_list = [translate_ik_to_fol(p, world_term=w0) for p in norm_premises]

        frame_axioms = get_ik_frame_axioms(sorted(preds))
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


def prove_ik_translation_resolution(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_steps: int = 1000,
    timeout_sec: float = 10.0,
) -> Optional[TranslationResolutionResult]:
    """Proves a Constructive Modal Logic IK formula using Relational Translation Resolution.

    Args:
        formula (Formula): Goal formula to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis premises.
        max_steps (int, default=1000): Maximum resolution steps in the FOL prover.
        timeout_sec (float, default=10.0): Wall-clock timeout in seconds.

    Returns:
        Optional[TranslationResolutionResult]: Proof result if valid, None if unprovable.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies, Box
        >>> from logic_prover.constructive.resolution.translation import prove_ik_translation_resolution
        >>> p = PredicateApp("P", 0, ())
        >>> proof = prove_ik_translation_resolution(Implies(Box(p), Box(p)))
        >>> proof is not None and proof.is_valid
        True
    """
    prover = IKTranslationResolutionProver(
        max_steps=max_steps,
        timeout_sec=timeout_sec,
    )
    return prover.prove(target=formula, premises=premises)


__all__ = [
    "translate_ipc_to_fol",
    "translate_ik_to_fol",
    "get_frame_axioms",
    "get_ik_frame_axioms",
    "_extract_predicate_declarations",
    "_extract_predicate_names",
    "TranslationResolutionResult",
    "TranslationResolutionProver",
    "IKTranslationResolutionProver",
    "prove_translation_resolution",
    "prove_ik_translation_resolution",
]
