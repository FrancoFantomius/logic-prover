"""Function theory axioms (injective, surjective, bijective, identity)."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import (
    Formula, Variable, Constant, FunctionApp, PredicateApp, Equality, Forall, Exists, Implies, And, Iff
)
from logic_prover.core.sorts import PrimitiveSort, Ind
from logic_prover.core.signature import Signature

Dom: PrimitiveSort = PrimitiveSort("Dom")
Codom: PrimitiveSort = PrimitiveSort("Codom")
FuncSort: PrimitiveSort = PrimitiveSort("Func")


def get_function_signature() -> Signature:
    """Returns signature declaring function concepts (apply, comp, id_func, is_injective, etc.)."""
    sig = Signature()
    sig.register_function("apply", 2, (FuncSort, Ind), Ind)
    sig.register_function("comp", 2, (FuncSort, FuncSort), FuncSort)
    sig.register_constant("id_func", FuncSort)
    sig.register_predicate("is_injective", 1, (FuncSort,))
    sig.register_predicate("is_surjective", 1, (FuncSort,))
    sig.register_predicate("is_bijective", 1, (FuncSort,))
    return sig


def get_function_axioms() -> List[Tuple[str, Formula]]:
    """Returns function concept axioms: composition, injectivity, surjectivity, bijectivity, identity function."""
    f = Variable(0, sort=FuncSort)
    g = Variable(1, sort=FuncSort)
    x = Variable(2, sort=Dom)
    y = Variable(3, sort=Dom)
    z = Variable(4, sort=Codom)

    id_f = Constant("id_func", sort=FuncSort)

    afx = FunctionApp("apply", 2, (f, x), return_sort=Ind)
    afy = FunctionApp("apply", 2, (f, y), return_sort=Ind)

    # 1. func_well_defined: forall f forall x forall y, (x = y => apply(f, x) = apply(f, y))
    func_well_defined = Forall(
        f,
        Forall(
            x,
            Forall(y, Implies(Equality(x, y), Equality(afx, afy))),
        ),
    )

    # 2. func_comp_def: forall g forall f forall x, apply(comp(g, f), x) = apply(g, apply(f, x))
    comp_gf = FunctionApp("comp", 2, (g, f), return_sort=FuncSort)
    acomp = FunctionApp("apply", 2, (comp_gf, x), return_sort=Ind)
    ag_afx = FunctionApp("apply", 2, (g, afx), return_sort=Ind)
    func_comp_def = Forall(
        g,
        Forall(
            f,
            Forall(x, Equality(acomp, ag_afx)),
        ),
    )

    # 3. func_injective_def: forall f, (is_injective(f) <=> forall x forall y, (apply(f, x) = apply(f, y) => x = y))
    inj_f = PredicateApp("is_injective", 1, (f,))
    func_injective_def = Forall(
        f,
        Iff(
            inj_f,
            Forall(
                x,
                Forall(y, Implies(Equality(afx, afy), Equality(x, y))),
            ),
        ),
    )

    # 4. func_surjective_def: forall f, (is_surjective(f) <=> forall z, exists x, apply(f, x) = z)
    surj_f = PredicateApp("is_surjective", 1, (f,))
    afx_eq_z = Equality(afx, z)
    func_surjective_def = Forall(
        f,
        Iff(
            surj_f,
            Forall(z, Exists(x, afx_eq_z)),
        ),
    )

    # 5. func_bijective_def: forall f, (is_bijective(f) <=> (is_injective(f) & is_surjective(f)))
    bij_f = PredicateApp("is_bijective", 1, (f,))
    func_bijective_def = Forall(
        f,
        Iff(bij_f, And(inj_f, surj_f)),
    )

    # 6. func_id_def: forall x, apply(id_func, x) = x
    aid_x = FunctionApp("apply", 2, (id_f, x), return_sort=Ind)
    func_id_def = Forall(x, Equality(aid_x, x))

    return [
        ("func_well_defined", func_well_defined),
        ("func_comp_def", func_comp_def),
        ("func_injective_def", func_injective_def),
        ("func_surjective_def", func_surjective_def),
        ("func_bijective_def", func_bijective_def),
        ("func_id_def", func_id_def),
    ]
