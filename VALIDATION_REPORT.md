# Solver Validation Report (PetroServe Casselton)

## Dataset Load Check

- Employees: 26
- Requirements: 759
- Store: PetroServe USA - Casselton (102 Langer Ave S Casselton, ND 58012)

## Current vs Previous Metrics

| Metric | CURRENT (HEAD) | PREVIOUS (HEAD^) |
|---|---:|---:|
| Runtime (sec) | 9.623045208999883 | 42.13100621600006 |
| Assignments | 161 | 202 |
| Total scheduled hours | 469.0 | 438.0 |
| Employees used | 24 | 24 |
| Employees unused | 2 | 2 |
| Average shift length (h) | 2.9130434782608696 | 2.1683168316831685 |
| Median shift length (h) | 3.0 | 2.0 |
| Total uncovered requirement blocks | 288 | 278 |
| Total uncovered shortfall ticks | 366 | 430 |
| Engine hard-rule violations | 0 | 0 |
| Total hard-rule violations | 0 | 0 |

## Uncovered Minimum Demand by Area

| Area | CURRENT | PREVIOUS |
|---|---:|---:|
| CARWASH | 114 | 58 |
| CSTORE | 76 | 256 |
| KITCHEN | 176 | 116 |

## Workforce Utilization Buckets

| Bucket | CURRENT | PREVIOUS |
|---|---:|---:|
| <10h | 3 | 5 |
| 10-20h | 14 | 14 |
| 20-30h | 7 | 5 |
| >30h | 2 | 2 |

## CURRENT: Solver Diagnostics

- uncovered_min_by_area (diag): `{'CSTORE': 42, 'KITCHEN': 132, 'CARWASH': 114}`
- master_envelope_consistency: `{'raw_assignment_hours': 469.0, 'derived_envelope_hours': 469.0, 'hours_parity_ok': True, 'overlap_ticks_detected': 0, 'envelope_count': 88}`
- phase_diagnostics:
  - phase0_seed_locked: `{'seed': {'locked_count': 0, 'locked_hours': 0.0, 'locked_hours_by_area': {'CSTORE': 0.0, 'KITCHEN': 0.0, 'CARWASH': 0.0}, 'locked_coverage': {}, 'locked_envelopes': {}, 'label': 'PetroServe Casselton'}, 'envelope_consistency': {'raw_assignment_hours': 0.0, 'derived_envelope_hours': 0.0, 'hours_parity_ok': True, 'overlap_ticks_detected': 0, 'envelope_count': 0}}`
  - phase1_cstore_primary: `{'attempts': 2209, 'adds': 90}`
  - phase2_kitchen: `{'attempts': 5420, 'adds': 49}`
  - phase3_cstore_backfill_after_kitchen: `{'attempts': 71, 'adds': 0}`
  - phase4_carwash: `{'attempts': 2925, 'adds': 22}`
  - phase5_cstore_backfill_after_carwash: `{'attempts': 71, 'adds': 0}`
  - phase6_targeted_final_repair: `{'constructive_checkpoint_engine_hard': 0, 'envelope_consistency': {'raw_assignment_hours': 469.0, 'derived_envelope_hours': 469.0, 'hours_parity_ok': True, 'overlap_ticks_detected': 0, 'envelope_count': 89}}`
  - phase7_final_legality: `{'final_total_violations': 0, 'final_engine_hard_violations': 0, 'override_only_violations': 0, 'repair_stats': {}}`

## CURRENT: Top 10 Uncovered Requirement Blocks

| Day | Area | Time | Required | Scheduled | Shortfall |
|---|---|---|---:|---:|---:|
| Fri | KITCHEN | 05:30 | 3 | 0 | 3 |
| Fri | KITCHEN | 09:00 | 3 | 0 | 3 |
| Fri | KITCHEN | 09:30 | 3 | 0 | 3 |
| Fri | KITCHEN | 10:00 | 3 | 0 | 3 |
| Fri | KITCHEN | 10:30 | 3 | 0 | 3 |
| Fri | KITCHEN | 11:00 | 3 | 0 | 3 |
| Fri | KITCHEN | 11:30 | 3 | 0 | 3 |
| Fri | KITCHEN | 12:00 | 3 | 0 | 3 |
| Fri | KITCHEN | 12:30 | 3 | 0 | 3 |
| Fri | KITCHEN | 13:00 | 3 | 0 | 3 |

## CURRENT: Weekly Employee Summary

