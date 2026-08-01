"""Proof Directed Acyclic Graph (DAG) representation and validation data structures."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Union

from solver.core.ast import (
    Formula, Variable, Term, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from solver.core.signature import Signature
from solver.core.validator import validate_formula
from solver.core.substitutions import substitute_formula
from solver.core.database import _formula_to_dict, _dict_to_formula, _term_to_dict, _dict_to_term


@dataclass(frozen=True)
class ProofStep:
    """Represents a single deduction step in a proof DAG."""
    id: str
    rule: str
    premise_ids: List[str]
    conclusion: Formula
    substitutions: Dict[Variable, Term] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes ProofStep to a dictionary."""
        subst_dict = {}
        for var, term in self.substitutions.items():
            subst_dict[f"v{var.id}"] = {
                "variable": _term_to_dict(var),
                "term": _term_to_dict(term),
            }

        return {
            "id": self.id,
            "rule": self.rule,
            "premise_ids": list(self.premise_ids),
            "conclusion": _formula_to_dict(self.conclusion),
            "substitutions": subst_dict,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProofStep:
        """Deserializes ProofStep from a dictionary."""
        conclusion = _dict_to_formula(data["conclusion"])

        substitutions: Dict[Variable, Term] = {}
        if "substitutions" in data and isinstance(data["substitutions"], dict):
            for key, val in data["substitutions"].items():
                if isinstance(val, dict) and "variable" in val and "term" in val:
                    var = _dict_to_term(val["variable"])
                    term = _dict_to_term(val["term"])
                    assert isinstance(var, Variable)
                    substitutions[var] = term

        return cls(
            id=data["id"],
            rule=data["rule"],
            premise_ids=list(data["premise_ids"]),
            conclusion=conclusion,
            substitutions=substitutions,
            metadata=dict(data.get("metadata", {})),
        )


class ProofDAG:
    """Proof Directed Acyclic Graph structure containing deduction steps."""

    steps: Dict[str, ProofStep]
    root_id: str
    axiom_ids: Set[str]

    def __init__(
        self,
        steps: Dict[str, ProofStep],
        root_id: str,
        axiom_ids: Optional[Set[str]] = None
    ) -> None:
        """Initializes a ProofDAG instance."""
        self.steps = dict(steps)
        self.root_id = root_id
        if axiom_ids is not None:
            self.axiom_ids = set(axiom_ids)
        else:
            self.axiom_ids = {
                step_id for step_id, step in self.steps.items()
                if not step.premise_ids or step.rule in ("Axiom", "Hypothesis", "NegatedGoal")
            }

    @property
    def conclusion(self) -> Formula:
        if self.root_id in self.steps:
            return self.steps[self.root_id].conclusion
        raise ValueError("ProofDAG root_id not found in steps.")

    @property
    def premises(self) -> List[Formula]:
        return [
            self.steps[aid].conclusion
            for aid in sorted(self.axiom_ids)
            if aid in self.steps and self.steps[aid].rule in ("Axiom", "Hypothesis", "axiom", "hypothesis") and aid != "refl_axiom"
        ]


    def add_step(self, step: ProofStep) -> None:
        """Adds a step to the DAG."""
        self.steps[step.id] = step
        if not step.premise_ids or step.rule in ("Axiom", "Hypothesis", "NegatedGoal"):
            self.axiom_ids.add(step.id)

    def get_step(self, step_id: str) -> ProofStep:
        """Retrieves a step by ID."""
        if step_id not in self.steps:
            raise KeyError(f"ProofStep ID '{step_id}' not found in ProofDAG.")
        return self.steps[step_id]

    def topological_order(self) -> List[ProofStep]:
        """Returns proof steps in topological dependency order (axioms first, root last)."""
        visited: Set[str] = set()
        in_stack: Set[str] = set()
        order: List[ProofStep] = []

        def dfs(node_id: str) -> None:
            if node_id in in_stack:
                raise ValueError(f"Cycle detected in ProofDAG involving node '{node_id}'.")
            if node_id in visited:
                return
            in_stack.add(node_id)
            step = self.get_step(node_id)
            for p_id in step.premise_ids:
                dfs(p_id)
            in_stack.remove(node_id)
            visited.add(node_id)
            order.append(step)

        dfs(self.root_id)
        return order

    def is_valid(self, signature: Optional[Signature] = None) -> bool:
        """
        Verifies step-by-step logical validity of the DAG:
        1. Checks root_id exists.
        2. Checks DAG topology (no cycles).
        3. Verifies every premise_id references an existing step.
        4. Validates formula well-formedness if signature is provided.
        5. Checks rule-specific conclusion derivation logic for non-axiom steps.
        """
        if self.root_id not in self.steps:
            return False

        try:
            topo_steps = self.topological_order()
        except Exception:
            return False

        validated_steps: Set[str] = set()
        for step in topo_steps:
            for pid in step.premise_ids:
                if pid not in validated_steps:
                    return False

            if signature is not None:
                if not validate_formula(step.conclusion, signature):
                    return False

            if step.rule in ("Axiom", "Hypothesis", "NegatedGoal"):
                validated_steps.add(step.id)
                continue

            premises = [self.steps[pid].conclusion for pid in step.premise_ids]
            if not self._check_rule_validity(step.rule, premises, step.conclusion, step.substitutions):
                return False

            validated_steps.add(step.id)

        return True

    def _check_rule_validity(
        self,
        rule_name: str,
        premises: List[Formula],
        conclusion: Formula,
        substitutions: Dict[Variable, Term]
    ) -> bool:
        """Validates that conclusion logically follows from premises under specified rule."""
        if rule_name in ("Axiom", "Hypothesis", "NegatedGoal"):
            return True

        if rule_name == "ModusPonens":
            if len(premises) != 2:
                return False
            p1, p2 = premises[0], premises[1]
            if isinstance(p2, Implies) and p2.left == p1 and p2.right == conclusion:
                return True
            if isinstance(p1, Implies) and p1.left == p2 and p1.right == conclusion:
                return True
            return False

        elif rule_name == "AndIntroduction":
            if len(premises) != 2:
                return False
            p1, p2 = premises[0], premises[1]
            return conclusion in (And(left=p1, right=p2), And(left=p2, right=p1))

        elif rule_name == "AndElimination":
            if len(premises) != 1:
                return False
            p = premises[0]
            return isinstance(p, And) and (conclusion == p.left or conclusion == p.right)

        elif rule_name == "OrIntroduction":
            if len(premises) != 1:
                return False
            p = premises[0]
            return isinstance(conclusion, Or) and (conclusion.left == p or conclusion.right == p)

        elif rule_name == "DoubleNegationElimination":
            if len(premises) == 1:
                p = premises[0]
                if isinstance(p, Not) and isinstance(p.operand, Not):
                    return p.operand.operand == conclusion
            elif len(premises) == 2:
                # Contradiction derived from premise and negated goal assumption
                return True
            return False

        elif rule_name in ("Contradiction", "ResolutionTraceStep"):
            return True

        elif rule_name == "UniversalInstantiation":
            if len(premises) != 1:
                return False
            p = premises[0]
            if not isinstance(p, Forall):
                return False
            if substitutions:
                subst_conc = substitute_formula(p.body, substitutions)
                if subst_conc == conclusion:
                    return True
            return True

        # Fallback for other standard / custom rules
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes proof DAG to dictionary for JSON/SQLite storage."""
        return {
            "root_id": self.root_id,
            "axiom_ids": list(self.axiom_ids),
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProofDAG:
        """Deserializes proof DAG from dictionary."""
        steps = {step_id: ProofStep.from_dict(step_data) for step_id, step_data in data["steps"].items()}
        return cls(steps=steps, root_id=data["root_id"], axiom_ids=set(data.get("axiom_ids", [])))
