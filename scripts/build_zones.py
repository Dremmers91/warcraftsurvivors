import copy
import json
from pathlib import Path

from enemy_classification import annotate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/warcraft_survivors/data"
core = json.loads((DATA / "content.json").read_text(encoding="utf-8"))
base = json.loads((DATA / "encounters.json").read_text(encoding="utf-8"))
enemies = []
attacks = []
elites = []
bosses = []
zones = []
zone_specs = [
    (
        "duskwood",
        "Duskwood",
        "Haunted roads and Raven Hill graves",
        1.2,
        71,
        "stitches",
        [
            ("zombie", "Rotting Villager", 32, 88, 12, 6, "chase", []),
            ("skeleton", "Grave Guardian", 48, 92, 15, 9, "bruiser", ["gnoll_smash"]),
            ("nightwolf", "Nightbane Hound", 39, 139, 14, 8, "flank", []),
            ("venom_spider", "Black Widow", 36, 115, 12, 9, "ranged", ["poison_spit"]),
            ("grave_caster", "Grave Necromancer", 61, 79, 17, 15, "ranged", ["lightning"]),
            ("restless_spirit", "Restless Spirit", 38, 112, 13, 10, "flank", ["spirit_wail"]),
            ("worgen", "Nightbane Stalker", 76, 151, 19, 14, "charge", ["worgen_lunge"]),
            ("skeletal_archer", "Raven Hill Archer", 52, 84, 16, 12, "ranged", ["arrow"]),
        ],
    ),
    (
        "stranglethorn",
        "Stranglethorn Vale",
        "Emerald jungle and forgotten troll temples",
        1.45,
        83,
        "bangalash",
        [
            ("raptor", "Jungle Raptor", 38, 140, 15, 8, "chase", []),
            ("troll", "Gurubashi Hunter", 52, 90, 18, 11, "ranged", ["arrow"]),
            ("panther", "Shadow Panther", 45, 150, 17, 10, "flank", []),
            ("jungle_boar", "Jungle Boar", 84, 116, 20, 14, "charge", ["boar_charge"]),
            ("troll_shaman", "Gurubashi Witch Doctor", 85, 80, 20, 18, "ranged", ["poison_spit"]),
            ("gorilla", "Jungle Gorilla", 118, 78, 24, 20, "bruiser", ["gorilla_slam"]),
            ("basilisk", "Crystal Basilisk", 74, 108, 18, 15, "ranged", ["basilisk_gaze"]),
            ("crocolisk", "River Crocolisk", 103, 111, 22, 18, "charge", ["boar_charge"]),
        ],
    ),
    (
        "plaguelands",
        "Eastern Plaguelands",
        "Blighted earth and the ruins of the Scourge",
        1.8,
        97,
        "rivendare",
        [
            ("ghoul", "Plague Ghoul", 48, 104, 18, 10, "chase", []),
            ("cultist", "Cult of the Damned", 73, 86, 22, 15, "ranged", ["lightning"]),
            ("plague_hound", "Plague Hound", 52, 146, 18, 12, "flank", []),
            ("crypt_fiend", "Crypt Fiend", 96, 95, 21, 17, "ranged", ["poison_spit"]),
            ("bone_knight", "Skeletal Deathguard", 133, 87, 28, 22, "bruiser", ["bear_swipe"]),
            ("banshee", "Plague Banshee", 62, 110, 19, 16, "ranged", ["spirit_wail"]),
            ("gargoyle", "Scourge Gargoyle", 94, 149, 24, 20, "flank", ["gargoyle_dive"]),
            ("abomination", "Plague Abomination", 184, 68, 30, 30, "bruiser", ["plague_bile"]),
        ],
    ),
    (
        "icecrown",
        "Icecrown",
        "Frozen wastes beneath the Icecrown Citadel",
        2.15,
        113,
        "lich_king",
        [
            ("geist", "Frozen Geist", 57, 127, 20, 13, "chase", []),
            ("vrykul", "Frost Vrykul", 106, 98, 28, 20, "bruiser", ["gnoll_smash"]),
            ("frost_hound", "Frost Hound", 63, 156, 22, 15, "flank", []),
            ("frost_cultist", "Frost Acolyte", 101, 83, 24, 22, "ranged", ["lightning"]),
            ("frost_abomination", "Frozen Abomination", 175, 76, 32, 28, "bruiser", ["bear_swipe"]),
            ("nerubian", "Nerubian Soldier", 138, 105, 29, 26, "charge", ["nerubian_rush"]),
            ("frost_revenant", "Frost Revenant", 114, 90, 25, 24, "ranged", ["revenant_shards"]),
            ("wyrm_hatchling", "Frost Wyrm Hatchling", 122, 145, 26, 25, "flank", ["wyrm_breath"]),
        ],
    ),
]


