# API Reference: `constructive`

# Module `logic_prover.constructive.common`

Shared constants, predicates, and normalization utilities for constructive logic.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def normalize_formula(formula: Formula) -> Formula`

Recursively normalizes connectives for constructive logic calculus.

Expands logical equivalence A <=> B into (A => B) & (B => A) and
negation ~A into A => _bot (falsum).

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The raw formula to normalize. |

**Returns:** `Formula` — The normalized formula using only atomic nodes, And, Or, and Implies.


---

# Module `logic_prover.constructive.kripke`

Kripke frames, possible worlds, and semantic models for Intuitionistic Logic.

This module provides Kripke semantics structures for intuitionistic propositional
logic (Fitting 1969; Chagrov & Zakharyaschev 1997). In intuitionistic Kripke semantics,
a model M = (W, <=, V) consists of a non-empty set of worlds W, a reflexive-transitive
preorder <=, and a monotone valuation V where u <= v implies V(u) <= V(v).

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class World`

Represents a possible world node in a Kripke frame.

### `class KripkeModel`

A finite Kripke Model (W, <=, V) for Intuitionistic Propositional Logic.

In intuitionistic Kripke semantics:
- W is a non-empty set of possible worlds.
- <= is a preorder (reflexive, transitive accessibility relation).
- V maps each world w in W to a set of true atomic propositions such that
  if w <= w' then V(w) <= V(w') (monotonicity / persistence / heredity).

#### Methods

##### `def __init__(self, worlds: Optional[List[World]], relations: Optional[Dict[World, Set[World]]], valuations: Optional[Dict[World, Set[Formula]]]) -> None`

Initializes a Kripke model with worlds, relations, and valuations.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `worlds` | `Optional[List[World]], default=None` | Initial list of worlds. |
| `relations` | `Optional[Dict[World, Set[World]]], default=None` | Initial accessibility edges. |
| `valuations` | `Optional[Dict[World, Set[Formula]]], default=None` | Initial truth assignments. |

**Returns:** `None`

##### `def add_world(self, world: World) -> None`

Adds a world to the model, ensuring reflexivity in the accessibility relation.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `world` | `World` | The world to add. |

**Returns:** `None`

##### `def add_relation(self, source: World, target: World) -> None`

Adds an accessibility edge source <= target and maintains transitive closure.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `source` | `World` | The starting world. |
| `target` | `World` | The accessible world. |

**Returns:** `None`

##### `def add_valuation(self, world: World, formula: Formula) -> None`

Assigns truth to an atomic proposition at a world, propagating along accessible worlds.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `world` | `World` | World where formula is true. |
| `formula` | `Formula` | Atomic formula to set true. |

**Returns:** `None`

##### `def is_accessible(self, source: World, target: World) -> bool`

Tests whether target is reachable from source (source <= target).

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `source` | `World` | Source world. |
| `target` | `World` | Target world. |

**Returns:** `bool` — True if source <= target, False otherwise.

##### `def accessible_worlds(self, world: World) -> Set[World]`

Returns the set of all worlds accessible from the given world.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `world` | `World` | Starting world. |

**Returns:** `Set[World]` — Set of accessible worlds {w' | world <= w'}.

##### `def evaluate(self, formula: Formula, world: World) -> bool`

Evaluates whether an intuitionistic formula is forced at a world: (M, world |= formula).

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The formula AST to evaluate. |
| `world` | `World` | The evaluation world in W. |

**Returns:** `bool` — True if world forces formula, False otherwise.

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the Kripke model structure to a dictionary.

**Returns:** `Dict[str, Any]` — Dictionary structure with worlds, relations, and valuations.

##### `def to_string(self) -> str`

Formats the Kripke model as a readable multi-line description.

**Returns:** `str` — Description of worlds, accessibility relation, and atomic valuations.


---

# Module `logic_prover.constructive.ljt`

Roy Dyckhoff's Contraction-Free Sequent Calculus (LJT / G4ip) for Intuitionistic Logic.

