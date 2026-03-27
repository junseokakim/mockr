"""Assessment screen — diagnostic interview across 3 modes."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, TextArea

_MODES = ["coding", "system-design", "behavioral"]
_CHALLENGES_DIR = Path(__file__).parent.parent.parent / "challenges" / "diagnostic"


class AssessmentScreen(Screen):
    """Diagnostic assessment — 3 mini-interviews to baseline skill level."""

    BINDINGS = [
        Binding("ctrl+enter", "submit_answer", "Submit"),
        Binding("escape", "go_back", "Back"),
    ]

    CSS = """
    AssessmentScreen {
        layout: vertical;
    }

    #assess-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        height: 3;
        content-align: center middle;
        background: $surface-darken-1;
    }

    #assess-body {
        height: 1fr;
        margin: 1 2;
    }

    #progress-bar {
        text-align: center;
        color: $accent;
        text-style: bold;
        height: 1;
        margin: 0 0 1 0;
    }

    #question-panel {
        border: round $primary;
        height: auto;
        max-height: 12;
        padding: 1;
        margin: 0 0 1 0;
        overflow-y: auto;
    }

    #answer-area {
        height: 1fr;
        min-height: 8;
    }

    #assess-status {
        text-align: center;
        color: $text-muted;
        height: 1;
        margin: 1 0 0 0;
    }

    #results-panel {
        border: round $accent;
        padding: 1 2;
        margin: 1 0;
        height: auto;
        max-height: 20;
        overflow-y: auto;
        display: none;
    }

    #results-panel.visible {
        display: block;
    }

    #result-buttons {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin: 1 0 0 0;
        display: none;
    }

    #result-buttons.visible {
        display: block;
    }

    #result-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, target_level: str = "senior") -> None:
        super().__init__()
        self._target_level = target_level
        self._current_mode_idx = 0
        self._current_question = ""
        self._assessment_result = None
        self._answers: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Diagnostic Assessment — Target: {self._target_level}", id="assess-title")
        with Vertical(id="assess-body"):
            yield Static("", id="progress-bar")
            yield Static("Loading question...", id="question-panel")
            yield TextArea(id="answer-area")
            yield Static("Press Ctrl+Enter to submit your answer", id="assess-status")
            yield Static("", id="results-panel")
            with Horizontal(id="result-buttons"):
                yield Button("Generate Plan", id="btn-plan", variant="primary")
                yield Button("Home", id="btn-home", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self._update_progress()
        self.run_worker(self._start_mode())

    def _update_progress(self) -> None:
        idx = self._current_mode_idx
        progress = self.query_one("#progress-bar", Static)
        dots = " ".join(
            f"[bold $accent]{_MODES[i].upper()}[/]" if i == idx
            else f"[dim]{_MODES[i]}[/]"
            for i in range(len(_MODES))
        )
        progress.update(f"Mode {idx + 1}/{len(_MODES)}: {dots}")

    async def _start_mode(self) -> None:
        from mockr.core.challenges.loader import load_challenges_from_dir
        from mockr.core.llm.fake_backend import FakeLLMBackend
        from mockr.core.types import Message, ModelConfig

        if self._current_mode_idx >= len(_MODES):
            return

        mode = _MODES[self._current_mode_idx]
        status = self.query_one("#assess-status", Static)
        status.update(f"Starting {mode} assessment...")

        backend = FakeLLMBackend()
        config = ModelConfig(model="fake", temperature=0.7, max_tokens=1024)

        challenges = load_challenges_from_dir(_CHALLENGES_DIR)
        challenge = next((c for c in challenges if c.mode == mode), None)

        if challenge is None:
            status.update(f"No diagnostic challenge found for {mode}")
            return

        level_config = challenge.levels.get(self._target_level)
        if level_config is None:
            available = list(challenge.levels.keys())
            level_config = challenge.levels[available[0]] if available else None

        if level_config is None:
            status.update(f"No level config for {self._target_level}")
            return

        messages = [
            Message(role="system", content=level_config.interviewer),
            Message(role="user", content="Start the interview with the first question."),
        ]
        question = await backend.generate(messages, config)
        self._current_question = question

        question_panel = self.query_one("#question-panel", Static)
        question_panel.update(f"[bold]{mode.upper()}[/bold]\n\n{question}")

        answer_area = self.query_one("#answer-area", TextArea)
        answer_area.clear()
        answer_area.focus()

        status.update("Press Ctrl+Enter to submit your answer")

    def action_submit_answer(self) -> None:
        answer_area = self.query_one("#answer-area", TextArea)
        answer = answer_area.text.strip()

        if not answer:
            status = self.query_one("#assess-status", Static)
            status.update("[red]Please type an answer before submitting[/red]")
            return

        mode = _MODES[self._current_mode_idx]
        self._answers[mode] = answer
        self._current_mode_idx += 1

        if self._current_mode_idx < len(_MODES):
            self._update_progress()
            self.run_worker(self._start_mode())
        else:
            self.run_worker(self._run_assessment())

    async def _run_assessment(self) -> None:
        from mockr.core.assessment.engine import AssessmentEngine
        from mockr.core.llm.fake_backend import FakeLLMBackend
        from mockr.core.types import ModelConfig

        status = self.query_one("#assess-status", Static)
        status.update("Scoring all responses...")

        backend = FakeLLMBackend()
        config = ModelConfig(model="fake", temperature=0.7, max_tokens=1024)

        engine = AssessmentEngine(
            backend=backend,
            config=config,
            challenges_dir=_CHALLENGES_DIR,
        )

        async def answer_callback(question: str, mode: str) -> str:
            return self._answers.get(mode, "No answer provided.")

        result = await engine.run_diagnostic(
            target_level=self._target_level,
            answer_callback=answer_callback,
        )
        self._assessment_result = result
        self._show_results(result)

    def _show_results(self, result) -> None:
        lines = [
            "[bold]Assessment Complete[/bold]\n",
            f"Target Level: [accent]{result.target_level}[/accent]",
            f"Inferred Level: [accent]{result.inferred_level}[/accent]\n",
        ]

        for mode, scores in result.mode_scores.items():
            lines.append(f"[bold]{mode.upper()}[/bold]")
            for dim, score in scores.items():
                bar_filled = int(score * 2)
                bar_empty = 10 - bar_filled
                color = "$success" if score >= 3.5 else ("$warning" if score >= 2.5 else "$error")
                lines.append(f"  {dim:20s} [{color}]{'█' * bar_filled}{'░' * bar_empty}[/] {score:.1f}")
            lines.append("")

        if result.gaps:
            lines.append(f"[bold]Gaps ({len(result.gaps)} dimensions below target):[/bold]")
            for gap in sorted(result.gaps, key=lambda g: g.gap_size, reverse=True)[:8]:
                lines.append(f"  {gap.mode}/{gap.dimension}: {gap.current_score:.1f} → needs {gap.target_score}")
        else:
            lines.append("[bold $success]No gaps — you meet all thresholds![/bold $success]")

        results_panel = self.query_one("#results-panel", Static)
        results_panel.update("\n".join(lines))
        results_panel.add_class("visible")

        result_buttons = self.query_one("#result-buttons", Horizontal)
        result_buttons.add_class("visible")

        self.query_one("#answer-area", TextArea).display = False
        self.query_one("#question-panel", Static).display = False

        status = self.query_one("#assess-status", Static)
        status.update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-plan":
                self._generate_plan()
            case "btn-home":
                self.app.pop_screen()

    def _generate_plan(self) -> None:
        if self._assessment_result is None:
            return

        from mockr.core.planning.generator import PlanGenerator
        from mockr.core.progress.store import ProgressStore

        result = self._assessment_result

        db_path = Path.home() / ".mockr" / "mockr.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        store = ProgressStore(db_path)
        store.save_assessment(result.id, result.target_level, result.inferred_level, result.mode_scores)

        challenges_dir = Path(__file__).parent.parent.parent / "challenges"
        generator = PlanGenerator(challenges_dir=challenges_dir)
        plan = generator.generate(result)

        store.save_practice_plan(plan.id, result.id, None, plan.target_level)
        for i, item in enumerate(plan.items):
            store.save_plan_item(
                f"item-{plan.id[:8]}-{i}",
                plan.id, item.dimension, item.mode,
                item.priority, item.gap_size, item.challenge_id, item.rationale,
            )
        store.close()

        status = self.query_one("#assess-status", Static)
        status.update(
            f"[bold $success]Plan generated with {len(plan.items)} practice items! View in Dashboard.[/bold $success]"
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()
