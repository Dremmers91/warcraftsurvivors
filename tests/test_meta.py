"""Permanent content effects, purchase rules, migration, recovery and unlock contracts."""

from __future__ import annotations

import copy
import json
import os

import pytest
from pygame import Vector2

from warcraft_survivors.combat import hurt_player, spell_stats
from warcraft_survivors.entities import ManualState, SpellState
from warcraft_survivors.manuals import activate, update
from warcraft_survivors.meta import MetaBonuses, RunLoadout, class_level, load_progression
from warcraft_survivors.persistence import SaveStore, save_path
from warcraft_survivors.simulation import FIXED_DT, Simulation

META = load_progression()


def earned_profile(save, cid, level=50):
    save.data["classes"][cid]["xp"] = 60 * level * (level - 1)
    return save.data["classes"][cid]


def allocate_all(save, cid):
    for t in META.trees[cid].values():
        for _ in range(t.max_rank):
            assert save.buy_talent(cid, t.id)


@pytest.mark.parametrize("cid", list(META.trees))
def test_distinct_trees_valid_prerequisites_and_complete_respec(tmp_path, cid):
    save = SaveStore(tmp_path / "save.json")
    assert len(META.trees[cid]) == 18
    assert len({t.name for tree in META.trees.values() for t in tree.values()}) >= 100
    assert not save.buy_talent(cid, "capstone")
    earned_profile(save, cid)
    assert not save.buy_talent(cid, "capstone")
    allocate_all(save, cid)
    before_xp = save.data["classes"][cid]["xp"]
    points = save.talent_points(cid)
    spent = sum(save.data["classes"][cid]["talents"].values())
    cost = save.respec_cost(cid)
    save.data["gold"] = cost - 1
    before = copy.deepcopy(save.data)
    assert not save.respec(cid) and save.data == before
    save.data["gold"] = cost
    assert save.select_starting(cid, META.trees[cid]["preparation"].starting_options[0])
    assert save.respec(cid)
    assert save.data["gold"] == 0 and save.talent_points(cid) == points + spent
    assert save.data["classes"][cid]["xp"] == before_xp
    assert save.data["classes"][cid]["starting_ability"] == ""
    assert SaveStore(save.path).talent_points(cid) == points + spent


@pytest.mark.parametrize(
    "cid,tid", [(cid, tid) for cid, tree in META.trees.items() for tid in tree]
)
def test_every_talent_has_an_observable_gameplay_effect(content, cid, tid):
    t = META.trees[cid][tid]
    baseline = Simulation(content, cid)
    changed = Simulation(
        content,
        cid,
        permanent=RunLoadout(
            MetaBonuses(t.effects), t.starting_options[0] if t.starting_options else ""
        ),
    )
    p, q = baseline.player, changed.player
    if t.starting_options:
        assert len(p.spells) == 1 and len(q.spells) == 2
        return
    for key, value in t.effects.items():
        p.health, q.health = p.max_health, q.max_health
        p.hurt_timer = q.hurt_timer = 0
        if key == "health":
            assert q.max_health > p.max_health
        elif key == "armor":
            hurt_player(p, 20)
            hurt_player(q, 20)
            assert q.max_health - q.health < p.max_health - p.health
        elif key == "speed":
            assert q.base_speed > p.base_speed
        elif key == "starting_shield":
            assert q.shield == value and p.shield == 0
        elif key == "regen":
            p.health -= 20
            q.health -= 20
            old = q.health
            update(q, 1)
            assert q.health > old
        elif key in {"kill_heal", "kill_shield"}:
            q.health -= 20
            old = q.health
            enemy = changed.spawn("kobold", q.pos + Vector2(30, 0))
            enemy.health = 0
            changed.collect_dead()
            assert (q.health > old) if key == "kill_heal" else q.shield > 0
        elif key == "manual_haste":
            p.manual = ManualState(content.classes[cid].manuals[1])
            q.manual = ManualState(p.manual.id)
            assert activate(baseline) and activate(changed)
            assert q.manual.timer < p.manual.timer
        elif key == "healing":
            p.health -= 30
            q.health -= 30
            heal = next(
                a for a in content.abilities.values() if a.mechanics.heal and a.kind != "dot"
            )
            p.health = p.max_health * 0.25
            q.health = q.max_health * 0.25
            ep = baseline.spawn("kobold", p.pos + Vector2(30, 0))
            eq = changed.spawn("kobold", q.pos + Vector2(30, 0))
            baseline.combat.hit(ep, 10, heal, SpellState())
            changed.combat.hit(eq, 10, heal, SpellState())
            assert q.health > p.health
        elif key in {"boss_damage", "execute"}:
            ep = baseline.spawn("kobold", p.pos + Vector2(30, 0))
            eq = changed.spawn("kobold", q.pos + Vector2(30, 0))
            ep.max_health = eq.max_health = 1000
            ep.health = eq.health = 200
            if key == "boss_damage":
                ep.boss_id = eq.boss_id = "hogger"
            a = content.abilities[content.classes[cid].abilities[0]]
            baseline.combat.hit(ep, 10, a, SpellState())
            changed.combat.hit(eq, 10, a, SpellState())
            assert eq.health < ep.health
        else:
            if key == "low_health_damage":
                p.health = q.health = 10
            pairs = [
                (
                    spell_stats(content.abilities[a], SpellState(), p),
                    spell_stats(content.abilities[a], SpellState(), q),
                )
                for a in content.classes[cid].abilities
            ]
            assert any(a != b for a, b in pairs), f"{cid} {tid}: unused effect {key}"


