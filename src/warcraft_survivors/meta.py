"""Typed permanent content and immutable per-run loadouts, independent of saving/UI."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files
from typing import Any


@dataclass(frozen=True)
class Talent:
    id: str
    name: str
    description: str
    max_rank: int
    tier: int
    column: int
    min_level: int
    spent_required: int
    requires: dict[str, int]
    effects: dict[str, float]
    class_id: str
    icon: str
    position: tuple[float, float]
    rank_effects: tuple[dict[str, float], ...]
    capstone: bool = False
    legacy_requires: dict[str, int] = field(default_factory=dict)
    starting_options: tuple[str, ...] = ()

    def at_rank(self, rank: int) -> dict[str, float]:
        return self.rank_effects[min(rank, self.max_rank) - 1].copy() if rank > 0 else {}


@dataclass(frozen=True)
class SharedUpgrade:
    id: str
    name: str
    description: str
    max_rank: int
    costs: tuple[int, ...]
    requires_ranks: int
    effects: dict[str, float]


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    metric: str
    target: int
    gold: int
    description: str
    class_id: str = ""


@dataclass(frozen=True)
class ClassUnlock:
    id: str
    name: str
    playable: bool
    achievement: str
    description: str


@dataclass(frozen=True)
class ProgressionContent:
    trees: dict[str, dict[str, Talent]]
    shared: dict[str, SharedUpgrade]
    achievements: dict[str, Achievement]
    classes: dict[str, ClassUnlock]
    zones: tuple[str, ...]
    tree_styles: dict[str, dict[str, Any]]


@lru_cache(maxsize=1)
def load_progression() -> ProgressionContent:
    from .content import load_content

    gameplay = load_content()
    raw = json.loads(files(__package__).joinpath("data/progression.json").read_text("utf-8"))
    art = json.loads(files(__package__).joinpath("assets/manifest.json").read_text("utf-8"))
    trees = {
        cid: {
            r["id"]: Talent(
                **{
                    k: v
                    for k, v in r.items()
                    if k not in {"starting_options", "position", "rank_effects"}
                },
                starting_options=tuple(r["starting_options"]),
                position=tuple(r["position"]),
                rank_effects=tuple(r["rank_effects"]),
            )
            for r in rows
        }
        for cid, rows in raw["trees"].items()
    }
    shared = {
        r["id"]: SharedUpgrade(
            **{k: v for k, v in r.items() if k != "costs"}, costs=tuple(r["costs"])
        )
        for r in raw["shared"]
    }
    achievements = {r["id"]: Achievement(**r) for r in raw["achievements"]}
    classes = {r["id"]: ClassUnlock(**r) for r in raw["classes"]}

    def validate_effects(effects: dict[str, float]) -> None:
        general = {
            "damage",
            "health",
            "armor",
            "haste",
            "speed",
            "pickup",
            "xp",
            "gold",
            "regen",
            "rerolls",
            "choices",
            "area",
            "duration",
            "count",
            "boss_damage",
            "execute",
            "low_health_damage",
            "kill_heal",
            "kill_shield",
            "healing",
            "starting_shield",
            "manual_haste",
        }
        for key, value in effects.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError("Invalid permanent effect amount")
            if key in general:
                continue
            parts = key.split(":")
            if (
                len(parts) == 2
                and parts[0] == "school"
                and parts[1] in {a.school for a in gameplay.abilities.values()}
            ):
                continue
            if (
                len(parts) == 2
                and parts[0] == "kind"
                and parts[1] in {a.kind for a in gameplay.abilities.values()}
            ):
                continue
            if (
                len(parts) == 3
                and parts[0] == "spell"
                and parts[1] in gameplay.abilities
                and parts[2]
                in {
                    "damage",
                    "radius",
                    "count",
                    "pierce",
                    "duration",
                    "speed",
                    "spread",
                    "waves",
                    "splash",
                    "splash_flat",
                    "opening",
                }
            ):
                continue
            raise ValueError("Unknown permanent effect")

    for cid, tree in trees.items():
        if not 12 <= len(tree) <= 18 or cid not in classes:
            raise ValueError("Invalid class talent tree")
        if len(tree) != len(raw["trees"][cid]):
            raise ValueError("Duplicate talent ID")
        if (
            len({t.position for t in tree.values()}) != len(tree)
            or sum(t.capstone for t in tree.values()) != 1
        ):
            raise ValueError("Invalid talent layout/capstone")
        for t in tree.values():
            validate_effects(t.effects)
            if len(t.rank_effects) != t.max_rank:
                raise ValueError("Invalid talent rank effects")
            for effects in t.rank_effects:
                validate_effects(effects)
            if not t.starting_options and not any(
                value > 0 for effects in t.rank_effects for value in effects.values()
            ):
                raise ValueError("Talent has no implemented benefit")
            icon_kind, _, icon_name = t.icon.partition(":")
            if t.class_id != cid or icon_name not in art.get(
                {"effect": "effects", "actor": "actors"}.get(icon_kind, ""), {}
            ):
                raise ValueError("Invalid talent class/icon")
            if len(t.position) != 2 or any(
                not math.isfinite(p) or not 0 <= p <= 1 for p in t.position
            ):
                raise ValueError("Invalid talent position")
            if any(aid not in gameplay.classes[cid].abilities for aid in t.starting_options):
                raise ValueError("Invalid starting ability")
            if (
                t.max_rank < 1
                or t.min_level < 1
                or t.spent_required < 0
                or not (0 <= t.column < 9 and 0 <= t.tier < 4)
                or (t.capstone and t.tier != 3)
            ):
                raise ValueError("Invalid talent requirements")
            if any(
                parent not in tree
                or tree[parent].tier >= t.tier
                or tree[parent].position[1] >= t.position[1]
                or not 1 <= rank <= tree[parent].max_rank
                for parent, rank in t.requires.items()
            ):
                raise ValueError("Invalid talent prerequisite")
    if any(u.max_rank != len(u.costs) or any(c <= 0 for c in u.costs) for u in shared.values()):
        raise ValueError("Invalid permanent upgrade costs")
    for upgrade in shared.values():
        validate_effects(upgrade.effects)
    if any(a.target <= 0 or a.gold < 0 for a in achievements.values()):
        raise ValueError("Invalid achievement")
    if any(c.achievement and c.achievement not in achievements for c in classes.values()):
        raise ValueError("Unknown class unlock achievement")
    if set(raw["tree_styles"]) != set(trees):
        raise ValueError("Missing class tree styles")
    for cid, style in raw["tree_styles"].items():
        if (
            cid not in trees
            or style["background"] not in art["images"]
            or len(style["accent"]) != 3
            or any(not 0 <= v <= 255 for v in style["accent"])
        ):
            raise ValueError("Invalid class tree style")
    return ProgressionContent(
        trees, shared, achievements, classes, tuple(raw["zones"]), raw["tree_styles"]
    )


def class_level(xp: int) -> int:
    level = 1
    remaining = max(0, xp)
    while remaining >= level * 120 and level < 100:
        remaining -= level * 120
        level += 1
    return level


def class_xp_progress(xp: int) -> tuple[int, int]:
    level = class_level(xp)
    return max(0, xp - 60 * level * (level - 1)), level * 120


def talent_reason(tree: dict[str, Talent], xp: int, allocated: dict[str, int], tid: str) -> str:
    if tid not in tree:
        return "Unknown talent."
    t = tree[tid]
    if allocated.get(tid, 0) >= t.max_rank:
        return "Talent is fully learned."
    if class_level(xp) - 1 <= sum(allocated.values()):
        return "Earn another class level for a talent point."
    if class_level(xp) < t.min_level:
        return f"Requires permanent class level {t.min_level}."
    if sum(allocated.values()) < t.spent_required:
        return f"Requires {t.spent_required} allocated points."
    for parent, rank in t.requires.items():
        if allocated.get(parent, 0) < rank:
            return f"Requires {tree[parent].name} Rank {rank}."
    return ""


@dataclass(frozen=True)
class MetaBonuses:
    values: dict[str, float] = field(default_factory=dict)

    def get(self, key: str) -> float:
        return self.values.get(key, 0.0)

    def spell(self, base: str, field_name: str) -> float:
        return self.get(f"spell:{base}:{field_name}")


@dataclass(frozen=True)
class RunLoadout:
    bonuses: MetaBonuses = field(default_factory=MetaBonuses)
    starting_ability: str = ""


def build_loadout(profile: dict[str, Any], cid: str) -> RunLoadout:
    content = load_progression()
    values: dict[str, float] = {}

    def add(effects: dict[str, float], rank: int) -> None:
        for key, value in effects.items():
            values[key] = values.get(key, 0) + value * rank

    for sid, rank in profile.get("shared", {}).items():
        if sid in content.shared:
            add(content.shared[sid].effects, min(content.shared[sid].max_rank, max(0, int(rank))))
    cls = profile["classes"][cid]
    for tid, rank in cls["talents"].items():
        if tid in content.trees[cid]:
            add(content.trees[cid][tid].at_rank(rank), 1)
    selected = cls.get("starting_ability", "")
    prep = content.trees[cid]["preparation"]
    if not cls["talents"].get("preparation") or selected not in prep.starting_options:
        selected = ""
    return RunLoadout(MetaBonuses(values), selected)
