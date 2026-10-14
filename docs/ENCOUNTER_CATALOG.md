# Elwynn encounter catalog — v0.5.0

Generated from shipped JSON by `scripts/encounter_catalog.py`. Stats below are unscaled base values; sprite IDs select bundled directional atlases. Time bounds are seconds; ordinary spawns honor time and forest/road restrictions.

## Regular enemies

| ID | HP | Damage | Speed | XP | Radius | Behavior | Attacks | First time | Terrain | Class XP | Sprite |
|---|---:|---:|---:|---:|---:|---|---|---:|---|---:|---|
| kobold | 32 | 10 | 84 | 6 | 13 | chase | contact | 0 | any | 1 | kobold |
| wolf | 30 | 10 | 132 | 6 | 12 | chase | contact | 0 | any | 1 | wolf |
| bandit | 55 | 14 | 86 | 10 | 15 | chase | contact | 120 | road | 2 | bandit |
| kobold_geomancer | 42 | 10 | 72 | 8 | 13 | ranged | stone_bolt | 300 | any | 2 | kobold_geomancer |
| defias_cutpurse | 38 | 10 | 145 | 8 | 13 | flank | contact | 240 | road | 2 | defias_cutpurse |
| defias_marksman | 48 | 13 | 84 | 10 | 14 | ranged | arrow | 480 | road | 2 | defias_marksman |
| gnoll | 88 | 17 | 90 | 14 | 17 | bruiser | gnoll_smash | 420 | any | 3 | gnoll |
| gnoll_shaman | 80 | 12 | 82 | 16 | 16 | ranged | lightning | 720 | any | 3 | gnoll_shaman |
| spider | 30 | 8 | 110 | 6 | 12 | ranged | poison_spit | 180 | forest | 1 | spider |
| forest_boar | 68 | 13 | 96 | 10 | 16 | charge | boar_charge | 360 | forest | 2 | forest_boar |
| forest_bear | 140 | 24 | 72 | 20 | 20 | bruiser | bear_swipe | 900 | forest | 4 | forest_bear |

All regular enemies have max_time 1800, 10% gold-drop chance and explicit health/damage/XP scaling factors in content.json. Difficulty uses each wave multiplier: base HP × (1 + (wave health − 1) × enemy health_scaling); equivalent damage/XP calculations use their corresponding factors. Speed adds wave speed. Elites multiply their scaled base stats; boss HP uses its own formula.

## Thirty minute waves

Rates are sustained enemies/second; batches control release intervals. Reinforcements release over three seconds on entering a wave. Density is a living-enemy budget, not a target that forcibly fills every frame. Composition uses weighted random sampling after spawn eligibility. New waves retain living foes.

