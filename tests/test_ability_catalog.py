"""Functional coverage of every shipped spell/evolution/manual, plus cross-system rules."""

from __future__ import annotations

import random

import pygame
import pytest
from pygame import Vector2

from warcraft_survivors.combat import hurt_player, spell_stats
from warcraft_survivors.content import SCHOOLS, load_content
from warcraft_survivors.entities import ManualState, SpellState
from warcraft_survivors.simulation import FIXED_DT, Simulation
from warcraft_survivors.upgrades import apply, eligible, evolution_eligible, roll

CATALOG = load_content()
BASE_IDS = tuple(CATALOG.abilities)
MANUAL_IDS = tuple(CATALOG.manuals)


def arena(content, aid, rank=1):
    cid = next(
        c.id
        for c in content.classes.values()
        if (content.ability(aid).base_id or aid) in c.abilities
    )
    sim = Simulation(content, cid, seed=22)
    sim.player.spells = {aid: SpellState(rank)}
    sim.player.invulnerable = True
    for radius in (35, 80, 150, 280, 500):
        for angle in range(0, 360, 45):
            e = sim.spawn("bandit", sim.player.pos + Vector2(radius, 0).rotate(angle))
            e.speed = 0
            e.health = e.max_health = 10000
    sim.grid.rebuild(sim.enemies)
    return sim


@pytest.mark.parametrize("aid", BASE_IDS)
@pytest.mark.parametrize("form", ("rank1", "rank8", "evolution"))
def test_every_automatic_form_functions_without_movement(content, aid, form):
    key = aid + "_evolved" if form == "evolution" else aid
    sim = arena(content, key, 1 if form == "rank1" else 8)
    start = sim.player.pos.copy()
    ability = content.ability(key)
    sim.combat.cast(ability, sim.player.spells[key])
    assert sim.projectiles or sim.visuals or sim.combat.fields or sim.combat.companions
    for _ in range(240):
        sim.combat.update_projectiles(FIXED_DT)
        sim.combat.update_fields(FIXED_DT)
        sim.combat.update_companions(FIXED_DT)
        sim.combat.update_statuses(FIXED_DT)
    damaged = [e for e in sim.enemies if e.health < e.max_health]
    assert damaged, f"{key} produced no real damage"
    assert all(e.last_damage_school == ability.school and e.owner == "player" for e in damaged)
    assert sim.player.pos == start


@pytest.mark.parametrize("aid", BASE_IDS)
def test_every_rank_and_evolution_contract(content, aid):
    a = content.abilities[aid]
    assert len(a.ranks) == 8 and a.evolution
    assert a.evolution.passive in content.passives
    assert a.school in SCHOOLS and a.description
    for old, new in zip(a.ranks, a.ranks[1:], strict=False):
        assert new.damage > old.damage and new.cooldown < old.cooldown
        assert new.radius >= old.radius and new.description
    sim = arena(content, aid, 7)
    p = sim.player
    p.passives[a.evolution.passive] = 1
    assert aid not in evolution_eligible(content, p)
    p.spells[aid].rank = 8
    p.passives.clear()
    assert aid not in evolution_eligible(content, p)
    p.passives[a.evolution.passive] = 1
    assert aid in evolution_eligible(content, p)
    assert not any(c.kind == "evolution" for c in eligible(content, sim.class_id, p))
    card = next(c for c in eligible(content, sim.class_id, p, chest=True) if c.id == aid)
    with pytest.raises(ValueError):
        apply(content, sim.class_id, p, card)
    before = spell_stats(a, p.spells[aid], p)
    apply(content, sim.class_id, p, card, chest=True)
    assert aid not in p.spells and len(p.spells) == 1 and a.evolution.id in p.spells
    evolved = content.ability(a.evolution.id)
    assert evolved.base_id == aid and evolved.evolved
    assert spell_stats(evolved, p.spells[evolved.id], p).damage > before.damage
    assert not any(c.id == aid for c in eligible(content, sim.class_id, p))
    assert not evolution_eligible(content, p)


