"""Displayed forecasts must agree with the upgrade actually applied to gameplay."""

from dataclasses import replace

import pytest
from pygame import Vector2

from warcraft_survivors.combat import spell_stats
from warcraft_survivors.content import load_content
from warcraft_survivors.descriptions import (
    automatic_notes,
    automatic_values,
    describe_choice,
    evolution_requirements,
    manual_values,
    number,
    passive_values,
)
from warcraft_survivors.entities import ManualState, SpellState
from warcraft_survivors.input_labels import controller_labels
from warcraft_survivors.meta import MetaBonuses, load_progression
from warcraft_survivors.meta_descriptions import bonus_summary
from warcraft_survivors.simulation import Simulation
from warcraft_survivors.upgrades import Choice, apply, eligible

CONTENT = load_content()
SPELLS = [(cid, aid) for cid, c in CONTENT.classes.items() for aid in c.abilities]
MANUALS = [(cid, mid) for cid, c in CONTENT.classes.items() for mid in c.manuals]


@pytest.mark.parametrize("cid,aid", SPELLS)
def test_each_spell_rank_forecast_matches_applied_effective_damage_and_timing(content, cid, aid):
    sim = Simulation(content, cid)
    p = sim.player
    p.passives = {"might": 2, "haste": 1, "area": 2, "projectiles": 1}
    p.meta = MetaBonuses({"damage": 0.07, "haste": 0.05, "count": 1})
    p.spells = {}
    for rank in range(1, 9):
        choice = next(c for c in eligible(content, cid, p) if c.kind == "spell" and c.id == aid)
        assert choice.rank == rank
        text = describe_choice(content, p, choice)
        assert text.kind == ("New Ability" if rank == 1 else "Spell Upgrade")
        assert text.rank == ("Rank 1 / 8" if rank == 1 else f"Rank {rank - 1} to {rank} / 8")
        before = spell_stats(content.abilities[aid], p.spells[aid], p) if rank > 1 else None
        apply(content, cid, p, choice)
        actual = spell_stats(content.abilities[aid], p.spells[aid], p)
        damage_line = next(line for line in text.changes if line.startswith("Damage per"))
        assert damage_line.endswith(number(actual.damage))
        if before:
            assert number(before.damage) + " to " in damage_line
        time_line = next(
            line for line in text.changes if line.startswith(("Cast interval", "Attack interval"))
        )
        assert time_line.endswith(number(actual.cooldown) + "s")
        assert "Effective now" in text.basis
    assert not any(c.kind == "spell" and c.id == aid for c in eligible(content, cid, p))
    equipped = describe_choice(content, p, Choice("spell", aid, "", "", 8, 0))
    assert equipped.kind == "Equipped Ability" and equipped.rank == "Rank 8 / 8 · MAX"
    assert not equipped.changes


@pytest.mark.parametrize("cid,mid", MANUALS)
def test_manual_forecasts_only_consumed_stats_and_actual_activation(content, cid, mid):
    sim = Simulation(content, cid)
    manual = content.manuals[mid]
    p = sim.player
    p.passives = {"haste": 2, "duration": 1, "might": 1}
    p.meta = MetaBonuses({"manual_haste": 0.05, "healing": 0.1})
    for rank in range(1, 4):
        p.manual = ManualState(mid, rank - 1) if rank > 1 else None
        choice = next(c for c in eligible(content, cid, p) if c.kind == "manual" and c.id == mid)
        text = describe_choice(content, p, choice, "Cross")
        assert text.kind == ("Manual Ability" if rank == 1 else "Manual Upgrade")
        assert text.notes[0] == "Activate with Cross."
        apply(content, cid, p, choice)
        values = {v.label: v.amount for v in manual_values(manual, rank, p)}
        p.health = p.max_health / 2
        p.manual.timer = 0
        assert sim.activate_manual(Vector2(1, 0))
        if manual.kind == "circle":
            assert p.manual.timer == 0 and sim.activate_manual()
        cooldown = values.get("Cooldown", values.get("Cooldown after return"))
        assert p.manual.timer == pytest.approx(cooldown)
        if manual.kind in {"blink", "leap"}:
            assert p.immune == pytest.approx(values["Arrival immunity"])
            assert "Effect duration" not in values and "power" not in choice.description
        elif manual.kind == "immune":
            assert p.immune == pytest.approx(values["Invulnerability"])
        elif manual.kind == "shield":
            assert p.shield == values["Shield"]
        elif manual.kind == "guard":
            assert min(75, (p.armor + p.guard_strength) * 100) == values["Armor after activation"]
        elif manual.kind == "buff":
            assert p.buff_power * 100 == values["Damage bonus"]
    assert not any(c.kind == "manual" for c in eligible(content, cid, p))


@pytest.mark.parametrize("pid", list(CONTENT.passives))
def test_passive_text_is_numeric_and_keeps_scope_and_maximum(content, pid):
    sim = Simulation(content)
    p = sim.player
    for rank in range(1, 6):
        choice = next(
            c for c in eligible(content, "paladin", p) if c.kind == "passive" and c.id == pid
        )
        text = describe_choice(content, p, choice)
        assert text.kind == "Passive Upgrade" and text.rank == f"Rank {rank - 1} to {rank} / 5"
        assert " to " in text.changes[0] and content.passives[pid].applicability in text.notes
        apply(content, "paladin", p, choice)
        assert p.passive(pid) == rank
    assert not any(c.kind == "passive" and c.id == pid for c in eligible(content, "paladin", p))
    if pid == "health":
        assert p.max_health == 235
    if pid == "area":
        assert passive_values(pid, 5)[0].amount == 100


