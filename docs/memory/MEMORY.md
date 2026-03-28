# mockr Project Memory

## Branch: feat/assessment-jd-prep

### Completed Tasks

#### Task 1: Expand Level Enum (2026-03-27)
- Expanded `Level` enum in `mockr/core/types.py` from 4 levels (mid/senior/staff/principal) to 9
- Full IC track: INTERN, JUNIOR, MID, SENIOR, STAFF, PRINCIPAL
- Management track placeholders (not yet implemented): ENGINEERING_MANAGER, DIRECTOR, VP
- Updated `mockr/cli.py` `--level` CLI choices to include intern and junior
- Added `TestLevelExpansion` test class to `tests/core/test_types.py` (TDD — tests written first)
- All 86 tests pass (pre-existing `duckdb` import error in `test_sql_runner.py` is unrelated)
- Committed: `7f78ed1 feat: expand Level enum with intern, junior, and management placeholders`

### Open Items
- Tasks 2–14 remain pending on this branch
- `tests/core/execution/test_sql_runner.py` fails to collect due to missing `duckdb` module — pre-existing issue, not introduced here
