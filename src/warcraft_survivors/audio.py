"""Preloaded original cues, streamed zone music and safe device failure handling."""

from __future__ import annotations

import logging
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent / "assets/audio"


class Audio:
    def __init__(self) -> None:
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.enabled = True
        self.cooldown = 0.0
        self.music_volume = 0.35
        self.sound_volume = 0.7
        self.track = ""
        self.available = pygame.mixer.get_init() is not None
        if not self.available:
            return
        try:
            pygame.mixer.set_num_channels(12)
            for path in ROOT.glob("*.wav"):
                if not path.stem.startswith("music_"):
                    self.sounds[path.stem] = pygame.mixer.Sound(str(path))
        except (OSError, pygame.error):
            logging.getLogger(__name__).warning(
                "Audio unavailable; continuing silently", exc_info=True
            )
            self.available = False

    def music(self, zone: str) -> None:
        if not self.available:
            return
        try:
            pygame.mixer.music.set_volume(self.music_volume)
            if self.track != zone:
                pygame.mixer.music.load(str(ROOT / f"music_{zone}.wav"))
                pygame.mixer.music.play(-1, fade_ms=600)
                self.track = zone
        except (OSError, pygame.error):
            logging.getLogger(__name__).warning(
                "Music unavailable; continuing silently", exc_info=True
            )
            self.available = False

    def play(self, events: list[str], dt: float) -> None:
        self.cooldown = max(0, self.cooldown - dt)
        if events and self.available and self.enabled and self.cooldown <= 0:
            name = max(
                events,
                key=lambda e: {
                    "hit": 1,
                    "enemy_death": 2,
                    "hurt": 3,
                    "level": 5,
                    "upgrade": 4,
                    "elite": 6,
                    "boss": 7,
                    "death": 8,
                    "evolution": 9,
                    "victory": 10,
                }.get(e, 0),
            )
            sound = self.sounds.get(name)
            if sound:
                try:
                    sound.set_volume(self.sound_volume)
                    sound.play()
                    self.cooldown = 0.07
                except pygame.error:
                    self.available = False
        events.clear()
