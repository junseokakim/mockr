"""TOML challenge loader and validator."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 12):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

from mockr.core.challenges.models import Challenge, LevelConfig, TestCase


def load_challenge(path: Path) -> Challenge:
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    meta = raw.get("meta", {})
    levels: dict[str, LevelConfig] = {}
    for level_name, level_data in raw.get("levels", {}).items():
        levels[level_name] = LevelConfig(
            estimated_minutes=level_data.get("estimated_minutes", 20),
            interviewer=level_data.get("interviewer", ""),
            must_cover=level_data.get("must_cover", []),
            follow_ups=level_data.get("follow_ups", []),
        )

    test_cases: list[TestCase] = []
    for tc in raw.get("test_cases", []):
        test_cases.append(
            TestCase(
                input=tc.get("input", ""),
                expected=tc.get("expected", ""),
                expected_columns=tc.get("expected_columns", []),
                expected_rows=tc.get("expected_rows", []),
                setup_extra=tc.get("setup_extra", ""),
                expected_note=tc.get("expected_note", ""),
                hidden=tc.get("hidden", False),
            )
        )

    return Challenge(
        id=meta.get("id", ""),
        title=meta.get("title", ""),
        mode=meta.get("mode", ""),
        tags=meta.get("tags", []),
        language=meta.get("language", ""),
        levels=levels,
        setup_sql=raw.get("setup", {}).get("sql", ""),
        test_cases=test_cases,
    )


def load_challenges_from_dir(directory: Path) -> list[Challenge]:
    challenges: list[Challenge] = []
    for path in sorted(directory.rglob("*.toml")):
        challenges.append(load_challenge(path))
    return challenges


def validate_challenge(challenge: Challenge) -> list[str]:
    errors: list[str] = []
    if not challenge.id:
        errors.append("Missing meta.id")
    if not challenge.title:
        errors.append("Missing meta.title")
    if not challenge.mode:
        errors.append("Missing meta.mode")
    if not challenge.levels:
        errors.append("No levels defined — need at least one level section")
    for level_name, level_cfg in challenge.levels.items():
        if not level_cfg.interviewer:
            errors.append(f"Level '{level_name}' missing interviewer prompt")
    return errors
