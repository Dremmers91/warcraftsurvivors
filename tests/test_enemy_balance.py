"""Zone variety, real attack/reward paths, measured metrics and load invariants."""

import json
from dataclasses import replace
from pathlib import Path

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.balance_metrics import BalanceMetrics
from warcraft_survivors.combat import damage_enemy
from warcraft_survivors.persistence import SaveStore
from warcraft_survivors.progression import xp_required
from warcraft_survivors.rendering import Renderer
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.spawning import ENEMY_LIMIT
from warcraft_survivors.world import SpatialHash

ZONES = ("elwynn", "duskwood", "stranglethorn", "plaguelands", "icecrown")
NEW = {
    "duskwood_restless_spirit": "undead",
    "duskwood_worgen": "humanoid",
    "duskwood_skeletal_archer": "undead",
    "stranglethorn_gorilla": "beast",
    "stranglethorn_basilisk": "beast",
    "stranglethorn_crocolisk": "beast",
    "plaguelands_banshee": "undead",
    "plaguelands_gargoyle": "undead",
    "plaguelands_abomination": "undead",
    "icecrown_nerubian": "undead",
    "icecrown_frost_revenant": "undead",
    "icecrown_wyrm_hatchling": "undead",
}
ATTACKS = (
    "spirit_wail",
    "worgen_lunge",
    "gorilla_slam",
    "basilisk_gaze",
    "gargoyle_dive",
    "plague_bile",
    "nerubian_rush",
    "revenant_shards",
    "wyrm_breath",
)


@pytest.mark.parametrize("zid", ZONES)
def test_rosters_are_live_varied_and_all_designs_available(content, zid):
    zone = content.zones[zid]
    assert len(zone.enemies) >= 8 and len(zone.elites) >= 3
    assert len({content.enemies[e].sprite for e in zone.enemies}) >= 8
    sim = Simulation(content, zone_id=zid)
    encountered = set()
    for minute in range(30):
        kinds, weights = sim.spawner.pool(minute * 60)
        encountered.update(kinds)
        assert all(w > 0 for w in weights)
    assert encountered == set(zone.enemies)
    assert {content.enemies[e].behavior for e in zone.enemies} >= {"ranged", "flank", "bruiser"}
    assert zone.boss_pool and all(b in content.bosses for b in zone.boss_pool)
    assert all(content.elites[e].enemy in zone.enemies for e in zone.elites)
    first, late = zone.waves[0], zone.waves[-1]
    assert first.rate < late.rate and first.health < late.health and first.xp < late.xp
    assert late.density <= ENEMY_LIMIT and late.surge >= 1200


@pytest.mark.parametrize("eid,family", NEW.items())
def test_new_creatures_load_animate_and_attribute_actual_deaths(content, tmp_path, eid, family):
    pygame.init()
    pygame.display.set_mode((1280, 720))
    zid = eid.split("_")[0]
    sim = Simulation(content, "hunter", zone_id=zid)
    renderer = Renderer(content)
    spec = renderer.assets.manifest["actors"][eid]
    assert spec["active"]
    assert content.enemies[eid].family == family
    enemy = sim.spawn(eid, sim.player.pos + Vector2(75, 0))
    renderer.draw_game(sim)
    damage_enemy(enemy, enemy.health, source="beast_companion", delivery="companion")
    sim.collect_dead()
    event = sim.ledger.last_event
    assert event and event.family == family and event.zone == zid
    assert event.source == "beast_companion" and event.delivery == "companion"
    assert sim.class_xp_kills == content.enemies[eid].class_xp
    assert sum(p.value for p in sim.pickups.values() if p.kind == "xp") == enemy.xp
    save = SaveStore(tmp_path / "save.json")
    result = save.reward_run(
        "hunter", sim.kills, 0, 10, False, 0, 0, sim.class_xp_kills, summary=sim.ledger.summary(sim)
    )
    assert result["class_xp"] >= enemy.class_xp
    assert save.data["stats"]["family_kills"][family] == 1
    sim.enemies.append(enemy)
    sim.collect_dead()
    assert sim.kills == 1


