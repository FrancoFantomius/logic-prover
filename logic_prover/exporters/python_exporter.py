"""Python code generator translating Curry-Howard proof terms into executable Python functions.

Converts ProofTerm AST nodes into standard library ast.AST nodes, applies beta-normalization,
synthesizes type annotations, and unparses into formatted, runnable Python code.
"""

from __future__ import annotations
import ast
import re
from typing import Optional, List, Tuple, Sequence, Any, Union

from logic_prover.constructive.terms import (
    ProofTerm, ProofType, Var, Abs, App, Pair, Fst, Snd, Inl, Inr, Case,
    Unit, Abort, Refl, Subst, ExistsIntro, ExistsElim, NatRec,
    beta_normalize, infer_type
)
from logic_prover.exporters.python_runtime import type_to_python_annotation


class PythonExporter:
    """Translates constructive ProofTerm AST nodes into executable Python code."""

    def __init__(self, sanitize_identifiers: bool = True) -> None:
        """Initializes the PythonExporter instance.

        Args:
            sanitize_identifiers (bool, default=True): Whether to sanitize variable names to valid Python identifiers.

        Example:
            >>> from logic_prover.exporters.python_exporter import PythonExporter
            >>> exporter = PythonExporter()
            >>> isinstance(exporter, PythonExporter)
            True
        """
        self.sanitize_identifiers = sanitize_identifiers

    def _sanitize(self, name: str) -> str:
        """Sanitizes an identifier to ensure it is a valid Python variable name.

        Args:
            name (str): Original identifier name.

        Returns:
            str: Valid Python identifier.
        """
        if not self.sanitize_identifiers:
            return name
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if clean and clean[0].isdigit():
            clean = f"v_{clean}"
        return clean or "v"

    def term_to_ast(self, term: ProofTerm) -> ast.expr:
        """Translates a ProofTerm AST node into a corresponding Python ast.expr node.

        Args:
            term (ProofTerm): The proof term to translate.

        Returns:
            ast.expr: Synthesized Python AST expression node.

        Raises:
            TypeError: If the term type is unrecognized.

        Example:
            >>> import ast
            >>> from logic_prover.constructive.terms import Var
            >>> from logic_prover.exporters.python_exporter import PythonExporter
            >>> exp = PythonExporter()
            >>> node = exp.term_to_ast(Var("x"))
            >>> isinstance(node, ast.Name)
            True
        """
        if isinstance(term, Var):
            if re.match(r"^c\d+$", term.name):
                return ast.Constant(value=term.name)
            return ast.Name(id=self._sanitize(term.name), ctx=ast.Load())

        elif isinstance(term, Abs):
            arg_node = ast.arg(arg=self._sanitize(term.var))
            body_node = self.term_to_ast(term.body)
            args_node = ast.arguments(
                posonlyargs=[],
                args=[arg_node],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            )
            return ast.Lambda(args=args_node, body=body_node)

        elif isinstance(term, App):
            fn_node = self.term_to_ast(term.fn)
            arg_node = self.term_to_ast(term.arg)
            return ast.Call(func=fn_node, args=[arg_node], keywords=[])

        elif isinstance(term, Pair):
            left_node = self.term_to_ast(term.left)
            right_node = self.term_to_ast(term.right)
            return ast.Tuple(elts=[left_node, right_node], ctx=ast.Load())

        elif isinstance(term, Fst):
            inner_node = self.term_to_ast(term.term)
            return ast.Subscript(
                value=inner_node,
                slice=ast.Constant(value=0),
                ctx=ast.Load(),
            )

        elif isinstance(term, Snd):
            inner_node = self.term_to_ast(term.term)
            return ast.Subscript(
                value=inner_node,
                slice=ast.Constant(value=1),
                ctx=ast.Load(),
            )

        elif isinstance(term, Inl):
            inner_node = self.term_to_ast(term.term)
            return ast.Call(
                func=ast.Name(id="Left", ctx=ast.Load()),
                args=[inner_node],
                keywords=[],
            )

        elif isinstance(term, Inr):
            inner_node = self.term_to_ast(term.term)
            return ast.Call(
                func=ast.Name(id="Right", ctx=ast.Load()),
                args=[inner_node],
                keywords=[],
            )

        elif isinstance(term, Case):
            # Functional case elimination:
            # (lambda _s: ((lambda lv: lb)(_s.value) if isinstance(_s, Left) else (lambda rv: rb)(_s.value)))(scrutinee)
            s_node = self.term_to_ast(term.scrutinee)
            lv_name = self._sanitize(term.left_var)
            rv_name = self._sanitize(term.right_var)
            lb_node = self.term_to_ast(term.left_body)
            rb_node = self.term_to_ast(term.right_body)

            left_lambda = ast.Lambda(
                args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=lv_name)], kwonlyargs=[], kw_defaults=[], defaults=[]),
                body=lb_node,
            )
            right_lambda = ast.Lambda(
                args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=rv_name)], kwonlyargs=[], kw_defaults=[], defaults=[]),
                body=rb_node,
            )

            s_var = ast.Name(id="_s", ctx=ast.Load())
            s_val = ast.Attribute(value=s_var, attr="value", ctx=ast.Load())
            is_left_test = ast.Call(
                func=ast.Name(id="isinstance", ctx=ast.Load()),
                args=[s_var, ast.Name(id="Left", ctx=ast.Load())],
                keywords=[],
            )
            call_left = ast.Call(func=left_lambda, args=[s_val], keywords=[])
            call_right = ast.Call(func=right_lambda, args=[s_val], keywords=[])

            if_exp = ast.IfExp(test=is_left_test, body=call_left, orelse=call_right)
            outer_lambda = ast.Lambda(
                args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="_s")], kwonlyargs=[], kw_defaults=[], defaults=[]),
                body=if_exp,
            )
            return ast.Call(func=outer_lambda, args=[s_node], keywords=[])

        elif isinstance(term, Unit):
            return ast.Constant(value=None)

        elif isinstance(term, Abort):
            return ast.Call(func=ast.Name(id="_abort", ctx=ast.Load()), args=[], keywords=[])

        elif isinstance(term, Refl):
            return ast.Constant(value=None)

        elif isinstance(term, Subst):
            return self.term_to_ast(term.term)

        elif isinstance(term, ExistsIntro):
            # ⟨witness, proof⟩ -> (witness, proof)
            w_val = term.witness
            if isinstance(w_val, (int, float, str, bool)):
                w_node = ast.Constant(value=w_val)
            elif hasattr(w_val, "name"):
                w_node = ast.Constant(value=w_val.name)
            else:
                w_node = ast.Constant(value=str(w_val))
            p_node = self.term_to_ast(term.proof)
            return ast.Tuple(elts=[w_node, p_node], ctx=ast.Load())

        elif isinstance(term, ExistsElim):
            # unpack s as ⟨wv, pv⟩ in body -> (lambda _ex: (lambda wv, pv: body)(_ex[0], _ex[1]))(s)
            s_node = self.term_to_ast(term.scrutinee)
            wv_name = self._sanitize(term.witness_var)
            pv_name = self._sanitize(term.proof_var)
            b_node = self.term_to_ast(term.body)

            inner_lambda = ast.Lambda(
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg=wv_name), ast.arg(arg=pv_name)],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=b_node,
            )
            ex_var = ast.Name(id="_ex", ctx=ast.Load())
            w_sub = ast.Subscript(value=ex_var, slice=ast.Constant(value=0), ctx=ast.Load())
            p_sub = ast.Subscript(value=ex_var, slice=ast.Constant(value=1), ctx=ast.Load())
            inner_call = ast.Call(func=inner_lambda, args=[w_sub, p_sub], keywords=[])
            outer_lambda = ast.Lambda(
                args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="_ex")], kwonlyargs=[], kw_defaults=[], defaults=[]),
                body=inner_call,
            )
            return ast.Call(func=outer_lambda, args=[s_node], keywords=[])

        elif isinstance(term, NatRec):
            z_node = self.term_to_ast(term.zero_case)
            tgt_node = self.term_to_ast(term.target)
            vn = self._sanitize(term.succ_var_n)
            vih = self._sanitize(term.succ_var_ih)
            sc_node = self.term_to_ast(term.succ_case)
            step_lambda = ast.Lambda(
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg=vn), ast.arg(arg=vih)],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=sc_node,
            )
            return ast.Call(
                func=ast.Name(id="nat_rec", ctx=ast.Load()),
                args=[z_node, step_lambda, tgt_node],
                keywords=[],
            )

        raise TypeError(f"Unsupported ProofTerm AST node: {type(term)}")

    def export_function(
        self,
        term: ProofTerm,
        name: str,
        formula_type: Optional[ProofType] = None,
        docstring: Optional[str] = None
    ) -> str:
        """Translates a ProofTerm into an uncurried, type-annotated Python function definition string.

        Args:
            term (ProofTerm): The constructive proof term to translate.
            name (str): Identifier name for the generated function.
            formula_type (Optional[ProofType], default=None): Optional Curry-Howard type of the term.
            docstring (Optional[str], default=None): Optional docstring describing the proved theorem.

        Returns:
            str: Synthesized Python function source code.

        Example:
            >>> from logic_prover.constructive.terms import Var, Abs, AtomType
            >>> from logic_prover.exporters.python_exporter import PythonExporter
            >>> exp = PythonExporter()
            >>> term = Abs("x", AtomType("int"), Var("x"))
            >>> code = exp.export_function(term, "identity")
            >>> "def identity(x" in code
            True
        """
        norm_term = beta_normalize(term)
        clean_name = self._sanitize(name)

        # Uncurry top-level lambda abstractions
        parameters: List[Tuple[str, Optional[ProofType]]] = []
        curr = norm_term
        while isinstance(curr, Abs):
            parameters.append((curr.var, curr.var_type))
            curr = curr.body

        args_list: List[ast.arg] = []
        for p_name, p_type in parameters:
            ann_node = None
            if p_type is not None:
                ann_str = type_to_python_annotation(p_type)
                try:
                    ann_node = ast.parse(ann_str, mode="eval").body
                except Exception:
                    ann_node = ast.Name(id="Any", ctx=ast.Load())
            args_list.append(ast.arg(arg=self._sanitize(p_name), annotation=ann_node))

        # Determine return type annotation
        return_ann_node = None
        if formula_type is not None:
            # Unwind ArrowTypes corresponding to uncurried parameters
            curr_type = formula_type
            from logic_prover.constructive.terms import ArrowType
            for _ in parameters:
                if isinstance(curr_type, ArrowType):
                    curr_type = curr_type.right
            ret_str = type_to_python_annotation(curr_type)
            try:
                return_ann_node = ast.parse(ret_str, mode="eval").body
            except Exception:
                return_ann_node = None
        else:
            try:
                inferred = infer_type(curr)
                ret_str = type_to_python_annotation(inferred)
                return_ann_node = ast.parse(ret_str, mode="eval").body
            except Exception:
                return_ann_node = None

        body_expr = self.term_to_ast(curr)
        fn_body: List[ast.stmt] = []
        if docstring:
            fn_body.append(ast.Expr(value=ast.Constant(value=docstring)))
        fn_body.append(ast.Return(value=body_expr))

        func_def = ast.FunctionDef(
            name=clean_name,
            args=ast.arguments(
                posonlyargs=[],
                args=args_list,
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=fn_body,
            decorator_list=[],
            returns=return_ann_node,
        )
        ast.fix_missing_locations(func_def)

        return ast.unparse(func_def)

    def export_module(
        self,
        theorems: Sequence[Tuple[str, ProofTerm, Optional[ProofType]]],
        module_docstring: Optional[str] = None
    ) -> str:
        """Synthesizes a complete self-contained Python module file containing runtime preludes and functions.

        Args:
            theorems (Sequence[Tuple[str, ProofTerm, Optional[ProofType]]]): Collection of (name, proof_term, formula_type) triplets.
            module_docstring (Optional[str], default=None): Optional module-level docstring.

        Returns:
            str: Complete Python source code text ready to execute.

        Example:
            >>> from logic_prover.constructive.terms import Var, Abs, AtomType
            >>> from logic_prover.exporters.python_exporter import PythonExporter
            >>> exp = PythonExporter()
            >>> term = Abs("x", AtomType("int"), Var("x"))
            >>> code = exp.export_module([("identity", term, None)])
            >>> "from dataclasses import dataclass" in code
            True
        """
        lines: List[str] = []
        if module_docstring:
            lines.append(f'"""{module_docstring}"""')
            lines.append("")

        lines.extend([
            "from __future__ import annotations",
            "from dataclasses import dataclass",
            "from typing import Any, Callable, Generic, NoReturn, Tuple, TypeVar, Union",
            "",
            "T = TypeVar('T')",
            "U = TypeVar('U')",
            "",
            "@dataclass(frozen=True)",
            "class Left(Generic[T]):",
            "    value: T",
            "",
            "@dataclass(frozen=True)",
            "class Right(Generic[U]):",
            "    value: U",
            "",
            "def nat_rec(zero_val: Any, step_fn: Callable[[int, Any], Any], n: int) -> Any:",
            "    acc = zero_val",
            "    for k in range(n):",
            "        acc = step_fn(k, acc)",
            "    return acc",
            "",
            "def _abort() -> NoReturn:",
            "    raise RuntimeError('Unreachable: ex falso quodlibet branch executed.')",
            "",
            "",
        ])

        for name, term, formula_type in theorems:
            doc = f"Synthesized from constructive proof of {name}."
            fn_code = self.export_function(term, name, formula_type=formula_type, docstring=doc)
            lines.append(fn_code)
            lines.append("")
            lines.append("")

        return "\n".join(lines)


def export_function(
    term: ProofTerm,
    name: str,
    formula_type: Optional[ProofType] = None,
    docstring: Optional[str] = None
) -> str:
    """Convenience function generating an uncurried Python function definition from a ProofTerm.

    Args:
        term (ProofTerm): Target proof term.
        name (str): Function identifier.
        formula_type (Optional[ProofType], default=None): Optional Curry-Howard type.
        docstring (Optional[str], default=None): Optional docstring.

    Returns:
        str: Python function source code string.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, AtomType
        >>> from logic_prover.exporters.python_exporter import export_function
        >>> term = Abs("x", AtomType("int"), Var("x"))
        >>> code = export_function(term, "id_fn")
        >>> "def id_fn" in code
        True
    """
    exporter = PythonExporter()
    return exporter.export_function(term, name=name, formula_type=formula_type, docstring=docstring)


def export_module(
    theorems: Sequence[Tuple[str, ProofTerm, Optional[ProofType]]],
    module_docstring: Optional[str] = None
) -> str:
    """Convenience function generating a complete Python module containing synthesized functions.

    Args:
        theorems (Sequence[Tuple[str, ProofTerm, Optional[ProofType]]]): List of (name, proof_term, type) tuples.
        module_docstring (Optional[str], default=None): Optional module docstring.

    Returns:
        str: Python module source text.

    Example:
        >>> from logic_prover.constructive.terms import Var, Abs, AtomType
        >>> from logic_prover.exporters.python_exporter import export_module
        >>> term = Abs("x", AtomType("int"), Var("x"))
        >>> code = export_module([("id_fn", term, None)])
        >>> "def id_fn" in code
        True
    """
    exporter = PythonExporter()
    return exporter.export_module(theorems, module_docstring=module_docstring)


__all__ = [
    "PythonExporter",
    "export_function",
    "export_module",
]