| Employee | Total hours | # shifts | Areas worked |
|---|---:|---:|---|
| Acelynn | 0.0 | 0 |  |
| Aedan | 10.0 | 3 | CSTORE |
| Brianna | 24.0 | 9 | CSTORE, KITCHEN |
| Bryan | 30.0 | 10 | CSTORE, KITCHEN |
| Caleb | 19.0 | 7 | CARWASH, CSTORE |
| Emma | 16.0 | 5 | CSTORE, KITCHEN |
| Finely | 20.0 | 7 | CARWASH, CSTORE |
| Gail | 0.0 | 0 |  |
| Jaden | 12.0 | 3 | CSTORE |
| Jared | 18.0 | 6 | CARWASH, CSTORE |
| Jayden | 19.0 | 6 | CARWASH, CSTORE |
| Jess | 15.0 | 6 | CARWASH, CSTORE |
| Kelsey | 6.0 | 3 | CSTORE, KITCHEN |
| Kenny | 12.0 | 3 | CSTORE |
| Kris Tegtmeier | 40.0 | 10 | CSTORE |
| Laura | 12.0 | 4 | KITCHEN |
| Lauren | 12.0 | 5 | CSTORE, KITCHEN |
| Lisa | 24.0 | 6 | CSTORE |
| Mandy | 40.0 | 11 | CSTORE, KITCHEN |
| Mary | 17.0 | 7 | KITCHEN |
| Paris | 20.0 | 8 | CARWASH, CSTORE |
| Quincy | 18.0 | 9 | CSTORE, KITCHEN |
| Ryanne | 30.0 | 11 | CSTORE, KITCHEN |
| Simon | 19.0 | 7 | CSTORE, KITCHEN |
| Stacy | 16.0 | 7 | CSTORE |
| Sue | 20.0 | 8 | KITCHEN |

## CURRENT: Schedule Grouped by Employee and Day

### Aedan
- **Sun**
  - 06:00-10:00 (CSTORE)
  - 10:00-14:00 (CSTORE)
- **Sat**
  - 05:30-07:30 (CSTORE)

### Brianna
- **Sun**
  - 14:00-17:00 (KITCHEN)
  - 17:00-21:00 (CSTORE)
  - 21:00-22:00 (KITCHEN)
- **Tue**
  - 16:00-19:00 (KITCHEN)
  - 19:00-23:00 (CSTORE)
  - 23:00-24:00 (CSTORE)
- **Sat**
  - 07:30-08:30 (KITCHEN)
  - 08:30-11:30 (KITCHEN)
  - 11:30-15:30 (CSTORE)

### Bryan
- **Mon**
  - 07:00-08:00 (KITCHEN)
  - 08:00-11:00 (KITCHEN)
  - 11:00-15:00 (CSTORE)
- **Tue**
  - 11:00-15:00 (CSTORE)
- **Wed**
  - 10:00-11:00 (KITCHEN)
  - 11:00-15:00 (CSTORE)
  - 15:00-16:00 (CSTORE)
- **Thu**
  - 11:00-15:00 (CSTORE)
- **Fri**
  - 11:00-15:00 (CSTORE)
  - 15:00-19:00 (CSTORE)

### Caleb
- **Mon**
  - 17:00-21:00 (CSTORE)
  - 21:00-22:00 (CSTORE)
- **Tue**
  - 17:00-21:00 (CSTORE)
  - 21:00-22:00 (CARWASH)
- **Thu**
  - 16:00-19:00 (CARWASH)
- **Fri**
  - 16:00-19:00 (CARWASH)
  - 19:00-22:00 (CARWASH)

### Emma
- **Sun**
  - 10:00-11:00 (KITCHEN)
  - 11:00-14:00 (KITCHEN)
  - 14:00-18:00 (CSTORE)
- **Fri**
  - 18:00-22:00 (CSTORE)
- **Sat**
  - 10:00-14:00 (CSTORE)

### Finely
- **Sun**
  - 17:00-21:00 (CSTORE)
  - 21:00-22:00 (CARWASH)
- **Sat**
  - 07:30-11:30 (CSTORE)
- **Mon**
  - 16:00-19:00 (CARWASH)
  - 19:00-22:00 (CSTORE)
- **Tue**
  - 16:00-18:00 (CARWASH)
- **Thu**
  - 19:00-22:00 (CARWASH)

### Jaden
- **Sun**
  - 13:00-17:00 (CSTORE)
- **Fri**
  - 16:00-20:00 (CSTORE)
  - 20:00-24:00 (CSTORE)

### Jared
- **Tue**
  - 14:00-15:00 (CARWASH)
  - 15:00-19:00 (CSTORE)
- **Thu**
  - 14:00-15:00 (CARWASH)
  - 15:00-19:00 (CSTORE)
- **Sat**
  - 14:00-18:00 (CSTORE)
  - 18:00-22:00 (CSTORE)

### Jayden
- **Mon**
  - 14:00-15:00 (CARWASH)
  - 15:00-19:00 (CSTORE)
- **Fri**
  - 14:00-18:00 (CSTORE)
- **Sat**
  - 15:30-19:30 (CSTORE)
- **Sun**
  - 14:00-17:00 (CARWASH)
  - 17:00-20:00 (CARWASH)

### Jess
- **Tue**
  - 18:00-21:00 (CARWASH)
  - 21:00-22:00 (CSTORE)
- **Thu**
  - 17:00-21:00 (CSTORE)
  - 21:00-22:00 (CSTORE)
- **Wed**
  - 16:00-19:00 (CARWASH)
- **Mon**
  - 19:00-22:00 (CARWASH)

### Kelsey
- **Wed**
  - 16:00-17:00 (KITCHEN)
  - 17:00-21:00 (CSTORE)
  - 21:00-22:00 (KITCHEN)

