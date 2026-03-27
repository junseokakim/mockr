"""Shared utilities for mockr core."""

from __future__ import annotations

import json


def extract_json_object(raw: str) -> dict:
    """Extract the first JSON object from a string that may contain surrounding text."""
    json_start = raw.find("{")
    json_end = raw.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        return json.loads(raw[json_start:json_end])
    raise json.JSONDecodeError("No JSON found", raw, 0)
