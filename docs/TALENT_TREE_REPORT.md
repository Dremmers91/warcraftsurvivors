# Class talent tree overhaul — completion report

Implemented on `dremmers/class-talent-tree-overhaul`, based on main after the pets/summons PR was merged. The [initial audit](TALENT_TREE_AUDIT.md) records inspection before modification. The supplied screenshot inspired the connected square-icon layout and rank counters; none of its artwork was copied. This report covers the talent-tree prompt only.

| Requirement | Initial status | Improvements / preserved functionality | Final status |
|---|---|---|---|
| Six small class trees | Complete | Retained 18 stable node IDs and 40 total ranks per class | Complete |
| Vertical branching, 3–4 tiers, central path, final capstone | Partial | Four tiers; central Might → Duration → Preparation → Capstone path, side branches, one final capstone | Complete |
| Square readable icons | Missing | 64-pixel nodes using retained original spell/manual frames and class actor art | Complete |
| Visible prerequisite connections | Partial | Routed paths and arrow ends drawn before nodes; active prerequisites use class color | Complete |
| Grayscale unavailable nodes | Partial | Cached grayscale icon variants for unlearned locked nodes | Complete |
| Purchasable and maxed states | Partial | Gold available borders, double teal maxed frames, numerical rank badges and explicit detail states | Complete |
| Class-themed backgrounds | Partial | Six data-defined palettes and retained landmark/prop backgrounds | Complete |
| Hover / selection / visible focus | Partial | Hover updates the numerical detail panel; independent hover/focus edges; selected node survives purchase return | Complete |
| Damage/health/armor/cooldown/area/projectile stats | Complete | Preserved all functioning effects and supplemented missing projectile bonuses | Complete |
| Movement stat talents | Partial | Recovery nodes gain +1.5% movement per rank in every class, retaining regeneration | Complete |
| Class ability modifiers | Partial | Added actual delayed waves, spread, splash, opening-strike and volley-width behavior; tests prove damage/coverage changes | Complete |
| Permanent XP/levels and talent points | Complete | Existing class XP curve, level cap, one point per level after 1 and remaining point display retained | Complete |
| Prerequisites/tier gates/multi-rank/capstone validation | Complete | Preserved point/level thresholds and caps; four-tier paths use weaker original ancestors | Complete |
| Invalid purchase prevention and transaction safety | Complete | Existing eligibility revalidation and save rollback retained and covered by tests | Complete |
| Gold respec and confirmation | Complete | Exact 50 + 5 × spent cost, confirmation/cancel, insufficient funds, point refund, retained XP/level and persisted reset | Complete |
| Mouse/keyboard/gamepad navigation | Complete | Compact geometry feeds existing spatial input; click sets focus; D-pad/A/B and keyboard verified | Complete |
| Prerequisite explanations / exact benefits | Partial | Current and next cumulative talent benefits, level/spent thresholds, prerequisite ranks and blocking reason | Complete |
| Stable class/icon/position/rank/effect data | Partial | Explicit metadata, cumulative per-rank effect tables, capstone flag, class styles and loader validation | Complete |
| Supported-resolution usability | Partial | App output captured at 1280×720, 1600×900, 1920×1080 and 2560×1440; scaled mouse/controller flows tested | Complete |
| Persistence and existing-save compatibility | Complete / Partial | V2 IDs/caps/gates retained; 180 legal legacy allocations and starting choices preserved; conservative V1 migration retained | Complete |
| Automated unlock/prerequisite/gameplay validation | Partial | Added 35 new tree/modifier/input cases, retained all existing meaningful-effect and respec tests | Complete |

## New and changed nodes

**New node IDs: none.** All 108 existing class nodes receive icon/position/rank-table metadata and four-tier presentation. Names, caps and working effects are preserved except three signature names noted below. Every original bonus continues to work; the additions supplement it.

Stable IDs retained in each class: `might`, `health`, `haste`, `armor`, `school`, `area`, `duration`, `signature`, `recovery`, `specialist`, `slayer`, `technique`, `preparation`, `manual`, `mastery`, `capstone`, `survival`, `offense`. All exact names, ranks, gates, current prerequisites and effects are listed in the regenerated [progression catalog](PROGRESSION_CATALOG.md).

