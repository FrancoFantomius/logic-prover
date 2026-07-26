from abc import ABC, abstractmethod
import re

class Formula(ABC):
    @abstractmethod
    def substitute(self, sub_map):
        """Sostituisce le variabili presenti nelle chiavi di sub_map con le formule corrispondenti."""
        pass

    @abstractmethod
    def free_variables(self):
        """Restituisce l'insieme delle variabili libere presenti nella formula."""
        pass

    def match_schema(self, schema):
        """
        Controlla se la formula corrente fa il match con la formula schema (che contiene meta-variabili).
        Ritorna un dizionario di associazioni (nome_meta_variabile -> sottoformula) se il match ha successo,
        altrimenti None.
        """
        bindings = {}
        if self._match(schema, self, bindings):
            return bindings
        return None

    @staticmethod
    def _match(schema_node, concrete_node, bindings):
        if isinstance(schema_node, Var):
            if schema_node.name in bindings:
                return bindings[schema_node.name] == concrete_node
            else:
                bindings[schema_node.name] = concrete_node
                return True
        elif isinstance(schema_node, Not) and isinstance(concrete_node, Not):
            return Formula._match(schema_node.formula, concrete_node.formula, bindings)
        elif isinstance(schema_node, Implies) and isinstance(concrete_node, Implies):
            return (Formula._match(schema_node.left, concrete_node.left, bindings) and
                    Formula._match(schema_node.right, concrete_node.right, bindings))
        elif isinstance(schema_node, And) and isinstance(concrete_node, And):
            return (Formula._match(schema_node.left, concrete_node.left, bindings) and
                    Formula._match(schema_node.right, concrete_node.right, bindings))
        elif isinstance(schema_node, Or) and isinstance(concrete_node, Or):
            return (Formula._match(schema_node.left, concrete_node.left, bindings) and
                    Formula._match(schema_node.right, concrete_node.right, bindings))
        elif isinstance(schema_node, Iff) and isinstance(concrete_node, Iff):
            return (Formula._match(schema_node.left, concrete_node.left, bindings) and
                    Formula._match(schema_node.right, concrete_node.right, bindings))
        elif isinstance(schema_node, Forall) and isinstance(concrete_node, Forall):
            if schema_node.var == concrete_node.var:
                return Formula._match(schema_node.body, concrete_node.body, bindings)
        elif isinstance(schema_node, Exists) and isinstance(concrete_node, Exists):
            if schema_node.var == concrete_node.var:
                return Formula._match(schema_node.body, concrete_node.body, bindings)
        elif isinstance(schema_node, Equals) and isinstance(concrete_node, Equals):
            return (Formula._match(schema_node.left, concrete_node.left, bindings) and
                    Formula._match(schema_node.right, concrete_node.right, bindings))
        elif isinstance(schema_node, Pred) and isinstance(concrete_node, Pred):
            if schema_node.name in bindings:
                if bindings[schema_node.name] != concrete_node.name and bindings[schema_node.name] != concrete_node:
                    return False
            else:
                bindings[schema_node.name] = concrete_node.name
            if len(schema_node.args) == len(concrete_node.args):
                return all(Formula._match(sa, ca, bindings) for sa, ca in zip(schema_node.args, concrete_node.args))
        return False

    def __rshift__(self, other):
        if isinstance(other, str):
            other = parse_formula(other)
        if not isinstance(other, Formula):
            return NotImplemented
        return Implies(self, other)

    def __invert__(self):
        return Not(self)

    def __and__(self, other):
        if isinstance(other, str):
            other = parse_formula(other)
        if not isinstance(other, Formula):
            return NotImplemented
        return And(self, other)

    def __or__(self, other):
        if isinstance(other, str):
            other = parse_formula(other)
        if not isinstance(other, Formula):
            return NotImplemented
        return Or(self, other)


class Var(Formula):
    def __init__(self, name):
        self.name = name

    def substitute(self, sub_map):
        return sub_map.get(self.name, self)

    def free_variables(self):
        return {self.name}

    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name

    def __hash__(self):
        return hash(('Var', self.name))

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Var({self.name!r})"


class Not(Formula):
    def __init__(self, formula):
        if isinstance(formula, str):
            formula = parse_formula(formula)
        self.formula = formula

    def substitute(self, sub_map):
        return Not(self.formula.substitute(sub_map))

    def free_variables(self):
        return self.formula.free_variables()

    def __eq__(self, other):
        return isinstance(other, Not) and self.formula == other.formula

    def __hash__(self):
        return hash(('Not', self.formula))

    def __str__(self):
        if isinstance(self.formula, (Implies, And, Or, Iff)):
            return f"~({self.formula})"
        return f"~{self.formula}"

    def __repr__(self):
        return f"Not({self.formula!r})"


