"""Schedule, actual hostile attacks, boss outcomes and exact permanent reward contracts."""

from __future__ import annotations

import random
from dataclasses import replace

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.debug import DebugTools, parse_run_time
from warcraft_survivors.entities import HostileProjectile, SpellState
from warcraft_survivors.persistence import SaveStore
from warcraft_survivors.rewards import calculate_rewards
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.spawning import ENEMY_LIMIT
from warcraft_survivors.upgrades import roll
from warcraft_survivors.waves import ELITE_TIMES, RUN_SECONDS, WaveDirector


@pytest.mark.parametrize("minute", range(30))
def test_wave_boundary_and_catalog_restrictions(content, minute):
    d = WaveDirector(content)
    assert d.wave(minute * 60).start == minute * 60
    assert d.wave(minute * 60 + 59.999).start == minute * 60
    if minute:
        assert d.wave(minute * 60 - 0.001).start == (minute - 1) * 60
    wave = d.wave(minute * 60)
    sim = Simulation(content)
    kinds, weights = sim.spawner.pool(minute * 60)
    assert kinds and len(kinds) == len(weights)
    assert all(
        content.enemies[k].min_time <= minute * 60 <= content.enemies[k].max_time for k in kinds
    )
    assert wave.rate > 0 and wave.density > 0


def test_composition_density_scaling_and_more_than_900_enemies(content):
    early, middle, late = content.waves[0], content.waves[14], content.waves[29]
    assert early.rate < middle.rate < late.rate
    assert early.density < middle.density < late.density
    assert early.health < middle.health < late.health and early.xp < middle.xp < late.xp
    assert set(early.weights) < set(middle.weights) <= set(late.weights)
    assert late.density >= 4000 and ENEMY_LIMIT >= late.density
    sim = Simulation(content)
    for _ in range(2400):
        sim.spawner.update(0.05, 1740, sim.camera.pos, sim.player.pos, sim.enemies)
    assert len(sim.enemies) > 3000
    late_enemy = sim.spawner.create(
        1740, sim.camera.pos, sim.player.pos, "kobold", sim.player.pos + Vector2(60, 0)
    )
    assert (
        late_enemy.xp > content.enemies["kobold"].xp
        and late_enemy.health > content.enemies["kobold"].health
    )
    assert late_enemy.class_xp == content.enemies["kobold"].class_xp


def test_elite_schedule_is_idempotent_handles_overlap_and_excludes_final_boss(content):
    d = WaveDirector(content)
    for t in ELITE_TIMES:
        assert d.due_elites(t) == [t]
        assert not d.due_elites(t + 0.05)
    assert not d.due_elites(1800) and not d.due_elites(1900)
    sim = Simulation(content)
    sim.time = 299.99
    sim.step(FIXED_DT)
    assert len([e for e in sim.enemies if e.elite]) == 1
    first = next(e for e in sim.enemies if e.elite)
    sim.time = 599.99
    sim.step(FIXED_DT)
    assert first in sim.enemies and len([e for e in sim.enemies if e.elite]) == 2
    assert not sim.director.boss_spawned


@pytest.mark.parametrize("elite_id", ("defias_captain", "gnoll_packlord", "broodmother"))
def test_elites_have_distinct_attacks_rewards_and_usable_evolution_chests(content, elite_id):
    sim = Simulation(content)
    sim.player.spells = {"judgment": SpellState(8)}
    sim.player.passives = {"projectiles": 1}
    e = sim.spawn_elite(elite_id)
    assert e.elite_id == elite_id and e.sprite == content.elites[elite_id].sprite
    assert e.class_xp >= 100 and e.gold_reward > 0 and e.health > content.enemies[e.kind].health
    sim.enemy_combat.begin(e, content.elites[elite_id].attacks[0])
    assert sim.enemy_combat.attacks[0].warning > 0
    e.pos.update(sim.player.pos)
    e.health = 0
    sim.collect_dead()
    assert sim.elites == 1 and sim.class_xp_kills >= 100 and sim.gold == e.gold_reward
    assert any(p.kind == "chest" for p in sim.pickups.values())
    sim.collect_pickups(FIXED_DT)
    assert sim.chest_choice and len(sim.choices) == 3
    sim.choose(next(i for i, c in enumerate(sim.choices) if c.kind == "evolution"))
    assert "judgment_evolved" in sim.player.spells
    old = (sim.kills, sim.elites, sim.gold, sim.class_xp_kills)
    sim.collect_dead()
    assert old == (sim.kills, sim.elites, sim.gold, sim.class_xp_kills)


