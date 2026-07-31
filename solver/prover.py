import time
from .formula import parse_formula, Var, Not, Implies, Formula
from .database import TheoryDatabase

def get_subformulas(formula):
    """Recursively extracts all subformulas of a given formula."""
    subs = {formula}
    if isinstance(formula, Not):
        subs.update(get_subformulas(formula.formula))
    elif isinstance(formula, Implies):
        subs.update(get_subformulas(formula.left))
        subs.update(get_subformulas(formula.right))
    return subs

def reconstruct_proof(goal, derived, lemma_map=None, db=None):
    """
    Reconstructs the sequence of topologically ordered steps starting
    from the final goal and the justifications collected during search.
    """
    visited = {}
    steps = []
    
    def visit(formula):
        if formula in visited:
            return visited[formula]
        
        # If the formula is already a verified lemma in the database (excluding the goal itself),
        # we can use it as a lemma instead of reconstructing its derivation.
        if lemma_map and db and formula in lemma_map and formula != goal:
            lemma_name = lemma_map[formula]
            lemma_thm = db.get_theorem(lemma_name)
            if lemma_thm:
                lemma_thesis = parse_formula(lemma_thm['thesis_str'])
                lemma_hyps = [parse_formula(h) for h in lemma_thm['hypotheses']]
                
                bindings = formula.match_schema(lemma_thesis)
                sub_json = {k: str(v) for k, v in bindings.items()} if bindings else {}
                
                args = []
                for lh in lemma_hyps:
                    inst_lh = lh.substitute({k: parse_formula(v) for k, v in sub_json.items()})
                    args.append(visit(inst_lh))
                    
                idx = len(steps)
                step = {
                    'step_idx': idx,
                    'formula_str': str(formula),
                    'justification_type': 'Lemma',
                    'ref_name': lemma_name,
                    'substitution_json': sub_json
                }
                if len(args) >= 1:
                    step['arg1'] = args[0]
                if len(args) >= 2:
                    step['arg2'] = args[1]
                    
                steps.append(step)
                visited[formula] = idx
                return idx

        just = derived[formula]
        args = []
        
        # Visit arguments first to guarantee topological ordering
        if just['justification_type'] == 'MP':
            arg1_idx = visit(just['arg1_formula'])
            arg2_idx = visit(just['arg2_formula'])
            args = [arg1_idx, arg2_idx]
        elif just['justification_type'] == 'Lemma':
            if 'arg1_formula' in just:
                args.append(visit(just['arg1_formula']))
            if 'arg2_formula' in just:
                args.append(visit(just['arg2_formula']))
                
        idx = len(steps)
        step = {
            'step_idx': idx,
            'formula_str': str(formula),
            'justification_type': just['justification_type']
        }
        
        if 'ref_name' in just:
            step['ref_name'] = just['ref_name']
        if 'substitution_json' in just:
            step['substitution_json'] = just['substitution_json']
            
        if just['justification_type'] == 'MP':
            # Sort arguments so arg1 is the smaller formula
            # (conforming to verifier expectations)
            step['arg1'] = min(args)
            step['arg2'] = max(args)
        elif just['justification_type'] == 'Lemma':
            if len(args) >= 1:
                step['arg1'] = args[0]
            if len(args) >= 2:
                step['arg2'] = args[1]
                
        steps.append(step)
        visited[formula] = idx
        return idx

    visit(goal)
    return steps

