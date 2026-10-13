# Asset pipeline and visual validation

## Runtime versus build-time work

The game loads PNGs from `src/warcraft_survivors/assets/manifest.json` at renderer startup. `AssetManager` centralizes image decoding, path/dimension validation, sheet slicing, trimming, fixed anchors, cached hit variants and precomputed projectile rotations. No gameplay frame loads a texture, generates a complex sprite or rotates a projectile surface. Tests enforce that rule by replacing those functions with failures after initialization.

Runtime requires only Pygame-ce. Pillow is used by `scripts/build_assets.py` to rebuild committed rasters from the original generated source sheets. The built-in ImageGen tool created those sources once; no API key, image-generation call, external art download or Pillow import is required while playing.

## Files and conventions

- `art_sources/generated/`: eleven original RGBA image-generation outputs (nine actors, forest atlas, holy weapons atlas).
- `art_sources/prompts.json`: exact generation prompt set, shared style constraints and built-in-tool mode.
- `art_sources/source_hashes.json`: SHA-256 hashes of preserved original source rasters.
- `assets/actors/`: nine 320 × 1280 sheets. Each 80 × 80 cell has anchor `(40, 73)`; four columns and sixteen rows hold walk, idle, cast and death states, four directional rows per state. Walk poses are generated; idle/cast/death variants are derived offline and remain candidates for hand-animation refinement.
- `assets/effects/`: seventeen transparent animated weapon, rune, projectile prototype, impact, status and loot sheets.
- `assets/images/`: twenty-five texture, prop, shadow, spark, fallback, UI material and icon PNGs.
- `assets/manifest.json`: explicit image dimensions, frame anchors, actor speeds/active flags, projectile art sizes/rank scales and cosmetic profile data.

Actor source sheets are sliced with fractional grid boundaries because image generation can return dimensions not divisible by four. Visible alpha is cleaned before downsampling and anchors are normalized. Forest sprites are separated by connected alpha components, preserving complete canopies instead of guessing grid boundaries or importing neighbors' stray fragments. Runtime atlases use exact integer dimensions. Avoid rescaling every actor to the same proportions: Paladin 62 source pixels tall, Warrior 64, casters roughly 63, Hunter 60, Bandit 57, Kobold 46, Wolf at most 36 with a longer side silhouette.

Frames are trimmed once while retaining adjusted anchors. Walking/idle loop; cast/death select bounded non-looping phases. Direction is chosen from actual world motion or the player's existing facing. Pauses freeze cosmetic ages with simulation time. Four directional views serve the unchanged eight-direction movement controls.

## Read-only presentation

`Presentation` observes position, health and projectile identity without mutating the simulation. It derives facing, walking, cast feedback, cached hit flashes, short death fades and floating damage text. Its private random generator and reusable particle pool never consume gameplay randomness. A serialized-state test proves that drawing at all three quality settings leaves health, XP, enemies, projectiles, drops, choices, timer, kills, camera and PRNG state unchanged.

The optional two-pixel screen shake is disabled by default and affects only a render offset; it never writes the simulation camera or input math. Creature health bars remain informational UI, not independent combat entities.

## Layers

1. Cached textured grass/roads and low vegetation.
2. Future ground-decal/AoE textures (demonstrated in the separate art gallery).
3. Cached tree/actor ground shadows.
4. Animated gem/coin loot.
5. Y-sorted trunks, enemies and cosmetic death frames.
6. Player above crowded enemies for readability.
7. Animated/pre-rotated physical hammer projectiles.
8. Bounded spark trails, textured impacts and damage text.
9. Material-backed HUD and menus.

Tree artwork retains the existing obstacle trunk position and collision circle. Cosmetic art scale is independent from physics: Judgment's art grows from a visual baseline of 38 pixels using its own rank scale; its actual collision radius/damage/cooldown and volley geometry are unchanged. Ground-effect previews follow their displayed owner and use cached translucent runes, without adding absent spells to gameplay.

## Quality settings

Settings offer Low, Medium and High, persisted with conservative validation. Low disables optional trail particles and floating damage numbers. Medium/High allow 120/240 pooled sparks and larger cosmetic death/text budgets. Crowds above 500 enemies limit optional sparks to 64. All qualities render every live visible actor, every projectile, readable hit feedback, loot and impacts. Cosmetic budgets never skip damage or collision queries.

## Commands

```powershell
.\.venv\Scripts\python.exe scripts\build_assets.py
.\.venv\Scripts\python.exe scripts\validate_assets.py
.\.venv\Scripts\python.exe scripts\preview_assets.py
```

The gallery has actor, effects and environment pages. Keys: 1–3 choose page; arrows choose facing; A chooses walk/idle/cast/death; R cycles visual rank; Space pauses; Escape exits. It never unlocks classes, changes run content or executes damage. Generate still previews with:

```powershell
.\.venv\Scripts\python.exe scripts\preview_assets.py --headless --frames 1 --output docs\screenshots\previews
```