@pytest.mark.parametrize("sid", list(META.shared))
def test_shared_costs_caps_and_insufficient_gold_are_transactional(tmp_path, sid):
    save = SaveStore(tmp_path / "save.json")
    save.data["shared"] = {"health": 5, "might": 3} if sid == "choices" else {}
    upgrade = META.shared[sid]
    if upgrade.achievement:
        save.data["achievements"].append(upgrade.achievement)
    for cost in upgrade.costs:
        save.data["gold"] = cost - 1
        before = copy.deepcopy(save.data)
        assert not save.buy_shared(sid) and save.data == before
        save.data["gold"] = cost
        assert save.buy_shared(sid) and save.data["gold"] == 0
    before = copy.deepcopy(save.data)
    assert not save.buy_shared(sid) and save.data == before
    assert SaveStore(save.path).data["shared"][sid] == upgrade.max_rank


def test_fourth_card_and_rerolls_are_permanent_and_never_unlock_extra_chest_choices(
    content, tmp_path
):
    save = SaveStore(tmp_path / "save.json")
    save.data["gold"] = 100000
    assert not save.buy_shared("choices")
    for _ in range(5):
        assert save.buy_shared("health")
    for _ in range(3):
        assert save.buy_shared("might")
    assert not save.buy_shared("choices")
    save.data["achievements"].append("more_choices")
    assert save.buy_shared("choices") and save.buy_shared("rerolls")
    sim = Simulation(content, permanent=SaveStore(save.path).loadout("paladin"))
    sim.player.xp = sim.player.xp_required
    sim.level_check()
    assert len(sim.choices) == 4 and sim.rerolls == 1
    old = list(sim.choices)
    assert sim.reroll() and not sim.reroll() and not set(old) & set(sim.choices)
    sim.choose(3)
    sim.drop(sim.player.pos, "chest", 1)
    sim.collect_pickups(FIXED_DT)
    assert len(sim.choices) == 3 and not sim.reroll()
    # Four actual rewards remain available after every equipment slot is capped.
    sim.choices.clear()
    sim.chest_choice = False
    sim.player.spells = {
        aid + "_evolved": SpellState(8) for aid in content.classes["paladin"].abilities[:8]
    }
    sim.player.passives = {pid: 5 for pid in list(content.passives)[:8]}
    sim.player.manual = ManualState("divine_shield", 3)
    sim.player.xp = sim.player.xp_required
    sim.level_check()
    assert len(sim.choices) == 4


