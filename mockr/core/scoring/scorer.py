"""LLM-based scoring for interview answers."""
from __future__ import annotations
from dataclasses import dataclass, field

from mockr.core.utils import extract_json_object

DIMENSIONS_BY_MODE: dict[str, list[str]] = {
    "system-design": ["structure", "constraints", "tradeoffs", "reliability", "concreteness"],
    "coding": ["correctness", "efficiency", "code_quality", "edge_cases", "communication"],
    "behavioral": ["situation", "task", "action", "result", "impact"],
}


@dataclass
class ScoreResult:
    dimensions: dict[str, float]
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)


class Scorer:
    def build_scoring_prompt(self, mode: str, level: str, answer: str,
                              must_cover: list[str], turn_number: int) -> str:
        dimensions = DIMENSIONS_BY_MODE.get(mode, DIMENSIONS_BY_MODE["system-design"])
        dims_str = ", ".join(dimensions)
        must_cover_str = "\n".join(f"  - {item}" for item in must_cover) if must_cover else "  (none specified)"
        return f"""You are scoring a mock interview answer.

Mode: {mode}
Target level: {level}
Turn: {turn_number}

Candidate's answer:
{answer}

Required topics (items not addressed should lower relevant dimension scores):
{must_cover_str}

Score each dimension on a 1-5 scale:
  1 = Not addressed
  2 = Mentioned but shallow
  3 = Adequate for {level} level
  4 = Strong — shows depth and judgment
  5 = Exceptional — would impress at {level} level

Dimensions to score: {dims_str}

Return ONLY valid JSON in this exact format:
{{
  "dimensions": {{{", ".join(f'"{d}": <1-5>' for d in dimensions)}}},
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<improvement 1>", "<improvement 2>"]
}}"""

    def parse_score_response(self, raw: str, mode: str) -> ScoreResult:
        dimensions = DIMENSIONS_BY_MODE.get(mode, DIMENSIONS_BY_MODE["system-design"])
        try:
            data = extract_json_object(raw)
            dim_scores = {}
            raw_dims = data.get("dimensions", {})
            for d in dimensions:
                score = raw_dims.get(d, 3)
                dim_scores[d] = float(max(1, min(5, score)))
            return ScoreResult(
                dimensions=dim_scores,
                strengths=data.get("strengths", []),
                improvements=data.get("improvements", []),
            )
        except (ValueError, KeyError, TypeError):
            return ScoreResult(
                dimensions={d: 3.0 for d in dimensions},
                strengths=[], improvements=["(Scoring failed — using default scores)"],
            )
