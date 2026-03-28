from __future__ import annotations

import json

import pytest

from mockr.core.jd.intel import IntelGatherer
from mockr.core.jd.models import InterviewIntel
from mockr.core.types import Message, ModelConfig


class FakeIntelBackend:
    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        return json.dumps(
            {
                "format": ["phone screen", "2x coding", "system design", "behavioral"],
                "common_topics": ["API design", "concurrency", "system scalability"],
                "culture_signals": ["Strong emphasis on communication"],
                "gotchas": ["System design round is only 30 minutes"],
            }
        )


class FakeWebSearcher:
    async def search(self, query: str) -> list[dict]:
        return [
            {"url": "https://glassdoor.com/stripe-interview", "snippet": "Phone screen then coding rounds"},
            {"url": "https://reddit.com/r/cscareerquestions/stripe", "snippet": "System design is fast-paced"},
        ]


@pytest.mark.asyncio
class TestIntelGatherer:
    async def test_gather_intel(self) -> None:
        gatherer = IntelGatherer(
            backend=FakeIntelBackend(),
            config=ModelConfig(model="test"),
            web_searcher=FakeWebSearcher(),
        )
        intel = await gatherer.gather(company="Stripe", role_title="Senior Backend Engineer")
        assert isinstance(intel, InterviewIntel)
        assert len(intel.format) > 0
        assert len(intel.sources) > 0

    async def test_gather_intel_no_results(self) -> None:
        class EmptySearcher:
            async def search(self, query: str) -> list[dict]:
                return []

        gatherer = IntelGatherer(
            backend=FakeIntelBackend(),
            config=ModelConfig(model="test"),
            web_searcher=EmptySearcher(),
        )
        intel = await gatherer.gather(company="TinyStartup", role_title="SWE")
        assert intel is None
