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
