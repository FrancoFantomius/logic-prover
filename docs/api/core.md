# API Reference: `core`

# Module `logic_prover.core.database`

SQLite database persistence engine for logic formulas, axioms, and theorems.

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

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `db_path` | `Union[str, Path]` | Filesystem path to the SQLite database file, or ':memory:' for an in-memory database. Defaults to 'logic_data.db'. |

**Returns:** `None`

##### `def close(self) -> None`

Closes the underlying SQLite connection.

**Returns:** `None`

##### `def add_axiom(self, name: str, formula: Formula, category: str) -> None`

Registers a named axiom in database. Raises DatabaseError on duplicate name.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Unique string name for the axiom. |
| `formula` | `Formula` | The Formula AST node to store. |
| `category` | `str` | Optional classification label for the axiom (default 'general'). |

**Returns:** `None`

**Raises:**
- `DatabaseError`: If the axiom name is already registered or storage fails.

##### `def add_theorem(self, name: str, formula: Formula, proof: Optional[ProofDAG], category: str) -> None`

Registers a proved theorem and optional proof DAG.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Unique string name for the theorem. |
| `formula` | `Formula` | The Formula AST node to store. |
| `proof` | `Optional[ProofDAG]` | Optional proof object (ProofDAG, dict, or JSON string) to persist. |
| `category` | `str` | Optional classification label for the theorem (default 'general'). |

**Returns:** `None`

**Raises:**
- `DatabaseError`: If the theorem name is already registered or storage fails.

##### `def get_axioms(self, category: Optional[str]) -> List[Tuple[str, Formula]]`

Retrieves axioms, optionally filtered by category.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `category` | `Optional[str]` | Optional category name to filter axioms by. |

**Returns:** `List[Tuple[str, Formula]]` — List of (name, Formula) tuples for the retrieved axioms.

**Raises:**
- `DatabaseError`: If the database connection is closed.

##### `def get_theorems(self, category: Optional[str]) -> List[Tuple[str, Formula]]`

Retrieves theorems, optionally filtered by category.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `category` | `Optional[str]` | Optional category name to filter theorems by. |

**Returns:** `List[Tuple[str, Formula]]` — List of (name, Formula) tuples for the retrieved theorems.

**Raises:**
- `DatabaseError`: If the database connection is closed.

##### `def get_proof(self, theorem_name: str) -> Optional[ProofDAG]`

Retrieves proof DAG for named theorem.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `theorem_name` | `str` | Name of the theorem whose proof should be retrieved. |

**Returns:** `Optional[ProofDAG]` — The proof DAG object, a raw JSON string if deserialization is not possible, or None if no proof is stored.

**Raises:**
- `DatabaseError`: If the database connection is closed.

##### `def contains_formula(self, formula: Formula) -> bool`

Checks if formula (or an alpha-equivalent variant) exists in database.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The Formula AST node to look up. |

**Returns:** `bool` — True if an alpha-equivalent formula is stored, False otherwise.

**Raises:**
- `DatabaseError`: If the database connection is closed.

##### `def search_formulas(self, predicate_name: Optional[str], max_depth: Optional[int], max_size: Optional[int], category: Optional[str]) -> List[Formula]`

Queries formulas using indexed structural attributes.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `predicate_name` | `Optional[str]` | Optional predicate symbol name to filter by. |
| `max_depth` | `Optional[int]` | Optional maximum formula depth to include. |
| `max_size` | `Optional[int]` | Optional maximum formula size to include. |
| `category` | `Optional[str]` | Optional category name to filter by. |

**Returns:** `List[Formula]` — List of Formula nodes matching all provided filters.

**Raises:**
- `DatabaseError`: If the database connection is closed.

---

## Functions

### `def extract_predicates(formula: Formula) -> Set[str]`

Extracts all predicate symbol names from a formula.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The Formula AST node to scan for predicate symbols. |

**Returns:** `Set[str]` — Set of predicate name strings found in the formula.

### `def extract_functions(node: Union[Formula, Term]) -> Set[str]`

