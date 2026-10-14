# Upgrade description and UI clarity — completion report

Implemented on `dremmers/upgrade-ui-clarity`, based on updated main `f41cf52`. The initial audit is in [UPGRADE_CLARITY_AUDIT.md](UPGRADE_CLARITY_AUDIT.md). The changes improve presentation and descriptions while retaining the existing progression and mechanics.

| Requirement | Initial status | Changes made | Final status |
|---|---|---|---|
| Card types, ability identity and ranks | Partial | Player-facing types, affected title, current-to-next/max ranks; equipped maxed spells display MAX | Complete |
| Automatic rank improvements | Partial | Current/next damage, cast/attack interval, shots/targets/summons and meaningful footprint/duration comparisons from actual stat helpers | Complete |
| New ability explanations | Partial | Preserved accurate authored prose, shortened the Imp rank history, corrected unsupported stun/persistence claims | Complete |
| Passive applicability | Complete | Preserved scope; added contribution comparisons and clarified radius versus geometric area and shot lifetime applicability | Complete |
| Branches | Partial | Actual Force/Reach comparisons; slower casting and mutually exclusive branches stated clearly | Complete |
| Evolution name, requirements and readiness | Partial | Paused card details and equipped spellbook show current Rank 8 status, required passive ownership, chest condition and evolution identity | Complete |
| Manual activation and consumed values | Partial | Activation labels and cooldown on cards; actual immunity/shield/healing/armor/buff values; unused raw fields omitted | Complete |
| Controller labels | Missing | Common Xbox and PlayStation names adapt accept/ability/back/reroll/banish/shoulder labels; generic fallback | Complete within existing button mappings |
| Permanent talents | Complete | Preserved numerical side panel, cost/prerequisites/caps; current contribution and explicit next-rank total use shared formatting | Complete |
| Shared gold upgrades | Partial | Current/next contribution, cost/cap, achievement locks and transactional confirmation; unchanged purchase rules | Complete |
| Achievement rewards | Complete | Preserved one-time rewards and purchase/class eligibility descriptions from preceding milestone | Complete |
| Central comparison architecture | Missing | Read-only centralized formatter, unchanged shared passive constants/manual calculators, common permanent-bonus formatter | Complete |
| Icons | Partial | Reused all spell/manual art; twelve passive references and repeatable rewards now use suitable existing effects/icons | Complete |
| Layout, wrapping and detail positioning | Partial | Structured card blocks, fixed detail panels/pages, retained card focus, full scaled mouse/keyboard/controller navigation | Complete |
| Validation against gameplay | Partial | Exhaustive forecasts for 60 spells × eight ranks, 18 manuals, 60 evolutions, all passives; interaction/layout and full repository checks | Complete; evidence below |

## Corrections and numerical accuracy

- All 60 automatic spells use actual rank data and effective `spell_stats` previews. Changes prioritize count milestones, damage and timing; full details retain secondary improvements and special effects. New ranks explicitly announce radial volleys, spreading marks, wolf leaps, Imp splash and multi-firebolt milestones when those effects newly unlock. Evolutions use mechanics-derived explanations rather than raw booleans such as homing enabled: True.
- The second wolf arrives at **Rank 4**, while the second Imp arrives at **Rank 5**. Judgment Rank 3→4 retains two shots, increases base hit damage **46→55**, reduces cast interval **1.12→1.06 seconds**, widens its shot and gains pierce; the illustrative prompt numbers were not copied. Bonuses are incorporated in actual player previews.
- Blizzard's **0.5-second pulse interval** stays fixed across ranks; its cast interval changes. DoT ticks retain their **one-second interval**. The UI does not claim that Haste or those rank upgrades shorten damage ticks.
- Blink/Disengage/Leap arrival immunity is **0.5/0.7/0.9 seconds**, independent of their unused stored duration fields. Demonic Circle states the place/return sequence, starts cooldown after return and shows its fixed **0.5-second return immunity**. Ice Block shows rooting/regeneration. Manual healing, shields, buffs and capped armor use the behavior's actual consumed values, with stronger-shield/cap notes.
- Shockwave slows and pushes rather than stuns. Base Mind Sear pulses for its finite duration; its description no longer promises permanent persistence. Shield Wall's prose no longer promises a fixed 50-point armor addition at every rank; forecasts show capped total armor after activation. Reach says **radius**, avoiding the false implication that a 20% radius increase means only 20% more geometric area. Endurance explicitly includes shot lifetimes.
- Passive comparisons show their own contribution, avoiding multiplicative-bonus confusion. Shared/talent previews use authoritative effect tables and label the next **total** contribution rather than another independently stacking bonus.
- Content comparison against the branch's base confirmed unchanged IDs, all gameplay values, rank tables, mechanics and evolutions. Combat refactoring only names existing passive constants and extracts existing manual calculations for reuse; no damage/timing/cost/evolution/progression tuning was introduced.

## UI and artwork

Details are accessible through **Q**, **left shoulder**, **right-click**, or the card's Details button. They remain read only and paused, paginate special effects and restore originating focus. Pause → Spellbook displays equipped, capped and evolved spells. Manual ability labels adapt to recognized controller families. Passives/rewards reuse existing original art instead of placeholder bars: projectiles, area, might, haste, duration, travel/movement, pickup, armor, health, regeneration, pierce, power and shield all have appropriate references. No new raster assets were necessary.

Cards show up to three numerical comparisons; manual cooldown remains visible even when a manual has several changing benefits. Full details retain the remaining comparisons/effects. The bundled font lacks the requested arrow glyph, so visible comparisons use readable **to** text. Four-card wrapping was checked to ensure no lost text.

## Validation

- Full `scripts/check.ps1`: Ruff lint/format, strict mypy, **1,044 passing pytest cases**, asset/audio validation and all **44 launch smokes** (six classes × five zones, five bosses, nine menus).
- **170 new description tests** verify all spell ranks against actually applied effective damage/timing, manual activation/cooldown/immunity/shields, all passive ranks/caps/scopes, actual evolution forecasts and readiness, branches, shared rank formatting, controller-family fallback and read-only generation. Existing progression, combat, pet, achievement, save and talent tests remain intact.
- **Eight new interaction cases** cover Q/right-click/shoulder details, paused state and preserved focus/choices, equipped evolved/maxed spells, four scaled viewports and PlayStation labels.
- `scripts/verify_upgrade_ui.py` checks every automatic rank/evolution, manual rank, passive rank, all talent panels, shared pages, reward/mixed cards, equipped/evolved details and four resolutions. The final run checked **1,816 layouts** and saved **21 captures**. It records actual wrapped lines and fails on missing text, overflow or missing assets. Captures use an isolated synthetic QA profile; repeated-card stress scenes exercise the narrowest four-card columns. Representative mixed cards and details were visually inspected and are saved in [screenshots/upgrade-clarity](screenshots/upgrade-clarity). Full logs remain in ignored `artifacts/upgrade-clarity`.

## Remaining limits

Effective previews show current bonuses, not a promise about enemy-specific execute/boss effects, future buff expiry or every delayed snapshot; those effects are explained separately. Distances are relative to an unmodified Rank 1/base reference, because the game's map coordinates have no real-world unit. Controller recognition is name-based and uses the existing logical mappings; unknown devices get generic labels rather than an invented controller family. Achievement/future-class encounter availability stays as established in the previous milestone. Raw unused rank metadata remains available to the engine/developer catalog but is not dumped into player-facing cards. Gameplay and save progression were not redesigned, and no subsequent prompt was started.
