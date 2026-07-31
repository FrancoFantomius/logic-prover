"""
Deducer Module
==============
Forward Deduction Engine module.
Given a set of hypotheses and relying on axioms and prior formulas/theorems stored
in the theory database (TheoryDatabase), the Deducer derives logical consequences.
"""

import time
from typing import List, Dict, Set, Union, Optional
from .formula import (
    Formula, Var, Not, Implies, And, Or, Iff,
    Forall, Exists, Equals, Pred, parse_formula
)
from .database import TheoryDatabase
from .prover import reconstruct_proof
from .verifier import verify_proof_local


def _ensure_formula(f: Union[str, Formula]) -> Formula:
    """Converts a string or ensures the object is a Formula."""
    if isinstance(f, Formula):
        return f
    elif isinstance(f, str):
        return parse_formula(f)
    else:
        raise TypeError(f"Expected str or Formula, got {type(f)}")


def get_all_subformulas(formula: Formula) -> Set[Formula]:
    """Recursively extracts all subformulas of any Formula type."""
    subs = {formula}
    if isinstance(formula, Not):
        subs.update(get_all_subformulas(formula.formula))
    elif isinstance(formula, (Implies, And, Or, Iff, Equals)):
        subs.update(get_all_subformulas(formula.left))
        subs.update(get_all_subformulas(formula.right))
    elif isinstance(formula, (Forall, Exists)):
        subs.update(get_all_subformulas(formula.body))
    elif isinstance(formula, Pred):
        for arg in formula.args:
            if isinstance(arg, Formula):
                subs.update(get_all_subformulas(arg))
    return subs


class Consequence:
    """
    Represents a derived logical consequence along with its proof.
    """
    def __init__(self, formula: Formula, proof: List[Dict], justification_type: str, is_verified: bool = True):
        self.formula = formula
        self.formula_str = str(formula)
        self.proof = proof
        self.justification_type = justification_type
        self.is_verified = is_verified

    def __repr__(self):
        return f"<Consequence: {self.formula_str} ({self.justification_type})>"

    def __eq__(self, other):
        if isinstance(other, Consequence):
            return self.formula == other.formula
        elif isinstance(other, Formula):
            return self.formula == other
        elif isinstance(other, str):
            return self.formula_str == other
        return False

    def __hash__(self):
        return hash(self.formula)


