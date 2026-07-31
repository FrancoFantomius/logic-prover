"""
Group Theory Axioms Module
==========================
Contains Group Theory axioms compatible with Solver.
"""

from solver.database import TheoryDatabase
from solver.formula import parse_formula

# Group Theory axioms
GROUP_AXIOMS = {
    # Associativity: ∀x ∀y ∀z ((x * y) * z = x * (y * z))
    "group_assoc": "forall x, forall y, forall z, (f(f(x, y), z) = f(x, f(y, z)))",
    
    # Left Identity: ∀x (e * x = x)
    "group_identity_left": "forall x, (f(e, x) = x)",
    
    # Right Identity: ∀x (x * e = x)
    "group_identity_right": "forall x, (f(x, e) = x)",
    
    # Left Inverse: ∀x (inv(x) * x = e)
    "group_inverse_left": "forall x, (f(inv(x), x) = e)",
    
    # Right Inverse: ∀x (x * inv(x) = e)
    "group_inverse_right": "forall x, (f(x, inv(x)) = e)",
    
    # Commutativity (Abelian Groups): ∀x ∀y (x * y = y * x)
    "group_comm": "forall x, forall y, (f(x, y) = f(y, x))",
}


def get_group_axioms():
    """Returns a dictionary containing all Group Theory axioms."""
    return dict(GROUP_AXIOMS)


def load_group_axioms(db: TheoryDatabase, include_fol: bool = False):
    """
    Loads all Group Theory axioms into the specified theory database.
    If include_fol is True, also loads First-Order Logic (FOL) axioms.
    """
    if include_fol:
        from solver.dependencies.first_order_logic import load_first_order_axioms
        load_first_order_axioms(db)

    for name, formula_str in GROUP_AXIOMS.items():
        db.add_axiom(name, formula_str)


def explore_group_theory(db_path: str = "group_theory.db", basic_vars=None, max_depth: int = 1, max_theorems: int = 20, include_fol: bool = False):
    """
    Initializes the database, loads Group Theory axioms, and starts exploring logical consequences.
    """
    from solver.explorer import explore_consequences
    if basic_vars is None:
        basic_vars = ['x', 'y', 'z']
    db = TheoryDatabase(db_path)
    load_group_axioms(db, include_fol=include_fol)
    return explore_consequences(db, basic_vars=basic_vars, max_depth=max_depth, max_theorems=max_theorems)


if __name__ == "__main__":
    explore_group_theory()


