"""JD text parsing via LLM extraction."""

from __future__ import annotations

import uuid

from mockr.core.jd.models import RoleProfile, Skill
from mockr.core.types import Message, ModelConfig
from mockr.core.utils import extract_json_object

_JD_EXTRACTION_PROMPT = """You are extracting structured information from a job description.

Analyze the following job description and return a JSON object with these fields:
- "company": company name (string or null if not found)
- "role_title": the job title (string)
- "inferred_level": map to one of: "intern", "junior", "mid", "senior", "staff", "principal", "engineering_manager", "director", "vp"
- "tech_stack": list of technologies mentioned (strings)
- "domain": industry domain like "fintech", "healthcare", "e-commerce" (string or null)
- "key_skills": list of objects, each with:
  - "name": skill name (string)
  - "category": one of "system-design", "coding", "behavioral"
  - "dimensions": list of scoring dimensions this skill relates to
    - For coding: from ["correctness", "efficiency", "code_quality", "edge_cases", "communication"]
    - For system-design: from ["structure", "constraints", "tradeoffs", "reliability", "concreteness"]
    - For behavioral: from ["situation", "task", "action", "result", "impact"]
  - "weight": how prominently this skill features in the JD (0.0 to 1.0)

Return ONLY valid JSON.

Job Description:
{jd_text}"""


class JDParser:
    def __init__(self, backend: object, config: ModelConfig) -> None:
        self._backend = backend
        self._config = config

    async def parse_text(self, jd_text: str) -> RoleProfile:
        prompt = _JD_EXTRACTION_PROMPT.format(jd_text=jd_text)
        raw = await self._backend.generate(
            [Message(role="user", content=prompt)],
            self._config,
        )
        data = extract_json_object(raw)

        skills = [
            Skill(
                name=s["name"],
                category=s.get("category", "coding"),
                dimensions=s.get("dimensions", []),
                weight=s.get("weight", 0.5),
            )
            for s in data.get("key_skills", [])
        ]

        return RoleProfile(
            id=str(uuid.uuid4()),
            company=data.get("company"),
            role_title=data.get("role_title", "Unknown Role"),
            inferred_level=data.get("inferred_level", "mid"),
            tech_stack=data.get("tech_stack", []),
            domain=data.get("domain"),
            key_skills=skills,
            raw_text=jd_text,
        )