`scripts/check.ps1` now includes asset validation. The validator checks file locations, RGBA mode, exact sheet/frame sizes, alpha, unclipped aligned poses and distinct walk frames. Package data rules and PyInstaller explicitly include the asset directory. Source and packaged smoke tests verify the artwork is available without the source-art folder.

## Fallbacks and remaining production work

A missing/corrupt PNG falls back to the bundled detailed Paladin raster and reports an asset-repair notice. Missing registry/all fallback art still leaves a clearly marked magenta repair image so the app can run; this emergency image is not production artwork. Tests cover individual missing/corrupt files and a malformed registry.

The earlier graphics-only phase contained Paladin/Judgment and three active enemies; its preview-only restrictions are historical. Milestones 2 and 3 now activate the six-class ability roster and full encounter catalog. Some generated gait/equipment consistency and derived attack/death poses require an artist cleanup pass; future Hunter bow-release, caster channel and creature-specific authored death animations are explicit replacement requirements. Do not treat those derived variants or inactive effect prototypes as complete production combat animation.

## Milestone 2 extension

Run `scripts/build_assets.py` to rebuild the original base assets and then the complete ability/summon registry. `scripts/build_ability_assets.py` is the offline supplementary builder. Preserve `scripts/build_content.py` and the explicit JSON tables, then regenerate `docs/CONTENT_CATALOG.md` with `scripts/catalog.py` after gameplay changes. The gallery now exposes all classes, pets and every spell/evolution/manual via paginated sheets.

Equal-sized projectile rank frames share cached rotations; native Judgment still has independent rank art scaling. Melee directions are rotated during loading. Effect surfaces use a 64 MiB bounded cache and support subdued opacity for overlapping fields; the hero is drawn above effects. Status icons and companion markers remain visible at Low quality. Native assets remain available with safe image/registry repair fallbacks. No runtime file decoding, rotation, generation or network access is needed.

## Milestone 3 encounter assets

`build_assets.py` invokes the base, ability and encounter builders in order. `build_encounter_assets.py` also updates an existing manifest directly. Two retained original transparent source atlases were created with built-in image generation: `art_sources/generated/hogger-walk.png` and `art_sources/generated/elwynn-creatures.png`. Full exact prompts and generation method are preserved in `art_sources/milestone3-prompts.json`; hashes are in `source_hashes.json`. No API key, CLI imagegen fallback or runtime generation is involved.

Hogger uses a four-direction/four-phase walk source, 120-pixel cells and derived idle/cast/death poses. Gnoll, shaman, spider, boar and bear use four original directional poses with derived gait/action frames. Geomancer, cutpurse, marksman and Captain adapt the retained base sprites with equipment/color details; Packlord and Broodmother adapt the new creature sources with size/palette changes. Four hostile projectile atlases have cached directional rotations. All 25 actor sheets have validated alpha, anchors, bounds and distinct walk frames. Art scale is independent of collision radius. Production-specific cast/death choreography and perfect eight-leg/quadruped gait remain artist-polish tasks.

Boss animation and warnings use `elapsed`, which continues after the campaign timer reaches 30:00. Low quality preserves all gameplay telegraphs and hostile projectiles. Inspect `docs/screenshots/milestone3/` for staged warning, elite, evolution and result screens; their staged counters are not full-run balance evidence.

## Milestone 5 pipeline

1. Preserve the original inputs under `art_sources/milestone5/`, including exact prompts and hashes.
2. Run `build_content.py`, `build_encounters.py`, `build_zones.py`, `build_progression.py` in that order when regenerating data.
3. `build_assets.py` now runs base → ability → encounter → M5 builders. `build_milestone5_assets.py` can update an existing manifest directly.
4. `build_audio.py` independently composes the original WAV library.
5. Validate with `validate_assets.py`; it checks raster dimensions, RGBA, alpha, anchors, walk-pose distinction, icon presence and every audio file's PCM header.
6. Run `verify_milestone5.py` for labeled staged UI/map/elite/boss/choice screenshots, separate from full-run proofs. Regenerate catalogs with `catalog.py`, `encounter_catalog.py`, `zone_catalog.py`, `progression_catalog.py`.
7. Build and validate the packaged runtime with `build.ps1` / `verify_build.py`. Resource decoding warnings or missing original cues fail smoke QA.

All 57 actor atlases are original or derived from retained original artwork; the three earlier procedural demon silhouettes are replaced. Four new bosses have genuine generated four-direction/four-phase walking sources. New maps use original terrain tiles with subdued contrast, themed props and named landmarks. The Elwynn inn/mill are obstacles; the bridge is traversable decoration. Telegraphed warnings remain code-drawn geometric indicators deliberately, because their exact hit regions must stay readable; these are gameplay information, not placeholder actors.

Effect density adjusts optional pooled sparks, floating numbers and death effects. It never suppresses an enemy, projectile, hazard warning, damage tick or collision query. The HUD uses dark panels over bright maps. Five zone music loops are streamed; 21 original sound cues are preloaded and bounded. The application icon is derived from the original golden-hammer art.
