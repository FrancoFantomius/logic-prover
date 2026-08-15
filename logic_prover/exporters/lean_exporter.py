"""Lean 4 exporter for translating terms, formulas, and proof DAGs to formal Lean 4 code."""

from __future__ import annotations
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Union

from logic_prover.core.ast import (
    Term, Variable, Constant, FunctionApp, Formula, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Sort, PrimitiveSort, ParameterizedSort, FunctionSort, Ind
from logic_prover.prover.proof import ProofDAG, ProofStep
from logic_prover.core.exceptions import SolverError, ValidationError


class LeanExporter:
    """Translates logic AST nodes, formulas, theorem declarations, and proof DAGs into LEAN 4 code."""

    def __init__(
        self,
        lean_project_name: str = "Logic",
        universe_name: str = "u",
        default_sort_var: str = "α"
    ) -> None:
        """
        Initializes the LEAN exporter.

        Args:
            lean_project_name: Name of the project/namespace.
            universe_name: LEAN universe variable name (default "u").
            default_sort_var: Default type variable name for Ind sort (default "α").
        """
        self.lean_project_name = self._sanitize_identifier(lean_project_name)
        self.universe_name = universe_name
        self.default_sort_var = default_sort_var
        self._sort_mappings: Dict[str, str] = {
            "Nat": "ℕ",
            "Bool": "Bool",
            "Prop": "Prop",
            "Ind": default_sort_var,
        }

    def export_preamble(
        self,
        imports: Optional[List[str]] = None,
        open_namespaces: Optional[List[str]] = None
    ) -> str:
        """
        Generates LEAN 4 file header including module imports, universe variables, and namespace declarations.

        Args:
            imports: Optional list of modules to import (defaults to ["Mathlib.Tactic"]).
            open_namespaces: Optional list of LEAN namespaces to open.

        Returns:
            Formatted LEAN 4 preamble string.
        """
        if imports is None:
            imports = ["Mathlib.Tactic"]

        lines = [f"import {imp}" for imp in imports]
        lines.append("")
        lines.append(f"universe {self.universe_name}")
        lines.append(f"variable {{{self.default_sort_var} : Type {self.universe_name}}}")

        if open_namespaces:
            for ns in open_namespaces:
                lines.append(f"open {ns}")

        lines.append("")
        lines.append(f"namespace {self.lean_project_name}")
        lines.append("")
        return "\n".join(lines)

    def export_sort(self, sort: Sort) -> str:
        """
        Translates a Sort object into LEAN 4 type syntax.

        Args:
            sort: Target Sort instance.

        Returns:
            LEAN 4 sort representation string (e.g. "ℕ", "Set α", "α → α").
        """
        if isinstance(sort, PrimitiveSort):
            return self._sort_mappings.get(sort.sort_name, sort.sort_name)
        elif isinstance(sort, ParameterizedSort):
            args_str = " ".join(self.export_sort(arg) for arg in sort.args)
            return f"{sort.constructor} {args_str}"
        elif isinstance(sort, FunctionSort):
            arg_sorts = getattr(sort, "arg_sorts", getattr(sort, "param_sorts", ()))
            param_str = " → ".join(self.export_sort(p) for p in arg_sorts)
            ret_str = self.export_sort(sort.return_sort)
            return f"{param_str} → {ret_str}" if param_str else ret_str
        return self.default_sort_var

    def export_term(self, term: Term) -> str:
        """
        Translates a Term AST node into LEAN 4 term expression string.

        Args:
            term: Target Term instance.

        Returns:
            Formatted LEAN 4 term string.
        """
        if isinstance(term, Variable):
            name = getattr(term, "name", None)
            return name if name else f"v{term.id}"
        elif isinstance(term, Constant):
            return term.name
        elif isinstance(term, FunctionApp):
            func_name = term.func.name if hasattr(term.func, "name") else str(term.func)
            infix_ops = {"+", "-", "*", "/", "%"}
            if func_name in infix_ops and len(term.args) == 2:
                left = self.export_term(term.args[0])
                right = self.export_term(term.args[1])
                return f"({left} {func_name} {right})"
            args_str = " ".join(self.export_term(arg) for arg in term.args)
            return f"({func_name} {args_str})" if term.args else func_name
        raise SolverError(f"Unsupported Term node type: {type(term)}")

    def export_formula(self, formula: Formula) -> str:
        """
        Translates a Formula AST node into LEAN 4 proposition string.

        Args:
            formula: Target Formula instance.

        Returns:
            Formatted LEAN 4 proposition syntax string.
        """
        if isinstance(formula, PredicateApp):
            pred_name = formula.pred.name if hasattr(formula.pred, "name") else str(formula.pred)
            infix_rels = {"<", "<=", ">", ">=", "∈", "⊆"}
            if pred_name in infix_rels and len(formula.args) == 2:
                left = self.export_term(formula.args[0])
                right = self.export_term(formula.args[1])
                return f"({left} {pred_name} {right})"
            args_str = " ".join(self.export_term(arg) for arg in formula.args)
            return f"({pred_name} {args_str})" if formula.args else pred_name
        elif isinstance(formula, Equality):
            left = self.export_term(formula.left)
            right = self.export_term(formula.right)
            return f"({left} = {right})"
        elif isinstance(formula, Not):
            operand = getattr(formula, "operand", getattr(formula, "arg", None))
            if operand is None:
                raise SolverError("Not formula has no operand.")
            inner = self.export_formula(operand)
            return f"¬ ({inner})"
        elif isinstance(formula, And):
            left = self.export_formula(formula.left)
            right = self.export_formula(formula.right)
            return f"({left} ∧ {right})"
        elif isinstance(formula, Or):
            left = self.export_formula(formula.left)
            right = self.export_formula(formula.right)
            return f"({left} ∨ {right})"
        elif isinstance(formula, Implies):
            left = self.export_formula(formula.left)
            right = self.export_formula(formula.right)
            return f"({left} → {right})"
        elif isinstance(formula, Iff):
            left = self.export_formula(formula.left)
            right = self.export_formula(formula.right)
            return f"({left} ↔ {right})"
        elif isinstance(formula, Forall):
            var_name = getattr(formula.variable, "name", None) or f"v{formula.variable.id}"
            sort_str = self.export_sort(formula.variable.sort)
            body_str = self.export_formula(formula.body)
            return f"∀ ({var_name} : {sort_str}), {body_str}"
        elif isinstance(formula, Exists):
            var_name = getattr(formula.variable, "name", None) or f"v{formula.variable.id}"
            sort_str = self.export_sort(formula.variable.sort)
            body_str = self.export_formula(formula.body)
            return f"∃ ({var_name} : {sort_str}), {body_str}"
        elif type(formula).__name__ == "ForallPred":
            var_name = getattr(formula, "variable").name
            arity = getattr(formula, "variable").arity
            sort_type = " → ".join([self.default_sort_var] * arity) + " → Prop" if arity > 0 else "Prop"
            body_str = self.export_formula(getattr(formula, "body"))
            return f"∀ ({var_name} : {sort_type}), {body_str}"
        elif type(formula).__name__ == "ExistsPred":
            var_name = getattr(formula, "variable").name
            arity = getattr(formula, "variable").arity
            sort_type = " → ".join([self.default_sort_var] * arity) + " → Prop" if arity > 0 else "Prop"
            body_str = self.export_formula(getattr(formula, "body"))
            return f"∃ ({var_name} : {sort_type}), {body_str}"
        elif type(formula).__name__ == "ForallFunc":
            var_name = getattr(formula, "variable").name
            arity = getattr(formula, "variable").arity
            sort_type = " → ".join([self.default_sort_var] * (arity + 1))
            body_str = self.export_formula(getattr(formula, "body"))
            return f"∀ ({var_name} : {sort_type}), {body_str}"
        elif type(formula).__name__ == "ExistsFunc":
            var_name = getattr(formula, "variable").name
            arity = getattr(formula, "variable").arity
            sort_type = " → ".join([self.default_sort_var] * (arity + 1))
            body_str = self.export_formula(getattr(formula, "body"))
            return f"∃ ({var_name} : {sort_type}), {body_str}"
        raise SolverError(f"Unsupported Formula node type: {type(formula)}")

    def export_theorem_statement(
        self,
        name: str,
        formula: Formula,
        hypotheses: Optional[List[Tuple[str, Formula]]] = None
    ) -> str:
        """
        Generates a LEAN 4 theorem signature statement with a sorry placeholder.

        Args:
            name: Theorem identifier name.
            formula: Target conclusion formula.
            hypotheses: Optional list of named hypothesis premises [(h1_name, h1_formula), ...].

        Returns:
            Formatted LEAN 4 theorem statement string ending in ':= by\n  sorry'.
        """
        clean_name = self._sanitize_identifier(name)
        params = []
        if hypotheses:
            for h_name, h_form in hypotheses:
                clean_h_name = self._sanitize_identifier(h_name)
                h_str = self.export_formula(h_form)
                params.append(f"({clean_h_name} : {h_str})")

        param_str = " ".join(params) + " " if params else ""
        conc_str = self.export_formula(formula)
        return f"theorem {clean_name} {param_str}: {conc_str} := by\n  sorry"

    def export_proof(
        self,
        proof: ProofDAG,
        theorem_name: str = "thm"
    ) -> str:
        """
        Translates a ProofDAG into a structured LEAN 4 theorem declaration with tactic proof body.

        Args:
            proof: Validated ProofDAG object.
            theorem_name: Target theorem name.

        Returns:
            Complete LEAN 4 theorem with tactic block using Mathlib tactics.
        """
        clean_name = self._sanitize_identifier(theorem_name)
        top_steps = proof.topological_order()

        lean_ids = {step.id: self._sanitize_identifier(step.id) for step in top_steps}

        premise_steps = [
            step for step in top_steps
            if not step.premise_ids or str(step.rule).lower() in ("axiom", "hypothesis")
        ]
        premise_steps = sorted(premise_steps, key=lambda s: s.id)
        premise_set = {step.id for step in premise_steps}
        derivation_steps = [step for step in top_steps if step.id not in premise_set]

        hyp_args = []
        for p_step in premise_steps:
            hyp_name = lean_ids[p_step.id]
            hyp_formula_str = self.export_formula(p_step.conclusion)
            hyp_args.append(f"({hyp_name} : {hyp_formula_str})")

        hyp_str = " ".join(hyp_args) + " " if hyp_args else ""
        root_step = proof.steps[proof.root_id]
        target_str = self.export_formula(root_step.conclusion)

        lines = [f"theorem {clean_name} {hyp_str}: {target_str} := by"]

        for step in derivation_steps:
            tactic_code = self._translate_step_to_tactic(step, lean_ids)
            step_formula = self.export_formula(step.conclusion)
            step_lean_id = lean_ids[step.id]
            lines.append(f"  have {step_lean_id} : {step_formula} := {tactic_code}")

        root_lean_id = lean_ids[proof.root_id]
        lines.append(f"  exact {root_lean_id}")
        return "\n".join(lines)

    def export_file(
        self,
        file_path: str,
        theorems: List[Tuple[str, Formula, Optional[ProofDAG]]],
        stubs_only: bool = False,
        imports: Optional[List[str]] = None
    ) -> None:
        """
        Writes a complete standalone LEAN 4 source file containing preambles and theorem declarations.

        Args:
            file_path: Output disk path for .lean file.
            theorems: List of tuples (theorem_name, formula, optional_proof_dag).
            stubs_only: If True, exports all theorems as 'sorry' stubs regardless of proof availability.
            imports: Optional custom import module list.
        """
        content_blocks = [self.export_preamble(imports=imports)]

        for name, formula, proof in theorems:
            if stubs_only or proof is None:
                stmt = self.export_theorem_statement(name=name, formula=formula)
                content_blocks.append(stmt)
            else:
                proof_code = self.export_proof(proof=proof, theorem_name=name)
                content_blocks.append(proof_code)

        content_blocks.append(f"end {self.lean_project_name}\n")

        full_content = "\n\n".join(content_blocks)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(full_content)

    def _translate_step_to_tactic(
        self,
        step: ProofStep,
        lean_ids: Optional[Dict[str, str]] = None
    ) -> str:
        """Translates an individual ProofStep into LEAN 4 tactic expression."""
        rule_name = step.rule.name if hasattr(step.rule, "name") else str(step.rule)
        raw_p_ids = step.premise_ids
        p_ids = [lean_ids.get(pid, pid) for pid in raw_p_ids] if lean_ids else list(raw_p_ids)

        if rule_name in ("ModusPonens", "MP", "InferenceRule.MODUS_PONENS") and len(p_ids) == 2:
            return f"{p_ids[0]} {p_ids[1]}"
        elif rule_name in ("AndIntroduction", "AndIntro") and len(p_ids) == 2:
            return f"⟨{p_ids[0]}, {p_ids[1]}⟩"
        elif rule_name in ("AndEliminationLeft", "AndElimLeft") and len(p_ids) == 1:
            return f"{p_ids[0]}.1"
        elif rule_name in ("AndEliminationRight", "AndElimRight") and len(p_ids) == 1:
            return f"{p_ids[0]}.2"
        elif rule_name in ("AndElimination", "AndElim") and len(p_ids) == 1:
            return f"{p_ids[0]}.1"
        elif rule_name in ("UniversalInstantiation", "UI", "ForallElimination") and len(p_ids) >= 1:
            term_arg = " ".join(self.export_term(t) for t in step.substitutions.values()) if step.substitutions else "_"
            return f"{p_ids[0]} {term_arg}"
        elif rule_name in ("EqualityReflexivity", "EqRefl", "Refl"):
            return "rfl"
        elif rule_name in ("EqualitySymmetry", "EqSymm", "Symm") and len(p_ids) == 1:
            return f"{p_ids[0]}.symm"
        elif rule_name in ("EqualityTransitivity", "EqTrans", "Trans") and len(p_ids) == 2:
            return f"{p_ids[0]}.trans {p_ids[1]}"
        elif rule_name in ("Paramodulation", "Rewrite", "Simp") and len(p_ids) >= 1:
            return f"by simp [{', '.join(p_ids)}]"

        # Default fallback to LEAN automation tactics
        return "by aesop"

    def _sanitize_identifier(self, name: str) -> str:
        """Sanitizes theorem and variable names into valid LEAN 4 identifiers."""
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if clean and clean[0].isdigit():
            clean = f"thm_{clean}"
        return clean or "thm"
