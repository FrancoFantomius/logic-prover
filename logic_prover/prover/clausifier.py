"""Clausification pipeline for translating First-Order Logic formulas to Conjunctive Normal Form (CNF)."""

from __future__ import annotations
import itertools
from dataclasses import dataclass, field
from typing import List, Set, FrozenSet, Dict, Tuple, Optional, Union

from logic_prover.core.ast import (
    Term,
    Variable,
    Constant,
    FunctionApp,
    Formula,
    PredicateApp,
    Equality,
    Not,
    And,
    Or,
    Implies,
    Iff,
    Forall,
    Exists,
    free_variables,
    bound_variables,
)
from logic_prover.core.sorts import Sort, Ind
from logic_prover.core.signature import Signature
from logic_prover.core.substitutions import substitute_formula, substitute_term


_skolem_constant_counter = itertools.count(0)
_skolem_function_counter = itertools.count(0)
_standardize_var_counter = itertools.count(1000)


def reset_skolem_counters() -> None:
    """Resets global Skolem counters (useful for predictable testing)."""
    global _skolem_constant_counter, _skolem_function_counter, _standardize_var_counter
    _skolem_constant_counter = itertools.count(0)
    _skolem_function_counter = itertools.count(0)
    _standardize_var_counter = itertools.count(1000)


@dataclass(frozen=True, slots=True)
class Literal:
    atom: Union[PredicateApp, Equality]
    positive: bool = True
    _hash_cache: int = field(init=False, repr=False, compare=False, hash=False)
    _free_vars: FrozenSet[Variable] = field(init=False, repr=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, '_hash_cache', hash((type(self), self.atom, self.positive)))
        object.__setattr__(self, '_free_vars', frozenset(free_variables(self.atom)))

    def __hash__(self) -> int:
        return self._hash_cache

    def negate(self) -> Literal:
        """Returns the complementary literal."""
        return Literal(atom=self.atom, positive=not self.positive)

    def free_variables(self) -> Set[Variable]:
        """Returns all free variables in the literal atom."""
        return set(self._free_vars)

    def substitute(self, subst: Dict[Variable, Term]) -> Literal:
        """Applies variable substitution to the literal atom.

        Args:
            subst: Mapping of variables to replacement terms.

        Returns:
            A new Literal with the substitution applied, or self if subst is empty.
        """
        if not subst:
            return self
        new_atom = substitute_formula(self.atom, subst)
        assert isinstance(new_atom, (PredicateApp, Equality))
        return Literal(atom=new_atom, positive=self.positive)

    def to_string(self) -> str:
        """Formats literal for display."""
        prefix = "" if self.positive else "¬"
        if isinstance(self.atom, Equality):
            eq_str = f"{self.atom.left} = {self.atom.right}"
            return eq_str if self.positive else f"{self.atom.left} ≠ {self.atom.right}"
        return f"{prefix}{self.atom}"

    def __str__(self) -> str:
        return self.to_string()


@dataclass(frozen=True, slots=True)
class Clause:
    literals: FrozenSet[Literal] = field(default_factory=frozenset)
    _hash_cache: int = field(init=False, repr=False, compare=False, hash=False)
    _is_tautology: bool = field(init=False, repr=False, compare=False, hash=False)
    _free_vars: FrozenSet[Variable] = field(init=False, repr=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, '_hash_cache', hash((type(self), self.literals)))
        # Pre-compute tautology check
        positives = {lit.atom for lit in self.literals if lit.positive}
        negatives = {lit.atom for lit in self.literals if not lit.positive}
        object.__setattr__(self, '_is_tautology', bool(positives & negatives))
        # Pre-compute free variables
        fvs: Set[Variable] = set()
        for lit in self.literals:
            fvs.update(lit._free_vars)
        object.__setattr__(self, '_free_vars', frozenset(fvs))

    def __hash__(self) -> int:
        return self._hash_cache

    @property
    def is_empty(self) -> bool:
        """True if clause is the empty clause (contradiction ⊥)."""
        return len(self.literals) == 0

    @property
    def is_tautology(self) -> bool:
        """True if clause contains both L and ¬L."""
        return self._is_tautology

    @property
    def is_unit(self) -> bool:
        """True if clause consists of exactly one literal."""
        return len(self.literals) == 1

    def free_variables(self) -> Set[Variable]:
        """Returns all free variables across all literals in the clause."""
        return set(self._free_vars)

    def substitute(self, subst: Dict[Variable, Term]) -> Clause:
        """Applies variable substitution to all literals in the clause.

        Args:
            subst: Mapping of variables to replacement terms.

        Returns:
            A new Clause with the substitution applied, or self if subst is empty.
        """
        if not subst:
            return self
        return Clause(frozenset(lit.substitute(subst) for lit in self.literals))

    def to_string(self) -> str:
        """Formats clause as disjunction string."""
        if self.is_empty:
            return "□"
        return " ∨ ".join(sorted(lit.to_string() for lit in self.literals))

    def __str__(self) -> str:
        return self.to_string()


