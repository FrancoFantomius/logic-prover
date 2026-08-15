"""Term rewriting system for applying directional rewrite rules and normalizations."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from logic_prover.core.ast import (
    Term, Formula, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import is_compatible
from logic_prover.core.substitutions import substitute_term, substitute_formula
from logic_prover.core.exceptions import RewriteDivergenceError, ValidationError


@dataclass(frozen=True, slots=True)
class RewriteRule:
    """Oriented rewrite rule lhs -> rhs with optional side condition."""
    lhs: Union[Term, Formula]
    rhs: Union[Term, Formula]
    condition: Optional[Formula] = None
    name: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.lhs, Term) and not isinstance(self.rhs, Term):
            raise ValidationError("RewriteRule lhs is Term but rhs is Formula.")
        if isinstance(self.lhs, Formula) and not isinstance(self.rhs, Formula):
            raise ValidationError("RewriteRule lhs is Formula but rhs is Term.")


def match_term(
    pattern: Term, 
    target: Term, 
    subst: Optional[Dict[Variable, Term]] = None
) -> Optional[Dict[Variable, Term]]:
    """Single-direction pattern matching for terms.
    
    Args:
        pattern: Pattern term (may contain pattern variables).
        target: Ground/concrete target term.
        subst: Current variable mapping.
        
    Returns:
        Updated variable substitution dict if match succeeds, None otherwise.
    """
    if subst is None:
        subst = {}
    else:
        subst = dict(subst)

    if isinstance(pattern, Variable):
        if not is_compatible(pattern.sort, target.sort):
            return None
        if pattern in subst:
            return subst if subst[pattern] == target else None
        subst[pattern] = target
        return subst

    if isinstance(pattern, Constant):
        return subst if pattern == target else None

    if isinstance(pattern, FunctionApp):
        if not isinstance(target, FunctionApp):
            return None
        if pattern.func != target.func or pattern.arity != target.arity:
            return None
        for p_arg, t_arg in zip(pattern.args, target.args):
            res = match_term(p_arg, t_arg, subst)
            if res is None:
                return None
            subst = res
        return subst

    return None


def match_formula(
    pattern: Formula, 
    target: Formula, 
    subst: Optional[Dict[Variable, Term]] = None
) -> Optional[Dict[Variable, Term]]:
    """Single-direction pattern matching for formulas.
    
    Args:
        pattern: Pattern formula.
        target: Target formula.
        subst: Current variable mapping.
        
    Returns:
        Substitution dict if match succeeds, None otherwise.
    """
    if subst is None:
        subst = {}
    else:
        subst = dict(subst)

    if type(pattern) != type(target):
        return None

    if isinstance(pattern, PredicateApp) and isinstance(target, PredicateApp):
        if pattern.pred != target.pred or pattern.arity != target.arity:
            return None
        for p_arg, t_arg in zip(pattern.args, target.args):
            res = match_term(p_arg, t_arg, subst)
            if res is None:
                return None
            subst = res
        return subst

    if isinstance(pattern, Equality) and isinstance(target, Equality):
        res = match_term(pattern.left, target.left, subst)
        if res is None:
            return None
        return match_term(pattern.right, target.right, res)

    if isinstance(pattern, Not) and isinstance(target, Not):
        return match_formula(pattern.operand, target.operand, subst)

    if isinstance(pattern, (And, Or, Implies, Iff)) and isinstance(target, (And, Or, Implies, Iff)):
        res = match_formula(pattern.left, target.left, subst)
        if res is None:
            return None
        return match_formula(pattern.right, target.right, res)

    if isinstance(pattern, (Forall, Exists)) and isinstance(target, (Forall, Exists)):
        res = match_term(pattern.variable, target.variable, subst)
        if res is None:
            return None
        return match_formula(pattern.body, target.body, res)

    return None


def rewrite(node: Union[Term, Formula], rule: RewriteRule) -> Optional[Union[Term, Formula]]:
    """Applies a rewrite rule at the root of a node.
    
    Args:
        node: The Term or Formula to rewrite at root.
        rule: The RewriteRule to apply.
        
    Returns:
        Transformed node if rule matched and condition satisfied, None otherwise.
    """
    if isinstance(node, Term) and isinstance(rule.lhs, Term):
        subst = match_term(rule.lhs, node)
        if subst is None:
            return None
        if rule.condition is not None:
            cond_inst = substitute_formula(rule.condition, subst)
            if not _evaluate_condition(cond_inst):
                return None
        return substitute_term(rule.rhs, subst)

    elif isinstance(node, Formula) and isinstance(rule.lhs, Formula):
        subst = match_formula(rule.lhs, node)
        if subst is None:
            return None
        if rule.condition is not None:
            cond_inst = substitute_formula(rule.condition, subst)
            if not _evaluate_condition(cond_inst):
                return None
        return substitute_formula(rule.rhs, subst)

    return None


def _evaluate_condition(condition: Formula) -> bool:
    """Internal helper to evaluate side conditions on rewrite rules."""
    if isinstance(condition, Equality) and condition.left == condition.right:
        return True
    return False


def rewrite_all(node: Union[Term, Formula], rules: List[RewriteRule], max_root_steps: int = 1000) -> Union[Term, Formula]:
    """Applies matching rewrite rules bottom-up across subnodes until fixed point.
    
    Args:
        node: Term or Formula to rewrite.
        rules: List of RewriteRule instances.
        max_root_steps: Safety step limit for root-level iterations.
        
    Returns:
        Rewritten node.
    """
    curr = node

    # 1. Recurse down subnodes (Bottom-Up Inner-Most Strategy)
    if isinstance(curr, FunctionApp):
        new_args = tuple(rewrite_all(arg, rules, max_root_steps) for arg in curr.args)
        curr = FunctionApp(curr.func, curr.arity, new_args, curr.return_sort)
    elif isinstance(curr, PredicateApp):
        new_args = tuple(rewrite_all(arg, rules, max_root_steps) for arg in curr.args)
        curr = PredicateApp(curr.pred, curr.arity, new_args)
    elif isinstance(curr, Equality):
        new_l = rewrite_all(curr.left, rules, max_root_steps)
        new_r = rewrite_all(curr.right, rules, max_root_steps)
        curr = Equality(new_l, new_r)
    elif isinstance(curr, Not):
        curr = Not(rewrite_all(curr.operand, rules, max_root_steps))
    elif isinstance(curr, And):
        curr = And(rewrite_all(curr.left, rules, max_root_steps), rewrite_all(curr.right, rules, max_root_steps))
    elif isinstance(curr, Or):
        curr = Or(rewrite_all(curr.left, rules, max_root_steps), rewrite_all(curr.right, rules, max_root_steps))
    elif isinstance(curr, Implies):
        curr = Implies(rewrite_all(curr.left, rules, max_root_steps), rewrite_all(curr.right, rules, max_root_steps))
    elif isinstance(curr, Iff):
        curr = Iff(rewrite_all(curr.left, rules, max_root_steps), rewrite_all(curr.right, rules, max_root_steps))
    elif isinstance(curr, Forall):
        curr = Forall(curr.variable, rewrite_all(curr.body, rules, max_root_steps))
    elif isinstance(curr, Exists):
        curr = Exists(curr.variable, rewrite_all(curr.body, rules, max_root_steps))

    # 2. Try root rewrite rules in sequence until fixed point at root
    changed = True
    steps = 0
    while changed:
        changed = False
        for rule in rules:
            res = rewrite(curr, rule)
            if res is not None and res != curr:
                curr = res
                changed = True
                steps += 1
                if steps >= max_root_steps:
                    raise RewriteDivergenceError(
                        f"Root rewriting diverged after {steps} steps."
                    )
                break

    return curr


def normalize(formula: Formula, rules: List[RewriteRule], max_steps: int = 100) -> Formula:
    """Normalizes a formula by repeatedly applying rewrite_all up to max_steps iterations.
    
    Args:
        formula: Formula to normalize.
        rules: Set of rewrite rules.
        max_steps: Maximum normalization iterations allowed.
        
    Returns:
        Canonical normalized Formula.
        
    Raises:
        RewriteDivergenceError: If max_steps is exceeded without reaching a fixed point.
    """
    curr = formula
    for step in range(max_steps):
        nxt = rewrite_all(curr, rules, max_root_steps=max_steps)
        if nxt == curr:
            return curr
        curr = nxt

    raise RewriteDivergenceError(
        f"Normalization diverged: failed to reach fixed point after {max_steps} steps."
    )
