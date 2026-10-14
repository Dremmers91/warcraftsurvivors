"""Companion contracts, late-rank attacks and shared reward/profile integration."""

from dataclasses import replace

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.combat import spell_stats
from warcraft_survivors.entities import HostileProjectile, SpellState
from warcraft_survivors.meta import MetaBonuses
from warcraft_survivors.persistence import SaveStore
from warcraft_survivors.rendering import Renderer
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.upgrades import evolution_eligible

IMP = "summon_felguard"
WOLF = "beast_companion"


def setup(content, aid=IMP, rank=1):
    sim = Simulation(content, "hunter" if aid.startswith(WOLF) else "warlock", seed=47)
    sim.player.spells = {aid: SpellState(rank)}
    sim.spawner.timer = 10**9
    sim.combat.cast(content.ability(aid), sim.player.spells[aid])
    return sim


def enemy_at(sim, offset, health=10000):
    enemy = sim.spawn("bandit", sim.player.pos + Vector2(offset))
    enemy.health = enemy.max_health = health
    enemy.speed = 0
    return enemy


def tick(sim, seconds):
    for _ in range(round(seconds / FIXED_DT)):
        sim.combat.update_companions(FIXED_DT)
        sim.combat.update_projectiles(FIXED_DT)
        sim.combat.update_statuses(FIXED_DT)


@pytest.mark.parametrize("aid", (IMP, WOLF))
def test_invulnerable_untargetable_through_hostile_projectile_and_contact(content, aid):
    sim = setup(content, aid)
    pet = sim.combat.companions[0]
    pet.pos = sim.player.pos + Vector2(160, 0)
    enemy_at(sim, (160, 0))
    sim.enemy_combat.projectiles.append(
        HostileProjectile(pet.pos.copy(), Vector2(), 100, 12, "hostile_arrow")
    )
    health = sim.player.health
    for _ in range(30):
        sim.enemy_combat.update(FIXED_DT, sim.enemies)
    assert sim.player.health == health
    assert not hasattr(pet, "health") and not hasattr(pet, "xp")
    assert all(item is not pet for item in sim.grid.items())
    assert all(item is not pet for item in sim.enemies)


@pytest.mark.parametrize("aid", (IMP, WOLF))
def test_filters_outside_leash_before_selection_and_retargets_dead_enemy(content, aid):
    sim = setup(content, aid)
    pet = sim.combat.companions[0]
    pet.pos = sim.player.pos + Vector2(300, 0)
    outside = enemy_at(sim, (321, 0))
    inside = enemy_at(sim, (260, 0))
    sim.combat.update_companions(FIXED_DT)
    assert pet.target is inside
    inside.health = 0
    replacement = enemy_at(sim, (250, 10))
    sim.combat.update_companions(FIXED_DT)
    assert pet.target is replacement and outside.health == outside.max_health
    sim.player.pos += Vector2(1500, 0)
    sim.combat.update_companions(FIXED_DT)
    assert pet.pos.distance_to(sim.player.pos) <= pet.leash
    assert pet.target is None


def test_configurable_leash_spawn_return_and_no_outside_damage(content, monkeypatch):
    original = content.abilities[IMP]
    monkeypatch.setitem(
        content.abilities, IMP, replace(original, mechanics=replace(original.mechanics, leash=60))
    )
    sim = setup(content, rank=8)
    outside = enemy_at(sim, (61, 0))
    tick(sim, 0.5)
    assert all(p.pos.distance_to(sim.player.pos) <= 60 for p in sim.combat.companions)
    assert outside.health == outside.max_health


def test_target_search_is_throttled_and_never_enumerates_global_grid(content, monkeypatch):
    sim = setup(content)
    enemy_at(sim, (180, 0))
    queries = 0
    original = sim.combat.pet_candidates

    def candidates(*args):
        nonlocal queries
        queries += 1
        return original(*args)

    monkeypatch.setattr(sim.combat, "pet_candidates", candidates)
    monkeypatch.setattr(sim.grid, "items", lambda: pytest.fail("global companion search"))
    for _ in range(60):
        sim.combat.update_companions(FIXED_DT)
    assert 2 <= queries <= 12


@pytest.mark.parametrize(
    "rank,count,bolts", ((1, 1, 1), (4, 1, 1), (5, 2, 1), (6, 2, 2), (8, 2, 2))
)
def test_imp_rank_count_firebolt_origin_and_near_owner_position(content, rank, count, bolts):
    sim = setup(content, rank=rank)
    enemy = enemy_at(sim, (210, 0))
    sim.combat.update_companions(FIXED_DT)
    assert len(sim.combat.companions) == count
    assert len(sim.projectiles) == count * bolts
    assert all(p.sprite == "imp" for p in sim.combat.companions)
    assert all(p.pos.distance_to(sim.player.pos) < 70 for p in sim.combat.companions)
    assert any(shot.pos.distance_to(sim.combat.companions[0].pos) < 32 for shot in sim.projectiles)
    tick(sim, 0.6)
    assert enemy.health < enemy.max_health and enemy.owner == "player"


def test_splash_burn_unlocks_and_rank8_growth(content):
    values = []
    for rank in (1, 4, 6, 8):
        sim = setup(content, rank=rank)
        primary = enemy_at(sim, (180, 0))
        splash = enemy_at(sim, (180, 32))
        ability = content.abilities[IMP]
        sim.combat.hit(
            primary,
            spell_stats(ability, sim.player.spells[IMP], sim.player).damage,
            ability,
            sim.player.spells[IMP],
        )
        values.append((splash.max_health - splash.health, bool(primary.statuses)))
    assert values[0] == (0, False)
    assert values[1][0] > 0 and not values[1][1]
    assert values[2][1] and values[3][0] > values[2][0]


