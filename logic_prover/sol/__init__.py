"""Second-Order Logic (SOL) extension module providing higher-order quantification and pattern matching."""

from logic.sol.ast_ext import (
    PredicateVariable, FunctionVariable,
    ForallPred, ExistsPred, ForallFunc, ExistsFunc,
    free_predicate_variables, bound_predicate_variables,
    free_function_variables, bound_function_variables
)

__all__ = [
    "PredicateVariable",
    "FunctionVariable",
    "ForallPred",
    "ExistsPred",
    "ForallFunc",
    "ExistsFunc",
    "free_predicate_variables",
    "bound_predicate_variables",
    "free_function_variables",
    "bound_function_variables",
    "ho_pattern_unify",
    "is_ho_pattern",
    "beta_reduce_predicate",
    "beta_reduce_function",
    "substitute_predicate",
    "substitute_function",
    "get_sol_axioms",
    "instantiate_comprehension",
    "instantiate_induction",
    "SOLInstantiateRule",
]


def __getattr__(name: str):
    if name in (
        "ho_pattern_unify", "is_ho_pattern",
        "beta_reduce_predicate", "beta_reduce_function",
        "substitute_predicate", "substitute_function"
    ):
        import logic.sol.substitutions_ext as sub_ext
        return getattr(sub_ext, name)
    elif name in ("get_sol_axioms", "instantiate_comprehension", "instantiate_induction"):
        import logic.sol.kb_ext as kb_ext
        return getattr(kb_ext, name)
    elif name == "SOLInstantiateRule":
        from logic.prover.rules import SOLInstantiateRule
        return SOLInstantiateRule
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
