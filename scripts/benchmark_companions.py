"""Measure companion combat independently from enemy AI/rendering, sequentially."""

from __future__ import annotations

import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pygame import Vector2  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.entities import SpellState  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT, Simulation  # noqa: E402


def main():
    content = load_content()
    rows = []
    for enemies in (1000, 6000):
        for cid, aid in (
            ("hunter", ""),
            ("hunter", "beast_companion_evolved"),
            ("warlock", "summon_felguard_evolved"),
        ):
            sim = Simulation(content, cid, seed=47)
            sim.player.spells = {aid: SpellState(8)} if aid else {}
            sim.player.passives = {
                pid: 5 for pid in ("might", "haste", "area", "velocity", "projectiles")
            }
            for index in range(enemies):
                radius = 160 + math.sqrt(index / enemies) * 650
                e = sim.spawn(
                    "bandit", sim.player.pos + Vector2(radius, 0).rotate_rad(index * 2.39996)
                )
                e.health = e.max_health = 10**9
            sim.grid.rebuild(sim.enemies)
            samples = []
            for frame in range(180):
                start = time.perf_counter()
                sim.combat.update(FIXED_DT)
                end = time.perf_counter()
                sim.visuals.clear()
                sim.sound_events.clear()
                if frame >= 60:
                    samples.append((end - start) * 1000)
            rows.append(
                dict(
                    enemies=enemies,
                    ability=aid or "empty combat baseline",
                    pets=len(sim.combat.companions),
                    mean_ms=round(statistics.mean(samples), 3),
                    p95_ms=round(sorted(samples)[int(len(samples) * 0.95)], 3),
                )
            )
    out = ROOT / "artifacts/pets-summons/performance/companion-combat.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    result = dict(
        note="Sequential 120 measured fixed combat updates after 60 warmup frames; max ranks/passives, immortal stationary foes. Includes projectile collision, splash/burning and status processing; excludes enemy AI, grid rebuild and rendering. CPU time, not display FPS.",
        cases=rows,
    )
    out.write_text(json.dumps(result, indent=2) + "\n", "utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
