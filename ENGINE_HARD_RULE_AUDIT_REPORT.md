# Engine Hard-Rule Audit Report

## Scope and method
- Scope audited: scheduling engine + hard-rule enforcement path only, centered on `LaborForceScheduler/scheduler_app_v3_final.py`.
- Explicitly confirmed wrapper status of `engine/solver.py`.
- Traced rule read paths, generation, optimization, post-processing/repair, and warning-only checks.
- Reproduced actual returned-schedule violations using included dataset.

---

## 1. Engine Architecture Map

## Wrapper vs real engine
- **Wrapper**: `LaborForceScheduler/engine/solver.py` only re-exports `generate_schedule` / `generate_schedule_multi_scenario` from `scheduler_app_v3_final.py`; no hard-rule logic is implemented there.
- **Real implementation**: `LaborForceScheduler/scheduler_app_v3_final.py`.

## Main call flow
1. `generate_schedule_multi_scenario(...)`
   - Clones model, tweaks soft weights, calls `generate_schedule(...)` per scenario.
   - Chooses best by penalty score.
2. `generate_schedule(...)`
   - Builds requirement maps and seeded coverage.
   - Adds locked shifts via `add_assignment(...)`.
   - Greedy MIN fill and preferred fill via `feasible_segment(...)` + `add_best_segment(...)`.
   - Optional local-search optimizer (`step(...)` + `feasible_add(...)`).
   - `prune_short_shift_blocks(...)`.
   - Participation repair block (“if feasible”).
   - Appends warnings (including INFEASIBLE/WARNING/Soft), returns schedule **without strict final pass/fail gate**.

---

## 2. Hard-Rule Trace Matrix

Legend:
- H = enforced as hard-block (candidate rejected)
- W = warning-only (violation allowed in returned schedule)
- S = soft objective/scoring pressure only
- M = missing in that phase

| Rule | Read from data/UI | Generation (greedy/add) | Optimization (`step`/`feasible_add`) | Participation repair block | Post/final handling | Actual status |
|---|---|---|---|---|---|---|
| Employee active status | Employee `work_status` field | H (`is_employee_available`, candidate pool filters) | H (`is_employee_available`) | H (`is_employee_available`) | none | Hard during add phases |
| Areas allowed / qualifications | Employee `areas_allowed` | H (`is_employee_available`, pool filters) | H (`is_employee_available`) | H (iterates `areas_allowed`, availability) | none | Hard during add phases |
| Availability by day | Employee `availability[day]` | H (`is_employee_available`) | H (`is_employee_available`) | H (`is_employee_available`) | manual validator warns | Hard during add phases |
| Weekly overrides / blocked ranges / off-all-day | `weekly_overrides` | H (`is_employee_available`) | H (`is_employee_available`) | H (`is_employee_available`) | manual validator warns | Hard during add phases |
| Clopen / minimum rest | employee `avoid_clopens`, setting `min_rest_hours` | H (`is_employee_available` + `apply_clopen_from`) | H (`is_employee_available`, approximate clopen map) | H (`is_employee_available`) | manual validator warns | Hard during add phases |
| Store/area hours | store info + area hours | H (`is_within_area_hours` inside `is_employee_available`) | H | H | none | Hard during add phases |
| Overlap prevention | assignments | H (`add_assignment` overlap check) | H (`feasible_add` overlap check) | H (`_overlaps_existing`) | manual validator warns | Hard during add phases |
| Max shifts per day | employee `max_shifts_per_day` | H (`respects_daily_shift_limits`) | H for **added candidate only**; no whole-schedule revalidation after mutations | H (`respects_daily_shift_limits`) | manual validator warns | **Leaky in final output** |
| Split-shift permission | employee `split_shifts_ok` | H (`respects_daily_shift_limits`) | H for add checks only | H via daily limits | manual validator warns | **Leaky in final output** |
| Min hours per shift | employee `min_hours_per_shift` | H in `feasible_segment`; final prune also removes short blocks | H (`feasible_add`) | **M** (repair always 1-hour segment, no employee min check) | prune happens **before** this repair | Missing in late repair path |
| Max hours per shift | employee `max_hours_per_shift` (+ double shift flag) | H (`respects_daily_shift_limits`) | H (`feasible_add` uses daily limits) | H (daily limits) | none | Hard during add phases |
| Max consecutive days | employee `max_consecutive_days` | H (`respects_max_consecutive_days`) | H (`feasible_add`) | **M** (not checked in repair) | none | Missing in late repair path |
| Employee max weekly hours | employee `max_weekly_hours` | H (`add_assignment`) | H (`feasible_add`) | H (explicit per-emp check) | manual validator warns | Hard during add phases |
| Weekly labor cap (maximum weekly cap) | manager goals `maximum_weekly_cap` | H in `add_assignment` except explicit infeasible-min override path | **M** in `feasible_add` | H in repair (explicit check) | W (`INFEASIBLE` warning if exceeded) | Not globally hard |
| Requirement max staffing cap | requirement `max_count` -> `max_req` | H in `add_assignment` / `feasible_segment` | **M** in `feasible_add` | H (`_violates_max2`) | W (`WARNING` if max violations) | Not globally hard |
| ND minor time-window rules (start/end) | ND settings + employee minor type | H (`is_employee_available`) | H (`is_employee_available`) | H (`is_employee_available`) | manual validator warns | Hard on segment adds |
| ND minor daily-hour limits | ND settings + scheduled totals | M during construction | M | M | W-only checks appended after full schedule | Warning-only |
| ND minor weekly-hour limits | ND settings + scheduled totals | M during construction | M | M | W-only checks appended after full schedule | Warning-only |

