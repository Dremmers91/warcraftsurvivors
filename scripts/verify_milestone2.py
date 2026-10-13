"""Capture six class loadouts and decisions; run bounded six-class progression soaks."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame  # noqa: E402
from pygame import Vector2  # noqa: E402

from warcraft_survivors.app import App  # noqa: E402
from warcraft_survivors.entities import ManualState, SpellState  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT, Simulation  # noqa: E402
from warcraft_survivors.upgrades import eligible  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--screens-only", action="store_true")
    args = parser.parse_args()
    output = ROOT / "artifacts/milestone2/screens"
    output.mkdir(parents=True, exist_ok=True)
    app = App(SaveStore(ROOT / "artifacts/milestone2/private-save/save.json"), seed=47)
    app.goto("classes")
    app.draw()
    pygame.image.save(app.renderer.canvas, str(output / "classes.png"))
    reports = []
    for cid, cls in app.content.classes.items():
        sim = Simulation(app.content, cid, seed=47)
        sim.player.invulnerable = True
        for tick in range(0 if args.screens_only else 60 * args.seconds):
            while sim.choices:
                sim.choose(0)
            goal = Vector2(4096, 4096) + Vector2(180, 0).rotate(tick / 60 * 18)
            delta = goal - sim.player.pos
            sim.step(FIXED_DT, delta.normalize() if delta.length_squared() > 1 else Vector2())
            if tick % 30 == 0:
                sim.activate_manual()
            sim.sound_events.clear()
        reports.append(
            dict(
                class_id=cid,
                seconds=round(sim.time, 2),
                kills=sim.kills,
                level=sim.player.level,
                spells=list(sim.player.spells),
                manual=sim.player.manual.id if sim.player.manual else None,
                passives=sim.player.passives,
                enemies=len(sim.enemies),
            )
        )
        if not args.screens_only:
            assert sim.kills > 0 and sim.player.level > 1 and not sim.finished
        # Separate staged, immortal loadout screenshot; does not touch ordinary saves.
        app.select_class(cid)
        sim = app.sim
        assert sim is not None
        ids = list(cls.abilities[:8])
        if cid == "hunter":
            ids = list(cls.abilities[:6]) + list(cls.abilities[8:])
        sim.player.spells = {aid + "_evolved": SpellState(8) for aid in ids}
        sim.player.passives = {"area": 1, "projectiles": 1, "might": 1, "duration": 1}
        sim.player.manual = ManualState(cls.manuals[0], 2)
        sim.player.invulnerable = True
        sim.spawner.timer = 10000
        for index in range(60):
            e = sim.spawn(
                pos=sim.player.pos
                + Vector2(70 + math.sqrt(index / 60) * 360, 0).rotate(index * 137.5)
            )
            e.health = e.max_health = 10000
        for _tick in range(125):
            sim.step(FIXED_DT)
            sim.sound_events.clear()
        sim.activate_manual()
        app.draw()
        pygame.image.save(app.renderer.canvas, str(output / (cid + ".png")))
    app.select_class("paladin")
    sim = app.sim
    assert sim is not None
    sim.player.spells["judgment"].rank = 8
    sim.player.passives = {"projectiles": 1}
    sim.drop(sim.player.pos, "chest", 1)
    sim.collect_pickups(FIXED_DT)
    app.goto("level")
    app.draw()
    pygame.image.save(app.renderer.canvas, str(output / "evolution.png"))
    app.select_class("warlock")
    sim = app.sim
    assert sim is not None
    sim.choices = [
        next(c for c in eligible(app.content, "warlock", sim.player) if c.id == mid)
        for mid in app.content.classes["warlock"].manuals
    ]
    app.goto("level")
    app.draw()
    pygame.image.save(app.renderer.canvas, str(output / "manuals.png"))
    if not args.screens_only:
        (ROOT / "artifacts/milestone2/soak.json").write_text(
            json.dumps(
                {
                    "runs": reports,
                    "note": "Invulnerable deterministic harness; staged loadout screenshots; no balance or physical-controller claim",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    print(json.dumps(reports, indent=2))
    pygame.quit()


if __name__ == "__main__":
    main()
