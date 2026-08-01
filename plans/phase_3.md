# Phase 3 — Visitor Framework & Parser

**Goal**: Establish a generic AST traversal framework to eliminate boilerplate recursive logic, and implement a robust lexer, parser, and string serializer for converting formal logic text expressions to AST objects and vice-versa.

**Deliverables**:
- `solver/core/visitors.py` — Generic visitor and transformer base classes and built-in visitors.
- `solver/core/parser.py` — Lexer (`tokenize`), Pratt/Recursive Descent Parser (`parse_formula`, `parse_term`), and serializer (`to_string`).
- `tests/test_visitors.py` — Unit tests for generic AST traversal, dispatching, and transformations.
- `tests/test_parser.py` — Unit tests for lexing, parsing precedence, syntax error rejection, and property-based round-trip tests.

**Acceptance Criteria**:
- Visitor framework correctly dispatches to all 12 AST node types without missing branches or fallback errors.
- Parser round-trips: `parse_formula(to_string(f, notation="infix"), signature) == f` for all valid formulas.
- Parser rejects malformed syntax with clear `ParseError` messages containing line and column numbers.

**Dependencies**: Phase 1 (`solver/core/ast.py`, `solver/core/sorts.py`, `solver/core/signature.py`), Phase 2 (`solver/core/validator.py`, `solver/core/exceptions.py`).

---

## 1. Executive Overview & Architecture

Phase 3 provides the dual interface between human-readable text representations and internal AST data structures, as well as the engine for structural AST traversals across the `solver` codebase.

```
                   +-----------------------+
                   |   Input Text String   |
                   +-----------+-----------+
                               |
                               v
                   +-----------------------+
                   |  tokenize(text)       |  (Lexer: List[Token])
                   +-----------+-----------+
                               |
                               v
                   +-----------------------+
                   |  parse_formula /      |  (Pratt Parser +
                   |  parse_term           |   Signature Symbol Resolution)
                   +-----------+-----------+
                               |
                               v
                   +-----------------------+
                   |    AST (Term/Formula) |
                   +-----------+-----------+
                               |
            +------------------+------------------+
            |                                     |
            v                                     v
+-----------------------+             +-----------------------+
|   ASTVisitor[T]       |             |   to_string(node)     |
| (Depth, Size, Vars,   |             | (AST -> Text Infix /  |
|  Transformers, etc.)  |             |  Prefix / LaTeX)      |
+-----------------------+             +-----------------------+
```

### Key Architectural Objectives:
1. **Generic Traversal (`visitors.py`)**: Abstract recursive tree traversal out of individual AST nodes and function utilities. By inheriting from `ASTVisitor[T]` or `ASTTransformer`, new operations (e.g., scoring, rewriting, LEAN code export) can be implemented without adding methods to `ast.py` classes.
2. **Lexer & Pratt Parser (`parser.py`)**: Implement tokenization with line/column tracking, followed by a Pratt parsing algorithm for expressions with operator precedence (`~`, `&`, `|`, `=>`, `<=>`), equality (`=`), and scoped quantifiers (`forall`, `exists`).
3. **Symbol Resolution against Signature**: Parse terms and predicates while validating symbol declarations, arities, and argument sorts against a `Signature` context. Undeclared symbols or arity mismatches immediately raise informative `ParseError` exceptions.
4. **Bi-directional Round-Trip**: Ensure exact AST reconstruction via `parse_formula(to_string(f), sig) == f` for property-based testing and canonical string serialization.

---

## 2. Prerequisites

The following modules must be fully implemented and verified before starting Phase 3:

| Module | Core Dependencies Required in Phase 3 |
|---|---|
| `solver/core/ast.py` | `Term`, `Variable`, `Constant`, `FunctionApp`, `VariableKind`, `Formula`, `PredicateApp`, `Equality`, `Not`, `And`, `Or`, `Implies`, `Iff`, `Forall`, `Exists` |
| `solver/core/sorts.py` | `Sort`, `PrimitiveSort`, `ParameterizedSort`, `Ind`, `Nat`, `Bool`, `is_compatible` |
| `solver/core/signature.py` | `Signature`, `FunctionDecl`, `PredicateDecl`, `lookup_function`, `lookup_predicate` |
| `solver/core/exceptions.py` | `SolverError`, `ParseError` |
| `solver/core/validator.py` | `ValidationError`, `is_well_formed` |

---

## 3. Files to Create / Modify

```
solver/
├── solver/
│   └── core/
│       ├── visitors.py    # AST Visitor & Transformer framework + built-in visitors
│       └── parser.py      # Lexer, Pratt parser, and to_string serializer
└── tests/
    ├── test_visitors.py   # Unit tests for visitor pattern and traversals
    └── test_parser.py     # Unit and property-based tests for lexing and parsing
```

---

## 4. Detailed Implementation Guide

### 4.1 Module: `solver/core/visitors.py` (Section 3.5)

This module implements the generic visitor and transformer patterns for structural AST traversal, as well as concrete visitors for common operations (`DepthVisitor`, `SizeVisitor`, `FreeVariableCollector`, `SubstitutionTransformer`, `ExportVisitor`).

#### 4.1.1 Abstract Visitor Classes

