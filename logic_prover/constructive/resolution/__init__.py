"""Resolution theorem proving with prefixing and relational translation for Intuitionistic Logic.

This package provides two resolution theorem proving methods for Intuitionistic
Propositional Logic (IPC):
1. Prefixed Resolution: Direct clausal resolution over signed prefixed literals
   (p : A^pol) using intuitionistic T-string prefix unification and reduction ordering
   admissibility checks (Wallen 1990; Fitting 1990; Mints 1990; Otten & Kreitz 1996).
2. Relational Translation Resolution: Standard relational S4 translation embedding IPC
   into classical First-Order Logic (FOL) with reflexivity, transitivity, and monotonicity
   frame axioms, delegating refutation proof search to the classical First-Order
   resolution engine (TheoremProver).
"""

from __future__ import annotations

from logic_prover.constructive.resolution.clauses import (
    PrefixedLiteral,
    PrefixedClause,
    PrefixedResolutionStep,
    PrefixedResolutionProofResult,
    clausify_prefixed,
)
from logic_prover.constructive.resolution.prefixed import (
    _try_unify_formulas,
    resolve_prefixed_clauses,
    factor_prefixed_clause,
    _paramodulate_clauses,
    PrefixedResolutionProver,
    prove_prefixed_resolution,
)
from logic_prover.constructive.resolution.translation import (
    translate_ipc_to_fol,
    get_frame_axioms,
    _extract_predicate_declarations,
    _extract_predicate_names,
    TranslationResolutionResult,
    TranslationResolutionProver,
    prove_translation_resolution,
)
from logic_prover.constructive.resolution.prover import (
    ConstructiveResolutionProver,
    prove_resolution,
)

__all__ = [
    # Prefixed resolution structures
    "PrefixedLiteral",
    "PrefixedClause",
    "PrefixedResolutionStep",
    "PrefixedResolutionProofResult",
    # Prefixed operations & prover
    "clausify_prefixed",
    "resolve_prefixed_clauses",
    "factor_prefixed_clause",
    "PrefixedResolutionProver",
    "prove_prefixed_resolution",
    # Translation resolution
    "translate_ipc_to_fol",
    "get_frame_axioms",
    "TranslationResolutionResult",
    "TranslationResolutionProver",
    "prove_translation_resolution",
    # Unified resolution prover & API
    "ConstructiveResolutionProver",
    "prove_resolution",
]
