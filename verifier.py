import subprocess
import os
from database import TheoryDatabase
from formula import parse_formula, Implies
import lean_exporter

def verify_proof_local(thm, db: TheoryDatabase):
    """
    Esegue una convalida strutturale locale in Python della dimostrazione del teorema.
    Verifica la correttezza formale di ciascun passo di dimostrazione prima di passarla a Lean.
    """
    hypotheses = [parse_formula(h) for h in thm['hypotheses']]
    thesis = parse_formula(thm['thesis_str'])
    
    # Carica tutti gli assiomi presenti nel database
    axioms = {name: parse_formula(f_str) for name, f_str in db.get_all_axioms().items()}
    
    # Mappa per tracciare le formule associate ai passi per il controllo degli indici MP
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
                return False, f"Passo {idx}: Assioma '{ax_name}' non trovato nel database."
            schema = axioms[ax_name]
            bindings = f.match_schema(schema)
            if bindings is None:
                return False, f"Passo {idx}: La formula '{f}' non è un'istanza corretta dell'assioma {ax_name} '{schema}'."
            # Aggiorna o memorizza il dizionario delle sostituzioni per l'esportatore
            step['substitution_json'] = {k: str(v) for k, v in bindings.items()}
            
        elif j_type == 'Hypothesis':
            ref_name = step['ref_name']
            if not ref_name.startswith('h'):
                return False, f"Passo {idx}: Il riferimento all'ipotesi '{ref_name}' deve iniziare con 'h'."
            try:
                hyp_idx = int(ref_name[1:])
            except ValueError:
                return False, f"Passo {idx}: Indice dell'ipotesi '{ref_name}' non valido."
            if hyp_idx < 0 or hyp_idx >= len(hypotheses):
                return False, f"Passo {idx}: Indice dell'ipotesi '{ref_name}' fuori dai limiti."
            if f != hypotheses[hyp_idx]:
                return False, f"Passo {idx}: La formula '{f}' non corrisponde alla definizione dell'ipotesi {ref_name} '{hypotheses[hyp_idx]}'."
                
        elif j_type == 'MP':
            arg1 = step['arg1']
            arg2 = step['arg2']
            if arg1 not in step_formulas or arg2 not in step_formulas:
                return False, f"Passo {idx}: Argomenti MP ({arg1}, {arg2}) non trovati nei passi precedenti."
            if arg1 >= idx or arg2 >= idx:
                return False, f"Passo {idx}: Gli argomenti MP ({arg1}, {arg2}) devono riferirsi a passi antecedenti."
            
            f1 = step_formulas[arg1]
            f2 = step_formulas[arg2]
            
            # Cerca quale delle due formule è l'implicazione A -> B e quale l'antecedente A
            if isinstance(f1, Implies) and f1.left == f2:
                consequent = f1.right
            elif isinstance(f2, Implies) and f2.left == f1:
                consequent = f2.right
            else:
                return False, f"Passo {idx}: I passi {arg1} e {arg2} non formano una coppia Modus Ponens valida."
            
            if f != consequent:
                return False, f"Passo {idx}: La conclusione MP '{consequent}' non coincide con la formula del passo '{f}'."
                
        elif j_type == 'Lemma':
            lemma_name = step['ref_name']
            lemma = db.get_theorem(lemma_name)
            if not lemma:
                return False, f"Passo {idx}: Lemma '{lemma_name}' non trovato nel database."
            if not lemma['is_verified']:
                return False, f"Passo {idx}: Il lemma '{lemma_name}' non è verificato."
            
            lemma_thesis = parse_formula(lemma['thesis_str'])
            lemma_hyps = [parse_formula(h) for h in lemma['hypotheses']]
            
            # Estrae o deduce la sostituzione
            sub_json = step.get('substitution_json')
            if not sub_json:
                bindings = f.match_schema(lemma_thesis)
                if bindings is None:
                    return False, f"Passo {idx}: La formula '{f}' non corrisponde alla tesi del lemma {lemma_name} '{lemma_thesis}'."
                sub_json = {k: str(v) for k, v in bindings.items()}
                step['substitution_json'] = sub_json
                
            sub_map = {k: parse_formula(v) for k, v in sub_json.items()}
            
            # Verifica che la tesi sostituita corrisponda al passo corrente
            if lemma_thesis.substitute(sub_map) != f:
                return False, f"Passo {idx}: La formula '{f}' non coincide con la tesi del lemma '{lemma_name}' sotto sostituzione."
            
            # Verifica che le ipotesi sostituite corrispondano ai passi indicati
            if len(lemma_hyps) >= 1:
                arg1 = step.get('arg1')
                if arg1 is None or arg1 not in step_formulas:
                    return False, f"Passo {idx}: Il lemma richiede almeno un argomento in ingresso (arg1)."
                expected_hyp = lemma_hyps[0].substitute(sub_map)
                if step_formulas[arg1] != expected_hyp:
                    return False, f"Passo {idx}: Il passo argomenti {arg1} non corrisponde alla prima ipotesi del lemma (atteso: '{expected_hyp}')."
            
            if len(lemma_hyps) >= 2:
                arg2 = step.get('arg2')
                if arg2 is None or arg2 not in step_formulas:
                    return False, f"Passo {idx}: Il lemma richiede un secondo argomento in ingresso (arg2)."
                expected_hyp = lemma_hyps[1].substitute(sub_map)
                if step_formulas[arg2] != expected_hyp:
                    return False, f"Passo {idx}: Il passo argomenti {arg2} non corrisponde alla seconda ipotesi del lemma (atteso: '{expected_hyp}')."
        else:
            return False, f"Passo {idx}: Tipo di giustificazione sconosciuto '{j_type}'."

    # Verifica che l'ultimo passo corrisponda alla tesi
    last_idx = thm['steps'][-1]['step_idx']
    if step_formulas[last_idx] != thesis:
        return False, f"L'ultimo passo {last_idx} ({step_formulas[last_idx]}) non coincide con la tesi ({thesis})."

    return True, None

