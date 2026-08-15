"""
Automated reflection and AST documentation generator for the logic library.

Extracts docstrings, type annotations, and signatures from Python source modules
and formats them into Markdown documentation files.
"""

from __future__ import annotations
import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class ParamDoc:
    """Represents a parameter documentation entry."""
    name: str
    type_hint: str
    description: str


@dataclass
class ReturnDoc:
    """Represents a return value documentation entry."""
    type_hint: str
    description: str


@dataclass
class ExceptionDoc:
    """Represents an exception documentation entry."""
    type_name: str
    description: str


@dataclass
class FunctionDoc:
    """Represents a documented standalone function or method."""
    name: str
    signature: str
    summary: str
    description: str
    params: List[ParamDoc] = field(default_factory=list)
    returns: Optional[ReturnDoc] = None
    raises: List[ExceptionDoc] = field(default_factory=list)
    is_method: bool = False
    is_async: bool = False


@dataclass
class ClassDoc:
    """Represents a documented class."""
    name: str
    signature: str
    summary: str
    description: str
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionDoc] = field(default_factory=list)


@dataclass
class ModuleDoc:
    """Represents a documented Python module."""
    module_path: str
    module_name: str
    summary: str
    description: str
    classes: List[ClassDoc] = field(default_factory=list)
    functions: List[FunctionDoc] = field(default_factory=list)


def parse_google_docstring(
    docstring: Optional[str]
) -> Tuple[str, str, List[ParamDoc], Optional[ReturnDoc], List[ExceptionDoc]]:
    """
    Parses a Google-style docstring into structured components.

    Args:
        docstring: Raw docstring text.

    Returns:
        Tuple containing (summary, detailed_description, params_list, return_info, raises_list).
    """
    if not docstring:
        return "", "", [], None, []

    doc = docstring.strip()
    if not doc:
        return "", "", [], None, []

    lines = doc.splitlines()
    summary_lines: List[str] = []
    desc_lines: List[str] = []
    params: List[ParamDoc] = []
    returns: Optional[ReturnDoc] = None
    raises: List[ExceptionDoc] = []

    current_section = "summary"

    i = 0
    while i < len(lines):
        line = lines[i]
        trimmed = line.strip()

        if trimmed in ("Args:", "Arguments:", "Parameters:"):
            current_section = "args"
            i += 1
            continue
        elif trimmed in ("Returns:", "Return:"):
            current_section = "returns"
            i += 1
            continue
        elif trimmed in ("Raises:", "Exceptions:"):
            current_section = "raises"
            i += 1
            continue
        elif trimmed in ("Examples:", "Example:", "Notes:", "Note:", "Attributes:"):
            current_section = "other"
            i += 1
            continue

        if current_section == "summary":
            if not trimmed:
                if summary_lines:
                    current_section = "desc"
            else:
                summary_lines.append(trimmed)
        elif current_section == "desc":
            desc_lines.append(line)
        elif current_section == "args":
            if trimmed:
                if ":" in trimmed:
                    header, desc = trimmed.split(":", 1)
                    header = header.strip()
                    desc = desc.strip()
                    if "(" in header and ")" in header:
                        p_name = header[: header.find("(")].strip()
                        p_type = header[header.find("(") + 1 : header.find(")")].strip()
                    else:
                        p_name = header
                        p_type = ""
                    params.append(ParamDoc(name=p_name, type_hint=p_type, description=desc))
                else:
                    if params:
                        params[-1].description += " " + trimmed
        elif current_section == "returns":
            if trimmed:
                if ":" in trimmed:
                    r_type, r_desc = trimmed.split(":", 1)
                    returns = ReturnDoc(type_hint=r_type.strip(), description=r_desc.strip())
                else:
                    if returns is None:
                        returns = ReturnDoc(type_hint="", description=trimmed)
                    else:
                        returns.description += " " + trimmed
        elif current_section == "raises":
            if trimmed:
                if ":" in trimmed:
                    e_type, e_desc = trimmed.split(":", 1)
                    raises.append(ExceptionDoc(type_name=e_type.strip(), description=e_desc.strip()))
                else:
                    if raises:
                        raises[-1].description += " " + trimmed
        i += 1

    summary = " ".join(summary_lines)
    description = "\n".join(desc_lines).strip()
    return summary, description, params, returns, raises