@pytest.mark.parametrize("cid", tuple(CATALOG.classes))
def test_class_start_pool_and_source_simulation_smoke(content, cid):
    sim = Simulation(content, cid, seed=1)
    cls = content.classes[cid]
    assert len(cls.abilities) == 10 and len(cls.manuals) == 3
    assert list(sim.player.spells) == [cls.abilities[0]]
    assert sim.player.manual is None
    pool = eligible(content, cid, sim.player)
    assert {c.id for c in pool if c.kind == "spell"} == set(cls.abilities)
    assert {c.id for c in pool if c.kind == "manual"} == set(cls.manuals)
    sim.player.invulnerable = True
    for tick in range(360):
        while sim.choices:
            sim.choose(0)
        sim.step(FIXED_DT, Vector2(1, 0) if tick < 120 else Vector2())
    assert sim.time == pytest.approx(6) and sim.player.health > 0


@pytest.mark.parametrize("mid", MANUAL_IDS)
@pytest.mark.parametrize("rank", (1, 2, 3))
def test_all_manuals_activate_have_effect_and_cooldown(content, mid, rank):
    cid = next(c.id for c in content.classes.values() if mid in c.manuals)
    sim = Simulation(content, cid)
    p = sim.player
    p.manual = ManualState(mid, rank)
    p.health = p.max_health * 0.25
    enemy = sim.spawn("bandit", p.pos + Vector2(60, 0))
    sim.grid.rebuild(sim.enemies)
    position = p.pos.copy()
    assert sim.activate_manual(Vector2(1, 0))
    m = content.manuals[mid]
    if m.kind == "circle":
        assert p.manual.circle == position and p.manual.timer == 0
        p.pos += Vector2(3500, 1200)
        sim.camera.pos = sim.world.camera(p.pos)
        assert sim.activate_manual()
        assert p.pos == position and p.manual.circle is None
        assert sim.camera.pos == sim.world.camera(position)
    elif m.kind in {"blink", "leap"}:
        assert p.pos != position and p.immune > 0
    elif m.kind == "immune":
        assert p.immune > 0 and not hurt_player(p, 1000)
        assert bool(p.rooted) == m.root
    elif m.kind == "guard":
        assert p.guard > 0
        before = p.health
        assert hurt_player(p, 40)
        assert before - p.health <= 40 * 0.5
    elif m.kind == "heal":
        assert p.health > p.max_health * 0.25
    elif m.kind == "shield":
        assert p.shield > 0
    elif m.kind == "buff":
        assert p.buff_time > 0 and p.buff_power > 0
    elif m.kind == "rally":
        assert p.rally_bonus > 0 and p.max_health > content.classes[cid].health
    elif m.kind == "fear":
        assert enemy.fear > 0 and enemy.health < enemy.max_health
    assert p.manual.timer > 0 and not sim.activate_manual()
    timer = p.manual.timer
    sim.player.xp = p.xp_required
    sim.level_check()
    sim.step(FIXED_DT)
    assert p.manual.timer == timer
    for old, new in zip(m.ranks, m.ranks[1:], strict=False):
        assert new.cooldown < old.cooldown and new.duration > old.duration and new.power > old.power


@pytest.mark.parametrize("mid", MANUAL_IDS)
def test_manual_discovery_excludes_alternatives_and_ranks_cap(content, mid):
    cid = next(c.id for c in content.classes.values() if mid in c.manuals)
    sim = Simulation(content, cid)
    for rank in (1, 2, 3):
        choice = next(c for c in eligible(content, cid, sim.player) if c.id == mid)
        assert choice.rank == rank
        apply(content, cid, sim.player, choice)
        assert not any(
            c.kind == "manual" and c.id != mid for c in eligible(content, cid, sim.player)
        )
    assert not any(c.kind == "manual" for c in eligible(content, cid, sim.player))