# New encounter primitives retain clear locked telegraphs and add control/persistent zones.
def atk(
    aid,
    name,
    kind,
    damage,
    cd,
    warning,
    duration,
    radius,
    reach,
    speed=0,
    count=1,
    angle=100,
    effect="hostile_arrow",
    color=(245, 131, 80),
    **extra,
):
    attacks.append(
        dict(
            id=aid,
            name=name,
            kind=kind,
            damage=damage,
            cooldown=cd,
            warning=warning,
            duration=duration,
            radius=radius,
            reach=reach,
            speed=speed,
            count=count,
            angle=angle,
            effect=effect,
            color=list(color),
            **extra,
        )
    )


atk(
    "stitches_hook",
    "Meat Hook",
    "missile",
    28,
    5,
    1.2,
    0.2,
    13,
    680,
    520,
    effect="hostile_hook",
    pull=150,
)
atk("stitches_cleave", "Butcher Cleave", "arc", 44, 4.6, 1.25, 0.25, 195, 260, angle=150)
atk(
    "stitches_vomit",
    "Poisonous Bile",
    "circle",
    14,
    6,
    1.3,
    4,
    165,
    600,
    effect="hostile_poison",
    color=(163, 210, 84),
    pulse=0.8,
    growth=8,
)
atk("stitches_stomp", "Rotting Shockwave", "ring", 30, 5.5, 1.3, 1.5, 340, 700)
atk("bangalash_pounce", "Predator Pounce", "leap", 34, 3.5, 0.9, 0.25, 110, 780)
atk("bangalash_rush", "Tiger Rush", "charge", 32, 3.8, 0.85, 0.8, 32, 520, 620)
atk("bangalash_swipe", "Rending Claws", "arc", 36, 3.2, 0.7, 0.2, 115, 190, angle=120)
atk(
    "bangalash_roar",
    "Terrifying Roar",
    "ring",
    20,
    5,
    1.2,
    1.2,
    365,
    650,
    slow=0.3,
    slow_duration=2,
)
atk(
    "rivendare_decay",
    "Death and Decay",
    "circle",
    16,
    6,
    1.4,
    5,
    190,
    700,
    effect="hostile_shadow",
    color=(192, 125, 236),
    pulse=1,
)
atk(
    "rivendare_bolts",
    "Baron Shadow Volley",
    "missile",
    25,
    4.8,
    1.1,
    0.2,
    10,
    700,
    300,
    9,
    100,
    effect="hostile_shadow",
    color=(192, 125, 236),
)
atk("rivendare_blade", "Runeblade Sweep", "arc", 45, 4.3, 1, 0.25, 170, 280, angle=165)
atk("rivendare_charge", "Deathknight Charge", "charge", 38, 5.5, 1.15, 1.2, 36, 550, 430)
atk(
    "lich_defile",
    "Defile",
    "circle",
    12,
    7,
    1.35,
    7,
    145,
    700,
    effect="hostile_shadow",
    color=(170, 132, 225),
    pulse=0.8,
    growth=18,
)
atk(
    "lich_winter",
    "Remorseless Winter",
    "ring",
    36,
    6,
    1.6,
    2,
    480,
    750,
    effect="hostile_frost",
    color=(130, 217, 248),
    slow=0.3,
    slow_duration=2.5,
)
atk(
    "lich_reaper",
    "Soul Reaper",
    "arc",
    48,
    4.5,
    1.2,
    0.3,
    190,
    280,
    angle=130,
    effect="hostile_frost",
    color=(130, 217, 248),
)
atk(
    "lich_volley",
    "Frostmourne Shards",
    "missile",
    24,
    4.5,
    1.1,
    0.2,
    12,
    730,
    310,
    5,
    85,
    effect="hostile_frost",
    color=(130, 217, 248),
    slow=0.2,
    slow_duration=2,
)
# Boss stats/tempo are deliberately distinct instead of copied Hogger entries.
for attack in attacks:
    attack.update(armor_penetration=0.5, health_damage=0.06)