---

## 3. Exact Leak Points

1. **Optimizer add feasibility omits max staffing cap and weekly labor cap**
   - `feasible_add(...)` checks availability/daily/max-consecutive/min-shift/overlap/employee-weekly-hours only.
   - No per-tick `max_req` cap check.
   - No global `maximum_weekly_cap` check.
   - Therefore `step(...)` mutations can insert assignments that are infeasible under these two “hard” caps.

2. **Optimizer mutation does not run full hard-rule validation on resulting schedule**
   - `step(...)` may remove/reassign entries and returns candidate directly.
   - Acceptance uses score/unfilled comparisons; there is no centralized strict hard-rule validator before accepting `best`.
   - This allows structural side-effects (e.g., split-shift/day-limit violations after removals) to persist.

3. **Participation repair (late block) misses several hard rules**
   - Checks availability + daily shift limits + overlap + max staffing + employee weekly max + global weekly cap.
   - Does **not** check:
     - `respects_max_consecutive_days(...)`
     - employee-specific `min_hours_per_shift` (always tests 1-hour slot)
   - Appends assignment directly without full revalidation pass.

4. **No strict final validator gate before return**
   - Final phase emits warnings (`INFEASIBLE`, `WARNING`, `Soft`) but still returns schedule.
   - No single `validate_all_hard_rules(assignments)` that must pass before return.

5. **ND minor daily/weekly limits enforced only as warning text**
   - Daily/weekly hour checks for 14–15 minors occur after all scheduling and only append warning strings.
   - They do not reject or repair violating schedules.

---

## 4. Warning-Only “Hard” Rules

Rules currently handled as warning-only (or infeasible-note-only) at/near return:

- ND minor **daily** hours limits (3h school day / 8h otherwise): warning strings only.
- ND minor **weekly** hours limits (18h school week / 40h non-school): warning strings only.
- Maximum Weekly Labor Cap overage: reported via `INFEASIBLE: exceeded ...` warning, schedule still returned.
- Requirement max-staffing overages: `WARNING: Max staffing exceeded ...` warning, schedule still returned.
- Manual editor uses warnings for most violations; apply can be overridden by user prompt rather than strict block.

---

## 5. Concrete Bug Examples (from included data)

## Repro command
```bash
PYTHONHASHSEED=0 python - <<'PY'
import sys
sys.path.append('LaborForceScheduler')
import scheduler_app_v3_final as m
model=m.load_data('LaborForceScheduler/data/scheduler_data.json')
label=f"Week starting {model.week_start_sun or '2026-03-08'}"
assigns, emp_hours, total_hours, warnings, filled,total,iters,restarts,diag=m.generate_schedule(model,label)
print('warnings', warnings)
for e in model.employees:
    running=[]
    for a in sorted([x for x in assigns if x.employee_name==e.name], key=lambda x:(m.DAYS.index(x.day),x.start_t,x.end_t,x.area)):
        if not m.respects_daily_shift_limits(running,e,a.day,extra=(a.start_t,a.end_t)):
            print('VIOLATION', e.name, a.day, a.area, a.start_t, a.end_t)
        running.append(a)
PY
```

