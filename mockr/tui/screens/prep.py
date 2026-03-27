"""Prep screen — parse job description and create role profile."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, TextArea


class PrepScreen(Screen):
    """JD parsing — paste a job description to create a role-specific prep plan."""

    BINDINGS = [
        Binding("ctrl+enter", "parse_jd", "Parse JD"),
        Binding("escape", "go_back", "Back"),
    ]

    CSS = """
    PrepScreen {
        layout: vertical;
    }

    #prep-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        height: 3;
        content-align: center middle;
        background: $surface-darken-1;
    }

    #prep-body {
        height: 1fr;
        margin: 1 2;
    }

    #jd-label {
        color: $text-muted;
        text-style: bold;
        height: 1;
        margin: 0 0 1 0;
    }

    #jd-input {
        height: 1fr;
        min-height: 10;
    }

    #prep-status {
        text-align: center;
        color: $text-muted;
        height: 1;
        margin: 1 0 0 0;
    }

    #profile-panel {
        border: round $accent;
        padding: 1 2;
        margin: 1 0;
        height: auto;
        max-height: 20;
        overflow-y: auto;
        display: none;
    }

    #profile-panel.visible {
        display: block;
    }

    #prep-buttons {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin: 1 0 0 0;
        display: none;
    }

    #prep-buttons.visible {
        display: block;
    }

    #prep-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._profile = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Prep for Role — Paste Job Description", id="prep-title")
        with Vertical(id="prep-body"):
            yield Static("Paste the job description below, then press Ctrl+Enter to parse:", id="jd-label")
            yield TextArea(id="jd-input")
            yield Static("", id="prep-status")
            yield Static("", id="profile-panel")
            with Horizontal(id="prep-buttons"):
                yield Button("Save & Generate Plan", id="btn-save", variant="primary")
                yield Button("Back", id="btn-back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#jd-input", TextArea).focus()

    def action_parse_jd(self) -> None:
        jd_input = self.query_one("#jd-input", TextArea)
        jd_text = jd_input.text.strip()

        if not jd_text:
            status = self.query_one("#prep-status", Static)
            status.update("[red]Please paste a job description first[/red]")
            return

        status = self.query_one("#prep-status", Static)
        status.update("Parsing job description...")
        self.run_worker(self._parse(jd_text))

    async def _parse(self, jd_text: str) -> None:
        from mockr.core.jd.parser import JDParser
        from mockr.core.llm.fake_backend import FakeLLMBackend
        from mockr.core.types import ModelConfig

        backend = FakeLLMBackend()
        config = ModelConfig(model="fake", temperature=0.7, max_tokens=1024)
        parser = JDParser(backend=backend, config=config)

        profile = await parser.parse_text(jd_text)
        self._profile = profile
        self._show_profile(profile)

    def _show_profile(self, profile) -> None:
        lines = [
            "[bold]Extracted Role Profile[/bold]\n",
            f"  Company:  [accent]{profile.company or 'Not detected'}[/accent]",
            f"  Role:     [accent]{profile.role_title}[/accent]",
            f"  Level:    [accent]{profile.inferred_level}[/accent]",
        ]

        if profile.tech_stack:
            lines.append(f"  Stack:    {', '.join(profile.tech_stack)}")

        if profile.domain:
            lines.append(f"  Domain:   {profile.domain}")

        if profile.key_skills:
            lines.append(f"\n[bold]Key Skills ({len(profile.key_skills)}):[/bold]")
            for skill in profile.key_skills:
                weight_bar = "█" * int(skill.weight * 5) + "░" * (5 - int(skill.weight * 5))
                lines.append(f"  {weight_bar} {skill.name} ({skill.category})")

        if profile.interview_intel:
            intel = profile.interview_intel
            lines.append("\n[bold]Interview Intel:[/bold]")
            if intel.format:
                lines.append(f"  Format: {' → '.join(intel.format)}")
            if intel.common_topics:
                lines.append(f"  Topics: {', '.join(intel.common_topics)}")
            if intel.gotchas:
                for g in intel.gotchas:
                    lines.append(f"  ⚠ {g}")

        panel = self.query_one("#profile-panel", Static)
        panel.update("\n".join(lines))
        panel.add_class("visible")

        buttons = self.query_one("#prep-buttons", Horizontal)
        buttons.add_class("visible")

        # Shrink JD input
        self.query_one("#jd-input", TextArea).styles.max_height = 5

        status = self.query_one("#prep-status", Static)
        status.update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-save":
                self._save_profile()
            case "btn-back":
                self.app.pop_screen()

    def _save_profile(self) -> None:
        if self._profile is None:
            return

        import json

        from mockr.core.progress.store import ProgressStore

        profile = self._profile
        db_path = Path.home() / ".mockr" / "mockr.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        store = ProgressStore(db_path)

        skills_data = [
            {"name": s.name, "category": s.category, "dimensions": s.dimensions, "weight": s.weight}
            for s in profile.key_skills
        ]

        store.save_role_profile(
            profile_id=profile.id,
            company=profile.company,
            role_title=profile.role_title,
            inferred_level=profile.inferred_level,
            tech_stack=profile.tech_stack,
            domain=profile.domain,
            key_skills=skills_data,
            interview_intel=None,
            raw_text=profile.raw_text,
        )
        store.close()

        status = self.query_one("#prep-status", Static)
        status.update(f"[bold $success]Profile saved! Run an assessment to generate a practice plan.[/bold $success]")

    def action_go_back(self) -> None:
        self.app.pop_screen()
