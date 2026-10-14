from collections import defaultdict
from typing import cast

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.app import App
from warcraft_survivors.meta import load_progression
from warcraft_survivors.persistence import SaveStore
from warcraft_survivors.simulation import FIXED_DT


@pytest.fixture
def app(tmp_path):
    game = App(SaveStore(tmp_path / "save.json"), seed=1)
    yield game
    pygame.quit()


def test_keyboard_menu_pause_level_and_results(app):
    app.menu_key(pygame.K_RETURN)
    assert app.screen == "classes"
    app.menu_key(pygame.K_RETURN)
    assert app.screen == "game"
    app.menu_key(pygame.K_ESCAPE)
    app.update(1)
    assert app.screen == "pause" and app.sim.time == 0
    app.menu_key(pygame.K_RETURN)
    app.sim.player.xp = app.sim.player.xp_required
    app.update(FIXED_DT)
    assert app.screen == "level" and len(app.buttons) == 3
    app.menu_key(pygame.K_ESCAPE)
    assert app.screen == "level"
    app.menu_key(pygame.K_1)
    assert app.screen == "game"
    app.end_run()
    app.end_run()
    assert app.screen == "results" and app.save.data["stats"]["runs"] == 1


def test_mouse_and_controller_menu_events(app):
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(140, 354)))
    assert app.screen == "classes"
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
    assert app.screen == "game"
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=7))
    assert app.screen == "pause"
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
    assert app.screen == "game"


def test_keyboard_mouse_and_stick_switch_during_game(app, monkeypatch):
    app.start_run()
    keys = defaultdict(bool)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: keys)
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (False, False, False))
    keys[pygame.K_w] = True
    assert app.movement() == Vector2(0, -1)
    keys.clear()
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (True, False, False))
    pointer = app.sim.player.pos - app.sim.camera.pos + Vector2(100, 0)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (round(pointer.x), round(pointer.y)))
    assert app.movement() == Vector2(1, 0)
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (False, False, False))

    class Stick:
        def get_numaxes(self):
            return 2

        def get_axis(self, index):
            return (0, 1)[index]

    app.joysticks[1] = cast(pygame.joystick.JoystickType, Stick())
    assert app.movement() == Vector2(0, 1)


def test_frame_accumulator_and_focus_loss(app):
    app.start_run()
    start = app.sim.player.pos.copy()
    for _ in range(30):
        app.update(1 / 30, Vector2(1, 1))
    assert app.sim.time == pytest.approx(1)
    assert app.sim.player.pos.distance_to(start) == pytest.approx(215)
    app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert app.screen == "pause"


@pytest.mark.parametrize(
    "screen", ("main", "classes", "game", "pause", "level", "settings", "results")
)
def test_each_screen_renders_at_full_hd(app, screen):
    app.display = pygame.display.set_mode((1920, 1080))
    app.start_run()
    if screen == "level":
        app.sim.player.xp = app.sim.player.xp_required
        app.sim.level_check()
    if screen == "results":
        app.end_run()
    else:
        app.goto(screen)
    app.draw()
    assert app.viewport.size == (1920, 1080)


@pytest.mark.parametrize("victory", (False, True))
def test_campaign_results_save_once_and_render_complete_results(app, victory):
    app.select_class("mage")
    sim = app.sim
    sim.time = 1800
    sim.boss_time = 12
    sim.kills, sim.elites, sim.evolved = 100, 3, 1
    sim.gold, sim.class_xp_kills = 80, 700
    boss = sim.spawn_boss()
    if victory:
        boss.health = 0
        sim.collect_dead()
    else:
        sim.player.health = 0
    app.update(FIXED_DT, Vector2())
    assert sim.won == victory and app.screen == "results"
    assert sim.boss_result == ("defeated" if victory else "alive")
    assert app.result["recorded"] and app.result["gold"] > 80
    assert app.result["class_xp"] >= 1000
    assert app.save.data["classes"]["mage"]["xp"] == app.result["class_xp"]
    before = app.save.data["gold"]
    app.end_run()
    assert app.save.data["gold"] == before and app.save.data["stats"]["runs"] == 1
    app.draw()
    loaded = SaveStore(app.save.path)
    assert loaded.data["stats"]["wins"] == int(victory)


def test_developer_time_entry_pauses_then_resumes_live_simulation(app):
    from warcraft_survivors.debug import DebugTools

    app.debug = DebugTools(True)
    app.start_run()
    app.menu_key(pygame.K_t)
    app.update(0.1, Vector2(1, 0))
    assert app.sim.time == 0
    for key in (pygame.K_1, pygame.K_0, pygame.K_COLON, pygame.K_0, pygame.K_0, pygame.K_RETURN):
        app.menu_key(key)
    assert app.sim.time == 600 and app.screen == "game" and app.sim.debug_used
    app.update(FIXED_DT, Vector2())
    assert app.sim.time > 600


