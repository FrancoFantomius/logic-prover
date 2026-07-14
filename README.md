# Solver logico di Hilbert

Solver logico sperimentale in Python per modellare, dimostrare, verificare e memorizzare teoremi di logica proposizionale in stile Hilbert. Il progetto include:

- un parser e un AST per formule proposizionali con variabili, negazione e implicazione;
- un database SQLite per assiomi, teoremi, passaggi di dimostrazione e dipendenze;
- un prover automatico con limiti configurabili;
- una verifica locale delle dimostrazioni;
- un esportatore Lean 4 per generare file di prova self-contained.

## Stato del progetto

Il repository è pensato come prototipo di ricerca. Alcuni database e file Lean già presenti sono esempi o artefatti di esplorazioni precedenti.

## Requisiti

- Python 3.11 o superiore
- SQLite, incluso nella libreria standard di Python
- Lean 4 opzionale, necessario solo per la validazione esterna dei file `.lean`

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
