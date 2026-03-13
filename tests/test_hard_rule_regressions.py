import zipfile
from pathlib import Path

from LaborForceScheduler.scheduler_app_v3_final import (
    DAYS,
    Assignment,
    DataModel,
    Employee,
    ManagerGoals,
    RequirementBlock,
    Settings,
    count_coverage_per_tick,
    daily_shift_blocks,
    default_day_rules,
    generate_schedule,
    hours_between_ticks,
    load_data,
    respects_daily_shift_limits,
    respects_max_consecutive_days,
    validate_final_schedule_hard,
)


def _req(day: str, start_t: int, end_t: int, area: str = "CSTORE", min_count: int = 0, preferred_count: int = 0, max_count: int = 1):
    return RequirementBlock(day=day, area=area, start_t=start_t, end_t=end_t, min_count=min_count, preferred_count=preferred_count, max_count=max_count)


def _emp(name: str, **kwargs) -> Employee:
    base = dict(
        name=name,
        work_status="Active",
        wants_hours=True,
        availability=default_day_rules(),
        areas_allowed=["CSTORE"],
        preferred_areas=["CSTORE"],
    )
    base.update(kwargs)
    return Employee(**base)


def _run(model: DataModel, label: str = "2026-03-01"):
    model.settings = Settings(solver_scrutiny_level="Fast")
    assignments, _emp_hours, total_hours, _warnings, _filled, _total, _iters, _restarts, diagnostics = generate_schedule(model, label)
    return assignments, total_hours, diagnostics


def test_optimizer_enforces_staffing_cap():
    model = DataModel(
        employees=[_emp("A"), _emp("B")],
        requirements=[_req("Mon", 0, 48, min_count=0, preferred_count=0, max_count=1)],
    )

    assignments, _total_hours, _diag = _run(model)
    coverage = count_coverage_per_tick(assignments)

    assert assignments
    assert max(coverage.values(), default=0) <= 1


def test_optimizer_enforces_weekly_labor_cap():
    model = DataModel(
        employees=[_emp("A", max_weekly_hours=40.0), _emp("B", max_weekly_hours=40.0)],
        requirements=[_req("Mon", 16, 28, min_count=0, preferred_count=1, max_count=2)],
        manager_goals=ManagerGoals(maximum_weekly_cap=2.0),
    )

    _assignments, total_hours, _diag = _run(model)
    assert total_hours <= 2.0 + 1e-9


def test_participation_repair_respects_min_shift_length():
    model = DataModel(
        employees=[_emp("A", min_hours_per_shift=2.0, max_weekly_hours=6.0)],
        requirements=[_req("Tue", 16, 18, min_count=0, preferred_count=0, max_count=1)],
    )

    assignments, _total_hours, _diag = _run(model)
    blocks = daily_shift_blocks(assignments, "A", "Tue")

    assert all(hours_between_ticks(st, en) >= 2.0 - 1e-9 for st, en in blocks)


def test_participation_repair_respects_max_consecutive_days():
    employee = _emp("A", max_consecutive_days=1)
    baseline = [Assignment(day="Sat", area="CSTORE", start_t=16, end_t=18, employee_name="A", locked=True, source="locked")]

    assert not respects_max_consecutive_days(baseline, employee, "Sun")

    model = DataModel(
        employees=[employee],
        requirements=[
            _req("Sat", 16, 18, min_count=1, preferred_count=1, max_count=1),
            _req("Sun", 16, 18, min_count=0, preferred_count=0, max_count=1),
        ],
    )

    assignments, _total_hours, _diag = _run(model)
    assert all("max-consecutive-days" not in v for v in validate_final_schedule_hard(model, "2026-03-01", assignments))


def test_circular_max_consecutive_days_sat_to_sun_counts_as_consecutive():
    employee = _emp("A", max_consecutive_days=1)
    assigns = [Assignment(day="Sat", area="CSTORE", start_t=18, end_t=20, employee_name="A")]

    assert respects_max_consecutive_days(assigns, employee, "Sun") is False


