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
        + ability.mechanics.extra_pets
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
                if ability.kind in {"projectile", "field", "charge"} or ability.mechanics.ranged
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
                    combat.player.pos
                    + Vector2(min(45, ability.mechanics.leash), 0).rotate(i * 137.5),
                    ability.id,
                    combat.player,
                    ability.mechanics.summon,
                    leash=ability.mechanics.leash,
                    formation=i,
                )
            )
            if combat.visuals is not None and len(combat.visuals) < 180:
                combat.visuals.append(
                    Visual(
                        combat.companions[-1].pos.copy(), 38, ability.color, 0.35, 0.35, "summon"
                    )
                )
            else:
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
        if (
            ability.kind == "companion"
            and enemy.pos.distance_squared_to(self.player.pos) > m.leash**2
        ):
            return
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
        if not secondary and ((m.dot and state.rank >= m.dot_rank) or m.slow):
            stats = self.stats(ability, state)
            self.mark(
                enemy,
                ability,
                (damage if m.ranged else stats.damage) * m.dot,
                stats.duration,
                m.spread_dot,
            )
        if not secondary and m.splash and state.rank >= m.splash_rank:
            stats = self.stats(ability, state)
            splash = m.splash * (
                (1 + 0.12 * max(0, state.rank - 4))
                * stats.radius
                / ability.ranks[state.rank - 1].radius
                if m.ranged
                else 1 + 0.2 * self.player.passive("area")
            )
            for other in self.near(enemy.pos, splash):
                if other is not enemy:
                    self.hit(
                        other, (damage if m.ranged else stats.damage) * 0.6, ability, state, True
                    )
            self.show(enemy.pos, splash, ability)

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
        self.update_companions(dt)
        self.update_projectiles(dt)
        self.update_fields(dt)
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
                        if ability.kind == "companion":
                            shot.target = min(
                                (
                                    e
                                    for e in self.near(shot.pos, 400)
                                    if e.id not in shot.hit
                                    and e.pos.distance_squared_to(self.player.pos)
                                    <= ability.mechanics.leash**2
                                ),
                                key=lambda e: e.pos.distance_squared_to(shot.pos),
                                default=None,
                            )
                        else:
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
                if (
                    ability.kind == "companion"
                    and enemy.pos.distance_squared_to(self.player.pos) > ability.mechanics.leash**2
                ):
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
            stats = self.stats(ability, state)
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
                self.update_permanent_pet(pet, ability, state, stats, dt)
        self.companions[:] = [p for p in self.companions if p.life != 0]

    def pet_candidates(self, pet: Companion, reach: float) -> list[Enemy]:
        """Use local cells and filter the owner leash before selecting a target."""
        return [
            e
            for e in self.near(pet.pos, reach)
            if e.pos.distance_squared_to(pet.owner.pos) <= pet.leash**2
        ]

    def pet_target(self, pet: Companion, candidates: list[Enemy], clusters: bool) -> Enemy | None:
        # One local pass counts occupied cells; no quadratic cluster search.
        density: dict[tuple[int, int], int] = {}
        if clusters:
            for enemy in candidates:
                key = self.grid.key(enemy.pos)
                density[key] = density.get(key, 0) + 1
        return min(
            candidates,
            key=lambda e: (
                e.pos.distance_squared_to(pet.pos)
                / (1 + min(6, density.get(self.grid.key(e.pos), 0))),
                (e.id - pet.formation) % max(1, len(candidates)),
            ),
            default=None,
        )

    def update_permanent_pet(
        self, pet: Companion, ability: Ability, state: SpellState, stats: SpellStats, dt: float
    ) -> None:
        m = ability.mechanics
        start = pet.pos.copy()
        offset = pet.pos - pet.owner.pos
        if offset.length_squared() > pet.leash**2:
            # Return immediately after teleports; never continue chasing a stale target.
            pet.pos = pet.owner.pos + Vector2(min(45, pet.leash), 0).rotate(pet.formation * 137.5)
            pet.target = None
            pet.target_timer = 0
        reach = min(pet.leash, m.attack_range + m.range_per_rank * (state.rank - 1))
        pet.target_timer -= dt
        pet.leap_timer = max(0, pet.leap_timer - dt)
        pet.timer = max(0, pet.timer - dt)
        target = pet.target
        invalid = target is not None and (
            target.health <= 0
            or target.pos.distance_squared_to(pet.owner.pos) > pet.leash**2
            or target.pos.distance_squared_to(pet.pos) > (reach + target.radius) ** 2
        )
        if invalid or pet.target_timer <= 0:
            candidates = self.pet_candidates(pet, reach)
            pet.target = self.pet_target(pet, candidates, state.rank >= 4 or ability.evolved)
            pet.target_timer = 0.12 + (pet.formation % 4) * 0.015
        target = pet.target
        home = pet.owner.pos + Vector2(-45, 30).rotate(pet.formation * 137.5)
        goal = home if m.ranged or target is None else target.pos
        delta = goal - pet.pos
        stop = 5 if m.ranged or target is None else max(8, stats.radius * 0.65)
        if delta.length_squared() > stop**2:
            direction = delta.normalize()
            speed = m.movement_speed + (state.rank - 1) * 12
            step = min(delta.length() - stop, speed * dt)
            if target and not m.ranged and state.rank >= m.leap_rank and pet.leap_timer <= 0:
                step = min(delta.length() - stop, max(step, m.leap_distance))
                pet.leap_timer = max(0.5, stats.cooldown * 1.5)
            pet.pos += direction * step
            pet.facing = direction
        offset = pet.pos - pet.owner.pos
        if offset.length_squared() > pet.leash**2:
            pet.pos = pet.owner.pos + offset.normalize() * pet.leash
        pet.moving = pet.pos.distance_squared_to(start) > 0.01
        if target is None or target.health <= 0:
            return
        delta = target.pos - pet.pos
        attack_reach = reach if m.ranged else stats.radius + target.radius
        if delta.length_squared() > attack_reach**2 or pet.timer > 0:
            return
        if delta.length_squared() > 1:
            pet.facing = delta.normalize()
        buff = 1 + pet.owner.buff_power if pet.owner.pet_buff and pet.owner.buff_time > 0 else 1
        if m.ranged:
            candidates = self.pet_candidates(pet, reach)
            others = sorted(
                (e for e in candidates if e is not target),
                key=lambda e: e.pos.distance_squared_to(pet.pos),
            )
            targets = [target] + others
            count = m.volley_count + (1 if state.rank >= m.volley_rank else 0)
            for i in range(count):
                victim = (
                    targets[(i + pet.formation) % len(targets)]
                    if ability.evolved
                    else targets[i % len(targets)]
                )
                aim = victim.pos - pet.pos
                direction = aim.normalize() if aim.length_squared() > 1 else pet.facing
                # Anchor at the casting hand height, just ahead of the Imp body.
                origin = pet.pos + Vector2(0, -20) + direction * 10
                aim = victim.pos - origin
                direction = aim.normalize() if aim.length_squared() > 1 else direction
                self.projectiles.append(
                    Projectile(
                        origin,
                        direction * stats.speed,
                        ability.id,
                        stats.damage * buff,
                        stats.radius,
                        0,
                        reach / max(1, stats.speed) + 0.25,
                    )
                )
            self.show(pet.pos + Vector2(0, -20), 18, ability, pet.facing)
        else:
            self.disk(target.pos, stats.radius, stats.damage * buff, ability, state)
            # Reuse directional slash art while preserving the detailed wolf atlas.
            if self.visuals is not None and len(self.visuals) < 180:
                self.visuals.append(
                    Visual(
                        target.pos.copy(),
                        stats.radius,
                        ability.color,
                        0.24,
                        0.24,
                        "cleave",
                        pet.facing.copy(),
                    )
                )
            self.show(target.pos, stats.radius, ability)
        pet.timer = stats.cooldown
        pet.attack_time = 0.3

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
