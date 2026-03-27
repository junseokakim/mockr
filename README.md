# mockr

[![CI](https://github.com/junseokakim/mockr/actions/workflows/ci.yml/badge.svg)](https://github.com/junseokakim/mockr/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Terminal-native AI mock interview tool with real code execution, system design diagramming, and spaced repetition.

```
pip install -e .
mockr
```

## Why mockr?

Most interview prep tools are browser-based tutorial clones. mockr is built for engineers who live in the terminal:

- **Real code execution** — Python, SQL (DuckDB), Rust, JavaScript. Your code actually runs.
- **System design with diagramming** — Type `client -> api -> cache -> db` and get live ASCII diagrams + Mermaid export.
- **Adaptive difficulty** — SM-2 spaced repetition tracks your weaknesses and surfaces what you need to practice.
- **Any LLM** — Ollama (local), OpenAI, Anthropic, or use your existing Claude/Codex CLI login (zero API keys needed).
- **Role-anchored levels** — Mid, Senior, Staff, Principal. The interviewer adjusts expectations per level.

## Interview Modes

| Mode | What it does |
|------|-------------|
| `system-design` | Timed design round with shorthand diagramming, tradeoff probing |
| `coding` | Problem + code editor + test execution + follow-ups |
| `behavioral` | STAR-method coaching with real-time narrative feedback |
| `full-loop` | Chains all three: behavioral -> coding -> system-design |

## Architecture

```
mockr/
├── core/           # Library — no TUI dependency
│   ├── llm/        # 5 pluggable LLM providers
│   ├── sessions/   # State machine + turn orchestrator
│   ├── scoring/    # LLM-based evaluation (5 dimensions per mode)
│   ├── execution/  # Code runners (subprocess + DuckDB)
│   ├── diagrams/   # DSL parser + ASCII/Mermaid renderers
│   ├── challenges/ # TOML challenge bank loader
│   ├── progress/   # SQLite + SM-2 spaced repetition
│   └── events.py   # Event bus (core <-> TUI contract)
├── tui/            # Textual TUI (subscribes to core events)
│   ├── screens/    # Home, Setup, Interview (3 modes), Dashboard, Debrief
│   └── widgets/    # Timer, DiagramViewer, CodeEditor, ScorePanel, STARTracker
└── cli.py          # Click entry point
```

The core is event-driven and decoupled from the TUI. You can use it as a library:

```python
from mockr.core.sessions.session import Session
from mockr.core.sessions.orchestrator import TurnOrchestrator
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/junseokakim/mockr.git
cd mockr
python -m venv .venv && source .venv/bin/activate  # or .venv/Scripts/activate on Windows
pip install -e ".[dev]"

# Launch the TUI
mockr

# Or go direct to a session
mockr --mode coding --lang sql --level senior

# Practice due reviews (spaced repetition)
mockr practice

# View your progress
mockr dashboard

# Export data
mockr export --format json --output progress.json
```

## LLM Providers

Configure in `~/.mockr/config.toml`:

```toml
[llm]
provider = "claude-cli"   # zero setup if you have Claude Code installed

# Or use Ollama for fully local, private practice:
# provider = "ollama"

# Or API keys:
# provider = "openai"
# [llm.openai]
# api_key = "sk-..."
```

| Provider | Auth | Streaming |
|----------|------|-----------|
| `ollama` | None (local) | Yes |
| `openai` | API key | Yes |
| `anthropic` | API key | Yes |
| `claude-cli` | Claude Code OAuth | No (batch) |
| `codex-cli` | Codex OAuth | No (batch) |

## Diagram DSL

During system design interviews, type shorthand:

```
client -> api -> cache -> db
api -> queue -> worker -> db
cache [Redis, TTL=5m]
queue [Kafka, 3 partitions]
```

mockr renders this as live ASCII art in the terminal and saves Mermaid syntax for later.

## Challenge Bank

8 built-in challenges. Add your own by dropping a `.toml` file in `~/.mockr/challenges/`:

```toml
[meta]
id = "my-challenge"
title = "My Custom Challenge"
mode = "system-design"
tags = ["distributed-systems"]

[levels.senior]
estimated_minutes = 20
interviewer = "Design a distributed message queue."
must_cover = ["ordering", "durability", "consumer groups"]
follow_ups = ["What happens when a broker goes down?"]
```

Validate with: `mockr challenge validate my-challenge.toml`

## Tests

```bash
pytest tests/ -v
```

## Tech Stack

Python 3.11+ | Textual | DuckDB | SQLite | httpx | Click | asyncio

## License

MIT
