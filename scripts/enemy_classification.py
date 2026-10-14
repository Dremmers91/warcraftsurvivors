"""Explicit original-game creature classifications shared by offline builders."""

import json
from pathlib import Path

BEASTS = {
    "wolf",
    "spider",
    "forest_boar",
    "forest_bear",
    "duskwood_nightwolf",
    "duskwood_venom_spider",
    "stranglethorn_raptor",
    "stranglethorn_panther",
    "stranglethorn_jungle_boar",
    "stranglethorn_gorilla",
    "stranglethorn_basilisk",
    "stranglethorn_crocolisk",
}
UNDEAD = {
    "duskwood_zombie",
    "duskwood_skeleton",
    "plaguelands_ghoul",
    "plaguelands_plague_hound",
    "plaguelands_crypt_fiend",
    "plaguelands_bone_knight",
    "icecrown_geist",
    "icecrown_frost_hound",
    "icecrown_frost_abomination",
    "duskwood_restless_spirit",
    "duskwood_skeletal_archer",
    "plaguelands_banshee",
    "plaguelands_gargoyle",
    "plaguelands_abomination",
    "icecrown_nerubian",
    "icecrown_frost_revenant",
    "icecrown_wyrm_hatchling",
}


def annotate(enemies, bosses):
    for enemy in enemies:
        eid = enemy["id"]
        enemy["family"] = "beast" if eid in BEASTS else "undead" if eid in UNDEAD else "humanoid"
        enemy["faction"] = "defias" if eid == "bandit" or eid.startswith("defias_") else ""
    for boss in bosses:
        boss["family"] = (
            "beast"
            if boss["id"] == "bangalash"
            else "undead"
            if boss["id"] in {"stitches", "rivendare", "lich_king"}
            else "humanoid"
        )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "src/warcraft_survivors/data"
    for name in ("content", "encounters", "zones"):
        path = root / f"{name}.json"
        raw = json.loads(path.read_text("utf-8"))
        annotate(raw.get("enemies", []), raw.get("bosses", []))
        path.write_text(json.dumps(raw, indent=2) + "\n", "utf-8")
    print("Classified hostile creatures; no demon enemies or dragon bosses are shipped")