@pytest.mark.parametrize("aid", ATTACKS)
def test_new_attacks_warn_execute_and_can_damage(content, aid):
    definition = next(e for e in content.enemies.values() if aid in e.attacks)
    zid = definition.id.split("_")[0]
    sim = Simulation(content, zone_id=zid)
    sim.player.health = sim.player.max_health = 1000
    enemy = sim.spawn(definition.id, sim.player.pos + Vector2(100, 0))
    sim.enemy_combat.begin(enemy, aid)
    assert sim.enemy_combat.attacks[0].warning >= 0.9
    for _ in range(360):
        sim.player.hurt_timer = max(0, sim.player.hurt_timer - FIXED_DT)
        sim.enemy_combat.update_attacks(FIXED_DT)
        sim.enemy_combat.update_projectiles(FIXED_DT)
    assert sim.enemy_combat.attack_counts[aid] >= 1
    assert sim.player.health < 1000


@pytest.mark.parametrize("zid", ZONES[1:])
def test_third_elites_use_new_art_mechanics_rewards_and_chests(content, zid):
    sim = Simulation(content, zone_id=zid)
    sim.time = 1500
    definition = content.elites[zid + "_elite_2"]
    enemy = sim.spawn_elite(definition.id)
    assert enemy.sprite == definition.id and enemy.sprite != enemy.kind
    assert len(definition.attacks) == 2
    assert enemy.class_xp > 150 and enemy.radius > content.enemies[enemy.kind].radius
    damage_enemy(enemy, enemy.health, source="judgment")
    sim.collect_dead()
    assert sim.elites == 1 and sim.class_xp_kills == enemy.class_xp
    assert any(p.kind == "chest" for p in sim.pickups.values())
    assert sim.ledger.last_event.elite


def test_surge_obeys_safety_ceiling_even_with_large_schedule_density(content):
    sim = Simulation(content)
    wave = replace(content.waves[-1], density=ENEMY_LIMIT + 500, surge=10000)
    sim.spawner.director.waves = (*content.waves[:-1], wave)
    # Existing crowd fixture avoids spending time allocating 6,000 sprites.
    sim.enemies = [sim.spawn()] * (ENEMY_LIMIT - 1)
    sim.spawner.update(0.05, 1740, sim.camera.pos, sim.player.pos, sim.enemies)
    assert len(sim.enemies) == ENEMY_LIMIT


def test_developer_rates_are_rolling_bounded_and_reset_after_time_skip():
    metrics = BalanceMetrics()
    assert metrics.observe(0, 0, 0, 0) == (0, 0, 0)
    for tick in range(1, 241):
        result = metrics.observe(tick / 4, tick * 2, tick, tick * 5)
    assert result == pytest.approx((8, 4, 1200))
    assert len(metrics.samples) <= 48
    assert metrics.observe(1200, 9999, 9999, 99999) == (0, 0, 0)
    assert metrics.observe(0, 0, 0, 0) == (0, 0, 0)


def test_spatial_instrumentation_counts_checks_without_changing_hits(content):
    sim = Simulation(content)
    enemies = [sim.spawn(pos=sim.player.pos + Vector2(i * 15, 0)) for i in range(30)]
    grid = SpatialHash()
    grid.rebuild(enemies)
    expected = list(grid.nearby(sim.player.pos, 100))
    assert grid.candidate_checks == 0
    grid.track_queries = True
    assert list(grid.nearby(sim.player.pos, 100)) == expected
    assert grid.candidate_checks >= len(expected) and grid.queries == 1
    grid.reset_metrics()
    assert grid.candidate_checks == grid.queries == 0


def test_merged_gems_preserve_xp_and_measured_earnings_after_level_costs(content):
    sim = Simulation(content)
    for value in (11.25, 23.5, 70.75):
        sim.drop(sim.player.pos, "xp", value)
    assert len(sim.pickups) == 1
    sim.collect_pickups(FIXED_DT)
    assert sim.run_xp_collected == 105.5
    assert sim.player.xp == pytest.approx(105.5 - xp_required(1))
    sim.collect_pickups(FIXED_DT)
    assert sim.run_xp_collected == 105.5


def test_new_sources_have_recorded_prompts_and_matching_provenance():
    import hashlib

    source = Path(__file__).resolve().parents[1] / "art_sources/enemy_balance"
    records = json.loads((source / "source_hashes.json").read_text("utf-8"))
    prompts = json.loads((source / "prompts.json").read_text("utf-8"))
    assert len(prompts["prompts"]) == len(records) == 4
    for record in records.values():
        assert len(record["actors"]) == 4 and len(record["reviewed_cutouts"]) == 4
        assert (
            hashlib.sha256((source / record["file"]).read_bytes()).hexdigest() == record["sha256"]
        )
