# Warcraft Survivors — Milestone 5 (v0.5.0)

A native Windows/Pygame survival game with six classes, 60 automatic spells, 18 manual abilities, 12 passives, 60 evolutions and five complete survival zones. Elwynn Forest, Duskwood, Stranglethorn Vale, Eastern Plaguelands and Icecrown each have a finite 8192×8192 scrolling map, original terrain/landmarks, appropriate hordes, elites and a final boss. Persistent class talents, shared upgrades and achievements carry between runs.

The current source branch adds the [pets and summons overhaul](docs/PETS_SUMMONS_REPORT.md): allied wolves with rank-gated leaps, ranged Summon Imp with eight ranks and Imp Legion, retained detailed artwork and compatible profiles. Existing v0.5.0 release executables remain the previous build; use the source command below to play these changes.

## Play the Windows release

Extract **all** of `dist/WarcraftSurvivors-0.5.0-Windows.zip`, then double-click `WarcraftSurvivors/WarcraftSurvivors.exe`. Keep `_internal` beside the executable. No Python installation, network access or asset downloads are needed.

The optional `WarcraftSurvivors-0.5.0-Windows-OneFile.zip` contains `WarcraftSurvivorsOneFile.exe`. It extracts its embedded runtime to Windows temporary storage during launch; saves/logs use the same external profile. The onedir package remains the recommended distribution.

From this workspace:

```powershell
.\dist\WarcraftSurvivors\WarcraftSurvivors.exe
```

The source command remains:

```powershell
.\.venv\Scripts\python.exe run_game.py
```

Choose your class to play the selected zone (Elwynn initially), or use **Choose zone** first. A direct source launch example:

```powershell
.\.venv\Scripts\python.exe run_game.py --demo --class mage --zone duskwood
```

| Action | Keyboard | Mouse | Controller |
|---|---|---|---|
| Move | WASD / arrows | Hold left click toward cursor | Left stick |
| Equipped manual | Space | Space while moving with mouse | A |
| Pause / resume | Escape | Pause menu | Start |
| Browse menus/cards | Arrows / WASD / Tab | Hover | Stick / D-pad |
| Select | Enter / Space; 1–4 for cards | Left click | A |
| Reroll level cards | R | Reroll button | X |
| Back / cancel | Escape | Back / Cancel | B |

Diagonal movement is normalized; analog movement has a deadzone and proportional speed. Losing focus pauses gameplay. Window resizing uses letterboxing with correct mouse coordinates. Settings provide fullscreen, four window resolutions, independent music/sound volumes, quality, cosmetic effect density and optional screen shake. Essential attacks and warnings remain visible at every quality/density.

## Runs and progression

New champions start with exactly one Rank 1 spell: Judgment, Mortal Strike, Frostbolt, Arcane Shot, Shadow Bolt or Smite. Attacks fire automatically, including while stationary. Collect gems and select one paused upgrade card. Equip up to eight automatic spells, eight five-rank passives and one three-rank manual. Automatic spells have eight ranks; Rank 4 opens a Force/Reach branch. Manuals use Space/A and cooldowns; there are no class resource meters.

Elites appear at 5/10/15/20/25 minutes, persist into later waves and drop guaranteed chests. An evolution requires **Rank 8 + the specified passive + selection from a chest**. Qualified chests guarantee an eligible evolution among three choices. Evolving replaces the original slot. Hunter wolves and Warlock demons are invulnerable, leashed allies; learn them during the run or explicitly select a starting companion after unlocking an advanced preparation talent. New characters receive no automatic pets.

At **30:00**, the final encounter begins: Hogger, Stitches, King Bangalash, Baron Rivendare or the Lich King. Victory requires killing that boss while alive; the timer alone never ends the run. Watch locked warnings, charges, expanding rings, persistent pools and frost slows. Boss attacks penetrate some armor, scale partly with maximum health and briefly wound automatic recovery. Shields and manual immunity remain useful. Failed and abandoned runs retain earned class XP/gold; victory adds 5,000 class XP and 1,500 gold, plus boss and achievement rewards.

