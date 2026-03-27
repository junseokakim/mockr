from __future__ import annotations

import json

import pytest

from mockr.core.challenges.models import Challenge
from mockr.core.jd.challenge_gen import ChallengeGenerator
from mockr.core.jd.models import Skill
from mockr.core.types import Message, ModelConfig


class FakeChallengeBackend:
    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        content = " ".join(m.content.lower() for m in messages)
        if "review" in content and "solvable" in content:
            return json.dumps({"pass": True, "reason": "Challenge is well-scoped"})
        return json.dumps({
            "id": "generated-k8s-networking",
            "title": "Kubernetes Service Mesh Design",
            "mode": "system-design",
            "tags": ["kubernetes", "networking", "service-mesh"],
            "levels": {
                "senior": {
                    "estimated_minutes": 15,
                    "interviewer": "Design a service mesh for Kubernetes...",
                    "must_cover": ["sidecar proxy", "service discovery", "load balancing"],
                    "follow_ups": ["How do you handle mTLS?"],
                }
            },
        })


@pytest.mark.asyncio
class TestChallengeGenerator:
    async def test_generate_challenge_for_skill(self) -> None:
        skill = Skill(name="Kubernetes networking", category="system-design", dimensions=["structure"], weight=0.9)
        generator = ChallengeGenerator(
            backend=FakeChallengeBackend(),
            config=ModelConfig(model="test"),
        )
        challenge = await generator.generate_for_skill(skill, target_level="senior", tech_stack=["Kubernetes", "Go"])
        assert isinstance(challenge, Challenge)
        assert challenge.mode == "system-design"
        assert len(challenge.levels) > 0
        assert challenge.id.startswith("generated-")

    async def test_generate_challenge_marked_as_generated(self) -> None:
        skill = Skill(name="test", category="coding", dimensions=["correctness"], weight=0.5)
        generator = ChallengeGenerator(
            backend=FakeChallengeBackend(),
            config=ModelConfig(model="test"),
        )
        challenge = await generator.generate_for_skill(skill, target_level="senior")
        assert challenge.tags is not None
        assert "generated" in challenge.tags
