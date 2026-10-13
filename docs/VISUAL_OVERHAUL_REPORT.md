# Visual overhaul delivery

## Active game improvements

Replaced primitive Paladin/Kobold/Wolf/Defias sprites with detailed transparent animated raster designs, preserving their exact stats, movement and collision. Added four directional walk views, idle variants, cast feedback, cached damage flash and derived fall/fade deaths. Judgment now throws an engraved silver/gold holy hammer with a visible handle, four aura phases, precomputed flight rotation, optional pooled trails and a textured animated impact. Larger/more numerous rank volleys follow the original calculations; no radial-volley mechanics were invented.

World trees use three distinct textured oak silhouettes with bark, roots and canopy detail. Ground uses cached grass/road rasters, with original roads/obstacles unchanged. Loot uses animated crystal/coin textures; HUD/cards use material textures and raster spell/passive icons. Low/Medium/High quality, optional disabled-by-default screen shake, central asset management, slicing, validation, safe fallbacks and an interactive art gallery are implemented.

## Generated assets and licensing

Eleven original built-in ImageGen source rasters, nine directional actor atlases, seventeen effect sheets and twenty-five standalone images are saved in the project. The six class designs use distinct silhouettes/equipment rather than palette swaps. The game still exposes only Paladin. The prompt set and source hashes are preserved under `art_sources/`; no CLI/API fallback was used.

Kenney, OpenGameArt and itch.io were investigated and candidate licenses checked. No external art pack was downloaded or shipped. See `ASSET_CREDITS.md` for exact source URLs, authors, license checks and original-art provenance.

## Phases and scope

| Phase | Delivered and validated | Remaining / inactive |
|---|---|---|
| A | Audit, art direction, original source acquisition, loader/registry/anchors/cache/fallback/validation | None for the current runtime foundation |
| B | Active Paladin, three Elwynn enemies and Judgment | Blessed Hammer, Avenger's Shield and Consecration have textured animated art previews, not gameplay integration because those spells do not exist |
| C | Active hit, impact, death and damage-text presentation | No remaining active Paladin spells, statuses or elites exist; prototype effects are preview-only |
| D | Six distinct class designs with directional walk/idle and derived cast/death states in the gallery | Five classes remain unplayable; bespoke bow-release/channel/combat/death animation cleanup is not declared finished |
| E | Raster terrain, icon/material cohesion, bounded quality levels and measured density profiles | Artist polish, hardware/display testing and longer VFX soak remain open |

This is a validated overhaul of the active Milestone-1 visuals and asset infrastructure, not a claim that the full six-class end-game presentation or all production animations are complete.

## Verification

74 pytest tests pass, including the original 61 gameplay tests and asset, fallback, presentation non-mutation, caching, animation and quality tests. Ruff lint/format, strict mypy and asset validation pass. Source and packaged launch screenshots are checked; release debug protections remain enforced. PNG loading and runtime projectile rotation are prohibited by tests after renderer initialization.

Sequential 1920 × 1080 dummy-SDL measurements, including simulation/render/scaling, use immortal enemies and max-rank Judgment for sustained work:

| Entities / quality | Simulation mean | Rendering mean | Combined mean | Combined p95 |
|---|---:|---:|---:|---:|
| 400 / Medium | 3.51 ms | 2.09 ms | 5.60 ms | 6.85 ms |
| 900 / Low | 9.14 ms | 3.32 ms | 12.46 ms | 16.63 ms |
| 900 / Medium | 9.21 ms | 3.39 ms | 12.60 ms | 16.86 ms |
| 900 / High | 9.05 ms | 3.33 ms | 12.38 ms | 16.49 ms |

Quality timings overlap within normal run-to-run variation, especially under the crowded-spark cap. These are CPU measurements, not a guarantee of real-display 60 FPS. Ordinary 400-enemy work has useful headroom; near-cap spikes still need hardware profiling. Raw reports are `artifacts/visual-benchmark-*.json`.

## Review artifacts

- `docs/screenshots/before/game.png`, `before/main.png`: preserved primitive baseline.
- `docs/screenshots/after/`: six updated in-game/menu captures using the same staged combat setup.
- `docs/screenshots/previews/actors.png`: six classes and three enemies at 2× source inspection scale.
- `docs/screenshots/previews/effects.png`: holy ground/orbit/shield and spell prototype visual demonstration.
- `docs/screenshots/previews/environment.png`: reviewed standalone forest props.

## Known limits and replacement requirements

AI-generated walk poses can vary equipment/limb placement; idle/cast/death variants are processed derivatives, not fully hand-authored motion. Full bespoke Hunter bow-release, caster channels, enemy bite and species-specific death poses remain artist tasks. Frost/shadow/storm/status examples are starter art prototypes and have no current gameplay hookup. Elites, bosses and companions are not implemented in this game version, so their assets were not invented as finished content. Four directional sprite views serve the existing eight-direction movement.

No major active actor, weapon, loot or environmental object uses the former generic primitive placeholder. Simple bars, panel borders, rune geometry and optional sparks remain appropriate presentation components. Emergency repair graphics are intentionally conspicuous and are not described as polished artwork.