@pytest.mark.parametrize(
    "cid,companion", [("hunter", "beast_companion"), ("warlock", "summon_felguard")]
)
def test_companions_require_advanced_talent_and_explicit_starting_selection(
    tmp_path, content, cid, companion
):
    save = SaveStore(tmp_path / "save.json")
    assert len(Simulation(content, cid, permanent=save.loadout(cid)).player.spells) == 1
    assert not save.select_starting(cid, companion)
    earned_profile(save, cid)
    assert len(Simulation(content, cid, permanent=save.loadout(cid)).player.spells) == 1
    allocate_all(save, cid)
    assert len(Simulation(content, cid, permanent=save.loadout(cid)).player.spells) == 1
    assert save.select_starting(cid, companion)
    sim = Simulation(content, cid, permanent=SaveStore(save.path).loadout(cid))
    assert companion in sim.player.spells and len(sim.player.spells) == 2
    sim.step(FIXED_DT)
    assert sim.combat.companions
    if cid == "warlock":
        assert content.abilities[companion].name == "Summon Imp"
        assert all(p.sprite == "imp" for p in sim.combat.companions)
    assert not save.select_starting(cid, "judgment")
    save.data["gold"] = save.respec_cost(cid)
    assert save.respec(cid)
    assert len(Simulation(content, cid, permanent=save.loadout(cid)).player.spells) == 1


def test_shared_xp_pickup_recovery_damage_movement_and_gold_are_real(tmp_path, content):
    save = SaveStore(tmp_path / "save.json")
    save.data["gold"] = 10000
    for sid in ("might", "armor", "health", "movement", "magnet", "xp", "greed", "regen"):
        assert save.buy_shared(sid)
    sim = Simulation(content, permanent=save.loadout("paladin"))
    baseline = Simulation(content)
    sim.step(FIXED_DT, Vector2(1, 0))
    baseline.step(FIXED_DT, Vector2(1, 0))
    assert sim.player.pos.x > baseline.player.pos.x
    a = content.abilities["judgment"]
    assert (
        spell_stats(a, SpellState(), sim.player).damage
        > spell_stats(a, SpellState(), baseline.player).damage
    )
    sim.drop(sim.player.pos, "xp", 10)
    sim.collect_pickups(FIXED_DT)
    assert sim.player.xp == pytest.approx(10.4)
    sim.drop(sim.player.pos + Vector2(100, 0), "xp", 1)
    gem = list(sim.pickups.values())[0]
    old = gem.pos.copy()
    sim.collect_pickups(FIXED_DT)
    assert gem.pos != old
    # Achievement gold is excluded from the shared multiplier and pays only once.
    result = save.reward_run("paladin", 0, 0, 0, False, 100, 0, 0, sim.player.meta.get("gold"))
    assert result["gold"] == 104


def test_v1_migration_keeps_xp_gold_settings_and_refunds_invalid_talents(tmp_path):
    raw = dict(
        version=1,
        gold=999,
        classes={
            "hunter": {
                "xp": 30000,
                "talents": {"might": 5, "health": 5, "signature": 3, "removed": 9},
            }
        },
        shared={"choices": 1, "might": 5},
        achievements=["elite", "victory"],
        settings={"sound": False, "debug": True},
        stats={"kills": 350, "wins": 1},
    )
    path = tmp_path / "save.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    save = SaveStore(path)
    c = save.data["classes"]["hunter"]
    assert save.data["version"] == 2 and c["xp"] == 30000 and save.data["gold"] == 999
    assert c["level"] == class_level(30000) and c["talents"] == {"might": 3, "health": 3}
    assert c["talent_points"] == c["level"] - 1 - 6
    assert save.data["shared"]["choices"] == 1 and not save.data["settings"]["debug"]
    assert save.data["stats"]["bosses"] == 1 and save.data["stats"]["elites"] == 1
    assert (
        save.write()
        and json.loads(path.with_suffix(".bak").read_text(encoding="utf-8"))["classes"]["hunter"][
            "xp"
        ]
        == 30000
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("gold", True),
        ("classes", []),
        ("shared", None),
        ("stats", {"class_wins": []}),
        ("settings", {"effects_quality": []}),
        ("achievements", {}),
        ("unlocked_zones", {}),
        ("revision", -9),
    ],
)
def test_invalid_nested_v2_data_is_sanitized(field, value):
    raw = SaveStore.defaults()
    raw[field] = value
    clean = SaveStore.validate(raw)
    assert clean["version"] == 2 and clean["gold"] >= 0
    assert clean["unlocked_classes"] == list(META.trees)
    assert isinstance(clean["stats"]["class_wins"], dict)