def test_full_slots_branch_exclusivity_exhaustion_and_stale_cards(content):
    sim = Simulation(content)
    p = sim.player
    p.spells = {
        aid: SpellState(8, modifiers={"force"}) for aid in content.classes["paladin"].abilities[:8]
    }
    p.passives = {pid: 5 for pid in list(content.passives)[:8]}
    p.manual = ManualState("divine_shield", 3)
    assert {c.kind for c in eligible(content, "paladin", p)} == {"reward"}
    assert len({(c.kind, c.id) for c in roll(content, "paladin", p, random.Random(2))}) == 3
    p.spells["judgment"].modifiers.clear()
    branches = [c for c in eligible(content, "paladin", p) if c.kind == "modifier"]
    assert len(branches) == 2
    apply(content, "paladin", p, branches[0])
    with pytest.raises(ValueError):
        apply(content, "paladin", p, branches[1])
    assert not any(c.kind == "modifier" for c in eligible(content, "paladin", p))


def test_radial_progression_and_always_following_consecration_blizzard_evolution(content):
    for aid in ("judgment", "frostbolt", "shadow_bolt"):
        sim = arena(content, aid, 6)
        sim.combat.cast(content.abilities[aid], sim.player.spells[aid])
        angles = [s.velocity.as_polar()[1] % 360 for s in sim.projectiles]
        assert len(angles) >= 3 and max(angles) - min(angles) >= 180
    for aid in ("consecration", "blizzard_evolved"):
        sim = arena(content, aid, 8)
        sim.combat.cast(content.ability(aid), sim.player.spells[aid])
        sim.player.pos += Vector2(50, 0)
        sim.combat.update_fields(FIXED_DT)
        assert sim.combat.fields[0].pos == sim.player.pos
        if aid == "blizzard_evolved":
            assert sim.combat.fields[0].persistent
    sim = arena(content, "blizzard")
    sim.combat.cast(content.abilities["blizzard"], SpellState())
    pos = sim.combat.fields[0].pos.copy()
    sim.combat.update_fields(FIXED_DT)
    assert sim.combat.fields[0].pos != pos and not sim.combat.fields[0].follow


def test_execute_attacks_healthy_targets_and_bonuses_weakened(content):
    sim = arena(content, "execute")
    targets = sim.enemies[:2]
    a = content.abilities["execute"]
    state = sim.player.spells["execute"]
    targets[0].health = 10000
    targets[1].health = 2000
    sim.combat.hit(targets[0], 10, a, state)
    sim.combat.hit(targets[1], 10, a, state)
    assert targets[0].health == 9990 and targets[1].health == 1980


def test_dot_prioritizes_fresh_targets_and_spreads_on_death(content):
    sim = Simulation(content, "warlock")
    a = content.abilities["corruption"]
    sim.player.spells = {"corruption": SpellState(5)}
    enemies = [sim.spawn("bandit", sim.player.pos + Vector2(x, 0)) for x in (40, 80, 120, 160)]
    sim.grid.rebuild(enemies)
    sim.combat.cast(a, sim.player.spells["corruption"])
    marked = {e.id for e in enemies if e.statuses}
    sim.combat.cast(a, sim.player.spells["corruption"])
    assert all(e.statuses for e in enemies) and len(marked) == 2
    fresh = sim.spawn("bandit", sim.player.pos + Vector2(45, 5))
    sim.grid.rebuild(sim.enemies)
    enemies[0].health = 0
    sim.combat.update_statuses(FIXED_DT)
    assert fresh.statuses


@pytest.mark.parametrize(
    "aid", ("beast_companion", "summon_felguard", "stampede", "hand_of_gul_dan")
)
def test_companion_ownership_kills_scaling_and_no_targetable_health(content, aid):
    sim = arena(content, aid, 8)
    a = content.abilities[aid]
    sim.player.passives = {"might": 2, "projectiles": 2, "haste": 2}
    sim.combat.cast(a, sim.player.spells[aid])
    assert len(sim.combat.companions) == a.ranks[7].count + 2
    enemy = sim.enemies[0]
    enemy.health = 1
    for _ in range(120):
        sim.combat.update_companions(FIXED_DT)
    assert enemy.health == 0 and enemy.owner == "player"
    sim.collect_dead()
    assert sim.kills >= 1 and any(p.kind == "xp" for p in sim.pickups.values())
    for pet in sim.combat.companions:
        assert pet.owner is sim.player and not hasattr(pet, "health") and pet not in sim.enemies
    if a.kind == "companion":
        sim.player.pos += Vector2(2000, 0)
        sim.combat.update_companions(FIXED_DT)
        assert all(
            p.pos.distance_to(sim.player.pos) <= p.leash + 1e-6 for p in sim.combat.companions
        )


