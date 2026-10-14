"""Offline raster processing and original pixel textures. Never runs during gameplay."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "art_sources/generated"
OUTPUT = ROOT / "src/warcraft_survivors/assets"
FRAME = 80
ACTOR_HEIGHTS = {
    "paladin": 62,
    "warrior": 64,
    "mage": 63,
    "hunter": 60,
    "warlock": 63,
    "priest": 63,
    "kobold": 46,
    "wolf": 36,
    "bandit": 57,
}


def clear_alpha(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    # Generated sources can carry red RGB values under almost-transparent pixels.
    # Discard low-alpha fringes before resizing; preserve the actual visible colors.
    image.putalpha(image.getchannel("A").point(lambda value: 255 if value >= 100 else 0))
    return image


def fit(image: Image.Image, width: int, height: int) -> Image.Image:
    image = clear_alpha(image)
    box = image.getbbox()
    if box is None:
        raise ValueError("Empty source-art cell")
    image = image.crop(box)
    scale = min(width / image.width, height / image.height)
    image = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.BOX,
    )
    image.putalpha(image.getchannel("A").point(lambda value: 255 if value >= 100 else 0))
    return image


def forest_components(
    source: Image.Image, expected: int | None = 6
) -> list[tuple[tuple[int, int, int, int], Image.Image]]:
    """Separate complete transparent silhouettes instead of clipping guessed cells."""
    source = clear_alpha(source)
    width, height = source.size
    mask = bytearray(1 if alpha else 0 for alpha in source.getchannel("A").getdata())
    result = []
    for position in range(width * height):
        if not mask[position]:
            continue
        queue = deque([position])
        mask[position] = 0
        points = []
        left, top, right, bottom = width, height, 0, 0
        while queue:
            current = queue.popleft()
            y, x = divmod(current, width)
            points.append(current)
            left, top, right, bottom = min(left, x), min(top, y), max(right, x), max(bottom, y)
            neighbors = (
                current - width,
                current + width,
                current - 1 if x else -1,
                current + 1 if x < width - 1 else -1,
            )
            for neighbor in neighbors:
                if 0 <= neighbor < width * height and mask[neighbor]:
                    mask[neighbor] = 0
                    queue.append(neighbor)
        if len(points) < 1000:
            continue
        box = (left, top, right + 1, bottom + 1)
        image = source.crop(box)
        alpha = bytearray(image.width * image.height)
        for point in points:
            y, x = divmod(point, width)
            alpha[(y - top) * image.width + x - left] = 255
        image.putalpha(Image.frombytes("L", image.size, bytes(alpha)))
        result.append((box, image))
    if expected is not None and len(result) != expected:
        raise ValueError(f"Expected {expected} reviewed silhouettes, got {len(result)}")
    return result


def cells(source: Image.Image, columns: int, rows: int) -> list[list[Image.Image]]:
    return [
        [
            source.crop(
                (
                    round(x * source.width / columns),
                    round(y * source.height / rows),
                    round((x + 1) * source.width / columns),
                    round((y + 1) * source.height / rows),
                )
            )
            for x in range(columns)
        ]
        for y in range(rows)
    ]


def save(image: Image.Image, relative: str) -> None:
    path = OUTPUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def actor(name: str) -> None:
    source = Image.open(SOURCES / f"{name}.png")
    split = cells(source, 4, 4)
    sheet = Image.new("RGBA", (FRAME * 4, FRAME * 16))
    for direction in range(4):
        walk = []
        for phase in range(4):
            sprite = fit(split[direction][phase], 72, ACTOR_HEIGHTS[name])
            tile = Image.new("RGBA", (FRAME, FRAME))
            tile.alpha_composite(sprite, ((FRAME - sprite.width) // 2, 73 - sprite.height))
            walk.append(tile)
            sheet.alpha_composite(tile, (phase * FRAME, direction * FRAME))
        for phase in range(4):
            base = walk[0]
            # Idle frames gently compress/expand the torso rather than walking in place.
            idle = Image.new("RGBA", (FRAME, FRAME))
            body = base.crop((0, 0, FRAME, 59))
            bob = (0, -1, 0, 1)[phase]
            idle.alpha_composite(body, (0, bob))
            idle.alpha_composite(base.crop((0, 59, FRAME, FRAME)), (0, 59))
            sheet.alpha_composite(idle, (phase * FRAME, (4 + direction) * FRAME))
            cast = walk[(0, 1, 3, 0)[phase]].copy()
            glow = Image.new("RGBA", cast.size)
            gd = ImageDraw.Draw(glow)
            color = (245, 212, 107, 75) if name in ("paladin", "priest") else (112, 196, 240, 65)
            gd.line([(18, 36), (15, 28), (19, 22)], fill=color, width=2)
            cast.alpha_composite(glow)
            sheet.alpha_composite(cast, (phase * FRAME, (8 + direction) * FRAME))
            # Derived fall/fade animation; no physics or hit timing is changed.
            dying = fit(base, 65, ACTOR_HEIGHTS[name])
            dying = dying.rotate(
                (0, 18, 42, 65)[phase], resample=Image.Resampling.NEAREST, expand=True
            )
            dying.thumbnail((76, 70), Image.Resampling.NEAREST)
            dying.putalpha(
                dying.getchannel("A").point(
                    lambda a, factor=(1, 0.85, 0.5, 0.14)[phase]: round(a * factor)
                )
            )
            tile = Image.new("RGBA", (FRAME, FRAME))
            tile.alpha_composite(dying, ((FRAME - dying.width) // 2, 73 - dying.height))
            sheet.alpha_composite(tile, (phase * FRAME, (12 + direction) * FRAME))
    save(sheet, f"actors/{name}.png")
    if name == "paladin":
        save(sheet.crop((0, 0, 80, 80)), "images/fallback_actor.png")


def texture(seed: int, road: bool) -> Image.Image:
    rng = random.Random(seed)
    image = Image.new("RGBA", (32, 32))
    d = ImageDraw.Draw(image)
    palette = (
        [(92, 78, 53), (101, 86, 59), (110, 94, 66), (80, 72, 49)]
        if road
        else [(34, 52, 30), (42, 62, 34), (46, 65, 35), (38, 57, 31)]
    )
    for y in range(32):
        for x in range(32):
            image.putpixel((x, y), (*palette[rng.randrange(len(palette))], 255))
    for _ in range(70 if road else 115):
        x, y = rng.randrange(32), rng.randrange(32)
        if road:
            shade = rng.choice(((117, 102, 74), (70, 64, 45), (130, 116, 83)))
            d.line([(x, y), (x + rng.randrange(1, 4), y)], fill=shade)
        else:
            shade = rng.choice(((67, 84, 41), (56, 77, 39), (79, 89, 46), (29, 49, 27)))
            d.line([(x, y), (x - 1, y - rng.randrange(2, 5))], fill=shade)
            d.point((x - 2, y - 1), fill=shade)
    return image


def sun_decal(phase: int) -> Image.Image:
    image = Image.new("RGBA", (256, 256))
    d = ImageDraw.Draw(image)
    alpha = (94, 115, 100, 80)[phase]
    for radius in (108, 102, 82, 76):
        d.ellipse(
            (128 - radius, 128 - radius, 128 + radius, 128 + radius),
            outline=(224, 185, 85, alpha),
            width=1,
        )
    for i in range(16):
        angle = i * math.tau / 16
        points = [
            (128 + math.cos(angle + delta) * radius, 128 + math.sin(angle + delta) * radius)
            for radius, delta in ((87, 0), (98, -0.035), (110, 0), (98, 0.035))
        ]
        d.polygon(points, fill=(252, 222, 123, alpha + 15))
        a = angle + 0.12
        rune = [
            (128 + math.cos(a + delta) * radius, 128 + math.sin(a + delta) * radius)
            for radius, delta in ((86, 0), (94, 0), (91, 0.04), (95, 0.065))
        ]
        d.line(rune, fill=(254, 239, 173, alpha + 25), width=2)
    for count, radius, color in ((8, 62, (226, 185, 88, alpha)), (8, 40, (255, 231, 154, alpha))):
        points = [
            (
                128 + math.cos(i * math.tau / count + phase * 0.015) * radius,
                128 + math.sin(i * math.tau / count + phase * 0.015) * radius,
            )
            for i in range(count)
        ]
        for index in range(count):
            d.line([points[index], points[(index + 3) % count]], fill=color, width=1)
    d.polygon(
        [
            (128, 92),
            (135, 120),
            (164, 128),
            (135, 135),
            (128, 164),
            (120, 135),
            (92, 128),
            (120, 120),
        ],
        fill=(255, 237, 167, alpha + 20),
    )
    return image


def effect_sheet(name: str, frames: list[Image.Image]) -> None:
    sheet = Image.new("RGBA", (frames[0].width * len(frames), frames[0].height))
    for index, frame in enumerate(frames):
        sheet.alpha_composite(frame, (index * frame.width, 0))
    save(sheet, f"effects/{name}.png")


def generated_effects() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}

    def register(name: str, frames: list[Image.Image]) -> None:
        effect_sheet(name, frames)
        result[name] = {
            "file": f"effects/{name}.png",
            "size": list(frames[0].size),
            "frames": len(frames),
            "anchor": [frames[0].width // 2, frames[0].height // 2],
        }

    weapons = cells(Image.open(SOURCES / "holy_weapons.png"), 4, 2)
    for row, name in enumerate(("holy_hammer", "holy_shield")):
        frames = []
        for cell in weapons[row]:
            item = fit(cell, 44, 44)
            frame = Image.new("RGBA", (48, 48))
            frame.alpha_composite(item, ((48 - item.width) // 2, (48 - item.height) // 2))
            frames.append(frame)
        register(name, frames)
    register("consecration", [sun_decal(i) for i in range(4)])
    for name in ("frostbolt", "shadow_bolt"):
        frames = []
        for phase in range(4):
            frame = Image.new("RGBA", (48, 48))
            d = ImageDraw.Draw(frame)
            if name == "frostbolt":
                d.polygon(
                    [(5, 28), (34, 8), (42, 6), (37, 25), (18, 38)],
                    fill=(103, 189, 222, 255),
                    outline=(40, 81, 119, 255),
                )
                d.polygon([(12, 26), (42, 6), (25, 28), (18, 36)], fill=(201, 241, 249, 255))
                d.line([(13, 29), (25, 21), (31, 20), (39, 9)], fill=(247, 255, 255, 255), width=1)
                for offset in (0, 7, 14):
                    d.line(
                        [(4 + phase, 33 - offset // 3), (10 + phase, 29 - offset // 3)],
                        fill=(116, 203, 235, 145),
                        width=2,
                    )
            else:
                for i in range(6):
                    start = phase * 35 + i * 15
                    d.arc(
                        (7 + i, 7 + i, 40 - i, 40 - i),
                        start,
                        start + 205,
                        fill=(94 + i * 15, 47 + i * 8, 130 + i * 14, 220),
                        width=2,
                    )
                d.polygon(
                    [(12, 31), (27, 10), (36, 15), (33, 28), (19, 37)], fill=(44, 20, 76, 245)
                )
                d.line([(15, 30), (27, 15), (33, 17), (30, 28)], fill=(194, 134, 231, 220), width=2)
                d.line([(3, 39), (13, 31), (8, 23)], fill=(142, 91, 188, 140), width=3)
            frames.append(frame)
        register(name, frames)
    blizzard = []
    for phase in range(4):
        frame = Image.new("RGBA", (256, 256))
        d = ImageDraw.Draw(frame)
        d.ellipse((18, 18, 238, 238), fill=(40, 103, 147, 24), outline=(133, 213, 236, 95), width=2)
        rng = random.Random(78)
        for _ in range(36):
            x, y = rng.randrange(25, 231), rng.randrange(25, 231)
            if (x - 128) ** 2 + (y - 128) ** 2 > 95**2:
                continue
            y = (y + phase * 11) % 180 + 35
            d.polygon(
                [(x, y - 8), (x + 3, y - 2), (x, y + 3), (x - 3, y - 2)], fill=(189, 236, 251, 160)
            )
            d.line([(x + 2, y - 14), (x, y - 8)], fill=(98, 184, 223, 110), width=1)
        blizzard.append(frame)
    register("blizzard", blizzard)
    for name, color in (
        ("holy_impact", (255, 220, 119)),
        ("frost_impact", (131, 223, 253)),
        ("shadow_impact", (163, 113, 233)),
        ("summon", (110, 229, 127)),
    ):
        frames = []
        for phase in range(6):
            frame = Image.new("RGBA", (72, 72))
            d = ImageDraw.Draw(frame)
            radius = 9 + phase * 5
            for index in range(12):
                angle = index * math.tau / 12 + phase * 0.15
                inner, outer = radius * 0.5, radius
                d.line(
                    [
                        (36 + math.cos(angle) * inner, 36 + math.sin(angle) * inner),
                        (36 + math.cos(angle) * outer, 36 + math.sin(angle) * outer),
                    ],
                    fill=(*color, max(0, 255 - phase * 35)),
                    width=max(1, 4 - phase // 2),
                )
            if phase < 3:
                d.polygon(
                    [
                        (36, 36 - radius),
                        (40, 32),
                        (36 + radius, 36),
                        (40, 40),
                        (36, 36 + radius),
                        (32, 40),
                        (36 - radius, 36),
                        (32, 32),
                    ],
                    fill=(255, 249, 219, 220 - phase * 40),
                )
            frames.append(frame)
        register(name, frames)
    # Textured sweeping arcs, used in the art-only Divine Storm preview.
    storm = []
    for phase in range(6):
        frame = Image.new("RGBA", (192, 192))
        d = ImageDraw.Draw(frame)
        for inset, alpha in ((20, 110), (25, 185), (31, 70)):
            d.arc(
                (inset, inset, 192 - inset, 192 - inset),
                phase * 55,
                phase * 55 + 225,
                fill=(255, 221, 126, alpha),
                width=3,
            )
        storm.append(frame)
    register("divine_storm", storm)
    for name, color in (
        ("corruption", (169, 99, 213)),
        ("rend", (197, 70, 64)),
        ("poison", (107, 211, 99)),
        ("burn", (239, 124, 58)),
    ):
        frames = []
        for phase in range(4):
            frame = Image.new("RGBA", (24, 24))
            d = ImageDraw.Draw(frame)
            d.line(
                [(7, 3), (16, 6), (8, 12), (17, 18), (11, 22)],
                fill=(*color, 180 + phase * 15),
                width=2,
            )
            d.line([(4, 11), (20, 11)], fill=(*color, 180), width=1)
            frames.append(frame)
        register(name, frames)
    return result


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in ACTOR_HEIGHTS:
        if not (SOURCES / f"{name}.png").exists():
            raise FileNotFoundError(f"Required original sprite sheet missing: {name}")
        actor(name)
    images: dict[str, dict[str, object]] = {}

    def image(name: str, bitmap: Image.Image) -> None:
        save(bitmap, f"images/{name}.png")
        images[name] = {"file": f"images/{name}.png", "size": list(bitmap.size)}

    images["fallback_actor"] = {"file": "images/fallback_actor.png", "size": [80, 80]}
    for index in range(4):
        image(f"grass_{index}", texture(index + 31, False))
        image(f"road_{index}", texture(index + 61, True))
    forest = Image.open(SOURCES / "forest.png")
    parts = forest_components(forest)
    trees = sorted(
        (part for part in parts if part[0][1] < forest.height * 0.61), key=lambda part: part[0][0]
    )
    props = sorted(
        (part for part in parts if part[0][1] >= forest.height * 0.61), key=lambda part: part[0][0]
    )
    for index, (_, source) in enumerate(trees):
        sprite = fit(source, 150, 176)
        canvas = Image.new("RGBA", (160, 192))
        canvas.alpha_composite(sprite, ((160 - sprite.width) // 2, 180 - sprite.height))
        image(f"tree_{index}", canvas)
    for (_, source), name in zip(props, ("bush", "log", "rocks"), strict=True):
        sprite = fit(source, 64, 48)
        canvas = Image.new("RGBA", (72, 56))
        canvas.alpha_composite(sprite, ((72 - sprite.width) // 2, 52 - sprite.height))
        image(name, canvas)
    shadow = Image.new("RGBA", (42, 20))
    d = ImageDraw.Draw(shadow)
    for inset, alpha in ((0, 10), (2, 16), (4, 22), (7, 28)):
        d.ellipse((inset, inset // 2, 42 - inset, 19 - inset // 2), fill=(8, 12, 14, alpha))
    image("shadow", shadow)
    for name, color in (("xp", (80, 205, 233)), ("gold", (228, 184, 78))):
        frames = []
        for phase in range(4):
            frame = Image.new("RGBA", (20, 20))
            d = ImageDraw.Draw(frame)
            if name == "xp":
                d.polygon(
                    [(10, 2), (16, 7), (13, 16), (10, 18), (5, 12), (4, 7)],
                    fill=(*color, 255),
                    outline=(17, 63, 82, 255),
                )
                d.polygon([(10, 3), (12, 9), (10, 16), (6, 8)], fill=(154, 235, 251, 255))
                d.line([(10, 3), (15, 7), (12, 9)], fill=(225, 255, 254, 255), width=1)
            else:
                d.ellipse((3, 3, 17, 16), fill=(*color, 255), outline=(92, 66, 32, 255), width=2)
                d.line([(9, 6), (12, 7), (8, 11), (12, 13)], fill=(255, 232, 154, 255), width=1)
            d.line([(12 + phase % 2, 4), (14 + phase % 2, 4)], fill=(255, 255, 225, 255))
            frames.append(frame)
        effect_sheet(name, frames)
    effects = generated_effects()
    for name in ("xp", "gold"):
        effects[name] = {
            "file": f"effects/{name}.png",
            "size": [20, 20],
            "frames": 4,
            "anchor": [10, 10],
        }
    for name in ("spark_gold", "spark_frost", "spark_shadow"):
        color = {
            "spark_gold": (252, 216, 120),
            "spark_frost": (154, 231, 253),
            "spark_shadow": (181, 115, 223),
        }[name]
        sprite = Image.new("RGBA", (7, 7))
        d = ImageDraw.Draw(sprite)
        d.line([(3, 0), (3, 6)], fill=(*color, 180))
        d.line([(0, 3), (6, 3)], fill=(*color, 180))
        d.point((3, 3), fill=(255, 249, 222, 255))
        image(name, sprite)
    # Original etched UI material/icon rasters; generated once, not per draw.
    panel = Image.new("RGBA", (128, 128))
    rng = random.Random(45)
    for y in range(128):
        for x in range(128):
            noise = rng.randrange(-2, 3)
            panel.putpixel((x, y), (21 + noise, 31 + noise, 36 + noise, 246))
    image("panel_material", panel)
    for name, color in (
        ("might", (218, 154, 98)),
        ("area", (132, 190, 215)),
        ("projectiles", (235, 195, 104)),
        ("armor", (153, 172, 195)),
        ("health", (211, 108, 121)),
    ):
        icon = Image.new("RGBA", (32, 32))
        d = ImageDraw.Draw(icon)
        if name == "might":
            d.polygon(
                [(5, 22), (20, 5), (25, 5), (25, 10), (10, 26)],
                fill=(*color, 255),
                outline=(61, 52, 48),
            )
            d.line([(5, 18), (15, 28)], fill=(243, 224, 164), width=3)
        elif name == "armor":
            d.polygon(
                [(5, 6), (16, 3), (27, 6), (25, 20), (16, 29), (7, 20)],
                fill=(*color, 255),
                outline=(41, 53, 65),
            )
            d.line([(16, 5), (16, 25)], fill=(241, 229, 180), width=2)
        elif name == "health":
            d.polygon(
                [(16, 27), (4, 15), (4, 7), (10, 4), (16, 9), (22, 4), (28, 7), (28, 15)],
                fill=(*color, 255),
                outline=(88, 39, 48),
            )
            d.line([(7, 9), (10, 7), (13, 11)], fill=(255, 171, 170), width=2)
        else:
            for offset in (-8, 0, 8) if name == "projectiles" else (0,):
                d.polygon(
                    [
                        (16 + offset, 3),
                        (19 + offset, 12),
                        (26 + offset, 16),
                        (19 + offset, 20),
                        (16 + offset, 29),
                        (13 + offset, 20),
                        (6 + offset, 16),
                        (13 + offset, 12),
                    ],
                    fill=(*color, 255),
                    outline=(62, 71, 70),
                )
        image(f"icon_{name}", icon)
    manifest = {
        "version": 1,
        "actors": {
            name: {
                "file": f"actors/{name}.png",
                "frame_size": [80, 80],
                "anchor": [40, 73],
                "walk_fps": 10 if name == "wolf" else 9,
                "active": name in ("paladin", "kobold", "wolf", "bandit"),
            }
            for name in ACTOR_HEIGHTS
        },
        "images": images,
        "effects": effects,
        "projectiles": {
            "judgment": {
                "effect": "holy_hammer",
                "art_size": 38,
                "rank_scale": 0.025,
                "spin_degrees": 90,
                "trail": "spark_gold",
                "active": True,
            },
            "blessed_hammer": {"effect": "holy_hammer", "art_size": 38, "rank_scale": 0.025},
            "avengers_shield": {"effect": "holy_shield", "art_size": 40, "rank_scale": 0.02},
        },
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), "utf-8")
    provenance = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in SOURCES.glob("*.png")
    }
    (ROOT / "art_sources/source_hashes.json").write_text(json.dumps(provenance, indent=2), "utf-8")
    print(
        f"Built {len(ACTOR_HEIGHTS)} directional actor atlases, {len(images)} images and {len(effects)} effect sheets"
    )


if __name__ == "__main__":
    main()
    from build_ability_assets import main as build_abilities

    build_abilities()
    from build_encounter_assets import main as build_encounters

    build_encounters()
    from build_milestone5_assets import main as build_expansion

    build_expansion()
