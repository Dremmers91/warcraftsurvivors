# Pets and summons — initial audit

Audited before implementation on `dremmers/pets-summons-overhaul`, based on the supplied Pets and Summons Overhaul prompt. No project or ancestor AGENTS.md was found; the located user-level `.codex/AGENTS.md` is empty. Reviewed GAME_DESIGN, CONTENT_CATALOG, ARCHITECTURE, ART_DIRECTION, ASSET_PIPELINE, SAVE_FORMAT, combat/entities, enemy targeting, rewards, rendering/presentation, asset loading/builders, progression and existing tests.

Actual wolf and Imp PNG atlases and existing Hunter/Elwynn gameplay screenshots were inspected. The wolf has detailed directional quadruped artwork and distinct walking poses. The Imp has a small red demonic body, horns, limbs, tail and green casting accents. Preserve both, along with Felguard/Dreadguard art. Their idle/cast sequences are derived poses, not fully authored animation. The wolf's existing cast frames have small generic accents; supplement attacks with existing slash art rather than replace the animal.

| Requirement | Initial status | Evidence / planned action |
|---|---|---|
| Automatic ability slots, no pet equipment/XP/commands | Complete | CompanionSpell uses the equipped spell; pets have no separate progression. Preserve. |
| Invulnerability, untargetable, no health bars | Complete | Companion has no health/Enemy identity; hostile paths address Player only; renderer bars enumerate enemies. Add regression coverage. |
| Player damage/kill/XP/gold/achievement credit | Complete | Combat.hit uses player ownership; collect_dead and run settlement share existing reward paths. Verify end to end. |
| Leash and return | Partial | 320 clamp exists; nearest out-of-leash enemy can hide a valid target; spawn/ranged formation need configurable leash. |
| Spatial target selection | Partial | SpatialHash used, but every permanent pet searches every fixed step; no retained targets or cluster preference. |
| Rank/passive scaling | Partial | Damage/cooldown/area/count work; pets repeatedly recompute stats; no ranged projectile scaling. |
| Hunter wolf artwork | Complete | Detailed native atlas inspected; retain original art and walking animation. |
| Hunter allied distinction | Partial | Same wolf as hostiles, only ALLY text. Add cached subdued outline and ground marker. |
| Hunter idle / bite / hit / summon feedback | Partial | Walk always selected outside cast; cast accents are generic. Use real idle state and existing directional slash/impact/summon art. |
| Primary Warlock Imp | Missing | Summon Felguard uses a melee Felguard. Suitable detailed Imp atlas already exists; reuse. |
| Eight Imp ranks and Imp Legion | Missing | Generic companion rank curve/evolution lacks ranged firebolts, splash, burning and legion behavior. |
| Late-game melee usefulness | Partial | Slow pursuit, nearest individual selection and attack-after-other-spells can starve hits. Add rank-gated bounded leap and cluster cleave. |
| Late-game ranged usefulness | Missing | Permanent companions share only melee logic. Implement near-owner ranged casting and multi-target volleys. |
| In-game visual validation / multiple-pet performance | Partial | Existing asset tests and prior staged screenshots exist; new behavior requires actual renderer captures at all qualities and terrain checks. |
| Save compatibility | Complete | Profiles store starting ability IDs, not active pets/runs. Retain the existing internal summon_felguard ID for purchased talent/starting selections while changing the visible name and behavior. |
| Companion tests | Partial | Existing stationary damage, ownership, basic leash and scaling tests; extend edge cases, ranged ranks, rewards, targeting and cached presentation. |

This chat handles this supplied overhaul only. Further prompts will use the same branch when supplied; no commit or push is authorized.
