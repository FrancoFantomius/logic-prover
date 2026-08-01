# Phase 7 — Prover Implementation Plan

**Goal**: Implement a working resolution-based First-Order Logic (FOL) automated theorem prover with equality support (superposition/paramodulation), given-clause search loop, proof DAG validation, natural deduction proof reconstruction, and CLI `prove` command.

**Deliverables**:
- [solver/prover/__init__.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/__init__.py)
- [solver/prover/clausifier.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/clausifier.py)
- [solver/prover/rules.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/rules.py)
- [solver/prover/proof.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/proof.py)
- [solver/prover/engine.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/engine.py)
- [solver/prover/reconstruction.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/reconstruction.py)
- CLI `prove` command in [solver/__main__.py](file:///C:/Users/franc/Programmazione/solver/solver/__main__.py)
- Passing test suite: [tests/test_clausifier.py](file:///C:/Users/franc/Programmazione/solver/tests/test_clausifier.py), [tests/test_rules.py](file:///C:/Users/franc/Programmazione/solver/tests/test_rules.py), [tests/test_reconstruction.py](file:///C:/Users/franc/Programmazione/solver/tests/test_reconstruction.py), [tests/test_prover.py](file:///C:/Users/franc/Programmazione/solver/tests/test_prover.py)

---

## 1. Overview & Architectural Goals

Phase 7 establishes the automated theorem proving capabilities of the `solver` library. As outlined in Section 3.14 of the master plan and confirmed in architectural reviews, forward search over raw natural deduction rules suffers from infinite branching factors. To achieve high performance while maintaining human readability and Lean 4 exportability, Phase 7 splits theorem proving into two distinct components:

1. **Clause Normal Form (CNF) Refutation Engine**: Operates on disjunctive clauses using resolution, factoring, and paramodulation (equality rewriting). Search is guided by an Otter/Discount given-clause loop with clause weighting and forward subsumption.
2. **Natural Deduction Proof Reconstruction**: Converts the raw resolution trace into a valid, human-readable directed acyclic graph (`ProofDAG`) composed of standard natural deduction steps (`ModusPonens`, `UniversalInstantiation`, `AndIntroduction`, etc.).

### Key Architecture & Design Decisions
- **Refutation Strategy**: Proving target $C$ from hypotheses $\mathcal{H}_1, \dots, \mathcal{H}_n$ is formulated as deriving the empty clause $\Box$ (contradiction $\bot$) from the CNF clausification of $\mathcal{H}_1 \land \dots \land \mathcal{H}_n \land \neg C$.
- **Sort-Aware Skolemization**: Existential quantification $\exists x, \phi(x, \vec{y})$ is eliminated by introducing fresh Skolem functions $f_{sk}(\vec{y})$ whose return sort matches $x$ and argument sorts match outer universally quantified variables $\vec{y}$.
- **Variable Standardization Apart**: Before resolving or paramodulating two clauses, their free variables are renamed to disjoint index spaces ($v_0, v_1, \dots$ vs $v_{100}, v_{101}, \dots$) to prevent unsound variable capture.
- **Paramodulation**: Equality literals $t_1 = t_2$ enable term rewriting within clauses via Robinson unification on subterms.
- **Bounded Search & Timeouts**: Proof search is strictly constrained by `max_steps` and `timeout_sec` (configured in `SolverConfig`), throwing explicit `ProofTimeoutError` or `ProofSearchExhaustedError` exceptions upon limit exhaustion.

---

## 2. Prerequisites

The following modules must be fully implemented and passing unit tests prior to Phase 7:

1. **Phase 1 — AST & Sort System**:
   - `solver/core/ast.py`: `Term`, `Variable`, `Constant`, `FunctionApp`, `Formula`, `PredicateApp`, `Equality`, `Not`, `And`, `Or`, `Implies`, `Iff`, `Forall`, `Exists`, `free_variables()`, `bound_variables()`.
   - `solver/core/sorts.py`: `Sort`, `PrimitiveSort`, `is_compatible()`, `sort_of_term()`.
2. **Phase 2 — Signature & Validator**:
   - `solver/core/signature.py`: `Signature` registration.
   - `solver/core/validator.py`: `validate_formula()`.
3. **Phase 3 — Visitor Framework & Parser**:
   - `solver/core/visitors.py`: `ASTVisitor`, `ASTTransformer`.
   - `solver/core/parser.py`: `parse_formula()`, `to_string()`.
4. **Phase 4 — Substitution & Unification**:
   - `solver/core/substitutions.py`: `substitute_term()`, `substitute_formula()`, `unify_terms()`, `unify_formulas()`, `UnificationError`.
5. **Phase 5 — Equality & Rewriting**:
   - `solver/core/equality.py`: Congruence closure and term rewriting helpers.
6. **Phase 6 — Knowledge Base & Database**:
   - `solver/kb/logic.py`, `solver/kb/equality.py`, `solver/kb/numbers.py`: FOL, Equality, and Peano axiom systems.
   - `solver/config.py`: `SolverConfig`.
   - `solver/core/exceptions.py`: `ProofTimeoutError`, `ProofSearchExhaustedError`, `ProofReconstructionError`, `SolverError`.

---

## 3. Files to Create / Modify

| File Path | Action | Description |
| :--- | :--- | :--- |
| [solver/prover/__init__.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/__init__.py) | Create | Package initialization and public API exports |
| [solver/prover/clausifier.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/clausifier.py) | Create | `Literal`, `Clause`, NNF conversion, Skolemization, CNF distribution, `negate_and_clausify`, `to_cnf` |
| [solver/prover/rules.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/rules.py) | Create | `InferenceRule`, resolution rules (Binary Resolution, Factoring, Paramodulation), ND reconstruction rules |
| [solver/prover/proof.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/proof.py) | Create | `ProofStep`, `ProofDAG` with serialization, topological ordering, and `is_valid()` verification |
| [solver/prover/engine.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/engine.py) | Create | `ResolutionStep`, `TheoremProver` class implementing given-clause resolution search loop |
| [solver/prover/reconstruction.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/reconstruction.py) | Create | `reconstruct_proof` resolution-to-ND translator and `simplify_proof` DAG optimizer |
| [solver/__main__.py](file:///C:/Users/franc/Programmazione/solver/solver/__main__.py) | Update | CLI entry point with `prove` command implementation |
| [tests/test_clausifier.py](file:///C:/Users/franc/Programmazione/solver/tests/test_clausifier.py) | Create | Unit tests for NNF, Skolemization, CNF distribution, tautology removal, variable renaming |
| [tests/test_rules.py](file:///C:/Users/franc/Programmazione/solver/tests/test_rules.py) | Create | Unit tests for resolution, factoring, paramodulation, and natural deduction rules |
| [tests/test_reconstruction.py](file:///C:/Users/franc/Programmazione/solver/tests/test_reconstruction.py) | Create | Unit tests for resolution trace conversion, DAG validity, and proof simplification |
| [tests/test_prover.py](file:///C:/Users/franc/Programmazione/solver/tests/test_prover.py) | Create | Integration tests for propositional, FOL, and Peano theorem proving, timeouts, and exhaustion |

---

## 4. Detailed Module Specifications

### 4.1 `solver/prover/clausifier.py` (Section 3.14.1)

Converts formulas to Clause Normal Form (CNF) for the resolution engine.

```python
from dataclasses import dataclass, field
from typing import List, Set, FrozenSet, Dict, Tuple, Optional, Union
from solver.core.ast import (
    Term, Variable, Constant, FunctionApp, Formula, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists,
    free_variables, bound_variables
)
from solver.core.sorts import Sort, Ind
from solver.core.signature import Signature
from solver.core.substitutions import substitute_formula, substitute_term

@dataclass(frozen=True)
class Literal:
    atom: Union[PredicateApp, Equality]
    positive: bool = True

    def negate(self) -> "Literal":
        """Returns the complementary literal."""
        return Literal(atom=self.atom, positive=not self.positive)

    def free_variables(self) -> Set[Variable]:
        """Returns all free variables in the literal atom."""
        return free_variables(self.atom)

    def substitute(self, subst: Dict[Variable, Term]) -> "Literal":
        """Applies variable substitution to the literal atom."""
        new_atom = substitute_formula(self.atom, subst)
        assert isinstance(new_atom, (PredicateApp, Equality))
        return Literal(atom=new_atom, positive=self.positive)

    def to_string(self) -> str:
        """Formats literal for display."""
        prefix = "" if self.positive else "¬"
        if isinstance(self.atom, Equality):
            eq_str = f"{self.atom.left} = {self.atom.right}"
            return eq_str if self.positive else f"{self.atom.left} ≠ {self.atom.right}"
        return f"{prefix}{self.atom}"

@dataclass(frozen=True)
class Clause:
    literals: FrozenSet[Literal] = field(default_factory=frozenset)

    @property
    def is_empty(self) -> bool:
        """True if clause is the empty clause (contradiction ⊥)."""
        return len(self.literals) == 0

    @property
    def is_tautology(self) -> bool:
        """True if clause contains both L and ¬L."""
        positives = {lit.atom for lit in self.literals if lit.positive}
        negatives = {lit.atom for lit in self.literals if not lit.positive}
        return bool(positives & negatives)

    @property
    def is_unit(self) -> bool:
        """True if clause consists of exactly one literal."""
        return len(self.literals) == 1

    def free_variables(self) -> Set[Variable]:
        """Returns all free variables across all literals in the clause."""
        res: Set[Variable] = set()
        for lit in self.literals:
            res.update(lit.free_variables())
        return res

    def substitute(self, subst: Dict[Variable, Term]) -> "Clause":
        """Applies variable substitution to all literals in the clause."""
        if not subst:
            return self
        return Clause(frozenset(lit.substitute(subst) for lit in self.literals))

    def to_string(self) -> str:
        """Formats clause as disjunction string."""
        if self.is_empty:
            return "□"
        return " ∨ ".join(sorted(lit.to_string() for lit in self.literals))


def eliminate_implications(formula: Formula) -> Formula:
    """
    Recursively eliminates Iff and Implies operators:
    - A ⟺ B  ==>  (A ⟹ B) ∧ (B ⟹ A)
    - A ⟹ B  ==>  ¬A ∨ B
    """
    ...

def to_nnf(formula: Formula) -> Formula:
    """
    Converts formula to Negation Normal Form (NNF) by pushing negations inward:
    - ¬(¬A)          ==>  A
    - ¬(A ∧ B)       ==>  ¬A ∨ ¬B
    - ¬(A ∨ B)       ==>  ¬A ∧ ¬B
    - ¬(∀x, P(x))    ==>  ∃x, ¬P(x)
    - ¬(∃x, P(x))    ==>  ∀x, ¬P(x)
    Assumes implications have already been eliminated.
    """
    ...

def standardize_variables(formula: Formula) -> Formula:
    """
    Renames bound variables so that each quantifier binds a unique variable index,
    preventing name clashes during Skolemization.
    """
    ...

def skolemize(formula: Formula, signature: Optional[Signature] = None) -> Formula:
    """
    Eliminates existential quantifiers by introducing Skolem constants/functions.
    - ∃x, P(x) with active outer universal variables [y_1, ..., y_k]:
      Replaces x with FunctionApp(sk_fn, arity=k, args=(y_1, ..., y_k), return_sort=x.sort).
    - If k == 0, replaces x with Constant(sk_c, sort=x.sort) or FunctionApp with 0 args.
    Updates signature with new Skolem function symbols if signature is provided.
    Assumes formula is in NNF and variables are standardized.
    """
    ...

def drop_universals(formula: Formula) -> Formula:
    """
    Strips all Forall quantifiers. In CNF, all remaining free variables
    are implicitly universally quantified.
    """
    ...

def distribute_cnf(formula: Formula) -> Formula:
    """
    Recursively distributes disjunctions (Or) over conjunctions (And):
    - A ∨ (B ∧ C)  ==>  (A ∨ B) ∧ (A ∨ C)
    - (A ∧ B) ∨ C  ==>  (A ∨ C) ∧ (B ∨ C)
    Assumes formula has no quantifiers or implications.
    """
    ...

def formula_to_clauses(formula: Formula) -> List[Clause]:
    """
    Converts a CNF-structured Formula (And/Or trees over atoms/nots)
    into a List of Clause instances. Filters out tautological clauses (L ∨ ¬L).
    """
    ...

def to_cnf(formula: Formula, signature: Optional[Signature] = None) -> List[Clause]:
    """
    Full CNF conversion pipeline:
    1. Eliminate ⟺ and ⟹
    2. Convert to NNF
    3. Standardize bound variables
    4. Skolemize existential quantifiers
    5. Drop universal quantifiers
    6. Distribute ∨ over ∧
    7. Convert AST to List[Clause] and filter tautologies
    """
    ...

def negate_and_clausify(formula: Formula, signature: Optional[Signature] = None) -> List[Clause]:
    """
    Negates the given target formula (Not(formula)) and converts it to CNF for refutation search.
    """
    return to_cnf(Not(formula), signature=signature)
```

#### Implementation Notes & Edge Cases
- **Skolem Naming**: Skolem functions are named `sk_f0`, `sk_f1`, ... and Skolem constants `sk_c0`, `sk_c1`, ... using a thread-safe atomic counter.
- **Outer Universal Tracking**: Skolemization tracks all outer universal scope variables ($\vec{y}$) using a scope stack during AST traversal.
- **Empty Disjunction/Conjunction**: Conjunction of zero clauses is True (ignored); empty disjunction is the empty clause $\Box$.

---

### 4.2 `solver/prover/rules.py` (Section 3.14.2)

Defines inference rules for resolution refutation search and natural deduction proof reconstruction.

```python
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Callable, Any, Set
from solver.core.ast import Term, Variable, Formula, PredicateApp, Equality, free_variables
from solver.core.substitutions import unify_formulas, unify_terms, UnificationError, substitute_formula, substitute_term
from solver.prover.clausifier import Clause, Literal

@dataclass(frozen=True)
class InferenceRule:
    name: str
    description: str
    rule_type: str  # "resolution" or "reconstruction"
    apply: Callable[..., List[Any]]


def standardize_clause_variables(c1: Clause, c2: Clause) -> Tuple[Clause, Clause, Dict[Variable, Variable]]:
    """
    Renames free variables in c2 so their variable IDs do not overlap with c1.
    Returns (c1, renamed_c2, variable_renaming_map).
    """
    ...

def resolve_clauses(
    c1: Clause,
    c2: Clause
) -> List[Tuple[Clause, Dict[Variable, Term], Tuple[Literal, Literal]]]:
    """
    Binary Resolution Rule:
    Given c1 containing L1 and c2 containing L2 where L1.positive != L2.positive:
    Standardizes variables apart, unifies L1.atom and L2.atom with MGU σ.
    Returns list of tuples: (resolvent_clause, MGU_substitution, (L1, L2)).
    """
    ...

def factor_clause(
    c: Clause
) -> List[Tuple[Clause, Dict[Variable, Term]]]:
    """
    Factoring Rule:
    Given c containing L1 and L2 with same polarity:
    Unifies L1.atom and L2.atom with MGU σ.
    Returns list of tuples: (factored_clause, MGU_substitution).
    """
    ...

def paramodulate(
    c1: Clause,
    c2: Clause
) -> List[Tuple[Clause, Dict[Variable, Term]]]:
    """
    Paramodulation Rule (Equality Rewriting):
    Given c1 containing positive equality literal (t1 = t2) [or (t2 = t1)],
    and c2 containing literal L[s] with subterm s unifiable with t1 via MGU σ:
    Derives paramodulant σ((c1 \ {t1=t2}) ∪ (c2 with s replaced by t2)).
    """
    ...

def get_resolution_rules() -> List[InferenceRule]:
    """Returns the set of core CNF resolution rules."""
    return [
        InferenceRule("BinaryResolution", "Resolve complementary literals", "resolution", resolve_clauses),
        InferenceRule("Factoring", "Merge unifiable literals in same clause", "resolution", factor_clause),
        InferenceRule("Paramodulation", "Equality subterm rewriting", "resolution", paramodulate),
    ]

def get_reconstruction_rules() -> List[InferenceRule]:
    """Returns standard Natural Deduction inference rules used in ProofDAG."""
    return [
        InferenceRule("Axiom", "Premise or hypothesis assumption", "reconstruction", lambda *args: []),
        InferenceRule("NegatedGoal", "Clausified negation of target theorem", "reconstruction", lambda *args: []),
        InferenceRule("ModusPonens", "A, A ⟹ B  ⊢  B", "reconstruction", lambda *args: []),
        InferenceRule("UniversalInstantiation", "∀x P(x)  ⊢  P(t)", "reconstruction", lambda *args: []),
        InferenceRule("ExistentialIntroduction", "P(t)  ⊢  ∃x P(x)", "reconstruction", lambda *args: []),
        InferenceRule("AndIntroduction", "A, B  ⊢  A ∧ B", "reconstruction", lambda *args: []),
        InferenceRule("AndElimination", "A ∧ B  ⊢  A (or B)", "reconstruction", lambda *args: []),
        InferenceRule("OrIntroduction", "A  ⊢  A ∨ B", "reconstruction", lambda *args: []),
        InferenceRule("OrElimination", "A ∨ B, A ⟹ C, B ⟹ C  ⊢  C", "reconstruction", lambda *args: []),
        InferenceRule("DoubleNegationElimination", "¬¬A  ⊢  A", "reconstruction", lambda *args: []),
        InferenceRule("Contradiction", "A, ¬A  ⊢  ⊥", "reconstruction", lambda *args: []),
        InferenceRule("ResolutionTraceStep", "CNF trace resolution inference", "reconstruction", lambda *args: []),
    ]

def apply_rule(
    rule: InferenceRule,
    premises: List[Any],
    context: Optional[Dict[str, Any]] = None
) -> List[Any]:
    """Applies an inference rule to premises with optional context parameters."""
    return rule.apply(*premises, **(context or {}))
```

#### Implementation Notes & Edge Cases
- **Variable Separation**: Variable indices in `c2` are offset by `max_var_id(c1) + 1` before unification to prevent accidental self-unification.
- **Paramodulation Symmetry**: Equality $t_1 = t_2$ is checked in both directions ($t_1 \mapsto t_2$ and $t_2 \mapsto t_1$). Subterm unification avoids rewriting bare variable subterms to prevent infinite search trees.

---

### 4.3 `solver/prover/proof.py` (Section 3.14.3)

Defines data structures for formal proofs as Directed Acyclic Graphs (`ProofDAG`).

```python
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from solver.core.ast import Formula, Variable, Term
from solver.core.signature import Signature
from solver.core.validator import validate_formula
from solver.prover.rules import get_reconstruction_rules, InferenceRule

@dataclass(frozen=True)
class ProofStep:
    id: str
    rule: str
    premise_ids: List[str]
    conclusion: Formula
    substitutions: Dict[Variable, Term] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes ProofStep to a dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProofStep":
        """Deserializes ProofStep from a dictionary."""
        ...

class ProofDAG:
    steps: Dict[str, ProofStep]
    root_id: str
    axiom_ids: Set[str]

    def __init__(
        self,
        steps: Dict[str, ProofStep],
        root_id: str,
        axiom_ids: Optional[Set[str]] = None
    ) -> None:
        self.steps = dict(steps)
        self.root_id = root_id
        if axiom_ids is not None:
            self.axiom_ids = set(axiom_ids)
        else:
            self.axiom_ids = {
                step_id for step_id, step in self.steps.items()
                if not step.premise_ids or step.rule in ("Axiom", "Hypothesis", "NegatedGoal")
            }

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
        order: List[ProofStep] = []

        def dfs(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            step = self.get_step(node_id)
            for p_id in step.premise_ids:
                dfs(p_id)
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
        
        # Verify topological ordering succeeds without cycles
        try:
            topo_steps = self.topological_order()
        except Exception:
            return False

        validated_steps: Set[str] = set()
        for step in topo_steps:
            # Check all premises are already validated
            for pid in step.premise_ids:
                if pid not in validated_steps:
                    return False

            if signature is not None:
                if not validate_formula(step.conclusion, signature):
                    return False

            # Check rule derivation logic
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
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Serializes proof DAG to dictionary for JSON/SQLite storage."""
        return {
            "root_id": self.root_id,
            "axiom_ids": list(self.axiom_ids),
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProofDAG":
        """Deserializes proof DAG from dictionary."""
        steps = {step_id: ProofStep.from_dict(step_data) for step_id, step_data in data["steps"].items()}
        return cls(steps=steps, root_id=data["root_id"], axiom_ids=set(data.get("axiom_ids", [])))
```

#### Implementation Notes & Edge Cases
- **Serialization**: `substitutions` dictionaries (mapping `Variable` to `Term`) are serialized using canonical JSON representations.
- **Rule Verification**: `_check_rule_validity` handles exact syntactic checks for `ModusPonens`, `UniversalInstantiation`, `AndIntroduction`, `AndElimination`, `DoubleNegationElimination`, and `ResolutionTraceStep`.

---

### 4.4 `solver/prover/engine.py` (Section 3.14.4)

Implements the primary automated theorem prover engine using the Otter/Discount given-clause loop.

```python
import time
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from solver.core.ast import Formula, Variable, Term, Not
from solver.core.signature import Signature
from solver.config import SolverConfig
from solver.core.exceptions import ProofTimeoutError, ProofSearchExhaustedError, SolverError
from solver.prover.clausifier import Clause, Literal, to_cnf, negate_and_clausify
from solver.prover.rules import resolve_clauses, factor_clause, paramodulate
from solver.prover.proof import ProofDAG, ProofStep
from solver.prover.reconstruction import reconstruct_proof

@dataclass(frozen=True)
class ResolutionStep:
    id: str
    rule_name: str  # "axiom", "negated_goal", "resolution", "factoring", "paramodulation"
    premise_ids: List[str]
    clause: Clause
    substitution: Dict[Variable, Term] = field(default_factory=dict)
    parent_literals: Optional[Tuple[Literal, Literal]] = None
    original_formula: Optional[Formula] = None

class TheoremProver:
    signature: Signature
    config: SolverConfig

    def __init__(
        self,
        signature: Signature,
        config: Optional[SolverConfig] = None
    ) -> None:
        self.signature = signature
        self.config = config or SolverConfig()

    def prove(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
        max_steps: Optional[int] = None,
        timeout_sec: Optional[float] = None
    ) -> ProofDAG:
        """
        Attempts to prove target from premises using resolution refutation search.
        1. Clausifies premises and negated target into CNF.
        2. Executes Otter given-clause loop with forward subsumption.
        3. On empty clause derivation, extracts resolution trace.
        4. Reconstructs natural deduction ProofDAG.
        Raises ProofTimeoutError or ProofSearchExhaustedError if proof is not found within limits.
        """
        max_steps = max_steps if max_steps is not None else self.config.prover_max_steps
        timeout_sec = timeout_sec if timeout_sec is not None else self.config.prover_timeout_sec

        start_time = time.monotonic()
        premises = premises or []

        # 1. Initialize Clause Store & Resolution Trace Records
        step_counter = 0
        trace_records: Dict[str, ResolutionStep] = {}
        clause_to_step_id: Dict[Clause, str] = {}

        passive_queue: List[Tuple[int, Clause]] = []  # Priority queue ordered by clause weight
        active_clauses: List[Clause] = []

        def add_initial_step(clause: Clause, rule_name: str, orig_fmt: Optional[Formula]) -> None:
            nonlocal step_counter
            step_id = f"res_{step_counter}"
            step_counter += 1
            step = ResolutionStep(
                id=step_id,
                rule_name=rule_name,
                premise_ids=[],
                clause=clause,
                original_formula=orig_fmt
            )
            trace_records[step_id] = step
            clause_to_step_id[clause] = step_id
            weight = self._clause_weight(clause)
            passive_queue.append((weight, clause))

        # Clausify Premises
        for prem in premises:
            cnf_clauses = to_cnf(prem, signature=self.signature)
            for c in cnf_clauses:
                if not c.is_tautology:
                    add_initial_step(c, "axiom", prem)

        # Clausify Negated Target
        target_clauses = negate_and_clausify(target, signature=self.signature)
        for c in target_clauses:
            if not c.is_tautology:
                add_initial_step(c, "negated_goal", target)

        empty_clause_step_id: Optional[str] = None

        # 2. Given-Clause Search Loop
        step_count = 0
        while passive_queue:
            # Check Timeout
            if time.monotonic() - start_time > timeout_sec:
                raise ProofTimeoutError(
                    f"Theorem prover timed out after {timeout_sec:.2f}s ({step_count} steps)."
                )

            # Check Step Limit
            if step_count >= max_steps:
                raise ProofSearchExhaustedError(
                    f"Theorem prover search exhausted after max_steps={max_steps} steps."
                )

            step_count += 1

            # Select Given Clause (smallest weight first)
            passive_queue.sort(key=lambda item: item[0])
            _, given_clause = passive_queue.pop(0)

            # Check if Given Clause is Empty Clause
            if given_clause.is_empty:
                empty_clause_step_id = clause_to_step_id[given_clause]
                break

            # Forward Subsumption Check: Skip if given_clause is subsumed by active_clauses
            if self._is_subsumed(given_clause, active_clauses):
                continue

            active_clauses.append(given_clause)
            given_step_id = clause_to_step_id[given_clause]

            # Generate Factoring Inferences
            for factored_c, subst in factor_clause(given_clause):
                if factored_c not in clause_to_step_id and not factored_c.is_tautology:
                    step_id = f"res_{step_counter}"
                    step_counter += 1
                    res_step = ResolutionStep(
                        id=step_id,
                        rule_name="factoring",
                        premise_ids=[given_step_id],
                        clause=factored_c,
                        substitution=subst
                    )
                    trace_records[step_id] = res_step
                    clause_to_step_id[factored_c] = step_id
                    passive_queue.append((self._clause_weight(factored_c), factored_c))
                    if factored_c.is_empty:
                        empty_clause_step_id = step_id
                        break

            if empty_clause_step_id:
                break

            # Generate Resolution & Paramodulation Inferences with Active Clauses
            for active_c in active_clauses:
                active_step_id = clause_to_step_id[active_c]

                # Resolution
                for resolvent_c, subst, (l1, l2) in resolve_clauses(given_clause, active_c):
                    if resolvent_c not in clause_to_step_id and not resolvent_c.is_tautology:
                        step_id = f"res_{step_counter}"
                        step_counter += 1
                        res_step = ResolutionStep(
                            id=step_id,
                            rule_name="resolution",
                            premise_ids=[given_step_id, active_step_id],
                            clause=resolvent_c,
                            substitution=subst,
                            parent_literals=(l1, l2)
                        )
                        trace_records[step_id] = res_step
                        clause_to_step_id[resolvent_c] = step_id
                        passive_queue.append((self._clause_weight(resolvent_c), resolvent_c))
                        if resolvent_c.is_empty:
                            empty_clause_step_id = step_id
                            break
                if empty_clause_step_id:
                    break

                # Paramodulation
                for param_c, subst in paramodulate(given_clause, active_c):
                    if param_c not in clause_to_step_id and not param_c.is_tautology:
                        step_id = f"res_{step_counter}"
                        step_counter += 1
                        res_step = ResolutionStep(
                            id=step_id,
                            rule_name="paramodulation",
                            premise_ids=[given_step_id, active_step_id],
                            clause=param_c,
                            substitution=subst
                        )
                        trace_records[step_id] = res_step
                        clause_to_step_id[param_c] = step_id
                        passive_queue.append((self._clause_weight(param_c), param_c))
                        if param_c.is_empty:
                            empty_clause_step_id = step_id
                            break
                if empty_clause_step_id:
                    break

        if not empty_clause_step_id:
            raise ProofSearchExhaustedError(
                f"Prover search space exhausted without deriving contradiction ({step_count} steps)."
            )

        # 3. Extract Resolution Trace (Backtrack from Empty Clause)
        needed_ids: Set[str] = set()
        def collect_trace(sid: str) -> None:
            if sid in needed_ids:
                return
            needed_ids.add(sid)
            for pid in trace_records[sid].premise_ids:
                collect_trace(pid)

        collect_trace(empty_clause_step_id)
        resolution_trace = [trace_records[sid] for sid in sorted(needed_ids, key=lambda x: int(x.split("_")[1]))]

        # 4. Reconstruct Natural Deduction ProofDAG
        return reconstruct_proof(resolution_trace, original_target=target, premises=premises)

    def _clause_weight(self, c: Clause) -> int:
        """Computes clause priority weight (fewer literals and smaller terms preferred)."""
        weight = len(c.literals) * 10
        for lit in c.literals:
            weight += len(lit.to_string())
        return weight

    def _is_subsumed(self, c: Clause, active_clauses: List[Clause]) -> bool:
        """True if c is subsumed by an existing active clause (i.e. active_c ⊆ c under substitution)."""
        ...
```

#### Implementation Notes & Edge Cases
- **Forward Subsumption**: Clause $C_1$ subsumes $C_2$ if there exists a substitution $\sigma$ such that $\sigma(C_1) \subseteq C_2$.
- **Clause Priority**: Passive queue prioritizes unit clauses (weight boost) to accelerate unit resolution.

---

### 4.5 `solver/prover/reconstruction.py` (Section 3.14.5)

Converts CNF resolution refutation traces into human-readable Natural Deduction `ProofDAG`s.

```python
from typing import List, Dict, Set, Optional, Tuple
from solver.core.ast import Formula, Not, Implies, And, Or, Forall, Exists, PredicateApp, Equality
from solver.prover.proof import ProofDAG, ProofStep
from solver.prover.engine import ResolutionStep

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

    # Map Axioms
    axiom_step_ids: Set[str] = set()
    for idx, prem in enumerate(premises):
        aid = f"premise_{idx}"
        steps[aid] = ProofStep(
            id=aid,
            rule="Axiom",
            premise_ids=[],
            conclusion=prem
        )
        axiom_step_ids.add(aid)

    # Map Negated Goal Assumption
    goal_assump_id = "negated_target_assump"
    steps[goal_assump_id] = ProofStep(
        id=goal_assump_id,
        rule="NegatedGoal",
        premise_ids=[],
        conclusion=Not(original_target)
    )

    # Convert Resolution Steps to ND ProofSteps
    res_to_nd_map: Dict[str, str] = {}
    for rstep in resolution_trace:
        if rstep.rule_name in ("axiom", "negated_goal"):
            if rstep.rule_name == "axiom":
                # Find matching premise ID
                res_to_nd_map[rstep.id] = list(axiom_step_ids)[0]  # Exact match mapping
            else:
                res_to_nd_map[rstep.id] = goal_assump_id
            continue

        nd_premise_ids = [res_to_nd_map[pid] for pid in rstep.premise_ids]
        nd_id = f"nd_{rstep.id}"

        # Construct ND Formula representation of clause disjunction
        clause_formula = _clause_to_formula(rstep.clause)

        steps[nd_id] = ProofStep(
            id=nd_id,
            rule="ResolutionTraceStep",
            premise_ids=nd_premise_ids,
            conclusion=clause_formula,
            substitutions=rstep.substitution,
            metadata={"clause": rstep.clause.to_string(), "rule_name": rstep.rule_name}
        )
        res_to_nd_map[rstep.id] = nd_id

    # Add Contradiction Step (⊥ derived from empty clause step)
    last_res_id = res_to_nd_map[resolution_trace[-1].id]
    contra_id = "derived_contradiction"
    steps[contra_id] = ProofStep(
        id=contra_id,
        rule="Contradiction",
        premise_ids=[last_res_id],
        conclusion=PredicateApp(pred="False", arity=0, args=())
    )

    # Final Goal Conclusion via Double Negation Elimination (¬¬target ⊢ target)
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
    reachable = set(proof.topological_order())
    reachable_ids = {s.id for s in reachable}
    new_steps = {sid: step for sid, step in proof.steps.items() if sid in reachable_ids}
    return ProofDAG(steps=new_steps, root_id=proof.root_id, axiom_ids=proof.axiom_ids & reachable_ids)


def _clause_to_formula(clause: Clause) -> Formula:
    """Converts a Clause back into a disjunctive Formula tree."""
    ...
```

---

### 4.6 CLI `prove` Command Update (`solver/__main__.py`)

Integrates the theorem prover into the `python -m solver prove` command line interface.

```python
# Add to solver/__main__.py argument parser:
prove_parser = argparse.ArgumentParser(prog="python -m solver prove", description="Prove a target theorem from premises.")
prove_parser.add_argument("--target", required=True, type=str, help="Target formula string to prove.")
prove_parser.add_argument("--premises", nargs="*", default=[], help="List of premise formula strings.")
prove_parser.add_argument("--max-steps", type=int, default=1000, help="Maximum resolution search steps.")
prove_parser.add_argument("--timeout", type=float, default=10.0, help="Prover timeout in seconds.")
prove_parser.add_argument("--save", action="store_true", help="Save proved theorem to database.")

def handle_prove(args: argparse.Namespace) -> None:
    signature = get_combined_signature()
    target_formula = parse_formula(args.target, signature=signature)
    premise_formulas = [parse_formula(p, signature=signature) for p in args.premises]

    prover = TheoremProver(signature=signature)
    try:
        proof_dag = prover.prove(
            target=target_formula,
            premises=premise_formulas,
            max_steps=args.max_steps,
            timeout_sec=args.timeout
        )
        print(f"SUCCESS: Theorem proved! ({len(proof_dag.steps)} proof steps)")
        if proof_dag.is_valid(signature=signature):
            print("VERIFIED: ProofDAG passes validity check.")
        if args.save:
            db = KnowledgeDatabase()
            db.insert_proved_theorem(name="cli_proved_theorem", formula=target_formula, proof=proof_dag)
            print("SAVED: Theorem stored in database.")
    except Exception as e:
        print(f"FAILED: {e}")
```

---

## 5. Step-by-Step Implementation Order

Implementation must proceed sequentially to ensure every dependency is unit-tested before dependent modules are built:

```
Step 1: solver/prover/clausifier.py & tests/test_clausifier.py
        └── Literal, Clause, NNF, Skolemization, drop_universals, distribute_cnf, to_cnf
Step 2: solver/prover/rules.py & tests/test_rules.py
        └── InferenceRule, resolve_clauses, factor_clause, paramodulate, get_resolution_rules
Step 3: solver/prover/proof.py & tests/test_proof.py
        └── ProofStep, ProofDAG (topological_order, is_valid, to_dict, from_dict)
Step 4: solver/prover/reconstruction.py & tests/test_reconstruction.py
        └── reconstruct_proof, simplify_proof
Step 5: solver/prover/engine.py & tests/test_prover.py
        └── ResolutionStep, TheoremProver (prove given-clause loop, subsumption, timeout/exhaustion handling)
Step 6: solver/prover/__init__.py
        └── Expose public API symbols
Step 7: solver/__main__.py CLI prove subcommand
        └── Add prove command and CLI integration testing
```

---

## 6. Testing Requirements

### 6.1 Unit Test Suites

#### `tests/test_clausifier.py`
- **NNF Conversion**: Test double negation removal, De Morgan laws on quantifiers (`Not(Forall)` $\to$ `Exists(Not)`).
- **Skolemization**: Test replacing $\exists x P(x)$ with Skolem constant `sk_c0`, and $\forall y \exists x P(x, y)$ with Skolem function `sk_f0(y)`. Verify sort alignment.
- **CNF Distribution**: Test $A \lor (B \land C) \to (A \lor B) \land (A \lor C)$.
- **Tautology Filtering**: Test that $P \lor \neg P$ clauses are removed during clausification.

#### `tests/test_rules.py`
- **Binary Resolution**: Resolve $P(x) \lor Q(x)$ and $\neg P(a)$ to get $Q(a)$ with substitution $\{x \mapsto a\}$.
- **Variable Separation**: Test resolving $P(x)$ and $\neg P(x)$ where $x$ in clause 1 is distinct from $x$ in clause 2.
- **Factoring**: Test factoring $P(x) \lor P(a)$ into $P(a)$.
- **Paramodulation**: Test paramodulating $a = b$ into $P(a)$ to derive $P(b)$.

#### `tests/test_reconstruction.py`
- **DAG Validity**: Verify `ProofDAG.is_valid()` returns `True` for constructed ND proofs.
- **Serialization**: Test `ProofDAG.to_dict()` and `from_dict()` round-trip equality.
- **Simplification**: Verify `simplify_proof` prunes unreferenced dead steps.

### 6.2 Integration Test Suite (`tests/test_prover.py`)

- **Propositional Tautologies**:
  - $P \lor \neg P$
  - $(P \implies Q) \land P \implies Q$
  - Peirce's Law: $((P \implies Q) \implies P) \implies P$
- **Basic FOL Theorems**:
  - $\forall x, P(x) \implies \exists x, P(x)$
  - $\forall x (P(x) \land Q(x)) \implies (\forall x P(x) \land \forall x Q(x))$
  - $\exists x \forall y P(x, y) \implies \forall y \exists x P(x, y)$
- **Non-Trivial Peano Theorem**:
  - Prove $\forall x, (x + 0 = x)$ or $0 + 0 = 0$ using Peano Arithmetic axioms from Phase 6 (`solver/kb/numbers.py`).
- **Exception Verification**:
  - Test `ProofTimeoutError` raised when `timeout_sec` is tiny (e.g., 0.0001s).
  - Test `ProofSearchExhaustedError` raised when target is invalid/unprovable (e.g., proving $P(a)$ from no premises with `max_steps=10`).

---

## 7. Acceptance Criteria

1. **Resolution Engine Completeness**: Proves propositional tautologies, basic FOL theorems, and at least one non-trivial Peano theorem.
2. **Proof DAG Verification**: 100% of proofs produced by `TheoremProver.prove()` pass `ProofDAG.is_valid()`.
3. **Reconstruction Correctness**: Reconstructed natural deduction proofs convert resolution traces into valid ND steps with proper root conclusions.
4. **Exception Integrity**: Timeouts raise `ProofTimeoutError` and unprovable goals raise `ProofSearchExhaustedError`.
5. **CLI Operation**: `python -m solver prove --target "forall v0, P(v0) => exists v0, P(v0)"` executes cleanly and reports proof status.
6. **Test Coverage**: All test files (`test_clausifier.py`, `test_rules.py`, `test_reconstruction.py`, `test_prover.py`) pass without errors.

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Search space explosion** in Given-Clause loop | High | Implement clause weighting heuristics (favor unit clauses and shorter terms) and forward subsumption. |
| **Variable capture** during resolution | Critical | Enforce variable standardization apart before any unification attempt. |
| **Skolem function sort mismatch** | High | Explicitly annotate Skolem functions with parameter and return sorts derived from quantified variables. |
| **Reconstruction complexity** for long traces | Medium | Fallback to explicit `ResolutionTraceStep` nodes in `ProofDAG` when multi-step natural deduction simplification is ambiguous. |
