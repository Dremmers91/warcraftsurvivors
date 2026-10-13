# Codex Master Prompt — Warcraft Survivors

You are the lead game developer, technical architect, gameplay designer, UI designer, and quality assurance engineer for a complete Windows desktop game called **Warcraft Survivors**.

The human developer is using an AI-assisted development workflow. You are responsible for implementing working systems, choosing reasonable defaults, fixing bugs, creating game content, maintaining documentation, and preparing builds.

Do not ask routine design questions. Make sensible decisions based on this specification and document them. Only ask for clarification if implementation is genuinely blocked.

## 1. Game concept

Build a complete 2D, top-down, World of Warcraft-inspired survival roguelite based on the core gameplay loop of Vampire Survivors.

This is a private, educational, non-commercial project.

The game combines:
- Warcraft classes and recognizable fantasy spells.
- Automatically activated combat abilities.
- Large hordes of enemies.
- Movement-focused survival.
- Randomized level-up upgrades.
- Weapon and spell evolutions.
- Elite enemies and boss encounters.
- Distinct scrolling environments.
- Permanent upgrades and class talent trees.
- Achievement-based class unlocks.
- Substantial visual effects and late-game power scaling.

Use original or procedurally created artwork and effects rather than depending on extracted game assets. The game must function without downloading third-party copyrighted assets.

## 2. Technology

Required:
- Python 3.
- Pygame-ce.
- Windows as the primary platform.
- PyInstaller for executable distribution.
- Local persistent save files.
- Data-driven content definitions.
- Automated tests using pytest.
- Appropriate Python linting and type checking.

Choose stable, compatible dependency versions.

Use a clean Python package structure, type annotations, reusable systems, and separation between simulation, content data, UI, rendering, and persistence.

Do not create a web application or replace Pygame with another engine.

## 3. Controls

Support:
- Arrow keys and WASD for movement.
- Left mouse button held down to move continuously toward the cursor.
- Gamepad left analog stick for movement.
- Space for the equipped manual ability.
- Gamepad primary face button for the manual ability.
- Escape/Start for pause.
- Full keyboard, mouse, and gamepad menu navigation.

The player does not manually aim automatic attacks.

Input methods should be switchable during gameplay.

Movement must work in eight directions with normalized diagonal movement and frame-rate-independent behavior.

## 4. Core combat

Characters move freely around a scrolling 2D map.

Automatic spells activate according to cooldowns.

Directional abilities can intelligently acquire nearby enemies and launch toward them. If no enemy is nearby, they can launch in the player's last facing direction.

AoE spells damage surrounding areas, create persistent effects, or generate attacks around the player.

Allow specialized effects such as:
- Orbiting projectiles.
- Piercing and bouncing projectiles.
- Damage-over-time effects.
- Persistent ground effects.
- Autonomous companions.
- Summoned temporary attackers.
- Chained damage.
- Expanding shockwaves.
- Radial projectile volleys.

All automatic spells must function without additional player input.

Each spell must produce recognizable visible effects even at Rank 1.

An important progression goal is that directional attacks can become screen-covering attacks. A single Shadow Bolt can eventually become a Shadow Volley, while Judgment can evolve from one hammer into hammers firing in every direction.

The game should eventually support extreme late-game enemy density and powerful overlapping visual effects.

## 5. Playable classes

Initially implement these six classes:

1. Paladin — starts with Judgment.
2. Warrior — starts with Mortal Strike.
3. Mage — starts with Frostbolt.
4. Hunter — starts with Arcane Shot.
5. Warlock — starts with Shadow Bolt.
6. Priest — starts with Smite.

All six are available from the beginning.

Each class eventually has:
- 10 automatic abilities.
- 3 manual abilities.
- One predetermined starting automatic ability.
- Distinct visual identity.
- Distinct damage and survival characteristics.
- A permanent class talent tree.

Do not implement specialization selection. Classes can use iconic abilities from multiple Warcraft specializations.

All classes use cooldown-based combat.

Do not implement Mana, Rage, Energy, Holy Power, or other class resource systems in the initial version.

Additional Warcraft classes will be implemented later and unlocked through achievements rather than gold.

## 6. Ability and level-up system

Every run begins at Level 1 with exactly one equipped automatic ability.

Automatic ability capacity: 8.
Passive upgrade capacity: 8.
Manual ability capacity: 1 additional slot.

Automatic spells:
- Have eight ranks.
- Use mostly predefined rank improvements.
- May occasionally offer special branching modifiers.
- Can evolve into a more powerful form.
- Have one evolution each initially.

Manual abilities:
- Are discovered through the randomized level-up system.
- Have three ranks.
- Require a button press to activate.
- Have cooldowns.
- Once one is equipped, other manual abilities are excluded from the upgrade pool for that run.

