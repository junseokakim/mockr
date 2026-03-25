"""Render Diagram model to Mermaid syntax."""
from __future__ import annotations
from mockr.core.diagrams.parser import Diagram

def render_mermaid(diagram: Diagram) -> str:
    lines = ["graph LR"]
    for edge in diagram.edges:
        lines.append(f"    {edge.source} --> {edge.target}")
    return "\n".join(lines)
