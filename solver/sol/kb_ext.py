"""Second-Order Logic knowledge base extensions (induction schemas, comprehension axioms)."""

from __future__ import annotations
from typing import List, Tuple, Optional

from solver.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp,
    Forall, Implies, And, Iff, Exists, Equality
)
from solver.core.sorts import Ind, Nat
from solver.sol.ast_ext import PredicateVariable, FunctionVariable, ForallPred, ExistsPred, ForallFunc
from solver.core.substitutions import substitute_formula


def get_sol_axioms() -> List[Tuple[str, Formula]]:
    """
    Returns the core Second-Order Logic axioms and schemas:
    1. Second-Order Comprehension Schema (unary and binary predicate variants)
    2. Second-Order Peano Induction Principle
    3. Predicate Extensionality Principle
    4. Function Extensionality Principle
    """
    p_var1 = PredicateVariable(0, 1)
    p_ex1 = PredicateVariable(1, 1)
    x = Variable(0, sort=Ind)
    comp_unary = ForallPred(
        p_var1,
        ExistsPred(
            p_ex1,
            Forall(
                x,
                Iff(
                    left=PredicateApp(p_ex1, 1, (x,)),
                    right=PredicateApp(p_var1, 1, (x,))
                )
            )
        )
    )

    p_var2 = PredicateVariable(0, 2)
    p_ex2 = PredicateVariable(1, 2)
    y = Variable(1, sort=Ind)
    comp_binary = ForallPred(
        p_var2,
        ExistsPred(
            p_ex2,
            Forall(
                x,
                Forall(
                    y,
                    Iff(
                        left=PredicateApp(p_ex2, 2, (x, y)),
                        right=PredicateApp(p_var2, 2, (x, y))
                    )
                )
            )
        )
    )

    p_ind = PredicateVariable(0, 1)
    n = Variable(0, sort=Nat)
    zero = Constant("zero", sort=Nat)
    succ_n = FunctionApp("succ", 1, (n,), return_sort=Nat)

    base = PredicateApp(p_ind, 1, (zero,))
    step = Forall(n, Implies(PredicateApp(p_ind, 1, (n,)), PredicateApp(p_ind, 1, (succ_n,))))
    hyp = And(base, step)
    conc = Forall(n, PredicateApp(p_ind, 1, (n,)))
    peano_induction = ForallPred(p_ind, Implies(hyp, conc))

    p_ext1 = PredicateVariable(0, 1)
    p_ext2 = PredicateVariable(1, 1)
    pred_ext = ForallPred(
        p_ext1,
        ForallPred(
            p_ext2,
            Implies(
                Forall(x, Iff(PredicateApp(p_ext1, 1, (x,)), PredicateApp(p_ext2, 1, (x,)))),
                Forall(x, Iff(PredicateApp(p_ext1, 1, (x,)), PredicateApp(p_ext2, 1, (x,))))
            )
        )
    )

    f_ext1 = FunctionVariable(0, 1, (Ind,), Ind)
    f_ext2 = FunctionVariable(1, 1, (Ind,), Ind)
    func_ext = ForallFunc(
        f_ext1,
        ForallFunc(
            f_ext2,
            Implies(
                Forall(x, Equality(FunctionApp(f_ext1, 1, (x,)), FunctionApp(f_ext2, 1, (x,)))),
                Forall(x, Equality(FunctionApp(f_ext1, 1, (x,)), FunctionApp(f_ext2, 1, (x,))))
            )
        )
    )

    return [
        ("sol_comprehension_unary", comp_unary),
        ("sol_comprehension_binary", comp_binary),
        ("sol_peano_induction", peano_induction),
        ("sol_predicate_extensionality", pred_ext),
        ("sol_function_extensionality", func_ext),
    ]


def instantiate_comprehension(
    pred_var: PredicateVariable,
    params: Tuple[Variable, ...],
    body: Formula
) -> Formula:
    """
    Constructs an explicit instance of the Second-Order Comprehension Schema for a given body formula φ(x_1, ..., x_k):
    ∃P. ∀x_1 ... ∀x_k. (P(x_1, ..., x_k) ⇔ φ(x_1, ..., x_k))
    """
    p_bound = PredicateVariable(index=pred_var.index + 100, arity=len(params))
    inner: Formula = Iff(
        left=PredicateApp(pred=p_bound, arity=len(params), args=params),
        right=body
    )
    for var in reversed(params):
        inner = Forall(variable=var, body=inner)
    return ExistsPred(variable=p_bound, body=inner)


def instantiate_induction(
    property_formula: Formula,
    bound_var: Variable,
    zero_term: Optional[Term] = None,
    succ_func_name: str = "succ"
) -> Formula:
    """
    Instantiates the Second-Order Peano Induction Principle for a specific property formula φ(n):
    (φ(0) ∧ ∀n. (φ(n) ⇒ φ(S(n)))) ⇒ ∀n. φ(n)
    """
    if zero_term is None:
        zero_term = Constant("zero", sort=bound_var.sort)

    succ_term = FunctionApp(func=succ_func_name, arity=1, args=(bound_var,), return_sort=bound_var.sort)

    base_case = substitute_formula(property_formula, {bound_var: zero_term})
    step_body = substitute_formula(property_formula, {bound_var: succ_term})
    step_case = Forall(variable=bound_var, body=Implies(left=property_formula, right=step_body))

    hypothesis = And(left=base_case, right=step_case)
    conclusion = Forall(variable=bound_var, body=property_formula)

    return Implies(left=hypothesis, right=conclusion)
