# Save format and recovery — version 2

Normal Windows profiles live at `%LOCALAPPDATA%\WarcraftSurvivors\save.json`, outside the install directory. Non-Windows fallback is `~/.local/share/WarcraftSurvivors/save.json`. Source QA uses explicit private profile directories; normal profiles are not replaced by smoke tests or staged captures.

## Stored state

The pets/summons overhaul retains V2 and the internal ability IDs `beast_companion`, `summon_felguard` and their `_evolved` forms. The latter now displays Summon Imp / Imp Legion and uses the original Imp artwork. Existing Warlock preparation selections and spell-specific talent bonuses continue through the same base ID; no pet objects or active-run state are added to profiles. Regression tests reopen an eligible profile with the retained selection and verify that it summons Imps.

| Field | Purpose |
|---|---|
| `version`, `revision` | Version 2 schema and incrementing successful-write revision |
| `gold` | Shared permanent currency |
| `classes` | Per registry class: total `xp`, derived `level`, available `talent_points`, allocated `talents`, selected `starting_ability` |
| `shared` | Purchased shared upgrade ranks |
| `achievements`, `achievement_progress` | Completed IDs and progress values rebuilt from authoritative counters |
| `unlocked_classes`, `unlocked_zones` | Registry-validated class achievement unlocks and shipped zone unlocks |
| `stats` | Total runs/kills/wins/elites/evolutions/bosses, best time, best run kills, per-class runs/wins, per-boss kill counts |
| `settings` | Fullscreen, sound, music/sound volumes, window resolution, cosmetic effect density, effects quality, screen shake; saved debug opt-in is always disabled |

Levels/points are recomputed from XP, not trusted from editable cached fields. A class level requires 120 × current level XP to advance; available points = class level − 1 − allocated ranks, never negative. Every tree currently supports 40 allocated ranks; class level is capped at 100 for compatibility. Unknown/over-budget/prerequisite-invalid talent allocations refund their points without reducing earned XP. Unsupported ranks/IDs and invalid nested field types are conservatively sanitized.

The profile includes nine registry classes, while only the initial six have playable content. Six initial unlocks are always retained. Future class unlocks derive only from completed registry achievements; an arbitrary `unlocked_classes` entry cannot bypass a gate. All five shipped zones are granted to new and existing profiles without spending currency. New classes can later become playable without removing earned unlocks.

## Commit and recovery

1. Validate a complete version 2 snapshot, increment its revision, serialize to `save.tmp`, flush and `fsync` it.
2. When the current main file is valid, serialize the previous snapshot to `save.bak.tmp`, flush it, then atomically replace `save.bak`.
3. Atomically replace the main `save.json` with `save.tmp`. Windows replace operations retry up to three times for transient permission/file-lock failures; other errors return a clear notice.

Purchases, talent allocation, starting selections and resets hold an in-memory snapshot and restore it if committing fails. A failed purchase does not spend gold/points or grant a bonus. Reward calculation failures are not silently discarded: earned in-memory rewards remain available for a later write on exit, with a visible save-error notice. The results screen awards once; revisiting it cannot duplicate rewards.

Loading prefers a valid committed main file, then `save.bak`, then a valid interrupted `save.tmp` if no committed profile can be read. A valid main profile always wins over a newer uncommitted temporary file. Corrupt main data is preserved once as `save.corrupt`; backup recovery does not copy corruption over the good backup. Missing profiles use safe defaults. Invalid backup/temp files do not crash startup. Newer unsupported schema versions are kept intact and put the session in read-only mode; the game never downgrades or overwrites them.

This local profile is not encrypted, cloud-synchronized or designed for simultaneous concurrent writers. Active runs are not resumed after process exit. Ordinary Quit/Finish records already earned progression; an abrupt process loss preserves the last committed profile.

## Version 1 migration

Migration retains gold, per-class XP, settings, supported shared ranks and completed achievements. Legacy might/health/haste ranks are retained up to the new caps and available point budget. Obsolete, excessive or newly ineligible signature ranks are refunded to unspent points. Existing unlocked Wisdom ranks remain usable; future purchases must satisfy the eight-shared-rank requirement. Level and talent-point fields are derived and written in version 2 on the next successful save.

Old aggregate stats remain. Only proven lower bounds are inferred: a completed elite/evolution record proves at least one; version 1 wins identify the historical Hogger encounter. Per-class wins and exact historical elite/evolution totals were not stored, so migration does not invent them. Existing achievement rewards do not pay again. Newly introduced achievements whose migrated counters already meet their condition complete on the next recorded run. Migration shows a notice; it does not require throwing away an existing profile.

## Verified real loop

`verify_progression_loop.py` launches three separate processes. A genuine normal run died at 5:10, recording 388 kills, 233 gold and 493 class XP. The next process confirmed Endurance Rank 1 for 65 gold. A third process reopened the same file and started with 139.05 health (135 base × 1.03), retained 168 gold and 493 class XP, and still had exactly one starting ability. This loop is also part of pytest; see `artifacts/milestone4/loop.json`.

## Compatible Milestone 5 extension

The schema remains V2: optional validated settings fields default to music volume 0.35, sound volume 0.7, density 1.0 and 1280×720. Gains/density clamp to 0–1; NaN/non-number/bool values use defaults. Resolutions are selected from 1280×720, 1600×900, 1920×1080 and 2560×1440. New boss achievement counters use the existing per-boss dictionary, and the registry adds four boss completion achievements. Older profiles receive all five initial zones while retaining XP, gold and allocations. Unknown future versions remain read-only.

The M5 three-process loop earned 123 gold/250 class XP through genuine failures, confirmed a 65-gold Endurance upgrade, then reopened with 58 gold, unchanged XP and 139.05 starting health. See `artifacts/milestone5/loop.json`; the preceding M4 proof is historical. Logs are independent of saves under the adjacent `logs` directory (or the explicit private QA save directory).
