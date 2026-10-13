"""Original offline pixel effects and demon atlases for the full ability catalog."""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/warcraft_survivors/assets"
COLORS = {
    "holy": (255, 218, 110),
    "physical": (202, 208, 216),
    "fire": (255, 120, 47),
    "frost": (105, 224, 255),
    "arcane": (212, 128, 255),
    "shadow": (168, 99, 225),
    "nature": (119, 218, 94),
}


def glow(color, factor):
    return tuple(min(255, round(c * factor)) for c in color)


def effect(aid, kind, school, evolved=False):
    color = COLORS[school]
    seed = int.from_bytes(hashlib.sha256(aid.encode()).digest()[:4], "little")
    size = 48 if kind in {"projectile", "orbit", "dot"} else 160
    frames = []
    for phase in range(4):
        rng = random.Random(seed + phase)
        im = Image.new("RGBA", (48, 48))
        d = ImageDraw.Draw(im)
        dark = (*glow(color, 0.42), 255)
        bright = (*glow(color, 1.3), 255)
        base = (*color, 255)
        aura = (*color, 80)
        for _ in range(13 + phase * 2):
            x, y = rng.randrange(5, 43), rng.randrange(5, 43)
            d.rectangle((x, y, x + 1, y + 1), fill=(*color, rng.randrange(70, 200)))
        if kind in {"projectile", "orbit"}:
            if any(w in aid for w in ("hammer", "judgment")):
                d.polygon([(13, 34), (16, 37), (34, 15), (31, 12)], fill=dark, outline=bright)
                d.polygon(
                    [(24, 8), (35, 6), (42, 14), (40, 23), (31, 26), (22, 18)],
                    fill=base,
                    outline=dark,
                )
                d.line((25, 11, 34, 9, 39, 15), fill=bright, width=2)
                d.line((27, 18, 35, 13, 37, 20), fill=(255, 255, 222), width=1)
            elif "shield" in aid:
                d.polygon(
                    [(10, 9), (37, 9), (39, 27), (24, 41), (9, 27)], fill=dark, outline=bright
                )
                d.polygon([(14, 13), (33, 13), (34, 26), (24, 35), (14, 26)], fill=base)
                d.line((24, 13, 24, 33), fill=bright, width=3)
                d.line((15, 21, 32, 21), fill=bright, width=3)
            elif (
                any(w in aid for w in ("shot", "fire", "barrage", "lance", "smite", "penance"))
                and "ball" not in aid
                and "pyro" not in aid
            ):
                d.polygon(
                    [(8, 36), (29, 15), (27, 11), (42, 6), (37, 22), (33, 18), (12, 39)],
                    fill=dark,
                    outline=base,
                )
                d.line((10, 36, 36, 11), fill=bright, width=2)
                d.polygon([(8, 31), (15, 32), (16, 39), (8, 40)], fill=base)
            elif "throw" in aid:
                d.polygon([(9, 36), (12, 39), (35, 12), (32, 9)], fill=base, outline=dark)
                d.polygon(
                    [(24, 9), (31, 6), (42, 7), (40, 22), (34, 27), (29, 18)],
                    fill=bright,
                    outline=dark,
                )
            elif "star" in aid or "ashes" in aid:
                points = []
                for i in range(10):
                    angle = i * math.pi / 5 + phase * 0.07
                    r = 18 if i % 2 == 0 else 7
                    points.append((24 + math.cos(angle) * r, 24 + math.sin(angle) * r))
                d.polygon(points, fill=base, outline=bright)
                d.polygon([(24, 15), (31, 24), (24, 33), (17, 24)], fill=bright)
            else:
                # Bolts have layered jagged silhouettes and differently oriented cores.
                d.polygon(
                    [
                        (4, 40),
                        (13, 22),
                        (16, 27),
                        (21, 10),
                        (30, 7),
                        (39, 11),
                        (42, 21),
                        (30, 30),
                        (25, 28),
                        (11, 42),
                    ],
                    fill=aura,
                )
                d.polygon(
                    [
                        (9, 36),
                        (17, 23),
                        (20, 25),
                        (23, 13),
                        (32, 10),
                        (39, 16),
                        (35, 25),
                        (27, 28),
                        (24, 25),
                    ],
                    fill=dark,
                    outline=base,
                )
                d.polygon([(23, 16), (31, 12), (36, 18), (30, 25), (25, 22)], fill=bright)
                d.line((15, 32, 29, 18), fill=base, width=2)
        elif kind == "dot":
            # Status sigils are visible crowns/brands, not anonymous dots.
            d.polygon(
                [(12, 33), (10, 14), (19, 23), (24, 9), (29, 23), (38, 14), (36, 33)],
                fill=dark,
                outline=bright,
            )
            for i in range(3):
                d.rectangle((16 + i * 7, 28, 18 + i * 7, 35), fill=base)
            d.line((13, 38, 35, 38), fill=base, width=2)
        elif kind in {"arc", "area", "wave"}:
            for offset in (0, 3, 6):
                d.arc(
                    (4 + offset, 4 + offset, 44 - offset, 44 - offset),
                    200 + phase * 8,
                    350 + phase * 8,
                    fill=(*color, 210 - offset * 13),
                    width=2,
                )
            # A specific steel/holy weapon in each sweep.
            center = (seed % 7) + 17
            d.polygon([(13, 34), (16, 37), (36, 14), (35, 7), (29, 9)], fill=dark, outline=bright)
            d.line((center, 29, 34, 14), fill=base, width=2)
            d.polygon([(8, 31), (16, 39), (20, 36), (11, 28)], fill=base)
        elif kind == "beam" or kind == "chain":
            points = [(5, 38), (16, 27), (14, 21), (28, 23), (25, 12), (40, 7)]
            d.line(points, fill=dark, width=7)
            d.line(points, fill=base, width=4)
            d.line(points, fill=bright, width=1)
        elif kind in {"companion", "charge"}:
            d.polygon(
                [
                    (6, 30),
                    (10, 13),
                    (17, 24),
                    (23, 8),
                    (30, 24),
                    (39, 14),
                    (42, 31),
                    (34, 38),
                    (13, 38),
                ],
                fill=dark,
                outline=base,
            )
            d.rectangle((15, 27, 19, 30), fill=bright)
            d.rectangle((29, 27, 33, 30), fill=bright)
            d.polygon([(22, 33), (27, 33), (24, 38)], fill=bright)
        else:
            # Rune fields vary by school, spell seed, glyph count and particle layout.
            d.ellipse((4, 4, 44, 44), outline=(*color, 150), width=2)
            d.ellipse((8, 8, 40, 40), outline=dark, width=2)
            points = []
            count = 3 + seed % 5
            for i in range(count):
                ang = i * math.tau / count + phase * 0.035
                points.append((24 + math.cos(ang) * 14, 24 + math.sin(ang) * 14))
            d.line(points + [points[0]], fill=base, width=1)
            if school == "fire":
                for x in (15, 23, 31):
                    d.polygon(
                        [
                            (x - 4, 30),
                            (x - 5, 24),
                            (x, 12 + phase),
                            (x + 2, 23),
                            (x + 5, 20),
                            (x + 5, 30),
                        ],
                        fill=base,
                        outline=bright,
                    )
            elif school == "frost":
                for ang in range(0, 360, 60):
                    x = 24 + math.cos(math.radians(ang)) * 12
                    y = 24 + math.sin(math.radians(ang)) * 12
                    d.line((24, 24, x, y), fill=bright, width=2)
            else:
                d.polygon([(24, 12), (33, 24), (24, 36), (15, 24)], fill=dark, outline=bright)
                d.line((20, 24, 28, 24), fill=base, width=2)
        # Each ability's central rune encodes a unique visible constellation.
        for i in range(6):
            if seed & (1 << i):
                d.rectangle(
                    (17 + i * 2, 22 + (i % 2) * 3, 18 + i * 2, 23 + (i % 2) * 3),
                    fill=(255, 255, 235, 255),
                )
        if evolved:
            for x, y in ((7, 7), (40, 7), (7, 40), (40, 40)):
                d.line((x - 2, y, x + 2, y), fill=(255, 255, 229), width=1)
                d.line((x, y - 2, x, y + 2), fill=(255, 255, 229), width=1)
            d.ellipse((2, 2, 46, 46), outline=(*color, 130), width=1)
        frames.append(im.resize((size, size), Image.Resampling.NEAREST))
    sheet = Image.new("RGBA", (size * 4, size))
    for i, frame in enumerate(frames):
        sheet.paste(frame, (i * size, 0))
    sheet.save(ASSETS / f"effects/{aid}.png")
    return dict(
        file=f"effects/{aid}.png", size=[size, size], anchor=[size // 2, size // 2], frames=4
    )


def demon(name, color, small=False):
    sheet = Image.new("RGBA", (320, 1280))
    for state in range(4):
        for direction in range(4):
            for phase in range(4):
                tile = Image.new("RGBA", (80, 80))
                d = ImageDraw.Draw(tile)
                bob = phase % 2
                lean = (phase - 1) * 2 if state == 2 else 0
                cx = 40 + lean + (direction - 1)
                dark = glow(color, 0.35)
                light = glow(color, 1.5)
                foot = 70
                if small:
                    foot = 65
                height = 28 if small else 48
                top = foot - height + bob
                # Muscle plates, boots, articulated limbs, horns, glowing eyes and cleaver.
                d.polygon(
                    [
                        (cx - 13, top + 15),
                        (cx + 13, top + 15),
                        (cx + 11, foot - 13),
                        (cx - 10, foot - 13),
                    ],
                    fill=color,
                    outline=dark,
                )
                d.rectangle((cx - 9, top + 15, cx - 2, top + 24), fill=light)
                d.rectangle((cx + 3, top + 15, cx + 10, top + 24), fill=dark)
                for side in (-1, 1):
                    step = ((phase + (0 if side < 0 else 2)) % 4 - 1) * 2
                    d.polygon(
                        [
                            (cx + side * 5, foot - 14),
                            (cx + side * 12, foot - 13),
                            (cx + side * 13 + step, foot - 2),
                            (cx + side * 3 + step, foot - 2),
                        ],
                        fill=dark,
                        outline=color,
                    )
                    d.rectangle(
                        (cx + side * 8 - 4 + step, foot - 6, cx + side * 8 + 5 + step, foot),
                        fill=(49, 42, 65),
                    )
                    d.polygon(
                        [
                            (cx + side * 11, top + 16),
                            (cx + side * 20, top + 18),
                            (cx + side * 22, top + 32),
                            (cx + side * 14, top + 32),
                        ],
                        fill=color,
                        outline=dark,
                    )
                d.ellipse((cx - 9, top + 1, cx + 9, top + 17), fill=color, outline=dark)
                d.polygon(
                    [(cx - 8, top + 5), (cx - 15, top - 4), (cx - 10, top - 2), (cx - 4, top + 4)],
                    fill=(184, 167, 146),
                    outline=dark,
                )
                d.polygon(
                    [(cx + 8, top + 5), (cx + 15, top - 4), (cx + 10, top - 2), (cx + 4, top + 4)],
                    fill=(184, 167, 146),
                    outline=dark,
                )
                # Directional armor/cape details survive frame trimming.
                if direction == 0:
                    d.line((cx - 7, top + 18, cx + 7, top + 27), fill=(202, 158, 103), width=3)
                elif direction == 1:
                    d.polygon(
                        [(cx - 11, top + 15), (cx - 16, top + 31), (cx - 8, top + 33)],
                        fill=(61, 40, 87),
                        outline=light,
                    )
                elif direction == 3:
                    d.polygon(
                        [(cx + 11, top + 15), (cx + 16, top + 31), (cx + 8, top + 33)],
                        fill=(61, 40, 87),
                        outline=light,
                    )
                else:
                    d.rectangle(
                        (cx - 7, top + 18, cx + 7, top + 29), fill=(65, 40, 92), outline=light
                    )
                if direction != 2:
                    d.rectangle((cx - 6, top + 8, cx - 2, top + 10), fill=(168, 255, 81))
                    d.rectangle((cx + 2, top + 8, cx + 6, top + 10), fill=(168, 255, 81))
                    d.line((cx - 4, top + 14, cx + 4, top + 14), fill=(231, 216, 171), width=2)
                else:
                    d.rectangle((cx - 5, top + 5, cx + 5, top + 13), fill=dark)
                if not small:
                    d.line((cx + 20, top + 25, cx + 24, foot - 8), fill=(166, 137, 83), width=3)
                    d.polygon(
                        [
                            (cx + 20, top + 24),
                            (cx + 19, top + 14),
                            (cx + 33, top + 10),
                            (cx + 31, top + 26),
                        ],
                        fill=(151, 157, 176),
                        outline=(59, 48, 75),
                    )
                    d.line((cx + 22, top + 16, cx + 30, top + 13), fill=(235, 227, 189), width=2)
                if state == 3:
                    tile.putalpha(
                        tile.getchannel("A").point(
                            lambda a, fade=phase: round(a * (1 - fade * 0.24))
                        )
                    )
                sheet.paste(tile, (phase * 80, (state * 4 + direction) * 80))
    sheet.save(ASSETS / f"actors/{name}.png")
    return dict(file=f"actors/{name}.png", frame_size=[80, 80], anchor=[40, 73], walk_fps=9)


def main():
    manifest = json.loads((ASSETS / "manifest.json").read_text("utf-8"))
    data = json.loads((ROOT / "src/warcraft_survivors/data/content.json").read_text("utf-8"))
    for a in data["abilities"]:
        aid = a["id"]
        native = {
            "judgment": "holy_hammer",
            "blessed_hammer": "holy_hammer",
            "avenger_s_shield": "holy_shield",
            "consecration": "consecration",
            "frostbolt": "frostbolt",
            "shadow_bolt": "shadow_bolt",
            "blizzard": "blizzard",
            "divine_storm": "divine_storm",
        }.get(aid)
        manifest["effects"][aid] = (
            manifest["effects"][native].copy()
            if native in manifest["effects"]
            else effect(aid, a["kind"], a["school"])
        )
        evo = a["evolution"]
        manifest["effects"][evo["id"]] = effect(evo["id"], evo["kind"], a["school"], True)
        for key, kind in ((aid, a["kind"]), (evo["id"], evo["kind"])):
            if kind in {"projectile", "orbit"}:
                manifest["projectiles"][key] = dict(
                    effect=key,
                    art_size=38 if a["school"] in {"holy", "fire"} else 32,
                    rank_scale=0,
                    spin_degrees=90 if "hammer" in aid or "throw" in aid else 0,
                    trail="spark_"
                    + (
                        "frost"
                        if a["school"] == "frost"
                        else "shadow"
                        if a["school"] in {"shadow", "arcane"}
                        else "gold"
                    ),
                    active=True,
                )
        if aid == "judgment":
            manifest["projectiles"][aid].update(
                effect="holy_hammer", art_size=38, rank_scale=0.025, spin_degrees=90
            )
    for m in data["manuals"]:
        manifest["effects"][m["id"]] = effect(m["id"], "field", m["school"])
    for name, color, small in [
        ("felguard", (120, 69, 128), False),
        ("dreadguard", (104, 43, 164), False),
        ("imp", (147, 71, 84), True),
    ]:
        manifest["actors"][name] = demon(name, color, small)
    manifest["actors"]["alpha_wolf"] = manifest["actors"]["wolf"].copy()
    # Bright transformed wolf, keeping the original authored directional poses.
    wolf = Image.open(ASSETS / "actors/wolf.png").convert("RGBA")
    pixels = wolf.load()
    for y in range(wolf.height):
        for x in range(wolf.width):
            r, g, b, alpha = pixels[x, y]
            if alpha:
                pixels[x, y] = (min(255, r + 30), min(255, g + 38), min(255, b + 52), alpha)
    wolf.save(ASSETS / "actors/alpha_wolf.png")
    manifest["actors"]["alpha_wolf"]["file"] = "actors/alpha_wolf.png"
    for p in data["passives"]:
        if "icon_" + p["id"] in manifest["images"]:
            continue
        icon = Image.new("RGBA", (32, 32))
        d = ImageDraw.Draw(icon)
        d.rounded_rectangle((1, 1, 30, 30), 4, fill=(34, 42, 55), outline=(224, 186, 108), width=2)
        seed = int.from_bytes(hashlib.sha256(p["id"].encode()).digest()[:2], "little")
        for i in range(5):
            x = 6 + i * 4
            d.line((x, 25, x, 7 + (seed >> i) % 12), fill=(118, 210, 226), width=2)
        icon.save(ASSETS / f"images/icon_{p['id']}.png")
        manifest["images"]["icon_" + p["id"]] = dict(
            file=f"images/icon_{p['id']}.png", size=[32, 32]
        )
    chest = Image.new("RGBA", (40, 36))
    d = ImageDraw.Draw(chest)
    d.rounded_rectangle((3, 8, 36, 32), 4, fill=(94, 59, 37), outline=(236, 186, 85), width=3)
    d.rectangle((4, 18, 35, 21), fill=(221, 164, 68))
    d.rectangle((17, 15, 22, 25), fill=(255, 219, 108))
    chest.save(ASSETS / "images/chest.png")
    manifest["images"]["chest"] = dict(file="images/chest.png", size=[40, 36])
    for reward, source in (("heal", "health"), ("power", "might")):
        manifest["images"]["icon_" + reward] = manifest["images"]["icon_" + source].copy()
    manifest["images"]["icon_gold"] = manifest["images"]["chest"].copy()
    manifest["directional_effects"] = [a["id"] for a in data["abilities"] if a["kind"] == "arc"] + [
        a["evolution"]["id"] for a in data["abilities"] if a["evolution"]["kind"] == "arc"
    ]
    for actor in manifest["actors"].values():
        actor["active"] = True
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    print("Catalog effects, manual icons, chest and original demon atlases built")


if __name__ == "__main__":
    main()
