# Solver logico di Hilbert

Solver logico sperimentale in Python per modellare, dimostrare, verificare e memorizzare teoremi di logica proposizionale in stile Hilbert. Il progetto include:

- un parser e un AST per formule proposizionali con variabili, negazione e implicazione;
- un database SQLite per assiomi, teoremi, passaggi di dimostrazione e dipendenze;
- un prover automatico con limiti configurabili;
- una verifica locale delle dimostrazioni;
- un esportatore Lean 4 per generare file di prova self-contained.

## Stato del progetto

Il repository è pensato come prototipo didattico/di ricerca. Alcuni database e file Lean già presenti sono esempi o artefatti di esplorazioni precedenti.

## Requisiti

- Python 3.11 o superiore
- SQLite, incluso nella libreria standard di Python
- Lean 4 opzionale, necessario solo per la validazione esterna dei file `.lean`

Non sono richieste dipendenze Python di terze parti per eseguire i test attuali.

## Installazione

Clona il repository ed entra nella cartella di progetto:

```bash
git clone <url-del-repository>
cd solver
```

Crea e attiva un ambiente virtuale:

```bash
python -m venv .venv
source .venv/bin/activate
```

Il progetto usa solo librerie standard; l'installazione in modalità editable è opzionale:

```bash
python -m pip install -e .
```

## Uso rapido

Esegui l'esploratore dimostrativo di esempio:

```bash
python main.py
```

Lo script inizializza `theory.db`, registra gli assiomi standard della logica proposizionale e prova a generare nuovi teoremi verificati.

## Test

Esegui la suite con `unittest`:

```bash
python -m unittest discover -v
```

## Struttura del repository

| Percorso | Descrizione |
| --- | --- |
| `formula.py` | AST, parser, sostituzione e matching di formule proposizionali. |
| `database.py` | Persistenza SQLite per assiomi, teoremi, ipotesi, passi e dipendenze. |
| `prover.py` | Ricerca e ricostruzione di dimostrazioni Hilbert. |
| `verifier.py` | Verifica locale e coordinamento della verifica con Lean. |
| `lean_exporter.py` | Generazione di codice Lean 4 self-contained. |
| `explorer.py` | Generazione ed esplorazione automatica di candidati teoremi. |
| `main.py` | Esempio eseguibile dell'esplorazione logica. |
| `test_solver.py` | Test unitari principali. |
| `implementation_plan.md` | Note architetturali e piano di implementazione. |

## Note sui file generati

Durante l'uso possono essere generati database SQLite (`*.db`), file Lean (`*.lean`) e cache Python (`__pycache__/`). La `.gitignore` evita di aggiungere nuovi artefatti generati, mentre i file già tracciati rimangono nella cronologia finché non vengono rimossi esplicitamente.

## Licenza

Distribuito con licenza MIT. Vedi `LICENSE` per i dettagli.
