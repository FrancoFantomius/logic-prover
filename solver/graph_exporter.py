"""
Graph Exporter Module
=====================
Builds directed graph representations of theories, axioms, hypotheses, and derived theorems
from a TheoryDatabase. Supports exporting to DOT format, JSON, and interactive HTML visualization.
"""

import json
from typing import Dict, List, Set, Tuple
from .database import TheoryDatabase


def build_theory_graph(db: TheoryDatabase) -> Dict:
    """
    Extracts nodes and directed edges from the TheoryDatabase.
    Nodes represent Axioms, Hypotheses, or Derived Theorems.
    Edges represent logical derivation dependencies.
    """
    nodes = []
    edges = []
    node_set = set()

    # 1. Add Axiom nodes
    axioms = db.get_all_axioms()
    for ax_name, ax_str in axioms.items():
        node_id = f"axiom_{ax_name}"
        if node_id not in node_set:
            node_set.add(node_id)
            nodes.append({
                "id": node_id,
                "label": f"Axiom: {ax_name}\n{ax_str}",
                "name": ax_name,
                "formula": ax_str,
                "type": "axiom"
            })

    # 2. Extract Theorems and dependencies
    with db.connection_scope() as conn:
        cursor = conn.execute("SELECT name FROM theorems WHERE is_verified = 1;")
        thm_names = [row[0] for row in cursor.fetchall()]

    for thm_name in thm_names:
        thm = db.get_theorem(thm_name)
        if not thm:
            continue

        thm_node_id = f"thm_{thm['name']}"
        if thm_node_id not in node_set:
            node_set.add(thm_node_id)
            nodes.append({
                "id": thm_node_id,
                "label": f"Result: {thm['name']}\n{thm['thesis_str']}",
                "name": thm['name'],
                "formula": thm['thesis_str'],
                "type": "theorem"
            })

        # Add Hypotheses nodes and edges
        for idx, hyp_str in enumerate(thm['hypotheses']):
            hyp_node_id = f"hyp_{abs(hash(hyp_str))}"
            if hyp_node_id not in node_set:
                node_set.add(hyp_node_id)
                nodes.append({
                    "id": hyp_node_id,
                    "label": f"Hypothesis: h{idx}\n{hyp_str}",
                    "formula": hyp_str,
                    "type": "hypothesis"
                })
            edges.append({
                "source": hyp_node_id,
                "target": thm_node_id,
                "relationship": "hypothesis"
            })

        # Add Axiom & Lemma step dependencies
        for step in thm['steps']:
            j_type = step['justification_type']
            ref_name = step.get('ref_name')

            if j_type == 'Axiom' and ref_name:
                ax_node_id = f"axiom_{ref_name}"
                edges.append({
                    "source": ax_node_id,
                    "target": thm_node_id,
                    "relationship": "axiom_justification"
                })
            elif j_type == 'Lemma' and ref_name:
                lemma_node_id = f"thm_{ref_name}"
                edges.append({
                    "source": lemma_node_id,
                    "target": thm_node_id,
                    "relationship": "lemma_justification"
                })

    # Remove duplicate edges
    unique_edges = []
    seen_edges = set()
    for e in edges:
        edge_key = (e['source'], e['target'], e['relationship'])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            unique_edges.append(e)

    return {"nodes": nodes, "edges": unique_edges}


def export_graph_dot(db: TheoryDatabase, output_path: str = "group_graph.dot") -> str:
    """
    Exports theory graph into Graphviz DOT syntax.
    """
    graph_data = build_theory_graph(db)

    dot_lines = [
        "digraph TheoryGraph {",
        "  rankdir=LR;",
        "  node [shape=box, style=filled, fontname=\"Helvetica\"];",
        ""
    ]

    for node in graph_data["nodes"]:
        n_type = node["type"]
        lbl = node["label"].replace('"', '\\"').replace("\n", "\\n")
        if n_type == "axiom":
            color = "lightskyblue"
        elif n_type == "hypothesis":
            color = "lightyellow"
        else:
            color = "palegreen"

        dot_lines.append(f'  "{node["id"]}" [label="{lbl}", fillcolor="{color}"];')

    dot_lines.append("")

    for edge in graph_data["edges"]:
        dot_lines.append(f'  "{edge["source"]}" -> "{edge["target"]}";')

    dot_lines.append("}")

    content = "\n".join(dot_lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return content


def export_graph_json(db: TheoryDatabase, output_path: str = "group_graph.json") -> str:
    """
    Exports theory graph into JSON format.
    """
    graph_data = build_theory_graph(db)
    content = json.dumps(graph_data, indent=2)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return content


def export_graph_html(db: TheoryDatabase, output_path: str = "group_graph.html") -> str:
    """
    Exports theory graph as an interactive HTML document using vis-network.
    """
    graph_data = build_theory_graph(db)

    vis_nodes = []
    for n in graph_data["nodes"]:
        color = "#87CEFA" if n["type"] == "axiom" else ("#FFFACD" if n["type"] == "hypothesis" else "#98FB98")
        vis_nodes.append({
            "id": n["id"],
            "label": f"{n['type'].upper()}: {n.get('name', '')}\n{n['formula']}",
            "color": color,
            "shape": "box"
        })

    vis_edges = [
        {"from": e["source"], "to": e["target"], "arrows": "to"}
        for e in graph_data["edges"]
    ]

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Theory Proof Graph Visualization</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        #network {{
            width: 100%;
            height: 900px;
            border: 1px solid lightgray;
            background-color: #f8f9fa;
        }}
        body {{ font-family: sans-serif; margin: 20px; }}
        h2 {{ color: #333; }}
    </style>
</head>
<body>
    <h2>Group Theory Proof Dependency Graph</h2>
    <p><b>Blue:</b> Axioms | <b>Yellow:</b> Hypotheses | <b>Green:</b> Derived Results/Theorems</p>
    <div id="network"></div>
    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(vis_nodes)});
        var edges = new vis.DataSet({json.dumps(vis_edges)});
        var container = document.getElementById('network');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            layout: {{ hierarchical: {{ direction: 'LR', sortMethod: 'directed' }} }},
            physics: {{ hierarchicalRepulsion: {{ nodeDistance: 180 }} }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_content
