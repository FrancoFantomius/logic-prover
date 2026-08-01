# API Reference: `core`

# Module `solver.core.ast`

Abstract Syntax Tree (AST) definitions for First-Order Logic terms and formulas.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class VariableKind(Enum)`

Distinguishes variable usage in logic expressions.

### `class Term(ABC)`

Abstract Base Class for all term AST nodes.

### `class Formula(ABC)`

Abstract Base Class for all formula AST nodes.

### `class Variable(Term)`

Represents an individual variable v_id with an integer index, sort, and kind.

### `class Constant(Term)`

Represents a constant symbol c_name with a sort annotation.

### `class FunctionApp(Term)`

Represents function application f(t_1, ..., t_k).

### `class PredicateApp(Formula)`

Represents predicate application P(t_1, ..., t_k).

### `class Equality(Formula)`

Represents term equality t_1 = t_2.

### `class Not(Formula)`

Represents logical negation ~operand.

### `class And(Formula)`

Represents logical conjunction left & right.

### `class Or(Formula)`

Represents logical disjunction left | right.

### `class Implies(Formula)`

Represents logical implication left => right.

### `class Iff(Formula)`

Represents logical equivalence left <=> right.

### `class Forall(Formula)`

Represents universal quantification forall variable. body.

### `class Exists(Formula)`

Represents existential quantification exists variable. body.

---

## Functions

### `def free_variables(node: Union[Term, Formula]) -> Set[Variable]`

Returns the set of free individual variables present in a term or formula AST node.

**Returns:** `Set[Variable]`

### `def bound_variables(node: Union[Term, Formula]) -> Set[Variable]`

Returns the set of bound variables introduced by quantifiers in a formula AST node.

**Returns:** `Set[Variable]`

### `def formula_depth(formula: Formula) -> int`

Computes the maximum height/depth of the formula AST.

Leaf formula nodes (PredicateApp, Equality) have depth 1.

**Returns:** `int`

### `def formula_size(formula: Formula) -> int`

Computes the total number of AST nodes (both Formula and Term nodes) in a formula tree.

**Returns:** `int`

### `def canonicalize_bound_variables(formula: Formula) -> Formula`

Performs canonical alpha-conversion of bound variables in a formula.

Free variables retain their original IDs and sorts.
Bound variables are renamed sequentially (v_0, v_1, ...) skipping free variable IDs.

Guarantees:
1. Idempotency: canonicalize(canonicalize(f)) == canonicalize(f)
2. Alpha-equivalence: If f1 and f2 are alpha-equivalent, canonicalize(f1) == canonicalize(f2)
3. Free variable preservation: free_variables(canonicalize(f)) == free_variables(f)

**Returns:** `Formula`


---

# Module `solver.core.database`

SQLite database persistence engine for solver formulas, axioms, and theorems.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class KnowledgeDatabase`

SQLite persistent storage engine for AST formulas, axioms, proved theorems, and proof DAGs.

#### Methods

##### `def __init__(self, db_path: Union[str, Path]) -> None`

Initializes the database connection and schema tables.

**Returns:** `None`

##### `def close(self) -> None`

Closes the underlying SQLite connection.

**Returns:** `None`

##### `def add_axiom(self, name: str, formula: Formula, category: str) -> None`

Registers a named axiom in database. Raises DatabaseError on duplicate name.

**Returns:** `None`

##### `def add_theorem(self, name: str, formula: Formula, proof: Optional[ProofDAG], category: str) -> None`

Registers a proved theorem and optional proof DAG.

**Returns:** `None`

##### `def get_axioms(self, category: Optional[str]) -> List[Tuple[str, Formula]]`

Retrieves axioms, optionally filtered by category.

**Returns:** `List[Tuple[str, Formula]]`

##### `def get_theorems(self, category: Optional[str]) -> List[Tuple[str, Formula]]`

Retrieves theorems, optionally filtered by category.

**Returns:** `List[Tuple[str, Formula]]`

##### `def get_proof(self, theorem_name: str) -> Optional[ProofDAG]`

