# Engine Hard-Rule Repair Blueprint

This blueprint is derived from the confirmed findings in `ENGINE_HARD_RULE_AUDIT_REPORT.md` and is intended to drive implementation with minimal regression risk.

## 1. Repair Strategy Overview

## Primary objective
Stop illegal schedules from being produced, while preserving current scoring/optimization behavior except where required to prevent hard-rule violations.

## Why order matters
Patching isolated symptoms (e.g., only `feasible_add`) is risky because rule checks are currently duplicated and inconsistent across:
- generation (`feasible_segment`, `add_assignment`),
- optimization (`feasible_add`, `step`),
- participation repair,
- warning-only tail checks.

A symptom-only fix can create new mismatches and make future maintenance harder. The safest path is:
1. close highest-impact leak points,
2. introduce shared hard-rule validator APIs,
3. route all mutation paths through those APIs,
4. add one final strict validation gate.

## Safest order of operations
1. **Leak closure in optimizer/repair path first** (smallest surgical fixes that stop known bypasses).
2. **Centralize validation logic** (eliminate drift across functions).
3. **Convert warning-only legal limits to enforceable hard checks where required** (ND daily/weekly).
4. **Add strict final pre-return hard validation** (single source of truth for returned legality).
5. **Cleanup + diagnostics alignment** (remove duplicate checks, improve reason reporting).

---

## 2. Centralized Hard-Rule Validation Design

## Design goals
- Single canonical hard-rule logic for both incremental checks and full-schedule validation.
- Machine-readable reason codes + human-readable messages.
- Reusable from generation, optimizer, participation repair, and final gate.

## Proposed data structures
```python
@dataclass
class HardRuleViolation:
    code: str                  # e.g. "MAX_STAFFING_CAP", "MAX_CONSEC_DAYS"
    severity: str              # "hard" or "soft"
    employee_name: str = ""
    day: str = ""
    area: str = ""
    start_t: int = 0
    end_t: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    message: str = ""

@dataclass
class HardRuleCheckResult:
    ok: bool
    violations: List[HardRuleViolation] = field(default_factory=list)
```

## Proposed function set

### A) Incremental candidate check (single add)
```python
def validate_assignment_hard(
    model: DataModel,
    label: str,
    candidate: Assignment,
    assignments: List[Assignment],
    emp_hours: Dict[str, float],
    total_labor_hours: float,
    coverage: Dict[Tuple[str, str, int], int],
    max_req: Dict[Tuple[str, str, int], int],
    clopen_min_start: Dict[Tuple[str, str], int],
    *,
    enforce_weekly_labor_cap: bool = True,
    allow_locked_exceptions: bool = False,
    context: str = "solver",   # "solver" | "optimizer" | "participation" | "locked"
) -> HardRuleCheckResult:
    ...
```
Checks included:
- active status
- area allowed
- store/area hours
- availability + weekly overrides + off-all-day + blocked ranges
- clopen/min rest
- overlap
- daily shift limits (max shifts/day + split-shift policy + max shift length)
- max consecutive days
- min shift length
- employee max weekly hours
- weekly labor cap
- per-tick max staffing cap
- ND minor time-window constraints

### B) Full-schedule strict validator (global gate)
```python
def validate_schedule_hard(
    model: DataModel,
    label: str,
    assignments: List[Assignment],
    *,
    enforce_weekly_labor_cap: bool = True,
    enforce_nd_daily_weekly_limits: bool = True,
    include_locked_exceptions_as_violations: bool = True,
) -> HardRuleCheckResult:
    ...
```
Checks included:
- all per-assignment checks via deterministic replay
- global caps and aggregate constraints:
  - requirement max staffing cap
  - weekly labor cap
  - ND daily/weekly limits
  - per-employee max weekly hours
- no warning-only fallback for hard rules (violations returned as hard failures)

### C) Helper reason formatting
```python
def format_hard_rule_violation(v: HardRuleViolation) -> str:
    ...

def summarize_hard_rule_violations(violations: List[HardRuleViolation], max_items: int = 20) -> List[str]:
    ...
```

## Existing functions that must call the shared validator
- `add_assignment(...)` (replace direct ad-hoc checks with validator call).
- `feasible_segment(...)` (delegate to incremental validator in dry-run mode).
- `feasible_add(...)` (same as above; includes missing max staffing + weekly labor cap checks).
- participation repair candidate scan block (replace subset check chain with validator call).
- optimizer acceptance path (`step` consumer loop): validate candidate schedule before accepting as `cur`/`best`.
- final return path in `generate_schedule(...)`: strict `validate_schedule_hard(...)` gate.

---

## 3. Phase-by-Phase Implementation Plan

