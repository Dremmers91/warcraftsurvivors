"""Capture native talent states and supported-resolution output using private profiles."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pygame  # noqa: E402

from warcraft_survivors.app import App  # noqa: E402
from warcraft_survivors.meta import load_progression  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402


def main():
    out = ROOT / "artifacts/talent-trees/screenshots"
    out.mkdir(parents=True, exist_ok=True)
    selected = ROOT / "docs/screenshots/talent-trees"
    selected.mkdir(parents=True, exist_ok=True)
    app = App(SaveStore(ROOT / "artifacts/talent-trees/capture/save.json"))
    evidence = []
    for cid, tree in load_progression().trees.items():
        for state in ("fresh", "partial", "maxed"):
            app.save.data = SaveStore.defaults()
            c = app.save.data["classes"][cid]
            if state != "fresh":
                c["xp"] = 60 * 50 * 49
                for t in tree.values():
                    if state == "partial" and t.tier >= 2:
                        break
                    c["talents"][t.id] = t.max_rank if state == "maxed" else 1
            app.save.data = SaveStore.validate(app.save.data)
            app.selected_class = cid
            app.goto("talents")
            if state == "partial":
                app.focus = list(tree).index("technique")
            app.draw()
            assert not app.renderer.assets.warnings
            assert len(app.buttons) == len(tree) + 5
            name = f"{cid}-{state}.png"
            pygame.image.save(app.renderer.canvas, str(out / name))
            if state == "partial":
                pygame.image.save(app.renderer.canvas, str(selected / name))
            evidence.append(
                dict(class_id=cid, state=state, nodes=len(tree), points=app.save.talent_points(cid))
            )
    for resolution in ("1280x720", "1600x900", "1920x1080", "2560x1440"):
        app.save.data["settings"]["resolution"] = resolution
        app.apply_display()
        app.draw()
        pygame.image.save(app.display, str(out / f"resolution-{resolution}.png"))
    report = ROOT / "artifacts/talent-trees/visual-smoke.json"
    report.write_text(
        json.dumps(
            dict(
                cases=evidence,
                resolutions=4,
                note="Staged private profiles; real App/renderer, not earned progression or a human controller test.",
            ),
            indent=2,
        )
        + "\n",
        "utf-8",
    )
    pygame.quit()
    print("Verified six trees × three allocation states, plus four supported resolutions")


if __name__ == "__main__":
    main()