Retrieves proof DAG for named theorem.

**Returns:** `Optional[ProofDAG]`

##### `def contains_formula(self, formula: Formula) -> bool`

Checks if formula (or an alpha-equivalent variant) exists in database.

**Returns:** `bool`

##### `def search_formulas(self, predicate_name: Optional[str], max_depth: Optional[int], max_size: Optional[int], category: Optional[str]) -> List[Formula]`

Queries formulas using indexed structural attributes.

**Returns:** `List[Formula]`

---

## Functions

### `def extract_predicates(formula: Formula) -> Set[str]`

Extracts all predicate symbol names from a formula.

**Returns:** `Set[str]`

### `def extract_functions(node: Union[Formula, Term]) -> Set[str]`

Extracts all function symbol names from a formula or term.

**Returns:** `Set[str]`


---

# Module `solver.core.equality`

Congruence closure algorithms for tracking ground term equivalences and function congruences.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class CongruenceClosure`

Congruence closure subsystem for tracking term equivalences and propagating function congruences.

#### Methods

##### `def __init__(self) -> None`

Initializes an empty CongruenceClosure instance.

**Returns:** `None`

##### `def add_term(self, term: Term) -> None`

Recursively registers a term and all its subterms in the congruence graph.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `term` | `Term` | The Term instance to add. |

**Returns:** `None`

##### `def find(self, term: Term) -> Term`

Finds the equivalence class representative of a term with path compression.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `term` | `Term` | The term to look up. |

**Returns:** `Term` — The representative Term instance.

##### `def merge(self, t1: Term, t2: Term) -> None`

Asserts t1 = t2 and propagates congruence through function applications.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `t1` | `Term` | Left term of equality. |
| `t2` | `Term` | Right term of equality. |

**Returns:** `None`

##### `def are_equal(self, t1: Term, t2: Term) -> bool`

Checks if two terms belong to the same equivalence class.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `t1` | `Term` | First term. |
| `t2` | `Term` | Second term. |

**Returns:** `bool` — True if t1 and t2 are proven equal, False otherwise.

##### `def explain(self, t1: Term, t2: Term) -> Optional[List[Equality]]`

Generates a chain of Equalities proving t1 = t2 using BFS pathfinding on the proof graph.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `t1` | `Term` | Start term. |
| `t2` | `Term` | Target term. |

**Returns:** `Optional[List[Equality]]` — List of Equality steps proving t1 = t2, empty list if t1 == t2, or None if not equal.

---

## Functions

### `def equality_substitution(eq: Equality, formula: Formula) -> List[Formula]`

Generates all non-trivial formulas obtained by replacing occurrences of eq.left with eq.right or vice versa.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `eq` | `Equality` | The Equality rule (t1 = t2). |
| `formula` | `Formula` | Target formula to perform substitutions on. |

**Returns:** `List[Formula]` — List of distinct newly formed Formula objects.


---

# Module `solver.core.exceptions`

Custom exception hierarchy for the solver library.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class SolverError(Exception)`

Base exception for all errors raised by the solver library.

#### Methods

##### `def __init__(self, message: str) -> None`

Initializes a SolverError exception instance.

**Returns:** `None`

### `class ParseError(SolverError)`

Raised when parsing formula or term text fails due to syntax or token errors.

### `class UnificationError(SolverError)`

Raised when term or formula unification fails.

### `class SortMismatchError(UnificationError)`

Raised when terms or expressions of incompatible sorts are combined or unified.

#### Methods

##### `def __init__(self, message: str, expected_sort: Optional[Sort], actual_sort: Optional[Sort]) -> None`

Initializes a SortMismatchError exception instance.

**Returns:** `None`

### `class ProofTimeoutError(SolverError)`

Raised when automated proof search exceeds the allocated time limit.

### `class ProofSearchExhaustedError(SolverError)`

Raised when proof search completes without finding a proof or refutation.

### `class InvalidFormulaError(SolverError)`

Raised when constructing an ill-formed AST node (e.g. arity mismatch, invalid ID).

### `class ValidationError(SolverError)`

