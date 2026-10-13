"""Explicit development tools; frozen/release builds reject them at both gates."""

from __future__ import annotations

import sys

import pygame
from pygame import Vector2

from .simulation import Simulation


def parse_run_time(value: str) -> float:
    if ":" in value:
        parts = value.split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts) or int(parts[1]) >= 60:
            raise ValueError("Use MM:SS")
        seconds = int(parts[0]) * 60 + int(parts[1])
    else:
        seconds = int(value)
    if not 0 <= seconds <= 1800:
        raise ValueError("Time must be between 0:00 and 30:00")
    return float(seconds)


def debug_allowed(requested: bool, release: bool = False) -> bool:
    return requested and not release and not bool(getattr(sys, "frozen", False))


class DebugTools:
    def __init__(self, requested: bool = False, release: bool = False) -> None:
        self.enabled = debug_allowed(requested, release)
        self.overlay = self.enabled
        self.speed = 1
        self.time_entry: str | None = None

    def reset(self) -> None:
        self.speed = 1
        self.overlay = self.enabled
        self.time_entry = None

    def input_time(self, key: int, sim: Simulation) -> bool:
        if not self.enabled or bool(getattr(sys, "frozen", False)) or self.time_entry is None:
            return False
        if key == pygame.K_ESCAPE:
            self.time_entry = None
        elif key == pygame.K_BACKSPACE:
            self.time_entry = self.time_entry[:-1]
        elif pygame.K_0 <= key <= pygame.K_9 and len(self.time_entry) < 6:
            self.time_entry += chr(key)
        elif key in (pygame.K_COLON, pygame.K_SEMICOLON) and ":" not in self.time_entry:
            self.time_entry += ":"
        elif key == pygame.K_RETURN:
            try:
                sim.jump_time(parse_run_time(self.time_entry))
                self.time_entry = None
            except ValueError:
                sim.notify("DEBUG: enter MM:SS or seconds between 0 and 1800")
        return True

    def handle(self, key: int, sim: Simulation) -> bool:
        if not self.enabled or bool(getattr(sys, "frozen", False)) or sim.finished or sim.choices:
            return False
        if key == pygame.K_F3:
            self.overlay = not self.overlay
        elif key == pygame.K_F4:
            self.speed = {1: 2, 2: 4, 4: 8, 8: 16, 16: 32, 32: 64, 64: 1}[self.speed]
            sim.notify(f"DEBUG: simulation speed {self.speed}x")
        elif key == pygame.K_F5:
            sim.player.xp += sim.player.xp_required
            sim.level_check()
        elif key == pygame.K_F6:
            for index in range(10):
                offset = Vector2(240, 0).rotate(index * 36)
                sim.spawn(pos=sim.player.pos + offset)
            sim.notify("DEBUG: ten enemies spawned")
        elif key == pygame.K_F7:
            for enemy in sim.enemies:
                enemy.health = 0
            sim.collect_dead()
            sim.notify("DEBUG: all enemies defeated")
        elif key == pygame.K_F8:
            sim.player.invulnerable = not sim.player.invulnerable
            sim.notify("DEBUG: invulnerability " + ("ON" if sim.player.invulnerable else "OFF"))
        elif key == pygame.K_F9:
            sim.jump_time((int(sim.time // 60) + 1) * 60)
        elif key == pygame.K_F10:
            sim.spawn_elite()
        elif key == pygame.K_F11:
            sim.spawn_boss(force=True)
        elif key == pygame.K_F12:
            sim.gold += 100
            sim.notify("DEBUG: 100 run gold granted")
        elif key == pygame.K_t:
            self.time_entry = ""
        else:
            return False
        sim.debug_used = True
        return True
