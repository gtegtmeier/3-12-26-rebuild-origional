#!/usr/bin/env python3
import argparse
import copy
import json
import os
import random
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict

sys.path.append('LaborForceScheduler')
import scheduler_app_v3_final as sched




def resolve_data_path(data_arg):
    if data_arg and os.path.exists(data_arg):
        return data_arg

    if data_arg and '::' in data_arg:
        zip_path, member = data_arg.split('::', 1)
        if os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path) as zf:
                with zf.open(member) as src:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                    tmp.write(src.read())
                    tmp.flush()
                    tmp.close()
                    return tmp.name

    zip_default = 'LaborForceScheduler_V3_5_Phase5_E3_M12_EMPLOYEE_LOCKED_PATCH.zip'
    zip_member = 'LaborForceScheduler/data/scheduler_data.json'
    if data_arg in (None, '', 'auto') and os.path.exists(zip_default):
        with zipfile.ZipFile(zip_default) as zf:
            with zf.open(zip_member) as src:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                tmp.write(src.read())
                tmp.flush()
                tmp.close()
                return tmp.name

    return data_arg

def max_consecutive_info(assignments, employee):
    lim = int(getattr(employee, 'max_consecutive_days', 0) or 0)
    if lim <= 0:
        return {"limit": lim, "max_run": 0, "runs": [], "violates": False}
    worked = {a.day for a in assignments if a.employee_name == employee.name and a.day in sched.DAYS}
    flags = [d in worked for d in sched.DAYS]
    if not any(flags):
        return {"limit": lim, "max_run": 0, "runs": [], "violates": False}

    doubled = flags + flags
    runs = []
    i = 0
    while i < len(doubled):
        if not doubled[i]:
            i += 1
            continue
        j = i
        while j < len(doubled) and doubled[j]:
            j += 1
        length = j - i
        if i < len(sched.DAYS):
            runs.append((i, min(length, len(sched.DAYS))))
        i = j

    max_run = max((r[1] for r in runs), default=0)
    violating_runs = [(st, ln) for st, ln in runs if ln > lim]
    return {
        "limit": lim,
        "max_run": max_run,
        "runs": violating_runs,
        "violates": bool(violating_runs),
    }


def summarize(assignments, model, label):
    by_emp_day = defaultdict(list)
    for a in assignments:
        by_emp_day[(a.employee_name, a.day)].append(a)

    violations = []
    for e in model.employees:
        info = max_consecutive_info(assignments, e)
        if not info["violates"]:
            continue
        worked_days = [d for d in sched.DAYS if any(x.employee_name == e.name and x.day == d for x in assignments)]

        viol_days = set()
        chains = []
        for st, ln in info["runs"]:
            chain = [sched.DAYS[(st + k) % len(sched.DAYS)] for k in range(ln)]
            chains.append(chain)
            viol_days.update(chain)

        chain_assignments = [a for a in assignments if a.employee_name == e.name and a.day in viol_days]
        src_counts = Counter((a.source or "") for a in chain_assignments)
        locked_count = sum(1 for a in chain_assignments if bool(getattr(a, 'locked', False)))

        violations.append({
            "employee": e.name,
            "limit": info["limit"],
            "max_run": info["max_run"],
            "worked_days": worked_days,
            "chains": chains,
            "source_counts": dict(src_counts),
            "locked_in_chain": locked_count,
            "assignments": [
                {
                    "day": a.day,
                    "area": a.area,
                    "start": sched.tick_to_hhmm(a.start_t),
                    "end": sched.tick_to_hhmm(a.end_t),
                    "source": a.source,
                    "locked": bool(a.locked),
                }
                for a in sorted(chain_assignments, key=lambda x: (sched.DAYS.index(x.day), x.start_t, x.end_t, x.area))
            ],
        })

    phase_counter = Counter()
    for v in violations:
        if v["locked_in_chain"] > 0:
            phase_counter["locked_shifts"] += 1
        for src, n in v["source_counts"].items():
            if src in ("participation",):
                phase_counter["participation_repair"] += n
            elif src in ("solver",):
                phase_counter["greedy_or_optimizer_solver"] += n
            elif src in ("recurring_locked", "fixed_locked"):
                phase_counter["locked_shifts"] += n
            else:
                phase_counter[f"other:{src or 'unknown'}"] += n

    return {
        "label": label,
        "violation_count": len(violations),
        "violations": violations,
        "phase_signal": dict(phase_counter),
    }


def run_once(model, label, seed, optimizer_iterations=None):
    random.seed(seed)
    m = copy.deepcopy(model)
    if optimizer_iterations is not None:
        m.settings.optimizer_iterations = int(optimizer_iterations)
    assigns, *_rest = sched.generate_schedule(m, label)
    return assigns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='auto',
                    help="Path to scheduler_data.json. Also supports ZIP::member syntax; default auto-loads from the bundled project ZIP.")
    ap.add_argument('--label', default='')
    ap.add_argument('--seed', type=int, default=0)
    args = ap.parse_args()

    resolved_data = resolve_data_path(args.data)
    try:
        model = sched.load_data(resolved_data)
    except FileNotFoundError:
        print(f"ERROR: data file not found: {args.data}")
        if resolved_data != args.data:
            print(f"Resolved path attempted: {resolved_data}")
        print("Pass --data with the included dataset path and rerun.")
        raise SystemExit(2)
    label = args.label or f"Week starting {model.week_start_sun or '2026-03-08'}"

    baseline_assigns = run_once(model, label, args.seed, optimizer_iterations=0)
    full_assigns = run_once(model, label, args.seed, optimizer_iterations=model.settings.optimizer_iterations)

    baseline = summarize(baseline_assigns, model, label)
    full = summarize(full_assigns, model, label)

    baseline_keys = {
        (v['employee'], tuple(tuple(c) for c in v['chains']))
        for v in baseline['violations']
    }
    full_keys = {
        (v['employee'], tuple(tuple(c) for c in v['chains']))
        for v in full['violations']
    }

    print('=== MAX CONSECUTIVE DAYS TRACE ===')
    print(f"data={args.data}")
    print(f"resolved_data={resolved_data}")
    print(f"label={label}")
    print(f"seed={args.seed}")
    print(f"optimizer_iterations(full)={model.settings.optimizer_iterations}")
    print(f"baseline_iterations=0 violations={baseline['violation_count']}")
    print(f"full_iterations={model.settings.optimizer_iterations} violations={full['violation_count']}")
    print()
    print('Phase signals (full run):')
    print(json.dumps(full['phase_signal'], indent=2))
    print()

    new_after_optimizer = sorted(full_keys - baseline_keys)
    if new_after_optimizer:
        print('Likely optimizer-introduced violation chains:')
        for emp, chains in new_after_optimizer:
            print(f"  - {emp}: {list(chains)}")
    else:
        print('No new chains appeared only after optimizer (same seed); check locked/greedy paths.')
    print()

    for v in full['violations']:
        print(f"EMPLOYEE={v['employee']} limit={v['limit']} max_run={v['max_run']} worked={v['worked_days']}")
        print(f"  chains={v['chains']}")
        print(f"  source_counts={v['source_counts']} locked_in_chain={v['locked_in_chain']}")
        for a in v['assignments']:
            print(
                f"    {a['day']} {a['area']} {a['start']}-{a['end']} src={a['source']} locked={a['locked']}"
            )
        print()


if __name__ == '__main__':
    main()
