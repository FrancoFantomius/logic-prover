"""
Solver Dependencies Subpackage
==============================
Contains axiom packages and foundational logic theories for first-order logic,
second-order logic, and modular theory exploration.
"""

from .first_order_logic import (
    FIRST_ORDER_AXIOMS,
    FOL_PROPOSITIONAL_AXIOMS,
    FOL_QUANTIFIER_AXIOMS,
    FOL_EQUALITY_AXIOMS,
    get_first_order_axioms,
    load_first_order_axioms,
)

from .second_order_logic import (
    SECOND_ORDER_AXIOMS,
    SOL_QUANTIFIER_AXIOMS,
    SOL_STRUCTURAL_AXIOMS,
    SOL_INDUCTION_AXIOMS,
    get_second_order_axioms,
    load_second_order_axioms,
)

from .logic import (
    LOGIC_AXIOMS,
    get_all_logic_axioms,
    load_all_logic_axioms,
)

__all__ = [
    "FIRST_ORDER_AXIOMS",
    "FOL_PROPOSITIONAL_AXIOMS",
    "FOL_QUANTIFIER_AXIOMS",
    "FOL_EQUALITY_AXIOMS",
    "get_first_order_axioms",
    "load_first_order_axioms",
    "SECOND_ORDER_AXIOMS",
    "SOL_QUANTIFIER_AXIOMS",
    "SOL_STRUCTURAL_AXIOMS",
    "SOL_INDUCTION_AXIOMS",
    "get_second_order_axioms",
    "load_second_order_axioms",
    "LOGIC_AXIOMS",
    "get_all_logic_axioms",
    "load_all_logic_axioms",
]
