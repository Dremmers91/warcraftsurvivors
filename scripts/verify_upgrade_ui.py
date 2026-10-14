"""Exhaustive staged layout checks and representative renders, without player saves."""

import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame  # noqa: E402

from warcraft_survivors.app import App  # noqa: E402
from warcraft_survivors.entities import ManualState, SpellState  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402
from warcraft_survivors.upgrades import REWARDS, eligible  # noqa: E402


def main() -> None:
    output = Path("artifacts/upgrade-clarity/ui")
    output.mkdir(parents=True, exist_ok=True)
    app = App(SaveStore(output / "staged-qa.json"))
    app.save.data = SaveStore.defaults()
    original_wrapped = app.renderer.wrapped
    checked, captures = 0, 0
    issues = []

    def audit_wrap(message, rect, size=24, color=(150, 171, 173)):
        # Observe real rendered text lines, including any shrink-to-fit decision.
        drawn = []
        original_text = app.renderer.text

        def record(message, pos, font_size=24, color=(239, 234, 213), center=False):
            drawn.append((message, pos, font_size))
            original_text(message, pos, font_size, color, center)

        app.renderer.text = record
        original_wrapped(message, rect, size, color)
        app.renderer.text = original_text
        if " ".join(line[0] for line in drawn).split() != message.split():
            issues.append("Missing wrapped text: " + message)
        for line, pos, font_size in drawn:
            if app.renderer.fonts[font_size].size(line)[0] > rect.width:
                issues.append("Text wider than its panel: " + line)
            if pos[1] + font_size > rect.bottom:
                issues.append("Text below its panel: " + line)

    app.renderer.wrapped = audit_wrap

    def render(name=None):
        nonlocal checked, captures
        app.draw()
        checked += 1
        if name:
            pygame.image.save(app.renderer.canvas, str(output / (name + ".png")))
            captures += 1

    try:
        for cid, cls in app.content.classes.items():
            app.sim = None
            app.selected_class = cid
            app.start_run()
            sim = app.sim
            assert sim
            for aid in cls.abilities:
                for rank in range(0, 8):
                    sim.player.spells = {aid: SpellState(rank)} if rank else {}
                    sim.player.manual = None
                    sim.player.passives.clear()
                    choice = next(
                        c
                        for c in eligible(app.content, cid, sim.player)
                        if c.kind == "spell" and c.id == aid
                    )
                    sim.choices = [choice] * 4
                    app.goto("level")
                    render(
                        f"{aid}-rank{rank + 1}"
                        if (aid, rank)
                        in {
                            ("judgment", 3),
                            ("beast_companion", 3),
                            ("summon_felguard", 4),
                            ("blizzard", 5),
                        }
                        else None
                    )
                    app.upgrade_ui.open(app, choice)
                    for page in range(len(app.upgrade_ui.sections(app))):
                        app.upgrade_ui.page = page
                        render(
                            "evolution-readiness"
                            if aid == "judgment" and rank == 7 and page == 0
                            else None
                        )
                a = app.content.abilities[aid]
                assert a.evolution
                sim.player.spells = {aid: SpellState(8)}
                sim.player.passives[a.evolution.passive] = 1
                sim.chest_choice = True
                evolution = next(
                    c for c in eligible(app.content, cid, sim.player, True) if c.id == aid
                )
                sim.choices = [evolution] * 3
                app.goto("level")
                render("evolution-card" if aid == "judgment" else None)
                app.upgrade_ui.open(app, evolution)
                for page in range(len(app.upgrade_ui.sections(app))):
                    app.upgrade_ui.page = page
                    render()
                sim.chest_choice = False
            for mid in cls.manuals:
                for rank in range(0, 3):
                    sim.player.manual = ManualState(mid, rank) if rank else None
                    choice = next(
                        c
                        for c in eligible(app.content, cid, sim.player)
                        if c.kind == "manual" and c.id == mid
                    )
                    sim.choices = [choice] * 4
                    app.goto("level")
                    render("manual-cards" if mid == "blink" and rank == 1 else None)
                    app.upgrade_ui.open(app, choice)
                    render("manual-details" if mid == "demonic_circle" and rank == 0 else None)
        sim = app.sim
        assert sim
        sim.player.spells = {"smite": SpellState(7), "holy_fire": SpellState(4)}
        sim.player.manual = None
        sim.player.passives = {"might": 1}
        sim.player.level = 25
        pool = eligible(app.content, app.selected_class, sim.player)
        sim.choices = [
            next(c for c in pool if c.kind == kind and c.id == aid)
            for kind, aid in (
                ("spell", "smite"),
                ("spell", "holy_fire"),
                ("manual", "power_word_shield"),
                ("passive", "might"),
            )
        ]
        app.goto("level")
        render("mixed-cards")
        for pid in app.content.passives:
            sim.player.passives.clear()
            for rank in range(5):
                sim.player.passives[pid] = rank
                choice = next(
                    c
                    for c in eligible(app.content, app.selected_class, sim.player)
                    if c.kind == "passive" and c.id == pid
                )
                sim.choices = [choice] * 4
                app.goto("level")
                render("passive-cards" if pid == "area" and rank == 1 else None)
                app.upgrade_ui.open(app, choice)
                render()
        sim.choices = list(REWARDS)
        app.goto("level")
        render("reward-cards")
        sim.finished = True
        for page in range(3):
            app.progression_ui.shop_page = page
            app.goto("shop")
            render(f"shop-{page + 1}")
        from warcraft_survivors.meta import load_progression

        for cid, tree in load_progression().trees.items():
            app.selected_class = cid
            app.goto("talents")
            for index, tid in enumerate(tree):
                app.focus = index
                render("talent-tooltip" if cid == "paladin" and tid == "might" else None)
        app.selected_class = "paladin"
        app.sim = None
        app.start_run()
        app.sim.player.spells = {"judgment_evolved": SpellState(8), "consecration": SpellState(8)}
        app.goto("spellbook")
        render("spellbook")
        app.buttons[0].action()
        render("evolved-details")
        for resolution in ("1280x720", "1600x900", "1920x1080", "2560x1440"):
            app.save.data["settings"]["resolution"] = resolution
            app.apply_display()
            render("viewport-" + resolution)
        assert not app.renderer.assets.warnings
        assert not issues, "\n".join(sorted(set(issues)))
        print(
            f"Upgrade UI OK: {checked} layouts checked, {captures} captures, no missing/clipped wrapped text or assets"
        )
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
