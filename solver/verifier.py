import subprocess
import os
from .database import TheoryDatabase
from .formula import parse_formula, Implies
from . import lean_exporter

def verify_proof_local(thm, db: TheoryDatabase):
    """
    Performs local Python structural validation of the theorem proof.
    Verifies formal correctness of each proof step before passing it to Lean.
    """
    hypotheses = [parse_formula(h) for h in thm['hypotheses']]
    thesis = parse_formula(thm['thesis_str'])
    
    # Load all axioms present in the database
    axioms = {name: parse_formula(f_str) for name, f_str in db.get_all_axioms().items()}
    
    # Map to track step formulas for checking MP indices
    step_formulas = {}
    for step in thm['steps']:
        step_formulas[step['step_idx']] = parse_formula(step['formula_str'])
        
    for step in thm['steps']:
        idx = step['step_idx']
        f = step_formulas[idx]
        j_type = step['justification_type']
        
        if j_type == 'Axiom':
            ax_name = step['ref_name']
            if ax_name not in axioms:
                return False, f"Step {idx}: Axiom '{ax_name}' not found in database."
            schema = axioms[ax_name]
            bindings = f.match_schema(schema)
            if bindings is None:
                return False, f"Step {idx}: Formula '{f}' is not a valid instance of axiom {ax_name} '{schema}'."
            # Update or store substitution dictionary for the exporter
            step['substitution_json'] = {k: str(v) for k, v in bindings.items()}
            
        elif j_type == 'Hypothesis':
            ref_name = step['ref_name']
            if not ref_name.startswith('h'):
                return False, f"Step {idx}: Hypothesis reference '{ref_name}' must start with 'h'."
            try:
                hyp_idx = int(ref_name[1:])
            except ValueError:
                return False, f"Step {idx}: Invalid hypothesis index '{ref_name}'."
            if hyp_idx < 0 or hyp_idx >= len(hypotheses):
                return False, f"Step {idx}: Hypothesis index '{ref_name}' out of bounds."
            if f != hypotheses[hyp_idx]:
                return False, f"Step {idx}: Formula '{f}' does not match definition of hypothesis {ref_name} '{hypotheses[hyp_idx]}'."
                
        elif j_type == 'MP':
            arg1 = step['arg1']
            arg2 = step['arg2']
            if arg1 not in step_formulas or arg2 not in step_formulas:
                return False, f"Step {idx}: MP arguments ({arg1}, {arg2}) not found in previous steps."
            if arg1 >= idx or arg2 >= idx:
                return False, f"Step {idx}: MP arguments ({arg1}, {arg2}) must refer to prior steps."
            
            f1 = step_formulas[arg1]
            f2 = step_formulas[arg2]
            
            # Search which formula is implication A -> B and which is antecedent A
            if isinstance(f1, Implies) and f1.left == f2:
                consequent = f1.right
            elif isinstance(f2, Implies) and f2.left == f1:
                consequent = f2.right
            else:
                return False, f"Step {idx}: Steps {arg1} and {arg2} do not form a valid Modus Ponens pair."
            
            if f != consequent:
                return False, f"Step {idx}: MP conclusion '{consequent}' does not match step formula '{f}'."
                
        elif j_type == 'Lemma':
            lemma_name = step['ref_name']
            lemma = db.get_theorem(lemma_name)
            if not lemma:
                return False, f"Step {idx}: Lemma '{lemma_name}' not found in database."
            if not lemma['is_verified']:
                return False, f"Step {idx}: Lemma '{lemma_name}' is not verified."
            
            lemma_thesis = parse_formula(lemma['thesis_str'])
            lemma_hyps = [parse_formula(h) for h in lemma['hypotheses']]
            
            # Extract or deduce substitution
            sub_json = step.get('substitution_json')
            if not sub_json:
                bindings = f.match_schema(lemma_thesis)
                if bindings is None:
                    return False, f"Step {idx}: Formula '{f}' does not match thesis of lemma {lemma_name} '{lemma_thesis}'."
                sub_json = {k: str(v) for k, v in bindings.items()}
                step['substitution_json'] = sub_json
                
            sub_map = {k: parse_formula(v) for k, v in sub_json.items()}
            
            # Verify substituted thesis matches current step
            if lemma_thesis.substitute(sub_map) != f:
                return False, f"Step {idx}: Formula '{f}' does not match thesis of lemma '{lemma_name}' under substitution."
            
            # Verify substituted hypotheses match indicated steps
            if len(lemma_hyps) >= 1:
                arg1 = step.get('arg1')
                if arg1 is None or arg1 not in step_formulas:
                    return False, f"Step {idx}: Lemma requires at least one input argument (arg1)."
                expected_hyp = lemma_hyps[0].substitute(sub_map)
                if step_formulas[arg1] != expected_hyp:
                    return False, f"Step {idx}: Argument step {arg1} does not match first hypothesis of lemma (expected: '{expected_hyp}')."
            
            if len(lemma_hyps) >= 2:
                arg2 = step.get('arg2')
                if arg2 is None or arg2 not in step_formulas:
                    return False, f"Step {idx}: Lemma requires a second input argument (arg2)."
                expected_hyp = lemma_hyps[1].substitute(sub_map)
                if step_formulas[arg2] != expected_hyp:
                    return False, f"Step {idx}: Argument step {arg2} does not match second hypothesis of lemma (expected: '{expected_hyp}')."
        else:
            return False, f"Step {idx}: Unknown justification type '{j_type}'."

    # Verify that the last step matches the thesis
    last_idx = thm['steps'][-1]['step_idx']
    if step_formulas[last_idx] != thesis:
        return False, f"Last step {last_idx} ({step_formulas[last_idx]}) does not match thesis ({thesis})."

    return True, None

