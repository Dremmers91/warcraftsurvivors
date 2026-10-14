"""Tree topology, old-profile retention, device input and actual new spell modifiers."""

import copy
import random

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.app import App
from warcraft_survivors.combat import spell_stats
from warcraft_survivors.entities import SpellState
from warcraft_survivors.meta import MetaBonuses, RunLoadout, load_progression, talent_reason
from warcraft_survivors.persistence import SaveStore
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.talent_ui import TREE_RECT, effect_summary, node_rect

META = load_progression()


@pytest.mark.parametrize("cid", tuple(META.trees))
def test_four_tiers_center_path_layout_and_rank_tables(cid):
    tree = META.trees[cid]
    assert len(tree) == 18 and {t.tier for t in tree.values()} == {0, 1, 2, 3}
    assert sum(t.max_rank for t in tree.values()) == 40
    assert [t.id for t in tree.values() if t.capstone] == ["capstone"]
    assert tree["capstone"].requires == {"preparation": 1}
    assert tree["preparation"].requires == {"duration": 1}
    assert tree["duration"].requires == {"might": 1}
    assert (
        len({tree[tid].position[0] for tid in ("might", "duration", "preparation", "capstone")})
        == 1
    )
    rectangles = [node_rect(t) for t in tree.values()]
    assert all(TREE_RECT.contains(r) and r.width == r.height == 64 for r in rectangles)
    assert all(not a.colliderect(b) for i, a in enumerate(rectangles) for b in rectangles[i + 1 :])
    for t in tree.values():
        assert t.class_id == cid and t.icon
        for rank in range(1, t.max_rank + 1):
            assert t.at_rank(rank) == {
                key: pytest.approx(value * rank) for key, value in t.effects.items()
            }
        for parent in t.requires:
            assert tree[parent].tier < t.tier and node_rect(tree[parent]).bottom < node_rect(t).top


@pytest.mark.parametrize("cid", tuple(META.trees))
def test_valid_legacy_allocations_and_starting_selections_survive_reopen(cid, tmp_path):
    # Generate legal former six-row allocations, including different purchase orders.
    rng = random.Random(42)
    for sample in range(30):
        raw = SaveStore.defaults()
        c = raw["classes"][cid]
        c["xp"] = 60 * 50 * 49
        allocated = {}
        for _ in range(sample + 11):
            eligible = [
                t
                for t in META.trees[cid].values()
                if allocated.get(t.id, 0) < t.max_rank
                and sum(allocated.values()) >= t.spent_required
                and all(
                    allocated.get(parent, 0) >= rank for parent, rank in t.legacy_requires.items()
                )
            ]
            if not eligible:
                break
            t = rng.choice(eligible)
            allocated[t.id] = allocated.get(t.id, 0) + 1
        c["talents"] = allocated.copy()
        c["starting_ability"] = (
            META.trees[cid]["preparation"].starting_options[0] if "preparation" in allocated else ""
        )
        clean = SaveStore.validate(raw)
        assert clean["classes"][cid]["talents"] == allocated
        assert clean["classes"][cid]["starting_ability"] == c["starting_ability"]
    save = SaveStore(tmp_path / "save.json")
    save.data = clean
    assert save.write()
    assert SaveStore(save.path).data["classes"][cid]["talents"] == allocated


@pytest.mark.parametrize("cid", tuple(META.trees))
def test_caps_tier_class_level_prerequisite_and_point_budget(cid):
    tree = META.trees[cid]
    assert "class level" in talent_reason(tree, 0, {}, "might")
    xp = 60 * 50 * 49
    assert "allocated" in talent_reason(tree, xp, {}, "armor")
    assert (
        talent_reason(tree, xp, {"health": 3}, "armor") == f"Requires {tree['might'].name} Rank 1."
    )
    assert not talent_reason(tree, xp, {"might": 3}, "armor")
    assert "fully" in talent_reason(tree, xp, {"might": 3}, "might")
    assert talent_reason(tree, 120, {"might": 1}, "health")
    assert talent_reason(tree, xp, {"might": 3, "health": 3, "haste": 3}, "capstone")


def sim_for(content, cid, aid, bonuses=None):
    sim = Simulation(content, cid, permanent=RunLoadout(MetaBonuses(bonuses or {})))
    sim.player.spells = {aid: SpellState()}
    target = sim.spawn("bandit", sim.player.pos + Vector2(60, 0))
    target.health = target.max_health = 10000
    return sim, target


@pytest.mark.parametrize(
    "cid,aid",
    (
        ("mage", "frostbolt"),
        ("warlock", "shadow_bolt"),
        ("priest", "smite"),
        ("paladin", "judgment"),
        ("hunter", "arcane_shot"),
    ),
)
def test_signature_extra_projectile_is_actually_cast(content, cid, aid):
    counts = []
    for bonuses in ({}, META.trees[cid]["signature"].at_rank(1)):
        sim, _ = sim_for(content, cid, aid, bonuses)
        sim.combat.cast(content.abilities[aid], sim.player.spells[aid])
        counts.append(len(sim.projectiles))
    assert counts[1] == counts[0] + 1


def test_divine_storm_extra_wave_deals_delayed_damage_and_keeps_evolved_base_id(content):
    for aid in ("divine_storm", "divine_storm_evolved"):
        sim, enemy = sim_for(content, "paladin", aid, {"spell:divine_storm:waves": 1})
        sim.combat.cast(content.ability(aid), sim.player.spells[aid])
        health = enemy.health
        assert len(sim.combat.fields) == 1 and sim.combat.fields[0].repeat_arc
        sim.combat.update_fields(0.1)
        assert enemy.health == health
        for _ in range(15):
            sim.combat.update_fields(FIXED_DT)
        assert enemy.health < health and not sim.combat.fields


