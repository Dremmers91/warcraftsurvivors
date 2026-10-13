# Milestone 5 QA — Windows v0.5.0

Validated on Windows 11 x64 using Python 3.13.15, Pygame-ce 2.5.8 and PyInstaller 6.22.3. No AGENTS.md was present. Earlier milestone reports preserve historical results.

## Automated checks

**PASS: 770 tests in 86.72 seconds**, Ruff lint/format (69 Python files), strict mypy (26 runtime modules), all original raster/audio/icon validation. The final beam/body-edge regression and all ability tests also passed as a 454-case focused check before rebuilt releases.

Coverage includes XP/movement/damage, all 60 spells at low/high/evolved configurations, every rank/evolution contract, all 18 manuals and three ranks, pets/ownership/leashes, every talent/shared upgrade, purchase/reset rules, achievements, save migration/corruption/interruption/rollback, exact rewards and victory/death conditions. New checks exercise all 30 class/zone combinations, every schedule, elite overlaps/chests, new boss attacks, hooks/slows/pulsing/growing fields, high-defense boss damage, actual-damage/bounded healing, beam collision with a large body beyond its endpoint, theme cache isolation, cosmetic read-only behavior, zone navigation, audio fallback and settings migration.

Keyboard, mouse and controller behavior is tested through Pygame events and input-provider fixtures, including viewport mapping, diagonal/analog math, navigation, pause/manuals and choices. Physical gamepads detected on this environment: **0**. Hardware controller testing is therefore not claimed.

## Actual campaigns and progression loop

Every campaign below advances every real fixed step, with legal card choices, movement and manual inputs. None uses invulnerability, time skips, injected in-run ranks or forced boss health. Each killed five elites and its final boss; all four boss attacks executed. New-zone runs intentionally start with a private advanced permanent-progression fixture, bought through normal purchase APIs after injecting fixture XP/gold. They still start with one Rank 1 ability and learn the run build legally.

| Run | Progression fixture | Survival | Kills | Level | Evolutions | Gold | Class XP |
|---|---|---|---:|---:|---:|---:|---:|
| elwynn | Fresh; one Rank 1 starter | 31:39 | 25,449 | 163 | 4 | 9,744 | 51,279 |
| hunter-elwynn | Fresh; one Rank 1 starter | 31:22 | 25,390 | 163 | 2 | 10,011 | 51,115 |
| duskwood | Advanced talents/shared training; one Rank 1 starter | 30:32 | 25,718 | 172 | 3 | 12,592 | 72,024 |
| stranglethorn | Advanced talents/shared training; one Rank 1 starter | 30:29 | 26,213 | 193 | 4 | 12,934 | 73,726 |
| plaguelands | Advanced talents/shared training; one Rank 1 starter | 30:52 | 26,794 | 215 | 4 | 12,592 | 75,160 |
| icecrown | Advanced talents/shared training; one Rank 1 starter | 30:53 | 27,299 | 241 | 4 | 13,327 | 76,630 |

Proofs: `artifacts/milestone5/campaign-final/*/full-run.json`. Early/final checkpoints and exact attack counts are preserved; these are simulation proofs rather than human playtest certification. The fresh Hunter finished with about 105 health, demonstrating a survivable boss encounter with actual damage and a movement manual.

`verify_balance.py` tested all six fresh classes for three minutes with movement, and all six stationary fresh characters died at roughly 17–41 seconds. A staged advanced 29:00 fixture with 1,200 initial enemies plus real reinforcements cleared roughly 1,745–1,751 kills per class over 20 seconds while stationary; all six survived. Fixtures explicitly preload developed equipment/talents and do not claim those upgrades were earned during that probe.

The independent three-process loop produced genuine deaths at 1:34 and 1:58, earning a total of **123 gold / 250 class XP**. A second process confirmed the **65-gold** Endurance purchase. A third reopened with **58 gold**, unchanged class XP, one Judgment starter and **139.05 starting health**. See `artifacts/milestone5/loop.json`; the loop is also a pytest case.

