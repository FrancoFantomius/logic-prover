"""Congruence closure algorithms for tracking ground term equivalences and function congruences."""

from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple, Union
from collections import deque

from solver.core.ast import (
    Term, Formula, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from solver.core.sorts import is_compatible
from solver.core.exceptions import ValidationError


class CongruenceClosure:
    """Congruence closure subsystem for tracking term equivalences and propagating function congruences."""

    def __init__(self) -> None:
        """Initializes an empty CongruenceClosure instance."""
        self._parent: Dict[Term, Term] = {}
        self._rank: Dict[Term, int] = {}
        self._terms: Set[Term] = set()
        self._use_list: Dict[Term, Set[FunctionApp]] = {}
        self._lookup: Dict[Tuple[str, Tuple[Term, ...]], FunctionApp] = {}
        self._proof_graph: Dict[Term, List[Tuple[Term, Equality]]] = {}

    def add_term(self, term: Term) -> None:
        """Recursively registers a term and all its subterms in the congruence graph.
        
        Args:
            term: The Term instance to add.
        """
        if term in self._terms:
            return

        self._terms.add(term)
        self._parent[term] = term
        self._rank[term] = 0
        self._proof_graph[term] = []

        if isinstance(term, FunctionApp):
            # Recursively register subterm arguments
            for arg in term.args:
                self.add_term(arg)

            # Determine argument representatives
            arg_reps = tuple(self.find(arg) for arg in term.args)

            # Add to use_list of each argument representative
            for arg_rep in set(arg_reps):
                if arg_rep not in self._use_list:
                    self._use_list[arg_rep] = set()
                self._use_list[arg_rep].add(term)

            # Check lookup table for existing congruent function application
            lookup_key = (term.func, arg_reps)
            if lookup_key in self._lookup:
                existing = self._lookup[lookup_key]
                if existing != term:
                    self.merge(term, existing)
            else:
                self._lookup[lookup_key] = term

    def find(self, term: Term) -> Term:
        """Finds the equivalence class representative of a term with path compression.
        
        Args:
            term: The term to look up.
            
        Returns:
            The representative Term instance.
        """
        if term not in self._parent:
            self.add_term(term)
            return term

        path: List[Term] = []
        curr = term
        while self._parent[curr] != curr:
            path.append(curr)
            curr = self._parent[curr]

        # Path compression
        for node in path:
            self._parent[node] = curr

        return curr

    def merge(self, t1: Term, t2: Term) -> None:
        """Asserts t1 = t2 and propagates congruence through function applications.
        
        Args:
            t1: Left term of equality.
            t2: Right term of equality.
        """
        self.add_term(t1)
        self.add_term(t2)

        # Iterative queue to prevent recursion depth exhaustion on deep congruence trees
        pending: deque[Tuple[Term, Term]] = deque([(t1, t2)])

        while pending:
            u, v = pending.popleft()
            r1 = self.find(u)
            r2 = self.find(v)

            if r1 == r2:
                continue

            # Record undirected edge in explanation graph
            eq_edge = Equality(u, v)
            self._proof_graph[u].append((v, eq_edge))
            self._proof_graph[v].append((u, eq_edge))

            # Union-by-rank
            if self._rank[r1] < self._rank[r2]:
                r1, r2 = r2, r1

            self._parent[r2] = r1
            if self._rank[r1] == self._rank[r2]:
                self._rank[r1] += 1

            # Combine use lists and detect new congruences
            use_r1 = self._use_list.get(r1, set())
            use_r2 = self._use_list.get(r2, set())

            for f1 in use_r1:
                for f2 in use_r2:
                    if f1.func == f2.func and len(f1.args) == len(f2.args):
                        reps1 = tuple(self.find(a) for a in f1.args)
                        reps2 = tuple(self.find(a) for a in f2.args)
                        if reps1 == reps2 and self.find(f1) != self.find(f2):
                            pending.append((f1, f2))

            # Update combined use_list
            self._use_list[r1] = use_r1.union(use_r2)
            if r2 in self._use_list:
                del self._use_list[r2]

    def are_equal(self, t1: Term, t2: Term) -> bool:
        """Checks if two terms belong to the same equivalence class.
        
        Args:
            t1: First term.
            t2: Second term.
            
        Returns:
            True if t1 and t2 are proven equal, False otherwise.
        """
        self.add_term(t1)
        self.add_term(t2)
        return self.find(t1) == self.find(t2)

    def explain(self, t1: Term, t2: Term) -> Optional[List[Equality]]:
        """Generates a chain of Equalities proving t1 = t2 using BFS pathfinding on the proof graph.
        
        Args:
            t1: Start term.
            t2: Target term.
            
        Returns:
            List of Equality steps proving t1 = t2, empty list if t1 == t2, or None if not equal.
        """
        if not self.are_equal(t1, t2):
            return None

        if t1 == t2:
            return []

        # BFS for shortest path in undirected proof graph
        queue: deque[Tuple[Term, List[Equality]]] = deque([(t1, [])])
        visited: Set[Term] = {t1}

        while queue:
            curr, path = queue.popleft()
            if curr == t2:
                return path

            for nxt, edge in self._proof_graph.get(curr, []):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [edge]))

        return None


