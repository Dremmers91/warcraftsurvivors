# Warcraft Survivors — Visual Overhaul and Asset Pipeline

You are responsible for upgrading the graphics of Warcraft Survivors from a primitive Pygame prototype into a visually coherent, detailed fantasy pixel-art game.

The current graphics are unacceptable as final assets:
- Characters are too basic to identify their classes.
- Enemies are visually unclear or strangely shaped.
- Weapons and spells are rendered as generic circles, dots, or other primitives.
- Ability effects are not recognizable.
- The world lacks the visual quality expected of a detailed fantasy survival game.

This is a GRAPHICS AND PRESENTATION milestone, not a gameplay redesign.

Preserve the existing game mechanics, class definitions, ability calculations, progression, player movement, and collision behavior.

## 1. First, audit the existing game

Inspect:
- The current rendering implementation.
- Player sprites and class visual definitions.
- Enemy sprites and animations.
- Spell and projectile rendering.
- AoE graphics.
- Existing assets.
- Texture loading and caching.
- Camera rendering.
- Asset-related performance bottlenecks.

Document the current problems in `docs/VISUAL_AUDIT.md`.

Identify which visuals use generic primitives and which already use proper textures.

Do not assume the current asset system must be discarded; reuse good infrastructure where appropriate.

## 2. Establish an art direction

Target detailed, modern 2D pixel art with a slightly angled top-down or 3/4 perspective.

Visual inspiration:
- Death Must Die.
- Halls of Torment.
- Classic Warcraft fantasy character silhouettes.

The game should feel like a polished fantasy bullet-heaven game rather than an abstract arcade prototype.

Requirements:
- Recognizable characters and enemies.
- Consistent sprite scale.
- Consistent viewing angle.
- Clear silhouettes.
- Distinct equipment and weapons.
- Detailed but readable combat effects.
- Smooth sprite animations.
- Cohesive color palettes.
- Transparent-background sprite assets.
- Pixel-perfect or visually appropriate texture scaling.

Aim for approximately 48–64 pixels of source-art height for principal player characters, subject to testing at actual gameplay zoom.

Do not enforce the same size on every creature. Wolves, kobolds, humans, and bosses should have visibly different proportions.

Use an art style guide to prevent inconsistent asset additions.

## 3. Asset acquisition and creation

Investigate reputable sources of free game art, including:

- https://kenney.nl/assets/
- https://opengameart.org/
- https://itch.io/game-assets/free

Prefer CC0 assets when suitable.

Other openly licensed assets may be used if their conditions are understood and followed.

For every downloaded asset:
- Confirm its actual license.
- Record the source URL.
- Record the author.
- Record required attribution.
- Record any share-alike or redistribution obligations.
- Save the license information in `docs/ASSET_CREDITS.md`.

Do not assume all free-to-download artwork is free to redistribute.

Do not scrape arbitrary copyrighted graphics, extract Blizzard client assets, or depend on undocumented asset URLs.

Where a suitable free asset is unavailable, create an original asset using appropriate image generation, sprite editing, or programmatic image construction.

Tools such as Pillow can be used to produce sprites, texture atlases, transparency, composited layers, and animation frames.

Important: generating images programmatically must not become an excuse to continue using simple circles and rectangles as final visual assets.

If a sufficiently detailed asset cannot be produced in the current environment, create a clearly identified replacement requirement and continue improving the remaining assets. Do not falsely claim that primitive placeholders are polished artwork.

Use downloaded or original raster sprites at runtime, not expensive per-frame generation of complex artwork.

## 4. Player character graphics

Implement visually distinct animated characters for:

- Paladin
- Warrior
- Mage
- Hunter
- Warlock
- Priest

Each class must be recognizable without its name displayed.

Visual requirements:

Paladin:
- Heavy plate armor.
- Gold and silver accents.
- Holy-themed visual details.
- Hammer or appropriate martial weapon.

Warrior:
- Heavy armor.
- Large sword or axe.
- Physical combat visual identity.
- Stronger, more aggressive silhouette.

Mage:
- Robes.
- Staff or magical implement.
- Arcane or frost-colored details.
- Clearly recognizable caster silhouette.

Hunter:
- Bow or ranged weapon.
- Lighter armor.
- Ranger appearance.
- Distinct ranged combat animations.

Warlock:
- Dark robes and fel/shadow accents.
- Visually distinct from Mage.
- Shadow-themed equipment and colors.

Priest:
- Light or ceremonial robes.
- Holy-themed accents.
- Distinct silhouette from Mage and Warlock.

