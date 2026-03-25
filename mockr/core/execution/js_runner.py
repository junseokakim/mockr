"""JavaScript code execution via Node.js subprocess."""
from __future__ import annotations
import asyncio
import tempfile
import time
from pathlib import Path

from mockr.core.execution.python_runner import RunResult


class JSRunner:
    def __init__(self, timeout: int = 10) -> None:
        self._timeout = timeout

    async def run(self, code: str, test_code: str) -> RunResult:
        full_code = f"{code}\n\n{test_code}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(full_code)
            tmp_path = f.name
        try:
            start = time.monotonic()
            proc = await asyncio.create_subprocess_exec(
                "node", tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self._timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                elapsed = int((time.monotonic() - start) * 1000)
                return RunResult(
                    stdout="",
                    stderr=f"Timeout after {self._timeout}s",
                    exit_code=1,
                    execution_time_ms=elapsed,
                )
            elapsed = int((time.monotonic() - start) * 1000)
            return RunResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                execution_time_ms=elapsed,
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)
