# Examples

Ready-to-run example scripts that exercise the library end to end. Each file is self-contained, commented, and can be executed directly with `python examples/<name>.py`.

## Table of Contents

- [01_formula_construction.py](#01_formula_constructionpy)
- [02_theorem_proving.py](#02_theorem_provingpy)
- [03_knowledge_base.py](#03_knowledge_basepy)
- [04_formula_explorer.py](#04_formula_explorerpy)
- [05_dependency_deducer.py](#05_dependency_deducerpy)
- [06_exporters.py](#06_exporterspy)
- [07_second_order_logic.py](#07_second_order_logicpy)
- [08_cli_usage.py](#08_cli_usagepy)

---

## 01_formula_construction.py

**File:** `examples/01_formula_construction.py` — run with `python examples/01_formula_construction.py`

Example 01: Build, parse, and inspect logic formulas.

This example shows the two ways of constructing formulas with the library:

1. Programmatically, by composing the typed AST node classes directly
   (``Variable``, ``Constant``, ``PredicateApp``, ``And``, ``Forall``, ...).
2. From a string, using ``parse_formula`` with a ``Signature`` that declares
   every predicate, function, constant, and sort the formula may use.

It also demonstrates the inspection helpers ``to_string``, ``free_variables``,
``formula_depth``, and ``formula_size`` that the rest of the library builds on.

Run it with:

    python examples/01_formula_construction.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.

### Source

```python
"""Example 01: Build, parse, and inspect logic formulas.

This example shows the two ways of constructing formulas with the library:

1. Programmatically, by composing the typed AST node classes directly
   (``Variable``, ``Constant``, ``PredicateApp``, ``And``, ``Forall``, ...).
2. From a string, using ``parse_formula`` with a ``Signature`` that declares
   every predicate, function, constant, and sort the formula may use.

It also demonstrates the inspection helpers ``to_string``, ``free_variables``,
``formula_depth``, and ``formula_size`` that the rest of the library builds on.

Run it with:

    python examples/01_formula_construction.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

from logic_prover.core.ast import (
    Variable, Constant, PredicateApp, Equality, Implies, Forall,
    free_variables, formula_depth, formula_size,
)
from logic_prover.core.sorts import Ind
from logic_prover.core.signature import Signature
from logic_prover.core.parser import parse_formula, to_string


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Programmatic AST construction
    # ------------------------------------------------------------------
    # Variables are indexed and typed with a sort. Use id=0, 1, ... for
    # distinct variables and re-use the same object for the same variable.
    x = Variable(id=0, sort=Ind)

    # Constants carry a name and a sort.
    a = Constant(name="a", sort=Ind)

    # A predicate application P(x) - predicates are registered by name in
    # the signature, but building the AST directly does not need one.
    px = PredicateApp(pred="P", arity=1, args=(x,))
    pa = PredicateApp(pred="P", arity=1, args=(a,))

    # Combine nodes with the standard connectives and quantifiers.
    formula = Forall(
        variable=x,
        body=Implies(left=px, right=Equality(left=x, right=a)),
    )

    print("AST-built formula:", to_string(formula, notation="infix"))
    print("Free variables   :", sorted(v.id for v in free_variables(formula)))
    print("AST depth        :", formula_depth(formula))
    print("AST size         :", formula_size(formula))
    print()

    # ------------------------------------------------------------------
    # 2. String parsing against a declared Signature
    # ------------------------------------------------------------------
    # The parser validates every symbol against the signature, so declare
    # P, Q, and a before parsing strings that use them.
    sig = Signature()
    sig.register_predicate("P", 1, (Ind,))
    sig.register_predicate("Q", 1, (Ind,))
    sig.register_constant("a", sort=Ind)

    # Infix notation mirrors the ASCII connectives: ~, &, |, =>, <=>.
    parsed = parse_formula("forall v0 : Ind, P(v0) => (Q(v0) & P(a))", signature=sig)
    print("Parsed formula   :", to_string(parsed, notation="infix"))

    # Prefix (Lisp-style) notation is also accepted and round-trips.
    round_tripped = parse_formula(to_string(parsed, notation="prefix"), signature=sig)
    print("Round-trips      :", round_tripped == parsed)

    # Unknown or mis-typed symbols raise ParseError instead of failing silently.
    try:
        parse_formula("UnknownPredicate(v0)", signature=sig)
    except Exception as exc:  # ParseError
        print("Parser diagnostic:", type(exc).__name__, "-", exc)


if __name__ == "__main__":
    main()
```

---

## 02_theorem_proving.py

**File:** `examples/02_theorem_proving.py` — run with `python examples/02_theorem_proving.py`

Example 02: Prove theorems with the resolution prover.

Shows how to run the ``TheoremProver`` on propositional and first-order
targets, with and without premises, and how to validate the returned
``ProofDAG``.

Two prover configurations are covered:

- A hand-rolled ``Signature`` for toy predicate-logic examples (modus
  ponens, Peirce's law, quantifier reasoning).
- The built-in Peano arithmetic knowledge base, where real theorems such as
  ``add(zero, zero) = zero`` are proved from the Peano axioms.

Run it with:

    python examples/02_theorem_proving.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.

### Source

```python
"""Example 02: Prove theorems with the resolution prover.

Shows how to run the ``TheoremProver`` on propositional and first-order
targets, with and without premises, and how to validate the returned
``ProofDAG``.

Two prover configurations are covered:

- A hand-rolled ``Signature`` for toy predicate-logic examples (modus
  ponens, Peirce's law, quantifier reasoning).
- The built-in Peano arithmetic knowledge base, where real theorems such as
  ``add(zero, zero) = zero`` are proved from the Peano axioms.

Run it with:

    python examples/02_theorem_proving.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, Or, And, Implies, Forall, Exists,
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.core.signature import Signature
from logic_prover.prover.engine import TheoremProver
from logic_prover.axioms.peano import get_peano_signature, get_peano_axioms


def build_toy_signature() -> Signature:
    """Declares a minimal predicate-logic signature used by the examples."""
    sig = Signature()
    sig.register_predicate("P", 1, (Ind,))
    sig.register_predicate("Q", 1, (Ind,))
    sig.register_predicate("R", 2, (Ind, Ind))
    sig.register_predicate("PropP", 0, ())
    sig.register_predicate("PropQ", 0, ())
    sig.register_constant("a", Ind)
    sig.register_function("f", 1, (Ind,), return_sort=Ind)
    return sig


def prove_and_report(prover: TheoremProver, target, premises=None, label: str = "") -> None:
    """Attempts a proof and prints whether it succeeded and validates the DAG."""
    proof = prover.prove(target=target, premises=premises or [])
    status = "proved" if proof.is_valid() else "INVALID"
    print(f"[{label}] {status} in {len(proof.steps)} steps")
    return proof


def main() -> None:
    sig = build_toy_signature()
    prover = TheoremProver(signature=sig)

    p = PredicateApp(pred="PropP", arity=0, args=())
    q = PredicateApp(pred="PropQ", arity=0, args=())

    # ------------------------------------------------------------------
    # 1. Propositional logic
    # ------------------------------------------------------------------
    # A tautology needs no premises: P or not P.
    prove_and_report(prover, Or(left=p, right=Not(operand=p)), label="P | ~P")

    # Modus ponens: from (P => Q) and P, prove Q.
    prove_and_report(
        prover,
        target=q,
        premises=[And(left=Implies(left=p, right=q), right=p)],
        label="modus ponens",
    )

    # Peirce's law: ((P => Q) => P) => P.
    prove_and_report(
        prover,
        target=Implies(left=Implies(left=Implies(left=p, right=q), right=p), right=p),
        label="Peirce's law",
    )

    # ------------------------------------------------------------------
    # 2. First-order logic
    # ------------------------------------------------------------------
    x = Variable(id=0, sort=Ind)
    y = Variable(id=1, sort=Ind)
    px = PredicateApp(pred="P", arity=1, args=(x,))
    rxy = PredicateApp(pred="R", arity=2, args=(x, y))

    # (forall x. P(x)) => (exists x. P(x))
    prove_and_report(
        prover,
        target=Implies(left=Forall(variable=x, body=px),
                       right=Exists(variable=x, body=px)),
        label="forall => exists",
    )

    # (exists x forall y. R(x,y)) => (forall y exists x. R(x,y))
    prove_and_report(
        prover,
        target=Implies(
            left=Exists(variable=x, body=Forall(variable=y, body=rxy)),
            right=Forall(variable=y, body=Exists(variable=x, body=rxy)),
        ),
        label="exists/forall swap",
    )

    # ------------------------------------------------------------------
    # 3. Peano arithmetic from the built-in knowledge base
    # ------------------------------------------------------------------
    peano_sig = get_peano_signature()
    peano_axioms = [formula for _, formula in get_peano_axioms()]
    peano_prover = TheoremProver(signature=peano_sig)

    zero = Constant("zero", sort=Nat)
    add_0_0 = FunctionApp("add", 2, (zero, zero), return_sort=Nat)
    prove_and_report(
        peano_prover,
        target=Equality(left=add_0_0, right=zero),
        premises=peano_axioms,
        label="add(zero, zero) = zero",
    )


if __name__ == "__main__":
    main()
```

---

## 03_knowledge_base.py

**File:** `examples/03_knowledge_base.py` — run with `python examples/03_knowledge_base.py`

Example 03: Store and query formulas in the SQLite knowledge base.

The ``KnowledgeDatabase`` persists formulas, axioms, theorems, and proofs in
a SQLite file. Formulas are canonicalized (alpha-equivalent formulas are
detected as duplicates) and indexed by structural attributes such as depth,
size, and the predicate names they mention.

This example:

1. Creates an in-memory database (use a path to persist across runs).
2. Registers a few axioms with categories.
3. Stores a proved theorem together with its proof DAG.
4. Queries the database by category and by structural filters.

Run it with:

    python examples/03_knowledge_base.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.

### Source

```python
"""Example 03: Store and query formulas in the SQLite knowledge base.

The ``KnowledgeDatabase`` persists formulas, axioms, theorems, and proofs in
a SQLite file. Formulas are canonicalized (alpha-equivalent formulas are
detected as duplicates) and indexed by structural attributes such as depth,
size, and the predicate names they mention.

This example:

1. Creates an in-memory database (use a path to persist across runs).
2. Registers a few axioms with categories.
3. Stores a proved theorem together with its proof DAG.
4. Queries the database by category and by structural filters.

Run it with:

    python examples/03_knowledge_base.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

from logic_prover.core.ast import Variable, Constant, PredicateApp, Implies, Forall
from logic_prover.core.sorts import Ind
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.prover.proof import ProofStep, ProofDAG
from logic_prover.axioms import get_all_axioms, get_combined_signature


def main() -> None:
    # ':memory:' keeps everything in RAM; pass a file path to persist.
    # You can also use the context manager form: with KnowledgeDatabase(...) as db:
    db = KnowledgeDatabase(":memory:")

    # ------------------------------------------------------------------
    # 1. Register axioms (name, formula, category)
    # ------------------------------------------------------------------
    sig = get_combined_signature()

    # Parse a few axioms from strings using the full library signature.
    db.add_axiom("refl_like", parse_or_build(sig, "forall v0 : Ind, P(v0) => P(v0)"), category="demo")
    db.add_axiom("impl_like", parse_or_build(sig, "forall v0 : Ind, (P(v0) & Q(v0)) => P(v0)"), category="demo")

    # Or add the entire built-in knowledge base at once.
    for name, formula, category in get_all_axioms():
        try:
            db.add_axiom(name, formula, category)
        except Exception:
            pass  # duplicate names are skipped

    print(f"Stored axioms: {len(db.get_axioms())}")
    print(f"Axioms in category 'peano': {len(db.get_axioms(category='peano'))}")
    print()

    # ------------------------------------------------------------------
    # 2. Store a proved theorem (with its proof DAG)
    # ------------------------------------------------------------------
    x = Variable(id=0, sort=Ind)
    px = PredicateApp(pred="P", arity=1, args=(x,))
    theorem_formula = Forall(variable=x, body=Implies(left=px, right=px))

    # A ProofDAG records the inference steps; here a single-axiom proof.
    step = ProofStep(id="reflexive_impl", rule="Axiom", premise_ids=[], conclusion=theorem_formula)
    proof = ProofDAG(steps={"reflexive_impl": step}, root_id="reflexive_impl")
    db.add_theorem(name="reflexive_impl", formula=theorem_formula, proof=proof, category="demo")

    # contains_formula detects alpha-equivalent duplicates, not just identity.
    y = Variable(id=1, sort=Ind)
    py = PredicateApp(pred="P", arity=1, args=(y,))
    alpha_equivalent = Forall(variable=y, body=Implies(left=py, right=py))
    print("Contains alpha-equivalent theorem?:", db.contains_formula(alpha_equivalent))
    print()

    # ------------------------------------------------------------------
    # 3. Structural queries
    # ------------------------------------------------------------------
    # search_formulas filters on depth/size and the predicates a formula uses.
    small_demo = db.search_formulas(predicate_name="P", max_depth=4)
    print(f"Formulas using 'P' with depth <= 4: {len(small_demo)}")

    # A proof (ProofDAG) can be stored and retrieved by theorem name.
    proof = db.get_proof("reflexive_impl")
    print("Stored proof for 'reflexive_impl':", "present" if proof is not None else "none")

    db.close()


def parse_or_build(sig, text: str):
    """Small helper that parses a formula string against the given signature."""
    from logic_prover.core.parser import parse_formula
    return parse_formula(text, signature=sig)


if __name__ == "__main__":
    main()
```

---

## 04_formula_explorer.py

**File:** `examples/04_formula_explorer.py` — run with `python examples/04_formula_explorer.py`

Example 04: Generate and rank novel formulas with the FormulaExplorer.

The explorer invents candidate formulas from the axioms in a database using
several strategies (rewriting, anti-unification, saturation, lemma
combination, and a mixed mode) and then ranks them with heuristic scores:

- ``calculate_diversity_scores`` measures structural diversity of a formula.
- ``composite_interestingness`` combines those metrics into a single score.
- ``FormulaFilter`` tracks already-seen formulas so exploration does not
  repeat itself; its state can be saved to disk between runs.

Run it with:

    python examples/04_formula_explorer.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.

### Source

```python
"""Example 04: Generate and rank novel formulas with the FormulaExplorer.

The explorer invents candidate formulas from the axioms in a database using
several strategies (rewriting, anti-unification, saturation, lemma
combination, and a mixed mode) and then ranks them with heuristic scores:

- ``calculate_diversity_scores`` measures structural diversity of a formula.
- ``composite_interestingness`` combines those metrics into a single score.
- ``FormulaFilter`` tracks already-seen formulas so exploration does not
  repeat itself; its state can be saved to disk between runs.

Run it with:

    python examples/04_formula_explorer.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from logic_prover.config import SolverConfig
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.core.parser import to_string
from logic_prover.axioms import get_all_axioms, get_combined_signature
from logic_prover.explorer import (
    FormulaExplorer,
    calculate_diversity_scores,
    composite_interestingness,
)


def main() -> None:
    # Explorer works against a database seeded with axioms. Use a temp file
    # so nothing is left behind in the repository.
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "explorer.db")
        db = KnowledgeDatabase(db_path)

        # Seed the database with the full built-in axiom set.
        for name, formula, category in get_all_axioms():
            db.add_axiom(name, formula, category)

        signature = get_combined_signature()
        config = SolverConfig(db_path=db_path)
        explorer = FormulaExplorer(db=db, signature=signature, config=config)

        # ------------------------------------------------------------------
        # 1. Generate candidate formulas with a chosen strategy
        # ------------------------------------------------------------------
        candidates = explorer.generate_candidates(
            strategy="mixed",
            max_depth=4,
            count=20,
        )
        print(f"Generated {len(candidates)} raw candidates")
        print()

        # ------------------------------------------------------------------
        # 2. Rank and select the most interesting candidates
        # ------------------------------------------------------------------
        top = explorer.rank_and_select(candidates, top_k=5)
        print("Top-ranked candidates:")
        print("-" * 60)
        for idx, formula in enumerate(top, 1):
            metrics = calculate_diversity_scores(formula)
            score = composite_interestingness(metrics)
            print(f"[{idx}] score={score:.2f} size={metrics.ast_size} "
                  f"entropy={metrics.symbol_entropy:.2f}  {to_string(formula)}")
        print()

        # ------------------------------------------------------------------
        # 3. The filter remembers what has already been proposed
        # ------------------------------------------------------------------
        print(f"Distinct formulas seen so far: {len(explorer.filter)}")
        seen_again = explorer.rank_and_select(top, top_k=5)
        print(f"Re-ranking the same candidates yields {len(seen_again)} new formulas "
              "(0 because they are already seen).")

        db.close()


if __name__ == "__main__":
    main()
```

---

## 05_dependency_deducer.py

**File:** `examples/05_dependency_deducer.py` — run with `python examples/05_dependency_deducer.py`

Example 05: Analyze dependencies and deduce minimal hypotheses.

The deducer subsystem studies how formulas relate to one another:

- ``DependencyGraph`` stores named formulas and directed ``implies`` /
  ``equivalent`` edges and supports traversals and cycle detection.
- ``analyze_dependencies`` builds such a graph across a collection of
  formulas, optionally running expensive pairwise implication proofs.
- ``find_minimal_hypotheses`` removes hypotheses one at a time to find a
  minimal sufficient subset for a given target.
- ``detect_redundant_hypotheses`` reports every hypothesis that can be
  dropped individually.
- ``compute_equivalence_classes`` groups formulas that mutually imply each
  other, fast-pathing on syntactic alpha-equivalence.

Run it with:

    python examples/05_dependency_deducer.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.

### Source

```python
"""Example 05: Analyze dependencies and deduce minimal hypotheses.

The deducer subsystem studies how formulas relate to one another:

- ``DependencyGraph`` stores named formulas and directed ``implies`` /
  ``equivalent`` edges and supports traversals and cycle detection.
- ``analyze_dependencies`` builds such a graph across a collection of
  formulas, optionally running expensive pairwise implication proofs.
- ``find_minimal_hypotheses`` removes hypotheses one at a time to find a
  minimal sufficient subset for a given target.
- ``detect_redundant_hypotheses`` reports every hypothesis that can be
  dropped individually.
- ``compute_equivalence_classes`` groups formulas that mutually imply each
  other, fast-pathing on syntactic alpha-equivalence.

Run it with:

    python examples/05_dependency_deducer.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

from logic_prover.core.ast import (
    Variable, Constant, PredicateApp, Not, Or, And, Implies,
)
from logic_prover.core.sorts import Ind
from logic_prover.core.signature import Signature
from logic_prover.prover.engine import TheoremProver
from logic_prover.deducer.graph import DependencyGraph
from logic_prover.deducer.analyzer import (
    analyze_dependencies,
    find_minimal_hypotheses,
    detect_redundant_hypotheses,
    compute_equivalence_classes,
)


def main() -> None:
    sig = Signature()
    sig.register_predicate("P", 1, (Ind,))
    sig.register_predicate("Q", 1, (Ind,))
    sig.register_predicate("R", 1, (Ind,))
    sig.register_constant("a", Ind)
    prover = TheoremProver(signature=sig)

    p_a = PredicateApp("P", 1, (Constant("a"),))
    q_a = PredicateApp("Q", 1, (Constant("a"),))
    r_a = PredicateApp("R", 1, (Constant("a"),))

    # ------------------------------------------------------------------
    # 1. Build a dependency graph manually
    # ------------------------------------------------------------------
    graph = DependencyGraph()
    graph.add_node("A", p_a)
    graph.add_node("B", q_a)
    graph.add_node("C", r_a)
    graph.add_edge("A", "B", "implies")
    graph.add_edge("B", "C", "implies")

    print("Nodes:", list(graph.nodes))
    print("Successors of A:", graph.successors("A"))
    print("Predecessors of C:", graph.predecessors("C"))
    print("Transitive closure of A:", sorted(graph.transitive_closure("A")))
    print("Acyclic (modulo equivalence)?:", graph.is_acyclic_modulo_equivalence())
    print()

    # ------------------------------------------------------------------
    # 2. Find a minimal subset of hypotheses for a target
    # ------------------------------------------------------------------
    # H1: P(a), H2: Q(a) (redundant), H3: P(a) => R(a). Target: R(a).
    h1, h2, h3 = p_a, q_a, Implies(left=p_a, right=r_a)
    minimal = find_minimal_hypotheses(target=r_a, available_hypotheses=[h1, h2, h3], prover=prover)
    print(f"Minimal hypothesis subset for R(a): {len(minimal)} formula(s)")
    for f in minimal:
        print("  -", f)

    redundant = detect_redundant_hypotheses(hypotheses=[h1, h2, h3], target=r_a, prover=prover)
    print(f"Individually redundant hypotheses: {len(redundant)}")
    print()

    # ------------------------------------------------------------------
    # 3. Equivalent formulas and full dependency analysis
    # ------------------------------------------------------------------
    # P(a) => Q(a) and ~P(a) | Q(a) are logically equivalent.
    f1 = Implies(left=p_a, right=q_a)
    f2 = Or(left=Not(operand=p_a), right=q_a)
    classes = compute_equivalence_classes([("F1", f1), ("F2", f2), ("F3", r_a)], prover=prover)
    print("Equivalence classes:", [sorted(c) for c in classes])

    dep_graph = analyze_dependencies(
        [("F1", f1), ("F2", f2), ("F3", r_a)],
        prover=prover,
        pairwise=True,
    )
    print("Dependency edges:", dep_graph.edges)


if __name__ == "__main__":
    main()
```

---

## 06_exporters.py

**File:** `examples/06_exporters.py` — run with `python examples/06_exporters.py`

Example 06: Export theorems to Lean 4 and interactive HTML graphs.

Two exporters turn in-memory results into artifacts you can use elsewhere:

- ``LeanExporter`` emits Lean 4 theorem declarations (with ``sorry`` stubs
  when proofs are not available) from a list of (name, formula, proof)
  tuples, ready to paste into a Mathlib project.
- ``GraphExporter`` renders a ``ProofDAG`` or a ``DependencyGraph`` into a
  self-contained interactive HTML file using the vis-network library.

Run it with:

    python examples/06_exporters.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.

### Source

```python
"""Example 06: Export theorems to Lean 4 and interactive HTML graphs.

Two exporters turn in-memory results into artifacts you can use elsewhere:

- ``LeanExporter`` emits Lean 4 theorem declarations (with ``sorry`` stubs
  when proofs are not available) from a list of (name, formula, proof)
  tuples, ready to paste into a Mathlib project.
- ``GraphExporter`` renders a ``ProofDAG`` or a ``DependencyGraph`` into a
  self-contained interactive HTML file using the vis-network library.

Run it with:

    python examples/06_exporters.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Lean 4 output uses Unicode symbols; force UTF-8 stdout so the print below
# works even on consoles whose default codepage is not UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from logic_prover.core.ast import (
    Variable, Constant, PredicateApp, Implies,
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.prover.engine import TheoremProver
from logic_prover.prover.proof import ProofStep, ProofDAG
from logic_prover.deducer.graph import DependencyGraph
from logic_prover.exporters.lean_exporter import LeanExporter
from logic_prover.exporters.graph_exporter import GraphExporter


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Build a proof DAG the way the prover would
    # ------------------------------------------------------------------
    v0 = Variable(id=0, sort=Ind)
    p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
    q_v0 = PredicateApp(pred="Q", arity=1, args=(v0,))

    step_h1 = ProofStep(id="h1", rule="Hypothesis", premise_ids=[], conclusion=p_v0)
    step_h2 = ProofStep(id="h2", rule="Hypothesis", premise_ids=[], conclusion=Implies(left=p_v0, right=q_v0))
    step_mp = ProofStep(id="step_mp", rule="ModusPonens", premise_ids=["h2", "h1"], conclusion=q_v0)

    proof = ProofDAG(
        steps={"h1": step_h1, "h2": step_h2, "step_mp": step_mp},
        root_id="step_mp",
    )

    # ------------------------------------------------------------------
    # 2. Export a theorem to Lean 4
    # ------------------------------------------------------------------
    lean_exporter = LeanExporter(lean_project_name="LogicExamples", universe_name="u")
    lean_code = lean_exporter.export_proof(proof=proof, theorem_name="modus_ponens_demo")
    print("=== Lean 4 export ===")
    print(lean_code)
    print()

    # ------------------------------------------------------------------
    # 3. Write the proof graph and a dependency graph to HTML
    # ------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp_dir:
        proof_html = str(Path(tmp_dir) / "proof.html")
        dep_html = str(Path(tmp_dir) / "dependency.html")

        graph_exporter = GraphExporter(theme="light")
        graph_exporter.export_proof_to_html(proof, proof_html, title="Modus Ponens Proof")

        # A small dependency graph with an 'implies' edge.
        dep_graph = DependencyGraph()
        dep_graph.add_node("Axiom1", p_v0)
        dep_graph.add_node("Thm1", q_v0)
        dep_graph.add_edge("Axiom1", "Thm1", "implies")
        graph_exporter.export_dependency_network_to_html(dep_graph, dep_html, title="Dependency Network")

        print("=== HTML exports ===")
        print(f"Proof graph     : {proof_html} ({Path(proof_html).stat().st_size} bytes)")
        print(f"Dependency graph: {dep_html} ({Path(dep_html).stat().st_size} bytes)")

    # ------------------------------------------------------------------
    # 4. Export from the database using the library-level API
    # ------------------------------------------------------------------
    db_path = ":memory:"
    db = KnowledgeDatabase(db_path)
    db.add_theorem("modus_ponens_demo", q_v0, proof=proof)

    theorems = [(name, formula, db.get_proof(name)) for name, formula in db.get_theorems()]
    with tempfile.TemporaryDirectory() as tmp_dir:
        lean_file = str(Path(tmp_dir) / "theorems.lean")
        lean_exporter.export_file(lean_file, theorems, stubs_only=False)
        print(f"Exported {len(theorems)} theorem(s) to {lean_file}")
    db.close()


if __name__ == "__main__":
    main()
```

---

## 07_second_order_logic.py

**File:** `examples/07_second_order_logic.py` — run with `python examples/07_second_order_logic.py`

Example 07: Second-order logic — predicate variables and schemas.

The ``logic_prover.sol`` package extends first-order ASTs with:

- ``PredicateVariable`` / ``FunctionVariable`` and the SOL quantifiers
  ``ForallPred`` / ``ExistsPred`` / ``ForallFunc`` / ``ExistsFunc``.
- Free/bound variable collectors for predicate and function variables.
- Schema instantiation helpers ``instantiate_comprehension`` and
  ``instantiate_induction`` that build explicit instances of the
  second-order comprehension and Peano induction schemas.
- Higher-order pattern unification (``ho_pattern_unify``) and beta
  reduction for applying predicate/function templates to arguments.

Run it with:

    python examples/07_second_order_logic.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.

### Source

```python
"""Example 07: Second-order logic — predicate variables and schemas.

The ``logic_prover.sol`` package extends first-order ASTs with:

- ``PredicateVariable`` / ``FunctionVariable`` and the SOL quantifiers
  ``ForallPred`` / ``ExistsPred`` / ``ForallFunc`` / ``ExistsFunc``.
- Free/bound variable collectors for predicate and function variables.
- Schema instantiation helpers ``instantiate_comprehension`` and
  ``instantiate_induction`` that build explicit instances of the
  second-order comprehension and Peano induction schemas.
- Higher-order pattern unification (``ho_pattern_unify``) and beta
  reduction for applying predicate/function templates to arguments.

Run it with:

    python examples/07_second_order_logic.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

import sys

# Second-order formulas render with Unicode quantifiers; force UTF-8 stdout
# so the print below works even on consoles whose default codepage is not UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality, Forall,
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.core.parser import to_string
from logic_prover.sol.ast_ext import (
    PredicateVariable, FunctionVariable, ForallPred, ExistsPred,
    free_predicate_variables, free_function_variables,
)
from logic_prover.sol.kb_ext import (
    get_sol_axioms,
    instantiate_comprehension,
    instantiate_induction,
)
from logic_prover.sol.substitutions_ext import (
    ho_pattern_unify,
    beta_reduce_predicate,
)


def show(label: str, formula) -> None:
    """Prints a formula through the human-readable infix printer."""
    print(f"{label:16s}: {to_string(formula)}")


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Predicate variables and SOL quantifiers
    # ------------------------------------------------------------------
    p = PredicateVariable(index=0, arity=1)
    x = Variable(id=0, sort=Ind)
    px = PredicateApp(pred=p, arity=1, args=(x,))

    # ∀P. P(x) => P(x) — the P is bound by ForallPred.
    formula = ForallPred(variable=p, body=PredicateApp(pred=p, arity=1, args=(x,)))
    show("SOL formula", formula)
    print("Free pred vars   :", sorted(v.index for v in free_predicate_variables(px)))
    print("Bound pred vars  :", sorted(v.index for v in free_predicate_variables(formula)))
    print()

    # ------------------------------------------------------------------
    # 2. Beta reduction: apply a template φ(x) to a concrete argument
    # ------------------------------------------------------------------
    a = Constant(name="a", sort=Ind)
    # Template: x = a  (predicate 'equals a')
    template = Equality(left=x, right=a)
    # β-reduce [x ↦ a]:  a = a
    reduced = beta_reduce_predicate(template, params=(x,), args=(a,))
    show("Beta-reduced", reduced)
    print()

    # ------------------------------------------------------------------
    # 3. Instantiate the comprehension schema
    # ------------------------------------------------------------------
    # ∃P. ∀x. (P(x) <=> (x = a))
    comp = instantiate_comprehension(p, params=(x,), body=template)
    show("Comprehension", comp)
    print()

    # ------------------------------------------------------------------
    # 4. Instantiate the Peano induction schema for add(n, zero) = n
    # ------------------------------------------------------------------
    n = Variable(id=0, sort=Nat)
    zero = Constant("zero", sort=Nat)
    add_n_zero = FunctionApp("add", 2, (n, zero), return_sort=Nat)
    prop = Equality(left=add_n_zero, right=n)
    induction = instantiate_induction(prop, n)
    show("Induction schema", induction)
    print()

    # ------------------------------------------------------------------
    # 5. Higher-order pattern unification
    # ------------------------------------------------------------------
    # Unify P(x) with (x = a): the solution binds P to the template (x = a).
    p_x = PredicateApp(pred=PredicateVariable(0, 1), arity=1, args=(x,))
    x_eq_a = Equality(left=x, right=a)
    solution = ho_pattern_unify(p_x, x_eq_a)
    print("HO unification   :", solution is not None, "(solution bound below)")
    if solution:
        pred_sol = next(iter(solution))
        params, template = solution[pred_sol]
        print("   binds", pred_sol.name, "-> params", [v.id for v in params],
              "template", to_string(template))

    # ------------------------------------------------------------------
    # 6. The built-in SOL axiom schemas
    # ------------------------------------------------------------------
    axioms = get_sol_axioms()
    print("\nSOL axiom schemas:", [name for name, _ in axioms])


if __name__ == "__main__":
    main()
```

---

## 08_cli_usage.py

**File:** `examples/08_cli_usage.py` — run with `python examples/08_cli_usage.py`

Example 08: Drive the full pipeline through the CLI entry point.

The package exposes a small command-line interface in
``logic_prover.__main__``. Every command can also be invoked as a plain
Python call via ``main([...])``, which is convenient for scripting and
testing. This example walks a complete workflow:

    init        -> create a database seeded with the axiom knowledge base
    prove       -> prove a target and save it as a theorem
    analyze     -> run dependency analysis over the database
    export lean -> emit Lean 4 declarations
    export graph-> render an interactive dependency HTML graph

Run it with:

    python examples/08_cli_usage.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.

### Source

```python
"""Example 08: Drive the full pipeline through the CLI entry point.

The package exposes a small command-line interface in
``logic_prover.__main__``. Every command can also be invoked as a plain
Python call via ``main([...])``, which is convenient for scripting and
testing. This example walks a complete workflow:

    init        -> create a database seeded with the axiom knowledge base
    prove       -> prove a target and save it as a theorem
    analyze     -> run dependency analysis over the database
    export lean -> emit Lean 4 declarations
    export graph-> render an interactive dependency HTML graph

Run it with:

    python examples/08_cli_usage.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from logic_prover.__main__ import main as run_cli


def main() -> None:
    # All CLI commands share a global config; run everything inside one
    # temporary directory so no database or export files are left behind.
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "logic_data.db")
        lean_path = str(Path(tmp_dir) / "theorems.lean")
        graph_path = str(Path(tmp_dir) / "dependency.html")
        analysis_path = str(Path(tmp_dir) / "analysis.json")

        # 1. init: create and seed the database with all built-in axioms.
        ret = run_cli(["init", "--db-path", db_path, "--force"])
        print(f"[init]    exit={ret} db={'created' if Path(db_path).exists() else 'missing'}")

        # 2. prove: prove a first-order tautology and save it to the database.
        ret = run_cli([
            "prove", "forall v0 : Ind, P(v0) => P(v0)",
            "--db-path", db_path,
            "--save",
        ])
        print(f"[prove]   exit={ret}")

        # 3. analyze: build a dependency graph and export it as JSON.
        ret = run_cli(["analyze", "--db-path", db_path, "--output", analysis_path])
        print(f"[analyze] exit={ret} output={'created' if Path(analysis_path).exists() else 'missing'}")

        # 4. export lean: emit stubs for every theorem/axiom in the database.
        ret = run_cli(["export", "lean", "--output", lean_path, "--db-path", db_path, "--stubs-only"])
        print(f"[lean]    exit={ret} output={'created' if Path(lean_path).exists() else 'missing'}")

        # 5. export graph: render the dependency network to interactive HTML.
        ret = run_cli(["export", "graph", "--type", "dependency", "--output", graph_path, "--db-path", db_path])
        print(f"[graph]   exit={ret} output={'created' if Path(graph_path).exists() else 'missing'}")

        # 6. docs: regenerate the documentation site (defaults to docs/).
        docs_dir = str(Path(tmp_dir) / "docs")
        ret = run_cli(["docs", "--output-dir", docs_dir])
        print(f"[docs]    exit={ret} index={'created' if Path(docs_dir, 'index.md').exists() else 'missing'}")

        print("\nAll artifacts written under:", tmp_dir)


if __name__ == "__main__":
    main()
```
