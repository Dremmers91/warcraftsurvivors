"""Validate packaged raster dimensions, alpha, animation poses and provenance."""

from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/warcraft_survivors/assets"


def validate(root: Path = ASSETS) -> list[str]:
    manifest = json.loads((root / "manifest.json").read_text("utf-8"))
    errors = []
    for category in ("actors", "images", "effects"):
        for name, spec in manifest[category].items():
            path = (root / spec["file"]).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                errors.append(f"{name}: missing or escaping path")
                continue
            with Image.open(path) as image:
                if image.mode != "RGBA":
                    errors.append(f"{name}: expected RGBA")
                if category == "actors":
                    fw, fh = spec["frame_size"]
                    expected = fw * 4, fh * 16
                    hashes = set()
                    for row in range(4):
                        for column in range(4):
                            frame = image.crop(
                                (column * fw, row * fh, (column + 1) * fw, (row + 1) * fh)
                            )
                            bounds = frame.getbbox()
                            if (
                                bounds is None
                                or bounds[0] < 1
                                or bounds[2] > fw - 1
                                or bounds[3] > spec["anchor"][1]
                            ):
                                errors.append(
                                    f"{name}: empty/clipped/misaligned walk frame {row}:{column}"
                                )
                            hashes.add(hashlib.sha256(frame.tobytes()).hexdigest())
                    if len(hashes) < 12:
                        errors.append(
                            f"{name}: directional walk frames are not sufficiently distinct"
                        )
                elif category == "effects":
                    expected = spec["size"][0] * spec["frames"], spec["size"][1]
                else:
                    expected = tuple(spec["size"])
                if image.size != expected:
                    errors.append(f"{name}: expected {expected}, got {image.size}")
                if category != "images" and image.getchannel("A").getextrema()[0] != 0:
                    errors.append(f"{name}: missing transparency")
    audio_file = root / "audio/manifest.json"
    if not audio_file.exists():
        errors.append("audio: missing manifest")
    else:
        audio = json.loads(audio_file.read_text(encoding="utf-8"))
        for name in audio["tracks"] + audio["cues"]:
            try:
                path = (root / "audio" / name).resolve()
                if not path.is_relative_to(root.resolve()):
                    raise ValueError("Audio path escapes root")
                with wave.open(str(path)) as sound:
                    if (
                        sound.getnchannels() != 2
                        or sound.getsampwidth() != 2
                        or sound.getframerate() != 22050
                        or sound.getnframes() < 100
                    ):
                        errors.append(f"audio {name}: invalid sound format")
            except (OSError, ValueError, wave.Error):
                errors.append(f"audio {name}: missing/corrupted sound")
    if not (root / "game_icon.ico").exists():
        errors.append("icon: missing Windows application icon")
    return errors


if __name__ == "__main__":
    errors = validate()
    if errors:
        raise SystemExit("\n".join(errors))
    print("All actor/image/effect dimensions, alpha, poses and anchors validated")
