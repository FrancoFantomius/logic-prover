# API Reference: `exporters`

# Module `solver.exporters.graph_exporter`

Interactive HTML visualizer for proof DAGs and theorem dependency networks.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class GraphExporter`

Exports ProofDAGs and DependencyGraphs into interactive standalone HTML files using vis.js.

#### Methods

##### `def __init__(self, theme: str, embed_vis_js: bool) -> None`

Initializes the graph exporter.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `theme` | `str` | Visual theme ('light' or 'dark'). |
| `embed_vis_js` | `bool` | Whether to link vis-network via CDN. |

**Returns:** `None`

##### `def export_proof_to_html(self, proof: ProofDAG, output_path: str, title: Optional[str]) -> None`

Renders a natural deduction ProofDAG into an interactive hierarchical HTML visualization.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `proof` | `ProofDAG` | Target ProofDAG instance. |
| `output_path` | `str` | Output disk path for the .html file. |
| `title` | `Optional[str]` | Optional title header for the page. |

**Returns:** `None`

##### `def export_dependency_network_to_html(self, graph: DependencyGraph, output_path: str, title: Optional[str]) -> None`

Renders a theorem dependency network (DependencyGraph) into an interactive HTML visualization.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `graph` | `DependencyGraph` | Target DependencyGraph instance. |
| `output_path` | `str` | Output disk path for the .html file. |
| `title` | `Optional[str]` | Optional title header for the page. |

**Returns:** `None`


---

# Module `solver.exporters.lean_exporter`

Lean 4 exporter for translating terms, formulas, and proof DAGs to formal Lean 4 code.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class LeanExporter`

Translates solver AST nodes, formulas, theorem declarations, and proof DAGs into LEAN 4 code.

#### Methods

##### `def __init__(self, lean_project_name: str, universe_name: str, default_sort_var: str) -> None`

Initializes the LEAN exporter.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `lean_project_name` | `str` | Name of the project/namespace. |
| `universe_name` | `str` | LEAN universe variable name (default "u"). |
| `default_sort_var` | `str` | Default type variable name for Ind sort (default "α"). |

**Returns:** `None`

##### `def export_preamble(self, imports: Optional[List[str]], open_namespaces: Optional[List[str]]) -> str`

Generates LEAN 4 file header including module imports, universe variables, and namespace declarations.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `imports` | `Optional[List[str]]` | Optional list of modules to import (defaults to ["Mathlib.Tactic"]). |
| `open_namespaces` | `Optional[List[str]]` | Optional list of LEAN namespaces to open. |

**Returns:** `str` — Formatted LEAN 4 preamble string.

##### `def export_sort(self, sort: Sort) -> str`

Translates a Sort object into LEAN 4 type syntax.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `sort` | `Sort` | Target Sort instance. |

**Returns:** `str` — LEAN 4 sort representation string (e.g. "ℕ", "Set α", "α → α").

##### `def export_term(self, term: Term) -> str`

Translates a Term AST node into LEAN 4 term expression string.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `term` | `Term` | Target Term instance. |

**Returns:** `str` — Formatted LEAN 4 term string.

##### `def export_formula(self, formula: Formula) -> str`

Translates a Formula AST node into LEAN 4 proposition string.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | Target Formula instance. |

**Returns:** `str` — Formatted LEAN 4 proposition syntax string.

##### `def export_theorem_statement(self, name: str, formula: Formula, hypotheses: Optional[List[Tuple[str, Formula]]]) -> str`

Generates a LEAN 4 theorem signature statement with a sorry placeholder.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Theorem identifier name. |
| `formula` | `Formula` | Target conclusion formula. |
| `hypotheses` | `Optional[List[Tuple[str, Formula]]]` | Optional list of named hypothesis premises [(h1_name, h1_formula), ...]. |

**Returns:** `Formatted LEAN 4 theorem statement string ending in '` — = by sorry'.

##### `def export_proof(self, proof: ProofDAG, theorem_name: str) -> str`

Translates a ProofDAG into a structured LEAN 4 theorem declaration with tactic proof body.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `proof` | `ProofDAG` | Validated ProofDAG object. |
| `theorem_name` | `str` | Target theorem name. |

**Returns:** `str` — Complete LEAN 4 theorem with tactic block using Mathlib tactics.

##### `def export_file(self, file_path: str, theorems: List[Tuple[str, Formula, Optional[ProofDAG]]], stubs_only: bool, imports: Optional[List[str]]) -> None`

Writes a complete standalone LEAN 4 source file containing preambles and theorem declarations.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `file_path` | `str` | Output disk path for .lean file. |
| `theorems` | `List[Tuple[str, Formula, Optional[ProofDAG]]]` | List of tuples (theorem_name, formula, optional_proof_dag). |
| `stubs_only` | `bool` | If True, exports all theorems as 'sorry' stubs regardless of proof availability. |
| `imports` | `Optional[List[str]]` | Optional custom import module list. |

**Returns:** `None`


---