@pytest.mark.parametrize("cid,aid", SPELLS)
def test_evolution_readiness_and_forecast_use_real_transformed_spell(content, cid, aid):
    sim = Simulation(content, cid)
    a = content.abilities[aid]
    assert a.evolution
    p = sim.player
    p.spells = {aid: SpellState(8)}
    before = evolution_requirements(content, p, aid)
    assert before[0] == "Evolution: " + a.evolution.name and "Required at Rank 1+" in before[2]
    p.passives[a.evolution.passive] = 1
    requirement = evolution_requirements(content, p, aid, True)
    assert (
        "Complete" in requirement[1] and "Owned" in requirement[2] and "Open now" in requirement[3]
    )
    choice = next(c for c in eligible(content, cid, p, True) if c.id == aid)
    text = describe_choice(content, p, choice)
    expected = spell_stats(content.ability(a.evolution.id), p.spells[aid], p)
    apply(content, cid, p, choice, True)
    actual = spell_stats(content.ability(a.evolution.id), p.spells[a.evolution.id], p)
    assert text.kind == "Evolution" and actual == expected
    assert not any(word in text.summary for word in ("True", "False", "enabled:", "radial_rank"))
    assert next(line for line in text.changes if line.startswith("Damage")).endswith(
        number(actual.damage)
    )
    equipped = describe_choice(content, p, Choice("spell", a.evolution.id, "", "", 8, 0))
    assert "MAX" in equipped.rank
    assert "already equipped" in evolution_requirements(content, p, a.evolution.id)[0]


def test_real_milestones_and_fixed_intervals_replace_prompt_example_numbers(content):
    sim = Simulation(content)
    wolves = content.abilities["beast_companion"]
    assert automatic_values(wolves, SpellState(3), sim.player)[0].amount == 1
    assert automatic_values(wolves, SpellState(4), sim.player)[0].amount == 2
    imp = content.abilities["summon_felguard"]
    assert automatic_values(imp, SpellState(4), sim.player)[0].amount == 1
    assert automatic_values(imp, SpellState(5), sim.player)[0].amount == 2
    assert automatic_values(imp, SpellState(6), sim.player)[1].amount == 2
    sim.player.meta = MetaBonuses({"spell:summon_felguard:splash_flat": 15})
    assert "Firebolts splash nearby enemies." in automatic_notes(imp, SpellState(1), sim.player)
    assert "units" not in bonus_summary(sim.player.meta.values, content)
    for rank in (5, 6):
        assert (
            "Damage interval: 0.5s"
            in automatic_notes(content.abilities["blizzard"], SpellState(rank), sim.player)[0]
        )
    assert "stun" not in content.abilities["shockwave"].description
    assert "Persistent" not in content.abilities["mind_sear"].description


@pytest.mark.parametrize("branch", ["force", "reach"])
def test_branches_compare_real_stats_and_preserve_exclusivity(content, branch):
    sim = Simulation(content)
    sim.player.spells["judgment"].rank = 4
    choice = next(
        c for c in eligible(content, "paladin", sim.player) if c.id == "judgment:" + branch
    )
    text = describe_choice(content, sim.player, choice)
    apply(content, "paladin", sim.player, choice)
    stats = spell_stats(content.abilities["judgment"], sim.player.spells["judgment"], sim.player)
    assert text.kind == "Special Modifier" and text.changes
    if branch == "force":
        assert "casts take longer" in text.summary
        assert any(line.endswith(number(stats.cooldown) + "s") for line in text.changes)
    else:
        assert any("Shot width" in line for line in text.changes)
    assert not any(c.kind == "modifier" for c in eligible(content, "paladin", sim.player))


@pytest.mark.parametrize("sid", list(load_progression().shared))
def test_shared_bonus_formats_every_capped_rank_from_authoritative_effects(content, sid):
    u = load_progression().shared[sid]
    for rank in range(u.max_rank + 1):
        text = bonus_summary({key: value * rank for key, value in u.effects.items()}, content)
        assert text and not any(key + ":" in text for key in ("chest_gold", "banishes"))
    assert len(u.costs) == u.max_rank


@pytest.mark.parametrize(
    "name,accept,details",
    [
        ("Xbox Wireless Controller", "A", "LB"),
        ("Sony DualSense", "Cross", "L1"),
        ("USB Generic Gamepad", "Button 1", "Left shoulder"),
    ],
)
def test_controller_family_labels_have_a_safe_fallback(name, accept, details):
    labels = controller_labels(name)
    assert labels.accept == accept and labels.details == details


def test_description_generation_never_mutates_state(content):
    sim = Simulation(content)
    before = replace(
        sim.player, spells=sim.player.spells.copy(), passives=sim.player.passives.copy()
    )
    for c in eligible(content, "paladin", sim.player):
        describe_choice(content, sim.player, c)
    assert sim.player == before
