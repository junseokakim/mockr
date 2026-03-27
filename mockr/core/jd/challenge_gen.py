"""LLM-based challenge generation from JD skills."""

from __future__ import annotations

import json

from mockr.core.challenges.models import Challenge, LevelConfig
from mockr.core.jd.models import Skill
from mockr.core.types import Message, ModelConfig
from mockr.core.utils import extract_json_object

_GENERATION_PROMPT = """Generate a mock interview challenge for the following skill.

Skill: {skill_name}
Mode: {mode}
Target level: {target_level}
Tech stack context: {tech_stack}

Return a JSON object with:
- "id": a slug starting with "generated-" (e.g., "generated-k8s-networking")
- "title": a descriptive title
- "mode": "{mode}"
- "tags": list of relevant tags (include the skill name)
- "levels": {{
    "{target_level}": {{
      "estimated_minutes": 15,
      "interviewer": "system prompt for the interviewer (2-3 sentences describing the problem)",
      "must_cover": ["topic 1", "topic 2", "topic 3"],
      "follow_ups": ["follow-up question 1", "follow-up question 2"]
    }}
  }}

Make the challenge appropriately scoped for {target_level} level.
Return ONLY valid JSON."""

_QUALITY_CHECK_PROMPT = """Review this interview challenge for quality.

{challenge_json}

Is this challenge:
1. Solvable within the estimated time?
2. Appropriately scoped for {target_level} level?
3. Testing the right skill ({skill_name})?

Return JSON: {{"pass": true/false, "reason": "..."}}"""


class ChallengeGenerator:
    def __init__(self, backend: object, config: ModelConfig) -> None:
        self._backend = backend
        self._config = config

    async def generate_for_skill(
        self,
        skill: Skill,
        target_level: str,
        tech_stack: list[str] | None = None,
    ) -> Challenge:
        prompt = _GENERATION_PROMPT.format(
            skill_name=skill.name,
            mode=skill.category,
            target_level=target_level,
            tech_stack=", ".join(tech_stack) if tech_stack else "general",
        )
        raw = await self._backend.generate(
            [Message(role="user", content=prompt)], self._config,
        )
        data = extract_json_object(raw)

        levels: dict[str, LevelConfig] = {}
        for level_name, level_data in data.get("levels", {}).items():
            levels[level_name] = LevelConfig(
                estimated_minutes=level_data.get("estimated_minutes", 15),
                interviewer=level_data.get("interviewer", ""),
                must_cover=level_data.get("must_cover", []),
                follow_ups=level_data.get("follow_ups", []),
            )

        tags = data.get("tags", [])
        if "generated" not in tags:
            tags.append("generated")

        challenge = Challenge(
            id=data.get("id", f"generated-{skill.name.lower().replace(' ', '-')}"),
            title=data.get("title", f"Generated: {skill.name}"),
            mode=data.get("mode", skill.category),
            tags=tags,
            levels=levels,
        )

        await self._quality_check(challenge, target_level, skill.name)

        return challenge

    async def _quality_check(self, challenge: Challenge, target_level: str, skill_name: str) -> None:
        challenge_json = json.dumps({
            "id": challenge.id,
            "title": challenge.title,
            "mode": challenge.mode,
            "levels": {
                name: {"interviewer": lc.interviewer, "must_cover": lc.must_cover}
                for name, lc in challenge.levels.items()
            },
        })
        prompt = _QUALITY_CHECK_PROMPT.format(
            challenge_json=challenge_json,
            target_level=target_level,
            skill_name=skill_name,
        )
        try:
            await self._backend.generate(
                [Message(role="user", content=prompt)], self._config,
            )
        except Exception:  # noqa: BLE001
            pass
