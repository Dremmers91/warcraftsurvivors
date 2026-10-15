"""Finite deterministic terrain and reusable spatial queries."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pygame import Vector2

from .content import LandmarkDef

WORLD_SIZE = 8192
CHUNK_SIZE = 256
VIEW_SIZE = (1280, 720)


class Located(Protocol):
    @property
    def pos(self) -> Vector2: ...


T = TypeVar("T", bound=Located)


class SpatialHash(Generic[T]):
    def __init__(self, cell_size: int = 96) -> None:
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], list[T]] = defaultdict(list)
        self.track_queries = False
        self.queries = 0
        self.candidate_checks = 0

    def reset_metrics(self) -> None:
        self.queries = self.candidate_checks = 0

    def rebuild(self, entities: Iterable[T]) -> None:
        self.cells.clear()
        for entity in entities:
            self.cells[self.key(entity.pos)].append(entity)

    def insert(self, entity: T) -> None:
        self.cells[self.key(entity.pos)].append(entity)

    def key(self, pos: Vector2) -> tuple[int, int]:
        return math.floor(pos.x / self.cell_size), math.floor(pos.y / self.cell_size)

    def items(self) -> Iterable[T]:
        for cell in self.cells.values():
            yield from cell

    def nearby(self, pos: Vector2, radius: float) -> Iterable[T]:
        if self.track_queries:
            self.queries += 1
        size = self.cell_size
        lo = (math.floor((pos.x - radius) / size), math.floor((pos.y - radius) / size))
        hi = (math.floor((pos.x + radius) / size), math.floor((pos.y + radius) / size))
        r2 = radius * radius
        for x in range(lo[0], hi[0] + 1):
            for y in range(lo[1], hi[1] + 1):
                cell = self.cells.get((x, y), ())
                if self.track_queries:
                    for entity in cell:
                        self.candidate_checks += 1
                        if entity.pos.distance_squared_to(pos) <= r2:
                            yield entity
                else:
                    # Keep instrumentation out of every candidate's hot path.
                    for entity in cell:
                        if entity.pos.distance_squared_to(pos) <= r2:
                            yield entity


@dataclass(frozen=True)
class Obstacle:
    pos: Vector2
    radius: float
    style: int


class World:
    def __init__(
        self, seed: int = 41, zone_id: str = "elwynn", landmarks: tuple[LandmarkDef, ...] = ()
    ) -> None:
        self.seed = seed
        self.zone_id = zone_id
        self.landmarks = landmarks
        rng = random.Random(seed)
        self.obstacles: list[Obstacle] = []
        for _ in range(1100):
            pos = Vector2(rng.randrange(80, WORLD_SIZE - 80), rng.randrange(80, WORLD_SIZE - 80))
            if not self.on_road(pos) and pos.distance_to(Vector2(4096, 4096)) > 240:
                style = (
                    rng.randrange(3)
                    if zone_id == "elwynn"
                    else rng.choices([0, 1, 3], [65, 30, 5])[0]
                    if zone_id == "duskwood"
                    else rng.choices([0, 2, 3], [60, 35, 5])[0]
                )
                self.obstacles.append(Obstacle(pos, rng.uniform(17, 26), style))
        for point in landmarks:
            pos = Vector2(point.x, point.y)
            self.obstacles = [
                o
                for o in self.obstacles
                if o.pos.distance_squared_to(pos) > (point.radius + 90) ** 2
            ]
            if point.radius > 0:
                self.obstacles.append(Obstacle(pos, point.radius, point.style))
        self.max_obstacle_radius = max((o.radius for o in self.obstacles), default=28)
        self.grid: SpatialHash[Obstacle] = SpatialHash(256)
        self.grid.rebuild(self.obstacles)

    def road_center(self, y: float) -> float:
        return 4096 + math.sin(y / (620 if self.zone_id == "elwynn" else 480)) * (
            0 if self.zone_id == "icecrown" else 210 if self.zone_id == "stranglethorn" else 145
        )

    def on_road(self, pos: Vector2) -> bool:
        horizontal = 4096 + (math.sin(pos.x / 510) * 170 if self.zone_id == "stranglethorn" else 0)
        return abs(pos.x - self.road_center(pos.y)) < 75 or abs(pos.y - horizontal) < 65

    @staticmethod
    def clamp(pos: Vector2, margin: float = 16) -> Vector2:
        return Vector2(
            max(margin, min(WORLD_SIZE - margin, pos.x)),
            max(margin, min(WORLD_SIZE - margin, pos.y)),
        )

    def resolve(self, pos: Vector2, radius: float = 14) -> Vector2:
        result = self.clamp(pos, radius)
        for _ in range(3):
            adjusted = False
            for obstacle in self.grid.nearby(result, radius + self.max_obstacle_radius):
                delta = result - obstacle.pos
                distance = delta.length()
                if distance < radius + obstacle.radius:
                    normal = delta / distance if distance > 0.001 else Vector2(1, 0)
                    result = obstacle.pos + normal * (radius + obstacle.radius + 0.1)
                    adjusted = True
            if not adjusted:
                break
        return self.clamp(result, radius)

    def move(self, pos: Vector2, displacement: Vector2, radius: float = 14) -> Vector2:
        # Swept substeps prevent a fast-moving body from jumping through trunks.
        steps = max(1, math.ceil(displacement.length() / max(1, radius * 0.5)))
        result = pos.copy()
        for _ in range(steps):
            result = self.resolve(result + displacement / steps, radius)
        return result

    @staticmethod
    def camera(pos: Vector2) -> Vector2:
        return Vector2(
            max(0, min(WORLD_SIZE - VIEW_SIZE[0], pos.x - VIEW_SIZE[0] / 2)),
            max(0, min(WORLD_SIZE - VIEW_SIZE[1], pos.y - VIEW_SIZE[1] / 2)),
        )