def eliminate_implications(formula: Formula) -> Formula:
    """
    Recursively eliminates Iff and Implies operators:
    - A ⟺ B  ==>  (A ⟹ B) ∧ (B ⟹ A)
    - A ⟹ B  ==>  ¬A ∨ B

    Args:
        formula: The Formula AST node to transform.

    Returns:
        An equivalent formula with only And/Or/Not and quantifiers.

    Raises:
        ValueError: If an unsupported formula node is encountered.
    """
    if isinstance(formula, (PredicateApp, Equality)):
        return formula
    elif isinstance(formula, Not):
        return Not(operand=eliminate_implications(formula.operand))
    elif isinstance(formula, Implies):
        a = eliminate_implications(formula.left)
        b = eliminate_implications(formula.right)
        return Or(left=Not(operand=a), right=b)
    elif isinstance(formula, Iff):
        a = eliminate_implications(formula.left)
        b = eliminate_implications(formula.right)
        imp1 = Or(left=Not(operand=a), right=b)
        imp2 = Or(left=Not(operand=b), right=a)
        return And(left=imp1, right=imp2)
    elif isinstance(formula, And):
        return And(
            left=eliminate_implications(formula.left),
            right=eliminate_implications(formula.right),
        )
    elif isinstance(formula, Or):
        return Or(
            left=eliminate_implications(formula.left),
            right=eliminate_implications(formula.right),
        )
    elif isinstance(formula, Forall):
        return Forall(variable=formula.variable, body=eliminate_implications(formula.body))
    elif isinstance(formula, Exists):
        return Exists(variable=formula.variable, body=eliminate_implications(formula.body))
    else:
        raise ValueError(f"Unsupported formula node: {type(formula)}")


def to_nnf(formula: Formula) -> Formula:
    """
    Converts formula to Negation Normal Form (NNF) by pushing negations inward:
    - ¬(¬A)          ==>  A
    - ¬(A ∧ B)       ==>  ¬A ∨ ¬B
    - ¬(A ∨ B)       ==>  ¬A ∧ ¬B
    - ¬(∀x, P(x))    ==>  ∃x, ¬P(x)
    - ¬(∃x, P(x))    ==>  ∀x, ¬P(x)
    Assumes implications have already been eliminated.

    Args:
        formula: The Formula AST node to transform.

    Returns:
        An equivalent formula in Negation Normal Form.

    Raises:
        ValueError: If an unsupported formula node is encountered.
    """
    if isinstance(formula, (PredicateApp, Equality)):
        return formula
    elif isinstance(formula, Not):
        op = formula.operand
        if isinstance(op, Not):
            return to_nnf(op.operand)
        elif isinstance(op, And):
            return Or(left=to_nnf(Not(op.left)), right=to_nnf(Not(op.right)))
        elif isinstance(op, Or):
            return And(left=to_nnf(Not(op.left)), right=to_nnf(Not(op.right)))
        elif isinstance(op, Forall):
            return Exists(variable=op.variable, body=to_nnf(Not(op.body)))
        elif isinstance(op, Exists):
            return Forall(variable=op.variable, body=to_nnf(Not(op.body)))
        elif isinstance(op, (Implies, Iff)):
            return to_nnf(Not(eliminate_implications(op)))
        elif isinstance(op, (PredicateApp, Equality)):
            return formula
        else:
            raise ValueError(f"Unsupported negated formula operand: {type(op)}")
    elif isinstance(formula, And):
        return And(left=to_nnf(formula.left), right=to_nnf(formula.right))
    elif isinstance(formula, Or):
        return Or(left=to_nnf(formula.left), right=to_nnf(formula.right))
    elif isinstance(formula, Forall):
        return Forall(variable=formula.variable, body=to_nnf(formula.body))
    elif isinstance(formula, Exists):
        return Exists(variable=formula.variable, body=to_nnf(formula.body))
    elif isinstance(formula, (Implies, Iff)):
        return to_nnf(eliminate_implications(formula))
    else:
        raise ValueError(f"Unsupported formula node: {type(formula)}")


