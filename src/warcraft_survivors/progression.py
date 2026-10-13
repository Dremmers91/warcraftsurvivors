"""Pure in-run XP calculations, shared by HUD, simulation and tests."""


def xp_required(level: int) -> float:
    if level < 1:
        raise ValueError("Level must be positive")
    # Preserve quick early decisions; extend build development into the late run
    # instead of flooding a completed arsenal with hundreds of reward cards.
    return float(10 + level * 7 + level**1.45 * 1.6 + max(0, level - 40) ** 1.65 * 2.5)
