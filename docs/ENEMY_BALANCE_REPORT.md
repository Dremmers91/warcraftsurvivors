# Enemy variety and gameplay balance

Branch: `dremmers/enemy-variety-balance`, starting at main `83cd0fe`.

## Initial audit (recorded before implementation)

Inspected the design/content/zone/encounter/architecture reports; enemy and actor catalogs;
actual zombie, original creature and Lich King atlases; a native 1280×720 Duskwood boss
capture; spawning, wave director, encounter AI, simulation, combat, progression, spatial
hash, rendering, developer tools, asset builders/validator and encounter/reward tests.

| Requirement | Initial status | Changes made | Final status |
|---|---|---|---|
| Eight regular designs per zone | Partial: Elwynn 11; other zones 5 | Add twelve original designs, scheduled in real weighted pools | Complete |
| Three elite variants per zone | Partial: Elwynn 3; other zones 2 | Add four separately armored elite designs with two mechanics each | Complete |
| Detailed sprites and feedback | Complete for shipped creatures; partial silhouette variety | Retain existing art; sixteen additional directional/action atlases, native-zoom review | Complete (derived animation cycles) |
| Simple varied enemy behaviors | Complete: pursuit, flank, ranged, charge, bruiser | Nine warned attack definitions, reuse existing inexpensive primitives | Complete |
| Thirty minute waves | Complete: 30 rows per zone, rising rate/health/XP | Tune late arrivals/HP/surges, preserve director and events | Complete |
| Density and late-game balance | Partial: high ceilings; actual battlefield sometimes sparse | Measure actual peaks and kills; stronger arrivals, unchanged ceilings | Complete as a measured tuning pass; continuous density remains build-dependent |
| Run XP, collection and upgrade pacing | Partial: rising costs and lossless 32px merging; needs measured pacing | Preserve early costs and all drop values; increase post-40 cost term | Complete |
| Permanent progression and attribution | Complete: distinct run/class XP, gold, failure rewards, death ledger | Preserve; test new beast/undead/humanoid deaths and failed rewards | Complete |
| Spell/pet/summon scaling | Complete implementation; representative late probes needed | 90 staged late probes, companion-inclusive arsenals and real campaigns | Complete |
| Elite and boss encounters | Complete: 5-minute elites, 30-minute iconic boss, telegraphs/chests | Preserve; new elite mechanics and chest/reward checks | Complete |
| Additional random bosses supported | Complete: data-driven boss pools | Preserve independent extensible pools | Complete |
| Rendering and collision performance | Partial: caching, batching, culling, spatial hash; load measurement needed | Profile, remove redundant splash/status work, optional spatial metrics | Partial: target-size measurements complete; 6,000 immortal-enemy worst case remains slow |
| Development balancing tools | Partial: speed/time skip and save protection; rates missing | Bounded rolling spawn/kill/XP rates, particles, elites, wave/time and candidate checks | Complete |
| Validation and measured report | Partial: 1,044 existing tests; current milestone coverage needed | Add 35 regression cases, native captures, campaigns and load measurements | Complete |

The existing safety ceiling is 6,000; scheduled ceilings reach 4,600. These are ceilings,
not active targets. Baseline Hunter fixed-step play, legal cards and movement, seed 47:
at 5/10/15/20 minutes there were only 6/10/15/15 living enemies despite increasing
spawn pressure; level 24/50/75/102. Thus raising a ceiling alone cannot fill the screen.
Baseline HP rises from ×1 to ×7.008; XP from ×1 to ×3.175 by minute 29 in Elwynn.
Existing bosses, reward accounting, companion systems and spatial partitioning are retained.

Initial CPU load probes (dummy SDL 1920×1080, medium, 1,600 immortal enemies,
90 measured frames after 30 warmup, eight evolved spells): Hunter 21.06ms mean,
34.51ms P95; Warlock 30.57ms mean, 47.85ms P95. These first probes ran concurrently
with the campaign, so use isolated repeat measurements for before/after comparisons.

## Content and original artwork

There are now **43 regular definitions, 15 elite variants, five initial final bosses
and 73 actor atlases**. All 150 minute rows remain data driven. Every new regular
has positive weights in actual playable waves; all new elites belong to their zone's
random elite pool. No counting-only definitions were added.

