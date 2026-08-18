"""Constructive and intuitionistic logic subsystems including LJT calculus and Wallen's matrix method."""

from __future__ import annotations

from logic_prover.constructive.common import (
    FALSUM,
    VERUM,
    _is_falsum,
    _is_verum,
    _is_atomic,
    normalize_formula,
    _formula_weight,
)
from logic_prover.constructive.prefix import (
    PrefixSymbol,
    PrefixConstant,
    PrefixVariable,
    Prefix,
    PrefixSubstitution,
    unify_prefixes,
    is_admissible,
)
from logic_prover.constructive.matrix import (
    PositionType,
    Position,
    FormulaTree,
    Connection,
)
from logic_prover.constructive.ljt import (
    Sequent,
    LJTProofNode,
    LJTProofTree,
    LJTProver,
    prove_ljt,
)
from logic_prover.constructive.wallen import (
    WallenProofResult,
    WallenProver,
    prove_wallen,
)
from logic_prover.constructive.kripke import (
    World,
    KripkeModel,
)
from logic_prover.constructive.tableau import (
    Sign,
    SignedFormula,
    TableauNode,
    TableauProofTree,
    TableauProofResult,
    TableauProver,
    prove_tableau,
)
from logic_prover.constructive.resolution import (
    PrefixedLiteral,
    PrefixedClause,
    PrefixedResolutionStep,
    PrefixedResolutionProofResult,
    clausify_prefixed,
    resolve_prefixed_clauses,
    factor_prefixed_clause,
    PrefixedResolutionProver,
    prove_prefixed_resolution,
    translate_ipc_to_fol,
    get_frame_axioms,
    TranslationResolutionResult,
    TranslationResolutionProver,
    prove_translation_resolution,
    ConstructiveResolutionProver,
    prove_resolution,
)

__all__ = [
    # Common
    "FALSUM",
    "VERUM",
    "_is_falsum",
    "_is_verum",
    "_is_atomic",
    "normalize_formula",
    "_formula_weight",
    # LJT
    "Sequent",
    "LJTProofNode",
    "LJTProofTree",
    "LJTProver",
    "prove_ljt",
    # Prefix
    "PrefixSymbol",
    "PrefixConstant",
    "PrefixVariable",
    "Prefix",
    "PrefixSubstitution",
    "unify_prefixes",
    "is_admissible",
    # Matrix
    "PositionType",
    "Position",
    "FormulaTree",
    "Connection",
    # Wallen
    "WallenProofResult",
    "WallenProver",
    "prove_wallen",
    # Tableau
    "Sign",
    "World",
    "SignedFormula",
    "KripkeModel",
    "TableauNode",
    "TableauProofTree",
    "TableauProofResult",
    "TableauProver",
    "prove_tableau",
    # Resolution
    "PrefixedLiteral",
    "PrefixedClause",
    "PrefixedResolutionStep",
    "PrefixedResolutionProofResult",
    "clausify_prefixed",
    "resolve_prefixed_clauses",
    "factor_prefixed_clause",
    "PrefixedResolutionProver",
    "prove_prefixed_resolution",
    "translate_ipc_to_fol",
    "get_frame_axioms",
    "TranslationResolutionResult",
    "TranslationResolutionProver",
    "prove_translation_resolution",
    "ConstructiveResolutionProver",
    "prove_resolution",
]