This module implements the terminating, contraction-free sequent calculus LJT
developed by Roy Dyckhoff (1992) for propositional intuitionistic logic (IPC).

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class Sequent`

Represents a single-conclusion intuitionistic sequent Gamma => G.

#### Methods

##### `def to_string(self, notation: str) -> str`

Formats the sequent as a human-readable string.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `notation` | `str, default='infix'` | String notation ('infix' or 'latex'). |

**Returns:** `str` — String representation of the sequent.

### `class LJTProofNode`

Represents a node in an LJT derivation tree.

#### Methods

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the proof node and its subtree to a dictionary.

**Returns:** `Dict[str, Any]` — Dictionary structure of the proof tree.

### `class LJTProofTree`

Container and visualization manager for an LJT deduction tree.

#### Methods

##### `def __init__(self, root: LJTProofNode) -> None`

Initializes the proof tree.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `root` | `LJTProofNode` | The root node of the derivation. |

**Returns:** `None`

##### `def depth(self) -> int`

Computes the height of the proof derivation tree.

**Returns:** `int` — The maximum depth of the derivation tree.

##### `def size(self) -> int`

Computes the total number of deduction steps in the proof tree.

**Returns:** `int` — Total node count in the derivation.

##### `def is_valid(self) -> bool`

Validates that all leaves in the derivation tree are closed axioms.

**Returns:** `bool` — True if every leaf is an established axiom, False otherwise.

##### `def to_ascii(self) -> str`

Generates an ASCII visualization of the sequent calculus proof tree.

**Returns:** `str` — Multi-line string showing the formatted deduction tree.

##### `def to_latex(self) -> str`

Exports the proof tree into LaTeX bussproofs format.

**Returns:** `str` — LaTeX code snippet utilizing the bussproofs package.

##### `def to_dict(self) -> Dict[str, Any]`

Converts the proof tree to a structured dictionary.

**Returns:** `Dict[str, Any]` — Structured tree data.

### `class LJTProver`

Automated Theorem Prover for Intuitionistic Propositional Logic using LJT / G4ip calculus.

#### Methods

##### `def __init__(self) -> None`

Initializes the LJT theorem prover instance.

**Returns:** `None`

##### `def prove(self, target: Formula, premises: Optional[List[Formula]]) -> Optional[LJTProofTree]`

Attempts to construct an intuitionistic LJT proof tree for target from premises.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | The goal formula to be proved. |
| `premises` | `Optional[List[Formula]], default=None` | Optional list of hypothesis formulas. |

**Returns:** `Optional[LJTProofTree]` — Complete derivation tree if provable, or None if unprovable.

##### `def is_provable(self, target: Formula, premises: Optional[List[Formula]]) -> bool`

Checks whether a formula is intuitionistically valid in LJT calculus.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | The goal formula to test. |
| `premises` | `Optional[List[Formula]], default=None` | Optional list of hypotheses. |

**Returns:** `bool` — True if provable intuitionistically, False otherwise.

---

## Functions

### `def prove_ljt(formula: Formula, premises: Optional[List[Formula]]) -> Optional[LJTProofTree]`

Top-level convenience function to prove a formula using the LJT calculus.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The formula to prove. |
| `premises` | `Optional[List[Formula]], default=None` | Optional list of hypothesis premises. |

**Returns:** `Optional[LJTProofTree]` — The derivation proof tree if valid, None if not provable.


---

# Module `logic_prover.constructive.matrix`

Matrix decomposition, position trees, and connections for Wallen's method.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class PositionType(str, Enum)`

Wallen primary types for positions in intuitionistic logic.

Members:
    ALPHA: Non-branching propositional conjunction/disjunction position.
    BETA: Branching propositional position.
    PHI: Intuitionistic dynamic universal/implication premise position introducing prefix variables.
    PSI: Intuitionistic static existential/implication goal position introducing prefix constants.
    ATOM: Atomic proposition leaf position.

### `class Position`

A node in the polar decomposition tree with prefix annotations.

#### Methods

##### `def is_leaf(self) -> bool`

Checks if this position is a leaf (atomic proposition).

**Returns:** `bool` — True if ATOM type, False otherwise.

##### `def to_string(self) -> str`

Returns a string representation of the signed position.

**Returns:** `str` — Formatted position label.

### `class FormulaTree`

Constructs and manages the polar decomposition tree and paths for Wallen's method.

#### Methods

##### `def __init__(self, target: Formula, premises: Optional[List[Formula]], multiplicity: int) -> None`

