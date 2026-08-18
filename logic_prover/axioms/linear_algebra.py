"""Linear algebra, vector spaces, and inner product spaces axioms, signatures, and Theory definitions."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import (
    Formula, Variable, Constant, FunctionApp, PredicateApp, Equality,
    Forall, Iff
)
from logic_prover.core.sorts import PrimitiveSort, Ind
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory

Vector: PrimitiveSort = PrimitiveSort("Vector")
Scalar: PrimitiveSort = PrimitiveSort("Scalar")


def get_linear_algebra_signature() -> Signature:
    """Constructs the signature for Linear Algebra (vector spaces and inner products).

    Registers sorts Vector and Scalar, constants 'vzero', 'szero', 'sone', vector operations
    'vadd', 'vneg', 'smul_v', scalar operations 'sadd', 'smul', 'sneg', inner product 'dot',
    'norm_sq', and predicate 'orthogonal'.

    Returns:
        Signature: The initialized linear algebra Signature instance.

    Example:
        >>> sig = get_linear_algebra_signature()
        >>> sig.has_symbol("vadd") and sig.has_symbol("smul_v") and sig.has_symbol("dot")
        True
    """
    sig = Signature()
    sig.register_constant("vzero", Vector)
    sig.register_constant("szero", Scalar)
    sig.register_constant("sone", Scalar)

    sig.register_function("vadd", 2, (Vector, Vector), Vector)
    sig.register_function("vneg", 1, (Vector,), Vector)
    sig.register_function("smul_v", 2, (Scalar, Vector), Vector)

    sig.register_function("sadd", 2, (Scalar, Scalar), Scalar)
    sig.register_function("smul", 2, (Scalar, Scalar), Scalar)
    sig.register_function("sneg", 1, (Scalar,), Scalar)

    sig.register_function("dot", 2, (Vector, Vector), Scalar)
    sig.register_function("norm_sq", 1, (Vector,), Scalar)

    sig.register_predicate("sle", 2, (Ind, Ind))
    sig.register_predicate("orthogonal", 2, (Vector, Vector))
    return sig


def get_linear_algebra_axioms() -> List[Tuple[str, Formula]]:
    """Generates the fundamental First-Order Axioms of Linear Algebra.

    Includes:
    - Vector space abelian group axioms (vadd assoc, comm, identity vzero, inverse vneg)
    - Scalar multiplication axioms (associativity, identity sone, vector/scalar distributivity)
    - Inner product axioms (symmetry, bilinearity, zero vector dot product, orthogonality)

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for linear algebra.

    Example:
        >>> axioms = get_linear_algebra_axioms()
        >>> len(axioms) == 14
        True
        >>> axioms[0][0]
        'vec_add_assoc'
    """
    vzero = Constant("vzero", sort=Vector)
    szero = Constant("szero", sort=Scalar)
    sone = Constant("sone", sort=Scalar)

    u = Variable(0, sort=Vector)
    v = Variable(1, sort=Vector)
    w = Variable(2, sort=Vector)

    a = Variable(3, sort=Scalar)
    b = Variable(4, sort=Scalar)
    c = Variable(5, sort=Scalar)

    # 1. vec_add_assoc: forall u v w, vadd(vadd(u, v), w) = vadd(u, vadd(v, w))
    vadd_uv = FunctionApp("vadd", 2, (u, v), return_sort=Vector)
    vadd_vw = FunctionApp("vadd", 2, (v, w), return_sort=Vector)
    vec_add_assoc = Forall(
        u,
        Forall(
            v,
            Forall(
                w,
                Equality(
                    FunctionApp("vadd", 2, (vadd_uv, w), return_sort=Vector),
                    FunctionApp("vadd", 2, (u, vadd_vw), return_sort=Vector),
                ),
            ),
        ),
    )

    # 2. vec_add_comm: forall u v, vadd(u, v) = vadd(v, u)
    vadd_vu = FunctionApp("vadd", 2, (v, u), return_sort=Vector)
    vec_add_comm = Forall(u, Forall(v, Equality(vadd_uv, vadd_vu)))

    # 3. vec_add_zero: forall v, vadd(v, vzero) = v
    vadd_v_zero = FunctionApp("vadd", 2, (v, vzero), return_sort=Vector)
    vec_add_zero = Forall(v, Equality(vadd_v_zero, v))

    # 4. vec_add_inv: forall v, vadd(v, vneg(v)) = vzero
    vneg_v = FunctionApp("vneg", 1, (v,), return_sort=Vector)
    vadd_v_negv = FunctionApp("vadd", 2, (v, vneg_v), return_sort=Vector)
    vec_add_inv = Forall(v, Equality(vadd_v_negv, vzero))

    # 5. vec_smul_assoc: forall a b v, smul_v(a, smul_v(b, v)) = smul_v(smul(a, b), v)
    smul_bv = FunctionApp("smul_v", 2, (b, v), return_sort=Vector)
    smul_a_bv = FunctionApp("smul_v", 2, (a, smul_bv), return_sort=Vector)
    smul_ab = FunctionApp("smul", 2, (a, b), return_sort=Scalar)
    smul_ab_v = FunctionApp("smul_v", 2, (smul_ab, v), return_sort=Vector)
    vec_smul_assoc = Forall(a, Forall(b, Forall(v, Equality(smul_a_bv, smul_ab_v))))

    # 6. vec_smul_one: forall v, smul_v(sone, v) = v
    smul_1_v = FunctionApp("smul_v", 2, (sone, v), return_sort=Vector)
    vec_smul_one = Forall(v, Equality(smul_1_v, v))

    # 7. vec_distrib_vector: forall a u v, smul_v(a, vadd(u, v)) = vadd(smul_v(a, u), smul_v(a, v))
    smul_a_uv = FunctionApp("smul_v", 2, (a, vadd_uv), return_sort=Vector)
    smul_au = FunctionApp("smul_v", 2, (a, u), return_sort=Vector)
    smul_av = FunctionApp("smul_v", 2, (a, v), return_sort=Vector)
    vadd_sau_sav = FunctionApp("vadd", 2, (smul_au, smul_av), return_sort=Vector)
    vec_distrib_vector = Forall(a, Forall(u, Forall(v, Equality(smul_a_uv, vadd_sau_sav))))

    # 8. vec_distrib_scalar: forall a b v, smul_v(sadd(a, b), v) = vadd(smul_v(a, v), smul_v(b, v))
    sadd_ab = FunctionApp("sadd", 2, (a, b), return_sort=Scalar)
    smul_sadd_ab_v = FunctionApp("smul_v", 2, (sadd_ab, v), return_sort=Vector)
    smul_bv_val = FunctionApp("smul_v", 2, (b, v), return_sort=Vector)
    vadd_sav_sbv = FunctionApp("vadd", 2, (smul_av, smul_bv_val), return_sort=Vector)
    vec_distrib_scalar = Forall(a, Forall(b, Forall(v, Equality(smul_sadd_ab_v, vadd_sav_sbv))))

    # 9. vec_dot_comm: forall u v, dot(u, v) = dot(v, u)
    dot_uv = FunctionApp("dot", 2, (u, v), return_sort=Scalar)
    dot_vu = FunctionApp("dot", 2, (v, u), return_sort=Scalar)
    vec_dot_comm = Forall(u, Forall(v, Equality(dot_uv, dot_vu)))

    # 10. vec_dot_add_distrib: forall u v w, dot(vadd(u, v), w) = sadd(dot(u, w), dot(v, w))
    dot_vadd_uv_w = FunctionApp("dot", 2, (vadd_uv, w), return_sort=Scalar)
    dot_uw = FunctionApp("dot", 2, (u, w), return_sort=Scalar)
    dot_vw = FunctionApp("dot", 2, (v, w), return_sort=Scalar)
    sadd_dot_uw_vw = FunctionApp("sadd", 2, (dot_uw, dot_vw), return_sort=Scalar)
    vec_dot_add_distrib = Forall(u, Forall(v, Forall(w, Equality(dot_vadd_uv_w, sadd_dot_uw_vw))))

    # 11. vec_dot_smul: forall c u v, dot(smul_v(c, u), v) = smul(c, dot(u, v))
    smul_cu = FunctionApp("smul_v", 2, (c, u), return_sort=Vector)
    dot_smul_cu_v = FunctionApp("dot", 2, (smul_cu, v), return_sort=Scalar)
    smul_c_dot_uv = FunctionApp("smul", 2, (c, dot_uv), return_sort=Scalar)
    vec_dot_smul = Forall(c, Forall(u, Forall(v, Equality(dot_smul_cu_v, smul_c_dot_uv))))

    # 12. vec_dot_zero: forall v, dot(vzero, v) = szero
    dot_vzero_v = FunctionApp("dot", 2, (vzero, v), return_sort=Scalar)
    vec_dot_zero = Forall(v, Equality(dot_vzero_v, szero))

    # 13. vec_norm_sq_def: forall v, norm_sq(v) = dot(v, v)
    norm_sq_v = FunctionApp("norm_sq", 1, (v,), return_sort=Scalar)
    dot_vv = FunctionApp("dot", 2, (v, v), return_sort=Scalar)
    vec_norm_sq_def = Forall(v, Equality(norm_sq_v, dot_vv))

    # 14. vec_orthogonal_def: forall u v, (orthogonal(u, v) <=> dot(u, v) = szero)
    orth_uv = PredicateApp("orthogonal", 2, (u, v))
    vec_orthogonal_def = Forall(u, Forall(v, Iff(orth_uv, Equality(dot_uv, szero))))

    return [
        ("vec_add_assoc", vec_add_assoc),
        ("vec_add_comm", vec_add_comm),
        ("vec_add_zero", vec_add_zero),
        ("vec_add_inv", vec_add_inv),
        ("vec_smul_assoc", vec_smul_assoc),
        ("vec_smul_one", vec_smul_one),
        ("vec_distrib_vector", vec_distrib_vector),
        ("vec_distrib_scalar", vec_distrib_scalar),
        ("vec_dot_comm", vec_dot_comm),
        ("vec_dot_add_distrib", vec_dot_add_distrib),
        ("vec_dot_smul", vec_dot_smul),
        ("vec_dot_zero", vec_dot_zero),
        ("vec_norm_sq_def", vec_norm_sq_def),
        ("vec_orthogonal_def", vec_orthogonal_def),
    ]


# Instantiated Theory object
linear_algebra_theory: Theory = Theory(
    name="linear_algebra",
    description="First-order theory of linear algebra (vector spaces, scalar multiplication, inner products, orthogonality).",
    sorts={"Vector": Vector, "Scalar": Scalar},
    signature=get_linear_algebra_signature(),
    axioms=dict(get_linear_algebra_axioms()),
)
register_theory(linear_algebra_theory)
