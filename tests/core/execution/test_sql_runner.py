from __future__ import annotations

import pytest

from mockr.core.execution.sql_runner import SQLRunner


@pytest.mark.asyncio
class TestSQLRunner:
    async def test_correct_query(self) -> None:
        runner = SQLRunner()
        result = await runner.run(
            setup_sql="CREATE TABLE t (id INT); INSERT INTO t VALUES (1), (2), (3);",
            query="SELECT id FROM t ORDER BY id",
            expected_columns=["id"],
            expected_rows=[[1], [2], [3]],
        )
        assert result.passed is True

    async def test_wrong_query(self) -> None:
        runner = SQLRunner()
        result = await runner.run(
            setup_sql="CREATE TABLE t (id INT); INSERT INTO t VALUES (1);",
            query="SELECT id FROM t",
            expected_columns=["id"],
            expected_rows=[[999]],
        )
        assert result.passed is False

    async def test_setup_extra(self) -> None:
        runner = SQLRunner()
        result = await runner.run(
            setup_sql="CREATE TABLE t (id INT); INSERT INTO t VALUES (1);",
            query="SELECT count(*) as cnt FROM t",
            expected_columns=["cnt"],
            expected_rows=[[2]],
            setup_extra="INSERT INTO t VALUES (2);",
        )
        assert result.passed is True
