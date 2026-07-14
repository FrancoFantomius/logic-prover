import os
from database import TheoryDatabase
from explorer import explore_consequences

def main():
    print("=== TEORIA DEI GRUPPI: PRIMO TEOREMA DI ISOMORFISMO ===")
    
    db_path = "group_theory.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass
            
    db = TheoryDatabase(db_path)
    
    # Registra le basi (assiomi e ipotesi di base) per la teoria dei gruppi
    # Hom: phi è un omomorfismo
    # Ker: K è il nucleo di phi
    # Normal: K è un sottogruppo normale di G
    # QuotientGroup: G/K è un gruppo quoziente ben definito
    # InducedHom: la mappa indotta phi_bar è un omomorfismo
    # Bijective: phi_bar è biettiva
    # Isomorphism: phi_bar è un isomorfismo (G/K ~= Im(phi))
    
    print("\nRegistrazione assiomi della teoria dei gruppi...")
    db.add_axiom("gp_hyp_hom", "Hom")  # Assunzione iniziale: phi è omomorfismo
    db.add_axiom("gp_ax1", "Hom -> Ker")  # Il nucleo è ben definito
    db.add_axiom("gp_ax2", "Ker -> Normal")  # Il nucleo è normale
    db.add_axiom("gp_ax3", "Normal -> QuotientGroup")  # Il quoziente è un gruppo
    db.add_axiom("gp_ax4", "QuotientGroup -> (Hom -> InducedHom)")  # La mappa indotta è un omomorfismo
    db.add_axiom("gp_ax5", "Hom -> Bijective")  # La mappa indotta è biettiva
    db.add_axiom("gp_ax6", "InducedHom -> (Bijective -> Isomorphism)")  # Omo + Bie => Isomorfismo
    
    print("\nAssiomi registrati:")
    for name, f_str in db.get_all_axioms().items():
        print(f"  {name}: {f_str}")
        
    print("\nAvvio dell'esplorazione delle conseguenze logiche...")
    print("Filtro: Vengono salvati solo i teoremi con una dimostrazione più lunga di 4 passi (min_proof_steps=5).")
    
    # Esegue l'esploratore con profondità 0 per concentrarsi sulle combinazioni dirette degli assiomi della teoria
    count = explore_consequences(
        db,
        basic_vars=['Hom', 'Ker', 'Normal', 'QuotientGroup', 'InducedHom', 'Bijective', 'Isomorphism'],
        max_depth=0,
        max_theorems=50,
        min_proof_steps=5
    )
    
    print(f"\nEsplorazione completata! Nuovi teoremi validati e salvati: {count}")
    
    # Mostra l'elenco di tutti i teoremi salvati nel database con la loro dimostrazione Lean
    print("\nTeoremi salvati nel database:")
    with db.connection_scope() as conn:
        cursor = conn.execute("SELECT name, thesis_str, lean_code FROM theorems WHERE is_verified = 1;")
        rows = cursor.fetchall()
        for row in rows:
            print(f"\n--- {row[0]}: {row[1]} ---")
            print(row[2])

if __name__ == "__main__":
    main()