| Start | Name | Rate | Batch | Density | Surge | HP × | Damage × | XP × | Speed + | Composition weights |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 00:00 | Forest Patrol 1 | 1.20 | 1 | 75 | 0 | 1.000 | 1.000 | 1.000 | 0.0 | kobold:8, wolf:2 |
| 01:00 | Forest Patrol 2 | 1.50 | 1 | 115 | 0 | 1.120 | 1.018 | 1.075 | 1.1 | kobold:8, wolf:2 |
| 02:00 | Forest Patrol 3 | 1.80 | 1 | 155 | 0 | 1.240 | 1.036 | 1.150 | 2.2 | kobold:8, wolf:2, bandit:2 |
| 03:00 | Forest Patrol 4 | 2.30 | 2 | 195 | 0 | 1.360 | 1.054 | 1.225 | 3.3 | kobold:8, wolf:2, bandit:2, spider:1 |
| 04:00 | Forest Patrol 5 | 2.80 | 2 | 235 | 0 | 1.480 | 1.072 | 1.300 | 4.4 | kobold:8, wolf:2, bandit:2, defias_cutpurse:2, spider:1 |
| 05:00 | Riverpaw Incursion 6 | 2.80 | 3 | 240 | 0 | 1.600 | 1.090 | 1.375 | 5.5 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, spider:1 |
| 06:00 | Riverpaw Incursion 7 | 3.45 | 3 | 325 | 0 | 1.720 | 1.108 | 1.450 | 6.6 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, spider:1, forest_boar:2 |
| 07:00 | Riverpaw Incursion 8 | 4.10 | 3 | 410 | 0 | 1.840 | 1.126 | 1.525 | 7.7 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, gnoll:2, spider:1, forest_boar:2 |
| 08:00 | Riverpaw Incursion 9 | 4.75 | 3 | 495 | 35 | 1.960 | 1.144 | 1.600 | 8.8 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, spider:1, forest_boar:2 |
| 09:00 | Riverpaw Incursion 10 | 5.40 | 4 | 580 | 44 | 2.080 | 1.162 | 1.675 | 9.9 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, spider:1, forest_boar:2 |
| 10:00 | Defias Reinforcements 11 | 6.05 | 4 | 665 | 53 | 2.200 | 1.180 | 1.750 | 11.0 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, spider:1, forest_boar:2 |
| 11:00 | Defias Reinforcements 12 | 6.98 | 4 | 750 | 62 | 2.419 | 1.198 | 1.825 | 12.1 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, spider:1, forest_boar:2 |
| 12:00 | Defias Reinforcements 13 | 7.97 | 4 | 835 | 71 | 2.670 | 1.216 | 1.900 | 13.2 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, gnoll_shaman:1, spider:1, forest_boar:2 |
| 13:00 | Defias Reinforcements 14 | 9.01 | 5 | 920 | 80 | 2.944 | 1.234 | 1.975 | 14.3 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, gnoll_shaman:1, spider:1, forest_boar:2 |
| 14:00 | Defias Reinforcements 15 | 10.11 | 5 | 1005 | 89 | 3.236 | 1.252 | 2.050 | 15.4 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, gnoll_shaman:1, spider:1, forest_boar:2 |
| 15:00 | Forest Under Siege 16 | 12.11 | 6 | 1300 | 100 | 3.545 | 1.270 | 2.125 | 16.5 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:2 |
| 16:00 | Forest Under Siege 17 | 13.84 | 6 | 1465 | 118 | 3.870 | 1.288 | 2.200 | 17.6 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:2 |
| 17:00 | Forest Under Siege 18 | 15.67 | 6 | 1630 | 136 | 4.211 | 1.306 | 2.275 | 18.7 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:2 |
| 18:00 | Forest Under Siege 19 | 17.58 | 6 | 1795 | 154 | 4.568 | 1.324 | 2.350 | 19.8 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:2 |
| 19:00 | Forest Under Siege 20 | 19.58 | 6 | 1960 | 172 | 4.939 | 1.342 | 2.425 | 20.9 | kobold:6, wolf:4, bandit:2, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:2, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:2 |
| 20:00 | Forest Under Siege 21 | 21.67 | 6 | 2125 | 190 | 5.326 | 1.360 | 2.500 | 22.0 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 21:00 | Forest Under Siege 22 | 23.85 | 6 | 2290 | 208 | 5.727 | 1.378 | 2.575 | 23.1 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 22:00 | Forest Under Siege 23 | 26.12 | 6 | 2455 | 226 | 6.143 | 1.396 | 2.650 | 24.2 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 23:00 | Forest Under Siege 24 | 28.47 | 6 | 2620 | 244 | 6.573 | 1.414 | 2.725 | 25.3 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 24:00 | Forest Under Siege 25 | 30.92 | 6 | 2785 | 262 | 7.018 | 1.432 | 2.800 | 26.4 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 25:00 | Last Stand of Elwynn 26 | 34.26 | 8 | 3200 | 600 | 7.478 | 1.450 | 2.875 | 27.5 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 26:00 | Last Stand of Elwynn 27 | 37.83 | 8 | 3550 | 775 | 7.952 | 1.468 | 2.950 | 28.6 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 27:00 | Last Stand of Elwynn 28 | 41.52 | 8 | 3900 | 950 | 8.440 | 1.486 | 3.025 | 29.7 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 28:00 | Last Stand of Elwynn 29 | 45.35 | 8 | 4250 | 1125 | 8.943 | 1.504 | 3.100 | 30.8 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |
| 29:00 | Last Stand of Elwynn 30 | 49.32 | 8 | 4600 | 1300 | 9.461 | 1.522 | 3.175 | 31.9 | kobold:12, wolf:8, bandit:7, kobold_geomancer:1, defias_cutpurse:2, defias_marksman:1, gnoll:5, gnoll_shaman:1, spider:1, forest_boar:2, forest_bear:3 |

After 30:00, sustained weak adds use kobold:wolf 7:3 at 3.5/sec in pairs, without reinforcement surges. The regular-enemy safety ceiling is 6,000; living elites/bosses are additional. The campaign timer stops but the boss encounter remains live.

## Elite archetypes

One randomly selected archetype appears at 05:00, 10:00, 15:00, 20:00 and 25:00. No elite is scheduled at 30:00. Multiple surviving elites coexist. Every elite drops a chest and bonus XP/gold/class XP exactly once.

| Name | Base enemy | HP × | Damage × | XP × | Radius × | Bonus class XP | Gold | Attacks |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Defias Captain | bandit | 18 | 1.5 | 12 | 1.55 | 100 | 25 | captain_volley, captain_bomb |
| Riverpaw Packlord | gnoll | 18 | 1.4 | 12 | 1.55 | 125 | 35 | pack_charge, pack_smash |
| Forest Broodmother | spider | 30 | 1.5 | 12 | 1.55 | 150 | 45 | web_trap, venom_volley |

