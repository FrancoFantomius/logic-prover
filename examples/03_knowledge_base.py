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