def test_progression_purchases_confirm_cancel_and_controller_navigation(app):
    app.save.data["gold"] = 100
    app.goto("shop")
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 250)))
    assert app.screen == "confirm" and "65 gold" in app.progression_ui.confirmation.body
    assert app.focus == 1
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
    assert app.screen == "shop" and app.save.data["gold"] == 100
    app.menu_key(pygame.K_RETURN)
    app.handle_event(pygame.event.Event(pygame.JOYHATMOTION, hat=0, value=(-1, 0)))
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
    assert (
        app.screen == "shop"
        and app.save.data["gold"] == 35
        and app.save.data["shared"]["health"] == 1
    )
    app.selected_class = "paladin"
    app.start_run()
    assert app.sim.player.max_health == pytest.approx(135 * 1.03)
    before = app.save.data["gold"]
    app.goto("shop")
    assert app.screen == "game" and app.save.data["gold"] == before


def test_talent_respec_requires_visible_confirmation_and_refunds_only_points(app):
    app.save.data["classes"]["hunter"]["xp"] = 360
    app.save.data["gold"] = 100
    app.selected_class = "hunter"
    app.goto("talents")
    app.menu_key(pygame.K_RETURN)
    assert (
        app.screen == "confirm"
        and "one available talent point" in app.progression_ui.confirmation.body
    )
    app.menu_key(pygame.K_LEFT)
    app.menu_key(pygame.K_RETURN)
    assert app.save.data["classes"]["hunter"]["talents"] == {"might": 1}
    app.progression_ui.respec(app)
    assert app.screen == "confirm" and "55 gold" in app.progression_ui.confirmation.body
    app.menu_key(pygame.K_ESCAPE)
    assert app.save.data["gold"] == 100 and app.save.talent_points("hunter") == 1
    app.progression_ui.respec(app)
    app.menu_key(pygame.K_LEFT)
    app.menu_key(pygame.K_RETURN)
    assert app.save.data["gold"] == 45 and app.save.talent_points("hunter") == 2
    assert app.save.data["classes"]["hunter"]["xp"] == 360
    app.draw()


def test_all_progression_screens_four_cards_and_reroll_draw_without_missing_assets(app):
    from warcraft_survivors.meta import load_progression

    app.save.data["gold"] = 10000
    app.save.data["shared"] = {"health": 5, "might": 3, "choices": 1, "rerolls": 2}
    app.selected_class = "hunter"
    app.save.data["classes"]["hunter"]["xp"] = 100000
    for t in load_progression().trees["hunter"].values():
        for _ in range(t.max_rank):
            assert app.save.buy_talent("hunter", t.id)
    for screen in ("progression", "talents", "shop", "achievements", "unlocks", "starting"):
        app.goto(screen)
        app.draw()
        app.menu_key(pygame.K_TAB)
        app.draw()
    app.progression_ui.shop_page = 1
    app.goto("shop")
    app.draw()
    for page in range(4):
        app.progression_ui.achievement_page = page
        app.goto("achievements")
        app.draw()
    app.select_class("hunter")
    app.sim.player.xp = app.sim.player.xp_required
    app.update(FIXED_DT, Vector2())
    assert app.screen == "level" and len(app.sim.choices) == 4
    app.draw()
    remaining = app.sim.rerolls
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=2))
    assert app.sim.rerolls == remaining - 1
    app.menu_key(pygame.K_4)
    assert app.screen == "game"
    assert not app.renderer.assets.warnings


def test_talent_grid_arrows_and_controller_preserve_spatial_navigation(app):
    tree = list(load_progression().trees["paladin"])
    app.goto("talents")
    app.menu_key(pygame.K_DOWN)
    assert tree[app.focus] == "duration"
    app.menu_key(pygame.K_RIGHT)
    assert tree[app.focus] == "area"
    app.handle_event(pygame.event.Event(pygame.JOYHATMOTION, hat=0, value=(0, 1)))
    assert tree[app.focus] == "haste"
    app.menu_key(pygame.K_LEFT)
    assert tree[app.focus] == "might"


def test_confirmation_revalidates_available_gold_before_purchasing(app):
    app.save.data["gold"] = 100
    app.goto("shop")
    app.menu_key(pygame.K_RETURN)
    assert app.screen == "confirm"
    app.save.data["gold"] = 0
    app.menu_key(pygame.K_LEFT)
    app.menu_key(pygame.K_RETURN)
    assert (
        app.screen == "shop"
        and not app.save.data["shared"].get("health")
        and app.save.data["gold"] == 0
    )
