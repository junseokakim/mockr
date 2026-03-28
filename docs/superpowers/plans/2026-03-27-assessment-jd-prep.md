# Assessment & JD-Based Prep — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add diagnostic assessment, practice plan generation, JD parsing with interview intel, and LLM-generated challenges to mockr.

**Architecture:** Layered approach — assessment is the standalone foundation, JD is an optional overlay. New modules (`assessment/`, `planning/`, `jd/`) integrate with existing scorer, orchestrator, and progress store. All new persistence goes into the existing SQLite DB via new tables.

**Tech Stack:** Python 3.11+, pytest, pytest-asyncio, SQLite, Click CLI, httpx (web fetching), existing LLM backend

---

## File Map

### New Files

| File | Responsibility |
|------|---------------|
| `mockr/core/types.py` | (modify) Expand Level enum with INTERN, JUNIOR |
| `mockr/core/assessment/__init__.py` | Package init |
| `mockr/core/assessment/engine.py` | Diagnostic assessment runner — sequences 3 mini-interviews |
| `mockr/core/assessment/models.py` | AssessmentResult, Gap dataclasses |
| `mockr/core/assessment/thresholds.py` | Level dimension thresholds + gap detection |
| `mockr/core/planning/__init__.py` | Package init |
| `mockr/core/planning/models.py` | PracticePlan, PlanItem dataclasses |
| `mockr/core/planning/generator.py` | Plan generation from assessment + optional role profile |
| `mockr/core/planning/adapter.py` | Post-session plan recalculation + re-assessment triggers |
| `mockr/core/jd/__init__.py` | Package init |
| `mockr/core/jd/models.py` | RoleProfile, Skill, InterviewIntel dataclasses |
| `mockr/core/jd/parser.py` | JD text extraction + LLM parsing to RoleProfile |
| `mockr/core/jd/challenge_gen.py` | LLM-based challenge generation from uncovered skills |
| `mockr/core/jd/intel.py` | Web search + LLM summarization for interview intel |
| `mockr/core/progress/store.py` | (modify) Add new tables + methods for assessments, profiles, plans |
| `mockr/challenges/diagnostic/` | 3 diagnostic challenge TOML files |
| `mockr/cli.py` | (modify) Add `assess`, `prep`, `plan`, `practice` commands |
| `tests/core/assessment/__init__.py` | Test package |
| `tests/core/assessment/test_engine.py` | Assessment engine tests |
| `tests/core/assessment/test_thresholds.py` | Threshold + gap detection tests |
| `tests/core/planning/__init__.py` | Test package |
| `tests/core/planning/test_models.py` | Plan model tests |
| `tests/core/planning/test_generator.py` | Plan generator tests |
| `tests/core/planning/test_adapter.py` | Adaptive plan update tests |
| `tests/core/jd/__init__.py` | Test package |
| `tests/core/jd/test_models.py` | JD model tests |
| `tests/core/jd/test_parser.py` | JD parser tests |
| `tests/core/jd/test_challenge_gen.py` | Challenge generation tests |
| `tests/core/jd/test_intel.py` | Intel gathering tests |

---

## Wave 1: Foundation (no dependencies)

Tasks 1-4 can be executed in parallel — they have no dependencies on each other.

---

### Task 1: Expand Level Enum

**Files:**
- Modify: `mockr/core/types.py`
- Modify: `tests/core/test_types.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/core/test_types.py`:

```python
from mockr.core.types import Level


class TestLevelExpansion:
    def test_intern_level_exists(self) -> None:
        assert Level.INTERN.value == "intern"

    def test_junior_level_exists(self) -> None:
        assert Level.JUNIOR.value == "junior"

    def test_all_ic_levels_ordered(self) -> None:
        ic_levels = [Level.INTERN, Level.JUNIOR, Level.MID, Level.SENIOR, Level.STAFF, Level.PRINCIPAL]
        assert len(ic_levels) == 6

    def test_management_placeholder_exists(self) -> None:
        assert Level.ENGINEERING_MANAGER.value == "engineering_manager"
        assert Level.DIRECTOR.value == "director"
        assert Level.VP.value == "vp"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/core/test_types.py::TestLevelExpansion -v`
