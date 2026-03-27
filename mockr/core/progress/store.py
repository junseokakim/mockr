"""SQLite persistence for sessions and progress tracking."""

from __future__ import annotations

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

    def close(self) -> None:
        self._conn.close()
