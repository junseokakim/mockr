# Assessment & JD-Based Prep — Design Spec

**Date:** 2026-03-27
**Status:** Approved

## Overview

Two complementary features for mockr:

1. **Diagnostic Assessment** — a multi-mode mini-interview that baselines the user's current skill level against a target level, producing a gap report and actionable practice plan.
2. **JD-Based Prep** — an optional overlay where the user provides a job description (paste, file, or URL). mockr extracts a role profile, gathers interview intel via web search, and sharpens the practice plan with role-specific priorities and LLM-generated challenges.

**Architecture: Layered.** Assessment is the foundation (works standalone). JD is an overlay that enriches the plan when provided. The adaptive engine works the same either way.

---

## Section 1: Diagnostic Assessment Engine

**New module:** `mockr/core/assessment/`

### Flow

1. User runs `mockr assess --target senior` (or selects from TUI).
2. mockr runs 3 mini-interviews back-to-back: coding (1 problem), system design (1 problem), behavioral (1 scenario).
3. Each mini is ~10-15 min, shorter than a full session. Uses curated "diagnostic" challenges (separate from the regular bank to avoid tainting spaced repetition data).
4. Scoring uses the existing `Scorer` — same 5 dimensions per mode, same LLM evaluation.
5. Results produce an `AssessmentResult` with per-dimension scores across all 3 modes and an inferred current level.

### Data Model

```
AssessmentResult:
  id: str
  target_level: Level
  inferred_level: Level
  created_at: datetime
  mode_scores: dict[Mode, dict[str, float]]  # e.g. {"coding": {"correctness": 3.2, ...}}
  gaps: list[Gap]  # dimensions where score < target threshold
```

### Gap Detection

Each level has dimension thresholds (e.g., senior coding correctness = 3.5). Anything below is a gap. Thresholds are configurable per level in a new `levels.toml` config file.

### Diagnostic Challenges

Separate TOML files in `challenges/diagnostic/` — one per mode, designed to probe breadth rather than depth. Tagged with `diagnostic = true` so they don't appear in regular practice.

---

## Section 2: Practice Plan Generator

**New module:** `mockr/core/planning/`

### What It Produces

A `PracticePlan` — an ordered list of practice items, each targeting a specific gap, with clear rationale.

```
PracticePlan:
  id: str
  assessment_id: str
  target_level: Level
  role_profile_id: str | None  # linked JD, if any
  created_at: datetime
  items: list[PlanItem]

PlanItem:
  dimension: str          # e.g. "tradeoffs"
  mode: Mode              # system-design
  priority: float         # 0-1, derived from gap size + JD weight
  gap_size: float         # target - current score
  challenge_id: str | None  # existing challenge, or None if LLM-generated
  rationale: str          # "Your tradeoffs score is 2.1, senior needs 3.5"
  status: pending | in_progress | validated
```

### Priority Calculation

- **Base priority** = gap size (bigger gap = higher priority)
- **JD multiplier** = if a JD is loaded, dimensions matching JD-required skills get boosted
- **Interview intel multiplier** = if the company is known to emphasize certain areas, those get boosted further
- **Dependencies** = foundational skills (correctness, structure) get slight priority boost since other skills build on them

### Adaptive Updates

After every completed session:

1. New scores flow in via existing `ProgressStore`.
2. Plan generator recalculates priorities based on updated dimension averages.
3. Items that reach the target threshold move to `validated` status.
4. **Re-assessment triggers** fire when 5+ sessions complete in a gap area without reaching threshold, OR when the rolling average of the last 3 sessions shows < 0.2 improvement (plateau detection). Not scheduled — earned. mockr prompts: "You've done 5 distributed systems sessions — let's do a quick validation round to check real progress." The validation round is a single targeted mini-interview in the gap area (not a full 3-mode diagnostic).

### Plan Presentation

In TUI dashboard or CLI output — shows items sorted by priority, with progress bars per dimension showing current vs. target. `mockr plan` prints it, `mockr practice` auto-picks the highest priority item.

---

## Section 3: JD Parsing & Role Profile

**New module:** `mockr/core/jd/`

### Input Paths

- **Raw paste:** `mockr prep --jd "paste text here"` or paste into TUI prompt
- **File:** `mockr prep --jd-file ./job-description.txt`
- **URL:** `mockr prep --url "https://..."` — fetches page content, extracts JD text

### LLM Extraction

JD text is sent to the LLM, which extracts a structured `RoleProfile`:

