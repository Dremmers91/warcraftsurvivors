# Achievements and class unlocks — initial audit

Inspected before implementation on `dremmers/achievements-class-unlocks`, created from updated main after the two preceding PRs were merged. Read GAME_DESIGN, CONTENT_CATALOG, PROGRESSION_CATALOG, SAVE_FORMAT and ARCHITECTURE; inspected achievement definitions, UI screenshots, reward settlement, profiles/migration, class/shop registries, combat ownership, spawning, pickups, manual/evolution paths and tests. No project/ancestor AGENTS.md was found; the previously located user-level file is empty.

| Requirement | Initial status | Evidence / planned action |
|---|---|---|
| Existing cumulative/per-class/boss achievements | Complete | 33 stable IDs with stats-derived progress and once-only gold. Preserve IDs, completions, earned rewards and counters. |
| 40–60 meaningful achievements | Partial | Extend the existing catalog to 60, covering current gameplay rather than duplicates. |
| Categories, icon, reward types, availability, prerequisites | Missing | Add data fields, categories and original-art icons; support gated shop and class rewards. |
| Current/max progress and completion state | Partial | Existing numeric counters/completed list work; extend to multiple-condition and build facts. |
| Completion timestamps | Missing | Record UTC timestamps for new completions; preserve unknown dates for legacy records. |
| Creature-family/faction/type/damage-source kill tracking | Missing | Existing Enemy retains last damage school/owner, but no authoritative structured death record or family catalog. |
| Automatic/DoT/pet/Imp/temporary/evolved player attribution | Partial | Shared damage path credits player; retain it and add source/delivery metadata and deduplicated death events. |
| Boss/zone tracking | Partial | Boss-specific victory counters exist; add exact zone/boss death facts and zone wins. |
| Spell/evolution/build/chest facts | Missing | Only total evolution count exists; track distinct IDs, run maxima and actual chest openings. |
| Single-run survival/manual/damage/healing-pickup challenges | Missing | Add authoritative live counters; healing cards/spells are distinct from pickup collection. Ordinary loot currently spawns no healing pickups. |
| Initial six classes remain unlocked/playable | Complete | Preserve all six and require complete assets/content/tree before a registry entry can be playable. |
| Rogue/Druid/Shaman achievement unlocks | Partial | Current conditions differ from supplied prompt; reuse IDs with requested requirements and preserve earned legacy unlocks. |
| Death Knight/Monk/Demon Hunter/Evoker registry | Missing | Add future registry entries; all remain unplayable. |
| Demon Hunter / Evoker encounter availability | Missing | No hostile demon family or dragon boss exists in the shipped catalog; show unavailable requirements rather than false attainable goals. |
| Achievement shop rewards | Missing | Gate new Wisdom purchases on More Choices; retain purchased ranks. Add Treasure Hunter, Spell Master reroll and Master of Arms banish purchase options with actual gameplay effects. |
| Achievement/class-selection UI | Partial | Text-only paginated achievements and three future-class cards; add categories, icons, detail/status screens and all seven future entries in selection. |
| Mouse/keyboard/controller input | Complete | Existing spatial navigation/click/A/B/D-pad paths; extend without replacing them. |
| Failed/successful run persistence/respec/restart | Complete | Existing settlement and atomic V2 profiles work; add compatible optional fields and conservative migration. |
| Duplicate event/settlement protection | Partial | Removed enemies and App.result prevent ordinary duplicates; add explicit per-run death IDs and persistent settlement IDs for replay/restart protection. |
| Automated tests | Partial | Existing progression/rewards/profile coverage; add event, family, challenge, unlock, reward-gate and replay tests plus rendered UI validation. |

This prompt is authorized through testing, staging, committing, pushing and opening a PR. Unfinished classes will not become playable and no later prompt is started.
