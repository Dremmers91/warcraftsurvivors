"""Fixed-step run orchestration; mechanics live in independently testable systems."""

from __future__ import annotations

import math
import random

from pygame import Vector2

from .camera import Camera
from .combat import CombatSystem
from .content import Content
from .enemy_combat import EnemySystem
from .entities import Enemy, Pickup, Player, Projectile, SpellState, Visual
from .manuals import activate
from .manuals import update as update_manual
from .meta import RunLoadout
from .movement import normalized
from .run_events import DeathEvent, RunLedger
from .spawning import Spawner
from .upgrades import Choice, apply, roll
from .waves import RUN_SECONDS
from .world import SpatialHash, World

FIXED_DT = 1 / 60


class Simulation:
    def __init__(
        self,
        content: Content,
        class_id: str = "paladin",
        seed: int = 1,
        permanent: RunLoadout | None = None,
        zone_id: str = "elwynn",
    ) -> None:
        self.content, self.class_id = content, class_id
        self.rng = random.Random(seed)
        self.zone = content.zones[zone_id]
        self.world = World(self.zone.seed, zone_id, self.zone.landmarks)
        cls = content.classes[class_id]
        self.player = Player(Vector2(4096, 4096), cls.health, cls.health, cls.speed, cls.armor)
        self.player.spells[cls.abilities[0]] = SpellState()
        loadout = permanent or RunLoadout()
        self.player.meta = loadout.bonuses
        self.player.health = self.player.max_health = cls.health * (
            1 + loadout.bonuses.get("health")
        )
        self.player.base_speed *= 1 + loadout.bonuses.get("speed")
        self.player.armor = min(0.75, cls.armor + loadout.bonuses.get("armor"))
        self.player.shield = loadout.bonuses.get("starting_shield")
        self.player.shield_time = 20 if self.player.shield else 0
        if loadout.starting_ability:
            if (
                loadout.starting_ability not in cls.abilities
                or loadout.starting_ability == cls.abilities[0]
            ):
                raise ValueError("Invalid extra starting ability")
            self.player.spells[loadout.starting_ability] = SpellState()
        self.rerolls = int(loadout.bonuses.get("rerolls"))
        self.banishes = int(loadout.bonuses.get("banishes"))
        self.ledger = RunLedger()
        self.boss_damage_start = 0.0
        self.camera = Camera(self.player.pos)
        self.enemies: list[Enemy] = []
        self.grid: SpatialHash[Enemy] = SpatialHash()
        self.projectiles: list[Projectile] = []
        self.pickups: dict[tuple[str, int, int], Pickup] = {}
        self.pickup_grid: SpatialHash[Pickup] = SpatialHash(128)
        self.visuals: list[Visual] = []
        self.choices: list[Choice] = []
        self.combat = CombatSystem(content, self.player, self.grid, self.projectiles, self.impact)
        self.combat.visuals = self.visuals
        self.combat.resolve = self.world.resolve
        self.spawner = Spawner(content, self.rng, self.world)
        self.time = 0.0
        self.finished = False
        self.kills = 0
        self.gold = 0
        self.elites = 0
        self.evolved = 0
        self.director = self.spawner.director
        self.boss: Enemy | None = None
        self.boss_defeated = False
        self.boss_time = 0.0
        self.won = False
        self.outcome = ""
        self.class_xp_kills = 0
        self.wave_index = 0
        self.enemy_combat = EnemySystem(
            content, self.world, self.player, self.grid, lambda: self.sound_events.append("hurt")
        )
        self.pending_chests = 0
        self.chest_choice = False
        self.debug_used = False
        self.messages: list[tuple[str, float]] = []
        self.sound_events: list[str] = []

    def notify(self, message: str) -> None:
        self.messages.append((message, 3))
        self.messages = self.messages[-3:]

    def impact(self, pos: Vector2, radius: float, color: tuple[int, int, int]) -> None:
        if "hit" not in self.sound_events:
            self.sound_events.append("hit")
        if len(self.visuals) < 180:
            self.visuals.append(Visual(pos.copy(), radius, color, 0.3, 0.3))

    def spawn(self, kind: str | None = None, pos: Vector2 | None = None) -> Enemy:
        enemy = self.spawner.create(self.time, self.camera.pos, self.player.pos, kind, pos)
        self.enemies.append(enemy)
        self.grid.insert(enemy)
        return enemy

    @property
    def elapsed(self) -> float:
        return self.time + self.boss_time

    @property
    def boss_result(self) -> str:
        return (
            "defeated"
            if self.boss_defeated
            else "alive"
            if self.director.boss_spawned
            else "not_reached"
        )

    def finish(self, outcome: str) -> None:
        if self.finished:
            return
        if outcome == "victory" and (
            not self.boss_defeated or self.time < RUN_SECONDS or self.player.health <= 0
        ):
            raise ValueError("Victory requires surviving the final boss defeat after 30 minutes")
        self.finished = True
        self.outcome = outcome
        self.won = outcome == "victory"
        self.choices.clear()
        self.chest_choice = False
        self.sound_events.append("victory" if self.won else "death")

    def spawn_elite(self, elite_id: str | None = None) -> Enemy:
        definition = self.content.elites[elite_id or self.rng.choice(self.zone.elites)]
        enemy = self.spawn(definition.enemy)
        enemy.elite = True
        enemy.elite_id = definition.id
        enemy.sprite = definition.sprite
        enemy.health *= definition.health
        enemy.max_health = enemy.health
        enemy.damage *= definition.damage
        enemy.xp *= definition.xp
        enemy.class_xp += definition.class_xp
        enemy.gold_reward = definition.gold
        enemy.radius *= definition.radius_scale
        enemy.pos = self.world.resolve(enemy.pos, enemy.radius)
        enemy.attack_timer = 1.5
        self.notify(f"{definition.name} approaches · defeat it for an evolution chest")
        self.sound_events.append("elite")
        return enemy

    def spawn_boss(self, force: bool = False) -> Enemy | None:
        if self.director.boss_spawned or (self.time + 1e-8 < RUN_SECONDS and not force):
            return self.boss
        if force:
            self.debug_used = True
        pool = self.content.boss_pool if self.zone.id == "elwynn" else self.zone.boss_pool
        definition = self.content.bosses[self.rng.choice(pool)]
        self.director.boss_spawned = True
        self.spawner.next_id += 1
        health = definition.health * (1 + 0.008 * max(0, self.player.level - 30))
        pos = self.world.resolve(self.player.pos + Vector2(480, 0), definition.radius)
        enemy = Enemy(
            self.spawner.next_id,
            pos,
            health,
            health,
            definition.speed,
            definition.damage,
            definition.xp,
            definition.id,
            definition.radius,
            sprite=definition.sprite,
            boss_id=definition.id,
            class_xp=definition.class_xp,
            gold_reward=definition.gold,
            attack_timer=2,
        )
        self.boss = enemy
        self.boss_damage_start = self.player.damage_taken
        self.enemies.append(enemy)
        self.grid.insert(enemy)
        self.notify(f"{definition.name} has arrived · defeat the boss to win")
        self.sound_events.append("boss")
        return enemy

    def jump_time(self, seconds: float) -> None:
        self.debug_used = True
        self.time = max(0, min(RUN_SECONDS, seconds))
        self.director.seek(self.time)
        self.spawner.timer = 0
        self.notify(f"DEBUG: jumped to {int(self.time) // 60:02}:{int(self.time) % 60:02}")
        if self.director.boss_due(self.time):
            self.spawn_boss()

    def activate_manual(self, direction: Vector2 | None = None) -> bool:
        success = activate(self, direction)
        self.ledger.manual_uses += int(success)
        return success

    def drop(self, pos: Vector2, kind: str, value: float) -> None:
        key = (kind, math.floor(pos.x / 32), math.floor(pos.y / 32))
        pickup = self.pickups.get(key)
        if pickup:
            pickup.value += value
        else:
            self.pickups[key] = Pickup(pos.copy(), kind, value, self.elapsed)

    def collect_dead(self) -> None:
        survivors = []
        for enemy in self.enemies:
            if enemy.health > 0:
                survivors.append(enemy)
            else:
                definition = (
                    self.content.bosses[enemy.boss_id]
                    if enemy.boss_id
                    else self.content.enemies[enemy.kind]
                )
                event = DeathEvent(
                    self.ledger.run_id,
                    enemy.id,
                    enemy.kind,
                    definition.family,
                    self.content.enemies[enemy.kind].faction if not enemy.boss_id else "",
                    self.zone.id,
                    enemy.elite,
                    enemy.boss_id,
                    enemy.last_damage_source,
                    enemy.last_damage_school,
                    enemy.owner,
                    enemy.last_damage_delivery,
                )
                if not self.ledger.record(event):
                    continue
                if enemy.owner not in {"", "player"}:
                    continue
                self.kills += 1
                self.class_xp_kills += enemy.class_xp
                if self.player.health > 0:
                    self.player.health = min(
                        self.player.max_health,
                        self.player.health + self.player.meta.get("kill_heal"),
                    )
                    if self.player.meta.get("kill_shield"):
                        self.player.shield = max(
                            self.player.shield,
                            min(
                                self.player.max_health * 0.25,
                                self.player.shield + self.player.meta.get("kill_shield"),
                            ),
                        )
                        self.player.shield_time = max(3, self.player.shield_time)
                self.gold += enemy.gold_reward
                if enemy.boss_id:
                    self.boss_defeated = True
                    if (
                        enemy.owner == "player"
                        and self.player.damage_taken == self.boss_damage_start
                    ):
                        self.ledger.untouched_bosses += 1
                if enemy.elite:
                    self.elites += 1
                    self.drop(enemy.pos, "chest", 1)
                self.drop(enemy.pos, "xp", enemy.xp)
                if (
                    not enemy.boss_id
                    and self.rng.random() < self.content.enemies[enemy.kind].gold_chance
                ):
                    self.drop(enemy.pos, "gold", 1)
                self.impact(enemy.pos, 24, (237, 192, 122))
                if "enemy_death" not in self.sound_events:
                    self.sound_events.append("enemy_death")
        self.enemies = survivors

    def level_check(self) -> None:
        p = self.player
        if self.pending_chests and not self.choices and not self.finished:
            self.pending_chests -= 1
            self.chest_choice = True
            self.ledger.chests_opened += 1
            self.gold += int(p.meta.get("chest_gold"))
            self.choices = roll(self.content, self.class_id, p, self.rng, chest=True)
            self.sound_events.append("chest")
            return
        if not self.choices and not self.finished and p.xp >= p.xp_required:
            p.xp -= p.xp_required
            p.level += 1
            self.ledger.observe(self)
            self.choices = roll(self.content, self.class_id, p, self.rng)
            self.sound_events.append("level")

    def choose(self, index: int) -> None:
        if 0 <= index < len(self.choices):
            choice = self.choices[index]
            self.gold += apply(self.content, self.class_id, self.player, choice, self.chest_choice)
            if choice.kind == "evolution":
                self.evolved += 1
                self.ledger.evolved_spells.add(choice.id)
                # Expire the replaced behavior; the evolved form casts on the next tick.
                self.projectiles[:] = [s for s in self.projectiles if s.ability != choice.id]
                self.combat.fields[:] = [f for f in self.combat.fields if f.ability != choice.id]
                self.combat.companions[:] = [
                    p for p in self.combat.companions if p.ability != choice.id
                ]
                self.notify(f"Evolved: {choice.name}")
                self.sound_events.append("evolution")
            else:
                self.sound_events.append("upgrade")
            self.chest_choice = False
            self.choices.clear()
            self.ledger.observe(self)
            self.level_check()

    def banish(self, index: int) -> bool:
        if (
            self.finished
            or self.chest_choice
            or self.banishes <= 0
            or not 0 <= index < len(self.choices)
        ):
            return False
        choice = self.choices[index]
        if choice.kind not in {"spell", "passive", "manual", "modifier"}:
            return False
        self.player.banished.add((choice.kind, choice.id))
        self.choices = roll(self.content, self.class_id, self.player, self.rng)
        self.banishes -= 1
        return True

    def reroll(self) -> bool:
        if self.finished or self.chest_choice or not self.choices or self.rerolls <= 0:
            return False
        choices = roll(self.content, self.class_id, self.player, self.rng, excluded=self.choices)
        if set(choices) == set(self.choices):
            return False
        self.choices = choices
        self.rerolls -= 1
        return True

    def collect_pickups(self, dt: float) -> None:
        p = self.player
        # Preserve visible collection without leaving run XP stranded behind a
        # ranged build: old gems home toward the hero after 45 live seconds.
        for pickup in self.pickups.values():
            if pickup.kind == "xp" and self.elapsed - pickup.born >= 45:
                delta = p.pos - pickup.pos
                distance = delta.length()
                if distance > 0.01:
                    pickup.pos += delta / distance * min(distance, 450 * dt)
        self.pickup_grid.rebuild(self.pickups.values())
        collected: set[int] = set()
        for pickup in self.pickup_grid.nearby(
            p.pos, 95 + 30 * p.passive("pickup") + p.meta.get("pickup")
        ):
            delta = p.pos - pickup.pos
            length = delta.length()
            if length > 0.01:
                pickup.pos += delta / length * min(length, 500 * dt)
            if pickup.pos.distance_squared_to(p.pos) < 20**2:
                collected.add(id(pickup))
                if pickup.kind == "xp":
                    p.xp += pickup.value * (1 + p.meta.get("xp"))
                elif pickup.kind == "chest":
                    self.pending_chests += int(pickup.value)
                elif pickup.kind in {"heal", "healing"}:
                    self.ledger.observe(self)
                    self.ledger.healing_pickups += 1
                    p.health = min(p.max_health, p.health + pickup.value)
                else:
                    self.gold += int(pickup.value)
        if collected:
            self.pickups = {
                key: pickup for key, pickup in self.pickups.items() if id(pickup) not in collected
            }
        self.level_check()

    def step(self, dt: float, movement: Vector2 | None = None) -> None:
        if not 0 < dt <= 0.05:
            raise ValueError("Use a fixed step no larger than 50 ms")
        if self.finished or self.choices:
            return
        if self.player.health <= 0:
            self.finish("death")
            return
        self.level_check()
        if self.choices:
            return
        p = self.player
        before = self.time
        self.time = min(RUN_SECONDS, self.time + dt)
        if self.time >= RUN_SECONDS - 1e-8:
            self.time = RUN_SECONDS
        self.boss_time += max(0, dt - (self.time - before))
        self.ledger.observe(self)
        wave = self.director.wave(self.time)
        index = int(wave.start // 60)
        if index != self.wave_index:
            self.wave_index = index
            self.notify(wave.name)
        for _ in self.director.due_elites(self.time):
            self.spawn_elite()
        if self.director.boss_due(self.time):
            self.spawn_boss()
        p.hurt_timer = max(0, p.hurt_timer - dt)
        p.cast_age += dt
        p.wound_time = max(0, p.wound_time - dt)
        p.slow_time = max(0, p.slow_time - dt)
        if not p.slow_time:
            p.slow_strength = 0
        p.power = max(0, p.power - dt)
        update_manual(p, dt)
        move = normalized(movement if movement is not None else Vector2())
        if move.length_squared() > 0.001 and p.rooted <= 0:
            p.facing = move.normalize()
            p.pos = self.world.move(
                p.pos,
                move
                * p.base_speed
                * (1 + 0.08 * p.passive("movement"))
                * (1 - p.slow_strength)
                * dt,
                p.radius,
            )
        self.camera.update(p.pos, dt)
        self.spawner.update(dt, self.time, self.camera.pos, p.pos, self.enemies)
        self.grid.rebuild(self.enemies)
        self.enemy_combat.update(dt, self.enemies)
        if p.health <= 0:
            self.collect_dead()
            self.finish("death")
            return
        self.grid.rebuild(e for e in self.enemies if e.health > 0)
        if self.combat.update(dt):
            p.cast_age = 0
            self.sound_events.append("cast_" + p.last_damage_school)
        self.collect_dead()
        if p.health <= 0:
            self.finish("death")
        elif self.boss_defeated and self.time + 1e-8 >= RUN_SECONDS:
            self.finish("victory")
        else:
            self.collect_pickups(dt)
        for visual in self.visuals:
            visual.life -= dt
        self.visuals[:] = [v for v in self.visuals if v.life > 0]
        self.messages = [(message, life - dt) for message, life in self.messages if life > dt]
