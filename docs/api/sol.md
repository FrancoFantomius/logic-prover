# API Reference: `sol`

# Module `solver.sol.ast_ext`

AST extensions for Second-Order Logic (predicate/function variables and quantifiers).

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class PredicateVariable`

Quantifiable predicate variable P_index with a fixed arity.

#### Methods

##### `def name(self) -> str`

**Returns:** `str`

### `class FunctionVariable`

Quantifiable function variable F_index with argument sorts and return sort.

#### Methods

##### `def name(self) -> str`

**Returns:** `str`

### `class ForallPred(Formula)`

Universal quantification over a predicate variable: ∀P. φ

### `class ExistsPred(Formula)`

Existential quantification over a predicate variable: ∃P. φ

### `class ForallFunc(Formula)`

Universal quantification over a function variable: ∀F. φ

### `class ExistsFunc(Formula)`

Existential quantification over a function variable: ∃F. φ

---

## Functions

### `def free_predicate_variables(node: Union[Formula, Term]) -> Set[PredicateVariable]`

Returns all unquantified PredicateVariable instances in a formula or term.

**Returns:** `Set[PredicateVariable]`

### `def bound_predicate_variables(node: Union[Formula, Term]) -> Set[PredicateVariable]`

Returns all quantified PredicateVariable instances in a formula.

**Returns:** `Set[PredicateVariable]`

### `def free_function_variables(node: Union[Formula, Term]) -> Set[FunctionVariable]`

Returns all unquantified FunctionVariable instances in a formula or term.

**Returns:** `Set[FunctionVariable]`

### `def bound_function_variables(node: Union[Formula, Term]) -> Set[FunctionVariable]`

Returns all quantified FunctionVariable instances in a formula.

**Returns:** `Set[FunctionVariable]`


---

# Module `solver.sol.kb_ext`

Second-Order Logic knowledge base extensions (induction schemas, comprehension axioms).

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def get_sol_axioms() -> List[Tuple[str, Formula]]`

Returns the core Second-Order Logic axioms and schemas: 1. Second-Order Comprehension Schema (unary and binary predicate variants) 2. Second-Order Peano Induction Principle 3. Predicate Extensionality Principle 4. Function Extensionality Principle

**Returns:** `List[Tuple[str, Formula]]`

### `def instantiate_comprehension(pred_var: PredicateVariable, params: Tuple[Variable, ...], body: Formula) -> Formula`

Constructs an explicit instance of the Second-Order Comprehension Schema for a given body formula φ(x_1, ..., x_k): ∃P. ∀x_1 ... ∀x_k. (P(x_1, ..., x_k) ⇔ φ(x_1, ..., x_k))

**Returns:** `Formula`

### `def instantiate_induction(property_formula: Formula, bound_var: Variable, zero_term: Optional[Term], succ_func_name: str) -> Formula`

Instantiates the Second-Order Peano Induction Principle for a specific property formula φ(n): (φ(0) ∧ ∀n. (φ(n) ⇒ φ(S(n)))) ⇒ ∀n. φ(n)

**Returns:** `Formula`


---

# Module `solver.sol.substitutions_ext`

Higher-order pattern unification and beta-reduction algorithms for SOL.

---

## Table of Contents
- [Functions](#functions)

---

## Functions

### `def is_ho_pattern(app: Union[PredicateApp, FunctionApp], bound_vars: Optional[Set[Variable]]) -> bool`

Checks if an application node is a valid Miller-Pfenning higher-order pattern: 1. The head symbol is a PredicateVariable or FunctionVariable. 2. All argument expressions are individual Variable instances. 3. The argument variables are pairwise distinct. 4. All argument variables belong to the current bound_vars scope (if specified).

**Returns:** `bool`

### `def beta_reduce_predicate(template: Formula, params: Tuple[Variable, ...], args: Tuple[Term, ...]) -> Formula`

Applies arguments to a predicate formula template φ(x_1, ..., x_k). Performs parameter substitution [x_i ↦ t_i] with full capture avoidance.

**Returns:** `Formula`

### `def beta_reduce_function(template: Term, params: Tuple[Variable, ...], args: Tuple[Term, ...]) -> Term`

Applies arguments to a function term template t(x_1, ..., x_k). Performs parameter substitution [x_i ↦ t_i] with full capture avoidance.

**Returns:** `Term`

### `def substitute_predicate(formula: Formula, mapping: Dict[PredicateVariable, Union[Formula, Tuple[Tuple[Variable, ...], Formula]]], params_mapping: Optional[Dict[PredicateVariable, Tuple[Variable, ...]]]) -> Formula`

Substitutes occurrences of PredicateApp(pred=P, args=(t1, ..., tk)) where P in mapping with the corresponding formula template φ, performing beta-reduction [x_i ↦ t_i].

**Returns:** `Formula`

### `def substitute_function(node: Union[Formula, Term], mapping: Dict[FunctionVariable, Union[Term, Tuple[Tuple[Variable, ...], Term]]], params_mapping: Optional[Dict[FunctionVariable, Tuple[Variable, ...]]]) -> Union[Formula, Term]`

Substitutes occurrences of FunctionApp(func=F, args=(t1, ..., tk)) where F in mapping with the corresponding term template t, performing beta-reduction [x_i ↦ t_i].

**Returns:** `Union[Formula, Term]`

### `def apply_subst(node: Union[Formula, Term], subst: Dict[Any, Any]) -> Union[Formula, Term]`

Applies a combined substitution mapping (Variable, PredicateVariable, FunctionVariable).

**Returns:** `Union[Formula, Term]`

### `def compose_subst(subst1: Dict[Any, Any], subst2: Dict[Any, Any]) -> Dict[Any, Any]`

Composes two substitution dictionaries: subst1 o subst2.

**Returns:** `Dict[Any, Any]`

### `def ho_pattern_unify(node1: Union[Formula, Term], node2: Union[Formula, Term], bound_vars: Optional[Set[Variable]]) -> Optional[Dict[Union[PredicateVariable, FunctionVariable, Variable], Any]]`

Miller-Pfenning Higher-Order Pattern Unification algorithm. Restricted to higher-order patterns: P(x_1, ..., x_k) where x_i are distinct bound variables.

Returns a unified substitution dictionary mapping:
- PredicateVariable -> Tuple[Tuple[Variable, ...], Formula] (params, formula_template)
- FunctionVariable -> Tuple[Tuple[Variable, ...], Term] (params, term_template)
- Variable -> Term

Returns None if unification fails or nodes are not in pattern form.

**Returns:** `Optional[Dict[Union[PredicateVariable, FunctionVariable, Variable], Any]]`


---