Initializes and decomposes the formula tree.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | Goal formula AST to decompose. |
| `premises` | `Optional[List[Formula]], default=None` | Optional hypothesis formulas. |
| `multiplicity` | `int, default=1` | Multiplicity bound for phi-node duplications. |

**Returns:** `None`

##### `def get_paths(self) -> List[List[Position]]`

Extracts all vertical paths (sets of atomic leaves) through the matrix.

**Returns:** `List[List[Position]]` — List of paths, where each path is a list of leaf positions.

### `class Connection`

A complementary pair of atomic leaf positions (u^0, v^1) with identical predicate.

#### Methods

##### `def to_string(self) -> str`

Formats the connection as a string showing leaves and prefixes.

**Returns:** `str` — Human-readable connection representation.


---

# Module `logic_prover.constructive.prefix`

Prefix data structures, string unification, and admissibility checks for Wallen's method.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class PrefixSymbol`

Base class for world prefix symbols in Kripke frames.

### `class PrefixConstant(PrefixSymbol)`

Static world parameter constant generated by intuitionistic psi-nodes.

### `class PrefixVariable(PrefixSymbol)`

Dynamic world variable generated by intuitionistic phi-nodes.

### `class Prefix`

An immutable sequence of world prefix symbols representing a path in a Kripke frame.

#### Methods

##### `def append(self, symbol: PrefixSymbol) -> Prefix`

Appends a prefix symbol and returns a new Prefix.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `symbol` | `PrefixSymbol` | The symbol to append. |

**Returns:** `Prefix` — Extended prefix.

##### `def variables(self) -> Set[PrefixVariable]`

Returns the set of prefix variables occurring in the prefix.

**Returns:** `Set[PrefixVariable]` — All prefix variables in this prefix.

##### `def constants(self) -> Set[PrefixConstant]`

Returns the set of prefix constants occurring in the prefix.

**Returns:** `Set[PrefixConstant]` — All prefix constants in this prefix.

##### `def to_string(self) -> str`

Formats the prefix as a dot-separated string.

**Returns:** `str` — Dot-separated string of prefix symbols.

### `class PrefixSubstitution`

Mapping from prefix variables to sequences of prefix symbols.

#### Methods

##### `def copy(self) -> PrefixSubstitution`

Creates a deep copy of the substitution.

**Returns:** `PrefixSubstitution` — Cloned substitution.

##### `def bind(self, var: PrefixVariable, term: Tuple[PrefixSymbol, ...]) -> PrefixSubstitution`

Binds a variable to a term and applies substitution transitively.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `var` | `PrefixVariable` | Variable to bind. |
| `term` | `Tuple[PrefixSymbol, ...]` | Replacement tuple of symbols. |

**Returns:** `PrefixSubstitution` — New extended substitution.

##### `def get(self, var: PrefixVariable) -> Optional[Tuple[PrefixSymbol, ...]]`

Retrieves the bound term for a prefix variable.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `var` | `PrefixVariable` | Variable to look up. |

**Returns:** `Optional[Tuple[PrefixSymbol, ...]]` — Bound term or None.

##### `def apply(self, prefix: Prefix) -> Prefix`

Applies the substitution fully to a prefix.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `prefix` | `Prefix` | Prefix to instantiate. |

**Returns:** `Prefix` — Instantiated prefix.

##### `def to_dict(self) -> Dict[str, str]`

Serializes the substitution to a string-keyed dictionary.

**Returns:** `Dict[str, str]` — Serialized variable-to-string mappings.

---

## Functions

### `def unify_prefixes(p1: Prefix, p2: Prefix, subst: Optional[PrefixSubstitution]) -> List[PrefixSubstitution]`

Generates all most general intuitionistic T-string prefix substitutions solving p1 = p2.

Implements string equation solving for S4 / intuitionistic world prefix words
(Otten & Kreitz 1996; Wallen 1990).

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `p1` | `Prefix` | First prefix word. |
| `p2` | `Prefix` | Second prefix word. |
| `subst` | `Optional[PrefixSubstitution], default=None` | Initial prefix substitution. |

**Returns:** `List[PrefixSubstitution]` — List of viable unifying substitutions.

