# Class talent trees — initial audit

Audited on the existing `dremmers/pets-summons-overhaul` branch before implementation. Read GAME_DESIGN, CONTENT_CATALOG, PROGRESSION_CATALOG, SAVE_FORMAT and ARCHITECTURE; inspected `meta.py`, progression JSON/builder, progression UI/device input, actual gameplay modifiers, persistence and tests. No project/ancestor AGENTS.md is present; the previously located user-level file is empty. Inspected the user's reference and the actual existing talent screenshot. The reference inspires connected square nodes and rank counters; its artwork will not be copied.

| Requirement | Initial status | Evidence / intended action |
|---|---|---|
| Six small data-driven class trees | Complete | Six distinct 18-node / 40-rank trees with stable IDs; retain IDs, rank caps and working effects. |
| Vertical branching layout, 3–4 tiers, central path, one final capstone | Partial | Six rows of three rectangular text nodes, three end nodes; reorganize four tiers with center path and branches. |
| Square recognizable talent icons | Missing | Talent screen contains only names/rank text; reuse existing detailed spell/manual/actor art. |
| Visible prerequisite connections | Partial | Thin lines mostly hidden by full-width cards; render paths before compact nodes, with active/locked distinction. |
| Grayscale locked, highlighted available, distinct maxed states | Partial | Text colors vary, but there are no icon states; add cached grayscale icons and explicit borders/status labels. |
| Class-themed background | Partial | Every class uses the same forest backdrop; reuse original zone/character art with class palettes. |
| Rank counters and point display | Complete | Current/max and available permanent points already displayed; preserve with larger readable badges. |
| Permanent XP/levels and multi-rank allocation | Complete | One point per permanent level after 1; class XP and levels independent from runs, capped at 100. Preserve. |
| Prerequisites, tier/level gates, capstone validation | Complete | Pure eligibility and transactional revalidation exist; adapt layout/gates without invalidating previously valid allocations. |
| Stat talents | Complete / Partial | Damage/health/armor/haste/area exist; movement is limited to one class/shared training. Preserve and supplement. |
| Requested class ability modifiers | Partial | Some projectile/radius/duration bonuses work; missing extra wave, earlier/broader spreading, Imp splash and wolf opening attack. Implement actual calculations. |
| Gold respec with confirmation/refund/XP preservation | Complete | Exact `50 + 5 × spent` cost, cancel focus, insufficient-funds prevention and atomic persistence already tested. Preserve. |
| Mouse selection / keyboard / gamepad | Complete | Click, spatial directional navigation and D-pad/A/B already work. Preserve, verify compact positions and focus. |
| Hover tooltip, locked explanations, exact current/next benefits | Partial | Mouse hover updates focus and side panel shows generic per-rank text / one reason. Add current/next totals and all gates. |
| Stable IDs/class/icon/position/tier/rank/effects/prerequisites | Partial | Most fields exist; class is outer key and icon/normalized position are absent. Add explicit presentation metadata and validation. |
| Supported resolution usability | Partial | Logical 1280×720 letterbox scaling exists; new tree layout needs captures and mapped-input tests at every supported resolution. |
| Save compatibility and regression tests | Complete / Partial | V2 recovery/validation works; retain allocations and starting choices when reorganizing gates, add old-profile compatibility tests. |

No changes to the already committed pet overhaul are discarded. This prompt is implemented without committing or pushing; later prompts remain pending.