def test_elite_chest_pauses_evolves_replaces_and_cleans_original_effect(content):
    sim = Simulation(content)
    sim.player.spells = {"consecration": SpellState(8)}
    sim.player.passives = {"duration": 1}
    sim.combat.cast(content.abilities["consecration"], sim.player.spells["consecration"])
    elite = sim.spawn_elite()
    elite.pos.update(sim.player.pos)
    elite.health = 0
    sim.collect_dead()
    sim.collect_pickups(FIXED_DT)
    assert sim.elites == 1 and sim.chest_choice and len(sim.choices) == 3
    time = sim.time
    sim.step(FIXED_DT)
    assert sim.time == time
    index = next(i for i, c in enumerate(sim.choices) if c.kind == "evolution")
    sim.choose(index)
    assert "consecration_evolved" in sim.player.spells and "consecration" not in sim.player.spells
    assert not sim.combat.fields and sim.evolved == 1
    # Clear queued XP decisions, which are independently required after the chest.
    while sim.choices:
        sim.choose(0)
    sim.step(FIXED_DT)
    assert sim.combat.fields[0].persistent


@pytest.mark.parametrize("pid", tuple(CATALOG.passives))
def test_all_passives_have_real_applicable_effects(content, pid):
    sim = Simulation(content)
    p = sim.player
    a = content.abilities["judgment"]
    state = p.spells["judgment"]
    before = spell_stats(a, state, p)
    card = next(c for c in eligible(content, "paladin", p) if c.id == pid)
    health = p.health
    maxhealth = p.max_health
    position = p.pos.copy()
    apply(content, "paladin", p, card)
    after = spell_stats(a, state, p)
    field = {
        "projectiles": "count",
        "area": "radius",
        "might": "damage",
        "haste": "cooldown",
        "duration": "duration",
        "velocity": "speed",
        "piercing": "pierce",
    }.get(pid)
    if field:
        assert getattr(before, field) != getattr(after, field)
    elif pid == "movement":
        p.spells.clear()
        sim.step(FIXED_DT, Vector2(1, 0))
        assert p.pos.distance_to(position) > p.base_speed * FIXED_DT
    elif pid == "pickup":
        sim.drop(p.pos + Vector2(115, 0), "xp", 1)
        pickup = next(iter(sim.pickups.values()))
        old = pickup.pos.copy()
        sim.collect_pickups(FIXED_DT)
        assert pickup.pos != old
    elif pid == "health":
        assert p.max_health > maxhealth and p.health > health
    elif pid == "regen":
        p.health -= 10
        old = p.health
        p.spells.clear()
        sim.step(FIXED_DT)
        assert p.health > old
    elif pid == "armor":
        hurt_player(p, 100)
        assert health - p.health < 90
    assert content.passives[pid].applicability


def test_device_manual_activation_and_class_menu(app):
    # Fixture is local below to avoid coupling to test_app module fixtures.
    app.menu_key(pygame.K_RETURN)
    assert app.screen == "classes"
    for _ in range(3):
        app.menu_key(pygame.K_RIGHT)
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
    assert app.sim.class_id == "hunter"
    app.sim.player.manual = ManualState("disengage")
    old = app.sim.player.pos.copy()
    app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
    assert app.sim.player.pos != old and app.sim.player.manual.timer > 0
    app.sim.player.manual.timer = 0
    app.menu_key(pygame.K_SPACE)
    assert app.sim.player.manual.timer > 0


@pytest.fixture
def app(tmp_path):
    from warcraft_survivors.app import App
    from warcraft_survivors.persistence import SaveStore

    game = App(SaveStore(tmp_path / "save.json"))
    yield game
    pygame.quit()


