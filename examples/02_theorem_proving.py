"""Example 02: Prove theorems with the resolution prover.

Shows how to run the ``TheoremProver`` on propositional and first-order
targets, with and without premises, and how to validate the returned
``ProofDAG``.

Two prover configurations are covered:

- A hand-rolled ``Signature`` for toy predicate-logic examples (modus
  ponens, Peirce's law, quantifier reasoning).
- The built-in Peano arithmetic knowledge base, where real theorems such as
  ``add(zero, zero) = zero`` are proved from the Peano axioms.

Run it with:

    python examples/02_theorem_proving.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, Or, And, Implies, Forall, Exists,
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.core.signature import Signature
from logic_prover.prover.engine import TheoremProver
from logic_prover.axioms.peano import get_peano_signature, get_peano_axioms


def build_toy_signature() -> Signature:
    """Declares a minimal predicate-logic signature used by the examples."""
    sig = Signature()
    sig.register_predicate("P", 1, (Ind,))
    sig.register_predicate("Q", 1, (Ind,))
    sig.register_predicate("R", 2, (Ind, Ind))
    sig.register_predicate("PropP", 0, ())
    sig.register_predicate("PropQ", 0, ())
    sig.register_constant("a", Ind)
    sig.register_function("f", 1, (Ind,), return_sort=Ind)
    return sig


def prove_and_report(prover: TheoremProver, target, premises=None, label: str = "") -> None:
    """Attempts a proof and prints whether it succeeded and validates the DAG."""
    proof = prover.prove(target=target, premises=premises or [])
    status = "proved" if proof.is_valid() else "INVALID"
    print(f"[{label}] {status} in {len(proof.steps)} steps")
    return proof


def main() -> None:
    sig = build_toy_signature()
    prover = TheoremProver(signature=sig)

    p = PredicateApp(pred="PropP", arity=0, args=())
    q = PredicateApp(pred="PropQ", arity=0, args=())

    # ------------------------------------------------------------------
    # 1. Propositional logic
    # ------------------------------------------------------------------
    # A tautology needs no premises: P or not P.
    prove_and_report(prover, Or(left=p, right=Not(operand=p)), label="P | ~P")

    # Modus ponens: from (P => Q) and P, prove Q.
    prove_and_report(
        prover,
        target=q,
        premises=[And(left=Implies(left=p, right=q), right=p)],
        label="modus ponens",
    )

    # Peirce's law: ((P => Q) => P) => P.
    prove_and_report(
        prover,
        target=Implies(left=Implies(left=Implies(left=p, right=q), right=p), right=p),
        label="Peirce's law",
    )

    # ------------------------------------------------------------------
    # 2. First-order logic
    # ------------------------------------------------------------------
    x = Variable(id=0, sort=Ind)
    y = Variable(id=1, sort=Ind)
    px = PredicateApp(pred="P", arity=1, args=(x,))
    rxy = PredicateApp(pred="R", arity=2, args=(x, y))

    # (forall x. P(x)) => (exists x. P(x))
    prove_and_report(
        prover,
        target=Implies(left=Forall(variable=x, body=px),
                       right=Exists(variable=x, body=px)),
        label="forall => exists",
    )

    # (exists x forall y. R(x,y)) => (forall y exists x. R(x,y))
    prove_and_report(
        prover,
        target=Implies(
            left=Exists(variable=x, body=Forall(variable=y, body=rxy)),
            right=Forall(variable=y, body=Exists(variable=x, body=rxy)),
        ),
        label="exists/forall swap",
    )

    # ------------------------------------------------------------------
    # 3. Peano arithmetic from the built-in knowledge base
    # ------------------------------------------------------------------
    peano_sig = get_peano_signature()
    peano_axioms = [formula for _, formula in get_peano_axioms()]
    peano_prover = TheoremProver(signature=peano_sig)

    zero = Constant("zero", sort=Nat)
    add_0_0 = FunctionApp("add", 2, (zero, zero), return_sort=Nat)
    prove_and_report(
        peano_prover,
        target=Equality(left=add_0_0, right=zero),
        premises=peano_axioms,
        label="add(zero, zero) = zero",
    )


if __name__ == "__main__":
    main()
