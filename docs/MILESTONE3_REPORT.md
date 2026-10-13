# Milestone 3 report — v0.3.0

The initial Elwynn Forest campaign is playable from its ordinary Rank 1 start through the final boss. The existing six-class ability system is retained. The documented source command is:

```powershell
.\.venv\Scripts\python.exe run_game.py
```

Choose a class in the menu. `play.cmd` opens the same game. The Windows executable is `dist/WarcraftSurvivors/WarcraftSurvivors.exe`; distribute its entire folder or `dist/WarcraftSurvivors-0.3.0-Windows.zip`.

## Implemented

- Eleven catalog enemies: Kobold, Wolf, Defias Bandit, Kobold Geomancer, Defias Cutpurse, Defias Marksman, Riverpaw Gnoll, Gnoll Shaman, Forest Spider, Wild Boar and Forest Bear. Typed definitions include stats, rewards, collision, sprites, terrain/time eligibility, scaling and chase/flank/ranged/bruiser/charge behavior.
- Thirty authored minute waves grow in composition, stats, XP, rate and density. Late reinforcements release over three seconds; the final minute supports 4,600 living regular enemies, with a 6,000 safety ceiling. Area attacks and evolutions can keep actual living counts far below this budget.
- Random Defias Captain, Riverpaw Packlord or Forest Broodmother at 5/10/15/20/25 minutes. Each has distinct art, larger body/HP, an attack sequence with warnings, bonus XP/class XP/gold and a chest. Living elites persist. Qualified chests guarantee an eligible evolution among three unique options; selection still requires Rank 8 plus its passive.
- Hogger appears once at 30:00, with his own sprite/animations, large health bar, cleave, swept charge, leap and expanding shockwave. Warnings lock aim/location before damage. He enrages at half HP, resists crowd control and has level-adjusted HP. The campaign timer caps at 30:00 while live boss time/animation continue. Boss selection/attacks/rewards are data-defined for future additions.
- Victory requires a dead boss and living player after 30 minutes. Death/abandon preserve earned rewards; death during the boss fight records failure. Death and victory screens show survival time, level, kills, elites, boss outcome, gold, permanent class XP and new achievements. Saving is idempotent and selected-class correct.
- Run gem XP and permanent class XP are separate calculations. Enemy gem values scale with waves; distant gems drift after 45 live seconds to sustain progression. Catalog kill/elite/boss rewards bank class XP; victory adds 5,000 class XP and 1,500 gold. Existing achievements do not pay twice.
- Source-only debug tools add 64x acceleration, next-wave skipping, paused specific-time entry, elite/boss spawns and run-gold testing to existing XP/spawn/kill/immunity/FPS tools. Modified runs receive no saved rewards; packaged/release controls remain protected. Sequential density benchmarks export timings and entity counts.
- Spatial collision/targeting, swept projectiles, bounded local separation, distance-based movement updates and visible-cell rendering support large populations. Fixed steps govern movement, warnings, cooldowns and attacks. Lethal damage cannot be reversed by same-tick regeneration or automatic healing.

## Validation and complete-run evidence

Source check: **PASS: 568 tests (32.80 seconds); Ruff lint/format (53 Python files), strict mypy (23 source modules), all raster validation, six 180-frame class launches and a boss boundary launch**. Includes Ruff lint/format, strict mypy, pytest, raster validation, six ordinary class launch smokes and a bounded headless Hogger boundary smoke.

`verify_full_run.py` advances every actual 1/60-second simulation tick, from ordinary Paladin Rank 1, using only movement, legal randomly offered card selections and manual activation. There are no time jumps, pre-equipped upgrades, invulnerability or debug grants. It writes a fresh private profile, separate from the player's save. Seed 47 result:

- Victory at **31:29** (1889.08 simulated seconds), with 235 health, level **226**, **25,220 kills**, **5 elites**, **4 evolutions**.
- Hogger lasted approximately **89 seconds**; all four attacks executed: hogger_cleave 4, hogger_charge 4, hogger_leap 4, hogger_quake 3.
- Saved rewards: **51,009 class XP**, **7,026 gold**, all six fresh achievements. Wall time: 125.07 seconds.
- Checkpoint levels at 5/10/15/20/25/30 minutes: **19 / 46 / 78 / 121 / 166 / 222**, demonstrating continued XP progression.

Machine-readable proof: `artifacts/milestone3/full-run.json`. `verify_milestone3.py` separately captures staged early/mid/late enemies, all elite designs, qualified evolution choices, four boss warnings and death/victory screens. Those captures use injected counters/private profiles and are not full-run balance evidence. Boss animations beyond 30:00, six classes damaging the live boss, warning/dodge/cancellation, lethal ties, failure reward retention and results saving are covered by automated tests.

