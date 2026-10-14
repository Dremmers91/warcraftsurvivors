# Achievements and class unlocks — completion report

Branch: `dremmers/achievements-class-unlocks`, based on updated main `4235013`. The initial inspection is recorded in [ACHIEVEMENTS_AUDIT.md](ACHIEVEMENTS_AUDIT.md). Existing systems were extended in place. No subsequent prompt or unfinished playable class was implemented.

| Requirement | Initial status | Changes made | Final status |
|---|---|---|---|
| Existing cumulative/per-class/boss achievements | Complete | Kept all 33 IDs, previous completions, gold and existing aggregate counters | Complete |
| 40–60 meaningful achievements | Partial | Added 27 distinct entries; 60 total, 58 currently obtainable | Complete |
| Category, icon, reward types, availability, prerequisites | Missing | Typed catalog fields, five categories, existing original-art icons, prerequisite validation, class/shop rewards and encounter availability | Complete |
| Current/max progress and completion state | Partial | Retained progress derivation; added multiple-condition requirements, numeric bars, completed/incomplete/locked/unavailable states | Complete |
| Completion timestamps | Missing | UTC ISO timestamps for new completions; unknown legacy dates retained as null | Complete |
| Creature-family/faction/type/source tracking | Missing | Enemy/boss family catalog, Defias faction, owned kill histograms and structured death metadata | Complete |
| Spell/DoT/pet/Imp/temporary/evolved credit | Partial | Extended existing damage paths with source/school/delivery; one enemy instance processed once | Complete |
| Boss/zone tracking | Partial | Exact zone/boss deaths, per-zone survival/wins; Lich King gate requires Icecrown | Complete |
| Spell/evolution/build/chest facts | Missing | Actual evolution IDs, distinct bases, spell rank/equipment/run-level maxima and opened elite chests | Complete |
| Survival/manual/damage/healing-pickup challenges | Missing | Run facts track live time before first healing pickup, successful manual activations and boss damage including absorbed hits | Complete |
| Six initial classes playable/unlocked | Complete | Preserved all six; playable registry entries require shipped class, actor, manuals and tree | Complete |
| Rogue/Druid/Shaman unlock requirements | Partial | Reused IDs with supplied thresholds; preserved previously earned unlocks | Complete |
| Death Knight/Monk registry | Missing | Added achievement gates using implemented content; unplayable Coming Soon cards | Complete for unlock tracking; playable content deferred |
| Demon Hunter/Evoker registry and encounter availability | Missing | Registered conditions; disabled achievement completion while required hostile demons/dragon boss are missing | Complete for registry/UI; encounters unavailable |
| More Choices reward | Missing | Run level 40 enables the existing Wisdom purchase; retained bought ranks and eight-shared-rank/450-gold cost | Complete |
| Treasure Hunter reward | Missing | 25 opened elite chests enable three ranks of Treasure Training; +5 run gold per opened chest per rank | Complete |
| Spell Master reward | Missing | Reused ten-evolution achievement; enables one extra purchased reroll | Complete |
| Master of Arms reward | Missing | Wins with all six starting classes enable one purchased banish per run | Complete |
| Achievement/class-selection UI | Partial | Five category tabs, paged icon cards, requirement/reward/date details, all seven future classes in character selection | Complete |
| Mouse/keyboard/controller input | Complete | Extended existing navigation; normal card reroll R/X, selected-card banish B/Y/button; pause retained | Complete |
| Failed/successful runs, restart, respec, migration | Complete | Optional compatible V2 fields; retain XP/gold/talents/purchases/completions and conservative historical inference | Complete |
| Duplicate events/rewards | Partial | Per-run enemy IDs plus persisted settlement IDs guard gold, XP, counters and unlocks; invalid summaries cannot partially mutate profiles | Complete for normal gameplay |
| Automated and rendered validation | Partial | Added event/unlock/challenge/purchase/replay tests, interaction tests and exhaustive isolated UI captures | Complete; evidence below |

## Catalog changes

All **33 existing IDs** are preserved: `first_blood`, `centurion`, `survivor`, `elite`, `evolution`, `victory`, `kills_500`, `kills_5000`, `kills_25000`, `elites_10`, `elites_25`, `survive_10`, `survive_20`, `survive_30`, `hogger_5`, `evolve_10`, `level_5`, `level_15`, `level_30`, `wins_2`, `unlock_rogue`, `unlock_druid`, `unlock_shaman`, `level_paladin`, `level_warrior`, `level_mage`, `level_hunter`, `level_warlock`, `level_priest`, `boss_stitches`, `boss_bangalash`, `boss_rivendare`, `boss_lich_king`. Existing gold values are unchanged. Rogue/Druid/Shaman unearned requirements change to the supplied conditions; completed records continue to grant their unlocks. The Lich King ID also serves the Death Knight gate, avoiding another achievement for the same encounter. `evolve_10` becomes Spell Master and retains its gold reward.

