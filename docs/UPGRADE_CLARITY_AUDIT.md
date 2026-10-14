# Upgrade description and UI clarity — initial audit

Audited before changes on `dremmers/upgrade-ui-clarity`, created from updated main `f41cf52` after the achievements PR merged. Read GAME_DESIGN and CONTENT_CATALOG and inspected upgrade eligibility/application, all automatic/manual rank data, spell strategies, passive formulas, branches, evolutions, talent hover/focus panels, shared purchases, achievement rewards, icons, input and tests. No workspace/ancestor AGENTS.md exists.

| Requirement | Initial status | Findings / planned change |
|---|---|---|
| Card types, affected ability, current/next/max ranks | Partial | Internal kinds and next rank shown; add player-facing types and transitions while preserving eligibility. |
| Actual automatic rank improvements | Partial | Next raw damage/cooldown/radius/count/pierce dumped into prose; compare authoritative current/next values and distinguish base/effective stats. |
| New ability explanations | Partial | Most descriptions work; retain accurate behavior prose, shorten Imp rank history and correct unsupported stun/persistence claims. |
| Passive applicability | Complete | Existing catalog accurately distinguishes affected mechanics; retain scope and add numerical current/next benefits. |
| Branches | Partial | Force/Reach text is largely accurate; clarify slower casts, radius versus area and show comparisons. |
| Evolution requirements/readiness | Partial | Rank/passive/chest hints exist but crowd cards; add accessible details with name, all requirements, ownership/readiness and transformed behavior. |
| Manual activation and rank values | Partial | Good behavior descriptions but no card activation prompt; generated text exposes unused power/distance/duration fields. Show only values consumed by each manual strategy. |
| Controller labels | Missing | Fixed A/B/X/Y throughout; identify common controller families where possible and retain generic fallback. |
| Talent tooltip ranks/effects/prerequisites/points | Complete | Existing fixed side panel is numerical and follows hover/focus; preserve it and clarify effect labels and current-to-next contribution. |
| Gold upgrades | Partial | Costs/caps/achievement gates work; add current/next benefit and full lock requirements, retain transactional confirmations. |
| Achievement rewards | Complete | Typed rewards and availability now work; retain accurate one-time gold/class/shop explanations. |
| Centralized description/comparison architecture | Missing | No shared card formatter; derive comparisons from current rank data and runtime stat helpers without changing gameplay formulas. |
| Icons | Partial | Spell/manual art exists; many passives share placeholder bars and reward power uses a placeholder. Reuse distinct existing art. |
| Wrapping/layout/focus/details | Partial | Cards fit through font shrinking but mix prose/stats/evolution hints. Add readable blocks and a paused details screen accessible to all input devices. |
| Validation | Partial | Behavior/eligibility/input tests are strong; add description-to-behavior, boundary, wrapping and detail/navigation coverage. |

This milestone changes presentation and accurate descriptions; progression rules, combat formulas, costs and save schema remain in place.
