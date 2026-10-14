"""Extend existing stable achievement IDs, shop gates and future class registry."""


def extend(data):
    achievements = data["achievements"]
    by_id = {a["id"]: a for a in achievements}
    for aid, name, metric, target in (
        ("unlock_rogue", "Defias Infiltrator", "faction:defias", 2500),
        ("unlock_druid", "Keeper of the Wild", "family:beast", 5000),
        ("unlock_shaman", "Elemental Calling", "elemental_kills", 2000),
    ):
        by_id[aid].update(
            name=name,
            metric=metric,
            target=target,
            description=f"Defeat {target:,} "
            + {
                "faction:defias": "Defias bandits across runs.",
                "family:beast": "beast enemies across runs.",
                "elemental_kills": "enemies with Fire, Frost or Nature damage.",
            }[metric],
        )
    by_id["boss_lich_king"].update(
        metric="boss_zone:icecrown:lich_king", description="Defeat the Lich King in Icecrown."
    )
    by_id["evolve_10"]["name"] = "Spell Master"
    additions = [
        (
            "kills_1000",
            "Skirmish Veteran",
            "kills",
            1000,
            120,
            "combat",
            "Defeat 1,000 enemies across runs.",
        ),
        (
            "kills_10000",
            "Horde Vanquisher",
            "kills",
            10000,
            350,
            "combat",
            "Defeat 10,000 enemies across runs.",
        ),
        (
            "kills_50000",
            "Endless Onslaught",
            "kills",
            50000,
            750,
            "combat",
            "Defeat 50,000 enemies across runs.",
        ),
        (
            "elites_100",
            "Elite Nemesis",
            "elites",
            100,
            600,
            "combat",
            "Defeat 100 elites across runs.",
        ),
        (
            "undead_2000",
            "Scourge Hunter",
            "family:undead",
            2000,
            250,
            "combat",
            "Defeat 2,000 undead enemies across runs.",
        ),
        (
            "battle_proven",
            "Battle Proven",
            "multiple",
            100,
            300,
            "combat",
            "Defeat 10,000 enemies and 25 elites across runs.",
        ),
        (
            "icecrown_survivor",
            "Frozen Wanderer",
            "zone_survival:icecrown",
            600,
            150,
            "exploration",
            "Survive ten minutes during an Icecrown run.",
        ),
        (
            "all_zones",
            "World Defender",
            "winning_zones",
            5,
            600,
            "exploration",
            "Win in all five implemented zones.",
        ),
        (
            "evolve_judgment",
            "Judgment Ascendant",
            "evolved:judgment",
            1,
            100,
            "builds",
            "Evolve Judgment in a run.",
        ),
        (
            "distinct_evolutions",
            "Versatile Spellcraft",
            "distinct_evolutions",
            10,
            350,
            "builds",
            "Evolve ten different automatic spells across runs.",
        ),
        (
            "full_arsenal",
            "Full Arsenal",
            "max_automatic_slots",
            8,
            150,
            "builds",
            "Equip eight automatic spells in one run.",
        ),
        (
            "max_spell",
            "Perfected Spell",
            "max_spell_rank",
            8,
            100,
            "builds",
            "Raise an automatic spell to Rank 8.",
        ),
        (
            "treasure_hunter",
            "Treasure Hunter",
            "chests_opened",
            25,
            200,
            "builds",
            "Open 25 elite treasure chests across runs.",
        ),
        (
            "more_choices",
            "More Choices",
            "best_run_level",
            40,
            0,
            "builds",
            "Reach level 40 during a run; unlock the Wisdom purchase.",
        ),
        (
            "level_25",
            "Class Veteran",
            "class_level",
            25,
            400,
            "mastery",
            "Reach permanent level 25 with a class.",
        ),
        (
            "master_of_arms",
            "Master of Arms",
            "winning_classes",
            6,
            500,
            "mastery",
            "Win with all six starting classes; unlock Banish Training.",
        ),
        (
            "unlock_monk",
            "Unbroken Journey",
            "no_heal_survival",
            1200,
            250,
            "survival",
            "Survive 20 minutes in one run before collecting any healing pickup.",
        ),
        (
            "unlock_demon_hunter",
            "Demon Slayer",
            "family:demon",
            1500,
            350,
            "combat",
            "Defeat 1,500 demon enemies across runs.",
        ),
        (
            "unlock_evoker",
            "Dragon Victor",
            "dragon_bosses",
            1,
            350,
            "exploration",
            "Defeat a dragon boss.",
        ),
        (
            "untouched_boss",
            "Untouched Champion",
            "untouched_bosses",
            1,
            250,
            "survival",
            "Defeat a boss without taking damage during its encounter.",
        ),
        (
            "no_manual_win",
            "Automatic Victory",
            "no_manual_wins",
            1,
            250,
            "survival",
            "Win without activating a manual ability.",
        ),
    ]
    for aid, name, metric, target, gold, category, description in additions:
        achievements.append(
            dict(
                id=aid,
                name=name,
                metric=metric,
                target=target,
                gold=gold,
                category=category,
                description=description,
                class_id="",
            )
        )
    for cls in data["classes"][:6]:
        achievements.append(
            dict(
                id="win_" + cls["id"],
                name=cls["name"] + " Champion",
                metric="class_win:" + cls["id"],
                target=1,
                gold=150,
                category="mastery",
                description="Win a complete run with " + cls["name"] + ".",
                class_id=cls["id"],
            )
        )
    future = [
        ("rogue", "Rogue", "unlock_rogue", "Defeat 2,500 Defias bandits", "shadowburn"),
        (
            "death_knight",
            "Death Knight",
            "boss_lich_king",
            "Defeat the Lich King in Icecrown",
            "ice_lance",
        ),
        ("druid", "Druid", "unlock_druid", "Defeat 5,000 beast enemies", "beast_companion"),
        (
            "shaman",
            "Shaman",
            "unlock_shaman",
            "Defeat 2,000 enemies with Fire, Frost or Nature",
            "thunder_clap",
        ),
        (
            "monk",
            "Monk",
            "unlock_monk",
            "Survive 20 minutes without a healing pickup",
            "desperate_prayer",
        ),
        (
            "demon_hunter",
            "Demon Hunter",
            "unlock_demon_hunter",
            "Defeat 1,500 demon enemies",
            "chaos_bolt",
        ),
        ("evoker", "Evoker", "unlock_evoker", "Defeat a dragon boss", "fireball"),
    ]
    data["classes"] = [c for c in data["classes"] if c["playable"]] + [
        dict(
            id=cid,
            name=name,
            playable=False,
            achievement=aid,
            description=description,
            icon="effect:" + icon,
        )
        for cid, name, aid, description, icon in future
    ]
    data["shared"].extend(
        [
            dict(
                id="treasure",
                name="Treasure Training",
                description="Each opened elite chest awards +5 run gold per rank",
                max_rank=3,
                costs=[300, 600, 900],
                requires_ranks=0,
                effects={"chest_gold": 5},
                achievement="treasure_hunter",
            ),
            dict(
                id="reroll_mastery",
                name="Spellmaster's Insight",
                description="One additional reroll per run",
                max_rank=1,
                costs=[600],
                requires_ranks=0,
                effects={"rerolls": 1},
                achievement="evolve_10",
            ),
            dict(
                id="banish",
                name="Banish Training",
                description="Banish one selected normal upgrade from a run (B / Y)",
                max_rank=1,
                costs=[800],
                requires_ranks=0,
                effects={"banishes": 1},
                achievement="master_of_arms",
            ),
        ]
    )
    next(u for u in data["shared"] if u["id"] == "choices")["achievement"] = "more_choices"
    reward_ids = {aid: [("class", cid)] for cid, _, aid, _, _ in future}
    for aid, sid in (
        ("more_choices", "choices"),
        ("treasure_hunter", "treasure"),
        ("evolve_10", "reroll_mastery"),
        ("master_of_arms", "banish"),
    ):
        reward_ids.setdefault(aid, []).append(("shop", sid))
    for a in achievements:
        metric = a["metric"]
        category = a.get("category") or (
            "mastery"
            if metric in {"class_level", "winning_classes"}
            else "exploration"
            if metric == "hogger" or metric.startswith("boss")
            else "builds"
            if metric == "evolved"
            else "survival"
            if metric == "best_time"
            else "combat"
        )
        a["category"] = category
        a["conditions"] = (
            [{"metric": metric, "target": a["target"]}]
            if metric != "multiple"
            else [{"metric": "kills", "target": 10000}, {"metric": "elites", "target": 25}]
        )
        a["icon"] = (
            "actor:" + a["class_id"]
            if a["class_id"]
            else "effect:"
            + {
                "combat": "cleave",
                "exploration": "eye_of_tyr",
                "builds": "arcane_missiles",
                "mastery": "judgment",
                "survival": "power_word_shield",
            }[category]
        )
        a["rewards"] = ([dict(kind="gold", value=a["gold"], target="")] if a["gold"] else []) + [
            dict(kind=kind, target=target, value=1) for kind, target in reward_ids.get(a["id"], [])
        ]
        a["prerequisites"] = ["kills_10000"] if a["id"] == "kills_50000" else []
        a["available"] = a["id"] not in {"unlock_demon_hunter", "unlock_evoker"}
        a["availability_reason"] = {
            "unlock_demon_hunter": "No hostile demon enemies are implemented yet.",
            "unlock_evoker": "No dragon boss is implemented yet.",
        }.get(a["id"], "")
    assert len(achievements) == 60 and len({a["id"] for a in achievements}) == 60, (
        f"Unexpected achievement count: {len(achievements)}, {len(set(a['id'] for a in achievements))} unique"
    )
    return data
