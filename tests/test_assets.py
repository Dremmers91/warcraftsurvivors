import json
import pickle
import shutil

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.asset_manager import (
    ASSET_ROOT,
    DIRECTIONS,
    AssetManager,
    facing,
    slice_sheet,
)
from warcraft_survivors.presentation import ParticlePool, ScreenShake
from warcraft_survivors.rendering import Renderer
from warcraft_survivors.simulation import FIXED_DT, Simulation


@pytest.fixture
def renderer(content):
    pygame.init()
    pygame.display.set_mode((1280, 720))
    result = Renderer(content)
    yield result
    pygame.quit()


def test_actor_registry_has_distinct_directional_animated_silhouettes(renderer):
    assets = renderer.assets
    assert not assets.warnings
    assert {
        "paladin",
        "warrior",
        "mage",
        "hunter",
        "warlock",
        "priest",
        "kobold",
        "wolf",
        "bandit",
        "hogger",
        "gnoll",
        "spider",
        "forest_bear",
        "forest_boar",
        "broodmother",
    } <= set(assets.actors)
    identities = set()
    for name in assets.actors:
        frames = []
        for direction in DIRECTIONS:
            for index in range(4):
                frame = assets.actor(name, "walk", direction, index / assets.actor_fps[name])
                frames.append(pygame.image.tobytes(frame.image, "RGBA"))
                assert frame.image.get_flags() & pygame.SRCALPHA
                assert 0 <= frame.anchor[1] <= assets.manifest["actors"][name]["frame_size"][1]
        assert len(set(frames)) >= 12
        identities.add(frames[0])
        for state in ("idle", "cast", "death"):
            assert assets.actor(name, state, "south", 0).image.get_width() > 1
    assert len(identities) == len(assets.actors)


def test_animation_facing_and_cached_projectile_sizes_ignore_collision_radius(renderer, content):
    assert facing(Vector2(1, 0)) == "east"
    assert facing(Vector2(-1, 0)) == "west"
    assert facing(Vector2(0, -1)) == "north"
    assets = renderer.assets
    first = assets.projectile("judgment", 1, 0, 0)
    assert first is assets.projectile("judgment", 1, 0, 0)
    sim = Simulation(content)
    sim.player.passives["area"] = 5
    assert first is assets.projectile("judgment", 1, 0, 0)
    assert assets.projectile("judgment", 8, 0, 0).image.get_width() > first.image.get_width()


def test_slicing_retains_world_anchor_and_rejects_bad_dimensions():
    pygame.init()
    sheet = pygame.Surface((16, 8), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))
    sheet.fill((255, 255, 255, 255), (2, 1, 4, 5))
    frames = slice_sheet(sheet, (8, 8), (4, 7))
    assert frames[0][0].anchor == (2, 6)
    assert frames[0][0].at(Vector2(100, 100)) == (98, 94)
    with pytest.raises(ValueError):
        slice_sheet(sheet, (7, 8), (4, 7))
    pygame.quit()


def test_missing_and_corrupt_rasters_have_safe_fallbacks(renderer, tmp_path):
    shutil.copytree(ASSET_ROOT, tmp_path / "assets")
    root = tmp_path / "assets"
    (root / "actors/paladin.png").unlink()
    (root / "effects/holy_hammer.png").write_bytes(b"broken png")
    assets = AssetManager(root)
    assert any("paladin" in warning for warning in assets.warnings)
    assert any("holy_hammer" in warning for warning in assets.warnings)
    assert assets.actor("paladin", "walk", "south", 0).image.get_width() > 0
    assert assets.projectile("judgment", 1, 0, 0).image.get_width() > 0
    (root / "manifest.json").write_text("[]")
    empty = AssetManager(root)
    assert empty.warnings
    assert empty.actor("paladin", "idle", "south", 0).image.get_width() > 0


def snapshot(sim):
    return pickle.dumps(
        (
            sim.player,
            sim.enemies,
            sim.projectiles,
            sim.pickups,
            sim.visuals,
            sim.choices,
            sim.time,
            sim.kills,
            sim.gold,
            sim.camera.pos,
            sim.rng.getstate(),
        )
    )


def test_rendering_is_read_only_and_quality_cannot_change_combat(renderer, content, monkeypatch):
    sim = Simulation(content, seed=71)
    sim.spawn("bandit", sim.player.pos + Vector2(80, 0))

    # After loading, no combat draw may decode a file or create a rotation.
    def forbidden(*args, **kwargs):
        raise AssertionError("Runtime image loading/rotation is forbidden")

    monkeypatch.setattr(pygame.image, "load", forbidden)
    monkeypatch.setattr(pygame.transform, "rotate", forbidden)
    for quality in ("low", "medium", "high"):
        renderer.quality = quality
        for _ in range(30):
            sim.step(FIXED_DT)
            before = snapshot(sim)
            renderer.draw_game(sim)
            assert snapshot(sim) == before