### `def is_admissible(tree: FormulaTree, subst: PrefixSubstitution) -> bool`

Verifies that the reduction ordering < = (<_0 U <_sigma)+ is strictly acyclic.

In Wallen's matrix proof method, an intuitionistic substitution sigma is admissible
if the combination of formula tree ordering <_0 and induced substitution ordering
<_sigma contains no directed cycles.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `tree` | `FormulaTree` | The formula tree defining tree ordering <_0. |
| `subst` | `PrefixSubstitution` | The candidate prefix substitution. |

**Returns:** `bool` — True if the combined reduction ordering is acyclic, False otherwise.


---

# Module `logic_prover.constructive.resolution`

Resolution theorem proving with prefixing and relational translation for Intuitionistic Logic.

This module provides two resolution theorem proving methods for Intuitionistic
Propositional Logic (IPC):
1. Prefixed Resolution: Direct clausal resolution over signed prefixed literals
   (p : A^pol) using intuitionistic T-string prefix unification and reduction ordering
   admissibility checks (Wallen 1990; Fitting 1990; Mints 1990; Otten & Kreitz 1996).
2. Relational Translation Resolution: Standard relational S4 translation embedding IPC
   into classical First-Order Logic (FOL) with reflexivity, transitivity, and monotonicity
   frame axioms, delegating refutation proof search to the classical First-Order
   resolution engine (TheoremProver).

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class PrefixedLiteral`

A signed atomic proposition annotated with a Kripke world prefix.

#### Methods

##### `def negate(self) -> PrefixedLiteral`

Returns the complementary prefixed literal with toggled polarity.

**Returns:** `PrefixedLiteral` — Complementary literal with inverted polarity.

##### `def substitute(self, subst: PrefixSubstitution) -> PrefixedLiteral`

Applies a prefix substitution to the literal's prefix.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `subst` | `PrefixSubstitution` | The prefix substitution to apply. |

**Returns:** `PrefixedLiteral` — New literal with instantiated prefix.

##### `def variables(self) -> Set[PrefixVariable]`

Returns the set of prefix variables occurring in this literal.

**Returns:** `Set[PrefixVariable]` — Set of prefix variables in the literal.

##### `def constants(self) -> Set[PrefixConstant]`

Returns the set of prefix constants occurring in this literal.

**Returns:** `Set[PrefixConstant]` — Set of prefix constants in the literal.

##### `def to_string(self) -> str`

Returns a string representation of the signed prefixed literal.

**Returns:** `str` — Formatted literal string (e.g. 'P^1:c0.V1').

### `class PrefixedClause`

An immutable disjunction of prefixed signed literals.

#### Methods

##### `def is_empty(self) -> bool`

Checks if this clause is the empty contradiction clause.

**Returns:** `bool` — True if clause has no literals, False otherwise.

##### `def substitute(self, subst: PrefixSubstitution) -> PrefixedClause`

Applies a prefix substitution to all literals in the clause.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `subst` | `PrefixSubstitution` | The prefix substitution to apply. |

**Returns:** `PrefixedClause` — Instantiated clause.

##### `def variables(self) -> Set[PrefixVariable]`

Returns the set of prefix variables occurring across all literals.

**Returns:** `Set[PrefixVariable]` — Set of all prefix variables in the clause.

##### `def constants(self) -> Set[PrefixConstant]`

Returns the set of prefix constants occurring across all literals.

**Returns:** `Set[PrefixConstant]` — Set of all prefix constants in the clause.

##### `def to_string(self) -> str`

Formats the clause as a sorted bracketed string of literals.

**Returns:** `str` — String representation of the clause (e.g. '[ P^1:c0, Q^0:c0.c1 ]' or '[]').

### `class PrefixedResolutionStep`

Represents a single step in a prefixed resolution derivation trace.

#### Methods

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the resolution step to a dictionary.

**Returns:** `Dict[str, Any]` — Dictionary structure with step metadata and clause.

### `class PrefixedResolutionProofResult`

Container for the results of a prefixed resolution proof search.

#### Methods

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the prefixed resolution proof result to a JSON-compatible dictionary.

**Returns:** `Dict[str, Any]` — Dictionary containing validity, target, premises, steps, and substitution.

##### `def to_string(self) -> str`

Formats the proof result as a readable multi-line derivation summary.

**Returns:** `str` — Multi-line string showing resolution derivation steps.

### `class PrefixedResolutionProver`

Resolution theorem prover operating directly on prefixed clauses for IPC.

#### Methods

##### `def __init__(self, max_multiplicity: int, max_steps: int) -> None`

Initializes the PrefixedResolutionProver with search bounds.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `max_multiplicity` | `int, default=3` | Maximum multiplicity limit. |
| `max_steps` | `int, default=1000` | Maximum search iteration limit. |

**Returns:** `None`

##### `def prove(self, target: Formula, premises: Optional[Sequence[Formula]]) -> Optional[PrefixedResolutionProofResult]`

Attempts to prove a formula in Intuitionistic Propositional Logic using Prefixed Resolution.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | Goal formula AST to prove. |
| `premises` | `Optional[Sequence[Formula]], default=None` | Optional hypothesis premises. |

**Returns:** `Optional[PrefixedResolutionProofResult]` — Proof result if proven valid, None otherwise.

### `class TranslationResolutionResult`

Container for the derivation results of Translation-based Resolution.

#### Methods

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the translation resolution result to a JSON dictionary.

**Returns:** `Dict[str, Any]` — Serialized result dictionary.

##### `def to_string(self) -> str`

Formats the translation proof result as a multi-line report.

**Returns:** `str` — Multi-line description of the translation proof.

### `class TranslationResolutionProver`

Resolution prover utilizing Relational S4 Translation to First-Order Logic.

#### Methods

##### `def __init__(self, max_steps: int, timeout_sec: float) -> None`

Initializes the TranslationResolutionProver with limits.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `max_steps` | `int, default=1000` | Maximum search steps. |
| `timeout_sec` | `float, default=10.0` | Search timeout in seconds. |

**Returns:** `None`

##### `def prove(self, target: Formula, premises: Optional[Sequence[Formula]]) -> Optional[TranslationResolutionResult]`

Attempts to prove an IPC formula by translating to FOL and running the First-Order resolution prover.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | The IPC formula AST to prove. |
| `premises` | `Optional[Sequence[Formula]], default=None` | Optional hypothesis premises. |

**Returns:** `Optional[TranslationResolutionResult]` — Proof result if proven valid, None if unprovable.

### `class ConstructiveResolutionProver`

Unified resolution theorem prover supporting both Prefixed and Translation methods for IPC.

#### Methods

##### `def __init__(self, method: str, max_multiplicity: int, max_steps: int, timeout_sec: float) -> None`

Initializes the unified constructive resolution prover.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `method` | `str, default='prefixed'` | Resolution method ('prefixed', 'translation', 'auto'). |
| `max_multiplicity` | `int, default=3` | Multiplicity limit for prefixed resolution. |
| `max_steps` | `int, default=1000` | Maximum resolution steps limit. |
| `timeout_sec` | `float, default=10.0` | Wall-clock timeout limit in seconds. |

**Returns:** `None`

##### `def prove(self, target: Formula, premises: Optional[Sequence[Formula]]) -> Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]`

Attempts to prove an IPC formula using the configured resolution strategy.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | Formula AST to prove. |
| `premises` | `Optional[Sequence[Formula]], default=None` | Optional hypothesis premises. |

**Returns:** `Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]` —  Proof result if valid, None otherwise.

---

## Functions

### `def clausify_prefixed(target: Formula, premises: Optional[Sequence[Formula]], multiplicity: int) -> Tuple[List[PrefixedClause], FormulaTree]`

Decomposes an intuitionistic formula and premises into a set of prefixed initial clauses.

Constructs a polar FormulaTree and extracts each matrix path as a prefixed clause
representing an elementary goal to refute.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | Goal formula AST. |
| `premises` | `Optional[Sequence[Formula]], default=None` | Optional hypothesis premises. |
| `multiplicity` | `int, default=1` | Multiplicity bound for phi-node duplications. |

**Returns:** `Tuple[List[PrefixedClause], FormulaTree]` — List of initial prefixed clauses and decomposition tree.

### `def resolve_prefixed_clauses(c1: PrefixedClause, c2: PrefixedClause, subst: Optional[PrefixSubstitution], tree: Optional[FormulaTree]) -> List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]`

Computes all possible binary resolvents between two prefixed clauses under admissible prefix unifiers.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `c1` | `PrefixedClause` | First parent clause. |
| `c2` | `PrefixedClause` | Second parent clause. |
| `subst` | `Optional[PrefixSubstitution], default=None` | Current accumulated prefix substitution. |
| `tree` | `Optional[FormulaTree], default=None` | Formula tree used for reduction ordering admissibility. |

**Returns:** `List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]` —  List of (resolvent_clause, new_substitution, lit1, lit2) tuples.

### `def factor_prefixed_clause(clause: PrefixedClause, subst: Optional[PrefixSubstitution], tree: Optional[FormulaTree]) -> List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]`

Computes all possible factors of a prefixed clause by unifying identical literals.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `clause` | `PrefixedClause` | The clause to factor. |
| `subst` | `Optional[PrefixSubstitution], default=None` | Accumulated prefix substitution. |
| `tree` | `Optional[FormulaTree], default=None` | Formula tree for admissibility validation. |

**Returns:** `List[Tuple[PrefixedClause, PrefixSubstitution, PrefixedLiteral, PrefixedLiteral]]` —  List of (factored_clause, new_substitution, lit1, lit2) tuples.

### `def translate_ipc_to_fol(formula: Formula, world_term: Optional[Term], var_counter: Optional[List[int]]) -> Formula`

Translates an Intuitionistic Propositional Logic formula into a First-Order Logic formula.

Implements the standard relational translation (embedding IPC into modal S4 and FOL):
- tau(P, w) = P(w)
- tau(_bot, w) = _bot
- tau(_top, w) = _top
- tau(~A, w) = forall w'. (R(w, w') => ~tau(A, w'))
- tau(A & B, w) = tau(A, w) & tau(B, w)
- tau(A | B, w) = tau(A, w) | tau(B, w)
- tau(A => B, w) = forall w'. ((R(w, w') & tau(A, w')) => tau(B, w'))

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The IPC formula AST to translate. |
| `world_term` | `Optional[Term], default=None` | World parameter term (defaults to Constant('w0')). |
| `var_counter` | `Optional[List[int]], default=None` | Mutable integer counter for unique world variables. |

**Returns:** `Formula` — The translated First-Order Logic formula AST.

### `def get_frame_axioms(atomic_predicates: Sequence[str]) -> List[Formula]`

Generates the Kripke frame reflexivity, transitivity, and monotonicity axioms in FOL.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `atomic_predicates` | `Sequence[str]` | List of proposition names occurring in the target. |

**Returns:** `List[Formula]` — Frame and monotonicity axioms in FOL.

### `def prove_prefixed_resolution(formula: Formula, premises: Optional[List[Formula]], max_multiplicity: int, max_steps: int) -> Optional[PrefixedResolutionProofResult]`

Proves an intuitionistic propositional formula using Prefixed Resolution.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | Goal formula to prove. |
| `premises` | `Optional[List[Formula]], default=None` | Optional hypothesis premises. |
| `max_multiplicity` | `int, default=3` | Multiplicity bound for phi-node duplications. |
| `max_steps` | `int, default=1000` | Maximum search iterations. |

**Returns:** `Optional[PrefixedResolutionProofResult]` — Derivation proof result if valid, None if unprovable.

### `def prove_translation_resolution(formula: Formula, premises: Optional[List[Formula]], max_steps: int, timeout_sec: float) -> Optional[TranslationResolutionResult]`

Proves an intuitionistic propositional formula using Relational S4 Translation Resolution.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | Goal formula to prove. |
| `premises` | `Optional[List[Formula]], default=None` | Optional hypothesis premises. |
| `max_steps` | `int, default=1000` | Maximum resolution steps in the FOL prover. |
| `timeout_sec` | `float, default=10.0` | Wall-clock timeout in seconds. |

**Returns:** `Optional[TranslationResolutionResult]` — Proof result if valid, None if unprovable.

### `def prove_resolution(formula: Formula, premises: Optional[List[Formula]], method: str, max_multiplicity: int, max_steps: int, timeout_sec: float) -> Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]`

Proves an intuitionistic propositional formula using resolution (prefixed or translation).

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | Formula AST to prove. |
| `premises` | `Optional[List[Formula]], default=None` | Optional hypothesis premises. |
| `method` | `str, default='prefixed'` | Resolution method ('prefixed', 'translation', 'auto'). |
| `max_multiplicity` | `int, default=3` | Maximum multiplicity limit for prefixed resolution. |
| `max_steps` | `int, default=1000` | Maximum search iterations. |
| `timeout_sec` | `float, default=10.0` | Wall-clock timeout in seconds. |

**Returns:** `Optional[Union[PrefixedResolutionProofResult, TranslationResolutionResult]]` —  Proof result if valid, None if unprovable.


---

# Module `logic_prover.constructive.tableau`

Semantic Tableaux with Kripke Semantics for Intuitionistic Propositional Logic (IPC).

This module implements a labelled/prefixed semantic tableau calculus for intuitionistic
propositional logic (Fitting 1969, 1983; Goré 1999). Proof search decomposes signed
formulas across explicit Kripke worlds. When a formula is intuitionistically valid,
all tableau branches close. When a formula is unprovable (e.g. classical tautologies
such as excluded middle or double negation elimination), an open saturated branch
is used to construct an explicit finite Kripke countermodel (W, <=, V) falsifying
the target.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class Sign(str, Enum)`

