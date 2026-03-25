from __future__ import annotations
import pytest
from mockr.core.execution.python_runner import PythonRunner


@pytest.mark.asyncio
class TestPythonRunner:
    async def test_correct_code_passes(self) -> None:
        runner = PythonRunner()
        result = await runner.run(
            code="def two_sum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i]+nums[j]==target:\n                return [i,j]",
            test_code="assert two_sum([2,7,11,15], 9) == [0, 1]\nprint('PASS')",
        )
        assert result.exit_code == 0
        assert "PASS" in result.stdout

    async def test_wrong_code_fails(self) -> None:
        runner = PythonRunner()
        result = await runner.run(
            code="def two_sum(nums, target):\n    return [0, 0]",
            test_code="assert two_sum([2,7,11,15], 9) == [0, 1]",
        )
        assert result.exit_code != 0

    async def test_timeout_kills_process(self) -> None:
        runner = PythonRunner(timeout=2)
        result = await runner.run(
            code="import time\ntime.sleep(10)",
            test_code="pass",
        )
        assert result.exit_code != 0

    async def test_syntax_error_captured(self) -> None:
        runner = PythonRunner()
        result = await runner.run(
            code="def broken(\n",
            test_code="pass",
        )
        assert result.exit_code != 0
        assert "SyntaxError" in result.stderr or "Error" in result.stderr