## Phase 1 — Optimizer + repair leak closure (fast risk reduction)
**Functions to edit**:
- `feasible_add(...)`
- optimizer acceptance loop around `nxt = step(cur)`
- participation repair block (the 1-hour segment selection/add path)

**Behavior changes**:
- `feasible_add(...)` must enforce:
  - per-tick max staffing cap,
  - maximum weekly labor cap.
- participation repair must enforce:
  - `respects_max_consecutive_days(...)`,
  - employee `min_hours_per_shift` (do not place 1-hour shift if min > 1 unless segment length adjusted).
- optimizer acceptance must reject mutated schedules that fail strict hard validation.

**Do not change**:
- score weights, penalty formula, scenario scoring logic.

**Regression risk**: Medium-low.
- May reduce coverage in edge cases previously relying on illegal placements.

## Phase 2 — Central validator integration
**Functions to edit**:
- `add_assignment(...)`
- `feasible_segment(...)`
- `feasible_add(...)`
- participation repair candidate checks
- optionally add helper functions near constraint-check section

**Behavior changes**:
- Route assignment legality checks through `validate_assignment_hard(...)`.
- Remove duplicated branches where equivalent.

**Do not change**:
- candidate ranking (`candidate_score(...)`),
- scenario variant tuning.

**Regression risk**: Medium.
- Major control-flow touch, mitigated by phase-by-phase tests.

## Phase 3 — ND minor daily/weekly hard-limit enforcement
**Functions to edit**:
- post-solve ND block currently appending warnings
- `validate_schedule_hard(...)`

**Behavior changes**:
- Move ND daily/weekly checks into hard validation path.
- Keep warning text generation for UI visibility, but derive from hard violations.

**Do not change**:
- existing ND time-window rules in `is_employee_available(...)`.

**Regression risk**: Medium-high (legal-rule strictness can increase infeasible outcomes).

## Phase 4 — Final strict validation gate
**Functions to edit**:
- end of `generate_schedule(...)` before return
- `generate_schedule_multi_scenario(...)` if needed to react to strict-fail result

**Behavior changes**:
- Run `validate_schedule_hard(...)` on final assignments.
- If violations exist, mark scenario infeasible with explicit structured diagnostics.
- Never return a “clean” schedule that violates hard rules.

**Do not change**:
- multi-scenario ranking mechanics beyond adding hard-validity gate criteria.

**Regression risk**: Medium.

## Phase 5 — Cleanup, deduplication, and diagnostics
**Functions to edit**:
- remove/trim redundant ad-hoc checks once shared validator is trusted.
- improve warnings/diagnostics serialization.

**Behavior changes**:
- unify violation code vocabulary.
- surface top-N actionable violations in warnings/diagnostics.

**Do not change**:
- optimizer objective design.

**Regression risk**: Low (post-stabilization cleanup).

---

## 4. Rule Coverage Matrix (target state after repair)

| Rule | Assignment-time check | Optimization-time recheck | Repair-time recheck | Final strict validation |
|---|---|---|---|---|
| Employee active status | `validate_assignment_hard` | `validate_assignment_hard` + candidate strict gate | `validate_assignment_hard` | `validate_schedule_hard` |
| Areas allowed | same | same | same | same |
| Availability by day | same | same | same | same |
| Weekly overrides/off-all-day/blocked | same | same | same | same |
| Clopen/min rest | same | same | same | same |
| Store/area hours | same | same | same | same |
| Overlap prevention | same | same | same | same |
| Max shifts/day | same | same | same | same |
| Split-shift permission | same | same | same | same |
| Min hours/shift | same | same | same | same |
| Max hours/shift | same | same | same | same |
| Max consecutive days | same | same | same | same |
| Employee max weekly hours | same | same | same | same |
| Weekly labor cap | same (`enforce_weekly_labor_cap`) | same | same | same |
| Requirement max staffing cap | same (coverage + max_req) | same | same | same |
| ND minor time-window rules | same | same | same | same |
| ND minor daily-hour limits | n/a (aggregate) | n/a | n/a | `validate_schedule_hard` hard fail |
| ND minor weekly-hour limits | n/a (aggregate) | n/a | n/a | `validate_schedule_hard` hard fail |

---

## 5. Detailed Edit Plan (code locations)

## A) `add_assignment(...)`
- Replace current hand-built rule chain with:
  1. call `validate_assignment_hard(...)`;
  2. handle locked exception policy explicitly;
  3. apply mutation only when result is `ok` or explicitly allowed locked exception.
- Preserve side effects only after legality pass:
  - append assignment,
  - update `emp_day_segments`, `emp_hours`, `total_labor_hours`, `coverage`, `clopen_min_start`.