Passive upgrades:
- Affect eligible spells or character attributes.
- Include additional projectiles, expanded AoE, increased damage, reduced cooldowns, increased duration, improved movement, and defensive bonuses.
- Do not include Mastery or Versatility.
- May contain narrowly defined damage or attack-frequency bonuses.

Every level-up pauses gameplay and presents three randomly selected eligible upgrade cards.

A permanent shared upgrade can eventually increase this to four cards.

Eligible cards may include:
- New class automatic abilities.
- Upgrades to equipped automatic abilities.
- Shared passive upgrades.
- A new manual ability when its slot is empty.
- Upgrades to the equipped manual ability.
- Special spell modifiers when requirements are satisfied.

Selections are weighted and randomized. Do not guarantee one card per equipped ability or one card of each type.

Never display duplicate choices in the same selection.

Exclude unavailable, incompatible, or maximized upgrades.

When slots are full, exclude new abilities that cannot be equipped.

When all regular upgrades are exhausted, offer appropriate repeatable rewards such as healing, gold, or temporary bonuses.

Spell evolution requires:
1. The spell is at its maximum rank.
2. The player owns its required passive.
3. The player opens an eligible elite or boss treasure chest.

Evolution replaces the original spell without consuming another slot.

## 7. Classes and abilities

Use the following initial automatic ability pools.

Paladin:
- Judgment
- Divine Storm
- Consecration
- Avenger's Shield
- Hammer of Wrath
- Blade of Justice
- Holy Shock
- Wake of Ashes
- Blessed Hammer
- Eye of Tyr

Manual:
- Divine Shield
- Lay on Hands
- Avenging Wrath

Warrior:
- Mortal Strike
- Whirlwind
- Thunder Clap
- Execute
- Bladestorm
- Heroic Throw
- Rend
- Cleave
- Ravager
- Shockwave

Manual:
- Heroic Leap
- Shield Wall
- Rallying Cry

Mage:
- Frostbolt
- Fireball
- Arcane Missiles
- Blizzard
- Frozen Orb
- Flamestrike
- Arcane Explosion
- Pyroblast
- Ice Lance
- Meteor

Manual:
- Blink
- Ice Block
- Combustion

Hunter:
- Arcane Shot
- Multi-Shot
- Aimed Shot
- Rapid Fire
- Barrage
- Explosive Shot
- Kill Shot
- Serpent Sting
- Beast Companion
- Stampede

Manual:
- Disengage
- Aspect of the Turtle
- Bestial Wrath

Warlock:
- Shadow Bolt
- Corruption
- Immolate
- Rain of Fire
- Chaos Bolt
- Seed of Corruption
- Hand of Gul'dan
- Summon Felguard
- Shadowburn
- Cataclysm

Manual:
- Demonic Circle
- Unending Resolve
- Dark Soul

Priest:
- Smite
- Holy Fire
- Shadow Word: Pain
- Mind Blast
- Mind Sear
- Penance
- Shadow Crash
- Holy Nova
- Void Torrent
- Divine Star

Manual:
- Power Word: Shield
- Desperate Prayer
- Psychic Scream

Maintain these as data-driven content definitions rather than hardcoded conditionals scattered across the engine.

Give each ability unique behavior, visual effects, upgrade ranks, and evolution requirements.

Important ability rules:

Consecration always follows the Paladin and expands with upgrades.

Execute always attacks normally, with bonus damage against enemies at low health. It must not sit unused while waiting for an eligible low-health enemy.

Blizzard begins as a traveling storm and eventually evolves into a permanent storm that follows the Mage.

Demonic Circle:
- First button activation places a visible circle.
- Second activation teleports the player to that circle.
- Teleporting triggers a cooldown.
- After the cooldown, the player can place another circle.
- Do not strand the player by requiring them to return to teleport range.
- The circle must remain within valid map coordinates.

Damage-over-time abilities automatically apply visible status effects, prioritize useful targets, and can gain spreading behavior through upgrades.

## 8. Pets and companions

Pets are implemented as autonomous ability effects, not independent player-controlled characters.

Examples include Hunter wolves and Warlock demons.

Rules:
- Pets cannot take damage.
- Pets cannot be killed.
- Enemies cannot target pets.
- Pets have no health bars.
- Pets have no independent XP or equipment.
- Pets stay inside a configurable leash radius.
- Pets attack nearby enemies automatically.
- Pets return to their owner if they move too far away.
- Pet damage scales with relevant player upgrades and permanent talents.
- Pet kills contribute XP, gold, achievements, and kill counts to the player.
- Pets have clear, recognizable attack animations.

Pets occupy their associated automatic ability slot and do not require separate upgrades beyond that ability's normal ranks.