class Implies(Formula):
    def __init__(self, left, right):
        if isinstance(left, str):
            left = parse_formula(left)
        if isinstance(right, str):
            right = parse_formula(right)
        self.left = left
        self.right = right

    def substitute(self, sub_map):
        return Implies(self.left.substitute(sub_map), self.right.substitute(sub_map))

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def __eq__(self, other):
        return (isinstance(other, Implies) and 
                self.left == other.left and 
                self.right == other.right)

    def __hash__(self):
        return hash(('Implies', self.left, self.right))

    def __str__(self):
        return f"({self.left} -> {self.right})"

    def __repr__(self):
        return f"Implies({self.left!r}, {self.right!r})"


class And(Formula):
    def __init__(self, left, right):
        if isinstance(left, str):
            left = parse_formula(left)
        if isinstance(right, str):
            right = parse_formula(right)
        self.left = left
        self.right = right

    def substitute(self, sub_map):
        return And(self.left.substitute(sub_map), self.right.substitute(sub_map))

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def __eq__(self, other):
        return isinstance(other, And) and self.left == other.left and self.right == other.right

    def __hash__(self):
        return hash(('And', self.left, self.right))

    def __str__(self):
        return f"({self.left} & {self.right})"

    def __repr__(self):
        return f"And({self.left!r}, {self.right!r})"


class Or(Formula):
    def __init__(self, left, right):
        if isinstance(left, str):
            left = parse_formula(left)
        if isinstance(right, str):
            right = parse_formula(right)
        self.left = left
        self.right = right

    def substitute(self, sub_map):
        return Or(self.left.substitute(sub_map), self.right.substitute(sub_map))

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def __eq__(self, other):
        return isinstance(other, Or) and self.left == other.left and self.right == other.right

    def __hash__(self):
        return hash(('Or', self.left, self.right))

    def __str__(self):
        return f"({self.left} | {self.right})"

    def __repr__(self):
        return f"Or({self.left!r}, {self.right!r})"


class Iff(Formula):
    def __init__(self, left, right):
        if isinstance(left, str):
            left = parse_formula(left)
        if isinstance(right, str):
            right = parse_formula(right)
        self.left = left
        self.right = right

    def substitute(self, sub_map):
        return Iff(self.left.substitute(sub_map), self.right.substitute(sub_map))

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def __eq__(self, other):
        return isinstance(other, Iff) and self.left == other.left and self.right == other.right

    def __hash__(self):
        return hash(('Iff', self.left, self.right))

    def __str__(self):
        return f"({self.left} <-> {self.right})"

    def __repr__(self):
        return f"Iff({self.left!r}, {self.right!r})"


class Forall(Formula):
    def __init__(self, var, body):
        self.var = var.name if isinstance(var, Var) else str(var)
        if isinstance(body, str):
            body = parse_formula(body)
        self.body = body

    def substitute(self, sub_map):
        filtered_map = {k: v for k, v in sub_map.items() if k != self.var}
        return Forall(self.var, self.body.substitute(filtered_map))

    def free_variables(self):
        return self.body.free_variables() - {self.var}

    def __eq__(self, other):
        return isinstance(other, Forall) and self.var == other.var and self.body == other.body

    def __hash__(self):
        return hash(('Forall', self.var, self.body))

    def __str__(self):
        return f"(forall {self.var}, {self.body})"

    def __repr__(self):
        return f"Forall({self.var!r}, {self.body!r})"


class Exists(Formula):
    def __init__(self, var, body):
        self.var = var.name if isinstance(var, Var) else str(var)
        if isinstance(body, str):
            body = parse_formula(body)
        self.body = body

    def substitute(self, sub_map):
        filtered_map = {k: v for k, v in sub_map.items() if k != self.var}
        return Exists(self.var, self.body.substitute(filtered_map))

    def free_variables(self):
        return self.body.free_variables() - {self.var}

    def __eq__(self, other):
        return isinstance(other, Exists) and self.var == other.var and self.body == other.body

    def __hash__(self):
        return hash(('Exists', self.var, self.body))

    def __str__(self):
        return f"(exists {self.var}, {self.body})"

    def __repr__(self):
        return f"Exists({self.var!r}, {self.body!r})"


class Equals(Formula):
    def __init__(self, left, right):
        if isinstance(left, str):
            left = parse_formula(left)
        if isinstance(right, str):
            right = parse_formula(right)
        self.left = left
        self.right = right

    def substitute(self, sub_map):
        return Equals(self.left.substitute(sub_map), self.right.substitute(sub_map))

    def free_variables(self):
        return self.left.free_variables() | self.right.free_variables()

    def __eq__(self, other):
        return isinstance(other, Equals) and self.left == other.left and self.right == other.right

    def __hash__(self):
        return hash(('Equals', self.left, self.right))

    def __str__(self):
        return f"({self.left} = {self.right})"

    def __repr__(self):
        return f"Equals({self.left!r}, {self.right!r})"