Raised when AST validation checks fail (e.g., sort mismatch, unbound index).

### `class DatabaseError(SolverError)`

Raised when persistence operations (SQLite I/O, schema errors, serialization) fail.

### `class RewriteDivergenceError(SolverError)`

Raised when formula normalization fails to reach a fixed point within max_steps.


---

# Module `solver.core.parser`

Lexer, parser, and string serializer for First-Order Logic terms and formulas.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class TokenType(Enum)`

Enumeration of token types recognized by the formula and term lexer.

### `class Token`

---

## Functions

### `def tokenize(text: str) -> List[Token]`

Scans text into a list of Token objects with line and column tracking. Raises ParseError on unrecognized character sequences.

**Returns:** `List[Token]`

### `def parse_formula(text: str, signature: Signature) -> Formula`

Parses text into a Formula AST object using signature context. Raises ParseError on syntax error or symbol mismatch.

**Returns:** `Formula`

### `def parse_term(text: str, signature: Signature) -> Term`

Parses text into a Term AST object using signature context. Raises ParseError on syntax error or symbol mismatch.

**Returns:** `Term`

### `def to_string(node: Union[Term, Formula], notation: str) -> str`

Serializes a Term or Formula AST to a string representation. Supported notations: 'infix' (default), 'prefix', 'latex'.

**Returns:** `str`


---

# Module `solver.core.rewriter`

Term rewriting system for applying directional rewrite rules and normalizations.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class RewriteRule`

Oriented rewrite rule lhs -> rhs with optional side condition.

---

## Functions

### `def match_term(pattern: Term, target: Term, subst: Optional[Dict[Variable, Term]]) -> Optional[Dict[Variable, Term]]`

Single-direction pattern matching for terms.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `pattern` | `Term` | Pattern term (may contain pattern variables). |
| `target` | `Term` | Ground/concrete target term. |
| `subst` | `Optional[Dict[Variable, Term]]` | Current variable mapping. |

**Returns:** `Optional[Dict[Variable, Term]]` — Updated variable substitution dict if match succeeds, None otherwise.

### `def match_formula(pattern: Formula, target: Formula, subst: Optional[Dict[Variable, Term]]) -> Optional[Dict[Variable, Term]]`

Single-direction pattern matching for formulas.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `pattern` | `Formula` | Pattern formula. |
| `target` | `Formula` | Target formula. |
| `subst` | `Optional[Dict[Variable, Term]]` | Current variable mapping. |

**Returns:** `Optional[Dict[Variable, Term]]` — Substitution dict if match succeeds, None otherwise.

### `def rewrite(node: Union[Term, Formula], rule: RewriteRule) -> Optional[Union[Term, Formula]]`

Applies a rewrite rule at the root of a node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Union[Term, Formula]` | The Term or Formula to rewrite at root. |
| `rule` | `RewriteRule` | The RewriteRule to apply. |

**Returns:** `Optional[Union[Term, Formula]]` — Transformed node if rule matched and condition satisfied, None otherwise.

### `def rewrite_all(node: Union[Term, Formula], rules: List[RewriteRule], max_root_steps: int) -> Union[Term, Formula]`

Applies matching rewrite rules bottom-up across subnodes until fixed point.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Union[Term, Formula]` | Term or Formula to rewrite. |
| `rules` | `List[RewriteRule]` | List of RewriteRule instances. |
| `max_root_steps` | `int` | Safety step limit for root-level iterations. |

**Returns:** `Union[Term, Formula]` — Rewritten node.

### `def normalize(formula: Formula, rules: List[RewriteRule], max_steps: int) -> Formula`

Normalizes a formula by repeatedly applying rewrite_all up to max_steps iterations.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | Formula to normalize. |
| `rules` | `List[RewriteRule]` | Set of rewrite rules. |
| `max_steps` | `int` | Maximum normalization iterations allowed. |

**Returns:** `Formula` — Canonical normalized Formula.

**Raises:**
- `RewriteDivergenceError`: If max_steps is exceeded without reaching a fixed point.


