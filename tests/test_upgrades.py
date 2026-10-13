import random

import pytest
from pygame import Vector2

from warcraft_survivors.combat import hurt_player, spell_stats
from warcraft_survivors.entities import ManualState, SpellState
from warcraft_survivors.progression import xp_required
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.upgrades import apply, eligible, roll


def test_xp_thresholds_and_one_level_at_a_time(content):
    assert xp_required(1) == pytest.approx(18.6)
    assert all(xp_required(level + 1) > xp_required(level) for level in range(1, 100))
    with pytest.raises(ValueError):
        xp_required(0)
    sim = Simulation(content)
    sim.player.xp = xp_required(1) + xp_required(2) + 3
    sim.level_check()
    assert sim.player.level == 2 and len(sim.choices) == 3
    sim.choose(0)
    assert sim.player.level == 3 and len(sim.choices) == 3
    assert sim.player.xp == pytest.approx(3)
    sim.choose(0)
    assert not sim.choices


def test_visible_gems_preserve_xp_and_can_be_collected(content):
    sim = Simulation(content)
    sim.drop(sim.player.pos, "xp", 5)
    sim.drop(sim.player.pos, "xp", 7)
    assert len(sim.pickups) == 1
    sim.collect_pickups(FIXED_DT)
    assert sim.player.xp == 12 and not sim.pickups


def test_randomized_unique_cards_and_maximum_rank_exclusion(content):
    sim = Simulation(content)
    seen = set()
    for seed in range(120):
        cards = roll(content, "paladin", sim.player, random.Random(seed))
        assert len(cards) == 3 and len({(c.kind, c.id) for c in cards}) == 3
        assert cards == roll(content, "paladin", sim.player, random.Random(seed))
        seen.add(tuple(c.id for c in cards))
    assert len(seen) > 10
    sim.player.spells = {
        aid: SpellState(8, modifiers={"force"}) for aid in content.classes["paladin"].abilities[:8]
    }
    sim.player.manual = ManualState("divine_shield", 3)
    sim.player.passives = {pid: p.max_rank for pid, p in content.passives.items()}
    assert {c.kind for c in eligible(content, "paladin", sim.player)} == {"reward"}
    assert len(roll(content, "paladin", sim.player, random.Random())) == 3
    sim.player.passives["armor"] = 4
    cards = eligible(content, "paladin", sim.player)
    assert sum(c.kind == "passive" for c in cards) == 1 and len(cards) >= 3


@pytest.mark.parametrize("pid", ("projectiles", "area", "might", "armor", "health", "judgment"))
def test_every_upgrade_has_actual_gameplay_effect(content, pid):
    sim = Simulation(content)
    p = sim.player
    ability, state = content.abilities["judgment"], p.spells["judgment"]
    before = spell_stats(ability, state, p)
    choice = next(c for c in eligible(content, "paladin", p) if c.id == pid)
    apply(content, "paladin", p, choice)
    after = spell_stats(ability, state, p)
    if pid == "projectiles":
        sim.combat.cast(ability, state)
        assert after.count == before.count + 1 and len(sim.projectiles) == 2
    elif pid == "area":
        assert after.radius == pytest.approx(before.radius * 1.2)
    elif pid == "might":
        assert after.damage == pytest.approx(before.damage * 1.15)
    elif pid == "armor":
        hurt_player(p, 100)
        assert p.max_health - p.health == pytest.approx(82)
    elif pid == "health":
        assert p.max_health == 155 and p.health == 155
    else:
        assert after.damage > before.damage and after.cooldown < before.cooldown


def test_area_upgrade_changes_collision_result(content):
    def run(with_upgrade):
        sim = Simulation(content)
        enemy = sim.spawn("bandit", sim.player.pos + Vector2(90, 27))
        sim.grid.rebuild(sim.enemies)
        if with_upgrade:
            sim.player.passives["area"] = 1
        sim.player.facing.update(1, 0)
        # Cast along x, then offset enemy; avoid aim compensating for radius.
        sim.grid.rebuild([])
        sim.combat.cast(content.abilities["judgment"], sim.player.spells["judgment"])
        sim.grid.rebuild(sim.enemies)
        sim.combat.update_projectiles(0.3)
        return enemy.health

    assert run(True) < run(False)


def test_one_selection_and_stale_upgrade_rejection(content):
    sim = Simulation(content)
    choice = next(c for c in eligible(content, "paladin", sim.player) if c.id == "judgment")
    apply(content, "paladin", sim.player, choice)
    with pytest.raises(ValueError):
        apply(content, "paladin", sim.player, choice)
    sim.player.xp = sim.player.xp_required
    sim.level_check()
    choice = sim.choices[0]
    sim.choose(0)
    snapshot = (sim.player.spells["judgment"].rank, dict(sim.player.passives))
    sim.choose(0)
    assert snapshot == (sim.player.spells["judgment"].rank, sim.player.passives)
    assert not sim.choices and choice is not None


def test_level_pause_freezes_movement_cooldowns_enemies_and_timer(content):
    sim = Simulation(content)
    sim.player.xp = sim.player.xp_required
    sim.level_check()
    position, timer = sim.player.pos.copy(), sim.player.spells["judgment"].timer
    for _ in range(60):
        sim.step(FIXED_DT)
    assert sim.time == 0 and sim.player.pos == position
    assert sim.player.spells["judgment"].timer == timer and not sim.enemies
