"""Real analysis, ordered fields, and metric space axioms, signatures, and Theory definitions."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import (
    Formula, Variable, Constant, FunctionApp, PredicateApp, Equality,
    Forall, Implies, And, Or, Not, Iff
)
from logic_prover.core.sorts import PrimitiveSort, Ind
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory

Real: PrimitiveSort = PrimitiveSort("Real")


def get_analysis_signature() -> Signature:
    """Constructs the signature for Real Analysis (ordered fields and metric spaces).

    Registers constants 'real_zero', 'real_one', arithmetic functions 'real_add', 'real_mul',
    'real_neg', 'real_inv', metric functions 'abs_val', 'dist', and order predicates 'le', 'lt', 'ge', 'gt'.

    Returns:
        Signature: The initialized real analysis Signature instance.

    Example:
        >>> sig = get_analysis_signature()
        >>> sig.has_symbol("real_add") and sig.has_symbol("dist") and sig.has_symbol("le")
        True
    """
    sig = Signature()
    sig.register_constant("real_zero", Real)
    sig.register_constant("real_one", Real)
    sig.register_function("real_add", 2, (Real, Real), Real)
    sig.register_function("real_mul", 2, (Real, Real), Real)
    sig.register_function("real_neg", 1, (Real,), Real)
    sig.register_function("real_inv", 1, (Real,), Real)
    sig.register_function("abs_val", 1, (Real,), Real)
    sig.register_function("dist", 2, (Real, Real), Real)
    sig.register_predicate("le", 2, (Ind, Ind))
    sig.register_predicate("lt", 2, (Ind, Ind))
    sig.register_predicate("ge", 2, (Ind, Ind))
    sig.register_predicate("gt", 2, (Ind, Ind))
    return sig


def get_analysis_axioms() -> List[Tuple[str, Formula]]:
    """Generates the fundamental First-Order Axioms for Real Analysis.

    Includes:
    - Field operations (addition & multiplication assoc, comm, id, inv, distrib, non-triviality)
    - Ordered field properties (reflexivity, antisymmetry, transitivity, totality, compatibility)
    - Metric and absolute value properties (positivity, symmetry, triangle inequalities)

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for real analysis.

    Example:
        >>> axioms = get_analysis_axioms()
        >>> len(axioms) >= 15
        True
        >>> axioms[0][0]
        'real_add_assoc'
    """
    zero = Constant("real_zero", sort=Real)
    one = Constant("real_one", sort=Real)

    x = Variable(0, sort=Real)
    y = Variable(1, sort=Real)
    z = Variable(2, sort=Real)

    # 1. real_add_assoc: forall x y z, (x + y) + z = x + (y + z)
    add_xy = FunctionApp("real_add", 2, (x, y), return_sort=Real)
    add_yz = FunctionApp("real_add", 2, (y, z), return_sort=Real)
    real_add_assoc = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Equality(
                    FunctionApp("real_add", 2, (add_xy, z), return_sort=Real),
                    FunctionApp("real_add", 2, (x, add_yz), return_sort=Real),
                ),
            ),
        ),
    )

    # 2. real_add_comm: forall x y, x + y = y + x
    add_yx = FunctionApp("real_add", 2, (y, x), return_sort=Real)
    real_add_comm = Forall(x, Forall(y, Equality(add_xy, add_yx)))

    # 3. real_add_zero: forall x, x + 0 = x
    add_x0 = FunctionApp("real_add", 2, (x, zero), return_sort=Real)
    real_add_zero = Forall(x, Equality(add_x0, x))

    # 4. real_add_inv: forall x, x + (-x) = 0
    neg_x = FunctionApp("real_neg", 1, (x,), return_sort=Real)
    add_x_negx = FunctionApp("real_add", 2, (x, neg_x), return_sort=Real)
    real_add_inv = Forall(x, Equality(add_x_negx, zero))

    # 5. real_mul_assoc: forall x y z, (x * y) * z = x * (y * z)
    mul_xy = FunctionApp("real_mul", 2, (x, y), return_sort=Real)
    mul_yz = FunctionApp("real_mul", 2, (y, z), return_sort=Real)
    real_mul_assoc = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Equality(
                    FunctionApp("real_mul", 2, (mul_xy, z), return_sort=Real),
                    FunctionApp("real_mul", 2, (x, mul_yz), return_sort=Real),
                ),
            ),
        ),
    )

    # 6. real_mul_comm: forall x y, x * y = y * x
    mul_yx = FunctionApp("real_mul", 2, (y, x), return_sort=Real)
    real_mul_comm = Forall(x, Forall(y, Equality(mul_xy, mul_yx)))

    # 7. real_mul_one: forall x, x * 1 = x
    mul_x1 = FunctionApp("real_mul", 2, (x, one), return_sort=Real)
    real_mul_one = Forall(x, Equality(mul_x1, x))

    # 8. real_distrib: forall x y z, x * (y + z) = (x * y) + (x * z)
    mul_x_add_yz = FunctionApp("real_mul", 2, (x, add_yz), return_sort=Real)
    mul_xz = FunctionApp("real_mul", 2, (x, z), return_sort=Real)
    add_mul_xy_mul_xz = FunctionApp("real_add", 2, (mul_xy, mul_xz), return_sort=Real)
    real_distrib = Forall(x, Forall(y, Forall(z, Equality(mul_x_add_yz, add_mul_xy_mul_xz))))

    # 9. real_non_trivial: ~(0 = 1)
    real_non_trivial = Not(Equality(zero, one))

    # 10. real_order_refl: forall x, x <= x
    le_xx = PredicateApp("le", 2, (x, x))
    real_order_refl = Forall(x, le_xx)

    # 11. real_order_antisymm: forall x y, ((x <= y & y <= x) => x = y)
    le_xy = PredicateApp("le", 2, (x, y))
    le_yx = PredicateApp("le", 2, (y, x))
    real_order_antisymm = Forall(x, Forall(y, Implies(And(le_xy, le_yx), Equality(x, y))))

    # 12. real_order_trans: forall x y z, ((x <= y & y <= z) => x <= z)
    le_yz = PredicateApp("le", 2, (y, z))
    le_xz = PredicateApp("le", 2, (x, z))
    real_order_trans = Forall(x, Forall(y, Forall(z, Implies(And(le_xy, le_yz), le_xz))))

    # 13. real_order_total: forall x y, (x <= y | y <= x)
    real_order_total = Forall(x, Forall(y, Or(le_xy, le_yx)))

    # 14. real_order_add_compat: forall x y z, (x <= y => (x + z) <= (y + z))
    add_xz = FunctionApp("real_add", 2, (x, z), return_sort=Real)
    add_yz_val = FunctionApp("real_add", 2, (y, z), return_sort=Real)
    le_add = PredicateApp("le", 2, (add_xz, add_yz_val))
    real_order_add_compat = Forall(x, Forall(y, Forall(z, Implies(le_xy, le_add))))

    # 15. real_order_mul_compat: forall x y, ((0 <= x & 0 <= y) => 0 <= (x * y))
    le_0x = PredicateApp("le", 2, (zero, x))
    le_0y = PredicateApp("le", 2, (zero, y))
    le_0_mul_xy = PredicateApp("le", 2, (zero, mul_xy))
    real_order_mul_compat = Forall(x, Forall(y, Implies(And(le_0x, le_0y), le_0_mul_xy)))

    # 16. real_lt_def: forall x y, (x < y <=> (x <= y & ~(x = y)))
    lt_xy = PredicateApp("lt", 2, (x, y))
    real_lt_def = Forall(x, Forall(y, Iff(lt_xy, And(le_xy, Not(Equality(x, y))))))

    # 17. real_abs_pos: forall x, 0 <= abs_val(x)
    abs_x = FunctionApp("abs_val", 1, (x,), return_sort=Real)
    abs_y = FunctionApp("abs_val", 1, (y,), return_sort=Real)
    abs_add_xy = FunctionApp("abs_val", 1, (add_xy,), return_sort=Real)
    add_abs_x_abs_y = FunctionApp("real_add", 2, (abs_x, abs_y), return_sort=Real)
    real_abs_pos = Forall(x, PredicateApp("le", 2, (zero, abs_x)))

    # 18. real_abs_triangle: forall x y, abs_val(x + y) <= abs_val(x) + abs_val(y)
    real_abs_triangle = Forall(x, Forall(y, PredicateApp("le", 2, (abs_add_xy, add_abs_x_abs_y))))

    # 19. real_dist_pos: forall x y, 0 <= dist(x, y)
    dist_xy = FunctionApp("dist", 2, (x, y), return_sort=Real)
    dist_yx = FunctionApp("dist", 2, (y, x), return_sort=Real)
    dist_xz = FunctionApp("dist", 2, (x, z), return_sort=Real)
    dist_yz = FunctionApp("dist", 2, (y, z), return_sort=Real)
    add_dist_xy_dist_yz = FunctionApp("real_add", 2, (dist_xy, dist_yz), return_sort=Real)

    real_dist_pos = Forall(x, Forall(y, PredicateApp("le", 2, (zero, dist_xy))))

    # 20. real_dist_eq_zero: forall x y, (dist(x, y) = 0 <=> x = y)
    real_dist_eq_zero = Forall(x, Forall(y, Iff(Equality(dist_xy, zero), Equality(x, y))))

    # 21. real_dist_symm: forall x y, dist(x, y) = dist(y, x)
    real_dist_symm = Forall(x, Forall(y, Equality(dist_xy, dist_yx)))

    # 22. real_dist_triangle: forall x y z, dist(x, z) <= dist(x, y) + dist(y, z)
    real_dist_triangle = Forall(x, Forall(y, Forall(z, PredicateApp("le", 2, (dist_xz, add_dist_xy_dist_yz)))))

    return [
        ("real_add_assoc", real_add_assoc),
        ("real_add_comm", real_add_comm),
        ("real_add_zero", real_add_zero),
        ("real_add_inv", real_add_inv),
        ("real_mul_assoc", real_mul_assoc),
        ("real_mul_comm", real_mul_comm),
        ("real_mul_one", real_mul_one),
        ("real_distrib", real_distrib),
        ("real_non_trivial", real_non_trivial),
        ("real_order_refl", real_order_refl),
        ("real_order_antisymm", real_order_antisymm),
        ("real_order_trans", real_order_trans),
        ("real_order_total", real_order_total),
        ("real_order_add_compat", real_order_add_compat),
        ("real_order_mul_compat", real_order_mul_compat),
        ("real_lt_def", real_lt_def),
        ("real_abs_pos", real_abs_pos),
        ("real_abs_triangle", real_abs_triangle),
        ("real_dist_pos", real_dist_pos),
        ("real_dist_eq_zero", real_dist_eq_zero),
        ("real_dist_symm", real_dist_symm),
        ("real_dist_triangle", real_dist_triangle),
    ]


# Instantiated Theory object
analysis_theory: Theory = Theory(
    name="analysis",
    description="First-order Real Analysis theory covering ordered fields, absolute values, and metric spaces.",
    sorts={"Real": Real},
    signature=get_analysis_signature(),
    axioms=dict(get_analysis_axioms()),
)
register_theory(analysis_theory)
