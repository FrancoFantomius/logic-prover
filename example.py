from solver.deducer import Deducer, deduce_consequences
# Example 1: Deduce group theory consequences focusing on domain axioms (grp_*)
consequences = deduce_consequences(
    hypotheses=["f(e, e) = e"],
    require_axioms=True,
    target_axiom_prefix="grp_"
)
for c in consequences:
    print(f"Derived: {c.formula_str} via {c.justification_type}")
# Example 2: Pure Modus Ponens deduction between hypotheses (disable axiom requirement)
results = deduce_consequences(
    hypotheses=["p -> q", "q -> r", "p"],
    require_axioms=False,
    exclude_pure_hypotheses=False
)
for res in results:
    print(f"Consequence: {res.formula_str}")