def test_qualified_chests_always_offer_at_least_one_evolution(content):
    p = Simulation(content).player
    p.spells = {"judgment": SpellState(8)}
    p.passives = {"projectiles": 1}
    for seed in range(100):
        cards = roll(content, "paladin", p, random.Random(seed), chest=True)
        assert any(c.kind == "evolution" for c in cards)
        assert len({(c.kind, c.id) for c in cards}) == 3


def test_boss_spawns_once_at_30_minutes_timer_freezes_but_encounter_continues(content):
    sim = Simulation(content)
    assert sim.spawn_boss() is None
    sim.time = 1799.99
    sim.player.invulnerable = True
    sim.step(FIXED_DT)
    boss = sim.boss
    assert boss and boss.boss_id == "hogger" and not sim.finished and sim.time == 1800
    for _ in range(60):
        sim.step(FIXED_DT)
    assert sim.boss is boss and len([e for e in sim.enemies if e.boss_id]) == 1
    assert sim.time == 1800 and sim.boss_time >= 0.99 and sim.elapsed > 1800
    assert sim.boss_result == "alive" and not sim.won and not sim.elites


def test_victory_requires_boss_death_and_alive_player(content):
    sim = Simulation(content)
    sim.time = RUN_SECONDS
    boss = sim.spawn_boss()
    assert boss
    sim.step(FIXED_DT)
    assert not sim.finished and not sim.won
    boss.health = 0
    sim.collect_dead()
    sim.step(FIXED_DT)
    assert sim.finished and sim.won and sim.outcome == "victory" and sim.boss_result == "defeated"
    assert sim.class_xp_kills >= 500 and sim.gold >= 200
    sim = Simulation(content)
    sim.time = RUN_SECONDS
    boss = sim.spawn_boss()
    assert boss
    boss.health = 0
    sim.player.health = 0
    sim.collect_dead()
    sim.step(FIXED_DT)
    assert sim.finished and not sim.won and sim.outcome == "death"
    sim = Simulation(content)
    sim.time = RUN_SECONDS
    sim.spawn_boss()
    sim.player.health = 0
    sim.step(FIXED_DT)
    assert sim.finished and sim.boss_result == "alive" and not sim.won


@pytest.mark.parametrize(
    "aid",
    (
        "hogger_cleave",
        "hogger_charge",
        "hogger_leap",
        "hogger_quake",
        "captain_volley",
        "captain_bomb",
        "pack_charge",
        "pack_smash",
        "web_trap",
        "venom_volley",
    ),
)
def test_hostile_telegraphs_delay_real_damage_then_can_hit(content, aid):
    sim = Simulation(content)
    sim.time = RUN_SECONDS
    boss = sim.spawn_boss()
    assert boss
    boss.pos = sim.player.pos + Vector2(-90, 0)
    a = content.attacks[aid]
    sim.enemy_combat.begin(boss, aid)
    hp = sim.player.health
    for _ in range(int(a.warning / FIXED_DT) - 2):
        sim.player.hurt_timer = 0
        sim.enemy_combat.update_attacks(FIXED_DT)
    assert sim.player.health == hp
    for _ in range(100):
        sim.enemy_combat.update_attacks(FIXED_DT)
        sim.enemy_combat.update_projectiles(FIXED_DT)
        sim.player.hurt_timer = max(0, sim.player.hurt_timer - FIXED_DT)
    assert sim.player.health < hp
    if a.kind in {"charge", "leap"}:
        assert boss.pos != sim.player.pos + Vector2(-90, 0)


