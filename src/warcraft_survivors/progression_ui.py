"""Between-run progression screens and explicit purchase/respec confirmations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

import pygame
from pygame import Rect, Vector2

from .achievement_ui import AchievementView
from .meta import class_level, class_xp_progress, load_progression
from .meta_descriptions import bonus_summary
from .rendering import CREAM, GOLD, MUTED
from .talent_ui import TalentTreeView, effect_summary, node_rect

if TYPE_CHECKING:
    from .app import App

SCREENS = {
    "progression",
    "talents",
    "shop",
    "achievements",
    "unlocks",
    "starting",
    "confirm",
    "achievement_detail",
}
GREEN = (114, 192, 143)


@dataclass
class Confirmation:
    title: str
    body: str
    action: Callable[[], bool]
    return_screen: str


class ProgressionUI:
    def __init__(self) -> None:
        self.shop_page = 0
        self.achievements = AchievementView()
        self.confirmation: Confirmation | None = None
        self.tree = TalentTreeView()

    def open_tree(self, app: App, cid: str) -> None:
        app.selected_class = cid
        app.goto("talents")

    def page(self, app: App, screen: str, amount: int) -> None:
        if screen == "shop":
            self.shop_page = (self.shop_page + amount) % ((len(load_progression().shared) + 5) // 6)
        else:
            self.achievements.turn_page(app, amount)
        app.goto(screen)

    def cycle_class(self, app: App, amount: int) -> None:
        ids = list(app.content.classes)
        self.open_tree(app, ids[(ids.index(app.selected_class) + amount) % len(ids)])

    def request(self, app: App, title: str, body: str, action: Callable[[], bool]) -> None:
        if app.sim and not app.sim.finished:
            app.toast("Finish the current run before changing permanent progression.")
            return
        self.confirmation = Confirmation(title, body, action, app.screen)
        app.goto("confirm")
        app.focus = 1  # Cancel is initially focused; purchase is always explicit.

    def confirm(self, app: App) -> None:
        confirmation = self.confirmation
        if not confirmation:
            return
        success = confirmation.action()
        app.toast(
            "Progression saved."
            if success
            else app.save.notice or "Purchase unavailable; no gold or points spent."
        )
        app.goto(confirmation.return_screen)
        self.confirmation = None

    def cancel(self, app: App) -> None:
        target = self.confirmation.return_screen if self.confirmation else "main"
        self.confirmation = None
        app.goto(target)

    def talent(self, app: App, tid: str) -> None:
        cid = app.selected_class
        reason = app.save.talent_reason(cid, tid)
        if reason:
            app.toast(reason)
            return
        t = load_progression().trees[cid][tid]
        rank = app.save.data["classes"][cid]["talents"].get(tid, 0) + 1
        self.tree.selected[cid] = tid
        self.request(
            app,
            f"Learn {t.name} · Rank {rank}",
            effect_summary(t, rank, app)
            + " Spend one available talent point. Class XP is retained.",
            partial(app.save.buy_talent, cid, tid),
        )

    def shared(self, app: App, sid: str) -> None:
        reason = app.save.shared_reason(sid)
        if reason:
            app.toast(reason)
            return
        upgrade = load_progression().shared[sid]
        cost = app.save.shared_cost(sid)
        self.request(
            app,
            upgrade.name,
            "Current: "
            + bonus_summary(
                {k: v * app.save.data["shared"].get(sid, 0) for k, v in upgrade.effects.items()},
                app.content,
            )
            + " Next: "
            + bonus_summary(
                {
                    k: v * (app.save.data["shared"].get(sid, 0) + 1)
                    for k, v in upgrade.effects.items()
                },
                app.content,
            )
            + f" Cost: {cost} gold. Applies to future runs.",
            partial(app.save.buy_shared, sid),
        )

    def respec(self, app: App) -> None:
        cid = app.selected_class
        points = sum(app.save.data["classes"][cid]["talents"].values())
        cost = app.save.respec_cost(cid)
        if not points or app.save.data["gold"] < cost or app.save.read_only:
            app.toast(
                "No allocated talents to reset." if not points else f"Reset requires {cost} gold."
            )
            return
        self.request(
            app,
            f"Reset {app.content.classes[cid].name} talents?",
            f"Cost: {cost} gold. Refund {points} allocated talent points. Your class XP and level stay intact. Clear the selected extra starting ability.",
            partial(app.save.respec, cid),
        )

    def starting(self, app: App) -> None:
        if not app.save.data["classes"][app.selected_class]["talents"].get("preparation"):
            app.toast(
                "Learn the advanced preparation talent before choosing an extra starting ability."
            )
            return
        app.goto("starting")

    def select_starting(self, app: App, aid: str) -> None:
        if app.save.select_starting(app.selected_class, aid):
            app.toast("Starting loadout saved. Applies to your next run.")
            app.goto("talents")
        else:
            app.toast(app.save.notice or "Starting choice unavailable.")

    def build(self, app: App, add: Callable[[Rect, str, Callable[[], None]], None]) -> None:
        screen = app.screen
        meta = load_progression()
        cid = app.selected_class
        if screen == "progression":
            for i, cls in enumerate(app.content.classes.values()):
                add(
                    Rect(64 + i % 3 * 384, 195 + i // 3 * 196, 366, 180),
                    cls.name,
                    partial(self.open_tree, app, cls.id),
                )
            add(Rect(64, 640, 230, 48), "Back", partial(app.goto, "main"))
            add(Rect(900, 640, 314, 48), "Future unlocks", partial(app.goto, "unlocks"))
        elif screen == "talents":
            for t in meta.trees[cid].values():
                add(
                    node_rect(t),
                    t.name,
                    partial(self.talent, app, t.id),
                )
            add(Rect(64, 640, 170, 48), "Classes", partial(app.goto, "progression"))
            add(Rect(250, 640, 160, 48), "Previous", partial(self.cycle_class, app, -1))
            add(Rect(426, 640, 160, 48), "Next", partial(self.cycle_class, app, 1))
            add(
                Rect(602, 640, 286, 48),
                f"Reset · {app.save.respec_cost(cid)} gold",
                partial(self.respec, app),
            )
            add(Rect(904, 640, 310, 48), "Starting ability", partial(self.starting, app))
            self.tree.hovered = None
            app.focus = list(meta.trees[cid]).index(
                self.tree.selected.get(cid, next(iter(meta.trees[cid])))
            )
        elif screen == "shop":
            shared_entries = list(meta.shared.values())[self.shop_page * 6 : self.shop_page * 6 + 6]
            for i, u in enumerate(shared_entries):
                add(
                    Rect(64 + i % 2 * 584, 195 + i // 2 * 138, 566, 124),
                    u.name,
                    partial(self.shared, app, u.id),
                )
            add(Rect(64, 640, 230, 48), "Back", partial(app.goto, "main"))
            add(Rect(740, 640, 230, 48), "Previous", partial(self.page, app, "shop", -1))
            add(Rect(984, 640, 230, 48), "Next", partial(self.page, app, "shop", 1))
        elif screen in {"achievements", "achievement_detail", "unlocks"}:
            self.achievements.build(app, add)
        elif screen == "starting":
            options = ("",) + meta.trees[cid]["preparation"].starting_options
            for i, aid in enumerate(options):
                add(
                    Rect(64 + i * 384, 230, 366, 240),
                    app.content.abilities[aid].name if aid else "No extra ability",
                    partial(self.select_starting, app, aid),
                )
            add(Rect(64, 640, 230, 48), "Back", partial(app.goto, "talents"))
        elif screen == "confirm":
            add(Rect(270, 500, 350, 64), "Confirm", partial(self.confirm, app))
            add(Rect(660, 500, 350, 64), "Cancel", partial(self.cancel, app))

    def escape(self, app: App) -> None:
        if app.screen == "confirm":
            self.cancel(app)
        else:
            app.goto(
                "achievements"
                if app.screen == "achievement_detail"
                else "progression"
                if app.screen == "talents"
                else "talents"
                if app.screen == "starting"
                else "main"
            )

    def draw(self, app: App) -> None:
        r = app.renderer
        screen = app.screen
        meta = load_progression()
        cid = app.selected_class
        c = app.save.data["classes"][cid]
        if screen == "progression":
            r.backdrop(
                "Your champions",
                "Permanent class XP earns talent points. Select a class to shape its tree.",
            )
            for i, cls in enumerate(app.content.classes.values()):
                rect = app.buttons[i].rect
                data = app.save.data["classes"][cls.id]
                r.panel(rect, app.focus == i)
                frame = r.assets.actor(cls.id, "idle", "south", pygame.time.get_ticks() / 1000)
                r.canvas.blit(frame.image, frame.at(Vector2(rect.right - 40, rect.y + 92)))
                r.text(cls.name, (rect.x + 18, rect.y + 18), 32, GOLD)
                r.text(
                    f"Class level {class_level(data['xp'])} · {app.save.talent_points(cls.id)} points",
                    (rect.x + 18, rect.y + 64),
                    23,
                    CREAM,
                )
                current, required = class_xp_progress(data["xp"])
                r.bar(Rect(rect.x + 18, rect.y + 101, 280, 8), min(1, current / required), GREEN)
                r.text(
                    f"{data['xp']:,} total XP · {current:,} / {required:,}",
                    (rect.x + 18, rect.y + 123),
                    20,
                    MUTED,
                )
            start = 6
        elif screen == "talents":
            self.tree.draw(app)
            start = len(meta.trees[cid])
        elif screen == "shop":
            r.backdrop(
                "Shared training",
                f"Gold {app.save.data['gold']:,} · Page {self.shop_page + 1}/{(len(meta.shared) + 5) // 6} · Bonuses apply to every class in future runs.",
            )
            shared_entries = list(meta.shared.values())[self.shop_page * 6 : self.shop_page * 6 + 6]
            for i, u in enumerate(shared_entries):
                rect = app.buttons[i].rect
                r.panel(rect, app.focus == i)
                rank = app.save.data["shared"].get(u.id, 0)
                cost = app.save.shared_cost(u.id)
                r.text(u.name, (rect.x + 16, rect.y + 12), 28, GOLD)
                r.text(
                    f"{rank}/{u.max_rank} · " + (f"{cost} gold" if cost is not None else "MAX"),
                    (rect.right - 190, rect.y + 15),
                    21,
                    CREAM,
                )
                current_bonus = bonus_summary(
                    {k: v * rank for k, v in u.effects.items()}, app.content
                )
                next_bonus = bonus_summary(
                    {k: v * min(u.max_rank, rank + 1) for k, v in u.effects.items()}, app.content
                )
                r.wrapped(
                    "Current: " + current_bonus, Rect(rect.x + 16, rect.y + 43, 530, 25), 20, CREAM
                )
                r.wrapped(
                    "Next: " + next_bonus if cost is not None else "Maximum rank reached.",
                    Rect(rect.x + 16, rect.y + 70, 530, 25),
                    20,
                    GOLD,
                )
                gate = (
                    "Requires " + meta.achievements[u.achievement].name + ". "
                    if u.achievement
                    else ""
                )
                r.wrapped(
                    app.save.shared_reason(u.id) or gate + "Select to review purchase.",
                    Rect(rect.x + 16, rect.y + 98, 530, 21),
                    18,
                    MUTED,
                )
            start = len(shared_entries)
        elif screen in {"achievements", "achievement_detail", "unlocks"}:
            self.achievements.draw(app)
            return
        elif screen == "starting":
            r.backdrop(
                "Prepare your next run",
                "Choose one optional extra Rank 1 ability. This occupies an ordinary spell slot.",
            )
            options = ("",) + meta.trees[cid]["preparation"].starting_options
            for i, aid in enumerate(options):
                rect = app.buttons[i].rect
                r.panel(rect, app.focus == i)
                label = app.content.abilities[aid].name if aid else "No extra ability"
                r.wrapped(label, Rect(rect.x + 20, rect.y + 25, 326, 65), 34, GOLD)
                body = (
                    app.content.abilities[aid].description
                    if aid
                    else "Begin with only your class signature spell."
                )
                r.wrapped(body, Rect(rect.x + 20, rect.y + 110, 326, 80), 23, CREAM)
                if c["starting_ability"] == aid:
                    r.text("SELECTED", (rect.x + 20, rect.y + 209), 22, GREEN)
            start = len(options)
        elif screen == "confirm":
            r.backdrop(
                "Review your choice",
                "Progression changes apply between runs. Cancel keeps your current profile.",
            )
            r.panel(Rect(250, 210, 780, 240))
            if self.confirmation:
                r.wrapped(self.confirmation.title, Rect(280, 240, 720, 60), 38, GOLD)
                r.wrapped(self.confirmation.body, Rect(280, 320, 720, 105), 26, CREAM)
            start = 0
        else:
            return
        for i in range(start, len(app.buttons)):
            b = app.buttons[i]
            r.button(b.rect, b.label, selected=app.focus == i)
