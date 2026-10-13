# Milestone 5 report — v0.5.0

Milestone scope is implemented: five native finite survival zones, distinct final encounters, original art/audio, expanded settings/navigation, compatible progression, measured optimization and Windows onedir/onefile distributions. Both actual distributions and their final ZIP archives have been validated, including extracted startup without a source/Python PATH. No next milestone was started.

## Implemented features

- Preserved Elwynn and added Duskwood, Stranglethorn Vale, Eastern Plaguelands and Icecrown, each with an 8192×8192 scrolling map, themed ground/roads/obstacles, three named landmarks and an independent 30-minute schedule. Elwynn gained original inn/mill/traversable bridge artwork.
- Expanded to **31 normal variants, 11 elite variants and five bosses**. All zones retain five scheduled elites, surviving enemies, real XP/reward drops and evolution-eligible chests. Each independent boss pool ships one iconic boss and supports future randomized entries.
- Stitches has hook pulls and bile; Bangalash has pounce/rush/roar; Rivendare has shadow volleys/decay; the Lich King has frost slows, winter and growing/pulsing Defile. Boss warnings, health bars, enrage, damage and movement are real. Victory requires defeating the boss while alive.
- Integrated original art from ten retained generation sources, **57 directional actor definitions**, recognizable zone props, magic sheets, new demon artwork and a golden-hammer application icon. Some gait/action frames and themed variants are derived from originals.
- Added five original stereo music loops and 21 original synthesized sound cues. Music and sound volumes are independent; device/file failures remain nonfatal in normal play.
- Polished class/zone selection, settings, HUD contrast, messages/statuses, telegraphs, cards, results and existing progression screens. Keyboard/mouse/gamepad event navigation, window resizing/letterboxing, four resolutions, fullscreen, quality, cosmetic density and shake work together.
- Profiled before optimizing. Cached/staggered crowd steering, adaptive movement cadence, numeric spatial bounds, early-exit obstacle resolution and reused actor views improve CPU work. Damage/DoT/projectile/AoE collision checks and the 6,000-enemy ceiling remain intact. Beam lookups now include large bodies at segment ends.
- Reviewed the six-class/rank/manual/passive/evolution/talent/economy systems through functional tests, early/advanced probes and complete runs. Early foes demand movement; late XP requirements grow faster after level 40. Life steal uses actual damage and bounded recovery, while armor-piercing/health-scaled boss hits wound it briefly. Failed-run progression remains useful.
- Added compatible V2 settings/zone availability and four persistent boss achievements (33 total). Existing class trees, purchases, respecs and explicit advanced starting companions are preserved.
- Added user-data rotating logs, actionable fatal errors, protected release controls, reproducible icon/resource bundling, onedir and optional onefile builds, and release integrity guards.

## Files changed

| Area | Files and assets |
|---|---|
| Content and zones | `content.py`, `waves.py`, `spawning.py`, `world.py`, `data/content.json`, `data/encounters.json`, new `data/zones.json`, `data/progression.json` |
| Simulation/combat | `entities.py`, `simulation.py`, `combat.py`, `enemy_combat.py`, `movement.py`, `manuals.py`, `progression.py` |
| Frontend/presentation | `app.py`, `audio.py`, `presentation.py`, `rendering.py`, new `launch.py`, `__main__.py`, `run_game.py` |
| Runtime art/audio | `assets/manifest.json`, new/updated `assets/actors`, `assets/effects`, `assets/images`, `assets/audio`, `game_icon.png`, `game_icon.ico`; retained sources/prompts/hashes under `art_sources/milestone5` |
| Data/art authoring | `build_encounters.py`, `build_progression.py`, `build_assets.py`, new `build_zones.py`, `build_milestone5_assets.py`, `build_audio.py` |
| QA/reference scripts | `benchmark.py`, `verify_full_run.py`, `verify_progression_loop.py`, `validate_assets.py`, `verify_build.py`, new `verify_release.py`, `catalog.py`, `encounter_catalog.py`, `progression_catalog.py`, new `zone_catalog.py`, `verify_balance.py`, `verify_milestone5.py` |
| Tests | Updated `test_combat.py`; new `test_zones.py` with zone, encounter, settings, audio, healing and beam regressions |
| Release/config | `pyproject.toml`, `__init__.py`, `scripts/check.ps1`, `build.ps1`, `package.ps1`, regenerated PyInstaller spec files |
| Documentation | `README.md`, `GAME_DESIGN.md`, `ARCHITECTURE.md`, `MILESTONES.md`, `SAVE_FORMAT.md`, `ASSET_CREDITS.md`, `ASSET_PIPELINE.md`, catalogs, current `QA.md`, this report, preserved `MILESTONE5_REQUEST.md`, staged screenshots |

