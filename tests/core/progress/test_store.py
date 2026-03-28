from __future__ import annotations

import json
from pathlib import Path

from mockr.core.progress.store import ProgressStore


class TestProgressStore:
    def test_create_tables(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        store = ProgressStore(db_path)
        tables = store.list_tables()
        assert "sessions" in tables
        assert "turn_scores" in tables
        assert "challenge_stats" in tables
        assert "dimension_stats" in tables

    def test_save_and_get_session(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_session(session_id="s1", mode="coding", challenge_id="two-sum", level="senior", provider="ollama")
        session = store.get_session("s1")
        assert session is not None
        assert session["mode"] == "coding"
        assert session["level"] == "senior"

    def test_save_turn_score(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_session(session_id="s1", mode="coding", challenge_id="x", level="mid", provider="ollama")
        store.save_turn_score(session_id="s1", turn_number=1, dimension="correctness", score=4.0, feedback="Good job")
        scores = store.get_turn_scores("s1")
        assert len(scores) == 1
        assert scores[0]["score"] == 4.0

    def test_update_challenge_stats(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.update_challenge_stats("cache", "senior", score=3.5)
        stats = store.get_challenge_stats("cache", "senior")
        assert stats["times_attempted"] == 1
        assert stats["avg_score"] == 3.5
        store.update_challenge_stats("cache", "senior", score=4.5)
        stats = store.get_challenge_stats("cache", "senior")
        assert stats["times_attempted"] == 2
        assert stats["avg_score"] == 4.0

    def test_list_sessions(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_session(session_id="s1", mode="coding", challenge_id="a", level="mid", provider="ollama")
        store.save_session(session_id="s2", mode="behavioral", challenge_id="b", level="staff", provider="claude-cli")
        sessions = store.list_sessions()
        assert len(sessions) == 2

    def test_complete_session(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_session(session_id="s1", mode="coding", challenge_id="a", level="mid", provider="ollama")
        store.complete_session("s1", overall_score=4.0, debrief="Great session")
        session = store.get_session("s1")
        assert session["state"] == "complete"
        assert session["overall_score"] == 4.0

    def test_pause_and_resume(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_session(session_id="s1", mode="coding", challenge_id="a", level="mid", provider="ollama")
        store.pause_session("s1", suspended_state='{"turn": 3}')
        session = store.get_session("s1")
        assert session["state"] == "paused"
        assert session["suspended_state"] == '{"turn": 3}'


class TestAssessmentPersistence:
    def test_new_tables_created(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        tables = store.list_tables()
        assert "assessments" in tables
        assert "role_profiles" in tables
        assert "practice_plans" in tables
        assert "plan_items" in tables

    def test_save_and_get_assessment(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        mode_scores = {"coding": {"correctness": 3.5, "efficiency": 2.0}}
        store.save_assessment(
            assessment_id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores=mode_scores,
        )
        result = store.get_assessment("a1")
        assert result is not None
        assert result["target_level"] == "senior"
        assert json.loads(result["mode_scores"]) == mode_scores

    def test_save_and_get_role_profile(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        skills = [{"name": "Python", "category": "coding", "dimensions": ["correctness"], "weight": 0.9}]
        store.save_role_profile(
            profile_id="rp1",
            company="Stripe",
            role_title="Senior Backend Engineer",
            inferred_level="senior",
            tech_stack=["Python", "PostgreSQL"],
            domain="fintech",
            key_skills=skills,
            interview_intel=None,
            raw_text="We are looking for...",
        )
        result = store.get_role_profile("rp1")
        assert result is not None
        assert result["company"] == "Stripe"
        assert json.loads(result["tech_stack"]) == ["Python", "PostgreSQL"]

    def test_list_role_profiles(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_role_profile("rp1", "Stripe", "SWE", "senior", [], None, [], None, "text1")
        store.save_role_profile("rp2", "Google", "SRE", "staff", [], None, [], None, "text2")
        profiles = store.list_role_profiles()
        assert len(profiles) == 2

    def test_save_and_get_practice_plan(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_assessment("a1", "senior", "mid", {"coding": {"correctness": 2.0}})
        store.save_practice_plan(
            plan_id="p1",
            assessment_id="a1",
            role_profile_id=None,
            target_level="senior",
        )
        plan = store.get_practice_plan("p1")
        assert plan is not None
        assert plan["target_level"] == "senior"

    def test_save_and_get_plan_items(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_assessment("a1", "senior", "mid", {})
        store.save_practice_plan("p1", "a1", None, "senior")
        store.save_plan_item(
            item_id="i1",
            plan_id="p1",
            dimension="correctness",
            mode="coding",
            priority=0.8,
            gap_size=1.5,
            challenge_id=None,
            rationale="Score 2.0, need 3.5",
        )
        items = store.get_plan_items("p1")
        assert len(items) == 1
        assert items[0]["priority"] == 0.8

    def test_update_plan_item_status(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_assessment("a1", "senior", "mid", {})
        store.save_practice_plan("p1", "a1", None, "senior")
        store.save_plan_item("i1", "p1", "correctness", "coding", 0.8, 1.5, None, "reason")
        store.update_plan_item_status("i1", "validated")
        items = store.get_plan_items("p1")
        assert items[0]["status"] == "validated"
