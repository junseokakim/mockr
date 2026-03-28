"""Interview intel gathering via web search + LLM summarization."""

from __future__ import annotations

from mockr.core.jd.models import InterviewIntel
from mockr.core.types import Message, ModelConfig
from mockr.core.utils import extract_json_object

_INTEL_PROMPT = """You are summarizing interview process information for a candidate.

Based on the following search results about interviews at {company} for {role_title}, extract:
- "format": list of interview stages/rounds (strings)
- "common_topics": list of commonly asked topics (strings)
- "culture_signals": list of what interviewers value (strings)
- "gotchas": list of known quirks or tips (strings)

If the search results don't contain useful interview information, return {{"empty": true}}.

Return ONLY valid JSON.

Search results:
{search_results}"""


class IntelGatherer:
    def __init__(self, backend: object, config: ModelConfig, web_searcher: object) -> None:
        self._backend = backend
        self._config = config
        self._searcher = web_searcher

    async def gather(self, company: str, role_title: str) -> InterviewIntel | None:
        queries = [
            f"{company} software engineer interview process glassdoor",
            f"{company} interview questions reddit",
            f"{company} {role_title} interview blind",
        ]

        all_results: list[dict] = []
        for query in queries:
            results = await self._searcher.search(query)
            all_results.extend(results)

        if not all_results:
            return None

        sources = [r["url"] for r in all_results]
        snippets = "\n".join(f"- [{r['url']}]: {r['snippet']}" for r in all_results)

        prompt = _INTEL_PROMPT.format(
            company=company,
            role_title=role_title,
            search_results=snippets,
        )
        raw = await self._backend.generate(
            [Message(role="user", content=prompt)],
            self._config,
        )

        try:
            data = extract_json_object(raw)
        except (ValueError, KeyError):
            return None

        if data.get("empty"):
            return None

        return InterviewIntel(
            format=data.get("format", []),
            common_topics=data.get("common_topics", []),
            culture_signals=data.get("culture_signals", []),
            gotchas=data.get("gotchas", []),
            sources=sources,
        )
