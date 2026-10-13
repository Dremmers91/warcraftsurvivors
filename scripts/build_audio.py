"""Compose project-original music and cues offline without external recordings."""

from __future__ import annotations

import json
import math
import random
import wave
from array import array
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "src/warcraft_survivors/assets/audio"
RATE = 22050


def tone(buffer, start, duration, note, gain, voice="bell", pan=0):
    begin, count = round(start * RATE), round(duration * RATE)
    freq = 440 * 2 ** ((note - 69) / 12)
    rng = random.Random(note + begin)
    for i in range(min(count, len(buffer) // 2 - begin)):
        t, phase = i / RATE, i / RATE * freq * math.tau
        envelope = min(1, t / 0.025) * min(1, (duration - t) / 0.07)
        if voice == "bell":
            value = (
                math.sin(phase) + 0.35 * math.sin(phase * 2.01) + 0.15 * math.sin(phase * 4.03)
            ) * math.exp(-t * 3)
        elif voice == "strings":
            value = (math.sin(phase) + 0.3 * math.sin(phase * 2) + 0.18 * math.sin(phase * 3)) * (
                0.8 + 0.2 * math.sin(t * 5)
            )
        else:
            value = (
                rng.uniform(-1, 1) * 0.4 + math.sin(phase * max(0.1, 1 - t * 3)) * 0.6
            ) * math.exp(-t * 14)
        buffer[(begin + i) * 2] += value * gain * envelope * (1 - pan * 0.5)
        buffer[(begin + i) * 2 + 1] += value * gain * envelope * (1 + pan * 0.5)


def save(name, buffer):
    samples = array("h", (round(max(-0.96, min(0.96, v)) * 32767) for v in buffer))
    with wave.open(str(OUT / f"{name}.wav"), "wb") as writer:
        writer.setparams((2, 2, RATE, len(buffer) // 2, "NONE", "not compressed"))
        writer.writeframes(samples.tobytes())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tracks = [
        (
            "elwynn",
            72,
            [0, 4, 7, 9, 7, 4, 2, 4],
            [[0, 4, 7], [-5, -1, 2], [-3, 0, 4], [-7, -3, 0]],
            "bell",
        ),
        (
            "duskwood",
            60,
            [0, 3, 7, 6, 3, 2, -2, 0],
            [[0, 3, 7], [-2, 1, 5], [-5, -2, 2], [-1, 2, 6]],
            "strings",
        ),
        (
            "stranglethorn",
            67,
            [0, 2, 7, 9, 7, 5, 2, 0],
            [[0, 3, 7], [-5, -2, 2], [-3, 0, 4], [-5, -2, 2]],
            "bell",
        ),
        (
            "plaguelands",
            57,
            [0, 1, 7, 3, 1, -2, 0, -1],
            [[0, 3, 6], [-1, 2, 5], [-5, -2, 1], [-2, 1, 4]],
            "strings",
        ),
        (
            "icecrown",
            62,
            [0, 7, 3, 10, 7, 2, -2, 0],
            [[0, 3, 7], [-2, 1, 5], [-5, -2, 2], [-1, 2, 6]],
            "strings",
        ),
    ]
    for name, root, melody, chords, voice in tracks:
        beat = 0.6 if name in {"duskwood", "icecrown"} else 0.5
        buffer = [0.0] * round(32 * beat * RATE * 2)
        for bar, chord in enumerate(chords * 2):
            for note in chord:
                tone(buffer, bar * 4 * beat, 3.8 * beat, root - 12 + note, 0.035, "strings", -0.2)
            tone(buffer, bar * 4 * beat, 0.4, root - 24 + chord[0], 0.05, "drum")
            for step in range(4):
                tone(
                    buffer,
                    (bar * 4 + step) * beat,
                    0.8 * beat,
                    root + melody[(bar * 4 + step) % 8],
                    0.05,
                    voice,
                    0.2,
                )
                if name == "stranglethorn":
                    tone(
                        buffer, (bar * 4 + step + 0.5) * beat, 0.12, 45 + step, 0.025, "drum", -0.3
                    )
        save(f"music_{name}", buffer)
    cues = {
        "cast_holy": ([79, 86], 0.13, "bell"),
        "cast_frost": ([88, 81], 0.12, "bell"),
        "cast_arcane": ([74, 81, 86], 0.16, "bell"),
        "cast_fire": ([48, 55], 0.14, "drum"),
        "cast_shadow": ([51, 54, 50], 0.18, "strings"),
        "cast_physical": ([43, 47], 0.1, "drum"),
        "cast_nature": ([79, 83], 0.13, "bell"),
        "cast": ([72, 79], 0.09, "bell"),
        "hit": ([39, 35], 0.1, "drum"),
        "hurt": ([48, 43], 0.2, "strings"),
        "death": ([55, 51, 48, 43], 0.8, "strings"),
        "elite": ([48, 55, 60], 0.8, "strings"),
        "boss": ([36, 43, 48, 39], 1.2, "strings"),
        "level": ([72, 76, 79, 84], 0.6, "bell"),
        "evolution": ([60, 67, 72, 76, 79, 84], 1, "bell"),
        "upgrade": ([72, 79, 84], 0.45, "bell"),
        "pickup": ([86], 0.08, "bell"),
        "menu": ([72, 76], 0.1, "bell"),
        "victory": ([60, 64, 67, 72, 76, 79, 84], 1.8, "strings"),
        "chest": ([67, 72, 79], 0.45, "bell"),
        "enemy_death": ([39], 0.1, "drum"),
    }
    for name, (notes, duration, voice) in cues.items():
        buffer = [0.0] * round(duration * RATE * 2)
        for index, note in enumerate(notes):
            start = index * duration * 0.6 / len(notes)
            tone(buffer, start, duration - start, note, 0.1, voice)
        save(name, buffer)
    (OUT / "manifest.json").write_text(
        json.dumps(
            dict(
                method="Original offline synthesis; authored melodies, chords and instruments",
                sample_rate=RATE,
                tracks=[f"music_{z[0]}.wav" for z in tracks],
                cues=[f"{c}.wav" for c in cues],
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Composed five stereo loop tracks and 21 original sound cues")


if __name__ == "__main__":
    main()
