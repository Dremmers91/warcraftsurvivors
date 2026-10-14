"""Bounded read-only rolling rates for developer HUDs; never written to saves."""

from collections import deque


class BalanceMetrics:
    def __init__(self) -> None:
        self.samples: deque[tuple[float, int, int, float]] = deque(maxlen=48)

    def observe(
        self, seconds: float, spawned: int, kills: int, xp: float
    ) -> tuple[float, float, float]:
        current = seconds, spawned, kills, xp
        if self.samples and (seconds < self.samples[-1][0] or seconds - self.samples[-1][0] > 2):
            # Time skips must not manufacture measured arrivals/earnings.
            self.samples.clear()
        if not self.samples or seconds - self.samples[-1][0] >= 0.25:
            self.samples.append(current)
        while len(self.samples) > 1 and seconds - self.samples[0][0] > 10:
            self.samples.popleft()
        first = self.samples[0]
        duration = seconds - first[0]
        if duration <= 0:
            return 0, 0, 0
        return (
            (spawned - first[1]) / duration,
            (kills - first[2]) / duration,
            (xp - first[3]) * 60 / duration,
        )
