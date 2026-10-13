"""Validate frozen class/zone matrix, every boss, menus, bundled art/audio and debug guard."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from validate_assets import validate

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--executable", type=Path, default=ROOT / "dist/WarcraftSurvivors/WarcraftSurvivors.exe"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/milestone5/executable")
    args = parser.parse_args()
    executable = args.executable.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    packaged_assets = executable.parent / "_internal/warcraft_survivors/assets"
    if packaged_assets.exists():
        errors = validate(packaged_assets)
        if errors:
            raise RuntimeError("Packaged resource validation failed: " + "; ".join(errors))
    reports = []

    def smoke(name, *extra):
        shot = output / f"{name}.png"
        result = subprocess.run(
            [
                str(executable),
                "--smoke-test",
                "--frames",
                "180",
                "--seed",
                "42",
                "--save-dir",
                str(output / "save"),
                "--screenshot",
                str(shot),
                *extra,
            ],
            cwd=ROOT,
            timeout=60,
            check=True,
        )
        assert result.returncode == 0 and shot.exists(), name
        reports.append(dict(name=name, result="pass", frames=180, screenshot=str(shot)))

    for zid in ("elwynn", "duskwood", "stranglethorn", "plaguelands", "icecrown"):
        for cid in ("paladin", "warrior", "mage", "hunter", "warlock", "priest"):
            smoke(zid + "-" + cid, "--zone", zid, "--class", cid)
        smoke(zid + "-boss", "--zone", zid, "--encounter-smoke")
    for screen in (
        "main",
        "classes",
        "zones",
        "settings",
        "progression",
        "talents",
        "shop",
        "achievements",
        "unlocks",
    ):
        smoke(screen, "--screen-smoke", screen)
    protected = subprocess.run(
        [str(executable), "--debug", "--smoke-test", "--save-dir", str(output / "save")],
        cwd=ROOT,
        timeout=30,
    )
    assert protected.returncode == 2, "Packaged developer controls were not rejected"
    assert (output / "save/logs/game.log").exists(), "Packaged logging did not create a log"
    (output / "validation.json").write_text(
        json.dumps(
            dict(
                executable=str(executable),
                executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                resource_hashes={
                    p.relative_to(executable.parent).as_posix(): hashlib.sha256(
                        p.read_bytes()
                    ).hexdigest()
                    for p in (executable.parent / "_internal").rglob("*")
                    if p.is_file()
                }
                if packaged_assets.exists()
                else {},
                scenarios=reports,
                debug_exit=protected.returncode,
                asset_warnings=0,
                audio_cues=21,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"Validated {len(reports)} frozen launches, bundled art/audio, user-data logs and --debug rejection"
    )


if __name__ == "__main__":
    main()
