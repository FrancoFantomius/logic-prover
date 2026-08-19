"""
Command Line Interface (CLI) entry point for the logic library.

Supports all 6 logic commands:
- init: Initialize database with foundational logic axioms
- explore: Generate and rank novel candidate formulas
- prove: Attempt resolution proof for a target formula
- analyze: Conduct hypothesis deduction and dependency analysis
- export lean: Translate theorems and proofs to Lean 4 formal code
- export graph: Export interactive proof or dependency DAG HTML graphs
"""

from __future__ import annotations
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from logic_prover.config import SolverConfig
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.core.exceptions import SolverError, ParseError, ProofTimeoutError
from logic_prover.core.parser import parse_formula, to_string, tokenize, TokenType
from logic_prover.core.signature import PredicateDecl
from logic_prover.deducer import analyze_dependencies, compute_equivalence_classes
from logic_prover.explorer import FormulaExplorer, calculate_diversity_scores, composite_interestingness
from logic_prover.exporters import LeanExporter, GraphExporter
from logic_prover.axioms import get_all_axioms, get_combined_signature
from logic_prover.logging import get_logger, setup_logging
from logic_prover.prover import TheoremProver
from logic_prover.constructive.ljt import LJTProver
from logic_prover.constructive.tableau import TableauProver
from logic_prover.constructive.wallen import WallenProver
from logic_prover.constructive.resolution import TranslationResolutionProver

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

    # 3b. prove-intuitionistic command
    prove_int_parser = subparsers.add_parser(
        "prove-intuitionistic", help="Prove target formula in Intuitionistic Logic (IPC/IQC)"
    )
    prove_int_parser.add_argument(
        "target_pos", nargs="?", default=None, metavar="FORMULA", help="Target formula string to prove"
    )
    prove_int_parser.add_argument("--target", type=str, default=None, help="Target formula string to prove")
    prove_int_parser.add_argument("--premises", nargs="*", default=[], help="Space-separated premise formula strings")
    prove_int_parser.add_argument(
        "--method", choices=["ljt", "tableau", "wallen", "translation"], default="ljt", help="Intuitionistic proof engine method"
    )
    prove_int_parser.add_argument("--max-term-depth", type=int, default=2, help="Maximum term depth for quantifier instantiation")
    prove_int_parser.add_argument("--timeout", type=float, default=10.0, help="Prover wall-clock timeout in seconds")
    prove_int_parser.add_argument("--max-steps", type=int, default=1000, help="Maximum search steps")

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

    return parser


build_cli_parser = build_parser


def cmd_init(args: argparse.Namespace, config: SolverConfig) -> int:
    """
    Executes the 'init' command: creates the database (optionally resetting it) and
    populates it with all foundational axioms from the knowledge base.

    Args:
        args: Parsed command-line arguments. Uses `args.db_path` (falling back to
            `config.db_path`) as the SQLite file path and `args.reset` to force
            re-creation of the database.
        config: Global SolverConfig providing the default database path.

    Returns:
        Exit code 0 on success.
    """
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
    """
    Executes the 'explore' command: generates novel candidate formulas with the
    FormulaExplorer and prints the top-ranked candidates with their interestingness scores.

    Args:
        args: Parsed command-line arguments. Uses `args.db_path` (falling back to
            `config.db_path`) for the database, `args.strategy` for the generation
            strategy, `args.depth` and `args.count` for candidate generation limits,
            `args.top_k` for the number of displayed results, and `args.filter_file`
            for the persistent filter state path.
        config: Global SolverConfig passed to the FormulaExplorer.

    Returns:
        Exit code 0 on success.
    """
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
    """
    Executes the 'prove' command: attempts a resolution proof of the target formula
    from the given premises and prints success/failure information, optionally saving
    the proved theorem to the database.

    Args:
        args: Parsed command-line arguments. Uses `args.target_pos` or `args.target`
            as the target formula string, `args.premises` as the premise formula
            strings, `args.stubs_only` for syntax-only checking, `args.max_steps` and
            `args.timeout` for prover limits, `args.save` to store the theorem, and
            `args.db_path` (falling back to `config.db_path`) for the database.
        config: Global SolverConfig passed to the TheoremProver.

    Returns:
        Exit code 0 on success, 1 on failure or missing target.
    """
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