##### `ASTVisitor[T]` (Generic Abstract Base Class)
Generic over return type `T`. Defines visit dispatch methods for all 12 AST node types.

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union, Set, Dict, Optional, List
from solver.core.ast import (
    Term, Variable, Constant, FunctionApp,
    Formula, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)

T = TypeVar("T")

class ASTVisitor(ABC, Generic[T]):
    """Generic visitor base class for AST traversal."""

    def visit(self, node: Union[Term, Formula]) -> T:
        """Master dispatch method targeting specific visit_* methods."""
        if isinstance(node, Variable):
            return self.visit_variable(node)
        elif isinstance(node, Constant):
            return self.visit_constant(node)
        elif isinstance(node, FunctionApp):
            return self.visit_function_app(node)
        elif isinstance(node, PredicateApp):
            return self.visit_predicate_app(node)
        elif isinstance(node, Equality):
            return self.visit_equality(node)
        elif isinstance(node, Not):
            return self.visit_not(node)
        elif isinstance(node, And):
            return self.visit_and(node)
        elif isinstance(node, Or):
            return self.visit_or(node)
        elif isinstance(node, Implies):
            return self.visit_implies(node)
        elif isinstance(node, Iff):
            return self.visit_iff(node)
        elif isinstance(node, Forall):
            return self.visit_forall(node)
        elif isinstance(node, Exists):
            return self.visit_exists(node)
        else:
            raise TypeError(f"Unsupported AST node type: {type(node).__name__}")

    @abstractmethod
    def visit_variable(self, node: Variable) -> T:
        pass

    @abstractmethod
    def visit_constant(self, node: Constant) -> T:
        pass

    @abstractmethod
    def visit_function_app(self, node: FunctionApp) -> T:
        pass

    @abstractmethod
    def visit_predicate_app(self, node: PredicateApp) -> T:
        pass

    @abstractmethod
    def visit_equality(self, node: Equality) -> T:
        pass

    @abstractmethod
    def visit_not(self, node: Not) -> T:
        pass

    @abstractmethod
    def visit_and(self, node: And) -> T:
        pass

    @abstractmethod
    def visit_or(self, node: Or) -> T:
        pass

    @abstractmethod
    def visit_implies(self, node: Implies) -> T:
        pass

    @abstractmethod
    def visit_iff(self, node: Iff) -> T:
        pass

    @abstractmethod
    def visit_forall(self, node: Forall) -> T:
        pass

    @abstractmethod
    def visit_exists(self, node: Exists) -> T:
        pass
```

##### `ASTTransformer` (Base Class for Tree Transformation)
Specialization of `ASTVisitor[Union[Term, Formula]]` where default implementation returns an identical or transformed node. Subclasses override specific node handlers.

```python
class ASTTransformer(ASTVisitor[Union[Term, Formula]]):
    """Visitor that returns transformed AST nodes (bottom-up structural transformation)."""

    def visit_variable(self, node: Variable) -> Term:
        return node

    def visit_constant(self, node: Constant) -> Term:
        return node

    def visit_function_app(self, node: FunctionApp) -> Term:
        new_args = tuple(self.visit(arg) for arg in node.args)
        if all(new_arg is orig for new_arg, orig in zip(new_args, node.args)):
            return node
        return FunctionApp(func=node.func, arity=node.arity, args=new_args, return_sort=node.return_sort)

    def visit_predicate_app(self, node: PredicateApp) -> Formula:
        new_args = tuple(self.visit(arg) for arg in node.args)
        if all(new_arg is orig for new_arg, orig in zip(new_args, node.args)):
            return node
        return PredicateApp(pred=node.pred, arity=node.arity, args=new_args)

    def visit_equality(self, node: Equality) -> Formula:
        new_left = self.visit(node.left)
        new_right = self.visit(node.right)
        if new_left is node.left and new_right is node.right:
            return node
        return Equality(left=new_left, right=new_right)

    def visit_not(self, node: Not) -> Formula:
        new_op = self.visit(node.operand)
        if new_op is node.operand:
            return node
        return Not(operand=new_op)

    def visit_and(self, node: And) -> Formula:
        new_l = self.visit(node.left)
        new_r = self.visit(node.right)
        if new_l is node.left and new_r is node.right:
            return node
        return And(left=new_l, right=new_r)

    def visit_or(self, node: Or) -> Formula:
        new_l = self.visit(node.left)
        new_r = self.visit(node.right)
        if new_l is node.left and new_r is node.right:
            return node
        return Or(left=new_l, right=new_r)

    def visit_implies(self, node: Implies) -> Formula:
        new_l = self.visit(node.left)
        new_r = self.visit(node.right)
        if new_l is node.left and new_r is node.right:
            return node
        return Implies(left=new_l, right=new_r)

    def visit_iff(self, node: Iff) -> Formula:
        new_l = self.visit(node.left)
        new_r = self.visit(node.right)
        if new_l is node.left and new_r is node.right:
            return node
        return Iff(left=new_l, right=new_r)

    def visit_forall(self, node: Forall) -> Formula:
        new_var = self.visit(node.variable)
        new_body = self.visit(node.body)
        if new_var is node.variable and new_body is node.body:
            return node
        return Forall(variable=new_var, body=new_body)

    def visit_exists(self, node: Exists) -> Formula:
        new_var = self.visit(node.variable)
        new_body = self.visit(node.body)
        if new_var is node.variable and new_body is node.body:
            return node
        return Exists(variable=new_var, body=new_body)
