"""Frame-independent exponential follow, always clamped to finite terrain."""

from __future__ import annotations

import math

from pygame import Vector2

from .world import World


class Camera:
    def __init__(self, player_pos: Vector2, response: float = 9) -> None:
        self.pos = World.camera(player_pos)
        self.response = response

    def update(self, player_pos: Vector2, dt: float) -> None:
        target = World.camera(player_pos)
        self.pos += (target - self.pos) * (1 - math.exp(-self.response * dt))
