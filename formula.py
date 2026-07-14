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
        return False

    def __rshift__(self, other):
        if isinstance(other, str):
            other = parse_formula(other)
        if not isinstance(other, Formula):
            return NotImplemented
        return Implies(self, other)

    def __invert__(self):
        return Not(self)


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
        # Aggiungiamo parentesi se la formula interna è un'implicazione per evitare ambiguità visiva,
        # anche se la negazione lega più forte.
        if isinstance(self.formula, Implies):
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


def tokenize(s):
    token_specification = [
        ('IMPLIES', r'->|→'),
        ('NOT',     r'[~¬!]'),
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
        res = self.parse_implies()
        if self.peek() is not None:
            raise ValueError(f"Token extra inatteso alla fine: '{self.peek()[1]}'")
        return res

    def parse_implies(self):
        left = self.parse_not()
        tok = self.peek()
        if tok and tok[0] == 'IMPLIES':
            self.consume('IMPLIES')
            right = self.parse_implies()
            return Implies(left, right)
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
            self.consume('VAR')
            return Var(tok[1])
        elif tok[0] == 'LPAREN':
            self.consume('LPAREN')
            expr = self.parse_implies()
            self.consume('RPAREN')
            return expr
        else:
            raise ValueError(f"Token inatteso: '{tok[1]}'")


def parse_formula(s):
    """Esegue il parsing di una stringa in un oggetto Formula."""
    tokens = tokenize(s)
    parser = Parser(tokens)
    return parser.parse_formula()
