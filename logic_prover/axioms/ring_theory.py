"""Ring and field theory axioms, signatures, and Theory definitions."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import Formula, Variable, Constant, FunctionApp, Equality, Forall, Implies, Not
from logic_prover.core.sorts import PrimitiveSort
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory

RingElem: PrimitiveSort = PrimitiveSort("RingElem")


def get_ring_signature() -> Signature:
    """Constructs the signature for algebraic Ring and Field theories.

    Registers constants 'rzero', 'rone', addition 'radd', negation 'rneg',
    multiplication 'rmul', and inverse 'rinv'.

    Returns:
        Signature: The initialized ring theory Signature instance.

    Example:
        >>> sig = get_ring_signature()
        >>> sig.has_symbol("radd") and sig.has_symbol("rmul") and sig.has_symbol("rzero")
        True
    """
    sig = Signature()
    sig.register_constant("rzero", RingElem)
    sig.register_constant("rone", RingElem)
    sig.register_function("radd", 2, (RingElem, RingElem), RingElem)
    sig.register_function("rmul", 2, (RingElem, RingElem), RingElem)
    sig.register_function("rneg", 1, (RingElem,), RingElem)
    sig.register_function("rinv", 1, (RingElem,), RingElem)
    return sig


def get_ring_axioms() -> List[Tuple[str, Formula]]:
    """Generates the fundamental First-Order Axioms for a Ring with unity.

    Includes:
    - Abelian group for addition (assoc, comm, zero, additive inverse)
    - Monoid for multiplication (assoc, left/right unity)
    - Distributivity (left and right)

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for ring theory.

    Example:
        >>> axioms = get_ring_axioms()
        >>> len(axioms) == 9
        True
        >>> axioms[0][0]
        'ring_add_assoc'
    """
    rzero = Constant("rzero", sort=RingElem)
    rone = Constant("rone", sort=RingElem)

    x = Variable(0, sort=RingElem)
    y = Variable(1, sort=RingElem)
    z = Variable(2, sort=RingElem)

    # 1. ring_add_assoc
    add_xy = FunctionApp("radd", 2, (x, y), return_sort=RingElem)
    add_yz = FunctionApp("radd", 2, (y, z), return_sort=RingElem)
    ring_add_assoc = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Equality(
                    FunctionApp("radd", 2, (add_xy, z), return_sort=RingElem),
                    FunctionApp("radd", 2, (x, add_yz), return_sort=RingElem),
                ),
            ),
        ),
    )

    # 2. ring_add_comm
    add_yx = FunctionApp("radd", 2, (y, x), return_sort=RingElem)
    ring_add_comm = Forall(x, Forall(y, Equality(add_xy, add_yx)))

    # 3. ring_add_zero
    add_x0 = FunctionApp("radd", 2, (x, rzero), return_sort=RingElem)
    ring_add_zero = Forall(x, Equality(add_x0, x))

    # 4. ring_add_inv
    neg_x = FunctionApp("rneg", 1, (x,), return_sort=RingElem)
    add_x_negx = FunctionApp("radd", 2, (x, neg_x), return_sort=RingElem)
    ring_add_inv = Forall(x, Equality(add_x_negx, rzero))

    # 5. ring_mul_assoc
    mul_xy = FunctionApp("rmul", 2, (x, y), return_sort=RingElem)
    mul_yz = FunctionApp("rmul", 2, (y, z), return_sort=RingElem)
    ring_mul_assoc = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Equality(
                    FunctionApp("rmul", 2, (mul_xy, z), return_sort=RingElem),
                    FunctionApp("rmul", 2, (x, mul_yz), return_sort=RingElem),
                ),
            ),
        ),
    )

    # 6. ring_distrib_left: x * (y + z) = (x * y) + (x * z)
    mul_x_add_yz = FunctionApp("rmul", 2, (x, add_yz), return_sort=RingElem)
    mul_xz = FunctionApp("rmul", 2, (x, z), return_sort=RingElem)
    add_mul_xy_xz = FunctionApp("radd", 2, (mul_xy, mul_xz), return_sort=RingElem)
    ring_distrib_left = Forall(x, Forall(y, Forall(z, Equality(mul_x_add_yz, add_mul_xy_xz))))

    # 7. ring_distrib_right: (x + y) * z = (x * z) + (y * z)
    mul_add_xy_z = FunctionApp("rmul", 2, (add_xy, z), return_sort=RingElem)
    mul_yz_val = FunctionApp("rmul", 2, (y, z), return_sort=RingElem)
    add_mul_xz_yz = FunctionApp("radd", 2, (mul_xz, mul_yz_val), return_sort=RingElem)
    ring_distrib_right = Forall(x, Forall(y, Forall(z, Equality(mul_add_xy_z, add_mul_xz_yz))))

    # 8. ring_mul_one_left: 1 * x = x
    mul_1x = FunctionApp("rmul", 2, (rone, x), return_sort=RingElem)
    ring_mul_one_left = Forall(x, Equality(mul_1x, x))

    # 9. ring_mul_one_right: x * 1 = x
    mul_x1 = FunctionApp("rmul", 2, (x, rone), return_sort=RingElem)
    ring_mul_one_right = Forall(x, Equality(mul_x1, x))

    return [
        ("ring_add_assoc", ring_add_assoc),
        ("ring_add_comm", ring_add_comm),
        ("ring_add_zero", ring_add_zero),
        ("ring_add_inv", ring_add_inv),
        ("ring_mul_assoc", ring_mul_assoc),
        ("ring_distrib_left", ring_distrib_left),
        ("ring_distrib_right", ring_distrib_right),
        ("ring_mul_one_left", ring_mul_one_left),
        ("ring_mul_one_right", ring_mul_one_right),
    ]


def get_field_axioms() -> List[Tuple[str, Formula]]:
    """Generates the Field Theory axioms extending commutative ring axioms with non-triviality and multiplicative inverse.

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for field theory.

    Example:
        >>> axioms = get_field_axioms()
        >>> len(axioms) == 12
        True
    """
    axioms = get_ring_axioms()

    rzero = Constant("rzero", sort=RingElem)
    rone = Constant("rone", sort=RingElem)

    x = Variable(0, sort=RingElem)
    y = Variable(1, sort=RingElem)

    # Commutativity of multiplication
    mul_xy = FunctionApp("rmul", 2, (x, y), return_sort=RingElem)
    mul_yx = FunctionApp("rmul", 2, (y, x), return_sort=RingElem)
    ring_mul_comm = Forall(x, Forall(y, Equality(mul_xy, mul_yx)))

    # Non-triviality: ~(0 = 1)
    field_non_trivial = Not(Equality(rzero, rone))

    # Multiplicative inverse: forall x, (~(x = 0) => x * inv(x) = 1)
    inv_x = FunctionApp("rinv", 1, (x,), return_sort=RingElem)
    mul_x_invx = FunctionApp("rmul", 2, (x, inv_x), return_sort=RingElem)
    field_mul_inv = Forall(x, Implies(Not(Equality(x, rzero)), Equality(mul_x_invx, rone)))

    axioms.extend([
        ("ring_mul_comm", ring_mul_comm),
        ("field_non_trivial", field_non_trivial),
        ("field_mul_inv", field_mul_inv),
    ])
    return axioms


# Instantiated Theory objects
ring_theory: Theory = Theory(
    name="ring_theory",
    description="First-order theory of rings with unity and distributivity.",
    sorts={"RingElem": RingElem},
    signature=get_ring_signature(),
    axioms=dict(get_ring_axioms()),
)
register_theory(ring_theory)

field_theory: Theory = Theory(
    name="field_theory",
    description="First-order theory of fields (commutative rings with multiplicative inverses and non-triviality).",
    sorts={"RingElem": RingElem},
    signature=get_ring_signature(),
    axioms=dict(get_field_axioms()),
)
register_theory(field_theory)