def test_nd_minor_daily_hour_cap_enforced():
    minor = _emp("Minor", minor_type="MINOR_14_15", max_weekly_hours=40.0)
    model = DataModel(
        employees=[minor],
        requirements=[_req("Mon", 14, 24, min_count=1, preferred_count=1, max_count=1)],
    )

    assignments, _total_hours, _diag = _run(model)
    mon_hours = sum(hours_between_ticks(a.start_t, a.end_t) for a in assignments if a.employee_name == "Minor" and a.day == "Mon")
    assert mon_hours <= 3.0 + 1e-9


def test_nd_minor_weekly_hour_cap_enforced():
    minor = _emp("Minor", minor_type="MINOR_14_15", max_weekly_hours=80.0)
    requirements = [_req(day, 14, 28, min_count=1, preferred_count=1, max_count=1) for day in DAYS]
    model = DataModel(employees=[minor], requirements=requirements)

    assignments, _total_hours, _diag = _run(model)
    weekly = sum(hours_between_ticks(a.start_t, a.end_t) for a in assignments if a.employee_name == "Minor")
    assert weekly <= 18.0 + 1e-9


def test_final_validation_gate_catches_forced_hard_violation():
    employee = _emp("A")
    model = DataModel(
        employees=[employee],
        requirements=[_req("Mon", 16, 20, min_count=0, preferred_count=0, max_count=1)],
    )
    invalid = [
        Assignment(day="Mon", area="CSTORE", start_t=16, end_t=20, employee_name="A"),
        Assignment(day="Mon", area="CSTORE", start_t=17, end_t=19, employee_name="A"),
    ]

    violations = validate_final_schedule_hard(model, "2026-03-01", invalid)

    assert violations
    assert any("rule=overlap" in v for v in violations)


def _load_bundled_dataset_for_tests() -> DataModel:
    repo_root = Path(__file__).resolve().parents[1]
    zip_path = repo_root / "LaborForceScheduler_V3_5_Phase5_E3_M12_EMPLOYEE_LOCKED_PATCH.zip"
    with zipfile.ZipFile(zip_path) as zf:
        data_member = "LaborForceScheduler/data/scheduler_data.json"
        with zf.open(data_member) as fp:
            tmp = repo_root / ".tmp_bundled_dataset_test.json"
            tmp.write_bytes(fp.read())
    try:
        return load_data(str(tmp))
    finally:
        tmp.unlink(missing_ok=True)


def test_bundled_dataset_final_validation_passes():
    model = _load_bundled_dataset_for_tests()
    label = model.week_start_sun or "2026-03-01"

    _assignments, _total_hours, diagnostics = _run(model, label=label)

    assert diagnostics["final_hard_validation_failed"] is False
    assert diagnostics["final_hard_validation_violation_count"] == 0


def test_optimizer_step_mutation_keeps_day_level_hard_rules_safe():
    e1 = _emp("A", split_shifts_ok=False, max_shifts_per_day=1, max_hours_per_shift=4.0)
    e2 = _emp("B", split_shifts_ok=False, max_shifts_per_day=1, max_hours_per_shift=4.0)
    reqs = [
        _req("Wed", 16, 20, min_count=1, preferred_count=1, max_count=1),
        _req("Wed", 20, 24, min_count=1, preferred_count=1, max_count=1),
    ]
    model = DataModel(employees=[e1, e2], requirements=reqs)

    assignments, _total_hours, _diag = _run(model)

    for emp in (e1, e2):
        assert respects_daily_shift_limits(assignments, emp, "Wed")
    violations = validate_final_schedule_hard(model, "2026-03-01", assignments)
    assert all("max-shifts-per-day/split-shift/max-hours-per-shift" not in v for v in violations)
    assert all("rule=max-hours-per-shift" not in v for v in violations)
