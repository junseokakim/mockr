"""Session setup screen — configure and launch an interview."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    RadioButton,
    RadioSet,
    Static,
)

from mockr.core.challenges.loader import load_challenges_from_dir
from mockr.core.types import Level, Mode

# Default challenges directory; real CLI entry can override.
_DEFAULT_CHALLENGES_DIR = Path(__file__).parent.parent.parent / "challenges"

_MODE_OPTIONS = [
    ("System Design", Mode.SYSTEM_DESIGN),
    ("Coding", Mode.CODING),
    ("Behavioral", Mode.BEHAVIORAL),
    ("Full Loop", Mode.FULL_LOOP),
]

_LEVEL_OPTIONS = [
    ("Mid", Level.MID),
    ("Senior", Level.SENIOR),
    ("Staff", Level.STAFF),
    ("Principal", Level.PRINCIPAL),
]

_LANGUAGE_OPTIONS = [
    ("Python", "python"),
    ("SQL", "sql"),
    ("Rust", "rust"),
    ("JavaScript", "javascript"),
]


class SetupScreen(Screen):
    """Configure the interview session before starting."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("ctrl+s", "start_interview", "Start"),
    ]

    CSS = """
    SetupScreen {
        align: center middle;
    }

    #setup-container {
        width: 70;
        height: auto;
        border: round $primary;
        padding: 1 2;
    }

    #setup-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 0 0 1 0;
    }

    .section-label {
        color: $text-muted;
        text-style: bold;
        margin: 1 0 0 0;
    }

    RadioSet {
        margin: 0 0 0 2;
        height: auto;
    }

    #language-section {
        display: none;
    }

    #language-section.visible {
        display: block;
    }

    #challenge-list {
        height: 8;
        border: round $surface-lighten-1;
        margin: 0 0 0 2;
    }

    #setup-buttons {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin: 2 0 0 0;
    }

    #setup-buttons Button {
        margin: 0 1;
    }

    #status-label {
        text-align: center;
        color: $text-muted;
        height: 1;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, practice_mode: bool = False) -> None:
        super().__init__()
        self._practice_mode = practice_mode
        self._selected_mode = Mode.SYSTEM_DESIGN
        self._selected_level = Level.SENIOR
        self._selected_language = "python"
        self._selected_challenge: str | None = None
        self._challenges: list = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="setup-container"):
            yield Static("Configure Interview Session", id="setup-title")

            yield Label("Mode", classes="section-label")
            with RadioSet(id="mode-select"):
                for label, value in _MODE_OPTIONS:
                    yield RadioButton(label, value=(value == Mode.SYSTEM_DESIGN))

            yield Label("Level", classes="section-label")
            with RadioSet(id="level-select"):
                for label, value in _LEVEL_OPTIONS:
                    yield RadioButton(label, value=(value == Level.SENIOR))

            with Vertical(id="language-section"):
                yield Label("Language", classes="section-label")
                with RadioSet(id="language-select"):
                    for label, value in _LANGUAGE_OPTIONS:
                        yield RadioButton(label, value=(value == "python"))

            yield Label("Challenge  (↑↓ to select, first entry = random)", classes="section-label")
            yield ListView(
                ListItem(Label("  Random"), id="challenge-random"),
                id="challenge-list",
            )

            with Horizontal(id="setup-buttons"):
                yield Button("Start Interview  [Ctrl+S]", id="btn-start", variant="primary")
                yield Button("Back  [Esc]", id="btn-back", variant="default")

            yield Static("", id="status-label")

        yield Footer()

    def on_mount(self) -> None:
        self._load_challenges()
        if self._practice_mode:
            self.query_one("#status-label", Static).update("Practice mode — showing due-review challenges first")

    def _load_challenges(self) -> None:
        challenge_list = self.query_one("#challenge-list", ListView)
        if _DEFAULT_CHALLENGES_DIR.exists():
            try:
                self._challenges = load_challenges_from_dir(_DEFAULT_CHALLENGES_DIR)
            except Exception:
                self._challenges = []
        for challenge in self._challenges:
            item = ListItem(
                Label(f"  {challenge.title}  [{challenge.mode}]"),
                id=f"challenge-{challenge.id}",
            )
            challenge_list.append(item)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        radio_set = event.radio_set
        idx = event.index

        if radio_set.id == "mode-select":
            self._selected_mode = _MODE_OPTIONS[idx][1]
            lang_section = self.query_one("#language-section", Vertical)
            if self._selected_mode == Mode.CODING:
                lang_section.add_class("visible")
            else:
                lang_section.remove_class("visible")

        elif radio_set.id == "level-select":
            self._selected_level = _LEVEL_OPTIONS[idx][1]

        elif radio_set.id == "language-select":
            self._selected_language = _LANGUAGE_OPTIONS[idx][1]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == "challenge-random":
            self._selected_challenge = None
        else:
            challenge_id = item_id.removeprefix("challenge-")
            self._selected_challenge = challenge_id

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-start":
                self.action_start_interview()
            case "btn-back":
                self.action_go_back()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_start_interview(self) -> None:
        """Validate, create session, push the correct interview screen."""
        from mockr.core.events import EventBus
        from mockr.core.sessions.session import Session

        status = self.query_one("#status-label", Static)

        mode = self._selected_mode
        level = self._selected_level

        # Resolve challenge
        challenge = None
        if self._selected_challenge and self._challenges:
            matches = [c for c in self._challenges if c.id == self._selected_challenge]
            challenge = matches[0] if matches else None

        if challenge is None and self._challenges:
            # Pick a random one matching the mode if available
            import random

            mode_challenges = [c for c in self._challenges if c.mode == self._selected_mode.value]
            if mode_challenges:
                challenge = random.choice(mode_challenges)
            elif self._challenges:
                challenge = random.choice(self._challenges)

        bus = EventBus()
        session = Session(bus=bus, mode=mode, level=level)

        if challenge:
            level_cfg = challenge.levels.get(level.value)
            timer = level_cfg.estimated_minutes if level_cfg else 20
            session.setup(challenge_id=challenge.id, timer_minutes=timer)
        else:
            session.setup(challenge_id="demo", timer_minutes=20)

        session.start()

        status.update("Starting interview…")
        self._push_interview_screen(session, challenge, bus)

    def _push_interview_screen(self, session, challenge, bus) -> None:
        mode = session.mode

        if mode == Mode.CODING:
            from mockr.tui.screens.interview_coding import CodingInterviewScreen

            self.app.push_screen(
                CodingInterviewScreen(
                    session=session,
                    challenge=challenge,
                    bus=bus,
                    language=self._selected_language,
                )
            )
        elif mode == Mode.BEHAVIORAL:
            from mockr.tui.screens.interview_behavioral import BehavioralInterviewScreen

            self.app.push_screen(
                BehavioralInterviewScreen(
                    session=session,
                    challenge=challenge,
                    bus=bus,
                )
            )
        else:
            # system-design or full-loop defaults to sysdesign screen
            from mockr.tui.screens.interview_sysdesign import SysDesignInterviewScreen

            self.app.push_screen(
                SysDesignInterviewScreen(
                    session=session,
                    challenge=challenge,
                    bus=bus,
                )
            )
