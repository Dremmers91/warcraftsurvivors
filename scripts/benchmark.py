"""Measure six-class builds, including enemy obstacle/separation work."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame  # noqa: E402
from pygame import Vector2  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.entities import SpellState  # noqa: E402
from warcraft_survivors.rendering import Renderer  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT, Simulation  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enemies", type=int, default=400)
    parser.add_argument("--frames", type=int, default=300)
    parser.add_argument("--quality", choices=("low", "medium", "high"), default="medium")
    parser.add_argument("--class", dest="class_id", default="paladin")
    parser.add_argument("--zone", default="elwynn")
    parser.add_argument("--track-collisions", action="store_true")
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--complete-loadout", action="store_true")
    parser.add_argument("--time", type=float, default=1740)
    parser.add_argument("--output", type=Path, default=Path("artifacts/milestone5/performance"))
    args = parser.parse_args()
    pygame.init()
    pygame.display.set_mode((1920, 1080))
    content = load_content()
    renderer = Renderer(content)
    renderer.quality = args.quality
    sim = Simulation(content, args.class_id, seed=47, zone_id=args.zone)
    sim.grid.track_queries = sim.world.grid.track_queries = args.track_collisions
    sim.time = max(0, min(1740, args.time))
    sim.director.seek(sim.time)
    sim.spawner.wave_start = sim.director.wave(sim.time).start
    sim.wave_index = int(sim.time // 60)
    sim.player.spells[next(iter(sim.player.spells))].rank = 8
    if args.complete_loadout:
        ids = content.classes[args.class_id].abilities[:8]
        if args.class_id == "hunter":
            ids = (
                content.classes[args.class_id].abilities[:6]
                + content.classes[args.class_id].abilities[8:]
            )
        sim.player.spells = {aid + "_evolved": SpellState(8) for aid in ids}
    sim.player.passives = {"might": 5, "area": 5, "projectiles": 5}
    if args.complete_loadout:
        sim.player.passives.update(haste=5, duration=5, velocity=5, piercing=5, armor=5)
    sim.player.invulnerable = True
    sim.spawner.timer = 10**9
    for index in range(args.enemies):
        radius = 160 + math.sqrt(index / max(1, args.enemies)) * 650
        enemy = sim.spawn(pos=sim.player.pos + Vector2(radius, 0).rotate_rad(index * 2.39996))
        enemy.health = enemy.max_health = 10**9
    measured = []
    checks = []
    destination = pygame.Surface((1920, 1080))
    for frame in range(args.frames + 30):
        start = time.perf_counter()
        sim.step(FIXED_DT)
        middle = time.perf_counter()
        renderer.draw_game(sim)
        # Renderer follows HUD visibility; benchmark instrumentation is explicit.
        sim.grid.track_queries = sim.world.grid.track_queries = args.track_collisions
        pygame.transform.scale(renderer.canvas, (1920, 1080), destination)
        end = time.perf_counter()
        sim.sound_events.clear()
        if frame >= 30:
            measured.append(((middle - start) * 1000, (end - middle) * 1000))
            checks.append(sim.grid.candidate_checks + sim.world.grid.candidate_checks)
    combined = [simulation + render for simulation, render in measured]
    result = {
        "enemies": len(sim.enemies),
        "frames": args.frames,
        "resolution": "1920x1080",
        "quality": args.quality,
        "wave_time": args.time,
        "hostile_projectiles": len(sim.enemy_combat.projectiles),
        "telegraphs": len(sim.enemy_combat.attacks),
        "class": args.class_id,
        "zone": args.zone,
        "complete_loadout": args.complete_loadout,
        "projectiles": len(sim.projectiles),
        "fields": len(sim.combat.fields),
        "companions": len(sim.combat.companions),
        "particles": len(renderer.presentation.particles.active),
        "xp_gems": sum(p.kind == "xp" for p in sim.pickups.values()),
        "spatial_candidate_checks_mean": round(statistics.mean(checks)),
        "collision_metrics_enabled": args.track_collisions,
        "simulation_mean_ms": round(statistics.mean(s for s, _ in measured), 2),
        "render_mean_ms": round(statistics.mean(r for _, r in measured), 2),
        "combined_mean_ms": round(statistics.mean(combined), 2),
        "combined_p95_ms": round(sorted(combined)[int(len(combined) * 0.95)], 2),
        "note": "Dummy SDL; maximum ranks; immortal test entities; CPU measurement, not hardware FPS",
    }
    output = (
        args.output
        / f"benchmark-{args.zone}-{args.class_id}-{args.enemies}-{args.quality}-{args.complete_loadout}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), "utf-8")
    if args.capture:
        pygame.image.save(renderer.canvas, output.with_suffix(".png"))
    print(json.dumps(result, indent=2))
    pygame.quit()


if __name__ == "__main__":
    main()