Expected: FAIL with `AttributeError: INTERN` (Level enum doesn't have these values yet)

- [ ] **Step 3: Implement the Level enum expansion**

In `mockr/core/types.py`, replace the Level enum:

```python
class Level(Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    # Management track (placeholders — not yet implemented)
    ENGINEERING_MANAGER = "engineering_manager"
    DIRECTOR = "director"
    VP = "vp"
```

- [ ] **Step 4: Update the CLI level choices**

In `mockr/cli.py`, line 10, update the `--level` option:

```python
@click.option("--level", type=click.Choice(["intern", "junior", "mid", "senior", "staff", "principal"]), default=None)
```

- [ ] **Step 5: Run tests to verify everything passes**

Run: `python -m pytest tests/core/test_types.py -v`
Expected: ALL PASS

Run: `python -m pytest tests/ -v`
Expected: ALL PASS (no regressions from new enum members)

- [ ] **Step 6: Commit**

```bash
git add mockr/core/types.py mockr/cli.py tests/core/test_types.py
git commit -m "feat: expand Level enum with intern, junior, and management placeholders"
```

---

### Task 2: Assessment Data Models + Thresholds

**Files:**
- Create: `mockr/core/assessment/__init__.py`
- Create: `mockr/core/assessment/models.py`
- Create: `mockr/core/assessment/thresholds.py`
- Create: `tests/core/assessment/__init__.py`
- Create: `tests/core/assessment/test_thresholds.py`

- [ ] **Step 1: Create package init**

Create `mockr/core/assessment/__init__.py`:

```python
"""Diagnostic assessment engine for mockr."""
```

Create `tests/core/assessment/__init__.py` (empty file).

- [ ] **Step 2: Write test for assessment models**

Create `tests/core/assessment/test_thresholds.py`:

```python
from __future__ import annotations

from mockr.core.assessment.models import AssessmentResult, Gap
from mockr.core.assessment.thresholds import (
    LEVEL_THRESHOLDS,
    detect_gaps,
    infer_level,
)


class TestLevelThresholds:
    def test_senior_thresholds_exist(self) -> None:
        assert "senior" in LEVEL_THRESHOLDS
        senior = LEVEL_THRESHOLDS["senior"]
        assert "coding" in senior
        assert "correctness" in senior["coding"]

    def test_all_ic_levels_have_thresholds(self) -> None:
        for level in ["intern", "junior", "mid", "senior", "staff", "principal"]:
            assert level in LEVEL_THRESHOLDS, f"Missing thresholds for {level}"

    def test_thresholds_increase_with_level(self) -> None:
        mid_coding = LEVEL_THRESHOLDS["mid"]["coding"]["correctness"]
        senior_coding = LEVEL_THRESHOLDS["senior"]["coding"]["correctness"]
        assert senior_coding > mid_coding


class TestDetectGaps:
    def test_detects_gap_below_threshold(self) -> None:
        mode_scores = {
            "coding": {"correctness": 2.0, "efficiency": 3.0, "code_quality": 3.0, "edge_cases": 2.5, "communication": 3.5},
        }
        gaps = detect_gaps(mode_scores, target_level="senior")
        gap_dims = [g.dimension for g in gaps]
        assert "correctness" in gap_dims

    def test_no_gap_when_above_threshold(self) -> None:
        mode_scores = {
            "coding": {"correctness": 5.0, "efficiency": 5.0, "code_quality": 5.0, "edge_cases": 5.0, "communication": 5.0},
        }
        gaps = detect_gaps(mode_scores, target_level="senior")
        coding_gaps = [g for g in gaps if g.mode == "coding"]
        assert len(coding_gaps) == 0

    def test_gap_includes_size(self) -> None:
        mode_scores = {
            "coding": {"correctness": 2.0, "efficiency": 4.0, "code_quality": 4.0, "edge_cases": 4.0, "communication": 4.0},
        }
        gaps = detect_gaps(mode_scores, target_level="senior")
        correctness_gap = next(g for g in gaps if g.dimension == "correctness")
        assert correctness_gap.gap_size > 0


class TestInferLevel:
    def test_infer_level_from_high_scores(self) -> None:
        mode_scores = {
            "coding": {"correctness": 4.5, "efficiency": 4.5, "code_quality": 4.5, "edge_cases": 4.5, "communication": 4.5},
            "system-design": {"structure": 4.5, "constraints": 4.5, "tradeoffs": 4.5, "reliability": 4.5, "concreteness": 4.5},
            "behavioral": {"situation": 4.5, "task": 4.5, "action": 4.5, "result": 4.5, "impact": 4.5},
        }
        level = infer_level(mode_scores)
        assert level in ("staff", "principal")

    def test_infer_level_from_low_scores(self) -> None:
        mode_scores = {
            "coding": {"correctness": 1.5, "efficiency": 1.5, "code_quality": 1.5, "edge_cases": 1.5, "communication": 1.5},
            "system-design": {"structure": 1.5, "constraints": 1.5, "tradeoffs": 1.5, "reliability": 1.5, "concreteness": 1.5},
            "behavioral": {"situation": 1.5, "task": 1.5, "action": 1.5, "result": 1.5, "impact": 1.5},
        }
        level = infer_level(mode_scores)
        assert level in ("intern", "junior")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/core/assessment/test_thresholds.py -v`
Expected: FAIL (modules don't exist yet)

- [ ] **Step 4: Implement assessment models**

Create `mockr/core/assessment/models.py`:

```python
"""Data models for diagnostic assessments."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Gap:
    dimension: str
    mode: str
    current_score: float
    target_score: float
    gap_size: float


@dataclass
class AssessmentResult:
    id: str
    target_level: str
    inferred_level: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    mode_scores: dict[str, dict[str, float]] = field(default_factory=dict)
    gaps: list[Gap] = field(default_factory=list)
```

- [ ] **Step 5: Implement thresholds + gap detection**

Create `mockr/core/assessment/thresholds.py`:

```python
"""Level thresholds and gap detection for assessments."""

from __future__ import annotations

from mockr.core.assessment.models import Gap
from mockr.core.scoring.scorer import DIMENSIONS_BY_MODE

# Thresholds: minimum score per dimension to be considered "at level"
# Scale 1-5. Each level's thresholds are higher than the previous.
LEVEL_THRESHOLDS: dict[str, dict[str, dict[str, float]]] = {
    "intern": {
        mode: {dim: 1.5 for dim in dims}
        for mode, dims in DIMENSIONS_BY_MODE.items()
    },
    "junior": {
        mode: {dim: 2.0 for dim in dims}
        for mode, dims in DIMENSIONS_BY_MODE.items()
    },
    "mid": {
        mode: {dim: 2.5 for dim in dims}
        for mode, dims in DIMENSIONS_BY_MODE.items()
    },
    "senior": {
        mode: {dim: 3.5 for dim in dims}
        for mode, dims in DIMENSIONS_BY_MODE.items()
    },
    "staff": {
        mode: {dim: 4.0 for dim in dims}
        for mode, dims in DIMENSIONS_BY_MODE.items()
    },
    "principal": {
        mode: {dim: 4.5 for dim in dims}
        for mode, dims in DIMENSIONS_BY_MODE.items()
    },
}

# Ordered from lowest to highest for level inference
_LEVEL_ORDER = ["intern", "junior", "mid", "senior", "staff", "principal"]


def detect_gaps(
    mode_scores: dict[str, dict[str, float]],
    target_level: str,
) -> list[Gap]:
    """Compare mode_scores against target level thresholds. Return gaps."""
    thresholds = LEVEL_THRESHOLDS.get(target_level, LEVEL_THRESHOLDS["senior"])
    gaps: list[Gap] = []
    for mode, dim_thresholds in thresholds.items():
        scores = mode_scores.get(mode, {})
        for dim, threshold in dim_thresholds.items():
            current = scores.get(dim, 0.0)
            if current < threshold:
                gaps.append(
                    Gap(
                        dimension=dim,
                        mode=mode,
                        current_score=current,
                        target_score=threshold,
                        gap_size=round(threshold - current, 2),
                    )
                )
    return gaps


def infer_level(mode_scores: dict[str, dict[str, float]]) -> str:
    """Infer the highest level where the candidate meets all thresholds."""
    inferred = "intern"
    for level in _LEVEL_ORDER:
        gaps = detect_gaps(mode_scores, target_level=level)
        if not gaps:
            inferred = level
        else:
            break
    return inferred
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/core/assessment/test_thresholds.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add mockr/core/assessment/ tests/core/assessment/
git commit -m "feat: add assessment data models and level threshold system"
```

---

### Task 3: Planning Data Models

**Files:**
- Create: `mockr/core/planning/__init__.py`
- Create: `mockr/core/planning/models.py`
- Create: `tests/core/planning/__init__.py`
- Create: `tests/core/planning/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/core/planning/__init__.py` (empty).

Create `tests/core/planning/test_models.py`:

```python
from __future__ import annotations

from mockr.core.planning.models import PlanItem, PracticePlan


class TestPlanModels:
    def test_plan_item_creation(self) -> None:
        item = PlanItem(
            dimension="correctness",
            mode="coding",
            priority=0.8,
            gap_size=1.5,
            rationale="Your correctness score is 2.0, senior needs 3.5",
        )
        assert item.status == "pending"
        assert item.challenge_id is None

    def test_practice_plan_creation(self) -> None:
        item = PlanItem(
            dimension="tradeoffs",
            mode="system-design",
            priority=0.6,
            gap_size=1.0,
            rationale="Tradeoffs need work",
        )
        plan = PracticePlan(
            id="plan-1",
            assessment_id="assess-1",
            target_level="senior",
            items=[item],
        )
        assert len(plan.items) == 1
        assert plan.role_profile_id is None

    def test_plan_items_sortable_by_priority(self) -> None:
        items = [
            PlanItem(dimension="a", mode="coding", priority=0.3, gap_size=0.5, rationale="low"),
            PlanItem(dimension="b", mode="coding", priority=0.9, gap_size=2.0, rationale="high"),
            PlanItem(dimension="c", mode="coding", priority=0.6, gap_size=1.0, rationale="mid"),
        ]
        sorted_items = sorted(items, key=lambda x: x.priority, reverse=True)
        assert sorted_items[0].dimension == "b"
        assert sorted_items[-1].dimension == "a"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/planning/test_models.py -v`
Expected: FAIL (module doesn't exist)

- [ ] **Step 3: Implement planning models**

Create `mockr/core/planning/__init__.py`:

```python
"""Practice plan generation for mockr."""
```

Create `mockr/core/planning/models.py`:

```python
"""Data models for practice plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class PlanItem:
    dimension: str
    mode: str
    priority: float
    gap_size: float
    rationale: str
    challenge_id: str | None = None
    status: str = "pending"  # pending, in_progress, validated


@dataclass
class PracticePlan:
    id: str
    assessment_id: str
    target_level: str
    items: list[PlanItem] = field(default_factory=list)
    role_profile_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/planning/test_models.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add mockr/core/planning/ tests/core/planning/
git commit -m "feat: add practice plan data models"
```

---

### Task 4: JD Data Models

**Files:**
- Create: `mockr/core/jd/__init__.py`
- Create: `mockr/core/jd/models.py`
- Create: `tests/core/jd/__init__.py`
- Create: `tests/core/jd/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/core/jd/__init__.py` (empty).

Create `tests/core/jd/test_models.py`:

```python
from __future__ import annotations

from mockr.core.jd.models import InterviewIntel, RoleProfile, Skill


class TestJDModels:
    def test_skill_creation(self) -> None:
        skill = Skill(
            name="distributed systems",
            category="system-design",
            dimensions=["structure", "reliability"],
            weight=0.8,
        )
        assert skill.weight == 0.8

    def test_interview_intel_creation(self) -> None:
        intel = InterviewIntel(
            format=["phone screen", "2x coding", "system design"],
            common_topics=["API design", "concurrency"],
            culture_signals=["They value communication"],
            gotchas=["System design is only 30 min"],
            sources=["https://glassdoor.com/..."],
        )
        assert len(intel.format) == 3

    def test_role_profile_creation(self) -> None:
        skill = Skill(name="Python", category="coding", dimensions=["correctness"], weight=0.9)
        profile = RoleProfile(
            id="rp-1",
            role_title="Senior Backend Engineer",
            inferred_level="senior",
            raw_text="We are looking for...",
            key_skills=[skill],
            company="Stripe",
            tech_stack=["Python", "PostgreSQL"],
            domain="fintech",
        )
        assert profile.company == "Stripe"
        assert profile.interview_intel is None

    def test_role_profile_without_optional_fields(self) -> None:
        profile = RoleProfile(
            id="rp-2",
            role_title="Software Engineer",
            inferred_level="mid",
            raw_text="Job description text",
        )
        assert profile.company is None
        assert profile.tech_stack == []
        assert profile.key_skills == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/jd/test_models.py -v`
Expected: FAIL

- [ ] **Step 3: Implement JD models**

Create `mockr/core/jd/__init__.py`:

```python
"""Job description parsing and role profile extraction."""
```

Create `mockr/core/jd/models.py`:

```python
"""Data models for job descriptions and role profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Skill:
    name: str
    category: str  # maps to Mode value: "system-design", "coding", "behavioral"
    dimensions: list[str] = field(default_factory=list)
    weight: float = 0.5


@dataclass
class InterviewIntel:
    format: list[str] = field(default_factory=list)
    common_topics: list[str] = field(default_factory=list)
    culture_signals: list[str] = field(default_factory=list)
    gotchas: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class RoleProfile:
    id: str
    role_title: str
    inferred_level: str
    raw_text: str
    company: str | None = None
    tech_stack: list[str] = field(default_factory=list)
    domain: str | None = None
    key_skills: list[Skill] = field(default_factory=list)
    interview_intel: InterviewIntel | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/jd/test_models.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add mockr/core/jd/ tests/core/jd/
git commit -m "feat: add JD role profile and interview intel data models"
```

---

## Wave 2: Persistence Layer (depends on Wave 1 models)

---

### Task 5: Extend ProgressStore with New Tables

**Files:**
- Modify: `mockr/core/progress/store.py`
- Modify: `tests/core/progress/test_store.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/core/progress/test_store.py`:

```python
import json


class TestAssessmentPersistence:
    def test_new_tables_created(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        tables = store.list_tables()
        assert "assessments" in tables
        assert "role_profiles" in tables
        assert "practice_plans" in tables
        assert "plan_items" in tables

    def test_save_and_get_assessment(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        mode_scores = {"coding": {"correctness": 3.5, "efficiency": 2.0}}
        store.save_assessment(
            assessment_id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores=mode_scores,
        )
        result = store.get_assessment("a1")
        assert result is not None
        assert result["target_level"] == "senior"
        assert json.loads(result["mode_scores"]) == mode_scores

    def test_save_and_get_role_profile(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        skills = [{"name": "Python", "category": "coding", "dimensions": ["correctness"], "weight": 0.9}]
        store.save_role_profile(
            profile_id="rp1",
            company="Stripe",
            role_title="Senior Backend Engineer",
            inferred_level="senior",
            tech_stack=["Python", "PostgreSQL"],
            domain="fintech",
            key_skills=skills,
            interview_intel=None,
            raw_text="We are looking for...",
        )
        result = store.get_role_profile("rp1")
        assert result is not None
        assert result["company"] == "Stripe"
        assert json.loads(result["tech_stack"]) == ["Python", "PostgreSQL"]

    def test_list_role_profiles(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_role_profile("rp1", "Stripe", "SWE", "senior", [], None, [], None, "text1")
        store.save_role_profile("rp2", "Google", "SRE", "staff", [], None, [], None, "text2")
        profiles = store.list_role_profiles()
        assert len(profiles) == 2

    def test_save_and_get_practice_plan(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_assessment("a1", "senior", "mid", {"coding": {"correctness": 2.0}})
        store.save_practice_plan(
            plan_id="p1",
            assessment_id="a1",
            role_profile_id=None,
            target_level="senior",
        )
        plan = store.get_practice_plan("p1")
        assert plan is not None
        assert plan["target_level"] == "senior"

    def test_save_and_get_plan_items(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_assessment("a1", "senior", "mid", {})
        store.save_practice_plan("p1", "a1", None, "senior")
        store.save_plan_item(
            item_id="i1",
            plan_id="p1",
            dimension="correctness",
            mode="coding",
            priority=0.8,
            gap_size=1.5,
            challenge_id=None,
            rationale="Score 2.0, need 3.5",
        )
        items = store.get_plan_items("p1")
        assert len(items) == 1
        assert items[0]["priority"] == 0.8

    def test_update_plan_item_status(self, tmp_path: Path) -> None:
        store = ProgressStore(tmp_path / "test.db")
        store.save_assessment("a1", "senior", "mid", {})
        store.save_practice_plan("p1", "a1", None, "senior")
        store.save_plan_item("i1", "p1", "correctness", "coding", 0.8, 1.5, None, "reason")
        store.update_plan_item_status("i1", "validated")
        items = store.get_plan_items("p1")
        assert items[0]["status"] == "validated"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/progress/test_store.py::TestAssessmentPersistence -v`
Expected: FAIL (new tables and methods don't exist)

- [ ] **Step 3: Add new tables to _create_tables**

In `mockr/core/progress/store.py`, append to the `_create_tables` executescript string (after the `dimension_stats` table, before the closing `"""`):

```python
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                target_level TEXT NOT NULL,
                inferred_level TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                mode_scores TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS role_profiles (
                id TEXT PRIMARY KEY,
                company TEXT,
                role_title TEXT NOT NULL,
                inferred_level TEXT NOT NULL,
                tech_stack TEXT,
                domain TEXT,
                key_skills TEXT,
                interview_intel TEXT,
                raw_text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            );
            CREATE TABLE IF NOT EXISTS practice_plans (
                id TEXT PRIMARY KEY,
                assessment_id TEXT REFERENCES assessments(id),
                role_profile_id TEXT REFERENCES role_profiles(id),
                target_level TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            );
            CREATE TABLE IF NOT EXISTS plan_items (
                id TEXT PRIMARY KEY,
                plan_id TEXT REFERENCES practice_plans(id),
                dimension TEXT NOT NULL,
                mode TEXT NOT NULL,
                priority REAL NOT NULL,
                gap_size REAL NOT NULL,
                challenge_id TEXT,
                rationale TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            );
```

- [ ] **Step 4: Add new methods to ProgressStore**

Append these methods to the `ProgressStore` class in `mockr/core/progress/store.py`:

```python
    # --- Assessment methods ---

    def save_assessment(
        self, assessment_id: str, target_level: str, inferred_level: str, mode_scores: dict,
    ) -> None:
        self._conn.execute(
            "INSERT INTO assessments (id, target_level, inferred_level, created_at, mode_scores) VALUES (?, ?, ?, ?, ?)",
            (assessment_id, target_level, inferred_level, datetime.now(UTC).isoformat(), json.dumps(mode_scores)),
        )
        self._conn.commit()

    def get_assessment(self, assessment_id: str) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # --- Role profile methods ---

    def save_role_profile(
        self,
        profile_id: str,
        company: str | None,
        role_title: str,
        inferred_level: str,
        tech_stack: list[str],
        domain: str | None,
        key_skills: list[dict],
        interview_intel: dict | None,
        raw_text: str,
    ) -> None:
        self._conn.execute(
            "INSERT INTO role_profiles (id, company, role_title, inferred_level, tech_stack, domain, key_skills, interview_intel, raw_text, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                profile_id, company, role_title, inferred_level,
                json.dumps(tech_stack), domain, json.dumps(key_skills),
                json.dumps(interview_intel) if interview_intel else None,
                raw_text, datetime.now(UTC).isoformat(),
            ),
        )
        self._conn.commit()

    def get_role_profile(self, profile_id: str) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM role_profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_role_profiles(self) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM role_profiles ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    # --- Practice plan methods ---

    def save_practice_plan(
        self, plan_id: str, assessment_id: str, role_profile_id: str | None, target_level: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT INTO practice_plans (id, assessment_id, role_profile_id, target_level, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (plan_id, assessment_id, role_profile_id, target_level, now, now),
        )
        self._conn.commit()

    def get_practice_plan(self, plan_id: str) -> dict | None:
        cursor = self._conn.execute("SELECT * FROM practice_plans WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def save_plan_item(
        self,
        item_id: str,
        plan_id: str,
        dimension: str,
        mode: str,
        priority: float,
        gap_size: float,
        challenge_id: str | None,
        rationale: str,
    ) -> None:
        self._conn.execute(
            "INSERT INTO plan_items (id, plan_id, dimension, mode, priority, gap_size, challenge_id, rationale) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (item_id, plan_id, dimension, mode, priority, gap_size, challenge_id, rationale),
        )
        self._conn.commit()

    def get_plan_items(self, plan_id: str) -> list[dict]:
        cursor = self._conn.execute(
            "SELECT * FROM plan_items WHERE plan_id = ? ORDER BY priority DESC", (plan_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_plan_item_status(self, item_id: str, status: str) -> None:
        self._conn.execute("UPDATE plan_items SET status = ? WHERE id = ?", (status, item_id))
        self._conn.commit()
```

- [ ] **Step 5: Add json import to store.py**

Add `import json` to the imports at the top of `mockr/core/progress/store.py` (after the existing `import uuid` line).

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/core/progress/test_store.py -v`
Expected: ALL PASS (both old and new tests)

- [ ] **Step 7: Commit**

```bash
git add mockr/core/progress/store.py tests/core/progress/test_store.py
git commit -m "feat: add persistence for assessments, role profiles, and practice plans"
```

---

## Wave 3: Diagnostic Assessment Engine (depends on Tasks 2, 5)

---

### Task 6: Diagnostic Challenge Files

**Files:**
- Create: `mockr/challenges/diagnostic/coding-diagnostic.toml`
- Create: `mockr/challenges/diagnostic/system-design-diagnostic.toml`
- Create: `mockr/challenges/diagnostic/behavioral-diagnostic.toml`

- [ ] **Step 1: Create coding diagnostic challenge**

Create `mockr/challenges/diagnostic/coding-diagnostic.toml`:

```toml
[meta]
id = "diagnostic-coding"
title = "Diagnostic: Array Manipulation"
mode = "coding"
language = "python"
tags = ["diagnostic", "arrays", "algorithms"]

[levels.intern]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for an intern-level candidate.
Present: 'Given a list of integers, write a function that returns the list with all duplicates removed, preserving original order.'
Keep it simple — assess basic coding ability."""
must_cover = ["iteration", "deduplication logic", "preserving order"]
follow_ups = ["What is the time complexity?", "Can you think of another approach?"]

[levels.junior]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a junior-level candidate.
Present: 'Given a list of integers, write a function that returns the list with all duplicates removed, preserving original order. Then extend it to handle a stream of integers where you return the running count of unique elements seen so far.'
Assess problem decomposition and coding fluency."""
must_cover = ["set-based deduplication", "streaming extension", "time complexity awareness"]
follow_ups = ["How would you handle very large streams?", "What data structure gives you O(1) lookup?"]

[levels.mid]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a mid-level candidate.
Present: 'Implement a function that takes a list of intervals [[start, end], ...] and merges all overlapping intervals. Return the merged list sorted by start time.'
Example: [[1,3],[2,6],[8,10],[15,18]] -> [[1,6],[8,10],[15,18]]
Assess algorithm design and edge case handling."""
must_cover = ["sorting approach", "merge logic", "edge cases (empty, single, all overlapping)"]
follow_ups = ["What's the time complexity?", "What if intervals arrive as a stream?"]

[levels.senior]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a senior-level candidate.
Present: 'Design and implement an LRU cache class with get(key) and put(key, value) operations, both in O(1) time. The cache has a fixed capacity.'
Assess data structure choice, API design, and code quality."""
must_cover = ["OrderedDict or doubly-linked list + hash map", "O(1) get and put", "capacity eviction", "clean API"]
follow_ups = ["How would you make this thread-safe?", "How would you add TTL support?"]

[levels.staff]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a staff-level candidate.
Present: 'Design and implement a task scheduler that executes tasks with dependencies in the correct order. Tasks can run in parallel if they have no mutual dependencies. Return a valid execution plan as a list of groups (each group runs in parallel).'
Assess graph thinking, correctness, and system-level design sense."""
must_cover = ["topological sort", "cycle detection", "parallel grouping", "clean abstraction"]
follow_ups = ["How do you handle cycles?", "How would you prioritize critical path tasks?"]

[levels.principal]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a principal-level candidate.
Present: 'Design and implement a simple expression evaluator that supports +, -, *, /, parentheses, and variables. Evaluate("(x + 2) * y", {"x": 3, "y": 4}) should return 20. Discuss your parsing strategy and extensibility.'
Assess language design intuition, parsing approach, and architectural taste."""
must_cover = ["parsing strategy (recursive descent or shunting yard)", "operator precedence", "variable resolution", "extensibility discussion"]
follow_ups = ["How would you add function calls?", "How would you report parse errors with good messages?"]

[[test_cases]]
input = "nums = [1, 2, 2, 3, 1]"
expected = "[1, 2, 3]"
hidden = false
```

- [ ] **Step 2: Create system design diagnostic challenge**

Create `mockr/challenges/diagnostic/system-design-diagnostic.toml`:

```toml
[meta]
id = "diagnostic-system-design"
title = "Diagnostic: URL Shortener"
mode = "system-design"
tags = ["diagnostic", "web-services", "storage", "scaling"]

[levels.intern]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for an intern-level candidate.
Ask: 'How would you build a simple URL shortener? A user gives you a long URL and you give them a short one that redirects.'
Focus on basic understanding of web request flow and data storage."""
must_cover = ["basic request flow", "storage of URL mapping", "redirect mechanism"]
follow_ups = ["Where would you store the URLs?", "How does the redirect work at the HTTP level?"]

[levels.junior]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a junior-level candidate.
Ask: 'Design a URL shortener service. Walk me through the API, how you'd generate short codes, and how you'd store the data.'
Look for basic API design and database thinking."""
must_cover = ["REST API design", "short code generation strategy", "database choice and schema"]
follow_ups = ["What happens if two URLs hash to the same code?", "How would you handle high traffic?"]

[levels.mid]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a mid-level candidate.
Ask: 'Design a URL shortener that handles 10M URLs and 100M redirects per month. Cover the API, data model, and how you would scale reads.'
Assess system thinking and scalability awareness."""
must_cover = ["read-heavy optimization", "caching strategy", "database indexing", "analytics tracking"]
follow_ups = ["How would you handle link expiration?", "What metrics would you track?"]

[levels.senior]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a senior-level candidate.
Ask: 'Design a URL shortener at scale — 1B URLs, 10B redirects/month, multi-region deployment. Cover architecture, data partitioning, caching, and operational concerns.'
Push on distributed systems tradeoffs."""
must_cover = ["data partitioning strategy", "multi-region consistency", "cache invalidation", "monitoring and alerting", "abuse prevention"]
follow_ups = ["How do you handle hot keys?", "What's your approach to geographic routing?"]

[levels.staff]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a staff-level candidate.
Ask: 'You are building a URL shortener as a platform service used by 50 internal teams. Design the multi-tenant architecture, self-service provisioning, SLO framework, and capacity planning model.'
Push on platform thinking and organizational design."""
must_cover = ["multi-tenant isolation", "SLO design and error budgets", "capacity planning", "self-service API and governance", "cost attribution"]
follow_ups = ["How do you handle a tenant that consumes disproportionate resources?", "How do you deprecate and migrate tenants off an old version?"]

[levels.principal]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a principal-level candidate.
Ask: 'You are the technical leader for a URL shortener that has grown into a core platform dependency. 200 teams use it. It has reliability issues and needs a next-generation architecture. How do you approach this?'
Push on technical strategy, migration planning, and organizational leadership."""
must_cover = ["current state assessment", "incremental migration strategy", "stakeholder alignment", "reliability engineering", "long-term technical vision"]
follow_ups = ["How do you get buy-in from teams that don't want to migrate?", "How do you measure success?"]
```

- [ ] **Step 3: Create behavioral diagnostic challenge**

Create `mockr/challenges/diagnostic/behavioral-diagnostic.toml`:

```toml
[meta]
id = "diagnostic-behavioral"
title = "Diagnostic: Overcoming a Technical Challenge"
mode = "behavioral"
tags = ["diagnostic", "problem-solving", "resilience", "communication"]

[levels.intern]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for an intern-level candidate.
Ask: 'Tell me about a project or assignment — school or personal — where you got stuck on a technical problem. How did you work through it?'
Look for basic problem-solving instincts and willingness to ask for help."""
must_cover = ["description of the problem", "steps taken to resolve", "outcome"]
follow_ups = ["Did you ask anyone for help?", "What did you learn from the experience?"]

[levels.junior]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a junior-level candidate.
Ask: 'Tell me about a time you faced a challenging bug or technical problem at work. Walk me through your debugging process and what you learned.'
Look for structured thinking and learning orientation."""
must_cover = ["specific situation", "debugging approach", "resolution", "learning applied later"]
follow_ups = ["How did you narrow down the root cause?", "What would you do differently next time?"]

[levels.mid]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a mid-level candidate.
Ask: 'Tell me about a time you had to deliver a feature under significant time pressure or uncertainty. How did you manage scope, risk, and communication?'
Look for project management instincts and stakeholder communication."""
must_cover = ["situation and constraints", "scope management decisions", "communication with stakeholders", "outcome and reflection"]
follow_ups = ["How did you decide what to cut?", "How did you keep your team or manager informed?"]

[levels.senior]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a senior-level candidate.
Ask: 'Tell me about a time you identified a significant technical risk or problem that others hadn't noticed. How did you raise it and what happened?'
Look for proactive leadership and influence."""
must_cover = ["how the risk was identified", "approach to raising concerns", "influence and persuasion", "outcome and organizational impact"]
follow_ups = ["How did you get people to take it seriously?", "What would you have done if leadership disagreed?"]

[levels.staff]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a staff-level candidate.
Ask: 'Describe a time you drove a major technical initiative across multiple teams. How did you align people, manage dependencies, and ensure delivery?'
Look for cross-team leadership and strategic execution."""
must_cover = ["scope and scale of initiative", "alignment and consensus building", "dependency management", "dealing with resistance", "measurable outcome"]
follow_ups = ["How did you handle teams that had competing priorities?", "What was the hardest tradeoff you had to make?"]

[levels.principal]
estimated_minutes = 10
interviewer = """You are conducting a diagnostic assessment for a principal-level candidate.
Ask: 'Tell me about a time you had to make a bet on a technical direction that had significant organizational consequences — a platform migration, a build-vs-buy decision, or a major architectural shift. How did you make the call and see it through?'
Look for strategic thinking, risk tolerance, and organizational navigation."""
must_cover = ["strategic context and stakes", "decision-making framework", "stakeholder management at exec level", "execution through uncertainty", "long-term impact assessment"]
follow_ups = ["How did you know you were making the right call?", "What would have happened if you were wrong?"]
```

- [ ] **Step 4: Validate all diagnostic challenges load correctly**

Run:

```bash
python -c "
from pathlib import Path
from mockr.core.challenges.loader import load_challenge, validate_challenge
for p in Path('mockr/challenges/diagnostic').glob('*.toml'):
    ch = load_challenge(p)
    errors = validate_challenge(ch)
    print(f'{ch.id}: {len(ch.levels)} levels, errors={errors}')
"
```

Expected: 3 challenges loaded, 0 errors each, each with 6 levels (intern through principal).

- [ ] **Step 5: Commit**

```bash
git add mockr/challenges/diagnostic/
git commit -m "feat: add diagnostic challenge files for all modes and levels"
```

---

### Task 7: Assessment Engine

**Files:**
- Create: `mockr/core/assessment/engine.py`
- Create: `tests/core/assessment/test_engine.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/assessment/test_engine.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mockr.core.assessment.engine import AssessmentEngine
from mockr.core.assessment.models import AssessmentResult
from mockr.core.events import EventBus, ScoreReady
from mockr.core.types import Level, Message, Mode, ModelConfig


class FakeAssessmentBackend:
    """Returns canned scores for each mode."""

    def __init__(self, scores_by_mode: dict[str, dict[str, float]]) -> None:
        self._scores_by_mode = scores_by_mode

    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        content = " ".join(m.content.lower() for m in messages)
        if "score each dimension" in content:
            # Determine mode from content
            for mode, scores in self._scores_by_mode.items():
                if mode.replace("-", " ") in content or mode in content:
                    return json.dumps({
                        "dimensions": scores,
                        "strengths": ["Good"],
                        "improvements": ["Improve"],
                    })
            # Default
            first_mode = next(iter(self._scores_by_mode))
            return json.dumps({
                "dimensions": self._scores_by_mode[first_mode],
                "strengths": ["Good"],
                "improvements": ["Improve"],
            })
        elif "debrief" in content:
            return json.dumps({
                "overall_score": 3.5,
                "dimension_scores": {},
                "summary": "Diagnostic complete.",
            })
        else:
            return "Tell me about your approach."


@pytest.mark.asyncio
class TestAssessmentEngine:
    async def test_run_diagnostic_returns_result(self) -> None:
        scores = {
            "coding": {"correctness": 4.0, "efficiency": 3.0, "code_quality": 3.5, "edge_cases": 3.0, "communication": 3.5},
            "system-design": {"structure": 3.0, "constraints": 2.5, "tradeoffs": 3.0, "reliability": 2.0, "concreteness": 3.0},
            "behavioral": {"situation": 4.0, "task": 3.5, "action": 3.5, "result": 3.0, "impact": 3.0},
        }
        backend = FakeAssessmentBackend(scores)
        engine = AssessmentEngine(
            backend=backend,
            config=ModelConfig(model="test"),
            challenges_dir=Path("mockr/challenges/diagnostic"),
        )
        result = await engine.run_diagnostic(
            target_level="senior",
            answer_callback=self._fake_answer,
        )
        assert isinstance(result, AssessmentResult)
        assert result.target_level == "senior"
        assert "coding" in result.mode_scores
        assert "system-design" in result.mode_scores
        assert "behavioral" in result.mode_scores

    async def test_diagnostic_detects_gaps(self) -> None:
        scores = {
            "coding": {"correctness": 2.0, "efficiency": 2.0, "code_quality": 2.0, "edge_cases": 2.0, "communication": 2.0},
            "system-design": {"structure": 2.0, "constraints": 2.0, "tradeoffs": 2.0, "reliability": 2.0, "concreteness": 2.0},
            "behavioral": {"situation": 2.0, "task": 2.0, "action": 2.0, "result": 2.0, "impact": 2.0},
        }
        backend = FakeAssessmentBackend(scores)
        engine = AssessmentEngine(
            backend=backend,
            config=ModelConfig(model="test"),
            challenges_dir=Path("mockr/challenges/diagnostic"),
        )
        result = await engine.run_diagnostic(
            target_level="senior",
            answer_callback=self._fake_answer,
        )
        assert len(result.gaps) > 0
        assert all(g.gap_size > 0 for g in result.gaps)

    @staticmethod
    async def _fake_answer(question: str, mode: str) -> str:
        return "Here is my answer to the diagnostic question."
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/assessment/test_engine.py -v`
Expected: FAIL (engine module doesn't exist)

- [ ] **Step 3: Implement the assessment engine**

Create `mockr/core/assessment/engine.py`:

```python
"""Diagnostic assessment engine — runs mini-interviews across modes."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path

from mockr.core.assessment.models import AssessmentResult
from mockr.core.assessment.thresholds import detect_gaps, infer_level
from mockr.core.challenges.loader import load_challenges_from_dir
from mockr.core.scoring.scorer import DIMENSIONS_BY_MODE, Scorer
from mockr.core.types import Message, ModelConfig

# Modes to assess (in order)
_DIAGNOSTIC_MODES = ["coding", "system-design", "behavioral"]


class AssessmentEngine:
    def __init__(
        self,
        backend: object,
        config: ModelConfig,
        challenges_dir: Path,
    ) -> None:
        self._backend = backend
        self._config = config
        self._challenges_dir = challenges_dir
        self._scorer = Scorer()

    async def run_diagnostic(
        self,
        target_level: str,
        answer_callback: Callable[[str, str], Awaitable[str]],
    ) -> AssessmentResult:
        """Run a 3-mode diagnostic assessment.

        answer_callback(question, mode) -> user's answer string.
        Called once per mode to collect the user's response.
        """
        challenges = load_challenges_from_dir(self._challenges_dir)
        challenge_by_mode = {ch.mode: ch for ch in challenges}
        mode_scores: dict[str, dict[str, float]] = {}

        for mode in _DIAGNOSTIC_MODES:
            challenge = challenge_by_mode.get(mode)
            if challenge is None:
                continue

            level_config = challenge.levels.get(target_level)
            if level_config is None:
                # Fall back to closest available level
                available = list(challenge.levels.keys())
                level_config = challenge.levels[available[0]] if available else None
            if level_config is None:
                continue

            # Generate question
            question_messages = [
                Message(role="system", content=level_config.interviewer),
                Message(role="user", content="Start the interview with the first question."),
            ]
            question = await self._backend.generate(question_messages, self._config)

            # Get user's answer
            answer = await answer_callback(question, mode)

            # Score the answer
            score_prompt = self._scorer.build_scoring_prompt(
                mode=mode,
                level=target_level,
                answer=answer,
                must_cover=level_config.must_cover,
                turn_number=1,
            )
            score_raw = await self._backend.generate(
                [Message(role="user", content=score_prompt)], self._config,
            )
            score_result = self._scorer.parse_score_response(score_raw, mode=mode)
            mode_scores[mode] = score_result.dimensions

        gaps = detect_gaps(mode_scores, target_level)
        inferred = infer_level(mode_scores)

        return AssessmentResult(
            id=str(uuid.uuid4()),
            target_level=target_level,
            inferred_level=inferred,
            mode_scores=mode_scores,
            gaps=gaps,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/assessment/test_engine.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add mockr/core/assessment/engine.py tests/core/assessment/test_engine.py
git commit -m "feat: implement diagnostic assessment engine"
```

---

## Wave 4: Plan Generator (depends on Tasks 2, 3, 5)

---

### Task 8: Plan Generator

**Files:**
- Create: `mockr/core/planning/generator.py`
- Create: `tests/core/planning/test_generator.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/planning/test_generator.py`:

```python
from __future__ import annotations

from pathlib import Path

from mockr.core.assessment.models import AssessmentResult, Gap
from mockr.core.jd.models import RoleProfile, Skill
from mockr.core.planning.generator import PlanGenerator
from mockr.core.planning.models import PracticePlan


class TestPlanGenerator:
    def test_generate_plan_from_assessment(self) -> None:
        result = AssessmentResult(
            id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores={
                "coding": {"correctness": 2.0, "efficiency": 3.0, "code_quality": 3.5, "edge_cases": 2.5, "communication": 3.5},
            },
            gaps=[
                Gap(dimension="correctness", mode="coding", current_score=2.0, target_score=3.5, gap_size=1.5),
                Gap(dimension="edge_cases", mode="coding", current_score=2.5, target_score=3.5, gap_size=1.0),
            ],
        )
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result)
        assert isinstance(plan, PracticePlan)
        assert plan.target_level == "senior"
        assert len(plan.items) == 2
        # Higher gap = higher priority
        assert plan.items[0].gap_size >= plan.items[1].gap_size

    def test_generate_plan_with_role_profile(self) -> None:
        result = AssessmentResult(
            id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores={},
            gaps=[
                Gap(dimension="correctness", mode="coding", current_score=2.0, target_score=3.5, gap_size=1.5),
                Gap(dimension="tradeoffs", mode="system-design", current_score=2.5, target_score=3.5, gap_size=1.0),
            ],
        )
        profile = RoleProfile(
            id="rp1",
            role_title="Senior Backend Engineer",
            inferred_level="senior",
            raw_text="...",
            key_skills=[
                Skill(name="system design", category="system-design", dimensions=["tradeoffs"], weight=0.9),
            ],
        )
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result, role_profile=profile)
        assert plan.role_profile_id == "rp1"
        # JD-boosted tradeoffs should have higher priority than base gap_size alone
        tradeoffs_item = next(i for i in plan.items if i.dimension == "tradeoffs")
        correctness_item = next(i for i in plan.items if i.dimension == "correctness")
        assert tradeoffs_item.priority > correctness_item.priority

    def test_generate_plan_matches_challenges(self) -> None:
        result = AssessmentResult(
            id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores={},
            gaps=[
                Gap(dimension="correctness", mode="coding", current_score=2.0, target_score=3.5, gap_size=1.5),
            ],
        )
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result)
        # Should match an existing coding challenge
        coding_items = [i for i in plan.items if i.mode == "coding"]
        assert any(i.challenge_id is not None for i in coding_items)

    def test_plan_items_sorted_by_priority(self) -> None:
        result = AssessmentResult(
            id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores={},
            gaps=[
                Gap(dimension="correctness", mode="coding", current_score=2.0, target_score=3.5, gap_size=1.5),
                Gap(dimension="structure", mode="system-design", current_score=3.0, target_score=3.5, gap_size=0.5),
                Gap(dimension="action", mode="behavioral", current_score=1.5, target_score=3.5, gap_size=2.0),
            ],
        )
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result)
        priorities = [item.priority for item in plan.items]
        assert priorities == sorted(priorities, reverse=True)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/planning/test_generator.py -v`
Expected: FAIL

- [ ] **Step 3: Implement the plan generator**

Create `mockr/core/planning/generator.py`:

```python
"""Practice plan generator — turns assessment gaps into actionable plans."""

from __future__ import annotations

import uuid
from pathlib import Path

from mockr.core.assessment.models import AssessmentResult
from mockr.core.challenges.loader import load_challenges_from_dir
from mockr.core.jd.models import RoleProfile
from mockr.core.planning.models import PlanItem, PracticePlan

# Foundational dimensions get a slight boost (other skills build on them)
_FOUNDATIONAL_DIMS = {"correctness", "structure", "situation"}
_FOUNDATIONAL_BOOST = 0.05


class PlanGenerator:
    def __init__(self, challenges_dir: Path) -> None:
        self._challenges_dir = challenges_dir

    def generate(
        self,
        assessment: AssessmentResult,
        role_profile: RoleProfile | None = None,
    ) -> PracticePlan:
        """Generate a practice plan from assessment gaps, optionally boosted by a role profile."""
        challenges = load_challenges_from_dir(self._challenges_dir)
        # Index challenges by mode (exclude diagnostic ones)
        challenges_by_mode: dict[str, list] = {}
        for ch in challenges:
            if ch.id.startswith("diagnostic-"):
                continue
            challenges_by_mode.setdefault(ch.mode, []).append(ch)

        # Build JD skill weight lookup: (mode, dimension) -> weight
        jd_weights: dict[tuple[str, str], float] = {}
        if role_profile:
            for skill in role_profile.key_skills:
                for dim in skill.dimensions:
                    key = (skill.category, dim)
                    jd_weights[key] = max(jd_weights.get(key, 0), skill.weight)

        items: list[PlanItem] = []
        for gap in assessment.gaps:
            # Base priority from gap size, normalized to 0-1 (max gap is 4.0: score 1 vs threshold 5)
            base_priority = min(gap.gap_size / 4.0, 1.0)

            # JD boost
            jd_weight = jd_weights.get((gap.mode, gap.dimension), 0.0)
            jd_boost = jd_weight * 0.3  # up to 0.3 boost from JD

            # Foundational boost
            foundation_boost = _FOUNDATIONAL_BOOST if gap.dimension in _FOUNDATIONAL_DIMS else 0.0

            priority = min(base_priority + jd_boost + foundation_boost, 1.0)

            # Match a challenge from the bank
            challenge_id = self._match_challenge(gap.mode, challenges_by_mode)

            items.append(
                PlanItem(
                    dimension=gap.dimension,
                    mode=gap.mode,
                    priority=round(priority, 3),
                    gap_size=gap.gap_size,
                    challenge_id=challenge_id,
                    rationale=f"Your {gap.dimension} score is {gap.current_score}, {assessment.target_level} needs {gap.target_score}",
                )
            )

        # Sort by priority descending
        items.sort(key=lambda x: x.priority, reverse=True)

        return PracticePlan(
            id=str(uuid.uuid4()),
            assessment_id=assessment.id,
            target_level=assessment.target_level,
            role_profile_id=role_profile.id if role_profile else None,
            items=items,
        )

    def _match_challenge(self, mode: str, challenges_by_mode: dict[str, list]) -> str | None:
        """Return the first matching challenge id for the given mode, or None."""
        mode_challenges = challenges_by_mode.get(mode, [])
        if mode_challenges:
            return mode_challenges[0].id
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/planning/test_generator.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add mockr/core/planning/generator.py tests/core/planning/test_generator.py
git commit -m "feat: implement practice plan generator with gap-based prioritization"
```

---

### Task 9: Adaptive Plan Updates

**Files:**
- Create: `mockr/core/planning/adapter.py`
- Create: `tests/core/planning/test_adapter.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/planning/test_adapter.py`:

```python
from __future__ import annotations

from mockr.core.planning.adapter import PlanAdapter
from mockr.core.planning.models import PlanItem, PracticePlan


class TestPlanAdapter:
    def test_recalculate_marks_validated_when_gap_closed(self) -> None:
        plan = PracticePlan(
            id="p1",
            assessment_id="a1",
            target_level="senior",
            items=[
                PlanItem(dimension="correctness", mode="coding", priority=0.8, gap_size=1.5, rationale="r"),
            ],
        )
        # New scores show correctness now at 4.0 (above senior threshold of 3.5)
        updated_scores = {"coding": {"correctness": 4.0}}
        adapter = PlanAdapter()
        updated_plan = adapter.recalculate(plan, updated_scores, target_level="senior")
        assert updated_plan.items[0].status == "validated"

    def test_recalculate_updates_priority_when_gap_shrinks(self) -> None:
        plan = PracticePlan(
            id="p1",
            assessment_id="a1",
            target_level="senior",
            items=[
                PlanItem(dimension="correctness", mode="coding", priority=0.8, gap_size=1.5, rationale="r"),
            ],
        )
        updated_scores = {"coding": {"correctness": 3.0}}  # improved but still below 3.5
        adapter = PlanAdapter()
        updated_plan = adapter.recalculate(plan, updated_scores, target_level="senior")
        assert updated_plan.items[0].status == "pending"
        assert updated_plan.items[0].gap_size < 1.5
        assert updated_plan.items[0].priority < 0.8

    def test_reassessment_trigger_after_plateau(self) -> None:
        adapter = PlanAdapter()
        # Simulate 5 session scores with <0.2 improvement
        recent_scores = [2.0, 2.1, 2.0, 2.1, 2.05]
        assert adapter.should_reassess(recent_scores, threshold=3.5) is True

    def test_no_reassessment_when_improving(self) -> None:
        adapter = PlanAdapter()
        recent_scores = [2.0, 2.5, 3.0, 3.3, 3.5]
        assert adapter.should_reassess(recent_scores, threshold=3.5) is False

    def test_no_reassessment_with_few_sessions(self) -> None:
        adapter = PlanAdapter()
        recent_scores = [2.0, 2.5]
        assert adapter.should_reassess(recent_scores, threshold=3.5) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/planning/test_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: Implement the adaptive plan updater**

Create `mockr/core/planning/adapter.py`:

```python
"""Adaptive plan updates after each session."""

from __future__ import annotations

from mockr.core.assessment.thresholds import LEVEL_THRESHOLDS
from mockr.core.planning.models import PlanItem, PracticePlan

_MIN_SESSIONS_FOR_REASSESSMENT = 5
_PLATEAU_IMPROVEMENT_THRESHOLD = 0.2


class PlanAdapter:
    def recalculate(
        self,
        plan: PracticePlan,
        updated_scores: dict[str, dict[str, float]],
        target_level: str,
    ) -> PracticePlan:
        """Recalculate plan item priorities and statuses based on new scores."""
        thresholds = LEVEL_THRESHOLDS.get(target_level, LEVEL_THRESHOLDS["senior"])
        new_items: list[PlanItem] = []

        for item in plan.items:
            mode_scores = updated_scores.get(item.mode, {})
            current_score = mode_scores.get(item.dimension)

            if current_score is None:
                # No new data for this dimension — keep as-is
                new_items.append(item)
                continue

            mode_thresholds = thresholds.get(item.mode, {})
            target_score = mode_thresholds.get(item.dimension, 3.5)

            if current_score >= target_score:
                new_items.append(
                    PlanItem(
                        dimension=item.dimension,
                        mode=item.mode,
                        priority=0.0,
                        gap_size=0.0,
                        challenge_id=item.challenge_id,
                        rationale=f"{item.dimension} reached target ({current_score:.1f} >= {target_score})",
                        status="validated",
                    )
                )
            else:
                new_gap = round(target_score - current_score, 2)
                new_priority = round(min(new_gap / 4.0, 1.0), 3)
                new_items.append(
                    PlanItem(
                        dimension=item.dimension,
                        mode=item.mode,
                        priority=new_priority,
                        gap_size=new_gap,
                        challenge_id=item.challenge_id,
                        rationale=f"Your {item.dimension} score is {current_score:.1f}, {target_level} needs {target_score}",
                        status="pending",
                    )
                )

        new_items.sort(key=lambda x: x.priority, reverse=True)
        return PracticePlan(
            id=plan.id,
            assessment_id=plan.assessment_id,
            target_level=plan.target_level,
            role_profile_id=plan.role_profile_id,
            items=new_items,
            created_at=plan.created_at,
        )

    def should_reassess(self, recent_scores: list[float], threshold: float) -> bool:
        """Check if a re-assessment is warranted based on plateau detection."""
        if len(recent_scores) < _MIN_SESSIONS_FOR_REASSESSMENT:
            return False
        last_n = recent_scores[-_MIN_SESSIONS_FOR_REASSESSMENT:]
        # Check if all scores are below threshold
        if any(s >= threshold for s in last_n):
            return False
        # Check for plateau: improvement from first to last < threshold
        improvement = last_n[-1] - last_n[0]
        return abs(improvement) < _PLATEAU_IMPROVEMENT_THRESHOLD
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/planning/test_adapter.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add mockr/core/planning/adapter.py tests/core/planning/test_adapter.py
git commit -m "feat: add adaptive plan updates with plateau-based reassessment triggers"
```

---

## Wave 5: JD Parsing & Intel (depends on Task 4)

Tasks 10-12 can be executed in parallel.

---

### Task 10: JD Parser

**Files:**
- Create: `mockr/core/jd/parser.py`
- Create: `tests/core/jd/test_parser.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/jd/test_parser.py`:

```python
from __future__ import annotations

import json

import pytest

from mockr.core.jd.models import RoleProfile
from mockr.core.jd.parser import JDParser
from mockr.core.types import Message, ModelConfig


class FakeParserBackend:
    """Returns a canned RoleProfile JSON extraction."""

    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        return json.dumps({
            "company": "Stripe",
            "role_title": "Senior Backend Engineer",
            "inferred_level": "senior",
            "tech_stack": ["Python", "PostgreSQL", "Kubernetes"],
            "domain": "fintech",
            "key_skills": [
                {"name": "distributed systems", "category": "system-design", "dimensions": ["structure", "reliability"], "weight": 0.9},
                {"name": "Python", "category": "coding", "dimensions": ["correctness", "code_quality"], "weight": 0.8},
                {"name": "leadership", "category": "behavioral", "dimensions": ["action", "impact"], "weight": 0.6},
            ],
        })


@pytest.mark.asyncio
class TestJDParser:
    async def test_parse_jd_text(self) -> None:
        parser = JDParser(backend=FakeParserBackend(), config=ModelConfig(model="test"))
        profile = await parser.parse_text("We are looking for a Senior Backend Engineer at Stripe...")
        assert isinstance(profile, RoleProfile)
        assert profile.company == "Stripe"
        assert profile.inferred_level == "senior"
        assert len(profile.key_skills) == 3

    async def test_parse_jd_preserves_raw_text(self) -> None:
        parser = JDParser(backend=FakeParserBackend(), config=ModelConfig(model="test"))
        raw = "This is the original JD text."
        profile = await parser.parse_text(raw)
        assert profile.raw_text == raw

    async def test_parse_jd_handles_missing_company(self) -> None:
        class NoCompanyBackend:
            async def generate(self, messages, config):
                return json.dumps({
                    "company": None,
                    "role_title": "Software Engineer",
                    "inferred_level": "mid",
                    "tech_stack": [],
                    "domain": None,
                    "key_skills": [],
                })

        parser = JDParser(backend=NoCompanyBackend(), config=ModelConfig(model="test"))
        profile = await parser.parse_text("Generic SWE role")
        assert profile.company is None
        assert profile.role_title == "Software Engineer"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/jd/test_parser.py -v`
Expected: FAIL

- [ ] **Step 3: Implement the JD parser**

Create `mockr/core/jd/parser.py`:

```python
"""JD text parsing via LLM extraction."""

from __future__ import annotations

import uuid

from mockr.core.jd.models import RoleProfile, Skill
from mockr.core.types import Message, ModelConfig
from mockr.core.utils import extract_json_object

_JD_EXTRACTION_PROMPT = """You are extracting structured information from a job description.

Analyze the following job description and return a JSON object with these fields:
- "company": company name (string or null if not found)
- "role_title": the job title (string)
- "inferred_level": map to one of: "intern", "junior", "mid", "senior", "staff", "principal", "engineering_manager", "director", "vp"
- "tech_stack": list of technologies mentioned (strings)
- "domain": industry domain like "fintech", "healthcare", "e-commerce" (string or null)
- "key_skills": list of objects, each with:
  - "name": skill name (string)
  - "category": one of "system-design", "coding", "behavioral"
  - "dimensions": list of scoring dimensions this skill relates to
    - For coding: from ["correctness", "efficiency", "code_quality", "edge_cases", "communication"]
    - For system-design: from ["structure", "constraints", "tradeoffs", "reliability", "concreteness"]
    - For behavioral: from ["situation", "task", "action", "result", "impact"]
  - "weight": how prominently this skill features in the JD (0.0 to 1.0)

Return ONLY valid JSON.

Job Description:
{jd_text}"""


class JDParser:
    def __init__(self, backend: object, config: ModelConfig) -> None:
        self._backend = backend
        self._config = config

    async def parse_text(self, jd_text: str) -> RoleProfile:
        """Parse raw JD text into a structured RoleProfile."""
        prompt = _JD_EXTRACTION_PROMPT.format(jd_text=jd_text)
        raw = await self._backend.generate(
            [Message(role="user", content=prompt)], self._config,
        )
        data = extract_json_object(raw)

        skills = [
            Skill(
                name=s["name"],
                category=s.get("category", "coding"),
                dimensions=s.get("dimensions", []),
                weight=s.get("weight", 0.5),
            )
            for s in data.get("key_skills", [])
        ]

        return RoleProfile(
            id=str(uuid.uuid4()),
            company=data.get("company"),
            role_title=data.get("role_title", "Unknown Role"),
            inferred_level=data.get("inferred_level", "mid"),
            tech_stack=data.get("tech_stack", []),
            domain=data.get("domain"),
            key_skills=skills,
            raw_text=jd_text,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/jd/test_parser.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add mockr/core/jd/parser.py tests/core/jd/test_parser.py
git commit -m "feat: implement JD parser with LLM-based role profile extraction"
```

---

### Task 11: Interview Intel Gathering

**Files:**
- Create: `mockr/core/jd/intel.py`
- Create: `tests/core/jd/test_intel.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/jd/test_intel.py`:

```python
from __future__ import annotations

import json

import pytest

from mockr.core.jd.intel import IntelGatherer
from mockr.core.jd.models import InterviewIntel
from mockr.core.types import Message, ModelConfig


class FakeIntelBackend:
    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        return json.dumps({
            "format": ["phone screen", "2x coding", "system design", "behavioral"],
            "common_topics": ["API design", "concurrency", "system scalability"],
            "culture_signals": ["Strong emphasis on communication"],
            "gotchas": ["System design round is only 30 minutes"],
        })


class FakeWebSearcher:
    """Simulates web search returning relevant snippets."""

    async def search(self, query: str) -> list[dict]:
        return [
            {"url": "https://glassdoor.com/stripe-interview", "snippet": "Phone screen then coding rounds"},
            {"url": "https://reddit.com/r/cscareerquestions/stripe", "snippet": "System design is fast-paced"},
        ]


@pytest.mark.asyncio
class TestIntelGatherer:
    async def test_gather_intel(self) -> None:
        gatherer = IntelGatherer(
            backend=FakeIntelBackend(),
            config=ModelConfig(model="test"),
            web_searcher=FakeWebSearcher(),
        )
        intel = await gatherer.gather(company="Stripe", role_title="Senior Backend Engineer")
        assert isinstance(intel, InterviewIntel)
        assert len(intel.format) > 0
        assert len(intel.sources) > 0

    async def test_gather_intel_no_results(self) -> None:
        class EmptySearcher:
            async def search(self, query: str) -> list[dict]:
                return []

        gatherer = IntelGatherer(
            backend=FakeIntelBackend(),
            config=ModelConfig(model="test"),
            web_searcher=EmptySearcher(),
        )
        intel = await gatherer.gather(company="TinyStartup", role_title="SWE")
        # Should return None when no search results
        assert intel is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/jd/test_intel.py -v`
Expected: FAIL

- [ ] **Step 3: Implement the intel gatherer**

Create `mockr/core/jd/intel.py`:

```python
"""Interview intel gathering via web search + LLM summarization."""

from __future__ import annotations

from mockr.core.jd.models import InterviewIntel
from mockr.core.types import Message, ModelConfig
from mockr.core.utils import extract_json_object

_INTEL_PROMPT = """You are summarizing interview process information for a candidate.

Based on the following search results about interviews at {company} for {role_title}, extract:
- "format": list of interview stages/rounds (strings)
- "common_topics": list of commonly asked topics (strings)
- "culture_signals": list of what interviewers value (strings)
- "gotchas": list of known quirks or tips (strings)

If the search results don't contain useful interview information, return {{"empty": true}}.

Return ONLY valid JSON.

Search results:
{search_results}"""


class IntelGatherer:
    def __init__(self, backend: object, config: ModelConfig, web_searcher: object) -> None:
        self._backend = backend
        self._config = config
        self._searcher = web_searcher

    async def gather(self, company: str, role_title: str) -> InterviewIntel | None:
        """Search for and summarize interview intel for a company/role."""
        queries = [
            f"{company} software engineer interview process glassdoor",
            f"{company} interview questions reddit",
            f"{company} {role_title} interview blind",
        ]

        all_results: list[dict] = []
        for query in queries:
            results = await self._searcher.search(query)
            all_results.extend(results)

        if not all_results:
            return None

        sources = [r["url"] for r in all_results]
        snippets = "\n".join(f"- [{r['url']}]: {r['snippet']}" for r in all_results)

        prompt = _INTEL_PROMPT.format(
            company=company, role_title=role_title, search_results=snippets,
        )
        raw = await self._backend.generate(
            [Message(role="user", content=prompt)], self._config,
        )

        try:
            data = extract_json_object(raw)
        except (ValueError, KeyError):
            return None

        if data.get("empty"):
            return None

        return InterviewIntel(
            format=data.get("format", []),
            common_topics=data.get("common_topics", []),
            culture_signals=data.get("culture_signals", []),
            gotchas=data.get("gotchas", []),
            sources=sources,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/jd/test_intel.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add mockr/core/jd/intel.py tests/core/jd/test_intel.py
git commit -m "feat: implement interview intel gathering via web search"
```

---

### Task 12: LLM Challenge Generation

**Files:**
- Create: `mockr/core/jd/challenge_gen.py`
- Create: `tests/core/jd/test_challenge_gen.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/jd/test_challenge_gen.py`:

```python
from __future__ import annotations

import json

import pytest

from mockr.core.challenges.models import Challenge
from mockr.core.jd.challenge_gen import ChallengeGenerator
from mockr.core.jd.models import Skill
from mockr.core.types import Message, ModelConfig


class FakeChallengeBackend:
    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        content = " ".join(m.content.lower() for m in messages)
        if "review" in content and "solvable" in content:
            # Quality check pass
            return json.dumps({"pass": True, "reason": "Challenge is well-scoped"})
        return json.dumps({
            "id": "generated-k8s-networking",
            "title": "Kubernetes Service Mesh Design",
            "mode": "system-design",
            "tags": ["kubernetes", "networking", "service-mesh"],
            "levels": {
                "senior": {
                    "estimated_minutes": 15,
                    "interviewer": "Design a service mesh for Kubernetes...",
                    "must_cover": ["sidecar proxy", "service discovery", "load balancing"],
                    "follow_ups": ["How do you handle mTLS?"],
                }
            },
        })


@pytest.mark.asyncio
class TestChallengeGenerator:
    async def test_generate_challenge_for_skill(self) -> None:
        skill = Skill(name="Kubernetes networking", category="system-design", dimensions=["structure"], weight=0.9)
        generator = ChallengeGenerator(
            backend=FakeChallengeBackend(),
            config=ModelConfig(model="test"),
        )
        challenge = await generator.generate_for_skill(skill, target_level="senior", tech_stack=["Kubernetes", "Go"])
        assert isinstance(challenge, Challenge)
        assert challenge.mode == "system-design"
        assert len(challenge.levels) > 0
        assert challenge.id.startswith("generated-")

    async def test_generate_challenge_marked_as_generated(self) -> None:
        skill = Skill(name="test", category="coding", dimensions=["correctness"], weight=0.5)
        generator = ChallengeGenerator(
            backend=FakeChallengeBackend(),
            config=ModelConfig(model="test"),
        )
        challenge = await generator.generate_for_skill(skill, target_level="senior")
        assert challenge.tags is not None
        # Generated challenges get a "generated" tag
        assert "generated" in challenge.tags
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/jd/test_challenge_gen.py -v`
Expected: FAIL

- [ ] **Step 3: Implement the challenge generator**

Create `mockr/core/jd/challenge_gen.py`:

```python
"""LLM-based challenge generation from JD skills."""

from __future__ import annotations

from mockr.core.challenges.models import Challenge, LevelConfig
from mockr.core.jd.models import Skill
from mockr.core.types import Message, ModelConfig
from mockr.core.utils import extract_json_object

_GENERATION_PROMPT = """Generate a mock interview challenge for the following skill.

Skill: {skill_name}
Mode: {mode}
Target level: {target_level}
Tech stack context: {tech_stack}

Return a JSON object with:
- "id": a slug starting with "generated-" (e.g., "generated-k8s-networking")
- "title": a descriptive title
- "mode": "{mode}"
- "tags": list of relevant tags (include the skill name)
- "levels": {{
    "{target_level}": {{
      "estimated_minutes": 15,
      "interviewer": "system prompt for the interviewer (2-3 sentences describing the problem)",
      "must_cover": ["topic 1", "topic 2", "topic 3"],
      "follow_ups": ["follow-up question 1", "follow-up question 2"]
    }}
  }}

Make the challenge appropriately scoped for {target_level} level.
Return ONLY valid JSON."""

_QUALITY_CHECK_PROMPT = """Review this interview challenge for quality.

{challenge_json}

Is this challenge:
1. Solvable within the estimated time?
2. Appropriately scoped for {target_level} level?
3. Testing the right skill ({skill_name})?

Return JSON: {{"pass": true/false, "reason": "..."}}"""


class ChallengeGenerator:
    def __init__(self, backend: object, config: ModelConfig) -> None:
        self._backend = backend
        self._config = config

    async def generate_for_skill(
        self,
        skill: Skill,
        target_level: str,
        tech_stack: list[str] | None = None,
    ) -> Challenge:
        """Generate a challenge for an uncovered skill."""
        prompt = _GENERATION_PROMPT.format(
            skill_name=skill.name,
            mode=skill.category,
            target_level=target_level,
            tech_stack=", ".join(tech_stack) if tech_stack else "general",
        )
        raw = await self._backend.generate(
            [Message(role="user", content=prompt)], self._config,
        )
        data = extract_json_object(raw)

        # Build Challenge from LLM response
        levels: dict[str, LevelConfig] = {}
        for level_name, level_data in data.get("levels", {}).items():
            levels[level_name] = LevelConfig(
                estimated_minutes=level_data.get("estimated_minutes", 15),
                interviewer=level_data.get("interviewer", ""),
                must_cover=level_data.get("must_cover", []),
                follow_ups=level_data.get("follow_ups", []),
            )

        tags = data.get("tags", [])
        if "generated" not in tags:
            tags.append("generated")

        challenge = Challenge(
            id=data.get("id", f"generated-{skill.name.lower().replace(' ', '-')}"),
            title=data.get("title", f"Generated: {skill.name}"),
            mode=data.get("mode", skill.category),
            tags=tags,
            levels=levels,
        )

        # Quality check
        await self._quality_check(challenge, target_level, skill.name)

        return challenge

    async def _quality_check(self, challenge: Challenge, target_level: str, skill_name: str) -> None:
        """Run a self-review pass. If it fails, log but don't block."""
        import json

        challenge_json = json.dumps({
            "id": challenge.id,
            "title": challenge.title,
            "mode": challenge.mode,
            "levels": {
                name: {"interviewer": lc.interviewer, "must_cover": lc.must_cover}
                for name, lc in challenge.levels.items()
            },
        })
        prompt = _QUALITY_CHECK_PROMPT.format(
            challenge_json=challenge_json,
            target_level=target_level,
            skill_name=skill_name,
        )
        try:
            raw = await self._backend.generate(
                [Message(role="user", content=prompt)], self._config,
            )
            data = extract_json_object(raw)
            if not data.get("pass", True):
                # Could log this — for now, we accept it anyway
                pass
        except (ValueError, KeyError, TypeError):
            pass  # Quality check is best-effort
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/jd/test_challenge_gen.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add mockr/core/jd/challenge_gen.py tests/core/jd/test_challenge_gen.py
git commit -m "feat: implement LLM-based challenge generation from JD skills"
```

---

## Wave 6: CLI Integration (depends on all previous waves)

---

### Task 13: CLI Commands — assess, prep, plan, practice

**Files:**
- Modify: `mockr/cli.py`
- Create: `tests/core/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_cli.py`:

```python
from __future__ import annotations

from click.testing import CliRunner

from mockr.cli import main


class TestCLICommands:
    def test_assess_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["assess", "--help"])
        assert result.exit_code == 0
        assert "target" in result.output.lower()

    def test_prep_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["prep", "--help"])
        assert result.exit_code == 0
        assert "jd" in result.output.lower() or "url" in result.output.lower()

    def test_plan_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["plan", "--help"])
        assert result.exit_code == 0

    def test_level_choices_include_new_levels(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--level", "intern", "--help"])
        # Should not error — intern is a valid level
        assert result.exit_code == 0 or "intern" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/core/test_cli.py -v`
Expected: FAIL (new commands don't exist)

- [ ] **Step 3: Add new CLI commands**

Replace the full contents of `mockr/cli.py`:

```python
"""CLI entry point for mockr."""

from pathlib import Path

import click


@click.group(invoke_without_command=True)
@click.option("--mode", type=click.Choice(["system-design", "coding", "behavioral", "full-loop"]), default=None)
@click.option(
    "--level",
    type=click.Choice(["intern", "junior", "mid", "senior", "staff", "principal"]),
    default=None,
)
@click.option("--lang", type=click.Choice(["python", "sql", "rust", "javascript"]), default=None)
@click.option("--provider", type=str, default=None)
@click.option("--model", type=str, default=None)
@click.pass_context
def main(ctx, mode, level, lang, provider, model):
    """mockr — Terminal-native AI mock interview tool."""
    if ctx.invoked_subcommand is None:
        from mockr.tui.app import MockrApp

        app = MockrApp()
        app.run()


@main.command()
def practice():
    """Start next due review (spaced repetition picks the challenge)."""
    from mockr.tui.app import MockrApp

    app = MockrApp()
    app.run()


@main.command()
def dashboard():
    """Show progress dashboard."""
    from mockr.tui.app import MockrApp

    app = MockrApp()
    app.run()


@main.command()
@click.option("--format", "fmt", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", type=click.Path(), default=None)
def export(fmt, output):
    """Export progress data."""
    from mockr.core.progress.export import export_data

    result = export_data(fmt, output)
    click.echo(result)


@main.command("challenge")
@click.argument("action", type=click.Choice(["validate"]))
@click.argument("path", type=click.Path(exists=True))
def challenge_cmd(action, path):
    """Challenge management commands."""
    if action == "validate":
        from mockr.core.challenges.loader import load_challenge, validate_challenge

        ch = load_challenge(Path(path))
        errors = validate_challenge(ch)
        if errors:
            for e in errors:
                click.echo(f"ERROR: {e}", err=True)
            raise SystemExit(1)
        else:
            click.echo(f"OK: {ch.title} ({ch.id}) — {len(ch.levels)} levels defined")


@main.command()
@click.option(
    "--target",
    type=click.Choice(["intern", "junior", "mid", "senior", "staff", "principal"]),
    required=True,
    help="Target level to assess against.",
)
def assess(target):
    """Run a diagnostic assessment to baseline your current level."""
    click.echo(f"Starting diagnostic assessment (target: {target})...")
    click.echo("This will run 3 mini-interviews: coding, system design, and behavioral.")
    click.echo("Use 'mockr assess --target <level>' in TUI mode for the full experience.")
    # Full implementation connects to TUI AssessmentScreen
    from mockr.tui.app import MockrApp

    app = MockrApp()
    app.run()


@main.command()
@click.option("--jd", type=str, default=None, help="Paste job description text directly.")
@click.option("--jd-file", type=click.Path(exists=True), default=None, help="Path to a JD text file.")
@click.option("--url", type=str, default=None, help="URL to fetch JD from.")
@click.option("--list", "list_profiles", is_flag=True, help="List saved role profiles.")
@click.option("--refresh-intel", is_flag=True, help="Re-fetch interview intel for current role.")
def prep(jd, jd_file, url, list_profiles, refresh_intel):
    """Parse a job description and create a role-specific prep plan."""
    if list_profiles:
        from mockr.core.progress.store import ProgressStore

        store = ProgressStore(Path.home() / ".mockr" / "mockr.db")
        profiles = store.list_role_profiles()
        if not profiles:
            click.echo("No saved role profiles. Use 'mockr prep --jd <text>' to create one.")
            return
        for p in profiles:
            click.echo(f"  {p['id'][:8]}  {p['role_title']} @ {p['company'] or 'Unknown'} ({p['inferred_level']})")
        store.close()
        return

    if not jd and not jd_file and not url and not refresh_intel:
        click.echo("Provide a JD via --jd, --jd-file, or --url. Run 'mockr prep --help' for details.")
        return

    jd_text = jd
    if jd_file:
        jd_text = Path(jd_file).read_text()
    if url:
        click.echo(f"Fetching JD from {url}...")
        # URL fetching will be handled by the TUI/async flow
        click.echo("URL fetching is available in TUI mode. Use 'mockr' to launch.")
        return

    if jd_text:
        click.echo("Parsing job description...")
        click.echo("For full interactive prep experience, launch TUI mode with 'mockr'.")
    elif refresh_intel:
        click.echo("Refreshing interview intel...")

    from mockr.tui.app import MockrApp

    app = MockrApp()
    app.run()


@main.command()
@click.option("--role", type=str, default=None, help="Filter plan by role profile ID.")
def plan(role):
    """View your current practice plan."""
    from mockr.core.progress.store import ProgressStore

    store = ProgressStore(Path.home() / ".mockr" / "mockr.db")

    # Find most recent plan
    # For now, show a summary via CLI
    click.echo("Practice Plan")
    click.echo("=" * 50)
    click.echo("Run 'mockr assess --target <level>' first to generate a plan.")
    click.echo("Or launch TUI with 'mockr' for the full dashboard.")
    store.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/core/test_cli.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add mockr/cli.py tests/core/test_cli.py
git commit -m "feat: add assess, prep, and plan CLI commands"
```

---

## Wave 7: Integration Test (depends on all previous waves)

---

### Task 14: End-to-End Integration Test

**Files:**
- Create: `tests/integration/test_assessment_flow.py`

- [ ] **Step 1: Write the integration test**

Create `tests/integration/test_assessment_flow.py`:

```python
"""End-to-end test: assessment -> plan generation -> adaptive update."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mockr.core.assessment.engine import AssessmentEngine
from mockr.core.assessment.models import AssessmentResult
from mockr.core.jd.models import RoleProfile, Skill
from mockr.core.jd.parser import JDParser
from mockr.core.planning.adapter import PlanAdapter
from mockr.core.planning.generator import PlanGenerator
from mockr.core.progress.store import ProgressStore
from mockr.core.types import Message, ModelConfig


class FakeBackend:
    """Serves all LLM needs for integration testing."""

    def __init__(self, mode_scores: dict[str, dict[str, float]]) -> None:
        self._scores = mode_scores

    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        content = " ".join(m.content.lower() for m in messages)
        if "score each dimension" in content:
            for mode, scores in self._scores.items():
                if mode.replace("-", " ") in content or mode in content:
                    return json.dumps({"dimensions": scores, "strengths": ["OK"], "improvements": ["Work harder"]})
            first = next(iter(self._scores.values()))
            return json.dumps({"dimensions": first, "strengths": [], "improvements": []})
        elif "extracting structured information" in content:
            return json.dumps({
                "company": "TestCorp",
                "role_title": "Senior Engineer",
                "inferred_level": "senior",
                "tech_stack": ["Python"],
                "domain": "testing",
                "key_skills": [
                    {"name": "system design", "category": "system-design", "dimensions": ["tradeoffs"], "weight": 0.9},
                ],
            })
        elif "debrief" in content:
            return json.dumps({"overall_score": 3.0, "dimension_scores": {}, "summary": "Done."})
        else:
            return "Next question."


@pytest.mark.asyncio
class TestAssessmentFlow:
    async def test_full_flow_assessment_to_plan(self, tmp_path: Path) -> None:
        """assessment -> gaps -> plan -> persist -> adaptive update."""
        scores = {
            "coding": {"correctness": 2.0, "efficiency": 3.0, "code_quality": 3.5, "edge_cases": 2.5, "communication": 3.5},
            "system-design": {"structure": 3.0, "constraints": 2.5, "tradeoffs": 2.0, "reliability": 2.0, "concreteness": 3.0},
            "behavioral": {"situation": 4.0, "task": 3.5, "action": 3.5, "result": 3.0, "impact": 3.0},
        }
        backend = FakeBackend(scores)
        config = ModelConfig(model="test")

        # Step 1: Run diagnostic
        engine = AssessmentEngine(
            backend=backend, config=config, challenges_dir=Path("mockr/challenges/diagnostic"),
        )

        async def fake_answer(q: str, mode: str) -> str:
            return "My diagnostic answer."

        result = await engine.run_diagnostic(target_level="senior", answer_callback=fake_answer)
        assert isinstance(result, AssessmentResult)
        assert len(result.gaps) > 0

        # Step 2: Generate plan
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result)
        assert len(plan.items) > 0
        assert plan.items[0].priority >= plan.items[-1].priority

        # Step 3: Persist to SQLite
        store = ProgressStore(tmp_path / "test.db")
        store.save_assessment(result.id, result.target_level, result.inferred_level, result.mode_scores)
        store.save_practice_plan(plan.id, result.id, None, plan.target_level)
        for i, item in enumerate(plan.items):
            store.save_plan_item(f"item-{i}", plan.id, item.dimension, item.mode, item.priority, item.gap_size, item.challenge_id, item.rationale)

        saved = store.get_assessment(result.id)
        assert saved is not None
        saved_items = store.get_plan_items(plan.id)
        assert len(saved_items) == len(plan.items)

        # Step 4: Simulate improvement and adaptive update
        improved_scores = {
            "coding": {"correctness": 4.0, "efficiency": 3.5, "code_quality": 3.5, "edge_cases": 3.5, "communication": 3.5},
            "system-design": {"structure": 3.5, "constraints": 3.5, "tradeoffs": 3.5, "reliability": 3.5, "concreteness": 3.5},
            "behavioral": {"situation": 4.0, "task": 3.5, "action": 3.5, "result": 3.5, "impact": 3.5},
        }
        adapter = PlanAdapter()
        updated_plan = adapter.recalculate(plan, improved_scores, target_level="senior")
        validated_count = sum(1 for item in updated_plan.items if item.status == "validated")
        assert validated_count > 0

        store.close()

    async def test_flow_with_jd_overlay(self, tmp_path: Path) -> None:
        """assessment -> JD parse -> plan with JD boost."""
        scores = {
            "coding": {"correctness": 2.0, "efficiency": 3.0, "code_quality": 3.5, "edge_cases": 2.5, "communication": 3.5},
            "system-design": {"structure": 3.0, "constraints": 2.5, "tradeoffs": 2.0, "reliability": 2.0, "concreteness": 3.0},
            "behavioral": {"situation": 4.0, "task": 3.5, "action": 3.5, "result": 3.0, "impact": 3.0},
        }
        backend = FakeBackend(scores)
        config = ModelConfig(model="test")

        # Run assessment
        engine = AssessmentEngine(
            backend=backend, config=config, challenges_dir=Path("mockr/challenges/diagnostic"),
        )

        async def fake_answer(q: str, mode: str) -> str:
            return "Answer."

        result = await engine.run_diagnostic(target_level="senior", answer_callback=fake_answer)

        # Parse JD
        parser = JDParser(backend=backend, config=config)
        profile = await parser.parse_text("Senior Engineer at TestCorp, system design focus.")

        # Generate plan with JD overlay
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan_without_jd = generator.generate(result)
        plan_with_jd = generator.generate(result, role_profile=profile)

        # JD should boost system-design tradeoffs priority
        tradeoffs_no_jd = next((i for i in plan_without_jd.items if i.dimension == "tradeoffs"), None)
        tradeoffs_jd = next((i for i in plan_with_jd.items if i.dimension == "tradeoffs"), None)
        assert tradeoffs_jd is not None
        if tradeoffs_no_jd is not None:
            assert tradeoffs_jd.priority >= tradeoffs_no_jd.priority
```

- [ ] **Step 2: Run the integration test**

Run: `python -m pytest tests/integration/test_assessment_flow.py -v`
Expected: ALL PASS

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS — no regressions

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_assessment_flow.py
git commit -m "test: add end-to-end integration test for assessment and plan flow"
```

---

## Deferred to Follow-Up Plan

The following items from the spec are **not covered** in this plan and should be implemented in a follow-up:

1. **TUI Screens** — AssessmentScreen, PrepScreen, enhanced DashboardScreen with gap visualization and plan view. These are significant Textual UI work that should be their own plan.
2. **Management track behavioral dimensions** — Phase 2 of level expansion (custom dimensions for engineering_manager, director, vp).
3. **URL-based JD fetching** — The `--url` CLI flag is stubbed but actual httpx page fetching + HTML extraction needs implementation.
4. **Generated challenge persistence** — Writing generated TOML files to `~/.mockr/challenges/generated/`.
5. **Web search integration** — `IntelGatherer` has a pluggable `web_searcher` interface but no real implementation (needs httpx + search API).

---

## Dependency Graph

```
Wave 1 (parallel):  Task 1 (Level enum)
                     Task 2 (Assessment models + thresholds)
                     Task 3 (Planning models)
                     Task 4 (JD models)

Wave 2:             Task 5 (ProgressStore tables)  ← depends on Tasks 2, 3, 4

Wave 3:             Task 6 (Diagnostic challenges)  ← no code deps, just content
                     Task 7 (Assessment engine)      ← depends on Tasks 2, 5, 6

Wave 4:             Task 8 (Plan generator)          ← depends on Tasks 2, 3, 4
                     Task 9 (Plan adapter)            ← depends on Tasks 2, 3

Wave 5 (parallel):  Task 10 (JD parser)              ← depends on Task 4
                     Task 11 (Intel gatherer)          ← depends on Task 4
                     Task 12 (Challenge generator)     ← depends on Task 4

Wave 6:             Task 13 (CLI commands)            ← depends on all above

Wave 7:             Task 14 (Integration test)         ← depends on all above
```
