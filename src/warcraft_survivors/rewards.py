"""Permanent run rewards; deliberately independent from gem XP and run levels."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .meta import load_progression

ACHIEVEMENTS = {
    aid: (a.name, a.description, a.gold) for aid, a in load_progression().achievements.items()
}


@dataclass(frozen=True)
class RunRewards:
    class_xp: int
    gold: int
    achievements: tuple[str, ...]


def calculate_rewards(
    kills: int,
    elites: int,
    seconds: float,
    won: bool,
    gold: int,
    evolved: int,
    earned: Iterable[str] = (),
    class_xp_kills: int | None = None,
) -> RunRewards:
    if min(kills, elites, seconds, gold, evolved) < 0 or (
        class_xp_kills is not None and class_xp_kills < 0
    ):
        raise ValueError("Run counters cannot be negative")
    survival = min(1800, seconds)
    if won and seconds < 1800:
        raise ValueError("A successful full run must reach 30 minutes")
    kill_xp = kills // 3 + elites * 100 if class_xp_kills is None else class_xp_kills
    class_xp = kill_xp + int(survival / 6) + (5000 if won else 0)
    base_gold = gold + kills // 8 + int(survival / 20) + (1500 if won else 0)
    # Catalog rewards include elite gold in the collected bank. Legacy callers
    # lack that bank metadata and retain their explicit per-elite bonus.
    if class_xp_kills is None:
        base_gold += elites * 30
    achieved = {
        "first_blood": kills > 0,
        "centurion": kills >= 100,
        "survivor": seconds >= 300,
        "elite": elites > 0,
        "evolution": evolved > 0,
        "victory": won,
    }
    existing = set(earned)
    fresh = tuple(aid for aid, ok in achieved.items() if ok and aid not in existing)
    return RunRewards(class_xp, base_gold + sum(ACHIEVEMENTS[a][2] for a in fresh), fresh)