@pytest.mark.parametrize("aid", BASE_IDS)
def test_every_automatic_cast_has_a_visible_fallback_without_targets(content, aid):
    cid = next(c.id for c in content.classes.values() if aid in c.abilities)
    sim = Simulation(content, cid)
    sim.combat.cast(content.abilities[aid], SpellState())
    assert sim.projectiles or sim.visuals or sim.combat.fields or sim.combat.companions


def test_manual_school_and_pet_buffs_modify_only_applicable_damage(content):
    sim = Simulation(content, "mage")
    p = sim.player
    p.manual = ManualState("combustion")
    fire = content.abilities["fireball"]
    frost = content.abilities["frostbolt"]
    old_fire, old_frost = spell_stats(fire, SpellState(), p), spell_stats(frost, SpellState(), p)
    assert sim.activate_manual()
    assert spell_stats(fire, SpellState(), p).damage > old_fire.damage
    assert spell_stats(frost, SpellState(), p).damage == old_frost.damage
    sim = Simulation(content, "hunter")
    p = sim.player
    p.manual = ManualState("bestial_wrath")
    arrow = content.abilities["arcane_shot"]
    old = spell_stats(arrow, SpellState(), p).damage
    assert sim.activate_manual()
    assert spell_stats(arrow, SpellState(), p).damage == old
    assert p.pet_buff and p.buff_time > 0


@pytest.mark.parametrize("dt", (1 / 30, 1 / 60, 1 / 120))
def test_dot_ticks_and_manual_cooldowns_are_frame_independent(content, dt):
    sim = Simulation(content, "warlock")
    a = content.abilities["corruption"]
    sim.player.spells = {"corruption": SpellState()}
    enemy = sim.spawn("bandit", sim.player.pos + Vector2(50, 0))
    enemy.health = enemy.max_health = 10000
    sim.grid.rebuild(sim.enemies)
    sim.combat.mark(enemy, a, 10, 10)
    sim.player.manual = ManualState("dark_soul", timer=10)
    from warcraft_survivors.manuals import update

    for _ in range(round(4.9 / dt)):
        sim.combat.update_statuses(dt)
        update(sim.player, dt)
    assert enemy.health == 9950
    assert sim.player.manual.timer == pytest.approx(5.1)


def test_bestial_wrath_increases_actual_pet_hits_and_rally_expires(content):
    values = []
    for empowered in (False, True):
        sim = Simulation(content, "hunter")
        p = sim.player
        p.spells = {"beast_companion": SpellState()}
        enemy = sim.spawn("bandit", p.pos + Vector2(50, 0))
        sim.grid.rebuild(sim.enemies)
        sim.combat.cast(content.abilities["beast_companion"], p.spells["beast_companion"])
        if empowered:
            p.manual = ManualState("bestial_wrath")
            assert sim.activate_manual()
        sim.combat.update_companions(FIXED_DT)
        values.append(enemy.max_health - enemy.health)
    assert values[1] == pytest.approx(values[0] * 2)
    sim = Simulation(content, "warrior")
    p = sim.player
    original = p.max_health
    p.manual = ManualState("rallying_cry")
    assert sim.activate_manual() and p.max_health > original
    from warcraft_survivors.manuals import update

    update(p, 20)
    assert p.max_health == original and p.health <= original and p.rally_bonus == 0


def test_area_expands_dot_spread_and_velocity_excludes_pet_movement(content):
    spread = []
    for area in (0, 1):
        sim = Simulation(content, "warlock")
        sim.player.spells = {"corruption": SpellState(5)}
        sim.player.passives = {"area": area} if area else {}
        a = content.abilities["corruption"]
        host = sim.spawn("bandit", sim.player.pos + Vector2(40, 0))
        fresh = sim.spawn("bandit", host.pos + Vector2(200, 0))
        sim.grid.rebuild(sim.enemies)
        sim.combat.mark(host, a, 5, 5, spread=True)
        host.health = 0
        sim.combat.update_statuses(FIXED_DT)
        spread.append(bool(fresh.statuses))
    assert spread == [False, True]
    p = Simulation(content, "hunter").player
    pet = content.abilities["beast_companion"]
    old = spell_stats(pet, SpellState(), p).speed
    p.passives = {"velocity": 5}
    assert spell_stats(pet, SpellState(), p).speed == old