Truth sign in labelled semantic tableaux.

T denotes assertion of truth / forcing at a world (w |= A).
F denotes assertion of falsity / non-forcing at a world (w |/= A).

### `class SignedFormula`

A formula paired with a truth sign and world location in a Kripke frame.

#### Methods

##### `def to_string(self, notation: str) -> str`

Formats the signed formula as a human-readable string.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `notation` | `str, default='infix'` | String formatting notation ('infix' or 'latex'). |

**Returns:** `str` — Formatted signed formula string.

### `class TableauNode`

A node in a semantic tableau derivation tree.

#### Methods

##### `def is_leaf(self) -> bool`

Checks whether this node is a leaf in the tableau tree.

**Returns:** `bool` — True if the node has no children, False otherwise.

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the tableau node and its children into a dictionary.

**Returns:** `Dict[str, Any]` — Dictionary structure of the node.

##### `def to_string(self, prefix: str, is_last: bool) -> str`

Renders the node and its sub-branches in ASCII tree format.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `prefix` | `str, default=''` | Current indentation prefix. |
| `is_last` | `bool, default=True` | Whether this child is the last among its siblings. |

**Returns:** `str` — Multi-line ASCII tree.

### `class TableauProofTree`

Container and visualization manager for a semantic tableau derivation tree.

