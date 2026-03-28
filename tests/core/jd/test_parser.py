from __future__ import annotations

import json

import pytest

from mockr.core.jd.models import RoleProfile
from mockr.core.jd.parser import JDParser
from mockr.core.types import Message, ModelConfig


class FakeParserBackend:
    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        return json.dumps(
            {
                "company": "Stripe",
                "role_title": "Senior Backend Engineer",
                "inferred_level": "senior",
                "tech_stack": ["Python", "PostgreSQL", "Kubernetes"],
                "domain": "fintech",
                "key_skills": [
                    {
                        "name": "distributed systems",
                        "category": "system-design",
                        "dimensions": ["structure", "reliability"],
                        "weight": 0.9,
                    },
                    {
                        "name": "Python",
                        "category": "coding",
                        "dimensions": ["correctness", "code_quality"],
                        "weight": 0.8,
                    },
                    {"name": "leadership", "category": "behavioral", "dimensions": ["action", "impact"], "weight": 0.6},
                ],
            }
        )


@pytest.mark.asyncio
class TestJDParser:
    async def test_parse_jd_text(self) -> None:
        parser = JDParser(backend=FakeParserBackend(), config=ModelConfig(model="test"))
        profile = await parser.parse_text("We are looking for a Senior Backend Engineer at Stripe...")
        assert isinstance(profile, RoleProfile)
        assert profile.company == "Stripe"
        assert profile.inferred_level == "senior"
        assert len(profile.key_skills) == 3

    async def test_parse_jd_preserves_raw_text(self) -> None:
        parser = JDParser(backend=FakeParserBackend(), config=ModelConfig(model="test"))
        raw = "This is the original JD text."
        profile = await parser.parse_text(raw)
        assert profile.raw_text == raw

    async def test_parse_jd_handles_missing_company(self) -> None:
        class NoCompanyBackend:
            async def generate(self, messages, config):
                return json.dumps(
                    {
                        "company": None,
                        "role_title": "Software Engineer",
                        "inferred_level": "mid",
                        "tech_stack": [],
                        "domain": None,
                        "key_skills": [],
                    }
                )

        parser = JDParser(backend=NoCompanyBackend(), config=ModelConfig(model="test"))
        profile = await parser.parse_text("Generic SWE role")
        assert profile.company is None
        assert profile.role_title == "Software Engineer"