---

# Module `solver.core.signature`

Logical signature definition module for declaring function, predicate, and constant symbols.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class FunctionDecl`

Declaration of a function symbol in a logical signature.

### `class PredicateDecl`

Declaration of a predicate symbol in a logical signature.

### `class Signature`

Declares available functions, predicates, constants, and sort constructors in a logical context.

#### Methods

##### `def __init__(self, functions: Optional[Dict[str, FunctionDecl]], predicates: Optional[Dict[str, PredicateDecl]], constants: Optional[Dict[str, Sort]], sort_constructors: Optional[Dict[str, int]]) -> None`

Initializes a new Signature instance with optional predefined declarations.

**Returns:** `None`

##### `def register_function(self, name: str, arity: int, arg_sorts: Tuple[Sort, ...], return_sort: Sort) -> None`

Register a function symbol in the signature.

**Returns:** `None`

**Raises:**
- `ValidationError`: If symbol name collides with another predicate/constant or incompatible function decl.

##### `def register_predicate(self, name: str, arity: int, arg_sorts: Tuple[Sort, ...]) -> None`

Register a predicate symbol in the signature.

**Returns:** `None`

**Raises:**
- `ValidationError`: If symbol name collides with another function/constant or incompatible predicate decl.

##### `def register_constant(self, name: str, sort: Sort) -> None`

Register a constant symbol in the signature.

**Returns:** `None`

**Raises:**
- `ValidationError`: If symbol name collides with a function/predicate or incompatible constant declaration.

##### `def register_sort_constructor(self, name: str, arity: int) -> None`

Register a parameterized sort constructor (e.g. Set -> 1, Pair -> 2).

**Returns:** `None`

##### `def lookup_function(self, name: str) -> Optional[FunctionDecl]`

Retrieve function declaration by name.

**Returns:** `Optional[FunctionDecl]`

##### `def lookup_predicate(self, name: str) -> Optional[PredicateDecl]`

Retrieve predicate declaration by name.

**Returns:** `Optional[PredicateDecl]`

##### `def lookup_constant(self, name: str) -> Optional[Sort]`

Retrieve constant sort by name.

**Returns:** `Optional[Sort]`

##### `def lookup_sort_constructor(self, name: str) -> Optional[int]`

Retrieve sort constructor arity by name.

**Returns:** `Optional[int]`

##### `def has_symbol(self, name: str) -> bool`

Check if symbol name is declared as constant, function, or predicate.

**Returns:** `bool`

##### `def merge(self, other: Signature) -> Signature`

Merge two signatures into a new combined Signature.

**Returns:** `Signature`

**Raises:**
- `ValidationError`: If there is a declaration conflict between the two signatures.

##### `def clone(self) -> Signature`

Create a deep copy of the signature.

**Returns:** `Signature`

##### `def empty(cls) -> Signature`

Create an empty signature instance.

**Returns:** `Signature`


---

# Module `solver.core.sorts`

Sort system hierarchy for primitive, parameterized, and function sorts.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class Sort(ABC)`

Abstract Base Class for logical sorts.

#### Methods

##### `def name(self) -> str`

Returns the canonical string representation of the sort.

**Returns:** `str`

### `class PrimitiveSort(Sort)`

Represents an atomic sort (e.g. Ind, Nat, Bool).

#### Methods

##### `def name(self) -> str`

**Returns:** `str`

### `class ParameterizedSort(Sort)`

Represents a composite parameterized sort (e.g., Set(Nat), Pair(Nat, Bool)).

#### Methods

##### `def name(self) -> str`

**Returns:** `str`

### `class FunctionSort(Sort)`

Represents a function sort (domain sorts -> codomain sort). Reserved for SOL extensions.

#### Methods

##### `def name(self) -> str`

**Returns:** `str`

---

## Functions

### `def SetSort(element_sort: Sort) -> ParameterizedSort`

Helper constructing a Set parameterized sort for element_sort.

**Returns:** `ParameterizedSort`

### `def ListSort(element_sort: Sort) -> ParameterizedSort`

