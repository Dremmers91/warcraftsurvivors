from dataclasses import replace

import pytest
from pygame import Vector2

from warcraft_survivors.content import Mechanics
from warcraft_survivors.entities import SpellState
from warcraft_survivors.simulation import Simulation


@pytest.mark.parametrize(
    "kind",
    (
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
    ),
)
def test_shared_behavior_damages_stationary_target(content, kind, monkeypatch):
    sim = Simulation(content)
    enemy = sim.spawn("bandit", sim.player.pos + Vector2(50, 0))
    enemy.health = enemy.max_health = 10000
    sim.grid.rebuild(sim.enemies)
    template = content.abilities["judgment"]
    ability = replace(
        template,
        kind=kind,
        ranks=tuple(replace(r, radius=100, damage=10, duration=2) for r in template.ranks),
        mechanics=Mechanics(dot=1, follow=kind == "field"),
    )
    monkeypatch.setitem(content.abilities, "judgment", ability)
    sim.combat.cast(ability, SpellState())
    for _ in range(120):
        sim.combat.update_projectiles(1 / 60)
        sim.combat.update_fields(1 / 60)
        sim.combat.update_companions(1 / 60)
        sim.combat.update_statuses(1 / 60)
    assert enemy.health < enemy.max_health


def test_companion_has_no_enemy_health_and_leashes(content, monkeypatch):
    sim = Simulation(content)
    ability = replace(content.abilities["judgment"], kind="companion")
    monkeypatch.setitem(content.abilities, "judgment", ability)
    sim.combat.cast(ability, SpellState())
    pet = sim.combat.companions[0]
    assert pet.owner is sim.player and not hasattr(pet, "health")
    sim.player.pos += Vector2(2000, 0)
    sim.combat.update_companions(1 / 60)
    assert pet.pos.distance_to(sim.player.pos) <= pet.leash + 1e-6
