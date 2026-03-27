# Contributing to mockr

Thanks for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/andrewkim/mockr.git
cd mockr
python -m venv .venv
source .venv/bin/activate  # or .venv/Scripts/activate on Windows
pip install -e ".[dev,all]"
```

## Running Tests

```bash
pytest tests/ -v
```

DuckDB tests require the `duckdb` package (included in base dependencies). LLM provider tests are skipped if the optional SDK isn't installed.

## Code Style

- Type hints on all public functions and methods
- `from __future__ import annotations` at the top of every module
- Import order: stdlib > third-party > internal > relative, separated by blank lines
- Prefer early returns over deep nesting

## Making Changes

1. Fork the repo and create a branch: `feat/your-feature`, `fix/your-fix`
2. Write tests for new functionality
3. Run `pytest tests/ -v` and ensure all tests pass
4. Open a PR against `main` with a short summary and test plan

## Adding Challenges

Drop a `.toml` file in `challenges/<mode>/` following the existing format. Validate with:

```bash
mockr challenge validate your-challenge.toml
```

## Reporting Issues

Open an issue with:
- What you expected
- What happened
- Steps to reproduce
- Python version and OS
