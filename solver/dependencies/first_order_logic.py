"""
First-Order Logic (FOL) Axioms Module
=====================================
Contains standard Hilbert-style axiom schemas for First-Order Logic (FOL),
including Propositional Calculus, Quantifier Rules, and Equality (Leibniz) Axioms.
"""

from ..database import TheoryDatabase
from ..formula import parse_formula, Formula

# ---------------------------------------------------------------------------
# 1. Propositional Calculus Axioms (Hilbert System Basis)
# ---------------------------------------------------------------------------
FOL_PROPOSITIONAL_AXIOMS = {
    # ax1: Simplification / Positive Paradox: A -> (B -> A)
    "fol_k": "A -> (B -> A)",
    
    # ax2: Distribution / Frege's Axiom: (A -> (B -> C)) -> ((A -> B) -> (A -> C))
    "fol_s": "(A -> (B -> C)) -> ((A -> B) -> (A -> C))",
    
    # ax3: Contraposition / Double Negation Variant: (~A -> ~B) -> (B -> A)
    "fol_dn": "(~A -> ~B) -> (B -> A)",
}

# ---------------------------------------------------------------------------
# 2. First-Order Quantifier Axiom Schemas
# ---------------------------------------------------------------------------
FOL_QUANTIFIER_AXIOMS = {
    # Universal Instantiation (Specification Schema): ∀x P(x) -> P(t)
    "fol_ui": "(forall x, P(x)) -> P(t)",
    
    # Universal Generalization / Quantifier Distribution: ∀x (A -> B(x)) -> (A -> ∀x B(x))
    "fol_ug": "(forall x, (A -> B(x))) -> (A -> (forall x, B(x)))",
    
    # Existential Generalization (Introduction): P(t) -> ∃x P(x)
    "fol_eg": "P(t) -> (exists x, P(x))",
    
    # Existential Distribution / Elimination Schema: ∀x (P(x) -> A) -> (∃x P(x) -> A)
    "fol_ed": "(forall x, (P(x) -> A)) -> ((exists x, P(x)) -> A)",
}

# ---------------------------------------------------------------------------
# 3. First-Order Equality (Identity & Leibniz) Axioms
# ---------------------------------------------------------------------------
FOL_EQUALITY_AXIOMS = {
    # Reflexivity of Equality: ∀x (x = x)
    "eq_ref": "forall x, (x = x)",
    
    # Symmetry of Equality: ∀x ∀y (x = y -> y = x)
    "eq_sym": "forall x, forall y, ((x = y) -> (y = x))",
    
    # Transitivity of Equality: ∀x ∀y ∀z ((x = y) -> ((y = z) -> (x = z)))
    "eq_trans": "forall x, forall y, forall z, ((x = y) -> ((y = z) -> (x = z)))",
    
    # Substitution / Congruence (Leibniz's Law): ∀x ∀y ((x = y) -> (P(x) -> P(y)))
    "eq_subst": "forall x, forall y, ((x = y) -> (P(x) -> P(y)))",
}

# ---------------------------------------------------------------------------
# Consolidated First-Order Logic Axioms Dictionary
# ---------------------------------------------------------------------------
FIRST_ORDER_AXIOMS = {
    **FOL_PROPOSITIONAL_AXIOMS,
    **FOL_QUANTIFIER_AXIOMS,
    **FOL_EQUALITY_AXIOMS,
}


def get_first_order_axioms():
    """Returns a dictionary containing all First-Order Logic axioms."""
    return dict(FIRST_ORDER_AXIOMS)


def load_first_order_axioms(db: TheoryDatabase):
    """Loads all First-Order Logic axioms into the specified theory database."""
    for name, formula_str in FIRST_ORDER_AXIOMS.items():
        db.add_axiom(name, formula_str)
