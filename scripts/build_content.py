"""Author the explicit, reviewable milestone-two content tables (offline only)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "src/warcraft_survivors/data/content.json"
original = json.loads(PATH.read_text("utf-8"))
abilities = []
classes = []
manuals = []


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def add(
    name,
    kind,
    school,
    damage,
    cooldown,
    radius,
    speed,
    description,
    evolved,
    passive,
    changes,
    **mechanics,
):
    aid = slug(name)
    ranks = []
    for i in range(8):
        count = (
            1 + i // 3
            if kind in {"projectile", "dot", "chain", "orbit", "companion", "charge"}
            else 1
        )
        if name in {
            "Arcane Missiles",
            "Rapid Fire",
            "Barrage",
            "Penance",
            "Multi-Shot",
            "Stampede",
        }:
            count += 2
        if name in {"Frostbolt", "Shadow Bolt"}:
            count = 1 + i // 2
        pierce = i // 3 if kind in {"projectile", "orbit"} else 0
        if name in {"Aimed Shot", "Ice Lance", "Wake of Ashes", "Divine Star"}:
            pierce += 2
        duration = (
            2 + i * 0.25
            if kind in {"field", "wave", "beam", "orbit", "charge", "dot"}
            else 3 + i * 0.15
        )
        if kind == "wave":
            duration = 0.7 + i * 0.04
        if name in {"Meteor", "Flamestrike", "Cataclysm"}:
            duration = 0.2 + i * 0.04
        if name in {
            "Rend",
            "Corruption",
            "Immolate",
            "Holy Fire",
            "Shadow Word: Pain",
            "Serpent Sting",
            "Seed of Corruption",
        }:
            duration = 4 + i * 0.5
        row = dict(
            damage=round(damage * (1 + 0.23 * i + 0.018 * i * i), 2),
            cooldown=round(cooldown * (1 - 0.045 * i), 3),
            radius=round(radius * (1 + 0.07 * i), 2),
            count=count,
            pierce=pierce,
            duration=round(duration, 2),
        )
        row["description"] = (
            f"{row['damage']:g} {school} damage; {row['cooldown']:g}s cooldown; {row['radius']:g} reach; {count} effect(s); {pierce} pierce; {duration:g}s duration."
        )
        if mechanics.get("radial_rank", 99) <= i + 1:
            row["description"] += " Full radial volley."
        if kind == "dot" and i >= 4:
            row["description"] += " Spreads on expiry or death."
        ranks.append(row)
    if aid == "judgment":
        for row, values in zip(
            ranks,
            [
                (30, 1.25, 11, 1, 0),
                (38, 1.16, 13, 1, 0),
                (46, 1.12, 14, 2, 0),
                (55, 1.06, 16, 2, 1),
                (65, 1, 18, 3, 1),
                (77, 0.94, 20, 3, 2),
                (90, 0.87, 22, 4, 2),
                (108, 0.8, 25, 5, 3),
            ],
            strict=True,
        ):
            row.update(
                zip(("damage", "cooldown", "radius", "count", "pierce"), values, strict=True)
            )
            row["description"] = (
                f"{row['damage']} holy damage; {row['cooldown']}s cooldown; {row['count']} hammers; {row['radius']} radius; {row['pierce']} pierce."
                + (
                    " Radial volley."
                    if mechanics.get("radial_rank", 99) <= ranks.index(row) + 1
                    else ""
                )
            )
    evo_kind = changes.get("kind", kind)
    descriptions = []
    labels = {
        "radial_rank": "radial volleys from",
        "homing": "homing enabled",
        "bounce": "ricochets",
        "splash": "explosion radius",
        "dot": "damage-over-time fraction",
        "slow": "slow fraction",
        "execute": "weakened-target bonus",
        "heal": "damage returned as health",
        "knockback": "knockback distance",
        "follow": "follows player",
        "persistent": "permanent field",
        "pulse": "pulse interval",
        "angle": "arc degrees",
        "chain": "base chain hops",
        "summon": "transformed summon",
        "spread_dot": "DoT spreads",
        "death_burst": "death explosion",
        "shield": "absorb per damage",
    }
    for key, value in changes.items():
        descriptions.append(f"{labels.get(key, key)}: {value}")
    passive_name = {
        "projectiles": "Multicast",
        "area": "Reach",
        "might": "Might",
        "haste": "Haste",
        "duration": "Endurance",
        "velocity": "Velocity",
        "movement": "Fleetfoot",
        "pickup": "Magnetism",
        "armor": "Fortitude",
        "health": "Vitality",
        "regen": "Renewal",
        "piercing": "Penetration",
    }[passive]
    evo_m = mechanics | {k: v for k, v in changes.items() if k != "kind"}
    abilities.append(
        dict(
            id=aid,
            name=name,
            kind=kind,
            school=school,
            speed=speed,
            ranks=ranks,
            description=description,
            mechanics=mechanics,
            effect=aid,
            evolution=dict(
                id=aid + "_evolved",
                name=evolved,
                passive=passive,
                kind=evo_kind,
                mechanics=evo_m,
                description="+65% damage. "
                + "; ".join(descriptions)
                + f". Requires Rank 8 + {passive_name} + elite chest.",
            ),
        )
    )


def cls(cid, school, health, speed, armor, manual_ids):
    start = len(abilities)
    return lambda: classes.append(
        dict(
            id=cid,
            name=cid.title(),
            school=school,
            health=health,
            speed=speed,
            armor=armor,
            abilities=[a["id"] for a in abilities[start:]],
            manuals=manual_ids,
        )
    )


# Implement in the requested class order; each record chooses shared behaviors plus concrete mechanics.
finish = cls("paladin", "holy", 135, 215, 0.1, ["divine_shield", "lay_on_hands", "avenging_wrath"])
add(
    "Judgment",
    "projectile",
    "holy",
    30,
    1.25,
    11,
    440,
    "Aimed golden hammers; Rank 6 unlocks a radial volley.",
    "Judgment of the Heavens",
    "projectiles",
    {"radial_rank": 1, "homing": True},
    radial_rank=6,
)
add(
    "Divine Storm",
    "arc",
    "holy",
    24,
    2,
    120,
    0,
    "A full rotating holy weapon sweep around the hero.",
    "Tempest of Light",
    "area",
    {"angle": 360, "heal": 0.07},
    angle=360,
)
add(
    "Consecration",
    "field",
    "holy",
    8,
    2.2,
    105,
    0,
    "A pulsing golden rune field that always follows you.",
    "Hallowed Ground",
    "duration",
    {"persistent": True, "shield": 0.1},
    follow=True,
    pulse=0.5,
)
add(
    "Avenger's Shield",
    "projectile",
    "holy",
    26,
    2.5,
    16,
    390,
    "A holy shield ricochets between nearby enemies.",
    "Bulwark of the Light",
    "piercing",
    {"bounce": 8, "splash": 60},
    bounce=2,
)
add(
    "Hammer of Wrath",
    "projectile",
    "holy",
    40,
    2.8,
    15,
    530,
    "A homing execution hammer deals extra damage below 35% health.",
    "Final Reckoning",
    "might",
    {"execute": 2, "splash": 90},
    homing=True,
    execute=0.8,
)
add(
    "Blade of Justice",
    "arc",
    "holy",
    48,
    2.8,
    160,
    0,
    "A narrow long holy blade strike toward the nearest target.",
    "Heavenly Arsenal",
    "area",
    {"angle": 180, "knockback": 50},
    angle=55,
)
add(
    "Holy Shock",
    "chain",
    "holy",
    20,
    2,
    350,
    0,
    "Lightning chains across enemies and heals a little per hit.",
    "Holy Conduit",
    "haste",
    {"chain": 6, "heal": 0.08},
    chain=2,
    heal=0.03,
)
add(
    "Wake of Ashes",
    "projectile",
    "holy",
    35,
    3.5,
    24,
    310,
    "Piercing waves of holy flame burn and push enemies.",
    "Ashen Crusade",
    "velocity",
    {"radial_rank": 1, "dot": 0.45},
    spread=30,
    dot=0.25,
    knockback=20,
)
add(
    "Blessed Hammer",
    "orbit",
    "holy",
    22,
    3,
    85,
    145,
    "Engraved hammers orbit you and repeatedly strike nearby foes.",
    "Celestial Wheel",
    "projectiles",
    {"pulse": 0.25, "heal": 0.03},
    pulse=0.5,
)
add(
    "Eye of Tyr",
    "area",
    "holy",
    40,
    4.8,
    155,
    0,
    "A protective holy detonation grants a brief absorb shield.",
    "Tyr Eternal",
    "armor",
    {"shield": 1.5, "slow": 0.6},
    shield=0.5,
    slow=0.2,
)
finish()
finish = cls("warrior", "physical", 160, 220, 0.16, ["heroic_leap", "shield_wall", "rallying_cry"])
add(
    "Mortal Strike",
    "arc",
    "physical",
    38,
    1.1,
    100,
    0,
    "A heavy aimed axe arc cleaves nearby targets.",
    "Mortal Onslaught",
    "might",
    {"angle": 160, "execute": 0.75},
    angle=95,
)
add(
    "Whirlwind",
    "area",
    "physical",
    23,
    1.8,
    110,
    0,
    "A circular steel sweep hits all surrounding enemies.",
    "Iron Cyclone",
    "area",
    {"kind": "field", "follow": True, "pulse": 0.35},
    knockback=8,
)
add(
    "Thunder Clap",
    "wave",
    "physical",
    27,
    3,
    170,
    0,
    "An expanding thunder ring slows enemies it reaches.",
    "Thunderlord",
    "area",
    {"slow": 0.7, "knockback": 45},
    slow=0.3,
)
add(
    "Execute",
    "arc",
    "physical",
    44,
    2.1,
    115,
    0,
    "Always strikes; doubles damage against enemies below 35% health.",
    "Executioner",
    "might",
    {"execute": 3, "angle": 120},
    angle=70,
    execute=1,
)
add(
    "Bladestorm",
    "field",
    "physical",
    12,
    3.8,
    90,
    0,
    "A following storm of steel deals repeated damage.",
    "Unstoppable Storm",
    "duration",
    {"persistent": True, "pulse": 0.25},
    follow=True,
    pulse=0.4,
)
add(
    "Heroic Throw",
    "projectile",
    "physical",
    32,
    2,
    14,
    470,
    "A heavy returning axe strikes outward and on its return.",
    "Titanic Throw",
    "velocity",
    {"bounce": 5, "splash": 65},
    returning=True,
)
add(
    "Rend",
    "dot",
    "physical",
    9,
    2.7,
    18,
    0,
    "Bleeding wounds prioritize unmarked targets and spread at Rank 5.",
    "Bloodbath",
    "duration",
    {"spread_dot": True, "death_burst": True},
    dot=1,
)
add(
    "Cleave",
    "arc",
    "physical",
    28,
    1.5,
    135,
    0,
    "A broad low axe sweep knocks enemies away.",
    "Colossus Cleave",
    "area",
    {"angle": 260, "execute": 0.6},
    angle=150,
    knockback=25,
)
add(
    "Ravager",
    "field",
    "physical",
    14,
    4.2,
    100,
    100,
    "A thrown spinning axe storm travels through crowds.",
    "Ravaging Arsenal",
    "velocity",
    {"follow": True, "persistent": True},
    pulse=0.45,
)
add(
    "Shockwave",
    "arc",
    "physical",
    38,
    3.2,
    250,
    0,
    "A long forward ground rupture stuns through a narrow cone.",
    "Worldbreaker",
    "area",
    {"angle": 180, "slow": 0.85},
    angle=45,
    slow=0.65,
    knockback=35,
)
finish()
finish = cls("mage", "frost", 95, 225, 0.02, ["blink", "ice_block", "combustion"])
add(
    "Frostbolt",
    "projectile",
    "frost",
    25,
    1.15,
    12,
    430,
    "Crystal bolts slow enemies; Rank 6 opens radial frost volleys.",
    "Glacial Barrage",
    "projectiles",
    {"radial_rank": 1, "homing": True, "slow": 0.6},
    radial_rank=6,
    slow=0.25,
)
add(
    "Fireball",
    "projectile",
    "fire",
    32,
    1.8,
    14,
    350,
    "A fireball explodes and leaves burning wounds.",
    "Inferno Sphere",
    "area",
    {"splash": 160, "dot": 0.5},
    splash=65,
    dot=0.18,
)
add(
    "Arcane Missiles",
    "projectile",
    "arcane",
    14,
    1.6,
    10,
    480,
    "A tight homing spread of violet missiles seeks nearby targets.",
    "Arcane Fusillade",
    "haste",
    {"radial_rank": 1, "bounce": 2},
    homing=True,
    spread=8,
)
add(
    "Blizzard",
    "field",
    "frost",
    10,
    4,
    120,
    95,
    "A traveling ice storm pulses cold damage and slows enemies.",
    "Eternal Winter",
    "duration",
    {"follow": True, "persistent": True, "slow": 0.6},
    pulse=0.5,
    slow=0.3,
)
add(
    "Frozen Orb",
    "field",
    "frost",
    15,
    3.5,
    65,
    170,
    "A dense drifting frost orb pierces through nearby groups.",
    "Polar Vortex",
    "velocity",
    {"pulse": 0.2, "slow": 0.8},
    pulse=0.4,
    slow=0.4,
)
add(
    "Flamestrike",
    "field",
    "fire",
    58,
    3.8,
    125,
    0,
    "A brief marked delay precedes a fiery ground eruption.",
    "Phoenix Pillar",
    "area",
    {"persistent": True, "pulse": 1},
    delay=0.6,
    pulse=1,
    dot=0.2,
)
add(
    "Arcane Explosion",
    "area",
    "arcane",
    30,
    2.2,
    150,
    0,
    "A violet burst damages all enemies around you.",
    "Arcane Supernova",
    "area",
    {"kind": "wave", "knockback": 80},
    knockback=15,
)
add(
    "Pyroblast",
    "projectile",
    "fire",
    78,
    4.5,
    24,
    240,
    "A slow enormous fireball explodes with heavy burning damage.",
    "Sunfall",
    "might",
    {"splash": 180, "execute": 1},
    splash=100,
    dot=0.4,
)
add(
    "Ice Lance",
    "projectile",
    "frost",
    28,
    1.5,
    9,
    650,
    "Fast piercing ice spears strike straight through enemies.",
    "Shatterstorm",
    "piercing",
    {"radial_rank": 1, "slow": 0.8},
    slow=0.15,
    spread=18,
)
add(
    "Meteor",
    "field",
    "fire",
    95,
    6,
    180,
    0,
    "A large warning rune becomes a delayed meteor blast.",
    "Extinction",
    "area",
    {"death_burst": True, "dot": 0.7},
    delay=1,
    pulse=1,
    knockback=55,
)
finish()
finish = cls(
    "hunter", "nature", 115, 245, 0.06, ["disengage", "aspect_of_the_turtle", "bestial_wrath"]
)
add(
    "Arcane Shot",
    "projectile",
    "arcane",
    26,
    1.05,
    10,
    560,
    "An enchanted arrow acquires a nearby enemy automatically.",
    "Astral Quiver",
    "velocity",
    {"homing": True, "bounce": 3},
    spread=10,
)
add(
    "Multi-Shot",
    "projectile",
    "physical",
    20,
    1.9,
    10,
    500,
    "A wide fan of arrows covers several enemies.",
    "Thousand Arrows",
    "projectiles",
    {"radial_rank": 1, "spread": 30},
    spread=26,
)
add(
    "Aimed Shot",
    "projectile",
    "physical",
    58,
    2.8,
    10,
    760,
    "A powerful narrow piercing shot punches through a line.",
    "Deadeye",
    "piercing",
    {"execute": 2, "homing": True},
    spread=4,
)
add(
    "Rapid Fire",
    "projectile",
    "physical",
    11,
    0.7,
    7,
    620,
    "Rapid tight arrow volleys provide constant pressure.",
    "Endless Salvo",
    "haste",
    {"bounce": 3, "spread": 15},
    spread=6,
)
add(
    "Barrage",
    "projectile",
    "physical",
    17,
    2.5,
    11,
    460,
    "A sweeping fan of heavy penetrating bolts.",
    "Horizon Barrage",
    "projectiles",
    {"radial_rank": 1, "splash": 40},
    spread=42,
)
add(
    "Explosive Shot",
    "projectile",
    "fire",
    32,
    2.6,
    13,
    390,
    "An explosive arrow bursts into fire around its target.",
    "Cluster Bomb",
    "area",
    {"splash": 150, "dot": 0.4},
    splash=85,
)
add(
    "Kill Shot",
    "projectile",
    "physical",
    42,
    2,
    12,
    690,
    "A homing finisher gains bonus damage below 35% health.",
    "Death from Afar",
    "might",
    {"execute": 3, "bounce": 2},
    homing=True,
    execute=1.2,
)
add(
    "Serpent Sting",
    "dot",
    "nature",
    10,
    2.5,
    12,
    0,
    "Poison marks fresh targets and spreads from Rank 5.",
    "Venom Plague",
    "duration",
    {"spread_dot": True, "slow": 0.5},
    dot=1,
    slow=0.1,
)
add(
    "Beast Companion",
    "companion",
    "physical",
    24,
    1.2,
    35,
    270,
    "An invulnerable wolf leashes to you and attacks nearby foes.",
    "Alpha Pack",
    "might",
    {"execute": 1, "summon": "alpha_wolf", "extra_pets": 2, "leap_distance": 160},
    summon="wolf",
    leap_rank=3,
    leap_distance=110,
    attack_range=300,
)
add(
    "Stampede",
    "charge",
    "physical",
    38,
    5,
    28,
    400,
    "Temporary wolves charge through enemies, distinct from your pet.",
    "Primal Stampede",
    "projectiles",
    {"splash": 65, "knockback": 35},
    summon="wolf",
    spread=18,
)
finish()
finish = cls(
    "warlock", "shadow", 120, 205, 0.07, ["demonic_circle", "unending_resolve", "dark_soul"]
)
add(
    "Shadow Bolt",
    "projectile",
    "shadow",
    29,
    1.2,
    14,
    410,
    "Dark bolts progress to radial Shadow Volley at Rank 6.",
    "Shadow Volley",
    "projectiles",
    {"radial_rank": 1, "bounce": 3},
    radial_rank=6,
)
add(
    "Corruption",
    "dot",
    "shadow",
    10,
    2.6,
    18,
    0,
    "Corruption marks fresh foes and spreads from Rank 5.",
    "Absolute Corruption",
    "duration",
    {"spread_dot": True, "death_burst": True},
    dot=1,
)
add(
    "Immolate",
    "dot",
    "fire",
    12,
    2.8,
    20,
    0,
    "A fire curse burns over time and spreads from Rank 5.",
    "Unquenchable Flame",
    "might",
    {"spread_dot": True, "heal": 0.03},
    dot=1,
)
add(
    "Rain of Fire",
    "field",
    "fire",
    13,
    4.2,
    150,
    0,
    "Repeated fiery impacts burn a targeted ground zone.",
    "Hellfire Deluge",
    "duration",
    {"persistent": True, "pulse": 0.25},
    pulse=0.5,
    dot=0.15,
)
add(
    "Chaos Bolt",
    "projectile",
    "fire",
    65,
    3.2,
    20,
    320,
    "A homing fel bolt punches through targets and detonates.",
    "Chaos Cataclysm",
    "piercing",
    {"bounce": 4, "splash": 130},
    homing=True,
    splash=70,
)
add(
    "Seed of Corruption",
    "dot",
    "shadow",
    8,
    3.6,
    22,
    0,
    "A shadow seed ticks and explodes when its host dies.",
    "Soul Harvest",
    "area",
    {"spread_dot": True, "death_burst": True},
    dot=1,
    death_burst=True,
)
add(
    "Hand of Gul'dan",
    "charge",
    "shadow",
    42,
    4.5,
    35,
    310,
    "Temporary imps charge in a spread and explode on contact.",
    "Legionfall",
    "projectiles",
    {"summon": "felguard", "splash": 100},
    summon="imp",
    splash=60,
    spread=22,
)
add(
    "Summon Felguard",
    "companion",
    "fire",
    18,
    1.6,
    9,
    620,
    "An invulnerable Imp stays near you and casts fel firebolts. Rank 4 adds splash, Rank 5 a second Imp, Rank 6 twin bolts and burning, Rank 7 better range and haste, Rank 8 empowered blasts.",
    "Imp Legion",
    "armor",
    {"extra_pets": 2, "volley_count": 2, "splash": 65, "attack_range": 300, "homing": True},
    summon="imp",
    ranged=True,
    splash=24,
    splash_rank=4,
    dot=0.25,
    dot_rank=6,
    volley_rank=6,
    attack_range=240,
    range_per_rank=10,
)
# Keep IDs for existing saves and base-ID talent bonuses; only the visible identity changes.
imp = abilities[-1]
imp["name"] = "Summon Imp"
imp_progression = (
    (18, 1.6, 9, 1, "One Imp fires fel firebolts."),
    (25, 1.55, 9.5, 1, "Stronger firebolts."),
    (29, 1.25, 10, 1, "Faster casting."),
    (34, 1.2, 10.5, 1, "Firebolts gain small splash damage."),
    (39, 1.15, 11, 2, "Summon a second Imp."),
    (45, 1.1, 12, 2, "Twin firebolts apply burning damage."),
    (52, 0.85, 13, 2, "Longer range and faster casting."),
    (65, 0.75, 15, 2, "Empower both Imps with stronger splash blasts."),
)
for row, (damage, cooldown, radius, count, description) in zip(
    imp["ranks"], imp_progression, strict=True
):
    row.update(
        damage=damage,
        cooldown=cooldown,
        radius=radius,
        count=count,
        description=f"{description} {damage} fire damage; {cooldown}s interval; {count} Imp(s).",
    )
add(
    "Shadowburn",
    "chain",
    "shadow",
    45,
    2.5,
    350,
    0,
    "Dark fire jumps twice and executes weakened enemies.",
    "Soulfire Cascade",
    "haste",
    {"chain": 7, "execute": 2},
    chain=2,
    execute=0.8,
)
add(
    "Cataclysm",
    "field",
    "fire",
    82,
    5.5,
    175,
    0,
    "A delayed fel eruption applies burning wounds in a large zone.",
    "Apocalypse",
    "area",
    {"dot": 0.9, "slow": 0.6},
    delay=0.8,
    pulse=1,
    dot=0.4,
)
finish()
finish = cls(
    "priest", "holy", 105, 220, 0.04, ["power_word_shield", "desperate_prayer", "psychic_scream"]
)
add(
    "Smite",
    "projectile",
    "holy",
    28,
    1.1,
    12,
    500,
    "A searing golden spear seeks the nearest enemy.",
    "Divine Verdict",
    "might",
    {"homing": True, "execute": 1},
    spread=6,
)
add(
    "Holy Fire",
    "dot",
    "holy",
    13,
    2.7,
    19,
    0,
    "Golden brands burn fresh targets and return a little health.",
    "Sacred Flame",
    "duration",
    {"spread_dot": True, "heal": 0.1},
    dot=1,
    heal=0.04,
)
add(
    "Shadow Word: Pain",
    "dot",
    "shadow",
    11,
    2.4,
    17,
    0,
    "A violet curse marks fresh foes and spreads from Rank 5.",
    "Endless Torment",
    "duration",
    {"spread_dot": True, "slow": 0.5},
    dot=1,
)
add(
    "Mind Blast",
    "chain",
    "shadow",
    44,
    2.5,
    400,
    0,
    "Focused psychic energy jumps through a small enemy cluster.",
    "Psychic Rupture",
    "might",
    {"chain": 5, "splash": 80},
    chain=2,
)
add(
    "Mind Sear",
    "field",
    "shadow",
    12,
    3.4,
    95,
    0,
    "Persistent psychic pulses sear a targeted ground cluster.",
    "Mind Inferno",
    "area",
    {"follow": True, "persistent": True},
    pulse=0.35,
)
add(
    "Penance",
    "projectile",
    "holy",
    16,
    1.9,
    9,
    540,
    "A tight trio of homing holy bolts heals on impact.",
    "Absolution",
    "haste",
    {"bounce": 3, "heal": 0.15},
    homing=True,
    heal=0.04,
    spread=7,
)
add(
    "Shadow Crash",
    "projectile",
    "shadow",
    52,
    3.5,
    23,
    270,
    "A heavy shadow globe crashes into a large slowing explosion.",
    "Void Collapse",
    "area",
    {"splash": 180, "death_burst": True, "dot": 0.4},
    splash=110,
    slow=0.3,
)
add(
    "Holy Nova",
    "area",
    "holy",
    25,
    2.8,
    130,
    0,
    "A circular holy nova damages foes and heals the priest.",
    "Radiant Renewal",
    "health",
    {"heal": 0.15, "shield": 0.6},
    heal=0.08,
)
add(
    "Void Torrent",
    "beam",
    "shadow",
    16,
    4,
    480,
    0,
    "A channeled aimed void beam repeatedly cuts a straight line.",
    "Event Horizon",
    "duration",
    {"pulse": 0.15, "execute": 1},
    pulse=0.3,
    slow=0.2,
)
add(
    "Divine Star",
    "projectile",
    "holy",
    30,
    2.6,
    18,
    400,
    "A piercing holy star travels outward, then returns and heals.",
    "Celestial Return",
    "velocity",
    {"splash": 90, "heal": 0.12},
    returning=True,
    heal=0.05,
)
finish()

passive_rows = [
    (
        "projectiles",
        "Multicast",
        "+1 effect per rank.",
        "Projectile volleys, chains, DoT targets, orbiters and summons; no extra disks/arcs/fields/beams.",
    ),
    (
        "area",
        "Reach",
        "+20% attack area per rank.",
        "Projectile collision, melee reach, field/wave size, chain range and companion cleave. DoTs: spread/death explosion area only; no tick damage bonus.",
    ),
    (
        "might",
        "Might",
        "+15% damage per rank.",
        "All automatic damage, including DoT ticks and owner-bound companion attacks.",
    ),
    (
        "haste",
        "Haste",
        "-7% cooldown per rank.",
        "Automatic and manual cooldowns; companion attack interval. Does not shorten DoT tick interval.",
    ),
    (
        "duration",
        "Endurance",
        "+20% duration per rank.",
        "Fields, channels, DoTs, orbiters, temporary summons and manual timed effects; permanent pets never expire.",
    ),
    (
        "velocity",
        "Velocity",
        "+15% projectile speed per rank.",
        "Moving shots (including Imp firebolts), moving fields and charging summons; no permanent-pet movement or orbit rotation bonus.",
    ),
    (
        "movement",
        "Fleetfoot",
        "+8% movement speed per rank.",
        "Hero movement only; does not change projectile speed.",
    ),
    ("pickup", "Magnetism", "+30 pickup range per rank.", "XP, gold and chest attraction only."),
    (
        "armor",
        "Fortitude",
        "+8 percentage points damage reduction per rank, capped at 75%.",
        "Player contact damage only; companions cannot take damage.",
    ),
    ("health", "Vitality", "+20 maximum health and heal 20 per rank.", "Hero health only."),
    (
        "regen",
        "Renewal",
        "Regenerate 0.6 health per second per rank.",
        "Hero health only; pauses with gameplay.",
    ),
    (
        "piercing",
        "Penetration",
        "+1 enemy penetrated per rank.",
        "Traveling projectiles only; orbiters already strike repeatedly and do not benefit. Not disks, arcs, DoTs, beams or pets.",
    ),
]
passives = [
    dict(id=p, name=n, description=d, max_rank=5, applicability=a) for p, n, d, a in passive_rows
]


def manual(name, kind, school, cd, duration, power, distance, description, direction=1):
    rows = []
    for i in range(3):
        rows.append(
            dict(
                cooldown=round(cd * (1 - 0.15 * i), 2),
                duration=round(duration * (1 + 0.35 * i), 2),
                power=round(power * (1 + 0.3 * i), 3),
                distance=distance * (1 + 0.2 * i),
                description=f"{description} Rank {i + 1}: {cd * (1 - 0.15 * i):g}s cooldown, {duration * (1 + 0.35 * i):g}s duration, power {power * (1 + 0.3 * i):g}, distance {distance * (1 + 0.2 * i):g}.",
            )
        )
    manuals.append(
        dict(
            id=slug(name),
            name=name,
            kind=kind,
            school=school,
            ranks=rows,
            description=description,
            direction=direction,
        )
    )


manual("Divine Shield", "immune", "holy", 32, 3, 1, 0, "Move freely while immune to all damage.")
manual(
    "Lay on Hands",
    "heal",
    "holy",
    38,
    1,
    1,
    0,
    "Restore up to full health; higher ranks add an absorb shield.",
)
manual(
    "Avenging Wrath", "buff", "holy", 25, 5, 0.5, 0, "Increase all automatic damage for a duration."
)
manual(
    "Heroic Leap",
    "leap",
    "physical",
    16,
    1,
    40,
    230,
    "Leap along movement/facing and damage enemies at landing.",
)
manual(
    "Shield Wall",
    "guard",
    "physical",
    24,
    5,
    1,
    0,
    "Gain 50 percentage points of armor, subject to the damage cap.",
)
manual(
    "Rallying Cry",
    "rally",
    "physical",
    30,
    6,
    0.25,
    0,
    "Temporarily increase maximum health and heal the added amount.",
)
manual(
    "Blink",
    "blink",
    "arcane",
    10,
    1,
    1,
    250,
    "Teleport forward to a valid map position with brief immunity.",
)
manual(
    "Ice Block",
    "immune",
    "frost",
    25,
    4,
    1,
    0,
    "Become immune and regenerate inside an immobile ice block.",
)
manual(
    "Combustion",
    "buff",
    "fire",
    24,
    6,
    0.8,
    0,
    "Amplify fire damage; frost and arcane attacks keep their normal damage.",
)
manual(
    "Disengage",
    "blink",
    "nature",
    12,
    1,
    1,
    210,
    "Leap backward from facing with brief immunity.",
    -1,
)
manual(
    "Aspect of the Turtle",
    "immune",
    "nature",
    28,
    4,
    1,
    0,
    "Move freely inside an invulnerable protective shell.",
)
manual(
    "Bestial Wrath",
    "buff",
    "nature",
    23,
    6,
    1,
    0,
    "Greatly amplify permanent and charging companion damage.",
)
manual(
    "Demonic Circle",
    "circle",
    "shadow",
    14,
    1,
    1,
    0,
    "First press places a rune; second returns from any distance, then starts cooldown.",
)
manual(
    "Unending Resolve", "guard", "shadow", 24, 5, 1, 0, "Gain armor and a temporary absorb shield."
)
manual(
    "Dark Soul", "buff", "shadow", 26, 6, 0.8, 0, "Amplify shadow damage during the empowerment."
)
manual(
    "Power Word: Shield",
    "shield",
    "holy",
    15,
    5,
    45,
    0,
    "Absorb incoming damage with a timed protective shield.",
)
manual(
    "Desperate Prayer",
    "heal",
    "holy",
    25,
    1,
    0.5,
    0,
    "Instantly restore a fraction of maximum health; ranks increase healing.",
)
manual(
    "Psychic Scream",
    "fear",
    "shadow",
    18,
    3,
    25,
    200,
    "Damage nearby enemies and force them to flee temporarily.",
)
for m in manuals:
    if m["id"] == "ice_block":
        m.update(root=True, regen=0.03)
    if m["id"] == "unending_resolve":
        m["shield_fraction"] = 0.15
    if m["id"] == "combustion":
        m["buff_school"] = "fire"
    if m["id"] == "dark_soul":
        m["buff_school"] = "shadow"
    if m["id"] == "bestial_wrath":
        m["pet_buff"] = True
assert (
    len(abilities) == 60 and len(manuals) == 18 and all(len(c["abilities"]) == 10 for c in classes)
)
PATH.write_text(
    json.dumps(
        dict(
            classes=classes,
            abilities=abilities,
            manuals=manuals,
            passives=passives,
            enemies=original["enemies"],
        ),
        indent=2,
    )
    + "\n",
    "utf-8",
)
print(
    "Wrote 60 automatic definitions, 480 explicit rank records, 60 evolutions, 18 manuals and 12 passives"
)