Helper constructing a List parameterized sort for element_sort.

**Returns:** `ParameterizedSort`

### `def PairSort(sort_a: Sort, sort_b: Sort) -> ParameterizedSort`

Helper constructing a Pair parameterized sort for sort_a and sort_b.

**Returns:** `ParameterizedSort`

### `def is_compatible(s1: Sort, s2: Sort) -> bool`

Determines if two sorts are compatible for unification and term assignment.

Rules:
1. Identity: If s1 == s2, returns True.
2. Wildcard: Ind is compatible with all individual primitive and parameterized sorts.
3. Primitive: Two PrimitiveSorts must match names or involve Ind.
4. Parameterized: Same constructor, same arity, and recursively compatible arguments.
5. FunctionSort: Same argument arity, recursively compatible argument sorts and return sorts.

**Returns:** `bool`

### `def sort_of_term(term: Term, context: Optional[Dict[str, Sort]]) -> Sort`

Infers the sort of a Term node.

- Variable: term.sort
- Constant: term.sort or lookup in context if context provided
- FunctionApp: term.return_sort or lookup function return sort in context

**Returns:** `Sort`


---

# Module `solver.core.substitutions`

Substitutions and term/formula unification algorithms.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class SubstitutionTransformer(ASTTransformer)`

AST transformer for capture-avoiding variable substitution.

#### Methods

##### `def __init__(self, mapping: Dict[Variable, Term]) -> None`

Initializes a SubstitutionTransformer instance with mapping.

**Returns:** `None`

##### `def visit_variable(self, node: Variable) -> Term`

**Returns:** `Term`

##### `def visit_constant(self, node: Constant) -> Term`

**Returns:** `Term`

##### `def visit_function_app(self, node: FunctionApp) -> FunctionApp`

**Returns:** `FunctionApp`

##### `def visit_predicate_app(self, node: PredicateApp) -> PredicateApp`

**Returns:** `PredicateApp`

##### `def visit_equality(self, node: Equality) -> Equality`

**Returns:** `Equality`

##### `def visit_forall(self, node: Forall) -> Formula`

**Returns:** `Formula`

##### `def visit_exists(self, node: Exists) -> Formula`

**Returns:** `Formula`

---

## Functions

### `def substitute_term(term: Term, mapping: Dict[Variable, Term]) -> Term`

Replaces variables in a term according to mapping.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `term` | `Term` | Target Term AST node. |
| `mapping` | `Dict[Variable, Term]` | Dictionary mapping variables to replacement terms. |

**Returns:** `Term` — New Term node with variables substituted.

**Raises:**
- `SortMismatchError`: If any mapped term sort is incompatible with variable sort.

### `def substitute_formula(formula: Formula, mapping: Dict[Variable, Term]) -> Formula`

Replaces free variables in a formula while preventing variable capture.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | Target Formula AST node. |
| `mapping` | `Dict[Variable, Term]` | Dictionary mapping free variables to replacement terms. |

**Returns:** `Formula` — New Formula node with capture-avoiding substitution applied.

**Raises:**
- `SortMismatchError`: If any mapped term sort is incompatible with variable sort.

### `def apply_substitution(subst: Dict[Variable, Term], term: Term) -> Term`

Applies a substitution mapping to a term (idempotent helper wrapper).

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `subst` | `Dict[Variable, Term]` | Substitution dictionary. |
| `term` | `Term` | Target term. |

**Returns:** `Term` — Substituted term.

### `def compose_substitutions(s1: Dict[Variable, Term], s2: Dict[Variable, Term]) -> Dict[Variable, Term]`

Composes two substitutions s1 and s2 such that: apply_substitution(compose_substitutions(s1, s2), t) == apply_substitution(s1, apply_substitution(s2, t))

Mathematical Definition: (s1 o s2)(x) = s1(s2(x))

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `s1` | `Dict[Variable, Term]` | First substitution applied (outer substitution). |
| `s2` | `Dict[Variable, Term]` | Second substitution applied (inner substitution). |

**Returns:** `Dict[Variable, Term]` — Composed substitution dictionary.

### `def unify_terms(t1: Term, t2: Term, subst: Optional[Dict[Variable, Term]]) -> Dict[Variable, Term]`

Implements Robinson's unification algorithm on first-order terms with occur-check and sort compatibility checking.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `t1` | `Term` | First term. |
| `t2` | `Term` | Second term. |
| `subst` | `Optional[Dict[Variable, Term]]` | Accumulated substitution context (optional). |

**Returns:** `Dict[Variable, Term]` — Most General Unifier (MGU) as a dictionary mapping variables to terms.

**Raises:**
- `UnificationError`: If terms cannot be unified (e.g. constant mismatch, arity mismatch, occur-check failure).
- `SortMismatchError`: If term sorts are incompatible during variable binding.

### `def unify_formulas(f1: Formula, f2: Formula) -> Dict[Variable, Term]`

Unifies atomic predicate expressions (first-order only).

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `f1` | `Formula` | First atomic formula (PredicateApp or Equality). |
| `f2` | `Formula` | Second atomic formula (PredicateApp or Equality). |

**Returns:** `Dict[Variable, Term]` — MGU substitution dictionary.

**Raises:**
- `UnificationError`: If formulas are non-atomic or predicates/arities mismatch.


---

# Module `solver.core.validator`

Validation engine for checking AST sort and signature consistency.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def validate_term(term: Term, signature: Signature, scope: Optional[Set[Variable]]) -> List[ValidationError]`

