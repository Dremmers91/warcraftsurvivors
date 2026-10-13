# Milestone 2 — Classes and Complete Ability System

Read AGENTS.md, the game design documentation, and the existing implementation.

Extend the playable prototype with the complete six-class ability framework.

Preserve all previously working behavior.

## 1. Class selection

Implement a functional class selection screen.

Initially available:
- Paladin
- Warrior
- Mage
- Hunter
- Warlock
- Priest

Each class must:
- Have an original recognizable player sprite.
- Have appropriate starting statistics.
- Start with exactly one predetermined automatic spell.
- Have access only to its own class spell pool.
- Have access to shared passive upgrades.
- Support one discoverable manual ability.

## 2. Data-driven ability system

Build reusable implementations for:
- Homing or aimed projectiles.
- Directional spreads.
- Radial volleys.
- Melee attack arcs.
- Piercing projectiles.
- Bouncing projectiles.
- Orbiting projectiles.
- Moving area effects.
- Player-following area effects.
- Persistent ground damage.
- Expanding shockwaves.
- Chained damage.
- Damage-over-time statuses.
- Summoning and autonomous companions.
- Temporary charging summons.
- Player buffs and defensive effects.
- Mobility and teleport effects.

Targeting must be automatic.

Avoid building a unique hardcoded combat subsystem for each spell. Reuse these behaviors and extend them where unique spells require it.

## 3. Automatic ability roster

Implement the ten automatic abilities for each of the six classes, as specified in docs/GAME_DESIGN.md.

Each automatic ability needs:
- A distinct recognizable visual effect.
- Functional Rank 1 behavior.
- Eight rank definitions.
- Appropriate damage and cooldown scaling.
- Clear descriptions for upgrade cards.
- One unique evolved form.
- A documented required passive for evolution.
- Correct behavior when the player is stationary.

Use the abilities and starting spells established in the master specification.

Important:
- Judgment progresses toward radial hammer volleys.
- Consecration always follows the Paladin.
- Execute attacks normally and receives bonus damage against weakened enemies.
- Frostbolt progresses toward radial frost volleys.
- Blizzard begins as a traveling storm and evolves into a persistent player-following storm.
- Shadow Bolt can become a radial Shadow Volley.
- DoTs visibly mark affected enemies and can gain spread effects.
- No class resource meters are implemented.

Do not claim all 60 spells are complete until all have distinct, functioning behavior.

## 4. Manual abilities

Implement all 18 manual abilities from the specification.

Each manual ability:
- Can appear in level-up rewards.
- Occupies the one manual slot.
- Has three ranks.
- Has a visible cooldown indicator.
- Activates with Space or the gamepad primary face button.
- Has meaningful rank improvements.
- Continues to work with all supported input methods.

Once a manual ability is equipped, do not offer alternate manual abilities during the same run.

Demonic Circle specifically uses a two-press placement and teleport sequence, followed by cooldown before placing a new circle.

## 5. Pets and summons

Implement autonomous Hunter and Warlock companions.

Companions:
- Cannot receive damage.
- Cannot be targeted.
- Have no health bars.
- Remain within a leash radius.
- Attack nearby enemies.
- Scale with applicable player upgrades.
- Credit all kills and rewards to the owner.
- Remain effective during large enemy waves.

Make permanent pets distinct from temporary summoned attackers.

## 6. Passive upgrades

Implement an initial pool of at least 12 shared passives, with a maximum of eight equipped at once.

Include:
- Additional projectiles.
- Increased area.
- Increased damage.
- Reduced ability cooldowns.
- Increased effect duration.
- Increased projectile speed.
- Increased movement speed.
- Increased pickup radius.
- Additional armor.
- Increased maximum health.
- Health regeneration.
- Increased projectile piercing.

Allow applicable passives to modify multiple abilities.

Clearly identify effects that are not applicable to a particular spell.

## 7. Evolution system

Each automatic spell has one evolution.

Evolution requires:
- Maximum spell rank.
- Required passive.
- Opening an eligible treasure chest.

The evolved spell replaces its original spell.

Implement evolution eligibility checks, evolved behaviors, visual transformations, and upgrade-card metadata.

## 8. Randomized upgrade selection

Implement weighted selection from all eligible rewards.

Always offer three distinct choices when at least three eligible rewards exist.

Handle:
- Full spell slots.
- Full passive slots.
- Maxed ranks.
- Manual ability restrictions.
- Branching modifiers.
- Evolved abilities.
- Exhausted upgrade pools.

Avoid repeated or invalid cards.

## Implementation sequence

Work in this order:
1. Shared ability behaviors and tests.
2. Paladin.
3. Warrior.
4. Mage.
5. Hunter and companions.
6. Warlock and companions.
7. Priest.
8. Manual abilities.
9. Passives.
10. Evolutions and complete integration.

Use this order internally, but complete the full milestone before reporting it finished.

If implementation must be interrupted, clearly report the precise checkpoint and remaining work rather than claiming completion.

## Acceptance criteria

- All six classes are playable.
- Every class starts with its correct spell.
- All 60 automatic abilities work.
- All 18 manual abilities work.
- Rank improvements visibly and mechanically affect combat.
- Pets work according to the specification.
- Randomized level-up choices follow slot restrictions.
- Evolutions replace their original spells.
- The game remains playable without external assets.
- Automated tests cover every ability definition, evolution requirement, manual slot rule, damage type, and companion ownership rule.

Run automated tests and relevant gameplay smoke tests.

Update the content catalog with each implemented spell, ranks, and evolution.

Do not proceed to the next milestone automatically.