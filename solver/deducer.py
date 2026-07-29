"""
Deducer Module
==============
Modulo per la deduzione logica in avanti (Forward Deduction Engine).
Data una serie di ipotesi e basandosi su assiomi e formule/teoremi precedenti memorizzati
nel database delle teorie (TheoryDatabase), il Deducer deduce e ricava le conseguenze logiche.
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
    """Converte una stringa o garantisce che l'oggetto sia una Formula."""
    if isinstance(f, Formula):
        return f
    elif isinstance(f, str):
        return parse_formula(f)
    else:
        raise TypeError(f"Atteso str o Formula, ottenuto {type(f)}")


def get_all_subformulas(formula: Formula) -> Set[Formula]:
    """Estrae ricorsivamente tutte le sottoformule di qualsiasi tipo di Formula."""
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
    Rappresenta una conseguenza logica derivata con la relativa dimostrazione.
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
    Motore di deduzione logica in avanti (Forward Deductive Engine).
    Dati degli assiomi, teoremi/formule precedenti nel database e una serie di ipotesi,
    ricava automaticamente le conseguenze logiche tramite istanziazione e Modus Ponens.
    """

    def __init__(self, db: Optional[TheoryDatabase] = None, auto_load_axioms: bool = True):
        """
        Inizializza il Deducer.
        Se db è None, crea un database in-memory (:memory:).
        Se auto_load_axioms è True, assicura che gli assiomi logici di base siano presenti nel DB.
        """
        if db is None:
            self.db = TheoryDatabase(":memory:")
        else:
            self.db = db

        if auto_load_axioms:
            self._init_default_axioms()

    def _init_default_axioms(self):
        """Assicura che gli assiomi essenziali del calcolo proposizionale di Hilbert siano presenti nel DB."""
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
        Deduce le conseguenze logiche a partire dalle ipotesi date, basandosi sugli assiomi
        e sulle formule/lemmi salvati nel database.

        Args:
            hypotheses: Lista di stringhe o oggetti Formula che costituiscono le ipotesi.
            max_formulas: Numero massimo di formule da derivare nella ricerca.
            include_hypotheses: Se True, include anche le ipotesi nell'elenco di output.
            timeout_seconds: Limite di tempo in secondi.

        Returns:
            Lista di oggetti Consequence contenenti le formule conseguenti e le loro dimostrazioni.
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

        # 1. Inserisce le ipotesi iniziali
        for idx, hyp in enumerate(parsed_hyps):
            register(hyp, {
                'justification_type': 'Hypothesis',
                'ref_name': f'h{idx}',
                'formula_str': str(hyp)
            })

        # Carica gli assiomi dal DB
        axioms = self.db.get_all_axioms()
        parsed_axioms = {ax_name: parse_formula(ax_str) for ax_name, ax_str in axioms.items()}

        # Carica i lemmi verificati dal DB
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

                # Se current è un antecedente A
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

                # Se current è un'implicazione A -> B
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

            # 3. Istanziazione di Assiomi e Lemmi se MP è saturo o non ha derivato nuove formule
            added_any_inst = False

            # Raccogli candidati rilevanti dalle formule attualmente derivate ed ipotesi
            candidates: Set[Formula] = set()
            for f in list(derived.keys()):
                candidates.update(get_all_subformulas(f))
            for h in parsed_hyps:
                candidates.update(get_all_subformulas(h))

            extra_candidates = list(candidates)
            for c in extra_candidates:
                candidates.add(Not(c))

            candidate_list = list(candidates)

            # Istanziazione Assiomi
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

            # Istanziazione Lemmi
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

            # Se non sono state aggiunte nuove formule né tramite MP né tramite istanziazione, la deduzione è satura.
            if not added_any_mp and not added_any_inst:
                break

        # 4. Ricostruzione delle dimostrazioni e assemblaggio dei risultati
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
    Funzione ausiliaria per dedurre conseguenze da un insieme di ipotesi.
    """
    deducer = Deducer(db=db)
    return deducer.deduce(hypotheses, max_formulas=max_formulas, include_hypotheses=include_hypotheses)
