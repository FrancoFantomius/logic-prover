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
