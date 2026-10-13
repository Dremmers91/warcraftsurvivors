# Milestone 3 QA — v0.3.0

Windows / Python 3.13.15 / Pygame-ce 2.5.8 / pytest 8.4.2 / Ruff 0.13.3 / mypy 1.18.2 / PyInstaller 6.22.3. Milestone 2 historical results are preserved in `QA_MILESTONE2.md`.

## Automated checks

**PASS: 568 tests (32.80 seconds); Ruff lint/format (53 Python files), strict mypy (23 source modules), all raster validation, six 180-frame class launches and a boss boundary launch**

Coverage retains the complete six-class spell/manual/evolution suite and adds all 30 wave boundaries and restrictions, composition/scaling, >3,000 actual spawns, late reinforcement batches, all elite rewards/chests, guaranteed qualified evolution choices, event idempotence, boss timing/conditions, multiple overlapping elites, all hostile attack geometries, warnings/dodges/cancellation, swept hostile missiles/immunity, enrage, future boss-pool definitions, failure/success formulas, saved achievements and exactly-once class-correct results. Six full class arsenals damage a live boss. Regression cases prevent lethal damage resurrection and stopped post-30 animation. Developer release gates and paused time entry are tested.

## Runtime proof

`verify_full_run.py` completed every fixed simulation tick through 30 minutes and an 89-second Hogger fight, with ordinary Rank 1 Paladin start, legal cards/movement/manual inputs and no invulnerability or debug grants. Seed 47 won at 31:29, level 226, 25,220 kills, five elites and four evolutions. All four boss attacks executed. Fresh private save recorded 51,009 class XP, 7,026 gold and all six achievements. Checkpoint levels 19/46/78/121/166/222 show progression every five minutes. See `artifacts/milestone3/full-run.json`.

`verify_milestone3.py` captured staged wave populations, three elite visuals, qualified evolution cards, all boss warnings and death/victory results using private saves. Visual inspection verified the boss bar and warning geometry, readable enemy silhouettes, three distinct card choices and all result fields. These images are explicitly staged; their injected counters do not replace the full-run evidence. Source smoke captures are in `artifacts/milestone3/source/`; review images are in `docs/screenshots/milestone3/`.

## Release

**PASS: Windows PyInstaller build, packaged raster validation, six 180-frame class smokes, Hogger boundary smoke (asserts boss alive at 30:00 with additional elapsed time), and packaged --debug rejection with exit 2**

## Performance and limitations

See `MILESTONE3_REPORT.md` for sequential 1,000/3,000/6,000-foe Hunter timings, reproducible commands, changed files and exact balance limits. Large persistent hordes are supported but not guaranteed to meet 60 FPS: mean combined CPU work was 13.67 / 45.33 / 94.51 ms. These are dummy-SDL CPU stress tests with immortal enemies and a full arsenal, not hardware FPS. Further large-crowd optimization and class/seed balance tuning remain needed. Physical controller certification and active-run resume remain outstanding.

## Reproduce

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check.ps1
.\.venv\Scripts\python.exe scripts\verify_full_run.py
.\.venv\Scripts\python.exe scripts\verify_milestone3.py
.\.venv\Scripts\python.exe scripts\benchmark.py --class hunter --complete-loadout --enemies 3000 --frames 180
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build.ps1
.\.venv\Scripts\python.exe scripts\verify_build.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\package.ps1
```

Normal play: `.\.venv\Scripts\python.exe run_game.py`. Developer controls require explicit `--demo --debug`; F9 skips a minute, T enters MM:SS, F10/F11 spawn encounters and F12 grants run gold. Modified runs cannot save progression. No next milestone is started.
