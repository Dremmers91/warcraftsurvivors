"""Formatting for a permanent upgrade contribution, separate from run totals."""

from .content import Content
from .passive_effects import BASE_PICKUP_RADIUS


def bonus_summary(effects: dict[str, float], content: Content) -> str:
    if not effects:
        return "No bonus."
    labels = {
        "damage": "Damage",
        "health": "Base health",
        "armor": "Armor",
        "haste": "Cooldown",
        "manual_haste": "Manual cooldown",
        "speed": "Movement",
        "area": "Attack radius",
        "duration": "Duration",
        "boss_damage": "Boss damage",
        "low_health_damage": "Damage below 35% health",
        "execute": "Execute damage",
        "healing": "Healing",
        "count": "Volley / pet count",
        "regen": "Recovery",
        "kill_heal": "Health per kill",
        "kill_shield": "Shield per kill",
        "starting_shield": "Starting shield",
        "gold": "Run earnings (excludes achievements)",
        "xp": "Run gem XP",
        "rerolls": "Rerolls per run",
        "banishes": "Banishes per run",
        "choices": "Extra normal cards",
        "chest_gold": "Gold per opened elite chest",
        "pickup": "Attraction reach",
    }
    parts = []
    for key, value in effects.items():
        fields = key.split(":")
        label = labels.get(key, key)
        suffix = f"+{value * 100:g}%"
        if fields[0] == "spell":
            label = (
                content.abilities[fields[1]].name
                + ": "
                + {
                    "count": "projectiles/effects",
                    "pierce": "pierce",
                    "radius": "attack radius",
                    "duration": "duration",
                    "speed": "travel speed",
                    "damage": "damage",
                    "spread": "spread",
                    "waves": "extra waves",
                    "splash": "splash radius",
                    "splash_flat": "splash radius",
                    "opening": "opening damage",
                }[fields[2]]
            )
            if fields[2] in {"count", "pierce", "waves", "splash_flat"}:
                suffix = f"+{value:g}"
                if fields[2] == "splash_flat":
                    base_splash = content.abilities[fields[1]].mechanics.splash
                    suffix = (
                        f"+{value / base_splash * 100:.1f}% of base splash; splashes from Rank 1"
                    )
            if fields[2] == "spread" and content.abilities[fields[1]].kind == "dot":
                suffix += "; spread from Rank 1"
        elif fields[0] == "school":
            label = fields[1].title() + " damage"
        elif fields[0] == "kind":
            label = {
                "dot": "DoT",
                "companion": "Companion",
                "area": "Attack radius",
                "arc": "Cleave",
                "field": "Ground attack",
                "charge": "Charging summon",
            }.get(fields[1], fields[1]) + " damage"
        elif key == "armor":
            suffix = f"+{value * 100:g} percentage points"
        elif key in {"haste", "manual_haste"}:
            suffix = f"-{value * 100:g}%"
        elif key == "pickup":
            suffix = f"+{value / BASE_PICKUP_RADIUS * 100:.1f}% of base reach"
        elif key in {
            "count",
            "regen",
            "kill_heal",
            "kill_shield",
            "starting_shield",
            "rerolls",
            "banishes",
            "choices",
            "chest_gold",
        }:
            suffix = f"+{value:g}" + (" / second" if key == "regen" else "")
        parts.append(label + " " + suffix)
    return "; ".join(parts) + "."
