# API Reference: `prover`

# Module `solver.prover.clausifier`

Clausification pipeline for translating First-Order Logic formulas to Conjunctive Normal Form (CNF).

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class Literal`

#### Methods

##### `def negate(self) -> Literal`

Returns the complementary literal.

**Returns:** `Literal`

##### `def free_variables(self) -> Set[Variable]`

Returns all free variables in the literal atom.

**Returns:** `Set[Variable]`

##### `def substitute(self, subst: Dict[Variable, Term]) -> Literal`

Applies variable substitution to the literal atom.

**Returns:** `Literal`

##### `def to_string(self) -> str`

Formats literal for display.

**Returns:** `str`

### `class Clause`

#### Methods

##### `def is_empty(self) -> bool`

True if clause is the empty clause (contradiction ⊥).

**Returns:** `bool`

##### `def is_tautology(self) -> bool`

True if clause contains both L and ¬L.

**Returns:** `bool`

##### `def is_unit(self) -> bool`

True if clause consists of exactly one literal.

**Returns:** `bool`

##### `def free_variables(self) -> Set[Variable]`

Returns all free variables across all literals in the clause.

**Returns:** `Set[Variable]`

##### `def substitute(self, subst: Dict[Variable, Term]) -> Clause`

Applies variable substitution to all literals in the clause.

**Returns:** `Clause`

##### `def to_string(self) -> str`

Formats clause as disjunction string.

**Returns:** `str`

---

## Functions

### `def reset_skolem_counters() -> None`

Resets global Skolem counters (useful for predictable testing).

**Returns:** `None`

### `def eliminate_implications(formula: Formula) -> Formula`

Recursively eliminates Iff and Implies operators: - A ⟺ B  ==>  (A ⟹ B) ∧ (B ⟹ A) - A ⟹ B  ==>  ¬A ∨ B

**Returns:** `Formula`

### `def to_nnf(formula: Formula) -> Formula`

Converts formula to Negation Normal Form (NNF) by pushing negations inward: - ¬(¬A)          ==>  A - ¬(A ∧ B)       ==>  ¬A ∨ ¬B - ¬(A ∨ B)       ==>  ¬A ∧ ¬B - ¬(∀x, P(x))    ==>  ∃x, ¬P(x) - ¬(∃x, P(x))    ==>  ∀x, ¬P(x) Assumes implications have already been eliminated.

**Returns:** `Formula`

### `def standardize_variables(formula: Formula) -> Formula`

Renames bound variables so that each quantifier binds a unique variable index, preventing name clashes during Skolemization.

**Returns:** `Formula`

### `def skolemize(formula: Formula, signature: Optional[Signature]) -> Formula`

Eliminates existential quantifiers by introducing Skolem constants/functions. - ∃x, P(x) with active outer universal variables [y_1, ..., y_k]: Replaces x with FunctionApp(sk_fn, arity=k, args=(y_1, ..., y_k), return_sort=x.sort). - If k == 0, replaces x with Constant(sk_c, sort=x.sort). Updates signature with new Skolem function/constant symbols if signature is provided. Assumes formula is in NNF and variables are standardized.

**Returns:** `Formula`

### `def drop_universals(formula: Formula) -> Formula`

Strips all Forall quantifiers. In CNF, all remaining free variables are implicitly universally quantified.

**Returns:** `Formula`

### `def distribute_cnf(formula: Formula) -> Formula`

Recursively distributes disjunctions (Or) over conjunctions (And): - A ∨ (B ∧ C)  ==>  (A ∨ B) ∧ (A ∨ C) - (A ∧ B) ∨ C  ==>  (A ∨ C) ∧ (B ∨ C) Assumes formula has no quantifiers or implications.

**Returns:** `Formula`

### `def formula_to_clauses(formula: Formula) -> List[Clause]`

Converts a CNF-structured Formula (And/Or trees over atoms/nots) into a List of Clause instances. Filters out tautological clauses (L ∨ ¬L).

**Returns:** `List[Clause]`

### `def to_cnf(formula: Formula, signature: Optional[Signature]) -> List[Clause]`

Full CNF conversion pipeline: 1. Eliminate ⟺ and ⟹ 2. Convert to NNF 3. Standardize bound variables 4. Skolemize existential quantifiers 5. Drop universal quantifiers 6. Distribute ∨ over ∧ 7. Convert AST to List[Clause] and filter tautologies

**Returns:** `List[Clause]`

### `def negate_and_clausify(formula: Formula, signature: Optional[Signature]) -> List[Clause]`

Negates the given target formula (Not(formula)) and converts it to CNF for refutation search.

**Returns:** `List[Clause]`


---

# Module `solver.prover.engine`

Resolution theorem prover engine implementing given-clause resolution and superposition loops.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class ResolutionStep`

