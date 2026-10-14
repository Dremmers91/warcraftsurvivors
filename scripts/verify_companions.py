"""Run staged companion gameplay and capture actual renderer output, without user saves."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pygame  # noqa: E402
from pygame import Vector2  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.entities import SpellState  # noqa: E402
from warcraft_survivors.rendering import Renderer  # noqa: E402
from warcraft_survivors.simulation import FIXED_DT, Simulation  # noqa: E402


def main():
    pygame.init()
    pygame.display.set_mode((1280, 720))
    content = load_content()
    renderer = Renderer(content)
    out = ROOT / "artifacts/pets-summons/screenshots"
    out.mkdir(parents=True, exist_ok=True)
    selected = ROOT / "docs/screenshots/pets-summons"
    selected.mkdir(parents=True, exist_ok=True)
    evidence = []
    for zone in content.zones:
        for cid, base in (("hunter", "beast_companion"), ("warlock", "summon_felguard")):
            for form, rank in (("rank1", 1), ("rank8", 8), ("evolution", 8)):
                aid = base + "_evolved" if form == "evolution" else base
                sim = Simulation(content, cid, seed=47, zone_id=zone)
                sim.debug_used = True
                sim.player.spells = {aid: SpellState(rank)}
                sim.player.invulnerable = True
                sim.spawner.timer = 10**9
                for index in range(24):
                    kind = (
                        "wolf"
                        if zone == "elwynn" and index % 3 == 0
                        else content.zones[zone].enemies[index % len(content.zones[zone].enemies)]
                    )
                    enemy = sim.spawn(
                        kind,
                        sim.player.pos + Vector2(100 + index % 4 * 45, 0).rotate(index * 137.5),
                    )
                    enemy.speed = 0
                    enemy.health = enemy.max_health = 100000
                for _ in range(45):
                    sim.step(FIXED_DT)
                renderer.quality = "medium"
                renderer.draw_game(sim)
                pygame.image.save(renderer.canvas, str(out / f"{zone}-{cid}-{form}.png"))
                if (zone, cid, form) in {
                    ("elwynn", "hunter", "rank1"),
                    ("elwynn", "warlock", "evolution"),
                    ("stranglethorn", "hunter", "rank8"),
                }:
                    pygame.image.save(renderer.canvas, str(selected / f"{zone}-{cid}-{form}.png"))
                for quality in ("low", "high"):
                    renderer.quality = quality
                    renderer.draw_game(sim)
                    if zone in {"elwynn", "icecrown"} and form == "evolution":
                        pygame.image.save(
                            renderer.canvas, str(out / f"{zone}-{cid}-{form}-{quality}.png")
                        )
                        if zone == "icecrown" and cid == "warlock" and quality == "low":
                            pygame.image.save(
                                renderer.canvas,
                                str(selected / f"{zone}-{cid}-{form}-{quality}.png"),
                            )
                for _ in range(255):
                    sim.step(FIXED_DT)
                evidence.append(
                    dict(
                        zone=zone,
                        class_id=cid,
                        form=form,
                        companions=len(sim.combat.companions),
                        damage=round(sum(e.max_health - e.health for e in sim.enemies), 2),
                        damaged=sum(e.health < e.max_health for e in sim.enemies),
                        shots=len(sim.projectiles),
                    )
                )
                assert evidence[-1]["damage"] > 0
                assert all(
                    p.pos.distance_to(sim.player.pos) <= p.leash + 1e-6
                    for p in sim.combat.companions
                )
    assert not renderer.assets.warnings, renderer.assets.warnings
    report = ROOT / "artifacts/pets-summons/visual-smoke.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            dict(
                note="Staged fixed-step gameplay rendered at 1280x720; no balance certification or normal profile changes.",
                cases=evidence,
            ),
            indent=2,
        )
        + "\n",
        "utf-8",
    )
    pygame.quit()
    print(
        f"Verified {len(evidence)} companion scenarios, all terrains and qualities; captures: {out}"
    )


if __name__ == "__main__":
    main()
