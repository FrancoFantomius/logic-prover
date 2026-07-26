"""
Group Theory Axioms Module
==========================
Contiene gli assiomi della Teoria dei Gruppi compatibili con Solver.
"""

from solver.database import TheoryDatabase
from solver.formula import parse_formula

# Assiomi della teoria dei gruppi
GROUP_AXIOMS = {
    # Associatività: ∀x ∀y ∀z ((x * y) * z = x * (y * z))
    "group_assoc": "forall x, forall y, forall z, (f(f(x, y), z) = f(x, f(y, z)))",
    
    # Elemento neutro a sinistra: ∀x (e * x = x)
    "group_identity_left": "forall x, (f(e, x) = x)",
    
    # Elemento neutro a destra: ∀x (x * e = x)
    "group_identity_right": "forall x, (f(x, e) = x)",
    
    # Elemento inverso a sinistra: ∀x (inv(x) * x = e)
    "group_inverse_left": "forall x, (f(inv(x), x) = e)",
    
    # Elemento inverso a destra: ∀x (x * inv(x) = e)
    "group_inverse_right": "forall x, (f(x, inv(x)) = e)",
    
    # Commutatività (Gruppi Abeliani): ∀x ∀y (x * y = y * x)
    "group_comm": "forall x, forall y, (f(x, y) = f(y, x))",
}


def get_group_axioms():
    """Restituisce il dizionario contenente gli assiomi della teoria dei gruppi."""
    return dict(GROUP_AXIOMS)


def load_group_axioms(db: TheoryDatabase, include_fol: bool = False):
    """
    Carica tutti gli assiomi della teoria dei gruppi nel database specificato.
    Se include_fol è True, carica anche gli assiomi della Logica del Primo Ordine (FOL).
    """
    if include_fol:
        from solver.dependencies.first_order_logic import load_first_order_axioms
        load_first_order_axioms(db)

    for name, formula_str in GROUP_AXIOMS.items():
        db.add_axiom(name, formula_str)


def explore_group_theory(db_path: str = "group_theory.db", basic_vars=None, max_depth: int = 1, max_theorems: int = 20, include_fol: bool = False):
    """
    Inizializza il database, carica gli assiomi della teoria dei gruppi ed avvia l'esplorazione delle conseguenze logiche.
    """
    from solver.explorer import explore_consequences
    if basic_vars is None:
        basic_vars = ['x', 'y', 'z']
    db = TheoryDatabase(db_path)
    load_group_axioms(db, include_fol=include_fol)
    return explore_consequences(db, basic_vars=basic_vars, max_depth=max_depth, max_theorems=max_theorems)


if __name__ == "__main__":
    explore_group_theory()


