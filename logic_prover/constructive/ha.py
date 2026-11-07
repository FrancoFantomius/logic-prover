"""Heyting Arithmetic (HA) constructive theorem prover combining LJT, Tableau, and Translation methods."""

from __future__ import annotations
from typing import List, Tuple, Optional, Sequence, Union, Any, Set

from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Nat, Ind
from logic_prover.core.signature import Signature
from logic_prover.config import SolverConfig
from logic_prover.axioms.heyting_arithmetic import (
    get_ha_axioms,
    get_ha_signature,
    instantiate_ha_induction,
    ha_theory,
)
from logic_prover.axioms.equality import get_equality_axioms
from logic_prover.constructive.ljt import LJTProver, LJTProofTree
from logic_prover.constructive.tableau import TableauProver, TableauProofResult
from logic_prover.constructive.resolution.translation import (
    TranslationResolutionProver,
    TranslationResolutionResult,
)


def _extract_induction_candidates(formula: Formula, max_candidates: int = 4) -> List[Tuple[Formula, Variable]]:
    """Extracts candidate subformulas and bound variables for induction schema instantiation.

    Args:
        formula (Formula): Formula to inspect.
        max_candidates (int, default=4): Maximum number of candidates to extract.

    Returns:
        List[Tuple[Formula, Variable]]: List of (property_formula, bound_variable) pairs.

    Example:
        >>> from logic_prover.core.ast import Variable, Equality, Forall
        >>> from logic_prover.core.sorts import Nat
        >>> n = Variable(0, sort=Nat)
        >>> goal = Forall(n, Equality(n, n))
        >>> candidates = _extract_induction_candidates(goal)
        >>> len(candidates) > 0
        True
    """
    candidates: List[Tuple[Formula, Variable]] = []
    seen: Set[str] = set()

    def _traverse(f: Formula) -> None:
        if len(candidates) >= max_candidates:
            return
        if isinstance(f, Forall):
            key = f"{f.variable.id}:{type(f.body).__name__}"
            if key not in seen:
                seen.add(key)
                candidates.append((f.body, f.variable))
            _traverse(f.body)
        elif isinstance(f, Exists):
            _traverse(f.body)
        elif isinstance(f, (Not,)):
            _traverse(f.operand)
        elif isinstance(f, (And, Or, Implies, Iff)):
            _traverse(f.left)
            _traverse(f.right)

    _traverse(formula)
    return candidates