# Regular creatures use the existing cheap, locked-warning primitives; boss health
# damage/armor penetration intentionally do not apply to ordinary attackers.
atk(
    "spirit_wail",
    "Spectral Wail",
    "ring",
    13,
    7.5,
    1.1,
    0.8,
    125,
    330,
    effect="hostile_shadow",
    color=(189, 146, 238),
)
atk("worgen_lunge", "Stalker Lunge", "charge", 20, 7, 0.95, 0.45, 19, 270, 330)
atk("gorilla_slam", "Knuckle Slam", "circle", 24, 8, 1.25, 0.2, 105, 210)
atk(
    "basilisk_gaze",
    "Crystalline Gaze",
    "missile",
    16,
    8,
    1.2,
    0.2,
    9,
    440,
    230,
    effect="hostile_poison",
    slow=0.2,
    slow_duration=1.5,
)
atk("gargoyle_dive", "Stonewing Dive", "leap", 23, 8, 1.15, 0.25, 65, 440)
atk(
    "plague_bile",
    "Bile Pool",
    "circle",
    12,
    9,
    1.3,
    3,
    85,
    350,
    effect="hostile_poison",
    color=(159, 213, 83),
    pulse=1,
)
atk("nerubian_rush", "Chitin Rush", "charge", 27, 8, 1.1, 0.65, 24, 340, 300)
atk(
    "revenant_shards",
    "Ice Shards",
    "missile",
    20,
    8,
    1.2,
    0.2,
    10,
    470,
    260,
    3,
    40,
    effect="hostile_frost",
    color=(130, 217, 248),
)
atk(
    "wyrm_breath",
    "Chilling Breath",
    "arc",
    24,
    8,
    1.2,
    0.3,
    120,
    260,
    effect="hostile_frost",
    color=(130, 217, 248),
    slow=0.15,
    slow_duration=1.5,
)
for bid, name, hp, damage, speed, radius, sequence, enrage, ecd, edamage in [
    (
        "stitches",
        "Stitches - Terror of Darkshire",
        420000,
        34,
        72,
        52,
        ["stitches_hook", "stitches_cleave", "stitches_vomit", "stitches_stomp"],
        0.4,
        0.82,
        1.2,
    ),
    (
        "bangalash",
        "King Bangalash - Lord of the Jungle",
        350000,
        31,
        154,
        36,
        ["bangalash_pounce", "bangalash_rush", "bangalash_swipe", "bangalash_roar"],
        0.6,
        0.68,
        1.15,
    ),
    (
        "rivendare",
        "Baron Rivendare - Scourge Deathknight",
        560000,
        39,
        118,
        40,
        ["rivendare_decay", "rivendare_bolts", "rivendare_blade", "rivendare_charge"],
        0.55,
        0.75,
        1.3,
    ),
    (
        "lich_king",
        "The Lich King - Lord of Icecrown",
        720000,
        44,
        90,
        46,
        ["lich_volley", "lich_reaper", "lich_defile", "lich_winter"],
        0.35,
        0.65,
        1.35,
    ),
]:
    bosses.append(
        dict(
            id=bid,
            name=name,
            sprite=bid,
            health=hp,
            damage=damage,
            speed=speed,
            radius=radius,
            xp=1800,
            class_xp=1400,
            gold=350,
            attacks=sequence,
            enrage=enrage,
            enrage_cooldown=ecd,
            enrage_damage=edamage,
        )
    )
