"""
Second-Order Logic (SOL) Axioms Module
================----------------------
Contains standard axiom schemas for Second-Order Logic (SOL),
including Second-Order Quantifiers, Comprehension Schema, Second-Order Choice,
and Mathematical Induction in Second-Order Form.
"""

from ..database import TheoryDatabase
from ..formula import parse_formula, Formula

# ---------------------------------------------------------------------------
# 1. Second-Order Quantifier Axiom Schemas
# ---------------------------------------------------------------------------
SOL_QUANTIFIER_AXIOMS = {
    # Second-Order Universal Instantiation: ∀P Φ(P) -> Φ(R)
    "sol_ui": "(forall P, Phi(P)) -> Phi(R)",
    
    # Second-Order Universal Distribution: ∀P (A -> Φ(P)) -> (A -> ∀P Φ(P))
    "sol_ug": "(forall P, (A -> Phi(P))) -> (A -> (forall P, Phi(P)))",
    
    # Second-Order Existential Generalization: Φ(R) -> ∃P Φ(P)
    "sol_eg": "Phi(R) -> (exists P, Phi(P))",
    
    # Second-Order Existential Distribution: ∀P (Phi(P) -> A) -> ((exists P, Phi(P)) -> A)
    "sol_ed": "(forall P, (Phi(P) -> A)) -> ((exists P, Phi(P)) -> A)",
}

# ---------------------------------------------------------------------------
# 2. Second-Order Structural Axioms (Comprehension & Choice)
# ---------------------------------------------------------------------------
SOL_STRUCTURAL_AXIOMS = {
    # Schema of Comprehension: ∃P ∀x (P(x) <-> φ(x))
    # Expresses that every logical formula defines a predicate/relation
    "sol_comp": "exists P, (forall x, (P(x) <-> phi(x)))",
    
    # Second-Order Axiom of Choice (Relational / Functional Form)
    # ∀x ∃P Φ(x, P) -> ∃Q ∀x Φ(x, Q(x))
    "sol_choice": "(forall x, (exists P, Phi(x, P))) -> (exists Q, (forall x, Phi(x, Q(x))))",
}

# ---------------------------------------------------------------------------
# 3. Second-Order Induction Axiom Schema
# ---------------------------------------------------------------------------
SOL_INDUCTION_AXIOMS = {
    # Second-Order Mathematical Induction Schema:
    # ∀P ((P(zero) & ∀x (P(x) -> P(succ(x)))) -> ∀x P(x))
    "sol_induction": "forall P, (((P(zero) & (forall x, (P(x) -> P(succ(x)))))) -> (forall x, P(x)))",
}

# ---------------------------------------------------------------------------
# Consolidated Second-Order Logic Axioms Dictionary
# ---------------------------------------------------------------------------
SECOND_ORDER_AXIOMS = {
    **SOL_QUANTIFIER_AXIOMS,
    **SOL_STRUCTURAL_AXIOMS,
    **SOL_INDUCTION_AXIOMS,
}


def get_second_order_axioms():
    """Restituisce un dizionario contenente tutti gli assiomi della logica del secondo ordine."""
    return dict(SECOND_ORDER_AXIOMS)


def load_second_order_axioms(db: TheoryDatabase):
    """Carica tutti gli assiomi della logica del secondo ordine nel database delle teorie specificato."""
    for name, formula_str in SECOND_ORDER_AXIOMS.items():
        db.add_axiom(name, formula_str)