#### Methods

##### `def __init__(self, root: TableauNode) -> None`

Initializes the tableau proof tree.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `root` | `TableauNode` | The root node. |

**Returns:** `None`

##### `def is_closed(self) -> bool`

Determines if the entire tableau is closed (valid proof).

**Returns:** `bool` — True if root node is closed, False otherwise.

##### `def get_depth(self) -> int`

Computes the maximum depth of the tableau tree.

**Returns:** `int` — Height of the tree.

##### `def get_size(self) -> int`

Computes the total number of nodes in the tableau derivation.

**Returns:** `int` — Total node count.

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the tableau tree into a JSON-compatible dictionary.

**Returns:** `Dict[str, Any]` — Serialized dictionary.

##### `def to_string(self) -> str`

Renders the entire derivation tree as an ASCII diagram.

**Returns:** `str` — Multi-line ASCII tree.

##### `def to_latex(self) -> str`

Generates LaTeX forest / prooftrees markup for the derivation.

**Returns:** `str` — LaTeX formatted string.

### `class TableauProofResult`

Result of an intuitionistic semantic tableau proof search.

#### Methods

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the proof result to a JSON-compatible dictionary.

**Returns:** `Dict[str, Any]` — Dictionary structure of the result.

##### `def to_string(self) -> str`

