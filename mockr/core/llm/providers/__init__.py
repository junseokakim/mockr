"""LLM provider implementations."""

from __future__ import annotations

import asyncio
import os


async def run_subprocess(
    cmd: list[str],
    stdin_data: str,
    timeout: int,
    cwd: str | None = None,
    clear_env: list[str] | None = None,
) -> str:
    env = dict(os.environ)
    for key in clear_env or []:
        env.pop(key, None)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(stdin_data.encode("utf-8")), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.communicate()
        raise TimeoutError(f"Command timed out after {timeout}s")
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed (exit {proc.returncode}): {stderr.decode('utf-8', errors='replace')}")
    return stdout.decode("utf-8", errors="replace")