class HAProver:
    """Automated Theorem Prover for Heyting Arithmetic (HA).

    Combines the Peano axioms, first-order induction schema, and constructive proof engines
    (LJT contraction-free sequent calculus, semantic tableaux, and relational translation).

    Args:
        method (str, default='ljt'): Prover backend method ('ljt', 'tableau', 'translation', 'auto').
        max_ind_depth (int, default=3): Maximum nested induction search depth.
        max_induction_instances (int, default=4): Maximum induction schema instantiations for translation.
        max_steps (int, default=1000): Maximum prover search steps / iterations.
        timeout_sec (float, default=10.0): Wall-clock search timeout limit in seconds.

    Example:
        >>> from logic_prover.core.ast import Variable, Equality, Forall, FunctionApp
        >>> from logic_prover.core.sorts import Nat
        >>> from logic_prover.constructive.ha import HAProver
        >>> n = Variable(0, sort=Nat)
        >>> zero = Constant("zero", sort=Nat)
        >>> add_0_n = FunctionApp("add", 2, (zero, n), return_sort=Nat)
        >>> goal = Forall(n, Equality(add_0_n, n))
        >>> prover = HAProver(method="ljt")
        >>> res = prover.prove(goal)
        >>> res is not None and res.is_valid()
        True
    """

    method: str
    max_ind_depth: int
    max_induction_instances: int
    max_steps: int
    timeout_sec: float

    def __init__(
        self,
        method: str = "ljt",
        max_ind_depth: int = 3,
        max_induction_instances: int = 4,
        max_steps: int = 1000,
        timeout_sec: float = 10.0,
    ) -> None:
        """Initializes the Heyting Arithmetic prover instance.

        Args:
            method (str, default='ljt'): Proof engine ('ljt', 'tableau', 'translation', 'auto').
            max_ind_depth (int, default=3): Maximum nested induction depth.
            max_induction_instances (int, default=4): Maximum induction instances for translation.
            max_steps (int, default=1000): Maximum search iterations limit.
            timeout_sec (float, default=10.0): Search timeout limit in seconds.

        Example:
            >>> from logic_prover.constructive.ha import HAProver
            >>> prover = HAProver(method="ljt", max_ind_depth=2)
            >>> prover.method
            'ljt'
        """
        self.method = method.lower()
        self.max_ind_depth = max(0, max_ind_depth)
        self.max_induction_instances = max(1, max_induction_instances)
        self.max_steps = max(1, max_steps)
        self.timeout_sec = max(0.1, timeout_sec)

    def prove(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> Optional[Union[LJTProofTree, TableauProofResult, TranslationResolutionResult]]:
        """Attempts to prove a target formula in Heyting Arithmetic.

        Args:
            target (Formula): The arithmetic goal formula to prove.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis formulas.

        Returns:
            Optional[Union[LJTProofTree, TableauProofResult, TranslationResolutionResult]]:
                Derivation result if provable, None otherwise.

        Example:
            >>> from logic_prover.core.ast import Variable, Equality, Forall, FunctionApp
            >>> from logic_prover.core.sorts import Nat
            >>> from logic_prover.constructive.ha import HAProver
            >>> n = Variable(0, sort=Nat)
            >>> zero = Constant("zero", sort=Nat)
            >>> goal = Forall(n, Equality(FunctionApp("add", 2, (zero, n), return_sort=Nat), n))
            >>> prover = HAProver(method="ljt")
            >>> res = prover.prove(goal)
            >>> res is not None
            True
        """
        ha_axioms = [form for _, form in get_ha_axioms()]
        all_premises = list(ha_axioms) + list(premises or [])

        if self.method == "ljt":
            ljt = LJTProver(
                max_depth=self.max_steps,
                max_ind_depth=self.max_ind_depth,
            )
            return ljt.prove(target=target, premises=all_premises)

        elif self.method == "tableau":
            tab = TableauProver(
                max_depth=self.max_steps,
                max_ind_depth=self.max_ind_depth,
            )
            return tab.prove(target=target, premises=all_premises)

        elif self.method == "translation":
            # Instantiate induction schemas for subformulas of target and premises
            induction_instances: List[Formula] = []
            candidates = _extract_induction_candidates(target, max_candidates=self.max_induction_instances)
            for prop_form, var in candidates:
                ind_ax = instantiate_ha_induction(prop_form, var)
                induction_instances.append(ind_ax)

            for p in (premises or []):
                p_cands = _extract_induction_candidates(p, max_candidates=self.max_induction_instances)
                for prop_form, var in p_cands:
                    ind_ax = instantiate_ha_induction(prop_form, var)
                    if ind_ax not in induction_instances:
                        induction_instances.append(ind_ax)

            eq_axioms = [form for _, form in get_equality_axioms()]
            trans_premises = all_premises + induction_instances + eq_axioms

            trans = TranslationResolutionProver(
                max_steps=self.max_steps,
                timeout_sec=self.timeout_sec,
            )
            return trans.prove(target=target, premises=trans_premises)

        elif self.method == "auto":
            # 1. Try LJT
            ljt = LJTProver(
                max_depth=self.max_steps,
                max_ind_depth=self.max_ind_depth,
            )
            res_ljt = ljt.prove(target=target, premises=all_premises)
            if res_ljt is not None and res_ljt.is_valid():
                return res_ljt

            # 2. Try Tableau
            tab = TableauProver(
                max_depth=self.max_steps,
                max_ind_depth=self.max_ind_depth,
            )
            res_tab = tab.prove(target=target, premises=all_premises)
            if res_tab.is_valid:
                return res_tab

            # 3. Try Translation
            induction_instances = []
            candidates = _extract_induction_candidates(target, max_candidates=self.max_induction_instances)
            for prop_form, var in candidates:
                ind_ax = instantiate_ha_induction(prop_form, var)
                induction_instances.append(ind_ax)
            eq_axioms = [form for _, form in get_equality_axioms()]
            trans_premises = all_premises + induction_instances + eq_axioms
            trans = TranslationResolutionProver(
                max_steps=self.max_steps,
                timeout_sec=self.timeout_sec,
            )
            return trans.prove(target=target, premises=trans_premises)

        else:
            raise ValueError(f"Unknown HA proof method: {self.method}")

    def is_provable(
        self,
        target: Formula,
        premises: Optional[Sequence[Formula]] = None,
    ) -> bool:
        """Checks whether a formula is provable in Heyting Arithmetic.

        Args:
            target (Formula): The arithmetic goal formula to check.
            premises (Optional[Sequence[Formula]], default=None): Optional hypothesis formulas.

        Returns:
            bool: True if provable in HA, False otherwise.

        Example:
            >>> from logic_prover.core.ast import Variable, Equality, Forall, FunctionApp
            >>> from logic_prover.core.sorts import Nat
            >>> from logic_prover.constructive.ha import HAProver
            >>> n = Variable(0, sort=Nat)
            >>> zero = Constant("zero", sort=Nat)
            >>> goal = Forall(n, Equality(FunctionApp("add", 2, (zero, n), return_sort=Nat), n))
            >>> prover = HAProver()
            >>> prover.is_provable(goal)
            True
        """
        res = self.prove(target=target, premises=premises)
        if res is None:
            return False
        if isinstance(res, LJTProofTree):
            return res.is_valid()
        if isinstance(res, TableauProofResult):
            return res.is_valid
        if isinstance(res, TranslationResolutionResult):
            return res.is_valid
        return False


def prove_ha(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    method: str = "ljt",
    max_ind_depth: int = 3,
    max_induction_instances: int = 4,
    max_steps: int = 1000,
    timeout_sec: float = 10.0,
) -> Optional[Union[LJTProofTree, TableauProofResult, TranslationResolutionResult]]:
    """Proves a formula in Heyting Arithmetic (HA).

    Args:
        formula (Formula): Arithmetic goal formula to prove.
        premises (Optional[List[Formula]], default=None): Optional hypothesis premises.
        method (str, default='ljt'): Prover backend method ('ljt', 'tableau', 'translation', 'auto').
        max_ind_depth (int, default=3): Maximum nested induction depth limit.
        max_induction_instances (int, default=4): Maximum induction schema instances for translation.
        max_steps (int, default=1000): Maximum search iterations limit.
        timeout_sec (float, default=10.0): Search timeout limit in seconds.

    Returns:
        Optional[Union[LJTProofTree, TableauProofResult, TranslationResolutionResult]]:
            Proof derivation result if provable, None otherwise.

    Example:
        >>> from logic_prover.core.ast import Variable, Equality, Forall, FunctionApp
        >>> from logic_prover.core.sorts import Nat
        >>> from logic_prover.constructive.ha import prove_ha
        >>> n = Variable(0, sort=Nat)
        >>> zero = Constant("zero", sort=Nat)
        >>> goal = Forall(n, Equality(FunctionApp("add", 2, (zero, n), return_sort=Nat), n))
        >>> proof = prove_ha(goal)
        >>> proof is not None
        True
    """
    prover = HAProver(
        method=method,
        max_ind_depth=max_ind_depth,
        max_induction_instances=max_induction_instances,
        max_steps=max_steps,
        timeout_sec=timeout_sec,
    )
    return prover.prove(target=formula, premises=premises)


__all__ = [
    "_extract_induction_candidates",
    "HAProver",
    "prove_ha",
]