def test_wolf_rank_gated_leap_and_cluster_cleave(content):
    distances = []
    for rank in (1, 3):
        sim = setup(content, WOLF, rank)
        target = enemy_at(sim, (180, 0))
        nearby = enemy_at(sim, (180, 24))
        pet = sim.combat.companions[0]
        start = pet.pos.copy()
        sim.combat.update_companions(FIXED_DT)
        distances.append(pet.pos.distance_to(start))
        tick(sim, 0.7)
        assert target.health < target.max_health and nearby.health < nearby.max_health
    assert distances[1] > distances[0] * 10


def test_passives_meta_and_buff_scale_actual_imp_projectiles(content):
    shots = []
    for boosted in (False, True):
        sim = setup(content)
        enemy_at(sim, (180, 0))
        if boosted:
            sim.player.passives = {"might": 2, "haste": 2, "velocity": 2, "area": 2}
            sim.player.meta = MetaBonuses({"kind:companion": 0.2, "school:fire": 0.1})
            sim.player.pet_buff, sim.player.buff_time, sim.player.buff_power = True, 5, 0.5
        sim.combat.update_companions(FIXED_DT)
        shot = sim.projectiles[0]
        shots.append(
            (shot.damage, shot.velocity.length(), shot.radius, sim.combat.companions[0].timer)
        )
    assert all(shots[1][i] > shots[0][i] for i in range(3))
    assert shots[1][3] < shots[0][3]


def test_imp_legion_uses_existing_chest_replaces_pet_and_fires_multiple_directions(content):
    sim = setup(content, rank=8)
    sim.player.passives = {"armor": 1}
    assert IMP in evolution_eligible(content, sim.player)
    sim.pending_chests = 1
    sim.level_check()
    index = next(i for i, c in enumerate(sim.choices) if c.id == IMP and c.kind == "evolution")
    sim.choose(index)
    assert not sim.combat.companions and len(sim.player.spells) == 1
    aid = IMP + "_evolved"
    assert content.ability(aid).name == "Imp Legion"
    for angle in range(0, 360, 45):
        enemy_at(sim, Vector2(160, 0).rotate(angle))
    sim.combat.cast(content.ability(aid), sim.player.spells[aid])
    sim.combat.update_companions(FIXED_DT)
    assert len(sim.combat.companions) == 4 and len(sim.projectiles) == 12
    assert len({round(s.velocity.as_polar()[1] / 20) for s in sim.projectiles}) >= 4
    tick(sim, 0.5)
    assert sum(e.health < e.max_health for e in sim.enemies) >= 4


@pytest.mark.parametrize("aid", (IMP, WOLF))
def test_pet_kill_xp_gold_and_achievement_reach_owner_profile(content, aid, tmp_path):
    sim = setup(content, aid)
    enemy = enemy_at(sim, (60, 0), health=1)
    enemy.xp, enemy.class_xp, enemy.gold_reward = 7, 9, 3
    tick(sim, 0.5)
    assert enemy.health == 0 and enemy.owner == "player"
    sim.collect_dead()
    assert sim.kills == 1 and sim.gold == 3 and sim.class_xp_kills == 9
    for pickup in sim.pickups.values():
        pickup.pos.update(sim.player.pos)
    sim.collect_pickups(FIXED_DT)
    assert sim.player.xp == 7
    save = SaveStore(tmp_path / "save.json")
    result = save.reward_run(sim.class_id, sim.kills, 0, 0, False, sim.gold, 0, sim.class_xp_kills)
    assert result["saved"] and "first_blood" in result["achievements"]
    reopened = SaveStore(save.path)
    assert reopened.data["stats"]["kills"] == 1
    assert reopened.data["classes"][sim.class_id]["xp"] == 9
    assert reopened.data["gold"] >= 3


def test_visual_states_allied_edge_and_firebolt_cache_use_bundled_art(content, monkeypatch):
    pygame.init()
    pygame.display.set_mode((1280, 720))
    renderer = Renderer(content)
    try:
        assert not renderer.assets.warnings
        wolf = renderer.assets.actor("wolf", "idle", "east", 0)
        ally = renderer.assets.actor("wolf", "idle", "east", 0, allied=True)
        assert ally.image.get_width() == wolf.image.get_width() + 2
        assert renderer.assets.manifest["projectiles"][IMP]["spin_degrees"] == 0
        assert renderer.assets.manifest["effects"][IMP]["file"] == "effects/fireball.png"
        calls = []
        actor = renderer.assets.actor

        def observed(name, state, *args, **kwargs):
            if name == "imp":
                calls.append(state)
            return actor(name, state, *args, **kwargs)

        monkeypatch.setattr(renderer.assets, "actor", observed)
        monkeypatch.setattr(pygame.image, "load", lambda *args: pytest.fail("runtime decode"))
        monkeypatch.setattr(
            pygame.transform, "rotate", lambda *args: pytest.fail("runtime rotation")
        )
        sim = setup(content)
        for state in ("idle", "walk", "cast"):
            pet = sim.combat.companions[0]
            pet.moving = state == "walk"
            pet.attack_time = 0.2 if state == "cast" else 0
            renderer.draw_game(sim)
            assert state in calls
        enemy_at(sim, (160, 0))
        sim.combat.update_companions(FIXED_DT)
        for quality in ("low", "medium", "high"):
            renderer.quality = quality
            renderer.draw_game(sim)
    finally:
        pygame.quit()