```

#### 4.1.2 Concrete Visitor Implementations

```python
class DepthVisitor(ASTVisitor[int]):
    """Computes the maximum depth of an AST tree."""

    def visit_variable(self, node: Variable) -> int:
        return 1

    def visit_constant(self, node: Constant) -> int:
        return 1

    def visit_function_app(self, node: FunctionApp) -> int:
        if not node.args:
            return 1
        return 1 + max(self.visit(arg) for arg in node.args)

    def visit_predicate_app(self, node: PredicateApp) -> int:
        if not node.args:
            return 1
        return 1 + max(self.visit(arg) for arg in node.args)

    def visit_equality(self, node: Equality) -> int:
        return 1 + max(self.visit(node.left), self.visit(node.right))

    def visit_not(self, node: Not) -> int:
        return 1 + self.visit(node.operand)

    def visit_and(self, node: And) -> int:
        return 1 + max(self.visit(node.left), self.visit(node.right))

    def visit_or(self, node: Or) -> int:
        return 1 + max(self.visit(node.left), self.visit(node.right))

    def visit_implies(self, node: Implies) -> int:
        return 1 + max(self.visit(node.left), self.visit(node.right))

    def visit_iff(self, node: Iff) -> int:
        return 1 + max(self.visit(node.left), self.visit(node.right))

    def visit_forall(self, node: Forall) -> int:
        return 1 + self.visit(node.body)

    def visit_exists(self, node: Exists) -> int:
        return 1 + self.visit(node.body)


class SizeVisitor(ASTVisitor[int]):
    """Computes the total number of nodes in an AST tree."""

    def visit_variable(self, node: Variable) -> int:
        return 1

    def visit_constant(self, node: Constant) -> int:
        return 1

    def visit_function_app(self, node: FunctionApp) -> int:
        return 1 + sum(self.visit(arg) for arg in node.args)

    def visit_predicate_app(self, node: PredicateApp) -> int:
        return 1 + sum(self.visit(arg) for arg in node.args)

    def visit_equality(self, node: Equality) -> int:
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_not(self, node: Not) -> int:
        return 1 + self.visit(node.operand)

    def visit_and(self, node: And) -> int:
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_or(self, node: Or) -> int:
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_implies(self, node: Implies) -> int:
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_iff(self, node: Iff) -> int:
        return 1 + self.visit(node.left) + self.visit(node.right)

    def visit_forall(self, node: Forall) -> int:
        return 1 + self.visit(node.body)

    def visit_exists(self, node: Exists) -> int:
        return 1 + self.visit(node.body)


class FreeVariableCollector(ASTVisitor[Set[Variable]]):
    """Collects all free individual variables in a term or formula."""

    def visit_variable(self, node: Variable) -> Set[Variable]:
        return {node}

    def visit_constant(self, node: Constant) -> Set[Variable]:
        return set()

    def visit_function_app(self, node: FunctionApp) -> Set[Variable]:
        res = set()
        for arg in node.args:
            res.update(self.visit(arg))
        return res

    def visit_predicate_app(self, node: PredicateApp) -> Set[Variable]:
        res = set()
        for arg in node.args:
            res.update(self.visit(arg))
        return res

    def visit_equality(self, node: Equality) -> Set[Variable]:
        return self.visit(node.left) | self.visit(node.right)

    def visit_not(self, node: Not) -> Set[Variable]:
        return self.visit(node.operand)

    def visit_and(self, node: And) -> Set[Variable]:
        return self.visit(node.left) | self.visit(node.right)

    def visit_or(self, node: Or) -> Set[Variable]:
        return self.visit(node.left) | self.visit(node.right)

    def visit_implies(self, node: Implies) -> Set[Variable]:
        return self.visit(node.left) | self.visit(node.right)

    def visit_iff(self, node: Iff) -> Set[Variable]:
        return self.visit(node.left) | self.visit(node.right)

    def visit_forall(self, node: Forall) -> Set[Variable]:
        return self.visit(node.body) - {node.variable}

    def visit_exists(self, node: Exists) -> Set[Variable]:
        return self.visit(node.body) - {node.variable}


