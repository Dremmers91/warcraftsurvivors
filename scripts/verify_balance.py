"""Bounded fresh early dodging and advanced stationary horde probes; explicit QA fixtures."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pygame import Vector2  # noqa: E402
from verify_full_run import choose, movement  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.entities import SpellState  # noqa: E402
from warcraft_survivors.meta import load_progression  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT, Simulation  # noqa: E402


def advanced_profile(path):
    save = SaveStore(path)
    save.data["gold"] = 100000
    for cls in save.data["classes"].values():
        cls["xp"] = 120000
    for cid, tree in load_progression().trees.items():
        for talent in tree.values():
            for _ in range(talent.max_rank):
                assert save.buy_talent(cid, talent.id)
    for sid, upgrade in load_progression().shared.items():
        for _ in range(upgrade.max_rank):
            assert save.buy_shared(sid)
    return save


def main():
    out = ROOT / "artifacts/milestone5/balance"
    out.mkdir(parents=True, exist_ok=True)
    content = load_content()
    report = []
    for cid in content.classes:
        for moving in (False, True):
            sim = Simulation(content, cid, seed=47)
            lowest = sim.player.health
            for tick in range(180 * 60):
                while sim.choices:
                    choose(sim)
                sim.step(FIXED_DT, movement(sim, tick) if moving else Vector2())
                sim.sound_events.clear()
                lowest = min(lowest, sim.player.health)
                if sim.finished:
                    break
            row = dict(
                class_id=cid,
                fixture="fresh",
                moving=moving,
                elapsed=round(sim.elapsed, 2),
                health=round(sim.player.health, 2),
                lowest_health=round(lowest, 2),
                level=sim.player.level,
                kills=sim.kills,
                outcome=sim.outcome,
            )
            report.append(row)
            print(json.dumps(row), flush=True)
    save = advanced_profile(out / f"advanced-{time.time_ns()}/save.json")
    (out / "advanced-profile.json").write_text(json.dumps(save.data, indent=2), encoding="utf-8")
    for cid in content.classes:
        sim = Simulation(content, cid, seed=47, permanent=save.loadout(cid))
        sim.time = 1740
        sim.director.seek(sim.time)
        sim.wave_index = 29
        sim.spawner.wave_start = 1740
        # Staged developed arsenal: legal maximum eight spells and eight passives.
        ids = content.classes[cid].abilities[:8]
        sim.player.spells = {aid + "_evolved": SpellState(8) for aid in ids}
        sim.player.passives = dict(
            might=5, area=5, projectiles=5, haste=5, armor=5, regen=5, duration=5, piercing=5
        )
        starthealth = sim.player.health
        for index in range(1200):
            sim.spawn(pos=sim.player.pos + Vector2(250 + index % 300, 0).rotate(index * 137.5))
        for _ in range(20 * 60):
            while sim.choices:
                choose(sim)
            sim.step(FIXED_DT)
            sim.sound_events.clear()
            if sim.finished:
                break
        row = dict(
            class_id=cid,
            fixture="advanced staged 29:00; eight Rank 8 evolved spells and eight passives",
            moving=False,
            seconds=20,
            kills=sim.kills,
            health=round(sim.player.health, 2),
            starting_health=round(starthealth, 2),
            alive=not sim.finished,
            remaining_enemies=len(sim.enemies),
        )
        report.append(row)
        print(json.dumps(row), flush=True)
    (out / "probes.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
