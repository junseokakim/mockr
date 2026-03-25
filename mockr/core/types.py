"""Shared types for mockr core."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class SessionState(Enum):
    IDLE = "idle"
    SETUP = "setup"
    ACTIVE = "active"
    PAUSED = "paused"
    DEBRIEF = "debrief"
    COMPLETE = "complete"


class Level(Enum):
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"


class Mode(Enum):
    SYSTEM_DESIGN = "system-design"
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    FULL_LOOP = "full-loop"


@dataclass
class Message:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class ModelConfig:
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    stop_sequences: list[str] = field(default_factory=list)
