"""Dispatch execution to the correct language runner."""

from __future__ import annotations

from mockr.core.execution.js_runner import JSRunner
from mockr.core.execution.python_runner import PythonRunner, RunResult
from mockr.core.execution.rust_runner import RustRunner
from mockr.core.execution.sql_runner import SQLResult, SQLRunner


class ExecutionEngine:
    def __init__(self, timeout: int = 10) -> None:
        self._python = PythonRunner(timeout=timeout)
        self._sql = SQLRunner()
        self._rust = RustRunner(timeout=timeout)
        self._js = JSRunner(timeout=timeout)

    async def run_python(self, code: str, test_code: str) -> RunResult:
        return await self._python.run(code, test_code)

    async def run_sql(
        self,
        setup_sql: str,
        query: str,
        expected_columns: list[str],
        expected_rows: list[list],
        setup_extra: str = "",
    ) -> SQLResult:
        return await self._sql.run(setup_sql, query, expected_columns, expected_rows, setup_extra)

    async def run_rust(self, code: str, test_code: str) -> RunResult:
        return await self._rust.run(code, test_code)

    async def run_js(self, code: str, test_code: str) -> RunResult:
        return await self._js.run(code, test_code)
