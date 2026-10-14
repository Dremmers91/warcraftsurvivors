"""Reuse bundled detailed artwork for companion effects; no new raster generation."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "src/warcraft_survivors/assets/manifest.json"


def register_companion_effects(manifest):
    for aid, source in (
        ("summon_felguard", "fireball"),
        ("summon_felguard_evolved", "fireball_evolved"),
    ):
        manifest["effects"][aid] = manifest["effects"][source].copy()
        manifest["projectiles"][aid] = dict(
            effect=aid,
            art_size=26 if source == "fireball" else 34,
            rank_scale=0.02,
            spin_degrees=0,
            trail="spark_gold",
            active=True,
        )


def main():
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    register_companion_effects(manifest)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    print("Imp bolts reuse original fireball atlases; wolf/Imp/Felguard art preserved")


if __name__ == "__main__":
    main()