def equality_substitution(eq: Equality, formula: Formula) -> List[Formula]:
    """Generates all non-trivial formulas obtained by replacing occurrences of eq.left with eq.right or vice versa.
    
    Args:
        eq: The Equality rule (t1 = t2).
        formula: Target formula to perform substitutions on.
        
    Returns:
        List of distinct newly formed Formula objects.
    """
    t1, t2 = eq.left, eq.right
    results: Set[Formula] = set()

    def term_variants(term: Term, src: Term, dst: Term) -> List[Term]:
        variants: List[Term] = []
        if term == src:
            variants.append(dst)
        if isinstance(term, FunctionApp):
            args_variants = [term_variants(arg, src, dst) for arg in term.args]
            def combine_args(idx: int) -> List[Tuple[Term, ...]]:
                if idx == len(args_variants):
                    return [()]
                res: List[Tuple[Term, ...]] = []
                for head in args_variants[idx]:
                    for tail in combine_args(idx + 1):
                        res.append((head,) + tail)
                return res

            for new_args in combine_args(0):
                variants.append(FunctionApp(term.func, term.arity, new_args, term.return_sort))

        variants.append(term)
        unique: List[Term] = []
        for v in variants:
            if v not in unique:
                unique.append(v)
        return unique

    def formula_variants(fmt: Formula, src: Term, dst: Term) -> List[Formula]:
        variants: List[Formula] = []
        if isinstance(fmt, Equality):
            left_vars = term_variants(fmt.left, src, dst)
            right_vars = term_variants(fmt.right, src, dst)
            for l in left_vars:
                for r in right_vars:
                    variants.append(Equality(l, r))
        elif isinstance(fmt, PredicateApp):
            args_vars = [term_variants(arg, src, dst) for arg in fmt.args]
            def combine_pred_args(idx: int) -> List[Tuple[Term, ...]]:
                if idx == len(args_vars):
                    return [()]
                res: List[Tuple[Term, ...]] = []
                for head in args_vars[idx]:
                    for tail in combine_pred_args(idx + 1):
                        res.append((head,) + tail)
                return res

            for new_args in combine_pred_args(0):
                variants.append(PredicateApp(fmt.pred, fmt.arity, new_args))
        elif isinstance(fmt, Not):
            for sub in formula_variants(fmt.operand, src, dst):
                variants.append(Not(sub))
        elif isinstance(fmt, And):
            for l in formula_variants(fmt.left, src, dst):
                for r in formula_variants(fmt.right, src, dst):
                    variants.append(And(l, r))
        elif isinstance(fmt, Or):
            for l in formula_variants(fmt.left, src, dst):
                for r in formula_variants(fmt.right, src, dst):
                    variants.append(Or(l, r))
        elif isinstance(fmt, Implies):
            for l in formula_variants(fmt.left, src, dst):
                for r in formula_variants(fmt.right, src, dst):
                    variants.append(Implies(l, r))
        elif isinstance(fmt, Iff):
            for l in formula_variants(fmt.left, src, dst):
                for r in formula_variants(fmt.right, src, dst):
                    variants.append(Iff(l, r))
        elif isinstance(fmt, Forall):
            for b in formula_variants(fmt.body, src, dst):
                variants.append(Forall(fmt.variable, b))
        elif isinstance(fmt, Exists):
            for b in formula_variants(fmt.body, src, dst):
                variants.append(Exists(fmt.variable, b))
        else:
            variants.append(fmt)

        unique: List[Formula] = []
        for v in variants:
            if v not in unique:
                unique.append(v)
        return unique

    for f_var in formula_variants(formula, t1, t2):
        if f_var != formula:
            results.add(f_var)

    for f_var in formula_variants(formula, t2, t1):
        if f_var != formula:
            results.add(f_var)

    return list(results)
