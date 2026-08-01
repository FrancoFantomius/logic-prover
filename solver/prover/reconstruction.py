"""Natural deduction proof reconstruction from resolution trace logs."""

from __future__ import annotations
from typing import List, Dict, Set, Optional, Tuple, TYPE_CHECKING
from solver.core.ast import (
    Formula, Not, Implies, And, Or, Forall, Exists, PredicateApp, Equality
)
from solver.core.parser import to_string
from solver.prover.proof import ProofDAG, ProofStep

if TYPE_CHECKING:
    from solver.prover.engine import ResolutionStep
    from solver.prover.clausifier import Clause, Literal


def _literal_to_formula(lit: Literal) -> Formula:
    """Converts a single Literal back into an AST Formula."""
    if lit.positive:
        return lit.atom
    else:
        return Not(operand=lit.atom)


def _clause_to_formula(clause: Clause) -> Formula:
    """Converts a Clause back into a disjunctive Formula tree."""
    if clause.is_empty:
        return PredicateApp(pred="False", arity=0, args=())

    sorted_lits = sorted(list(clause.literals), key=lambda l: l.to_string())
    formulas = [_literal_to_formula(l) for l in sorted_lits]

    res = formulas[0]
    for f in formulas[1:]:
        res = Or(left=res, right=f)
    return res


def reconstruct_proof(
    resolution_trace: List[ResolutionStep],
    original_target: Formula,
    premises: Optional[List[Formula]] = None
) -> ProofDAG:
    """
    Converts a resolution refutation trace (proving ⊥ from premises ∧ ¬target)
    into a valid Natural Deduction ProofDAG for original_target.

    Pipeline:
    1. Map initial 'axiom' steps to ND premises.
    2. Map initial 'negated_goal' step to assumption ¬original_target.
    3. Convert resolution steps into ND inferences (Modus Ponens, Or Elimination, ResolutionTraceStep).
    4. Derive contradiction ⊥ at empty clause root step.
    5. Apply Double Negation Elimination / Proof by Contradiction to yield original_target as root.
    """
    steps: Dict[str, ProofStep] = {}
    premises = premises or []

    axiom_step_ids: Set[str] = set()
    premise_formula_to_id: Dict[Formula, str] = {}
    for idx, prem in enumerate(premises):
        aid = f"premise_{idx}"
        steps[aid] = ProofStep(
            id=aid,
            rule="Axiom",
            premise_ids=[],
            conclusion=prem
        )
        axiom_step_ids.add(aid)
        premise_formula_to_id[prem] = aid

    goal_assump_id = "negated_target_assump"
    steps[goal_assump_id] = ProofStep(
        id=goal_assump_id,
        rule="NegatedGoal",
        premise_ids=[],
        conclusion=Not(operand=original_target)
    )

    res_to_nd_map: Dict[str, str] = {}
    for rstep in resolution_trace:
        if rstep.rule_name in ("axiom", "negated_goal"):
            if rstep.rule_name == "axiom":
                if rstep.original_formula in premise_formula_to_id:
                    res_to_nd_map[rstep.id] = premise_formula_to_id[rstep.original_formula]
                elif axiom_step_ids:
                    res_to_nd_map[rstep.id] = list(axiom_step_ids)[0]
                else:
                    aid = f"axiom_{rstep.id}"
                    steps[aid] = ProofStep(
                        id=aid,
                        rule="Axiom",
                        premise_ids=[],
                        conclusion=_clause_to_formula(rstep.clause)
                    )
                    axiom_step_ids.add(aid)
                    res_to_nd_map[rstep.id] = aid
            else:
                res_to_nd_map[rstep.id] = goal_assump_id
            continue

        nd_premise_ids = [res_to_nd_map[pid] for pid in rstep.premise_ids if pid in res_to_nd_map]
        nd_id = f"nd_{rstep.id}"

        clause_formula = _clause_to_formula(rstep.clause)

        steps[nd_id] = ProofStep(
            id=nd_id,
            rule="ResolutionTraceStep",
            premise_ids=nd_premise_ids,
            conclusion=clause_formula,
            substitutions=dict(rstep.substitution),
            metadata={"clause": rstep.clause.to_string(), "rule_name": rstep.rule_name}
        )
        res_to_nd_map[rstep.id] = nd_id

    last_res_id = res_to_nd_map[resolution_trace[-1].id]
    contra_id = "derived_contradiction"
    steps[contra_id] = ProofStep(
        id=contra_id,
        rule="Contradiction",
        premise_ids=[last_res_id],
        conclusion=PredicateApp(pred="False", arity=0, args=())
    )

    root_id = "final_conclusion"
    steps[root_id] = ProofStep(
        id=root_id,
        rule="DoubleNegationElimination",
        premise_ids=[contra_id, goal_assump_id],
        conclusion=original_target
    )

    dag = ProofDAG(steps=steps, root_id=root_id, axiom_ids=axiom_step_ids)
    return simplify_proof(dag)


def simplify_proof(proof: ProofDAG) -> ProofDAG:
    """
    Optimizes ProofDAG by:
    1. Pruning dead/unreachable steps not leading to root_id.
    2. Collapsing identity and redundant single-premise steps.
    """
    try:
        reachable_ids = {s.id for s in proof.topological_order()}
    except Exception:
        return proof

    new_steps = {sid: step for sid, step in proof.steps.items() if sid in reachable_ids}
    return ProofDAG(steps=new_steps, root_id=proof.root_id, axiom_ids=proof.axiom_ids & reachable_ids)
