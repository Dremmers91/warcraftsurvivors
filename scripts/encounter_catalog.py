"""Regenerate the enemy/wave/attack reference directly from shipped campaign data."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
content = json.loads(
    (root / "src/warcraft_survivors/data/content.json").read_text(encoding="utf-8")
)
data = json.loads(
    (root / "src/warcraft_survivors/data/encounters.json").read_text(encoding="utf-8")
)
rows = [
    "# Elwynn encounter catalog — v0.5.0",
    "",
    "Generated from shipped JSON by `scripts/encounter_catalog.py`. Stats below are unscaled base values; sprite IDs select bundled directional atlases. Time bounds are seconds; ordinary spawns honor time and forest/road restrictions.",
    "",
    "## Regular enemies",
    "",
    "| ID | HP | Damage | Speed | XP | Radius | Behavior | Attacks | First time | Terrain | Class XP | Sprite |",
    "|---|---:|---:|---:|---:|---:|---|---|---:|---|---:|---|",
]
for e in content["enemies"]:
    rows.append(
        f"| {e['id']} | {e['health']} | {e['damage']} | {e['speed']} | {e['xp']} | {e['radius']} | {e['behavior']} | {', '.join(e['attacks']) or 'contact'} | {e['min_time']} | {e['terrain']} | {e['class_xp']} | {e['sprite']} |"
    )
rows += [
    "",
    "All regular enemies have max_time 1800, 10% gold-drop chance and explicit health/damage/XP scaling factors in content.json. Difficulty uses each wave multiplier: base HP × (1 + (wave health − 1) × enemy health_scaling); equivalent damage/XP calculations use their corresponding factors. Speed adds wave speed. Elites multiply their scaled base stats; boss HP uses its own formula.",
    "",
    "## Thirty minute waves",
    "",
    "Rates are sustained enemies/second; batches control release intervals. Reinforcements release over three seconds on entering a wave. Density is a living-enemy budget, not a target that forcibly fills every frame. Composition uses weighted random sampling after spawn eligibility. New waves retain living foes.",
    "",
    "| Start | Name | Rate | Batch | Density | Surge | HP × | Damage × | XP × | Speed + | Composition weights |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
]
for w in data["waves"]:
    rows.append(
        f"| {w['start'] // 60:02}:00 | {w['name']} | {w['rate']:.2f} | {w['batch']} | {w['density']} | {w['surge']} | {w['health']:.3f} | {w['damage']:.3f} | {w['xp']:.3f} | {w['speed']:.1f} | {', '.join(f'{k}:{v}' for k, v in w['weights'].items())} |"
    )
rows += [
    "",
    "After 30:00, sustained weak adds use kobold:wolf 7:3 at 3.5/sec in pairs, without reinforcement surges. The regular-enemy safety ceiling is 6,000; living elites/bosses are additional. The campaign timer stops but the boss encounter remains live.",
    "",
    "## Elite archetypes",
    "",
    "One randomly selected archetype appears at 05:00, 10:00, 15:00, 20:00 and 25:00. No elite is scheduled at 30:00. Multiple surviving elites coexist. Every elite drops a chest and bonus XP/gold/class XP exactly once.",
    "",
    "| Name | Base enemy | HP × | Damage × | XP × | Radius × | Bonus class XP | Gold | Attacks |",
    "|---|---|---:|---:|---:|---:|---:|---:|---|",
]
for e in data["elites"]:
    rows.append(
        f"| {e['name']} | {e['enemy']} | {e['health']} | {e['damage']} | {e.get('xp', 12)} | {e.get('radius_scale', 1.55)} | {e['class_xp']} | {e['gold']} | {', '.join(e['attacks'])} |"
    )
rows += [
    "",
    "Bonus class XP is added to base-enemy class XP. Chests pause gameplay with three unique options. If any spell has Rank 8 and its required passive, at least one eligible evolution is guaranteed. Choose exactly one; evolution consumes the original spell slot.",
    "",
    "## Hostile attacks",
    "",
    "Warnings lock aim/location and prevent contact damage while the owner is busy. Projectiles and charges use swept collision. Rings expand; ordinary hazards hit once. Boss attacks penetrate 0.5 armor and add 6% maximum health before mitigation; damaging hits wound automatic recovery for two seconds. Global immunity, shields and manual defenses still apply. Additional zones and persistent/control attacks are cataloged in ZONE_CATALOG.md.",
    "",
    "| ID | Shape | Damage | Cooldown s | Warning s | Active s | Radius | Reach | Speed | Count | Spread/arc ° |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for a in data["attacks"]:
    rows.append(
        f"| {a['id']} | {a['kind']} | {a['damage']} | {a['cooldown']} | {a['warning']} | {a['duration']} | {a['radius']} | {a['reach']} | {a['speed']} | {a['count']} | {a['angle']} |"
    )
rows += [
    "",
    "## Hogger and results",
    "",
    "Hogger is Elwynn's initial boss-pool entry. He spawns once at 30:00, with 450,000 × (1 + 0.008 × max(0, player level − 30)) HP, base damage 30, speed 105 and collision radius 42. Cleave → charge → leap → quake repeat when in range. At 50% HP, cooldown multiplier is 0.72 and attack damage multiplier 1.25. Boss kill grants 1,200 run XP, 1,000 class XP and 250 gold. Fear is ignored; slow is capped at 30% and knockback reduced to 10%.",
    "",
    "Victory requires Hogger dead and player alive after 30:00; a lethal tie is failure. Death/abandon keep prior earned rewards. Boss selection, art, attacks and rewards are data-defined for future randomized bosses.",
    "",
    "## Independent progression",
    "",
    "- Run requirement: `10 + level × 7 + level^1.45 × 1.6 + max(0, level−40)^1.65 × 2.5`. Only collected gems award run XP; their values scale with wave/variant. Gems merge spatially without losing value and drift toward the player after 45 live seconds.",
    "- Permanent class XP: actual sum of catalog kill rewards (including elite/boss bonuses) + floor(min(1800, elapsed)/6) + 5,000 on victory.",
    "- Gold: collected/banked gold + floor(kills/8) + floor(min(1800, elapsed)/20) + 1,500 on victory + first-time achievement gold. Elite/boss gold already belongs to the bank and is not added twice.",
    "- First Blood: 20 gold; Centurion: 50; Survivor: 75; Elite Hunter: 80; Ascension: 100; Defender of Elwynn: 300. Existing achievements never pay again. Saves credit the selected class once per results screen. Modified developer runs receive no saved rewards.",
    "",
    "Milestone 5 adds four zones with independent boss pools; no next milestone is enabled.",
]
(root / "docs/ENCOUNTER_CATALOG.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
print("Wrote docs/ENCOUNTER_CATALOG.md")