| Class | Changed gameplay nodes | Added implemented benefit |
|---|---|---|
| All six | `recovery` (class-specific names) | +1.5% movement per rank, retaining +0.08 health/sec per rank |
| Paladin | Radiant Hammer (`technique`) | One extra Divine Storm wave after 0.22 seconds; retains +1 Blessed Hammer |
| Warrior | Deep Wounds (`mastery`), Heavy Throw (`technique`) | Rend spreads from Rank 1 with +20% spread radius per talent rank; Whirlwind radius +15%. Existing Rend duration and Heroic Throw count retained |
| Mage | Twin Frostbolt (`signature`, formerly Piercing Frostbolt), Accelerated Missiles (`technique`) | +1 Frostbolt projectile while retaining pierce; Fireball splash radius +25% while retaining missile speed |
| Hunter | Beast Training (`specialist`), Piercing Aim (`technique`) | Wolf first attack +15% damage per talent rank, once per pet; Multi-Shot volley width +25%. Existing companion damage and Aimed Shot pierce retained |
| Warlock | Twin Shadow Bolt (`signature`, formerly Piercing Shadow Bolt), Intense Corruption (`technique`) | +1 Shadow Bolt projectile while retaining pierce; Corruption spreads from Rank 1 with +20% spread radius; Imp bolts gain 12 base splash units from Rank 1. Existing Corruption damage retained |
| Priest | Twin Smite (`signature`, formerly Piercing Smite), Shadow Revelation (`offense`) | +1 Smite projectile while retaining pierce; Shadow Word: Pain spreads from Rank 1 with +25% spread radius. Existing shadow damage/Mind Sear radius retained |

Already functioning requested examples were retained: Twin Judgment's extra hammer, Consecration's starting radius, Mortal Strike reach, Blizzard duration, Arcane Shot count and Holy Nova area. Spell-specific effects look up the base ability ID through evolution. Summon Imp continues using the saved-compatible `summon_felguard` ID established in the previous prompt.

No permanent XP curve, shared upgrade price, rank cap, respec price, class starting spell, run equipment capacity or chest evolution requirement was changed. The central path uses earlier ancestors from the original chains; node-specific class-level/spent thresholds remain exact, including advanced preparation and capstone gates.

## Graphics and interaction

Reused: original bundled automatic/manual effect frames, six actor portraits and Elwynn/Stranglethorn/Plaguelands/Icecrown prop/landmark artwork. No gameplay PNG was created or replaced. Color/grayscale icon variants and subdued class backdrops are cached in memory once per renderer. Six representative QA images were created under `docs/screenshots/talent-trees/`; full captures remain under ignored `artifacts/talent-trees/screenshots/`.

The tree uses the reference's icon-and-rank approach. Full names and benefits appear in the hover/focus panel, leaving the prerequisite lines clear. Locked nodes remain selectable so their level, point and prerequisite requirements can be read. Maxed nodes have a double teal border; the final capstone has an extra class-colored frame. Purchase/respec retain the existing explicit confirmation with Cancel initially focused. Footer controls remain reachable with mouse, keyboard and controller.

Representative native captures: [Paladin](screenshots/talent-trees/paladin-partial.png), [Warrior](screenshots/talent-trees/warrior-partial.png), [Mage](screenshots/talent-trees/mage-partial.png), [Hunter](screenshots/talent-trees/hunter-partial.png), [Warlock](screenshots/talent-trees/warlock-partial.png), [Priest](screenshots/talent-trees/priest-partial.png).

## Tests and verification

- `scripts/check.ps1`: **823 tests passed**, Ruff lint/format, strict mypy and raster/audio validation passed; **44 source launch smoke cases passed** across classes/zones, bosses and menus.
- `scripts/verify_talent_trees.py`: **18 allocation-state captures** (six classes × fresh/partial/maxed) and **four resolution captures**, using actual App/renderer and private staged profiles. No missing/repair assets.
- Final targeted reruns after metadata validation/presentation refinements: **184 progression/tree tests passed**, then the **35 new tree cases passed** after final visual layout cleanup.
- New tests prove exact current/max rank tables, four-tier topology/nonoverlapping hit regions, level/point/prerequisite/capstone gates, 180 former valid allocations, persisted starting choices, all-class projectile bonuses, delayed/evolved Divine Storm damage, early/wider DoT spread, actual extra splash hits, once-per-pet opening bonus, Multi-Shot angles and existing radius/duration modifiers.
- Mouse hover/click, keyboard and simulated D-pad/A events exercise actual purchase and gold-respec confirmation/settlement at each supported resolution. Existing transaction failures, invalid allocations, save recovery, V1/V2 compatibility and live-run isolation remain covered.

The renderer, connections and bonuses were verified together; connected nodes are not merely a cosmetic mockup. Tests also retain coverage of every original talent's observable gameplay effect.

## Remaining limitations

Some nodes reuse the same thematic spell/defense artwork; this preserves existing assets without inventing a separate icon art set. Hover/focus details identify their full names and exact effects. These are native Pygame captures and automated event flows, not physical controller or screen-reader certification. No packaged binary was rebuilt; existing v0.5.0 executables remain the previous release. No new complete thirty-minute balance campaigns were run for the additional permanent bonuses; broad human balance testing remains useful.

The class talent-tree changes are isolated on their own branch for review. No later prompt is included.
