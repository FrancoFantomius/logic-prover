"""
Command Line Interface (CLI) entry point for the logic library.

Supports all 7 logic commands:
- init: Initialize database with foundational logic axioms
- explore: Generate and rank novel candidate formulas
- prove: Attempt resolution proof for a target formula
- analyze: Conduct hypothesis deduction and dependency analysis
- export lean: Translate theorems and proofs to Lean 4 formal code
- export graph: Export interactive proof or dependency DAG HTML graphs
- docs: Build static Markdown documentation site
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from logic_prover.config import SolverConfig
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.core.exceptions import SolverError, ParseError, ProofTimeoutError
from logic_prover.core.parser import parse_formula, to_string
from logic_prover.deducer import analyze_dependencies, compute_equivalence_classes
from logic_prover.explorer import FormulaExplorer, calculate_diversity_scores, composite_interestingness
from logic_prover.exporters import LeanExporter, GraphExporter
from logic_prover.kb import get_all_axioms, get_combined_signature
from logic_prover.prover import TheoremProver
from logic_prover.utils.doc_generator import build_markdown_docs
from logic_prover.utils.logging import setup_logging, get_logger

logger = get_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    """
    Constructs the top-level ArgumentParser and all subcommand parsers.

    Subcommands:
    - init: Initialize database with axioms
    - explore: Run formula explorer
    - prove: Prove target formula from premises
    - analyze: Run deducer hypothesis analysis
    - export lean: Export to LEAN 4 code
    - export graph: Export interactive proof/dependency HTML graph
    - docs: Regenerate static API documentation

    Returns:
        Configured argparse.ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="logic",
        description="Formal Logic Explorer & Theorem Prover CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. init command
    init_parser = subparsers.add_parser("init", help="Initialize database with foundational axioms")
    init_parser.add_argument("--db-path", type=str, default=None, help="Path to SQLite database file")
    init_parser.add_argument(
        "--force", "--reset", dest="reset", action="store_true", help="Force re-creation of database tables"
    )

    # 2. explore command
    explore_parser = subparsers.add_parser("explore", help="Explore and generate novel candidate formulas")
    explore_parser.add_argument(
        "--strategy",
        choices=["mixed", "axiom_rewrite", "proof_frontier", "anti_unification", "saturation", "lemma_combination", "all"],
        default="all",
        help="Formula generation strategy (default: all)",
    )
    explore_parser.add_argument("--depth", type=int, default=3, help="Maximum search depth limit (default: 3)")
    explore_parser.add_argument("--count", type=int, default=50, help="Number of raw candidates to generate (default: 50)")
    explore_parser.add_argument("--top-k", type=int, default=10, help="Number of top candidates to display (default: 10)")
    explore_parser.add_argument("--filter-file", type=str, default=None, help="Path to persistent filter state JSON file")
    explore_parser.add_argument("--db-path", type=str, default=None, help="Path to SQLite database file")

    # 3. prove command
    prove_parser = subparsers.add_parser("prove", help="Prove target formula from premises")
    prove_parser.add_argument(
        "target_pos", nargs="?", default=None, metavar="FORMULA", help="Target formula string to prove"
    )
    prove_parser.add_argument("--target", type=str, default=None, help="Target formula string to prove")
    prove_parser.add_argument("--premises", nargs="*", default=[], help="Space-separated premise formula strings")
    prove_parser.add_argument("--timeout", type=float, default=10.0, help="Prover wall-clock timeout in seconds")
    prove_parser.add_argument("--max-steps", type=int, default=1000, help="Maximum given-clause search iterations")
    prove_parser.add_argument("--stubs-only", action="store_true", help="Check syntax without full resolution proof")
    prove_parser.add_argument("--save", action="store_true", help="Save proved theorem to database")
    prove_parser.add_argument("--db-path", type=str, default=None, help="Path to SQLite database file")

    # 4. analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze network dependencies and hypothesis-consequence relationships"
    )
    analyze_parser.add_argument("--db", type=str, default="logic_data.db", help="Path to SQLite database")
    analyze_parser.add_argument("--db-path", type=str, default=None, help="Path to SQLite database file")
    analyze_parser.add_argument("--category", type=str, default=None, help="Filter database theorems by category")
    analyze_parser.add_argument("--pairwise", action="store_true", help="Perform opt-in O(n^2) pairwise implication proofs")
    analyze_parser.add_argument("--output", type=str, default=None, help="Output JSON file path for exported DependencyGraph")

    # 5 & 6. export command with subcommands: lean, graph
    export_parser = subparsers.add_parser("export", help="Export theorems and proofs to LEAN 4 or HTML graphs")
    export_subparsers = export_parser.add_subparsers(dest="export_type", required=True)

    # export lean
    lean_parser = export_subparsers.add_parser("lean", help="Export to LEAN 4 formal proof file")
    lean_parser.add_argument("--output", "-o", default="output.lean", help="Output .lean file path (default: output.lean)")
    lean_parser.add_argument("--theorems", nargs="*", help="Specific theorem names to export")
    lean_parser.add_argument("--stubs-only", action="store_true", help="Emit theorem declarations with sorry stubs")
    lean_parser.add_argument("--db-path", help="Path to SQLite database")

    # export graph
    graph_parser = export_subparsers.add_parser("graph", help="Export proof or dependency graph to interactive HTML")
    graph_parser.add_argument("--output", "-o", default="graph.html", help="Output .html file path (default: graph.html)")
    graph_parser.add_argument("--type", choices=["proof", "dependency"], default="proof", help="Graph visualization type")
    graph_parser.add_argument("--theorem", help="Target theorem name for proof graph export")
    graph_parser.add_argument("--db-path", help="Path to SQLite database")

    # 7. docs command
    docs_parser = subparsers.add_parser("docs", help="Regenerate static API documentation")
    docs_parser.add_argument("--output-dir", type=str, default="docs", help="Target output directory for markdown docs (default: docs)")

    return parser