Represents a single step in a resolution proof search trace.

### `class TheoremProver`

Automated resolution theorem prover for First-Order Logic formulas.

#### Methods

##### `def __init__(self, signature: Signature, config: Optional[SolverConfig]) -> None`

Initializes TheoremProver with signature and configuration.

**Returns:** `None`

##### `def prove(self, target: Formula, premises: Optional[List[Formula]], max_steps: Optional[int], timeout_sec: Optional[float]) -> ProofDAG`

Attempts to prove target from premises using resolution refutation search. 1. Clausifies premises and negated target into CNF. 2. Executes Otter given-clause loop with forward subsumption. 3. On empty clause derivation, extracts resolution trace. 4. Reconstructs natural deduction ProofDAG. Raises ProofTimeoutError or ProofSearchExhaustedError if proof is not found within limits.

**Returns:** `ProofDAG`


---

# Module `solver.prover.proof`

Proof Directed Acyclic Graph (DAG) representation and validation data structures.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class ProofStep`

Represents a single deduction step in a proof DAG.

#### Methods

##### `def to_dict(self) -> Dict[str, Any]`

Serializes ProofStep to a dictionary.

**Returns:** `Dict[str, Any]`

##### `def from_dict(cls, data: Dict[str, Any]) -> ProofStep`

Deserializes ProofStep from a dictionary.

**Returns:** `ProofStep`

### `class ProofDAG`

Proof Directed Acyclic Graph structure containing deduction steps.

#### Methods

##### `def __init__(self, steps: Dict[str, ProofStep], root_id: str, axiom_ids: Optional[Set[str]]) -> None`

Initializes a ProofDAG instance.

**Returns:** `None`

##### `def conclusion(self) -> Formula`

**Returns:** `Formula`

##### `def premises(self) -> List[Formula]`

**Returns:** `List[Formula]`

##### `def add_step(self, step: ProofStep) -> None`

Adds a step to the DAG.

**Returns:** `None`

##### `def get_step(self, step_id: str) -> ProofStep`

Retrieves a step by ID.

**Returns:** `ProofStep`

##### `def topological_order(self) -> List[ProofStep]`

Returns proof steps in topological dependency order (axioms first, root last).

**Returns:** `List[ProofStep]`

##### `def is_valid(self, signature: Optional[Signature]) -> bool`

Verifies step-by-step logical validity of the DAG: 1. Checks root_id exists. 2. Checks DAG topology (no cycles). 3. Verifies every premise_id references an existing step. 4. Validates formula well-formedness if signature is provided. 5. Checks rule-specific conclusion derivation logic for non-axiom steps.

**Returns:** `bool`

##### `def to_dict(self) -> Dict[str, Any]`

Serializes proof DAG to dictionary for JSON/SQLite storage.

**Returns:** `Dict[str, Any]`

##### `def from_dict(cls, data: Dict[str, Any]) -> ProofDAG`

Deserializes proof DAG from dictionary.

**Returns:** `ProofDAG`


---

# Module `solver.prover.reconstruction`

Natural deduction proof reconstruction from resolution trace logs.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def reconstruct_proof(resolution_trace: List[ResolutionStep], original_target: Formula, premises: Optional[List[Formula]]) -> ProofDAG`

Converts a resolution refutation trace (proving ⊥ from premises ∧ ¬target) into a valid Natural Deduction ProofDAG for original_target.

Pipeline:
1. Map initial 'axiom' steps to ND premises.
2. Map initial 'negated_goal' step to assumption ¬original_target.
3. Convert resolution steps into ND inferences (Modus Ponens, Or Elimination, ResolutionTraceStep).
4. Derive contradiction ⊥ at empty clause root step.
5. Apply Double Negation Elimination / Proof by Contradiction to yield original_target as root.

