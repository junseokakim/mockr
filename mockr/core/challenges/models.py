"""Challenge data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TestCase:
    expected: str
    input: str = ""
    expected_columns: list[str] = field(default_factory=list)
    expected_rows: list[list] = field(default_factory=list)
    setup_extra: str = ""
    expected_note: str = ""
    hidden: bool = False


@dataclass
class LevelConfig:
    estimated_minutes: int
    interviewer: str
    must_cover: list[str] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)


@dataclass
class Challenge:
    id: str
    title: str
    mode: str
    tags: list[str] = field(default_factory=list)
    language: str = ""
    levels: dict[str, LevelConfig] = field(default_factory=dict)
    setup_sql: str = ""
    test_cases: list[TestCase] = field(default_factory=list)