## Observed returned-schedule violations (max_shifts_per_day=1 split-day violations)
- Kris Tegtmeier, Wed: `15:00-20:00` plus `21:00-22:00` (2 blocks).
- Kris Tegtmeier, Thu: `15:00-19:00` plus `21:00-22:00` (2 blocks).
- Emma, Sun: `15:00-18:00` plus `19:00-22:00` (2 blocks).
- Finely, Sat: `09:00-11:00` plus `15:00-17:00` (2 blocks).
- Jaden, Fri: `16:00-19:00` plus `21:00-24:00` (2 blocks).
- Lauren, Sat: `18:00-19:00` plus `21:00-22:00` (2 blocks).
- Kenny, Sun: `13:00-15:00` plus `18:00-19:00` (2 blocks).

These violate per-employee daily shift limits despite being returned as solver output.

---

## 6. Code Excerpts (confirmed issues)

## A) Wrapper-only `engine/solver.py`
```python
from scheduler_app_v3_final import (
    generate_schedule,
    generate_schedule_multi_scenario,
    improve_weak_areas,
)
```
(Confirms real logic is elsewhere.)

## B) `feasible_add(...)` missing max staffing + weekly labor cap checks
```python
def feasible_add(...):
    ...
    if not is_employee_available(...): return False
    if not respects_daily_shift_limits(...): return False
    if not respects_max_consecutive_days(...): return False
    ...
    if hours_now + h > emp.max_weekly_hours + 1e-9:
        return False
    return True
```
No `max_req`/coverage check and no `maximum_weekly_cap` check.

## C) `step(...)` mutations accepted without strict whole-schedule hard-rule gate
```python
nxt = step(cur)
unfilled = compute_unfilled(nxt)
sc = score_assignments(nxt, unfilled)
if sc < cur_score:
    cur, cur_score = nxt, sc
    if sc < best[0]:
        best = (sc, nxt)
```
Selection is score-based; no final `validate_hard_rules(nxt)`.

## D) Late participation repair missing max-consecutive + min-shift checks
```python
if not is_employee_available(...): continue
if not respects_daily_shift_limits(...): continue
if _overlaps_existing(...): continue
if _violates_max2(...): continue
...
if emp_hours.get(e.name, 0.0) + seg_h > e.max_weekly_hours: continue
if max_weekly_cap > 0.0 and ...: continue
...
assignments.append(a)
```
No `respects_max_consecutive_days(...)` and no check that 1-hour slot satisfies employee `min_hours_per_shift` if >1.

## E) ND minor daily/weekly limits are warning-only
```python
if h > 3.0 + 1e-9:
    warnings.append(...)
...
if week_h > 18.0 + 1e-9:
    warnings.append(...)
```
No reject/repair action.

## F) No strict final validator before return
```python
return assignments, emp_hours, total_hours, warnings, ...
```
Warnings can include `INFEASIBLE` yet schedule still returns.

---

## 7. Recommended Fix Strategy (no implementation yet)

Order these changes to minimize regression risk:

1. **Centralize hard-rule validation into one canonical function**
   - Create `validate_assignment_add(...)` for incremental checks (single add).
   - Create `validate_schedule_hard(...)` for full-schedule checks (all assignments).
   - Make all phases call the same logic, not ad-hoc subsets.

2. **Replace duplicated/partial rule checks**
   - Refactor `feasible_segment`, `feasible_add`, and participation candidate checks to call the same incremental validator.
   - Ensure incremental validator includes:
     - max staffing cap (`max_req`)
     - global weekly labor cap
     - max consecutive days
     - min/max shift rules
     - overlap, availability, area/store hours, ND time-window, etc.

3. **Add strict final validation gate before any schedule return**
   - Run `validate_schedule_hard(...)` on final assignments.
   - If violations exist:
     - Either repair iteratively, or
     - mark run infeasible and block return of violating schedule (depending on product decision), but do not silently return as “valid”.

4. **Prevent optimizer and repair phases from reintroducing violations**
   - In optimizer `step(...)`, validate mutated candidate schedule with hard validator before acceptance.
   - In participation repair, enforce max-consecutive and employee min-shift explicitly; after each append, revalidate incrementally.
   - After prune and after participation, rerun strict hard validation.

5. **Decide policy for currently warning-only constraints**
   - Convert ND daily/weekly hours to hard constraints if legally required.
   - If weekly labor cap and max staffing are intended hard constraints, convert from warning-only tail checks to strict rejection/repair logic.

---

## Verification of suspected findings

1. `feasible_add(...)` does **not** enforce per-tick max staffing cap and maximum weekly labor cap: **TRUE**.
2. Participation repair block does **not** enforce max consecutive days, does not enforce employee min-hours-per-shift >1h, and lacks full post-add revalidation: **TRUE**.
3. ND minor daily/weekly hour limits are warning-only: **TRUE**.
4. No single strict final validator gate for returned schedules: **TRUE**.
