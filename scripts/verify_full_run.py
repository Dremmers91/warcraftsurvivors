"""Accelerated real fixed-step run with legal cards/movement/manual inputs, no cheats by default."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pygame import Vector2  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.persistence import SaveStore  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT, Simulation  # noqa: E402


def choose(sim):
    priorities = {
        "judgment": 110,
        "projectiles": 90,
        "might": 80,
        "area": 75,
        "consecration": 70,
        "regen": 65,
        "health": 63,
        "armor": 62,
        "haste": 60,
        "pickup": 55,
        "movement": 52,
        "divine_shield": 95,
        "eye_of_tyr": 68,
        "holy_shock": 58,
        "divine_storm": 57,
        "blessed_hammer": 56,
        "avenger_s_shield": 54,
        "duration": 48,
        "piercing": 40,
        "velocity": 38,
    }

    def score(card):
        if card.kind == "evolution":
            return 1000
        if card.kind == "reward":
            return (
                250
                if card.id == "heal" and sim.player.health < sim.player.max_health * 0.65
                else 150
                if card.id == "power"
                else 0
            )
        value = priorities.get(card.id, 20)
        if card.id == sim.content.classes[sim.class_id].abilities[0]:
            value = 110
        if (
            card.id in {"health", "armor", "regen"}
            and sim.player.health < sim.player.max_health * 0.6
        ):
            value += 45
        if card.kind == "modifier":
            return 30 if card.id.endswith(":reach") else 25
        if card.kind == "spell" and card.rank == 1 and len(sim.player.spells) >= 5:
            value -= 15
        return value

    index = max(range(len(sim.choices)), key=lambda i: score(sim.choices[i]))
    choice = sim.choices[index]
    sim.choose(index)
    return choice


def movement(sim, tick):
    p = sim.player
    if sim.boss and sim.boss.health > 0:
        offset = p.pos - sim.boss.pos
        if offset.length_squared() < 1:
            offset = Vector2(1, 0)
        radial = offset.normalize()
        desired = radial.rotate(90) + radial * ((200 - offset.length()) / 80)
    else:
        goal = Vector2(4096, 4096) + Vector2(260, 0).rotate(tick / 60 * 24)
        candidates = [
            gem for gem in sim.pickup_grid.nearby(p.pos, 280) if gem.kind in {"xp", "chest"}
        ]
        if candidates:
            nearest = min(
                candidates,
                key=lambda g: (0 if g.kind == "chest" else 1, g.pos.distance_squared_to(p.pos)),
            )
            if nearest.pos.distance_squared_to(p.pos) > 25**2:
                goal = nearest.pos
        delta = goal - p.pos
        desired = delta.normalize() if delta.length_squared() > 1 else Vector2(1, 0)
        near = sim.combat.target(p.pos, 65)
        if near and near.pos.distance_squared_to(p.pos) < 45**2:
            away = p.pos - near.pos
            if away.length_squared() > 1:
                desired += away.normalize() * 1.2
    if desired.length_squared() < 0.01:
        desired = Vector2(1, 0)
    desired = desired.normalize()
    # Avoid getting stuck on a trunk without altering speed or world collision.
    predicted = sim.world.move(p.pos, desired * 25, p.radius)
    if predicted.distance_squared_to(p.pos) < 10**2:
        options = [desired.rotate(a) for a in (60, -60, 120, -120, 180)]
        desired = max(
            options,
            key=lambda v: sim.world.move(p.pos, v * 25, p.radius).distance_squared_to(p.pos),
        )
    return desired


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=47)
    parser.add_argument("--seconds", type=int, default=2100)
    parser.add_argument("--invulnerable", action="store_true")
    parser.add_argument("--class", dest="class_id", default="paladin")
    parser.add_argument("--zone", default="elwynn")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/milestone5/campaign")
    args = parser.parse_args()
    profile = SaveStore(args.profile) if args.profile else None
    sim = Simulation(
        load_content(),
        args.class_id,
        seed=args.seed,
        zone_id=args.zone,
        permanent=profile.loadout(args.class_id) if profile else None,
    )
    sim.player.invulnerable = args.invulnerable
    sim.debug_used = args.invulnerable
    start = time.perf_counter()
    checkpoints = []
    next_report = 60
    peak_enemies = 0
    card_counts = {}
    first_reward = None
    for tick in range(args.seconds * 60 + 1):
        while sim.choices:
            card = choose(sim)
            card_counts[card.kind] = card_counts.get(card.kind, 0) + 1
            if card.kind == "reward" and first_reward is None:
                first_reward = round(sim.elapsed, 2)
        heading = movement(sim, tick)
        if sim.player.manual:
            if (
                sim.player.health < sim.player.max_health * 0.8
                or sim.combat.target(sim.player.pos, 160)
                or sim.boss
            ):
                sim.activate_manual(heading)
        sim.step(FIXED_DT, heading)
        sim.sound_events.clear()
        peak_enemies = max(peak_enemies, len(sim.enemies))
        if sim.elapsed >= next_report:
            entry = dict(
                time=round(sim.elapsed, 1),
                level=sim.player.level,
                health=round(sim.player.health, 1),
                kills=sim.kills,
                enemies=len(sim.enemies),
                elites=sim.elites,
                evolved=sim.evolved,
                boss=sim.boss_result,
                peak_enemies=peak_enemies,
                xp_collected=round(sim.run_xp_collected),
                gems=sum(p.kind == "xp" for p in sim.pickups.values()),
            )
            checkpoints.append(entry)
            print(json.dumps(entry), flush=True)
            next_report += 60
            peak_enemies = 0
        if sim.finished:
            break
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    save = SaveStore(output / f"full-run-private-save-{args.seed}-{time.time_ns()}/save.json")
    rewards = (
        None
        if sim.debug_used
        else save.reward_run(
            sim.class_id,
            sim.kills,
            sim.elites,
            sim.elapsed,
            sim.won,
            sim.gold,
            sim.evolved,
            sim.class_xp_kills,
            sim.player.meta.get("gold"),
            sim.boss.boss_id if sim.boss else "",
            summary=sim.ledger.summary(sim),
        )
    )
    result = dict(
        outcome=sim.outcome or "timeout",
        class_id=args.class_id,
        zone=args.zone,
        permanent_profile=str(args.profile) if args.profile else None,
        won=sim.won,
        elapsed=sim.elapsed,
        health=sim.player.health,
        level=sim.player.level,
        kills=sim.kills,
        elites=sim.elites,
        evolved=sim.evolved,
        boss=sim.boss_result,
        boss_attacks={
            aid: count
            for aid, count in sim.enemy_combat.attack_counts.items()
            if sim.boss and aid in sim.content.bosses[sim.boss.boss_id].attacks
        },
        spells=list(sim.player.spells),
        passives=sim.player.passives,
        manual=sim.player.manual.id if sim.player.manual else None,
        cheats=args.invulnerable,
        wall_seconds=round(time.perf_counter() - start, 2),
        card_counts=card_counts,
        first_reward_seconds=first_reward,
        rewards=rewards,
        checkpoints=checkpoints,
    )
    path = output / ("full-run-invulnerable.json" if args.invulnerable else "full-run.json")
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "checkpoints"}, indent=2), flush=True)
    if args.seconds >= 1800 and not sim.won:
        raise SystemExit("Full run did not reach victory; inspect checkpoint report")


if __name__ == "__main__":
    main()
