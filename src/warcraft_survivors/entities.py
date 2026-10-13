"""Mutable per-run state; companions deliberately have no health or enemy identity."""

from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Vector2

from .meta import MetaBonuses
from .progression import xp_required


@dataclass
class SpellState:
    rank: int = 1
    timer: float = 0.0
    modifiers: set[str] = field(default_factory=set)


@dataclass
class ManualState:
    id: str
    rank: int = 1
    timer: float = 0
    circle: Vector2 | None = None


@dataclass
class Player:
    pos: Vector2
    health: float
    max_health: float
    base_speed: float
    armor: float
    facing: Vector2 = field(default_factory=lambda: Vector2(0, 1))
    radius: float = 14
    level: int = 1
    xp: float = 0
    spells: dict[str, SpellState] = field(default_factory=dict)
    passives: dict[str, int] = field(default_factory=dict)
    hurt_timer: float = 0
    power: float = 0
    invulnerable: bool = False
    manual: ManualState | None = None
    immune: float = 0
    guard: float = 0
    guard_strength: float = 0.5
    shield: float = 0
    shield_time: float = 0
    buff_time: float = 0
    buff_power: float = 0
    buff_school: str = ""
    pet_buff: bool = False
    rooted: float = 0
    block_regen: float = 0
    rally_bonus: float = 0
    rally_time: float = 0
    last_damage_school: str = ""
    meta: MetaBonuses = field(default_factory=MetaBonuses)
    slow_time: float = 0
    slow_strength: float = 0
    cast_age: float = 10
    healing_budget: float = 6
    wound_time: float = 0

    @property
    def xp_required(self) -> float:
        return xp_required(self.level)

    def passive(self, name: str) -> int:
        return self.passives.get(name, 0)


@dataclass
class Status:
    ability: str
    damage: float
    remaining: float
    timer: float = 0
    slow: float = 0
    spread: bool = False
    burst: bool = False
    radius_scale: float = 1


@dataclass
class Enemy:
    id: int
    pos: Vector2
    health: float
    max_health: float
    speed: float
    damage: float
    xp: float
    kind: str = "kobold"
    radius: float = 13
    flash: float = 0
    statuses: dict[str, Status] = field(default_factory=dict)
    fear: float = 0
    elite: bool = False
    last_damage_school: str = ""
    owner: str = ""
    sprite: str = ""
    elite_id: str = ""
    boss_id: str = ""
    class_xp: int = 1
    gold_reward: int = 0
    attack_timer: float = 1
    attack_index: int = 0
    busy: float = 0
    cast_age: float = 0
    facing: Vector2 = field(default_factory=lambda: Vector2(0, 1))
    move_time: float = 0
    enraged: bool = False
    steering_time: float = 0
    avoidance: Vector2 = field(default_factory=Vector2)
    separation: Vector2 = field(default_factory=Vector2)


@dataclass
class HostileAttack:
    owner: Enemy
    attack: str
    pos: Vector2
    direction: Vector2
    warning: float
    remaining: float
    damage: float
    age: float = 0
    started: bool = False
    hit_player: bool = False
    pulse_time: float = 0


@dataclass
class HostileProjectile:
    pos: Vector2
    velocity: Vector2
    damage: float
    radius: float
    effect: str
    life: float = 4
    pull: float = 0
    slow: float = 0
    slow_duration: float = 0
    origin: Vector2 = field(default_factory=Vector2)
    armor_penetration: float = 0


@dataclass
class Projectile:
    pos: Vector2
    velocity: Vector2
    ability: str
    damage: float
    radius: float
    pierce: int
    life: float = 3
    hit: set[int] = field(default_factory=set)
    bounces: int = 0
    age: float = 0
    returning: bool = False
    orbit_angle: float | None = None
    orbit_radius: float = 0
    pulse: float = 0
    target: Enemy | None = None
    target_timer: float = 0


@dataclass
class Field:
    pos: Vector2
    ability: str
    damage: float
    radius: float
    life: float
    velocity: Vector2 = field(default_factory=Vector2)
    follow: bool = False
    persistent: bool = False
    timer: float = 0
    delay: float = 0
    age: float = 0
    wave: bool = False
    hit: set[int] = field(default_factory=set)


@dataclass
class Companion:
    pos: Vector2
    ability: str
    owner: Player
    sprite: str
    life: float = -1
    timer: float = 0
    facing: Vector2 = field(default_factory=lambda: Vector2(0, 1))
    attack_time: float = 0
    velocity: Vector2 = field(default_factory=Vector2)
    hit: set[int] = field(default_factory=set)
    leash: float = 320
    target: Enemy | None = None
    target_timer: float = 0
    leap_timer: float = 0
    moving: bool = False
    formation: int = 0


@dataclass
class Pickup:
    pos: Vector2
    kind: str
    value: float
    born: float = 0


@dataclass
class Visual:
    pos: Vector2
    radius: float
    color: tuple[int, int, int]
    life: float
    total: float
    effect: str = ""
    direction: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    end: Vector2 | None = None
