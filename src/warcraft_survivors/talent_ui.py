"""Connected icon trees with data-driven layout and numerical hover/focus details."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Rect, Surface, Vector2

from .meta import Talent, class_level, load_progression
from .meta_descriptions import bonus_summary
from .rendering import CREAM, GOLD, MUTED

if TYPE_CHECKING:
    from .app import App
    from .rendering import Renderer

TREE_RECT = Rect(64, 184, 804, 446)
MAXED = (115, 203, 164)


def node_rect(talent: Talent) -> Rect:
    rect = Rect(0, 0, 64, 64)
    rect.center = (
        round(TREE_RECT.x + talent.position[0] * TREE_RECT.width),
        round(TREE_RECT.y + talent.position[1] * TREE_RECT.height),
    )
    return rect


def effect_summary(talent: Talent, rank: int, app: App) -> str:
    effects = talent.at_rank(rank)
    if talent.starting_options:
        return (
            "Choose one extra starting ability." if rank else "No extra starting ability unlocked."
        )
    if not effects:
        return "No bonus allocated yet."
    return bonus_summary(effects, app.content)


class TalentTreeView:
    def __init__(self) -> None:
        self.icons: dict[tuple[str, bool], Surface] = {}
        self.backgrounds: dict[str, Surface] = {}
        self.selected: dict[str, str] = {}
        self.hovered: str | None = None
        self.renderer: Renderer | None = None

    def prepare(self, renderer: Renderer) -> None:
        if self.renderer is renderer:
            return
        self.icons.clear()
        self.backgrounds.clear()
        meta = load_progression()
        for tree in meta.trees.values():
            for t in tree.values():
                if (t.icon, False) in self.icons:
                    continue
                kind, name = t.icon.split(":")
                frame = (
                    renderer.assets.actor(name, "idle", "south", 0)
                    if kind == "actor"
                    else renderer.assets.effect(name, 0.16)
                )
                source = frame.image
                factor = min(52 / source.get_width(), 52 / source.get_height())
                source = pygame.transform.scale(
                    source,
                    (
                        max(1, round(source.get_width() * factor)),
                        max(1, round(source.get_height() * factor)),
                    ),
                )
                tile = Surface((56, 56), pygame.SRCALPHA)
                tile.fill((19, 25, 35, 245))
                tile.blit(source, source.get_rect(center=(28, 28)))
                self.icons[t.icon, False] = tile
                gray = pygame.transform.grayscale(tile)
                gray.fill((150, 150, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
                self.icons[t.icon, True] = gray
        for cid, style in meta.tree_styles.items():
            accent = style["accent"]
            background = Surface(TREE_RECT.size)
            for y in range(background.get_height()):
                strength = 0.10 + 0.12 * y / background.get_height()
                color = tuple(round(channel * strength) for channel in accent)
                pygame.draw.line(background, color, (0, y), (background.get_width(), y))
            prop = renderer.assets.image(style["background"])
            factor = min(650 / prop.get_width(), 420 / prop.get_height())
            prop = pygame.transform.scale(
                prop, (round(prop.get_width() * factor), round(prop.get_height() * factor))
            )
            prop.set_alpha(55)
            background.blit(prop, prop.get_rect(midbottom=(TREE_RECT.width // 2, TREE_RECT.height)))
            for tier in range(4):
                y = round([0.10, 0.37, 0.64, 0.90][tier] * TREE_RECT.height)
                pygame.draw.line(
                    background,
                    tuple(round(channel * 0.24) for channel in accent),
                    (12, y),
                    (TREE_RECT.width - 12, y),
                    1,
                )
            self.backgrounds[cid] = background
        self.renderer = renderer

    def hover(self, app: App, pos: Vector2) -> None:
        self.hovered = next(
            (
                t.id
                for t in load_progression().trees[app.selected_class].values()
                if node_rect(t).collidepoint(pos)
            ),
            None,
        )

    def draw(self, app: App) -> None:
        r = app.renderer
        self.prepare(r)
        meta = load_progression()
        cid = app.selected_class
        tree = meta.trees[cid]
        c = app.save.data["classes"][cid]
        accent = tuple(meta.tree_styles[cid]["accent"])
        r.backdrop(
            app.content.classes[cid].name + " talents",
            f"Class level {class_level(c['xp'])} · {app.save.talent_points(cid)} available points · Gold {app.save.data['gold']:,} · Changes apply next run",
        )
        r.canvas.blit(self.backgrounds[cid], TREE_RECT)
        pygame.draw.rect(r.canvas, accent, TREE_RECT, 1)
        focused = (
            list(tree)[app.focus]
            if app.focus < len(tree)
            else self.selected.get(cid, next(iter(tree)))
        )
        self.selected[cid] = focused
        for t in tree.values():
            for parent, required in t.requires.items():
                source, destination = node_rect(tree[parent]), node_rect(t)
                active = c["talents"].get(parent, 0) >= required
                color = accent if active else (74, 86, 98)
                start, end = source.midbottom, destination.midtop
                middle = round((start[1] + end[1]) / 2) + (tree[parent].column - 4) * 4
                points = [start, (start[0], middle), (end[0], middle), end]
                pygame.draw.lines(r.canvas, (9, 14, 20), False, points, 6)
                pygame.draw.lines(r.canvas, color, False, points, 3 if active else 2)
                pygame.draw.polygon(
                    r.canvas, color, [(end[0] - 4, end[1] - 6), (end[0] + 4, end[1] - 6), end]
                )
        for i, t in enumerate(tree.values()):
            rect = node_rect(t)
            rank = c["talents"].get(t.id, 0)
            reason = app.save.talent_reason(cid, t.id)
            maxed = rank == t.max_rank
            locked = rank == 0 and bool(reason)
            color = MAXED if maxed else GOLD if not reason else accent if rank else MUTED
            pygame.draw.rect(r.canvas, (8, 14, 20), rect.inflate(4, 4))
            r.canvas.blit(self.icons[t.icon, locked], (rect.x + 4, rect.y + 4))
            pygame.draw.rect(r.canvas, color, rect, 3 if maxed or not reason else 2)
            if maxed:
                pygame.draw.rect(r.canvas, MAXED, rect.inflate(-8, -8), 1)
            if t.capstone:
                pygame.draw.rect(r.canvas, accent, rect.inflate(8, 8), 1)
            if app.focus == i or self.hovered == t.id:
                pygame.draw.rect(
                    r.canvas, CREAM if self.hovered == t.id else GOLD, rect.inflate(10, 10), 2
                )
            badge = Rect(rect.right - 32, rect.bottom - 16, 38, 20)
            pygame.draw.rect(r.canvas, (5, 10, 17), badge)
            r.text(f"{rank}/{t.max_rank}", (badge.centerx, badge.centery), 18, color, True)
        r.panel(Rect(898, 184, 316, 446))
        t = tree[self.hovered or focused]
        rank = c["talents"].get(t.id, 0)
        reason = app.save.talent_reason(cid, t.id)
        r.canvas.blit(self.icons[t.icon, False], (914, 200))
        r.wrapped(t.name, Rect(980, 204, 216, 57), 28, GOLD)
        state = (
            "MAXED"
            if rank == t.max_rank
            else "AVAILABLE"
            if not reason
            else "LOCKED"
            if not rank
            else "LEARNED"
        )
        r.text(
            f"{'CAPSTONE · ' if t.capstone else ''}{state} · {rank}/{t.max_rank} · Tier {t.tier + 1}",
            (914, 278),
            20,
            MAXED if state == "MAXED" else GOLD if state == "AVAILABLE" else MUTED,
        )
        r.text("CURRENT TALENT BONUS", (914, 313), 18, MUTED)
        r.wrapped(effect_summary(t, rank, app), Rect(914, 338, 284, 76), 20, CREAM)
        r.text(
            f"RANK {rank} to {rank + 1} · NEXT TOTAL" if rank < t.max_rank else "FULLY LEARNED",
            (914, 416),
            18,
            MUTED,
        )
        r.wrapped(
            effect_summary(t, rank + 1, app)
            if rank < t.max_rank
            else "All ranks allocated. Reset talents to choose a new path.",
            Rect(914, 441, 284, 83),
            20,
            CREAM,
        )
        requirements = [f"Class level {t.min_level}; {t.spent_required} points already spent."]
        requirements += [
            f"{tree[parent].name} {c['talents'].get(parent, 0)}/{amount} required."
            for parent, amount in t.requires.items()
        ]
        requirements.append(reason or "Select to review. Cost: 1 talent point.")
        r.wrapped(" ".join(requirements), Rect(914, 530, 284, 85), 18, MUTED)
        r.text(meta.tree_styles[cid]["title"] + " · 1 point per rank", (64, 166), 19, accent)
        r.text(
            f"Hover for details · Arrows / D-pad: move · Enter / {app.pad_labels().accept}: review · Esc / {app.pad_labels().back}: back",
            (64, 700),
            18,
            MUTED,
        )
