"""Capture staged UI/zone/boss artwork separately from the earned full-run proofs."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame  # noqa: E402
from pygame import Vector2  # noqa: E402

from warcraft_survivors.app import App  # noqa: E402
from warcraft_survivors.entities import SpellState  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402


def main():
    out = ROOT / "docs/screenshots/milestone5"
    out.mkdir(parents=True, exist_ok=True)
    app = App(SaveStore(ROOT / f"artifacts/milestone5/capture-{time.time_ns()}/save.json"), seed=47)

    def capture(name):
        if app.sim:
            app.sim.grid.rebuild(app.sim.enemies)
        app.draw()
        assert not app.renderer.assets.warnings
        pygame.image.save(app.renderer.canvas, str(out / f"{name}.png"))

    for screen in (
        "main",
        "classes",
        "zones",
        "settings",
        "progression",
        "shop",
        "talents",
        "achievements",
        "unlocks",
    ):
        app.goto(screen)
        capture(screen)
    for zid, zone in app.content.zones.items():
        app.sim = None
        app.selected_zone = zid
        app.start_run()
        sim = app.sim
        sim.debug_used = True
        sim.time = 900
        sim.wave_index = 15
        sim.director.seek(sim.time)
        sim.player.spells = {"judgment": SpellState(5), "consecration": SpellState(4)}
        sim.combat.update(0.016)
        for index in range(35):
            kind = zone.enemies[index % len(zone.enemies)]
            sim.spawn(
                kind, sim.player.pos + Vector2(130 + (index % 8) * 38, 0).rotate(index * 137.5)
            )
        capture(zid)
        for index, eid in enumerate(zone.elites):
            e = sim.spawn_elite(eid)
            e.pos = sim.world.resolve(
                sim.player.pos + Vector2(220, 0).rotate(index * 130), e.radius
            )
            sim.enemy_combat.begin(e, app.content.elites[eid].attacks[0])
        capture(zid + "-elites")
        sim.enemies = []
        sim.enemy_combat.attacks.clear()
        sim.time = 1800
        boss = sim.spawn_boss()
        boss.pos = sim.world.resolve(sim.player.pos + Vector2(200, 0), boss.radius)
        for aid in app.content.bosses[boss.boss_id].attacks:
            sim.enemy_combat.attacks.clear()
            sim.enemy_combat.begin(boss, aid)
            capture(aid)
        sim.messages.clear()
        capture(zid + "-boss")
        boss.health = 0
        sim.collect_dead()
        sim.finish("victory")
        app.end_run()
        capture(zid + "-victory")
    app.sim = None
    app.selected_zone = "icecrown"
    app.start_run()
    app.sim.player.health = 0
    app.sim.step(1 / 60)
    app.end_run()
    capture("death")
    app.sim = None
    app.selected_zone = "elwynn"
    app.start_run()
    app.sim.player.xp = app.sim.player.xp_required
    app.sim.level_check()
    app.goto("level")
    capture("level-cards")
    app.sim.choices.clear()
    app.sim.player.spells = {"judgment": SpellState(8)}
    app.sim.player.passives = {"projectiles": 1}
    app.sim.pending_chests = 1
    app.sim.level_check()
    app.goto("level")
    capture("evolution-cards")
    (out / "README.json").write_text(
        json.dumps(
            dict(
                note="Staged artwork/UI capture fixtures; not earned progress or full-run balance proof",
                screens=[p.name for p in out.glob("*.png")],
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    pygame.quit()
    print("Captured all zone, elite, boss telegraph, result and menu screens")


if __name__ == "__main__":
    main()