def standardize_variables(formula: Formula) -> Formula:
    """
    Renames bound variables so that each quantifier binds a unique variable index,
    preventing name clashes during Skolemization.

    Args:
        formula: The Formula AST node to standardize.

    Returns:
        An alpha-equivalent formula with unique bound variable indices.

    Raises:
        ValueError: If an unsupported formula node is encountered.
    """
    all_vars = free_variables(formula) | bound_variables(formula)
    max_id = max([v.id for v in all_vars], default=0)
    counter = itertools.count(max_id + 1)

    def _std(f: Formula, env: Dict[Variable, Variable]) -> Formula:
        if isinstance(f, (PredicateApp, Equality)):
            if not env:
                return f
            return substitute_formula(f, env)
        elif isinstance(f, Not):
            return Not(operand=_std(f.operand, env))
        elif isinstance(f, And):
            return And(left=_std(f.left, env), right=_std(f.right, env))
        elif isinstance(f, Or):
            return Or(left=_std(f.left, env), right=_std(f.right, env))
        elif isinstance(f, Implies):
            return Implies(left=_std(f.left, env), right=_std(f.right, env))
        elif isinstance(f, Iff):
            return Iff(left=_std(f.left, env), right=_std(f.right, env))
        elif isinstance(f, Forall):
            new_var = Variable(id=next(counter), sort=f.variable.sort, kind=f.variable.kind)
            new_env = dict(env)
            new_env[f.variable] = new_var
            return Forall(variable=new_var, body=_std(f.body, new_env))
        elif isinstance(f, Exists):
            new_var = Variable(id=next(counter), sort=f.variable.sort, kind=f.variable.kind)
            new_env = dict(env)
            new_env[f.variable] = new_var
            return Exists(variable=new_var, body=_std(f.body, new_env))
        else:
            raise ValueError(f"Unsupported formula: {type(f)}")

    return _std(formula, {})


def skolemize(formula: Formula, signature: Optional[Signature] = None) -> Formula:
    """
    Eliminates existential quantifiers by introducing Skolem constants/functions.
    - ∃x, P(x) with active outer universal variables [y_1, ..., y_k]:
      Replaces x with FunctionApp(sk_fn, arity=k, args=(y_1, ..., y_k), return_sort=x.sort).
    - If k == 0, replaces x with Constant(sk_c, sort=x.sort).
    Updates signature with new Skolem function/constant symbols if signature is provided.
    Assumes formula is in NNF and variables are standardized.

    Args:
        formula: The Formula AST node to Skolemize.
        signature: Optional Signature to register newly introduced Skolem symbols.

    Returns:
        A formula with all existential quantifiers eliminated.

    Raises:
        ValueError: If an unsupported formula node is encountered.
    """
    def _sk(f: Formula, outer_universals: List[Variable]) -> Formula:
        if isinstance(f, (PredicateApp, Equality)):
            return f
        elif isinstance(f, Not):
            return Not(operand=_sk(f.operand, outer_universals))
        elif isinstance(f, And):
            return And(left=_sk(f.left, outer_universals), right=_sk(f.right, outer_universals))
        elif isinstance(f, Or):
            return Or(left=_sk(f.left, outer_universals), right=_sk(f.right, outer_universals))
        elif isinstance(f, Forall):
            new_outer = outer_universals + [f.variable]
            return Forall(variable=f.variable, body=_sk(f.body, new_outer))
        elif isinstance(f, Exists):
            var = f.variable
            if not outer_universals:
                sk_name = f"sk_c{next(_skolem_constant_counter)}"
                sk_term: Term = Constant(name=sk_name, sort=var.sort)
                if signature is not None:
                    try:
                        signature.register_constant(sk_name, var.sort)
                    except Exception:
                        pass
            else:
                sk_name = f"sk_f{next(_skolem_function_counter)}"
                arg_sorts = [v.sort for v in outer_universals]
                sk_term = FunctionApp(
                    func=sk_name,
                    arity=len(outer_universals),
                    args=tuple(outer_universals),
                    return_sort=var.sort,
                )
                if signature is not None:
                    try:
                        signature.register_function(
                            sk_name, len(outer_universals), tuple(arg_sorts), var.sort
                        )
                    except Exception:
                        pass

            body_subst = substitute_formula(f.body, {var: sk_term})
            return _sk(body_subst, outer_universals)
        else:
            raise ValueError(f"Unsupported formula in skolemization: {type(f)}")

    return _sk(formula, [])


def drop_universals(formula: Formula) -> Formula:
    """
    Strips all Forall quantifiers. In CNF, all remaining free variables
    are implicitly universally quantified.

    Args:
        formula: The Formula AST node to strip quantifiers from.

    Returns:
        A formula without leading universal quantifiers.

    Raises:
        ValueError: If an unsupported formula node is encountered.
    """
    if isinstance(formula, Forall):
        return drop_universals(formula.body)
    elif isinstance(formula, Exists):
        return Exists(variable=formula.variable, body=drop_universals(formula.body))
    elif isinstance(formula, (PredicateApp, Equality)):
        return formula
    elif isinstance(formula, Not):
        return Not(operand=drop_universals(formula.operand))
    elif isinstance(formula, And):
        return And(left=drop_universals(formula.left), right=drop_universals(formula.right))
    elif isinstance(formula, Or):
        return Or(left=drop_universals(formula.left), right=drop_universals(formula.right))
    else:
        raise ValueError(f"Unsupported formula: {type(formula)}")


