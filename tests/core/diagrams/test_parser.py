from __future__ import annotations
from mockr.core.diagrams.parser import parse_dsl, Edge

class TestParseDSL:
    def test_simple_chain(self) -> None:
        diagram = parse_dsl("client -> api -> db")
        assert "client" in diagram.nodes
        assert "api" in diagram.nodes
        assert "db" in diagram.nodes
        assert Edge(source="client", target="api") in diagram.edges
        assert Edge(source="api", target="db") in diagram.edges

    def test_multiple_lines(self) -> None:
        dsl = "client -> api -> db\napi -> cache -> db"
        diagram = parse_dsl(dsl)
        assert len(diagram.nodes) == 4
        assert Edge(source="api", target="cache") in diagram.edges

    def test_annotations(self) -> None:
        dsl = "client -> api\napi [REST, rate-limited]"
        diagram = parse_dsl(dsl)
        assert diagram.nodes["api"].annotations == ["REST", "rate-limited"]

    def test_groups(self) -> None:
        dsl = "[ingestion]\n  source -> queue\n[serving]\n  api -> db"
        diagram = parse_dsl(dsl)
        assert diagram.nodes["source"].group == "ingestion"
        assert diagram.nodes["api"].group == "serving"

    def test_comments_ignored(self) -> None:
        dsl = "# this is a comment\nclient -> api"
        diagram = parse_dsl(dsl)
        assert len(diagram.nodes) == 2

    def test_empty_input(self) -> None:
        diagram = parse_dsl("")
        assert len(diagram.nodes) == 0
        assert len(diagram.edges) == 0
