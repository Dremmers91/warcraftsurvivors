from pygame import Rect, Vector2

from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.spawning import difficulty, spawn_interval
from warcraft_survivors.world import VIEW_SIZE, WORLD_SIZE


def test_difficulty_rises_gradually():
    assert spawn_interval(300) < spawn_interval(0)
    assert difficulty(300)[0] > difficulty(0)[0]
    assert difficulty(300)[1] > difficulty(0)[1]
    assert difficulty(300)[2] > difficulty(0)[2]


def test_spawns_are_outside_camera_even_at_world_edges(content):
    sim = Simulation(content)
    for pos in (Vector2(20, 20), Vector2(WORLD_SIZE - 20, WORLD_SIZE - 20), Vector2(4096, 4096)):
        camera = sim.world.camera(pos)
        view = Rect(round(camera.x), round(camera.y), *VIEW_SIZE)
        for _ in range(50):
            enemy = sim.spawner.create(0, camera, pos)
            assert not view.collidepoint(enemy.pos)
            assert enemy.radius <= enemy.pos.x <= WORLD_SIZE - enemy.radius


def test_spawn_timer_creates_enemies_and_kobolds_are_common(content):
    sim = Simulation(content)
    kinds = [sim.spawn().kind for _ in range(200)]
    assert kinds.count("kobold") > kinds.count("wolf")
    assert kinds.count("kobold") > kinds.count("bandit")
    sim = Simulation(content)
    sim.step(FIXED_DT)
    assert sim.enemies
