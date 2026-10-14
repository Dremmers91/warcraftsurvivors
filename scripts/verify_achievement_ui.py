"""Render every achievement/class page with an isolated, explicitly staged QA profile."""

import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame  # noqa: E402

from warcraft_survivors.achievements import CATEGORIES, complete  # noqa: E402
from warcraft_survivors.app import App  # noqa: E402
from warcraft_survivors.meta import load_progression  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402


def main() -> None:
    output = Path("artifacts/achievements/ui")
    output.mkdir(parents=True, exist_ok=True)
    profile = SaveStore(output / "staged-qa.json")
    profile.data = SaveStore.defaults()
    app = App(profile)
    view = app.progression_ui.achievements
    meta = load_progression()
    captures = 0

    def capture(name: str) -> None:
        nonlocal captures
        app.draw()
        pygame.image.save(app.renderer.canvas, str(output / (name + ".png")))
        captures += 1

    try:
        for category in CATEGORIES:
            view.category_select(app, category)
            for page in range((len(view.entries()) + 5) // 6):
                view.page = page
                app.goto("achievements")
                capture(f"{category}-{page + 1}")
        for aid in meta.achievements:
            view.detail(app, aid)
            capture("detail-" + aid)
        for page in range((len(meta.classes) + 5) // 6):
            app.class_page = page
            app.goto("classes")
            capture(f"classes-{page + 1}")
        for page in range(3):
            view.unlock_page = page
            app.goto("unlocks")
            capture(f"unlocks-{page + 1}")
            app.progression_ui.shop_page = page
            app.goto("shop")
            capture(f"shop-{page + 1}")
        # Show acquired class/shop gates, partial progress, and legacy dates.
        profile.data["stats"]["faction_kills"] = {"defias": 2500}
        profile.data["stats"]["family_kills"] = {"beast": 3180}
        profile.data["stats"]["best_run_level"] = 40
        profile.data["stats"]["chests_opened"] = 12
        profile.data["stats"]["evolved"] = 10
        complete(profile.data)
        profile.data["unlocked_classes"].append("rogue")
        view.unlock_page = 0
        app.goto("unlocks")
        capture("unlocks-earned")
        view.category_select(app, "builds")
        view.page = 1
        app.goto("achievements")
        capture("builds-earned")
        view.detail(app, "more_choices")
        capture("detail-earned")
        view.category_select(app, "combat")
        view.page = (len(view.entries()) + 5) // 6 - 1
        app.goto("achievements")
        for resolution in ("1280x720", "1600x900", "1920x1080", "2560x1440"):
            profile.data["settings"]["resolution"] = resolution
            app.apply_display()
            capture("viewport-" + resolution)
            assert app.viewport.size == app.display.get_size()
        profile.data["shared"].update(banish=1, rerolls=1)
        app.start_run()
        assert app.sim is not None
        app.sim.player.xp = app.sim.player.xp_required
        app.sim.level_check()
        app.goto("level")
        app.selected_choice, app.focus = 1, len(app.buttons) - 1
        capture("banish-selected")
        assert not app.renderer.assets.warnings
        print(
            f"Achievement UI OK: {captures} staged renders, every detail/page and four resolutions, no missing assets"
        )
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