Runtime filenames above are under `src/warcraft_survivors/`; builders/tests/docs use their corresponding project directories. Historical milestone requests/reports and prior release ZIPs are preserved.

## Validation and performance

**770 tests passed**, Ruff lint/format and strict mypy passed, original raster/audio validation passed. Forty-four source launch cases and 44 frozen cases per distribution covered all classes/zones, bosses and menus, with no repair assets/missing cues. Native Windows windowed/fullscreen startup passed. The genuine three-process reward → upgrade → reopen loop passed. Details and exact limitations are in QA.md.

Complete final fixed-step campaigns, all without invulnerability/time skips:

| Run | Progression fixture | Survival | Kills | Level | Evolutions | Gold | Class XP |
|---|---|---|---:|---:|---:|---:|---:|
| elwynn | Fresh; one Rank 1 starter | 31:39 | 25,449 | 163 | 4 | 9,744 | 51,279 |
| hunter-elwynn | Fresh; one Rank 1 starter | 31:22 | 25,390 | 163 | 2 | 10,011 | 51,115 |
| duskwood | Advanced talents/shared training; one Rank 1 starter | 30:32 | 25,718 | 172 | 3 | 12,592 | 72,024 |
| stranglethorn | Advanced talents/shared training; one Rank 1 starter | 30:29 | 26,213 | 193 | 4 | 12,934 | 73,726 |
| plaguelands | Advanced talents/shared training; one Rank 1 starter | 30:52 | 26,794 | 215 | 4 | 12,592 | 75,160 |
| icecrown | Advanced talents/shared training; one Rank 1 starter | 30:53 | 27,299 | 241 | 4 | 13,327 | 76,630 |

The four new-zone campaigns use explicitly staged advanced permanent training, then legally develop their in-run arsenal; they are not fresh-character balance certification. All boss attack sets executed. The fresh Hunter lost health and survived its encounter.

Sequential 1920×1080 dummy-SDL stress timings:

| Hunter complete evolved loadout | Before mean ms | Final mean ms | Final P95 ms |
|---|---:|---:|---:|
| 1,000 enemies | 15.26 | 9.82 | 13.45 |
| 3,000 enemies | 48.75 | 28.78 | 45.41 |
| 6,000 enemies | 104.99 | 56.86 | 100.77 |

These are CPU measurements, not measured display FPS. All six developed builds averaged about 9.8–14.8 ms at 1,000 enemies, but extreme crowds and some P95 frames exceed the 60 FPS budget. No damage was skipped to obtain these results.

## Play and limitations

Extract the entire recommended ZIP, then launch `WarcraftSurvivors/WarcraftSurvivors.exe`. From this workspace:

```powershell
.\dist\WarcraftSurvivors\WarcraftSurvivors.exe
```

Source: `.\.venv\Scripts\python.exe run_game.py`. Optional standalone binary: `dist/WarcraftSurvivorsOneFile.exe`. Saves remain under `%LOCALAPPDATA%\WarcraftSurvivors`; logs are adjacent. No Python/network is required for the frozen game. The README documents installation, controls, builds and recovery.

Physical gamepad testing was unavailable (zero devices detected), while synthetic navigation/input tests passed. Subjective speaker/music review, broad human balance certification, other gaming machines/Windows versions and antivirus behavior remain untested. Extreme 3,000–6,000 immortal crowds run below the 60 FPS target here. Some animation is derived, music uses short original loops, builds are unsigned, and each zone currently has one boss. Additional playable classes, multiplayer and cloud saves remain deferred.