def test_warning_can_be_dodged_and_owner_death_cancels_unfired_attack(content):
    sim = Simulation(content)
    e = sim.spawn_elite("defias_captain")
    e.pos = sim.player.pos + Vector2(-150, 0)
    sim.enemy_combat.begin(e, "captain_bomb")
    hp = sim.player.health
    sim.player.pos += Vector2(300, 0)
    for _ in range(120):
        sim.enemy_combat.update_attacks(FIXED_DT)
    assert sim.player.health == hp
    sim.enemy_combat.begin(e, "captain_volley")
    e.health = 0
    for _ in range(120):
        sim.enemy_combat.update_attacks(FIXED_DT)
    assert not sim.enemy_combat.projectiles and not sim.enemy_combat.attacks


def test_hostile_projectiles_use_swept_hits_and_immunity(content):
    sim = Simulation(content)
    p = sim.player
    sim.enemy_combat.projectiles = [
        HostileProjectile(p.pos - Vector2(100, 0), Vector2(1000, 0), 20, 8, "hostile_arrow")
    ]
    sim.enemy_combat.update_projectiles(0.2)
    assert p.health < p.max_health and not sim.enemy_combat.projectiles
    p.immune = 1
    old = p.health
    sim.enemy_combat.projectiles = [
        HostileProjectile(p.pos - Vector2(100, 0), Vector2(1000, 0), 20, 8, "hostile_arrow")
    ]
    sim.enemy_combat.update_projectiles(0.2)
    assert p.health == old


def test_boss_enrage_controls_and_catalog_pool_extensibility(content):
    sim = Simulation(content)
    sim.time = 1800
    boss = sim.spawn_boss()
    assert boss
    boss.health = boss.max_health * 0.49
    sim.enemy_combat.update(FIXED_DT, sim.enemies)
    assert boss.enraged
    other = replace(content.bosses["hogger"], id="test_boss", name="Test Boss")
    altered = replace(content, bosses={"test_boss": other}, boss_pool=("test_boss",))
    sim = Simulation(altered)
    sim.time = 1800
    boss = sim.spawn_boss()
    assert boss and boss.boss_id == "test_boss"


def test_exact_rewards_failures_victory_bonus_and_achievements(tmp_path):
    failed = calculate_rewards(80, 2, 600, False, 40, 1, class_xp_kills=350)
    assert failed.class_xp == 450
    assert failed.gold == 40 + 10 + 30 + 20 + 75 + 80 + 100
    won = calculate_rewards(80, 2, 1800, True, 40, 1, class_xp_kills=350)
    assert won.class_xp == 5650 and won.gold == 40 + 10 + 90 + 1500 + 20 + 75 + 80 + 100 + 300
    previous = calculate_rewards(80, 2, 1800, True, 40, 1, won.achievements, class_xp_kills=350)
    assert previous.achievements == () and previous.gold == 1640
    with pytest.raises(ValueError):
        calculate_rewards(-1, 0, 0, False, 0, 0)
    save = SaveStore(tmp_path / "save.json")
    result = save.reward_run("hunter", 80, 2, 600, False, 40, 1, 350)
    assert result["gold"] == failed.gold + 60 and result["class_xp"] == failed.class_xp
    assert "survive_10" in result["achievements"]
    loaded = SaveStore(tmp_path / "save.json")
    assert loaded.data["classes"]["hunter"]["xp"] == 450 and loaded.data["stats"]["wins"] == 0
    save.reward_run("hunter", 80, 2, 1800, True, 40, 1, 350)
    assert save.data["stats"]["wins"] == 1


@pytest.mark.parametrize(
    "value,seconds", (("0:00", 0), ("05:00", 300), ("29:59", 1799), ("1800", 1800))
)
def test_debug_specific_time_parser(value, seconds):
    assert parse_run_time(value) == seconds