Bonus class XP is added to base-enemy class XP. Chests pause gameplay with three unique options. If any spell has Rank 8 and its required passive, at least one eligible evolution is guaranteed. Choose exactly one; evolution consumes the original spell slot.

## Hostile attacks

Warnings lock aim/location and prevent contact damage while the owner is busy. Projectiles and charges use swept collision. Rings expand; ordinary hazards hit once. Boss attacks penetrate 0.5 armor and add 6% maximum health before mitigation; damaging hits wound automatic recovery for two seconds. Global immunity, shields and manual defenses still apply. Additional zones and persistent/control attacks are cataloged in ZONE_CATALOG.md.

| ID | Shape | Damage | Cooldown s | Warning s | Active s | Radius | Reach | Speed | Count | Spread/arc ° |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| stone_bolt | missile | 10 | 3.8 | 0.55 | 0.12 | 8 | 340 | 220 | 1 | 100 |
| arrow | missile | 12 | 3.5 | 0.6 | 0.12 | 6 | 380 | 320 | 1 | 100 |
| lightning | missile | 12 | 4 | 0.65 | 0.15 | 8 | 380 | 230 | 3 | 25 |
| poison_spit | missile | 8 | 4.5 | 0.65 | 0.12 | 8 | 260 | 210 | 1 | 100 |
| gnoll_smash | circle | 18 | 4.5 | 0.8 | 0.15 | 75 | 125 | 0 | 1 | 100 |
| bear_swipe | arc | 24 | 5 | 1 | 0.15 | 100 | 150 | 0 | 1 | 160 |
| boar_charge | charge | 16 | 7 | 0.85 | 0.7 | 23 | 230 | 330 | 1 | 100 |
| captain_volley | missile | 20 | 4 | 0.85 | 0.2 | 9 | 500 | 280 | 5 | 65 |
| captain_bomb | circle | 28 | 5 | 1.3 | 0.2 | 110 | 550 | 0 | 1 | 100 |
| pack_charge | charge | 26 | 5 | 1 | 0.85 | 34 | 400 | 460 | 1 | 100 |
| pack_smash | ring | 24 | 5 | 1.1 | 0.8 | 185 | 350 | 0 | 1 | 100 |
| web_trap | circle | 23 | 4.5 | 1.1 | 0.25 | 125 | 550 | 0 | 1 | 100 |
| venom_volley | missile | 16 | 4 | 0.85 | 0.2 | 10 | 500 | 230 | 7 | 95 |
| hogger_cleave | arc | 36 | 3.8 | 0.95 | 0.2 | 155 | 280 | 0 | 1 | 130 |
| hogger_charge | charge | 32 | 5 | 1.1 | 1 | 38 | 550 | 520 | 1 | 100 |
| hogger_leap | leap | 42 | 5.5 | 1.35 | 0.25 | 130 | 850 | 0 | 1 | 100 |
| hogger_quake | ring | 28 | 5.5 | 1.2 | 1.05 | 270 | 600 | 0 | 1 | 100 |

## Hogger and results

Hogger is Elwynn's initial boss-pool entry. He spawns once at 30:00, with 450,000 × (1 + 0.008 × max(0, player level − 30)) HP, base damage 30, speed 105 and collision radius 42. Cleave → charge → leap → quake repeat when in range. At 50% HP, cooldown multiplier is 0.72 and attack damage multiplier 1.25. Boss kill grants 1,200 run XP, 1,000 class XP and 250 gold. Fear is ignored; slow is capped at 30% and knockback reduced to 10%.

Victory requires Hogger dead and player alive after 30:00; a lethal tie is failure. Death/abandon keep prior earned rewards. Boss selection, art, attacks and rewards are data-defined for future randomized bosses.

## Independent progression

- Run requirement: `10 + level × 7 + level^1.45 × 1.6 + max(0, level−40)^1.65 × 3.75`. Only collected gems award run XP; their values scale with wave/variant. Gems merge spatially without losing value and drift toward the player after 45 live seconds.
- Permanent class XP: actual sum of catalog kill rewards (including elite/boss bonuses) + floor(min(1800, elapsed)/6) + 5,000 on victory.
- Gold: collected/banked gold + floor(kills/8) + floor(min(1800, elapsed)/20) + 1,500 on victory + first-time achievement gold. Elite/boss gold already belongs to the bank and is not added twice.
- First Blood: 20 gold; Centurion: 50; Survivor: 75; Elite Hunter: 80; Ascension: 100; Defender of Elwynn: 300. Existing achievements never pay again. Saves credit the selected class once per results screen. Modified developer runs receive no saved rewards.

Milestone 5 adds four zones with independent boss pools; no next milestone is enabled.
