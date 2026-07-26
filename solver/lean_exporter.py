from .formula import Formula, Var, Not, Implies, And, Or, Iff, Forall, Exists, Equals, Pred, parse_formula

def formula_to_lean(formula):
    """Converte un oggetto Formula nella sintassi di Lean 4."""
    if isinstance(formula, Var):
        return formula.name
    elif isinstance(formula, Not):
        return f"¬({formula_to_lean(formula.formula)})"
    elif isinstance(formula, Implies):
        return f"({formula_to_lean(formula.left)} → {formula_to_lean(formula.right)})"
    elif isinstance(formula, And):
        return f"({formula_to_lean(formula.left)} ∧ {formula_to_lean(formula.right)})"
    elif isinstance(formula, Or):
        return f"({formula_to_lean(formula.left)} ∨ {formula_to_lean(formula.right)})"
    elif isinstance(formula, Iff):
        return f"({formula_to_lean(formula.left)} ↔ {formula_to_lean(formula.right)})"
    elif isinstance(formula, Forall):
        return f"(∀ {formula.var}, {formula_to_lean(formula.body)})"
    elif isinstance(formula, Exists):
        return f"(∃ {formula.var}, {formula_to_lean(formula.body)})"
    elif isinstance(formula, Equals):
        return f"({formula_to_lean(formula.left)} = {formula_to_lean(formula.right)})"
    elif isinstance(formula, Pred):
        args_str = " ".join(formula_to_lean(a) if isinstance(a, Formula) else str(a) for a in formula.args)
        return f"({formula.name} {args_str})" if args_str else formula.name
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

    # Genera i blocchi per i lemmi da cui dipende questo teorema
    for dep in dep_thms:
        dep_vars = set()
        dep_vars.update(parse_formula(dep['thesis_str']).free_variables())
        for hyp in dep['hypotheses']:
            dep_vars.update(parse_formula(hyp).free_variables())
        for step in dep['steps']:
            dep_vars.update(parse_formula(step['formula_str']).free_variables())
            if step.get('substitution_json'):
                for sub_val_str in step['substitution_json'].values():
                    f = parse_formula(str(sub_val_str))
                    dep_vars.update(f.free_variables())
                    
        sorted_dep_vars = sorted(list(dep_vars))
        vars_str = " ".join(sorted_dep_vars)
        
        # Intestazione delle variabili per il lemma
        if sorted_dep_vars:
            lines.append(f"variable ({vars_str} : Prop)")
            
        hyp_strs = []
        for idx, hyp in enumerate(dep['hypotheses']):
            f_lean = formula_to_lean(parse_formula(hyp))
            hyp_strs.append(f"(h{idx} : {f_lean})")
            
        thesis_lean = formula_to_lean(parse_formula(dep['thesis_str']))
        hyps_part = (" " + " ".join(hyp_strs)) if hyp_strs else ""
        
        lines.append(f"theorem {dep['name']}{hyps_part} : {thesis_lean} := by")
        
        for step in dep['steps']:
            s_idx = step['step_idx']
            f_lean = formula_to_lean(parse_formula(step['formula_str']))
            j_type = step['justification_type']
            
            if j_type == 'Axiom':
                ax_name = step['ref_name']
                sub_json = step.get('substitution_json') or {}
                if ax_name in ['ax1', 'ax3']:
                    sub_a = formula_to_lean(parse_formula(sub_json.get('A', 'A')))
                    sub_b = formula_to_lean(parse_formula(sub_json.get('B', 'B')))
                    lines.append(f"  have step{s_idx} : {f_lean} := {ax_name} ({sub_a}) ({sub_b})")
                elif ax_name == 'ax2':
                    sub_a = formula_to_lean(parse_formula(sub_json.get('A', 'A')))
                    sub_b = formula_to_lean(parse_formula(sub_json.get('B', 'B')))
                    sub_c = formula_to_lean(parse_formula(sub_json.get('C', 'C')))
                    lines.append(f"  have step{s_idx} : {f_lean} := ax2 ({sub_a}) ({sub_b}) ({sub_c})")
                else:
                    lines.append(f"  have step{s_idx} : {f_lean} := {ax_name}")
            elif j_type == 'Hypothesis':
                ref_name = step['ref_name']
                lines.append(f"  have step{s_idx} : {f_lean} := {ref_name}")
            elif j_type == 'MP':
                arg1 = step['arg1']
                arg2 = step['arg2']
                lines.append(f"  have step{s_idx} : {f_lean} := step{arg2} step{arg1}")
            elif j_type == 'Lemma':
                lemma_name = step['ref_name']
                sub_json = step.get('substitution_json') or {}
                
                # Recupera la definizione del lemma per ricavare l'ordine delle sue variabili
                ref_lemma = db.get_theorem(lemma_name)
                ref_vars = set()
                if ref_lemma:
                    ref_vars.update(parse_formula(ref_lemma['thesis_str']).free_variables())
                    for h in ref_lemma['hypotheses']:
                        ref_vars.update(parse_formula(h).free_variables())
                    for s in ref_lemma['steps']:
                        ref_vars.update(parse_formula(s['formula_str']).free_variables())
                sorted_ref_vars = sorted(list(ref_vars))
                
                args_parts = []
                for rv in sorted_ref_vars:
                    val_str = sub_json.get(rv, rv)
                    args_parts.append(f"({formula_to_lean(parse_formula(str(val_str)))})")
                    
                if step.get('arg1') is not None:
                    args_parts.append(f"step{step['arg1']}")
                if step.get('arg2') is not None:
                    args_parts.append(f"step{step['arg2']}")
                    
                args_str = (" " + " ".join(args_parts)) if args_parts else ""
                lines.append(f"  have step{s_idx} : {f_lean} := {lemma_name}{args_str}")
                
        last_step_idx = dep['steps'][-1]['step_idx']
        lines.append(f"  exact step{last_step_idx}")
        lines.append("")

    # Genera il blocco per il teorema principale
    sorted_current_vars = sorted(list(current_vars))
    vars_str = " ".join(sorted_current_vars)
    if sorted_current_vars:
        lines.append(f"variable ({vars_str} : Prop)")
        
    hyp_strs = []
    for idx, hyp in enumerate(thm['hypotheses']):
        f_lean = formula_to_lean(parse_formula(hyp))
        hyp_strs.append(f"(h{idx} : {f_lean})")
        
    thesis_lean = formula_to_lean(parse_formula(thm['thesis_str']))
    hyps_part = (" " + " ".join(hyp_strs)) if hyp_strs else ""
    
    lines.append(f"theorem {thm['name']}{hyps_part} : {thesis_lean} := by")
    
    for step in thm['steps']:
        s_idx = step['step_idx']
        f_lean = formula_to_lean(parse_formula(step['formula_str']))
        j_type = step['justification_type']
        
        if j_type == 'Axiom':
            ax_name = step['ref_name']
            sub_json = step.get('substitution_json') or {}
            if ax_name in ['ax1', 'ax3']:
                sub_a = formula_to_lean(parse_formula(sub_json.get('A', 'A')))
                sub_b = formula_to_lean(parse_formula(sub_json.get('B', 'B')))
                lines.append(f"  have step{s_idx} : {f_lean} := {ax_name} ({sub_a}) ({sub_b})")
            elif ax_name == 'ax2':
                sub_a = formula_to_lean(parse_formula(sub_json.get('A', 'A')))
                sub_b = formula_to_lean(parse_formula(sub_json.get('B', 'B')))
                sub_c = formula_to_lean(parse_formula(sub_json.get('C', 'C')))
                lines.append(f"  have step{s_idx} : {f_lean} := ax2 ({sub_a}) ({sub_b}) ({sub_c})")
            else:
                lines.append(f"  have step{s_idx} : {f_lean} := {ax_name}")
        elif j_type == 'Hypothesis':
            ref_name = step['ref_name']
            lines.append(f"  have step{s_idx} : {f_lean} := {ref_name}")
        elif j_type == 'MP':
            arg1 = step['arg1']
            arg2 = step['arg2']
            lines.append(f"  have step{s_idx} : {f_lean} := step{arg2} step{arg1}")
        elif j_type == 'Lemma':
            lemma_name = step['ref_name']
            sub_json = step.get('substitution_json') or {}
            
            ref_lemma = db.get_theorem(lemma_name)
            ref_vars = set()
            if ref_lemma:
                ref_vars.update(parse_formula(ref_lemma['thesis_str']).free_variables())
                for h in ref_lemma['hypotheses']:
                    ref_vars.update(parse_formula(h).free_variables())
                for s in ref_lemma['steps']:
                    ref_vars.update(parse_formula(s['formula_str']).free_variables())
            sorted_ref_vars = sorted(list(ref_vars))
            
            args_parts = []
            for rv in sorted_ref_vars:
                val_str = sub_json.get(rv, rv)
                args_parts.append(f"({formula_to_lean(parse_formula(str(val_str)))})")
                
            if step.get('arg1') is not None:
                args_parts.append(f"step{step['arg1']}")
            if step.get('arg2') is not None:
                args_parts.append(f"step{step['arg2']}")
                
            args_str = (" " + " ".join(args_parts)) if args_parts else ""
            lines.append(f"  have step{s_idx} : {f_lean} := {lemma_name}{args_str}")
            
    last_step_idx = thm['steps'][-1]['step_idx']
    lines.append(f"  exact step{last_step_idx}")
    lines.append("")

    return "\n".join(lines)
