"""Capture every progression screen and bounded staged talent-enabled gameplay."""

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
from warcraft_survivors.meta import load_progression  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT  # noqa: E402


def main():
    output = ROOT / "docs/screenshots/milestone4"
    output.mkdir(parents=True, exist_ok=True)
    save = SaveStore(ROOT / f"artifacts/milestone4/staged-{time.time_ns()}/save.json")
    save.data["gold"] = 100000
    for c in save.data["classes"].values():
        c["xp"] = 120000
    app = App(save, seed=47)

    def capture(name):
        app.notifications.clear()
        app.draw()
        pygame.image.save(app.renderer.canvas, str(output / f"{name}.png"))

    app.goto("progression")
    capture("class-progression")
    app.goto("unlocks")
    capture("locked-classes")
    for cid, tree in load_progression().trees.items():
        app.selected_class = cid
        for t in tree.values():
            for _ in range(t.max_rank):
                assert save.buy_talent(cid, t.id)
        app.goto("talents")
        app.focus = 15
        capture("talents-" + cid)
    for sid, u in load_progression().shared.items():
        for _ in range(u.max_rank):
            assert save.buy_shared(sid)
    for page in range(2):
        app.progression_ui.shop_page = page
        app.goto("shop")
        capture("shared-" + str(page + 1))
    app.selected_class = "hunter"
    app.goto("starting")
    capture("starting-choice")
    assert save.select_starting("hunter", "beast_companion")
    app.goto("talents")
    app.progression_ui.respec(app)
    capture("respec-confirmation")
    app.menu_key(pygame.K_ESCAPE)
    for cid in ("paladin", "mage", "hunter"):
        save.reward_run(cid, 10000, 20, 1800, True, 300, 10, 1000)
    for page in range(4):
        app.progression_ui.achievement_page = page
        app.goto("achievements")
        capture("achievements-" + str(page + 1))
    app.goto("unlocks")
    capture("earned-unlocks")
    app.toast("Rogue unlocked for a future release.")
    app.draw()
    pygame.image.save(app.renderer.canvas, str(output / "unlock-notification.png"))
    reports = []
    for cid in app.content.classes:
        app.selected_class = cid
        app.start_run()
        sim = app.sim
        sim.debug_used = True
        for tick in range(1200):
            if app.screen == "level":
                app.choose(0)
            app.update(FIXED_DT, Vector2(1, 0).rotate(tick / 8))
        reports.append(
            dict(
                class_id=cid,
                kills=sim.kills,
                starting_extra=save.data["classes"][cid]["starting_ability"],
                max_health=sim.player.max_health,
                abilities=list(sim.player.spells),
            )
        )
        sim.player.xp = sim.player.xp_required
        app.update(FIXED_DT, Vector2())
        assert len(sim.choices) == 4
        capture("four-cards-" + cid)
        sim.finish("abandoned")
        app.sim = None
    (ROOT / "artifacts/milestone4/staged.json").write_text(
        json.dumps(
            dict(
                note="Injected progression fixture and short staged gameplay, not a balance proof; no ordinary profile touched",
                runs=reports,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    assert not app.renderer.assets.warnings
    pygame.quit()
    print(
        "Captured six full talent trees, shop pages, 29 achievements, locks/unlocks, confirmations, starting choices and four-card decisions."
    )


if __name__ == "__main__":
    main()