| Zone | Regular roster | Elite pool | Initial final boss |
|---|---|---|---|
| Elwynn | Kobold Miner, Forest Wolf, Defias Bandit, Kobold Geomancer, Defias Cutpurse, Defias Marksman, Riverpaw Gnoll, Riverpaw Shaman, Forest Spider, Feral Boar, Enraged Bear | Defias Captain, Riverpaw Packlord, Forest Broodmother | Hogger |
| Duskwood | Rotting Villager, Grave Guardian, Nightbane Hound, Black Widow, Grave Necromancer, **Restless Spirit, Nightbane Stalker, Raven Hill Archer** | Raven Hill Reaper, Black Widow Matriarch, **Nightbane Alpha** | Stitches |
| Stranglethorn | Jungle Raptor, Gurubashi Hunter, Shadow Panther, Jungle Boar, Gurubashi Witch Doctor, **Jungle Gorilla, Crystal Basilisk, River Crocolisk** | Gurubashi High Priest, Raptor Matriarch, **Ancient Silverback** | King Bangalash |
| Plaguelands | Plague Ghoul, Cult of the Damned, Plague Hound, Crypt Fiend, Skeletal Deathguard, **Plague Banshee, Scourge Gargoyle, Plague Abomination** | Plague Commander, Crypt Matriarch, **Furnace Abomination** | Baron Rivendare |
| Icecrown | Frozen Geist, Frost Vrykul, Frost Hound, Frost Acolyte, Frozen Abomination, **Nerubian Soldier, Frost Revenant, Frost Wyrm Hatchling** | Frozen Warlord, Frost Geist Reaper, **Nerubian Lord** | The Lich King |

All existing class, boss, companion, regular and elite sprites remain in use. The
existing terrain, props, effect sprites, hit flashes, death presentation and attack
warnings are retained. Reused hounds/spiders/casters form a minority of the expanded
late pools; the three additions receive 21 of 44 total late weights in each expansion
zone. They first become eligible at 4/8/12 minutes (in roster order).

New original sources are `art_sources/enemy_balance/{duskwood,stranglethorn,plaguelands,icecrown}.png`.
The complete final prompt set and built-in tool method are saved in
[prompts.json](../art_sources/enemy_balance/prompts.json); hashes and reviewed extraction
bounds are in [source_hashes.json](../art_sources/enemy_balance/source_hashes.json).
Each sheet has three regular designs and a separately armored elite, in four directions.
No external asset license was introduced. Runtime outputs are sixteen PNG atlases at
`src/warcraft_survivors/assets/actors/`, with the IDs from that provenance record.

The supplemental builder extracts complete connected silhouettes instead of cutting
an assumed grid. Reviewed rectangles retain the frost revenant's disconnected shards.
The existing derivation pipeline provides four directional walk/idle/cast/death cycles;
this is not hand-authored full creature choreography. Regular sprites use 80px frames,
elite sprites 104px frames, fixed feet anchors and creature-specific art/body sizes.
Flying/shrouded silhouettes, huge knuckles, long reptile bodies, chitin legs and plated
elites are distinct from the retained humanoids and wolves.

Native 1280×720 reviews: [Duskwood](screenshots/enemy-balance/duskwood.png),
[Stranglethorn](screenshots/enemy-balance/stranglethorn.png),
[Plaguelands](screenshots/enemy-balance/plaguelands.png),
[Icecrown](screenshots/enemy-balance/icecrown.png). These are staged real-renderer
captures with a cleared review area so canopy overlap cannot hide a design; normal
world collision/props are unchanged. Source launches separately exercise ordinary maps.

New family classifications: jungle reptiles/gorillas are beasts; the cursed worgen
is humanoid; spirits, skeletons and Scourge additions are undead, including the
**skeletal** frost wyrm. No living dragon boss or demon enemy was introduced, so the
existing future-class availability statements remain valid.

Nine attacks use existing primitives: spectral ring, stalker charge, knuckle slam,
slowing basilisk missile, gargoyle leap, persistent bile pool, nerubian rush, frost
missile volley and wyrm breath arc. Regular warning times are 0.95–1.3 seconds and
cooldowns 7–9 seconds. No individual expensive planner or manual targeting was added.
Third elites combine two warned mechanics and award bonus class XP, gold and an
evolution-eligible chest. The stronger armor penetration/max-health component remains
on boss attacks; it was deliberately not copied onto the new ordinary attacks.

## Spawn and XP curves

Early arrival rates and every density ceiling are unchanged. After minute ten,
`pressure = max(0, minute−10) / 19`; sustained rate multiplies by `1 + .8 × pressure`,
HP by `1 + .35 × pressure`. Minutes 25–29 use surges `600 + 175 × (minute−25)`
instead of `350 + 100 × (minute−25)`. Other surges and damage/speed/XP multipliers
are retained. Expansion zones keep their existing modest zone modifiers.