def test_quality_preserves_projectiles_and_impacts_while_reducing_particles(renderer, content):
    sim = Simulation(content)
    sim.step(FIXED_DT)
    renderer.quality = "high"
    renderer.draw_game(sim)
    assert renderer.presentation.particles.active
    count = len(sim.projectiles)
    renderer.quality = "low"
    renderer.draw_game(sim)
    assert not renderer.presentation.particles.active
    assert len(sim.projectiles) == count
    frame = renderer.assets.projectile("judgment", 1, 0, 0)
    assert frame.image.get_bounding_rect().width > 10
    assert renderer.assets.effect("holy_impact", 0).image.get_bounding_rect().width > 10


def test_death_hit_animation_and_pause_timing(renderer, content):
    sim = Simulation(content)
    enemy = sim.spawn("bandit", sim.player.pos + Vector2(130, 0))
    renderer.draw_game(sim)
    enemy.health = 0
    sim.collect_dead()
    sim.step(FIXED_DT)
    renderer.draw_game(sim)
    assert renderer.presentation.deaths
    age = renderer.presentation.deaths[0].age
    renderer.draw_game(sim)
    assert renderer.presentation.deaths[0].age == age
    original = renderer.assets.actor("paladin", "idle", "south", 0)
    flashed = renderer.assets.actor("paladin", "idle", "south", 0, flash=True)
    assert pygame.image.tobytes(original.image, "RGBA") != pygame.image.tobytes(
        flashed.image, "RGBA"
    )


def test_particle_pool_reuses_objects_and_never_exceeds_budget():
    pool = ParticlePool(8)
    original_ids = [id(p) for p in pool.particles]
    for _ in range(50):
        pool.emit(Vector2(10, 10), 5)
    assert len(pool.active) == 5
    pool.update(1)
    assert not pool.active and len(pool.free) == 8
    pool.emit(Vector2(0, 0), 8)
    assert original_ids == [id(p) for p in pool.particles]


def test_manifest_contains_all_playable_classes_and_ability_art(renderer, content):
    manifest = json.loads((ASSET_ROOT / "manifest.json").read_text("utf-8"))
    assert all(manifest["actors"][cid]["active"] for cid in content.classes)
    assert len(content.classes) == 6 and len(content.abilities) == 60
    assert all(
        aid in manifest["effects"]
        for aid in content.abilities | content.evolutions | content.manuals
    )


def test_optional_screen_shake_is_small_and_expires():
    shake = ScreenShake()
    assert shake.offset() == Vector2()
    shake.trigger()
    shake.update(0.03)
    assert shake.offset().length() <= 3
    shake.update(1)
    assert shake.offset() == Vector2()


def test_visual_settings_validate_without_loading_debug_preferences():
    from warcraft_survivors.persistence import SaveStore

    assert (
        SaveStore.validate({"version": 1, "settings": {"effects_quality": "low"}})["settings"][
            "effects_quality"
        ]
        == "low"
    )
    assert (
        SaveStore.validate({"version": 1, "settings": {"effects_quality": 99}})["settings"][
            "effects_quality"
        ]
        == "medium"
    )
    assert SaveStore.defaults()["settings"]["screen_shake"] is False


@pytest.mark.parametrize("missing_all", (False, True))
def test_missing_art_does_not_crash_actual_game_render(renderer, content, tmp_path, missing_all):
    root = tmp_path / "assets"
    if not missing_all:
        shutil.copytree(ASSET_ROOT, root)
        (root / "actors/paladin.png").unlink()
    fallback = Renderer(content, root)
    sim = Simulation(content)
    sim.step(FIXED_DT)
    fallback.draw_game(sim)
    assert fallback.assets.warnings
    assert fallback.canvas.get_size() == (1280, 720)


def test_shipped_raster_metadata_and_walk_anchors_are_valid():
    from scripts.validate_assets import validate

    assert validate() == []


def test_boss_animations_continue_after_campaign_clock_stops(renderer, content):
    sim = Simulation(content)
    sim.time = 1800
    sim.spawn_boss()
    sim.player.invulnerable = True
    sim.step(FIXED_DT, Vector2(1, 0))
    renderer.draw_game(sim)
    before = renderer.presentation.previous_time
    for _ in range(60):
        sim.step(FIXED_DT, Vector2(1, 0))
    renderer.draw_game(sim)
    assert sim.time == 1800 and renderer.presentation.previous_time > before
    assert renderer.presentation.previous_time == pytest.approx(sim.elapsed)
    state, clock = renderer.presentation.player_state(sim)
    assert state == "walk" and clock > 1800
