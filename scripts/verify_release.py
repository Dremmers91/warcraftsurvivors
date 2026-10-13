"""Check release ZIP integrity and run extracted frozen games from a source-free working directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--crc-only",
        action="store_true",
        help="Refresh archive fingerprints after documentation-only repackaging",
    )
    args = parser.parse_args()
    report_path = ROOT / "artifacts/milestone5/release-validation.json"
    previous = (
        json.loads(report_path.read_text(encoding="utf-8"))
        if args.crc_only and report_path.exists()
        else {}
    )
    reports = []
    for name, inner in (
        ("WarcraftSurvivors-0.5.0-Windows.zip", "WarcraftSurvivors/WarcraftSurvivors.exe"),
        ("WarcraftSurvivors-0.5.0-Windows-OneFile.zip", "WarcraftSurvivorsOneFile.exe"),
    ):
        archive = ROOT / "dist" / name
        if not archive.exists() and "OneFile" in name:
            continue
        destination = ROOT / f"artifacts/milestone5/release-extracted-{time.time_ns()}"
        with zipfile.ZipFile(archive) as packed:
            assert packed.testzip() is None, f"CRC failure in {name}"
            for member in packed.infolist():
                assert (
                    (destination / member.filename).resolve().is_relative_to(destination.resolve())
                ), "Archive contains escaping path"
            exe_hash = hashlib.sha256(packed.read(inner)).hexdigest()
            if args.crc_only:
                old = next(r for r in previous["archives"] if r["archive"] == name)
                assert exe_hash == old["executable_sha256"], (
                    "Binary changed; full extracted startup is required"
                )
                # Require every frozen runtime member to match the previously booted archive.
                resource_hashes = {
                    m.filename: hashlib.sha256(packed.read(m)).hexdigest()
                    for m in packed.infolist()
                    if not m.is_dir() and ("/_internal/" in m.filename or m.filename == inner)
                }
                assert resource_hashes == old["resource_hashes"], (
                    "Runtime resources changed; full startup required"
                )
                startup = old["extracted_startup"]
            else:
                packed.extractall(destination)
                executable = destination / inner
                output = destination / "qa-save"
                env = os.environ.copy()
                env.pop("PYTHONPATH", None)
                env["PATH"] = str(Path(env.get("SystemRoot", "C:/Windows")) / "System32")
                result = subprocess.run(
                    [
                        str(executable),
                        "--smoke-test",
                        "--zone",
                        "icecrown",
                        "--class",
                        "warlock",
                        "--save-dir",
                        str(output),
                        "--screenshot",
                        str(output / "extracted.png"),
                    ],
                    cwd=executable.parent,
                    env=env,
                    timeout=60,
                    check=True,
                )
                assert result.returncode == 0 and (output / "extracted.png").exists()
                startup = "pass; extracted source-free working directory and System32-only PATH"
                resource_hashes = {
                    m.filename: hashlib.sha256(packed.read(m)).hexdigest()
                    for m in packed.infolist()
                    if not m.is_dir() and ("/_internal/" in m.filename or m.filename == inner)
                }
            reports.append(
                dict(
                    archive=name,
                    crc="pass",
                    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                    bytes=archive.stat().st_size,
                    executable_sha256=exe_hash,
                    resource_hashes=resource_hashes,
                    extracted_startup=startup,
                )
            )
        print(f"Validated {name}: CRC, runtime fingerprints, extracted startup")
    report_path.write_text(json.dumps(dict(archives=reports), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
