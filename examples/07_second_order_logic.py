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
