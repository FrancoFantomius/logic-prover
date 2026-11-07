Step 1: plans/heyting-arithmetic.md — Already Completed
Status: Implemented in logic_prover.constructive.ha.
Provides the arithmetic axioms, quantifier handling, and induction scheme needed to prove constructive theorems over numbers.
Step 2: plans/proof-terms.md — Implement First (Core Prerequisite)

You cannot generate Python code without an intermediate functional representation.

Priority Phases to Implement:
Phase 0 (Term AST & Normalizer): Define ProofTerm (Var, Abs, App, Pair, Fst, Snd, Inl, Inr, Case, NatRec, Abort) in logic_prover/constructive/terms.py along with infer_type() and beta_normalize().
Phase 1 (LJT Extraction): Thread term annotations through LJTProver._search in logic_prover/constructive/ljt.py, so derivation rules produce lambda terms.
Phase 3 (Witness Extraction): Implement extract_witness to extract computational values for 
∃
∃ and 
∨
∨.
Step 3: plans/python-exporter.md — Implement Second (Delivers the Target Goal)

Directly translates the lambda terms produced in Step 2 into runnable Python code.

Phases to Implement:
Phase 0 & 1: Implement PythonExporter in logic_prover/exporters/python_exporter.py mapping ProofTerm nodes to Python ast.AST nodes (ast.FunctionDef, ast.Match, ast.Call, ast.Tuple).
Phase 2 & 3: Add normalization cleanup and the high-level export_function() / export_module() APIs using ast.unparse().
Phase 4 & 5: Wire --term-format python into the CLI and add unit tests that execute the generated code with exec().

Note on Critical Path: Steps 2 and 3 form the minimal viable path to generating Python code from logic proofs.

Step 4: plans/higher-order.md — Implement Last (Advanced / Research)
Why last?: This plan introduces Martin-Löf Dependent Type Theory (
Π
Π and 
Σ
Σ types, universes, identity types). It builds on top of proof-terms.md (generalizing simple types to dependent types), but it is not required for synthesizing standard Python functions and is the most complex theoretical component.