Release validation: **PASS: Windows PyInstaller build, packaged raster validation, six 180-frame class smokes, Hogger boundary smoke (asserts boss alive at 30:00 with additional elapsed time), and packaged --debug rejection with exit 2**.

## Performance

Sequential dummy-SDL CPU measurements at 1920×1080 / Medium effects / 29:00, full high-rank Hunter arsenal with permanent wolves and Stampede, immortal enemies so density persists. These measure CPU workload, not physical display FPS or GPU certification.

| Living enemies | Mean simulation ms | Mean render ms | Combined mean ms | Combined p95 ms |
|---:|---:|---:|---:|---:|
| 1,000 | 9.13 | 4.54 | 13.67 | 16.12 |
| 3,000 | 34.99 | 10.34 | 45.33 | 55.14 |
| 6,000 | 77.28 | 17.23 | 94.51 | 115.22 |

The supported density is not a 60-FPS guarantee. Persistent 3,000–6,000 surviving foes exceed a 16.7-ms frame budget on this machine. Cosmetic Low quality does not eliminate the physics/AI cost. The ordinary proof run clears enemies quickly; weak builds that let thousands accumulate need further optimization. The cap was not lowered to conceal this limitation.

## Files changed

Runtime:

- `src/warcraft_survivors/content.py`, `entities.py`, `simulation.py`, `spawning.py`, `combat.py`, `manuals.py`, `upgrades.py`, `persistence.py`, `app.py`, `rendering.py`, `debug.py`, `world.py`, `__init__.py`.
- New `src/warcraft_survivors/waves.py`, `enemy_combat.py`, `rewards.py`.
- `src/warcraft_survivors/data/content.json`; new `data/encounters.json`.
- `src/warcraft_survivors/assets/manifest.json`; new actor atlases `hogger`, `gnoll`, `gnoll_shaman`, `spider`, `forest_boar`, `forest_bear`, `kobold_geomancer`, `defias_cutpurse`, `defias_marksman`, `defias_captain`, `gnoll_packlord`, `broodmother`; new effects `hostile_arrow`, `hostile_stone`, `hostile_poison`, `hostile_lightning`.

Development/tests/art:

- New `scripts/build_encounters.py`, `build_encounter_assets.py`, `encounter_catalog.py`, `verify_full_run.py`, `verify_milestone3.py`; updated `build_assets.py`, `benchmark.py`, `check.ps1`, `verify_build.py`, `package.ps1`.
- New `tests/test_encounters.py`; updated `test_app.py`, `test_assets.py`, `test_combat.py`.
- `pyproject.toml`; `art_sources/generated/hogger-walk.png`, `elwynn-creatures.png`, `art_sources/milestone3-prompts.json`, `source_hashes.json`.
- README; `docs/ARCHITECTURE.md`, `GAME_DESIGN.md`, `MILESTONES.md`, `QA.md`, `ASSET_CREDITS.md`, `ASSET_PIPELINE.md`, `VISUAL_AUDIT.md`; new `MILESTONE3_REQUEST.md`, `MILESTONE3_REPORT.md`, `ENCOUNTER_CATALOG.md`, historical `QA_MILESTONE2.md` and `docs/screenshots/milestone3/`.
- Generated evidence under `artifacts/milestone3/`, Windows folder and v0.3.0 ZIP under `dist/`. Earlier milestone reports/archives remain historical.

No AGENTS.md was found in the workspace or checked ancestor directories. Existing project instructions, design, architecture and historical reports were inspected before changes. No automatic next milestone is included.

## Art and limitations

The imagegen skill was applied using built-in image generation for two original transparent atlases. Exact prompts and method are saved in `art_sources/milestone3-prompts.json`; source paths are listed above. Runtime requires no generation, network or source-art folder. Hogger has a generated directional walking cycle; derived cast/death poses and creature gaits still need an artist pass. No extracted Blizzard art was used.

Only Hogger ships in the final-boss pool. Enemy navigation uses local steering rather than global pathfinding; terrain may produce congestion. One deterministic Paladin victory validates the complete structure, not six-class/build/seed balance parity. The XP curve is generous after equipment caps and uses existing repeatable healing/gold/power cards; further difficulty/reward tuning is appropriate. Physical controller handling retains tested input calculations/events but no physical gamepad was available for certification. Active runs cannot be resumed from a save. Talent/shop expansion, other zones and further milestones remain deferred.
