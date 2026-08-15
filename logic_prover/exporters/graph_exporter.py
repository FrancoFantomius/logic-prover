"""Interactive HTML visualizer for proof DAGs and theorem dependency networks."""

from __future__ import annotations
import json
import html
from pathlib import Path
from typing import Optional, Dict, Any, List

from logic_prover.core.parser import to_string
from logic_prover.prover.proof import ProofDAG, ProofStep
from logic_prover.deducer.graph import DependencyGraph
from logic_prover.core.exceptions import SolverError


class GraphExporter:
    """Exports ProofDAGs and DependencyGraphs into interactive standalone HTML files using vis.js."""

    VIS_JS_CDN = "https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"

    def __init__(self, theme: str = "light", embed_vis_js: bool = True) -> None:
        """
        Initializes the graph exporter.

        Args:
            theme: Visual theme ('light' or 'dark').
            embed_vis_js: Whether to link vis-network via CDN.
        """
        self.theme = theme
        self.embed_vis_js = embed_vis_js

    def export_proof_to_html(
        self,
        proof: ProofDAG,
        output_path: str,
        title: Optional[str] = None
    ) -> None:
        """
        Renders a natural deduction ProofDAG into an interactive hierarchical HTML visualization.

        Args:
            proof: Target ProofDAG instance.
            output_path: Output disk path for the .html file.
            title: Optional title header for the page.
        """
        page_title = title or "Proof DAG Visualization"
        nodes = []
        edges = []

        for step_id, step in proof.steps.items():
            is_root = (step_id == proof.root_id)
            is_premise = (len(step.premise_ids) == 0) or (str(step.rule).lower() in ("axiom", "hypothesis"))

            rule_str = step.rule.name if hasattr(step.rule, "name") else str(step.rule)
            rule_lower = rule_str.lower()

            if is_root:
                color = {"background": "#ffebee", "border": "#d32f2f"}
                shape = "diamond"
            elif is_premise:
                color = {"background": "#e3f2fd", "border": "#1976d2"}
                shape = "box"
            elif "quantifier" in rule_lower or "universal" in rule_lower or "existential" in rule_lower:
                color = {"background": "#fff3e0", "border": "#f57c00"}
                shape = "ellipse"
            elif "resolution" in rule_lower or "paramodulation" in rule_lower:
                color = {"background": "#f3e5f5", "border": "#7b1fa2"}
                shape = "ellipse"
            else:
                color = {"background": "#e8f5e9", "border": "#388e3c"}
                shape = "ellipse"

            formula_str = to_string(step.conclusion)

            tooltip = (
                f"<b>ID:</b> {html.escape(step_id)}<br/>"
                f"<b>Rule:</b> {html.escape(rule_str)}<br/>"
                f"<b>Formula:</b> {html.escape(formula_str)}"
            )

            nodes.append({
                "id": step_id,
                "label": f"{step_id}\n{rule_str}",
                "title": tooltip,
                "color": color,
                "shape": shape,
                "font": {"multi": "md"}
            })

            for p_id in step.premise_ids:
                edges.append({
                    "from": p_id,
                    "to": step_id,
                    "arrows": "to",
                    "color": {"color": "#757575"}
                })

        options = {
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "UD",
                    "sortMethod": "directed"
                }
            },
            "physics": {"enabled": False},
            "nodes": {"margin": 10},
            "edges": {"smooth": True}
        }

        html_content = self._generate_html(
            title=page_title,
            nodes_json=json.dumps(nodes, indent=2),
            edges_json=json.dumps(edges, indent=2),
            vis_options_json=json.dumps(options, indent=2)
        )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def export_dependency_network_to_html(
        self,
        graph: DependencyGraph,
        output_path: str,
        title: Optional[str] = None
    ) -> None:
        """
        Renders a theorem dependency network (DependencyGraph) into an interactive HTML visualization.

        Args:
            graph: Target DependencyGraph instance.
            output_path: Output disk path for the .html file.
            title: Optional title header for the page.
        """
        page_title = title or "Theorem Dependency Network"
        nodes = []
        edges = []

        if hasattr(graph, "nodes") and isinstance(graph.nodes, dict):
            nodes_dict = graph.nodes
            edges_list = getattr(graph, "edges", [])
        else:
            graph_dict = graph.to_dict() if hasattr(graph, "to_dict") else {}
            nodes_raw = graph_dict.get("nodes", [])
            edges_raw = graph_dict.get("edges", [])
            if isinstance(nodes_raw, list):
                nodes_dict = {n.get("id", str(idx)): n.get("formula", "") for idx, n in enumerate(nodes_raw)}
            else:
                nodes_dict = nodes_raw
            edges_list = [(e.get("source"), e.get("target"), e.get("relationship", "implies")) for e in edges_raw] if isinstance(edges_raw, list) else edges_raw

        for node_id, formula_obj in nodes_dict.items():
            if isinstance(formula_obj, str):
                formula_str = formula_obj
            elif hasattr(formula_obj, "__class__") and formula_obj.__class__.__name__ in ("Formula", "PredicateApp", "Equality", "Not", "And", "Or", "Implies", "Iff", "Forall", "Exists"):
                formula_str = to_string(formula_obj)
            else:
                formula_str = str(formula_obj)

            color = {"background": "#e8f5e9", "border": "#2e7d32"}

            tooltip = (
                f"<b>Theorem:</b> {html.escape(node_id)}<br/>"
                f"<b>Formula:</b> {html.escape(formula_str)}"
            )

            nodes.append({
                "id": node_id,
                "label": node_id,
                "title": tooltip,
                "color": color,
                "shape": "box"
            })

        for edge in edges_list:
            if isinstance(edge, (list, tuple)):
                src, tgt = edge[0], edge[1]
                rel = edge[2] if len(edge) > 2 else "implies"
            elif isinstance(edge, dict):
                src, tgt, rel = edge.get("source"), edge.get("target"), edge.get("relationship", "implies")
            else:
                continue

            is_equiv = (rel == "equivalent")

            edges.append({
                "from": src,
                "to": tgt,
                "arrows": "to",
                "label": rel,
                "dashes": is_equiv,
                "color": {"color": "#1565c0" if is_equiv else "#424242"}
            })

        options = {
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -3000,
                    "centralGravity": 0.3,
                    "springLength": 95
                }
            },
            "edges": {"smooth": {"type": "continuous"}}
        }

        html_content = self._generate_html(
            title=page_title,
            nodes_json=json.dumps(nodes, indent=2),
            edges_json=json.dumps(edges, indent=2),
            vis_options_json=json.dumps(options, indent=2)
        )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_html(
        self,
        title: str,
        nodes_json: str,
        edges_json: str,
        vis_options_json: str
    ) -> str:
        """Generates self-contained HTML file template with embedded JavaScript and CSS."""
        bg_color = "#121212" if self.theme == "dark" else "#ffffff"
        text_color = "#ffffff" if self.theme == "dark" else "#333333"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(title)}</title>
  <script type="text/javascript" src="{self.VIS_JS_CDN}"></script>
  <style type="text/css">
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background-color: {bg_color};
      color: {text_color};
    }}
    #header {{
      padding: 12px 20px;
      background: #1976d2;
      color: white;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    #header h2 {{ margin: 0; font-size: 1.2rem; }}
    #controls {{ display: flex; gap: 10px; }}
    input[type="text"] {{
      padding: 6px 10px;
      border-radius: 4px;
      border: 1px solid #ccc;
    }}
    #mynetwork {{
      width: 100vw;
      height: calc(100vh - 60px);
      border: none;
    }}
  </style>
</head>
<body>
  <div id="header">
    <h2>{html.escape(title)}</h2>
    <div id="controls">
      <input type="text" id="searchInput" placeholder="Search node or formula..." onkeyup="searchNodes()">
    </div>
  </div>
  <div id="mynetwork"></div>

  <script type="text/javascript">
    const nodes = new vis.DataSet({nodes_json});
    const edges = new vis.DataSet({edges_json});
    const container = document.getElementById('mynetwork');
    const data = {{ nodes: nodes, edges: edges }};
    const options = {vis_options_json};
    const network = new vis.Network(container, data, options);

    function searchNodes() {{
      const query = document.getElementById('searchInput').value.toLowerCase();
      if (!query) {{
        nodes.forEach(n => nodes.update({{ id: n.id, hidden: false }}));
        return;
      }}
      nodes.forEach(n => {{
        const match = n.id.toLowerCase().includes(query) || (n.title && n.title.toLowerCase().includes(query));
        nodes.update({{ id: n.id, hidden: !match }});
      }});
    }}
  </script>
</body>
</html>
"""