Formats the proof result as a comprehensive multi-line report.

**Returns:** `str` — Human-readable proof summary.

### `class TableauProver`

Automated Theorem Prover and Countermodel Builder for Intuitionistic Logic.

Implements labelled semantic tableaux with explicit Kripke frame semantics.

#### Methods

##### `def __init__(self, max_depth: int, max_worlds: int) -> None`

Initializes the tableau prover with depth and world bounds.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `max_depth` | `int, default=100` | Maximum search depth. |
| `max_worlds` | `int, default=50` | Maximum number of generated worlds. |

**Returns:** `None`

##### `def prove(self, target: Formula, premises: Optional[List[Formula]]) -> TableauProofResult`

Attempts to prove an intuitionistic propositional formula or find a Kripke countermodel.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | The target formula to prove. |
| `premises` | `Optional[List[Formula]], default=None` | Optional list of hypothesis premises. |

**Returns:** `TableauProofResult` — Complete derivation result with validity status and tree.

##### `def is_valid(self, target: Formula, premises: Optional[List[Formula]]) -> bool`

Checks whether a formula is intuitionistically valid using semantic tableaux.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | Formula AST to test. |
| `premises` | `Optional[List[Formula]], default=None` | Optional hypothesis formulas. |

**Returns:** `bool` — True if intuitionistically provable, False otherwise.

