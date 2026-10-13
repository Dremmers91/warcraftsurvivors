import pytest
from pygame import Vector2

from warcraft_survivors.camera import Camera
from warcraft_survivors.movement import (
    analog_direction,
    chase,
    cursor_direction,
    keyboard_direction,
)
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.world import Obstacle, SpatialHash, World


def test_diagonal_and_analog_calculations():
    assert keyboard_direction(False, True, False, True).length() == pytest.approx(1)
    assert keyboard_direction(True, True, True, True) == Vector2()
    assert analog_direction(0.1, -0.1) == Vector2()
    assert analog_direction(1, 1).length() == pytest.approx(1)
    assert 0 < analog_direction(0.5, 0).length() < 1
    assert cursor_direction(Vector2(100, 0), Vector2()) == Vector2(1, 0)
    assert cursor_direction(Vector2(5, 0), Vector2()) == Vector2()


@pytest.mark.parametrize(
    "dt,move", ((1 / 30, Vector2(1, 1)), (1 / 60, Vector2(1, 0)), (1 / 120, Vector2(1, 1)))
)
def test_movement_is_frame_independent(content, dt, move):
    sim = Simulation(content)
    origin = sim.player.pos.copy()
    for _ in range(round(0.5 / dt)):
        sim.step(dt, move)
    assert sim.player.pos.distance_to(origin) == pytest.approx(107.5)


def test_smooth_camera_is_frame_independent_and_bounded():
    a, b = Camera(Vector2(4096, 4096)), Camera(Vector2(4096, 4096))
    target = Vector2(4500, 4096)
    old = a.pos.copy()
    a.update(target, 0.1)
    assert old.x < a.pos.x < World.camera(target).x
    for _ in range(10):
        b.update(target, 0.01)
    assert a.pos.distance_to(b.pos) < 0.0001
    a.update(Vector2(-500, 50000), 100)
    assert a.pos == World.camera(Vector2(-500, 50000))


def test_player_cannot_tunnel_through_obstacles(content):
    sim = Simulation(content)
    world = sim.world
    world.obstacles = [Obstacle(Vector2(4096, 4096), 24, 0)]
    world.grid.rebuild(world.obstacles)
    start = Vector2(4000, 4096)
    result = world.move(start, Vector2(250, 0))
    assert result.x <= 4096 - 24 - 14 + 0.2


def test_enemy_navigation_goes_around_tree_without_overlap(content):
    sim = Simulation(content)
    world = sim.world
    world.obstacles = [Obstacle(Vector2(4096, 4096), 24, 0)]
    world.grid.rebuild(world.obstacles)
    enemy = sim.spawn("kobold", Vector2(3970, 4096))
    goal = Vector2(4250, 4096)
    grid = SpatialHash()
    for _ in range(500):
        grid.rebuild([enemy])
        chase(enemy, goal, FIXED_DT, world, grid)
        assert enemy.pos.distance_to(world.obstacles[0].pos) >= 24 + enemy.radius - 0.01
    assert enemy.pos.distance_to(goal) < 20


def test_enemy_separation_reduces_body_overlap(content):
    sim = Simulation(content)
    a = sim.spawn("kobold", Vector2(4096, 4096))
    b = sim.spawn("kobold", Vector2(4096, 4096))
    for _ in range(60):
        sim.grid.rebuild(sim.enemies)
        chase(a, Vector2(4500, 4096), FIXED_DT, sim.world, sim.grid)
        chase(b, Vector2(4500, 4096), FIXED_DT, sim.world, sim.grid)
    assert a.pos.distance_to(b.pos) > 10