Implement:
- Idle animations.
- Directional movement animations.
- Hit feedback.
- Appropriate attack/casting feedback where useful.
- Class-appropriate outlines or accent colors.

Movement animation must reflect the character's direction.

Do not rely exclusively on recoloring one identical silhouette for every class.

## 5. Enemy graphics

Replace primitive enemy graphics with recognizable fantasy creatures.

Begin with all enemy types currently implemented in Elwynn Forest.

Examples:
- Kobolds with distinct heads and candles or mining equipment.
- Wolves with quadruped silhouettes.
- Defias bandits with humanoid outfits and weapons.
- Gnolls with hyena-like features.
- Boars and spiders with appropriate body shapes.
- Elites with identifiable enhanced appearance.
- Bosses with distinctive large sprites and animations.

Different enemy species must have different visual identities.

Requirements:
- Idle/walk animation.
- Directional facing or appropriate sprite flipping.
- Damage flash.
- Death animation.
- Distinct visual outlines.
- Appropriate sprite scaling.
- Readable silhouettes when enemies overlap.

Elites should receive subtle additional visual treatments, such as special outlines, accents, or aura effects.

Bosses should have substantially more detailed artwork and attack animations than normal enemies.

Do not turn all enemies into recolored humanoids.

## 6. Spell and weapon graphics

This is a critical requirement.

Every implemented ability must have a recognizable visual representation based on what the spell actually does.

Do not represent a physical object such as a hammer, shield, sword, axe, arrow, or meteor as a colored circle.

Physical projectiles must look like the object being thrown.

Magic projectiles must have distinctive shapes, internal texture, and animation.

Use sprite textures, animation frames, rotation, alpha transparency, additive light effects where supported, particle trails, and impact animations.

### Blessed Hammer

Current problem:
A plain yellow circle or dot orbits the player.

Required:
- A recognizable hammer sprite.
- Visible hammer head and handle.
- Metallic body with holy/golden accents.
- Appropriate rotation while orbiting.
- Clear impact feedback.
- Optional holy trail.
- Increasing number of visible hammers as the ability ranks up.

The hammer must remain recognizable at actual gameplay scale.

### Avenger's Shield

Current problem:
A simple dot travels and bounces.

Required:
- A recognizable shield sprite.
- Clear shield shape and central emblem or ornamentation.
- Metallic border.
- Holy glow.
- Spinning or rotating flight animation.
- Small impact burst when it hits an enemy.
- Visible directional changes when it bounces.

Its art size must be independent from the projectile's collision radius.

### Judgment

Required:
- Recognizable holy hammer projectile.
- Golden-white energy accent.
- Distinct impact flash.
- Additional hammers visibly appear as the rank increases.
- Higher ranks produce increasingly wide and radial volleys.

### Consecration

Current problem:
A circle with generic dots.

Required:
- An animated holy ground effect attached to the Paladin.
- Subtle textured golden runes or geometric holy markings.
- A translucent ground pattern.
- Pulses of holy energy.
- Small rising or drifting particles.
- Clear visible radius.
- Larger and more detailed effects at higher ranks.

Consecration always follows the Paladin.

Use a combination of a cached ground texture, animated overlays, and limited particle effects.

### Divine Storm

Required:
- Large sweeping arcs of holy energy.
- Distinct rotational or radial movement.
- Clearly visible activation.
- Bright but readable holy impact effects.

### Frostbolt

Required:
- Recognizable icy projectile.
- Crystal or shard structure.
- Frost trail.
- Shattering impact.
- Slow/freeze indicator on affected enemies.

### Blizzard

Required:
- Defined storm area.
- Animated falling ice shards.
- Snow and frost effects.
- Distinct ground coverage.
- Traveling storm movement before evolution.
- A persistent player-following storm after evolution.

### Shadow Bolt

Required:
- Dark purple or black-purple magical projectile.
- Recognizable swirling shadow shape.
- Shadow trail and impact burst.
- Expanded volleys as the ability ranks up.

### Damage-over-time abilities

Corruption, Rend, Serpent Sting, and similar abilities must have identifiable effects.

Examples:
- Corruption: purple cursed aura, dark runes, or shadow marks.
- Rend: red slash marks and brief bleed effects.
- Serpent Sting: poison mark and green particles.
- Immolate: orange burning effect.

Status effects should remain visible without creating an excessive number of full particle simulations.

### Pets

Permanent companions must use animated creature sprites.

Examples:
- Hunter wolf with walk and bite animations.
- Warlock Felguard with appropriate movement and melee attacks.

Pets remain invulnerable, untargetable ability effects.

