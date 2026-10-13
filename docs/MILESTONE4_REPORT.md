# Milestone 4 report — v0.4.0

Permanent progression is playable around the completed six-class Elwynn campaign. Normal launch from the workspace:

```powershell
.\.venv\Scripts\python.exe run_game.py
```

Use the menu's Talents, Upgrades and Achievements buttons, or Spend rewards after a run. `play.cmd` opens the same menu. Windows executable: `dist/WarcraftSurvivors/WarcraftSurvivors.exe`, with its complete folder. Release archive: `dist/WarcraftSurvivors-0.4.0-Windows.zip`.

## Implemented

- Each class has independent persistent XP/level, XP progress and available talent points. Enemy/elite/boss kill XP, survival and substantial victory bonuses remain independent of run gem XP. Class levels preserve the existing increasing 120 × current level requirement; each level after the first awards one point, up to level 100.
- Six distinct 18-node talent trees (108 nodes, 40 allocatable ranks per class) combine damage, health, armor, cooldowns, school/strategy/spell-specific modifiers, recovery, offensive/defensive capstones and selected starting equipment. Every node has an observable gameplay-effect test. Prerequisites, minimum class levels, spent-point requirements, caps and point budgets are enforced.
- New/untalented classes retain exactly one Rank 1 signature ability. Advanced preparation unlocks selection of one optional extra Rank 1 ability; purchasing it grants no equipment automatically. Hunter/Warlock companions require preparation plus explicit selection. Extra spells occupy regular slots, and spell-specific bonuses persist through evolution.
- Between-run respec displays **50 + 5 × allocated ranks** gold before confirmation. Reset returns all spent points, preserves XP/level and clears the optional extra starting choice. Unaffordable or unsaved changes do not commit.
- Ten shared upgrades: health, damage, armor, movement, pickup, gem XP, gold rewards, recovery, rerolls and Wisdom. Ranks/costs are explicit. Wisdom requires eight shared ranks plus 450 gold and unlocks a permanent fourth normal card. Chests remain three choices; 1–3 run rerolls use R / controller X / button and cannot reroll chests. Exhausted four-card pools include a working shield reward.
- Twenty-nine persistent achievements have counters, conditions, completion, one-time gold rewards, progress pages and unlock notifications. Conditions include cumulative kills/elites/evolutions, 10/20/30-minute survival, identified Hogger kills, class levels and wins with distinct classes.
- Future Rogue/Druid/Shaman unlock registry entries persist achievement-earned eligibility. Gold cannot buy a class. Their playable content is explicitly deferred. Six initial classes and Elwynn remain available; the profile stores class and zone unlocks.
- Version 2 user-data profiles store all progression, selected starters, stats, per-class/per-boss counters and settings. V1 migration retains gold/XP/valid purchases and refunds obsolete/invalid talent ranks. Atomic main/backup replacement, fsync, corruption preservation, backup/temp recovery, transient Windows lock retry and future-schema read-only protection cover common failures.
- Purchases, allocation, starting selections and resets roll back on save failure. Levels/point budgets and registry unlocks are derived and validated. Results remain exactly-once and failed runs retain earnings. Developer-modified runs stay excluded, with frozen/release opt-in rejection preserved.
- Interactive class progression, prerequisite trees, shop pages, achievement progress, locked/earned future classes, explicit confirmations and starting choices support keyboard, mouse and controller events. Grid arrows are spatial; Tab cycles all controls. Dialogs initially focus Cancel. Progression mutations are unavailable during live runs.

## Tests and runtime proof

`check.ps1`: **PASS**. **722 pytest tests passed in 51.80 seconds**. Ruff lint and formatting passed (60 Python files after adding the catalog generator); strict mypy passed (25 source modules). Raster validation passed. Six classes, Hogger and five progression screens each completed 180-frame source launches.

The new progression suite contributes 149 persistence/content/effect tests plus five UI tests, retaining the existing 568 gameplay tests. It exercises all 108 talents with actual health/damage/cooldown/collection/companion/etc. effects, each shared upgrade's costs/caps, insufficient funds, prerequisites/point budgets, respec refund semantics, explicit companion selection, fourth-card/reroll behavior, all confirmations, actual controller events, V1/V2 nested-data validation, corruption/backup/temp/future-schema handling, transient file-lock recovery, purchase/respec/selection rollback and independent achievement counters/unlocks. A future different boss victory does not falsely grant a Hogger achievement.

