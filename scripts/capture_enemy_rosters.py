"""Review every zone roster at native gameplay zoom, using the real renderer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame  # noqa: E402
from pygame import Vector2  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.rendering import CREAM, Renderer  # noqa: E402
from warcraft_survivors.simulation import Simulation  # noqa: E402


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1280, 720))
    content = load_content()
    renderer = Renderer(content)
    output = ROOT / "artifacts/enemy-balance/rosters"
    output.mkdir(parents=True, exist_ok=True)
    for zone in content.zones.values():
        sim = Simulation(content, zone_id=zone.id)
        # Clear only the staged review area so terrain can neither occlude an
        # asset nor displace a labeled creature. This fixture never saves.
        area = pygame.Rect(
            round(sim.camera.pos.x + 140), round(sim.camera.pos.y + 130), 940, 490
        ).inflate(500, 500)
        sim.world.obstacles[:] = [o for o in sim.world.obstacles if not area.collidepoint(o.pos)]
        sim.world.grid.rebuild(sim.world.obstacles)
        sim.player.pos.update(sim.camera.pos + Vector2(1100, 420))
        labels = []
        for index, eid in enumerate(zone.enemies):
            pos = Vector2(230 + (index % 4) * 230, 240 + (index // 4) * 100)
            sim.spawn(eid, sim.camera.pos + pos)
            labels.append((content.enemies[eid].name, pos + Vector2(0, 20)))
        for index, elite_id in enumerate(zone.elites):
            enemy = sim.spawn_elite(elite_id)
            pos = Vector2(260 + index * 310, 560)
            enemy.pos.update(sim.camera.pos + pos)
            labels.append((content.elites[elite_id].name, pos + Vector2(0, 20)))
        sim.messages.clear()
        sim.grid.rebuild(sim.enemies)
        renderer.chunks.clear()
        renderer.draw_game(sim)
        for name, pos in labels:
            renderer.text(name, pos, 19, CREAM, True)
        pygame.image.save(renderer.canvas, output / f"{zone.id}.png")
        assert not renderer.assets.warnings, renderer.assets.warnings
    pygame.quit()


if __name__ == "__main__":
    main()
