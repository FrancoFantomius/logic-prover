from .formula import Formula, Var, Not, Implies, And, Or, Iff, Forall, Exists, Equals, Pred, parse_formula


def formula_to_lean(formula, has_fol=False):
    """Converte un oggetto Formula nella sintassi di Lean 4."""
    if isinstance(formula, Var):
        return formula.name
    elif isinstance(formula, Not):
        return f"¬({formula_to_lean(formula.formula, has_fol=has_fol)})"
    elif isinstance(formula, Implies):
        return f"({formula_to_lean(formula.left, has_fol=has_fol)} → {formula_to_lean(formula.right, has_fol=has_fol)})"
    elif isinstance(formula, And):
        return f"({formula_to_lean(formula.left, has_fol=has_fol)} ∧ {formula_to_lean(formula.right, has_fol=has_fol)})"
    elif isinstance(formula, Or):
        return f"({formula_to_lean(formula.left, has_fol=has_fol)} ∨ {formula_to_lean(formula.right, has_fol=has_fol)})"
    elif isinstance(formula, Iff):
        return f"({formula_to_lean(formula.left, has_fol=has_fol)} ↔ {formula_to_lean(formula.right, has_fol=has_fol)})"
    elif isinstance(formula, Forall):
        if has_fol:
            return f"(∀ ({formula.var} : U), {formula_to_lean(formula.body, has_fol=has_fol)})"
        else:
            return f"(∀ {formula.var}, {formula_to_lean(formula.body, has_fol=has_fol)})"
    elif isinstance(formula, Exists):
        if has_fol:
            return f"(∃ ({formula.var} : U), {formula_to_lean(formula.body, has_fol=has_fol)})"
        else:
            return f"(∃ {formula.var}, {formula_to_lean(formula.body, has_fol=has_fol)})"
    elif isinstance(formula, Equals):
        return f"({formula_to_lean(formula.left, has_fol=has_fol)} = {formula_to_lean(formula.right, has_fol=has_fol)})"
    elif isinstance(formula, Pred):
        args_str = " ".join(formula_to_lean(a, has_fol=has_fol) if isinstance(a, Formula) else str(a) for a in formula.args)
        return f"({formula.name} {args_str})" if args_str else formula.name
    else:
        raise TypeError(f"Tipo di formula non supportato: {type(formula)}")


def extract_domain_symbols(formulas):
    """Analizza le formule per separare simboli di proposizione, termini, funzioni e predicati FOL."""
    prop_vars = set()
    term_vars = set()
    func_vars = {}
    pred_vars = {}
    bound_vars = set()

    def analyze(f, in_term=False):
        nonlocal prop_vars, term_vars, func_vars, pred_vars, bound_vars
        if isinstance(f, Var):
            if f.name not in bound_vars:
                if in_term:
                    term_vars.add(f.name)
                else:
                    prop_vars.add(f.name)
        elif isinstance(f, Not):
            analyze(f.formula, in_term=in_term)
        elif isinstance(f, (Implies, And, Or, Iff)):
            analyze(f.left, in_term=in_term)
            analyze(f.right, in_term=in_term)
        elif isinstance(f, (Forall, Exists)):
            bound_vars.add(f.var)
            analyze(f.body, in_term=in_term)
            bound_vars.remove(f.var)
        elif isinstance(f, Equals):
            analyze(f.left, in_term=True)
            analyze(f.right, in_term=True)
        elif isinstance(f, Pred):
            if in_term:
                func_vars[f.name] = max(func_vars.get(f.name, 0), len(f.args))
            else:
                pred_vars[f.name] = max(pred_vars.get(f.name, 0), len(f.args))
            for arg in f.args:
                if isinstance(arg, Formula):
                    analyze(arg, in_term=True)
                elif isinstance(arg, str):
                    if arg not in bound_vars:
                        term_vars.add(arg)

    for f in formulas:
        analyze(f)

    term_vars -= set(func_vars.keys())
    term_vars -= set(pred_vars.keys())
    prop_vars -= set(func_vars.keys())
    prop_vars -= set(pred_vars.keys())
    prop_vars -= term_vars

    has_fol = bool(term_vars or func_vars or pred_vars)
    return has_fol, sorted(list(prop_vars)), sorted(list(term_vars)), func_vars, pred_vars


def get_formula_symbols(formula):
    """Raccoglie tutti i simboli liberi presenti in una formula (variabili libere, funzioni, predicati)."""
    symbols = set()
    bound_vars = set()

    def walk(f):
        nonlocal bound_vars
        if isinstance(f, Var):
            if f.name not in bound_vars:
                symbols.add(f.name)
        elif isinstance(f, Not):
            walk(f.formula)
        elif isinstance(f, (Implies, And, Or, Iff, Equals)):
            walk(f.left)
            walk(f.right)
        elif isinstance(f, (Forall, Exists)):
            bound_vars.add(f.var)
            walk(f.body)
            bound_vars.remove(f.var)
        elif isinstance(f, Pred):
            symbols.add(f.name)
            for a in f.args:
                if isinstance(a, Formula):
                    walk(a)
                elif isinstance(a, str):
                    if a not in bound_vars:
                        symbols.add(a)
    walk(formula)
    return symbols


