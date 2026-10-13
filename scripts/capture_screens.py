"""Render the six milestone-one screens with a staged, isolated gameplay scene."""

import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame  # noqa: E402
from pygame import Vector2  # noqa: E402

from warcraft_survivors.app import App  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT  # noqa: E402

output = Path("artifacts/milestone1/screens")
output.mkdir(parents=True, exist_ok=True)
app = App(SaveStore(output / "qa-save.json"), seed=4)
app.start_run()
assert app.sim is not None
sim = app.sim
sim.player.invulnerable = True
sim.player.spells["judgment"].rank = 3
sim.player.passives = {"area": 1, "projectiles": 1}
sim.player.level = 4
for index in range(45):
    enemy = sim.spawn(pos=sim.player.pos + Vector2(160 + index * 9, 0).rotate(index * 137))
    enemy.health = enemy.max_health = 90
for _ in range(80):
    sim.step(FIXED_DT)
for screen in ("main", "game", "pause", "settings", "level", "results"):
    if screen == "level":
        sim.player.xp = sim.player.xp_required
        sim.level_check()
    if screen == "results":
        app.end_run()
    else:
        app.goto(screen)
    app.draw()
    pygame.image.save(app.renderer.canvas, str(output / f"{screen}.png"))
pygame.quit()
print(f"Captured six milestone-one screens in {output}")
