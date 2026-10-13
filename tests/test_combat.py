from dataclasses import replace

import pytest
from pygame import Vector2

from warcraft_survivors.combat import damage_enemy, hurt_player, incoming_damage
from warcraft_survivors.entities import SpellState
from warcraft_survivors.simulation import FIXED_DT, Simulation


def test_content_has_six_classes_and_elwynn_enemy_catalog(content):
    assert len(content.classes) == 6
    assert len(content.abilities) == 60
    assert {"kobold", "wolf", "bandit", "gnoll", "spider", "forest_bear"} <= set(content.enemies)
    assert len(content.enemies) >= 8
    assert content.enemies["wolf"].speed > content.enemies["kobold"].speed
    assert content.enemies["bandit"].health > content.enemies["kobold"].health
    sim = Simulation(content)
    assert sim.player.level == 1 and list(sim.player.spells) == ["judgment"]
    assert sim.player.spells["judgment"].rank == 1 and not sim.player.passives


def test_stationary_judgment_auto_targets_and_kills_with_real_projectile(content):
    sim = Simulation(content)
    start = sim.player.pos.copy()
    enemy = sim.spawn("kobold", start + Vector2(80, 0))
    enemy.speed = 0
    sim.step(FIXED_DT)
    assert sim.projectiles and sim.projectiles[0].velocity.x > 0
    assert sim.projectiles[0].pos.x > start.x
    assert enemy.health == enemy.max_health  # It has not reached the enemy yet.
    for _ in range(120):
        sim.step(FIXED_DT)
    assert sim.player.pos == start and enemy.health == 0
    assert sim.kills == 1
    assert sim.player.xp > 0 or any(p.kind == "xp" for p in sim.pickups.values())


def test_no_target_uses_last_facing(content):
    sim = Simulation(content)
    sim.player.facing = Vector2(-1, 0)
    sim.combat.cast(content.abilities["judgment"], SpellState())
    assert sim.projectiles[0].velocity == Vector2(-440, 0)


def test_projectile_swept_collision_and_piercing(content):
    sim = Simulation(content)
    enemies = [sim.spawn("bandit", sim.player.pos + Vector2(x, 0)) for x in (80, 150)]
    sim.grid.rebuild(enemies)
    state = SpellState(4)
    sim.combat.cast(content.abilities["judgment"], state)
    sim.projectiles[0].velocity = Vector2(440, 0)
    sim.combat.update_projectiles(0.5)
    assert all(enemy.health == 0 for enemy in enemies)
    sim.collect_dead()
    assert sim.kills == 2 and sum(p.value for p in sim.pickups.values() if p.kind == "xp") == 20
    sim.collect_dead()
    assert sim.kills == 2  # Rewards are not duplicated.


def test_area_strategy_is_reusable_without_adding_a_playable_spell(content):
    sim = Simulation(content)
    near = sim.spawn(pos=sim.player.pos + Vector2(30, 0))
    far = sim.spawn(pos=sim.player.pos + Vector2(200, 0))
    sim.grid.rebuild(sim.enemies)
    template = content.abilities["judgment"]
    area = replace(template, kind="area", ranks=(replace(template.ranks[0], radius=80),))
    sim.combat.cast(area, SpellState())
    assert (
        near.health == max(0, near.max_health - area.ranks[0].damage)
        and far.health == far.max_health
    )
    assert sim.visuals


def test_damage_calculation_and_brief_hit_immunity(content):
    assert incoming_damage(100, 0.1, 2) == pytest.approx(74)
    assert incoming_damage(100, 5, 20) == 25
    sim = Simulation(content)
    p = sim.player
    assert hurt_player(p, 10)
    assert p.health == 126 and p.hurt_timer == 0.65
    assert not hurt_player(p, 100)
    for _ in range(40):
        sim.step(FIXED_DT)
    assert hurt_player(p, 10)
    p.invulnerable = True
    p.hurt_timer = 0
    assert not hurt_player(p, 1000)
    p.invulnerable = False
    assert hurt_player(p, 1000) and p.health == 0


def test_enemy_contact_chase_and_death_finish_run(content):
    sim = Simulation(content)
    enemy = sim.spawn("wolf", sim.player.pos + Vector2(60, 0))
    enemy.health = enemy.max_health = 100000
    distance = enemy.pos.distance_to(sim.player.pos)
    for _ in range(40):
        sim.step(FIXED_DT)
    assert enemy.pos.distance_to(sim.player.pos) < distance
    assert sim.player.health < sim.player.max_health
    sim.player.health = 1
    sim.player.hurt_timer = 0
    sim.step(FIXED_DT)
    assert sim.finished and sim.player.health == 0


@pytest.mark.parametrize("dt", (1 / 30, 1 / 60, 1 / 120))
def test_cooldowns_are_frame_independent(content, dt):
    sim = Simulation(content)
    casts = 0
    for _ in range(round(4.9 / dt)):
        casts += sim.combat.update(dt)
    assert casts == 4
    assert sim.player.spells["judgment"].timer == pytest.approx(0.1)


def test_damage_never_heals_or_rekills(content):
    sim = Simulation(content)
    enemy = sim.spawn()
    old = enemy.health
    damage_enemy(enemy, -5)
    assert enemy.health == old
    damage_enemy(enemy, 99999)
    damage_enemy(enemy, 99999)
    assert enemy.health == 0


def test_same_seed_replays(content):
    a, b = Simulation(content, seed=42), Simulation(content, seed=42)
    for _ in range(300):
        a.step(FIXED_DT, Vector2(0, 1))
        b.step(FIXED_DT, Vector2(0, 1))
    assert a.player.pos == b.player.pos and a.camera.pos == b.camera.pos
    assert [(e.kind, e.pos, e.health) for e in a.enemies] == [
        (e.kind, e.pos, e.health) for e in b.enemies
    ]
