"""Catalog-driven achievement requirements, availability and one-time rewards."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .content import load_content
from .meta import Achievement, class_level, load_progression
from .run_events import RunSummary

CATEGORIES = {
    "combat": "Combat",
    "exploration": "Exploration and Bosses",
    "builds": "Spells and Builds",
    "mastery": "Class Mastery",
    "survival": "Survival Challenges",
}
COUNT_MAPS = (
    "enemy_kills",
    "family_kills",
    "faction_kills",
    "damage_kills",
    "source_kills",
    "boss_zone_kills",
    "zone_wins",
    "zone_survival",
)
NEW_COUNTS = (
    "best_run_level",
    "max_spell_rank",
    "max_automatic_slots",
    "chests_opened",
    "no_heal_survival",
    "untouched_bosses",
    "no_manual_wins",
    "dragon_bosses",
)


def metric_label(metric: str, cid: str = "") -> str:
    """Player-facing requirement labels; counter keys stay internal."""
    prefix, _, key = metric.partition(":")
    gameplay = load_content()
    if prefix == "evolved" and key:
        return gameplay.abilities[key].name + " evolutions"
    if prefix == "class_win":
        return load_progression().classes[key].name + " victories"
    if prefix == "boss_zone":
        zid, bid = key.split(":", 1)
        return gameplay.bosses[bid].name.split(" - ")[0] + " defeats in " + gameplay.zones[zid].name
    if prefix == "boss":
        return gameplay.bosses[key].name.split(" - ")[0] + " defeats"
    if prefix == "zone_survival":
        return gameplay.zones[key].name + " survival seconds"
    if prefix == "family":
        return key.title() + " defeats"
    if prefix == "faction":
        return key.title() + " defeats"
    if metric == "class_level" and cid:
        return load_progression().classes[cid].name + " permanent level"
    return {
        "kills": "Enemies defeated",
        "run_kills": "Most kills in one run",
        "elites": "Elites defeated",
        "best_time": "Best survival seconds",
        "hogger": "Hogger defeats",
        "evolved": "Spell evolutions",
        "class_level": "Highest permanent class level",
        "winning_classes": "Starting classes with a victory",
        "winning_zones": "Zones with a victory",
        "distinct_evolutions": "Different spells evolved",
        "elemental_kills": "Fire, Frost and Nature defeats",
        "max_automatic_slots": "Automatic spells equipped",
        "max_spell_rank": "Highest automatic spell rank",
        "chests_opened": "Elite chests opened",
        "best_run_level": "Highest level during a run",
        "no_heal_survival": "Survival seconds before a healing pickup",
        "untouched_bosses": "Bosses defeated without taking damage",
        "no_manual_wins": "Victories without manual abilities",
        "dragon_bosses": "Dragon bosses defeated",
    }.get(metric, metric.replace("_", " ").title())


def metric_value(data: dict[str, Any], metric: str, cid: str = "") -> int:
    stats = data["stats"]
    initial = [key for key, entry in load_progression().classes.items() if entry.playable]
    if metric == "class_level":
        return max(class_level(data["classes"][key]["xp"]) for key in ([cid] if cid else initial))
    if metric == "winning_classes":
        return sum(stats["class_wins"].get(key, 0) > 0 for key in initial)
    if metric == "winning_zones":
        return sum(stats.get("zone_wins", {}).get(zid, 0) > 0 for zid in load_progression().zones)
    if metric == "distinct_evolutions":
        return len(stats.get("evolved_spells", []))
    if metric.startswith("evolved:"):
        return int(metric.split(":", 1)[1] in stats.get("evolved_spells", []))
    if metric == "elemental_kills":
        return sum(
            stats.get("damage_kills", {}).get(school, 0) for school in ("fire", "frost", "nature")
        )
    if metric == "hogger":
        return int(stats["boss_kills"].get("hogger", 0))
    prefix, _, key = metric.partition(":")
    maps = {
        "boss": "boss_kills",
        "class_win": "class_wins",
        "family": "family_kills",
        "faction": "faction_kills",
        "damage": "damage_kills",
        "source": "source_kills",
        "enemy": "enemy_kills",
        "zone": "zone_wins",
        "boss_zone": "boss_zone_kills",
        "zone_survival": "zone_survival",
    }
    if key and prefix in maps:
        return int(stats.get(maps[prefix], {}).get(key, 0))
    return int(stats.get(metric, 0))


def progress(data: dict[str, Any], achievement: Achievement) -> int:
    values = [metric_value(data, c.metric, achievement.class_id) for c in achievement.conditions]
    if len(values) == 1:
        return values[0]
    return min(
        int(min(1, value / c.target) * achievement.target)
        for value, c in zip(values, achievement.conditions, strict=True)
    )


def state(data: dict[str, Any], achievement: Achievement) -> str:
    if achievement.id in data["achievements"]:
        return "completed"
    if not achievement.available:
        return "unavailable"
    if any(aid not in data["achievements"] for aid in achievement.prerequisites):
        return "locked"
    return "incomplete"


def reward_text(achievement: Achievement) -> str:
    meta = load_progression()
    parts = []
    for reward in achievement.rewards:
        parts.append(
            f"{reward.value} gold"
            if reward.kind == "gold"
            else meta.classes[reward.target].name + " unlock (Coming Soon)"
            if reward.kind == "class"
            else "Shop: " + meta.shared[reward.target].name
        )
    return " · ".join(parts) or "Achievement record"


def apply_summary(data: dict[str, Any], summary: RunSummary, seconds: float, won: bool) -> None:
    stats = data["stats"]
    for name in COUNT_MAPS[:6]:
        counters = getattr(summary, name)
        for key, value in counters.items():
            if (
                not isinstance(key, str)
                or not 0 < len(key) <= 96
                or isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
            ):
                raise ValueError("Invalid run event counter")
            stats[name][key] = stats[name].get(key, 0) + value
    for name in NEW_COUNTS:
        value = getattr(summary, name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("Invalid run fact")
        stats[name] = (
            max(stats[name], value)
            if name
            in {"best_run_level", "max_spell_rank", "max_automatic_slots", "no_heal_survival"}
            else stats[name] + value
        )
    if any(aid not in load_content().abilities for aid in summary.evolved_spells):
        raise ValueError("Unknown evolved spell")
    stats["evolved_spells"] = sorted(set(stats["evolved_spells"]) | set(summary.evolved_spells))
    if summary.zone not in load_progression().zones:
        raise ValueError("Unknown run zone")
    stats["zone_survival"][summary.zone] = max(
        stats["zone_survival"].get(summary.zone, 0), int(seconds)
    )
    if won:
        stats["zone_wins"][summary.zone] = stats["zone_wins"].get(summary.zone, 0) + 1


def complete(data: dict[str, Any]) -> tuple[list[str], int]:
    fresh: list[str] = []
    gold = 0
    catalog = load_progression().achievements
    for _ in range(len(catalog)):
        added = False
        for aid, achievement in catalog.items():
            data["achievement_progress"][aid] = progress(data, achievement)
            if state(data, achievement) not in {"incomplete"}:
                continue
            if all(
                metric_value(data, c.metric, achievement.class_id) >= c.target
                for c in achievement.conditions
            ):
                data["achievements"].append(aid)
                data["achievement_completed_at"][aid] = datetime.now(UTC).isoformat(
                    timespec="seconds"
                )
                fresh.append(aid)
                gold += achievement.gold
                added = True
        if not added:
            break
    return fresh, gold
