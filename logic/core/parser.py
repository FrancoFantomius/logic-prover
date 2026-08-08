"""Lexer, parser, and string serializer for First-Order Logic terms and formulas."""

from __future__ import annotations
import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Union

from logic.core.exceptions import ParseError
from logic.core.ast import (
    Term, Variable, Constant, FunctionApp, VariableKind,
    Formula, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic.core.sorts import Sort, PrimitiveSort, ParameterizedSort, FunctionSort, Ind, Nat, Bool
from logic.core.signature import Signature


from logic.sol.ast_ext import (
    PredicateVariable, FunctionVariable,
    ForallPred, ExistsPred, ForallFunc, ExistsFunc
)


class TokenType(Enum):
    """Enumeration of token types recognized by the formula and term lexer."""
    QUANTIFIER = auto()   # forall, exists, ∀, ∃
    FORALL_PRED = auto()  # forall_pred
    EXISTS_PRED = auto()  # exists_pred
    FORALL_FUNC = auto()  # forall_func
    EXISTS_FUNC = auto()  # exists_func
    PRED_VAR = auto()     # P0, P1, P_0, P_1, ...
    FUNC_VAR = auto()     # F0, F1, F_0, F_1, ...
    VARIABLE = auto()     # v0, v1, v2, ...
    IDENTIFIER = auto()   # P, Q, f, c, Ind, Nat, etc.
    COLON = auto()        # :
    COMMA = auto()        # ,
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    NOT = auto()          # ~, not, ¬
    AND = auto()          # &, and, ∧
    OR = auto()           # |, or, ∨
    IMPLIES = auto()      # =>, implies, →
    IFF = auto()          # <=>, iff, ↔
    EQUAL = auto()        # =
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    position: int
    line: int
    col: int


TOKEN_PATTERNS = [
    (r"\bforall_pred\b", TokenType.FORALL_PRED),
    (r"\bexists_pred\b", TokenType.EXISTS_PRED),
    (r"\bforall_func\b", TokenType.FORALL_FUNC),
    (r"\bexists_func\b", TokenType.EXISTS_FUNC),
    (r"\b(forall|exists)\b|∀|∃", TokenType.QUANTIFIER),
    (r"\bP_\d+\b|\bP\d+\b", TokenType.PRED_VAR),
    (r"\bF_\d+\b|\bF\d+\b", TokenType.FUNC_VAR),
    (r"\bv\d+\b", TokenType.VARIABLE),
    (r"<=>|\biff\b|↔", TokenType.IFF),
    (r"=>|\bimplies\b|→", TokenType.IMPLIES),
    (r"~|\bnot\b|¬", TokenType.NOT),
    (r"&|\band\b|∧", TokenType.AND),
    (r"\||\bor\b|∨", TokenType.OR),
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
        ws_match = re.match(r"\s+", text[pos:])
        if ws_match:
            val = ws_match.group(0)
            newlines = val.count("\n")
            if newlines > 0:
                line += newlines
                col = len(val) - val.rfind("\n")
            else:
                col += len(val)
            pos += len(val)
            continue

        match = None
        for pattern, token_type in TOKEN_PATTERNS:
            regex = re.compile(pattern)
            m = regex.match(text, pos)
            if m:
                match = m
                val = m.group(0)
                tokens.append(Token(type=token_type, value=val, position=pos, line=line, col=col))
                newlines = val.count("\n")
                if newlines > 0:
                    line += newlines
                    col = len(val) - val.rfind("\n")
                else:
                    col += len(val)
                pos = m.end()
                break

        if not match:
            raise ParseError(f"Unexpected character '{text[pos]}' at line {line}, col {col} (pos {pos})")

    tokens.append(Token(type=TokenType.EOF, value="", position=length, line=line, col=col))
    return tokens


class _Parser:
    """Internal Pratt parser state machine supporting infix, prefix, and quantifier notation."""

    def __init__(self, tokens: List[Token], signature: Signature) -> None:
        self.tokens = tokens
        self.signature = signature
        self.idx = 0

    def peek(self, offset: int = 0) -> Token:
        pos = self.idx + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]

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

        # Handle SOL quantifiers
        if tok.type in (TokenType.FORALL_PRED, TokenType.EXISTS_PRED, TokenType.FORALL_FUNC, TokenType.EXISTS_FUNC):
            return self._parse_sol_quantifier()

        # Handle quantifiers (lowest precedence, scoped)
        if tok.type == TokenType.QUANTIFIER:
            return self._parse_quantifier()

        # Prefix operator: NOT
        if tok.type == TokenType.NOT:
            self.consume(TokenType.NOT)
            operand = self.parse_formula(min_prec=50)
            lhs: Formula = Not(operand=operand)
        elif tok.type == TokenType.LPAREN:
            lhs = self._parse_parenthesized_or_prefix_formula()
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

    def _parse_parenthesized_or_prefix_formula(self) -> Formula:
        t1 = self.peek(1)
        if t1.type == TokenType.QUANTIFIER:
            self.consume(TokenType.LPAREN)
            form = self._parse_quantifier()
            self.consume(TokenType.RPAREN)
            return form
        elif t1.type == TokenType.NOT:
            self.consume(TokenType.LPAREN)
            self.consume(TokenType.NOT)
            operand = self.parse_formula(0)
            self.consume(TokenType.RPAREN)
            return Not(operand=operand)
        elif t1.type == TokenType.AND:
            self.consume(TokenType.LPAREN)
            self.consume(TokenType.AND)
            l = self.parse_formula(0)
            r = self.parse_formula(0)
            self.consume(TokenType.RPAREN)
            return And(left=l, right=r)
        elif t1.type == TokenType.OR:
            self.consume(TokenType.LPAREN)
            self.consume(TokenType.OR)
            l = self.parse_formula(0)
            r = self.parse_formula(0)
            self.consume(TokenType.RPAREN)
            return Or(left=l, right=r)
        elif t1.type == TokenType.IMPLIES:
            self.consume(TokenType.LPAREN)
            self.consume(TokenType.IMPLIES)
            l = self.parse_formula(0)
            r = self.parse_formula(0)
            self.consume(TokenType.RPAREN)
            return Implies(left=l, right=r)
        elif t1.type == TokenType.IFF:
            self.consume(TokenType.LPAREN)
            self.consume(TokenType.IFF)
            l = self.parse_formula(0)
            r = self.parse_formula(0)
            self.consume(TokenType.RPAREN)
            return Iff(left=l, right=r)
        elif t1.type == TokenType.EQUAL:
            self.consume(TokenType.LPAREN)
            self.consume(TokenType.EQUAL)
            t1_term = self.parse_term()
            t2_term = self.parse_term()
            self.consume(TokenType.RPAREN)
            return Equality(left=t1_term, right=t2_term)
        elif t1.type == TokenType.IDENTIFIER:
            t2 = self.peek(2)
            if t2.type != TokenType.LPAREN:
                pred_decl = self.signature.lookup_predicate(t1.value)
                if pred_decl is not None:
                    self.consume(TokenType.LPAREN)
                    pred_tok = self.consume(TokenType.IDENTIFIER)
                    args = []
                    for _ in range(pred_decl.arity):
                        args.append(self.parse_term())
                    self.consume(TokenType.RPAREN)
                    return PredicateApp(pred=pred_decl.name, arity=pred_decl.arity, args=tuple(args))

        saved_idx = self.idx
        self.consume(TokenType.LPAREN)
        try:
            inner_formula = self.parse_formula(min_prec=0)
        except ParseError:
            self.idx = saved_idx
            return self._parse_atomic_formula()

        self.consume(TokenType.RPAREN)
        return inner_formula

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
        has_paren = False
        if self.peek().type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            has_paren = True

        var_tok = self.consume(TokenType.VARIABLE)
        var_id = int(var_tok.value[1:])

        sort: Sort = Ind
        if self.peek().type == TokenType.COLON:
            self.consume(TokenType.COLON)
            sort = self._parse_sort()

        if has_paren:
            self.consume(TokenType.RPAREN)
        elif self.peek().type == TokenType.COMMA:
            self.consume(TokenType.COMMA)

        body = self.parse_formula(min_prec=0)

        variable = Variable(id=var_id, sort=sort, kind=VariableKind.INDIVIDUAL)
        if q_tok.value in ("forall", "∀"):
            return Forall(variable=variable, body=body)
        else:
            return Exists(variable=variable, body=body)

    def _parse_sol_quantifier(self) -> Formula:
        q_tok = self.consume()
        has_paren = False
        if self.peek().type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            has_paren = True

        if q_tok.type in (TokenType.FORALL_PRED, TokenType.EXISTS_PRED):
            var_tok = self.consume(TokenType.PRED_VAR)
            var_idx = int(var_tok.value.split("_")[-1].replace("P", ""))
            arity = 1
            if self.peek().type == TokenType.COLON:
                self.consume(TokenType.COLON)
                arity_tok = self.consume(TokenType.IDENTIFIER)
                arity = int(arity_tok.value)
            if has_paren:
                self.consume(TokenType.RPAREN)
            body = self.parse_formula(min_prec=0)
            pred_var = PredicateVariable(index=var_idx, arity=arity)
            return ForallPred(variable=pred_var, body=body) if q_tok.type == TokenType.FORALL_PRED else ExistsPred(variable=pred_var, body=body)
        else:
            var_tok = self.consume(TokenType.FUNC_VAR)
            var_idx = int(var_tok.value.split("_")[-1].replace("F", ""))
            arity = 1
            if self.peek().type == TokenType.COLON:
                self.consume(TokenType.COLON)
                arity_tok = self.consume(TokenType.IDENTIFIER)
                arity = int(arity_tok.value)
            if has_paren:
                self.consume(TokenType.RPAREN)
            body = self.parse_formula(min_prec=0)
            func_var = FunctionVariable(index=var_idx, arity=arity, arg_sorts=tuple(Ind for _ in range(arity)))
            return ForallFunc(variable=func_var, body=body) if q_tok.type == TokenType.FORALL_FUNC else ExistsFunc(variable=func_var, body=body)

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
        tok = self.peek()

        if tok.type == TokenType.PRED_VAR:
            pred_tok = self.consume(TokenType.PRED_VAR)
            var_idx = int(pred_tok.value.split("_")[-1].replace("P", ""))
            args = []
            if self.peek().type == TokenType.LPAREN:
                self.consume(TokenType.LPAREN)
                args.append(self.parse_term())
                while self.peek().type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
                    args.append(self.parse_term())
                self.consume(TokenType.RPAREN)
            arity = len(args)
            pred_var = PredicateVariable(index=var_idx, arity=arity)
            return PredicateApp(pred=pred_var, arity=arity, args=tuple(args))

        # Try parsing term equality (term = term)
        saved_idx = self.idx
        try:
            left_term = self.parse_term()
            if self.peek().type == TokenType.EQUAL:
                self.consume(TokenType.EQUAL)
                right_term = self.parse_term()
                return Equality(left=left_term, right=right_term)
            else:
                self.idx = saved_idx
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
        if tok.type == TokenType.FUNC_VAR:
            func_tok = self.consume(TokenType.FUNC_VAR)
            var_idx = int(func_tok.value.split("_")[-1].replace("F", ""))
            args = []
            if self.peek().type == TokenType.LPAREN:
                self.consume(TokenType.LPAREN)
                args.append(self.parse_term())
                while self.peek().type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
                    args.append(self.parse_term())
                self.consume(TokenType.RPAREN)
            arity = len(args)
            func_var = FunctionVariable(index=var_idx, arity=arity, arg_sorts=tuple(Ind for _ in range(arity)))
            return FunctionApp(func=func_var, arity=arity, args=tuple(args), return_sort=Ind)
        elif tok.type == TokenType.VARIABLE:
            var_tok = self.consume(TokenType.VARIABLE)
            var_id = int(var_tok.value[1:])
            return Variable(id=var_id, sort=Ind, kind=VariableKind.INDIVIDUAL)
        elif tok.type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            func_tok = self.consume(TokenType.IDENTIFIER)
            func_name = func_tok.value
            func_decl = self.signature.lookup_function(func_name)
            if func_decl is None:
                raise ParseError(
                    f"Undeclared function symbol '{func_name}' at line {func_tok.line}, col {func_tok.col}"
                )
            args = []
            for _ in range(func_decl.arity):
                args.append(self.parse_term())
            self.consume(TokenType.RPAREN)
            return FunctionApp(func=func_name, arity=func_decl.arity, args=tuple(args), return_sort=func_decl.return_sort)
        elif tok.type == TokenType.IDENTIFIER:
            id_tok = self.consume(TokenType.IDENTIFIER)
            name = id_tok.value

            # Function check in signature
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

            const_sort = self.signature.lookup_constant(name)
            if const_sort is not None:
                return Constant(name=name, sort=const_sort)

            raise ParseError(f"Undeclared term symbol '{name}' at line {id_tok.line}, col {id_tok.col}")

        raise ParseError(f"Unexpected token '{tok.value}' when parsing term at line {tok.line}, col {tok.col}")


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
    from logic.core.visitors import ExportVisitor
    visitor = ExportVisitor(notation=notation)
    return visitor.visit(node)