Extracts all function symbol names from a formula or term.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Union[Formula, Term]` | The Formula or Term AST node to scan for function symbols. |

**Returns:** `Set[str]` — Set of function name strings found in the node.


---

# Module `logic_prover.core.parser`

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

Scans text into a list of Token objects with line and column tracking.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `text` | `str` | Raw input string to tokenize. |

**Returns:** `List[Token]` — List of Token objects ending with an EOF token.

**Raises:**
- `ParseError`: On unrecognized character sequences.

### `def parse_formula(text: str, signature: Signature) -> Formula`

Parses text into a Formula AST object using signature context.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `text` | `str` | Formula string to parse. |
| `signature` | `Signature` | Logical signature resolving symbols used in the formula. |

**Returns:** `Formula` — The parsed Formula AST node.

**Raises:**
- `ParseError`: On syntax error or symbol mismatch.

### `def parse_term(text: str, signature: Signature) -> Term`

Parses text into a Term AST object using signature context.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `text` | `str` | Term string to parse. |
| `signature` | `Signature` | Logical signature resolving symbols used in the term. |

**Returns:** `Term` — The parsed Term AST node.

**Raises:**
- `ParseError`: On syntax error or symbol mismatch.

### `def to_string(node: Union[Term, Formula], notation: str) -> str`

Serializes a Term or Formula AST to a string representation.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Union[Term, Formula]` | The Term or Formula AST node to serialize. |
| `notation` | `str` | Output notation, one of 'infix' (default), 'prefix', or 'latex'. |

**Returns:** `str` — The serialized string representation of the node.

**Raises:**
- `ValueError`: If notation is not one of the supported values.


---

# Module `logic_prover.core.rewriter`

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

# Module `logic_prover.core.substitutions`

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

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `mapping` | `Dict[Variable, Term]` | Dictionary mapping variables to their replacement terms. |

**Returns:** `None`

##### `def visit_variable(self, node: Variable) -> Term`

Handles visitation of a Variable node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Variable` | The Variable AST node being visited. |

**Returns:** `Term` — Result of visiting this node.

##### `def visit_constant(self, node: Constant) -> Term`

Handles visitation of a Constant node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Constant` | The Constant AST node being visited. |

**Returns:** `Term` — Result of visiting this node.

##### `def visit_function_app(self, node: FunctionApp) -> FunctionApp`

Handles visitation of a FunctionApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `FunctionApp` | The FunctionApp AST node being visited. |

**Returns:** `FunctionApp` — Result of visiting this node.

##### `def visit_predicate_app(self, node: PredicateApp) -> PredicateApp`

Handles visitation of a PredicateApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `PredicateApp` | The PredicateApp AST node being visited. |

**Returns:** `PredicateApp` — Result of visiting this node.

##### `def visit_equality(self, node: Equality) -> Equality`

Handles visitation of a Equality node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Equality` | The Equality AST node being visited. |

**Returns:** `Equality` — Result of visiting this node.

##### `def visit_forall(self, node: Forall) -> Formula`

Handles visitation of a Forall node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Forall` | The Forall AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_exists(self, node: Exists) -> Formula`

Handles visitation of a Exists node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Exists` | The Exists AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

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

# Module `logic_prover.core.validator`

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

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Union[Term, Formula]` | The Term or Formula AST node to check. |
| `signature` | `Signature` | The logical signature context used for validation. |

**Returns:** `bool` — True if the node is well-formed, False otherwise.


---

# Module `logic_prover.core.visitors`

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

Master dispatch method targeting specific visit_* methods via O(1) dict lookup.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Union[Term, Formula]` | The Term or Formula AST node to visit. |

**Returns:** `T` — Result of the matching visit_* method.

**Raises:**
- `TypeError`: If the node type is not supported.

##### `def visit_variable(self, node: Variable) -> T`

Handles visitation of a Variable node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Variable` | The Variable AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_constant(self, node: Constant) -> T`

Handles visitation of a Constant node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Constant` | The Constant AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_function_app(self, node: FunctionApp) -> T`

Handles visitation of a FunctionApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `FunctionApp` | The FunctionApp AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_predicate_app(self, node: PredicateApp) -> T`

Handles visitation of a PredicateApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `PredicateApp` | The PredicateApp AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_equality(self, node: Equality) -> T`

Handles visitation of a Equality node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Equality` | The Equality AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_not(self, node: Not) -> T`

Handles visitation of a Not node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Not` | The Not AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_and(self, node: And) -> T`

