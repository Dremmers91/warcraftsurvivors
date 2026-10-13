"""Minute-based wave selection and idempotent scheduled encounter events."""

from __future__ import annotations

from bisect import bisect_right

from .content import Content, WaveDef

RUN_SECONDS = 1800.0
ELITE_TIMES = (300.0, 600.0, 900.0, 1200.0, 1500.0)


class WaveDirector:
    def __init__(self, content: Content, zone_id: str = "elwynn") -> None:
        self.content = content
        self.waves = content.waves if zone_id == "elwynn" else content.zones[zone_id].waves
        self.starts = tuple(w.start for w in self.waves)
        self.elite_events: set[float] = set()
        self.boss_spawned = False

    def wave(self, seconds: float) -> WaveDef:
        return self.waves[max(0, min(29, bisect_right(self.starts, max(0, seconds)) - 1))]

    def due_elites(self, seconds: float) -> list[float]:
        if seconds + 1e-8 >= RUN_SECONDS:
            return []
        due = [t for t in ELITE_TIMES if t <= seconds + 1e-8 and t not in self.elite_events]
        self.elite_events.update(due)
        return due

    def boss_due(self, seconds: float) -> bool:
        return seconds + 1e-8 >= RUN_SECONDS and not self.boss_spawned

    def seek(self, seconds: float) -> None:
        # Explicit debug seeks skip past events rather than producing a five-elite burst.
        self.elite_events.update(t for t in ELITE_TIMES if t < seconds - 1e-8)