The **27 added IDs** are `kills_1000`, `kills_10000`, `kills_50000`, `elites_100`, `undead_2000`, `battle_proven`, `icecrown_survivor`, `all_zones`, `evolve_judgment`, `distinct_evolutions`, `full_arsenal`, `max_spell`, `treasure_hunter`, `more_choices`, `level_25`, `master_of_arms`, `unlock_monk`, `unlock_demon_hunter`, `unlock_evoker`, `untouched_boss`, `no_manual_win`, and one `win_<class>` for each of the six initial classes. The last two unavailable encounter achievements still display their requirements/rewards explicitly. The catalog regression test verifies 60 distinct requirement combinations.

## Class unlocks and rewards

| Class | Configurable condition | Unlock obtainable now? | Playable? |
|---|---|---|---|
| Paladin, Warrior, Mage, Hunter, Warlock, Priest | Initially unlocked | Yes | Yes |
| Rogue | 2,500 Defias defeats across runs | Yes | Coming Soon |
| Death Knight | Defeat the Lich King in Icecrown | Yes | Coming Soon |
| Druid | 5,000 beast defeats across runs | Yes | Coming Soon |
| Shaman | 2,000 kills with Fire/Frost/Nature across runs | Yes | Coming Soon |
| Monk | 1,200 live seconds in one run before any healing pickup | Yes | Coming Soon |
| Demon Hunter | 1,500 hostile demon defeats | Not Yet Available: no hostile demon enemies | Coming Soon |
| Evoker | Defeat a dragon boss | Not Yet Available: no dragon boss | Coming Soon |

Implemented reward types are **one-time gold, class unlock eligibility and shared-shop purchase eligibility**. Shop rewards include the fourth normal card, chest gold, an additional reroll and an additional banish. They require explicit gold purchases and capped ranks; achievements do not repeatedly grant stacking bonuses. Cosmetic rewards were optional and no new cosmetic system was added. Class and shop gates derive from completed achievement IDs, rather than duplicate independent unlock flags. Normal run earnings retain the existing gold multiplier; achievement gold remains fixed.

## Validation evidence

- `scripts/check.ps1`: Ruff lint/format, strict mypy, **866 passing pytest cases**, raster/audio validation and **44 source launch smokes** (six classes × five zones, five boss encounters, nine menus).
- New coverage exercises actual automatic/pet/Imp/temporary/evolved/DoT kill paths, family/faction/damage attribution, cumulative thresholds, exact boss-zone credit, challenge boundaries, shield damage, unavailable encounters, multiple requirements/prerequisites, gold distribution, replay after restart/write failure, invalid-summary rollback, migration/respec preservation, real gated purchases, banishment, chest gold and distinct evolutions.
- Menu tests cover category/detail/pagination, every future class, the extra shop page and keyboard/mouse/controller banishment while paused. Existing real-process earn/purchase/reopen progression checks remain part of pytest.
- `scripts/verify_achievement_ui.py`: **89 staged renders** covering every achievement detail and category page, all character/unlock/shop pages, earned/partial/locked/unavailable states, a selected banish card and all four supported resolutions; no missing assets. Screenshots use an isolated synthetic QA profile, not the player's normal save.
- Representative renders were visually inspected for readable labels, bars, requirements, rewards and availability. Selected evidence is in [screenshots/achievements](screenshots/achievements); full logs/captures remain under ignored `artifacts/achievements` and the ordinary source-smoke directory.

## Known limitations

All seven additional classes lack complete playable content and deliberately remain unavailable to start. Demon Hunter/Evoker require future encounter content; availability is configured in the catalog and must be updated when those encounters ship. Ordinary loot currently creates no healing pickups; healing cards/manuals/life steal do not count as pickup collection. The challenge hook supports actual `heal`/`healing` pickups without altering normal loot balance. New family/source/chest/build counters begin with this version because older profiles did not record those facts; migration does not invent them. Legacy completion timestamps remain unknown. Active runs are not resumed after abrupt process loss; normal Finish/Quit records earned progress using the existing settlement flow. Idempotent run replay requires a run summary/identity; the retained legacy positional helper cannot distinguish two intentionally separate calls with identical counters. Normal App gameplay always passes the authoritative run summary. Balance remains prototype tuning rather than broad human playtest certification.