def _generate_steps(steps, has_fol):
    lines = []
    for step in steps:
        s_idx = step['step_idx']
        f_lean = formula_to_lean(parse_formula(step['formula_str']), has_fol=has_fol)
        j_type = step['justification_type']

        if j_type == 'Axiom':
            ax_name = step['ref_name']
            sub_json = step.get('substitution_json') or {}
            if ax_name in ['ax1', 'ax3']:
                sub_a = formula_to_lean(parse_formula(sub_json.get('A', 'A')), has_fol=has_fol)
                sub_b = formula_to_lean(parse_formula(sub_json.get('B', 'B')), has_fol=has_fol)
                lines.append(f"  have step{s_idx} : {f_lean} := {ax_name} ({sub_a}) ({sub_b})")
            elif ax_name == 'ax2':
                sub_a = formula_to_lean(parse_formula(sub_json.get('A', 'A')), has_fol=has_fol)
                sub_b = formula_to_lean(parse_formula(sub_json.get('B', 'B')), has_fol=has_fol)
                sub_c = formula_to_lean(parse_formula(sub_json.get('C', 'C')), has_fol=has_fol)
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
            args_parts = []
            if step.get('arg1') is not None:
                args_parts.append(f"step{step['arg1']}")
            if step.get('arg2') is not None:
                args_parts.append(f"step{step['arg2']}")

            args_str = (" " + " ".join(args_parts)) if args_parts else ""
            lines.append(f"  have step{s_idx} : {f_lean} := {lemma_name}{args_str}")

    last_step_idx = steps[-1]['step_idx']
    lines.append(f"  exact step{last_step_idx}")
    return lines


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

    all_db_axioms = db.get_all_axioms()

    # Raccoglie tutte le formule per l'analisi dei simboli
    all_formulas = []
    for ax_str in all_db_axioms.values():
        all_formulas.append(parse_formula(ax_str))

    for t in [thm] + dep_thms:
        all_formulas.append(parse_formula(t['thesis_str']))
        for hyp in t['hypotheses']:
            all_formulas.append(parse_formula(hyp))
        for step in t['steps']:
            all_formulas.append(parse_formula(step['formula_str']))
            if step.get('substitution_json'):
                for sub_val_str in step['substitution_json'].values():
                    all_formulas.append(parse_formula(str(sub_val_str)))

    has_fol, prop_vars, term_vars, func_vars, pred_vars = extract_domain_symbols(all_formulas)

    lines = []
    lines.append("-- Assiomi standard della logica proposizionale")
    lines.append("axiom ax1 (A B : Prop) : A → (B → A)")
    lines.append("axiom ax2 (A B C : Prop) : (A → (B → C)) → ((A → B) → (A → C))")
    lines.append("axiom ax3 (A B : Prop) : (¬A → ¬B) → (B → A)")
    lines.append("")

    # Dichiarazione delle variabili di sezione per Lean (con parentesi graffe per renderle implicite)
    if has_fol:
        lines.append("variable {U : Type}")
        for tv in term_vars:
            lines.append(f"variable {{{tv} : U}}")
        for f_name, arity in sorted(func_vars.items()):
            t_sig = " → ".join(["U"] * (arity + 1))
            lines.append(f"variable {{{f_name} : {t_sig}}}")
        for p_name, arity in sorted(pred_vars.items()):
            t_sig = " → ".join(["U"] * arity) + " → Prop"
            lines.append(f"variable {{{p_name} : {t_sig}}}")
    if prop_vars:
        for pv in prop_vars:
            lines.append(f"variable {{{pv} : Prop}}")

    # Esporta tutti gli assiomi personalizzati del database
    lines.append("")
    lines.append("-- Assiomi specifici del database della teoria")
    for ax_name, ax_str in all_db_axioms.items():
        if ax_name in ['ax1', 'ax2', 'ax3']:
            continue
        ax_f = parse_formula(ax_str)
        ax_lean = formula_to_lean(ax_f, has_fol=has_fol)
        lines.append(f"axiom {ax_name} : {ax_lean}")
    lines.append("")

    # Genera i blocchi per i lemmi da cui dipende questo teorema
    for dep in dep_thms:
        hyp_strs = []
        for idx, hyp in enumerate(dep['hypotheses']):
            f_lean = formula_to_lean(parse_formula(hyp), has_fol=has_fol)
            hyp_strs.append(f"(h{idx} : {f_lean})")

        thesis_lean = formula_to_lean(parse_formula(dep['thesis_str']), has_fol=has_fol)
        hyps_part = (" " + " ".join(hyp_strs)) if hyp_strs else ""

        lines.append(f"theorem {dep['name']}{hyps_part} : {thesis_lean} := by")
        lines.extend(_generate_steps(dep['steps'], has_fol=has_fol))
        lines.append("")

    # Genera il blocco per il teorema principale
    hyp_strs = []
    for idx, hyp in enumerate(thm['hypotheses']):
        f_lean = formula_to_lean(parse_formula(hyp), has_fol=has_fol)
        hyp_strs.append(f"(h{idx} : {f_lean})")

    thesis_lean = formula_to_lean(parse_formula(thm['thesis_str']), has_fol=has_fol)
    hyps_part = (" " + " ".join(hyp_strs)) if hyp_strs else ""

    lines.append(f"theorem {thm['name']}{hyps_part} : {thesis_lean} := by")
    lines.extend(_generate_steps(thm['steps'], has_fol=has_fol))
    lines.append("")

    return "\n".join(lines)



