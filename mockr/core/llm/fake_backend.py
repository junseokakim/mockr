"""Fake LLM backend for TUI testing — returns canned responses."""

from __future__ import annotations

import asyncio
import json

from mockr.core.types import Message, ModelConfig

_QUESTION_RESPONSES = {
    "system-design": (
        "INTERVIEWER: Let's design a URL shortener like bit.ly. "
        "Walk me through how you'd approach this system. "
        "Start with requirements and high-level components.\n\n"
        "COACH: Think about scale, read/write ratios, and database choice."
    ),
    "coding": (
        "INTERVIEWER: Given a list of integers, write a function that returns "
        "the two numbers that sum to a target value. "
        "Assume exactly one solution exists.\n\n"
        "COACH: Think about time complexity — can you do better than O(n²)?"
    ),
    "behavioral": (
        "INTERVIEWER: Tell me about a time you had to make a difficult technical "
        "decision with incomplete information. What was the situation and outcome?"
    ),
    "default": (
        "INTERVIEWER: Let's start the interview. Tell me about your background "
        "and what kind of problems you enjoy solving most."
    ),
}

_SCORE_TEMPLATE = {
    "dimensions": {
        "structure": 3.5,
        "constraints": 3.0,
        "tradeoffs": 3.5,
        "reliability": 3.0,
        "concreteness": 3.5,
    },
    "strengths": [
        "Good high-level structure",
        "Identified key components clearly",
    ],
    "improvements": [
        "Quantify scale requirements (QPS, data size)",
        "Discuss database choice trade-offs",
    ],
}

_NEXT_QUESTION_RESPONSES = [
    (
        "INTERVIEWER: Good start! Now let's dig deeper. How would you handle "
        "caching to reduce latency on read-heavy endpoints?\n\n"
        "COACH: Consider cache invalidation strategies and TTL."
    ),
    (
        "INTERVIEWER: Interesting approach. How would this system handle "
        "a 10x traffic spike? What bottlenecks do you foresee?\n\n"
        "COACH: Think about horizontal scaling and statelessness."
    ),
    (
        "INTERVIEWER: Let's discuss failure modes. What happens if your "
        "primary database goes down?\n\n"
        "COACH: Replicas, failover time, and read availability matter here."
    ),
    (
        "INTERVIEWER: Walk me through how you'd monitor this system "
        "in production. What metrics would you track?\n\n"
        "COACH: SLOs, error rates, latency percentiles are a good start."
    ),
]

_DEBRIEF_TEMPLATE = {
    "overall_score": 3.5,
    "dimension_scores": {
        "structure": 3.5,
        "constraints": 3.0,
        "tradeoffs": 4.0,
        "reliability": 3.0,
        "concreteness": 3.5,
    },
    "summary": (
        "Strong opening with clear system decomposition. The candidate demonstrated "
        "good intuition about caching and horizontal scaling. Main areas to improve: "
        "be more precise about scale numbers upfront and discuss failure modes proactively."
    ),
}


# Pre-serialized JSON responses — avoid repeated json.dumps on every call
_DEBRIEF_JSON = json.dumps(_DEBRIEF_TEMPLATE)
_SCORE_JSON = json.dumps(_SCORE_TEMPLATE)


class FakeLLMBackend:
    """Returns deterministic canned responses for TUI smoke-testing."""

    def __init__(self, mode: str = "system-design", delay: float = 0.5) -> None:
        self._mode = mode
        self._delay = delay
        self._call_count = 0

    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        await asyncio.sleep(self._delay)
        self._call_count += 1
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        last_lower = last_user.lower()
        if "debrief" in last_lower or "overall_score" in last_lower:
            return _DEBRIEF_JSON
        if "score each dimension" in last_lower:
            return _SCORE_JSON
        if self._call_count == 1 or "start the interview" in last_lower:
            return _QUESTION_RESPONSES.get(self._mode, _QUESTION_RESPONSES["default"])
        idx = min(self._call_count - 2, len(_NEXT_QUESTION_RESPONSES) - 1)
        return _NEXT_QUESTION_RESPONSES[idx]