def _format_ast_annotation(node: Optional[ast.AST]) -> str:
    """Formats an AST type annotation node as string."""
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _extract_func_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Tuple[str, Dict[str, str], str]:
    """Extracts signature string, parameter type map, and return type hint from a FunctionDef AST node."""
    arg_strings = []
    arg_type_map: Dict[str, str] = {}

    args_obj = node.args
    # Handle args
    for arg in args_obj.args:
        type_str = _format_ast_annotation(arg.annotation)
        arg_name = arg.arg
        if type_str:
            arg_strings.append(f"{arg_name}: {type_str}")
            arg_type_map[arg_name] = type_str
        else:
            arg_strings.append(arg_name)
            arg_type_map[arg_name] = ""

    sig_str = f"({', '.join(arg_strings)})"
    ret_str = _format_ast_annotation(node.returns)
    if ret_str:
        sig_str += f" -> {ret_str}"

    return sig_str, arg_type_map, ret_str


def extract_docstrings_from_module(module_path: str) -> ModuleDoc:
    """
    Inspects docstrings and signatures from a Python module file using AST and reflection.

    Args:
        module_path: Absolute or relative file path to a .py file (e.g. 'logic_prover/core/ast.py').

    Returns:
        ModuleDoc containing parsed classes, functions, signatures, and docstring sections.

    Raises:
        FileNotFoundError: If module_path does not exist.
        SyntaxError: If module_path contains invalid Python syntax.
    """
    path_obj = Path(module_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Module file non-existent: {module_path}")

    source = path_obj.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=module_path)

    raw_mod_doc = ast.get_docstring(tree)
    mod_summary, mod_desc, _, _, _ = parse_google_docstring(raw_mod_doc)

    mod_name = path_obj.stem
    # Convert file path to module dotted path if inside logic_prover or logic
    parts = list(path_obj.parts)
    if "logic_prover" in parts:
        pkg_idx = parts.index("logic_prover")
        mod_parts = list(parts[pkg_idx:])
        if mod_parts[-1].endswith(".py"):
            mod_parts[-1] = mod_parts[-1][:-3]
        if mod_parts[-1] == "__init__":
            mod_parts = mod_parts[:-1]
        mod_name = ".".join(mod_parts)
    elif "logic" in parts:
        pkg_idx = parts.index("logic")
        mod_parts = list(parts[pkg_idx:])
        if mod_parts[-1].endswith(".py"):
            mod_parts[-1] = mod_parts[-1][:-3]
        if mod_parts[-1] == "__init__":
            mod_parts = mod_parts[:-1]
        mod_name = ".".join(mod_parts)

    classes: List[ClassDoc] = []
    functions: List[FunctionDoc] = []

    for item in tree.body:
        if isinstance(item, ast.ClassDef):
            if item.name.startswith("_"):
                continue

            raw_cls_doc = ast.get_docstring(item)
            cls_summary, cls_desc, _, _, _ = parse_google_docstring(raw_cls_doc)
            bases = [_format_ast_annotation(b) for b in item.bases]

            methods: List[FunctionDoc] = []
            for stmt in item.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if stmt.name.startswith("_") and stmt.name != "__init__":
                        continue

                    raw_m_doc = ast.get_docstring(stmt)
                    m_summary, m_desc, m_params, m_returns, m_raises = parse_google_docstring(raw_m_doc)
                    m_sig, arg_map, ret_hint = _extract_func_signature(stmt)

                    # Update param type hints from AST if empty
                    for p in m_params:
                        if not p.type_hint and p.name in arg_map:
                            p.type_hint = arg_map[p.name]

                    if m_returns is None and ret_hint:
                        m_returns = ReturnDoc(type_hint=ret_hint, description="")
                    elif m_returns is not None and not m_returns.type_hint:
                        m_returns.type_hint = ret_hint

                    methods.append(
                        FunctionDoc(
                            name=stmt.name,
                            signature=m_sig,
                            summary=m_summary,
                            description=m_desc,
                            params=m_params,
                            returns=m_returns,
                            raises=m_raises,
                            is_method=True,
                            is_async=isinstance(stmt, ast.AsyncFunctionDef),
                        )
                    )

            classes.append(
                ClassDoc(
                    name=item.name,
                    signature=f"class {item.name}({', '.join(bases)})" if bases else f"class {item.name}",
                    summary=cls_summary,
                    description=cls_desc,
                    bases=bases,
                    methods=methods,
                )
            )

        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name.startswith("_"):
                continue

            raw_f_doc = ast.get_docstring(item)
            f_summary, f_desc, f_params, f_returns, f_raises = parse_google_docstring(raw_f_doc)
            f_sig, arg_map, ret_hint = _extract_func_signature(item)

            for p in f_params:
                if not p.type_hint and p.name in arg_map:
                    p.type_hint = arg_map[p.name]

            if f_returns is None and ret_hint:
                f_returns = ReturnDoc(type_hint=ret_hint, description="")
            elif f_returns is not None and not f_returns.type_hint:
                f_returns.type_hint = ret_hint

            functions.append(
                FunctionDoc(
                    name=item.name,
                    signature=f_sig,
                    summary=f_summary,
                    description=f_desc,
                    params=f_params,
                    returns=f_returns,
                    raises=f_raises,
                    is_method=False,
                    is_async=isinstance(item, ast.AsyncFunctionDef),
                )
            )

    return ModuleDoc(
        module_path=module_path,
        module_name=mod_name,
        summary=mod_summary,
        description=mod_desc,
        classes=classes,
        functions=functions,
    )


