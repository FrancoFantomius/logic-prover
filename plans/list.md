Step 1: plans/heyting-arithmetic.md — Already Completed
Status: Implemented in logic_prover.constructive.ha.
Provides the arithmetic axioms, quantifier handling, and induction scheme needed to prove constructive theorems over numbers.
Step 2: plans/proof-terms.md — Completed
Status: Implemented in logic_prover.constructive.terms and logic_prover.constructive.ljt.
Provides typed lambda term AST, bidirectional type checking, capture-avoiding beta normalization, LJT term extraction, BHK witness extraction, and Lean 4 export.
Step 3: plans/python-exporter.md — Completed
Status: Implemented in logic_prover.exporters.python_exporter and logic_prover.exporters.python_runtime.
Directly translates extracted Curry-Howard lambda terms into executable, type-hinted Python functions and modules using standard library ast.AST and unparse. Supports Left/Right tagged unions, primitive recursion over Nat, and live code execution via exec().

Step 4: plans/higher-order.md — Implement Last (Advanced / Research)
Why last?: This plan introduces Martin-Löf Dependent Type Theory (
Π
Π and 
Σ
Σ types, universes, identity types). It builds on top of proof-terms.md (generalizing simple types to dependent types), but it is not required for synthesizing standard Python functions and is the most complex theoretical component.