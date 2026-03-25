from __future__ import annotations
from mockr.core.diagrams.mermaid_renderer import render_mermaid
from mockr.core.diagrams.parser import parse_dsl

class TestMermaidRenderer:
    def test_simple_chain(self) -> None:
        diagram = parse_dsl("client -> api -> db")
        output = render_mermaid(diagram)
        assert "graph LR" in output
        assert "client --> api" in output
        assert "api --> db" in output

    def test_empty_diagram(self) -> None:
        diagram = parse_dsl("")
        output = render_mermaid(diagram)
        assert "graph LR" in output
