"""SQLite persistence for sessions and progress tracking."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path


class ProgressStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, mode TEXT NOT NULL, challenge_id TEXT,
                level TEXT, provider TEXT, state TEXT NOT NULL DEFAULT 'active',
                started_at TIMESTAMP, ended_at TIMESTAMP, overall_score REAL,
                debrief TEXT, suspended_state TEXT
            );
            CREATE TABLE IF NOT EXISTS turn_scores (
                id TEXT PRIMARY KEY, session_id TEXT REFERENCES sessions(id),
                turn_number INTEGER, dimension TEXT, score REAL, feedback TEXT
            );
            CREATE TABLE IF NOT EXISTS challenge_stats (
                challenge_id TEXT NOT NULL, level TEXT NOT NULL,
                times_attempted INTEGER DEFAULT 0, avg_score REAL DEFAULT 0,
                last_attempted TIMESTAMP, next_review TIMESTAMP,
                ease_factor REAL DEFAULT 2.5,
                PRIMARY KEY (challenge_id, level)
            );
            CREATE TABLE IF NOT EXISTS dimension_stats (
                dimension TEXT PRIMARY KEY, total_scores INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0, trend TEXT
            );
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                target_level TEXT NOT NULL,
                inferred_level TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                mode_scores TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS role_profiles (
                id TEXT PRIMARY KEY,
                company TEXT,
                role_title TEXT NOT NULL,
                inferred_level TEXT NOT NULL,
                tech_stack TEXT,
                domain TEXT,
                key_skills TEXT,
                interview_intel TEXT,
                raw_text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            );
            CREATE TABLE IF NOT EXISTS practice_plans (
                id TEXT PRIMARY KEY,
                assessment_id TEXT REFERENCES assessments(id),
                role_profile_id TEXT REFERENCES role_profiles(id),
                target_level TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            );
            CREATE TABLE IF NOT EXISTS plan_items (
                id TEXT PRIMARY KEY,
                plan_id TEXT REFERENCES practice_plans(id),
                dimension TEXT NOT NULL,
                mode TEXT NOT NULL,
                priority REAL NOT NULL,
                gap_size REAL NOT NULL,
                challenge_id TEXT,
                rationale TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            );
        """)
        self._conn.commit()

    def list_tables(self) -> list[str]:
        cursor = self._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row["name"] for row in cursor.fetchall()]

    def save_session(self, session_id: str, mode: str, challenge_id: str, level: str, provider: str) -> None:
        self._conn.execute(
            "INSERT INTO sessions (id, mode, challenge_id, level, provider, state, started_at) VALUES (?, ?, ?, ?, ?, 'active', ?)",
            (session_id, mode, challenge_id, level, provider, datetime.now(UTC).isoformat()),
        )
        self._conn.commit()

    def get_session(self, session_id: str) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_sessions(self, limit: int = 50) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def complete_session(self, session_id: str, overall_score: float, debrief: str) -> None:
        self._conn.execute(
            "UPDATE sessions SET state = 'complete', overall_score = ?, debrief = ?, ended_at = ? WHERE id = ?",
            (overall_score, debrief, datetime.now(UTC).isoformat(), session_id),
        )
        self._conn.commit()

    def pause_session(self, session_id: str, suspended_state: str) -> None:
        self._conn.execute(
            "UPDATE sessions SET state = 'paused', suspended_state = ? WHERE id = ?", (suspended_state, session_id)
        )
        self._conn.commit()

    def resume_session(self, session_id: str) -> None:
        self._conn.execute("UPDATE sessions SET state = 'active', suspended_state = NULL WHERE id = ?", (session_id,))
        self._conn.commit()

    def save_turn_score(self, session_id: str, turn_number: int, dimension: str, score: float, feedback: str) -> None:
        self._conn.execute(
            "INSERT INTO turn_scores (id, session_id, turn_number, dimension, score, feedback) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, turn_number, dimension, score, feedback),
        )
        self._conn.commit()

    def get_turn_scores(self, session_id: str) -> list[dict]:
        cursor = self._conn.execute(
            "SELECT * FROM turn_scores WHERE session_id = ? ORDER BY turn_number", (session_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_challenge_stats(self, challenge_id: str, level: str, score: float) -> None:
        existing = self.get_challenge_stats(challenge_id, level)
        now = datetime.now(UTC).isoformat()
        if existing:
            new_count = existing["times_attempted"] + 1
            new_avg = (existing["avg_score"] * existing["times_attempted"] + score) / new_count
            self._conn.execute(
                "UPDATE challenge_stats SET times_attempted = ?, avg_score = ?, last_attempted = ? WHERE challenge_id = ? AND level = ?",
                (new_count, new_avg, now, challenge_id, level),
            )
        else:
            self._conn.execute(
                "INSERT INTO challenge_stats (challenge_id, level, times_attempted, avg_score, last_attempted, ease_factor) VALUES (?, ?, 1, ?, ?, 2.5)",
                (challenge_id, level, score, now),
            )
        self._conn.commit()

    def get_challenge_stats(self, challenge_id: str, level: str) -> dict | None:
        cursor = self._conn.execute(
            "SELECT * FROM challenge_stats WHERE challenge_id = ? AND level = ?", (challenge_id, level)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_challenge_stats(self) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM challenge_stats ORDER BY next_review ASC")
        return [dict(row) for row in cursor.fetchall()]

    def save_assessment(
        self,
        assessment_id: str,
        target_level: str,
        inferred_level: str,
        mode_scores: dict,
    ) -> None:
        self._conn.execute(
            "INSERT INTO assessments (id, target_level, inferred_level, created_at, mode_scores) VALUES (?, ?, ?, ?, ?)",
            (assessment_id, target_level, inferred_level, datetime.now(UTC).isoformat(), json.dumps(mode_scores)),
        )
        self._conn.commit()

    def get_assessment(self, assessment_id: str) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def save_role_profile(
        self,
        profile_id: str,
        company: str | None,
        role_title: str,
        inferred_level: str,
        tech_stack: list[str],
        domain: str | None,
        key_skills: list[dict],
        interview_intel: dict | None,
        raw_text: str,
    ) -> None:
        self._conn.execute(
            "INSERT INTO role_profiles (id, company, role_title, inferred_level, tech_stack, domain, key_skills, interview_intel, raw_text, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                profile_id,
                company,
                role_title,
                inferred_level,
                json.dumps(tech_stack),
                domain,
                json.dumps(key_skills),
                json.dumps(interview_intel) if interview_intel else None,
                raw_text,
                datetime.now(UTC).isoformat(),
            ),
        )
        self._conn.commit()

    def get_role_profile(self, profile_id: str) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM role_profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_role_profiles(self) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM role_profiles ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def save_practice_plan(
        self,
        plan_id: str,
        assessment_id: str,
        role_profile_id: str | None,
        target_level: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT INTO practice_plans (id, assessment_id, role_profile_id, target_level, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (plan_id, assessment_id, role_profile_id, target_level, now, now),
        )
        self._conn.commit()

    def get_practice_plan(self, plan_id: str) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM practice_plans WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_latest_practice_plan(self) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM practice_plans ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

    def save_plan_item(
        self,
        item_id: str,
        plan_id: str,
        dimension: str,
        mode: str,
        priority: float,
        gap_size: float,
        challenge_id: str | None,
        rationale: str,
    ) -> None:
        self._conn.execute(
            "INSERT INTO plan_items (id, plan_id, dimension, mode, priority, gap_size, challenge_id, rationale) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (item_id, plan_id, dimension, mode, priority, gap_size, challenge_id, rationale),
        )
        self._conn.commit()

    def get_plan_items(self, plan_id: str) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM plan_items WHERE plan_id = ? ORDER BY priority DESC", (plan_id,))
        return [dict(row) for row in cursor.fetchall()]

    def update_plan_item_status(self, item_id: str, status: str) -> None:
        self._conn.execute("UPDATE plan_items SET status = ? WHERE id = ?", (status, item_id))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