@pytest.mark.parametrize("value", ("31:00", "10:60", "-1", "a:b", ""))
def test_debug_invalid_time_parser(value):
    with pytest.raises(ValueError):
        parse_run_time(value)


def test_new_debug_actions_are_protected_and_operational(content):
    keys = (pygame.K_F9, pygame.K_F10, pygame.K_F11, pygame.K_F12, pygame.K_t)
    for key in keys:
        sim = Simulation(content)
        assert not DebugTools().handle(key, sim) and not DebugTools(True, True).handle(key, sim)
        assert sim.time == 0 and not sim.enemies and not sim.gold
    sim = Simulation(content)
    debug = DebugTools(True)
    debug.handle(pygame.K_F9, sim)
    assert sim.time == 60 and sim.debug_used
    debug.handle(pygame.K_F10, sim)
    assert any(e.elite for e in sim.enemies)
    debug.handle(pygame.K_F11, sim)
    assert sim.boss and sim.debug_used
    debug.handle(pygame.K_F12, sim)
    assert sim.gold == 100
    debug.handle(pygame.K_t, sim)
    for key in (pygame.K_3, pygame.K_0, pygame.K_COLON, pygame.K_0, pygame.K_0, pygame.K_RETURN):
        debug.input_time(key, sim)
    assert sim.time == 1800 and debug.time_entry is None
    debug.reset()
    assert debug.speed == 1 and debug.time_entry is None


def test_late_reinforcement_surge_is_real_and_distant_old_xp_remains_collectable(content):
    sim = Simulation(content)
    wave = content.waves[29]
    assert wave.surge >= 700
    for _ in range(180):
        sim.spawner.update(FIXED_DT, 1740, sim.camera.pos, sim.player.pos, sim.enemies)
    assert len(sim.enemies) >= wave.surge and sim.spawner.pending_surge == 0
    sim = Simulation(content)
    sim.drop(sim.player.pos + Vector2(600, 0), "xp", 5)
    gem = next(iter(sim.pickups.values()))
    before = gem.pos.copy()
    sim.collect_pickups(FIXED_DT)
    assert gem.pos == before and sim.player.xp == 0
    sim.time = 46
    for _ in range(120):
        sim.collect_pickups(FIXED_DT)
    assert sim.player.xp == 5 and not sim.pickups


def test_lethal_damage_cannot_be_reversed_by_regen_or_automatic_healing(content):
    for already_dead in (False, True):
        sim = Simulation(content)
        sim.player.spells = {"holy_shock": SpellState(8)}
        sim.player.passives = {"regen": 5}
        sim.player.health = 0 if already_dead else 1
        enemy = sim.spawn("wolf", sim.player.pos + Vector2(20, 0))
        old = enemy.health
        sim.step(FIXED_DT)
        assert sim.finished and sim.outcome == "death" and sim.player.health == 0
        assert enemy.health == old
    sim = Simulation(content)
    with pytest.raises(ValueError):
        sim.finish("victory")
    with pytest.raises(ValueError):
        calculate_rewards(1, 0, 10, True, 0, 0)


@pytest.mark.parametrize("cid", ("paladin", "warrior", "mage", "hunter", "warlock", "priest"))
def test_every_class_can_damage_live_boss_with_full_arsenal(content, cid):
    sim = Simulation(content, cid)
    sim.player.invulnerable = True
    cls = content.classes[cid]
    sim.player.spells = {aid + "_evolved": SpellState(8) for aid in cls.abilities[:8]}
    sim.player.passives = {"might": 5, "area": 5, "haste": 5, "projectiles": 5}
    sim.time = 1800
    boss = sim.spawn_boss()
    boss.pos = sim.player.pos + Vector2(70, 0)
    sim.grid.rebuild(sim.enemies)
    before = boss.health
    for _ in range(180):
        sim.step(FIXED_DT)
    assert boss.health < before and not sim.finished
    assert boss.boss_id == "hogger"