Each class has separate permanent XP/levels and an 18-node talent tree with prerequisites. Every class level after the first grants one point. Reset costs **50 + 5 × allocated points** gold, shown before confirmation; it returns points, preserves XP and clears any selected extra starter. Ten shared upgrades improve all classes. Wisdom unlocks a fourth normal card after eight shared ranks and 450 gold; chests keep three. Rerolls refresh normal choices with R/X. The chronicle tracks 33 achievements, including the four added bosses. Rogue/Druid/Shaman unlock through achievements, but their playable content is deferred.

Normal saves live at `%LOCALAPPDATA%\WarcraftSurvivors\save.json`; logs are in the adjacent `logs` directory. Version 1/2 saves remain compatible, with atomic commits, backup/temp recovery, conservative validation and future-version preservation. All five shipped zones are available to new and migrated profiles. Active runs are not resumed after closing. Back up the user-data folder to move progression.

## Development and validation

The workspace virtual environment is ready. For a fresh checkout use 64-bit Python 3.11–3.14, then:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check.ps1
.\.venv\Scripts\python.exe scripts\verify_balance.py
.\.venv\Scripts\python.exe scripts\verify_full_run.py
.\.venv\Scripts\python.exe scripts\verify_progression_loop.py
.\.venv\Scripts\python.exe scripts\verify_milestone5.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build.ps1
.\.venv\Scripts\python.exe scripts\verify_build.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\package.ps1
.\.venv\Scripts\python.exe scripts\verify_release.py
```

For the optional single executable: run `scripts/build.ps1 -OneFile`, validate with `scripts/verify_build.py --executable dist/WarcraftSurvivorsOneFile.exe --output artifacts/milestone5/executable-onefile`, then use `scripts/package.ps1 -IncludeOneFile`. Packaging checks that validated binary/resource hashes still match.

The check script covers Ruff, strict mypy, pytest, original raster/audio validation and 44 source launch scenarios. Frozen verification exercises the same class/zone matrix, all bosses and menus, resource loading, logs and debug rejection. Full-run proofs advance every real fixed step with legal cards/movement/manual inputs. Private fixtures and staged captures are identified in their reports; normal profiles are untouched.

Rebuild content in order: `build_content.py`, `build_encounters.py`, `build_zones.py`, `build_progression.py`. Rebuild all raster assets with `build_assets.py` (includes M5), and original audio with `build_audio.py`. `build_milestone5_assets.py` updates an existing registry from retained sources. Regenerate references with `catalog.py`, `encounter_catalog.py`, `zone_catalog.py`, `progression_catalog.py`. Pillow and image generation are development-only; the game uses bundled assets.

Source developer tools require `--demo --debug`. F3 counts/FPS; F4 acceleration; F5 XP; F6 spawn; F7 kill; F8 invulnerability; F9 wave; F10 zone elite; F11 zone boss; F12 run gold; T paused time entry. Modified runs cannot save progression. Frozen/release builds reject debug opt-in with exit code 2.

See [final QA](docs/QA.md), [M5 report](docs/MILESTONE5_REPORT.md), [zone catalog](docs/ZONE_CATALOG.md), [ability catalog](docs/CONTENT_CATALOG.md), [progression catalog](docs/PROGRESSION_CATALOG.md), [save recovery](docs/SAVE_FORMAT.md), [architecture](docs/ARCHITECTURE.md), [art/audio provenance](docs/ASSET_CREDITS.md) and [asset pipeline](docs/ASSET_PIPELINE.md).

Known limits: extreme 3,000–6,000 immortal-enemy stress cases exceed the 60 FPS budget on this environment; see measured CPU timings in QA. Physical-controller testing and subjective speaker/music review require user hardware. Several gait/cast/death poses are derived from original directional art. More bosses per zone, additional playable classes, multiplayer and cloud saves are deferred. The Windows build is unsigned and may prompt SmartScreen.

Private educational, non-commercial fan project; not affiliated with Blizzard Entertainment. No extracted Blizzard artwork or stock art packs are bundled. No next milestone is started automatically.