class Deducer:
    """
    Forward Logical Deductive Engine.
    Given axioms, previous theorems/formulas in the database, and a set of hypotheses,
    it automatically derives logical consequences via instantiation and Modus Ponens.
    """

    def __init__(self, db: Optional[TheoryDatabase] = None, auto_load_axioms: bool = True):
        """
        Initializes the Deducer.
        If db is None, creates an in-memory database (:memory:).
        If auto_load_axioms is True, ensures essential basic logical axioms are present in the DB.
        """
        if db is None:
            self.db = TheoryDatabase(":memory:")
        else:
            self.db = db

        if auto_load_axioms:
            self._init_default_axioms()

    def _init_default_axioms(self):
        """Ensures essential Hilbert propositional calculus axioms are present in the DB."""
        existing = self.db.get_all_axioms()
        default_axioms = {
            "ax1": "A -> (B -> A)",
            "ax2": "(A -> (B -> C)) -> ((A -> B) -> (A -> C))",
            "ax3": "(~B -> ~A) -> (A -> B)",
        }
        for name, f_str in default_axioms.items():
            if name not in existing:
                self.db.add_axiom(name, f_str)

    def deduce(
        self,
        hypotheses: List[Union[str, Formula]],
        max_formulas: int = 200,
        include_hypotheses: bool = False,
        timeout_seconds: float = 30.0
    ) -> List[Consequence]:
        """
        Deduces logical consequences from the given hypotheses, based on axioms
        and formulas/lemmas stored in the database.

        Args:
            hypotheses: List of strings or Formula objects representing the hypotheses.
            max_formulas: Maximum number of formulas to derive in the search.
            include_hypotheses: If True, includes the hypotheses in the output list.
            timeout_seconds: Time limit in seconds.

        Returns:
            List of Consequence objects containing the resulting formulas and their proofs.
        """
        start_time = time.time()
        parsed_hyps = [_ensure_formula(h) for h in hypotheses]
        
        derived: Dict[Formula, Dict] = {}
        queue: List[Formula] = []
        implications_by_ant: Dict[Formula, List[Implies]] = {}

        def register(formula: Formula, justification: Dict) -> bool:
            if formula not in derived:
                derived[formula] = justification
                queue.append(formula)
                if isinstance(formula, Implies):
                    if formula.left not in implications_by_ant:
                        implications_by_ant[formula.left] = []
                    implications_by_ant[formula.left].append(formula)
                return True
            return False

        # 1. Insert initial hypotheses
        for idx, hyp in enumerate(parsed_hyps):
            register(hyp, {
                'justification_type': 'Hypothesis',
                'ref_name': f'h{idx}',
                'formula_str': str(hyp)
            })

        # Load axioms from DB
        axioms = self.db.get_all_axioms()
        parsed_axioms = {ax_name: parse_formula(ax_str) for ax_name, ax_str in axioms.items()}

        # Load verified lemmas from DB
        verified_lemmas = []
        existing_lemma_map = {}
        with self.db.connection_scope() as conn:
            cursor = conn.execute("SELECT name FROM theorems WHERE is_verified = 1;")
            lemma_names = [row[0] for row in cursor.fetchall()]

        for name in lemma_names:
            lemma = self.db.get_theorem(name)
            if lemma:
                verified_lemmas.append(lemma)
                existing_lemma_map[parse_formula(lemma['thesis_str'])] = name

        head = 0
        instantiated_axioms_and_lemmas = False

        while len(derived) < max_formulas and (time.time() - start_time) < timeout_seconds:
            added_any_mp = False

            # 2. Modus Ponens Saturation Loop
            while head < len(queue) and len(derived) < max_formulas:
                if (time.time() - start_time) > timeout_seconds:
                    break
                current = queue[head]
                head += 1

                # If current is an antecedent A
                if current in implications_by_ant:
                    for impl in list(implications_by_ant[current]):
                        consequent = impl.right
                        just = {
                            'justification_type': 'MP',
                            'arg1_formula': current,
                            'arg2_formula': impl
                        }
                        if register(consequent, just):
                            added_any_mp = True

                # If current is an implication A -> B
                if isinstance(current, Implies):
                    if current.left in derived:
                        consequent = current.right
                        just = {
                            'justification_type': 'MP',
                            'arg1_formula': current.left,
                            'arg2_formula': current
                        }
                        if register(consequent, just):
                            added_any_mp = True

            # 3. Axiom and Lemma instantiation if MP is saturated or derived no new formulas
            added_any_inst = False

            # Collect relevant candidate formulas from currently derived formulas and hypotheses
            candidates: Set[Formula] = set()
            for f in list(derived.keys()):
                candidates.update(get_all_subformulas(f))
            for h in parsed_hyps:
                candidates.update(get_all_subformulas(h))

            extra_candidates = list(candidates)
            for c in extra_candidates:
                candidates.add(Not(c))

            candidate_list = list(candidates)

            # Axiom instantiation
            for ax_name, schema in parsed_axioms.items():
                schema_vars = sorted(list(schema.free_variables()))
                if schema_vars:
                    if len(schema_vars) <= 3:
                        def get_substitutions(vars_list):
                            if not vars_list:
                                yield {}
                                return
                            v = vars_list[0]
                            for c in candidate_list:
                                for rest in get_substitutions(vars_list[1:]):
                                    res = dict(rest)
                                    res[v] = c
                                    yield res

                        for sub in get_substitutions(schema_vars):
                            if len(derived) >= max_formulas or (time.time() - start_time) > timeout_seconds:
                                break
                            inst_f = schema.substitute(sub)
                            if register(inst_f, {
                                'justification_type': 'Axiom',
                                'ref_name': ax_name,
                                'substitution_json': {k: str(v) for k, v in sub.items()}
                            }):
                                added_any_inst = True
                else:
                    if register(schema, {
                        'justification_type': 'Axiom',
                        'ref_name': ax_name,
                        'substitution_json': {}
                    }):
                        added_any_inst = True

            # Lemma instantiation
            for lemma in verified_lemmas:
                if len(derived) >= max_formulas or (time.time() - start_time) > timeout_seconds:
                    break
                lemma_thesis = parse_formula(lemma['thesis_str'])
                lemma_hyps = [parse_formula(h) for h in lemma['hypotheses']]
                lemma_vars = set(lemma_thesis.free_variables())
                for h in lemma_hyps:
                    lemma_vars.update(h.free_variables())
                sorted_vars = sorted(list(lemma_vars))

                if len(sorted_vars) == 0:
                    if all(ih in derived for ih in lemma_hyps):
                        just = {
                            'justification_type': 'Lemma',
                            'ref_name': lemma['name'],
                            'substitution_json': {}
                        }
                        if len(lemma_hyps) >= 1:
                            just['arg1_formula'] = lemma_hyps[0]
                        if len(lemma_hyps) >= 2:
                            just['arg2_formula'] = lemma_hyps[1]
                        if register(lemma_thesis, just):
                            added_any_inst = True
                elif len(sorted_vars) <= 3:
                    def get_substitutions(vars_list):
                        if not vars_list:
                            yield {}
                            return
                        v = vars_list[0]
                        for c in candidate_list:
                            for rest in get_substitutions(vars_list[1:]):
                                res = dict(rest)
                                res[v] = c
                                yield res

                    for sub in get_substitutions(sorted_vars):
                        inst_thesis = lemma_thesis.substitute(sub)
                        inst_hyps = [lh.substitute(sub) for lh in lemma_hyps]
                        if all(ih in derived for ih in inst_hyps):
                            just = {
                                'justification_type': 'Lemma',
                                'ref_name': lemma['name'],
                                'substitution_json': {k: str(v) for k, v in sub.items()}
                            }
                            if len(inst_hyps) >= 1:
                                just['arg1_formula'] = inst_hyps[0]
                            if len(inst_hyps) >= 2:
                                just['arg2_formula'] = inst_hyps[1]
                            if register(inst_thesis, just):
                                added_any_inst = True

            # If no new formulas were added via MP or instantiation, deduction is saturated.
            if not added_any_mp and not added_any_inst:
                break

        # 4. Proof reconstruction and result assembly
        hyp_set = set(parsed_hyps)
        hyp_strs = [str(h) for h in parsed_hyps]
        consequences = []

        for goal, just in derived.items():
            if not include_hypotheses and goal in hyp_set:
                continue

            try:
                steps = reconstruct_proof(goal, derived, lemma_map=existing_lemma_map, db=self.db)
                thm = {
                    'name': 'temp_deduction',
                    'thesis_str': str(goal),
                    'hypotheses': hyp_strs,
                    'steps': steps
                }
                ok, _ = verify_proof_local(thm, self.db)
                if ok:
                    consequences.append(Consequence(
                        formula=goal,
                        proof=steps,
                        justification_type=just['justification_type'],
                        is_verified=True
                    ))
            except Exception:
                continue

        return consequences


def deduce_consequences(
    hypotheses: List[Union[str, Formula]],
    db: Optional[TheoryDatabase] = None,
    max_formulas: int = 200,
    include_hypotheses: bool = False
) -> List[Consequence]:
    """
    Helper function to deduce consequences from a set of hypotheses.
    """
    deducer = Deducer(db=db)
    return deducer.deduce(hypotheses, max_formulas=max_formulas, include_hypotheses=include_hypotheses)
