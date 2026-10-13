"""Expansion schedule, boss mechanics, audio/device recovery and UI integration contracts."""

from __future__ import annotations

import pickle
import wave

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.app import App
from warcraft_survivors.audio import ROOT, Audio
from warcraft_survivors.combat import automatic_heal, damage_enemy
from warcraft_survivors.entities import Field, SpellState
from warcraft_survivors.persistence import SaveStore
from warcraft_survivors.rendering import Renderer
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.waves import WaveDirector
from warcraft_survivors.world import WORLD_SIZE

ZONES = ("elwynn", "duskwood", "stranglethorn", "plaguelands", "icecrown")
CLASSES = ("paladin", "warrior", "mage", "hunter", "warlock", "priest")


@pytest.mark.parametrize("zid", ZONES)
def test_every_zone_complete_schedule_restrictions_and_encounters(content, zid):
    zone = content.zones[zid]
    assert zone.enemies and zone.elites and zone.boss_pool
    assert WORLD_SIZE > 720 * 10
    sim = Simulation(content, zone_id=zid)
    director = WaveDirector(content, zid)
    for minute in range(30):
        wave = director.wave(minute * 60)
        assert wave.start == minute * 60
        assert director.wave(minute * 60 + 59.999) == wave
        kinds, weights = sim.spawner.pool(minute * 60)
        assert kinds and all(w > 0 for w in weights)
        assert set(kinds) <= set(zone.enemies)
        assert all(content.enemies[k].min_time <= minute * 60 for k in kinds)
    first, last = director.wave(0), director.wave(1799)
    assert last.rate > first.rate and last.density >= 4000
    assert last.health > first.health and last.xp > first.xp
    assert len(last.weights) > len(first.weights)
    sim.time = 299.99
    sim.step(FIXED_DT)
    elite = next(e for e in sim.enemies if e.elite)
    assert elite.elite_id in zone.elites
    sim.time = 599.99
    sim.step(FIXED_DT)
    assert elite in sim.enemies
    sim.player.spells = {"judgment": SpellState(8)}
    sim.player.passives = {"projectiles": 1}
    damage_enemy(elite, elite.health)
    sim.collect_dead()
    assert sim.elites == 1
    chest = next(p for p in sim.pickups.values() if p.kind == "chest")
    sim.player.pos = chest.pos.copy()
    sim.collect_pickups(FIXED_DT)
    assert sim.chest_choice and any(c.kind == "evolution" for c in sim.choices)
    while sim.choices:
        sim.choose(0)
    sim.time = 1799.99
    sim.director.seek(sim.time)
    sim.step(FIXED_DT)
    assert sim.boss and sim.boss.boss_id in zone.boss_pool and not sim.won
    damage_enemy(sim.boss, sim.boss.health)
    sim.step(FIXED_DT)
    assert sim.won and sim.boss_defeated


@pytest.mark.parametrize("zid", ZONES)
@pytest.mark.parametrize("cid", CLASSES)
def test_all_class_zone_combinations_start_one_spell_and_real_damage(content, zid, cid):
    sim = Simulation(content, cid, zone_id=zid)
    assert tuple(sim.player.spells) == (content.classes[cid].abilities[0],)
    assert not sim.combat.companions
    sim.spawner.timer = 1e9
    e = sim.spawn(content.zones[zid].enemies[0], sim.player.pos + Vector2(35, 0))
    e.health = e.max_health = 10000
    sim.player.invulnerable = True
    for _ in range(180):
        sim.step(FIXED_DT)
    assert e.health < e.max_health
    assert sim.player.pos == Vector2(4096, 4096)


