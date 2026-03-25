"""Code editor widget — TextArea with language-aware starter text."""
from __future__ import annotations

from textual.widgets import TextArea

_STARTERS: dict[str, str] = {
    "python": "def solution():\n    pass\n",
    "javascript": "function solution() {\n    \n}\n",
    "rust": "fn solution() {\n    \n}\n",
    "sql": "-- Write your query here\nSELECT\n    \nFROM\n    \n;\n",
}

# Languages Textual's TextArea recognises for syntax highlighting
_SUPPORTED_HIGHLIGHT = {"python", "javascript", "rust", "sql"}


class CodeEditor(TextArea):
    """TextArea pre-configured for a specific coding language."""

    def __init__(self, language: str = "python", **kwargs) -> None:
        lang_id = language if language in _SUPPORTED_HIGHLIGHT else "python"
        super().__init__(
            text=_STARTERS.get(language, ""),
            language=lang_id,
            **kwargs,
        )
        self._coding_language = language

    @property
    def coding_language(self) -> str:
        return self._coding_language
