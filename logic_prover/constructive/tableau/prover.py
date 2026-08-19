"""Semantic Tableaux theorem prover and Kripke countermodel builder for Intuitionistic Logic with Equality."""

from __future__ import annotations
from typing import List, Tuple, Optional, Set

from logic_prover.core.ast import (
    Formula, Term, Constant, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.parser import to_string
from logic_prover.core.substitutions import substitute_formula
from logic_prover.core.equality import CongruenceClosure, equality_substitution
from logic_prover.constructive.common import (
    FALSUM,
    _is_falsum,
    _is_verum,
    _is_atomic,
    kbo_compare,
    fresh_constant,
)
from logic_prover.constructive.ljt import _collect_constants_and_functions
from logic_prover.constructive.kripke import World, KripkeModel
from logic_prover.constructive.tableau.ast import (
    Sign,
    SignedFormula,
    TableauNode,
    TableauProofTree,
    TableauProofResult,
)
from logic_prover.constructive.tableau.branch import _BranchState


class TableauProver:
    """Automated Theorem Prover and Countermodel Builder for Intuitionistic First-Order Logic with Equality (iFOL=).

    Implements labelled semantic tableaux with explicit Kripke frame semantics and equality reasoning.

    Args:
        max_depth (int, default=100): Maximum branch depth limit.
        max_worlds (int, default=50): Maximum number of Kripke worlds allowed.
        eq_subst_max (int, default=5): Maximum equality substitution branching depth.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.tableau.prover import TableauProver
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> prover = TableauProver()
        >>> res = prover.prove(target=Implies(p, p))
        >>> res.is_valid
        True
    """

    max_depth: int
    max_worlds: int
    eq_subst_max: int
    _node_counter: int

    def __init__(self, max_depth: int = 100, max_worlds: int = 50, eq_subst_max: int = 5) -> None:
        """Initializes the tableau prover with depth, world bounds, and equality substitution limits.

        Args:
            max_depth (int, default=100): Maximum search depth.
            max_worlds (int, default=50): Maximum number of generated worlds.
            eq_subst_max (int, default=5): Maximum equality substitution steps.

        Example:
            >>> from logic_prover.constructive.tableau.prover import TableauProver
            >>> prover = TableauProver(max_depth=50)
            >>> prover.max_depth
            50
        """
        self.max_depth = max(1, max_depth)
        self.max_worlds = max(1, max_worlds)
        self.eq_subst_max = max(0, eq_subst_max)
        self._node_counter = 0

    def _next_node_id(self) -> int:
        """Generates a unique node identifier.

        Returns:
            int: Next integer ID.
        """
        self._node_counter += 1
        return self._node_counter

    def _check_clash(self, state: _BranchState) -> Optional[Tuple[World, Formula, str]]:
        """Checks if a branch contains an immediate semantic contradiction.

        Args:
            state (_BranchState): Current branch state.

        Returns:
            Optional[Tuple[World, Formula, str]]: Clash info (world, formula, explanation) or None.
        """
        for w in state.worlds:
            # 1. Falsum asserted true: w |= _bot
            for f in state.t_formulas.get(w, set()):
                if _is_falsum(f):
                    return (w, f, f"Falsum bot asserted TRUE at {w.name}")

            # 2. Verum asserted false: w |/= _top
            for f in state.f_formulas.get(w, set()):
                if _is_verum(f):
                    return (w, f, f"Verum top asserted FALSE at {w.name}")

            # 3. Direct complementary clash: w |= A and w |/= A
            t_set = state.t_formulas.get(w, set())
            f_set = state.f_formulas.get(w, set())
            common = t_set.intersection(f_set)
            if common:
                clash_formula = next(iter(common))
                return (w, clash_formula, f"Complementary clash on {to_string(clash_formula)} at {w.name}")

            # 4. Reflexivity clash: F(t = t, w)
            for f in f_set:
                if isinstance(f, Equality) and f.left == f.right:
                    return (w, f, f"Reflexivity clash on {to_string(f)} at {w.name}")

            # 5. Equality Congruence clash
            eqs = state.equalities.get(w, set())
            if eqs:
                cc = CongruenceClosure()
                for eq in eqs:
                    cc.merge(eq.left, eq.right)

                # Check if an equality in f_set is proved true by cc
                for f in f_set:
                    if isinstance(f, Equality) and cc.are_equal(f.left, f.right):
                        return (w, f, f"Equality clash on {to_string(f)} at {w.name}")

                # Check predicate congruence clash
                for tf in t_set:
                    if isinstance(tf, PredicateApp):
                        for ff in f_set:
                            if isinstance(ff, PredicateApp) and tf.pred == ff.pred and tf.arity == ff.arity:
                                if len(tf.args) == len(ff.args) and all(cc.are_equal(a1, a2) for a1, a2 in zip(tf.args, ff.args)):
                                    return (w, ff, f"Predicate congruence clash on {to_string(ff)} at {w.name}")

        return None

    def _extract_countermodel(self, state: _BranchState) -> KripkeModel:
        """Constructs an explicit Kripke countermodel from an open saturated branch.

        Args:
            state (_BranchState): Saturated open branch.

        Returns:
            KripkeModel: The constructed Kripke model (W, <=, D, V, E).
        """
        model = KripkeModel()
        for w in state.worlds:
            model.add_world(w)
        for u in state.worlds:
            for v in state.relations.get(u, set()):
                model.add_relation(u, v)
        for w in state.worlds:
            for t in state.domains.get(w, set()):
                model.add_domain_element(w, t)
            for f in state.t_formulas.get(w, set()):
                if _is_atomic(f) and not _is_falsum(f) and not _is_verum(f):
                    model.add_valuation(w, f)
            for eq in state.equalities.get(w, set()):
                model.add_equality(w, eq)
        return model

    def prove(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
    ) -> TableauProofResult:
        """Attempts to prove an intuitionistic formula or find a Kripke countermodel.

        Args:
            target (Formula): The target formula to prove.
            premises (Optional[List[Formula]], default=None): Optional list of hypothesis premises.

        Returns:
            TableauProofResult: Complete derivation result with validity status and tree.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.tableau.prover import TableauProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = TableauProver()
            >>> res = prover.prove(target=Implies(p, p))
            >>> res.is_valid
            True
        """
        self._node_counter = 0
        premise_list = tuple(premises or [])

        w0 = World(id=0, name="w0")
        initial_state = _BranchState()
        initial_state.add_world(w0)

        consts, _ = _collect_constants_and_functions(list(premise_list) + [target])
        if consts:
            for c in consts:
                initial_state.add_domain_element(w0, c)
        else:
            initial_state.add_domain_element(w0, Constant("c0"))

        for p in premise_list:
            initial_state.add_t_formula(w0, p)
        initial_state.add_f_formula(w0, target)

        root_node = TableauNode(
            id=self._next_node_id(),
            signed_formula=SignedFormula(Sign.FALSE, target, w0),
            rule="Target",
            world=w0,
        )

        is_closed, open_state = self._expand_branch(state=initial_state, node=root_node, depth=1)
        root_node.is_closed = is_closed

        tree = TableauProofTree(root=root_node)
        countermodel: Optional[KripkeModel] = None
        if not is_closed and open_state is not None:
            countermodel = self._extract_countermodel(open_state)

        return TableauProofResult(
            is_valid=is_closed,
            tree=tree,
            countermodel=countermodel,
            target=target,
            premises=premise_list,
        )

    def _expand_branch(
        self,
        state: _BranchState,
        node: TableauNode,
        depth: int,
    ) -> Tuple[bool, Optional[_BranchState]]:
        """Recursively expands a tableau branch applying semantic rules.

        Args:
            state (_BranchState): Current branch state.
            node (TableauNode): Current tree node.
            depth (int): Current tree depth.

        Returns:
            Tuple[bool, Optional[_BranchState]]: (is_closed, open_branch_state).
        """
        # Step 1: Check for contradiction / clash
        clash = self._check_clash(state)
        if clash is not None:
            w, f, desc = clash
            node.is_closed = True
            node.clash_details = desc
            return True, None

        if depth >= self.max_depth or len(state.worlds) > self.max_worlds:
            # Depth bound reached: treat as open branch
            node.is_closed = False
            return False, state

        # Step 2: Apply Non-Branching Rules
        # 2a. T(And): T(A & B, w) -> T(A, w), T(B, w)
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, And):
                    sig = ("T_And", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f, w),
                            rule="T_And",
                            world=w,
                        )
                        node.children.append(child)
                        state.add_t_formula(w, f.left)
                        state.add_t_formula(w, f.right)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 2b. F(Or): F(A | B, w) -> F(A, w), F(B, w)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, Or):
                    sig = ("F_Or", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f, w),
                            rule="F_Or",
                            world=w,
                        )
                        node.children.append(child)
                        state.add_f_formula(w, f.left)
                        state.add_f_formula(w, f.right)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 2c. T(Not): T(~A, w) -> F(A, w') for all accessible w'
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Not):
                    for w_prime in list(state.relations.get(w, set())):
                        sig = ("T_Not", f, w, w_prime)
                        if sig not in state.applied_rules:
                            state.applied_rules.add(sig)
                            child = TableauNode(
                                id=self._next_node_id(),
                                signed_formula=SignedFormula(Sign.TRUE, f, w),
                                rule="T_Not",
                                world=w_prime,
                            )
                            node.children.append(child)
                            state.add_f_formula(w_prime, f.operand)
                            is_closed, open_b = self._expand_branch(state, child, depth + 1)
                            node.is_closed = is_closed
                            return is_closed, open_b

        # 2d. F(Forall): F(forall x. A, w) -> creates fresh domain element a in D(w), F(A[a/x], w)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, Forall):
                    sig = ("F_Forall", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        all_forms = [form for w_f in state.worlds for form in (state.t_formulas.get(w_f, set()) | state.f_formulas.get(w_f, set()))]
                        existing_consts, _ = _collect_constants_and_functions(all_forms)
                        a_const = fresh_constant(prefix="a", existing_constants=existing_consts | state.domains.get(w, set()))
                        state.add_domain_element(w, a_const)
                        inst = substitute_formula(f.body, {f.variable: a_const})
                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f, w),
                            rule=f"F_Forall ({to_string(a_const)})",
                            world=w,
                        )
                        node.children.append(child)
                        state.add_f_formula(w, inst)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 2e. T(Exists): T(exists x. A, w) -> creates fresh domain element a in D(w), T(A[a/x], w)
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Exists):
                    sig = ("T_Exists", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        all_forms = [form for w_f in state.worlds for form in (state.t_formulas.get(w_f, set()) | state.f_formulas.get(w_f, set()))]
                        existing_consts, _ = _collect_constants_and_functions(all_forms)
                        a_const = fresh_constant(prefix="a", existing_constants=existing_consts | state.domains.get(w, set()))
                        state.add_domain_element(w, a_const)
                        inst = substitute_formula(f.body, {f.variable: a_const})
                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f, w),
                            rule=f"T_Exists ({to_string(a_const)})",
                            world=w,
                        )
                        node.children.append(child)
                        state.add_t_formula(w, inst)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 2f. T(Equality Subst): Oriented equality rewriting from T(s = t, w)
        for w in list(state.worlds):
            for eq in list(state.equalities.get(w, set())):
                if eq.left != eq.right:
                    cmp_res = kbo_compare(eq.left, eq.right)
                    orientations: List[Tuple[Term, Term]] = []
                    if cmp_res == "gt":
                        orientations.append((eq.left, eq.right))
                    elif cmp_res == "lt":
                        orientations.append((eq.right, eq.left))
                    else:
                        orientations.append((eq.left, eq.right))
                        orientations.append((eq.right, eq.left))

                    for src, dst in orientations:
                        eq_rule = Equality(src, dst)
                        # Substitute into T-formulas
                        for f in list(state.t_formulas.get(w, set())):
                            if f == eq:
                                continue
                            vars_t = equality_substitution(eq_rule, f)
                            for v in vars_t:
                                if v != f and v not in state.t_formulas.get(w, set()):
                                    sig = ("T_Eq_Subst_T", eq_rule, f, v, w)
                                    if sig not in state.applied_rules:
                                        state.applied_rules.add(sig)
                                        child = TableauNode(
                                            id=self._next_node_id(),
                                            signed_formula=SignedFormula(Sign.TRUE, v, w),
                                            rule=f"T_Eq_Subst ({to_string(eq_rule)})",
                                            world=w,
                                        )
                                        node.children.append(child)
                                        state.add_t_formula(w, v)
                                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                                        node.is_closed = is_closed
                                        return is_closed, open_b

                        # Substitute into F-formulas
                        for f in list(state.f_formulas.get(w, set())):
                            vars_f = equality_substitution(eq_rule, f)
                            for v in vars_f:
                                if v != f and v not in state.f_formulas.get(w, set()):
                                    sig = ("T_Eq_Subst_F", eq_rule, f, v, w)
                                    if sig not in state.applied_rules:
                                        state.applied_rules.add(sig)
                                        child = TableauNode(
                                            id=self._next_node_id(),
                                            signed_formula=SignedFormula(Sign.FALSE, v, w),
                                            rule=f"T_Eq_Subst_F ({to_string(eq_rule)})",
                                            world=w,
                                        )
                                        node.children.append(child)
                                        state.add_f_formula(w, v)
                                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                                        node.is_closed = is_closed
                                        return is_closed, open_b

        # Step 3: Apply World-Creating Rules (Kripke World Transitions)
        # 3a. F(Implies): F(A => B, w) -> creates w_new >= w with T(A, w_new), F(B, w_new)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, Implies) and not (_is_falsum(f.right)):
                    sig = ("F_Imp", f, w)
                    if sig not in state.applied_rules and len(state.worlds) < self.max_worlds:
                        state.applied_rules.add(sig)
                        new_world_id = len(state.worlds)
                        w_new = World(id=new_world_id, name=f"w{new_world_id}")
                        state.add_world(w_new)
                        state.add_relation(w, w_new)
                        state.add_t_formula(w_new, f.left)
                        state.add_f_formula(w_new, f.right)

                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f, w),
                            rule=f"F_Imp ({w.name} <= {w_new.name})",
                            world=w_new,
                        )
                        node.children.append(child)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 3b. F(Not) or F(A => _bot): F(~A, w) -> creates w_new >= w with T(A, w_new), F(_bot, w_new)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                is_neg = isinstance(f, Not)
                is_imp_bot = isinstance(f, Implies) and _is_falsum(f.right)
                if is_neg or is_imp_bot:
                    sig = ("F_Not", f, w)
                    if sig not in state.applied_rules and len(state.worlds) < self.max_worlds:
                        state.applied_rules.add(sig)
                        operand = f.operand if is_neg else f.left
                        new_world_id = len(state.worlds)
                        w_new = World(id=new_world_id, name=f"w{new_world_id}")
                        state.add_world(w_new)
                        state.add_relation(w, w_new)
                        state.add_t_formula(w_new, operand)
                        state.add_f_formula(w_new, FALSUM)

                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f, w),
                            rule=f"F_Not ({w.name} <= {w_new.name})",
                            world=w_new,
                        )
                        node.children.append(child)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # Step 4: Apply Branching Rules
        # 4a. F(And): F(A & B, w) -> F(A, w) | F(B, w)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, And):
                    sig = ("F_And", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)

                        # Left branch: F(A, w)
                        state_l = state.copy()
                        state_l.add_f_formula(w, f.left)
                        child_l = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f.left, w),
                            rule="F_And_L",
                            world=w,
                        )
                        node.children.append(child_l)
                        closed_l, open_l = self._expand_branch(state_l, child_l, depth + 1)

                        if not closed_l:
                            node.is_closed = False
                            return False, open_l

                        # Right branch: F(B, w)
                        state_r = state.copy()
                        state_r.add_f_formula(w, f.right)
                        child_r = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, f.right, w),
                            rule="F_And_R",
                            world=w,
                        )
                        node.children.append(child_r)
                        closed_r, open_r = self._expand_branch(state_r, child_r, depth + 1)

                        node.is_closed = closed_l and closed_r
                        return node.is_closed, open_r if not closed_r else None

        # 4b. T(Or): T(A | B, w) -> T(A, w) | T(B, w)
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Or):
                    sig = ("T_Or", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)

                        # Left branch: T(A, w)
                        state_l = state.copy()
                        state_l.add_t_formula(w, f.left)
                        child_l = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f.left, w),
                            rule="T_Or_L",
                            world=w,
                        )
                        node.children.append(child_l)
                        closed_l, open_l = self._expand_branch(state_l, child_l, depth + 1)

                        if not closed_l:
                            node.is_closed = False
                            return False, open_l

                        # Right branch: T(B, w)
                        state_r = state.copy()
                        state_r.add_t_formula(w, f.right)
                        child_r = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f.right, w),
                            rule="T_Or_R",
                            world=w,
                        )
                        node.children.append(child_r)
                        closed_r, open_r = self._expand_branch(state_r, child_r, depth + 1)

                        node.is_closed = closed_l and closed_r
                        return node.is_closed, open_r if not closed_r else None

        # 4c. T(Implies): T(A => B, w) -> for all accessible w' >= w, F(A, w') | T(B, w')
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Implies) and not _is_falsum(f.right):
                    for w_prime in list(state.relations.get(w, set())):
                        sig = ("T_Imp", f, w, w_prime)
                        if sig not in state.applied_rules:
                            state.applied_rules.add(sig)

                            # Left branch: F(A, w')
                            state_l = state.copy()
                            state_l.add_f_formula(w_prime, f.left)
                            child_l = TableauNode(
                                id=self._next_node_id(),
                                signed_formula=SignedFormula(Sign.FALSE, f.left, w_prime),
                                rule=f"T_Imp_F ({w_prime.name})",
                                world=w_prime,
                            )
                            node.children.append(child_l)
                            closed_l, open_l = self._expand_branch(state_l, child_l, depth + 1)

                            if not closed_l:
                                node.is_closed = False
                                return False, open_l

                            # Right branch: T(B, w')
                            state_r = state.copy()
                            state_r.add_t_formula(w_prime, f.right)
                            child_r = TableauNode(
                                id=self._next_node_id(),
                                signed_formula=SignedFormula(Sign.TRUE, f.right, w_prime),
                                rule=f"T_Imp_T ({w_prime.name})",
                                world=w_prime,
                            )
                            node.children.append(child_r)
                            closed_r, open_r = self._expand_branch(state_r, child_r, depth + 1)

                            node.is_closed = closed_l and closed_r
                            return node.is_closed, open_r if not closed_r else None

        # 4d. T(Iff): T(A <=> B, w) -> T(A => B, w), T(B => A, w)
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Iff):
                    sig = ("T_Iff", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        imp1 = Implies(left=f.left, right=f.right)
                        imp2 = Implies(left=f.right, right=f.left)
                        state.add_t_formula(w, imp1)
                        state.add_t_formula(w, imp2)
                        child = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.TRUE, f, w),
                            rule="T_Iff",
                            world=w,
                        )
                        node.children.append(child)
                        is_closed, open_b = self._expand_branch(state, child, depth + 1)
                        node.is_closed = is_closed
                        return is_closed, open_b

        # 4e. F(Iff): F(A <=> B, w) -> F(A => B, w) | F(B => A, w)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, Iff):
                    sig = ("F_Iff", f, w)
                    if sig not in state.applied_rules:
                        state.applied_rules.add(sig)
                        imp1 = Implies(left=f.left, right=f.right)
                        imp2 = Implies(left=f.right, right=f.left)

                        # Left branch: F(A => B, w)
                        state_l = state.copy()
                        state_l.add_f_formula(w, imp1)
                        child_l = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, imp1, w),
                            rule="F_Iff_L",
                            world=w,
                        )
                        node.children.append(child_l)
                        closed_l, open_l = self._expand_branch(state_l, child_l, depth + 1)

                        if not closed_l:
                            node.is_closed = False
                            return False, open_l

                        # Right branch: F(B => A, w)
                        state_r = state.copy()
                        state_r.add_f_formula(w, imp2)
                        child_r = TableauNode(
                            id=self._next_node_id(),
                            signed_formula=SignedFormula(Sign.FALSE, imp2, w),
                            rule="F_Iff_R",
                            world=w,
                        )
                        node.children.append(child_r)
                        closed_r, open_r = self._expand_branch(state_r, child_r, depth + 1)

                        node.is_closed = closed_l and closed_r
                        return node.is_closed, open_r if not closed_r else None

        # 4f. T(Forall): T(forall x. A, w) -> for all accessible w' >= w and t in D(w'), T(A[t/x], w')
        for w in list(state.worlds):
            for f in list(state.t_formulas.get(w, set())):
                if isinstance(f, Forall):
                    for w_prime in list(state.relations.get(w, set())):
                        for t in list(state.domains.get(w_prime, set())):
                            sig = ("T_Forall", f, w, w_prime, t)
                            if sig not in state.applied_rules:
                                state.applied_rules.add(sig)
                                inst = substitute_formula(f.body, {f.variable: t})
                                child = TableauNode(
                                    id=self._next_node_id(),
                                    signed_formula=SignedFormula(Sign.TRUE, inst, w_prime),
                                    rule=f"T_Forall ({w_prime.name}, {to_string(t)})",
                                    world=w_prime,
                                )
                                node.children.append(child)
                                state.add_t_formula(w_prime, inst)
                                is_closed, open_b = self._expand_branch(state, child, depth + 1)
                                node.is_closed = is_closed
                                return is_closed, open_b

        # 4g. F(Exists): F(exists x. A, w) -> for all t in D(w), F(A[t/x], w)
        for w in list(state.worlds):
            for f in list(state.f_formulas.get(w, set())):
                if isinstance(f, Exists):
                    for t in list(state.domains.get(w, set())):
                        sig = ("F_Exists", f, w, t)
                        if sig not in state.applied_rules:
                            state.applied_rules.add(sig)
                            inst = substitute_formula(f.body, {f.variable: t})
                            child = TableauNode(
                                id=self._next_node_id(),
                                signed_formula=SignedFormula(Sign.FALSE, inst, w),
                                rule=f"F_Exists ({w.name}, {to_string(t)})",
                                world=w,
                            )
                            node.children.append(child)
                            state.add_f_formula(w, inst)
                            is_closed, open_b = self._expand_branch(state, child, depth + 1)
                            node.is_closed = is_closed
                            return is_closed, open_b

        # Step 5: Saturated branch with no further rules applicable and no clash
        node.is_closed = False
        return False, state

    def is_valid(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
    ) -> bool:
        """Checks whether a formula is intuitionistically valid using semantic tableaux.

        Args:
            target (Formula): Formula AST to test.
            premises (Optional[List[Formula]], default=None): Optional hypothesis formulas.

        Returns:
            bool: True if intuitionistically provable, False otherwise.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Implies
            >>> from logic_prover.constructive.tableau.prover import TableauProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = TableauProver()
            >>> prover.is_valid(Implies(p, p))
            True
        """
        result = self.prove(target=target, premises=premises)
        return result.is_valid

    def countermodel(
        self,
        target: Formula,
        premises: Optional[List[Formula]] = None,
    ) -> Optional[KripkeModel]:
        """Extracts a Kripke countermodel falsifying the formula if it is not valid.

        Args:
            target (Formula): Formula AST to check.
            premises (Optional[List[Formula]], default=None): Optional hypothesis formulas.

        Returns:
            Optional[KripkeModel]: Falsifying Kripke countermodel if unprovable, None if valid.

        Example:
            >>> from logic_prover.core.ast import PredicateApp, Or, Not
            >>> from logic_prover.constructive.tableau.prover import TableauProver
            >>> p = PredicateApp(pred="P", arity=0, args=())
            >>> prover = TableauProver()
            >>> cm = prover.countermodel(Or(p, Not(p)))
            >>> cm is not None
            True
        """
        result = self.prove(target=target, premises=premises)
        return result.countermodel


def prove_tableau(
    formula: Formula,
    premises: Optional[List[Formula]] = None,
    max_depth: int = 100,
    max_worlds: int = 50,
    eq_subst_max: int = 5,
) -> TableauProofResult:
    """Proves an intuitionistic formula or extracts a Kripke countermodel via semantic tableaux with equality.

    Args:
        formula (Formula): Target formula AST to prove.
        premises (Optional[List[Formula]], default=None): Optional list of hypothesis formulas.
        max_depth (int, default=100): Maximum search depth bound.
        max_worlds (int, default=50): Maximum number of possible worlds to construct.
        eq_subst_max (int, default=5): Maximum number of equality substitution steps.

    Returns:
        TableauProofResult: Complete derivation result container with tree and countermodel.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Implies
        >>> from logic_prover.constructive.tableau.prover import prove_tableau
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> res = prove_tableau(Implies(p, p))
        >>> res.is_valid
        True
    """
    prover = TableauProver(max_depth=max_depth, max_worlds=max_worlds, eq_subst_max=eq_subst_max)
    return prover.prove(target=formula, premises=premises)


__all__ = [
    "TableauProver",
    "prove_tableau",
]