@pytest.mark.parametrize(
    "cid,aid,tid",
    (
        ("warrior", "rend", "mastery"),
        ("warlock", "corruption", "technique"),
        ("priest", "shadow_word_pain", "offense"),
    ),
)
def test_dot_talent_early_and_wider_spread_is_real(content, cid, aid, tid):
    outcomes = []
    for bonuses in ({}, META.trees[cid][tid].at_rank(1)):
        sim, enemy = sim_for(content, cid, aid, bonuses)
        fresh = sim.spawn("bandit", enemy.pos + Vector2(150, 0))
        sim.combat.cast(content.abilities[aid], sim.player.spells[aid])
        enemy.health = 0
        sim.combat.update_statuses(FIXED_DT)
        outcomes.append(aid in fresh.statuses)
    assert outcomes == [False, True]


@pytest.mark.parametrize(
    "cid,aid,tid,offset",
    (("mage", "fireball", "technique", 90), ("warlock", "summon_felguard", "technique", 22)),
)
def test_splash_talents_reach_actual_additional_enemy(content, cid, aid, tid, offset):
    outcomes = []
    for bonuses in ({}, META.trees[cid][tid].at_rank(1)):
        sim, enemy = sim_for(content, cid, aid, bonuses)
        extra = sim.spawn("bandit", enemy.pos + Vector2(0, offset))
        extra.health = extra.max_health = 10000
        sim.combat.hit(enemy, 20, content.abilities[aid], sim.player.spells[aid])
        outcomes.append(extra.max_health - extra.health)
    assert outcomes[0] == 0 and outcomes[1] > 0


def test_wolf_opening_bonus_applies_once_per_pet(content):
    sim, enemy = sim_for(
        content, "hunter", "beast_companion", {"spell:beast_companion:opening": 0.15}
    )
    sim.combat.cast(content.abilities["beast_companion"], SpellState())
    sim.combat.update_companions(FIXED_DT)
    first = enemy.max_health - enemy.health
    pet = sim.combat.companions[0]
    pet.timer = 0
    health = enemy.health
    sim.combat.update_companions(FIXED_DT)
    assert first == pytest.approx((health - enemy.health) * 1.15)
    assert pet.attacks == 2


def test_multishot_coverage_and_existing_area_duration_modifiers(content):
    angles = []
    for bonuses in ({}, META.trees["hunter"]["technique"].at_rank(1)):
        sim, _ = sim_for(content, "hunter", "multi_shot", bonuses)
        sim.combat.cast(content.abilities["multi_shot"], SpellState())
        values = [p.velocity.as_polar()[1] for p in sim.projectiles]
        angles.append(max(values) - min(values))
    assert angles[1] == pytest.approx(angles[0] * 1.25)
    for cid, aid, tid, stat in (
        ("paladin", "consecration", "mastery", "radius"),
        ("warrior", "mortal_strike", "signature", "radius"),
        ("warrior", "whirlwind", "technique", "radius"),
        ("mage", "blizzard", "mastery", "duration"),
        ("priest", "holy_nova", "mastery", "radius"),
    ):
        sim, _ = sim_for(content, cid, aid)
        before = spell_stats(content.abilities[aid], SpellState(), sim.player)
        sim.player.meta = MetaBonuses(META.trees[cid][tid].at_rank(1))
        after = spell_stats(content.abilities[aid], SpellState(), sim.player)
        assert getattr(after, stat) > getattr(before, stat)


@pytest.mark.parametrize("resolution", ("1280x720", "1600x900", "1920x1080", "2560x1440"))
def test_hover_click_keyboard_controller_respec_and_scaled_input(tmp_path, resolution):
    save = SaveStore(tmp_path / "save.json")
    save.data["settings"]["resolution"] = resolution
    save.data["classes"]["paladin"]["xp"] = 60 * 50 * 49
    app = App(save)
    try:
        app.goto("talents")
        app.draw()
        node = node_rect(META.trees["paladin"]["might"])
        scale = app.viewport.width / 1280
        pos = (
            round(app.viewport.x + node.centerx * scale),
            round(app.viewport.y + node.centery * scale),
        )
        app.handle_event(
            pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0))
        )
        assert app.progression_ui.tree.hovered == "might"
        assert "+2%" in effect_summary(META.trees["paladin"]["might"], 1, app)
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
        assert app.screen == "confirm" and app.focus == 1
        app.menu_key(pygame.K_LEFT)
        app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
        assert save.data["classes"]["paladin"]["talents"]["might"] == 1
        app.draw()
        app.menu_key(pygame.K_DOWN)
        assert app.focus < 18
        app.handle_event(pygame.event.Event(pygame.JOYHATMOTION, hat=0, value=(0, 1)))
        assert list(META.trees["paladin"])[app.focus] == "might"
        before = copy.deepcopy(save.data)
        app.progression_ui.respec(app)
        assert app.screen == "talents" and save.data == before
        save.data["gold"] = save.respec_cost("paladin")
        xp = save.data["classes"]["paladin"]["xp"]
        app.progression_ui.respec(app)
        assert app.screen == "confirm" and "55 gold" in app.progression_ui.confirmation.body
        app.progression_ui.confirm(app)
        assert save.data["gold"] == 0 and not save.data["classes"]["paladin"]["talents"]
        assert SaveStore(save.path).data["classes"]["paladin"]["xp"] == xp
    finally:
        pygame.quit()
