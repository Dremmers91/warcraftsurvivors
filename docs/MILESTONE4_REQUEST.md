# Milestone 4 — Permanent Progression and Unlocks

Read AGENTS.md and existing game documentation. Implement persistent progression while preserving all completed gameplay systems.

## Class leveling

Every class has its own persistent class XP and permanent level. Enemy kills, elites, survival, completed runs and final bosses earn class XP separately from in-run XP. Permanent levels award talent points.

## Talent trees

Provide distinct 15–20 meaningful talent trees for the six classes: damage, health/armor, cooldowns, class offense, ability-changing modifiers, selected starting bonuses and capstones. Every talent must affect gameplay, with prerequisites and sensible progression. Hunter/Warlock receive no automatic starting companions. Advanced talents may allow a selected companion or additional ability; new characters retain one starter. Talents should help late progression without trivializing early gameplay.

## Respecialization

Between runs, reset a class tree for gold after displaying the cost and confirming. Refund allocated points; retain earned class XP.

## Shared upgrades

Gold buys ranked/costed health, damage, armor, speed, pickup, XP, gold, recovery, rerolls and additional choices. The fourth level-up choice is a shared permanent unlock. Prevent unaffordable purchases.

## Achievements and unlocks

Persistent counters, completion, rewards, notifications and a screen should cover total kills, elite counts, 10/20/30-minute survival, Hogger, evolutions, class levels and wins across classes. Future classes unlock through achievements, never gold. Provide an extensible registry/conditions without implementing their future playable content.

## Save system

Versioned Windows user-data saves store gold; class XP/levels/points/talents; shared upgrades; achievements; class/zone unlocks; stats; settings. Use safe atomic writes and recover from missing, invalid, corrupt, older and interrupted saves.

## UI and acceptance

Show class progression, interactive talent trees, gold upgrades, achievement progress, locked classes, unlock notifications, purchase and respec confirmations. All support keyboard, mouse and gamepad. Verify persistent XP/achievements, allocation effects, costs/caps, refunds, failure/victory rewards and recovery. Automated tests cover persistence/purchase rules. Test starting a run, dying, earning rewards, buying an upgrade, closing, reopening and seeing the upgrade active.

Do not proceed to the next milestone automatically.
