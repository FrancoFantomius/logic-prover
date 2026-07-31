import time
import sys
from .database import TheoryDatabase
from .formula import parse_formula, Var, Not, Implies, And, Or, Iff, Forall, Exists, Equals, Pred, Formula
from .verifier import verify_and_save
from .prover import reconstruct_proof

def generate_candidates(basic_vars, max_depth):
    """
    Recursively generates candidate formulas composed of basic variables
    up to a given nesting depth.
    """
    current = [Var(v) for v in basic_vars]
    all_candidates = list(current)
    
    for depth in range(1, max_depth + 1):
        next_candidates = []
        # Negations of formulas from previous depth
        for f in current:
            next_candidates.append(Not(f))
        
        # Implications A -> B with at least one formula from previous depth
        for A in all_candidates:
            for B in all_candidates:
                if A in current or B in current:
                    next_candidates.append(Implies(A, B))
                    
        # Remove duplicates
        seen = set(all_candidates)
        unique_next = []
        for f in next_candidates:
            if f not in seen:
                seen.add(f)
                unique_next.append(f)
                
        current = unique_next
        all_candidates.extend(current)
        
    return all_candidates

def explore_consequences(db: TheoryDatabase, basic_vars=['p'], max_depth=1, max_theorems=20, min_proof_steps=0):
    """
    Systematically generates logical consequences by instantiating axioms and lemmas
    and applying Modus Ponens. Registers and validates each result via Lean 4.
    """
    candidates = generate_candidates(basic_vars, max_depth)
    print(f"Generated candidate formulas ({len(candidates)}): {[str(c) for c in candidates]}")
    
    derived = {}
    
    def register(formula, justification):
        if formula not in derived:
            derived[formula] = justification
            return True
        return False
        
    # 1. Instantiate Axioms present in the database
    axioms = db.get_all_axioms()
    for ax_name, ax_str in axioms.items():
        schema = parse_formula(ax_str)
        if ax_name in ['ax1', 'ax2', 'ax3']:
            schema_vars = sorted(list(schema.free_variables()))
            
            def get_substitutions(vars_list):
                if not vars_list:
                    yield {}
                    return
                v = vars_list[0]
                for c in candidates:
                    for rest in get_substitutions(vars_list[1:]):
                        rest[v] = c
                        yield rest
                        
            for sub in get_substitutions(schema_vars):
                inst_f = schema.substitute(sub)
                register(inst_f, {
                    'justification_type': 'Axiom',
                    'ref_name': ax_name,
                    'substitution_json': {k: str(v) for k, v in sub.items()}
                })
        else:
            # Domain-specific axiom (non-schematic)
            register(schema, {
                'justification_type': 'Axiom',
                'ref_name': ax_name,
                'substitution_json': {}
            })
            
    # 2. Load and instantiate verified Lemmas from database
    lemmas = []
    with db.connection_scope() as conn:
        cursor = conn.execute("SELECT name FROM theorems WHERE is_verified = 1;")
        names = [row[0] for row in cursor.fetchall()]
        for name in names:
            lemmas.append(db.get_theorem(name))
            
    for lemma in lemmas:
        lemma_thesis = parse_formula(lemma['thesis_str'])
        lemma_hyps = [parse_formula(h) for h in lemma['hypotheses']]
        lemma_vars = set(lemma_thesis.free_variables())
        for h in lemma_hyps:
            lemma_vars.update(h.free_variables())
        sorted_vars = sorted(list(lemma_vars))
        
        if len(sorted_vars) > 3:
            continue
            
        def get_substitutions(vars_list):
            if not vars_list:
                yield {}
                return
            v = vars_list[0]
            for c in candidates:
                for rest in get_substitutions(vars_list[1:]):
                    rest[v] = c
                    yield rest
                    
        for sub in get_substitutions(sorted_vars):
            inst_thesis = lemma_thesis.substitute(sub)
            inst_hyps = [lh.substitute(sub) for lh in lemma_hyps]
            
            # The lemma is applicable if all of its hypotheses have already been derived
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
                    
                register(inst_thesis, just)

    # 3. BFS for Modus Ponens
    queue = list(derived.keys())
    
    implications_by_ant = {}
    for f in queue:
        if isinstance(f, Implies):
            if f.left not in implications_by_ant:
                implications_by_ant[f.left] = []
            implications_by_ant[f.left].append(f)
            
    head = 0
    while head < len(queue):
        current = queue[head]
        head += 1
        
        # Case A: current is an antecedent (A)
        if current in implications_by_ant:
            for impl in implications_by_ant[current]:
                consequent = impl.right
                just = {
                    'justification_type': 'MP',
                    'arg1_formula': current,
                    'arg2_formula': impl
                }
                if register(consequent, just):
                    queue.append(consequent)
                    if isinstance(consequent, Implies):
                        if consequent.left not in implications_by_ant:
                            implications_by_ant[consequent.left] = []
                        implications_by_ant[consequent.left].append(consequent)
                        
        # Case B: current is an implication (A -> B)
        if isinstance(current, Implies):
            if current.left not in implications_by_ant:
                implications_by_ant[current.left] = []
            if current not in implications_by_ant[current.left]:
                implications_by_ant[current.left].append(current)
                
            if current.left in derived:
                consequent = current.right
                just = {
                    'justification_type': 'MP',
                    'arg1_formula': current.left,
                    'arg2_formula': current
                }
                if register(consequent, just):
                    queue.append(consequent)
                    if isinstance(consequent, Implies):
                        if consequent.left not in implications_by_ant:
                            implications_by_ant[consequent.left] = []
                        implications_by_ant[consequent.left].append(consequent)

    print(f"Saturation completed. Total derived formulas: {len(derived)}")
    
    # 4. Load existing theorems from database to avoid duplicating them
    existing_theorems = {}
    with db.connection_scope() as conn:
        cursor = conn.execute("SELECT name, thesis_str FROM theorems WHERE is_verified = 1;")
        for row in cursor.fetchall():
            existing_theorems[parse_formula(row[1])] = row[0]
            
    # Sort derived formulas by structural complexity (simpler formulas first)
    def formula_complexity(f):
        if isinstance(f, Var):
            return 1
        elif isinstance(f, Not):
            return 1 + formula_complexity(f.formula)
        elif isinstance(f, (Implies, And, Or, Iff, Equals)):
            return 1 + formula_complexity(f.left) + formula_complexity(f.right)
        elif isinstance(f, (Forall, Exists)):
            return 1 + formula_complexity(f.body)
        elif isinstance(f, Pred):
            return 1 + sum(formula_complexity(a) for a in f.args if isinstance(a, Formula))
        return 1
            
    sorted_derived = sorted(list(derived.keys()), key=formula_complexity)
    
    new_theorems_count = 0
    with db.connection_scope() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM theorems;")
        thm_id_counter = cursor.fetchone()[0] + 1

    for goal in sorted_derived:
        if new_theorems_count >= max_theorems:
            break
            
        if goal in existing_theorems:
            continue
            
        try:
            steps = reconstruct_proof(goal, derived, lemma_map=existing_theorems, db=db)
        except Exception as e:
            print(f"Error reconstructing steps for {goal}: {e}")
            continue
            
        if len(steps) < min_proof_steps:
            continue
            
        thm_name = f"thm_{thm_id_counter}"
        thm = {
            'name': thm_name,
            'thesis_str': str(goal),
            'hypotheses': [],
            'steps': steps
        }
        
        print(f"Formal verification and saving of {thm_name}: {goal}")
        success, res_msg = verify_and_save(thm, db)
        if success:
            print(f"  -> Successfully verified in Lean 4 and saved to database!")
            existing_theorems[goal] = thm_name
            new_theorems_count += 1
            thm_id_counter += 1
        else:
            safe_msg = str(res_msg).encode(getattr(sys.stdout, 'encoding', None) or 'utf-8', errors='replace').decode(getattr(sys.stdout, 'encoding', None) or 'utf-8', errors='replace')
            print(f"  -> Failed: {safe_msg}")
            
    return new_theorems_count
