"""
Unified Logic Axioms Module
===========================
Aggregates Propositional, First-Order, and Second-Order logic axioms
and provides high-level convenience utilities for loading them into a TheoryDatabase.
"""

from ..database import TheoryDatabase
from .first_order_logic import FIRST_ORDER_AXIOMS, load_first_order_axioms, get_first_order_axioms
from .second_order_logic import SECOND_ORDER_AXIOMS, load_second_order_axioms, get_second_order_axioms

LOGIC_AXIOMS = {
    **FIRST_ORDER_AXIOMS,
    **SECOND_ORDER_AXIOMS,
}


def get_all_logic_axioms():
    """Restituisce un dizionario completo con tutti gli assiomi del primo e del secondo ordine."""
    return dict(LOGIC_AXIOMS)


def load_all_logic_axioms(db: TheoryDatabase):
    """Carica tutti gli assiomi del primo e del secondo ordine nel database fornito."""
    load_first_order_axioms(db)
    load_second_order_axioms(db)
