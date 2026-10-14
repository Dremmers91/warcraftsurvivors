"""Achievement categories, requirement details and future champion cards."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from .achievements import CATEGORIES, metric_label, metric_value, reward_text, state
from .meta import Achievement, ClassUnlock, load_progression
from .rendering import CREAM, GOLD, MUTED

if TYPE_CHECKING:
    from .app import App

GREEN = (114, 192, 143)


def icon(app: App, reference: str, pos: tuple[int, int], size: int = 44) -> None:
    kind, key = reference.split(":", 1)
    assets = app.renderer.assets
    picture = (
        assets.actor(key, "idle", "south", 0).image
        if kind == "actor"
        else assets.scaled_effect(key, 0, size).image
    )
    app.renderer.canvas.blit(pygame.transform.scale(picture, (size, size)), pos)


def future_classes() -> list[ClassUnlock]:
    return [c for c in load_progression().classes.values() if not c.playable]


def future_card(app: App, entry: ClassUnlock, rect: Rect, focused: bool) -> None:
    r = app.renderer
    achievement = load_progression().achievements[entry.achievement]
    earned = entry.id in app.save.data["unlocked_classes"]
    value = app.save.achievement_value(app.save.data, achievement.id)
    r.panel(rect, focused)
    icon(app, entry.icon, (rect.right - 62, rect.y + 16))
    r.text(entry.name, (rect.x + 18, rect.y + 15), 30, GOLD)
    r.text(
        "Coming Soon · " + ("unlock earned" if earned else "locked"),
        (rect.x + 18, rect.y + 54),
        21,
        GREEN if earned else MUTED,
    )
    r.wrapped(entry.description, Rect(rect.x + 18, rect.y + 87, rect.width - 36, 58), 21, CREAM)
    r.bar(
        Rect(rect.x + 18, rect.bottom - 45, rect.width - 36, 6),
        min(1, value / achievement.target),
        GREEN,
    )
    r.text(
        (
            f"{min(value, achievement.target):,} / {achievement.target:,}"
            if achievement.available
            else "Not Yet Available · no encounter"
        ),
        (rect.x + 18, rect.bottom - 29),
        18,
        MUTED,
    )


class AchievementView:
    def __init__(self) -> None:
        self.category = "combat"
        self.page = 0
        self.selected = "kills_1000"
        self.unlock_page = 0

    def entries(self) -> list[Achievement]:
        return [a for a in load_progression().achievements.values() if a.category == self.category]

    def category_select(self, app: App, category: str) -> None:
        self.category, self.page = category, 0
        app.goto("achievements")

    def turn_page(self, app: App, amount: int, unlocks: bool = False) -> None:
        if unlocks:
            self.unlock_page = (self.unlock_page + amount) % ((len(future_classes()) + 2) // 3)
            app.goto("unlocks")
        else:
            self.page = (self.page + amount) % ((len(self.entries()) + 5) // 6)
            app.goto("achievements")

    def detail(self, app: App, aid: str) -> None:
        self.selected = aid
        app.goto("achievement_detail")

    def build(self, app: App, add: Callable[[Rect, str, Callable[[], None]], None]) -> None:
        if app.screen == "achievement_detail":
            add(Rect(64, 650, 240, 48), "Back", partial(app.goto, "achievements"))
        elif app.screen == "unlocks":
            for i, entry in enumerate(
                future_classes()[self.unlock_page * 3 : self.unlock_page * 3 + 3]
            ):
                add(
                    Rect(64 + i * 384, 220, 366, 365),
                    entry.name,
                    partial(self.detail, app, entry.achievement),
                )
            add(Rect(64, 650, 240, 48), "Class selection", partial(app.goto, "classes"))
            add(Rect(740, 650, 230, 48), "Previous", partial(self.turn_page, app, -1, True))
            add(Rect(984, 650, 230, 48), "Next", partial(self.turn_page, app, 1, True))
        else:
            for i, (category, label) in enumerate(CATEGORIES.items()):
                add(
                    Rect(64 + i * 233, 160, 220, 48),
                    label,
                    partial(self.category_select, app, category),
                )
            for i, achievement in enumerate(self.entries()[self.page * 6 : self.page * 6 + 6]):
                add(
                    Rect(64 + i % 2 * 584, 224 + i // 2 * 132, 566, 122),
                    achievement.name,
                    partial(self.detail, app, achievement.id),
                )
            add(Rect(64, 650, 230, 48), "Back", partial(app.goto, "main"))
            add(Rect(740, 650, 230, 48), "Previous", partial(self.turn_page, app, -1))
            add(Rect(984, 650, 230, 48), "Next", partial(self.turn_page, app, 1))

    def draw(self, app: App) -> None:
        r = app.renderer
        if app.screen == "achievement_detail":
            a = load_progression().achievements[self.selected]
            status = state(app.save.data, a)
            r.backdrop(a.name, CATEGORIES[a.category] + " · " + status.upper())
            r.panel(Rect(64, 190, 1150, 430))
            icon(app, a.icon, (100, 222), 72)
            r.wrapped(a.description, Rect(205, 216, 955, 64), 30, CREAM)
            y = 307
            for condition in a.conditions:
                value = metric_value(app.save.data, condition.metric, a.class_id)
                r.text(
                    f"{metric_label(condition.metric, a.class_id)} · {min(value, condition.target):,} / {condition.target:,}",
                    (100, y),
                    23,
                    CREAM,
                )
                r.bar(Rect(100, y + 32, 1060, 7), min(1, value / condition.target), GREEN)
                y += 55
            r.wrapped("Reward: " + reward_text(a), Rect(100, 433, 1060, 58), 25, GOLD)
            note = (
                a.availability_reason
                if not a.available
                else "Requires: "
                + ", ".join(load_progression().achievements[aid].name for aid in a.prerequisites)
                if status == "locked"
                else "Completed: "
                + (
                    app.save.data["achievement_completed_at"].get(a.id)
                    or "earned in an earlier version"
                )
                if status == "completed"
                else "Progress is saved when a run ends, including failed runs."
            )
            r.wrapped(note, Rect(100, 522, 1060, 64), 23, MUTED)
            start = 0
        elif app.screen == "unlocks":
            r.backdrop(
                "Future champions",
                f"Page {self.unlock_page + 1}/{(len(future_classes()) + 2) // 3} · Earn an unlock through achievements · playable content is Coming Soon",
            )
            entries = future_classes()[self.unlock_page * 3 : self.unlock_page * 3 + 3]
            for i, entry in enumerate(entries):
                future_card(app, entry, app.buttons[i].rect, app.focus == i)
                a = load_progression().achievements[entry.achievement]
                r.wrapped(
                    a.availability_reason or "Select to view achievement requirements and rewards.",
                    Rect(app.buttons[i].rect.x + 18, 387, 330, 104),
                    22,
                    MUTED,
                )
            start = len(entries)
        else:
            r.backdrop(
                "Chronicle of Azeroth",
                f"{len(app.save.data['achievements'])}/{len(load_progression().achievements)} completed · {CATEGORIES[self.category]} · Page {self.page + 1}/{(len(self.entries()) + 5) // 6}",
            )
            for i, category in enumerate(CATEGORIES):
                button = app.buttons[i]
                r.panel(button.rect, app.focus == i or category == self.category)
                r.wrapped(
                    button.label,
                    Rect(button.rect.x + 12, button.rect.y + 13, 196, 30),
                    22,
                    GREEN if category == self.category else CREAM,
                )
            achievements = self.entries()[self.page * 6 : self.page * 6 + 6]
            for i, a in enumerate(achievements, start=5):
                rect = app.buttons[i].rect
                status = state(app.save.data, a)
                value = app.save.achievement_value(app.save.data, a.id)
                r.panel(rect, app.focus == i)
                icon(app, a.icon, (rect.x + 12, rect.y + 12))
                r.text(
                    a.name, (rect.x + 66, rect.y + 10), 26, GREEN if status == "completed" else GOLD
                )
                r.text(
                    status.upper() + (" · Coming Soon" if status == "unavailable" else ""),
                    (rect.x + 66, rect.y + 36),
                    17,
                    MUTED,
                )
                r.wrapped(a.description, Rect(rect.x + 12, rect.y + 57, 542, 28), 19, CREAM)
                r.text(
                    f"{min(value, a.target):,}/{a.target:,}",
                    (rect.right - 142, rect.y + 36),
                    18,
                    MUTED,
                )
                r.wrapped(reward_text(a), Rect(rect.x + 12, rect.y + 88, 542, 21), 17, GOLD)
                r.bar(Rect(rect.x + 12, rect.bottom - 8, 542, 4), min(1, value / a.target), GREEN)
            start = 5 + len(achievements)
        for i in range(start, len(app.buttons)):
            b = app.buttons[i]
            r.button(b.rect, b.label, selected=app.focus == i)