@pytest.mark.parametrize("zid", ZONES[1:])
def test_distinct_boss_attacks_all_execute_and_zone_rewards_persist(content, tmp_path, zid):
    sim = Simulation(content, zone_id=zid)
    sim.time = 1800
    boss = sim.spawn_boss()
    assert boss is not None
    definition = content.bosses[boss.boss_id]
    assert len(definition.attacks) >= 4 and definition.radius > 30
    sim.player.invulnerable = True
    for aid in definition.attacks:
        boss.pos = sim.world.resolve(sim.player.pos + Vector2(100, 0), boss.radius)
        sim.enemy_combat.begin(boss, aid)
        attack = content.attacks[aid]
        for _ in range(round((attack.warning + attack.duration + 0.15) / FIXED_DT)):
            sim.enemy_combat.update_attacks(FIXED_DT)
            sim.enemy_combat.update_projectiles(FIXED_DT)
        assert sim.enemy_combat.attack_counts[aid] >= 1
    boss.health = 0
    sim.collect_dead()
    sim.finish("victory")
    save = SaveStore(tmp_path / "save.json")
    result = save.reward_run(
        "paladin",
        sim.kills,
        sim.elites,
        sim.elapsed,
        True,
        sim.gold,
        0,
        sim.class_xp_kills,
        0,
        boss.boss_id,
    )
    assert result["gold"] >= 1500 and result["class_xp"] >= 5000
    assert "boss_" + boss.boss_id in result["achievements"]
    reload = SaveStore(save.path)
    assert reload.data["stats"]["boss_kills"][boss.boss_id] == 1
    assert reload.data["unlocked_zones"] == list(ZONES)


def test_defile_pulses_grows_and_frost_slow_preserves_immunity(content):
    sim = Simulation(content, zone_id="icecrown")
    sim.time = 1800
    boss = sim.spawn_boss()
    sim.player.health = sim.player.max_health = 1000
    sim.enemy_combat.begin(boss, "lich_defile")
    hazard = sim.enemy_combat.attacks[-1]
    for _ in range(300):
        sim.player.hurt_timer = max(0, sim.player.hurt_timer - FIXED_DT)
        sim.enemy_combat.update_attacks(FIXED_DT)
    assert sim.player.health < 970 and hazard.age > 3
    sim.enemy_combat.attacks.clear()
    sim.player.hurt_timer = 0
    sim.enemy_combat.damage(20, 0.3, 2)
    assert sim.player.slow_time == 2 and sim.player.slow_strength == 0.3
    sim.player.immune = 1
    assert not sim.enemy_combat.damage(20, 0.6, 4)
    assert sim.player.slow_strength == 0.3


def test_hook_pull_respects_obstacles_and_damage_immunity(content):
    sim = Simulation(content, zone_id="duskwood")
    start = sim.player.pos.copy()
    assert sim.enemy_combat.damage(10, pull=150, origin=start + Vector2(500, 0))
    assert sim.player.pos.distance_to(start) == pytest.approx(150)
    position = sim.player.pos.copy()
    assert not sim.enemy_combat.damage(10, pull=150, origin=start)
    assert sim.player.pos == position


def test_zone_chunk_cache_and_cosmetic_density_do_not_change_damage(content):
    pygame.init()
    pygame.display.set_mode((1280, 720))
    renderer = Renderer(content)
    colors = []
    for zid in ZONES:
        sim = Simulation(content, zone_id=zid)
        before = pickle.dumps(sim.player)
        renderer.presentation.density = 0
        renderer.draw_game(sim)
        assert pickle.dumps(sim.player) == before
        colors.append(pygame.image.tobytes(renderer.chunk(16, 16, sim.world), "RGB"))
        assert not renderer.assets.warnings
    assert len(set(colors)) == 5
    assert all(len(key) == 4 for key in renderer.chunks)
    assert (
        pygame.image.tobytes(renderer.chunk(16, 16, Simulation(content).world), "RGB") == colors[0]
    )
    pygame.quit()