class Pred(Formula):
    def __init__(self, name, args):
        self.name = name
        self.args = [parse_formula(a) if isinstance(a, str) else a for a in args]

    def substitute(self, sub_map):
        new_args = [a.substitute(sub_map) if isinstance(a, Formula) else a for a in self.args]
        return Pred(self.name, new_args)

    def free_variables(self):
        res = set()
        for a in self.args:
            if isinstance(a, Formula):
                res.update(a.free_variables())
        return res

    def __eq__(self, other):
        return isinstance(other, Pred) and self.name == other.name and self.args == other.args

    def __hash__(self):
        return hash(('Pred', self.name, tuple(self.args)))

    def __str__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"

    def __repr__(self):
        return f"Pred({self.name!r}, {self.args!r})"


def tokenize(s):
    token_specification = [
        ('IFF',     r'<->|↔'),
        ('IMPLIES', r'->|→'),
        ('AND',     r'&|∧'),
        ('OR',      r'\||∨'),
        ('NOT',     r'[~¬!]'),
        ('EQUALS',  r'='),
        ('FORALL',  r'forall|∀'),
        ('EXISTS',  r'exists|∃'),
        ('COMMA',   r','),
        ('LPAREN',  r'\('),
        ('RPAREN',  r'\)'),
        ('VAR',     r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('SKIP',    r'\s+'),
        ('MISMATCH',r'.'),
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    tokens = []
    for mo in re.finditer(tok_regex, s):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise ValueError(f"Carattere inatteso: '{value}'")
        else:
            tokens.append((kind, value))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_kind=None):
        tok = self.peek()
        if tok is None:
            raise ValueError("Fine inattesa dell'input")
        if expected_kind and tok[0] != expected_kind:
            raise ValueError(f"Atteso token '{expected_kind}', trovato '{tok[0]}' ('{tok[1]}')")
        self.pos += 1
        return tok

    def parse_formula(self):
        res = self.parse_quantifier()
        if self.peek() is not None:
            raise ValueError(f"Token extra inatteso alla fine: '{self.peek()[1]}'")
        return res

    def parse_quantifier(self):
        tok = self.peek()
        if tok and tok[0] == 'FORALL':
            self.consume('FORALL')
            var_tok = self.consume('VAR')
            if self.peek() and self.peek()[0] == 'COMMA':
                self.consume('COMMA')
            body = self.parse_quantifier()
            return Forall(var_tok[1], body)
        elif tok and tok[0] == 'EXISTS':
            self.consume('EXISTS')
            var_tok = self.consume('VAR')
            if self.peek() and self.peek()[0] == 'COMMA':
                self.consume('COMMA')
            body = self.parse_quantifier()
            return Exists(var_tok[1], body)
        return self.parse_iff()

    def parse_iff(self):
        left = self.parse_implies()
        tok = self.peek()
        if tok and tok[0] == 'IFF':
            self.consume('IFF')
            right = self.parse_iff()
            return Iff(left, right)
        return left

    def parse_implies(self):
        left = self.parse_or()
        tok = self.peek()
        if tok and tok[0] == 'IMPLIES':
            self.consume('IMPLIES')
            right = self.parse_implies()
            return Implies(left, right)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.peek() and self.peek()[0] == 'OR':
            self.consume('OR')
            right = self.parse_and()
            left = Or(left, right)
        return left

    def parse_and(self):
        left = self.parse_equals()
        while self.peek() and self.peek()[0] == 'AND':
            self.consume('AND')
            right = self.parse_equals()
            left = And(left, right)
        return left

    def parse_equals(self):
        left = self.parse_not()
        tok = self.peek()
        if tok and tok[0] == 'EQUALS':
            self.consume('EQUALS')
            right = self.parse_not()
            return Equals(left, right)
        return left

    def parse_not(self):
        tok = self.peek()
        if tok and tok[0] == 'NOT':
            self.consume('NOT')
            inner = self.parse_not()
            return Not(inner)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()
        if tok is None:
            raise ValueError("Attesa variabile o parentesi aperta, fine dell'input raggiunta")
        if tok[0] == 'VAR':
            var_tok = self.consume('VAR')
            if self.peek() and self.peek()[0] == 'LPAREN':
                # Predicato P(x, y)
                self.consume('LPAREN')
                args = []
                if self.peek() and self.peek()[0] != 'RPAREN':
                    args.append(self.parse_implies())
                    while self.peek() and self.peek()[0] == 'COMMA':
                        self.consume('COMMA')
                        args.append(self.parse_implies())
                self.consume('RPAREN')
                return Pred(var_tok[1], args)
            return Var(var_tok[1])
        elif tok[0] == 'LPAREN':
            self.consume('LPAREN')
            expr = self.parse_quantifier()
            self.consume('RPAREN')
            return expr
        else:
            raise ValueError(f"Token inatteso: '{tok[1]}'")


def parse_formula(s):
    """Esegue il parsing di una stringa in un oggetto Formula."""
    tokens = tokenize(s)
    parser = Parser(tokens)
    return parser.parse_formula()
