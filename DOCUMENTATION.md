# Manuale di Documentazione dei Moduli (`solver`)

Questo documento contiene la guida di riferimento dettagliata per ciascun modulo e sottopacchetto presente nella libreria `solver`.

---

## Indice

1. [solver.formula](#1-solverformula)
2. [solver.database](#2-solverdatabase)
3. [solver.prover](#3-solverprover)
4. [solver.verifier](#4-solververifier)
5. [solver.explorer](#5-solverexplorer)
6. [solver.lean_exporter](#6-solverlean_exporter)
7. [solver.dependencies](#7-solverdependencies)

---

## 1. `solver.formula`

Il modulo [`solver.formula`](file:///c:/Users/franc/Programmazione/solver/solver/formula.py) definisce la struttura dell'Abstract Syntax Tree (AST) per le formule logiche e fornisce un parser da stringa a oggetto AST.

### Classi dell'AST

Tutte le formule ereditano dalla classe astratta `Formula`.

- **`Var(name)`**: Rappresenta una variabile proposizionale o individuale (es. `Var("p")`, `Var("x")`).
- **`Not(formula)`**: Negazione logica (`~A` o `Not(A)`).
- **`Implies(left, right)`**: Implicazione logica (`A -> B` o `A >> B`).
- **`And(left, right)`**: Congiunzione logica (`A & B` o `And(A, B)`).
- **`Or(left, right)`**: Disgiunzione logica (`A | B` or `Or(A, B)`).
- **`Iff(left, right)`**: Doppia implicazione / Equivalenza logica (`A <-> B` o `Iff(A, B)`).
- **`Forall(var, body)`**: Quantificatore universale (`forall x, P(x)` o `Forall("x", P)`).
- **`Exists(var, body)`**: Quantificatore esistenziale (`exists x, P(x)` o `Exists("x", P)`).
- **`Equals(left, right)`**: Uguaglianza formale (`x = y` o `Equals("x", "y")`).
- **`Pred(name, args)`**: Applicazione di un predicato (es. `Pred("P", [Var("x"), Var("y")])`).

### Overloading degli Operatori Python

È possibile combinare le istanze di `Formula` con sintassi nativa Python:
- `~f` $\rightarrow$ `Not(f)`
- `f1 >> f2` $\rightarrow$ `Implies(f1, f2)`
- `f1 & f2` $\rightarrow$ `And(f1, f2)`
- `f1 | f2` $\rightarrow$ `Or(f1, f2)`

### Metodi Principali di `Formula`

#### `substitute(sub_map)`
Sostituisce le variabili specificate nelle chiavi del dizionario `sub_map` (es. `{"A": Var("p"), "B": Var("q")}`) con le corrispettive formule. Gestisce correttamente il fenomeno del variable binding evitando la sostituzione involontaria delle variabili legate da quantificatori.

#### `free_variables()`
Restituisce un insieme (`set`) contenente i nomi di tutte le variabili libere presenti nella formula.

#### `match_schema(schema)`
Confronta la formula corrente con una formula schema (contenente meta-variabili). Se il matching ha successo, restituisce un dizionario `{nome_meta_variabile: sottoformula_o_stringa}`, altrimenti restituisce `None`.

### Funzione `parse_formula(s)`

Converte una stringa di testo in un albero `Formula`.

- **Operatori ASCII supportati**: `->`, `<->`, `&`, `|`, `~`, `!`, `=`, `forall`, `exists`.
- **Simboli Unicode supportati**: `→`, `↔`, `∧`, `∨`, `¬`, `∀`, `∃`.

#### Esempio di utilizzo:

```python
from solver.formula import parse_formula, Var, Not, Implies

# Uso degli operatori Python
A = Var("A")
B = Var("B")
f1 = (~A) >> B
print(f1)  # (~A -> B)

# Parsing da stringa
f2 = parse_formula("forall x, (P(x) -> (exists y, (x = y)))")
print("Variabili libere in f2:", f2.free_variables())

# Matching di uno schema
schema = parse_formula("P -> Q")
concrete = parse_formula("(a & b) -> c")
bindings = concrete.match_schema(schema)
print("Bindings del match:", bindings)  # {'P': And(Var('a'), Var('b')), 'Q': Var('c')}
```

---

## 2. `solver.database`

Il modulo [`solver.database`](file:///c:/Users/franc/Programmazione/solver/solver/database.py) gestisce la persistenza dei dati relativi a teorie, assiomi, teoremi e dimostrazioni mediante un database SQLite.

### Classe `TheoryDatabase`

#### Inizializzazione
```python
db = TheoryDatabase(db_path="theory.db")
```

All'atto della creazione, `init_db()` viene eseguito automaticamente per creare le seguenti tabelle se non esistono:
1. **`axioms`**: Memorizza gli assiomi (`id`, `name`, `formula_str`).
2. **`theorems`**: Memorizza la tesi dei teoremi (`id`, `name`, `thesis_str`, `lean_code`, `is_verified`).
3. **`theorem_hypotheses`**: Mantiene l'elenco delle ipotesi associate a ciascun teorema.
4. **`theorem_steps`**: Memorizza ciascun passo della dimostrazione con tipo di giustificazione (`Axiom`, `Hypothesis`, `MP`, `Lemma`), indici dei passi argomenti (`arg1`, `arg2`), riferimento (`ref_name`) e sostituzioni JSON.
5. **`dependencies`**: Traccia le dipendenze orientate (DAG) tra teoremi e lemmi.

### Metodi Principali

- **`add_axiom(name, formula_str)`**: Inserisce un nuovo assioma nel database.
- **`get_axiom(name)`**: Recupera la stringa della formula dell'assioma specificato.
- **`get_all_axioms()`**: Restituisce un dizionario `{nome: stringa_formula}` di tutti gli assiomi registrati.
- **`save_theorem(name, thesis_str, hypotheses, steps, dependencies=None, lean_code=None, is_verified=0)`**: Salva o sovrascrive un teorema, le sue ipotesi, i suoi passi e le sue dipendenze.
- **`get_theorem(name)`**: Carica dal database la struttura completa di un teorema sotto forma di dizionario Python.
- **`get_dependencies_recursive(theorem_name)`**: Restituisce la lista ordinata topologicamente di tutti i lemmi da cui il teorema dipende ricorsivamente.

#### Esempio di utilizzo:

```python
from solver.database import TheoryDatabase

db = TheoryDatabase("algebra.db")
db.add_axiom("associativita", "forall x, forall y, forall z, (f(f(x, y), z) = f(x, f(y, z)))")

axioms = db.get_all_axioms()
print("Assiomi salvati:", axioms)
```

---

## 3. `solver.prover`

Il modulo [`solver.prover`](file:///c:/Users/franc/Programmazione/solver/solver/prover.py) fornisce l'algoritmo per la ricerca automatica di dimostrazioni formali nel sistema alla Hilbert.

### Funzioni Principali

#### `prove(thesis_str, hypotheses_strs, db, exclude_name=None, max_depth=10, max_formulas=1000, timeout_seconds=30)`

Ricerca automaticamente una sequenza di passi deduttivi per dimostrare `thesis_str` a partire da `hypotheses_strs`.

**Algoritmo**:
1. Estrae le sottoformule dalla tesi e dalle ipotesi per costruire il *Candidate Pool*.
2. Istanzia gli schemi assiomatici di Hilbert (`ax1`, `ax2`, `ax3`) e i lemmi già verificati nel `TheoryDatabase` usando i candidati.
3. Applica una ricerca in ampiezza (BFS) basata sulla regola del **Modus Ponens (MP)** per derivare nuove formule finché la tesi non viene raggiunta o si supera il timeout.
4. Richiama `reconstruct_proof` per generare una sequenza di passi ordinata topologicamente.

#### `reconstruct_proof(goal, derived, lemma_map=None, db=None)`
Ripercorre a ritroso le giustificazioni raccolte e ricostruisce la catena minimale di passi di dimostrazione dal primo assioma/ipotesi fino al `goal`.

#### `get_subformulas(formula)`
Funzione ausiliaria ricorsiva che estrae tutte le sottoformule che compongono un oggetto `Formula`.

#### Esempio di utilizzo:

```python
from solver.database import TheoryDatabase
from solver.prover import prove

db = TheoryDatabase("logic.db")
db.add_axiom("ax1", "A -> (B -> A)")
db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")

# Dimostra che (p -> (q -> p)) segue direttamente dall'assioma 1
steps = prove(thesis_str="p -> (q -> p)", hypotheses_strs=[], db=db)
print("Numero di passi trovati:", len(steps))
```

---

## 4. `solver.verifier`

Il modulo [`solver.verifier`](file:///c:/Users/franc/Programmazione/solver/solver/verifier.py) esegue la verifica a due livelli delle dimostrazioni formali.

### Funzioni Principali

#### `verify_proof_local(thm, db)`
Esegue un controllo di validità formale in ambiente Python puro.
Verifica che ogni passo sia giustificato da:
- **`Axiom`**: La formula deve fare il match con uno schema di assioma presente nel DB.
- **`Hypothesis`**: Il riferimento `ref_name` (es. `h0`) deve corrispondere esattamente all'ipotesi.
- **`MP`**: La formula deve essere la conclusione valida del Modus Ponens applicato ai due passi precedenti specificati da `arg1` e `arg2`.
- **`Lemma`**: La formula e gli argomenti devono corrispondere alla tesi e alle ipotesi sostituite di un lemma verificato nel DB.

Restituisce una tupla `(ok: bool, error_message: str | None)`.

#### `verify_proof_with_lean(thm, db)`
Genera il codice sorgente Lean 4 autosufficiente per il teorema (tramite `solver.lean_exporter`) e lo compila invocando l'eseguibile CLI `lean`.
Restituisce `(True, lean_code)` se la compilazione avviene con successo (exit code 0), altrimenti `(False, error_message)`.

#### `verify_and_save(thm, db)`
Esegue prima `verify_proof_local`. Se ha successo, tenta la verifica con `verify_proof_with_lean`. Se Lean 4 approva il teorema, lo memorizza nel `TheoryDatabase` impostando `is_verified = 1`.

#### Esempio di utilizzo:

```python
from solver.database import TheoryDatabase
from solver.verifier import verify_proof_local

db = TheoryDatabase("logic.db")
thm_def = {
    'name': 'demo_thm',
    'thesis_str': 'A -> (B -> A)',
    'hypotheses': [],
    'steps': [
        {
            'step_idx': 0,
            'formula_str': 'A -> (B -> A)',
            'justification_type': 'Axiom',
            'ref_name': 'ax1',
            'substitution_json': {'A': 'A', 'B': 'B'}
        }
    ]
}

is_valid, error = verify_proof_local(thm_def, db)
print("Dimostrazione valida localmente:", is_valid)
```

---

## 5. `solver.explorer`

Il modulo [`solver.explorer`](file:///c:/Users/franc/Programmazione/solver/solver/explorer.py) offre funzionalità di esplorazione automatizzata e scoperta di teoremi in modo autonomo.

### Funzioni Principali

#### `explore_consequences(db, basic_vars=['p'], max_depth=1, max_theorems=20, min_proof_steps=0)`

1. **Genera Formule Candidate**: Crea un insieme combinatorio di formule usando le variabili `basic_vars` fino alla profondità `max_depth` (tramite `generate_candidates`).
2. **Istanzia Assiomi e Lemmi**: Applica le formule candidate agli assiomi e lemmi presenti nel DB.
3. **Saturazione Modus Ponens**: Esegue un ciclo BFS per derivare tutte le conseguenze logiche possibili.
4. **Filtro e Salvataggio**: Ordina le formule derivate per complessità strutturale, ricostruisce le relative dimostrazioni ed esegue `verify_and_save` con Lean 4 per ciascun nuovo teorema trovato.

#### `generate_candidates(basic_vars, max_depth)`
Genera ricorsivamente tutte le formule combinatorie formabili a partire da una lista di variabili base (es. `['p', 'q']`).

#### Esempio di utilizzo:

```python
from solver.database import TheoryDatabase
from solver.dependencies import load_first_order_axioms
from solver.explorer import explore_consequences

db = TheoryDatabase("explore_demo.db")
load_first_order_axioms(db)

# Esplora fino a 3 nuovi teoremi
nuovi_trovati = explore_consequences(db, basic_vars=['p'], max_depth=1, max_theorems=3)
print(f"Teoremi scoperti e verificati: {nuovi_trovati}")
```

---

## 6. `solver.lean_exporter`

Il modulo [`solver.lean_exporter`](file:///c:/Users/franc/Programmazione/solver/solver/lean_exporter.py) converte la sintassi interna dell'AST Python nella sintassi formale di **Lean 4**.

### Funzioni Principali

#### `formula_to_lean(formula)`
Mappa ricorsivamente un nodo dell'AST `Formula` nella stringa corrispondente in sintassi Lean 4:
- `Implies(A, B)` $\rightarrow$ `(A → B)`
- `And(A, B)` $\rightarrow$ `(A ∧ B)`
- `Or(A, B)` $\rightarrow$ `(A ∨ B)`
- `Not(A)` $\rightarrow$ `¬(A)`
- `Forall("x", body)` $\rightarrow$ `(∀ x, body)`
- `Exists("x", body)` $\rightarrow$ `(∃ x, body)`
- `Equals(a, b)` $\rightarrow$ `(a = b)`
- `Pred("P", [a, b])` $\rightarrow$ `(P a b)`

#### `export_proof(theorem_name, db)`
Carica il teorema ed il grafo delle sue dipendenze dal database e genera un documento sorgente Lean 4 completo e autosufficiente (comprensivo di definizioni di assiomi, lemmi preliminari e passi della dimostrazione tramite tattiche `have` ed `exact`).

#### Esempio di utilizzo:

```python
from solver.formula import parse_formula
from solver.lean_exporter import formula_to_lean

f = parse_formula("forall x, (P(x) & Q(x))")
print("Sintassi Lean 4:", formula_to_lean(f))
# Stampa: (∀ x, ((P x) ∧ (Q x)))
```

---

## 7. `solver.dependencies`

Il sottopacchetto [`solver.dependencies`](file:///c:/Users/franc/Programmazione/solver/solver/dependencies/__init__.py) fornisce librerie assiomatiche predefinite per la logica matematica.

### Moduli Inclusi

#### 1. `solver.dependencies.first_order_logic`
Contiene gli assiomi standard per la Logica del Primo Ordine (FOL):
- **Calcolo Proposizionale**: `fol_k`, `fol_s`, `fol_dn`.
- **Quantificatori**: `fol_ui` (Istanziazione universale), `fol_ug` (Generalizzazione universale), `fol_eg` (Generalizzazione esistenziale), `fol_ed` (Eliminazione esistenziale).
- **Uguaglianza (Leibniz)**: `eq_ref` (Riflessività), `eq_sym` (Simmetria), `eq_trans` (Transitività), `eq_subst` (Sostituzione/Congruenza).

Funzioni: `get_first_order_axioms()`, `load_first_order_axioms(db)`.

#### 2. `solver.dependencies.second_order_logic`
Contiene gli assiomi per la Logica del Secondo Ordine (SOL):
- **Quantificatori del Secondo Ordine**: `sol_ui`, `sol_ug`, `sol_eg`, `sol_ed`.
- **Strutturali**: `sol_comp` (Schema di Comprensione), `sol_choice` (Assioma della Scelta Relazionale).
- **Induzione**: `sol_induction` (Schema di Induzione Matematica di Peano al Secondo Ordine).

Funzioni: `get_second_order_axioms()`, `load_second_order_axioms(db)`.

#### 3. `solver.dependencies.logic`
Modulo unificato che aggrega sia FOL sia SOL.

Funzioni: `get_all_logic_axioms()`, `load_all_logic_axioms(db)`.

#### Esempio di utilizzo:

```python
from solver.database import TheoryDatabase
from solver.dependencies import load_all_logic_axioms, get_first_order_axioms

db = TheoryDatabase("fol_sol_demo.db")

# Carica tutti gli assiomi di FOL e SOL
load_all_logic_axioms(db)

axioms = db.get_all_axioms()
print(f"Caricati {len(axioms)} assiomi nel database.")
print("Assioma eq_subst:", axioms.get("eq_subst"))
```
