"""Three-process real failed-run -> confirmed upgrade -> reopen integration proof."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame  # noqa: E402
from pygame import Vector2  # noqa: E402
from verify_full_run import movement as probe_movement  # noqa: E402

from warcraft_survivors.app import App  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("earn", "purchase", "reopen"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or ROOT / f"artifacts/milestone5/loop-{time.time_ns()}"
    output.mkdir(parents=True, exist_ok=True)
    if not args.phase:
        for phase in ("earn", "purchase", "reopen"):
            subprocess.run(
                [sys.executable, str(Path(__file__)), "--phase", phase, "--output", str(output)],
                cwd=ROOT,
                check=True,
                timeout=120,
            )
        report = {
            phase: json.loads((output / f"{phase}.json").read_text(encoding="utf-8"))
            for phase in ("earn", "purchase", "reopen")
        }
        report["note"] = (
            "Three separate application processes; real deaths, legal cards, no debug grants/invulnerability/preloaded progression."
        )
        (ROOT / "artifacts/milestone5/loop.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        return
    save = SaveStore(output / "save.json")
    save.data["settings"]["sound"] = False
    app = App(save, seed=47)
    if args.phase == "earn":
        runs = []
        for _attempt in range(6):
            app.start_run()
            sim = app.sim
            for _tick in range(600 * 60):
                if app.screen == "level":

                    def survival_card(i, choices=sim.choices):
                        card = choices[i]
                        if card.kind == "manual":
                            return 100
                        values = {
                            "movement": 80,
                            "pickup": 75,
                            "velocity": 70,
                            "duration": 65,
                            "health": 50,
                            "armor": 40,
                            "regen": 30,
                        }
                        return values.get(card.id, 0)

                    index = max(range(len(sim.choices)), key=survival_card)
                    app.menu_key(pygame.K_1 + index)
                app.update(FIXED_DT, probe_movement(sim, _tick) if _tick < 90 * 60 else Vector2())
                if sim.finished:
                    break
            if not sim.finished:
                raise RuntimeError("Stationary weak-attack build did not die within ten minutes")
            assert sim.outcome == "death" and not sim.debug_used and app.result["recorded"]
            runs.append(
                dict(
                    time=sim.elapsed,
                    kills=sim.kills,
                    level=sim.player.level,
                    earned_gold=app.result["gold"],
                    class_xp=app.result["class_xp"],
                )
            )
            app.draw()
            pygame.image.save(app.renderer.canvas, str(output / "death.png"))
            if save.data["gold"] >= 65:
                break
        assert save.data["gold"] >= 65
        result = dict(
            runs=runs,
            gold=save.data["gold"],
            class_xp=save.data["classes"]["paladin"]["xp"],
            save_version=save.data["version"],
        )
    elif args.phase == "purchase":
        before = save.data["gold"]
        before_xp = save.data["classes"]["paladin"]["xp"]
        app.goto("shop")
        app.menu_key(pygame.K_RETURN)
        assert app.screen == "confirm" and "65 gold" in app.progression_ui.confirmation.body
        app.draw()
        pygame.image.save(app.renderer.canvas, str(output / "purchase-confirmation.png"))
        app.menu_key(pygame.K_LEFT)
        app.menu_key(pygame.K_RETURN)
        assert save.data["gold"] == before - 65 and save.data["shared"]["health"] == 1
        assert save.data["classes"]["paladin"]["xp"] == before_xp
        result = dict(
            gold_before=before,
            gold_after=save.data["gold"],
            cost=65,
            shared=save.data["shared"],
            class_xp=before_xp,
        )
    else:
        app.start_run()
        sim = app.sim
        assert sim.player.max_health == 135 * 1.03 and len(sim.player.spells) == 1
        previous = json.loads((output / "purchase.json").read_text(encoding="utf-8"))
        assert (
            save.data["gold"] == previous["gold_after"]
            and save.data["classes"]["paladin"]["xp"] == previous["class_xp"]
        )
        app.draw()
        pygame.image.save(app.renderer.canvas, str(output / "reopened.png"))
        result = dict(
            upgrade_active=True,
            max_health=sim.player.max_health,
            base_health=135,
            shared_rank=save.data["shared"]["health"],
            starting_abilities=list(sim.player.spells),
            gold=save.data["gold"],
            class_xp=save.data["classes"]["paladin"]["xp"],
        )
        # QA preview is not another completed run.
        app.sim = None
    (output / f"{args.phase}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    app.quit()
    pygame.quit()
    print(json.dumps(dict(phase=args.phase, result=result)), flush=True)


if __name__ == "__main__":
    main()