Validate a term AST node for symbol registration, arity, and sort correctness.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `term` | `Term` | The term node to validate. |
| `signature` | `Signature` | The logical signature context. |
| `scope` | `Optional[Set[Variable]]` | Set of currently bound variables in outer scopes. |

**Returns:** `List[ValidationError]` — A list of validation errors found in the term (empty if well-formed).

### `def validate_formula(formula: Formula, signature: Signature, scope: Optional[Set[Variable]]) -> List[ValidationError]`

Validate a formula AST node for arity, sorts, binder scoping, and quantifier well-formedness.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The formula node to validate. |
| `signature` | `Signature` | The logical signature context. |
| `scope` | `Optional[Set[Variable]]` | Set of currently bound variables in outer scopes. |

**Returns:** `List[ValidationError]` — A list of validation errors found in the formula (empty if well-formed).

### `def is_well_formed(node: Union[Term, Formula], signature: Signature) -> bool`

Convenience wrapper returning True if the AST node has zero validation errors.

**Returns:** `bool`


---

# Module `solver.core.visitors`

AST Visitor pattern implementations for traversal, size computation, and serialization.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class ASTVisitor(ABC, Generic[T])`

Generic visitor base class for AST traversal.

#### Methods

##### `def visit(self, node: Union[Term, Formula]) -> T`

Master dispatch method targeting specific visit_* methods.

**Returns:** `T`

##### `def visit_variable(self, node: Variable) -> T`

**Returns:** `T`

##### `def visit_constant(self, node: Constant) -> T`

**Returns:** `T`

##### `def visit_function_app(self, node: FunctionApp) -> T`

**Returns:** `T`

##### `def visit_predicate_app(self, node: PredicateApp) -> T`

**Returns:** `T`

##### `def visit_equality(self, node: Equality) -> T`

**Returns:** `T`

##### `def visit_not(self, node: Not) -> T`

**Returns:** `T`

##### `def visit_and(self, node: And) -> T`

**Returns:** `T`

##### `def visit_or(self, node: Or) -> T`

**Returns:** `T`

##### `def visit_implies(self, node: Implies) -> T`

**Returns:** `T`

##### `def visit_iff(self, node: Iff) -> T`

**Returns:** `T`

##### `def visit_forall(self, node: Forall) -> T`

**Returns:** `T`

##### `def visit_exists(self, node: Exists) -> T`

**Returns:** `T`

##### `def visit_forall_pred(self, node: ForallPred) -> T`

**Returns:** `T`

##### `def visit_exists_pred(self, node: ExistsPred) -> T`

**Returns:** `T`

##### `def visit_forall_func(self, node: ForallFunc) -> T`

**Returns:** `T`

##### `def visit_exists_func(self, node: ExistsFunc) -> T`

**Returns:** `T`

### `class ASTTransformer(ASTVisitor[Union[Term, Formula]])`

Visitor that returns transformed AST nodes (bottom-up structural transformation).

#### Methods

##### `def visit_variable(self, node: Variable) -> Term`

**Returns:** `Term`

##### `def visit_constant(self, node: Constant) -> Term`

**Returns:** `Term`

##### `def visit_function_app(self, node: FunctionApp) -> Term`

**Returns:** `Term`

##### `def visit_predicate_app(self, node: PredicateApp) -> Formula`

**Returns:** `Formula`

##### `def visit_equality(self, node: Equality) -> Formula`

**Returns:** `Formula`

##### `def visit_not(self, node: Not) -> Formula`

**Returns:** `Formula`

##### `def visit_and(self, node: And) -> Formula`

**Returns:** `Formula`

##### `def visit_or(self, node: Or) -> Formula`

**Returns:** `Formula`

##### `def visit_implies(self, node: Implies) -> Formula`

**Returns:** `Formula`

##### `def visit_iff(self, node: Iff) -> Formula`

**Returns:** `Formula`

##### `def visit_forall(self, node: Forall) -> Formula`

**Returns:** `Formula`

##### `def visit_exists(self, node: Exists) -> Formula`

**Returns:** `Formula`

##### `def visit_forall_pred(self, node: ForallPred) -> Formula`

**Returns:** `Formula`

##### `def visit_exists_pred(self, node: ExistsPred) -> Formula`

**Returns:** `Formula`

##### `def visit_forall_func(self, node: ForallFunc) -> Formula`

**Returns:** `Formula`

##### `def visit_exists_func(self, node: ExistsFunc) -> Formula`

**Returns:** `Formula`

### `class DepthVisitor(ASTVisitor[int])`

Computes the maximum depth of an AST tree.

#### Methods

##### `def visit_variable(self, node: Variable) -> int`

**Returns:** `int`

##### `def visit_constant(self, node: Constant) -> int`

**Returns:** `int`

##### `def visit_function_app(self, node: FunctionApp) -> int`

**Returns:** `int`

##### `def visit_predicate_app(self, node: PredicateApp) -> int`

**Returns:** `int`

##### `def visit_equality(self, node: Equality) -> int`

**Returns:** `int`

##### `def visit_not(self, node: Not) -> int`

**Returns:** `int`

##### `def visit_and(self, node: And) -> int`

**Returns:** `int`

##### `def visit_or(self, node: Or) -> int`

**Returns:** `int`

##### `def visit_implies(self, node: Implies) -> int`

**Returns:** `int`

##### `def visit_iff(self, node: Iff) -> int`

**Returns:** `int`

##### `def visit_forall(self, node: Forall) -> int`

**Returns:** `int`

##### `def visit_exists(self, node: Exists) -> int`

**Returns:** `int`

##### `def visit_forall_pred(self, node: ForallPred) -> int`

**Returns:** `int`

##### `def visit_exists_pred(self, node: ExistsPred) -> int`

**Returns:** `int`

##### `def visit_forall_func(self, node: ForallFunc) -> int`

**Returns:** `int`

##### `def visit_exists_func(self, node: ExistsFunc) -> int`

**Returns:** `int`

### `class SizeVisitor(ASTVisitor[int])`

Computes the total number of nodes in an AST tree.

#### Methods

##### `def visit_variable(self, node: Variable) -> int`

**Returns:** `int`

##### `def visit_constant(self, node: Constant) -> int`

**Returns:** `int`

##### `def visit_function_app(self, node: FunctionApp) -> int`

**Returns:** `int`

##### `def visit_predicate_app(self, node: PredicateApp) -> int`

**Returns:** `int`

##### `def visit_equality(self, node: Equality) -> int`

**Returns:** `int`

##### `def visit_not(self, node: Not) -> int`

**Returns:** `int`

##### `def visit_and(self, node: And) -> int`

**Returns:** `int`

##### `def visit_or(self, node: Or) -> int`

**Returns:** `int`

##### `def visit_implies(self, node: Implies) -> int`

**Returns:** `int`

##### `def visit_iff(self, node: Iff) -> int`

**Returns:** `int`

##### `def visit_forall(self, node: Forall) -> int`

**Returns:** `int`

##### `def visit_exists(self, node: Exists) -> int`

**Returns:** `int`

##### `def visit_forall_pred(self, node: ForallPred) -> int`

**Returns:** `int`

##### `def visit_exists_pred(self, node: ExistsPred) -> int`

**Returns:** `int`

##### `def visit_forall_func(self, node: ForallFunc) -> int`

**Returns:** `int`

##### `def visit_exists_func(self, node: ExistsFunc) -> int`

**Returns:** `int`

### `class FreeVariableCollector(ASTVisitor[Set[Variable]])`

Collects all free individual variables in a term or formula.

#### Methods

##### `def visit_variable(self, node: Variable) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_constant(self, node: Constant) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_function_app(self, node: FunctionApp) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_predicate_app(self, node: PredicateApp) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_equality(self, node: Equality) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_not(self, node: Not) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_and(self, node: And) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_or(self, node: Or) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_implies(self, node: Implies) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_iff(self, node: Iff) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_forall(self, node: Forall) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_exists(self, node: Exists) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_forall_pred(self, node: ForallPred) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_exists_pred(self, node: ExistsPred) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_forall_func(self, node: ForallFunc) -> Set[Variable]`

**Returns:** `Set[Variable]`

##### `def visit_exists_func(self, node: ExistsFunc) -> Set[Variable]`

**Returns:** `Set[Variable]`

### `class SubstitutionTransformer(ASTTransformer)`

Applies variable substitutions to terms and formulas with capture avoidance.

#### Methods

##### `def __init__(self, mapping: Dict[Variable, Term]) -> None`

Initializes the substitution transformer with a variable to term mapping.

**Returns:** `None`

##### `def visit_variable(self, node: Variable) -> Term`

**Returns:** `Term`

##### `def visit_forall(self, node: Forall) -> Formula`

**Returns:** `Formula`

##### `def visit_exists(self, node: Exists) -> Formula`

**Returns:** `Formula`

### `class ExportVisitor(ASTVisitor[str])`

Translates AST to string in various notations ('infix', 'prefix', 'latex').

#### Methods

##### `def __init__(self, notation: str) -> None`

Initializes ExportVisitor with string notation.

**Returns:** `None`

##### `def visit_variable(self, node: Variable) -> str`

**Returns:** `str`

##### `def visit_constant(self, node: Constant) -> str`

**Returns:** `str`

##### `def visit_function_app(self, node: FunctionApp) -> str`

**Returns:** `str`

##### `def visit_predicate_app(self, node: PredicateApp) -> str`

**Returns:** `str`

##### `def visit_equality(self, node: Equality) -> str`

**Returns:** `str`

##### `def visit_not(self, node: Not) -> str`

**Returns:** `str`

##### `def visit_and(self, node: And) -> str`

**Returns:** `str`

##### `def visit_or(self, node: Or) -> str`

**Returns:** `str`

##### `def visit_implies(self, node: Implies) -> str`

**Returns:** `str`

##### `def visit_iff(self, node: Iff) -> str`

**Returns:** `str`

##### `def visit_forall(self, node: Forall) -> str`

**Returns:** `str`

##### `def visit_exists(self, node: Exists) -> str`

**Returns:** `str`

##### `def visit_forall_pred(self, node: ForallPred) -> str`

**Returns:** `str`

##### `def visit_exists_pred(self, node: ExistsPred) -> str`

**Returns:** `str`

##### `def visit_forall_func(self, node: ForallFunc) -> str`

**Returns:** `str`

##### `def visit_exists_func(self, node: ExistsFunc) -> str`

**Returns:** `str`


---