Handles visitation of a And node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `And` | The And AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_or(self, node: Or) -> T`

Handles visitation of a Or node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Or` | The Or AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_implies(self, node: Implies) -> T`

Handles visitation of a Implies node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Implies` | The Implies AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_iff(self, node: Iff) -> T`

Handles visitation of a Iff node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Iff` | The Iff AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_forall(self, node: Forall) -> T`

Handles visitation of a Forall node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Forall` | The Forall AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_exists(self, node: Exists) -> T`

Handles visitation of a Exists node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Exists` | The Exists AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_forall_pred(self, node: ForallPred) -> T`

Handles visitation of a ForallPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallPred` | The ForallPred AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_exists_pred(self, node: ExistsPred) -> T`

Handles visitation of a ExistsPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsPred` | The ExistsPred AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_forall_func(self, node: ForallFunc) -> T`

Handles visitation of a ForallFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallFunc` | The ForallFunc AST node being visited. |

**Returns:** `T` — Result of visiting this node.

##### `def visit_exists_func(self, node: ExistsFunc) -> T`

Handles visitation of a ExistsFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsFunc` | The ExistsFunc AST node being visited. |

**Returns:** `T` — Result of visiting this node.

### `class ASTTransformer(ASTVisitor[Union[Term, Formula]])`

Visitor that returns transformed AST nodes (bottom-up structural transformation).

#### Methods

##### `def visit_variable(self, node: Variable) -> Term`

Handles visitation of a Variable node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Variable` | The Variable AST node being visited. |

**Returns:** `Term` — Result of visiting this node.

##### `def visit_constant(self, node: Constant) -> Term`

Handles visitation of a Constant node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Constant` | The Constant AST node being visited. |

**Returns:** `Term` — Result of visiting this node.

##### `def visit_function_app(self, node: FunctionApp) -> Term`

Handles visitation of a FunctionApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `FunctionApp` | The FunctionApp AST node being visited. |

**Returns:** `Term` — Result of visiting this node.

##### `def visit_predicate_app(self, node: PredicateApp) -> Formula`

Handles visitation of a PredicateApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `PredicateApp` | The PredicateApp AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_equality(self, node: Equality) -> Formula`

Handles visitation of a Equality node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Equality` | The Equality AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_not(self, node: Not) -> Formula`

Handles visitation of a Not node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Not` | The Not AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_and(self, node: And) -> Formula`

Handles visitation of a And node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `And` | The And AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_or(self, node: Or) -> Formula`

Handles visitation of a Or node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Or` | The Or AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_implies(self, node: Implies) -> Formula`

Handles visitation of a Implies node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Implies` | The Implies AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_iff(self, node: Iff) -> Formula`

Handles visitation of a Iff node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Iff` | The Iff AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_forall(self, node: Forall) -> Formula`

Handles visitation of a Forall node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Forall` | The Forall AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_exists(self, node: Exists) -> Formula`

Handles visitation of a Exists node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Exists` | The Exists AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_forall_pred(self, node: ForallPred) -> Formula`

Handles visitation of a ForallPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallPred` | The ForallPred AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_exists_pred(self, node: ExistsPred) -> Formula`

Handles visitation of a ExistsPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsPred` | The ExistsPred AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_forall_func(self, node: ForallFunc) -> Formula`

Handles visitation of a ForallFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallFunc` | The ForallFunc AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_exists_func(self, node: ExistsFunc) -> Formula`

Handles visitation of a ExistsFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsFunc` | The ExistsFunc AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

### `class DepthVisitor(ASTVisitor[int])`

Computes the maximum depth of an AST tree.

#### Methods

##### `def visit_variable(self, node: Variable) -> int`

Handles visitation of a Variable node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Variable` | The Variable AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_constant(self, node: Constant) -> int`

Handles visitation of a Constant node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Constant` | The Constant AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_function_app(self, node: FunctionApp) -> int`

Handles visitation of a FunctionApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `FunctionApp` | The FunctionApp AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_predicate_app(self, node: PredicateApp) -> int`

Handles visitation of a PredicateApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `PredicateApp` | The PredicateApp AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_equality(self, node: Equality) -> int`

Handles visitation of a Equality node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Equality` | The Equality AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_not(self, node: Not) -> int`

Handles visitation of a Not node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Not` | The Not AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_and(self, node: And) -> int`

