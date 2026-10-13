import sys

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.app import App
from warcraft_survivors.debug import DebugTools, debug_allowed
from warcraft_survivors.persistence import SaveStore
from warcraft_survivors.simulation import FIXED_DT, Simulation


@pytest.mark.parametrize(
    "key", (pygame.K_F3, pygame.K_F4, pygame.K_F5, pygame.K_F6, pygame.K_F7, pygame.K_F8)
)
def test_debug_is_disabled_by_default_and_in_release(content, key):
    for tools in (DebugTools(), DebugTools(True, release=True)):
        sim = Simulation(content)
        assert not tools.handle(key, sim)
        assert tools.speed == 1 and not tools.overlay
        assert (
            sim.time == 0 and sim.player.xp == 0 and not sim.enemies and not sim.player.invulnerable
        )


def test_packaged_gate_cannot_be_enabled(monkeypatch, content):
    tools = DebugTools(True)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert not debug_allowed(True)
    assert not DebugTools(True).enabled
    assert not tools.handle(pygame.K_F8, Simulation(content))


def test_all_debug_actions_and_reset(tmp_path):
    app = App(SaveStore(tmp_path / "save.json"), debug=True)
    app.start_run()
    sim = app.sim
    app.menu_key(pygame.K_F8)
    assert sim.player.invulnerable
    app.menu_key(pygame.K_F4)
    app.update(FIXED_DT, Vector2())
    assert sim.time == pytest.approx(FIXED_DT * 2)
    app.menu_key(pygame.K_F6)
    assert len(sim.enemies) >= 10
    app.menu_key(pygame.K_F7)
    assert not sim.enemies and sim.kills >= 10 and sim.pickups
    app.menu_key(pygame.K_F5)
    assert app.screen == "level" and sim.player.level == 2
    app.choose(0)
    app.end_run()
    assert not app.result["recorded"] and app.save.data["stats"]["runs"] == 0
    app.start_run()
    assert not app.sim.player.invulnerable and app.debug.speed == 1
    pygame.quit()
