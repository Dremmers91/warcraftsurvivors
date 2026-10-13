"""Bounded automated prototype soak. The harness enables invulnerability only here."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pygame import Vector2  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT, Simulation  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=120)
    args = parser.parse_args()
    sim = Simulation(load_content(), seed=47)
    sim.player.invulnerable = True
    for tick in range(60 * args.seconds):
        while sim.choices:
            sim.choose(0)
        goal = Vector2(4096, 4096) + Vector2(330, 0).rotate(tick / 60 * 18)
        delta = goal - sim.player.pos
        sim.step(FIXED_DT, delta.normalize() if delta.length_squared() > 1 else Vector2())
        sim.sound_events.clear()
    report = {
        "timer": sim.time,
        "kills": sim.kills,
        "level": sim.player.level,
        "enemies": len(sim.enemies),
        "note": "Invulnerable automated player; not a balance test",
    }
    assert sim.kills > 0 and sim.player.level > 1 and not sim.finished
    output = Path("artifacts/milestone1/soak.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), "utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
