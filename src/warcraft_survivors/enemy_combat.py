"""Reusable enemy steering and telegraphed hostile attacks; no rendering mutation."""

from __future__ import annotations

import math
from collections.abc import Callable

from pygame import Vector2

from .combat import hurt_player
from .content import Content
from .entities import Enemy, HostileAttack, HostileProjectile, Player
from .movement import chase
from .world import SpatialHash, World


def segment_distance_squared(point: Vector2, start: Vector2, end: Vector2) -> float:
    delta = end - start
    t = max(0, min(1, (point - start).dot(delta) / max(1e-9, delta.length_squared())))
    return point.distance_squared_to(start + delta * t)


class EnemySystem:
    def __init__(
        self,
        content: Content,
        world: World,
        player: Player,
        grid: SpatialHash[Enemy],
        hurt: Callable[[], None],
    ) -> None:
        self.content, self.world, self.player, self.grid, self.hurt = (
            content,
            world,
            player,
            grid,
            hurt,
        )
        self.attacks: list[HostileAttack] = []
        self.projectiles: list[HostileProjectile] = []
        self.attack_counts: dict[str, int] = {}

    def damage(
        self,
        amount: float,
        slow: float = 0,
        duration: float = 0,
        pull: float = 0,
        origin: Vector2 | None = None,
        armor_penetration: float = 0,
    ) -> bool:
        before = self.player.health
        if hurt_player(self.player, amount, armor_penetration):
            self.hurt()
            if armor_penetration and self.player.health < before:
                self.player.wound_time = 2
            if slow:
                self.player.slow_strength = max(self.player.slow_strength, slow)
                self.player.slow_time = max(self.player.slow_time, duration)
            if pull and origin is not None:
                delta = origin - self.player.pos
                if delta.length_squared() > 1:
                    self.player.pos = self.world.move(
                        self.player.pos,
                        delta.normalize() * min(pull, delta.length()),
                        self.player.radius,
                    )
            return True
        return False

    def begin(self, enemy: Enemy, aid: str) -> None:
        self.attack_counts[aid] = self.attack_counts.get(aid, 0) + 1
        attack = self.content.attacks[aid]
        delta = self.player.pos - enemy.pos
        direction = delta.normalize() if delta.length_squared() > 1 else enemy.facing.copy()
        enemy.facing = direction.copy()
        pos = self.player.pos.copy() if attack.kind in {"circle", "leap"} else enemy.pos.copy()
        pos = self.world.clamp(pos)
        baseline = (
            self.content.bosses[enemy.boss_id].damage
            if enemy.boss_id
            else self.content.enemies[enemy.kind].damage
        )
        damage = attack.damage * enemy.damage / baseline
        damage += self.player.max_health * attack.health_damage
        if enemy.enraged:
            damage *= self.content.bosses[enemy.boss_id].enrage_damage
        self.attacks.append(
            HostileAttack(enemy, aid, pos, direction, attack.warning, attack.duration, damage)
        )
        enemy.busy = attack.warning + attack.duration
        enemy.cast_age = 0
        cooldown = attack.cooldown * (
            self.content.bosses[enemy.boss_id].enrage_cooldown if enemy.enraged else 1
        )
        enemy.attack_timer = cooldown + attack.warning + attack.duration
        enemy.attack_index += 1

    def update(self, dt: float, enemies: list[Enemy]) -> None:
        p = self.player
        for enemy in enemies:
            if enemy.health <= 0:
                continue
            enemy.flash = max(0, enemy.flash - dt)
            enemy.busy = max(0, enemy.busy - dt)
            enemy.cast_age += dt
            enemy.attack_timer -= dt
            delta = p.pos - enemy.pos
            distance2 = delta.length_squared()
            attacks = (
                self.content.bosses[enemy.boss_id].attacks
                if enemy.boss_id
                else self.content.elites[enemy.elite_id].attacks
                if enemy.elite_id
                else self.content.enemies[enemy.kind].attacks
            )
            if enemy.boss_id:
                enemy.enraged = (
                    enemy.health / enemy.max_health <= self.content.bosses[enemy.boss_id].enrage
                )
            if enemy.fear > 0 and not enemy.boss_id:
                enemy.fear = max(0, enemy.fear - dt)
                goal = enemy.pos - (delta.normalize() if distance2 > 1 else Vector2(1, 0)) * 200
            else:
                goal = p.pos
                if attacks and enemy.attack_timer <= 0 and enemy.busy <= 0:
                    aid = attacks[enemy.attack_index % len(attacks)]
                    if distance2 <= self.content.attacks[aid].reach ** 2:
                        self.begin(enemy, aid)
                behavior = (
                    "chase"
                    if enemy.boss_id or enemy.elite
                    else self.content.enemies[enemy.kind].behavior
                )
                if behavior == "ranged" and distance2 < 200**2:
                    goal = enemy.pos - (delta.normalize() if distance2 > 1 else Vector2(1, 0)) * 150
                elif behavior == "ranged" and distance2 < 310**2:
                    goal = enemy.pos
                elif behavior == "flank" and distance2 > 160**2:
                    goal = p.pos + delta.normalize().rotate(90 if enemy.id % 2 else -90) * 110
            if enemy.busy <= 0:
                enemy.move_time += dt
                cadence = (
                    1 / 60
                    if distance2 < 220**2 or enemy.elite or enemy.boss_id
                    else 1 / 30
                    if distance2 < 650**2
                    else 0.1
                )
                if enemy.move_time + 1e-9 >= cadence:
                    slow = (
                        max((s.slow for s in enemy.statuses.values()), default=0)
                        if enemy.statuses
                        else 0
                    )
                    enemy.facing = delta.normalize() if distance2 > 1 else enemy.facing
                    cap = 0.3 if enemy.boss_id else 0.6 if enemy.elite else 0.85
                    chase(
                        enemy,
                        goal,
                        enemy.move_time * (1 - min(cap, slow)),
                        self.world,
                        self.grid,
                        12 if len(enemies) > 1200 else 24,
                    )
                    enemy.move_time = 0
                if (
                    distance2 < (enemy.radius + p.radius + enemy.speed * dt + 12) ** 2
                    and enemy.pos.distance_squared_to(p.pos) < (enemy.radius + p.radius) ** 2
                ):
                    self.damage(enemy.damage)
                    offset = enemy.pos - p.pos
                    normal = offset.normalize() if offset.length_squared() > 0.01 else Vector2(1, 0)
                    enemy.pos = self.world.resolve(
                        p.pos + normal * (enemy.radius + p.radius), enemy.radius
                    )
        self.update_attacks(dt)
        self.update_projectiles(dt)

    def update_attacks(self, dt: float) -> None:
        for hazard in self.attacks:
            a = self.content.attacks[hazard.attack]
            if hazard.owner.health <= 0 and not hazard.started:
                hazard.remaining = 0
                continue
            if hazard.owner.fear > 0 and not hazard.owner.boss_id and not hazard.started:
                hazard.remaining = 0
                hazard.owner.busy = 0
                continue
            if hazard.warning > 0:
                hazard.warning = max(0, hazard.warning - dt)
                if hazard.warning > 0:
                    continue
            if not hazard.started:
                hazard.started = True
                if a.kind == "missile":
                    for i in range(a.count):
                        heading = hazard.direction.rotate(
                            (i - (a.count - 1) / 2) * (a.angle / max(1, a.count - 1))
                        )
                        self.projectiles.append(
                            HostileProjectile(
                                hazard.owner.pos.copy(),
                                heading * a.speed,
                                hazard.damage,
                                a.radius,
                                a.effect,
                                pull=a.pull,
                                slow=a.slow,
                                slow_duration=a.slow_duration,
                                origin=hazard.owner.pos.copy(),
                                armor_penetration=a.armor_penetration,
                            )
                        )
                elif a.kind == "leap":
                    hazard.owner.pos = self.world.resolve(hazard.pos, hazard.owner.radius)
            hazard.age += dt
            hazard.remaining -= dt
            if a.pulse:
                hazard.pulse_time -= dt
                if hazard.pulse_time <= 0:
                    hazard.hit_player = False
                    hazard.pulse_time += a.pulse
            p = self.player
            delta = p.pos - hazard.pos
            hit = False
            if a.kind == "charge":
                start = hazard.owner.pos.copy()
                if hazard.owner.health > 0:
                    hazard.owner.pos = self.world.move(
                        start, hazard.direction * a.speed * dt, hazard.owner.radius
                    )
                hit = (
                    segment_distance_squared(p.pos, start, hazard.owner.pos)
                    <= (a.radius + p.radius) ** 2
                )
            elif a.kind in {"circle", "leap"}:
                hit = delta.length_squared() <= (a.radius + a.growth * hazard.age + p.radius) ** 2
            elif a.kind == "arc":
                hit = delta.length_squared() <= (a.radius + p.radius) ** 2 and (
                    delta.length_squared() < 1
                    or hazard.direction.dot(delta.normalize())
                    >= math.cos(math.radians(a.angle / 2))
                )
            elif a.kind == "ring":
                radius = a.radius * min(1, hazard.age / a.duration)
                hit = abs(delta.length() - radius) <= p.radius + 16
            if hit and not hazard.hit_player:
                hazard.hit_player = True
                self.damage(
                    hazard.damage,
                    a.slow,
                    a.slow_duration,
                    a.pull,
                    hazard.owner.pos,
                    a.armor_penetration,
                )
        self.attacks[:] = [a for a in self.attacks if a.remaining > 0]

    def update_projectiles(self, dt: float) -> None:
        alive = []
        for shot in self.projectiles:
            start = shot.pos.copy()
            shot.pos += shot.velocity * dt
            shot.life -= dt
            if (
                segment_distance_squared(self.player.pos, start, shot.pos)
                <= (self.player.radius + shot.radius) ** 2
            ):
                self.damage(
                    shot.damage,
                    shot.slow,
                    shot.slow_duration,
                    shot.pull,
                    shot.origin,
                    shot.armor_penetration,
                )
                shot.life = 0
            if shot.life > 0 and self.world.clamp(shot.pos, 0) == shot.pos:
                alive.append(shot)
        self.projectiles[:] = alive
