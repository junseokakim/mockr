"""Rust code execution via rustc + subprocess."""

from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path

from mockr.core.execution.python_runner import RunResult


class RustRunner:
    def __init__(self, timeout: int = 10) -> None:
        self._timeout = timeout

    async def run(self, code: str, test_code: str) -> RunResult:
        full_code = f"{code}\n\n{test_code}\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / "src.rs"
            out_path = Path(tmpdir) / "out"
            src_path.write_text(full_code, encoding="utf-8")

            # Compile step
            start = time.monotonic()
            compile_proc = await asyncio.create_subprocess_exec(
                "rustc",
                str(src_path),
                "-o",
                str(out_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                c_stdout, c_stderr = await asyncio.wait_for(compile_proc.communicate(), timeout=self._timeout)
            except TimeoutError:
                compile_proc.kill()
                await compile_proc.communicate()
                elapsed = int((time.monotonic() - start) * 1000)
                return RunResult(
                    stdout="",
                    stderr=f"Compile timeout after {self._timeout}s",
                    exit_code=1,
                    execution_time_ms=elapsed,
                )

            if compile_proc.returncode != 0:
                elapsed = int((time.monotonic() - start) * 1000)
                return RunResult(
                    stdout=c_stdout.decode("utf-8", errors="replace"),
                    stderr=c_stderr.decode("utf-8", errors="replace"),
                    exit_code=compile_proc.returncode,
                    execution_time_ms=elapsed,
                )

            # Run step
            run_proc = await asyncio.create_subprocess_exec(
                str(out_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                r_stdout, r_stderr = await asyncio.wait_for(run_proc.communicate(), timeout=self._timeout)
            except TimeoutError:
                run_proc.kill()
                await run_proc.communicate()
                elapsed = int((time.monotonic() - start) * 1000)
                return RunResult(
                    stdout="",
                    stderr=f"Timeout after {self._timeout}s",
                    exit_code=1,
                    execution_time_ms=elapsed,
                )

            elapsed = int((time.monotonic() - start) * 1000)
            return RunResult(
                stdout=r_stdout.decode("utf-8", errors="replace"),
                stderr=r_stderr.decode("utf-8", errors="replace"),
                exit_code=run_proc.returncode or 0,
                execution_time_ms=elapsed,
            )
