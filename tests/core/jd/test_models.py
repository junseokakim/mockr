from __future__ import annotations

from mockr.core.jd.models import InterviewIntel, RoleProfile, Skill


class TestJDModels:
    def test_skill_creation(self) -> None:
        skill = Skill(
            name="distributed systems",
            category="system-design",
            dimensions=["structure", "reliability"],
            weight=0.8,
        )
        assert skill.weight == 0.8

    def test_interview_intel_creation(self) -> None:
        intel = InterviewIntel(
            format=["phone screen", "2x coding", "system design"],
            common_topics=["API design", "concurrency"],
            culture_signals=["They value communication"],
            gotchas=["System design is only 30 min"],
            sources=["https://glassdoor.com/..."],
        )
        assert len(intel.format) == 3

    def test_role_profile_creation(self) -> None:
        skill = Skill(name="Python", category="coding", dimensions=["correctness"], weight=0.9)
        profile = RoleProfile(
            id="rp-1",
            role_title="Senior Backend Engineer",
            inferred_level="senior",
            raw_text="We are looking for...",
            key_skills=[skill],
            company="Stripe",
            tech_stack=["Python", "PostgreSQL"],
            domain="fintech",
        )
        assert profile.company == "Stripe"
        assert profile.interview_intel is None

    def test_role_profile_without_optional_fields(self) -> None:
        profile = RoleProfile(
            id="rp-2",
            role_title="Software Engineer",
            inferred_level="mid",
            raw_text="Job description text",
        )
        assert profile.company is None
        assert profile.tech_stack == []
        assert profile.key_skills == []