## B) `feasible_segment(...)`
- Convert to lightweight wrapper around `validate_assignment_hard(...)` with a constructed candidate assignment and current state snapshots.
- Keep return type bool to avoid large call-site changes in first pass.

## C) `feasible_add(...)`
- Replace with shared incremental validator call.
- Ensure inputs include current coverage and total weekly labor hours context.
- This is where missing max staffing and weekly labor cap leak must be eliminated.

## D) Optimizer mutation/swap helpers (`step(...)` and acceptance loop)
- Keep mutation generation logic unchanged.
- Before accepting `nxt` schedule as `cur` or `best`, run strict schedule validation.
- If invalid: reject candidate regardless of score.

## E) Participation repair block
- Replace ad-hoc chain with `validate_assignment_hard(...)`.
- Compute repair segment length based on employee `min_hours_per_shift` (or skip employee if infeasible under hard rules).
- Revalidate each accepted participation insert incrementally and preserve diagnostics reasons when skipped.

## F) Warning-only ND minor checks
- Move rule computation into `validate_schedule_hard(...)` as hard failures.
- Leave warning messages as derived views of violations for UI.

## G) Post-solve/final validation location
- Immediately before final return in `generate_schedule(...)`:
  - run `validate_schedule_hard(...)`.
  - if violations:
    - add `INFEASIBLE` summary + top violations in warnings,
    - set diagnostics keys (`hard_validation_failed`, `hard_violation_count`, `hard_violation_codes`),
    - enforce no “valid” path for violating schedules.

---

## 6. Test Plan

Implement tests around deterministic miniature models (unit-style) plus one integration run on included scheduler data.

## A) Max shifts per day
- **Positive**: employee with `max_shifts_per_day=2` accepts two separated blocks.
- **Negative**: employee with `max_shifts_per_day=1` rejects second non-touching block.

## B) Split-shift disallow
- **Positive**: touching intervals merge as one contiguous block when `split_shifts_ok=False`.
- **Negative**: separated second block rejected when `split_shifts_ok=False`.

## C) Overlap prevention
- **Positive**: adjacent non-overlapping assignments accepted.
- **Negative**: overlapping assignment rejected.

## D) Max consecutive days
- **Positive**: up to limit allowed.
- **Negative**: adding day beyond limit rejected in generation, optimizer, and participation repair.

## E) Employee max weekly hours
- **Positive**: assignment up to cap allowed.
- **Negative**: assignment that exceeds cap rejected.

## F) Weekly labor cap
- **Positive**: schedule under cap passes final strict validation.
- **Negative**: added assignment over cap rejected; forced overage flagged as hard validation fail (or explicit infeasible mode according to policy).

## G) Requirement max staffing cap
- **Positive**: coverage at max cap accepted.
- **Negative**: extra assignment over per-tick cap rejected in generation/optimizer/repair.

## H) ND minor daily/weekly caps
- **Positive**: minor schedule within daily/weekly limits passes.
- **Negative**: exceed 3h school day / 18h school week fails strict validation.

## I) Clopen/rest rules
- **Positive**: next-day assignment after sufficient rest accepted.
- **Negative**: starts before computed min-rest threshold rejected.

## J) Min shift length
- **Positive**: assignment at or above `min_hours_per_shift` accepted.
- **Negative**: shorter assignment rejected across generation/optimizer/repair.

## K) Max shift length
- **Positive**: assignment within `max_hours_per_shift` accepted.
- **Negative**: longer contiguous block rejected.

## L) Integration regression on included data
- Run deterministic solve (`PYTHONHASHSEED=0`) and assert:
  - no returned hard-rule violations under strict validator,
  - warnings reflect true infeasible causes only,
  - no false “valid” schedule with hard breaches.

---

## 7. Safe Implementation Order (PR strategy)

## Recommendation: several smaller PRs (not one large PR)
Use **4–5 focused PRs**:
1. PR1: leak closure in optimizer + participation (no architecture refactor yet).
2. PR2: introduce shared validator + integrate into `add_assignment`/`feasible_*`.
3. PR3: ND daily/weekly hard enforcement + diagnostics updates.
4. PR4: final strict validation gate + multi-scenario handling of hard invalidity.
5. PR5 (optional): cleanup/deduplication and test hardening.

## Why multiple PRs is safer
- Isolates risk and makes regressions attributable.
- Enables quick rollback of one phase without losing unrelated fixes.
- Simplifies validation and code review for each defect class.
- Prevents accidental optimization/scoring drift while enforcing legality.

---

## Non-goals (to avoid scope creep)
- No UI redesign.
- No overhaul of scoring math or manager goal weighting.
- No behavior changes unrelated to hard-rule legality.
- No broad architectural migration outside scheduler hard-rule path.
