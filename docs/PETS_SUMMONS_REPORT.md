# Pets and summons overhaul — completion report

Implemented on `dremmers/pets-summons-overhaul`, created directly from local `main`. No commits or pushes were made. This report covers the supplied overhaul prompt only; the next four prompts remain pending on the same branch. Initial evidence and classifications are recorded in [PETS_SUMMONS_AUDIT.md](PETS_SUMMONS_AUDIT.md).

| Requirement | Initial status | Changes made | Final status |
|---|---|---|---|
| Mandatory asset/system/documentation audit | Missing | Inspected actual wolf/Imp atlases, prior gameplay captures, combat/rendering/targeting/rewards/profile/build systems and docs before implementation | Complete |
| Permanent pets are automatic ability effects | Complete | Preserved CompanionSpell and regular equipped-slot ownership | Complete |
| Invulnerable, untargetable, no health bars | Complete | Preserved healthless entities and player-only hostile targeting; tested contact/projectiles across pet positions | Complete |
| No pet XP/equipment/commands/talent trees | Complete | Preserved owner-only progression and equipment | Complete |
| Configurable leash and automatic return | Partial | Mechanics-defined leash; spawn/formation bounds; owner teleport return; filter enemies before selection | Complete |
| Automatic nearby targeting | Partial | Retain targets, invalidate dead/out-of-leash targets promptly, favor local clusters at later ranks | Complete |
| Ability rank and applicable passive scaling | Partial | Reuse stats cache; preserve Might/Haste/Reach/Multicast/meta buffs; Velocity affects Imp bolts without changing wolf movement | Complete |
| Player damage/kill/XP/gold/achievement attribution | Complete | Preserve shared hit/death/settlement paths; test pet kills through gem collection and saved first-blood achievement/class XP/gold | Complete |
| Hunter remains a wolf, original good art preserved | Complete | Reused wolf and brighter alpha_wolf atlases without rewriting them | Complete |
| Clear allied distinction from hostile wolves | Partial | Cached subdued one-pixel outline and small ground marker; native forest/jungle screenshots inspected | Complete |
| Wolf idle/movement/bite/slash/hit/summon feedback | Partial | Select idle when stationary; keep walk/cast poses; use existing directional cleave overlay, enemy hit feedback and summon rune | Complete functional; authored animation polish remains |
| Responsive late-rank melee attacks | Partial | Faster rank-scaled movement, stopping inside reach, Rank 3 bounded leap, wider ranked cleaves and longer Alpha Pack leaps | Complete functional; broader balance playtesting remains |
| Warlock primary ranged Imp | Missing | Reused original detailed Imp with horns/limbs/claws/tail/fel accents; stays in owner formation and casts firebolts | Complete |
| Eight Imp ranks | Missing | Damage/frequency ranks, splash R4, second Imp R5, twin bolts/burning R6, improved R7 range/frequency, empowered R8 blasts | Complete |
| Imp Legion through evolution/chests | Missing | Preserve Rank 8 + Fortitude + chest requirement and slot replacement; add two empowered Imps, three-bolt multi-target volleys, homing and larger splash | Complete |
| Preserve Felguard artwork for future content | Complete | Retained Felguard/Dreadguard PNGs and registries; neither is the primary permanent Warlock pet | Complete |
| Ranged attack travel, splash, target groups and high-rank coverage | Missing | Fast cached firebolts, rank-gated splash/burning, distinct legion target directions and bounded target selection | Complete functional; broader balance playtesting remains |
| Useful while stationary | Partial | Both pets attack stationary crowds; staged Rank 1/8/evolution scenarios deal verified real damage | Complete |
| Avoid expensive global per-frame pet searches | Partial | SpatialHash queries every 120–165 ms with immediate stale-target repair; local one-pass density scores and shared spell stats | Complete |
| Actual loading/scaling/facing/origin/visibility/quality verification | Partial | Rendered 30 fixed-step companion scenarios across all five terrains at three qualities; checked native screenshots and cached idle/move/cast/projectile paths | Complete functional; derived sprite polish remains |
| Multiple pets, save compatibility and regression coverage | Partial | Added 18 companion cases; existing profile reopen test verifies retained Warlock ID now summons Imps; existing ownership tests process ranged projectiles | Complete |

## Assets and definitions

Reused gameplay artwork: `actors/wolf.png`, `actors/alpha_wolf.png`, `actors/imp.png`, `effects/fireball.png`, `effects/fireball_evolved.png`, `effects/cleave.png`, `effects/summon.png`, existing shadows and spark/impact feedback. Retained `actors/felguard.png` and `actors/dreadguard.png`, including their existing temporary-summon uses.

Created gameplay raster assets: **none**. Replaced gameplay raster files: **none**. Allied edge variants are prepared in memory once during asset loading. Four representative QA PNGs are saved in `docs/screenshots/pets-summons/`; the other staged captures and numerical evidence stay under ignored `artifacts/pets-summons/`.

Modified definitions: **Beast Companion / Alpha Pack** and **Summon Imp / Imp Legion**. The latter retain internal IDs `summon_felguard` / `summon_felguard_evolved` for existing preparation selections and base-ID talent bonuses. Its school is now fire. No save schema migration is needed. The class starter remains Shadow Bolt; companions still require an ability selection. Velocity's applicability text now includes Imp firebolts. Rebuilt content/progression catalogs and added effect aliases to the reproducible asset pipeline.