Do not render pet health bars.

## 7. General spell effect system

Design reusable visual components for:
- Projectile sprite animation.
- Projectile rotation.
- Particle trails.
- Impact bursts.
- Ground decals.
- Persistent AoE textures.
- Radial shockwaves.
- Slashes.
- Glows.
- Screen shake.
- Status marks.
- Evolution transformations.
- Damage flashes.
- Summoning effects.

Visual behavior should be configured through data where appropriate.

Separate damage and collision logic from visual presentation.

A projectile sprite may be visually larger or smaller than its collision area.

The same gameplay ability must continue to work if cosmetic particles are reduced.

## 8. Rendering layers

Implement consistent rendering order.

Suggested layering:
1. Ground terrain.
2. Ground decals.
3. Consecration and ground AoE effects.
4. Ground shadows.
5. Loot and pickups.
6. Enemies and companions.
7. Player.
8. Projectiles, melee effects, and elevated attacks.
9. Overhead effects and visual particles.
10. Damage text and indicators.
11. HUD and menus.

Use appropriate Y-sorting for world entities where it improves depth perception.

Ensure ground effects appear below characters rather than obscuring them completely.

## 9. Performance

Do not sacrifice late-game performance for cosmetic complexity.

Required:
- Cache loaded textures.
- Precompute rotation frames where useful.
- Avoid loading images during combat.
- Pool particles.
- Reuse animation frame references.
- Cull off-screen objects.
- Avoid expensive Python drawing operations inside large enemy loops.
- Use lower-cost effects when the screen is extremely crowded.
- Maintain full gameplay damage and collision accuracy.

Add configurable effects quality:
- Low
- Medium
- High

Low effects quality may reduce cosmetic particles but must not remove essential visual indicators or affect spell damage.

Target 60 FPS during normal gameplay.

Measure performance under high enemy and projectile counts.

## 10. Asset pipeline and maintainability

Create or improve:

- A centralized asset manager.
- A sprite/animation registry.
- Sprite-sheet slicing utilities.
- Texture caching.
- Consistent rendering scales.
- Asset validation.
- Fallback handling for missing images.
- A development asset preview tool.

Create documentation:

- `docs/ART_DIRECTION.md`
- `docs/ASSET_CREDITS.md`
- `docs/VISUAL_AUDIT.md`
- `docs/ASSET_PIPELINE.md`

Where practical, include visual comparison screenshots in `docs/screenshots/`.

## 11. Implementation order

Do not replace every graphic at once.

Work in this sequence:

Phase A:
- Inspect current rendering.
- Establish art direction and asset standards.
- Build sprite-loading and animation infrastructure.

Phase B:
- Replace Paladin with a recognizable animated character.
- Replace the existing Elwynn enemies.
- Upgrade Judgment, Blessed Hammer, Avenger's Shield, and Consecration.

Phase C:
- Upgrade the remaining implemented Paladin spells.
- Add visual effects for damage, impacts, status effects, and elites.

Phase D:
- Apply the sprite system to Warrior, Mage, Hunter, Warlock, and Priest.
- Replace their currently implemented spell visuals.
- Create consistent visual definitions for future abilities.

Phase E:
- Improve environmental art, UI iconography, and overall cohesion.
- Profile and optimize dense combat.

Complete and validate each phase before treating it as finished.

Do not advance through unfinished phases while reporting them as completed.

## 12. Acceptance criteria

The graphics milestone is successful when:

- The Paladin is recognizable as a Paladin without a text label.
- The Warrior, Mage, Hunter, Warlock, and Priest have distinct visual designs when implemented.
- Kobolds, wolves, bandits, and other Elwynn enemies are distinguishable.
- Blessed Hammer visibly resembles a hammer.
- Avenger's Shield visibly resembles a shield.
- Judgment visibly throws hammers.
- Consecration resembles holy ground magic rather than a plain circle.
- Spells produce animated visual effects.
- Animations remain correct when the player moves.
- The game does not crash when an asset is unavailable.
- Graphics render correctly after camera movement.
- Visual effects scale appropriately with spell rank.
- Low graphics settings preserve essential combat information.
- Existing gameplay, damage, progression, and collision behavior remain intact.

Run the test suite and perform gameplay validation.

Report:
- Visual systems added.
- Assets added or generated.
- Licenses and attribution recorded.
- Abilities upgraded.
- Screenshots or preview sheets created.
- Performance measurements.
- Remaining visual placeholders.
- Known limitations.

Do not describe the overhaul as complete while major visible objects are still generic primitive placeholders.