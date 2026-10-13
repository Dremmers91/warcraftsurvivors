# Visual audit — baseline before the overhaul

The current runtime is Milestone 1: Paladin, Judgment, Kobold, Wolf and Defias Bandit. No Blessed Hammer, Avenger's Shield, Consecration, other class spells, pets, elites or bosses exist in gameplay. Their artwork may be prepared and previewed, but visual work must not add or change their mechanics.

## What is on screen

- Characters are 32 × 42 surfaces made from rectangles and ellipses. The Paladin is stretched to 40 × 52, with a flat colored shirt, basic face and a tiny sword; the plate, shoulders, tabard and holy hammer silhouette are missing.
- Kobold and bandit share the same humanoid geometry; the candle and shirt palette are their main differences. The wolf has a quadruped outline, but its anatomy, fur and gait need replacement.
- Actors have no directional animation frames. Enemies only bob by a sine offset; the player is static, so walking and facing do not read correctly.
- Judgment is a procedural two-rectangle hammer with a line trail. Its size directly follows collision radius, and cached rotations are created lazily during combat. The object reads more like a bright bar than an engraved metallic weapon.
- Impacts and hit immunity use plain expanding circle outlines. XP gems are diamond polygons. Enemy death is a generic circle, with no species-specific animation.
- Terrain is a patchwork of 16-unit flat tiles plus per-chunk grass lines. Trees are enlarged ellipses and a rectangle trunk. Neither actors nor terrain load authored raster sprites.
- HUD panels and menu artwork are generated from primitives; labels and hierarchy are serviceable, but class/spell/passive icons and material texture are absent.

## Infrastructure to reuse

The finite world, smoothed camera and pointer scaling are correct and stay intact. The 256-unit terrain cache, bounded text cache, off-screen culling, fixed-step simulation and existing spatial collision lookup are useful. Keep those boundaries while replacing generated geometry with preloaded raster artwork. The player already draws above crowds, which helps readability.

## Performance risks

Lazy hammer rotations allocate surfaces in the combat path. Grass/tree detail is inexpensive because terrain chunks are cached, but image loading, per-enemy tinting/scaling or frame construction inside large entity loops would be a regression. Animation frame, hit-flash and death variants should be prepared once. Cosmetic particles need a bounded reusable pool and quality budgets independent from damage/collision.

## Baseline evidence

Existing automated checks pass (61 tests). Before-overhaul screenshots are saved under `docs/screenshots/before/`. The earlier dummy-SDL benchmark included body steering and collision, averaging approximately 5.09 ms at 400 enemies and 10.89 ms at 900 enemies; remeasure the new renderer with the same harness before comparing.

## Phase applicability

A: audit/style/loading/validation; B: active Paladin, three enemies and Judgment, plus preview-only hammer/shield/holy-ground assets; C: active damage/death/impact presentation, with inactive spell examples kept out of gameplay; D: distinct art-only class registry/previews; E: raster terrain, iconography, quality settings and profiling. Report inactive integrations and artwork limitations explicitly rather than claiming gameplay implementations that do not exist.

## Milestone 2 production follow-up

All six classes and the full ability roster now have functional runtime assets. See `MILESTONE2_REPORT.md` and `docs/screenshots/milestone2/` for current visual verification. Existing engraved weapons, rune fields and original character designs are preserved. New supplemental effects and demon poses remain procedural art pending further hand-authored polish; this implementation does not retroactively declare every production-art cleanup item in the earlier audit complete.

## Milestone 3 follow-up

Eleven ordinary variants, three larger elite designs and an original animated Hogger now have runtime art. Four hostile projectiles and telegraphed line/cone/circle/ring attacks remain visible at every quality setting. The large boss bar, running boss-time counter, qualified chest cards and eight-field death/victory results are captured under `docs/screenshots/milestone3/`. Captures are staged; the genuine legal-input full-run report is `artifacts/milestone3/full-run.json`. Boss animations were regression-tested beyond 30:00 after fixing use of the stopped campaign timer. Artist cleanup of derived action/death/gait poses remains outstanding.
