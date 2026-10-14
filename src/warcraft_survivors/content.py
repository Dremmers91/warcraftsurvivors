"""Validated content contracts shared by all classes and reusable behaviors."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from importlib.resources import files

SCHOOLS = {
    "holy": (255, 220, 112),
    "physical": (217, 157, 144),
    "fire": (255, 116, 48),
    "frost": (103, 219, 255),
    "arcane": (212, 133, 255),
    "shadow": (165, 100, 224),
    "nature": (126, 224, 106),
}
KINDS = {
    "projectile",
    "area",
    "arc",
    "field",
    "wave",
    "chain",
    "dot",
    "orbit",
    "companion",
    "charge",
    "beam",
}


@dataclass(frozen=True)
class Rank:
    damage: float
    cooldown: float
    radius: float
    count: int
    pierce: int = 0
    duration: float = 3
    description: str = ""


@dataclass(frozen=True)
class Mechanics:
    radial_rank: int = 99
    spread: float = 12
    homing: bool = False
    bounce: int = 0
    splash: float = 0
    dot: float = 0
    slow: float = 0
    execute: float = 0
    heal: float = 0
    knockback: float = 0
    follow: bool = False
    persistent: bool = False
    pulse: float = 0.5
    angle: float = 100
    chain: int = 1
    summon: str = "wolf"
    delay: float = 0
    returning: bool = False
    spread_dot: bool = False
    death_burst: bool = False
    stationary: bool = False
    shield: float = 0
    leash: float = 320
    ranged: bool = False
    attack_range: float = 240
    range_per_rank: float = 10
    movement_speed: float = 270
    extra_pets: int = 0
    volley_rank: int = 99
    volley_count: int = 1
    splash_rank: int = 1
    dot_rank: int = 1
    leap_rank: int = 99
    leap_distance: float = 100


@dataclass(frozen=True)
class Evolution:
    id: str
    name: str
    passive: str
    description: str
    kind: str
    mechanics: Mechanics


@dataclass(frozen=True)
class Ability:
    id: str
    name: str
    kind: str
    school: str
    speed: float
    ranks: tuple[Rank, ...]
    description: str = ""
    mechanics: Mechanics = field(default_factory=Mechanics)
    evolution: Evolution | None = None
    base_id: str = ""
    effect: str = ""

    @property
    def color(self) -> tuple[int, int, int]:
        return SCHOOLS[self.school]

    @property
    def evolved(self) -> bool:
        return bool(self.base_id)


@dataclass(frozen=True)
class ManualRank:
    cooldown: float
    duration: float
    power: float
    distance: float
    description: str


@dataclass(frozen=True)
class Manual:
    id: str
    name: str
    kind: str
    school: str
    ranks: tuple[ManualRank, ...]
    description: str
    direction: float = 1
    root: bool = False
    regen: float = 0
    shield_fraction: float = 0
    buff_school: str = ""
    pet_buff: bool = False


@dataclass(frozen=True)
class ClassDef:
    id: str
    name: str
    school: str
    health: float
    speed: float
    armor: float
    abilities: tuple[str, ...]
    manuals: tuple[str, ...] = ()


@dataclass(frozen=True)
class Passive:
    id: str
    name: str
    description: str
    max_rank: int = 5
    applicability: str = "All abilities"


@dataclass(frozen=True)
class EnemyDef:
    id: str
    name: str
    health: float
    speed: float
    damage: float
    xp: float
    radius: float
    weight: float
    color: tuple[int, int, int]
    behavior: str = "chase"
    sprite: str = ""
    attacks: tuple[str, ...] = ()
    min_time: float = 0
    max_time: float = 1800
    terrain: str = "any"
    health_scaling: float = 1
    damage_scaling: float = 1
    xp_scaling: float = 1
    class_xp: int = 1
    gold_chance: float = 0.1
    family: str = "humanoid"
    faction: str = ""


@dataclass(frozen=True)
class AttackDef:
    id: str
    name: str
    kind: str
    damage: float
    cooldown: float
    warning: float
    duration: float
    radius: float
    reach: float
    speed: float = 0
    count: int = 1
    angle: float = 100
    color: tuple[int, int, int] = (255, 124, 68)
    effect: str = "hostile_arrow"
    pulse: float = 0
    growth: float = 0
    pull: float = 0
    slow: float = 0
    slow_duration: float = 0
    armor_penetration: float = 0
    health_damage: float = 0


@dataclass(frozen=True)
class WaveDef:
    start: float
    name: str
    rate: float
    batch: int
    density: int
    health: float
    damage: float
    xp: float
    speed: float
    weights: dict[str, float]
    surge: int = 0


@dataclass(frozen=True)
class EliteDef:
    id: str
    name: str
    enemy: str
    sprite: str
    health: float
    damage: float
    attacks: tuple[str, ...]
    class_xp: int
    gold: int
    xp: float = 12
    radius_scale: float = 1.55


@dataclass(frozen=True)
class BossDef:
    id: str
    name: str
    sprite: str
    health: float
    damage: float
    speed: float
    radius: float
    xp: float
    class_xp: int
    gold: int
    attacks: tuple[str, ...]
    enrage: float = 0.5
    enrage_cooldown: float = 0.72
    enrage_damage: float = 1.25
    family: str = "humanoid"


@dataclass(frozen=True)
class LandmarkDef:
    name: str
    x: float
    y: float
    style: int
    radius: float


@dataclass(frozen=True)
class ZoneDef:
    id: str
    name: str
    description: str
    difficulty: float
    seed: int
    ground: str
    road: str
    props: tuple[str, ...]
    enemies: tuple[str, ...]
    elites: tuple[str, ...]
    boss_pool: tuple[str, ...]
    waves: tuple[WaveDef, ...]
    music: str
    landmarks: tuple[LandmarkDef, ...]


@dataclass(frozen=True)
class Content:
    classes: dict[str, ClassDef]
    abilities: dict[str, Ability]
    passives: dict[str, Passive]
    enemies: dict[str, EnemyDef]
    manuals: dict[str, Manual] = field(default_factory=dict)
    evolutions: dict[str, Ability] = field(default_factory=dict)
    waves: tuple[WaveDef, ...] = ()
    attacks: dict[str, AttackDef] = field(default_factory=dict)
    elites: dict[str, EliteDef] = field(default_factory=dict)
    bosses: dict[str, BossDef] = field(default_factory=dict)
    boss_pool: tuple[str, ...] = ("hogger",)
    zones: dict[str, ZoneDef] = field(default_factory=dict)

    def ability(self, aid: str) -> Ability:
        return self.abilities[aid] if aid in self.abilities else self.evolutions[aid]


def load_content() -> Content:
    raw = json.loads(files(__package__).joinpath("data/content.json").read_text("utf-8"))
    expansion = json.loads(files(__package__).joinpath("data/zones.json").read_text("utf-8"))
    raw["enemies"].extend(expansion["enemies"])
    abilities: dict[str, Ability] = {}
    evolutions: dict[str, Ability] = {}
    for row in raw["abilities"]:
        fields = {k: v for k, v in row.items() if k not in {"ranks", "mechanics", "evolution"}}
        evolution = row.get("evolution")
        evo = (
            Evolution(
                **{k: v for k, v in evolution.items() if k != "mechanics"},
                mechanics=Mechanics(**evolution["mechanics"]),
            )
            if evolution
            else None
        )
        ability = Ability(
            **fields,
            ranks=tuple(Rank(**r) for r in row["ranks"]),
            mechanics=Mechanics(**row.get("mechanics", {})),
            evolution=evo,
        )
        if ability.id in abilities or ability.kind not in KINDS or ability.school not in SCHOOLS:
            raise ValueError(f"Invalid spell: {ability.id}")
        if len(ability.ranks) != 8 or any(
            r.damage <= 0 or r.cooldown <= 0 or r.radius <= 0 or r.count < 1 or r.duration <= 0
            for r in ability.ranks
        ):
            raise ValueError(f"Invalid spell ranks: {ability.id}")
        for mechanics in (ability.mechanics, evo.mechanics if evo else ability.mechanics):
            if (
                mechanics.leash <= 0
                or mechanics.movement_speed <= 0
                or mechanics.attack_range <= 0
                or mechanics.range_per_rank < 0
                or mechanics.extra_pets < 0
                or mechanics.volley_count < 1
                or min(
                    mechanics.volley_rank,
                    mechanics.splash_rank,
                    mechanics.dot_rank,
                    mechanics.leap_rank,
                )
                < 1
                or mechanics.leap_distance < 0
            ):
                raise ValueError(f"Invalid companion mechanics: {ability.id}")
        abilities[ability.id] = ability
        if evo:
            if evo.kind not in KINDS or evo.id in evolutions or evo.id in abilities:
                raise ValueError(f"Invalid evolution: {evo.id}")
            evolutions[evo.id] = replace(
                ability,
                id=evo.id,
                name=evo.name,
                kind=evo.kind,
                mechanics=evo.mechanics,
                base_id=ability.id,
                description=evo.description,
                evolution=None,
                effect=evo.id,
            )
    manuals = {
        row["id"]: Manual(
            **{k: v for k, v in row.items() if k != "ranks"},
            ranks=tuple(ManualRank(**r) for r in row["ranks"]),
        )
        for row in raw.get("manuals", [])
    }
    if len(manuals) != len(raw.get("manuals", [])) or any(
        len(m.ranks) != 3
        or m.kind
        not in {
            "immune",
            "heal",
            "buff",
            "leap",
            "guard",
            "rally",
            "blink",
            "circle",
            "shield",
            "fear",
        }
        or m.school not in SCHOOLS
        or any(r.cooldown <= 0 or r.duration <= 0 or r.power <= 0 for r in m.ranks)
        for m in manuals.values()
    ):
        raise ValueError("Invalid manual definition")
    classes: dict[str, ClassDef] = {}
    for row in raw["classes"]:
        cls = ClassDef(
            **{k: v for k, v in row.items() if k not in {"abilities", "manuals"}},
            abilities=tuple(row["abilities"]),
            manuals=tuple(row.get("manuals", [])),
        )
        if (
            cls.id in classes
            or not cls.abilities
            or any(a not in abilities for a in cls.abilities)
            or any(m not in manuals for m in cls.manuals)
        ):
            raise ValueError(f"Invalid class: {cls.id}")
        classes[cls.id] = cls
    passives = {row["id"]: Passive(**row) for row in raw["passives"]}
    if any(a.evolution and a.evolution.passive not in passives for a in abilities.values()):
        raise ValueError("Unknown evolution passive")
    enemies = {
        row["id"]: EnemyDef(
            **{k: v for k, v in row.items() if k not in {"color", "attacks"}},
            color=tuple(row["color"]),
            attacks=tuple(row.get("attacks", [])),
        )
        for row in raw["enemies"]
    }
    if any(
        e.health <= 0 or e.speed <= 0 or e.radius <= 0 or e.weight <= 0 for e in enemies.values()
    ):
        raise ValueError("Invalid enemy definition")
    if any(
        e.family not in {"humanoid", "beast", "undead", "demon", "dragon"} for e in enemies.values()
    ):
        raise ValueError("Invalid creature family")
    encounters = json.loads(files(__package__).joinpath("data/encounters.json").read_text("utf-8"))
    for kind in ("attacks", "elites", "bosses"):
        encounters[kind].extend(expansion[kind])
    attacks = {
        r["id"]: AttackDef(**{k: v for k, v in r.items() if k != "color"}, color=tuple(r["color"]))
        for r in encounters["attacks"]
    }
    waves = tuple(WaveDef(**r) for r in encounters["waves"])
    elites = {
        r["id"]: EliteDef(
            **{k: v for k, v in r.items() if k != "attacks"}, attacks=tuple(r["attacks"])
        )
        for r in encounters["elites"]
    }
    bosses = {
        r["id"]: BossDef(
            **{k: v for k, v in r.items() if k != "attacks"}, attacks=tuple(r["attacks"])
        )
        for r in encounters["bosses"]
    }
    if any(
        b.family not in {"humanoid", "beast", "undead", "demon", "dragon"} for b in bosses.values()
    ):
        raise ValueError("Invalid boss creature family")
    if len(waves) != 30 or tuple(w.start for w in waves) != tuple(i * 60 for i in range(30)):
        raise ValueError("Wave schedule must cover each minute of the 30-minute run")
    if any(
        w.rate <= 0
        or w.batch < 1
        or w.density < 1
        or min(w.health, w.damage, w.xp) <= 0
        or not w.weights
        or any(k not in enemies or weight <= 0 for k, weight in w.weights.items())
        for w in waves
    ):
        raise ValueError("Invalid wave definition")
    if any(
        a.kind not in {"arc", "circle", "ring", "charge", "missile", "leap"}
        or min(a.cooldown, a.warning, a.duration, a.radius, a.reach) <= 0
        or a.damage < 0
        or a.count < 1
        or not 0 <= a.armor_penetration <= 0.75
        or not 0 <= a.health_damage <= 0.5
        or not 0 <= a.slow <= 0.85
        or min(a.pulse, a.growth, a.pull, a.slow_duration) < 0
        for a in attacks.values()
    ):
        raise ValueError("Invalid hostile attack")
    if any(
        e.behavior not in {"chase", "flank", "ranged", "bruiser", "charge"}
        or e.terrain not in {"any", "forest", "road"}
        or any(a not in attacks for a in e.attacks)
        or e.min_time < 0
        or e.max_time < e.min_time
        or e.class_xp < 0
        for e in enemies.values()
    ):
        raise ValueError("Invalid enemy behavior or restriction")
    if any(
        e.enemy not in enemies or not e.attacks or any(a not in attacks for a in e.attacks)
        for e in elites.values()
    ) or any(
        not b.attacks or any(a not in attacks for a in b.attacks) or b.health <= 0 or b.radius <= 0
        for b in bosses.values()
    ):
        raise ValueError("Invalid elite or boss definition")
    pool = tuple(encounters["boss_pool"])
    if not pool or any(b not in bosses for b in pool):
        raise ValueError("Invalid final boss pool")
    zones = {}
    for row in expansion["zones"]:
        zone = ZoneDef(
            **{
                k: v
                for k, v in row.items()
                if k not in {"props", "enemies", "elites", "boss_pool", "waves", "landmarks"}
            },
            props=tuple(row["props"]),
            enemies=tuple(row["enemies"]),
            elites=tuple(row["elites"]),
            boss_pool=tuple(row["boss_pool"]),
            waves=tuple(WaveDef(**w) for w in row["waves"]),
            landmarks=tuple(LandmarkDef(**p) for p in row["landmarks"]),
        )
        if (
            zone.id in zones
            or zone.difficulty < 1
            or not zone.boss_pool
            or any(b not in bosses for b in zone.boss_pool)
            or any(e not in elites for e in zone.elites)
            or any(e not in enemies for e in zone.enemies)
            or tuple(w.start for w in zone.waves) != tuple(i * 60 for i in range(30))
            or any(
                w.rate <= 0
                or w.density <= 0
                or min(w.health, w.damage, w.xp) <= 0
                or any(k not in zone.enemies or value <= 0 for k, value in w.weights.items())
                for w in zone.waves
            )
            or any(p.style not in range(len(zone.props)) or p.radius < 0 for p in zone.landmarks)
        ):
            raise ValueError(f"Invalid zone: {zone.id}")
        zones[zone.id] = zone
    return Content(
        classes,
        abilities,
        passives,
        enemies,
        manuals,
        evolutions,
        waves,
        attacks,
        elites,
        bosses,
        pool,
        zones,
    )