def verify_and_save(thm, db: TheoryDatabase):
    """
    Verifica localmente e poi tramite Lean 4 il teorema fornito.
    Se ha successo, memorizza il teorema come verificato nel database SQLite.
    """
    # 1. Verifica strutturale locale in Python
    ok, err = verify_proof_local(thm, db)
    if not ok:
        return False, f"Errore di validazione locale: {err}"

    # Trova le dipendenze dirette per salvarle
    dependencies = set()
    for step in thm['steps']:
        if step['justification_type'] == 'Lemma':
            dependencies.add(step['ref_name'])

    # Salvataggio temporaneo nel DB come non verificato per consentire all'esportatore di leggerlo
    db.save_theorem(
        name=thm['name'],
        thesis_str=thm['thesis_str'],
        hypotheses=thm['hypotheses'],
        steps=thm['steps'],
        dependencies=list(dependencies),
        lean_code=None,
        is_verified=0
    )

    # 2. Genera il codice sorgente Lean 4
    try:
        lean_code = lean_exporter.export_proof(thm['name'], db)
    except Exception as e:
        return False, f"Errore durante la generazione di Lean 4: {e}"

    # Scrive il codice Lean in un file temporaneo
    temp_filename = "temp_proof.lean"
    with open(temp_filename, "w", encoding="utf-8") as f:
        f.write(lean_code)

    # 3. Compila il file con Lean 4
    try:
        res = subprocess.run(
            ["lean", temp_filename],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if res.returncode == 0:
            # Se la compilazione ha successo, aggiorna il teorema a verificato
            db.save_theorem(
                name=thm['name'],
                thesis_str=thm['thesis_str'],
                hypotheses=thm['hypotheses'],
                steps=thm['steps'],
                dependencies=list(dependencies),
                lean_code=lean_code,
                is_verified=1
            )
            # Rimuove il file temporaneo
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            return True, lean_code
        else:
            # Altrimenti mantiene is_verified = 0 ed elimina il file temporaneo
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            error_msg = res.stderr if res.stderr else res.stdout
            return False, f"Errore di compilazione Lean 4:\n{error_msg}"
    except Exception as e:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return False, f"Impossibile avviare il compilatore Lean 4: {e}"