def cmd_prove_intuitionistic(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'prove-intuitionistic' command using constructive provers (LJT, Tableau, Wallen, Translation).

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        config (SolverConfig): Global SolverConfig providing defaults.

    Returns:
        int: Exit code 0 on success/provable, 1 on unprovable or error.

    Example:
        >>> import argparse
        >>> from logic_prover.config import SolverConfig
        >>> from logic_prover.__main__ import cmd_prove_intuitionistic
        >>> args = argparse.Namespace(target="P => P", target_pos=None, premises=[], method="ljt", max_term_depth=2, timeout=10.0, max_steps=1000)
        >>> cmd_prove_intuitionistic(args, SolverConfig())
        0
    """
    target_str = args.target or args.target_pos
    if not target_str:
        print("Error: No target formula provided to prove.", file=sys.stderr)
        return 1

    signature = get_combined_signature()
    for s in [target_str] + list(args.premises or []):
        tokens = tokenize(s)
        for i, tok in enumerate(tokens):
            if tok.type == TokenType.IDENTIFIER and tok.value not in ("Ind", "Nat", "Bool", "forall", "exists", "true", "false"):
                next_tok = tokens[i + 1] if i + 1 < len(tokens) else None
                if not next_tok or next_tok.type != TokenType.LPAREN:
                    signature.predicates[tok.value] = PredicateDecl(name=tok.value, arity=0, arg_sorts=())

    target_formula = parse_formula(target_str, signature=signature)
    premise_formulas = [parse_formula(p, signature=signature) for p in args.premises]

    method = getattr(args, "method", None) or config.constructive_method or "ljt"
    max_term_depth = getattr(args, "max_term_depth", None) or config.iqc_max_term_depth or 2

    print(f"Target formula: {to_string(target_formula)}")
    if premise_formulas:
        print(f"Premises: {', '.join(to_string(p) for p in premise_formulas)}")
    print(f"Method: {method}")

    if method == "ljt":
        prover = LJTProver(max_term_depth=max_term_depth)
        proof = prover.prove(target=target_formula, premises=premise_formulas)
        if proof is not None and proof.is_valid():
            print("SUCCESS: Formula is intuitionistically VALID (proven via LJT / G4ip).")
            print("\n--- Derivation Tree ---")
            print(proof.to_ascii())
            return 0
        else:
            print("FAILED: Formula could not be proven intuitionistically with LJT.")
            return 1
    elif method == "tableau":
        prover_tab = TableauProver(max_depth=getattr(args, "max_steps", 100))
        result_tab = prover_tab.prove(target=target_formula, premises=premise_formulas)
        if result_tab.is_valid:
            print("SUCCESS: Formula is intuitionistically VALID (proven via Semantic Tableau).")
            print("\n--- Tableau Tree ---")
            print(result_tab.to_string())
            return 0
        else:
            print("FAILED: Formula is intuitionistically UNPROVABLE.")
            if result_tab.countermodel:
                print("\n--- Falsifying Kripke Countermodel ---")
                print(result_tab.countermodel.to_string())
            return 1
    elif method == "wallen":
        prover_wal = WallenProver()
        result_wal = prover_wal.prove(target=target_formula, premises=premise_formulas)
        if result_wal.is_valid:
            print("SUCCESS: Formula is intuitionistically VALID (proven via Wallen Matrix Method).")
            print(result_wal.to_string())
            return 0
        else:
            print("FAILED: Formula could not be proven intuitionistically with Wallen matrix.")
            return 1
    elif method == "translation":
        prover_trans = TranslationResolutionProver(
            max_steps=getattr(args, "max_steps", 1000), timeout_sec=getattr(args, "timeout", 10.0)
        )
        result_trans = prover_trans.prove(target=target_formula, premises=premise_formulas)
        if result_trans is not None and result_trans.is_valid:
            print("SUCCESS: Formula is intuitionistically VALID (proven via Relational Translation Resolution).")
            print(result_trans.to_string())
            return 0
        else:
            print("FAILED: Formula could not be proven intuitionistically via Translation Resolution.")
            return 1
    else:
        print(f"Unknown constructive method '{method}'.", file=sys.stderr)
        return 1


def cmd_analyze(args: argparse.Namespace, config: SolverConfig) -> int:
    """
    Executes the 'analyze' command: performs dependency analysis and equivalence class
    computation over the theorems in the database and prints a summary, optionally
    exporting the dependency graph to a JSON file.

    Args:
        args: Parsed command-line arguments. Uses `args.db_path` (falling back to
            `args.db` and then `config.db_path`) for the database, `args.category` to
            filter theorems, `args.pairwise` to enable O(n^2) pairwise implication
            proofs, and `args.output` for the JSON export path.
        config: Global SolverConfig passed to the TheoremProver.

    Returns:
        Exit code 0 on success.
    """
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
    """
    Executes the 'export lean' command: exports theorems (with optional proofs) from
    the database to a Lean 4 formal proof file, or emits a preamble if none are found.

    Args:
        args: Parsed command-line arguments. Uses `args.db_path` (falling back to
            `config.db_path`) for the database, `args.theorems` to select specific
            theorem names, `args.stubs_only` to emit sorry stubs, and `args.output`
            for the target .lean file path.
        config: Global SolverConfig providing the default database path.

    Returns:
        Exit code 0 on success.
    """
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
    """
    Executes the 'export graph' command: exports either a proof DAG or a theorem
    dependency network to an interactive HTML visualization.

    Args:
        args: Parsed command-line arguments. Uses `args.db_path` (falling back to
            `config.db_path`) for the database, `args.type` ('proof' or 'dependency')
            to select the visualization, `args.theorem` for the target theorem name,
            and `args.output` for the target .html file path.
        config: Global SolverConfig providing the default database path.

    Returns:
        Exit code 0 on success, 1 on error.
    """
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


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for CLI invocation.

    Args:
        argv: Optional list of argument strings (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 for success, non-zero for failure.
    """
    config = SolverConfig()

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
        elif args.command == "prove-intuitionistic":
            return cmd_prove_intuitionistic(args, config)
        elif args.command == "analyze":
            return cmd_analyze(args, config)
        elif args.command == "export":
            if args.export_type == "lean":
                return cmd_export_lean(args, config)
            elif args.export_type == "graph":
                return cmd_export_graph(args, config)
    except (SolverError, ParseError, Exception) as e:
        print(f"Error executing command '{args.command}': {e}", file=sys.stderr)
        logger.error(f"Command '{args.command}' failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
