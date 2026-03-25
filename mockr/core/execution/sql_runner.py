"""SQL execution via DuckDB (in-process)."""
from __future__ import annotations
from dataclasses import dataclass
import duckdb


@dataclass
class SQLResult:
    passed: bool
    actual_columns: list[str]
    actual_rows: list[list]
    error: str = ""


class SQLRunner:
    async def run(
        self,
        setup_sql: str,
        query: str,
        expected_columns: list[str],
        expected_rows: list[list],
        setup_extra: str = "",
    ) -> SQLResult:
        try:
            conn = duckdb.connect(":memory:")
            conn.execute(setup_sql)
            if setup_extra:
                conn.execute(setup_extra)
            result = conn.execute(query)
            columns = [desc[0] for desc in result.description]
            rows = [list(row) for row in result.fetchall()]
            conn.close()
            actual_sorted = sorted(rows)
            expected_sorted = sorted(expected_rows)
            passed = (
                [c.lower() for c in columns] == [c.lower() for c in expected_columns]
                and actual_sorted == expected_sorted
            )
            return SQLResult(passed=passed, actual_columns=columns, actual_rows=rows)
        except Exception as e:
            return SQLResult(passed=False, actual_columns=[], actual_rows=[], error=str(e))