for zi, (zid, name, description, difficulty, seed, boss_id, regulars) in enumerate(zone_specs):
    ids = []
    for i, (suffix, label, hp, speed, damage, xp, behavior, attack_ids) in enumerate(regulars):
        eid = zid + "_" + suffix
        ids.append(eid)
        enemies.append(
            dict(
                id=eid,
                name=label,
                health=hp,
                speed=speed,
                damage=damage,
                xp=xp,
                radius=(
                    [13, 13, 13, 17, 17, 13, 17, 13]
                    if zi == 0
                    else [13, 13, 13, 17, 17, 23, 18, 21]
                    if zi == 1
                    else [13, 13, 13, 17, 17, 13, 18, 25]
                    if zi == 2
                    else [13, 13, 13, 17, 17, 22, 18, 20]
                )[i],
                weight=1,
                color=[140, 180, 160],
                sprite=eid,
                behavior=behavior,
                attacks=attack_ids,
                min_time=[0, 0, 180, 300, 600, 240, 480, 720][i],
                max_time=1800,
                terrain="any",
                health_scaling=1,
                damage_scaling=1,
                xp_scaling=1,
                class_xp=2 + i // 2,
                gold_chance=0.12,
            )
        )
    elite_ids = []
    seq = next(b["attacks"] for b in bosses if b["id"] == boss_id)
    for j, (label, index) in enumerate(
        [
            (
                [
                    "Raven Hill Reaper",
                    "Gurubashi High Priest",
                    "Plague Commander",
                    "Frozen Warlord",
                ][zi],
                1,
            ),
            (
                [
                    "Black Widow Matriarch",
                    "Raptor Matriarch",
                    "Crypt Matriarch",
                    "Frost Geist Reaper",
                ][zi],
                [3, 0, 3, 0][zi],
            ),
            (
                ["Nightbane Alpha", "Ancient Silverback", "Furnace Abomination", "Nerubian Lord"][
                    zi
                ],
                [6, 5, 7, 5][zi],
            ),
        ]
    ):
        eid = zid + "_elite_" + str(j)
        elite_ids.append(eid)
        elites.append(
            dict(
                id=eid,
                name=label,
                enemy=ids[index],
                sprite=eid,
                health=24 + j * 8,
                damage=1.45,
                attacks=(
                    [seq[j], seq[j + 2]]
                    if j < 2
                    else [
                        ["worgen_lunge", "bangalash_roar"],
                        ["gorilla_slam", "pack_smash"],
                        ["plague_bile", "stitches_hook"],
                        ["nerubian_rush", "lich_volley"],
                    ][zi]
                ),
                class_xp=150 + zi * 50,
                gold=40 + zi * 15,
                xp=14,
                radius_scale=1.55,
            )
        )
    waves = []
    for minute in range(30):
        source = copy.deepcopy(base["waves"][minute])
        weights = {ids[0]: 12, ids[1]: 7}
        for i in range(2, len(ids)):
            if minute * 60 >= [0, 0, 180, 300, 600, 240, 480, 720][i]:
                weights[ids[i]] = [5, 3, 3, 6, 5, 4][i - 2]
        if minute >= 15:
            # New shapes become a substantial part of the late horde; retained
            # wolves and humanoids do not dominate all four themed rosters.
            weights.update({ids[i]: 7 for i in range(5, 8)})
            weights[ids[0]], weights[ids[1]], weights[ids[2]] = 8, 5, 4
        source.update(
            name=f"{name} {'Incursion' if minute < 10 else 'Siege' if minute < 25 else 'Last Stand'} {minute + 1}",
            weights=weights,
            health=source["health"] * (1 + 0.09 * (zi + 1)),
            damage=source["damage"] * (1 + 0.05 * (zi + 1)),
            xp=source["xp"] * (1 + 0.07 * (zi + 1)),
            rate=source["rate"] * (1 + 0.025 * (zi + 1)),
        )
        waves.append(source)
    zones.append(
        dict(
            id=zid,
            name=name,
            description=description,
            difficulty=difficulty,
            seed=seed,
            ground=zid + "_ground",
            road=zid + "_road",
            props=[zid + "_prop_" + str(i) for i in range(4)],
            enemies=ids,
            elites=elite_ids,
            boss_pool=[boss_id],
            waves=waves,
            music=zid,
            landmarks=[
                dict(
                    name=[
                        "Raven Hill Cemetery",
                        "Gurubashi Ruins",
                        "Light's Hope Chapel",
                        "Icecrown Citadel",
                    ][zi],
                    x=4500,
                    y=4050,
                    style=[2, 1, 1, 1][zi],
                    radius=55,
                ),
                dict(
                    name=[
                        "Darkshire Outpost",
                        "Nesingwary Camp",
                        "Corin's Crossing",
                        "The Frozen Gate",
                    ][zi],
                    x=3490,
                    y=4300,
                    style=[3, 0, 3, 3][zi],
                    radius=45,
                ),
                dict(
                    name=[
                        "Twilight Grove",
                        "Zul'Kunda Temple",
                        "The Noxious Glade",
                        "Sindragosa's Fall",
                    ][zi],
                    x=4400,
                    y=3240,
                    style=[0, 3, 2, 2][zi],
                    radius=40,
                ),
            ],
        )
    )
zones.insert(
    0,
    dict(
        id="elwynn",
        name="Elwynn Forest",
        description="Sunlit woods and familiar forest roads",
        difficulty=1,
        seed=41,
        ground="grass_0",
        road="road_0",
        props=["tree_0", "tree_1", "tree_2", "elwynn_inn", "elwynn_mill", "elwynn_bridge"],
        enemies=[e["id"] for e in core["enemies"]],
        elites=[e["id"] for e in base["elites"]],
        boss_pool=["hogger"],
        waves=base["waves"],
        music="elwynn",
        landmarks=[
            dict(name="Goldshire Inn", x=4520, y=4200, style=3, radius=55),
            dict(name="Eastvale Lumber Mill", x=3450, y=4500, style=4, radius=50),
            dict(name="Forest Crossing", x=4400, y=4160, style=5, radius=0),
        ],
    ),
)
annotate(enemies, bosses)
(DATA / "zones.json").write_text(
    json.dumps(
        dict(zones=zones, enemies=enemies, attacks=attacks, elites=elites, bosses=bosses), indent=2
    )
    + "\n",
    encoding="utf-8",
)
print(
    "Five zones, 150 wave rows, 32 expansion enemies, twelve expansion elites and four final bosses"
)