## Profiling and performance

Profiles retained at `artifacts/milestone5/before.prof` and `after.prof` identified steering, repeated spatial queries and redundant obstacle resolution as the largest simulation costs. Raw timings below are separate, sequential, unprofiled runs without competing validation/build jobs. They render a 1280×720 canvas and scale to 1920×1080 on dummy SDL, with eight maximum-rank evolved abilities and immortal test enemies. They measure CPU frame work, **not hardware/display FPS**.

| Hunter complete evolved loadout | Before mean ms | Final mean ms | Final P95 ms |
|---|---:|---:|---:|
| 1,000 enemies | 15.26 | 9.82 | 13.45 |
| 3,000 enemies | 48.75 | 28.78 | 45.41 |
| 6,000 enemies | 104.99 | 56.86 | 100.77 |

| Class at 1,000 enemies | Simulation ms | Rendering/scaling ms | Combined ms | P95 ms |
|---|---:|---:|---:|---:|
| Paladin | 5.32 | 7.37 | 12.68 | 21.02 |
| Warrior | 5.31 | 9.35 | 14.66 | 20.94 |
| Mage | 5.74 | 9.03 | 14.78 | 19.64 |
| Hunter | 4.86 | 4.95 | 9.82 | 13.45 |
| Warlock | 5.62 | 7.59 | 13.21 | 18.31 |
| Priest | 4.98 | 7.12 | 12.09 | 17.41 |

The 6,000-enemy Hunter stress mean improved about 46%; Low quality measured 52.79 ms / P95 88.86 ms. The 60 FPS target is a 16.67 ms budget: typical 1,000-enemy means meet it, but some P95 frames and the extreme 3,000–6,000 immortal crowds exceed it here. No smaller enemy ceiling or skipped damage ticks hides that limit. Ordinary developed-run counts were much lower because enemies could die. Modern gaming-hardware certification and prolonged GPU/display measurements remain outstanding. CPU model access was unavailable in this sandbox.

## Windows distributions and native launches

**PASS: onedir and optional onefile builds; 44 frozen scenarios each**, including 30 class/zone combinations, five boundary/boss launches and nine menu/progression screens at 180 fixed frames per case. All bundled art decoded without repair warnings; all 21 sound cues and zone music loaded. Frozen `--debug` exited **2**; QA logs were created outside the executable. Integrity fingerprints accompany the validation reports in `artifacts/milestone5/executable*/validation.json`.

The final onedir executable additionally launched with real Windows SDL in both 1920×1080 windowed and fullscreen profiles for 120 frames, producing native captures. Saves/logs were isolated under `artifacts/milestone5/native`; no ordinary profile was replaced. This verifies native startup/rendering, not manual hardware-input playtesting.

**PASS: both release ZIPs passed full CRC validation and extracted executable startup.** Each was launched from its extracted directory with no source tree and a System32-only PATH (no Python installation lookup). Binary/runtime fingerprints and final ZIP SHA-256 values are in `artifacts/milestone5/release-validation.json`. Documentation-only repackaging rechecks every CRC and requires the embedded runtime hashes to match the previously booted distribution.

## Reproduce and limits

Run `scripts/check.ps1`, `verify_balance.py`, `verify_full_run.py`, `verify_progression_loop.py`, `verify_milestone5.py`, then `build.ps1`, `verify_build.py`, and `package.ps1`, followed by `verify_release.py`. The README gives full commands and optional onefile verification. Packaging rejects binaries/resources changed since verification.

Staged screenshots under `docs/screenshots/milestone5/` cover all map/elite/boss warnings, menus, choices and results; their counters are fixtures. Review found and fixed snow/HUD contrast issues. Original music is composed as short loops; subjective speaker/music review remains unperformed. Several gait/cast/death frames are derived and could benefit from artist cleanup. Builds are unsigned; Windows SmartScreen/antivirus behavior and other Windows versions/machines were not certified. Multiple bosses per zone, further playable classes, cloud saves and multiplayer remain deferred. No next milestone was started.
