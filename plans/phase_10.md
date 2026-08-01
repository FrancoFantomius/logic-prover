# Phase 10 — Exporters Implementation Plan

**Goal**: Implement LEAN 4 formal proof export across formula, theorem statement, and tactic proof tiers, alongside interactive HTML graph visualization for proof DAGs and theorem dependency networks.

**Deliverables**:
- [solver/exporters/__init__.py](file:///C:/Users/franc/Programmazione/solver/solver/exporters/__init__.py)
- [solver/exporters/lean_exporter.py](file:///C:/Users/franc/Programmazione/solver/solver/exporters/lean_exporter.py)
- [solver/exporters/graph_exporter.py](file:///C:/Users/franc/Programmazione/solver/solver/exporters/graph_exporter.py)
- CLI `export` commands in [solver/__main__.py](file:///C:/Users/franc/Programmazione/solver/solver/__main__.py)
- Passing test suite: [tests/test_exporters.py](file:///C:/Users/franc/Programmazione/solver/tests/test_exporters.py)

---

## 1. Overview & Architectural Goals

Phase 10 connects the solver's internal logical data structures—Abstract Syntax Tree (`Formula`, `Term`), `Sort` system, proof DAG (`ProofDAG`), and dependency graph (`DependencyGraph`)—to external interactive environments and interactive formal proof assistants. As outlined in Section 3.16 of the master plan:

1. **LEAN 4 Exporter (`LeanExporter`)**:
   Provides formal verification interoperability by outputting syntactically valid, parseable LEAN 4 code (`.lean`). The export functionality is organized into three tiers of increasing detail:
   - **Tier 1 — Formula Export (`export_formula`)**: Translates AST formulas into idiomatic LEAN 4 proposition expressions, respecting variable sorts, standard logical unicode symbols (`∀`, `∃`, `∧`, `∨`, `→`, `↔`, `¬`, `=`), and operator precedence.
   - **Tier 2 — Theorem Statement Export (`export_theorem_statement`)**: Translates theorem declarations into LEAN 4 `theorem` signatures with named hypothesis parameters and `sorry` stubs for unproven assertions or `--stubs-only` mode.
   - **Tier 3 — Proof Export (`export_proof`)**: Translates natural deduction `ProofDAG` structures into LEAN 4 structured tactic blocks (`by`). Translates DAG proof steps into intermediate `have` assertions and utilizes Mathlib tactics (`simp`, `aesop`, `exact`, `have`, `apply`) to produce clean, high-level proofs.

2. **Interactive HTML Graph Exporter (`GraphExporter`)**:
   Generates standalone, self-contained HTML visualizers using [vis.js (vis-network)](https://visjs.org/).
   - **Proof DAG Visualization**: Renders natural deduction proof DAGs in hierarchical layout. Colors nodes according to step rule types (Hypothesis, Premise, ModusPonens, UniversalInstantiation, Resolution, etc.), shows formulas and rule details in tooltips, and draws directed dependency edges.
   - **Dependency Network Visualization**: Renders global theorem networks (`DependencyGraph` from Phase 9), node-colored by provability/category status, showing directed implication, dependency, and logical equivalence edges with interactive search, zoom, and force-directed controls.

---

## 2. Prerequisites

The following preceding phases must be implemented and passing unit tests prior to Phase 10:

1. **Phase 1 — AST & Sort System**:
   - [solver/core/ast.py](file:///C:/Users/franc/Programmazione/solver/solver/core/ast.py): `Term`, `Variable`, `Constant`, `FunctionApp`, `Formula`, `PredicateApp`, `Equality`, `Not`, `And`, `Or`, `Implies`, `Iff`, `Forall`, `Exists`.
   - [solver/core/sorts.py](file:///C:/Users/franc/Programmazione/solver/solver/core/sorts.py): `Sort`, `PrimitiveSort`, `ParameterizedSort`, `FunctionSort`, `Ind`.
2. **Phase 3 — Visitor Framework & Parser**:
   - [solver/core/visitors.py](file:///C:/Users/franc/Programmazione/solver/solver/core/visitors.py): `ASTVisitor`.
   - [solver/core/parser.py](file:///C:/Users/franc/Programmazione/solver/solver/core/parser.py): Formula string generation and parsing.
3. **Phase 6 — Config & Exception Hierarchy**:
   - [solver/config.py](file:///C:/Users/franc/Programmazione/solver/solver/config.py): `SolverConfig` (`lean_mathlib_version`, `log_level`).
   - [solver/core/exceptions.py](file:///C:/Users/franc/Programmazione/solver/solver/core/exceptions.py): `SolverError`, `ValidationError`.
4. **Phase 7 — Prover & Proof DAG**:
   - [solver/prover/proof.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/proof.py): `ProofStep`, `ProofDAG`, `topological_order()`, `is_valid()`.
   - [solver/prover/rules.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/rules.py): `InferenceRule` enum and natural deduction step classifications.
5. **Phase 9 — Deducer & Dependency Network**:
   - [solver/deducer/graph.py](file:///C:/Users/franc/Programmazione/solver/solver/deducer/graph.py): `DependencyGraph`, `predecessors()`, `successors()`, `to_dict()`.

---

## 3. Files to Create / Modify

| File Path | Action | Description |
| :--- | :--- | :--- |
| [solver/exporters/__init__.py](file:///C:/Users/franc/Programmazione/solver/solver/exporters/__init__.py) | Create | Exposes `LeanExporter` and `GraphExporter` as public API |
| [solver/exporters/lean_exporter.py](file:///C:/Users/franc/Programmazione/solver/solver/exporters/lean_exporter.py) | Create | `LeanExporter` class for Tier 1, Tier 2, and Tier 3 LEAN 4 translation |
| [solver/exporters/graph_exporter.py](file:///C:/Users/franc/Programmazione/solver/solver/exporters/graph_exporter.py) | Create | `GraphExporter` class for standalone vis.js HTML visualization of ProofDAGs and DependencyGraphs |
| [solver/__main__.py](file:///C:/Users/franc/Programmazione/solver/solver/__main__.py) | Update | Add `export lean` and `export graph` CLI subcommands |
| [tests/test_exporters.py](file:///C:/Users/franc/Programmazione/solver/tests/test_exporters.py) | Create | Unit and integration test suite covering LEAN translation and HTML file generation |

---

## 4. Detailed Module Specifications

### 4.1 `solver/exporters/__init__.py`

Public entry point for the exporters package.

```python
from solver.exporters.lean_exporter import LeanExporter
from solver.exporters.graph_exporter import GraphExporter

__all__ = ["LeanExporter", "GraphExporter"]
```

---

### 4.2 `solver/exporters/lean_exporter.py` (Section 3.16.1)

Translates `Sort`, `Term`, `Formula`, theorem headers, and natural deduction `ProofDAG` objects into parseable LEAN 4 code.

#### LEAN 4 Mapping Rules:

| Python AST / Sort | LEAN 4 Syntax | Example / Notes |
| :--- | :--- | :--- |
| `PrimitiveSort("Nat")` | `ℕ` | Mapped via lookup dictionary |
| `PrimitiveSort("Bool")` | `Bool` or `Prop` | Sort representation |
| `PrimitiveSort("Ind")` | `α` | Default universe type variable |
| `ParameterizedSort("Set", (Nat,))` | `Set ℕ` | Parameterized types |
| `FunctionSort((S1, S2), S3)` | `S1 → S2 → S3` | Curried function signature |
| `Variable(id=0, name="x")` | `x` (or `v0` if unnamed) | Variable identifier |
| `Constant(name="c")` | `c` | Constant identifier |
| `FunctionApp(name="f", args=[t1, t2])` | `f t1 t2` | Prefix application with space separators |
| `FunctionApp(name="+", args=[t1, t2])` | `(t1 + t2)` | Infix application for binary operators |
| `PredicateApp(name="P", args=[t1])` | `P t1` | Predicate application |
| `Equality(left, right)` | `(left = right)` | Logical equality |
| `Not(arg)` | `¬ (arg)` | Negation |
| `And(left, right)` | `(left ∧ right)` | Conjunction |
| `Or(left, right)` | `(left ∨ right)` | Disjunction |
| `Implies(left, right)` | `(left → right)` | Implication |
| `Iff(left, right)` | `(left ↔ right)` | Logical equivalence |
| `Forall(var, body)` | `∀ (var : Sort), body` | Universal quantifier |
| `Exists(var, body)` | `∃ (var : Sort), body` | Existential quantifier |

#### Tactic Proof Translation Strategy (Tier 3):

When exporting a `ProofDAG`:
1. Obtain the steps in topological order using `proof.topological_order()`.
2. Map initial premise/hypothesis steps to theorem input arguments (e.g. `(h1 : P x) (h2 : P x → Q x)`).
3. For each intermediate step in the topological ordering (excluding initial premises and root target):
   - Determine rule type (`InferenceRule`):
     - **ModusPonens** ($P \to Q, P \vdash Q$): `have step_id : Q := h_implies h_p`
     - **AndIntroduction** ($P, Q \vdash P \land Q$): `have step_id : P ∧ Q := ⟨h_p, h_q⟩`
     - **AndEliminationLeft** ($P \land Q \vdash P$): `have step_id : P := h_and.1`
     - **AndEliminationRight** ($P \land Q \vdash Q$): `have step_id : Q := h_and.2`
     - **UniversalInstantiation** ($\forall x. P(x) \vdash P(t)$): `have step_id : P t := h_forall t`
     - **UniversalGeneralization** ($P(x) \vdash \forall x. P(x)$): `have step_id : ∀ x, P x := fun x => h_body`
     - **EqualityReflexivity** ($\vdash t = t$): `have step_id : t = t := rfl`
     - **EqualitySymmetry** ($t_1 = t_2 \vdash t_2 = t_1$): `have step_id : t_2 = t_1 := h_eq.symm`
     - **EqualityTransitivity** ($t_1 = t_2, t_2 = t_3 \vdash t_1 = t_3$): `have step_id : t_1 = t_3 := h1.trans h2`
     - **Paramodulation / Rewriting** ($t_1 = t_2, P(t_1) \vdash P(t_2)$): `have step_id : P t_2 := by rw [h_eq] at h_premise; exact h_premise`
     - **Resolution / Factoring / General Deduction**: `have step_id : Conclusion := by aesop` or `have step_id : Conclusion := by simp [*]`
4. For the final root conclusion step, end with `exact root_step_id` or `by exact root_step_id`.

#### Class Code Structure:

```python
from typing import List, Dict, Tuple, Optional, Set, Union
import re
from solver.core.ast import (
    Term, Variable, Constant, FunctionApp, Formula, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from solver.core.sorts import Sort, PrimitiveSort, ParameterizedSort, FunctionSort, Ind
from solver.prover.proof import ProofDAG, ProofStep
from solver.prover.rules import InferenceRule
from solver.core.exceptions import SolverError, ValidationError

class LeanExporter:
    """Translates solver AST nodes, formulas, theorem declarations, and proof DAGs into LEAN 4 code."""

    def __init__(
        self,
        lean_project_name: str = "Solver",
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
        self.lean_project_name = lean_project_name
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
            param_str = " → ".join(self.export_sort(p) for p in sort.param_sorts)
            ret_str = self.export_sort(sort.return_sort)
            return f"{param_str} → {ret_str}"
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
            return term.name if term.name else f"v{term.id}"
        elif isinstance(term, Constant):
            return term.name
        elif isinstance(term, FunctionApp):
            infix_ops = {"+", "-", "*", "/", "%"}
            if term.name in infix_ops and len(term.args) == 2:
                left = self.export_term(term.args[0])
                right = self.export_term(term.args[1])
                return f"({left} {term.name} {right})"
            args_str = " ".join(self.export_term(arg) for arg in term.args)
            return f"({term.name} {args_str})" if term.args else term.name
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
            infix_rels = {"<", "<=", ">", ">=", "∈", "⊆"}
            if formula.name in infix_rels and len(formula.args) == 2:
                left = self.export_term(formula.args[0])
                right = self.export_term(formula.args[1])
                return f"({left} {formula.name} {right})"
            args_str = " ".join(self.export_term(arg) for arg in formula.args)
            return f"({formula.name} {args_str})" if formula.args else formula.name
        elif isinstance(formula, Equality):
            left = self.export_term(formula.left)
            right = self.export_term(formula.right)
            return f"({left} = {right})"
        elif isinstance(formula, Not):
            inner = self.export_formula(formula.arg)
            return f"¬ {inner}"
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
            var_name = formula.variable.name if formula.variable.name else f"v{formula.variable.id}"
            sort_str = self.export_sort(formula.variable.sort)
            body_str = self.export_formula(formula.body)
            return f"∀ ({var_name} : {sort_str}), {body_str}"
        elif isinstance(formula, Exists):
            var_name = formula.variable.name if formula.variable.name else f"v{formula.variable.id}"
            sort_str = self.export_sort(formula.variable.sort)
            body_str = self.export_formula(formula.body)
            return f"∃ ({var_name} : {sort_str}), {body_str}"
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
            Formatted LEAN 4 theorem statement string ending in ':= by sorry'.
        """
        clean_name = self._sanitize_identifier(name)
        params = []
        if hypotheses:
            for h_name, h_form in hypotheses:
                h_str = self.export_formula(h_form)
                params.append(f"({h_name} : {h_str})")
        
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

        # Separate premises (leaf steps with no premise IDs) and derivation steps
        premise_steps = [step for step in top_steps if not step.premise_ids]
        derivation_steps = [step for step in top_steps if step.premise_ids]

        # Format hypothesis arguments
        hyp_args = []
        for p_step in premise_steps:
            hyp_name = p_step.id
            hyp_formula_str = self.export_formula(p_step.conclusion)
            hyp_args.append(f"({hyp_name} : {hyp_formula_str})")

        hyp_str = " ".join(hyp_args) + " " if hyp_args else ""
        root_step = proof.steps[proof.root_id]
        target_str = self.export_formula(root_step.conclusion)

        lines = [f"theorem {clean_name} {hyp_str}: {target_str} := by"]

        # Step by step tactic generation
        for step in derivation_steps:
            tactic_code = self._translate_step_to_tactic(step)
            step_formula = self.export_formula(step.conclusion)
            lines.append(f"  have {step.id} : {step_formula} := {tactic_code}")

        # Final assertion step
        lines.append(f"  exact {proof.root_id}")
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

        content_blocks.append(f"\nend {self.lean_project_name}")

        full_content = "\n\n".join(content_blocks)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

    def _translate_step_to_tactic(self, step: ProofStep) -> str:
        """Translates an individual ProofStep into LEAN 4 tactic expression."""
        rule = step.rule
        p_ids = step.premise_ids

        if rule == InferenceRule.MODUS_PONENS and len(p_ids) == 2:
            return f"{p_ids[0]} {p_ids[1]}"
        elif rule == InferenceRule.AND_INTRODUCTION and len(p_ids) == 2:
            return f"⟨{p_ids[0]}, {p_ids[1]}⟩"
        elif rule == InferenceRule.AND_ELIMINATION_LEFT and len(p_ids) == 1:
            return f"{p_ids[0]}.1"
        elif rule == InferenceRule.AND_ELIMINATION_RIGHT and len(p_ids) == 1:
            return f"{p_ids[0]}.2"
        elif rule == InferenceRule.UNIVERSAL_INSTANTIATION and len(p_ids) == 1:
            term_arg = " ".join(self.export_term(t) for t in step.substitutions.values()) if step.substitutions else "_"
            return f"{p_ids[0]} {term_arg}"
        elif rule == InferenceRule.EQUALITY_REFLEXIVITY:
            return "rfl"
        elif rule == InferenceRule.EQUALITY_SYMMETRY and len(p_ids) == 1:
            return f"{p_ids[0]}.symm"
        elif rule == InferenceRule.EQUALITY_TRANSITIVITY and len(p_ids) == 2:
            return f"{p_ids[0]}.trans {p_ids[1]}"
        elif rule in (InferenceRule.PARAMODULATION, InferenceRule.REWRITE) and len(p_ids) >= 1:
            return f"by simp [{', '.join(p_ids)}]"

        # Default fallback to LEAN automation tactics
        return "by aesop"

    def _sanitize_identifier(self, name: str) -> str:
        """Sanitizes theorem and variable names into valid LEAN 4 identifiers."""
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if clean and clean[0].isdigit():
            clean = f"thm_{clean}"
        return clean or "thm"
```

---

### 4.3 `solver/exporters/graph_exporter.py` (Section 3.16.2)

Exports `ProofDAG` and `DependencyGraph` instances to standalone, interactive HTML pages rendered with `vis.js` (vis-network).

#### HTML Graph Rendering Specifications:

1. **Proof DAG Layout**:
   - Layout: Hierarchical layout (`direction: 'UD'` top-down or `'LR'` left-right).
   - Node styling by inference step:
     - `Premise / Hypothesis`: Light blue `#e3f2fd`, border `#1976d2`.
     - `ModusPonens / Deduction`: Light green `#e8f5e9`, border `#388e3c`.
     - `Quantifier Rule`: Light orange `#fff3e0`, border `#f57c00`.
     - `Resolution / Paramodulation`: Light purple `#f3e5f5`, border `#7b1fa2`.
     - `Root Conclusion`: Crimson red `#ffebee`, border `#d32f2f`, shape `diamond`.
   - Tooltips: HTML popup showing Step ID, Rule Name, Formula string, Premises, and Substitutions.

2. **Dependency Network Layout**:
   - Layout: Force-directed layout (Barnes-Hut algorithm with smooth curves).
   - Node styling by formula role/status:
     - `Axiom`: Light cyan `#e1f5fe`.
     - `Proved Theorem`: Light green `#e8f5e9`.
     - `Unproven Hypothesis`: Light yellow `#fffde7`.
     - `Redundant Hypothesis`: Light gray `#efebe9`.
   - Edge styling: Directed arrows; solid lines for `implies`/`depends`, dashed lines for `equivalent`.

3. **Interactive Controls**:
   - Integrated search bar to filter and focus nodes by identifier or formula substring.
   - Interactive zoom, drag, node physics toggle, and export PNG button.

#### Class Code Structure:

```python
import json
import html
from typing import Optional, Dict, Any, List
from solver.prover.proof import ProofDAG, ProofStep
from solver.deducer.graph import DependencyGraph
from solver.core.exceptions import SolverError

class GraphExporter:
    """Exports ProofDAGs and DependencyGraphs into interactive standalone HTML files using vis.js."""

    VIS_JS_CDN = "https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"

    def __init__(self, theme: str = "light", embed_vis_js: bool = True) -> None:
        """
        Initializes the graph exporter.

        Args:
            theme: Visual theme ('light' or 'dark').
            embed_vis_js: Whether to link vis-network via CDN.
        """
        self.theme = theme
        self.embed_vis_js = embed_vis_js

    def export_proof_to_html(
        self,
        proof: ProofDAG,
        output_path: str,
        title: Optional[str] = None
    ) -> None:
        """
        Renders a natural deduction ProofDAG into an interactive hierarchical HTML visualization.

        Args:
            proof: Target ProofDAG instance.
            output_path: Output disk path for the .html file.
            title: Optional title header for the page.
        """
        page_title = title or "Proof DAG Visualization"
        nodes = []
        edges = []

        for step_id, step in proof.steps.items():
            is_root = (step_id == proof.root_id)
            is_premise = len(step.premise_ids) == 0

            # Color coding logic
            if is_root:
                color = {"background": "#ffebee", "border": "#d32f2f"}
                shape = "diamond"
            elif is_premise:
                color = {"background": "#e3f2fd", "border": "#1976d2"}
                shape = "box"
            else:
                color = {"background": "#e8f5e9", "border": "#388e3c"}
                shape = "ellipse"

            formula_str = str(step.conclusion)
            rule_str = step.rule.value if hasattr(step.rule, "value") else str(step.rule)
            
            tooltip = (
                f"<b>ID:</b> {html.escape(step_id)}<br/>"
                f"<b>Rule:</b> {html.escape(rule_str)}<br/>"
                f"<b>Formula:</b> {html.escape(formula_str)}"
            )

            nodes.append({
                "id": step_id,
                "label": f"{step_id}\n{rule_str}",
                "title": tooltip,
                "color": color,
                "shape": shape,
                "font": {"multi": "md"}
            })

            for p_id in step.premise_ids:
                edges.append({
                    "from": p_id,
                    "to": step_id,
                    "arrows": "to",
                    "color": {"color": "#757575"}
                })

        options = {
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "UD",
                    "sortMethod": "directed"
                }
            },
            "physics": {"enabled": False},
            "nodes": {"margin": 10},
            "edges": {"smooth": True}
        }

        html_content = self._generate_html(
            title=page_title,
            nodes_json=json.dumps(nodes, indent=2),
            edges_json=json.dumps(edges, indent=2),
            vis_options_json=json.dumps(options, indent=2)
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def export_dependency_network_to_html(
        self,
        graph: DependencyGraph,
        output_path: str,
        title: Optional[str] = None
    ) -> None:
        """
        Renders a theorem dependency network (DependencyGraph) into an interactive HTML visualization.

        Args:
            graph: Target DependencyGraph instance.
            output_path: Output disk path for the .html file.
            title: Optional title header for the page.
        """
        page_title = title or "Theorem Dependency Network"
        nodes = []
        edges = []

        graph_dict = graph.to_dict() if hasattr(graph, "to_dict") else {}
        nodes_raw = graph_dict.get("nodes", {})
        edges_raw = graph_dict.get("edges", [])

        for node_id, formula_data in nodes_raw.items():
            formula_str = str(formula_data)
            color = {"background": "#e8f5e9", "border": "#2e7d32"}

            tooltip = (
                f"<b>Theorem:</b> {html.escape(node_id)}<br/>"
                f"<b>Formula:</b> {html.escape(formula_str)}"
            )

            nodes.append({
                "id": node_id,
                "label": node_id,
                "title": tooltip,
                "color": color,
                "shape": "box"
            })

        for edge in edges_raw:
            src, tgt, rel = edge[0], edge[1], edge[2] if len(edge) > 2 else "implies"
            is_equiv = (rel == "equivalent")

            edges.append({
                "from": src,
                "to": tgt,
                "arrows": "to",
                "label": rel,
                "dashes": is_equiv,
                "color": {"color": "#1565c0" if is_equiv else "#424242"}
            })

        options = {
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -3000,
                    "centralGravity": 0.3,
                    "springLength": 95
                }
            },
            "edges": {"smooth": {"type": "continuous"}}
        }

        html_content = self._generate_html(
            title=page_title,
            nodes_json=json.dumps(nodes, indent=2),
            edges_json=json.dumps(edges, indent=2),
            vis_options_json=json.dumps(options, indent=2)
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_html(
        self,
        title: str,
        nodes_json: str,
        edges_json: str,
        vis_options_json: str
    ) -> str:
        """Generates self-contained HTML file template with embedded JavaScript and CSS."""
        bg_color = "#121212" if self.theme == "dark" else "#ffffff"
        text_color = "#ffffff" if self.theme == "dark" else "#333333"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(title)}</title>
  <script type="text/javascript" src="{self.VIS_JS_CDN}"></script>
  <style type="text/css">
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background-color: {bg_color};
      color: {text_color};
    }}
    #header {{
      padding: 12px 20px;
      background: #1976d2;
      color: white;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    #header h2 {{ margin: 0; font-size: 1.2rem; }}
    #controls {{ display: flex; gap: 10px; }}
    input[type="text"] {{
      padding: 6px 10px;
      border-radius: 4px;
      border: 1px solid #ccc;
    }}
    #mynetwork {{
      width: 100vw;
      height: calc(100vh - 60px);
      border: none;
    }}
  </style>
</head>
<body>
  <div id="header">
    <h2>{html.escape(title)}</h2>
    <div id="controls">
      <input type="text" id="searchInput" placeholder="Search node or formula..." onkeyup="searchNodes()">
    </div>
  </div>
  <div id="mynetwork"></div>

  <script type="text/javascript">
    const nodes = new vis.DataSet({nodes_json});
    const edges = new vis.DataSet({edges_json});
    const container = document.getElementById('mynetwork');
    const data = {{ nodes: nodes, edges: edges }};
    const options = {vis_options_json};
    const network = new vis.Network(container, data, options);

    function searchNodes() {{
      const query = document.getElementById('searchInput').value.toLowerCase();
      if (!query) {{
        nodes.forEach(n => nodes.update({{ id: n.id, hidden: false }}));
        return;
      }}
      nodes.forEach(n => {{
        const match = n.id.toLowerCase().includes(query) || (n.title && n.title.toLowerCase().includes(query));
        nodes.update({{ id: n.id, hidden: !match }});
      }});
    }}
  </script>
</body>
</html>
"""
```

---

### 4.4 CLI Updates in `solver/__main__.py` (Section 3.20)

Add the `export` command family with subcommands `lean` and `graph` to `solver/__main__.py`.

```python
# argparse setup additions in solver/__main__.py:

export_parser = subparsers.add_parser("export", help="Export theorems and proofs to LEAN 4 or HTML graphs.")
export_subparsers = export_parser.add_subparsers(dest="export_type", required=True)

# Command: python -m solver export lean --output FILE [--theorems T1 T2 ...] [--stubs-only]
lean_parser = export_subparsers.add_parser("lean", help="Export to LEAN 4 formal proof file.")
lean_parser.add_argument("--output", "-o", required=True, help="Output .lean file path.")
lean_parser.add_argument("--theorems", nargs="*", help="Specific theorem names to export.")
lean_parser.add_argument("--stubs-only", action="store_true", help="Export theorem stubs with sorry placeholders.")
lean_parser.add_argument("--db-path", help="Path to SQLite database.")

# Command: python -m solver export graph --output FILE --type {proof|dependency} [--theorem NAME]
graph_parser = export_subparsers.add_parser("graph", help="Export proof or dependency graph to interactive HTML.")
graph_parser.add_argument("--output", "-o", required=True, help="Output .html file path.")
graph_parser.add_argument("--type", choices=["proof", "dependency"], required=True, help="Graph type to render.")
graph_parser.add_argument("--theorem", help="Theorem name for proof graph export.")
graph_parser.add_argument("--db-path", help="Path to SQLite database.")
```

---

## 5. Step-by-Step Implementation Order

1. **Step 1 — LEAN Exporter Package Setup (`solver/exporters/__init__.py`)**:
   - Create package init file and define `__all__`.

2. **Step 2 — LEAN Exporter (`solver/exporters/lean_exporter.py`)**:
   - Implement `export_sort()` for `PrimitiveSort`, `ParameterizedSort`, `FunctionSort`.
   - Implement `export_term()` for `Variable`, `Constant`, `FunctionApp`.
   - Implement Tier 1 `export_formula()` for all `Formula` AST nodes.
   - Implement Tier 2 `export_theorem_statement()` with hypothesis parameters and `sorry` stubs.
   - Implement Tier 3 `export_proof()` converting `ProofDAG` topological step sequences into LEAN 4 `have` assertions and Mathlib tactics (`simp`, `aesop`, `exact`, `rfl`, `trans`, `symm`).
   - Implement `export_file()` for batch generation of `.lean` source files.

3. **Step 3 — HTML Graph Exporter (`solver/exporters/graph_exporter.py`)**:
   - Implement `_generate_html()` template builder with responsive CSS, search controls, and vis.js dataset setup.
   - Implement `export_proof_to_html()` rendering hierarchical proof DAGs.
   - Implement `export_dependency_network_to_html()` rendering force-directed dependency graphs.

4. **Step 4 — CLI Integration (`solver/__main__.py`)**:
   - Connect `export lean` and `export graph` subcommands to `LeanExporter` and `GraphExporter`.

5. **Step 5 — Unit and Integration Test Suite (`tests/test_exporters.py`)**:
   - Add comprehensive tests for sort, term, formula, theorem statement, tactic proof, HTML output, and CLI commands.

---

## 6. Testing Requirements

### 6.1 LEAN 4 Exporter Unit & Integration Tests
- **Sort Export**: Verify `Nat` $\to$ `ℕ`, `Ind` $\to$ `α`, `Set(Nat)` $\to$ `Set ℕ`, `FunctionSort` $\to$ `A → B`.
- **Formula AST Export**:
  - Predicates: `P(x, y)` $\to$ `(P x y)`.
  - Binary relations: `x < y` $\to$ `(x < y)`.
  - Connectives: `P ∧ Q`, `P ∨ Q`, `P → Q`, `P ↔ Q`, `¬ P`.
  - Quantifiers: `∀ (x : ℕ), P x`, `∃ (y : α), Q y`.
- **Theorem Statements**: Verify generated `theorem thm_name (h1 : P) : Q := by\n sorry` syntax.
- **Proof DAG Tactic Translation**:
  - Modus Ponens step $\to$ `h1 h2`.
  - And Intro step $\to$ `⟨h1, h2⟩`.
  - Instantiation step $\to$ `h1 t`.
  - Paramodulation step $\to$ `by simp [h1]`.
  - Root step $\to$ `exact step_id`.
- **File Export**: Verify complete file output including `import Mathlib.Tactic`, universe declarations, and namespace boundaries. Verify `--stubs-only` forces `sorry` stubs.

### 6.2 Graph Exporter Unit Tests
- **HTML Validity**: Verify output contains `<!DOCTYPE html>`, `<script src="...">`, `<div id="mynetwork">`.
- **Proof Graph Data**: Verify `nodes` JSON array contains step IDs, formatted formulas, and rule colors. Verify `edges` JSON array contains directed premise links.
- **Dependency Network Data**: Verify nodes match `DependencyGraph` formulas and edges reflect relationship attributes (`implies`, `equivalent`).

---

## 7. Acceptance Criteria

1. **Parseable LEAN Formula Syntax**:
   - `export_formula()` produces valid LEAN 4 string expressions for all AST nodes without syntax errors or unescaped symbols.
2. **Syntactically Valid Theorem Statements**:
   - `export_theorem_statement()` generates properly formatted LEAN 4 theorem headers with hypothesis types and `sorry` stubs.
3. **Mathlib Tactic Proof Export**:
   - `export_proof()` translates `ProofDAG` objects into structured `by` tactic blocks using standard Mathlib tactics (`simp`, `aesop`, `exact`, `have`, `apply`).
4. **Stubs-Only Mode**:
   - Passing `--stubs-only` to `export_file()` or the CLI outputs theorem stubs with `sorry` placeholders for all theorems.
5. **Interactive HTML Visualizations**:
   - `export_proof_to_html()` and `export_dependency_network_to_html()` produce valid, self-contained HTML files with embedded JSON datasets that open and render correctly in standard web browsers.
6. **CLI Integration**:
   - `python -m solver export lean --output out.lean` and `python -m solver export graph --output out.html --type proof` execute cleanly from the CLI.
7. **Test Coverage**:
   - All tests in `tests/test_exporters.py` pass with high coverage.

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| Complex nested formulas producing invalid LEAN operator precedence | High | Wrap non-atomic subformulas in explicit parentheses `(...)` during formula export |
| Invalid LEAN identifiers (e.g. spaces, reserved keywords, hyphens) | Medium | Pass all theorem and variable names through `_sanitize_identifier()` regex sanitizer |
| Proof DAG topological order cycles or missing steps | High | Validate DAG structure with `proof.is_valid()` before invoking `export_proof()` |
| vis.js CDN unavailability in offline test environments | Low | Unit tests verify embedded HTML string and JSON structures without launching headless browser renders |