## 9. Enemies, elites, and bosses

Enemy density and difficulty increase throughout each 30-minute run.

Regular enemies:
- Spawn in appropriate locations around the camera.
- Move toward the player.
- Use varied movement speeds, damage, and behaviors.
- Become more numerous throughout the run.
- Drop XP and occasionally other pickups.

Elites:
- Appear at approximately five-minute intervals initially.
- Have distinctive appearances and attacks.
- Award substantial XP and permanent progression bonuses.
- Drop treasure chests.
- May also appear through later wave or level milestones.

Final boss:
- Appears when the timer reaches 30 minutes.
- Uses recognizable mechanics with visible attack indicators.
- Must be defeated to win.
- Each zone initially has one iconic final boss.
- Support randomized zone boss pools later.

The timer may stop at 30 minutes while the final encounter continues, rather than ending the game automatically.

## 10. Experience and permanent progression

In-run XP:
- Earned by defeating enemies and collecting XP gems.
- Requirements increase with level.
- Enemy XP values and density scale throughout the run.
- Large hordes should provide frequent upgrades.
- Pet kills award XP to the player.

Permanent progression:
- Separate from in-run XP.
- Each class earns permanent class XP.
- Permanent class levels award talent points.
- Every class has its own talent tree.
- Talent trees combine stat bonuses and ability-changing modifiers.
- Respecializing a class costs gold.
- Shared upgrades use gold earned from runs.
- Additional classes unlock through achievements.

Unsuccessful runs still provide useful rewards based on:
- Enemies defeated.
- Elites killed.
- Survival time.
- Achievements earned.

Completing the full 30-minute run and defeating the boss awards a substantial bonus.

Do not make failed runs worthless.

Long-term progression should gradually improve the player's ability to reach powerful, screen-clearing late-game builds.

## 11. Maps and environments

Each zone is a large, finite, scrolling map.

The camera follows the player and displays only the surrounding section of the world.

The world should be significantly larger than the viewport.

Initial zone:
- Elwynn Forest.

Later zones:
- Duskwood.
- Stranglethorn Vale.
- Eastern Plaguelands.
- Icecrown.

Maps should feature recognizable environmental themes, roads, forests, landmarks, obstacles, and zone-specific enemies.

Use chunked rendering and spatial organization where appropriate.

The player must not see the entire map at once.

## 12. Visual identity

Use detailed modern pixel art inspired by fantasy RPGs.

Prioritize readability during dense combat.

Visual language:
- Holy: gold and white.
- Fire: orange and red.
- Frost: cyan and blue.
- Arcane: violet and magenta.
- Shadow: purple and black.
- Nature and poison: green.
- Physical attacks: steel, red impact accents.

Use clearly recognizable:
- Spell projectiles.
- Impact animations.
- Area attack boundaries.
- Damage-over-time indicators.
- Companion attacks.
- Elite and boss attacks.
- Upgrade and evolution effects.

Start with self-contained procedural placeholder assets that are visually understandable. Replace them with original, consistent assets during later milestones.

No feature may require missing asset files to launch.

## 13. Performance

Target smooth 60 FPS at 1920×1080 on typical modern Windows gaming hardware.

Implement:
- Frame-rate-independent simulation.
- Spatial partitioning for nearby entity queries.
- Efficient collision detection.
- Object pooling where appropriate.
- Cached assets and rendered surfaces.
- Off-screen culling.
- Efficient particle handling.
- Reasonable limits on cosmetic effects without suppressing gameplay damage.

Combat should eventually support thousands of enemies or equivalent densely packed hordes without requiring individual full-cost rendering or collision checks for every possible interaction.

Keep deterministic testing possible where practical.

Prioritize accuracy of gameplay calculations over purely decorative particle effects.

## 14. User interface

Required screens:
- Main menu.
- Class selection.
- Zone selection.
- In-game HUD.
- Level-up selection.
- Pause menu.
- Character talent trees.
- Shared upgrades.
- Achievement and unlocks screen.
- Run results.
- Settings.

The HUD should show:
- Player health.
- Current level and XP progress.
- Elapsed run time.
- Equipped spells.
- Manual ability and cooldown.
- Relevant status effects.
- Optional performance information in debug mode.

## 15. Persistence

Save:
- Unlocked content.
- Class progression.
- Talent points and purchases.
- Shared permanent upgrades.
- Gold.
- Achievements.
- Player settings.
- Run statistics.

Use versioned, validated save data with safe defaults and recovery from corrupted files.

Do not put mutable saves inside the installed executable directory.

## 16. Development workflow

Build the project incrementally through milestones.

Do not attempt to implement every feature immediately.

Every milestone must:
1. Leave the game runnable.
2. Include working