### Kenny
- **Sun**
  - 09:00-13:00 (CSTORE)
  - 13:00-17:00 (CSTORE)
- **Sat**
  - 06:00-10:00 (CSTORE)

### Kris Tegtmeier
- **Mon**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)
- **Tue**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)
- **Wed**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)
- **Thu**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)
- **Fri**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)

### Laura
- **Mon**
  - 06:00-09:00 (KITCHEN)
- **Tue**
  - 06:00-09:00 (KITCHEN)
- **Wed**
  - 06:00-09:00 (KITCHEN)
- **Thu**
  - 06:00-09:00 (KITCHEN)

### Lauren
- **Wed**
  - 16:00-20:00 (CSTORE)
  - 20:00-22:00 (CSTORE)
- **Sat**
  - 16:00-17:00 (KITCHEN)
  - 17:00-21:00 (CSTORE)
  - 21:00-22:00 (CSTORE)

### Lisa
- **Sun**
  - 05:00-09:00 (CSTORE)
- **Tue**
  - 07:00-11:00 (CSTORE)
- **Wed**
  - 07:00-11:00 (CSTORE)
- **Thu**
  - 07:00-11:00 (CSTORE)
- **Fri**
  - 05:00-09:00 (CSTORE)
- **Sat**
  - 05:00-09:00 (CSTORE)

### Mandy
- **Sun**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)
- **Mon**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)
- **Tue**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)
- **Wed**
  - 05:00-09:00 (CSTORE)
  - 09:00-13:00 (CSTORE)
- **Thu**
  - 05:00-09:00 (CSTORE)
  - 09:00-12:00 (KITCHEN)
  - 12:00-13:00 (KITCHEN)

### Mary
- **Mon**
  - 06:00-09:00 (KITCHEN)
  - 09:00-10:00 (KITCHEN)
- **Tue**
  - 06:00-09:00 (KITCHEN)
  - 09:00-10:00 (KITCHEN)
- **Wed**
  - 06:00-09:00 (KITCHEN)
- **Thu**
  - 06:00-09:00 (KITCHEN)
- **Fri**
  - 06:00-09:00 (KITCHEN)

### Paris
- **Fri**
  - 07:00-11:00 (CSTORE)
  - 11:00-14:00 (CARWASH)
  - 14:00-15:00 (CARWASH)
- **Sat**
  - 07:00-09:00 (CARWASH)
  - 09:00-13:00 (CSTORE)
  - 13:00-15:00 (CARWASH)
- **Sun**
  - 09:00-10:00 (CARWASH)
  - 10:00-13:00 (CARWASH)

### Quincy
- **Sun**
  - 17:00-18:00 (KITCHEN)
  - 18:00-21:00 (KITCHEN)
  - 21:00-22:00 (CSTORE)
- **Wed**
  - 17:00-18:00 (KITCHEN)
  - 18:00-21:00 (KITCHEN)
  - 21:00-22:00 (CSTORE)
- **Thu**
  - 17:00-19:00 (KITCHEN)
  - 19:00-22:00 (CSTORE)
- **Mon**
  - 16:00-19:00 (KITCHEN)

### Ryanne
- **Sun**
  - 21:00-22:00 (CSTORE)
- **Mon**
  - 11:00-13:00 (KITCHEN)
  - 13:00-17:00 (CSTORE)
- **Tue**
  - 09:00-10:00 (KITCHEN)
  - 10:00-13:00 (KITCHEN)
  - 13:00-17:00 (CSTORE)
- **Wed**
  - 09:00-10:00 (KITCHEN)
  - 10:00-13:00 (KITCHEN)
  - 13:00-17:00 (CSTORE)
- **Thu**
  - 10:00-13:00 (KITCHEN)
  - 13:00-17:00 (CSTORE)

### Simon
- **Sun**
  - 18:00-22:00 (CSTORE)
  - 22:00-24:00 (CSTORE)
- **Fri**
  - 17:00-19:00 (KITCHEN)
  - 19:00-22:00 (CSTORE)
- **Sat**
  - 12:00-13:00 (KITCHEN)
  - 13:00-17:00 (CSTORE)
  - 17:00-20:00 (KITCHEN)

### Stacy
- **Mon**
  - 07:00-11:00 (CSTORE)
- **Tue**
  - 13:00-14:00 (CSTORE)
- **Wed**
  - 13:00-14:00 (CSTORE)
- **Thu**
  - 09:00-13:00 (CSTORE)
  - 13:00-14:00 (CSTORE)
- **Fri**
  - 09:00-13:00 (CSTORE)
  - 13:00-14:00 (CSTORE)

### Sue
- **Mon**
  - 09:00-12:00 (KITCHEN)
  - 12:00-15:00 (KITCHEN)
  - 15:00-16:00 (KITCHEN)
- **Tue**
  - 09:00-12:00 (KITCHEN)
  - 12:00-15:00 (KITCHEN)
  - 15:00-16:00 (KITCHEN)
- **Wed**
  - 09:00-12:00 (KITCHEN)
  - 12:00-15:00 (KITCHEN)