class SubstitutionTransformer(ASTTransformer):
    """Applies variable substitutions to terms and formulas with capture avoidance."""

    def __init__(self, mapping: Dict[Variable, Term]):
        self.mapping = mapping

    def visit_variable(self, node: Variable) -> Term:
        return self.mapping.get(node, node)

    def visit_forall(self, node: Forall) -> Formula:
        # Check if bound variable is captured by free vars in target terms
        bound_var = node.variable
        replacement_free_vars = set()
        for v, t in self.mapping.items():
            if v != bound_var:
                replacement_free_vars.update(FreeVariableCollector().visit(t))

        if bound_var in replacement_free_vars:
            # Rename bound variable to avoid variable capture
            max_idx = max((v.id for v in FreeVariableCollector().visit(node.body) | replacement_free_vars), default=0) + 1
            fresh_var = Variable(id=max_idx, sort=bound_var.sort, kind=bound_var.kind)
            renamed_body = SubstitutionTransformer({bound_var: fresh_var}).visit(node.body)
            new_body = self.visit(renamed_body)
            return Forall(variable=fresh_var, body=new_body)
        else:
            # Filter out bound_var from active mapping for inner body
            inner_mapping = {v: t for v, t in self.mapping.items() if v != bound_var}
            new_body = SubstitutionTransformer(inner_mapping).visit(node.body)
            return Forall(variable=bound_var, body=new_body)

    def visit_exists(self, node: Exists) -> Formula:
        bound_var = node.variable
        replacement_free_vars = set()
        for v, t in self.mapping.items():
            if v != bound_var:
                replacement_free_vars.update(FreeVariableCollector().visit(t))

        if bound_var in replacement_free_vars:
            max_idx = max((v.id for v in FreeVariableCollector().visit(node.body) | replacement_free_vars), default=0) + 1
            fresh_var = Variable(id=max_idx, sort=bound_var.sort, kind=bound_var.kind)
            renamed_body = SubstitutionTransformer({bound_var: fresh_var}).visit(node.body)
            new_body = self.visit(renamed_body)
            return Exists(variable=fresh_var, body=new_body)
        else:
            inner_mapping = {v: t for v, t in self.mapping.items() if v != bound_var}
            new_body = SubstitutionTransformer(inner_mapping).visit(node.body)
            return Exists(variable=bound_var, body=new_body)


class ExportVisitor(ASTVisitor[str]):
    """Translates AST to string in various notations ('infix', 'prefix', 'latex')."""

    def __init__(self, notation: str = "infix"):
        if notation not in ("infix", "prefix", "latex"):
            raise ValueError(f"Unsupported notation: {notation}")
        self.notation = notation

    def visit_variable(self, node: Variable) -> str:
        if self.notation == "latex":
            return f"v_{{{node.id}}}"
        return f"v{node.id}"

    def visit_constant(self, node: Constant) -> str:
        return node.name

    def visit_function_app(self, node: FunctionApp) -> str:
        args_str = ", ".join(self.visit(arg) for arg in node.args)
        if self.notation == "prefix":
            return f"({node.func} {args_str})"
        return f"{node.func}({args_str})"

    def visit_predicate_app(self, node: PredicateApp) -> str:
        if not node.args:
            return node.pred
        args_str = ", ".join(self.visit(arg) for arg in node.args)
        if self.notation == "prefix":
            return f"({node.pred} {args_str})"
        return f"{node.pred}({args_str})"

    def visit_equality(self, node: Equality) -> str:
        left_str = self.visit(node.left)
        right_str = self.visit(node.right)
        if self.notation == "prefix":
            return f"(= {left_str} {right_str})"
        return f"{left_str} = {right_str}"

    def visit_not(self, node: Not) -> str:
        op_str = self.visit(node.operand)
        if self.notation == "prefix":
            return f"(not {op_str})"
        elif self.notation == "latex":
            return f"\\neg ({op_str})" if isinstance(node.operand, (And, Or, Implies, Iff)) else f"\\neg {op_str}"
        return f"~({op_str})" if isinstance(node.operand, (And, Or, Implies, Iff)) else f"~{op_str}"

    def visit_and(self, node: And) -> str:
        l_str = self.visit(node.left)
        r_str = self.visit(node.right)
        if self.notation == "prefix":
            return f"(and {l_str} {r_str})"
        elif self.notation == "latex":
            return f"({l_str} \\land {r_str})"
        return f"({l_str} & {r_str})"

    def visit_or(self, node: Or) -> str:
        l_str = self.visit(node.left)
        r_str = self.visit(node.right)
        if self.notation == "prefix":
            return f"(or {l_str} {r_str})"
        elif self.notation == "latex":
            return f"({l_str} \\lor {r_str})"
        return f"({l_str} | {r_str})"

    def visit_implies(self, node: Implies) -> str:
        l_str = self.visit(node.left)
        r_str = self.visit(node.right)
        if self.notation == "prefix":
            return f"(=> {l_str} {r_str})"
        elif self.notation == "latex":
            return f"({l_str} \\implies {r_str})"
        return f"({l_str} => {r_str})"

    def visit_iff(self, node: Iff) -> str:
        l_str = self.visit(node.left)
        r_str = self.visit(node.right)
        if self.notation == "prefix":
            return f"(<=> {l_str} {r_str})"
        elif self.notation == "latex":
            return f"({l_str} \\iff {r_str})"
        return f"({l_str} <=> {r_str})"

    def visit_forall(self, node: Forall) -> str:
        v_str = self.visit(node.variable)
        b_str = self.visit(node.body)
        sort_str = node.variable.sort.name if hasattr(node.variable.sort, 'name') else str(node.variable.sort)
        if self.notation == "prefix":
            return f"(forall ({v_str} : {sort_str}) {b_str})"
        elif self.notation == "latex":
            return f"\\forall {v_str} : {sort_str}, {b_str}"
        return f"forall {v_str} : {sort_str}, {b_str}"

    def visit_exists(self, node: Exists) -> str:
        v_str = self.visit(node.variable)
        b_str = self.visit(node.body)
        sort_str = node.variable.sort.name if hasattr(node.variable.sort, 'name') else str(node.variable.sort)
        if self.notation == "prefix":
            return f"(exists ({v_str} : {sort_str}) {b_str})"
        elif self.notation == "latex":
            return f"\\exists {v_str} : {sort_str}, {b_str}"
        return f"exists {v_str} : {sort_str}, {b_str}"
