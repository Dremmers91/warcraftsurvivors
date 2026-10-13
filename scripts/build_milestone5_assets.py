"""Reproducible offline processing of retained original M5 art sources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_assets import cells, fit
from build_encounter_assets import atlas, tint
from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art_sources/milestone5"
ASSETS = ROOT / "src/warcraft_survivors/assets"


def main():
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    zones = json.loads(
        (ROOT / "src/warcraft_survivors/data/zones.json").read_text(encoding="utf-8")
    )
    for name in ("stitches", "bangalash", "rivendare", "lich_king"):
        poses = cells(Image.open(SOURCE / f"{name}.png"), 4, 4)
        manifest["actors"][name] = atlas(
            name, poses, 136 if name == "stitches" else 128, 112 if name == "stitches" else 104
        )
    creature = cells(Image.open(SOURCE / "enemies.png"), 4, 8)
    # Alternate palettes share a recognizable species while retaining class/zone silhouettes.
    species = {
        "duskwood": [
            (0, None, (1, 1, 1)),
            (1, None, (1, 1, 1)),
            (None, "wolf", (0.85, 0.75, 1.1)),
            (None, "spider", (0.85, 0.75, 1.2)),
            (5, None, (1, 1, 1)),
        ],
        "stranglethorn": [
            (2, None, (1, 1, 1)),
            (3, None, (1, 1, 1)),
            (None, "bangalash", (0.35, 0.4, 0.45)),
            (None, "forest_boar", (0.9, 1.18, 0.85)),
            (5, None, (0.75, 1.25, 0.7)),
        ],
        "plaguelands": [
            (4, None, (0.85, 1.12, 0.8)),
            (5, None, (1, 0.85, 1.15)),
            (None, "wolf", (0.8, 1.15, 0.7)),
            (None, "spider", (0.8, 1.15, 0.8)),
            (1, None, (0.8, 0.9, 0.8)),
        ],
        "icecrown": [
            (7, None, (1, 1, 1)),
            (6, None, (1, 1, 1)),
            (None, "wolf", (0.85, 1.2, 1.4)),
            (5, None, (0.7, 1.05, 1.45)),
            (None, "stitches", (0.6, 0.9, 1.2)),
        ],
    }
    for zone in zones["zones"][1:]:
        for eid, (row, base, color) in zip(zone["enemies"], species[zone["id"]], strict=True):
            if row is not None:
                poses = [[tint(creature[row][d], *color) for _ in range(4)] for d in range(4)]
                derived = True
            else:
                poses = [
                    [tint(p, *color) for p in line]
                    for line in cells(Image.open(ASSETS / manifest["actors"][base]["file"]), 4, 16)[
                        :4
                    ]
                ]
                derived = False
            height = (
                40 if any(v in eid for v in ("wolf", "hound", "panther", "spider", "fiend")) else 64
            )
            manifest["actors"][eid] = atlas(eid, poses, height=height, derived=derived)
        for elite_id in zone["elites"]:
            definition = next(e for e in zones["elites"] if e["id"] == elite_id)
            source = Image.open(ASSETS / manifest["actors"][definition["enemy"]]["file"])
            poses = [[tint(p, 1.18, 0.88, 1.12) for p in line] for line in cells(source, 4, 16)[:4]]
            manifest["actors"][elite_id] = atlas(elite_id, poses, 104, 82, decor="captain")
    pets = cells(Image.open(SOURCE / "companions.png"), 4, 3)
    for row, name in enumerate(("felguard", "dreadguard", "imp")):
        manifest["actors"][name] = atlas(
            name,
            [[pets[row][d] for _ in range(4)] for d in range(4)],
            height=48 if name == "imp" else 66,
            derived=True,
        )
    props = cells(Image.open(SOURCE / "environment.png"), 4, 4)
    textures = cells(Image.open(SOURCE / "terrain.png"), 4, 2)
    for index, zone in enumerate(zones["zones"][1:]):
        for style in range(4):
            image = Image.new("RGBA", (192, 224))
            obj = fit(props[index][style], 184, 208)
            image.alpha_composite(obj, ((192 - obj.width) // 2, 214 - obj.height))
            name = zone["props"][style]
            image.save(ASSETS / f"images/{name}.png", optimize=True)
            manifest["images"][name] = dict(file=f"images/{name}.png", size=[192, 224])
        for row, key in enumerate(("ground", "road")):
            name = zone[key]
            tile = textures[row][index].convert("RGB").resize((64, 64), Image.Resampling.BOX)
            tile = ImageEnhance.Contrast(tile).enhance(0.45 if zone["id"] == "icecrown" else 0.65)
            tile = ImageEnhance.Brightness(tile).enhance(0.75 if zone["id"] == "icecrown" else 0.9)
            tile.convert("RGBA").save(ASSETS / f"images/{name}.png")
            manifest["images"][name] = dict(file=f"images/{name}.png", size=[64, 64])
    effects = cells(Image.open(SOURCE / "effects.png"), 6, 3)
    elwynn = cells(Image.open(SOURCE / "elwynn.png"), 3, 1)[0]
    for source, name in zip(elwynn, ("elwynn_inn", "elwynn_mill", "elwynn_bridge"), strict=True):
        image = Image.new("RGBA", (224, 224))
        obj = fit(source, 216, 208)
        image.alpha_composite(obj, ((224 - obj.width) // 2, 214 - obj.height))
        image.save(ASSETS / f"images/{name}.png", optimize=True)
        manifest["images"][name] = dict(file=f"images/{name}.png", size=[224, 224])
    raw = json.loads(
        (ROOT / "src/warcraft_survivors/data/content.json").read_text(encoding="utf-8")
    )
    schools = ["holy", "frost", "arcane", "fire", "shadow", "physical"]
    definitions = []
    for a in raw["abilities"]:
        definitions.append((a["id"], a["kind"], a["school"], False))
        if a.get("evolution"):
            definitions.append((a["evolution"]["id"], a["evolution"]["kind"], a["school"], True))
    # Keep shaped shields, axes, arrows, stars, orbiting weapons and companion symbols.
    for name, kind, school, evolved in definitions:
        if school not in schools or name not in manifest["effects"]:
            continue
        if (
            kind in {"companion", "orbit", "dot", "beam", "chain", "charge"}
            or (school == "physical")
            or (
                school == "holy"
                and not any(w in name for w in ("judgment", "hammer", "consecration"))
            )
        ):
            continue
        source_row = 0 if kind == "projectile" else 2 if kind == "field" else 1
        spec = manifest["effects"][name]
        size = spec["size"][0]
        bitmap = fit(effects[source_row][schools.index(school)], size - 4, size - 4)
        seed = int.from_bytes(hashlib.sha256(name.encode()).digest()[:2], "little")
        if school != "holy":
            bitmap = tint(
                bitmap,
                1 + (seed % 9 - 4) / 40,
                1 + ((seed // 9) % 9 - 4) / 40,
                1 + ((seed // 81) % 9 - 4) / 40,
            )
        sheet = Image.new("RGBA", (size * spec["frames"], size))
        for phase in range(spec["frames"]):
            scale = (
                (0.8, 0.92, 1, 0.94)[phase % 4]
                if source_row != 0
                else (1, 0.94, 0.98, 0.91)[phase % 4]
            )
            obj = bitmap.resize(
                (round(bitmap.width * scale), round(bitmap.height * scale)),
                Image.Resampling.NEAREST,
            )
            if source_row == 2:
                obj.putalpha(
                    obj.getchannel("A").point(
                        lambda a, factor=0.55 if evolved else 0.4: round(a * factor)
                    )
                )
            tile = Image.new("RGBA", (size, size))
            tile.alpha_composite(obj, ((size - obj.width) // 2, (size - obj.height) // 2))
            if evolved:
                ImageDraw.Draw(tile).arc(
                    (3, 3, size - 4, size - 4),
                    phase * 35,
                    phase * 35 + 260,
                    fill=(245, 231, 205, 145),
                    width=2,
                )
            sheet.alpha_composite(tile, (phase * size, 0))
        sheet.save(ASSETS / spec["file"], optimize=True)
    for name, school in (
        ("hostile_frost", "frost"),
        ("hostile_shadow", "shadow"),
        ("hostile_hook", "physical"),
    ):
        size = 40
        obj = fit(effects[0][schools.index(school)], size - 4, size - 4)
        sheet = Image.new("RGBA", (size * 4, size))
        for phase in range(4):
            sheet.alpha_composite(
                obj, (phase * size + (size - obj.width) // 2, (size - obj.height) // 2)
            )
        sheet.save(ASSETS / f"effects/{name}.png")
        manifest["effects"][name] = dict(
            file=f"effects/{name}.png", size=[size, size], anchor=[20, 20], frames=4
        )
        manifest["projectiles"][name] = dict(
            effect=name, art_size=30, rank_scale=0, spin_degrees=0, active=True
        )
    for name, school, color in (
        ("hostile_poison_field", "shadow", (0.55, 1.65, 0.4)),
        ("hostile_frost_field", "frost", (1, 1, 1)),
        ("hostile_shadow_field", "shadow", (1, 1, 1)),
    ):
        size = 160
        obj = tint(fit(effects[2][schools.index(school)], 152, 152), *color)
        sheet = Image.new("RGBA", (size * 4, size))
        for phase in range(4):
            tile = obj.copy()
            tile.putalpha(
                tile.getchannel("A").point(
                    lambda a, factor=(0.3, 0.4, 0.35, 0.4)[phase]: round(a * factor)
                )
            )
            sheet.alpha_composite(
                tile, (phase * size + (size - tile.width) // 2, (size - tile.height) // 2)
            )
        sheet.save(ASSETS / f"effects/{name}.png")
        manifest["effects"][name] = dict(
            file=f"effects/{name}.png", size=[size, size], anchor=[80, 80], frames=4
        )
    icon = Image.new("RGBA", (256, 256), (13, 25, 34, 255))
    d = ImageDraw.Draw(icon)
    d.rounded_rectangle(
        (6, 6, 249, 249), radius=38, fill=(23, 41, 50), outline=(222, 186, 115), width=7
    )
    obj = fit(effects[0][0], 230, 230)
    icon.alpha_composite(obj, ((256 - obj.width) // 2, (256 - obj.height) // 2))
    icon.save(ASSETS / "game_icon.png")
    icon.save(ASSETS / "game_icon.ico", sizes=[(v, v) for v in (16, 24, 32, 48, 64, 128, 256)])
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (SOURCE / "hashes.json").write_text(
        json.dumps(
            {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.glob("*.png")},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Built {len(manifest['actors'])} actor definitions, zone terrain/landmarks, original spell effects and Windows icon"
    )


if __name__ == "__main__":
    main()
