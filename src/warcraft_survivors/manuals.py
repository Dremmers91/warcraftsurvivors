"""Manual activation and timed hero effects, independent of input devices and UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Vector2

from .combat import damage_enemy
from .content import SCHOOLS, Manual
from .entities import Player, Visual
from .passive_effects import BONUS

if TYPE_CHECKING:
    from .simulation import Simulation


def manual_cooldown(manual: Manual, rank: int, player: Player) -> float:
    return (
        manual.ranks[rank - 1].cooldown
        * max(0.4, 1 - BONUS["haste"] * player.passive("haste"))
        * max(0.65, 1 - player.meta.get("haste") - player.meta.get("manual_haste"))
    )


def manual_duration(manual: Manual, rank: int, player: Player) -> float:
    return (
        manual.ranks[rank - 1].duration
        * (1 + BONUS["duration"] * player.passive("duration"))
        * (1 + player.meta.get("duration"))
    )


def activate(sim: Simulation, direction: Vector2 | None = None) -> bool:
    p = sim.player
    state = p.manual
    if state is None or state.timer > 0 or sim.finished or sim.choices or p.health <= 0:
        return False
    ability = sim.content.manuals[state.id]
    rank = ability.ranks[state.rank - 1]
    duration = manual_duration(ability, state.rank, p)
    heading = (
        direction.normalize()
        if direction is not None and direction.length_squared() > 0.01
        else p.facing
    )
    if ability.kind == "circle" and state.circle is None:
        state.circle = sim.world.resolve(p.pos, p.radius)
        sim.notify("Circle placed · Space / A returns from any distance")
        return True
    if ability.kind == "circle":
        assert state.circle is not None
        p.pos = sim.world.resolve(state.circle, p.radius)
        sim.camera.pos = sim.world.camera(p.pos)
        state.circle = None
        p.immune = 0.5
    elif ability.kind in {"blink", "leap"}:
        destination = sim.world.resolve(
            p.pos + heading * rank.distance * ability.direction, p.radius
        )
        p.pos = destination
        p.immune = 0.5 + 0.2 * (state.rank - 1)
        if ability.kind == "leap":
            for enemy in sim.combat.near(p.pos, 100 * (1 + BONUS["area"] * p.passive("area"))):
                damage_enemy(
                    enemy,
                    rank.power * (1 + BONUS["might"] * p.passive("might")),
                    ability.school,
                    source=ability.id,
                    delivery="manual",
                )
    elif ability.kind == "immune":
        p.immune = duration
        if ability.root:
            p.rooted = duration
            p.block_regen = ability.regen
    elif ability.kind == "guard":
        p.guard = duration
        p.guard_strength = 0.5 * rank.power
        p.shield = max(p.shield, ability.shield_fraction * p.max_health * rank.power)
        p.shield_time = duration
    elif ability.kind == "heal":
        p.health = min(
            p.max_health, p.health + p.max_health * rank.power * (1 + p.meta.get("healing"))
        )
        p.shield = max(p.shield, p.max_health * max(0, rank.power - 1))
        p.shield_time = 5
    elif ability.kind == "shield":
        p.shield = max(p.shield, rank.power)
        p.shield_time = duration
    elif ability.kind == "buff":
        p.buff_time, p.buff_power, p.buff_school, p.pet_buff = (
            duration,
            rank.power,
            ability.buff_school,
            ability.pet_buff,
        )
    elif ability.kind == "rally":
        if p.rally_bonus:
            p.max_health -= p.rally_bonus
        p.rally_bonus = p.max_health * rank.power
        p.max_health += p.rally_bonus
        p.health = min(p.max_health, p.health + p.rally_bonus)
        p.rally_time = duration
    elif ability.kind == "fear":
        for enemy in sim.combat.near(
            p.pos, rank.distance * (1 + BONUS["area"] * p.passive("area"))
        ):
            enemy.fear = 0 if enemy.boss_id else min(duration, 1.5) if enemy.elite else duration
            damage_enemy(
                enemy,
                rank.power * (1 + BONUS["might"] * p.passive("might")),
                ability.school,
                source=ability.id,
                delivery="manual",
            )
    state.timer = manual_cooldown(ability, state.rank, p)
    sim.visuals.append(Visual(p.pos.copy(), 100, SCHOOLS[ability.school], 0.6, 0.6, state.id))
    p.cast_age = 0
    sim.sound_events.append("cast_" + ability.school)
    return True


def update(player: Player, dt: float) -> None:
    # This is called only by live simulation ticks, so pause freezes every buff/cooldown.
    if player.manual:
        player.manual.timer = max(0, player.manual.timer - dt)
    for attr in ("immune", "guard", "shield_time", "buff_time", "rooted", "rally_time"):
        setattr(player, attr, max(0, getattr(player, attr) - dt))
    if player.shield_time <= 0:
        player.shield = 0
    if player.rally_bonus and player.rally_time <= 0:
        player.max_health -= player.rally_bonus
        player.health = min(player.health, player.max_health)
        player.rally_bonus = 0
    regen = (
        BONUS["regen"] * player.passive("regen")
        + player.meta.get("regen")
        + (player.max_health * player.block_regen if player.rooted > 0 else 0)
    )
    player.health = min(player.max_health, player.health + regen * dt)
