"""Pure input vectors plus obstacle-aware movement, independently testable."""

from __future__ import annotations

from pygame import Vector2

from .entities import Enemy
from .world import SpatialHash, World


def normalized(move: Vector2) -> Vector2:
    return move.normalize() if move.length_squared() > 1 else move.copy()


def keyboard_direction(left: bool, right: bool, up: bool, down: bool) -> Vector2:
    return normalized(Vector2(int(right) - int(left), int(down) - int(up)))


def analog_direction(x: float, y: float, deadzone: float = 0.18) -> Vector2:
    direction = Vector2(x, y)
    length = direction.length()
    if length <= deadzone:
        return Vector2()
    return direction / length * min(1, (length - deadzone) / (1 - deadzone))


def cursor_direction(cursor_world: Vector2, player_pos: Vector2) -> Vector2:
    delta = cursor_world - player_pos
    length = delta.length()
    return delta / length * min(1, length / 40) if length > 8 else Vector2()


def chase(
    enemy: Enemy,
    goal: Vector2,
    dt: float,
    world: World,
    grid: SpatialHash[Enemy],
    neighbor_limit: int = 24,
) -> None:
    delta = goal - enemy.pos
    if delta.length_squared() < 0.01:
        return
    desired = delta.normalize()
    enemy.steering_time -= dt
    if enemy.steering_time <= 0:
        refresh_steering(enemy, desired, world, grid, neighbor_limit)
        # Staggered local steering is cosmetic crowd separation. Body collision,
        # pursuit direction, attack timers and player contact retain fixed steps.
        enemy.steering_time = 0.075 + (enemy.id % 7) * 0.008
    steering = desired + enemy.avoidance
    heading = steering.normalize() if steering.length_squared() > 0.001 else desired
    move = heading * enemy.speed * dt + enemy.separation * 65 * dt
    enemy.pos = world.move(enemy.pos, move, enemy.radius)


def refresh_steering(
    enemy: Enemy, desired: Vector2, world: World, grid: SpatialHash[Enemy], neighbor_limit: int
) -> None:
    steering = Vector2()
    # Stable tangent choice lets a pursuing enemy go around a tree rather than
    # repeatedly pushing straight into its trunk.
    for obstacle in world.grid.nearby(enemy.pos, 90):
        offset = obstacle.pos - enemy.pos
        ahead = offset.dot(desired)
        sideways = abs(offset.cross(desired))
        if 0 < ahead < 70 and sideways < enemy.radius + obstacle.radius + 5:
            side = 1 if offset.cross(desired) >= 0 else -1
            if sideways < 0.1:
                side = 1 if enemy.id % 2 else -1
            steering += desired.rotate(90 * side) * (1.6 * (1 - ahead / 90))
    repulsion = Vector2()
    for index, other in enumerate(grid.nearby(enemy.pos, enemy.radius + 16)):
        if index >= neighbor_limit:
            break
        if other.id == enemy.id or other.health <= 0:
            continue
        offset = enemy.pos - other.pos
        distance = offset.length()
        overlap = enemy.radius + other.radius - distance
        if overlap > 0:
            normal = (
                offset / distance
                if distance > 1.0
                else Vector2(1 if enemy.id > other.id else -1, 0)
            )
            repulsion += normal * (overlap / (enemy.radius + other.radius))
    enemy.avoidance.update(steering)
    enemy.separation.update(normalized(repulsion))