Handles visitation of a And node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `And` | The And AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_or(self, node: Or) -> int`

Handles visitation of a Or node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Or` | The Or AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_implies(self, node: Implies) -> int`

Handles visitation of a Implies node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Implies` | The Implies AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_iff(self, node: Iff) -> int`

Handles visitation of a Iff node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Iff` | The Iff AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_forall(self, node: Forall) -> int`

Handles visitation of a Forall node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Forall` | The Forall AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_exists(self, node: Exists) -> int`

Handles visitation of a Exists node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Exists` | The Exists AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_forall_pred(self, node: ForallPred) -> int`

Handles visitation of a ForallPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallPred` | The ForallPred AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_exists_pred(self, node: ExistsPred) -> int`

Handles visitation of a ExistsPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsPred` | The ExistsPred AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_forall_func(self, node: ForallFunc) -> int`

Handles visitation of a ForallFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallFunc` | The ForallFunc AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_exists_func(self, node: ExistsFunc) -> int`

Handles visitation of a ExistsFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsFunc` | The ExistsFunc AST node being visited. |

**Returns:** `int` — Result of visiting this node.

### `class SizeVisitor(ASTVisitor[int])`

Computes the total number of nodes in an AST tree.

#### Methods

##### `def visit_variable(self, node: Variable) -> int`

Handles visitation of a Variable node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Variable` | The Variable AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_constant(self, node: Constant) -> int`

Handles visitation of a Constant node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Constant` | The Constant AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_function_app(self, node: FunctionApp) -> int`

Handles visitation of a FunctionApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `FunctionApp` | The FunctionApp AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_predicate_app(self, node: PredicateApp) -> int`

Handles visitation of a PredicateApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `PredicateApp` | The PredicateApp AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_equality(self, node: Equality) -> int`

Handles visitation of a Equality node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Equality` | The Equality AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_not(self, node: Not) -> int`

Handles visitation of a Not node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Not` | The Not AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_and(self, node: And) -> int`

Handles visitation of a And node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `And` | The And AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_or(self, node: Or) -> int`

Handles visitation of a Or node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Or` | The Or AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_implies(self, node: Implies) -> int`

Handles visitation of a Implies node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Implies` | The Implies AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_iff(self, node: Iff) -> int`

Handles visitation of a Iff node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Iff` | The Iff AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_forall(self, node: Forall) -> int`

Handles visitation of a Forall node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Forall` | The Forall AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_exists(self, node: Exists) -> int`

Handles visitation of a Exists node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Exists` | The Exists AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_forall_pred(self, node: ForallPred) -> int`

Handles visitation of a ForallPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallPred` | The ForallPred AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_exists_pred(self, node: ExistsPred) -> int`

Handles visitation of a ExistsPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsPred` | The ExistsPred AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_forall_func(self, node: ForallFunc) -> int`

Handles visitation of a ForallFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallFunc` | The ForallFunc AST node being visited. |

**Returns:** `int` — Result of visiting this node.

##### `def visit_exists_func(self, node: ExistsFunc) -> int`

Handles visitation of a ExistsFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsFunc` | The ExistsFunc AST node being visited. |

**Returns:** `int` — Result of visiting this node.

### `class FreeVariableCollector(ASTVisitor[Set[Variable]])`

Collects all free individual variables in a term or formula.

#### Methods

##### `def visit_variable(self, node: Variable) -> Set[Variable]`

Handles visitation of a Variable node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Variable` | The Variable AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_constant(self, node: Constant) -> Set[Variable]`

Handles visitation of a Constant node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Constant` | The Constant AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_function_app(self, node: FunctionApp) -> Set[Variable]`

Handles visitation of a FunctionApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `FunctionApp` | The FunctionApp AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_predicate_app(self, node: PredicateApp) -> Set[Variable]`

Handles visitation of a PredicateApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `PredicateApp` | The PredicateApp AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_equality(self, node: Equality) -> Set[Variable]`

Handles visitation of a Equality node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Equality` | The Equality AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_not(self, node: Not) -> Set[Variable]`

Handles visitation of a Not node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Not` | The Not AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_and(self, node: And) -> Set[Variable]`

Handles visitation of a And node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `And` | The And AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_or(self, node: Or) -> Set[Variable]`

Handles visitation of a Or node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Or` | The Or AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_implies(self, node: Implies) -> Set[Variable]`

Handles visitation of a Implies node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Implies` | The Implies AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_iff(self, node: Iff) -> Set[Variable]`

