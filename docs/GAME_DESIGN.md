# Warcraft Survivors - implemented game design

Milestone 5 expands the completed six-class survival game to five zones, adds original art/audio, improves menus and profiles performance, and delivers validated Windows builds. `USER_SPEC.md` preserves the original long-term design, `MILESTONE5_REQUEST.md` preserves the current request, and `CONTENT_CATALOG.md` documents every shipped spell, rank and evolution. No AGENTS.md was found in this workspace or its parent directories.

The native Pygame-ce game runs on an 8192 x 8192 finite Elwynn map. WASD/arrows, held left mouse and a gamepad left stick control normalized movement. The camera follows smoothly. Automatic attacks acquire nearby enemies or use last facing; they function while stationary. Space or gamepad A activates a discovered manual ability. No mana, rage, energy or other class resources are used.

| Class | Starter | Health | Movement | Armor |
|---|---|---:|---:|---:|
| Paladin | Judgment | 135 | 215 | 10% |
| Warrior | Mortal Strike | 160 | 220 | 16% |
| Mage | Frostbolt | 95 | 225 | 2% |
| Hunter | Arcane Shot | 115 | 245 | 6% |
| Warlock | Shadow Bolt | 120 | 205 | 7% |
| Priest | Smite | 105 | 220 | 4% |

All six initial classes start unlocked. New/untalented characters have exactly one Rank 1 automatic spell and no manual/passives; advanced preparation can explicitly select one extra starting spell. Each has ten own-class automatic abilities and three possible manual abilities. Equipment capacity is eight automatic spells, eight passives and one manual. Automatic ranks cap at eight, manual ranks at three, passives at five. Passive applicability is explicit in cards and the catalog.

Kills drop visible XP; XP requirements increase with level. Leveling freezes the entire simulation and rolls three weighted distinct eligible cards, or four after permanent Wisdom training. New spells/manuals, rank upgrades, passives and mutually exclusive Rank 4 branches can appear. Full slots and capped/evolved abilities are excluded. Once a manual is discovered its alternatives never appear again that run. When fewer than three regular cards remain, healing, gold and temporary power fill the pool. Overflow XP queues one decision per level.

Judgment, Frostbolt and Shadow Bolt unlock radial volleys at Rank 6. Consecration always follows the player. Execute attacks healthy enemies and gains a low-health bonus. Blizzard travels at first; Eternal Winter persists and follows. DoTs visibly mark targets, prioritize fresh targets and spread from Rank 5. Wolves and demons are autonomous untargetable companions with no health bars, a 320-unit leash and player-owned damage/rewards. Stampede and Hand of Gul'dan create temporary charging summons with swept collision and a larger leash.

The pets/summons overhaul preserves the detailed original wolf, Imp and Felguard artwork. Permanent wolves use Rank 3 leaps, broader high-rank cleaves and cached allied outlines; Alpha Pack adds two wolves. Summon Imp replaces the primary melee Felguard with ranged autonomous Imps that stay near their owner. Eight ranks add damage/frequency, splash at Rank 4, a second Imp at Rank 5, twin bolts/burning at Rank 6 and stronger late ranks. Imp Legion adds two empowered Imps, three-bolt multi-target volleys, homing and larger splash. Rank 8 + Fortitude + an elite chest remains required. `summon_felguard` stays the internal base ID for existing profiles/talents. No separate pet progression is introduced. See `PETS_SUMMONS_AUDIT.md` and `PETS_SUMMONS_REPORT.md` for verification and limits.

Elites appear at 5, 10, 15, 20 and 25 minutes: Defias Captain (volley/bomb), Riverpaw Packlord (charge/shockwave), Forest Broodmother (web/venom). Their own sprites, size, HP, attacks and warnings distinguish them from ordinary enemies. They persist across wave changes, award extra class XP/gold/run XP and always drop chests. Chest choices guarantee an eligible evolution when one exists. Rank 8 plus the named passive at Rank 1 or higher remains required. Evolution replaces the original slot, clears its old projectiles/fields/pets and starts the transformed behavior; existing DoT snapshots can finish.

Demonic Circle places a visible valid-world rune on the first activation, returns from any distance on the second, then starts cooldown. Movement manuals use current movement direction or last facing. Damage immunity, shields, mitigation, healing, buffs, temporary health, fear and rooted Ice Block all have real timed effects and pause consistently.

HUD: health, XP, level, time, kills, gold, eight spell slots/ranks/evolution names, passives, manual cooldown/readiness and active defenses/buffs. The class screen, level cards and menus support keyboard, mouse and controller navigation. Low effects quality retains attacks, field boundaries, statuses, summons and loot.

