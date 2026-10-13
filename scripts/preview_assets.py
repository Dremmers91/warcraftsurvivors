"""Read-only paginated gallery of shipped actors and catalog effects."""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


import pygame  # noqa: E402
from pygame import Vector2  # noqa: E402

from warcraft_survivors.asset_manager import DIRECTIONS  # noqa: E402
from warcraft_survivors.content import load_content  # noqa: E402
from warcraft_survivors.rendering import CREAM, GOLD, MUTED, Renderer  # noqa: E402


def draw_gallery(
    renderer: Renderer,
    page: int,
    direction: int,
    state: str,
    seconds: float,
    rank: int,
    sheet_page: int = 0,
) -> None:
    renderer.backdrop(
        "The Elwynn art workshop",
        "Original raster assets  /  Six playable classes and the complete ability catalog",
    )

    assets = renderer.assets

    if page == 0:
        for index, name in enumerate(list(assets.actors)[sheet_page * 9 : sheet_page * 9 + 9]):
            x, y = 64 + index % 3 * 388, 190 + index // 3 * 158

            renderer.panel(pygame.Rect(x, y, 364, 145))

            renderer.text(name.replace("_", " ").title(), (x + 18, y + 14), 28, GOLD)

            frame = assets.actor(name, state, DIRECTIONS[direction], seconds)

            image = pygame.transform.scale(
                frame.image, (frame.image.get_width() * 2, frame.image.get_height() * 2)
            )

            renderer.canvas.blit(
                image, (x + 264 - frame.anchor[0] * 2, y + 139 - frame.anchor[1] * 2)
            )

            renderer.text(
                "Playable" if name in renderer.content.classes else "Enemy / summon",
                (x + 18, y + 64),
                18,
                MUTED,
            )

            renderer.text(f"{DIRECTIONS[direction]} / {state}", (x + 18, y + 99), 20, CREAM)

    elif page == 1:
        center = Vector2(380 + math.sin(seconds * 0.6) * 20, 450)

        rune = assets.effect("consecration", seconds, loop=True)

        renderer.canvas.blit(rune.image, rune.at(center))

        actor = assets.actor("paladin", "idle", "south", seconds)

        renderer.canvas.blit(actor.image, actor.at(center))

        for index in range(1 + rank // 2):
            angle = seconds * 90 + index * 360 / (1 + rank // 2)

            point = center + Vector2(100, 0).rotate(angle)

            hammer = assets.projectile("blessed_hammer", rank, seconds, angle)

            renderer.canvas.blit(hammer.image, hammer.at(point))

        renderer.text("Consecration + Blessed Hammer", (180, 205), 28, GOLD)

        renderer.text("Following ground / orbit visual demonstration", (165, 250), 20, MUTED)

        shield = assets.projectile("avengers_shield", rank, seconds, seconds * 180)

        point = Vector2(980 + math.sin(seconds * 1.7) * 130, 315)

        renderer.canvas.blit(shield.image, shield.at(point))

        renderer.text("Avenger's Shield", (835, 205), 28, GOLD)

        renderer.text("Cached rotations / independent art size", (835, 245), 20, MUTED)

        for index, name in enumerate(
            ("holy_hammer", "frostbolt", "shadow_bolt", "holy_impact", "divine_storm", "blizzard")
        ):
            frame = assets.effect(name, seconds, loop=True)

            point = Vector2(785 + index % 3 * 165, 450 + index // 3 * 140)

            surface = pygame.transform.scale(
                frame.image, (min(115, frame.image.get_width()), min(115, frame.image.get_height()))
            )

            renderer.canvas.blit(surface, surface.get_rect(center=point))

            renderer.text(name.replace("_", " ").title(), (point.x, point.y + 66), 18, CREAM, True)

    elif page == 2:
        for index, name in enumerate(("tree_0", "tree_1", "tree_2", "bush", "log", "rocks")):
            x, y = 100 + index % 3 * 380, 190 + index // 3 * 240

            renderer.panel(pygame.Rect(x, y, 330, 220))

            image = assets.image(name)

            renderer.canvas.blit(image, image.get_rect(midbottom=(x + 165, y + 194)))

            renderer.text(name.replace("_", " ").title(), (x + 20, y + 196), 20, GOLD)

    else:
        names = list(
            renderer.content.abilities | renderer.content.evolutions | renderer.content.manuals
        )

        for index, name in enumerate(names[sheet_page * 12 : sheet_page * 12 + 12]):
            x, y = 64 + index % 4 * 294, 180 + index // 4 * 164

            renderer.panel(pygame.Rect(x, y, 280, 151))

            renderer.wrapped(
                name.replace("_", " ").title(), pygame.Rect(x + 12, y + 10, 256, 45), 22, GOLD
            )

            frame = assets.scaled_effect(name, seconds, 82)

            renderer.canvas.blit(frame.image, frame.at(Vector2(x + 140, y + 98)))

    renderer.text(
        "Tab / PageDown: next sheet · 1 actors  /  2 effects  /  3 environment / 4 catalog / arrows facing  /  A animation  /  R rank  /  Space pause",
        (640, 702),
        18,
        MUTED,
        True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--headless", action="store_true")

    parser.add_argument("--frames", type=int, default=0)

    parser.add_argument("--output", type=Path)

    args = parser.parse_args()

    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()

    screen = pygame.display.set_mode((1280, 720))

    pygame.display.set_caption("Warcraft Survivors — asset gallery")

    renderer = Renderer(load_content())

    clock = pygame.time.Clock()

    seconds = 0.0

    page, direction, state_index, rank = 0, 0, 0, 1

    sheet_page = 0

    paused = False

    running = True

    count = 0

    states = ("walk", "idle", "cast", "death")

    while running and (args.frames == 0 or count < args.frames):
        dt = clock.tick(60) / 1000

        seconds += 0 if paused else dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif pygame.K_1 <= event.key <= pygame.K_4:
                    page = event.key - pygame.K_1

                    sheet_page = 0

                elif event.key in (pygame.K_TAB, pygame.K_PAGEDOWN, pygame.K_PAGEUP):
                    total = (
                        math.ceil(len(renderer.assets.actors) / 9)
                        if page == 0
                        else math.ceil(
                            (
                                len(renderer.content.abilities)
                                + len(renderer.content.evolutions)
                                + len(renderer.content.manuals)
                            )
                            / 12
                        )
                        if page == 3
                        else 1
                    )

                    sheet_page = (sheet_page + (-1 if event.key == pygame.K_PAGEUP else 1)) % total

                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    direction = (direction + (1 if event.key == pygame.K_RIGHT else -1)) % 4

                elif event.key == pygame.K_a:
                    state_index = (state_index + 1) % 4

                elif event.key == pygame.K_r:
                    rank = rank % 8 + 1

                elif event.key == pygame.K_SPACE:
                    paused = not paused

        draw_gallery(renderer, page, direction, states[state_index], seconds, rank, sheet_page)

        screen.blit(renderer.canvas, (0, 0))

        pygame.display.flip()

        count += 1

    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)

        for page, name in enumerate(("actors", "effects", "environment")):
            draw_gallery(renderer, page, 0, "walk", 0.15, 6)

            pygame.image.save(renderer.canvas, str(args.output / f"{name}.png"))

    pygame.quit()


if __name__ == "__main__":
    main()