```
RoleProfile:
  id: str
  company: str | None
  role_title: str           # "Senior Backend Engineer"
  inferred_level: Level     # mapped to mockr's level enum
  tech_stack: list[str]     # ["Python", "Kubernetes", "PostgreSQL"]
  domain: str | None        # "fintech", "healthcare", etc.
  key_skills: list[Skill]   # extracted with weights
  created_at: datetime
  raw_text: str             # original JD for reference
  interview_intel: InterviewIntel | None

Skill:
  name: str                 # "distributed systems"
  category: Mode            # maps to system-design, coding, behavioral
  dimensions: list[str]     # which scoring dimensions this touches
  weight: float             # how prominent in the JD (0-1)
```

### Connection to the Plan

The plan generator accepts an optional `RoleProfile`. When present:

- `Skill.weight` boosts priority of matching dimensions.
- `InterviewIntel.format` reweights mode distribution (more system design rounds = more system design practice).
- Skills not covered by existing challenges trigger LLM challenge generation.

### Persistence

Role profiles stored in SQLite. User can have multiple (prepping for several roles). `mockr prep --list` shows saved profiles.

---

## Section 4: LLM Challenge Generation

**Lives in:** `mockr/core/jd/challenge_gen.py`

### When It Triggers

During plan generation, after matching JD skills against existing challenge bank. Any skill with no matching challenge gets a generated one.

### Flow

1. Plan generator identifies uncovered skills (e.g., JD asks for "Kubernetes networking" — no challenge in bank).
2. Sends to LLM: skill name + mode + target level + tech stack context from RoleProfile.
3. LLM returns a challenge in the same structure as TOML challenges — problem statement, must_cover items, follow_ups, test cases (for coding).
4. Generated challenge is validated against the `Challenge` schema.
5. Stored as TOML in `~/.mockr/challenges/generated/` so it persists and can be reused.

### Guardrails

- Generated coding challenges include test cases, but they're LLM-authored — flagged as `generated = true` so the user knows tests may need tweaking.
- Generated challenges don't pollute the built-in bank — separate directory, separate tag.
- Cap generation at ~5 challenges per JD to avoid overwhelming the plan.
- **Quality check:** After generation, a quick LLM self-review pass: "Is this challenge solvable, appropriately scoped for {level}, and testing the right skill?" If it fails, regenerate once, then skip with a note.

---

## Section 5: Interview Intel Gathering

**Lives in:** `mockr/core/jd/intel.py`

### When It Triggers

During JD processing, when a company name is identified. Runs in parallel with skill extraction — doesn't block the core flow.

### Flow

1. Extract company name from JD (or user provides it).
2. Run web searches: `"{company} software engineer interview glassdoor"`, `"{company} interview process reddit"`, `"{company} {role} interview blind"`.
3. Collect top results, fetch page content.
4. LLM summarizes raw content into structured `InterviewIntel`:

```
InterviewIntel:
  format: list[str]         # ["phone screen", "2x system design", "behavioral"]
  common_topics: list[str]
  culture_signals: list[str]
  gotchas: list[str]
  sources: list[str]        # URLs where intel was found
```

### Presentation

Shown as a separate section when the user runs `mockr prep` or views the plan in TUI:

```
Interview Intel: Stripe
  Format: Phone screen -> Take-home -> 2x Coding -> System Design -> Cross-functional
  Hot topics: API design, payment state machines, idempotency
  Culture: Strong emphasis on clear communication, they want you to drive the interview
  Watch out: Take-home is timed (3 hrs), system design round is only 30 min
  Sources: glassdoor.com/..., reddit.com/r/cscareerquestions/...
```

### Staleness

Intel is timestamped. If older than 90 days, mockr suggests refreshing. User can manually refresh with `mockr prep --refresh-intel`.

### Graceful Degradation

If web search returns nothing useful (small company, no public data), mockr skips intel and notes "No interview intel found — plan based on JD analysis only." No fake data.

---

## Section 6: Level System Expansion

### Current State

`Level` enum: `mid`, `senior`, `staff`, `principal` (IC-only).

### Expanded Design

```
IC Track:         intern -> junior -> mid -> senior -> staff -> principal
Management Track: engineering_manager -> director -> vp
```

Each level maps to its own dimension thresholds. Management track leans heavier on behavioral dimensions (leadership, stakeholder management) and system design (architecture vision), while de-emphasizing coding.

