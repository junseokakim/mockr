"""Shared test fixtures for mockr."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Provide a clean temporary directory."""
    return tmp_path


@pytest.fixture
def sample_challenge_toml() -> str:
    """Minimal valid challenge TOML for testing."""
    return '''
[meta]
id = "test-challenge"
title = "Test Challenge"
mode = "system-design"
tags = ["testing"]

[levels.senior]
estimated_minutes = 20
interviewer = "Design a test system."
must_cover = ["scalability"]
follow_ups = ["What about failure modes?"]
'''
