"""Preloaded raster registry, sheet slicing, fixed anchors and safe fallbacks."""

from __future__ import annotations

import json
import math
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame
from pygame import Surface, Vector2

ASSET_ROOT = Path(__file__).resolve().parent / "assets"
DIRECTIONS = ("south", "east", "north", "west")


def facing(direction: Vector2) -> str:
    if abs(direction.x) > abs(direction.y):
        return "east" if direction.x > 0 else "west"
    return "south" if direction.y >= 0 else "north"


@dataclass(frozen=True)
class Frame:
    image: Surface
    anchor: tuple[int, int]

    def at(self, pos: Vector2) -> tuple[int, int]:
        return round(pos.x - self.anchor[0]), round(pos.y - self.anchor[1])


def slice_sheet(
    sheet: Surface, size: tuple[int, int], anchor: tuple[int, int]
) -> list[list[Frame]]:
    width, height = size
    if width < 1 or height < 1 or sheet.get_width() % width or sheet.get_height() % height:
        raise ValueError("Sprite sheet dimensions must be exact frame multiples")
    result = []
    for y in range(0, sheet.get_height(), height):
        row = []
        for x in range(0, sheet.get_width(), width):
            tile = sheet.subsurface((x, y, width, height))
            bounds = tile.get_bounding_rect(min_alpha=1)
            if bounds.width == 0:
                bounds = pygame.Rect(0, 0, 1, 1)
            row.append(
                Frame(tile.subsurface(bounds).copy(), (anchor[0] - bounds.x, anchor[1] - bounds.y))
            )
        result.append(row)
    return result


