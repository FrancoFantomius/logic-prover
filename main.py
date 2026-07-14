from database import TheoryDatabase
from explorer import explore_consequences

def main():
    print("=== MOTORE DI ESPLORAZIONE DELLE CONSEGUENZE LOGICHE ===")
    print("Inizializzazione database...")
    db = TheoryDatabase("theory.db")
    
    # Inizializza gli assiomi standard della logica proposizionale
    db.add_axiom("ax1", "A -> (B -> A)")
    db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")
    db.add_axiom("ax3", "(~A -> ~B) -> (B -> A)")
    
    # Consente di aggiungere definizioni aggiuntive espresse come assiomi.
    # Ad esempio, la definizione di OR (A | B) espressa come (~A -> B):
    # db.add_axiom("or_def_1", "(A | B) -> (~A -> B)")
    # db.add_axiom("or_def_2", "(~A -> B) -> (A | B)")
    
    print("\nAssiomi registrati:")
    for name, f_str in db.get_all_axioms().items():
        print(f"  {name}: {f_str}")
        
    print("\nAvvio dell'esplorazione delle conseguenze logiche...")
    print("Configurazione: Variabili di base = ['p'], Profondità massima = 2")
    
    # Esegue l'esploratore
    count = explore_consequences(db, basic_vars=['p'], max_depth=2, max_theorems=15)
    
    print(f"\nEsplorazione completata! Nuovi teoremi validati e salvati: {count}")
    
    # Mostra l'elenco di tutti i teoremi salvati
    print("\nElenco di tutti i teoremi verificati nel database:")
    with db.connection_scope() as conn:
        cursor = conn.execute("SELECT name, thesis_str FROM theorems WHERE is_verified = 1;")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    main()
