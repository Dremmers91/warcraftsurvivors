from pygame import Vector2

from warcraft_survivors.entities import Pickup
from warcraft_survivors.world import WORLD_SIZE, SpatialHash, World


def test_spatial_queries_match_brute_force_including_negative_cells():
    points = [
        Pickup(Vector2(x, y), "xp", 1) for x in range(-300, 300, 35) for y in range(-300, 300, 47)
    ]
    grid = SpatialHash(96)
    grid.rebuild(points)
    for center in (Vector2(0, 0), Vector2(-110, 205), Vector2(140, -180)):
        actual = {id(p) for p in grid.nearby(center, 157)}
        expected = {id(p) for p in points if p.pos.distance_to(center) <= 157}
        assert actual == expected


def test_world_is_finite_camera_scrolls_and_obstacles_resolve():
    world = World()
    assert world.clamp(Vector2(-200, 99999)) == Vector2(16, WORLD_SIZE - 16)
    assert world.camera(Vector2(4096, 4096)) != world.camera(Vector2(4500, 4096))
    assert world.camera(Vector2(0, 0)) == Vector2()
    obstacle = world.obstacles[0]
    resolved = world.resolve(obstacle.pos.copy())
    assert resolved.distance_to(obstacle.pos) >= obstacle.radius + 14
