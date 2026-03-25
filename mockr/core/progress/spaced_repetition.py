"""SM-2 spaced repetition algorithm adapted for interview practice."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class ReviewResult:
    next_interval_days: int
    ease_factor: float
    next_review: datetime


def _score_to_quality(score: float) -> int:
    if score >= 4.5:
        return 5
    elif score >= 3.5:
        return 4
    elif score >= 2.5:
        return 3
    elif score >= 1.5:
        return 2
    else:
        return 0


def compute_next_review(score: float, ease_factor: float, last_interval_days: int,
                         now: datetime | None = None) -> ReviewResult:
    now = now or datetime.now(timezone.utc)
    quality = _score_to_quality(score)
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)
    if quality < 3:
        next_interval = 1
    elif last_interval_days <= 0:
        next_interval = 1
    elif last_interval_days == 1:
        next_interval = 6
    else:
        next_interval = round(last_interval_days * new_ef)
    next_review = now + timedelta(days=next_interval)
    return ReviewResult(next_interval_days=next_interval, ease_factor=round(new_ef, 2), next_review=next_review)
