"""Pack preserved original creature cutouts; no generative art at runtime."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_assets import forest_components
from build_encounter_assets import atlas
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art_sources/enemy_balance"
ASSETS = ROOT / "src/warcraft_survivors/assets"
DESIGNS = {
    "duskwood": [("restless_spirit", 62), ("worgen", 64), ("skeletal_archer", 60), ("elite_2", 83)],
    "stranglethorn": [("gorilla", 57), ("basilisk", 47), ("crocolisk", 40), ("elite_2", 82)],
    "plaguelands": [("banshee", 63), ("gargoyle", 53), ("abomination", 67), ("elite_2", 84)],
    "icecrown": [("nerubian", 61), ("frost_revenant", 63), ("wyrm_hatchling", 48), ("elite_2", 83)],
}


def main() -> None:
    manifest_path = ASSETS / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    provenance = {}
    for zone, designs in DESIGNS.items():
        path = SOURCE / f"{zone}.png"
        # Sources have generous alpha gaps but irregular row heights/long tails.
        # Connected silhouettes prevent guessed grid boundaries clipping heads.
        source = Image.open(path)
        if zone == "icecrown":
            # Ice revenants intentionally have detached floating shards. Keep
            # those parts together using reviewed alpha-safe cell rectangles.
            cutouts = [
                item
                for item in forest_components(source, expected=None)
                if item[0][3] <= 280 or item[0][1] >= 640
            ]
            for left, right in ((0, 313), (313, 637), (637, 950), (950, 1254)):
                box = left, 280, right, 640
                cutouts.append((box, source.crop(box)))
            assert len(cutouts) == 16
        else:
            cutouts = forest_components(source, expected=16)
        cutouts.sort(key=lambda item: (item[0][1] + item[0][3]) / 2)
        boxes = []
        for row, (suffix, height) in enumerate(designs):
            directions = sorted(cutouts[row * 4 : row * 4 + 4], key=lambda item: item[0][0])
            boxes.append([box for box, _ in directions])
            poses = [[image for _ in range(4)] for _, image in directions]
            actor = f"{zone}_{suffix}"
            manifest["actors"][actor] = atlas(
                actor, poses, 104 if row == 3 else 80, height, derived=True
            )
        provenance[zone] = dict(
            file=path.name,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            reviewed_cutouts=boxes,
            actors=[f"{zone}_{d[0]}" for d in designs],
        )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    (SOURCE / "source_hashes.json").write_text(json.dumps(provenance, indent=2) + "\n", "utf-8")
    print("Packed sixteen original detailed directional atlases, with walk/idle/cast/death frames")


if __name__ == "__main__":
    main()
