"""Author the permanent progression catalog; runtime reads only the emitted JSON."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/warcraft_survivors/data"
content = json.loads((DATA / "content.json").read_text(encoding="utf-8"))
classes = content["classes"]
names = {
    "paladin": [
        "Crusader Training",
        "Blessed Constitution",
        "Swift Justice",
        "Sanctified Plate",
        "Holy Conviction",
        "Hallowed Ground",
        "Lasting Blessings",
        "Twin Judgment",
        "Light of Recovery",
        "Zealous Storm",
        "Champion of Elwynn",
        "Radiant Hammer",
        "Chosen Blessing",
        "Devout Focus",
        "Sacred Reach",
        "Avenging Light",
        "Bastion of Hope",
        "Heavenly Judgment",
    ],
    "warrior": [
        "Weapon Discipline",
        "Iron Constitution",
        "Combat Rhythm",
        "Forged Armor",
        "Arms Mastery",
        "Sweeping Blades",
        "Enduring Fury",
        "Broad Mortal Strike",
        "Second Breath",
        "War Machine",
        "Monster Slayer",
        "Heavy Throw",
        "Battle Preparation",
        "Veteran Reflexes",
        "Deep Wounds",
        "Titan Strength",
        "Unbreakable",
        "Executioner",
    ],
    "mage": [
        "Arcane Study",
        "Mystic Vigor",
        "Quick Casting",
        "Ice Armor",
        "Frost Attunement",
        "Expansive Magic",
        "Lingering Sorcery",
        "Piercing Frostbolt",
        "Meditation",
        "Burning Fields",
        "Giant Killer",
        "Accelerated Missiles",
        "Prepared Grimoire",
        "Spellweaving",
        "Lasting Blizzard",
        "Archmage Convergence",
        "Prismatic Ward",
        "Frostfire Mastery",
    ],
    "hunter": [
        "Steady Training",
        "Survivalist",
        "Quick Draw",
        "Reinforced Leathers",
        "Arcane Marksmanship",
        "Wide Volley",
        "Lingering Traps",
        "Twin Arcane Shot",
        "Natural Recovery",
        "Beast Training",
        "Hogger Tracker",
        "Piercing Aim",
        "Chosen Companion",
        "Instinctive Reflexes",
        "Long Hunt",
        "Master of the Wild",
        "Predator Focus",
        "Explosive Arsenal",
    ],
    "warlock": [
        "Forbidden Study",
        "Dark Vitality",
        "Rapid Rituals",
        "Demon Skin",
        "Shadow Affinity",
        "Spreading Shadows",
        "Lingering Curses",
        "Piercing Shadow Bolt",
        "Siphoned Recovery",
        "Demonic Command",
        "Boss Hex",
        "Intense Corruption",
        "Pact Preparation",
        "Dark Focus",
        "Lasting Fire",
        "Lord of Dread",
        "Soul Harvest",
        "Chaotic Dominion",
    ],
    "priest": [
        "Devout Study",
        "Inner Vitality",
        "Swift Prayers",
        "Inner Armor",
        "Holy Affinity",
        "Radiant Reach",
        "Lasting Words",
        "Piercing Smite",
        "Quiet Recovery",
        "Persistent Agony",
        "Exorcist",
        "Empowered Penance",
        "Prepared Liturgy",
        "Prayer Discipline",
        "Wide Holy Nova",
        "Divine Ascendance",
        "Aegis of Light",
        "Shadow Revelation",
    ],
}
starters = {c["id"]: c["abilities"][0] for c in classes}
selected = {
    "paladin": ["consecration", "blessed_hammer"],
    "warrior": ["thunder_clap", "rend"],
    "mage": ["fireball", "arcane_missiles"],
    "hunter": ["beast_companion", "serpent_sting"],
    "warlock": ["summon_felguard", "corruption"],
    "priest": ["holy_fire", "shadow_word_pain"],
}
ids = [
    "might",
    "health",
    "haste",
    "armor",
    "school",
    "area",
    "duration",
    "signature",
    "recovery",
    "specialist",
    "slayer",
    "technique",
    "preparation",
    "manual",
    "mastery",
    "capstone",
    "survival",
    "offense",
]
schools = {
    "paladin": "holy",
    "warrior": "physical",
    "mage": "frost",
    "hunter": "arcane",
    "warlock": "shadow",
    "priest": "holy",
}
kinds = {
    "paladin": "area",
    "warrior": "arc",
    "mage": "field",
    "hunter": "companion",
    "warlock": "companion",
    "priest": "dot",
}
tech = {
    "paladin": ("blessed_hammer", "count", 1),
    "warrior": ("heroic_throw", "count", 1),
    "mage": ("arcane_missiles", "speed", 0.2),
    "hunter": ("aimed_shot", "pierce", 1),
    "warlock": ("corruption", "damage", 0.12),
    "priest": ("penance", "count", 1),
}
master = {
    "paladin": ("consecration", "radius", 0.15),
    "warrior": ("rend", "duration", 0.15),
    "mage": ("blizzard", "duration", 0.15),
    "hunter": ("serpent_sting", "duration", 0.15),
    "warlock": ("immolate", "duration", 0.15),
    "priest": ("holy_nova", "radius", 0.15),
}
cap = {
    "paladin": {"school:holy": 0.12, "boss_damage": 0.2, "kill_heal": 0.25},
    "warrior": {"school:physical": 0.12, "low_health_damage": 0.2, "armor": 0.03},
    "mage": {"school:fire": 0.12, "school:frost": 0.12, "school:arcane": 0.12, "area": 0.15},
    "hunter": {"kind:companion": 0.3, "count": 1, "boss_damage": 0.15},
    "warlock": {"kind:dot": 0.25, "kind:companion": 0.2, "duration": 0.1},
    "priest": {"school:holy": 0.15, "kill_shield": 0.5, "healing": 0.2},
}
survival = {
    "paladin": {"kill_shield": 0.4},
    "warrior": {"health": 0.08, "armor": 0.02},
    "mage": {"starting_shield": 25, "healing": 0.1},
    "hunter": {"speed": 0.05, "boss_damage": 0.1},
    "warlock": {"kill_heal": 0.4},
    "priest": {"starting_shield": 30, "armor": 0.02},
}
offense = {
    "paladin": {"spell:judgment:count": 1, "spell:judgment:damage": 0.1},
    "warrior": {"execute": 0.2, "spell:execute:radius": 0.15},
    "mage": {"school:fire": 0.15, "school:frost": 0.15},
    "hunter": {"spell:explosive_shot:radius": 0.2, "kind:charge": 0.2},
    "warlock": {"spell:chaos_bolt:damage": 0.2, "spell:chaos_bolt:pierce": 1},
    "priest": {"school:shadow": 0.2, "spell:mind_sear:radius": 0.2},
}
ability_names = {a["id"]: a["name"] for a in content["abilities"]}


def describe(key, value):
    if key.startswith("school:"):
        return f"{key.split(':')[1].title()} automatic damage +{value:.1%}"
    if key.startswith("kind:"):
        labels = {
            "arc": "Cleave",
            "area": "Area",
            "field": "Ground attack",
            "dot": "Damage over time",
            "companion": "Companion",
            "charge": "Charging summon",
        }
        return f"{labels[key.split(':')[1]]} damage +{value:.0%}"
    if key.startswith("spell:"):
        _, aid, stat = key.split(":")
        label = {
            "count": "additional effects",
            "pierce": "additional pierces",
            "speed": "travel speed",
            "radius": "attack area",
            "damage": "damage",
            "duration": "duration",
        }[stat]
        amount = f"+{value:g}" if stat in {"count", "pierce"} else f"+{value:.0%}"
        return f"{ability_names[aid]} {label} {amount}"
    labels = {
        "damage": "Automatic damage",
        "health": "Base maximum health",
        "armor": "Armor",
        "haste": "All cooldowns",
        "manual_haste": "Manual cooldowns",
        "area": "Attack area",
        "duration": "Attack duration",
        "speed": "Movement speed",
        "healing": "Healing received",
        "boss_damage": "Damage to bosses",
        "low_health_damage": "Damage while below 35% health",
        "execute": "Damage against foes below 35% health",
    }
    if key in {"haste", "manual_haste"}:
        return f"{labels[key]} -{value:.1%}"
    if key in labels:
        return f"{labels[key]} +{value:.1%}"
    if key == "regen":
        return f"Recover {value:g} health/second"
    if key == "kill_heal":
        return f"Restore {value:g} health per kill"
    if key == "kill_shield":
        return f"Gain {value:g} shield per kill, capped at 25% health"
    if key == "starting_shield":
        return f"Start with {value:g} shield for 20 seconds"
    if key == "count":
        return f"+{value:g} effects for volleys, companions, chains and curses"
    raise ValueError(key)


trees = {}
for cls in classes:
    cid = cls["id"]
    starter = starters[cid]
    ta, tf, tv = tech[cid]
    ma, mf, mv = master[cid]
    effects = [
        {"damage": 0.02},
        {"health": 0.03},
        {"haste": 0.015},
        {"armor": 0.01},
        {"school:" + schools[cid]: 0.035},
        {"area": 0.025},
        {"duration": 0.04},
        {f"spell:{starter}:radius": 0.12}
        if cid == "warrior"
        else {f"spell:{starter}:count": 1}
        if cid in ("paladin", "hunter")
        else {f"spell:{starter}:pierce": 1},
        {"regen": 0.08},
        {"kind:" + kinds[cid]: 0.04},
        {"boss_damage": 0.03},
        {f"spell:{ta}:{tf}": tv},
        {},
        {"manual_haste": 0.04},
        {f"spell:{ma}:{mf}": mv},
        cap[cid],
        survival[cid],
        offense[cid],
    ]
    ranks = [3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 1, 2, 2, 1, 1, 1]
    rows = []
    for i, tid in enumerate(ids):
        tier = i // 3
        requirements = {} if tier == 0 else {ids[i - 3]: 1}
        description = "; ".join(describe(k, v) for k, v in effects[i].items()) + ". Per rank."
        if tid == "preparation":
            description = "Unlock one optional extra Rank 1 starting ability. Choose it here between runs; no selection means no extra ability."
        rows.append(
            dict(
                id=tid,
                name=names[cid][i],
                description=description,
                max_rank=ranks[i],
                tier=tier,
                column=i % 3,
                min_level=[1, 3, 6, 10, 15, 22][tier],
                spent_required=[0, 3, 6, 10, 15, 22][tier],
                requires=requirements,
                effects=effects[i],
                starting_options=selected[cid] if tid == "preparation" else [],
            )
        )
    trees[cid] = rows
shared = []
for sid, name, desc, capn, base, key, value in [
    ("health", "Endurance", "Maximum health +3% per rank", 5, 65, "health", 0.03),
    ("might", "Training", "All automatic damage +2% per rank", 5, 80, "damage", 0.02),
    ("armor", "Reinforcement", "Armor +1 percentage point per rank", 5, 90, "armor", 0.01),
    ("movement", "Trailcraft", "Movement speed +2% per rank", 5, 75, "speed", 0.02),
    ("magnet", "Gathering", "Pickup range +12 units per rank", 5, 55, "pickup", 12),
    ("xp", "Insight", "Run gem XP +4% per rank", 5, 100, "xp", 0.04),
    (
        "greed",
        "Prosperity",
        "Run gold rewards +4% per rank; achievement gold unchanged",
        5,
        110,
        "gold",
        0.04,
    ),
    ("regen", "Recovery", "Regenerate 0.1 health/sec per rank", 5, 90, "regen", 0.1),
    (
        "rerolls",
        "Second Thoughts",
        "One additional card reroll each run per rank (R / X)",
        3,
        180,
        "rerolls",
        1,
    ),
    (
        "choices",
        "Wisdom",
        "Permanent fourth level-up card; requires eight shared ranks",
        1,
        450,
        "choices",
        1,
    ),
]:
    shared.append(
        dict(
            id=sid,
            name=name,
            description=desc,
            max_rank=capn,
            costs=[base * (r + 1) for r in range(capn)],
            requires_ranks=8 if sid == "choices" else 0,
            effects={key: value},
        )
    )
ach = []


def achievement(aid, name, metric, target, gold, description=None, cid=""):
    ach.append(
        dict(
            id=aid,
            name=name,
            metric=metric,
            target=target,
            gold=gold,
            description=description or f"{metric.replace('_', ' ').title()}: {target}",
            class_id=cid,
        )
    )


for args in [
    ("first_blood", "First Blood", "kills", 1, 20),
    ("centurion", "Centurion", "run_kills", 100, 50),
    ("survivor", "Survivor", "best_time", 300, 75),
    ("elite", "Elite Hunter", "elites", 1, 80),
    ("evolution", "Ascension", "evolved", 1, 100),
    ("victory", "Defender of Elwynn", "hogger", 1, 300),
    ("kills_500", "Forest Defender", "kills", 500, 100),
    ("kills_5000", "Horde Breaker", "kills", 5000, 300),
    ("kills_25000", "Legend of Elwynn", "kills", 25000, 700),
    ("elites_10", "Champion Hunter", "elites", 10, 200),
    ("elites_25", "Elite Vanguard", "elites", 25, 400),
    ("survive_10", "Tenacious", "best_time", 600, 60),
    ("survive_20", "Unyielding", "best_time", 1200, 100),
    ("survive_30", "Last Stand", "best_time", 1800, 150),
    ("hogger_5", "Gnoll Nemesis", "hogger", 5, 600),
    ("evolve_10", "Master of Evolution", "evolved", 10, 300),
    ("level_5", "Apprentice Champion", "class_level", 5, 150),
    ("level_15", "Seasoned Champion", "class_level", 15, 300),
    ("level_30", "Veteran Champion", "class_level", 30, 600),
    ("wins_2", "Versatile Champion", "winning_classes", 2, 300),
    ("unlock_rogue", "Three Roads to Victory", "winning_classes", 3, 400),
    ("unlock_druid", "Keeper of Elwynn", "evolved", 25, 500),
    ("unlock_shaman", "Voice of the Forest", "elites", 50, 500),
]:
    achievement(*args)
for cls in classes:
    achievement("level_" + cls["id"], cls["name"] + " Adept", "class_level", 10, 200, cid=cls["id"])
for bid, name in (
    ("stitches", "Terror of Darkshire"),
    ("bangalash", "King of the Jungle"),
    ("rivendare", "Scourgebreaker"),
    ("lich_king", "Frozen Throne"),
):
    achievement(
        "boss_" + bid,
        name,
        "boss:" + bid,
        1,
        250,
        "Defeat " + bid.replace("_", " ").title() + " in a complete run",
    )
registry = [
    dict(
        id=c["id"], name=c["name"], playable=True, achievement="", description="Initially unlocked"
    )
    for c in classes
]
registry += [
    dict(id=cid, name=name, playable=False, achievement=aid, description=desc)
    for cid, name, aid, desc in [
        ("rogue", "Rogue", "unlock_rogue", "Win with three different classes"),
        ("druid", "Druid", "unlock_druid", "Evolve 25 spells across runs"),
        ("shaman", "Shaman", "unlock_shaman", "Defeat 50 elites across runs"),
    ]
]
(DATA / "progression.json").write_text(
    json.dumps(
        dict(
            trees=trees,
            shared=shared,
            achievements=ach,
            classes=registry,
            zones=["elwynn", "duskwood", "stranglethorn", "plaguelands", "icecrown"],
        ),
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(
    f"Authored six 18-node trees, ten shared upgrades, {len(ach)} achievements and achievement-only future unlocks"
)