### Three-process actual progression loop

`verify_progression_loop.py` starts three independent application processes using a private profile. No starting progression, time jump, XP/gold grants or invulnerability are injected. The harness chooses legal cards, leaves a weak-attack build stationary and lets actual enemies kill it.

1. Normal Paladin run died at **5:10** (310.58 seconds), player level **19**, **388 kills**, earning **233 gold** and **493 class XP** (permanent class level 3 / two talent points).
2. After closing, a new process reopened the same profile, displayed/confirmed Endurance Rank 1 for **65 gold**, retaining **168 gold** and all **493 class XP**.
3. After another close/reopen, the next run started with **139.05 maximum health** (135 × 1.03), retained the bank/XP and equipped **only Judgment**.

The entire three-process loop also runs inside pytest. Machine-readable result: `artifacts/milestone4/loop.json`; process-specific screenshots/JSON/private saves live in its generated loop folder or pytest temporary directory. This is actual gameplay/restart evidence, separate from staged UI captures.

### Campaign preservation

The legal-input, no-cheat full fixed-step campaign verification again won at **31:29**, with **25,220 kills**, five elites, four evolutions and player level 226. All four Hogger attacks executed. A fresh V2 profile saved **51,009 class XP**, **28 new talent points**, **9,086 gold** and **15 achievements**. Additional gold compared with v0.3 comes from the new one-time achievement catalog; the run XP/spell/wave/boss systems retained their behavior. Proof: `artifacts/milestone4/campaign/full-run.json`.

`verify_milestone4.py` separately captured all six full talent trees, both shared-shop pages, four achievement pages, locked/earned future entries, notifications, respec review, optional companion selection and four-card decisions for every class. These use an injected private progression fixture and short staged gameplay; they are not balance or earned-profile evidence. Visual review verified card fit, cost/rank text, prerequisite lines and progress bars. No new assets or network access are required.

Release verification: **PASS: Windows PyInstaller build; packaged raster validation; six classes, Hogger and five progression screens launched at 180 frames each; frozen --debug rejected with exit code 2.**.

## Files changed

- New `src/warcraft_survivors/meta.py`, `progression_ui.py` and `data/progression.json`.
- Updated `persistence.py`, `rewards.py`, `entities.py`, `simulation.py`, `combat.py`, `manuals.py`, `upgrades.py`, `rendering.py`, `app.py`, `__init__.py` and `pyproject.toml`.
- New `scripts/build_progression.py`, `progression_catalog.py`, `verify_progression_loop.py`, `verify_milestone4.py`; updated `verify_full_run.py`, `check.ps1`, `verify_build.py`, `package.ps1`.
- New `tests/test_meta.py`; updated `test_app.py`, `test_persistence.py`, `test_encounters.py`, retaining all completed gameplay tests.
- README and current `GAME_DESIGN.md`, `ARCHITECTURE.md`, `MILESTONES.md`, `QA.md`; new `MILESTONE4_REQUEST.md`, `MILESTONE4_REPORT.md`, `PROGRESSION_CATALOG.md`, `SAVE_FORMAT.md`, `QA_MILESTONE3.md` and `docs/screenshots/milestone4/`.
- Generated proof under `artifacts/milestone4/`; executable folder and v0.4.0 ZIP under `dist/`. Historical milestone reports/archives remain. The existing original asset pipeline/PNG registry is unchanged.

No AGENTS.md was found in the workspace or checked ancestors. Existing design, master specification, architecture and gameplay documentation were inspected before changes. No next milestone is started.

## Limitations

Only the initial six classes and Elwynn are playable; the future registry entries represent earned unlocks awaiting later content. Talent/shared tuning is an initial balanced set of modest early bonuses and gated deeper effects, not a certification of every class/build/seed. Existing large-persistent-horde performance and local-steering limitations remain; no new performance guarantee is claimed. Physical gamepad certification remains outstanding, although navigation/activation events and math are tested. Active runs are not resumed. Profiles are local, unencrypted and not synchronized across simultaneous writers. The legacy class-level cap is 100; points beyond the current 40 talent ranks remain unspent for future expansion. Historical exact elite/evolution counts and class-specific wins cannot be reconstructed from V1, so migration preserves proven lower bounds rather than inventing totals. Derived creature action art remains a future polish task.
