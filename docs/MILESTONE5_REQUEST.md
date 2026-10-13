# Milestone 5 — Content Expansion, Polish, Optimization, and Windows Build

Read all existing project documentation and inspect the current implementation.

This milestone turns the working survival game into a polished Windows desktop experience.

Do not discard or rewrite functioning systems unnecessarily.

## 1. Additional zones

Implement large, scrolling, finite maps for:
- Duskwood.
- Stranglethorn Vale.
- Eastern Plaguelands.
- Icecrown.

Preserve Elwynn Forest.

Each map needs:
- Distinct terrain and visual identity.
- Original recognizable environment artwork.
- Roads and landmarks.
- Appropriate enemies.
- Distinct elite variants.
- Increasing difficulty.
- One iconic final boss.
- A 30-minute wave schedule.

Suggested initial bosses:
- Elwynn Forest: Hogger.
- Duskwood: Stitches.
- Stranglethorn Vale: King Bangalash.
- Eastern Plaguelands: Baron Rivendare.
- Icecrown: The Lich King.

Balance each boss for its particular zone rather than copying identical statistics and attacks.

Create a data-driven boss registry to support multiple possible final bosses per zone in future updates.

## 2. Art and animation

Replace temporary geometric placeholders with original, coherent pixel-art assets.

Prioritize:
- Playable characters.
- Regular enemies.
- Elite enemies.
- Bosses.
- Spell projectiles.
- Spell impacts.
- Ground effects.
- Companions.
- Environmental tiles.
- UI icons.

Keep combat effects readable at high enemy density.

Use consistent sprite scales, outlines, animations, and visual palettes.

All six classes must be visually distinguishable.

Visual effects should become more impressive as abilities gain ranks or evolve.

Maintain a consistent original fantasy pixel-art direction rather than mixing unrelated stock assets.

## 3. Menus and interface

Polish:
- Main menu.
- Class selection.
- Zone selection.
- Level-up cards.
- Run HUD.
- Boss health bars.
- Treasure chest interface.
- Talents.
- Achievements.
- Shared upgrades.
- Results.
- Settings.

Support:
- Mouse.
- Keyboard.
- Gamepad.
- Scalable resolutions.
- Windowed and fullscreen modes.

Use clear fonts, suitable spacing, readable tooltips, and coherent visual hierarchy.

## 4. Audio

Implement a reusable audio system.

Include original or appropriately licensed:
- Background music.
- Spell effects.
- Hit effects.
- Enemy death sounds.
- Elite and boss encounter cues.
- Level-up sounds.
- Evolution sounds.
- Menu sounds.

Support separate music and sound volume controls.

The game must remain functional if audio playback fails.

## 5. Optimization

Profile rather than guessing about bottlenecks.

Prioritize:
- Enemy updates.
- Projectile collision checks.
- DoT processing.
- AoE collision checks.
- Rendering.
- Particle systems.
- Map chunk rendering.
- Object creation and destruction.

Use spatial partitioning, pooling, caching, and batching where useful.

Maintain the full gameplay effect of damaging abilities while reducing unnecessary cosmetic work.

Target 60 FPS on modern gaming hardware at 1920×1080.

Produce performance measurements for escalating enemy counts.

Add a configurable visual-effects density setting without reducing actual combat damage.

## 6. Balancing

Review:
- All six classes.
- All automatic ability pools.
- All manual abilities.
- Eight-rank progression.
- Passives.
- Evolutions.
- Enemy scaling.
- Elite encounters.
- Boss encounters.
- XP progression.
- Permanent talents.
- Gold economy.

Ensure:
- Early runs require active dodging and movement.
- Midgame builds gain momentum.
- Advanced permanent progression enables powerful late-game builds.
- Strong builds can eventually survive dense hordes while stationary.
- Bosses retain meaningful mechanics.
- Unsuccessful runs still reward permanent progression.

## 7. Windows executable

Create a repeatable PyInstaller build process.

Requirements:
- Windows .exe output.
- All required resources bundled.
- No separate Python installation needed to play.
- Correct resource path handling when packaged.
- Persistent saves stored outside the executable.
- No development-only debug tools enabled by default.
- Meaningful application icon.
- Helpful error messages and logging.

Prefer an onedir distribution initially for reliability. Add a onefile build if it works reliably.

Include a script for creating a release package.

## 8. Final validation

Test:
- All six classes.
- All zones.
- All available spells.
- Manual abilities.
- Pets.
- Evolutions.
- Talents.
- Achievements.
- Save/load.
- Win/loss results.
- Keyboard and mouse controls.
- Gamepad support.
- Windows executable startup.
- Packaged asset loading.

Run automated tests and fix failures.

Document any tests that cannot be executed on the current platform rather than claiming they passed.

Deliver:
- The packaged Windows game if built on Windows.
- Build scripts.
- Installation and execution instructions.
- User controls.
- Known limitations.
- Final test results.
- Updated developer documentation.

Do not declare the milestone complete unless the actual game and its packaged distribution have been validated.