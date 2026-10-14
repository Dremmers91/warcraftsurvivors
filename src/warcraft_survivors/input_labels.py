"""Common controller-family labels with an explicit generic fallback."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerLabels:
    accept: str = "Button 1"
    back: str = "Button 2"
    reroll: str = "Button 3"
    banish: str = "Button 4"
    details: str = "Left shoulder"


def controller_labels(name: str) -> ControllerLabels:
    normalized = name.casefold()
    if any(word in normalized for word in ("playstation", "dualshock", "dualsense", "ps4", "ps5")):
        return ControllerLabels("Cross", "Circle", "Square", "Triangle", "L1")
    if any(word in normalized for word in ("xbox", "xinput", "360")):
        return ControllerLabels("A", "B", "X", "Y", "LB")
    return ControllerLabels()
