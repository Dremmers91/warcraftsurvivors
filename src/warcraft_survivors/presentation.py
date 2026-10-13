"""Read-only simulation observer and bounded reusable cosmetic particle pool."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

from pygame import Vector2

from .asset_manager import facing
from .simulation import Simulation

QUALITIES = ("low", "medium", "high")


@dataclass
class ActorView:
    kind: str
    pos: Vector2
    health: float
    direction: str
    moving: bool = True


@dataclass
class DeathView:
    kind: str
    pos: Vector2
    direction: str
    age: float = 0


@dataclass
class DamageText:
    pos: Vector2
    amount: int
    age: float = 0


@dataclass
class Particle:
    pos: Vector2 = field(default_factory=Vector2)
    velocity: Vector2 = field(default_factory=Vector2)
    life: float = 0
    sprite: str = "spark_gold"


class ScreenShake:
    """Optional cosmetic offset; never mutates the simulation camera."""

    def __init__(self) -> None:
        self.remaining = 0.0
        self.age = 0.0

    def trigger(self) -> None:
        self.remaining, self.age = 0.16, 0

    def update(self, dt: float) -> None:
        self.remaining = max(0, self.remaining - dt)
        self.age += dt

    def offset(self) -> Vector2:
        strength = self.remaining / 0.16 * 2
        return Vector2(
            round(math.sin(self.age * 95) * strength), round(math.cos(self.age * 79) * strength)
        )


class ParticlePool:
    def __init__(self, capacity: int = 240) -> None:
        self.particles = [Particle() for _ in range(capacity)]
        self.free = list(range(capacity))
        self.active: list[int] = []
        self.rng = random.Random(109)

    def clear(self) -> None:
        self.free[:] = range(len(self.particles))
        self.active.clear()

    def emit(self, pos: Vector2, limit: int, sprite: str = "spark_gold") -> None:
        if not self.free or len(self.active) >= limit:
            return
        index = self.free.pop()
        particle = self.particles[index]
        particle.pos.update(pos)
        particle.velocity.update(self.rng.uniform(-18, 18), self.rng.uniform(-30, 8))
        particle.life = self.rng.uniform(0.15, 0.35)
        particle.sprite = sprite
        self.active.append(index)

    def update(self, dt: float) -> None:
        survivors = []
        for index in self.active:
            particle = self.particles[index]
            particle.life -= dt
            if particle.life <= 0:
                self.free.append(index)
            else:
                particle.pos += particle.velocity * dt
                survivors.append(index)
        self.active[:] = survivors


class Presentation:
    def __init__(self, styles: dict[str, Any] | None = None) -> None:
        self.styles = styles or {}
        self.sim: Simulation | None = None
        self.previous_time = 0.0
        self.actors: dict[int, ActorView] = {}
        self.deaths: list[DeathView] = []
        self.damage: list[DamageText] = []
        self.projectile_ids: set[int] = set()
        self.player_pos = Vector2()
        self.player_moving = False
        self.cast_started = -10.0
        self.trail_timer = 0.0
        self.particles = ParticlePool()
        self.quality = "medium"
        self.density = 1.0
        self.shake = ScreenShake()
        self.player_health = 0.0

    def reset(self, sim: Simulation) -> None:
        self.sim = sim
        self.previous_time = sim.elapsed
        self.actors.clear()
        self.deaths.clear()
        self.damage.clear()
        self.projectile_ids.clear()
        self.particles.clear()
        self.player_pos = sim.player.pos.copy()
        self.player_moving = False
        self.cast_started = -10
        self.player_health = sim.player.health
        self.shake = ScreenShake()

    def observe(self, sim: Simulation) -> None:
        if self.quality == "low" or self.density <= 0:
            self.particles.clear()
        if self.density <= 0:
            self.deaths.clear()
            self.damage.clear()
        if self.sim is not sim or sim.elapsed < self.previous_time:
            self.reset(sim)
        dt = max(0, min(0.25, sim.elapsed - self.previous_time))
        if dt == 0 and self.actors:
            return
        if dt > 0:
            self.player_moving = sim.player.pos.distance_squared_to(self.player_pos) > 0.1
        self.player_pos.update(sim.player.pos)
        self.shake.update(dt)
        if sim.player.health < self.player_health:
            self.shake.trigger()
        self.player_health = sim.player.health
        self.previous_time = sim.elapsed
        for death in self.deaths:
            death.age += dt
        self.deaths = [death for death in self.deaths if death.age < 0.4]
        for text in self.damage:
            text.age += dt
        self.damage = [text for text in self.damage if text.age < 0.55]
        limit = 24 if self.quality == "low" else 48 if self.quality == "medium" else 72
        limit = round(limit * self.density)
        alive_ids = {enemy.id for enemy in sim.enemies}
        visible_ids = set()
        for enemy in sim.grid.nearby(sim.camera.pos + Vector2(640, 360), 960):
            visible_ids.add(enemy.id)
            previous = self.actors.get(enemy.id)
            movement = enemy.pos - previous.pos if previous else sim.player.pos - enemy.pos
            direction = (
                facing(movement)
                if movement.length_squared() > 0.1
                else previous.direction
                if previous
                else "south"
            )
            if (
                previous
                and enemy.health < previous.health
                and len(self.damage) < limit
                and self.quality != "low"
            ):
                self.damage.append(
                    DamageText(enemy.pos.copy(), round(previous.health - enemy.health))
                )
            if previous:
                previous.pos.update(enemy.pos)
                previous.health = enemy.health
                previous.direction = direction
                previous.moving = movement.length_squared() > 0.1
            else:
                self.actors[enemy.id] = ActorView(
                    enemy.sprite or enemy.kind, enemy.pos.copy(), enemy.health, direction, True
                )
        for eid in set(self.actors) - visible_ids:
            previous = self.actors.pop(eid)
            if eid not in alive_ids and len(self.deaths) < limit:
                self.deaths.append(
                    DeathView(previous.kind, previous.pos.copy(), previous.direction)
                )
        ids = {id(shot) for shot in sim.projectiles}
        if ids - self.projectile_ids:
            self.cast_started = sim.elapsed
        self.projectile_ids = ids
        self.particles.update(dt)
        self.trail_timer -= dt
        if self.trail_timer <= 0:
            budget = {"low": 0, "medium": 120, "high": 240}[self.quality]
            if len(sim.enemies) > 500:
                budget = min(budget, 64)
            budget = round(budget * self.density)
            for shot in sim.projectiles:
                self.particles.emit(
                    shot.pos, budget, self.styles.get(shot.ability, {}).get("trail", "spark_gold")
                )
            self.trail_timer = 0.035

    def player_state(self, sim: Simulation) -> tuple[str, float]:
        if self.player_moving:
            return "walk", sim.elapsed
        if sim.player.cast_age < 0.3:
            return "cast", sim.player.cast_age
        if sim.elapsed - self.cast_started < 0.3:
            return "cast", sim.elapsed - self.cast_started
        return "idle", sim.elapsed