class AssetManager:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ASSET_ROOT
        self.warnings: list[str] = []
        self.images: dict[str, Surface] = {}
        self.actors: dict[str, dict[str, list[list[Frame]]]] = {}
        self.flashes: dict[str, dict[str, list[list[Frame]]]] = {}
        self.allies: dict[str, dict[str, list[list[Frame]]]] = {}
        self.projectiles: dict[tuple[str, int, int, int], Frame] = {}
        self.effects: dict[str, list[Frame]] = {}
        self.scaled_effects: OrderedDict[tuple[str, int, int, int, int], Frame] = OrderedDict()
        self.scaled_effect_bytes = 0
        self.directional_effects: dict[tuple[str, int, int], Frame] = {}
        self.actor_fps: dict[str, float] = {}
        self.repair = self.emergency((16, 16))
        try:
            self.manifest: dict[str, Any] = json.loads(
                (self.root / "manifest.json").read_text("utf-8")
            )
            if not isinstance(self.manifest, dict) or self.manifest.get("version") != 1:
                raise ValueError("Unsupported or malformed asset registry")
        except (OSError, ValueError):
            self.manifest = {"actors": {}, "images": {}, "effects": {}, "projectiles": {}}
            self.warnings.append("Asset registry unavailable; using repair fallbacks")
        # Decode once, before combat. Runtime methods never call image.load.
        for name, spec in self.manifest.get("images", {}).items():
            self.images[name] = self.load(spec["file"], tuple(spec["size"]))
        for name, spec in self.manifest.get("actors", {}).items():
            self.load_actor(name, spec)
        for name, spec in self.manifest.get("effects", {}).items():
            sheet = self.load(spec["file"], (spec["size"][0] * spec["frames"], spec["size"][1]))
            try:
                self.effects[name] = slice_sheet(sheet, tuple(spec["size"]), tuple(spec["anchor"]))[
                    0
                ]
            except ValueError:
                self.warnings.append(f"Invalid effect sheet: {name}")
                self.effects[name] = [
                    Frame(self.emergency(tuple(spec["size"])), tuple(spec["anchor"]))
                ]
        rotation_cache: dict[tuple[str, int, int, int], Frame] = {}
        for name, spec in self.manifest.get("projectiles", {}).items():
            source = self.effects.get(spec["effect"], [Frame(self.emergency((32, 32)), (16, 16))])
            for rank in range(1, 9):
                size = round(spec["art_size"] * (1 + (rank - 1) * spec.get("rank_scale", 0)))
                for phase, frame in enumerate(source):
                    # The art size and rank scale are visual data, never collision radius.
                    square = Surface(
                        tuple(self.manifest["effects"][spec["effect"]]["size"]), pygame.SRCALPHA
                    )
                    square.blit(
                        frame.image,
                        (
                            square.get_width() // 2 - frame.anchor[0],
                            square.get_height() // 2 - frame.anchor[1],
                        ),
                    )
                    scaled = pygame.transform.scale(square, (size, size))
                    for angle in range(0, 360, 15):
                        cache_key = (spec["effect"], size, phase, angle)
                        if cache_key in rotation_cache:
                            self.projectiles[name, rank, phase, angle] = rotation_cache[cache_key]
                            continue
                        image = pygame.transform.rotate(scaled, -angle)
                        cached = Frame(image, (image.get_width() // 2, image.get_height() // 2))
                        self.projectiles[name, rank, phase, angle] = cached
                        rotation_cache[cache_key] = cached
        for name in self.manifest.get("directional_effects", []):
            for phase, frame in enumerate(self.effects.get(name, [])):
                size = self.manifest["effects"][name]["size"]
                square = Surface(size, pygame.SRCALPHA)
                square.blit(
                    frame.image, (size[0] // 2 - frame.anchor[0], size[1] // 2 - frame.anchor[1])
                )
                for angle in range(0, 360, 45):
                    rotated = pygame.transform.rotate(square, -angle)
                    self.directional_effects[name, phase, angle] = Frame(
                        rotated, (rotated.get_width() // 2, rotated.get_height() // 2)
                    )

    @staticmethod
    def emergency(size: tuple[int, int]) -> Surface:
        # Clearly marked repair art only, never used as the normal production asset.
        image = Surface(size, pygame.SRCALPHA)
        pygame.draw.polygon(
            image, (182, 61, 141), [(size[0] // 2, 2), (size[0] - 2, size[1] - 2), (2, size[1] - 2)]
        )
        return image

    def load(self, relative: str, expected: tuple[int, int]) -> Surface:
        try:
            path = (self.root / relative).resolve()
            if not path.is_relative_to(self.root.resolve()):
                raise ValueError("Asset path escapes its root")
            image = pygame.image.load(str(path)).convert_alpha()
            if image.get_size() != expected:
                raise ValueError("Unexpected raster dimensions")
            return image
        except (OSError, ValueError, pygame.error):
            self.warnings.append(f"Missing or invalid asset: {relative}")
            fallback = self.root / "images/fallback_actor.png"
            try:
                return pygame.transform.scale(
                    pygame.image.load(str(fallback)).convert_alpha(), expected
                )
            except (OSError, pygame.error):
                return self.emergency(expected)

    def load_actor(self, name: str, spec: dict[str, Any]) -> None:
        size = tuple(spec["frame_size"])
        anchor = tuple(spec["anchor"])
        source = self.load(spec["file"], (size[0] * 4, size[1] * 16))
        frames = slice_sheet(source, size, anchor)
        self.actors[name] = {}
        self.flashes[name] = {}
        for index, state in enumerate(("walk", "idle", "cast", "death")):
            rows = frames[index * 4 : index * 4 + 4]
            self.actors[name][state] = rows
            flash_rows = []
            for row in rows:
                flashes = []
                for frame in row:
                    bright = frame.image.copy()
                    bright.fill((110, 100, 85, 0), special_flags=pygame.BLEND_RGBA_ADD)
                    flashes.append(Frame(bright, frame.anchor))
                flash_rows.append(flashes)
            self.flashes[name][state] = flash_rows
        self.actor_fps[name] = float(spec.get("walk_fps", 9))
        if name in {"wolf", "alpha_wolf", "imp", "felguard", "dreadguard"}:
            # Subdued one-pixel allied edge, prepared once; preserve original art.
            self.allies[name] = {}
            for state, rows in self.actors[name].items():
                outlined: list[list[Frame]] = []
                for row in rows:
                    allied_row: list[Frame] = []
                    for frame in row:
                        mask = pygame.mask.from_surface(frame.image)
                        edge = mask.to_surface(
                            setcolor=(110, 164, 171, 210), unsetcolor=(0, 0, 0, 0)
                        )
                        surface = Surface(
                            (frame.image.get_width() + 2, frame.image.get_height() + 2),
                            pygame.SRCALPHA,
                        )
                        for offset in ((0, 1), (2, 1), (1, 0), (1, 2)):
                            surface.blit(edge, offset)
                        surface.blit(frame.image, (1, 1))
                        allied_row.append(
                            Frame(surface, (frame.anchor[0] + 1, frame.anchor[1] + 1))
                        )
                    outlined.append(allied_row)
                self.allies[name][state] = outlined

    def actor(
        self,
        name: str,
        state: str,
        direction: str,
        seconds: float,
        flash: bool = False,
        allied: bool = False,
    ) -> Frame:
        bank = (
            self.flashes
            if flash
            else self.allies
            if allied and name in self.allies
            else self.actors
        )
        if name not in bank:
            if "paladin" in bank:
                name = "paladin"
            else:
                return Frame(self.image("fallback_actor"), (40, 73))
        states = bank[name]
        rows = states.get(state, states["idle"])
        row = rows[DIRECTIONS.index(direction) if direction in DIRECTIONS else 0]
        fps = self.actor_fps[name] if state == "walk" else 4 if state == "idle" else 10
        index = math.floor(max(0, seconds) * fps)
        index = min(len(row) - 1, index) if state in ("cast", "death") else index % len(row)
        return row[index]

    def image(self, name: str) -> Surface:
        if name in self.images:
            return self.images[name]
        return self.images.get("fallback_actor", self.repair)

    def effect(self, name: str, seconds: float, fps: float = 12, loop: bool = False) -> Frame:
        frames = self.effects.get(name)
        if not frames:
            return Frame(self.image("fallback_actor"), (8, 8))
        index = math.floor(max(0, seconds) * fps)
        index = index % len(frames) if loop else min(len(frames) - 1, index)
        return frames[index]

    def projectile(self, name: str, rank: int, seconds: float, angle: float) -> Frame:
        phase_count = len(
            self.effects.get(
                self.manifest.get("projectiles", {}).get(name, {}).get("effect", ""), [None]
            )
        )
        phase = int(seconds * 12) % phase_count
        key = (name, max(1, min(8, rank)), phase, round(angle / 15) * 15 % 360)
        return self.projectiles.get(key, self.effect("holy_hammer", seconds, loop=True))

    def scaled_effect(
        self,
        name: str,
        seconds: float,
        diameter: float,
        angle: float | None = None,
        opacity: int = 255,
    ) -> Frame:
        phase = int(max(0, seconds) * 12) % max(1, len(self.effects.get(name, [])))
        size = max(16, min(1536, round(diameter / 16) * 16))
        heading = round(angle / 45) * 45 % 360 if angle is not None else -1
        key = (name, phase, size, heading, opacity)
        if key in self.scaled_effects:
            self.scaled_effects.move_to_end(key)
            return self.scaled_effects[key]
        frame = self.directional_effects.get(
            (name, phase, heading), self.effect(name, seconds, loop=True)
        )
        source_size = self.manifest.get("effects", {}).get(name, {}).get("size", [48, 48])[0]
        ratio = size / source_size
        image = pygame.transform.scale(
            frame.image,
            (
                max(1, round(frame.image.get_width() * ratio)),
                max(1, round(frame.image.get_height() * ratio)),
            ),
        )
        if opacity < 255:
            image.set_alpha(opacity)
        result = Frame(image, (round(frame.anchor[0] * ratio), round(frame.anchor[1] * ratio)))
        self.scaled_effects[key] = result
        self.scaled_effect_bytes += image.get_width() * image.get_height() * 4
        while self.scaled_effect_bytes > 64 * 1024 * 1024 or len(self.scaled_effects) > 256:
            _, expired = self.scaled_effects.popitem(last=False)
            self.scaled_effect_bytes -= expired.image.get_width() * expired.image.get_height() * 4
        return result
