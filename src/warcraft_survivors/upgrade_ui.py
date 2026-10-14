"""Readable power cards and paused, paged details for cards and equipped spells."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from .descriptions import automatic_values, describe_choice, evolution_requirements
from .rendering import CREAM, GOLD, MUTED
from .upgrades import Choice

if TYPE_CHECKING:
    from .app import App

PASSIVE_ICONS = {
    "projectiles": "arcane_missiles",
    "area": "consecration",
    "might": "mortal_strike",
    "haste": "rapid_fire",
    "duration": "ice_block",
    "velocity": "arcane_shot",
    "movement": "blink",
    "pickup": "demonic_circle",
    "armor": "shield_wall",
    "health": "lay_on_hands",
    "regen": "desperate_prayer",
    "piercing": "aimed_shot",
}
REWARD_ICONS = {
    "heal": "lay_on_hands",
    "gold": "icon_gold",
    "power": "avenging_wrath",
    "ward": "power_word_shield",
}


def draw_icon(app: App, choice: Choice, rect: Rect) -> None:
    assets = app.renderer.assets
    key = (
        PASSIVE_ICONS[choice.id]
        if choice.kind == "passive"
        else REWARD_ICONS[choice.id]
        if choice.kind == "reward"
        else choice.id.split(":")[0]
    )
    frame = assets.image(key) if key.startswith("icon_") else assets.scaled_effect(key, 0, 40).image
    image = pygame.transform.scale(frame, (40, 40))
    app.renderer.canvas.blit(image, (rect.right - 54, rect.y + 12))


class UpgradeView:
    def __init__(self) -> None:
        self.choice: Choice | None = None
        self.return_screen = "level"
        self.return_focus = 0
        self.page = 0

    def open(self, app: App, choice: Choice, return_screen: str = "level") -> None:
        self.choice = choice
        self.return_screen, self.return_focus, self.page = return_screen, app.focus, 0
        app.goto("upgrade_details")

    def close(self, app: App) -> None:
        app.goto(self.return_screen)
        app.focus = min(self.return_focus, len(app.buttons) - 1)
        if app.screen == "level" and app.sim and app.focus < len(app.sim.choices):
            app.selected_choice = app.focus

    def sections(self, app: App) -> list[tuple[str, tuple[str, ...]]]:
        assert self.choice and app.sim
        text = describe_choice(app.content, app.sim.player, self.choice, app.activation_label())
        sections = []
        if self.choice.kind in {"spell", "evolution"}:
            sections.append(
                (
                    "EVOLUTION REQUIREMENTS · CURRENT BUILD",
                    evolution_requirements(
                        app.content, app.sim.player, self.choice.id, app.sim.chest_choice
                    ),
                )
            )
        for i in range(0, len(text.notes), 5):
            sections.append(("SPECIAL EFFECTS / SCOPE", text.notes[i : i + 5]))
        return sections or [("SCOPE", (text.basis,))]

    def turn_page(self, app: App, amount: int) -> None:
        self.page = (self.page + amount) % len(self.sections(app))
        app.build_buttons()

    def equipped(self, app: App) -> list[Choice]:
        assert app.sim
        result = []
        for aid, state in app.sim.player.spells.items():
            a = app.content.ability(aid)
            result.append(Choice("spell", aid, a.name, a.description, state.rank, 0))
        return result

    def draw_cards(self, app: App) -> None:
        assert app.sim
        r, sim = app.renderer, app.sim
        for i, choice in enumerate(sim.choices):
            rect = app.buttons[i].rect
            text = describe_choice(app.content, sim.player, choice, app.activation_label())
            r.panel(
                rect, app.focus == i or (app.focus >= len(sim.choices) and app.selected_choice == i)
            )
            draw_icon(app, choice, rect)
            r.wrapped(
                f"{i + 1} · {text.kind}",
                Rect(rect.x + 18, rect.y + 16, rect.width - 80, 32),
                20,
                GOLD,
            )
            r.wrapped(choice.name, Rect(rect.x + 18, rect.y + 60, rect.width - 36, 54), 30, CREAM)
            r.wrapped(text.rank, Rect(rect.x + 18, rect.y + 114, rect.width - 36, 28), 22, GOLD)
            r.wrapped(text.summary, Rect(rect.x + 18, rect.y + 148, rect.width - 36, 56), 21, CREAM)
            if choice.kind == "manual":
                r.text("Activate: " + app.activation_label(), (rect.x + 18, rect.y + 207), 18, GOLD)
            changes = text.changes[:3]
            if choice.kind == "manual":
                cooldown = tuple(line for line in text.changes if line.startswith("Cooldown"))
                changes = (
                    tuple(line for line in text.changes if not line.startswith("Cooldown"))[:2]
                    + cooldown
                )
            for row, line in enumerate(changes):
                r.wrapped(
                    line, Rect(rect.x + 18, rect.y + 227 + row * 39, rect.width - 36, 38), 20, CREAM
                )
            r.wrapped(
                "This passive's bonus"
                if choice.kind == "passive"
                else "Effective now"
                if text.changes
                else text.basis,
                Rect(rect.x + 18, rect.bottom - 24, rect.width - 36, 22),
                17,
                MUTED,
            )
        r.text(
            f"Select: 1–{len(sim.choices)} / Enter / {app.pad_labels().accept} / click · Details: Q / {app.pad_labels().details} / right-click",
            (640, 622),
            21,
            MUTED,
            True,
        )
        for i, button in enumerate(app.buttons[len(sim.choices) :], start=len(sim.choices)):
            label = (
                f"B / {app.pad_labels().banish} · Banish card {app.selected_choice + 1} ({sim.banishes})"
                if button.action == app.banish
                else f"R / {app.pad_labels().reroll} · Reroll ({sim.rerolls})"
                if button.action == app.reroll
                else button.label
            )
            r.button(button.rect, label, selected=app.focus == i)

    def draw_details(self, app: App) -> None:
        assert self.choice and app.sim
        r, choice = app.renderer, self.choice
        text = describe_choice(app.content, app.sim.player, choice, app.activation_label())
        r.backdrop(choice.name, text.kind + " · " + text.rank + " · The world stays paused")
        r.panel(Rect(64, 185, 566, 425))
        r.panel(Rect(648, 185, 566, 425))
        draw_icon(app, choice, Rect(64, 185, 566, 425))
        r.wrapped(text.summary, Rect(88, 205, 475, 74), 27, CREAM)
        r.wrapped(text.basis, Rect(88, 287, 518, 40), 19, MUTED)
        changes = text.changes
        if not changes and choice.kind == "spell":
            ability = app.content.ability(choice.id)
            changes = tuple(
                v.label + ": " + v.text()
                for v in automatic_values(ability, app.sim.player.spells[choice.id], app.sim.player)
            )
        for i, line in enumerate(changes):
            r.wrapped(line, Rect(88, 337 + i * 36, 518, 34), 23, GOLD)
        title, lines = self.sections(app)[self.page]
        r.wrapped(title, Rect(672, 205, 518, 42), 22, GOLD)
        for i, line in enumerate(lines):
            r.wrapped(line, Rect(672, 267 + i * 64, 518, 60), 24, CREAM)
        r.text(
            f"Details page {self.page + 1}/{len(self.sections(app))} · Read only",
            (640, 628),
            20,
            MUTED,
            True,
        )
        for i, button in enumerate(app.buttons):
            r.button(button.rect, button.label, selected=app.focus == i)

    def draw_spellbook(self, app: App) -> None:
        assert app.sim
        r = app.renderer
        r.backdrop(
            "Your spellbook",
            "Select an equipped spell to inspect its values and evolution readiness. The world stays paused.",
        )
        entries = self.equipped(app)
        for i, choice in enumerate(entries):
            rect = app.buttons[i].rect
            r.panel(rect, app.focus == i)
            draw_icon(app, choice, rect)
            r.wrapped(choice.name, Rect(rect.x + 16, rect.y + 17, rect.width - 80, 40), 24, GOLD)
            r.text(
                f"Rank {choice.rank}/8"
                + (" · Evolved" if app.content.ability(choice.id).evolved else ""),
                (rect.x + 16, rect.y + 60),
                20,
                CREAM,
            )
        for i in range(len(entries), len(app.buttons)):
            b = app.buttons[i]
            r.button(b.rect, b.label, selected=app.focus == i)
