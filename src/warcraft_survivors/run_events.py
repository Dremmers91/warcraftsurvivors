"""Authoritative, deduplicated run facts; profiles store summaries, not every death."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .simulation import Simulation


@dataclass(frozen=True)
class DeathEvent:
    run_id: str
    enemy_id: int
    enemy_type: str
    family: str
    faction: str
    zone: str
    elite: bool
    boss: str
    source: str
    school: str
    owner: str
    delivery: str

    @property
    def event_id(self) -> str:
        return f"{self.run_id}:{self.enemy_id}"


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    zone: str
    enemy_kills: dict[str, int]
    family_kills: dict[str, int]
    faction_kills: dict[str, int]
    damage_kills: dict[str, int]
    source_kills: dict[str, int]
    boss_zone_kills: dict[str, int]
    evolved_spells: tuple[str, ...]
    best_run_level: int
    max_spell_rank: int
    max_automatic_slots: int
    chests_opened: int
    no_heal_survival: int
    untouched_bosses: int
    no_manual_wins: int
    dragon_bosses: int


@dataclass
class RunLedger:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    seen: set[int] = field(default_factory=set)
    enemy_kills: dict[str, int] = field(default_factory=dict)
    family_kills: dict[str, int] = field(default_factory=dict)
    faction_kills: dict[str, int] = field(default_factory=dict)
    damage_kills: dict[str, int] = field(default_factory=dict)
    source_kills: dict[str, int] = field(default_factory=dict)
    boss_zone_kills: dict[str, int] = field(default_factory=dict)
    evolved_spells: set[str] = field(default_factory=set)
    best_run_level: int = 1
    max_spell_rank: int = 1
    max_automatic_slots: int = 1
    chests_opened: int = 0
    healing_pickups: int = 0
    manual_uses: int = 0
    no_heal_survival: float = 0
    untouched_bosses: int = 0
    dragon_bosses: int = 0
    last_event: DeathEvent | None = None

    def record(self, event: DeathEvent) -> bool:
        if event.run_id != self.run_id or event.enemy_id in self.seen:
            return False
        self.seen.add(event.enemy_id)
        self.last_event = event
        if event.owner == "player":
            for counters, key in (
                (self.enemy_kills, event.enemy_type),
                (self.family_kills, event.family),
                (self.faction_kills, event.faction),
                (self.damage_kills, event.school),
                (self.source_kills, event.source),
            ):
                if key:
                    counters[key] = counters.get(key, 0) + 1
            if event.boss:
                key = f"{event.zone}:{event.boss}"
                self.boss_zone_kills[key] = self.boss_zone_kills.get(key, 0) + 1
                self.dragon_bosses += int(event.family == "dragon")
        return True

    def observe(self, sim: Simulation) -> None:
        self.best_run_level = max(self.best_run_level, sim.player.level)
        self.max_automatic_slots = max(self.max_automatic_slots, len(sim.player.spells))
        self.max_spell_rank = max(
            self.max_spell_rank, max((s.rank for s in sim.player.spells.values()), default=0)
        )
        if not self.healing_pickups:
            self.no_heal_survival = max(self.no_heal_survival, sim.elapsed)

    def summary(self, sim: Simulation) -> RunSummary:
        self.observe(sim)
        return RunSummary(
            self.run_id,
            sim.zone.id,
            self.enemy_kills.copy(),
            self.family_kills.copy(),
            self.faction_kills.copy(),
            self.damage_kills.copy(),
            self.source_kills.copy(),
            self.boss_zone_kills.copy(),
            tuple(sorted(self.evolved_spells)),
            self.best_run_level,
            self.max_spell_rank,
            self.max_automatic_slots,
            self.chests_opened,
            int(self.no_heal_survival + 1e-7),
            self.untouched_bosses,
            int(sim.won and self.manual_uses == 0),
            self.dragon_bosses,
        )
