import os
from database import TheoryDatabase
from explorer import explore_consequences

def main():
    print("=== ANALISI 1: ASSIOMI DEI NUMERI REALI E COMPLETEZZA ===")
    
    db_path = "analysis_1.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass
            
    db = TheoryDatabase(db_path)
    
    # Registra i concetti base di Analisi 1 come variabili proposizionali:
    # - OrderedField: R è un campo ordinato
    # - Complete: R soddisfa la completezza di Dedekind (proprietà del sup)
    # - Archimedean: R soddisfa la proprietà di Archimede
    # - MonotoneConvergence: vale il teorema di convergenza monotona
    # - NestedIntervals: vale il teorema degli intervalli inscatolati (Cantor)
    # - CauchyComplete: R è completo nel senso di Cauchy (ogni successione di Cauchy converge)
    # - BolzanoWeierstrass: vale il teorema di Bolzano-Weierstrass (successioni limitate hanno sottosuccessioni convergenti)
    # - HeineBorel: vale il teorema di Heine-Borel (i chiusi e limitati sono compatti)
    # - IntermediateValue: vale il teorema dei valori intermedi (teorema di Bolzano degli zeri)
    
    print("\nRegistrazione degli assiomi e delle implicazioni di Analisi 1...")
    
    # Assunzioni/Ipotesi di base
    db.add_axiom("an_hyp_field", "OrderedField")
    db.add_axiom("an_hyp_complete", "Complete")
    db.add_axiom("an_hyp_arch", "Archimedean")
    
    # Assiomi di implicazione (teoremi di connessione)
    db.add_axiom("an_ax1", "OrderedField -> (Complete -> MonotoneConvergence)")
    db.add_axiom("an_ax2", "OrderedField -> (MonotoneConvergence -> NestedIntervals)")
    db.add_axiom("an_ax3", "OrderedField -> (NestedIntervals -> (Archimedean -> CauchyComplete))")
    db.add_axiom("an_ax4", "OrderedField -> (CauchyComplete -> (Archimedean -> BolzanoWeierstrass))")
    db.add_axiom("an_ax5", "OrderedField -> (BolzanoWeierstrass -> HeineBorel)")
    db.add_axiom("an_ax6", "OrderedField -> (HeineBorel -> IntermediateValue)")
    
    print("\nAssiomi di Analisi 1 registrati:")
    for name, f_str in db.get_all_axioms().items():
        print(f"  {name}: {f_str}")
        
    print("\nAvvio dell'esplorazione delle conseguenze logiche...")
    print("Filtro: Vengono salvati solo i teoremi con una dimostrazione più lunga di 4 passi (min_proof_steps=5).")
    
    # Esegue l'esploratore
    count = explore_consequences(
        db,
        basic_vars=[
            'OrderedField', 'Complete', 'Archimedean', 
            'MonotoneConvergence', 'NestedIntervals', 
            'CauchyComplete', 'BolzanoWeierstrass', 
            'HeineBorel', 'IntermediateValue'
        ],
        max_depth=0,
        max_theorems=50,
        min_proof_steps=5
    )
    
    print(f"\nEsplorazione completata! Nuovi teoremi validati e salvati: {count}")
    
    # Esporta tutte le dimostrazioni in un unico file lean
    export_all_to_lean_file(db, "analysis_1.lean")

def export_all_to_lean_file(db: TheoryDatabase, filename="analysis_1.lean"):
    from formula import parse_formula, Implies
    from lean_exporter import formula_to_lean

    with db.connection_scope() as conn:
        cursor = conn.execute("SELECT name FROM theorems WHERE is_verified = 1 ORDER BY id;")
        thm_names = [row[0] for row in cursor.fetchall()]
        
    all_axioms = db.get_all_axioms()
    
    # Raccoglie tutte le variabili proposizionali del sistema per dichiararle nella firma di ogni teorema
    all_vars = {'A', 'B', 'C'}
    for thm_name in thm_names:
        thm = db.get_theorem(thm_name)
        all_vars.update(parse_formula(thm['thesis_str']).free_variables())
        for hyp in thm['hypotheses']:
            all_vars.update(parse_formula(hyp).free_variables())
        for step in thm['steps']:
            all_vars.update(parse_formula(step['formula_str']).free_variables())
            
    for name, f_str in all_axioms.items():
        if name not in ['ax1', 'ax2', 'ax3']:
            all_vars.update(parse_formula(f_str).free_variables())
            
    sorted_all_vars = sorted(list(all_vars))
    vars_decl = f"({ ' '.join(sorted_all_vars) } : Prop)"
    
    lines = []
    lines.append("namespace Analysis1")
    lines.append("")
    lines.append("set_option linter.unusedVariables false")
    lines.append("")
    lines.append("-- Assiomi standard della logica proposizionale")
    lines.append("axiom ax1 (A B : Prop) : A → (B → A)")
    lines.append("axiom ax2 (A B C : Prop) : (A → (B → C)) → ((A → B) → (A → C))")
    lines.append("axiom ax3 (A B : Prop) : (¬A → ¬B) → (B → A)")
    lines.append("")

    lines.append("-- Assiomi specifici di Analisi 1")
    for name, f_str in sorted(all_axioms.items()):
        if name not in ['ax1', 'ax2', 'ax3']:
            ax_f = parse_formula(f_str)
            ax_vars = sorted(list(ax_f.free_variables()))
            ax_vars_decl = f"({ ' '.join(ax_vars) } : Prop)" if ax_vars else ""
            lines.append(f"axiom {name} {ax_vars_decl} : {formula_to_lean(ax_f)}")
    lines.append("")

    for thm_name in thm_names:
        thm = db.get_theorem(thm_name)
        
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
                    raise ValueError(f"MP error at step {idx}")
            elif just_type == 'Lemma':
                lemma_name = step['ref_name']
                lemma_thm = db.get_theorem(lemma_name)
                
                args = [f"({v})" for v in sorted_all_vars]
                
                lemma_args = []
                if len(lemma_thm['hypotheses']) >= 1:
                    lemma_args.append(f"step{step['arg1']}")
                if len(lemma_thm['hypotheses']) >= 2:
                    lemma_args.append(f"step{step['arg2']}")
                term = f"{lemma_name} {' '.join(args)} {' '.join(lemma_args)}".strip()
                
            lines.append(f"  let step{idx} : {f_lean} := {term}")
            
        last_idx = thm['steps'][-1]['step_idx']
        lines.append(f"  step{last_idx}")
        lines.append("")
        
    lines.append("end Analysis1")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nSalvato con successo in {filename}")

if __name__ == "__main__":
    main()