def test_points_levels_prerequisites_and_forged_unlocks_are_validated():
    raw = SaveStore.defaults()
    raw["classes"]["paladin"] = dict(
        xp=120,
        level=99,
        talent_points=999,
        talents={"might": 3, "capstone": 1},
        starting_ability="beast_companion",
    )
    raw["unlocked_classes"] = ["rogue", "warlock"]
    clean = SaveStore.validate(raw)
    c = clean["classes"]["paladin"]
    assert (
        c["level"] == 2
        and c["talent_points"] == 0
        and c["talents"] == {"might": 1}
        and not c["starting_ability"]
    )
    assert "rogue" not in clean["unlocked_classes"] and "hunter" in clean["unlocked_classes"]


def test_interrupted_atomic_writes_and_purchase_failure_never_spend(tmp_path, monkeypatch):
    path = tmp_path / "save.json"
    save = SaveStore(path)
    save.data["gold"] = 1000
    earned_profile(save, "paladin")
    assert save.write()
    original = path.read_bytes()
    data = copy.deepcopy(save.data)

    def fail(*args):
        raise OSError("interrupted replace")

    monkeypatch.setattr(os, "replace", fail)
    assert not save.buy_shared("health") and save.data == data and path.read_bytes() == original
    assert not save.buy_talent("paladin", "might") and save.data == data
    assert SaveStore(path).data["gold"] == 1000


@pytest.mark.parametrize("suffix", [".bak", ".tmp"])
def test_missing_primary_recovers_valid_backup_or_interrupted_temp(tmp_path, suffix):
    path = tmp_path / "save.json"
    raw = SaveStore.defaults()
    raw["gold"] = 777
    path.with_suffix(suffix).write_text(json.dumps(raw), encoding="utf-8")
    save = SaveStore(path)
    assert save.data["gold"] == 777 and "Recovered" in save.notice and save.write()


def test_main_commit_beats_newer_uncommitted_temporary_profile(tmp_path):
    path = tmp_path / "save.json"
    save = SaveStore(path)
    save.data["gold"] = 500
    save.write()
    unfinished = copy.deepcopy(save.data)
    unfinished["gold"] = 20
    unfinished["revision"] += 1
    path.with_suffix(".tmp").write_text(json.dumps(unfinished), encoding="utf-8")
    assert SaveStore(path).data["gold"] == 500


def test_future_versions_are_preserved_and_never_overwritten(tmp_path):
    path = tmp_path / "save.json"
    original = '{"version":999,"gold":123456}'
    path.write_text(original, encoding="utf-8")
    save = SaveStore(path)
    assert save.read_only and not save.write() and not save.buy_shared("might")
    assert path.read_text(encoding="utf-8") == original


