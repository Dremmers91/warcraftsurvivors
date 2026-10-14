"""Authoritative facts, catalog gates, replay safety and progression compatibility."""

import copy
from dataclasses import replace
from datetime import datetime

import pytest
from pygame import Vector2

from warcraft_survivors.achievements import complete, progress, state
from warcraft_survivors.combat import damage_enemy, hurt_player
from warcraft_survivors.entities import ManualState, SpellState
from warcraft_survivors.meta import load_progression
from warcraft_survivors.persistence import SaveStore
from warcraft_survivors.run_events import RunLedger
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.upgrades import eligible

META = load_progression()


def summary(content, **facts):
    sim = Simulation(content)
    return replace(sim.ledger.summary(sim), **facts)


def settle(save, facts, *, cid="paladin", seconds=0, won=False, kills=0, evolved=0, boss="hogger"):
    return save.reward_run(cid, kills, 0, seconds, won, 0, evolved, 0, boss_id=boss, summary=facts)


def test_catalog_preserves_every_prior_id_and_has_real_nonduplicate_requirements():
    old_ids = set(
        "first_blood centurion survivor elite evolution victory kills_500 kills_5000 kills_25000 elites_10 elites_25 survive_10 survive_20 survive_30 hogger_5 evolve_10 level_5 level_15 level_30 wins_2 unlock_rogue unlock_druid unlock_shaman level_paladin level_warrior level_mage level_hunter level_warlock level_priest boss_stitches boss_bangalash boss_rivendare boss_lich_king".split()
    )
    assert len(old_ids) == 33 and old_ids <= set(META.achievements)
    assert len(META.achievements) == 60
    requirements = [(a.class_id, a.conditions) for a in META.achievements.values()]
    assert len(requirements) == len(set(requirements))
    assert {a.category for a in META.achievements.values()} == {
        "combat",
        "exploration",
        "builds",
        "mastery",
        "survival",
    }


@pytest.mark.parametrize(
    "cid,aid,delivery",
    [
        ("paladin", "judgment", "spell"),
        ("hunter", "beast_companion", "companion"),
        ("warlock", "summon_felguard", "companion"),
        ("hunter", "stampede", "temporary_summon"),
        ("warlock", "hand_of_gul_dan", "temporary_summon"),
        ("hunter", "beast_companion_evolved", "companion"),
        ("warlock", "summon_felguard_evolved", "companion"),
    ],
)
def test_real_attack_paths_emit_one_owned_classified_death(content, tmp_path, cid, aid, delivery):
    sim = Simulation(content, cid)
    sim.player.spells = {aid: SpellState(8)}
    enemy = sim.spawn("bandit", sim.player.pos + Vector2(50, 0))
    enemy.health = 1
    sim.grid.rebuild(sim.enemies)
    ability = content.ability(aid)
    sim.combat.cast(ability, sim.player.spells[aid])
    for _ in range(120):
        sim.combat.update_companions(FIXED_DT)
        sim.combat.update_projectiles(FIXED_DT)
    assert enemy.health == 0
    sim.collect_dead()
    event = sim.ledger.last_event
    assert event and event.source == aid and event.delivery == delivery
    assert event.owner == "player" and event.school == ability.school
    assert event.family == "humanoid" and event.faction == "defias" and event.zone == "elwynn"
    assert not event.elite and not event.boss and event.event_id.endswith(f":{enemy.id}")
    sim.enemies.append(enemy)  # A delayed callback cannot bank this death twice.
    sim.collect_dead()
    assert sim.kills == 1 and sim.ledger.faction_kills == {"defias": 1}
    assert not sim.ledger.record(event)
    assert not RunLedger().record(event)
    save = SaveStore(tmp_path / "save.json")
    settle(save, sim.ledger.summary(sim), cid=cid, kills=sim.kills)
    assert SaveStore(save.path).data["stats"]["source_kills"][aid] == 1


