"""Render Diagram model to ASCII box-drawing art."""
from __future__ import annotations
from collections import defaultdict, deque
from mockr.core.diagrams.parser import Diagram

def _topological_layers(diagram: Diagram) -> list[list[str]]:
    if not diagram.nodes:
        return []
    children: dict[str, list[str]] = defaultdict(list)
    parents: dict[str, list[str]] = defaultdict(list)
    for edge in diagram.edges:
        children[edge.source].append(edge.target)
        parents[edge.target].append(edge.source)
    all_nodes = list(diagram.nodes.keys())
    roots = [n for n in all_nodes if not parents[n]]
    if not roots:
        roots = [all_nodes[0]]
    depth: dict[str, int] = {n: 0 for n in all_nodes}
    visited: set[str] = set()
    queue: deque[str] = deque(roots)
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for child in children[node]:
            depth[child] = max(depth[child], depth[node] + 1)
            queue.append(child)
    for node in all_nodes:
        if node not in visited:
            visited.add(node)
    layers: dict[int, list[str]] = defaultdict(list)
    for node in all_nodes:
        layers[depth[node]].append(node)
    max_layer = max(layers.keys()) if layers else 0
    return [layers[i] for i in range(max_layer + 1)]

def render_ascii(diagram: Diagram) -> str:
    layers = _topological_layers(diagram)
    if not layers:
        return ""
    edge_set = {(e.source, e.target) for e in diagram.edges}
    col_strs: list[list[str]] = []
    max_rows = max(len(layer) for layer in layers)
    for layer in layers:
        col: list[str] = []
        for node_name in layer:
            node = diagram.nodes[node_name]
            label = node_name
            if node.annotations:
                label += f" [{', '.join(node.annotations)}]"
            box_width = len(label) + 4
            top = "┌" + "─" * (box_width - 2) + "┐"
            mid = "│ " + label + " │"
            bot = "└" + "─" * (box_width - 2) + "┘"
            col.append(f"{top}\n{mid}\n{bot}")
        while len(col) < max_rows:
            col.append("")
        col_strs.append(col)
    result_rows: list[str] = []
    for row_idx in range(max_rows):
        parts: list[str] = []
        for col_idx, col in enumerate(col_strs):
            cell = col[row_idx]
            if cell:
                lines = cell.split("\n")
                parts.append(lines[1] if len(lines) > 1 else cell)
            else:
                parts.append("")
            if col_idx < len(col_strs) - 1 and cell:
                src_nodes = layers[col_idx]
                tgt_nodes = layers[col_idx + 1]
                has_edge = any((s, t) in edge_set for s in src_nodes for t in tgt_nodes)
                parts.append(" ──→ " if has_edge else "     ")
        result_rows.append("".join(parts))
    return "\n".join(result_rows)
