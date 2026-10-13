"""Shared automatic behaviors, spatial collision, statuses and owner-bound summons."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from pygame import Vector2

from .content import Ability, Content
from .entities import Companion, Enemy, Field, Player, Projectile, SpellState, Status, Visual
from .world import SpatialHash

COUNT_KINDS = {"projectile", "orbit", "companion", "charge", "dot", "chain"}
PROJECTILE_KINDS = {"projectile"}


@dataclass(frozen=True)
class SpellStats:
    damage: float
    cooldown: float
    radius: float
    count: int
    pierce: int
    duration: float = 3
    speed: float = 440


def spell_stats(ability: Ability, state: SpellState, player: Player) -> SpellStats:
    rank = ability.ranks[state.rank - 1]
    meta = player.meta
    base = ability.base_id or ability.id
    buff = (
        player.buff_power
        if player.buff_time > 0
        and not player.pet_buff
        and player.buff_school in ("", ability.school)
        else 0
    )
    damage = (
        rank.damage
        * (1 + player.passive("might") * 0.15)
        * (2 if player.power > 0 else 1)
        * (1 + buff)
        * (
            1
            + meta.get("damage")
            + meta.get("school:" + ability.school)
            + meta.get("kind:" + ability.kind)
            + meta.spell(base, "damage")
        )
        * (1 + meta.get("low_health_damage") if player.health <= player.max_health * 0.35 else 1)
    )
    if ability.evolved:
        damage *= 1.65
    if "force" in state.modifiers:
        damage *= 1.3
    return SpellStats(
        damage,
        rank.cooldown
        * max(0.4, 1 - 0.07 * player.passive("haste"))
        * max(0.65, 1 - meta.get("haste"))
        * (1.15 if "force" in state.modifiers else 1),
        rank.radius
        * (1 + player.passive("area") * 0.2)
        * (1 + meta.get("area") + meta.spell(base, "radius"))
        * (1.3 if "reach" in state.modifiers else 1),
        rank.count
        + (
            player.passive("projectiles") + int(meta.get("count") + meta.spell(base, "count"))
            if ability.kind in COUNT_KINDS
            else 0
        ),
        rank.pierce
        + (
            player.passive("piercing") + int(meta.spell(base, "pierce"))
            if ability.kind in PROJECTILE_KINDS
            else 0
        ),
        rank.duration
        * (1 + 0.2 * player.passive("duration"))
        * (1 + meta.get("duration") + meta.spell(base, "duration")),
        ability.speed
        * (1 + meta.spell(base, "speed"))
        * (
            1
            + (
                0.15 * player.passive("velocity")
                if ability.kind in {"projectile", "field", "charge"}
                else 0
            )
        ),
    )


def incoming_damage(base: float, armor: float, fortitude_rank: int) -> float:
    return max(0, base) * (1 - min(0.75, max(0, armor) + fortitude_rank * 0.08))


def hurt_player(player: Player, amount: float, armor_penetration: float = 0) -> bool:
    if player.health <= 0 or player.invulnerable or player.immune > 0 or player.hurt_timer > 0:
        return False
    damage = incoming_damage(
        amount,
        max(
            0,
            min(
                0.75,
                player.armor
                + (player.guard_strength if player.guard > 0 else 0)
                + player.passive("armor") * 0.08,
            )
            - armor_penetration,
        ),
        0,
    )
    blocked = min(player.shield, damage)
    player.shield -= blocked
    player.health = max(0, player.health - damage + blocked)
    player.hurt_timer = 0.65
    return True


def automatic_heal(player: Player, amount: float) -> None:
    """Life steal uses actual damage and a shared recovery budget across hit/DoT paths."""
    recovery = min(
        player.healing_budget,
        max(0, player.max_health - player.health),
        max(0, amount) * (1 + player.meta.get("healing")) * (0.35 if player.wound_time > 0 else 1),
    )
    player.health = min(player.max_health, player.health + recovery)
    player.healing_budget -= recovery


def damage_enemy(
    enemy: Enemy, amount: float, school: str = "physical", owner: str = "player"
) -> None:
    if enemy.health > 0:
        enemy.health = max(0, enemy.health - max(0, amount))
        enemy.flash = 0.12
        enemy.last_damage_school, enemy.owner = school, owner


class SpellBehavior(Protocol):
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None: ...


class ProjectileSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        direction = combat.direction()
        radial = state.rank >= ability.mechanics.radial_rank
        for i in range(stats.count):
            angle = (
                i * 360 / stats.count
                if radial
                else (i - (stats.count - 1) / 2) * ability.mechanics.spread
            )
            combat.projectiles.append(
                Projectile(
                    combat.player.pos.copy(),
                    direction.rotate(angle) * stats.speed,
                    ability.id,
                    stats.damage,
                    stats.radius,
                    stats.pierce,
                    max(3, stats.duration),
                    bounces=ability.mechanics.bounce,
                    returning=ability.mechanics.returning,
                )
            )
        combat.show(combat.player.pos, 23, ability, direction)


class AreaSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        combat.disk(combat.player.pos, stats.radius, stats.damage, ability, state)
        combat.show(combat.player.pos, stats.radius, ability)
        if ability.mechanics.shield:
            combat.player.shield = max(
                combat.player.shield, stats.damage * ability.mechanics.shield
            )
            combat.player.shield_time = stats.duration


class ArcSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        direction = combat.direction()
        for enemy in combat.near(combat.player.pos, stats.radius):
            delta = enemy.pos - combat.player.pos
            if delta.length_squared() < 1 or direction.dot(delta.normalize()) >= math.cos(
                math.radians(ability.mechanics.angle / 2)
            ):
                combat.hit(enemy, stats.damage, ability, state)
        combat.show(combat.player.pos, stats.radius, ability, direction)


class FieldSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats, m = combat.stats(ability, state), ability.mechanics
        if m.follow or m.persistent:
            old = next((f for f in combat.fields if f.ability == ability.id), None)
            if old:
                old.life, old.damage, old.radius = stats.duration, stats.damage, stats.radius
                return
        target = combat.target(combat.player.pos, 650)
        pos = (
            combat.player.pos.copy()
            if m.follow or ability.speed > 0
            else target.pos.copy()
            if target
            else combat.player.pos + combat.player.facing * 150
        )
        velocity = combat.direction() * stats.speed if ability.speed else Vector2()
        combat.fields.append(
            Field(
                pos,
                ability.id,
                stats.damage,
                stats.radius,
                stats.duration,
                velocity,
                m.follow,
                m.persistent,
                delay=m.delay,
            )
        )


class WaveSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        combat.fields.append(
            Field(
                combat.player.pos.copy(),
                ability.id,
                stats.damage,
                stats.radius,
                stats.duration,
                wave=True,
            )
        )


class ChainSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        combat.show(combat.player.pos, 24, ability)
        pos = combat.player.pos
        seen: set[int] = set()
        for _ in range(stats.count + ability.mechanics.chain - 1):
            target = combat.target(pos, max(300, stats.radius), seen)
            if target is None:
                break
            combat.show(pos, stats.radius, ability, end=target.pos)
            combat.hit(target, stats.damage, ability, state)
            seen.add(target.id)
            pos = target.pos


class DotSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        combat.show(combat.player.pos, 24, ability)
        candidates = sorted(
            combat.near(combat.player.pos, 700),
            key=lambda e: (
                e.statuses.get(ability.id, Status("", 0, 0)).remaining,
                e.pos.distance_squared_to(combat.player.pos),
            ),
        )
        for enemy in candidates[: stats.count]:
            combat.hit(enemy, stats.damage * 0.2, ability, state)
            combat.mark(
                enemy,
                ability,
                stats.damage,
                stats.duration,
                spread=ability.mechanics.spread_dot or state.rank >= 5,
            )
            combat.show(combat.player.pos, 25, ability, end=enemy.pos)


class OrbitSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        if any(s.ability == ability.id for s in combat.projectiles):
            return
        for i in range(stats.count):
            angle = 360 * i / stats.count
            combat.projectiles.append(
                Projectile(
                    combat.player.pos + Vector2(80, 0).rotate(angle),
                    Vector2(),
                    ability.id,
                    stats.damage,
                    15 * (1 + 0.2 * combat.player.passive("area")),
                    stats.pierce,
                    stats.duration,
                    orbit_angle=angle,
                    orbit_radius=stats.radius,
                )
            )


class CompanionSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        pets = [p for p in combat.companions if p.ability == ability.id]
        for i in range(len(pets), stats.count):
            combat.companions.append(
                Companion(
                    combat.player.pos + Vector2(35, 0).rotate(i * 90),
                    ability.id,
                    combat.player,
                    ability.mechanics.summon,
                )
            )
            combat.show(combat.player.pos, 45, ability)


class ChargeSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        direction = combat.direction()
        for i in range(stats.count):
            velocity = (
                direction.rotate((i - (stats.count - 1) / 2) * ability.mechanics.spread)
                * stats.speed
            )
            combat.companions.append(
                Companion(
                    combat.player.pos.copy(),
                    ability.id,
                    combat.player,
                    ability.mechanics.summon,
                    stats.duration,
                    facing=direction,
                    velocity=velocity,
                    leash=900,
                )
            )


class BeamSpell:
    def cast(self, combat: CombatSystem, ability: Ability, state: SpellState) -> None:
        stats = combat.stats(ability, state)
        combat.fields.append(
            Field(
                combat.player.pos.copy(),
                ability.id,
                stats.damage,
                stats.radius,
                stats.duration,
                combat.direction(),
                follow=True,
            )
        )


class CombatSystem:
    def __init__(
        self,
        content: Content,
        player: Player,
        grid: SpatialHash[Enemy],
        projectiles: list[Projectile],
        impact: Callable[[Vector2, float, tuple[int, int, int]], None],
    ) -> None:
        self.content, self.player, self.grid, self.projectiles, self.impact = (
            content,
            player,
            grid,
            projectiles,
            impact,
        )
        self.fields: list[Field] = []
        self.companions: list[Companion] = []
        self.visuals: list[Visual] | None = None
        self.resolve: Callable[[Vector2, float], Vector2] | None = None
        self.stats_cache: dict[str, SpellStats] = {}
        self.updating = False
        self.max_enemy_radius = max(
            max(e.radius for e in content.enemies.values()),
            max(
                (content.enemies[e.enemy].radius * e.radius_scale for e in content.elites.values()),
                default=0,
            ),
            max((b.radius for b in content.bosses.values()), default=0),
        )
        self.behaviors: dict[str, SpellBehavior] = {
            "projectile": ProjectileSpell(),
            "area": AreaSpell(),
            "arc": ArcSpell(),
            "field": FieldSpell(),
            "wave": WaveSpell(),
            "chain": ChainSpell(),
            "dot": DotSpell(),
            "orbit": OrbitSpell(),
            "companion": CompanionSpell(),
            "charge": ChargeSpell(),
            "beam": BeamSpell(),
        }

    def near(self, pos: Vector2, radius: float) -> list[Enemy]:
        return [
            e
            for e in self.grid.nearby(pos, radius + self.max_enemy_radius)
            if e.health > 0 and e.pos.distance_squared_to(pos) <= (radius + e.radius) ** 2
        ]

    def target(self, pos: Vector2, radius: float, excluded: set[int] | None = None) -> Enemy | None:
        return min(
            (e for e in self.near(pos, radius) if not excluded or e.id not in excluded),
            key=lambda e: e.pos.distance_squared_to(pos),
            default=None,
        )

    def direction(self) -> Vector2:
        target = self.target(self.player.pos, 800)
        delta = target.pos - self.player.pos if target else self.player.facing
        return delta.normalize() if delta.length_squared() > 0.01 else self.player.facing.copy()

    def show(
        self,
        pos: Vector2,
        radius: float,
        ability: Ability,
        direction: Vector2 | None = None,
        end: Vector2 | None = None,
    ) -> None:
        if self.visuals is None:
            self.impact(pos, radius, ability.color)
        elif len(self.visuals) < 180:
            self.visuals.append(
                Visual(
                    pos.copy(),
                    radius,
                    ability.color,
                    0.35,
                    0.35,
                    ability.effect or ability.id,
                    direction.copy() if direction is not None else Vector2(1, 0),
                    end.copy() if end is not None else None,
                )
            )

    def mark(
        self, enemy: Enemy, ability: Ability, damage: float, duration: float, spread: bool = False
    ) -> None:
        previous = enemy.statuses.get(ability.id)
        enemy.statuses[ability.id] = Status(
            ability.id,
            damage,
            duration,
            previous.timer if previous else 0,
            ability.mechanics.slow,
            spread,
            ability.mechanics.death_burst,
            self.stats(ability, self.state(ability.id)).radius / ability.ranks[0].radius,
        )

    def hit(
        self,
        enemy: Enemy,
        damage: float,
        ability: Ability,
        state: SpellState,
        secondary: bool = False,
    ) -> None:
        if enemy.health <= 0:
            return
        m = ability.mechanics
        amount = damage * (1 + m.execute if enemy.health <= enemy.max_health * 0.35 else 1)
        amount *= (
            1
            + (self.player.meta.get("boss_damage") if enemy.boss_id else 0)
            + (self.player.meta.get("execute") if enemy.health <= enemy.max_health * 0.35 else 0)
        )
        dealt = min(enemy.health, amount)
        damage_enemy(enemy, amount, ability.school)
        if m.heal:
            automatic_heal(self.player, dealt * m.heal)
        if m.knockback:
            delta = enemy.pos - self.player.pos
            if delta.length_squared() > 1:
                enemy.pos += (
                    delta.normalize()
                    * m.knockback
                    * (0.1 if enemy.boss_id else 0.6 if enemy.elite else 1)
                )
                if self.resolve:
                    enemy.pos = self.resolve(enemy.pos, enemy.radius)
        if not secondary and (m.dot or m.slow):
            stats = self.stats(ability, state)
            self.mark(enemy, ability, stats.damage * m.dot, stats.duration, m.spread_dot)
        if not secondary and m.splash:
            stats = self.stats(ability, state)
            for other in self.near(enemy.pos, m.splash * (1 + 0.2 * self.player.passive("area"))):
                if other is not enemy:
                    self.hit(other, stats.damage * 0.6, ability, state, True)
            self.show(enemy.pos, m.splash, ability)

    def disk(
        self, pos: Vector2, radius: float, damage: float, ability: Ability, state: SpellState
    ) -> None:
        for enemy in self.near(pos, radius):
            self.hit(enemy, damage, ability, state)

    def cast(self, ability: Ability, state: SpellState) -> None:
        self.player.last_damage_school = ability.school
        self.behaviors[ability.kind].cast(self, ability, state)

    def state(self, aid: str) -> SpellState:
        return self.player.spells.get(aid, SpellState(8 if aid in self.content.evolutions else 1))

    def stats(self, ability: Ability, state: SpellState) -> SpellStats:
        if self.updating and ability.id in self.stats_cache:
            return self.stats_cache[ability.id]
        return spell_stats(ability, state, self.player)

    def update(self, dt: float) -> int:
        budget = self.player.max_health * 0.04 * (1 + self.player.meta.get("healing"))
        self.player.healing_budget = min(budget, self.player.healing_budget + budget * dt)
        self.stats_cache = {
            aid: spell_stats(self.content.ability(aid), state, self.player)
            for aid, state in self.player.spells.items()
        }
        self.updating = True
        casts = 0
        for aid, state in self.player.spells.items():
            ability = self.content.ability(aid)
            state.timer -= dt
            while state.timer <= 0:
                self.cast(ability, state)
                state.timer += self.stats(ability, state).cooldown
                casts += 1
        self.update_projectiles(dt)
        self.update_fields(dt)
        self.update_companions(dt)
        self.update_statuses(dt)
        self.updating = False
        return casts

    def update_projectiles(self, dt: float) -> None:
        alive = []
        for shot in self.projectiles:
            ability, state = self.content.ability(shot.ability), self.state(shot.ability)
            start = shot.pos.copy()
            shot.age += dt
            shot.life -= dt
            if shot.orbit_angle is not None:
                shot.orbit_angle += (ability.speed or 150) * dt
                shot.pos = self.player.pos + Vector2(shot.orbit_radius, 0).rotate(shot.orbit_angle)
                shot.velocity = shot.pos - start
                shot.pulse -= dt
                if shot.pulse <= 0:
                    shot.hit.clear()
                    shot.pulse += ability.mechanics.pulse
            else:
                if ability.mechanics.homing:
                    shot.target_timer -= dt
                    if shot.target_timer <= 0 or shot.target is None or shot.target.health <= 0:
                        shot.target = self.target(shot.pos, 400, shot.hit)
                        shot.target_timer = 0.15
                    target = shot.target
                    if target and target.pos.distance_squared_to(shot.pos) > 1:
                        goal = (target.pos - shot.pos).normalize() * shot.velocity.length()
                        shot.velocity = shot.velocity.lerp(goal, min(1, dt * 6))
                if shot.returning and shot.age >= 1:
                    if shot.age - dt < 1:
                        shot.hit.clear()
                    delta = self.player.pos - shot.pos
                    if delta.length_squared() < 20**2:
                        shot.life = 0
                    elif delta.length_squared() > 1:
                        shot.velocity = delta.normalize() * self.stats(ability, state).speed
                shot.pos += shot.velocity * dt
            segment = shot.pos - start
            length2 = segment.length_squared()
            radius = segment.length() / 2 + shot.radius + self.max_enemy_radius
            for enemy in sorted(
                self.grid.nearby((start + shot.pos) / 2, radius),
                key=lambda e: e.pos.distance_squared_to(start),
            ):
                if enemy.health <= 0 or enemy.id in shot.hit:
                    continue
                t = max(0, min(1, (enemy.pos - start).dot(segment) / length2)) if length2 else 0
                if (
                    enemy.pos.distance_squared_to(start + segment * t)
                    > (enemy.radius + shot.radius) ** 2
                ):
                    continue
                self.hit(enemy, shot.damage, ability, state)
                shot.hit.add(enemy.id)
                self.show(enemy.pos, shot.radius * 2 + 8, ability)
                if shot.orbit_angle is not None:
                    continue
                if shot.bounces > 0 and (not shot.returning or shot.age < 1):
                    target = self.target(enemy.pos, 400, shot.hit)
                    if target and target.pos.distance_squared_to(enemy.pos) > 1:
                        shot.pos = enemy.pos.copy()
                        shot.velocity = (
                            target.pos - enemy.pos
                        ).normalize() * shot.velocity.length()
                        shot.bounces -= 1
                        break
                if shot.returning:
                    continue
                shot.pierce -= 1
                if shot.pierce < 0:
                    shot.life = 0
                    break
            if shot.life > 0:
                alive.append(shot)
        self.projectiles[:] = alive

    def update_fields(self, dt: float) -> None:
        for field in self.fields:
            ability, state = self.content.ability(field.ability), self.state(field.ability)
            field.age += dt
            if field.delay > 0:
                field.delay = max(0, field.delay - dt)
                continue
            if not field.persistent:
                field.life -= dt
            if field.follow:
                field.pos.update(self.player.pos)
            elif not field.wave:
                field.pos += field.velocity * dt
            if field.wave:
                radius = field.radius * min(1, field.age / self.stats(ability, state).duration)
                for enemy in self.near(field.pos, radius):
                    if enemy.id not in field.hit:
                        self.hit(enemy, field.damage, ability, state)
                        field.hit.add(enemy.id)
            else:
                field.timer -= dt
                while field.timer <= 0:
                    if ability.kind == "beam":
                        end = field.pos + field.velocity * field.radius
                        segment = end - field.pos
                        thickness = 18 * (1 + 0.2 * self.player.passive("area"))
                        for enemy in self.grid.nearby(
                            (field.pos + end) / 2,
                            field.radius / 2 + thickness + self.max_enemy_radius,
                        ):
                            t = max(
                                0,
                                min(
                                    1,
                                    (enemy.pos - field.pos).dot(segment)
                                    / max(1, segment.length_squared()),
                                ),
                            )
                            if (
                                enemy.pos.distance_squared_to(field.pos + segment * t)
                                <= (enemy.radius + 18 * (1 + 0.2 * self.player.passive("area")))
                                ** 2
                            ):
                                self.hit(enemy, field.damage, ability, state)
                        self.show(field.pos, field.radius, ability, end=end)
                    else:
                        self.disk(field.pos, field.radius, field.damage, ability, state)
                        if ability.mechanics.shield:
                            self.player.shield = max(
                                self.player.shield, field.damage * ability.mechanics.shield
                            )
                            self.player.shield_time = 1
                    field.timer += ability.mechanics.pulse
        self.fields[:] = [f for f in self.fields if f.life > 0 or f.persistent]

    def update_companions(self, dt: float) -> None:
        for pet in self.companions:
            ability, state = self.content.ability(pet.ability), self.state(pet.ability)
            stats = spell_stats(ability, state, pet.owner)
            pet.attack_time = max(0, pet.attack_time - dt)
            if pet.life >= 0:
                pet.life = max(0, pet.life - dt)
                start = pet.pos.copy()
                pet.pos += pet.velocity * dt
                if pet.pos.distance_squared_to(pet.owner.pos) > pet.leash**2:
                    pet.life = 0
                segment = pet.pos - start
                for enemy in self.grid.nearby(
                    (start + pet.pos) / 2,
                    segment.length() / 2 + stats.radius + self.max_enemy_radius,
                ):
                    t = max(
                        0,
                        min(1, (enemy.pos - start).dot(segment) / max(1, segment.length_squared())),
                    )
                    if (
                        enemy.id not in pet.hit
                        and enemy.health > 0
                        and enemy.pos.distance_squared_to(start + t * segment)
                        <= (stats.radius + enemy.radius) ** 2
                    ):
                        buff = (
                            1 + pet.owner.buff_power
                            if pet.owner.pet_buff and pet.owner.buff_time > 0
                            else 1
                        )
                        self.hit(enemy, stats.damage * buff, ability, state)
                        pet.hit.add(enemy.id)
                        pet.attack_time = 0.3
                        self.show(enemy.pos, 38, ability)
            else:
                target = self.target(pet.pos, 220)
                if target and target.pos.distance_to(pet.owner.pos) > pet.leash:
                    target = None
                goal = target.pos if target else pet.owner.pos + Vector2(-45, 30)
                delta = goal - pet.pos
                if delta.length_squared() > 1:
                    pet.facing = delta.normalize()
                    pet.pos += pet.facing * min(delta.length(), max(230, stats.speed) * dt)
                offset = pet.pos - pet.owner.pos
                if offset.length() > pet.leash:
                    pet.pos = pet.owner.pos + offset.normalize() * pet.leash
                pet.timer -= dt
                if (
                    target
                    and pet.pos.distance_squared_to(target.pos)
                    <= (stats.radius + target.radius) ** 2
                    and pet.timer <= 0
                ):
                    buff = (
                        1 + pet.owner.buff_power
                        if pet.owner.pet_buff and pet.owner.buff_time > 0
                        else 1
                    )
                    self.disk(target.pos, stats.radius, stats.damage * buff, ability, state)
                    pet.timer = stats.cooldown
                    pet.attack_time = 0.3
                    self.show(target.pos, stats.radius, ability)
        self.companions[:] = [p for p in self.companions if p.life != 0]

    def update_statuses(self, dt: float) -> None:
        transfers: list[tuple[Enemy, Ability, Status]] = []
        for enemy in self.grid.items():
            for aid, status in list(enemy.statuses.items()):
                ability = self.content.ability(aid)
                status.remaining -= dt
                status.timer -= dt
                if enemy.health > 0 and status.damage > 0:
                    while status.timer <= 0:
                        amount = status.damage * (
                            1
                            + (self.player.meta.get("boss_damage") if enemy.boss_id else 0)
                            + (
                                self.player.meta.get("execute")
                                if enemy.health <= enemy.max_health * 0.35
                                else 0
                            )
                        )
                        dealt = min(enemy.health, amount)
                        damage_enemy(enemy, amount, ability.school)
                        if ability.mechanics.heal:
                            automatic_heal(self.player, dealt * ability.mechanics.heal)
                        status.timer += 1
                if status.spread and (enemy.health <= 0 or status.remaining <= 0):
                    for other in self.near(enemy.pos, 130 * status.radius_scale):
                        if other is not enemy and aid not in other.statuses:
                            transfers.append((other, ability, status))
                if status.burst and enemy.health <= 0:
                    self.disk(
                        enemy.pos,
                        110 * status.radius_scale,
                        status.damage * 2,
                        ability,
                        self.state(aid),
                    )
                    self.show(enemy.pos, 110 * status.radius_scale, ability)
                if status.remaining <= 0 or enemy.health <= 0:
                    del enemy.statuses[aid]
        for other, ability, status in transfers:
            self.mark(other, ability, status.damage * 0.75, 3, spread=False)