## Verification

- `scripts/check.ps1`: **788 tests passed**, Ruff lint/format and strict mypy passed, all raster/audio validation passed, and **44 source launch smoke cases passed** (30 class/zone combinations, five boss cases and nine screens).
- `scripts/verify_companions.py`: **30 staged five-second fixed-step scenarios** passed (two classes × five zones × Rank 1/Rank 8/evolution); each form renders at Low/Medium/High. No missing-asset repair warnings. Tests also exercise runtime idle/move/cast selection and forbid image decoding/projectile rotation after initialization.
- `scripts/benchmark_companions.py`: sequential companion combat timing, including actual collision, splash, burning/status work; excludes enemy AI/grid rebuild/rendering.
- `scripts/benchmark.py`: sequential complete evolved Hunter/Warlock stress tests with 6,000 immortal foes at 1920×1080 and Low quality; 120 measured frames after warmup.
- Final lint/format and `git diff --check` passed. HEAD is still the same commit as `main`.

Tests cover healthless/invulnerable/untargetable pets, configurable leash/teleport return, filtering before target selection, stale target replacement, throttled local queries, rank counts, hand-height projectile origin, near-owner formation, splash/burn unlocks, wolf leaps/cleave, passive/meta/manual-buff projectile scaling, chest replacement, multi-direction legion volleys, kill/gem/class-XP/gold/achievement settlement, saved starting selections, cached art and Low-quality effects.

Representative in-game evidence:

- [Allied wolf alongside hostile wolves at native zoom](screenshots/pets-summons/elwynn-hunter-rank1.png)
- [Imp Legion casting orange firebolts in Elwynn](screenshots/pets-summons/elwynn-warlock-evolution.png)
- [Imp Legion on snow at Low quality](screenshots/pets-summons/icecrown-warlock-evolution-low.png)
- [Rank 8 wolves against jungle terrain](screenshots/pets-summons/stranglethorn-hunter-rank8.png)

These are actual renderer captures after simulation steps, with staged loadouts and immortal foes. The staged fixture is not an earned campaign or normal profile.

## Damage and performance findings

The original weakness came from slow melee pursuit, searching every fixed step, selecting an invalid out-of-leash nearest enemy before filtering, and letting traveling spells/fields resolve before ready pet attacks. Permanent pets now attack before traveling projectiles/fields update, immediately reconsider dead targets, and use rank-gated reach/mobility or ranged coverage. Instant spell casts still retain their normal order.

In the five-second stationary Elwynn fixture, without passive bonuses and with identical 24-target positions:

| Companion | Rank 1 damage / targets hit | Rank 8 damage / targets hit | Evolved damage / targets hit |
|---|---:|---:|---:|
| Wolf | 240 / 2 | 4,944.79 / 8 | 12,445.79 / 8 |
| Imp | 72 / 3 | 3,825.25 / 7 | 28,110.23 / 16 |

These totals include real cleave/splash/burning, not theoretical DPS, and demonstrate the increased high-rank footprint. Rank 1 wolf damage remains unchanged; Rank 1 Imp starts at 18 damage every 1.6 seconds before bonuses. None of these measurements prove all possible mixed builds are balanced.

Sequential isolated combat timings (maximum ranks/applicable passives, static immortal crowd):

| Scenario | Enemies | Permanent pets | Combat mean ms | Combat P95 ms |
|---|---:|---:|---:|---:|
| Empty combat/status baseline | 1,000 | 0 | 0.075 | 0.091 |
| Alpha Pack | 1,000 | 10 | 0.175 | 0.455 |
| Imp Legion | 1,000 | 9 | 0.387 | 1.790 |
| Empty combat/status baseline | 6,000 | 0 | 0.554 | 0.600 |
| Alpha Pack | 6,000 | 10 | 1.003 | 2.590 |
| Imp Legion | 6,000 | 9 | 1.609 | 3.007 |

The query test measured at most 12 local candidate queries per second for one living-target Imp, versus the old 60 fixed-step acquisition queries, while retaining immediate dead-target repair. No pet search enumerates the global enemy list. Full evolved-loadout stress timings include enemy AI, all spells, hostile attacks, terrain and rendering: Hunter **55.74 ms mean / 96.08 ms P95**, Warlock **171.41 ms mean / 291.92 ms P95** at 6,000 immortal foes. These extreme crowds exceed the 16.67 ms / 60 FPS budget; companion-only timing is much lower. Results are dummy-SDL CPU measurements, not display FPS. Earlier concurrent exploratory runs were excluded from these tables.

## Remaining limitations

The preserved wolf and Imp idle/cast/death poses are derived from original artwork. They function in-game with timed casting, slash and impact effects, but still merit an artist's anatomy/gait/attack-pose cleanup. The one-pixel allied edge avoids a permanent glow; fully hand-authored collars/armor were unnecessary to distinguish the existing models.

Native renderer/headless smoke coverage does not substitute for human controller/visual/balance playtesting. No new full 30-minute campaigns or packaged binaries were produced for this source change. Existing `dist` builds remain v0.5.0. Extreme full-loadout crowds retain the performance limits above. Instant spell casts can still clear a target before a companion's turn; this patch improves mobility/coverage/targeting without adding artificial damage credit for already-dead enemies.

The four later prompts have not been started. All changes remain uncommitted on the requested branch.