##### `def countermodel(self, target: Formula, premises: Optional[List[Formula]]) -> Optional[KripkeModel]`

Extracts a Kripke countermodel falsifying the formula if it is not valid.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | Formula AST to check. |
| `premises` | `Optional[List[Formula]], default=None` | Optional hypothesis formulas. |

**Returns:** `Optional[KripkeModel]` — Falsifying Kripke countermodel if unprovable, None if valid.

---

## Functions

### `def prove_tableau(formula: Formula, premises: Optional[List[Formula]], max_depth: int, max_worlds: int) -> TableauProofResult`

Proves an intuitionistic formula or extracts a Kripke countermodel via semantic tableaux.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | Target formula AST to prove. |
| `premises` | `Optional[List[Formula]], default=None` | Optional list of hypothesis formulas. |
| `max_depth` | `int, default=100` | Maximum search depth bound. |
| `max_worlds` | `int, default=50` | Maximum number of possible worlds to construct. |

**Returns:** `TableauProofResult` — Complete derivation result container with tree and countermodel.


---

# Module `logic_prover.constructive.wallen`

Lincoln Wallen's Matrix and Connection Method for Intuitionistic Propositional Logic (IPC).

This module implements Wallen's prefix-based matrix characterization and connection
method for intuitionistic propositional logic (Wallen 1990; Otten & Kreitz 1996).
Formulas are decomposed into signed formula trees with Kripke world prefixes,
and theoremhood is established via path-spanning matings with admissible T-string
prefix unification.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class WallenProofResult`

Container for Wallen matrix proof derivation results.

#### Methods

##### `def to_dict(self) -> Dict[str, Any]`

Serializes the proof result to a JSON-compatible dictionary.

**Returns:** `Dict[str, Any]` — Dictionary structure of the proof.

##### `def to_string(self) -> str`

Formats the proof result as a multi-line report.

**Returns:** `str` — Multi-line proof summary.

### `class WallenProver`

Matrix / Connection Proof Searcher for Intuitionistic Propositional Logic.

#### Methods

##### `def __init__(self, max_multiplicity: int) -> None`

Initializes the Wallen prover with maximum multiplicity limit.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `max_multiplicity` | `int, default=3` | Maximum multiplicity bound for phi-node duplications. |

**Returns:** `None`

##### `def prove(self, target: Formula, premises: Optional[List[Formula]]) -> Optional[WallenProofResult]`

Attempts to prove a formula in Intuitionistic Propositional Logic using Wallen's method.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `target` | `Formula` | Formula AST to prove. |
| `premises` | `Optional[List[Formula]], default=None` | Optional list of hypothesis formulas. |

**Returns:** `Optional[WallenProofResult]` — Proof result if valid, None if not provable within bounds.

---

## Functions

### `def prove_wallen(formula: Formula, premises: Optional[List[Formula]], max_multiplicity: int) -> Optional[WallenProofResult]`

Proves an intuitionistic propositional formula using Wallen's matrix method.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The formula to prove. |
| `premises` | `Optional[List[Formula]], default=None` | Optional list of hypothesis premises. |
| `max_multiplicity` | `int, default=3` | Maximum multiplicity for phi-node duplications. |

**Returns:** `Optional[WallenProofResult]` — Derivation proof result if valid, None if unprovable.


---
