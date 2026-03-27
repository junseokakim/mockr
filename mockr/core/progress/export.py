"""JSON/CSV export for progress data."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from mockr.core.progress.store import ProgressStore

DEFAULT_DB_PATH = Path.home() / ".mockr" / "mockr.db"


def export_data(fmt: str, output_path: str | None = None) -> str:
    store = ProgressStore(DEFAULT_DB_PATH)
    sessions = store.list_sessions(limit=1000)
    store.close()

    if fmt == "json":
        content = json.dumps(sessions, indent=2, default=str)
    elif fmt == "csv":
        if not sessions:
            content = ""
        else:
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=sessions[0].keys())
            writer.writeheader()
            writer.writerows(sessions)
            content = buf.getvalue()
    else:
        content = ""

    if output_path:
        Path(output_path).write_text(content)
        return f"Exported {len(sessions)} sessions to {output_path}"
    return content