def distribute_cnf(formula: Formula) -> Formula:
    """
    Recursively distributes disjunctions (Or) over conjunctions (And):
    - A ∨ (B ∧ C)  ==>  (A ∨ B) ∧ (A ∨ C)
    - (A ∧ B) ∨ C  ==>  (A ∨ C) ∧ (B ∨ C)
    Assumes formula has no quantifiers or implications.

    Args:
        formula: The Formula AST node to distribute.

    Returns:
        An equivalent formula in Conjunctive Normal Form.

    Raises:
        ValueError: If an unsupported formula node is encountered.
    """
    if isinstance(formula, (PredicateApp, Equality)):
        return formula
    elif isinstance(formula, Not):
        return formula
    elif isinstance(formula, And):
        left_dist = distribute_cnf(formula.left)
        right_dist = distribute_cnf(formula.right)
        return And(left=left_dist, right=right_dist)
    elif isinstance(formula, Or):
        left_dist = distribute_cnf(formula.left)
        right_dist = distribute_cnf(formula.right)

        if isinstance(left_dist, And):
            # (A ∧ B) ∨ C ==> (A ∨ C) ∧ (B ∨ C)
            return distribute_cnf(
                And(
                    left=Or(left=left_dist.left, right=right_dist),
                    right=Or(left=left_dist.right, right=right_dist),
                )
            )
        elif isinstance(right_dist, And):
            # A ∨ (B ∧ C) ==> (A ∨ B) ∧ (A ∨ C)
            return distribute_cnf(
                And(
                    left=Or(left=left_dist, right=right_dist.left),
                    right=Or(left=left_dist, right=right_dist.right),
                )
            )
        else:
            return Or(left=left_dist, right=right_dist)
    else:
        raise ValueError(f"Unsupported formula in CNF distribution: {type(formula)}")


def formula_to_clauses(formula: Formula) -> List[Clause]:
    """
    Converts a CNF-structured Formula (And/Or trees over atoms/nots)
    into a List of Clause instances. Filters out tautological clauses (L ∨ ¬L).

    Args:
        formula: A CNF-structured Formula AST node.

    Returns:
        List of Clause objects, excluding tautologies.

    Raises:
        ValueError: If an unexpected node appears inside a clause.
    """
    conjunctions: List[Formula] = []

    def _collect_and(f: Formula) -> None:
        if isinstance(f, And):
            _collect_and(f.left)
            _collect_and(f.right)
        else:
            conjunctions.append(f)

    _collect_and(formula)

    clauses: List[Clause] = []
    for conj in conjunctions:
        lits: Set[Literal] = set()

        def _collect_or(f: Formula) -> None:
            if isinstance(f, Or):
                _collect_or(f.left)
                _collect_or(f.right)
            elif isinstance(f, Not):
                op = f.operand
                assert isinstance(op, (PredicateApp, Equality))
                lits.add(Literal(atom=op, positive=False))
            elif isinstance(f, (PredicateApp, Equality)):
                lits.add(Literal(atom=f, positive=True))
            else:
                raise ValueError(f"Unexpected formula inside clause: {type(f)}")

        _collect_or(conj)
        clause = Clause(frozenset(lits))
        if not clause.is_tautology:
            clauses.append(clause)

    return clauses


def to_cnf(formula: Formula, signature: Optional[Signature] = None) -> List[Clause]:
    """
    Full CNF conversion pipeline:
    1. Eliminate ⟺ and ⟹
    2. Convert to NNF
    3. Standardize bound variables
    4. Skolemize existential quantifiers
    5. Drop universal quantifiers
    6. Distribute ∨ over ∧
    7. Convert AST to List[Clause] and filter tautologies

    Args:
        formula: The Formula AST node to convert.
        signature: Optional Signature for Skolem symbol registration.

    Returns:
        List of Clause objects representing the CNF of the formula.
    """
    f1 = eliminate_implications(formula)
    f2 = to_nnf(f1)
    f3 = standardize_variables(f2)
    f4 = skolemize(f3, signature=signature)
    f5 = drop_universals(f4)
    f6 = distribute_cnf(f5)
    return formula_to_clauses(f6)


def negate_and_clausify(formula: Formula, signature: Optional[Signature] = None) -> List[Clause]:
    """
    Negates the given target formula (Not(formula)) and converts it to CNF for refutation search.

    Args:
        formula: The Formula AST node to negate and clausify.
        signature: Optional Signature for Skolem symbol registration.

    Returns:
        List of Clause objects representing the CNF of the negated formula.
    """
    return to_cnf(Not(formula), signature=signature)
