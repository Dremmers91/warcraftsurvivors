"""Weighted wave batches, catalog restrictions, scaled rewards and finite-map spawns."""

from __future__ import annotations

import random

from pygame import Vector2

from .content import Content, EnemyDef
from .entities import Enemy
from .waves import RUN_SECONDS, WaveDirector
from .world import VIEW_SIZE, World

# Safety ceiling above the schedule's 4,600 live-enemy density. Encounters bypass it.
ENEMY_LIMIT = 6000


def spawn_interval(seconds: float) -> float:
    return max(0.035, 0.85 / (1 + max(0, seconds) / 75))


def difficulty(seconds: float) -> tuple[float, float, float]:
    seconds = max(0, min(RUN_SECONDS, seconds))
    minute = seconds / 60
    return (
        1 + minute * 0.12 + max(0, minute - 10) ** 1.3 * 0.055,
        min(35, minute * 1.1),
        1 + minute * 0.018,
    )


class Spawner:
    def __init__(self, content: Content, rng: random.Random, world: World) -> None:
        self.content, self.rng, self.world = content, rng, world
        self.director = WaveDirector(content, world.zone_id)
        self.timer = 0.0
        self.next_id = 0
        self.wave_start = -1.0
        self.pending_surge = 0
        self.surge_budget = 0.0

    def pool(self, seconds: float) -> tuple[list[str], list[float]]:
        seconds = max(0, min(RUN_SECONDS, seconds))
        weights = (
            self.director.wave(seconds).weights
            if seconds < RUN_SECONDS
            else dict(zip(self.content.zones[self.world.zone_id].enemies[:2], (7, 3), strict=True))
        )
        kinds = [
            k
            for k in weights
            if self.content.enemies[k].min_time <= seconds <= self.content.enemies[k].max_time
        ]
        return kinds, [weights[k] for k in kinds]

    def position(self, camera: Vector2, player_pos: Vector2, definition: EnemyDef) -> Vector2:
        valid = []
        for _ in range(32):
            candidates = [
                camera + Vector2(-55, self.rng.uniform(0, VIEW_SIZE[1])),
                camera + Vector2(VIEW_SIZE[0] + 55, self.rng.uniform(0, VIEW_SIZE[1])),
                camera + Vector2(self.rng.uniform(0, VIEW_SIZE[0]), -55),
                camera + Vector2(self.rng.uniform(0, VIEW_SIZE[0]), VIEW_SIZE[1] + 55),
            ]
            valid = [p for p in candidates if self.world.clamp(p, 30) == p]
            terrain = [
                p
                for p in valid
                if definition.terrain == "any"
                or (self.world.on_road(p) == (definition.terrain == "road"))
            ]
            if terrain:
                return self.world.resolve(self.rng.choice(terrain), definition.radius)
        # A road can be far from this viewport. Walk back from a real road point
        # outside the viewport instead of breaking the terrain restriction.
        if definition.terrain == "road":
            y = max(
                40, min(8152, camera.y - 100 if camera.y > 100 else camera.y + VIEW_SIZE[1] + 100)
            )
            return self.world.resolve(Vector2(self.world.road_center(y), y), definition.radius)
        return self.world.resolve(
            self.rng.choice(valid) if valid else player_pos + Vector2(700, 0), definition.radius
        )

    def create(
        self,
        seconds: float,
        camera: Vector2,
        player_pos: Vector2,
        kind: str | None = None,
        pos: Vector2 | None = None,
    ) -> Enemy:
        if kind is None:
            kinds, weights = self.pool(seconds)
            kind = self.rng.choices(kinds, weights=weights, k=1)[0]
        definition = self.content.enemies[kind]
        pos = (
            self.position(camera, player_pos, definition)
            if pos is None
            else self.world.resolve(pos, definition.radius)
        )
        wave = self.director.wave(seconds)
        health = definition.health * (1 + (wave.health - 1) * definition.health_scaling)
        self.next_id += 1
        return Enemy(
            self.next_id,
            pos,
            health,
            health,
            definition.speed + wave.speed,
            definition.damage * (1 + (wave.damage - 1) * definition.damage_scaling),
            definition.xp * (1 + (wave.xp - 1) * definition.xp_scaling),
            kind,
            definition.radius,
            sprite=definition.sprite,
            class_xp=definition.class_xp,
            attack_timer=1 + (self.next_id % 13) * 0.15,
        )

    def update(
        self, dt: float, seconds: float, camera: Vector2, player_pos: Vector2, enemies: list[Enemy]
    ) -> None:
        wave = self.director.wave(seconds)
        rate, batch, density = (
            (3.5, 2, ENEMY_LIMIT)
            if seconds >= RUN_SECONDS
            else (wave.rate, wave.batch, wave.density)
        )
        if seconds < RUN_SECONDS and wave.start != self.wave_start:
            self.wave_start = wave.start
            self.pending_surge = wave.surge
            self.surge_budget = 0
        if seconds >= RUN_SECONDS:
            self.pending_surge = 0
        if self.pending_surge:
            self.surge_budget += wave.surge / 3 * dt
            amount = min(
                self.pending_surge,
                int(self.surge_budget + 1e-9),
                max(0, min(ENEMY_LIMIT, density) - len(enemies)),
            )
            for _ in range(amount):
                enemies.append(self.create(seconds, camera, player_pos))
            self.pending_surge -= amount
            self.surge_budget -= amount
        self.timer -= dt
        while self.timer <= 0:
            amount = min(batch, max(0, min(ENEMY_LIMIT, density) - len(enemies)))
            for _ in range(amount):
                enemies.append(self.create(seconds, camera, player_pos))
            self.timer += batch / rate