### Phased Rollout

- **Phase 1 (this build):** Add `intern` and `junior` to IC track. Define dimension thresholds for all IC levels. Management track exists in the enum but is not yet implemented — selecting it shows "Coming soon."
- **Phase 2 (follow-up):** Flesh out management track with custom behavioral dimensions (leadership, conflict_resolution, stakeholder_management, strategic_thinking, team_development) replacing the STAR-based ones.

### JD Level Mapping

The LLM maps the JD's role title to the closest level. "Junior Software Engineer" -> `junior`, "Engineering Manager" -> `engineering_manager`. User can override if the inference is wrong.

---

## Section 7: CLI & TUI Integration

### New CLI Commands

- `mockr assess --target senior` — run diagnostic assessment
- `mockr prep --jd "text"` / `--jd-file path` / `--url "https://..."` — parse JD, create role profile
- `mockr prep --list` — list saved role profiles
- `mockr plan` — view current practice plan (with gaps + priorities)
- `mockr plan --role <profile-id>` — view plan filtered by a specific JD
- `mockr practice` — auto-pick highest priority item from plan and start a session
- `mockr prep --refresh-intel` — re-fetch interview intel for current role

### TUI Changes

- **HomeScreen** gets two new options: "Take Assessment" and "Prep for Role"
- **New AssessmentScreen** — guides user through the 3 mini-interviews, shows progress ("Coding 1/1 -> System Design 1/1 -> Behavioral 1/1")
- **New PrepScreen** — JD input (paste or file path), shows extracted RoleProfile for confirmation, kicks off intel gathering
- **Enhanced DashboardScreen** — adds gap visualization (current vs. target per dimension), practice plan view, interview intel panel if a role is loaded
- **Existing interview screens unchanged** — they receive challenges from the plan instead of manual selection

### User Flow

```
New user:     assess -> see gaps -> (optionally) prep with JD -> plan generated -> practice
Returning:    mockr practice -> picks next priority item -> session -> plan updates
```

---

## Section 8: Data & Persistence

### New SQLite Tables

```sql
-- Assessment results
CREATE TABLE assessments (
  id TEXT PRIMARY KEY,
  target_level TEXT NOT NULL,
  inferred_level TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  mode_scores TEXT NOT NULL  -- JSON blob
);

-- Role profiles from JD parsing
CREATE TABLE role_profiles (
  id TEXT PRIMARY KEY,
  company TEXT,
  role_title TEXT NOT NULL,
  inferred_level TEXT NOT NULL,
  tech_stack TEXT,         -- JSON array
  domain TEXT,
  key_skills TEXT,         -- JSON array of Skill objects
  interview_intel TEXT,    -- JSON blob, nullable
  raw_text TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);

-- Practice plans (one active per target level + optional role)
CREATE TABLE practice_plans (
  id TEXT PRIMARY KEY,
  assessment_id TEXT REFERENCES assessments(id),
  role_profile_id TEXT REFERENCES role_profiles(id),
  target_level TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

-- Individual plan items
CREATE TABLE plan_items (
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

### Relationship to Existing Tables

Sessions and turn_scores stay as-is. The plan generator reads from `challenge_stats` and `dimension_stats` to compute gaps. After each session, the existing score-writing path triggers a plan recalculation.

### Migration

New tables only, no changes to existing schema. Backward compatible — users without assessments or plans see the same experience as today.

---

## New Module Summary

| Module | Purpose |
|--------|---------|
| `mockr/core/assessment/` | Diagnostic engine — runs mini-interviews, produces AssessmentResult |
| `mockr/core/planning/` | Practice plan generator — gap analysis, priority calculation, adaptive updates |
| `mockr/core/jd/` | JD parser, role profile extraction, challenge generation, interview intel |
| `challenges/diagnostic/` | Curated diagnostic challenges (separate from practice bank) |

## Dependencies on Existing Modules

| Existing Module | How It's Used |
|----------------|---------------|
| `core/scoring/scorer.py` | Assessment uses same scoring pipeline |
| `core/sessions/orchestrator.py` | Assessment runs mini-sessions through existing orchestrator |
| `core/challenges/loader.py` | Extended to load diagnostic + generated challenges |
| `core/progress/store.py` | Extended with new tables; plan reads from existing stats |
| `core/types.py` | Level enum expanded with intern, junior + management track placeholders |
| `tui/screens/dashboard.py` | Enhanced with gap visualization + plan view |