| Start time | Rate before → after /s | HP before → after | Living ceiling | Surge before → after | XP multiplier |
|---|---:|---:|---:|---:|---:|
| 0:00 | 1.20 → 1.20 | 1.000 → 1.000 | 75 | 0 → 0 | 1.000 |
| 5:00 | 2.80 → 2.80 | 1.600 → 1.600 | 240 | 0 → 0 | 1.375 |
| 10:00 | 6.05 → 6.05 | 2.200 → 2.200 | 665 | 53 → 53 | 1.750 |
| 15:00 | 10.00 → 12.11 | 3.246 → 3.545 | 1,300 | 100 → 100 | 2.125 |
| 20:00 | 15.25 → 21.67 | 4.497 → 5.326 | 2,125 | 190 → 190 | 2.500 |
| 25:00 | 21.00 → 34.26 | 5.859 → 7.478 | 3,200 | 350 → 600 | 2.875 |
| 29:00 | 27.40 → 49.32 | 7.008 → 9.461 | 4,600 | 750 → 1,300 | 3.175 |

Both surges and ordinary batches now obey the 6,000 safety ceiling; neither deletes
existing encounters. Fractional surge rounding was corrected so exactly three seconds
delivers the scheduled count rather than occasionally leaving one pending enemy.
The boss arrives at 30:00; five-minute elites, surviving enemies, weak boss-phase
adds, enrage mechanics and victory requirements remain unchanged.

Run XP costs change only after level 40:
`10 + 7L + 1.6L^1.45 + 3.75 max(0,L−40)^1.65`, previously coefficient `2.5`.
Every gem value and wave/enemy XP multiplier remains intact. Merged gems retain their
sum, old gems still home after 45 live seconds, and the new collected-XP counter counts
awards before level costs (including the permanent XP bonus exactly once).
Class XP/gold/achievement settlement and failure rewards were not retuned.

## Representative gameplay

Seed 47, actual fixed steps, legal cards/manuals/movement, no invulnerability:

| Final-curve run | Outcome / elapsed | Level | Kills | Elites | Evolutions | Largest minute peak | Permanent class XP awarded |
|---|---|---:|---:|---:|---:|---:|---:|
| Fresh Hunter, Elwynn | Victory 30:58.88 | 172 | 36,499 | 5 | 2 | 584 | 71,243 |
| Middle Warrior, Duskwood | Victory 32:26.45 | 188 | 37,535 | 5 | 2 | 740 | 137,076 |
| Advanced Warlock, Icecrown | Victory 31:20.33 | 270 | 39,505 | 5 | 5 | 308 | 145,206 |

Fresh Hunter HP finished at 43.525/115; all four Hogger attack types executed.
Stitches executed hook/cleave/vomit/stomp; the Lich King executed volley/reaper/defile/winter
and reduced the advanced Warlock to 188.8 HP at the 31-minute checkpoint before recovery.
Bosses were not removed, auto-credited or replaced with survival timers.

Fresh Hunter levels at 5/10/15/20/25/30 minutes changed from
24/50/75/102/130/161 to **24/49/74/102/131/170**. Final ten-minute minute-peaks
rose from 157 to 584 with the final tuning. It still obtained 7–9 levels per minute
during the final five minutes, rather than stalling. The faster-arrival intermediate
curve reached level 185 at 30:00; post-40 cost retuning brought that to 170.

The targets in the request are guides, not forced populations: strong legal builds
kill enemies between reinforcement bursts. Final Hunter had 34 living enemies at
30:00 despite a 584-enemy final-minute peak; the middle Warrior had 49 despite a
740 peak. Continuous 1,600-enemy occupancy is **not** claimed for these builds.
Increasing a cap alone would not change this. A future playtest can decide whether
to increase wave cadence further without turning normal enemies into damage sponges.

Twelve real three-minute fresh probes covered all six classes, stationary and moving.
Stationary fresh characters died at 16.95–40.82 seconds; all six moving characters
survived 180 seconds at levels 16–17. Thus stationary power is not an automatic start.
Ninety staged 29:00 probes covered every class/zone with fresh/middle/advanced permanent
profiles, 1,600 ordinary enemies and a developed eight-evolution arsenal. All survived
20 seconds and killed 2,542–2,688 enemies including real reinforcements. Hunter arsenals
included wolves/Stampede; Warlocks included Imps/Hand of Gul'dan. These are explicitly
**staged scaling fixtures**, not evidence that a fresh run can earn eight evolutions.
The staged probes preceded the post-40 retuning; final campaigns use the final curve.