def test_zone_menu_keyboard_mouse_controller_and_settings_round_trip(tmp_path):
    app = App(SaveStore(tmp_path / "save.json"))
    app.goto("zones")
    app.menu_key(pygame.K_RIGHT)
    app.menu_key(pygame.K_RETURN)
    assert app.selected_zone == "duskwood" and app.screen == "classes"
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
    assert app.sim.zone.id == "duskwood"
    app.end_run()
    app.goto("zones")
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(850, 220)))
    assert app.selected_zone == "stranglethorn"
    app.goto("settings")
    app.cycle_setting("music_volume", (0.0, 0.15, 0.35, 0.6, 1.0))
    app.cycle_setting("effects_density", (0.0, 0.25, 0.5, 0.75, 1.0))
    assert SaveStore(app.save.path).data["settings"]["music_volume"] == 0.6
    assert SaveStore(app.save.path).data["settings"]["effects_density"] == 0
    pygame.quit()


def test_original_audio_library_and_no_device_fallback(monkeypatch):
    for name in ("elwynn", "duskwood", "stranglethorn", "plaguelands", "icecrown"):
        with wave.open(str(ROOT / f"music_{name}.wav")) as track:
            assert track.getnchannels() == 2 and track.getframerate() == 22050
            assert track.getnframes() > 22050 * 10
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)
    audio = Audio()
    events = ["boss", "evolution"]
    audio.music("icecrown")
    audio.play(events, 1)
    assert not audio.available and not events


def test_save_settings_sanitization_and_older_profiles_unlock_zones(tmp_path):
    save = SaveStore(tmp_path / "save.json")
    raw = save.defaults()
    raw["unlocked_zones"] = ["elwynn"]
    raw["settings"].update(
        music_volume=float("nan"), sound_volume=-5, effects_density=5, resolution="bogus"
    )
    clean = save.validate(raw)
    assert clean["unlocked_zones"] == list(ZONES)
    assert clean["settings"]["music_volume"] == 0.35
    assert clean["settings"]["sound_volume"] == 0
    assert clean["settings"]["effects_density"] == 1
    assert clean["settings"]["resolution"] == "1280x720"


def test_boss_penetration_and_wound_make_maximum_armor_meaningful(content):
    sim = Simulation(content)
    p = sim.player
    p.armor = 0.75
    before = p.health
    assert sim.enemy_combat.damage(40, armor_penetration=0.5)
    assert before - p.health == 30 and p.wound_time == 2
    p.healing_budget = 100
    automatic_heal(p, 10)
    assert p.health == pytest.approx(before - 26.5)


def test_life_steal_uses_actual_damage_and_bounded_recovery(content):
    sim = Simulation(content, "warlock")
    sim.spawner.timer = 1e9
    sim.player.health = 20
    sim.player.healing_budget = 6
    ability = content.abilities["holy_shock"]
    target = sim.spawn("kobold", sim.player.pos + Vector2(40, 0))
    target.health = 1
    sim.combat.hit(target, 10000, ability, SpellState(8))
    assert sim.player.health - 20 <= 1
    target.health = target.max_health = 100000
    sim.combat.hit(target, 10000, ability, SpellState(8))
    assert sim.player.health <= 26
    before = sim.player.health
    sim.combat.hit(target, 10000, ability, SpellState(8))
    assert sim.player.health == before


def test_beam_broad_phase_includes_large_body_at_segment_end(content):
    sim = Simulation(content)
    aid = next(a.id for a in content.evolutions.values() if a.kind == "beam")
    sim.player.spells = {aid: SpellState(8)}
    enemy = sim.spawn("kobold", sim.player.pos + Vector2(360, 0))
    enemy.radius = 52
    enemy.health = enemy.max_health = 10000
    sim.grid.rebuild(sim.enemies)
    field = Field(sim.player.pos.copy(), aid, 20, 300, 1, Vector2(1, 0))
    sim.combat.fields = [field]
    sim.combat.update_fields(FIXED_DT)
    assert enemy.health < 10000
    enemy.health = 10000
    enemy.pos = sim.player.pos + Vector2(380, 0)
    sim.grid.rebuild(sim.enemies)
    field.timer = 0
    sim.combat.update_fields(FIXED_DT)
    assert enemy.health == 10000
