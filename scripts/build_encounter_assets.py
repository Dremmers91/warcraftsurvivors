"""Original encounter atlases from preserved ImageGen sources; deterministic offline derivation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_assets import cells, fit
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/warcraft_survivors/assets"
SOURCE = ROOT / "art_sources/generated"


def tint(image, red=1, green=1, blue=1):
    image = image.copy()
    r, g, b, a = image.split()
    image = Image.merge(
        "RGBA",
        (
            r.point(lambda v: min(255, round(v * red))),
            g.point(lambda v: min(255, round(v * green))),
            b.point(lambda v: min(255, round(v * blue))),
            a,
        ),
    )
    return image


def atlas(name, poses, size=80, height=64, derived=False, decor=""):
    anchor = size - 7
    sheet = Image.new("RGBA", (size * 4, size * 16))
    for direction in range(4):
        walk = []
        for phase in range(4):
            sprite = fit(poses[direction][phase], size - 12, height)
            tile = Image.new("RGBA", (size, size))
            tile.alpha_composite(sprite, ((size - sprite.width) // 2, anchor - sprite.height))
            if derived:
                # Alternating lower-limb segments preserve actual pose differences
                # after trim, rather than translating the same idle silhouette.
                legs = tile.crop((0, anchor - 17, size, anchor))
                tile.paste((0, 0, 0, 0), (0, anchor - 17, size, anchor))
                shift = (-2, 0, 2, 1)[phase]
                tile.alpha_composite(legs.crop((0, 0, size // 2, 17)), (shift, anchor - 17))
                tile.alpha_composite(
                    legs.crop((size // 2, 0, size, 17)), (size // 2 - shift, anchor - 17)
                )
            d = ImageDraw.Draw(tile)
            if decor == "captain":
                d.polygon(
                    [(size - 22, 17), (size - 12, 11), (size - 5, 17), (size - 11, 27)],
                    fill=(199, 160, 60, 235),
                    outline=(74, 52, 25, 255),
                )
            elif decor == "marksman":
                d.arc((size - 26, 27, size - 8, 62), 270, 90, fill=(158, 112, 61), width=3)
                d.line((size - 17, 28, size - 17, 61), fill=(220, 207, 159), width=1)
            elif decor == "geomancer":
                d.polygon(
                    [(11, 21), (16, 15), (21, 21), (16, 27)],
                    fill=(111, 216, 248),
                    outline=(231, 244, 253),
                )
                d.line((16, 27, 16, 58), fill=(122, 88, 47), width=2)
            elif decor == "cutpurse":
                d.line((size - 20, 47, size - 10, 35), fill=(218, 227, 229), width=3)
            elif decor == "packlord":
                d.polygon(
                    [(24, 19), (29, 12), (32, 18), (36, 11), (42, 20)],
                    fill=(208, 170, 78),
                    outline=(87, 49, 39),
                )
            walk.append(tile)
            sheet.alpha_composite(tile, (phase * size, direction * size))
        for phase in range(4):
            idle = walk[0].copy()
            torso = idle.crop((0, 0, size, anchor - 18))
            idle.paste((0, 0, 0, 0), (0, 0, size, anchor - 18))
            idle.alpha_composite(torso, (0, (-1, 0, 1, 0)[phase]))
            sheet.alpha_composite(idle, (phase * size, (4 + direction) * size))
            casting = walk[(0, 1, 3, 2)[phase]].copy()
            glow = Image.new("RGBA", casting.size)
            d = ImageDraw.Draw(glow)
            if phase > 0:
                d.arc(
                    (8, 12, size - 8, anchor - 4),
                    180,
                    300,
                    fill=(255, 150, 69, 65 + phase * 25),
                    width=2,
                )
            casting.alpha_composite(glow)
            sheet.alpha_composite(casting, (phase * size, (8 + direction) * size))
            death = walk[0].rotate(phase * 17, resample=Image.Resampling.NEAREST)
            death.putalpha(
                death.getchannel("A").point(
                    lambda a, factor=(1, 0.85, 0.5, 0.12)[phase]: round(a * factor)
                )
            )
            sheet.alpha_composite(death, (phase * size, (12 + direction) * size))
    path = ASSETS / f"actors/{name}.png"
    sheet.save(path, optimize=True)
    return dict(
        file=f"actors/{name}.png",
        frame_size=[size, size],
        anchor=[size // 2, anchor],
        walk_fps=9,
        active=True,
    )


def main():
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    hogger = cells(Image.open(SOURCE / "hogger-walk.png"), 4, 4)
    manifest["actors"]["hogger"] = atlas("hogger", hogger, 120, 102)
    creatures = cells(Image.open(SOURCE / "elwynn-creatures.png"), 4, 5)
    for row, (name, height) in enumerate(
        [
            ("gnoll", 64),
            ("gnoll_shaman", 65),
            ("spider", 42),
            ("forest_boar", 48),
            ("forest_bear", 57),
        ]
    ):
        poses = [[creatures[row][direction] for _ in range(4)] for direction in range(4)]
        manifest["actors"][name] = atlas(name, poses, height=height, derived=True)
    gnoll = [
        [tint(creatures[0][direction], 1.18, 0.86, 0.82) for _ in range(4)]
        for direction in range(4)
    ]
    manifest["actors"]["gnoll_packlord"] = atlas("gnoll_packlord", gnoll, 96, 79, True, "packlord")
    spider = [
        [tint(creatures[2][direction], 0.88, 1.25, 0.75) for _ in range(4)]
        for direction in range(4)
    ]
    manifest["actors"]["broodmother"] = atlas("broodmother", spider, 104, 76, True)
    for name, base, decor, size, height, colors in [
        ("kobold_geomancer", "kobold", "geomancer", 80, 48, (1.05, 0.98, 1.2)),
        ("defias_cutpurse", "bandit", "cutpurse", 80, 53, (0.8, 0.89, 1.12)),
        ("defias_marksman", "bandit", "marksman", 80, 57, (0.94, 1.12, 0.86)),
        ("defias_captain", "bandit", "captain", 96, 74, (1.15, 0.83, 0.78)),
    ]:
        source = Image.open(ASSETS / f"actors/{base}.png")
        frames = cells(source, 4, 16)[:4]
        frames = [[tint(frame, *colors) for frame in row] for row in frames]
        manifest["actors"][name] = atlas(name, frames, size, height, decor=decor)
    for effect, color, shape in [
        ("hostile_arrow", (240, 161, 92), "arrow"),
        ("hostile_stone", (198, 169, 121), "stone"),
        ("hostile_poison", (152, 235, 80), "orb"),
        ("hostile_lightning", (121, 201, 255), "bolt"),
    ]:
        sheet = Image.new("RGBA", (32 * 4, 32))
        for phase in range(4):
            tile = Image.new("RGBA", (32, 32))
            d = ImageDraw.Draw(tile)
            if shape == "arrow":
                d.line((4, 26, 24, 6), fill=color, width=3)
                d.polygon([(18, 5), (28, 3), (26, 14)], fill=(245, 235, 185), outline=color)
            elif shape == "stone":
                d.polygon(
                    [(9, 7), (21, 5), (27, 15), (23, 25), (10, 26), (5, 16)],
                    fill=color,
                    outline=(68, 62, 47),
                )
                d.line((10, 9, 20, 8, 23, 13), fill=(236, 218, 173), width=2)
            elif shape == "bolt":
                d.line([(4, 27), (14, 17), (10, 11), (23, 13), (25, 4)], fill=color, width=4)
                d.line(
                    [(4, 27), (14, 17), (10, 11), (23, 13), (25, 4)], fill=(222, 246, 255), width=1
                )
            else:
                d.ellipse((7, 7, 25, 25), fill=(*color, 180), outline=(225, 251, 143), width=2)
                d.ellipse((11, 10, 17, 16), fill=(237, 253, 176))
            d.rectangle((phase + 3, phase + 4, phase + 4, phase + 5), fill=(*color, 160))
            sheet.alpha_composite(tile, (phase * 32, 0))
        sheet.save(ASSETS / f"effects/{effect}.png")
        manifest["effects"][effect] = dict(
            file=f"effects/{effect}.png", size=[32, 32], anchor=[16, 16], frames=4
        )
        manifest["projectiles"][effect] = dict(
            effect=effect, art_size=26, rank_scale=0, spin_degrees=0, active=True
        )
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.glob("*.png")}
    (ROOT / "art_sources/source_hashes.json").write_text(
        json.dumps(hashes, indent=2), encoding="utf-8"
    )
    print("Encounter actors and hostile projectiles built from original retained sources")


if __name__ == "__main__":
    main()
