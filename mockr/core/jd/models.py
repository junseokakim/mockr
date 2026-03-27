"""Data models for job descriptions and role profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Skill:
    name: str
    category: str  # maps to Mode value: "system-design", "coding", "behavioral"
    dimensions: list[str] = field(default_factory=list)
    weight: float = 0.5


@dataclass
class InterviewIntel:
    format: list[str] = field(default_factory=list)
    common_topics: list[str] = field(default_factory=list)
    culture_signals: list[str] = field(default_factory=list)
    gotchas: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class RoleProfile:
    id: str
    role_title: str
    inferred_level: str
    raw_text: str
    company: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    domain: str | None = None
    key_skills: list[Skill] = field(default_factory=list)
    interview_intel: InterviewIntel | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
