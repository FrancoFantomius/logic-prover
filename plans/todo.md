# New Project Structure!
- lean_exporter: translates formulas into LEAN code
- graph_exporter: exports proof/deduction graphs into HTML
- explorer: generates new formulas to be proven
- prover: finds proofs for formulas
- deducer: analyzes relationships between hypotheses and consequences (IS IT REDUNDANT?)

Utility files, database/parser (former formula representation) are required.

Documentation: functions must be documented with docstrings directly in the files, and documentation must be automatically generated from them.

1. Reformat the formal language: Think of having infinitely indexed variables `v_n`, and axioms select a subset of these. Same for functions and constants, except functions and constants should not be used for creating new formula variable slots.
2. Base concepts must include: First-order and Second-order logic, sets, functions, numbers, and basic operations.
3. Encourage search for "diverse" formulas: Instead of infinite concatenations of the same formula (e.g. `A AND A AND A`), the explorer must construct a list of formulas and prefer those that utilize more axioms/variables/functions. A mechanism must also be implemented to ensure discarded formulas are not proposed again.