from __future__ import annotations

from pathlib import Path

import pytest

from mockr.core.challenges.loader import load_challenge, load_challenges_from_dir, validate_challenge
from mockr.core.challenges.models import Challenge


class TestLoadChallenge:
    def test_load_system_design(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "cache.toml"
        toml_file.write_text('''
[meta]
id = "cache"
title = "Distributed Cache"
mode = "system-design"
tags = ["caching"]

[levels.senior]
estimated_minutes = 20
interviewer = "Design a cache."
must_cover = ["eviction"]
follow_ups = ["What about TTL?"]
''')
        challenge = load_challenge(toml_file)
        assert challenge.id == "cache"
        assert challenge.mode == "system-design"
        assert "senior" in challenge.levels
        assert challenge.levels["senior"].estimated_minutes == 20

    def test_load_coding_with_test_cases(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "two-sum.toml"
        toml_file.write_text('''
[meta]
id = "two-sum"
title = "Two Sum"
mode = "coding"
language = "python"
tags = ["arrays"]

[levels.mid]
estimated_minutes = 30
interviewer = "Solve two sum."
follow_ups = ["Time complexity?"]

[[test_cases]]
input = "nums = [2, 7], target = 9"
expected = "[0, 1]"
hidden = false

[[test_cases]]
input = "nums = [3, 3], target = 6"
expected = "[0, 1]"
hidden = true
''')
        challenge = load_challenge(toml_file)
        assert challenge.language == "python"
        assert len(challenge.test_cases) == 2
        assert challenge.test_cases[1].hidden is True

    def test_load_sql_with_setup(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "cohort.toml"
        toml_file.write_text('''
[meta]
id = "cohort"
title = "Revenue Cohort"
mode = "coding"
language = "sql"
tags = ["sql"]

[setup]
sql = "CREATE TABLE users (id INT);"

[levels.senior]
estimated_minutes = 20
interviewer = "Write the query."
follow_ups = []

[[test_cases]]
expected_columns = ["id"]
expected_rows = [[1]]
hidden = false
''')
        challenge = load_challenge(toml_file)
        assert challenge.setup_sql == "CREATE TABLE users (id INT);"
        assert challenge.test_cases[0].expected_columns == ["id"]


class TestLoadFromDir:
    def test_loads_all_toml_files(self, tmp_path: Path) -> None:
        for name in ("a.toml", "b.toml"):
            (tmp_path / name).write_text(f'''
[meta]
id = "{name[0]}"
title = "Challenge {name[0].upper()}"
mode = "system-design"
tags = []

[levels.senior]
estimated_minutes = 20
interviewer = "Design something."
must_cover = []
follow_ups = []
''')
        challenges = load_challenges_from_dir(tmp_path)
        assert len(challenges) == 2

    def test_skips_non_toml(self, tmp_path: Path) -> None:
        (tmp_path / "readme.md").write_text("# not a challenge")
        challenges = load_challenges_from_dir(tmp_path)
        assert len(challenges) == 0


class TestValidation:
    def test_valid_challenge_passes(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "valid.toml"
        toml_file.write_text('''
[meta]
id = "valid"
title = "Valid"
mode = "system-design"
tags = []

[levels.senior]
estimated_minutes = 20
interviewer = "Design it."
must_cover = []
follow_ups = []
''')
        challenge = load_challenge(toml_file)
        errors = validate_challenge(challenge)
        assert errors == []

    def test_missing_levels_fails(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "bad.toml"
        toml_file.write_text('''
[meta]
id = "bad"
title = "Bad"
mode = "system-design"
tags = []
''')
        challenge = load_challenge(toml_file)
        errors = validate_challenge(challenge)
        assert any("level" in e.lower() for e in errors)