Handles visitation of a Iff node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Iff` | The Iff AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_forall(self, node: Forall) -> Set[Variable]`

Handles visitation of a Forall node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Forall` | The Forall AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_exists(self, node: Exists) -> Set[Variable]`

Handles visitation of a Exists node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Exists` | The Exists AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_forall_pred(self, node: ForallPred) -> Set[Variable]`

Handles visitation of a ForallPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallPred` | The ForallPred AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_exists_pred(self, node: ExistsPred) -> Set[Variable]`

Handles visitation of a ExistsPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsPred` | The ExistsPred AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_forall_func(self, node: ForallFunc) -> Set[Variable]`

Handles visitation of a ForallFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallFunc` | The ForallFunc AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

##### `def visit_exists_func(self, node: ExistsFunc) -> Set[Variable]`

Handles visitation of a ExistsFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsFunc` | The ExistsFunc AST node being visited. |

**Returns:** `Set[Variable]` — Result of visiting this node.

### `class SubstitutionTransformer(ASTTransformer)`

Applies variable substitutions to terms and formulas with capture avoidance.

#### Methods

##### `def __init__(self, mapping: Dict[Variable, Term]) -> None`

Initializes the substitution transformer with a variable to term mapping.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `mapping` | `Dict[Variable, Term]` | Dictionary mapping variables to their replacement terms. |

**Returns:** `None`

##### `def visit_variable(self, node: Variable) -> Term`

Handles visitation of a Variable node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Variable` | The Variable AST node being visited. |

**Returns:** `Term` — Result of visiting this node.

##### `def visit_forall(self, node: Forall) -> Formula`

Handles visitation of a Forall node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Forall` | The Forall AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

##### `def visit_exists(self, node: Exists) -> Formula`

Handles visitation of a Exists node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Exists` | The Exists AST node being visited. |

**Returns:** `Formula` — Result of visiting this node.

### `class ExportVisitor(ASTVisitor[str])`

Translates AST to string in various notations ('infix', 'prefix', 'latex').

#### Methods

##### `def __init__(self, notation: str) -> None`

Initializes ExportVisitor with string notation.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `notation` | `str` | Output notation, one of 'infix', 'prefix', or 'latex'. |

**Returns:** `None`

**Raises:**
- `ValueError`: If notation is not one of the supported values.

##### `def visit_variable(self, node: Variable) -> str`

Handles visitation of a Variable node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Variable` | The Variable AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_constant(self, node: Constant) -> str`

Handles visitation of a Constant node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Constant` | The Constant AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_function_app(self, node: FunctionApp) -> str`

Handles visitation of a FunctionApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `FunctionApp` | The FunctionApp AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_predicate_app(self, node: PredicateApp) -> str`

Handles visitation of a PredicateApp node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `PredicateApp` | The PredicateApp AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_equality(self, node: Equality) -> str`

Handles visitation of a Equality node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Equality` | The Equality AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_not(self, node: Not) -> str`

Handles visitation of a Not node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Not` | The Not AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_and(self, node: And) -> str`

Handles visitation of a And node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `And` | The And AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_or(self, node: Or) -> str`

Handles visitation of a Or node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Or` | The Or AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_implies(self, node: Implies) -> str`

Handles visitation of a Implies node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Implies` | The Implies AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_iff(self, node: Iff) -> str`

Handles visitation of a Iff node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Iff` | The Iff AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_forall(self, node: Forall) -> str`

Handles visitation of a Forall node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Forall` | The Forall AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_exists(self, node: Exists) -> str`

Handles visitation of a Exists node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `Exists` | The Exists AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_forall_pred(self, node: ForallPred) -> str`

Handles visitation of a ForallPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallPred` | The ForallPred AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_exists_pred(self, node: ExistsPred) -> str`

Handles visitation of a ExistsPred node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsPred` | The ExistsPred AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_forall_func(self, node: ForallFunc) -> str`

Handles visitation of a ForallFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ForallFunc` | The ForallFunc AST node being visited. |

**Returns:** `str` — Result of visiting this node.

##### `def visit_exists_func(self, node: ExistsFunc) -> str`

Handles visitation of a ExistsFunc node.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `node` | `ExistsFunc` | The ExistsFunc AST node being visited. |

**Returns:** `str` — Result of visiting this node.


---
