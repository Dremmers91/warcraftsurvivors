# Asset credits and acquisition record

## Bundled art

No third-party artwork pack was downloaded or bundled during this overhaul. The new actor, weapon and forest artwork was generated as original project artwork using the built-in OpenAI ImageGen tool, prompted by Codex. Subsequent sprite extraction, fixed-size/alpha processing, derived animation variants, terrain, rune decals, sparks, impact sheets and UI icon/material rasters were created with the project's Pillow build script.

| Asset family | Author/creation | Source | License/attribution record |
|---|---|---|---|
| Six class designs, three enemy designs | OpenAI ImageGen output, directed by Codex | `art_sources/generated/{paladin,warrior,mage,hunter,warlock,priest,kobold,wolf,bandit}.png` | Original generated project art; no asset-pack license or third-party attribution/share-alike obligation imported. Not relabeled as CC0. |
| Holy hammer and heraldic shield | OpenAI ImageGen output, directed by Codex | `art_sources/generated/holy_weapons.png` | Same original-project provenance. |
| Three oaks, bush, fallen log, stones | OpenAI ImageGen output, directed by Codex | `art_sources/generated/forest.png` | Same original-project provenance. |
| Derived animations, grass/road tiles, runes, impacts, spell prototypes, loot, shadows, UI icons/materials | Codex-authored programmatic construction and processing | `scripts/build_assets.py` | Original project source and generated output; no external artwork license imported. |

The exact prompt set and built-in-tool mode are recorded in `art_sources/prompts.json`; original source hashes are in `art_sources/source_hashes.json`. Style references used only previously generated original Paladin artwork. No Blizzard client artwork, audio, models, textures, logos or UI files were extracted. New PNG runtime assets reside under `src/warcraft_survivors/assets/`.

These records describe provenance; the project has not adopted an external CC0 license for its original artwork or issued a new public redistribution license. The user's existing private educational project context remains in place.

## Reputable sources investigated, not imported

