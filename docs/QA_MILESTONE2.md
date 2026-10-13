# Milestone 2 QA - v0.2.0

Validated on Windows 11 with Python 3.13.15, Pygame-ce 2.5.8, pytest 8.4.2, Ruff 0.13.3, mypy 1.18.2 and PyInstaller 6.22.3.

## Automated checks

- `scripts/check.ps1`: **PASS**. Ruff lint and formatting (44 Python files), strict mypy (20 source modules), **494 pytest tests passed**, all raster validation, and 180-frame launches for each of the six classes.
- Every automatic ability is exercised with actual damage at Rank 1, Rank 8 and its evolved form (180 functional cases), while the player stays stationary. Every spell also has a visible no-target fallback.
- Every automatic definition verifies eight increasing ranks, valid school/evolution metadata and rank/passive/chest evolution requirements. Replacing an original slot prevents re-offering it.
- All 18 manual abilities are activated at all three ranks, with actual immunity/heal/shield/guard/buff/mobility/circle/rally/fear effects, cooldown rejection and pause freezing. All manual-slot alternatives are excluded after discovery.
- Tests cover eight-slot spell/passive caps, branch exclusivity, unique weighted rolls, exhausted rewards, stale-card rejection, XP/levels/gems, armor/damage/immunity, school-specific buffs, actual Bestial Wrath damage, companion ownership/leashes/kill rewards and temporary-health expiry.
- Timing tests compare multiple frame steps for movement, cooldowns, DoTs and manual timers. Area modifies DoT spread; projectile-speed upgrades exclude permanent pet movement.
- Asset checks cover actors, every catalog effect, anchors/poses/alpha/dimensions, cached rotations and missing-art repair. Rendering remains a read-only simulation observer; Low quality preserves essential combat information.

## Runtime integration

`scripts/verify_milestone2.py --seconds 120` completed six deterministic invulnerable progression runs. These demonstrate combat/XP/upgrade integration; they are not balance tests.

| Class | Seconds | Kills | Level |
|---|---:|---:|---:|
| Paladin | 120 | 182 | 12 |
| Warrior | 120 | 180 | 12 |
| Mage | 120 | 182 | 13 |
| Hunter | 120 | 183 | 12 |
| Warlock | 120 | 182 | 10 |
| Priest | 120 | 180 | 12 |

Staged screenshots exercise eight evolved slots, manual abilities, status marks, permanent pets and temporary summons. Class selection, manual discovery and elite-chest evolution decisions were visually reviewed. Screenshot review corrected class-menu text overlap and reduced opaque spell overlays while retaining visible fields and the hero silhouette. The art gallery was launched headlessly and all current pages rendered.

Source launch command: `.\.venv\Scripts\python.exe run_game.py`. Six source launch screenshots: `artifacts/milestone2/source/`. Soak JSON and staged screenshots: `artifacts/milestone2/`. Review copies: `docs/screenshots/milestone2/`.

## Performance

Sequential CPU measurements at 1920x1080, Medium effects, maximum ranks/evolutions and eight high-rank passives. Test enemies and the hero are immortal, so the density persists. Hunter uses a loadout including both wolves and Stampede; Warlock includes felguards and temporary summons.

| Class | Enemies | Mean total ms | P95 ms |
|---|---:|---:|---:|
| Hunter | 400 | 9.30 | 10.86 |
| Mage | 400 | 10.85 | 13.60 |
| Paladin | 400 | 10.05 | 12.96 |
| Priest | 400 | 9.36 | 11.52 |
| Warlock | 400 | 9.71 | 12.60 |
| Warrior | 400 | 10.32 | 13.10 |
| Hunter | 900 | 16.82 | 19.59 |
| Mage | 900 | 22.94 | 28.48 |

The 400-enemy cases fit the 16.67 ms average frame budget in this environment. The 900-enemy maximized Mage case exceeds that budget; the Hunter pet/summon stress case approaches it. These are dummy-SDL CPU results, not hardware FPS certification. Homing target retention, per-tick stat caching, shared equal-size rank rotations and bounded field scaling reduce repeated work without suppressing damage.

## Scope and limitations

The run remains endless. Dedicated boss encounters, a 30-minute victory, new zones, talents/shop screens and additional unlock progression are outside this milestone. The guaranteed-chest elite is a marked tougher Defias contact fighter. Supplemental spell/demon art still needs production polish. Physical controller hardware was not certified; controller navigation, analog input and manual activation were checked through synthetic device events. Local steering can still trap enemies in dense tree clusters. Active runs cannot be resumed after exit.

The source venv prints a harmless interpreter-location warning on this machine; all reported checks and launches returned success. Packaged build validation is recorded below.

## Packaged release

`scripts/build.ps1` completed successfully with PyInstaller 6.22.3. `scripts/verify_build.py` validated packaged raster assets, launched Paladin/Warrior/Mage/Hunter/Warlock/Priest for 180 frames each with exit code 0 and generated six screenshots in `artifacts/milestone2/executable/`. The frozen executable rejected `--debug` with exit code 2. Ordinary saves were not touched; the harness supplied a private save directory.

The release folder is `dist/WarcraftSurvivors/`; keep its `_internal` folder beside `WarcraftSurvivors.exe`. The v0.2.0 archive includes the complete runtime and current catalog/report/QA/asset documentation and screenshots.
