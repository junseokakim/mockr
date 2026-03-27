from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mockr.core.progress.spaced_repetition import compute_next_review


class TestSM2:
    def test_high_score_increases_interval(self) -> None:
        now = datetime.now(UTC)
        result = compute_next_review(score=4.5, ease_factor=2.5, last_interval_days=1, now=now)
        assert result.next_interval_days > 1
        assert result.ease_factor >= 2.5

    def test_low_score_resets_interval(self) -> None:
        now = datetime.now(UTC)
        result = compute_next_review(score=1.5, ease_factor=2.5, last_interval_days=10, now=now)
        assert result.next_interval_days <= 1
        assert result.ease_factor < 2.5

    def test_medium_score_moderate_growth(self) -> None:
        now = datetime.now(UTC)
        result = compute_next_review(score=3.0, ease_factor=2.5, last_interval_days=3, now=now)
        assert result.next_interval_days >= 3
        assert result.next_interval_days <= 15

    def test_ease_factor_never_below_1_3(self) -> None:
        now = datetime.now(UTC)
        result = compute_next_review(score=1.0, ease_factor=1.3, last_interval_days=1, now=now)
        assert result.ease_factor >= 1.3

    def test_next_review_date(self) -> None:
        now = datetime.now(UTC)
        result = compute_next_review(score=4.0, ease_factor=2.5, last_interval_days=1, now=now)
        expected_min = now + timedelta(days=1)
        assert result.next_review >= expected_min
