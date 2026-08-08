"""AST Visitor pattern implementations for traversal, size computation, and serialization."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union, Set, Dict, Optional, Tuple, List

from logic.core.ast import (
    Term, Variable, Constant, FunctionApp,
    Formula, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic.sol.ast_ext import (
    ForallPred, ExistsPred, ForallFunc, ExistsFunc, PredicateVariable, FunctionVariable
)
from logic.core.sorts import Sort, PrimitiveSort, ParameterizedSort, FunctionSort, Ind, Nat, Bool

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
        elif isinstance(node, ForallPred):
            return self.visit_forall_pred(node)
        elif isinstance(node, ExistsPred):
            return self.visit_exists_pred(node)
        elif isinstance(node, ForallFunc):
            return self.visit_forall_func(node)
        elif isinstance(node, ExistsFunc):
            return self.visit_exists_func(node)
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

    def visit_forall_pred(self, node: ForallPred) -> T:
        raise NotImplementedError

    def visit_exists_pred(self, node: ExistsPred) -> T:
        raise NotImplementedError

    def visit_forall_func(self, node: ForallFunc) -> T:
        raise NotImplementedError

    def visit_exists_func(self, node: ExistsFunc) -> T:
        raise NotImplementedError


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
        # Ensure all args are Terms for typing
        args_terms = tuple(arg for arg in new_args if isinstance(arg, Term))
        return FunctionApp(func=node.func, arity=node.arity, args=args_terms, return_sort=node.return_sort)

    def visit_predicate_app(self, node: PredicateApp) -> Formula:
        new_args = tuple(self.visit(arg) for arg in node.args)
        if all(new_arg is orig for new_arg, orig in zip(new_args, node.args)):
            return node
        args_terms = tuple(arg for arg in new_args if isinstance(arg, Term))
        return PredicateApp(pred=node.pred, arity=node.arity, args=args_terms)

    def visit_equality(self, node: Equality) -> Formula:
        new_left = self.visit(node.left)
        new_right = self.visit(node.right)
        if new_left is node.left and new_right is node.right:
            return node
        assert isinstance(new_left, Term) and isinstance(new_right, Term)
        return Equality(left=new_left, right=new_right)

    def visit_not(self, node: Not) -> Formula:
        new_op = self.visit(node.operand)
        if new_op is node.operand:
            return node
        assert isinstance(new_op, Formula)
        return Not(operand=new_op)

    def visit_and(self, node: And) -> Formula:
        new_l = self.visit(node.left)
        new_r = self.visit(node.right)
        if new_l is node.left and new_r is node.right:
            return node
        assert isinstance(new_l, Formula) and isinstance(new_r, Formula)
        return And(left=new_l, right=new_r)

    def visit_or(self, node: Or) -> Formula:
        new_l = self.visit(node.left)
        new_r = self.visit(node.right)
        if new_l is node.left and new_r is node.right:
            return node
        assert isinstance(new_l, Formula) and isinstance(new_r, Formula)
        return Or(left=new_l, right=new_r)

    def visit_implies(self, node: Implies) -> Formula:
        new_l = self.visit(node.left)
        new_r = self.visit(node.right)
        if new_l is node.left and new_r is node.right:
            return node
        assert isinstance(new_l, Formula) and isinstance(new_r, Formula)
        return Implies(left=new_l, right=new_r)

    def visit_iff(self, node: Iff) -> Formula:
        new_l = self.visit(node.left)
        new_r = self.visit(node.right)
        if new_l is node.left and new_r is node.right:
            return node
        assert isinstance(new_l, Formula) and isinstance(new_r, Formula)
        return Iff(left=new_l, right=new_r)

    def visit_forall(self, node: Forall) -> Formula:
        new_var = self.visit(node.variable)
        new_body = self.visit(node.body)
        if new_var is node.variable and new_body is node.body:
            return node
        assert isinstance(new_var, Variable) and isinstance(new_body, Formula)
        return Forall(variable=new_var, body=new_body)

    def visit_exists(self, node: Exists) -> Formula:
        new_var = self.visit(node.variable)
        new_body = self.visit(node.body)
        if new_var is node.variable and new_body is node.body:
            return node
        assert isinstance(new_var, Variable) and isinstance(new_body, Formula)
        return Exists(variable=new_var, body=new_body)

    def visit_forall_pred(self, node: ForallPred) -> Formula:
        new_body = self.visit(node.body)
        if new_body is node.body:
            return node
        assert isinstance(new_body, Formula)
        return ForallPred(variable=node.variable, body=new_body)

    def visit_exists_pred(self, node: ExistsPred) -> Formula:
        new_body = self.visit(node.body)
        if new_body is node.body:
            return node
        assert isinstance(new_body, Formula)
        return ExistsPred(variable=node.variable, body=new_body)

    def visit_forall_func(self, node: ForallFunc) -> Formula:
        new_body = self.visit(node.body)
        if new_body is node.body:
            return node
        assert isinstance(new_body, Formula)
        return ForallFunc(variable=node.variable, body=new_body)

    def visit_exists_func(self, node: ExistsFunc) -> Formula:
        new_body = self.visit(node.body)
        if new_body is node.body:
            return node
        assert isinstance(new_body, Formula)
        return ExistsFunc(variable=node.variable, body=new_body)


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

    def visit_forall_pred(self, node: ForallPred) -> int:
        return 1 + self.visit(node.body)

    def visit_exists_pred(self, node: ExistsPred) -> int:
        return 1 + self.visit(node.body)

    def visit_forall_func(self, node: ForallFunc) -> int:
        return 1 + self.visit(node.body)

    def visit_exists_func(self, node: ExistsFunc) -> int:
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
        return 1 + self.visit(node.variable) + self.visit(node.body)

    def visit_exists(self, node: Exists) -> int:
        return 1 + self.visit(node.variable) + self.visit(node.body)

    def visit_forall_pred(self, node: ForallPred) -> int:
        return 1 + self.visit(node.body)

    def visit_exists_pred(self, node: ExistsPred) -> int:
        return 1 + self.visit(node.body)

    def visit_forall_func(self, node: ForallFunc) -> int:
        return 1 + self.visit(node.body)

    def visit_exists_func(self, node: ExistsFunc) -> int:
        return 1 + self.visit(node.body)


class FreeVariableCollector(ASTVisitor[Set[Variable]]):
    """Collects all free individual variables in a term or formula."""

    def visit_variable(self, node: Variable) -> Set[Variable]:
        return {node}

    def visit_constant(self, node: Constant) -> Set[Variable]:
        return set()

    def visit_function_app(self, node: FunctionApp) -> Set[Variable]:
        res: Set[Variable] = set()
        for arg in node.args:
            res.update(self.visit(arg))
        return res

    def visit_predicate_app(self, node: PredicateApp) -> Set[Variable]:
        res: Set[Variable] = set()
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

    def visit_forall_pred(self, node: ForallPred) -> Set[Variable]:
        return self.visit(node.body)

    def visit_exists_pred(self, node: ExistsPred) -> Set[Variable]:
        return self.visit(node.body)

    def visit_forall_func(self, node: ForallFunc) -> Set[Variable]:
        return self.visit(node.body)

    def visit_exists_func(self, node: ExistsFunc) -> Set[Variable]:
        return self.visit(node.body)


class SubstitutionTransformer(ASTTransformer):
    """Applies variable substitutions to terms and formulas with capture avoidance."""

    def __init__(self, mapping: Dict[Variable, Term]) -> None:
        """Initializes the substitution transformer with a variable to term mapping."""
        self.mapping = mapping

    def visit_variable(self, node: Variable) -> Term:
        return self.mapping.get(node, node)

    def visit_forall(self, node: Forall) -> Formula:
        bound_var = node.variable
        replacement_free_vars: Set[Variable] = set()
        collector = FreeVariableCollector()
        for v, t in self.mapping.items():
            if v != bound_var:
                replacement_free_vars.update(collector.visit(t))

        if bound_var in replacement_free_vars:
            body_free_vars = collector.visit(node.body)
            mapping_keys = set(self.mapping.keys())
            all_vars = body_free_vars | replacement_free_vars | mapping_keys
            max_idx = max((v.id for v in all_vars), default=0) + 1
            fresh_var = Variable(id=max_idx, sort=bound_var.sort, kind=bound_var.kind)

            renamed_body = SubstitutionTransformer({bound_var: fresh_var}).visit(node.body)
            assert isinstance(renamed_body, Formula)
            new_body = self.visit(renamed_body)
            assert isinstance(new_body, Formula)
            return Forall(variable=fresh_var, body=new_body)
        else:
            inner_mapping = {v: t for v, t in self.mapping.items() if v != bound_var}
            new_body = SubstitutionTransformer(inner_mapping).visit(node.body)
            assert isinstance(new_body, Formula)
            return Forall(variable=bound_var, body=new_body)

    def visit_exists(self, node: Exists) -> Formula:
        bound_var = node.variable
        replacement_free_vars: Set[Variable] = set()
        collector = FreeVariableCollector()
        for v, t in self.mapping.items():
            if v != bound_var:
                replacement_free_vars.update(collector.visit(t))

        if bound_var in replacement_free_vars:
            body_free_vars = collector.visit(node.body)
            mapping_keys = set(self.mapping.keys())
            all_vars = body_free_vars | replacement_free_vars | mapping_keys
            max_idx = max((v.id for v in all_vars), default=0) + 1
            fresh_var = Variable(id=max_idx, sort=bound_var.sort, kind=bound_var.kind)

            renamed_body = SubstitutionTransformer({bound_var: fresh_var}).visit(node.body)
            assert isinstance(renamed_body, Formula)
            new_body = self.visit(renamed_body)
            assert isinstance(new_body, Formula)
            return Exists(variable=fresh_var, body=new_body)
        else:
            inner_mapping = {v: t for v, t in self.mapping.items() if v != bound_var}
            new_body = SubstitutionTransformer(inner_mapping).visit(node.body)
            assert isinstance(new_body, Formula)
            return Exists(variable=bound_var, body=new_body)


class ExportVisitor(ASTVisitor[str]):
    """Translates AST to string in various notations ('infix', 'prefix', 'latex')."""

    def __init__(self, notation: str = "infix") -> None:
        """Initializes ExportVisitor with string notation."""
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
        func_str = node.func.name if hasattr(node.func, "name") else str(node.func)
        if self.notation == "prefix":
            args_str = " ".join(self.visit(arg) for arg in node.args)
            return f"({func_str} {args_str})" if node.args else func_str
        args_str = ", ".join(self.visit(arg) for arg in node.args)
        return f"{func_str}({args_str})"

    def visit_predicate_app(self, node: PredicateApp) -> str:
        pred_str = node.pred.name if hasattr(node.pred, "name") else str(node.pred)
        if not node.args:
            return pred_str
        if self.notation == "prefix":
            args_str = " ".join(self.visit(arg) for arg in node.args)
            return f"({pred_str} {args_str})"
        args_str = ", ".join(self.visit(arg) for arg in node.args)
        return f"{pred_str}({args_str})"

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
        sort_str = node.variable.sort.name
        if self.notation == "prefix":
            return f"(forall ({v_str} : {sort_str}) {b_str})"
        elif self.notation == "latex":
            return f"\\forall {v_str} : {sort_str}, {b_str}"
        return f"forall {v_str} : {sort_str}, {b_str}"

    def visit_exists(self, node: Exists) -> str:
        v_str = self.visit(node.variable)
        b_str = self.visit(node.body)
        sort_str = node.variable.sort.name
        if self.notation == "prefix":
            return f"(exists ({v_str} : {sort_str}) {b_str})"
        elif self.notation == "latex":
            return f"\\exists {v_str} : {sort_str}, {b_str}"
        return f"exists {v_str} : {sort_str}, {b_str}"

    def visit_forall_pred(self, node: ForallPred) -> str:
        b_str = self.visit(node.body)
        p_str = node.variable.name
        if self.notation == "prefix":
            return f"(forall_pred ({p_str}) {b_str})"
        elif self.notation == "latex":
            return f"\\forall {p_str}, {b_str}"
        return f"forall_pred {p_str}, {b_str}"

    def visit_exists_pred(self, node: ExistsPred) -> str:
        b_str = self.visit(node.body)
        p_str = node.variable.name
        if self.notation == "prefix":
            return f"(exists_pred ({p_str}) {b_str})"
        elif self.notation == "latex":
            return f"\\exists {p_str}, {b_str}"
        return f"exists_pred {p_str}, {b_str}"

    def visit_forall_func(self, node: ForallFunc) -> str:
        b_str = self.visit(node.body)
        f_str = node.variable.name
        if self.notation == "prefix":
            return f"(forall_func ({f_str}) {b_str})"
        elif self.notation == "latex":
            return f"\\forall {f_str}, {b_str}"
        return f"forall_func {f_str}, {b_str}"

    def visit_exists_func(self, node: ExistsFunc) -> str:
        b_str = self.visit(node.body)
        f_str = node.variable.name
        if self.notation == "prefix":
            return f"(exists_func ({f_str}) {b_str})"
        elif self.notation == "latex":
            return f"\\exists {f_str}, {b_str}"
        return f"exists_func {f_str}, {b_str}"