**Returns:** `ProofDAG`

### `def simplify_proof(proof: ProofDAG) -> ProofDAG`

Optimizes ProofDAG by: 1. Pruning dead/unreachable steps not leading to root_id. 2. Collapsing identity and redundant single-premise steps.

**Returns:** `ProofDAG`


---

# Module `solver.prover.rules`

Inference rules for resolution, factoring, paramodulation, and SOL instantiation.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class InferenceRule`

### `class SOLInstantiateRule(InferenceRule)`

Inference rule that attempts to instantiate SOL quantified axioms (e.g. Peano Induction) against target goal clauses or formulas using higher-order pattern matching. Generates ground FOL clauses for the CNF resolution solver.

#### Methods

##### `def __init__(self) -> None`

**Returns:** `None`

##### `def match_and_instantiate(self, sol_axiom: Formula, target_goal: Formula, signature: Any) -> List[Clause]`

Matches second-order logic templates against target goals and instantiates clauses.

**Returns:** `List[Clause]`

---

## Functions

### `def standardize_clause_variables(c1: Clause, c2: Clause) -> Tuple[Clause, Clause, Dict[Variable, Variable]]`

Renames free variables in c2 so their variable IDs do not overlap with c1. Returns (c1, renamed_c2, variable_renaming_map).

**Returns:** `Tuple[Clause, Clause, Dict[Variable, Variable]]`

### `def resolve_clauses(c1: Clause, c2: Clause) -> List[Tuple[Clause, Dict[Variable, Term], Tuple[Literal, Literal]]]`

Binary Resolution Rule: Given c1 containing L1 and c2 containing L2 where L1.positive != L2.positive: Standardizes variables apart, unifies L1.atom and L2.atom with MGU σ. Returns list of tuples: (resolvent_clause, MGU_substitution, (L1, L2)).

**Returns:** `List[Tuple[Clause, Dict[Variable, Term], Tuple[Literal, Literal]]]`

### `def factor_clause(c: Clause) -> List[Tuple[Clause, Dict[Variable, Term]]]`

Factoring Rule: Given c containing L1 and L2 with same polarity: Unifies L1.atom and L2.atom with MGU σ. Returns list of tuples: (factored_clause, MGU_substitution).

**Returns:** `List[Tuple[Clause, Dict[Variable, Term]]]`

### `def extract_subterms(term: Term) -> List[Term]`

Recursively collects all subterms of a term.

**Returns:** `List[Term]`

### `def extract_atom_subterms(atom: Union[PredicateApp, Equality]) -> List[Term]`

Collects all term subterms from a predicate application or equality atom.

**Returns:** `List[Term]`

### `def replace_subterm(term: Term, target: Term, replacement: Term) -> List[Term]`

Replaces occurrences of target subterm with replacement in term.

**Returns:** `List[Term]`

### `def replace_atom_subterm(atom: Union[PredicateApp, Equality], target: Term, replacement: Term) -> List[Union[PredicateApp, Equality]]`

Replaces occurrences of target subterm with replacement in atom.

**Returns:** `List[Union[PredicateApp, Equality]]`

### `def paramodulate(c1: Clause, c2: Clause) -> List[Tuple[Clause, Dict[Variable, Term]]]`

Paramodulation Rule (Equality Rewriting): Given c1 containing positive equality literal (t1 = t2) [or (t2 = t1)], and c2 containing literal L[s] with subterm s unifiable with t1 via MGU σ: Derives paramodulant σ((c1 \ {t1=t2}) ∪ (c2 with s replaced by t2)).

**Returns:** `List[Tuple[Clause, Dict[Variable, Term]]]`

### `def get_resolution_rules() -> List[InferenceRule]`

Returns the set of core CNF resolution rules.

**Returns:** `List[InferenceRule]`

### `def get_reconstruction_rules() -> List[InferenceRule]`

Returns standard Natural Deduction inference rules used in ProofDAG.

**Returns:** `List[InferenceRule]`

### `def apply_rule(rule: InferenceRule, premises: List[Any], context: Optional[Dict[str, Any]]) -> List[Any]`

Applies an inference rule to premises with optional context parameters.

**Returns:** `List[Any]`


---