All three requested catalogs were inspected: [Kenney](https://kenney.nl/assets/), [OpenGameArt](https://opengameart.org/), and [itch.io free game assets](https://itch.io/game-assets/free). Candidate licenses were checked on their actual author/source pages rather than inferred from “free download.”

| Candidate | Author/source | Verified source-page license | Attribution / redistribution considerations | Decision |
|---|---|---|---|---|
| Tiny Dungeon | Kenney — [source page](https://kenney.nl/assets/tiny-dungeon) | CC0; source page specifies 16 × 16 tiles | Kenney's [support page](https://kenney.nl/support) says attribution is optional; no share-alike condition for this CC0 candidate | Not downloaded: the tiny simplified style does not supply the requested detailed 48–64-pixel principal characters |
| DungeonTileset II | 0x72 / Robert — [author's itch.io page](https://0x72.itch.io/dungeontileset-ii) | Asset license CC0 1.0; author says credit is not required | No attribution/share-alike condition imported; verify extension authors separately if adopting extensions | Not downloaded: 16 × 16 scale and dungeon focus do not match the chosen forest/class art direction |
| LPC Revised Base Object Kit | Death's Darling / Eliza Wyatt; listed contributors Lanea Zimmerman (Sharm), BlueCarrot16 and Hyptosis — [source page](https://opengameart.org/content/lpc-revised-base-object-kit) | CC-BY-SA 3.0, with a page-specific DRM waiver statement | If adopted, preserve per-subfolder contributor credits, license link and change notices; respect share-alike for adapted artwork and the actual included notices | Not downloaded: a multi-author object set with different visual language; original matched artwork chosen |

Because none of these packs was imported, the Windows release does not inherit their asset attribution or share-alike obligations. No arbitrary media URLs or scraped copyrighted images were used.

## Existing software components

CPython, Pygame-ce/SDL and bundled fonts retain their existing component licenses; see `THIRD_PARTY_NOTICES.md`. Pillow is a development dependency for rebuilding PNGs, not a runtime requirement or bundled external artwork source.

## Milestone 2 additions (v0.2.0)

All six original class atlases are now playable. The complete ability roster adds project-authored offline pixel effects, visible status sigils, evolving effects, a chest icon, passive/reward icons, original procedural felguard/dreadguard/imp atlases and a transformed wolf variant. `scripts/build_ability_assets.py` is the reproducible source; it uses no external art pack. Native engraved hammers/shields and the earlier Consecration, Blizzard, Frostbolt and Shadow Bolt artwork remain in use. Evolutions and supplemental spell/summon artwork are functional procedural assets with later production-art polish still needed.

These additions are original project-authored work under the same private educational project terms. Pillow is a build-time tool; no Pillow or image-generation dependency is required while playing. Refer to `CONTENT_CATALOG.md` for asset IDs and `MILESTONE2_REPORT.md` for screenshots and validation. Earlier preview-only statements in historical reports refer to the v0.1.1 build.

## Milestone 3 additions (v0.3.0)

Original Hogger and five Elwynn creature designs were generated with the built-in `image_gen` tool, not extracted from Warcraft. Transparent originals are retained at `art_sources/generated/hogger-walk.png` and `art_sources/generated/elwynn-creatures.png`; exact prompts/method are in `art_sources/milestone3-prompts.json`. These are project assets under the same private educational terms as earlier original art. `scripts/build_encounter_assets.py` derives directional/action sheets, three elite designs, equipment variants and four project-authored hostile projectile atlases. Runtime PNGs are bundled and require no network, source images or image-generation service.

Hogger's generated walking cycle is distinct; derived attack/death and creature gait poses need a future production-art pass. This report does not claim hand-authored choreography or official Blizzard artwork.

## Milestone 5 original art and audio

Ten preserved original image-generation sources live in `art_sources/milestone5/`: four boss walking atlases, one four-zone prop atlas, one eight-species directional enemy atlas, terrain materials, demons, magic effects and Elwynn inn/mill/bridge landmarks. Built-in ImageGen produced these from project-authored prompts; full prompts/method are in `prompts.json` and `elwynn-prompt.txt`, with source hashes in `hashes.json`. Existing original six-class/Hogger/forest art is preserved. `build_milestone5_assets.py` derives 57 total actor registries, themed variants/elites, terrain/props, spell sheets and the Windows icon. Idle/cast/death and some regular-creature gait frames are derived, not fully hand-choreographed animations. No extracted game textures/sprites, random stock packs or downloaded recordings are bundled.

`scripts/build_audio.py` composes project-original music using authored melodies/chords and synthesized bell/string/percussion voices. Five stereo loop tracks and 21 cues are retained as PCM WAVs in `assets/audio`; the manifest records method and file IDs. There are no third-party recording licenses or external musical samples. Runtime playing requires neither Pillow nor an image-generation/audio-generation service. Existing CPython/Pygame/SDL/font notices remain in THIRD_PARTY_NOTICES.md.

## Enemy variety additions

Four original transparent sheets in `art_sources/enemy_balance/` contain twelve new regular creature designs and four separately armored elite designs. Built-in `image_gen` produced them; exact final prompts, method and source hashes are retained in `prompts.json` and `source_hashes.json`. No external art or extracted Warcraft sprites were acquired. These additions use the same private educational project terms as the retained original artwork.

`scripts/build_enemy_balance_assets.py` packs complete reviewed silhouettes (including the revenant's detached floating shards) into sixteen runtime atlases. Directional walk, idle, casting and death frames use the existing deterministic derivation pipeline, rather than hand-authored full animation cycles. Native gameplay-zoom captures are produced by `scripts/capture_enemy_rosters.py`. Existing boss/class/companion/zone art remains intact. To rebuild, run the existing asset builders first and this supplementary builder last; it needs Pillow only at build time.