def render_markdown_module(module_doc: ModuleDoc) -> str:
    """
    Renders a ModuleDoc object into GitHub-flavored Markdown text.

    Args:
        module_doc: ModuleDoc instance.

    Returns:
        Formatted Markdown string.
    """
    lines: List[str] = []
    lines.append(f"# Module `{module_doc.module_name}`")
    lines.append("")
    if module_doc.summary:
        lines.append(module_doc.summary)
        lines.append("")
    if module_doc.description:
        lines.append(module_doc.description)
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Table of Contents")
    if module_doc.classes:
        lines.append("- [Classes](#classes)")
    if module_doc.functions:
        lines.append("- [Functions](#functions)")
    lines.append("")

    if module_doc.classes:
        lines.append("---")
        lines.append("")
        lines.append("## Classes")
        lines.append("")
        for cls in module_doc.classes:
            bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
            lines.append(f"### `class {cls.name}{bases_str}`")
            lines.append("")
            if cls.summary:
                lines.append(cls.summary)
                lines.append("")
            if cls.description:
                lines.append(cls.description)
                lines.append("")

            if cls.methods:
                lines.append("#### Methods")
                lines.append("")
                for m in cls.methods:
                    async_prefix = "async " if m.is_async else ""
                    lines.append(f"##### `{async_prefix}def {m.name}{m.signature}`")
                    lines.append("")
                    if m.summary:
                        lines.append(m.summary)
                        lines.append("")
                    if m.params:
                        lines.append("**Parameters:**")
                        lines.append("| Name | Type | Description |")
                        lines.append("| :--- | :--- | :--- |")
                        for p in m.params:
                            type_str = f"`{p.type_hint}`" if p.type_hint else "-"
                            lines.append(f"| `{p.name}` | {type_str} | {p.description or '-'} |")
                        lines.append("")

                    if m.returns:
                        type_str = f"`{m.returns.type_hint}`" if m.returns.type_hint else ""
                        desc_str = m.returns.description if m.returns.description else ""
                        lines.append(f"**Returns:** {type_str} — {desc_str}".strip(" —"))
                        lines.append("")

                    if m.raises:
                        lines.append("**Raises:**")
                        for exc in m.raises:
                            lines.append(f"- `{exc.type_name}`: {exc.description}")
                        lines.append("")

    if module_doc.functions:
        lines.append("---")
        lines.append("")
        lines.append("## Functions")
        lines.append("")
        for f in module_doc.functions:
            async_prefix = "async " if f.is_async else ""
            lines.append(f"### `{async_prefix}def {f.name}{f.signature}`")
            lines.append("")
            if f.summary:
                lines.append(f.summary)
                lines.append("")
            if f.description:
                lines.append(f.description)
                lines.append("")

            if f.params:
                lines.append("**Parameters:**")
                lines.append("| Name | Type | Description |")
                lines.append("| :--- | :--- | :--- |")
                for p in f.params:
                    type_str = f"`{p.type_hint}`" if p.type_hint else "-"
                    lines.append(f"| `{p.name}` | {type_str} | {p.description or '-'} |")
                lines.append("")

            if f.returns:
                type_str = f"`{f.returns.type_hint}`" if f.returns.type_hint else ""
                desc_str = f.returns.description if f.returns.description else ""
                lines.append(f"**Returns:** {type_str} — {desc_str}".strip(" —"))
                lines.append("")

            if f.raises:
                lines.append("**Raises:**")
                for exc in f.raises:
                    lines.append(f"- `{exc.type_name}`: {exc.description}")
                lines.append("")

    return "\n".join(lines)