def test_achievement_counters_unlocks_and_once_only_rewards_persist(tmp_path):
    save = SaveStore(tmp_path / "save.json")
    for cid in ("paladin", "mage", "hunter"):
        result = save.reward_run(cid, 100, 20, 1800, True, 0, 10, 1000)
    assert "unlock_rogue" not in result["achievements"]
    assert not {"rogue", "druid", "shaman"} & set(save.data["unlocked_classes"])
    assert (
        save.data["stats"]["kills"] == 300
        and save.data["stats"]["elites"] == 60
        and save.data["stats"]["evolved"] == 30
    )
    assert save.data["stats"]["bosses"] == 3
    loaded = SaveStore(save.path)
    assert loaded.data["achievement_progress"]["unlock_rogue"] == 0 and not loaded.class_available(
        "rogue"
    )
    for cid in ("rogue", "druid", "shaman"):
        assert not loaded.buy_shared(cid) and not loaded.buy_talent(cid, "might")
    repeated = loaded.reward_run("hunter", 0, 0, 0, False, 0, 0, 0)
    assert repeated["gold"] == 0 and not repeated["achievements"] and not repeated["unlocks"]
    failure = loaded.reward_run("priest", 10, 1, 500, False, 7, 0, 50)
    assert failure["class_xp"] == 50 + 83 and loaded.data["classes"]["priest"]["xp"] == 133
    assert SaveStore(save.path).data["classes"]["priest"]["xp"] == 133


def test_windows_profile_location_uses_local_app_data(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert save_path() == tmp_path / "WarcraftSurvivors" / "save.json"


def test_transient_windows_replace_lock_retries_then_commits(tmp_path, monkeypatch):
    save = SaveStore(tmp_path / "save.json")
    save.data["gold"] = 100
    save.write()
    original = os.replace
    calls = []

    def briefly_locked(source, destination):
        calls.append(destination)
        if len(calls) == 1:
            raise PermissionError("scanner lock")
        original(source, destination)

    monkeypatch.setattr(os, "replace", briefly_locked)
    assert save.buy_shared("health")
    assert SaveStore(save.path).data["gold"] == 35 and len(calls) == 3


def test_real_progression_loop_uses_separate_processes(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/verify_progression_loop.py"),
            "--output",
            str(tmp_path),
        ],
        cwd=root,
        check=True,
        timeout=90,
        capture_output=True,
        text=True,
    )
    earned = json.loads((tmp_path / "earn.json").read_text(encoding="utf-8"))
    purchase = json.loads((tmp_path / "purchase.json").read_text(encoding="utf-8"))
    reopened = json.loads((tmp_path / "reopen.json").read_text(encoding="utf-8"))
    assert earned["runs"][0]["time"] > 0 and earned["runs"][0]["kills"] > 0
    assert purchase["gold_after"] == earned["gold"] - 65
    assert reopened["upgrade_active"] and reopened["starting_abilities"] == ["judgment"]
    assert reopened["class_xp"] == earned["class_xp"] and reopened["max_health"] == 139.05


def test_future_final_boss_victory_does_not_claim_hogger_achievement(tmp_path):
    save = SaveStore(tmp_path / "save.json")
    result = save.reward_run("paladin", 0, 0, 1800, True, 0, 0, 0, boss_id="future_boss")
    assert "victory" not in result["achievements"]
    assert (
        save.data["stats"]["bosses"] == 1 and save.data["stats"]["boss_kills"]["future_boss"] == 1
    )
    assert save.data["achievement_progress"]["victory"] == 0
    assert result["class_xp"] == 5300 and result["gold"] >= 1590
    result = save.reward_run("paladin", 0, 0, 1800, True, 0, 0, 0, boss_id="hogger")
    assert "victory" in result["achievements"]


def test_respec_and_starting_selection_roll_back_on_write_failure(tmp_path, monkeypatch):
    save = SaveStore(tmp_path / "save.json")
    earned_profile(save, "hunter")
    allocate_all(save, "hunter")
    save.data["gold"] = 1000
    assert save.write()
    before = copy.deepcopy(save.data)
    original = save.path.read_bytes()
    monkeypatch.setattr(save, "write", lambda: False)
    assert not save.respec("hunter") and save.data == before
    assert not save.select_starting("hunter", "beast_companion") and save.data == before
    assert save.path.read_bytes() == original