Middle/advanced profiles are separately created QA saves with real talent/shop purchases.
Advanced fixtures seed only shop gate prerequisites so gated purchases can be exercised.
Ordinary player save folders are never used. Campaign settlement now supplies the real
death ledger to the private QA save, including creature/source attribution.

## Performance and developer measurements

Isolated comparisons use archived starting-main code and final code, one process at a
time: dummy SDL, 1920×1080 medium, eight Rank 8 evolved spells, 1,600 immortal enemies,
30 warmup + 180 measured frames. These CPU timings are not hardware/display FPS claims.

| Class | Before simulation / render mean | Final simulation / render mean | Combined mean before → final | P95 before → final |
|---|---:|---:|---:|---:|
| Hunter | 8.94 / 7.62ms | 9.16 / 7.95ms | 16.56 → 17.11ms | 24.64 → 28.52ms |
| Warlock | 18.29 / 15.12ms | 16.64 / 14.68ms | 33.41 → 31.32ms | 50.67 → 46.85ms |

Hunter changed within a small measurement range; no general speedup is claimed.
Warlock's measured simulation improvement is about 9%. Profiling found large secondary
splash-hit fan-out; secondary hits now omit a talent lookup that cannot affect their
damage. Empty status dictionaries avoid a temporary list allocation. Instrumentation
branches sit outside the candidate hot loop when disabled. Real hit order, splash,
DoT transfers, healing, pet hits and death attribution are preserved.

Additional instrumented stress probes (30 warmup, 180 target / 120 ceiling frames):

| Fixture | Enemies | Mean / P95 | Spatial candidate checks/frame | Player / hostile shots | Fields / pets / particles |
|---|---:|---:|---:|---:|---:|
| Icecrown Warlock | 1,600 | 34.24 / 53.48ms | 31,365 | 0 / 634 | 1 / 17 / 5 |
| Elwynn Hunter | 6,000 | 67.85 / 120.15ms | 92,723 | 40 / 55 | 0 / 20 / 55 |
| Elwynn Warlock | 6,000 | 203.10 / 342.46ms | 337,927 | 0 / 107 | 1 / 17 / 1 |

The 6,000 immortal-enemy splash case is a severe CPU limit, **not a responsive 60 FPS
result**. No cap increase or spell damage/interactions reduction was used to hide it.
Target-sized horde fixtures remained stable; normal campaigns continually removed
enemies through actual damage. The immortal benchmark has zero XP gems by construction;
actual campaign gem counts peak at 675/524/735 in the three runs despite tens of
thousands of kills. See the retained [measurement JSON](ENEMY_BALANCE_MEASUREMENTS.json)
for full checkpoint, fixture and entity-count results.

F3 now adds a bounded ten-second rolling spawn/kill/collected-XP rate, living elites,
level/wave/run time, projectile/field/pet/particle/loot counts and spatial candidate
checks. The latter counts hash-query distance candidates, not every narrow-phase hit.
Time skips reset rate history. Spatial counters are ephemeral and disabled in ordinary rendering.
Existing speed/time entry and debug-save exclusion remain in force, including release
debug rejection. Benchmarks add zone, collision instrumentation and capture options.

## Validation and remaining concerns

`scripts/check.ps1`: Ruff lint/format, strict mypy, **1,079 tests**, asset/audio validation,
30 class/zone source starts, five boss starts and nine menu starts. Thirty-five new
cases cover actual roster availability, assets, new classifications/death settlement,
new attack execution/damage, third elite chests, surge safety, rolling rates, spatial
metrics, lossless XP and provenance. The initial surge rounding failure was repaired;
the focused 105-case encounter/overhaul suite then passed.

Reproduce: run `build_encounters.py`, `build_zones.py`, then the supplemental
`build_enemy_balance_assets.py` after the original asset builders; regenerate
`zone_catalog.py`/`encounter_catalog.py`. Use `capture_enemy_rosters.py`,
`verify_enemy_balance.py`, `verify_full_run.py` and `benchmark.py` for the measurements.

Remaining concerns: CPU-heavy immortal splash crowds at the emergency ceiling; late
screen density varies greatly with build and cadence; maxed permanent progression
still yields many fallback reward cards (155 in the advanced campaign); derived
animation cycles can receive a future choreography pass. Human controller playtests,
more seeds and slower hardware measurements remain useful; these three full campaigns
and staged probes do not establish universal balance or a minimum hardware specification.
No next milestone is started.