@pytest.mark.parametrize("aid", ["corruption", "immolate", "serpent_sting", "corruption_evolved"])
def test_dot_final_tick_records_source_and_school(content, aid):
    sim = Simulation(content, "warlock")
    enemy = sim.spawn("wolf", sim.player.pos + Vector2(30, 0))
    enemy.health = 1
    sim.grid.rebuild(sim.enemies)
    ability = content.ability(aid)
    sim.combat.mark(enemy, ability, 10, 3)
    sim.combat.update_statuses(FIXED_DT)
    sim.collect_dead()
    event = sim.ledger.last_event
    assert event and event.delivery == "dot" and event.source == aid
    assert event.school == ability.school and event.owner == "player"
    assert sim.ledger.family_kills == {"beast": 1}


def test_nonplayer_deaths_do_not_bank_player_rewards_or_achievement_counts(content):
    sim = Simulation(content)
    enemy = sim.spawn("bandit", sim.player.pos)
    damage_enemy(enemy, 999, owner="environment", source="test")
    sim.collect_dead()
    assert sim.kills == 0 and sim.gold == 0 and not sim.pickups
    assert not sim.ledger.family_kills


@pytest.mark.parametrize(
    "cid,aid,field,key,target",
    [
        ("rogue", "unlock_rogue", "faction_kills", "defias", 2500),
        ("druid", "unlock_druid", "family_kills", "beast", 5000),
        ("shaman", "unlock_shaman", "damage_kills", "fire", 2000),
    ],
)
def test_cumulative_class_unlock_boundaries_and_restart(
    content, tmp_path, cid, aid, field, key, target
):
    save = SaveStore(tmp_path / "save.json")
    settle(save, summary(content, **{field: {key: target - 1}}), kills=target - 1)
    loaded = SaveStore(save.path)
    assert loaded.data["achievement_progress"][aid] == target - 1
    assert cid not in loaded.data["unlocked_classes"]
    result = settle(loaded, summary(content, **{field: {key: 1}}), kills=1)
    assert aid in result["achievements"] and cid in result["unlocks"]
    assert not loaded.class_available(cid) and not loaded.buy_talent(cid, "might")
    assert loaded.data["stats"]["kills"] == target
    assert (
        datetime.fromisoformat(loaded.data["achievement_completed_at"][aid]).utcoffset() is not None
    )
    before = copy.deepcopy(loaded.data)
    loaded.write()
    assert SaveStore(save.path).data["gold"] == before["gold"]


def test_elemental_requirement_combines_only_fire_frost_and_nature(content, tmp_path):
    save = SaveStore(tmp_path / "save.json")
    settle(
        save,
        summary(content, damage_kills={"fire": 600, "frost": 700, "nature": 699, "shadow": 10000}),
    )
    assert save.data["achievement_progress"]["unlock_shaman"] == 1999
    settle(save, summary(content, damage_kills={"nature": 1}))
    assert "shaman" in save.data["unlocked_classes"]


def test_exact_boss_zone_unlock_and_every_zone_win(content, tmp_path):
    save = SaveStore(tmp_path / "save.json")
    settle(
        save,
        summary(content, boss_zone_kills={"elwynn:lich_king": 1}),
        seconds=1800,
        won=True,
        boss="lich_king",
    )
    assert "death_knight" not in save.data["unlocked_classes"]
    for zid, zone in content.zones.items():
        boss = zone.boss_pool[0]
        result = settle(
            save,
            summary(content, zone=zid, boss_zone_kills={f"{zid}:{boss}": 1}),
            seconds=1800,
            won=True,
            boss=boss,
        )
    assert "all_zones" in result["achievements"]
    assert "death_knight" in save.data["unlocked_classes"]
    assert not save.class_available("death_knight")


