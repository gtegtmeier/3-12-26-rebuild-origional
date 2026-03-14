#!/usr/bin/env python3
import argparse, cProfile, importlib.util, json, pstats, signal, sys, time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict


def load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location("scheduler_app_v3_final", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def timed_wrapper(name: str, fn, acc: Dict[str, Dict[str, float]], run_state: Dict[str, float], cutoff_s: float):
    def wrapped(*args, **kwargs):
        if cutoff_s > 0 and (time.perf_counter() - run_state["t0"]) >= cutoff_s:
            raise TimeoutError(f"Profiling cutoff reached at {cutoff_s}s inside {name}")
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            dt = time.perf_counter() - t0
            acc[name]["calls"] += 1
            acc[name]["total_s"] += dt
    return wrapped


def install_wrappers(mod, acc, run_state, cutoff_s):
    targets = ["generate_schedule", "generate_schedule_multi_scenario", "count_coverage_per_tick", "evaluate_schedule_hard_rules", "build_requirement_maps", "compute_requirement_shortfalls", "schedule_score", "_schedule_total_penalty"]
    originals = {}
    for name in targets:
        if hasattr(mod, name):
            original = getattr(mod, name)
            originals[name] = original
            setattr(mod, name, timed_wrapper(name, original, acc, run_state, cutoff_s))
    return originals


def call_generation(mod, model, label: str):
    prev_label, prev_tick_map = mod.load_prev_final_schedule_tick_map(label)
    if not prev_tick_map:
        prev_label, prev_tick_map = mod.load_last_schedule_tick_map()
    if bool(getattr(model.settings, "enable_multi_scenario_generation", True)):
        entry = "generate_schedule_multi_scenario"
        result = mod.generate_schedule_multi_scenario(model, label, prev_tick_map=prev_tick_map)
    else:
        entry = "generate_schedule"
        result = mod.generate_schedule(model, label, prev_tick_map=prev_tick_map)
    return entry, prev_label, result


def get_top_stats(pr, total_runtime_s: float, limit: int = 25):
    s = pstats.Stats(pr)
    rows = []
    for func, (cc, nc, tt, ct, _callers) in s.stats.items():
        filename, lineno, funcname = func
        if 'scheduler_app_v3_final.py' not in filename or ct <= 0:
            continue
        rows.append({"func": f"{funcname} ({Path(filename).name}:{lineno})", "call_count": int(nc), "cumtime_s": float(ct), "avg_ms": (ct/nc*1000.0) if nc else 0.0, "pct_total": (ct/total_runtime_s*100.0) if total_runtime_s else 0.0})
    rows.sort(key=lambda r: r["cumtime_s"], reverse=True)
    return rows[:limit]



def format_assignments(mod, assigns):
    rows=[]
    day_idx={d:i for i,d in enumerate(mod.DAYS)}
    for a in assigns:
        rows.append({
            "day": a.day,
            "area": a.area,
            "start": mod.tick_to_hhmm(a.start_t),
            "end": mod.tick_to_hhmm(a.end_t),
            "employee": a.employee_name,
            "hours": float(mod.hours_between_ticks(a.start_t, a.end_t)),
        })
    rows.sort(key=lambda r: (day_idx.get(r["day"], 99), r["area"], r["start"], r["employee"]))
    return rows


def employee_summary(rows):
    out={}
    for r in rows:
        e=r['employee']
        d=out.setdefault(e,{"employee":e,"total_hours":0.0,"shift_count":0,"areas":set()})
        d['total_hours'] += r['hours']
        d['shift_count'] += 1
        d['areas'].add(r['area'])
    res=[]
    for e in sorted(out):
        d=out[e]
        res.append({"employee":e,"total_hours":round(d['total_hours'],2),"shift_count":d['shift_count'],"areas":sorted(d['areas'])})
    return res


def uncovered_blocks(mod, model, assigns):
    cov=mod.count_coverage_per_tick(assigns)
    min_req, _pref, _mx = mod.build_requirement_maps(model.requirements, goals=getattr(model,'manager_goals',None), store_info=getattr(model,'store_info',None))
    out=[]
    for (day, area, t), req in min_req.items():
        cur=int(cov.get((day, area, t),0))
        if cur < int(req):
            out.append({"day":day,"area":area,"start":mod.tick_to_hhmm(t),"end":mod.tick_to_hhmm(t+1),"required":int(req),"scheduled":cur,"short":int(req-cur)})
    day_idx={d:i for i,d in enumerate(mod.DAYS)}
    out.sort(key=lambda r:(day_idx.get(r['day'],99),r['area'],r['start']))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="LaborForceScheduler/scheduler_app_v3_final.py")
    ap.add_argument("--data", default="LaborForceScheduler/data/scheduler_data.json")
    ap.add_argument("--label", default="Week starting 2026-03-08 (Sun-Sat)")
    ap.add_argument("--cutoff", type=float, default=120.0)
    ap.add_argument("--output", default="profiling_report.json")
    ap.add_argument("--scrutiny")
    ap.add_argument("--scenario-count", type=int)
    ap.add_argument("--multi", choices=["true", "false"])
    args = ap.parse_args()

    mod = load_module(Path(args.module).resolve())
    model = mod.load_data(args.data)
    if args.scrutiny: model.settings.solver_scrutiny_level = args.scrutiny
    if args.scenario_count is not None: model.settings.scenario_schedule_count = args.scenario_count
    if args.multi is not None: model.settings.enable_multi_scenario_generation = (args.multi == "true")

    acc = defaultdict(lambda: {"calls": 0, "total_s": 0.0})
    run_state = {"t0": time.perf_counter()}
    originals = install_wrappers(mod, acc, run_state, args.cutoff)

    timeout_message = f"Profiling cutoff reached at {args.cutoff}s"
    def _timeout_handler(_sig, _frame):
        raise TimeoutError(timeout_message)
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(max(1, int(args.cutoff)))

    profiler = cProfile.Profile(); profiler.enable()
    entry = None; prev_label = None; result = None; err = None; timed_out = False
    try:
        entry, prev_label, result = call_generation(mod, model, args.label)
    except TimeoutError as ex:
        timed_out = True; err = str(ex)
    except Exception as ex:
        err = f"{type(ex).__name__}: {ex}"
    finally:
        signal.alarm(0)
        profiler.disable()
        for n, fn in originals.items(): setattr(mod, n, fn)
    runtime = time.perf_counter() - run_state["t0"]

    report: Dict[str, Any] = {
        "status": "success" if result is not None else ("timeout" if timed_out else "failed"),
        "entrypoint": entry,
        "runtime_s": runtime,
        "timed_out": timed_out,
        "error": err,
        "label": args.label,
        "previous_label": prev_label,
        "timers": {k: {"calls": int(v["calls"]), "total_s": float(v["total_s"])} for k, v in acc.items()},
        "top_profile": get_top_stats(profiler, runtime),
    }
    if result is not None:
        assigns, emp_hours, total_hours, warnings, filled, total_slots, iters_done, restarts_done, diag = result
        rows = format_assignments(mod, assigns)
        hard = mod.evaluate_schedule_hard_rules(model, args.label, assigns, include_override_warnings=True)
        report["totals"] = {"assignments": len(assigns), "total_hours": total_hours, "filled": filled, "total_slots": total_slots, "iters": iters_done, "restarts": restarts_done}
        report["warnings"] = warnings
        report["diagnostics"] = diag
        report["assignments"] = rows
        report["employee_summary"] = employee_summary(rows)
        report["uncovered_blocks"] = uncovered_blocks(mod, model, assigns)
        report["hard_rule_violations"] = [{"employee":v.employee_name,"day":v.day,"rule":v.rule,"details":v.details,"severity":v.severity} for v in hard]

    Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({"status": report["status"], "runtime_s": runtime, "error": err, "output": args.output}, indent=2))


if __name__ == '__main__':
    main()
