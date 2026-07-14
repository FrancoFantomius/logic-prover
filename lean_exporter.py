from formula import Var, Not, Implies, parse_formula

def formula_to_lean(formula):
    """Converte un oggetto Formula nella sintassi di Lean 4."""
    if isinstance(formula, Var):
        return formula.name
    elif isinstance(formula, Not):
        return f"¬({formula_to_lean(formula.formula)})"
    elif isinstance(formula, Implies):
        return f"({formula_to_lean(formula.left)} → {formula_to_lean(formula.right)})"
    else:
        raise TypeError(f"Tipo di formula non supportato: {type(formula)}")

def export_proof(theorem_name, db):
    """
    Genera il codice sorgente Lean 4 self-contained per il teorema specificato,
    caricando le dipendenze dal database SQLite.
    """
    thm = db.get_theorem(theorem_name)
    if not thm:
        raise ValueError(f"Teorema '{theorem_name}' non trovato nel database.")

    # Carica le dipendenze ricorsive
    dep_names = db.get_dependencies_recursive(theorem_name)
    dep_thms = [db.get_theorem(name) for name in dep_names]

    # Raccoglie tutte le variabili del teorema corrente per l'intestazione
    current_vars = set()
    current_vars.update(parse_formula(thm['thesis_str']).free_variables())
    for hyp in thm['hypotheses']:
        current_vars.update(parse_formula(hyp).free_variables())
    for step in thm['steps']:
        current_vars.update(parse_formula(step['formula_str']).free_variables())
        if step.get('substitution_json'):
            for sub_val_str in step['substitution_json'].values():
                f = parse_formula(str(sub_val_str))
                current_vars.update(f.free_variables())

    lines = []
    lines.append("-- Assiomi standard della logica proposizionale")
    lines.append("axiom ax1 (A B : Prop) : A → (B → A)")
    lines.append("axiom ax2 (A B C : Prop) : (A → (B → C)) → ((A → B) → (A → C))")
    lines.append("axiom ax3 (A B : Prop) : (¬A → ¬B) → (B → A)")
    lines.append("")

    # Raccoglie e dichiara assiomi specifici del dominio
    domain_axioms = {}
    for step in thm['steps']:
        if step['justification_type'] == 'Axiom':
            ax_name = step['ref_name']
            if ax_name not in ['ax1', 'ax2', 'ax3']:
                domain_axioms[ax_name] = db.get_axiom(ax_name)
    if domain_axioms:
        lines.append("-- Assiomi specifici del dominio")
        for ax_name, ax_str in sorted(domain_axioms.items()):
            ax_f = parse_formula(ax_str)
            ax_vars = sorted(list(ax_f.free_variables()))
            vars_decl = f"({ ' '.join(ax_vars) } : Prop)" if ax_vars else ""
            lines.append(f"axiom {ax_name} {vars_decl} : {formula_to_lean(ax_f)}")
        lines.append("")

    # Dichiarazione dei lemmi come assiomi
    if dep_thms:
        lines.append("-- Lemmi caricati dal database")
        for dep in dep_thms:
            dep_interface_vars = set()
            dep_thesis_f = parse_formula(dep['thesis_str'])
            dep_interface_vars.update(dep_thesis_f.free_variables())
            dep_hyp_fs = [parse_formula(h) for h in dep['hypotheses']]
            for h_f in dep_hyp_fs:
                dep_interface_vars.update(h_f.free_variables())
            
            sorted_dep_vars = sorted(list(dep_interface_vars))
            vars_decl = f"({ ' '.join(sorted_dep_vars) } : Prop)" if sorted_dep_vars else ""
            
            # Formato: hyp0 → hyp1 → ... → thesis
            sig_types = [formula_to_lean(h_f) for h_f in dep_hyp_fs] + [formula_to_lean(dep_thesis_f)]
            sig_str = " → ".join(sig_types)
            
            lines.append(f"axiom {dep['name']} {vars_decl} : {sig_str}")
        lines.append("")

    # Dichiarazione del teorema corrente
    sorted_current_vars = sorted(list(current_vars))
    vars_decl = f"({ ' '.join(sorted_current_vars) } : Prop)" if sorted_current_vars else ""
    
    hyp_decls = []
    for idx, hyp_str in enumerate(thm['hypotheses']):
        hyp_f = parse_formula(hyp_str)
        hyp_decls.append(f"(h{idx} : {formula_to_lean(hyp_f)})")
    hyp_decl_str = " ".join(hyp_decls)
    
    thesis_f = parse_formula(thm['thesis_str'])
    thesis_lean = formula_to_lean(thesis_f)
    
    header = f"theorem {thm['name']} {vars_decl} {hyp_decl_str} : {thesis_lean} :="
    header = " ".join(header.split())
    lines.append(header)

    # Dizionario per tracciare le formule associate ai passi per il controllo di MP
    step_formulas = {}
    for step in thm['steps']:
        step_formulas[step['step_idx']] = parse_formula(step['formula_str'])

    for step in thm['steps']:
        idx = step['step_idx']
        f = step_formulas[idx]
        f_lean = formula_to_lean(f)
        just_type = step['justification_type']
        
        term = ""
        if just_type == 'Axiom':
            ax_name = step['ref_name']
            if ax_name in ['ax1', 'ax2', 'ax3']:
                if ax_name == 'ax1':
                    ax_vars = ['A', 'B']
                elif ax_name == 'ax2':
                    ax_vars = ['A', 'B', 'C']
                elif ax_name == 'ax3':
                    ax_vars = ['A', 'B']
                
                sub_json = step['substitution_json']
                args = []
                for v in ax_vars:
                    sub_val = parse_formula(str(sub_json[v]))
                    args.append(f"({formula_to_lean(sub_val)})")
                term = f"{ax_name} {' '.join(args)}"
            else:
                # Assioma specifico del dominio
                ax_formula_str = db.get_axiom(ax_name)
                ax_f = parse_formula(ax_formula_str)
                ax_vars = sorted(list(ax_f.free_variables()))
                args = [f"({v})" for v in ax_vars]
                term = f"{ax_name} {' '.join(args)}".strip()
            
        elif just_type == 'Hypothesis':
            term = step['ref_name']
            
        elif just_type == 'MP':
            arg1 = step['arg1']
            arg2 = step['arg2']
            f1 = step_formulas[arg1]
            f2 = step_formulas[arg2]
            
            if isinstance(f1, Implies) and f1.left == f2:
                term = f"step{arg1} step{arg2}"
            elif isinstance(f2, Implies) and f2.left == f1:
                term = f"step{arg2} step{arg1}"
            else:
                raise ValueError(f"I passi {arg1} e {arg2} non sono applicabili tramite Modus Ponens al passo {idx}.")
                
        elif just_type == 'Lemma':
            lemma_name = step['ref_name']
            lemma_thm = next((d for d in dep_thms if d['name'] == lemma_name), None)
            if not lemma_thm:
                lemma_thm = db.get_theorem(lemma_name)
            if not lemma_thm:
                raise ValueError(f"Lemma '{lemma_name}' non trovato per il passo {idx}.")
                
            dep_interface_vars = set()
            dep_interface_vars.update(parse_formula(lemma_thm['thesis_str']).free_variables())
            for h in lemma_thm['hypotheses']:
                dep_interface_vars.update(parse_formula(h).free_variables())
            sorted_dep_vars = sorted(list(dep_interface_vars))
            
            sub_json = step['substitution_json']
            args = []
            for v in sorted_dep_vars:
                sub_val = parse_formula(str(sub_json[v]))
                args.append(f"({formula_to_lean(sub_val)})")
                
            lemma_args = []
            if len(lemma_thm['hypotheses']) >= 1:
                lemma_args.append(f"step{step['arg1']}")
            if len(lemma_thm['hypotheses']) >= 2:
                lemma_args.append(f"step{step['arg2']}")
                
            term = f"{lemma_name} {' '.join(args)} {' '.join(lemma_args)}".strip()
            
        else:
            raise ValueError(f"Tipo di giustificazione sconosciuto '{just_type}' al passo {idx}.")
            
        lines.append(f"  let step{idx} : {f_lean} := {term}")

    last_idx = thm['steps'][-1]['step_idx']
    lines.append(f"  step{last_idx}")
    
    return "\n".join(lines)