@pytest.mark.parametrize("heal_at,expected", [(None, True), (1199, False), (1200, True)])
def test_single_run_monk_challenge_tracks_pickups_without_accumulating_runs(
    content, tmp_path, heal_at, expected
):
    save = SaveStore(tmp_path / "save.json")
    for _ in range(2):
        settle(save, summary(content, no_heal_survival=600), seconds=600)
    assert "monk" not in save.data["unlocked_classes"]
    sim = Simulation(content)
    if heal_at is not None:
        sim.time = heal_at
        sim.drop(sim.player.pos, "heal", 10)
        sim.collect_pickups(FIXED_DT)
        assert sim.ledger.healing_pickups == 1
    sim.time = 1200
    sim.finish("death")
    settle(save, sim.ledger.summary(sim), seconds=sim.elapsed)
    assert ("monk" in SaveStore(save.path).data["unlocked_classes"]) == expected


def test_healing_cards_and_manuals_are_distinct_from_healing_pickups(content):
    sim = Simulation(content)
    sim.player.manual = ManualState("lay_on_hands")
    assert sim.activate_manual()
    sim.time = 1200
    assert sim.ledger.summary(sim).no_heal_survival == 1200
    assert sim.ledger.manual_uses == 1


@pytest.mark.parametrize("take_hit,shield", [(False, False), (True, False), (True, True)])
def test_boss_damage_challenge_includes_absorbed_hits(content, take_hit, shield):
    sim = Simulation(content)
    sim.time = 1800
    boss = sim.spawn_boss()
    assert boss
    if shield:
        sim.player.shield = 100
    if take_hit:
        assert hurt_player(sim.player, 20)
    damage_enemy(boss, 10**6, source="judgment")
    sim.collect_dead()
    assert sim.ledger.untouched_bosses == int(not take_hit)
    assert sim.ledger.last_event.boss == "hogger"


def test_unavailable_encounters_never_grant_unfinished_classes(content, tmp_path):
    assert not any(e.family == "demon" for e in content.enemies.values())
    assert not any(b.family == "dragon" for b in content.bosses.values())
    save = SaveStore(tmp_path / "save.json")
    settle(save, summary(content, family_kills={"demon": 1500}, dragon_bosses=1))
    for cid in ("demon_hunter", "evoker"):
        a = META.achievements[META.classes[cid].achievement]
        assert state(save.data, a) == "unavailable"
        assert cid not in save.data["unlocked_classes"] and not save.class_available(cid)


def test_multiple_conditions_prerequisites_and_reward_gold_once(tmp_path):
    save = SaveStore(tmp_path / "save.json")
    save.data["stats"].update(kills=50000, elites=24)
    a = META.achievements["battle_proven"]
    assert progress(save.data, a) == 96
    assert state(save.data, META.achievements["kills_50000"]) == "locked"
    fresh, gold = complete(save.data)
    assert "kills_50000" in fresh and "battle_proven" not in fresh
    assert gold == sum(META.achievements[aid].gold for aid in fresh)
    assert complete(save.data) == ([], 0)
    save.data["stats"]["elites"] = 25
    assert complete(save.data)[0] == ["elites_25", "battle_proven"]


def test_settlement_replay_survives_restart_and_failed_save(content, tmp_path, monkeypatch):
    save = SaveStore(tmp_path / "save.json")
    facts = summary(content, family_kills={"beast": 5000})
    monkeypatch.setattr(save, "write", lambda: False)
    first = settle(save, facts, kills=5000)
    before = copy.deepcopy(save.data)
    assert first["gold"] > 0 and not first["saved"]
    assert settle(save, facts, kills=5000)["duplicate"] and save.data == before
    monkeypatch.undo()
    assert save.write()
    loaded = SaveStore(save.path)
    repeated = settle(loaded, facts, kills=5000)
    assert repeated["duplicate"] and repeated["gold"] == 0 and not repeated["achievements"]
    assert loaded.data["stats"]["runs"] == 1 and loaded.data["gold"] == first["gold"]


@pytest.mark.parametrize(
    "facts",
    [
        {"zone": "missing"},
        {"chests_opened": -1},
        {"family_kills": {"beast": True}},
        {"evolved_spells": ("missing",)},
    ],
)
def test_invalid_summary_cannot_partially_mutate_profile(content, tmp_path, facts):
    save = SaveStore(tmp_path / "save.json")
    before = copy.deepcopy(save.data)
    with pytest.raises(ValueError):
        settle(save, summary(content, **facts), kills=10)
    assert save.data == before and not save.path.exists()