build_cli_parser = build_parser


def cmd_init(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'init' command."""
    db_path = args.db_path or config.db_path
    if args.reset and Path(db_path).exists():
        try:
            Path(db_path).unlink()
        except Exception as e:
            logger.warning(f"Could not remove old database at '{db_path}': {e}")

    db = KnowledgeDatabase(db_path)
    axioms = get_all_axioms()
    added_count = 0
    for name, formula, category in axioms:
        try:
            db.add_axiom(name, formula, category)
            added_count += 1
        except Exception as e:
            logger.debug(f"Skipping duplicate/invalid axiom {name}: {e}")

    db.close()
    print(f"Successfully initialized database at '{db_path}' with {added_count} axioms.")
    logger.info(f"Database initialized at '{db_path}' with {added_count} axioms.")
    return 0


def cmd_explore(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'explore' command."""
    db_path = args.db_path or config.db_path
    db = KnowledgeDatabase(db_path=db_path)
    signature = get_combined_signature()

    strategy_arg = args.strategy
    if strategy_arg == "all":
        strategy_arg = "mixed"

    explorer = FormulaExplorer(
        db=db,
        signature=signature,
        config=config,
        filter_path=args.filter_file,
    )

    candidates = explorer.generate_candidates(
        strategy=strategy_arg,
        max_depth=args.depth,
        count=args.count,
    )

    top_formulas = explorer.rank_and_select(candidates, top_k=args.top_k)

    print("--- Formula Explorer Summary ---")
    print(f"Strategy: {args.strategy} | Generated: {len(candidates)} | Top Selected: {len(top_formulas)}")
    print("-" * 50)

    for idx, formula in enumerate(top_formulas, 1):
        metrics = calculate_diversity_scores(formula)
        score = composite_interestingness(metrics)
        form_str = to_string(formula)
        print(f"[{idx}] Score: {score:.2f} | Depth: {metrics.ast_size} | {form_str}")

    if args.filter_file or explorer.filter.storage_path:
        explorer.filter.save_state()
        print(f"Saved filter state ({len(explorer.filter)} formulas seen).")

    db.close()
    return 0


def cmd_prove(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'prove' command."""
    target_str = args.target_pos or args.target
    if not target_str:
        print("Error: Target formula string is required.")
        return 1

    signature = get_combined_signature()
    target_formula = parse_formula(target_str, signature=signature)
    premise_formulas = [parse_formula(p, signature=signature) for p in args.premises]

    if args.stubs_only:
        print(f"Parsed target formula successfully: {to_string(target_formula)}")
        return 0

    prover = TheoremProver(signature=signature, config=config)
    try:
        proof_dag = prover.prove(
            target=target_formula,
            premises=premise_formulas,
            max_steps=args.max_steps,
            timeout_sec=args.timeout,
        )
        print(f"SUCCESS: Theorem proved! ({len(proof_dag.steps)} proof steps)")
        if proof_dag.is_valid(signature=signature):
            print("VERIFIED: ProofDAG passes validity check.")

        if args.save:
            db_path = args.db_path or config.db_path
            db = KnowledgeDatabase(db_path)
            if hasattr(db, "insert_proved_theorem"):
                db.insert_proved_theorem(name="cli_proved_theorem", formula=target_formula, proof=proof_dag)
            else:
                db.add_theorem(name="cli_proved_theorem", formula=target_formula, proof=proof_dag)
            db.close()
            print("SAVED: Theorem stored in database.")
        return 0
    except (SolverError, ProofTimeoutError) as e:
        print(f"FAILED: {e}")
        logger.error(f"Prover failure: {e}")
        return 1


def cmd_analyze(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'analyze' command."""
    db_path = args.db_path or (args.db if args.db != "logic_data.db" or Path("logic_data.db").exists() else config.db_path)
    if not Path(db_path).exists():
        print(f"No theorems found in database '{db_path}'.")
        return 0

    db = KnowledgeDatabase(db_path)
    theorems = db.get_theorems(category=args.category)
    if not theorems:
        theorems = db.get_axioms(category=args.category)

    if not theorems:
        print(f"No theorems found in database '{db_path}'.")
        db.close()
        return 0

    formulas = [(t[0], t[1]) if isinstance(t, tuple) else (t.name, t.formula) for t in theorems]
    signature = get_combined_signature()
    prover = TheoremProver(signature=signature, config=config)

    print(f"Analyzing network dependencies for {len(formulas)} theorems...")
    graph = analyze_dependencies(formulas, prover, pairwise=args.pairwise)
    eq_classes = compute_equivalence_classes(formulas, prover)

    print("\n--- Analysis Summary ---")
    print(f"Total Nodes (Formulas): {len(graph.nodes)}")
    print(f"Total Directed Edges:   {len(graph.edges)}")
    print(f"Equivalence Classes:    {len(eq_classes)}")

    for idx, eq_set in enumerate(eq_classes, 1):
        if len(eq_set) > 1:
            print(f"  Class {idx}: {sorted(list(eq_set))}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(graph.to_dict(), f, indent=2)
        print(f"\nDependency graph exported to '{args.output}'.")

    db.close()
    return 0


def cmd_export_lean(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'export lean' command."""
    db_path = args.db_path or config.db_path
    exporter = LeanExporter()
    theorems_to_export = []

    if Path(db_path).exists():
        db = KnowledgeDatabase(db_path)
        if args.theorems:
            raw_theorems = []
            for name in args.theorems:
                t_list = [t for t in db.get_theorems() if t[0] == name]
                if not t_list:
                    t_list = [a for a in db.get_axioms() if a[0] == name]
                raw_theorems.extend(t_list)
        else:
            raw_theorems = db.get_theorems()
            if not raw_theorems:
                raw_theorems = db.get_axioms()

        for name, formula in raw_theorems:
            proof = None if args.stubs_only else db.get_proof(name)
            theorems_to_export.append((name, formula, proof))
        db.close()

    if not theorems_to_export:
        logger.warning(f"No theorems found to export in database '{db_path}'. Generating preamble.")

    output_path = args.output or "output.lean"
    exporter.export_file(output_path, theorems_to_export, stubs_only=args.stubs_only)
    print(f"Exported LEAN file to '{output_path}'.")
    return 0


def cmd_export_graph(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'export graph' command."""
    db_path = args.db_path or config.db_path
    exporter = GraphExporter()
    output_path = args.output or "graph.html"

    if args.type == "proof":
        if not Path(db_path).exists():
            print(f"Error: Database file '{db_path}' not found.")
            return 1
        db = KnowledgeDatabase(db_path)
        theorem_name = args.theorem
        if not theorem_name:
            all_thms = db.get_theorems()
            if all_thms:
                theorem_name = all_thms[0][0]
            else:
                print(f"Error: No theorems found in database '{db_path}'.")
                db.close()
                return 1

        proof = db.get_proof(theorem_name)
        db.close()
        if proof is None or not hasattr(proof, "steps"):
            print(f"Error: No ProofDAG found for theorem '{theorem_name}'.")
            return 1

        exporter.export_proof_to_html(proof, output_path, title=f"Proof DAG: {theorem_name}")
        print(f"Exported proof graph to '{output_path}'.")
        return 0

    elif args.type == "dependency":
        if not Path(db_path).exists():
            print(f"Error: Database file '{db_path}' not found.")
            return 1
        db = KnowledgeDatabase(db_path)
        theorems = db.get_theorems()
        if not theorems:
            theorems = db.get_axioms()

        formulas = [(t[0], t[1]) if isinstance(t, tuple) else (t.name, t.formula) for t in theorems]
        signature = get_combined_signature()
        prover = TheoremProver(signature=signature, config=config)
        graph = analyze_dependencies(formulas, prover)
        db.close()

        exporter.export_dependency_network_to_html(graph, output_path, title="Theorem Dependency Network")
        print(f"Exported dependency network graph to '{output_path}'.")
        return 0

    return 1


def cmd_docs(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'docs' command."""
    output_dir = args.output_dir or "docs"
    docs_created = build_markdown_docs(source_dir="logic_prover", output_docs_dir=output_dir)
    print(f"Successfully generated {len(docs_created)} documentation files under '{output_dir}/'.")
    logger.info(f"Generated {len(docs_created)} documentation files under '{output_dir}/'.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for CLI invocation.

    Args:
        argv: Optional list of argument strings (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 for success, non-zero for failure.
    """
    config = SolverConfig()
    setup_logging(config=config)

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2

    try:
        if args.command == "init":
            return cmd_init(args, config)
        elif args.command == "explore":
            return cmd_explore(args, config)
        elif args.command == "prove":
            return cmd_prove(args, config)
        elif args.command == "analyze":
            return cmd_analyze(args, config)
        elif args.command == "export":
            if args.export_type == "lean":
                return cmd_export_lean(args, config)
            elif args.export_type == "graph":
                return cmd_export_graph(args, config)
        elif args.command == "docs":
            return cmd_docs(args, config)
    except (SolverError, ParseError, Exception) as e:
        print(f"Error executing command '{args.command}': {e}", file=sys.stderr)
        logger.error(f"Command '{args.command}' failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