def prove(thesis_str, hypotheses_strs, db: TheoryDatabase, exclude_name=None, max_depth=10, max_formulas=1000, timeout_seconds=30):
    """
    Automatic proof search algorithm (Forward Search with BFS).
    Finds a proof for thesis_str starting from hypotheses_strs, using axioms
    and lemmas stored in the database.
    """
    start_time = time.time()
    
    thesis = parse_formula(thesis_str)
    hypotheses = [parse_formula(h) for h in hypotheses_strs]
    
    # 1. Collect subformulas to define the search space (Candidate Pool)
    all_fs = {thesis}
    for h in hypotheses:
        all_fs.update(get_subformulas(h))
    
    all_subformulas = set()
    for f in all_fs:
        all_subformulas.update(get_subformulas(f))
        
    candidates = set(all_subformulas)
    # Add negations for completeness
    for sf in all_subformulas:
        candidates.add(Not(sf))
        
    if not candidates:
        candidates.add(Var('p'))
        
    # Dictionary mapping each derived formula to its justification
    derived = {}
    
    # Insert hypotheses
    for idx, hyp in enumerate(hypotheses):
        derived[hyp] = {
            'justification_type': 'Hypothesis',
            'ref_name': f'h{idx}'
        }
        if hyp == thesis:
            return reconstruct_proof(thesis, derived)

    # Load all previously verified lemmas from database
    all_db_thms = []
    with db.connection_scope() as conn:
        if exclude_name:
            cursor = conn.execute("SELECT name FROM theorems WHERE is_verified = 1 AND name != ?;", (exclude_name,))
        else:
            cursor = conn.execute("SELECT name FROM theorems WHERE is_verified = 1;")
        names = [r[0] for r in cursor.fetchall()]
        for name in names:
            all_db_thms.append(db.get_theorem(name))

    def register(formula, justification):
        if formula not in derived:
            derived[formula] = justification
            return True
        return False

    # 2. Initial instantiation of axiom schemas with candidate formulas
    # Axiom 1: A -> (B -> A)
    for A in candidates:
        for B in candidates:
            f = Implies(A, Implies(B, A))
            register(f, {
                'justification_type': 'Axiom',
                'ref_name': 'ax1',
                'substitution_json': {'A': str(A), 'B': str(B)}
            })

    # Axiom 2: (A -> (B -> C)) -> ((A -> B) -> (A -> C))
    for A in candidates:
        for B in candidates:
            for C in candidates:
                f = Implies(Implies(A, Implies(B, C)), Implies(Implies(A, B), Implies(A, C)))
                register(f, {
                    'justification_type': 'Axiom',
                    'ref_name': 'ax2',
                    'substitution_json': {'A': str(A), 'B': str(B), 'C': str(C)}
                })

    # Axiom 3: (~A -> ~B) -> (B -> A)
    for A in candidates:
        for B in candidates:
            f = Implies(Implies(Not(A), Not(B)), Implies(B, A))
            register(f, {
                'justification_type': 'Axiom',
                'ref_name': 'ax3',
                'substitution_json': {'A': str(A), 'B': str(B)}
            })

    # Initial instantiation of lemmas
    for lemma in all_db_thms:
        lemma_thesis = parse_formula(lemma['thesis_str'])
        lemma_hyps = [parse_formula(h) for h in lemma['hypotheses']]
        
        lemma_vars = set(lemma_thesis.free_variables())
        for lh in lemma_hyps:
            lemma_vars.update(lh.free_variables())
        sorted_vars = sorted(list(lemma_vars))
        
        if len(sorted_vars) > 3:
            continue  # Prevents combinatorial explosion for overly complex lemmas
            
        def get_mappings(vars_list):
            if not vars_list:
                yield {}
                return
            v = vars_list[0]
            for c in candidates:
                for rest in get_mappings(vars_list[1:]):
                    rest[v] = c
                    yield rest
                    
        for mapping in get_mappings(sorted_vars):
            sub_map = {k: v for k, v in mapping.items()}
            sub_json = {k: str(v) for k, v in mapping.items()}
            
            inst_thesis = lemma_thesis.substitute(sub_map)
            inst_hyps = [lh.substitute(sub_map) for lh in lemma_hyps]
            
            # We can apply the lemma only if its hypotheses have been derived
            if all(ih in derived for ih in inst_hyps):
                just = {
                    'justification_type': 'Lemma',
                    'ref_name': lemma['name'],
                    'substitution_json': sub_json
                }
                if len(inst_hyps) >= 1:
                    just['arg1_formula'] = inst_hyps[0]
                if len(inst_hyps) >= 2:
                    just['arg2_formula'] = inst_hyps[1]
                    
                register(inst_thesis, just)

    if thesis in derived:
        return reconstruct_proof(thesis, derived)

    # 3. BFS via Modus Ponens
    queue = list(derived.keys())
    
    # Hash tables to speed up MP lookup
    implications_by_ant = {}
    for f in queue:
        if isinstance(f, Implies):
            if f.left not in implications_by_ant:
                implications_by_ant[f.left] = []
            implications_by_ant[f.left].append(f)

    head = 0
    while head < len(queue):
        if time.time() - start_time > timeout_seconds:
            break
        if len(derived) > max_formulas:
            break
            
        current = queue[head]
        head += 1
        
        # Case A: current is the antecedent (A). Search for implications A -> B.
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
                    if consequent == thesis:
                        return reconstruct_proof(thesis, derived)
                    if isinstance(consequent, Implies):
                        if consequent.left not in implications_by_ant:
                            implications_by_ant[consequent.left] = []
                        implications_by_ant[consequent.left].append(consequent)

        # Case B: current is the implication (A -> B). Check if antecedent A is known.
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
                    if consequent == thesis:
                        return reconstruct_proof(thesis, derived)
                    if isinstance(consequent, Implies):
                        if consequent.left not in implications_by_ant:
                            implications_by_ant[consequent.left] = []
                        implications_by_ant[consequent.left].append(consequent)

    raise TimeoutError(f"Could not find a proof for {thesis_str} within limits.")
