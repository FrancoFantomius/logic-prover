"""Example 01: Build, parse, and inspect logic formulas.

This example shows the two ways of constructing formulas with the library:

1. Programmatically, by composing the typed AST node classes directly
   (``Variable``, ``Constant``, ``PredicateApp``, ``And``, ``Forall``, ...).
2. From a string, using ``parse_formula`` with a ``Signature`` that declares
   every predicate, function, constant, and sort the formula may use.

It also demonstrates the inspection helpers ``to_string``, ``free_variables``,
``formula_depth``, and ``formula_size`` that the rest of the library builds on.

Run it with:

    python examples/01_formula_construction.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

from logic_prover.core.ast import (
    Variable, Constant, PredicateApp, Equality, Implies, Forall,
    free_variables, formula_depth, formula_size,
)
from logic_prover.core.sorts import Ind
from logic_prover.core.signature import Signature
from logic_prover.core.parser import parse_formula, to_string


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Programmatic AST construction
    # ------------------------------------------------------------------
    # Variables are indexed and typed with a sort. Use id=0, 1, ... for
    # distinct variables and re-use the same object for the same variable.
    x = Variable(id=0, sort=Ind)

    # Constants carry a name and a sort.
    a = Constant(name="a", sort=Ind)

    # A predicate application P(x) - predicates are registered by name in
    # the signature, but building the AST directly does not need one.
    px = PredicateApp(pred="P", arity=1, args=(x,))
    pa = PredicateApp(pred="P", arity=1, args=(a,))

    # Combine nodes with the standard connectives and quantifiers.
    formula = Forall(
        variable=x,
        body=Implies(left=px, right=Equality(left=x, right=a)),
    )

    print("AST-built formula:", to_string(formula, notation="infix"))
    print("Free variables   :", sorted(v.id for v in free_variables(formula)))
    print("AST depth        :", formula_depth(formula))
    print("AST size         :", formula_size(formula))
    print()

    # ------------------------------------------------------------------
    # 2. String parsing against a declared Signature
    # ------------------------------------------------------------------
    # The parser validates every symbol against the signature, so declare
    # P, Q, and a before parsing strings that use them.
    sig = Signature()
    sig.register_predicate("P", 1, (Ind,))
    sig.register_predicate("Q", 1, (Ind,))
    sig.register_constant("a", sort=Ind)

    # Infix notation mirrors the ASCII connectives: ~, &, |, =>, <=>.
    parsed = parse_formula("forall v0 : Ind, P(v0) => (Q(v0) & P(a))", signature=sig)
    print("Parsed formula   :", to_string(parsed, notation="infix"))

    # Prefix (Lisp-style) notation is also accepted and round-trips.
    round_tripped = parse_formula(to_string(parsed, notation="prefix"), signature=sig)
    print("Round-trips      :", round_tripped == parsed)

    # Unknown or mis-typed symbols raise ParseError instead of failing silently.
    try:
        parse_formula("UnknownPredicate(v0)", signature=sig)
    except Exception as exc:  # ParseError
        print("Parser diagnostic:", type(exc).__name__, "-", exc)


if __name__ == "__main__":
    main()
