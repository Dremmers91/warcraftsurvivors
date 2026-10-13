"""Capture staged wave/encounter/result screens in a private profile, separate from full-run proof."""

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
from warcraft_survivors.simulation import FIXED_DT  # noqa: E402


def main():
    output = ROOT / "docs/screenshots/milestone3"
    output.mkdir(parents=True, exist_ok=True)
    app = App(
        SaveStore(ROOT / f"artifacts/milestone3/capture-save-{time.time_ns()}/save.json"), seed=47
    )

    def capture(name):
        if app.sim:
            app.sim.grid.rebuild(app.sim.enemies)
        app.draw()
        pygame.image.save(app.renderer.canvas, str(output / f"{name}.png"))

    for seconds, name, count in ((60, "early", 18), (900, "midgame", 110), (1740, "late", 380)):
        app.start_run()
        sim = app.sim
        sim.debug_used = True
        sim.time = seconds
        sim.wave_index = int(seconds // 60)
        pool, _weights = sim.spawner.pool(seconds)
        for i in range(count):
            kind = pool[i % len(pool)]
            enemy = sim.spawn(
                kind, sim.player.pos + Vector2(150 + (i % 9) * 40, 0).rotate(i * 137.5)
            )
            enemy.health = enemy.max_health
        capture(name)
    app.start_run()
    sim = app.sim
    sim.debug_used = True
    sim.time = 900
    for i, eid in enumerate(app.content.elites):
        elite = sim.spawn_elite(eid)
        elite.pos = sim.player.pos + (Vector2(210, 90), Vector2(-170, 120), Vector2(-190, -60))[i]
        sim.enemy_combat.begin(elite, app.content.elites[eid].attacks[0])
    capture("elites")
    app.start_run()
    sim = app.sim
    sim.debug_used = True
    sim.player.spells["judgment"] = SpellState(8)
    sim.player.passives = {"projectiles": 1}
    sim.drop(sim.player.pos, "chest", 1)
    sim.collect_pickups(FIXED_DT)
    app.goto("level")
    capture("evolution")
    for aid in app.content.bosses["hogger"].attacks:
        app.start_run()
        sim = app.sim
        sim.debug_used = True
        sim.time = 1800
        boss = sim.spawn_boss()
        boss.pos = sim.player.pos + Vector2(160, 0)
        boss.health = boss.max_health * 0.45
        boss.enraged = True
        sim.enemy_combat.begin(boss, aid)
        capture(aid)
    reports = []
    for won in (False, True):
        app.start_run()
        sim = app.sim
        sim.time = 1800
        sim.boss_time = 70
        sim.kills, sim.elites, sim.evolved = 24000, 5, 4
        sim.gold, sim.class_xp_kills = 2600, 38000
        boss = sim.spawn_boss()
        if won:
            boss.health = 0
            sim.collect_dead()
        else:
            sim.player.health = 0
        app.update(FIXED_DT, Vector2())
        assert app.screen == "results" and sim.won == won
        reports.append(dict(outcome=sim.outcome, result=app.result, boss=sim.boss_result))
        capture("victory" if won else "death")
    (ROOT / "artifacts/milestone3/screens.json").write_text(
        json.dumps(
            dict(
                note="Staged scenarios and counters; private profile; not full-run evidence",
                results=reports,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    pygame.quit()
    print(
        "Staged early/mid/late, three elites, evolution, four boss tells, death/victory screens captured."
    )


if __name__ == "__main__":
    main()