def verify_proof_with_lean(thm, db: TheoryDatabase):
    """Generates and executes proof verification with Lean 4."""
    try:
        lean_code = lean_exporter.export_proof(thm['name'], db)
    except Exception as e:
        return False, f"Error during Lean 4 generation: {e}"

    temp_filename = f"temp_proof_{os.getpid()}_{thm['name']}.lean"
    with open(temp_filename, "w", encoding="utf-8") as f:
        f.write(lean_code)

    try:
        res = subprocess.run(
            ["lean", temp_filename],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if res.returncode == 0:
            return True, lean_code
        else:
            error_msg = res.stderr if res.stderr else res.stdout
            return False, f"Lean 4 compilation error:\n{error_msg}"
    except Exception as e:
        return False, f"Could not start Lean 4 compiler: {e}"
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except OSError:
                pass

def verify_and_save(thm, db: TheoryDatabase):
    """
    Verifies locally and then via Lean 4 the provided theorem.
    If successful, stores the theorem as verified in the SQLite database.
    """
    # 1. Local Python structural verification
    ok, err = verify_proof_local(thm, db)
    if not ok:
        return False, f"Local validation error: {err}"

    # Find direct dependencies to save them
    dependencies = set()
    for step in thm['steps']:
        if step['justification_type'] == 'Lemma':
            dependencies.add(step['ref_name'])

    # Temporary save in DB as unverified to allow exporter to read it
    db.save_theorem(
        name=thm['name'],
        thesis_str=thm['thesis_str'],
        hypotheses=thm['hypotheses'],
        steps=thm['steps'],
        dependencies=list(dependencies),
        lean_code=None,
        is_verified=0
    )

    # 2. Generate Lean 4 source code and execute Lean
    ok_lean, lean_res = verify_proof_with_lean(thm, db)
    if ok_lean:
        db.save_theorem(
            name=thm['name'],
            thesis_str=thm['thesis_str'],
            hypotheses=thm['hypotheses'],
            steps=thm['steps'],
            dependencies=list(dependencies),
            lean_code=lean_res,
            is_verified=1
        )
        return True, lean_res
    else:
        return False, lean_res
