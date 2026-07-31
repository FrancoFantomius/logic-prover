# Nuova struttura del Progetto!
- lean_exporter: traduce le formule in LEAN
- graph_exporter: esporta grafi in html
- explorer: crea le nuove formule da dimostrare
- prover: trova il modo di dimostrare le formule
- deducer: capisce le relazioni tra ipotesi e conseguenze, È RIDONDANTE?

ci devono essere dei file di utilità, database/parser (ex formula).

documentazione: le funzioni devono essere documentate con commenti già nei file, la documentazione deve essere ricavata automaticamente da questo


1. riformattare il linguaggio. Si deve pensare di avere sempre infinite variabili `v_n` e gli assiomi ne prendono solo alcune di queste. Idem per funzioni e costanti, solo che in questo caso non devono essere utilizzate per la creazione di nuove formule.
2. i concetti di base devono essere: logica del primo e secondo ordine, insiemi, funzioni, numeri e operazioni di base.
3. favorire la ricerca di formule "diverse": invece che avere concatenazioni infinite della stessa formula, l'explorer deve creare una lista di formule e preferire quelle che usano più assiomi/variabili/funzioni. Bisogna anche implementare un meccanismo per cui le formule scartate non vengano riproposte.