Thirty minute waves grow from sparse kobolds/wolves into mixed Elwynn hordes, with escalating HP/damage/XP, density and short reinforcement surges. Catalog variants include ranged geomancers/marksmen/shamans, flanking cutpurses, charging boars, heavy gnolls/bears and venom spiders. Scheduled late density reaches 4,600 living foes; damage can keep actual counts much lower. See `ENCOUNTER_CATALOG.md` for exact wave data.

Hogger appears at 30:00 and must be defeated to win. He has distinct directional animation, a large health bar, cleave, charge, leap, shockwave and a half-health enrage. Orange telegraphs warn before damage and lock their aim. Existing enemies/elites remain; weak reinforcements continue. The timer shows 30:00 with additional boss time; results include the full encounter. Death wins no victory bonus but preserves earned rewards. Pause -> Finish records an abandoned run.

Run gem XP and permanent class XP are independent. Gem requirements grow with level; drops scale with wave/enemy XP modifiers. Old distant gems drift after 45 live seconds. Permanent XP banks catalog kill/elite/boss values plus capped survival XP, with 5,000 additional victory XP. Gold includes pickups/catalog bonuses, kill/survival rewards, 1,500 victory gold and first-time achievements. Results save exactly once, using the selected class. Debug runs earn no saved progression. Version 1 saves migrate to version 2 with earned XP/gold retained. Talent/shop/achievement screens are now implemented; additional playable classes remain deferred; five zones now ship.

## Permanent progression

Each class retains its own XP, level, allocated ranks and available points. Class levels use the existing increasing 120 × current level requirement and cap at 100. Each level after 1 awards one point; six distinct 18-node trees offer 40 allocatable ranks each. Tier requirements combine level, spent points and prior-branch prerequisites. Root damage/health/cooldown bonuses are modest, while deep talent branches grant class-specific spell modifications, capstones and optional starting loadouts. Base-ID spell bonuses persist through evolution. Hunter/Warlock never receive a companion automatically: preparation and an explicit choice are both necessary.

Ten shared upgrades have capped ranks and increasing costs. Wisdom unlocks a fourth level card after eight shared ranks and 450 gold. Rerolls give 1–3 charges per run; R/X/button replaces eligible normal cards, preserves pause and cannot reroll chests. Health percentage bonuses affect base class health; in-run health upgrades remain flat. Gold-gain applies to ordinary run rewards, while one-time achievement gold stays fixed. See `PROGRESSION_CATALOG.md` for every effect and cost.

Between-run confirmation screens display exact costs/effects. Reset costs 50 + 5 × allocated ranks, refunds all allocated points and keeps class XP/level. It clears the optional starting ability. Active simulations receive a detached progression snapshot, so purchases cannot mutate a live run. Save failure rolls purchases back.

Thirty-three persistent achievements track total kills/elites/evolutions, best survival, identified Hogger kills, class levels and distinct class victories. Rewards pay once with visible notifications. Future Rogue/Druid/Shaman entries unlock through achievements, not gold; their abilities/content are not shipped yet. Initial six classes and all five shipped zones stay unlocked. Versioned user-data saves keep all progression, counters, registry unlocks and settings, with atomic replacement, a known-good backup, V1 migration, conservative validation and interrupted-write recovery. See `SAVE_FORMAT.md`.

## Milestone 5 zones and balance

Elwynn, Duskwood, Stranglethorn Vale, Eastern Plaguelands and Icecrown are separate finite scrolling maps with themed roads, three named landmarks each, appropriate enemy pools, distinct elites and independent 30-minute schedules. Their iconic final bosses are Hogger, Stitches, King Bangalash, Baron Rivendare and the Lich King. The registry permits additional boss choices later. Stitches combines a pulling hook, cleave, growing/pulsing bile and shockwave; Bangalash pounces, rushes, swipes and roars; Rivendare combines decay pools, shadow volleys, blade and charge; the Lich King uses frost volleys, Reaper, expanding Defile and winter. New boss-specific achievements preserve independent records/rewards. See ZONE_CATALOG.md for exact tuning.

Fresh early runs require movement: tougher wolves/kobolds and a modestly higher early spawn curve prevent an unbuilt hero from idling safely. Early gem collection rapidly develops the first abilities. Requirements gain an extra `2.5 × max(0, level−40)^1.65` term to stretch later build decisions while continuing to reward meaningful levels. Developed, permanently trained builds can clear dense hordes while stationary. Life steal no longer heals from hypothetical overkill and has a shared recovery budget; boss armor penetration, health scaling and wounds keep telegraphed attacks relevant. Boss HP/tempo/attack sets remain distinct across zones. These are initial measured tuning choices, not broad human playtesting certification.

Menus support keyboard/mouse/controller input and scalable window/fullscreen layouts. Independent music and sound volumes, cosmetic density and quality are persisted. Original synthesized zone music and cues cover casts, hits/deaths, elites/bosses, levels, evolutions and menus. Readable panels and warnings preserve contrast over snowy terrain.