```

---

### 4.2 Module: `solver/core/parser.py` (Section 3.7)

This module handles text-to-AST parsing (using Lexer + Pratt Parser) and AST-to-text formatting (`to_string`).

#### 4.2.1 Token Types & Lexer (`tokenize`)

##### Token Definition
```python
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Union
from solver.core.exceptions import ParseError
from solver.core.ast import (
    Term, Variable, Constant, FunctionApp, VariableKind,
    Formula, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from solver.core.sorts import Sort, PrimitiveSort, ParameterizedSort, Ind, Nat, Bool
from solver.core.signature import Signature

class TokenType(Enum):
    QUANTIFIER = auto()  # forall, exists, ∀, ∃
    VARIABLE = auto()    # v0, v1, v2, ...
    IDENTIFIER = auto()  # P, Q, f, c, Ind, Nat, etc.
    COLON = auto()       # :
    COMMA = auto()       # ,
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    NOT = auto()         # ~, not, ¬
    AND = auto()         # &, and, ∧
    OR = auto()          # |, or, ∨
    IMPLIES = auto()     # =>, implies, →
    IFF = auto()         # <=>, iff, ↔
    EQUAL = auto()       # =
    EOF = auto()

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    position: int
    line: int
    col: int
```

##### Lexer Algorithm (`tokenize`)
```python
import re

TOKEN_PATTERNS = [
    (r"\s+", None),  # Skip whitespace
    (r"\b(forall|exists|∀|∃)\b|∀|∃", TokenType.QUANTIFIER),
    (r"\bv\d+\b", TokenType.VARIABLE),
    (r"<=>|iff|↔", TokenType.IFF),
    (r"=>|implies|→", TokenType.IMPLIES),
    (r"~|not|¬", TokenType.NOT),
    (r"&|and|∧", TokenType.AND),
    (r"\||or|∨", TokenType.OR),
    (r"=", TokenType.EQUAL),
    (r":", TokenType.COLON),
    (r",", TokenType.COMMA),
    (r"\(", TokenType.LPAREN),
    (r"\)", TokenType.RPAREN),
    (r"[a-zA-Z_][a-zA-Z0-9_]*", TokenType.IDENTIFIER),
]

def tokenize(text: str) -> List[Token]:
    """Scans text into a list of Token objects with line and column tracking.
    Raises ParseError on unrecognized character sequences.
    """
    tokens: List[Token] = []
    pos = 0
    line = 1
    col = 1
    length = len(text)

    while pos < length:
        match = None
        for pattern, token_type in TOKEN_PATTERNS:
            regex = re.compile(pattern)
            match = regex.match(text, pos)
            if match:
                val = match.group(0)
                if token_type is not None:
                    tokens.append(Token(type=token_type, value=val, position=pos, line=line, col=col))
                
                # Advance line and col numbers
                newlines = val.count("\n")
                if newlines > 0:
                    line += newlines
                    col = len(val) - val.rfind("\n")
                else:
                    col += len(val)
                pos = match.end()
                break

        if not match:
            raise ParseError(f"Unexpected character '{text[pos]}' at line {line}, col {col} (pos {pos})")

    tokens.append(Token(type=TokenType.EOF, value="", position=length, line=line, col=col))
    return tokens
```

---

#### 4.2.2 Grammar & Operator Precedence

##### Formal EBNF Grammar
```ebnf
formula          ::= quantifier_expr | iff_expr ;

quantifier_expr  ::= QUANTIFIER var_decl "," formula ;
var_decl         ::= VARIABLE [ ":" sort_expr ] ;
sort_expr        ::= IDENTIFIER [ "(" sort_expr ("," sort_expr)* ")" ] ;

iff_expr         ::= implies_expr ( IFF implies_expr )* ;
implies_expr     ::= or_expr [ IMPLIES implies_expr ] ; (* Right-associative *)
or_expr          ::= and_expr ( OR and_expr )* ;
and_expr         ::= not_expr ( AND not_expr )* ;
not_expr         ::= NOT not_expr | atomic_formula ;

atomic_formula   ::= "(" formula ")"
                   | term EQUAL term
                   | IDENTIFIER "(" [ term ("," term)* ] ")"
                   | IDENTIFIER ; (* nullary predicate / proposition *)

term             ::= VARIABLE
                   | IDENTIFIER "(" term ("," term)* ")"
                   | IDENTIFIER ; (* constant or nullary function *)
```

##### Operator Precedence Binding Powers (Pratt Parser Table)
Higher binding power indicates tighter precedence.

| Precedence Rank | Operators | Associativity | Description |
|---|---|---|---|
| 0 (Lowest) | `forall`, `exists` | Scoped Right | Quantifier expressions |
| 10 | `<=>`, `iff`, `↔` | Left-associative | Logical Equivalence |
| 20 | `=>`, `implies`, `→` | Right-associative | Implication |
| 30 | `\|`, `or`, `∨` | Left-associative | Disjunction |
| 40 | `&`, `and`, `∧` | Left-associative | Conjunction |
| 50 | `~`, `not`, `¬` | Prefix Unary | Negation |
| 60 (Highest)| `=`, `(`, `)` | N/A | Atomic Equality / Function App / Grouping |

---

#### 4.2.3 Parser Engine Class (`_Parser`)

```python
class _Parser:
    """Internal Pratt parser state machine."""

    def __init__(self, tokens: List[Token], signature: Signature):
        self.tokens = tokens
        self.signature = signature
        self.idx = 0

    def peek(() -> Token:
        return self.tokens[self.idx]

    def consume(self, expected_type: Optional[TokenType] = None) -> Token:
        tok = self.peek()
        if expected_type is not None and tok.type != expected_type:
            raise ParseError(
                f"Expected token type '{expected_type.name}' but got '{tok.type.name}' ({tok.value!r}) "
                f"at line {tok.line}, col {tok.col}"
            )
        self.idx += 1
        return tok

    def parse_formula(self, min_prec: int = 0) -> Formula:
        tok = self.peek()

        # Handle quantifiers (lowest precedence, scoped)
        if tok.type == TokenType.QUANTIFIER:
            return self._parse_quantifier()

        # Prefix operator: NOT
        if tok.type == TokenType.NOT:
            self.consume(TokenType.NOT)
            operand = self.parse_formula(min_prec=50)
            lhs = Not(operand=operand)
        elif tok.type == TokenType.LPAREN:
            # Check if this is a parenthesized formula or term equality
            saved_idx = self.idx
            self.consume(TokenType.LPAREN)
            try:
                inner_formula = self.parse_formula(min_prec=0)
                if self.peek().type == TokenType.RPAREN:
                    self.consume(TokenType.RPAREN)
                    lhs = inner_formula
                else:
                    # Rollback and try parsing term equality / predicate
                    self.idx = saved_idx
                    lhs = self._parse_atomic_formula()
            except ParseError:
                self.idx = saved_idx
                lhs = self._parse_atomic_formula()
        else:
            lhs = self._parse_atomic_formula()

        # Infix binary operators
        while True:
            cur = self.peek()
            prec = self._infix_precedence(cur.type)
            if prec < min_prec or cur.type == TokenType.EOF:
                break

            if cur.type == TokenType.IFF:
                self.consume(TokenType.IFF)
                rhs = self.parse_formula(min_prec=prec + 1)
                lhs = Iff(left=lhs, right=rhs)
            elif cur.type == TokenType.IMPLIES:
                self.consume(TokenType.IMPLIES)
                # Right associative: min_prec stays prec
                rhs = self.parse_formula(min_prec=prec)
                lhs = Implies(left=lhs, right=rhs)
            elif cur.type == TokenType.OR:
                self.consume(TokenType.OR)
                rhs = self.parse_formula(min_prec=prec + 1)
                lhs = Or(left=lhs, right=rhs)
            elif cur.type == TokenType.AND:
                self.consume(TokenType.AND)
                rhs = self.parse_formula(min_prec=prec + 1)
                lhs = And(left=lhs, right=rhs)
            else:
                break

        return lhs

    def _infix_precedence(self, token_type: TokenType) -> int:
        if token_type == TokenType.IFF:
            return 10
        elif token_type == TokenType.IMPLIES:
            return 20
        elif token_type == TokenType.OR:
            return 30
        elif token_type == TokenType.AND:
            return 40
        return -1

    def _parse_quantifier(self) -> Formula:
        q_tok = self.consume(TokenType.QUANTIFIER)
        var_tok = self.consume(TokenType.VARIABLE)
        var_id = int(var_tok.value[1:])

        sort = Ind
        if self.peek().type == TokenType.COLON:
            self.consume(TokenType.COLON)
            sort = self._parse_sort()

        self.consume(TokenType.COMMA)
        body = self.parse_formula(min_prec=0)

        variable = Variable(id=var_id, sort=sort, kind=VariableKind.INDIVIDUAL)
        if q_tok.value in ("forall", "∀"):
            return Forall(variable=variable, body=body)
        else:
            return Exists(variable=variable, body=body)

    def _parse_sort(self) -> Sort:
        id_tok = self.consume(TokenType.IDENTIFIER)
        sort_name = id_tok.value
        if sort_name == "Ind":
            return Ind
        elif sort_name == "Nat":
            return Nat
        elif sort_name == "Bool":
            return Bool
        
        if self.peek().type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            args = []
            args.append(self._parse_sort())
            while self.peek().type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
                args.append(self._parse_sort())
            self.consume(TokenType.RPAREN)
            return ParameterizedSort(constructor=sort_name, args=tuple(args))
        return PrimitiveSort(name=sort_name)

    def _parse_atomic_formula(self) -> Formula:
        # Save token position for error checking
        tok = self.peek()

        # Try parsing term equality (term = term)
        saved_idx = self.idx
        try:
            left_term = self.parse_term()
            if self.peek().type == TokenType.EQUAL:
                self.consume(TokenType.EQUAL)
                right_term = self.parse_term()
                return Equality(left=left_term, right=right_term)
        except ParseError:
            self.idx = saved_idx

        # Parsing Predicate Application
        if tok.type == TokenType.IDENTIFIER:
            pred_tok = self.consume(TokenType.IDENTIFIER)
            pred_name = pred_tok.value

            pred_decl = self.signature.lookup_predicate(pred_name)
            if pred_decl is None:
                raise ParseError(
                    f"Undeclared predicate symbol '{pred_name}' at line {pred_tok.line}, col {pred_tok.col}"
                )

            args = []
            if pred_decl.arity > 0:
                self.consume(TokenType.LPAREN)
                args.append(self.parse_term())
                while self.peek().type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
                    args.append(self.parse_term())
                self.consume(TokenType.RPAREN)

            if len(args) != pred_decl.arity:
                raise ParseError(
                    f"Predicate '{pred_name}' expects {pred_decl.arity} arguments, but got {len(args)} "
                    f"at line {pred_tok.line}, col {pred_tok.col}"
                )

            return PredicateApp(pred=pred_name, arity=pred_decl.arity, args=tuple(args))

        raise ParseError(f"Unexpected token '{tok.value}' when expecting formula at line {tok.line}, col {tok.col}")

    def parse_term(self) -> Term:
        tok = self.peek()
        if tok.type == TokenType.VARIABLE:
            var_tok = self.consume(TokenType.VARIABLE)
            var_id = int(var_tok.value[1:])
            return Variable(id=var_id, sort=Ind, kind=VariableKind.INDIVIDUAL)
        elif tok.type == TokenType.IDENTIFIER:
            id_tok = self.consume(TokenType.IDENTIFIER)
            name = id_tok.value

            # Constant or Function check in signature
            func_decl = self.signature.lookup_function(name)
            if func_decl is not None:
                args = []
                if func_decl.arity > 0:
                    self.consume(TokenType.LPAREN)
                    args.append(self.parse_term())
                    while self.peek().type == TokenType.COMMA:
                        self.consume(TokenType.COMMA)
                        args.append(self.parse_term())
                    self.consume(TokenType.RPAREN)

                if len(args) != func_decl.arity:
                    raise ParseError(
                        f"Function '{name}' expects {func_decl.arity} arguments, got {len(args)} "
                        f"at line {id_tok.line}, col {id_tok.col}"
                    )
                return FunctionApp(func=name, arity=func_decl.arity, args=tuple(args), return_sort=func_decl.return_sort)

            const_sort = self.signature.constants.get(name)
            if const_sort is not None:
                return Constant(name=name, sort=const_sort)

            # Fallback if symbol is undeclared constant
            raise ParseError(f"Undeclared term symbol '{name}' at line {id_tok.line}, col {id_tok.col}")

        raise ParseError(f"Unexpected token '{tok.value}' when parsing term at line {tok.line}, col {tok.col}")
```

#### 4.2.4 Standalone Parser Functions & Serializer

```python
def parse_formula(text: str, signature: Signature) -> Formula:
    """Parses text into a Formula AST object using signature context.
    Raises ParseError on syntax error or symbol mismatch.
    """
    tokens = tokenize(text)
    parser = _Parser(tokens, signature)
    formula = parser.parse_formula(min_prec=0)
    if parser.peek().type != TokenType.EOF:
        unconsumed = parser.peek()
        raise ParseError(
            f"Unconsumed trailing tokens starting with '{unconsumed.value}' at line {unconsumed.line}, col {unconsumed.col}"
        )
    return formula

def parse_term(text: str, signature: Signature) -> Term:
    """Parses text into a Term AST object using signature context.
    Raises ParseError on syntax error or symbol mismatch.
    """
    tokens = tokenize(text)
    parser = _Parser(tokens, signature)
    term = parser.parse_term()
    if parser.peek().type != TokenType.EOF:
        unconsumed = parser.peek()
        raise ParseError(
            f"Unconsumed trailing tokens starting with '{unconsumed.value}' at line {unconsumed.line}, col {unconsumed.col}"
        )
    return term

def to_string(node: Union[Term, Formula], notation: str = "infix") -> str:
    """Serializes a Term or Formula AST to a string representation.
    Supported notations: 'infix' (default), 'prefix', 'latex'.
    """
    from solver.core.visitors import ExportVisitor
    visitor = ExportVisitor(notation=notation)
    return visitor.visit(node)
```

---

## 5. Step-by-Step Implementation Order

```
Step 1: solver/core/visitors.py
   ├── ASTVisitor[T] generic ABC
   ├── ASTTransformer base class
   ├── DepthVisitor & SizeVisitor
   ├── FreeVariableCollector
   ├── SubstitutionTransformer (with capture avoidance)
   └── ExportVisitor ('infix', 'prefix', 'latex')
         │
         v
Step 2: tests/test_visitors.py
   ├── Test generic dispatching for all 12 AST node types
   ├── Test depth and size calculations on deep nested formulas
   ├── Test free variable extraction on open/closed formulas
   ├── Test variable substitution and capture avoidance
   └── Test ExportVisitor output for all 3 notation modes
         │
         v
Step 3: solver/core/parser.py
   ├── TokenType enum and Token dataclass
   ├── tokenize() lexer with position tracking (line, col)
   ├── _Parser Pratt state machine
   ├── Symbol arity and sort validation against Signature
   ├── parse_formula() and parse_term()
   └── to_string() wrapper
         │
         v
Step 4: tests/test_parser.py
   ├── Lexer unit tests (valid token streams, position tracking)
   ├── Parser operator precedence tests (AND, OR, IMPLIES, IFF, NOT)
   ├── Syntax error rejection tests with ParseError location verification
   ├── Signature symbol resolution & arity mismatch error tests
   └── Property-based round-trip tests: parse_formula(to_string(f), sig) == f
```

---

## 6. Testing Requirements

### 6.1 `tests/test_visitors.py`

#### Test Cases:
1. **Visitor Dispatching**: Subclass `ASTVisitor` with counters for each method; traverse a formula containing all 12 AST node types (`Variable`, `Constant`, `FunctionApp`, `PredicateApp`, `Equality`, `Not`, `And`, `Or`, `Implies`, `Iff`, `Forall`, `Exists`) and verify all counters equal expected node counts.
2. **Depth & Size Calculation**:
   - Depth of single variable $v_0$ is `1`.
   - Depth of $P(v_0) \land Q(v_1)$ is `2`.
   - Size of $P(v_0) \land Q(v_1)$ is `4` (And, PredicateApp(P), Variable(v0), PredicateApp(Q), Variable(v1) -> total 5).
3. **Free Variable Collection**:
   - `FreeVariableCollector` on $v_0 = v_1$ returns `{v0, v1}`.
   - `FreeVariableCollector` on $\forall v_0 : \text{Ind}, (P(v_0) \land Q(v_1))$ returns `{v1}`.
4. **Substitution & Capture Avoidance**:
   - Substitute $\{v_0 \mapsto f(v_1)\}$ in $\forall v_1 : \text{Ind}, P(v_0, v_1)$. The visitor must rename bound $v_1$ to fresh variable $v_2$, yielding $\forall v_2 : \text{Ind}, P(f(v_1), v_2)$.
5. **Export Notation Modes**:
   - Infix format of $\forall v_0 : \text{Ind}, (P(v_0) \implies Q(v_0))$ matches `"forall v0 : Ind, (P(v0) => Q(v0))"`.
   - Prefix format matches `"(forall (v0 : Ind) (=> (P v0) (Q v0)))"`.
   - LaTeX format matches `"\\forall v_{0} : Ind, (P(v_{0}) \\implies Q(v_{0}))"`.

---

### 6.2 `tests/test_parser.py`

#### Test Cases:
1. **Lexer Verification**:
   - Tokenize `"forall v0 : Ind, (P(v0) => Q(v0))"`. Assert tokens match `[QUANTIFIER, VARIABLE, COLON, IDENTIFIER, COMMA, LPAREN, IDENTIFIER, LPAREN, VARIABLE, RPAREN, IMPLIES, IDENTIFIER, LPAREN, VARIABLE, RPAREN, RPAREN, EOF]`.
   - Verify line and column reporting on line breaks.
   - Verify `ParseError` raised on invalid characters like `#` or `$`.
2. **Operator Precedence & Associativity**:
   - `parse_formula("P(v0) & Q(v0) | R(v0)", sig)` parses as `Or(And(P(v0), Q(v0)), R(v0))`.
   - `parse_formula("P(v0) => Q(v0) => R(v0)", sig)` parses as `Implies(P(v0), Implies(Q(v0), R(v0)))` (Right-associative).
   - `parse_formula("~P(v0) & Q(v0)", sig)` parses as `And(Not(P(v0)), Q(v0))`.
3. **Quantifier & Sort Parsing**:
   - Parse `forall v0 : Nat, P(v0)`. Assert `variable.sort == Nat`.
   - Parse `exists v1 : List(Nat), Q(v1)`. Assert `variable.sort == ParameterizedSort("List", (Nat,))`.
4. **Error Diagnostics**:
   - Unclosed parenthesis: `"P(v0) & (Q(v0)"` raises `ParseError` referencing missing `)`.
   - Undeclared predicate `"Unknown(v0)"` raises `ParseError("Undeclared predicate symbol 'Unknown'...")`.
   - Arity mismatch `"P(v0, v1)"` where `P` is binary but called as unary raises `ParseError`.
5. **Property-Based Round-Trip (Hypothesis)**:
   - Use `Hypothesis` or a custom random AST generator to generate 100+ valid formulas.
   - Assert `parse_formula(to_string(f, "infix"), sig) == f`.

---

## 7. Acceptance Criteria

| Criteria | Verification Method | Pass Condition |
|---|---|---|
| Visitor Framework Coverage | `pytest tests/test_visitors.py` | 100% of AST node types dispatch cleanly without unhandled branches |
| Parser Round-Trip | `pytest tests/test_parser.py` | `parse_formula(to_string(f)) == f` passes for all generated valid ASTs |
| Syntax Error Rejection | `pytest tests/test_parser.py` | Malformed strings raise `ParseError` with valid line/col position info |
| Symbol Resolution | `pytest tests/test_parser.py` | Arity and symbol check failures raise `ParseError` containing symbol name |
| Code Quality | `mypy solver/core/` & `flake8` | Zero type errors and linter warnings |

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **Operator Precedence Ambiguities** | Wrong AST tree structure parsed | Explicit Pratt binding powers table with unit tests for every precedence combination |
| **Variable Capture during Substitution** | Logical unsoundness in prover | `SubstitutionTransformer` checks for free variables in replacement terms and renames bound variables dynamically |
| **Infinite Parsing Loops** | Process hangs on invalid input | `_Parser.consume()` enforces monotonic advancement of token stream index |
| **Round-Trip Parentheses Mismatch** | `parse(to_string(f)) != f` | `ExportVisitor` parenthesizes compound binary expressions strictly according to precedence rules |
