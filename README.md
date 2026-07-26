# Solver Library

**Solver** è una libreria Python per la rappresentazione di formule logiche, il dimostratore automatico di teoremi in sistemi alla Hilbert, la verifica formale locale e l'integrazione con l'assistente di prova **Lean 4**, nonché l'esplorazione automatica di nuove conseguenze logiche e la gestione di teorie di Primo e Secondo Ordine.

---

## Caratteristiche Principali

- **AST Logico e Parser**: Costruzione orientata agli oggetti di formule logiche (Proposizionali, Primo Ordine, Secondo Ordine, Uguaglianza) con supporto a sintassi Unicode (`∀`, `∃`, `→`, `↔`, `∧`, `∨`, `¬`) ed ASCII (`forall`, `exists`, `->`, `<->`, `&`, `|`, `~`).
- **Database SQLite per Teorie (`TheoryDatabase`)**: Memorizzazione strutturata e persistente di assiomi, ipotesi, teoremi dimostrati, passi della dimostrazione e grafico delle dipendenze.
- **Prover Automatico (`prove`)**: Algoritmo di forward search basato su Breadth-First Search (BFS) e Modus Ponens con istanziazione schematica di assiomi e riutilizzo di lemmi.
- **Verificatore a Due Livelli (`verifier`)**:
  1. Validazione strutturale e correttezza logica locale in Python.
  2. Generazione ed esecuzione di codice self-contained in **Lean 4** tramite la CLI ufficiale di Lean.
- **Esploratore di Conseguenze Logiche (`explore_consequences`)**: Generazione automatica e saturazione di nuove formule derivabili, con verifica ed inserimento automatico nel database.
- **Librerie Assiomatiche Pronte all'Uso (`solver.dependencies`)**: Moduli integrati con assiomi per il calcolo proposizionale, la logica del primo ordine (FOL) con uguaglianza di Leibniz e la logica del secondo ordine (SOL) con schema di comprensione, scelta ed induzione matematica.

---

## Installazione

Assicurati di avere Python >= 3.8 installato. Per installare la libreria in modalità sviluppatore:

```bash
pip install -e .
```

Per eseguire i test unitari:

```bash
python -m unittest discover tests
```

*(Opzionale)* Per abilitare la verifica tramite Lean 4, installa il compilatore `lean` e assicurati che sia disponibile nel `PATH` di sistema.

---

## Esempi Basici (Quick Start)

### 1. Creare e manipolare Formule

Puoi costruire le formule programmaticamente con l'AST, usare gli operatori overloaded di Python (`~`, `>>`, `&`, `|`), oppure usare il parser:

```python
from solver import Var, Implies, parse_formula, formula_to_lean

# Costruzione programmatica tramite AST
p = Var("p")
q = Var("q")
formula1 = p >> (q >> p)
print("Formula AST:", formula1)  # (p -> (q -> p))

# Parsing da stringa (supporta sintassi ASCII o Unicode)
formula2 = parse_formula("forall x, (P(x) -> Q(x))")
print("Formula Parser:", formula2)  # (forall x, (P(x) -> Q(x)))

# Conversione in sintassi Lean 4
print("Lean 4:", formula_to_lean(formula2))  # (∀ x, ((P x) → (Q x)))
```

### 2. Gestione del Database e Assiomi

Inizializza una teoria logica registrando gli assiomi del calcolo proposizionale:

```python
from solver import TheoryDatabase

db = TheoryDatabase("my_theory.db")

# Aggiunta manuale degli assiomi di Hilbert
db.add_axiom("ax1", "A -> (B -> A)")
db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")
db.add_axiom("ax3", "(~A -> ~B) -> (B -> A)")

print("Assiomi registrati:", db.get_all_axioms())
```

### 3. Dimostrazione Automatica di un Teorema

Genera una dimostrazione formale per la tesi $p \to p$ a partire dagli assiomi registrati:

```python
from solver import TheoryDatabase, prove

db = TheoryDatabase("my_theory.db")
db.add_axiom("ax1", "A -> (B -> A)")
db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")
db.add_axiom("ax3", "(~A -> ~B) -> (B -> A)")

# Dimostrazione di (p -> p) senza ipotesi
steps = prove(thesis_str="p -> p", hypotheses_strs=[], db=db)

for step in steps:
    print(f"Passo {step['step_idx']}: {step['formula_str']} [{step['justification_type']}]")
```

### 4. Validazione Locale, Lean 4 ed Esportazione

Verifica il teorema e salvalo nel database:

```python
from solver import TheoryDatabase, verify_and_save, export_proof

db = TheoryDatabase("my_theory.db")
# (Ipotizzando che gli assiomi siano stati caricati e i passi generati...)

thm = {
    'name': 'identita_p',
    'thesis_str': 'p -> p',
    'hypotheses': [],
    'steps': steps
}

success, msg = verify_and_save(thm, db)
if success:
    print("Teorema verificato con successo!")
    # Esporta il codice Lean 4 autosufficiente
    lean_code = export_proof("identita_p", db)
    print("\n--- Codice Sorgente Lean 4 ---")
    print(lean_code)
else:
    print("Errore di verifica:", msg)
```

### 5. Esplorazione Automatica di Nuovi Teoremi

Consenti al solver di esplorare e scoprire automaticamente nuove conseguenze derivabili dagli assiomi caricati:

```python
from solver import TheoryDatabase, explore_consequences, dependencies

db = TheoryDatabase("explore.db")

# Carica tutti gli assiomi logici di Primo e Secondo Ordine inclusi nel pacchetto
dependencies.load_all_logic_axioms(db)

# Genera ed esplora fino a 5 nuovi teoremi
nuovi_teoremi = explore_consequences(
    db, 
    basic_vars=['p'], 
    max_depth=1, 
    max_theorems=5
)

print(f"Generati e verificati {nuovi_teoremi} nuovi teoremi!")
```

---

## Documentazione dei Moduli

Per una guida completa su ciascun modulo della libreria, consulta la documentazione dettagliata:

**[DOCUMENTATION.md](DOCUMENTATION.md)**

Modulo | Descrizione
--- | ---
[`solver.formula`](DOCUMENTATION.md#1-solverformula) | AST per formule proposizionali, FOL e SOL, parser e trasformazioni
[`solver.database`](DOCUMENTATION.md#2-solverdatabase) | Interfaccia SQLite per assiomi, teoremi, passi e dipendenze
[`solver.prover`](DOCUMENTATION.md#3-solverprover) | Algoritmo di dimostrazione automatica Forward BFS con Modus Ponens
[`solver.verifier`](DOCUMENTATION.md#4-solververifier) | Verificatore strutturale locale e integrazione con il compilatore Lean 4
[`solver.explorer`](DOCUMENTATION.md#5-solverexplorer) | Generazione e saturazione automatica di nuove conseguenze teoriche
[`solver.lean_exporter`](DOCUMENTATION.md#6-solverlean_exporter) | Traduttore AST-Lean e generatore di sorgenti Lean 4 verificabili
[`solver.dependencies`](DOCUMENTATION.md#7-solverdependencies) | Pacchetto di assiomi per Logica del Primo Ordine (FOL) e Secondo Ordine (SOL)
