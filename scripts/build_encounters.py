"""Author the Elwynn enemy, wave, elite and boss catalog; offline only."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/warcraft_survivors/data"
content = json.loads((DATA / "content.json").read_text(encoding="utf-8"))


def enemy(
    aid,
    name,
    hp,
    speed,
    damage,
    xp,
    radius,
    behavior="chase",
    start=0,
    terrain="any",
    attacks=(),
    class_xp=1,
    color=(151, 112, 80),
    health_scaling=1,
):
    return dict(
        id=aid,
        name=name,
        health=hp,
        speed=speed,
        damage=damage,
        xp=xp,
        radius=radius,
        weight=6 if aid == "kobold" else 2,
        color=list(color),
        behavior=behavior,
        sprite=aid,
        attacks=list(attacks),
        min_time=start,
        max_time=1800,
        terrain=terrain,
        health_scaling=health_scaling,
        damage_scaling=1,
        xp_scaling=1,
        class_xp=class_xp,
        gold_chance=0.1,
    )


content["enemies"] = [
    enemy("kobold", "Kobold Miner", 32, 84, 10, 6, 13),
    enemy("wolf", "Forest Wolf", 30, 132, 10, 6, 12),
    enemy("bandit", "Defias Bandit", 55, 86, 14, 10, 15, start=120, terrain="road", class_xp=2),
    enemy(
        "kobold_geomancer",
        "Kobold Geomancer",
        42,
        72,
        10,
        8,
        13,
        "ranged",
        300,
        "any",
        ("stone_bolt",),
        2,
        (172, 133, 69),
    ),
    enemy(
        "defias_cutpurse", "Defias Cutpurse", 38, 145, 10, 8, 13, "flank", 240, "road", class_xp=2
    ),
    enemy(
        "defias_marksman",
        "Defias Marksman",
        48,
        84,
        13,
        10,
        14,
        "ranged",
        480,
        "road",
        ("arrow",),
        2,
    ),
    enemy(
        "gnoll",
        "Riverpaw Gnoll",
        88,
        90,
        17,
        14,
        17,
        "bruiser",
        420,
        "any",
        ("gnoll_smash",),
        3,
        (171, 128, 76),
    ),
    enemy(
        "gnoll_shaman",
        "Riverpaw Shaman",
        80,
        82,
        12,
        16,
        16,
        "ranged",
        720,
        "any",
        ("lightning",),
        3,
        (151, 133, 112),
    ),
    enemy(
        "spider",
        "Forest Spider",
        30,
        110,
        8,
        6,
        12,
        "ranged",
        180,
        "forest",
        ("poison_spit",),
        1,
        (84, 142, 65),
    ),
    enemy(
        "forest_boar",
        "Feral Boar",
        68,
        96,
        13,
        10,
        16,
        "charge",
        360,
        "forest",
        ("boar_charge",),
        2,
        (143, 89, 62),
    ),
    enemy(
        "forest_bear",
        "Enraged Bear",
        140,
        72,
        24,
        20,
        20,
        "bruiser",
        900,
        "forest",
        ("bear_swipe",),
        4,
        (110, 82, 61),
    ),
]


def attack(
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
    color=(255, 124, 68),
):
    return dict(
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
    )


attacks = [
    attack(
        "stone_bolt",
        "Stone Bolt",
        "missile",
        10,
        3.8,
        0.55,
        0.12,
        8,
        340,
        220,
        effect="hostile_stone",
    ),
    attack("arrow", "Aimed Arrow", "missile", 12, 3.5, 0.6, 0.12, 6, 380, 320),
    attack(
        "lightning",
        "Lightning Volley",
        "missile",
        12,
        4,
        0.65,
        0.15,
        8,
        380,
        230,
        3,
        25,
        "hostile_lightning",
    ),
    attack(
        "poison_spit",
        "Poison Spit",
        "missile",
        8,
        4.5,
        0.65,
        0.12,
        8,
        260,
        210,
        effect="hostile_poison",
        color=(163, 234, 94),
    ),
    attack("gnoll_smash", "Club Smash", "circle", 18, 4.5, 0.8, 0.15, 75, 125),
    attack("bear_swipe", "Bear Sweep", "arc", 24, 5, 1, 0.15, 100, 150, angle=160),
    attack("boar_charge", "Boar Charge", "charge", 16, 7, 0.85, 0.7, 23, 230, 330),
    attack("captain_volley", "Captain Volley", "missile", 20, 4, 0.85, 0.2, 9, 500, 280, 5, 65),
    attack(
        "captain_bomb",
        "Defias Powder Bomb",
        "circle",
        28,
        5,
        1.3,
        0.2,
        110,
        550,
        effect="hostile_stone",
    ),
    attack("pack_charge", "Packlord Charge", "charge", 26, 5, 1, 0.85, 34, 400, 460),
    attack("pack_smash", "Packlord Smash", "ring", 24, 5, 1.1, 0.8, 185, 350),
    attack(
        "web_trap",
        "Broodmother Venom",
        "circle",
        23,
        4.5,
        1.1,
        0.25,
        125,
        550,
        color=(163, 234, 94),
    ),
    attack(
        "venom_volley",
        "Venom Volley",
        "missile",
        16,
        4,
        0.85,
        0.2,
        10,
        500,
        230,
        7,
        95,
        "hostile_poison",
        (163, 234, 94),
    ),
    attack("hogger_cleave", "Brutal Cleave", "arc", 36, 3.8, 0.95, 0.2, 155, 280, angle=130),
    attack("hogger_charge", "Savage Charge", "charge", 32, 5, 1.1, 1, 38, 550, 520),
    attack("hogger_leap", "Crushing Leap", "leap", 42, 5.5, 1.35, 0.25, 130, 850),
    attack("hogger_quake", "Earthshaker", "ring", 28, 5.5, 1.2, 1.05, 270, 600),
]
elites = [
    dict(
        id="defias_captain",
        name="Defias Captain",
        enemy="bandit",
        sprite="defias_captain",
        health=18,
        damage=1.5,
        attacks=["captain_volley", "captain_bomb"],
        class_xp=100,
        gold=25,
    ),
    dict(
        id="gnoll_packlord",
        name="Riverpaw Packlord",
        enemy="gnoll",
        sprite="gnoll_packlord",
        health=18,
        damage=1.4,
        attacks=["pack_charge", "pack_smash"],
        class_xp=125,
        gold=35,
    ),
    dict(
        id="broodmother",
        name="Forest Broodmother",
        enemy="spider",
        sprite="broodmother",
        health=30,
        damage=1.5,
        attacks=["web_trap", "venom_volley"],
        class_xp=150,
        gold=45,
    ),
]
bosses = [
    dict(
        id="hogger",
        name="Hogger - Scourge of Elwynn",
        sprite="hogger",
        health=450000,
        damage=30,
        speed=105,
        radius=42,
        xp=1200,
        class_xp=1000,
        gold=250,
        attacks=["hogger_cleave", "hogger_charge", "hogger_leap", "hogger_quake"],
        enrage=0.5,
        enrage_cooldown=0.72,
        enrage_damage=1.25,
    )
]
for elite in elites:
    elite.update(xp=12, radius_scale=1.55)
for a in attacks:
    if a["id"].startswith("hogger_"):
        a.update(armor_penetration=0.5, health_damage=0.06)
waves = []
for minute in range(30):
    if minute < 5:
        rates = [1.2, 1.5, 1.8, 2.3, 2.8]
        rate = rates[minute]
        batch = 1 if minute < 3 else 2
        density = 75 + minute * 40
        label = "Forest Patrol"
    elif minute < 15:
        rate = 2.8 + (minute - 5) * 0.65
        batch = 3 + (minute - 5) // 4
        density = 240 + (minute - 5) * 85
        label = "Riverpaw Incursion" if minute < 10 else "Defias Reinforcements"
    elif minute < 25:
        rate = 10 + (minute - 15) * 1.05
        batch = 6
        density = 1300 + (minute - 15) * 165
        label = "Forest Under Siege"
    else:
        rate = 21 + (minute - 25) * 1.6
        batch = 8
        density = 3200 + (minute - 25) * 350
        label = "Last Stand of Elwynn"
    weights = {"kobold": 8 if minute < 5 else 6, "wolf": 2 if minute < 5 else 4}
    for e in content["enemies"]:
        if e["id"] in weights or e["min_time"] > minute * 60:
            continue
        weights[e["id"]] = 1 if e["behavior"] == "ranged" else 2
    if minute >= 20:
        weights.update(kobold=12, wolf=8, bandit=7, gnoll=5, forest_bear=3)
    waves.append(
        dict(
            start=minute * 60,
            name=f"{label} {minute + 1}",
            rate=round(rate, 2),
            batch=batch,
            density=density,
            health=round(1 + minute * 0.12 + (max(0, minute - 10) ** 1.3) * 0.055, 3),
            damage=round(1 + minute * 0.018, 3),
            xp=round(1 + minute * 0.075, 3),
            speed=min(35, minute * 1.1),
            weights=weights,
            surge=0
            if minute < 8
            else 35 + (minute - 8) * 9
            if minute < 15
            else 100 + (minute - 15) * 18
            if minute < 25
            else 350 + (minute - 25) * 100,
        )
    )
(DATA / "content.json").write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
(DATA / "encounters.json").write_text(
    json.dumps(
        dict(waves=waves, attacks=attacks, elites=elites, bosses=bosses, boss_pool=["hogger"]),
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print("Authored 11 regular enemies, 30 waves, 3 elites, 17 hostile attacks and Hogger")
