"""Real early play and staged late builds, isolated from ordinary player saves."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pygame import Vector2  # noqa: E402
from verify_balance import advanced_profile  # noqa: E402
from verify_full_run import choose, movement  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.entities import SpellState  # noqa: E402
from warcraft_survivors.meta import load_progression  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT, Simulation  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/enemy-balance/probes")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    content = load_content()
    advanced = advanced_profile(args.output / f"qa-advanced-{time.time_ns()}/save.json")
    middle = SaveStore(args.output / f"qa-middle-{time.time_ns()}/save.json")
    middle.data["gold"] = 30000
    for cls in middle.data["classes"].values():
        cls["xp"] = 15000
    meta = load_progression()
    for cid, tree in meta.trees.items():
        for talent in tree.values():
            for _ in range(min(2, talent.max_rank)):
                middle.buy_talent(cid, talent.id)
    for sid, upgrade in meta.shared.items():
        if not upgrade.achievement:
            for _ in range(min(2, upgrade.max_rank)):
                middle.buy_shared(sid)
    report = []

    def play(sim: Simulation, seconds: int, moving: bool) -> dict:
        start = sim.elapsed
        maximum = len(sim.enemies)
        for tick in range(seconds * 60):
            while sim.choices:
                choose(sim)
            sim.step(FIXED_DT, movement(sim, tick) if moving else Vector2())
            sim.sound_events.clear()
            maximum = max(maximum, len(sim.enemies))
            if sim.finished:
                break
        return dict(
            class_id=sim.class_id,
            zone=sim.zone.id,
            seconds=round(sim.elapsed - start, 2),
            moving=moving,
            alive=not sim.finished,
            health=round(sim.player.health, 1),
            level=sim.player.level,
            kills=sim.kills,
            enemies=len(sim.enemies),
            peak_enemies=maximum,
            xp_collected=round(sim.run_xp_collected),
            gems=sum(p.kind == "xp" for p in sim.pickups.values()),
            companions=len(sim.combat.companions),
            class_xp=sim.class_xp_kills,
        )

    for cid in content.classes:
        for moving in (False, True):
            row = play(Simulation(content, cid, seed=47), 180, moving)
            row["fixture"] = "fresh legal early play"
            report.append(row)
            print(json.dumps(row), flush=True)
    for zid in content.zones:
        for cid in content.classes:
            for label, profile in (("fresh", None), ("middle", middle), ("advanced", advanced)):
                sim = Simulation(
                    content,
                    cid,
                    seed=47,
                    zone_id=zid,
                    permanent=profile.loadout(cid) if profile else None,
                )
                sim.time = 1740
                sim.director.seek(sim.time)
                sim.wave_index = 29
                sim.spawner.wave_start = 1740
                ids = content.classes[cid].abilities[:8]
                if cid == "hunter":
                    ids = content.classes[cid].abilities[:6] + content.classes[cid].abilities[8:]
                # Same developed in-run arsenal isolates permanent strength.
                sim.player.spells = {aid + "_evolved": SpellState(8) for aid in ids}
                sim.player.passives = dict(
                    might=5,
                    area=5,
                    projectiles=5,
                    haste=5,
                    armor=5,
                    regen=5,
                    duration=5,
                    piercing=5,
                )
                for index in range(1600):
                    sim.spawn(
                        pos=sim.player.pos + Vector2(250 + index % 500, 0).rotate(index * 137.5)
                    )
                row = play(sim, 20, False)
                row["fixture"] = f"{label} permanent profile; staged developed arsenal at 29:00"
                report.append(row)
                print(json.dumps(row), flush=True)
    (args.output / "probes.json").write_text(json.dumps(report, indent=2) + "\n", "utf-8")


if __name__ == "__main__":
    main()