def build_markdown_docs(source_dir: str = "logic_prover", output_docs_dir: str = "docs") -> Dict[str, str]:
    """
    Scans the source codebase, extracts docstrings from all modules, and writes Markdown documentation.

    Generates:
    - docs/api/<submodule_group>.md (e.g. docs/api/core.md, docs/api/prover.md)
    - docs/index.md (Landing page with module links and summary tables)

    Args:
        source_dir: Root package directory to scan (default 'logic_prover').
        output_docs_dir: Target output directory for markdown files (default 'docs').

    Returns:
        Dictionary mapping created file paths to rendered content length.
    """
    output_path = Path(output_docs_dir)
    api_dir = output_path / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, str] = {}
    grouped_docs: Dict[str, List[ModuleDoc]] = {}

    for root, _, files in os.walk(source_dir):
        for file in sorted(files):
            if file.endswith(".py") and not file.startswith("_"):
                full_path = os.path.join(root, file)
                try:
                    doc = extract_docstrings_from_module(full_path)
                    rel_parts = Path(full_path).relative_to(source_dir).parts
                    if len(rel_parts) > 1:
                        group_name = rel_parts[0]
                    else:
                        group_name = Path(file).stem

                    if group_name not in grouped_docs:
                        grouped_docs[group_name] = []
                    grouped_docs[group_name].append(doc)
                except Exception:
                    pass

    # Generate API markdown file for each group
    group_summaries: List[Tuple[str, str, int, int]] = []

    for group, mod_docs in sorted(grouped_docs.items()):
        group_content: List[str] = [f"# API Reference: `{group}`", ""]
        total_classes = 0
        total_functions = 0

        for mdoc in mod_docs:
            rendered = render_markdown_module(mdoc)
            group_content.append(rendered)
            group_content.append("\n---\n")
            total_classes += len(mdoc.classes)
            total_functions += len(mdoc.functions)

        group_file = api_dir / f"{group}.md"
        final_text = "\n".join(group_content)
        group_file.write_text(final_text, encoding="utf-8")
        results[str(group_file)] = final_text
        group_summaries.append((group, f"api/{group}.md", total_classes, total_functions))

    # Generate docs/index.md
    index_lines: List[str] = [
        "# Logic Documentation Portal",
        "",
        "Welcome to the formal logic theorem prover, explorer, and deducer library documentation.",
        "",
        "## Submodule API Reference",
        "",
        "| Module Group | Documentation Link | Documented Classes | Documented Functions |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for gname, glink, ncls, nfn in group_summaries:
        index_lines.append(f"| `{gname}` | [{gname}]({glink}) | {ncls} | {nfn} |")

    index_lines.extend([
        "",
        "---",
        "",
        "## Architecture Overview",
        "",
        "- **`logic_prover.core`**: AST definitions, sort systems, signatures, parser, substitution, rewriting.",
        "- **`logic_prover.prover`**: Resolution theorem prover engine, clause generation, proof DAG reconstruction.",
        "- **`logic_prover.explorer`**: Novel formula generation, heuristic ranking, and diversity filters.",
        "- **`logic_prover.deducer`**: Network dependency analysis and hypothesis minimal subset detection.",
        "- **`logic_prover.exporters`**: Translation to Lean 4 formal code and interactive HTML DAG graph rendering.",
        "- **`logic_prover.kb`**: Knowledge database interface and foundational mathematical axioms.",
        "- **`logic_prover.sol`**: Second-Order Logic (SOL) extensions.",
        "- **`logic_prover.utils`**: Central logging subsystem and automated documentation generator.",
        "",
    ])

    index_file = output_path / "index.md"
    index_text = "\n".join(index_lines)
    index_file.write_text(index_text, encoding="utf-8")
    results[str(index_file)] = index_text

    return results
