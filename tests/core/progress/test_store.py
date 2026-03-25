from __future__ import annotations
from pathlib import Path
import pytest
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
