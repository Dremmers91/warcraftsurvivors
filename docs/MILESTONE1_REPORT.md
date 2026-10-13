# Milestone 1 completion report

## Implemented

Paladin with keyboard, held-mouse and analog movement; normalized diagonals; health/contact damage/hit immunity; smooth camera; finite textured Elwynn terrain and obstacle collision; three data-defined enemies with weighted increasing spawns, local avoidance/separation, damage/death and XP drops; stationary auto-targeted Judgment hammer projectiles; reusable projectile/area strategies; increasing XP and three unique paused upgrade cards with actual gameplay effects; required HUD; protected source-only development controls; source/Windows build tools and validation.

The former broad class/spell prototype was narrowed to the approved milestone. The save format stays compatible, with no legacy starting-stat modifiers. No next milestone was implemented.

## New files

- `src/warcraft_survivors/camera.py`
- `src/warcraft_survivors/combat.py`
- `src/warcraft_survivors/debug.py`
- `src/warcraft_survivors/movement.py`
- `src/warcraft_survivors/progression.py`
- `src/warcraft_survivors/spawning.py`
- `tests/test_debug.py`
- `tests/test_movement.py`
- `tests/test_spawning.py`
- `docs/MILESTONE1_REPORT.md`

## Changed files

- `src/warcraft_survivors/app.py`
- `src/warcraft_survivors/audio.py`
- `src/warcraft_survivors/content.py`
- `src/warcraft_survivors/data/content.json`
- `src/warcraft_survivors/entities.py`
- `src/warcraft_survivors/rendering.py`
- `src/warcraft_survivors/simulation.py`
- `src/warcraft_survivors/upgrades.py`
- `src/warcraft_survivors/world.py`
- `tests/test_app.py`
- `tests/test_combat.py`
- `tests/test_upgrades.py`
- `scripts/benchmark.py`
- `scripts/capture_screens.py`
- `scripts/soak.py`
- `scripts/verify_build.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/MILESTONES.md`
- `docs/QA.md`

Generated outputs include updated source screenshots, performance/soak JSON, a refreshed `dist/WarcraftSurvivors/` executable folder and the Windows ZIP. Generated outputs are excluded by `.gitignore`.

## Validation and limitations

See `QA.md` for the checks, test results, benchmark figures and known limitations. The focused pytest suite covers XP, damage, upgrade eligibility and movement calculations, plus integration and debug protection. No AGENTS.md existed in the repository or its parent folders; README and the architecture/milestone/QA documentation were read before changes.

## Exact play command

From `C:\Users\Razorpony\Documents\_coding\projects\WoWSurvivors`:

```powershell
.\.venv\Scripts\python.exe run_game.py --demo
```

To use developer controls from source, append `--debug`. The packaged release rejects that option.
