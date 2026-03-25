"""DSL parser: shorthand text -> Diagram model."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

@dataclass
class Node:
    name: str
    annotations: list[str] = field(default_factory=list)
    group: str | None = None

@dataclass(eq=True, frozen=True)
class Edge:
    source: str
    target: str

@dataclass
class Diagram:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

def _ensure_node(diagram: Diagram, name: str, group: str | None = None) -> None:
    if name not in diagram.nodes:
        diagram.nodes[name] = Node(name=name, group=group)
    elif group and not diagram.nodes[name].group:
        diagram.nodes[name].group = group

def parse_dsl(text: str) -> Diagram:
    diagram = Diagram()
    current_group: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        group_match = re.match(r"^\[(\w[\w\s-]*)\]\s*$", line)
        if group_match:
            current_group = group_match.group(1).strip()
            continue
        ann_match = re.match(r"^(\w[\w-]*)\s+\[(.+)\]\s*$", line)
        if ann_match:
            node_name = ann_match.group(1).strip()
            annotations = [a.strip() for a in ann_match.group(2).split(",")]
            _ensure_node(diagram, node_name, current_group)
            diagram.nodes[node_name].annotations = annotations
            continue
        if "->" in line:
            parts = [p.strip() for p in line.split("->")]
            for i in range(len(parts) - 1):
                src, tgt = parts[i], parts[i + 1]
                _ensure_node(diagram, src, current_group)
                _ensure_node(diagram, tgt, current_group)
                edge = Edge(source=src, target=tgt)
                if edge not in diagram.edges:
                    diagram.edges.append(edge)
    return diagram
