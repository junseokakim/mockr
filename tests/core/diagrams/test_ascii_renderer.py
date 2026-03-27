from __future__ import annotations

from mockr.core.diagrams.ascii_renderer import render_ascii
from mockr.core.diagrams.parser import parse_dsl


class TestASCIIRenderer:
    def test_simple_chain(self) -> None:
        diagram = parse_dsl("client -> api -> db")
        output = render_ascii(diagram)
        assert "client" in output
        assert "api" in output
        assert "db" in output
        assert ">" in output or "→" in output or "─" in output

    def test_empty_diagram(self) -> None:
        diagram = parse_dsl("")
        output = render_ascii(diagram)
        assert output.strip() == ""

    def test_fan_out(self) -> None:
        diagram = parse_dsl("api -> cache\napi -> queue")
        output = render_ascii(diagram)
        assert "api" in output
        assert "cache" in output
        assert "queue" in output