def test_legacy_v2_rewards_unlocks_and_purchases_survive_respec(tmp_path):
    raw = SaveStore.defaults()
    for key in ("achievement_completed_at", "settled_runs"):
        raw.pop(key)
    raw["achievements"] = ["unlock_rogue", "unlock_druid", "unlock_shaman", "boss_lich_king"]
    raw["shared"] = {"choices": 1, "rerolls": 3}
    raw["classes"]["paladin"].update(xp=120, talents={"might": 1})
    raw["gold"] = 55
    save = SaveStore(tmp_path / "save.json")
    save.data = SaveStore.validate(raw)
    assert {"rogue", "druid", "shaman", "death_knight"} <= set(save.data["unlocked_classes"])
    assert all(v is None for v in save.data["achievement_completed_at"].values())
    assert save.respec("paladin")
    loaded = SaveStore(save.path)
    assert loaded.data["shared"] == {"choices": 1, "rerolls": 3}
    assert loaded.data["achievements"] == raw["achievements"]
    assert loaded.data["classes"]["paladin"]["xp"] == 120


def test_actual_build_chest_and_purchase_effects(content, tmp_path):
    save = SaveStore(tmp_path / "save.json")
    save.data["gold"] = 100000
    save.data["shared"] = {"health": 5, "might": 3}
    for sid in ("choices", "treasure", "reroll_mastery", "banish"):
        assert "achievement" in save.shared_reason(sid)
        assert not save.buy_shared(sid)
    sim = Simulation(content)
    sim.player.level = 40
    sim.player.spells = {aid: SpellState(8) for aid in content.classes["paladin"].abilities[:8]}
    sim.player.passives[content.abilities["judgment"].evolution.passive] = 1
    sim.pending_chests = 25
    sim.level_check()
    assert sim.ledger.chests_opened == 1
    sim.choose(next(i for i, c in enumerate(sim.choices) if c.kind == "evolution"))
    for _ in range(24):
        sim.choose(0)
    assert sim.ledger.chests_opened == 25
    settle(save, sim.ledger.summary(sim), evolved=1)
    for aid in ("more_choices", "treasure_hunter", "full_arsenal", "max_spell", "evolve_judgment"):
        assert aid in save.data["achievements"]
    assert save.buy_shared("choices") and save.buy_shared("treasure")
    for i, cid in enumerate(META.trees):
        settle(save, summary(content), cid=cid, seconds=1800, won=True, evolved=9 if i == 0 else 0)
    assert save.buy_shared("reroll_mastery") and save.buy_shared("banish")
    new = Simulation(content, permanent=save.loadout("paladin"))
    assert new.rerolls == 1 and new.banishes == 1
    new.player.xp = new.player.xp_required
    new.level_check()
    assert len(new.choices) == 4
    banned = new.choices[0]
    assert new.banish(0) and not new.banish(0)
    assert (banned.kind, banned.id) not in {
        (c.kind, c.id) for c in eligible(content, "paladin", new.player)
    }
    new.choose(0)
    gold = new.gold
    new.pending_chests = 1
    new.level_check()
    assert new.gold == gold + 5 and len(new.choices) == 3
    assert not new.banish(0) and not new.reroll()


def test_distinct_spell_evolutions_do_not_count_same_spell_twice(content, tmp_path):
    save = SaveStore(tmp_path / "save.json")
    bases = tuple(aid for aid, a in content.abilities.items() if a.evolution)[:10]
    settle(save, summary(content, evolved_spells=bases[:5]), evolved=5)
    settle(save, summary(content, evolved_spells=bases[:5]), evolved=5)
    assert (
        "evolve_10" in save.data["achievements"]
        and "distinct_evolutions" not in save.data["achievements"]
    )
    settle(save, summary(content, evolved_spells=bases[5:]), evolved=5)
    assert "distinct_evolutions" in SaveStore(save.path).data["achievements"]
