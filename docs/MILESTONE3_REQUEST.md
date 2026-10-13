# Milestone 3 — Enemy Waves, Elites, Bosses, and Complete Runs

Read the project instructions and inspect the completed gameplay systems. Implement the complete 30-minute survival structure for the initial Elwynn Forest zone.

## Enemy systems

Implement a data-driven enemy catalog with health, damage, movement speed, XP rewards, attack behavior, collision size, visual definitions, spawn restrictions and difficulty scaling. Create at least eight recognizable Elwynn-themed variants including kobolds, wolves, Defias, gnolls, spiders and forest creatures. Keep varied behavior simple enough for very large hordes.

## Wave director

Implement a 30-minute schedule. Early: few enemies, lower health/damage and slower density growth. Midgame: larger hordes, more variants, greater density and toughness. Late: extremely large waves, stronger enemies mixed with weak enemies and dense hordes rewarding area/evolved attacks. Scale XP rewards with growing requirements so meaningful levels continue. Avoid artificially low enemy limits.

## Elites

Spawn approximately every five minutes except the final boss. Distinct visuals, increased health, unique attacks, visible telegraphs, bonus XP, permanent progression rewards and treasure chest drops are required. Chests must permit eligible evolutions. Handle elites still alive when later waves begin.

## Final boss

At 30:00 spawn Hogger with distinct sprite/animations, large health bar, multiple attacks, warnings, movement/charging, suitable health/damage scaling and defeat rewards. Do not automatically end at 30:00: victory requires defeating Hogger. Death during the encounter fails the run but preserves earned progression. Structure selection for additional randomized final bosses later.

## XP and balancing

Increase run XP requirements, scaled enemy XP and spawn rates. Keep independent run gem XP and permanent class XP calculations. Elite kills give bonuses; successful full runs give significant additional class XP and gold. Failed runs retain earned rewards.

## Results

Provide death and victory screens with survival time, player level, enemies killed, elites defeated, final boss result, gold earned, permanent class XP earned and achievements earned.

## Developer testing

Add wave skipping, specific run-time jumps, boss/elite spawning, XP/gold testing and enemy density/performance measurements.

## Acceptance

A real 30-minute run can complete. Composition/density change over time. Elites drop usable qualified evolution chests. Hogger spawns at 30:00; victory requires defeating him. Death/victory results and rewards are correct. Accelerated simulation exercises the complete schedule. Automated tests validate waves, boss conditions and reward calculations. Run tests and fix relevant failures.

Do not advance to the next milestone automatically.
