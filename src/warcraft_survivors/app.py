"""Native screens, input, fixed-step accumulator and campaign results."""

from __future__ import annotations

import argparse
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any

import pygame
from pygame import Rect, Vector2

from .achievement_ui import future_card
from .audio import Audio
from .content import load_content
from .debug import DebugTools, debug_allowed
from .input_labels import ControllerLabels, controller_labels
from .meta import class_level, load_progression
from .movement import analog_direction, cursor_direction, keyboard_direction
from .persistence import SaveStore
from .progression_ui import SCREENS, ProgressionUI
from .rendering import CREAM, GOLD, MUTED, Renderer
from .rewards import ACHIEVEMENTS
from .simulation import FIXED_DT, Simulation
from .upgrade_ui import UpgradeView
from .world import VIEW_SIZE


@dataclass
class Button:
    rect: Rect
    label: str
    action: Callable[[], None]


class App:
    def __init__(
        self, save: SaveStore, seed: int = 1, debug: bool = False, release: bool = False
    ) -> None:
        pygame.mixer.pre_init(22050, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("Warcraft Survivors — Milestone 5")
        self.save, self.seed = save, seed
        self.content = load_content()
        self.selected_class = "paladin"
        self.class_page = 0
        self.selected_choice = 0
        self.upgrade_ui = UpgradeView()
        self.input_device = "keyboard"
        self.selected_zone = "elwynn"
        self.progression_ui = ProgressionUI()
        self.notifications: list[tuple[str, float]] = []
        self.debug = DebugTools(debug, release)
        self.screen = "main"
        self.focus = 0
        self.buttons: list[Button] = []
        self.running = True
        self.sim: Simulation | None = None
        self.result: dict[str, Any] | None = None
        self.joysticks: dict[int, pygame.joystick.JoystickType] = {}
        self.axis_timer = 0.0
        self.clock = pygame.time.Clock()
        self.accumulator = 0.0
        self.display = pygame.display.set_mode(VIEW_SIZE, pygame.RESIZABLE)
        self.viewport = Rect(0, 0, *VIEW_SIZE)
        self.renderer = Renderer(self.content)
        self.audio = Audio()
        self.ui_sound_events: list[str] = []
        try:
            pygame.display.set_icon(
                pygame.image.load(str(self.renderer.assets.root / "game_icon.png"))
            )
        except (OSError, pygame.error):
            pass
        for index in range(pygame.joystick.get_count()):
            self.add_joystick(index)
        if (
            self.save.data["settings"]["fullscreen"]
            or self.save.data["settings"].get("resolution", "1280x720") != "1280x720"
        ):
            self.apply_display()
        self.build_buttons()

    def apply_display(self) -> None:
        fullscreen = self.save.data["settings"]["fullscreen"]
        self.display = pygame.display.set_mode(
            (0, 0)
            if fullscreen
            else tuple(
                int(v) for v in self.save.data["settings"].get("resolution", "1280x720").split("x")
            ),
            pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE,
        )

    def add_joystick(self, index: int) -> None:
        try:
            stick = pygame.joystick.Joystick(index)
            stick.init()
            self.joysticks[stick.get_instance_id()] = stick
        except pygame.error:
            pass

    def goto(self, screen: str) -> None:
        if screen in SCREENS | {"zones", "classes"} and self.sim and not self.sim.finished:
            self.toast("Finish the current run before changing progression.")
            return
        self.screen, self.focus, self.accumulator = screen, 0, 0.0
        if screen == "level":
            self.selected_choice = 0
        self.ui_sound_events.append("menu")
        self.build_buttons()

    def start_run(self) -> None:
        if not self.save.class_available(self.selected_class):
            self.toast("This class is locked or reserved for a future release.")
            return
        self.sim = Simulation(
            self.content,
            self.selected_class,
            seed=self.seed,
            permanent=self.save.loadout(self.selected_class),
            zone_id=self.selected_zone,
        )
        self.seed += 1
        self.debug.reset()
        self.notifications.clear()
        self.result = None
        self.goto("game")

    def end_run(self) -> None:
        if self.sim and self.result is None:
            sim = self.sim
            if not sim.finished:
                sim.finish("abandoned")
            if sim.debug_used:
                self.result = {
                    "recorded": False,
                    "gold": 0,
                    "class_xp": 0,
                    "achievements": [],
                    "saved": False,
                }
            else:
                self.result = self.save.reward_run(
                    sim.class_id,
                    sim.kills,
                    sim.elites,
                    sim.elapsed,
                    sim.won,
                    sim.gold,
                    sim.evolved,
                    sim.class_xp_kills,
                    sim.player.meta.get("gold"),
                    sim.boss.boss_id if sim.boss else "",
                    summary=sim.ledger.summary(sim),
                )
                self.result["recorded"] = True
                for aid in self.result["achievements"]:
                    self.toast("Achievement unlocked: " + ACHIEVEMENTS[aid][0])
                for cid in self.result["unlocks"]:
                    self.toast(
                        load_progression().classes[cid].name + " unlocked for a future release."
                    )
                if self.result["points"]:
                    self.toast(f"Class level gained · {self.result['points']} new talent points.")
        self.goto("results")

    def quit(self) -> None:
        if self.sim and self.result is None:
            self.end_run()
        self.save.write()
        self.running = False

    def toggle(self, key: str) -> None:
        settings = self.save.data["settings"]
        settings[key] = not settings[key]
        self.save.write()
        if key == "fullscreen":
            self.apply_display()
        self.build_buttons()

    def cycle_quality(self) -> None:
        qualities = ("low", "medium", "high")
        current = self.save.data["settings"].get("effects_quality", "medium")
        self.save.data["settings"]["effects_quality"] = qualities[
            (qualities.index(current) + 1) % 3
        ]
        self.save.write()
        self.build_buttons()

    def choose(self, index: int) -> None:
        if self.sim:
            self.sim.choose(index)
            self.goto("level" if self.sim.choices else "game")

    def cycle_setting(self, key: str, values: tuple[Any, ...]) -> None:
        settings = self.save.data["settings"]
        current = settings[key]
        index = values.index(current) if current in values else -1
        settings[key] = values[(index + 1) % len(values)]
        self.save.write()
        if key == "resolution":
            self.apply_display()
        self.build_buttons()

    def select_zone(self, zid: str) -> None:
        if zid not in self.save.data["unlocked_zones"]:
            self.toast("This zone is locked.")
            return
        self.selected_zone = zid
        self.goto("classes")

    def toast(self, message: str) -> None:
        self.notifications.append((message, 3.5))
        self.notifications = self.notifications[-40:]

    def reroll(self) -> None:
        if self.sim and self.sim.reroll():
            self.build_buttons()
        elif self.sim:
            self.toast("No reroll available for this choice.")

    def select_class(self, cid: str) -> None:
        if not self.save.class_available(cid):
            self.toast("This class requires an achievement and a future content release.")
            return
        self.selected_class = cid
        self.start_run()

    def class_turn_page(self, amount: int) -> None:
        self.class_page = (self.class_page + amount) % ((len(load_progression().classes) + 5) // 6)
        self.goto("classes")

    def banish(self) -> None:
        if self.sim:
            index = self.focus if self.focus < len(self.sim.choices) else self.selected_choice
            if self.sim.banish(index):
                self.focus = self.selected_choice = 0
                self.build_buttons()
            else:
                self.toast("No banish available for this choice.")

    def pad_labels(self) -> ControllerLabels:
        for stick in self.joysticks.values():
            return controller_labels(stick.get_name())
        return ControllerLabels()

    def activation_label(self) -> str:
        return (
            self.pad_labels().accept
            if self.input_device == "controller"
            else "Space / " + self.pad_labels().accept
        )

    def power_details(self) -> None:
        if self.screen == "level" and self.sim and self.sim.choices:
            index = self.focus if self.focus < len(self.sim.choices) else self.selected_choice
            self.upgrade_ui.open(self, self.sim.choices[index])

    def build_buttons(self) -> None:
        self.buttons = []

        def add(rect: Rect, label: str, action: Callable[[], None]) -> None:
            self.buttons.append(Button(rect, label, action))

        if self.screen == "main":
            add(Rect(80, 330, 360, 64), "Choose your class", lambda: self.goto("classes"))
            add(Rect(80, 414, 360, 64), "Settings", lambda: self.goto("settings"))
            add(Rect(80, 498, 360, 64), "Choose zone", lambda: self.goto("zones"))
            add(Rect(80, 580, 360, 54), "Exit", self.quit)
            add(Rect(650, 610, 170, 54), "Talents", lambda: self.goto("progression"))
            add(Rect(834, 610, 170, 54), "Upgrades", lambda: self.goto("shop"))
            add(Rect(1018, 610, 190, 54), "Achievements", lambda: self.goto("achievements"))
        elif self.screen == "zones":
            for index, zone in enumerate(self.content.zones.values()):
                add(
                    Rect(97 + (index % 3) * 368, 184 + (index // 3) * 220, 350, 202),
                    zone.name,
                    partial(self.select_zone, zone.id),
                )
            add(Rect(97, 650, 230, 48), "Back", lambda: self.goto("main"))
        elif self.screen in SCREENS:
            self.progression_ui.build(self, add)
        elif self.screen == "classes":
            entries = list(load_progression().classes.values())[
                self.class_page * 6 : self.class_page * 6 + 6
            ]
            for index, cls in enumerate(entries):
                add(
                    Rect(97 + (index % 3) * 368, 184 + (index // 3) * 220, 350, 202),
                    cls.name,
                    partial(self.select_class, cls.id),
                )
            add(Rect(350, 650, 300, 48), "Future champions", lambda: self.goto("unlocks"))
            add(Rect(740, 650, 230, 48), "Previous", partial(self.class_turn_page, -1))
            add(Rect(984, 650, 230, 48), "Next", partial(self.class_turn_page, 1))
            add(Rect(97, 650, 230, 48), "Back", lambda: self.goto("main"))
        elif self.screen == "pause":
            add(Rect(460, 275, 360, 64), "Resume", lambda: self.goto("game"))
            add(Rect(460, 359, 360, 64), "Finish this run", self.end_run)
            add(Rect(460, 443, 360, 64), "Exit game", self.quit)
            add(Rect(460, 527, 360, 64), "Spellbook", partial(self.goto, "spellbook"))
        elif self.screen == "spellbook" and self.sim:
            for index, choice in enumerate(self.upgrade_ui.equipped(self)):
                add(
                    Rect(64 + index % 2 * 584, 190 + index // 2 * 102, 566, 90),
                    choice.name,
                    partial(self.upgrade_ui.open, self, choice, "spellbook"),
                )
            add(Rect(64, 650, 230, 48), "Back", partial(self.goto, "pause"))
        elif self.screen == "upgrade_details" and self.sim:
            add(Rect(64, 650, 230, 48), "Back", partial(self.upgrade_ui.close, self))
            add(Rect(740, 650, 230, 48), "Previous", partial(self.upgrade_ui.turn_page, self, -1))
            add(Rect(984, 650, 230, 48), "Next", partial(self.upgrade_ui.turn_page, self, 1))
        elif self.screen == "level" and self.sim:
            for index, choice in enumerate(self.sim.choices):
                rect = (
                    Rect(64 + index * 292, 220, 278, 370)
                    if len(self.sim.choices) == 4
                    else Rect(97 + index * 368, 220, 350, 370)
                )
                add(rect, choice.name, partial(self.choose, index))
            add(Rect(64, 648, 176, 48), "Q · Details", self.power_details)
            if self.sim.player.meta.get("rerolls") and not self.sim.chest_choice:
                add(Rect(260, 648, 350, 48), f"R / X · Reroll ({self.sim.rerolls})", self.reroll)
            if self.sim.player.meta.get("banishes") and not self.sim.chest_choice:
                add(Rect(650, 648, 350, 48), f"B / Y · Banish ({self.sim.banishes})", self.banish)
        elif self.screen == "settings":
            for index, key in enumerate(("fullscreen", "sound", "screen_shake")):
                value = "ON" if self.save.data["settings"][key] else "OFF"
                add(
                    Rect(64, 194 + index * 66, 700, 54),
                    f"{'Sound effects' if key == 'sound' else key.replace('_', ' ').title()}: {value}",
                    partial(self.toggle, key),
                )
            quality = self.save.data["settings"].get("effects_quality", "medium")
            add(Rect(64, 392, 700, 54), f"Effects: {quality.title()}", self.cycle_quality)
            for index, (key, label, values) in enumerate(
                (
                    ("music_volume", "Music volume", (0.0, 0.15, 0.35, 0.6, 1.0)),
                    ("sound_volume", "Sound volume", (0.0, 0.25, 0.5, 0.7, 1.0)),
                    ("effects_density", "Cosmetic effect density", (0.0, 0.25, 0.5, 0.75, 1.0)),
                    (
                        "resolution",
                        "Window resolution",
                        ("1280x720", "1600x900", "1920x1080", "2560x1440"),
                    ),
                )
            ):
                value = self.save.data["settings"][key]
                detail = f"{value:.0%}" if isinstance(value, float) else value
                add(
                    Rect(64, 458 + index * 48, 700, 42),
                    f"{label}: {detail}",
                    partial(self.cycle_setting, key, values),
                )
            add(Rect(820, 610, 230, 54), "Back", lambda: self.goto("main"))
        elif self.screen == "results":
            add(Rect(64, 610, 280, 54), "Return to menu", lambda: self.goto("main"))
            add(Rect(380, 610, 280, 54), "Run again", self.start_run)
            add(Rect(760, 610, 280, 54), "Spend rewards", lambda: self.goto("progression"))
            add(Rect(902, 550, 312, 40), "View achievements", lambda: self.goto("achievements"))
        self.focus = min(self.focus, max(0, len(self.buttons) - 1))

    def mouse_position(self, pos: tuple[int, int]) -> Vector2:
        return Vector2(
            (pos[0] - self.viewport.x) * 1280 / self.viewport.width,
            (pos[1] - self.viewport.y) * 720 / self.viewport.height,
        )

    def menu_key(self, key: int) -> None:
        if self.screen == "upgrade_details" and key in {pygame.K_ESCAPE, pygame.K_q}:
            self.upgrade_ui.close(self)
            return
        if self.screen == "spellbook" and key == pygame.K_ESCAPE:
            self.goto("pause")
            return
        if self.screen == "level" and key == pygame.K_q:
            self.power_details()
            return
        if self.screen == "talents":
            self.progression_ui.tree.hovered = None
        if self.screen == "game" and self.sim and self.debug.input_time(key, self.sim):
            return
        if self.screen in SCREENS and key == pygame.K_ESCAPE:
            self.progression_ui.escape(self)
            return
        if self.screen == "level" and key == pygame.K_r:
            self.reroll()
            return
        if self.screen == "level" and key == pygame.K_b:
            self.banish()
            return
        if key == pygame.K_ESCAPE:
            if self.screen == "game":
                self.goto("pause")
            elif self.screen == "pause":
                self.goto("game")
            elif self.screen not in ("level", "main"):
                self.goto("main")
            return
        if self.screen == "game":
            if self.sim:
                if key == pygame.K_SPACE:
                    self.sim.activate_manual(self.movement())
                self.debug.handle(key, self.sim)
                if self.sim.choices:
                    self.goto("level")
            return
        if not self.buttons:
            return
        directions = {
            pygame.K_UP: Vector2(0, -1),
            pygame.K_w: Vector2(0, -1),
            pygame.K_DOWN: Vector2(0, 1),
            pygame.K_s: Vector2(0, 1),
            pygame.K_LEFT: Vector2(-1, 0),
            pygame.K_a: Vector2(-1, 0),
            pygame.K_RIGHT: Vector2(1, 0),
            pygame.K_d: Vector2(1, 0),
        }
        if (
            self.screen in SCREENS | {"classes", "zones", "spellbook", "upgrade_details"}
            and key in directions
        ):
            direction = directions[key]
            origin = Vector2(self.buttons[self.focus].rect.center)
            candidates = [
                (i, Vector2(button.rect.center) - origin)
                for i, button in enumerate(self.buttons)
                if i != self.focus
            ]
            ahead = [(i, delta) for i, delta in candidates if delta.dot(direction) > 1]
            if direction.x:
                ahead = [
                    (i, delta)
                    for i, delta in ahead
                    if abs(delta.y) <= self.buttons[self.focus].rect.height / 2
                ]
            if ahead:
                self.focus = min(
                    ahead,
                    key=lambda pair: abs(pair[1].cross(direction)) * 5 + pair[1].dot(direction),
                )[0]
            elif direction.x:
                self.focus = (self.focus + int(direction.x)) % len(self.buttons)
            return
        if key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w, pygame.K_a):
            self.focus = (self.focus - 1) % len(self.buttons)
        elif key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_s, pygame.K_d, pygame.K_TAB):
            self.focus = (self.focus + 1) % len(self.buttons)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self.buttons[self.focus].action()
        elif self.screen == "level" and pygame.K_1 <= key <= pygame.K_4:
            self.choose(key - pygame.K_1)
        if self.screen == "level" and self.sim and self.focus < len(self.sim.choices):
            self.selected_choice = self.focus

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.quit()
        elif event.type == pygame.KEYDOWN:
            self.input_device = "keyboard"
            self.menu_key(event.key)
        elif event.type == pygame.WINDOWFOCUSLOST and self.screen == "game":
            self.goto("pause")
        elif event.type == pygame.MOUSEMOTION and self.screen != "game":
            self.input_device = "mouse"
            pos = self.mouse_position(event.pos)
            if self.screen == "talents":
                self.progression_ui.tree.hover(self, pos)
            for index, button in enumerate(self.buttons):
                if button.rect.collidepoint(pos):
                    self.focus = index
                    if self.screen == "level" and self.sim and index < len(self.sim.choices):
                        self.selected_choice = index
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.screen != "game":
            self.input_device = "mouse"
            pos = self.mouse_position(event.pos)
            for index, button in enumerate(self.buttons):
                if button.rect.collidepoint(pos):
                    self.focus = index
                    button.action()
                    break
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 3
            and self.screen == "level"
            and self.sim
        ):
            self.input_device = "mouse"
            pos = self.mouse_position(event.pos)
            for index, button in enumerate(self.buttons[: len(self.sim.choices)]):
                if button.rect.collidepoint(pos):
                    self.focus = self.selected_choice = index
                    self.power_details()
                    break
        elif event.type == pygame.JOYDEVICEADDED:
            self.add_joystick(event.device_index)
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.joysticks.pop(event.instance_id, None)
        elif event.type == pygame.JOYBUTTONDOWN:
            self.input_device = "controller"
            if event.button == 0:
                self.menu_key(pygame.K_SPACE if self.screen == "game" else pygame.K_RETURN)
            elif event.button in (1, 7):
                self.menu_key(pygame.K_ESCAPE)
            elif event.button == 2 and self.screen == "level":
                self.reroll()
            elif event.button == 3 and self.screen == "level":
                self.banish()
            elif event.button == 4 and self.screen == "level":
                self.power_details()
        elif event.type == pygame.JOYHATMOTION and self.screen != "game":
            self.input_device = "controller"
            x, y = event.value
            if x or y:
                self.menu_key(
                    pygame.K_RIGHT
                    if x > 0
                    else pygame.K_LEFT
                    if x < 0
                    else pygame.K_UP
                    if y > 0
                    else pygame.K_DOWN
                )

    def analog(self) -> Vector2:
        for stick in self.joysticks.values():
            if stick.get_numaxes() >= 2:
                move = analog_direction(stick.get_axis(0), stick.get_axis(1))
                if move.length_squared() > 0:
                    return move
        return Vector2()

    def movement(self) -> Vector2:
        keys = pygame.key.get_pressed()
        keyboard = keyboard_direction(
            bool(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            bool(keys[pygame.K_d] or keys[pygame.K_RIGHT]),
            bool(keys[pygame.K_w] or keys[pygame.K_UP]),
            bool(keys[pygame.K_s] or keys[pygame.K_DOWN]),
        )
        if keyboard.length_squared():
            return keyboard
        if pygame.mouse.get_pressed()[0] and self.sim:
            cursor = self.mouse_position(pygame.mouse.get_pos()) + self.sim.camera.pos
            return cursor_direction(cursor, self.sim.player.pos)
        return self.analog()

    def update(self, dt: float, movement: Vector2 | None = None) -> None:
        if self.notifications:
            message, remaining = self.notifications[0]
            if remaining <= dt:
                self.notifications.pop(0)
            else:
                self.notifications[0] = (message, remaining - dt)
        self.axis_timer = max(0, self.axis_timer - dt)
        if self.screen != "game" and self.axis_timer <= 0:
            axis = self.analog()
            if axis.length() > 0.5:
                key = (
                    pygame.K_DOWN
                    if axis.y > 0.5
                    else pygame.K_UP
                    if axis.y < -0.5
                    else pygame.K_RIGHT
                    if axis.x > 0
                    else pygame.K_LEFT
                )
                self.menu_key(key)
                self.axis_timer = 0.22
        if self.screen == "game" and self.sim and self.debug.time_entry is None:
            self.accumulator += min(dt, 0.25) * self.debug.speed
            while self.accumulator + 1e-10 >= FIXED_DT and self.screen == "game":
                move = movement if movement is not None else self.movement()
                self.sim.step(FIXED_DT, move)
                self.accumulator = max(0, self.accumulator - FIXED_DT)
                if self.sim.finished:
                    self.end_run()
                elif self.sim.choices:
                    self.goto("level")
        self.audio.enabled = self.save.data["settings"]["sound"]
        self.audio.music_volume = self.save.data["settings"]["music_volume"]
        self.audio.sound_volume = self.save.data["settings"]["sound_volume"]
        self.audio.music(
            self.sim.zone.music
            if self.screen in {"game", "level", "pause", "results"} and self.sim
            else self.selected_zone
        )
        if self.sim:
            self.ui_sound_events.extend(self.sim.sound_events)
            self.sim.sound_events.clear()
        self.audio.play(self.ui_sound_events, dt)

    def draw(self) -> None:
        r = self.renderer
        r.activation_label = self.activation_label()
        r.quality = self.save.data["settings"].get("effects_quality", "medium")
        r.camera_shake = self.save.data["settings"].get("screen_shake", False)
        r.presentation.density = self.save.data["settings"]["effects_density"]
        if self.screen in ("game", "pause", "level") and self.sim:
            r.draw_game(self.sim, self.clock.get_fps(), self.debug.overlay)
            if self.debug.enabled:
                r.text(
                    f"DEVELOPMENT  /  {self.debug.speed}x  /  Invulnerable: {'ON' if self.sim.player.invulnerable else 'OFF'}",
                    (360, 96),
                    20,
                    GOLD,
                )
                r.text(
                    "F3 stats / F4 speed / F5 XP / F6 spawn / F7 kill / F8 immune / F9 wave / F10 elite / F11 boss / F12 gold / T time",
                    (640, 595),
                    17,
                    GOLD,
                    True,
                )
                if self.debug.time_entry is not None:
                    r.panel(Rect(360, 280, 560, 130))
                    r.text("Jump to MM:SS or seconds", (390, 300), 30, GOLD)
                    r.text(self.debug.time_entry + "_", (390, 342), 36, CREAM)
                    r.text(
                        "Enter applies / Escape cancels · simulation paused", (390, 380), 20, MUTED
                    )
            if self.screen != "game":
                r.canvas.blit(r.veil, (0, 0))
                r.text(
                    (
                        "Treasure of the champion"
                        if self.sim.chest_choice
                        else "Choose your next power"
                    )
                    if self.screen == "level"
                    else "A moment of respite",
                    (640, 130),
                    48,
                    CREAM,
                    True,
                )
                if self.screen == "level":
                    r.text(
                        f"LEVEL {self.sim.player.level}  /  Gameplay is paused",
                        (640, 180),
                        24,
                        GOLD,
                        True,
                    )
        elif self.screen == "upgrade_details":
            self.upgrade_ui.draw_details(self)
        elif self.screen == "spellbook":
            self.upgrade_ui.draw_spellbook(self)
        elif self.screen in SCREENS:
            self.progression_ui.draw(self)
        elif self.screen == "main":
            r.canvas.blit(r.menu_background, (0, 0))
            r.text("WARCRAFT", (76, 90), 64, GOLD)
            r.text("SURVIVORS", (74, 144), 86, CREAM)
            r.text("SIX CLASSES  /  FIVE SURVIVAL ZONES", (81, 224), 24, MUTED)
            r.text(f"Selected: {self.content.zones[self.selected_zone].name}", (80, 274), 24, GOLD)
            r.text(f"Gold {self.save.data['gold']:,} · Permanent progression", (680, 265), 24, GOLD)
            r.panel(Rect(650, 300, 546, 278))
            r.text("Forge your own arsenal.", (680, 330), 36, GOLD)
            r.wrapped(
                "Survive thirty minutes of escalating hordes. Evolve your arsenal with elite chests, then defeat your zone's final boss to win. Failed runs keep earned class XP and gold.",
                Rect(681, 386, 478, 130),
                28,
                CREAM,
            )
            r.text("WASD / arrows / held mouse / left stick", (681, 542), 22, MUTED)
            r.text(
                "Development tools enabled"
                if self.debug.enabled
                else "Private educational prototype",
                (80, 645),
                22,
                GOLD if self.debug.enabled else MUTED,
            )
        elif self.screen == "zones":
            r.backdrop(
                "Choose your expedition",
                "Large finite maps · 30-minute waves · five elites · defeat the final boss to win",
            )
            for index, zone in enumerate(self.content.zones.values()):
                rect = self.buttons[index].rect
                r.panel(rect, self.focus == index)
                r.text(zone.name, (rect.x + 18, rect.y + 18), 30, GOLD)
                r.wrapped(zone.description, Rect(rect.x + 18, rect.y + 57, 214, 55), 21, CREAM)
                boss = self.content.bosses[zone.boss_pool[0]]
                frame = r.assets.actor(boss.sprite, "idle", "south", pygame.time.get_ticks() / 1000)
                r.canvas.blit(frame.image, frame.at(Vector2(rect.right - 52, rect.y + 146)))
                r.text(
                    f"Threat rating {zone.difficulty:.2f}", (rect.x + 18, rect.y + 122), 23, MUTED
                )
                r.wrapped(
                    boss.name.split(" - ")[0], Rect(rect.x + 18, rect.y + 159, 300, 30), 22, GOLD
                )
            r.button(self.buttons[-1].rect, "Back", selected=self.focus == len(self.buttons) - 1)
        elif self.screen == "classes":
            r.backdrop(
                "Choose your champion",
                f"{self.content.zones[self.selected_zone].name} · Page {self.class_page + 1}/{(len(load_progression().classes) + 5) // 6} · Select an available champion to begin",
            )
            entries = list(load_progression().classes.values())[
                self.class_page * 6 : self.class_page * 6 + 6
            ]
            for index, entry in enumerate(entries):
                rect = self.buttons[index].rect
                if not entry.playable:
                    future_card(self, entry, rect, self.focus == index)
                    continue
                cls = self.content.classes[entry.id]
                r.panel(rect, self.focus == index)
                frame = r.assets.actor(cls.id, "idle", "south", pygame.time.get_ticks() / 1000)
                r.canvas.blit(frame.image, frame.at(Vector2(rect.right - 52, rect.y + 108)))
                r.text(cls.name, (rect.x + 20, rect.y + 20), 34, GOLD)
                r.text(
                    f"Class level {class_level(self.save.data['classes'][cls.id]['xp'])} · {self.save.talent_points(cls.id)} talent points",
                    (rect.x + 20, rect.y + 72),
                    22,
                    CREAM,
                )
                r.text(
                    f"{cls.health:g} base health · {cls.armor:.0%} armor",
                    (rect.x + 20, rect.y + 101),
                    20,
                    MUTED,
                )
                r.wrapped(
                    "Starts with " + self.content.abilities[cls.abilities[0]].name,
                    Rect(rect.x + 20, rect.y + 137, 300, 50),
                    22,
                    CREAM,
                )
            for index in range(len(entries), len(self.buttons)):
                button = self.buttons[index]
                r.button(button.rect, button.label, selected=self.focus == index)
        elif self.screen == "settings":
            r.backdrop("Make yourself at home", "Movement devices work without changing settings.")
            r.panel(Rect(800, 194, 416, 352))
            r.wrapped(
                f"Move: WASD, arrows, held left mouse, or left stick. Manual: {self.activation_label()}. Pause: Escape / Start. Menus: arrows, Enter, mouse, or controller. Level cards: 1–4. Reroll: R / {self.pad_labels().reroll}. Banish focused card: B / {self.pad_labels().banish}. Details: Q / {self.pad_labels().details} / right-click.",
                Rect(820, 224, 372, 240),
                28,
                MUTED,
            )
        elif self.screen == "results" and self.sim:
            sim = self.sim
            result = self.result or {}
            boss_name = (
                self.content.bosses[sim.boss.boss_id].name.split(" - ")[0]
                if sim.boss
                else "Final boss"
            )
            title = (
                f"Victory - {boss_name} defeated"
                if sim.won
                else f"Defeated in {sim.zone.name}"
                if sim.outcome == "death"
                else "Expedition ended"
            )
            r.backdrop(title, "Your earned progression survives an unsuccessful run.")
            r.panel(Rect(64, 195, 1150, 340))
            values = (
                ("SURVIVAL TIME", f"{int(sim.elapsed) // 60:02}:{int(sim.elapsed) % 60:02}"),
                ("PLAYER LEVEL", str(sim.player.level)),
                ("ENEMIES KILLED", str(sim.kills)),
                ("ELITES DEFEATED", str(sim.elites)),
                ("BOSS RESULT", sim.boss_result.replace("_", " ").upper()),
                ("GOLD EARNED", str(result.get("gold", 0))),
                ("PERMANENT CLASS XP", str(result.get("class_xp", 0))),
                ("CLASS", self.content.classes[sim.class_id].name),
            )
            for index, (label, value) in enumerate(values):
                x = 92 + (index % 4) * 284
                y = 218 + (index // 4) * 115
                r.text(label, (x, y), 20, MUTED)
                r.text(value, (x, y + 34), 32 if index == 4 else 42, GOLD)
            achievements = result.get("achievements", [])
            text = "Achievements: " + (
                (
                    f"{len(achievements)} new · "
                    + ", ".join(ACHIEVEMENTS[a][0] for a in achievements[:3])
                    + ". View the chronicle for all rewards."
                )
                if len(achievements) > 6
                else ", ".join(ACHIEVEMENTS[a][0] for a in achievements)
                if achievements
                else "None newly earned"
            )
            r.wrapped(text, Rect(92, 456, 1060, 56), 22, CREAM)
            r.text(
                "Debug run: no statistics or rewards saved."
                if not result.get("recorded", False)
                else "Progress saved locally."
                if result.get("saved", False)
                else self.save.notice or "Progress could not be saved.",
                (92, 565),
                22,
                MUTED,
            )
        if self.screen == "level" and self.sim:
            self.upgrade_ui.draw_cards(self)
        elif (
            self.screen not in {"classes", "zones", "spellbook", "upgrade_details"}
            and self.screen not in SCREENS
        ):
            for index, button in enumerate(self.buttons):
                r.button(button.rect, button.label, selected=self.focus == index)
        if self.save.notice:
            r.text(self.save.notice, (640, 680), 20, (244, 143, 107), True)
        if self.notifications:
            r.panel(Rect(650, 16, 558, 68))
            r.wrapped(self.notifications[0][0], Rect(668, 34, 522, 42), 23, GOLD)
        width, height = self.display.get_size()
        scale = min(width / 1280, height / 720)
        self.viewport = Rect(0, 0, max(1, round(1280 * scale)), max(1, round(720 * scale)))
        self.viewport.center = (width // 2, height // 2)
        self.display.fill((6, 12, 16))
        self.display.blit(pygame.transform.scale(r.canvas, self.viewport.size), self.viewport)
        pygame.display.flip()

    def run(
        self,
        frames: int = 0,
        demo: bool = False,
        screenshot: Path | None = None,
        smoke: bool = False,
    ) -> None:
        if demo:
            self.start_run()
        count = 0
        while self.running and (frames == 0 or count < frames):
            dt = FIXED_DT if smoke else self.clock.tick(60) / 1000
            for event in pygame.event.get():
                self.handle_event(event)
            if smoke and self.screen == "level":
                self.choose(0)
            self.update(dt, Vector2(1, 0) if smoke else None)
            self.draw()
            count += 1
        if screenshot:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.renderer.canvas, str(screenshot))
        if smoke:
            print(f"Smoke OK: {count} frames, screen={self.screen}, class={self.selected_class}")
            if self.renderer.assets.warnings:
                raise RuntimeError(
                    "Packaged asset loading failed: " + "; ".join(self.renderer.assets.warnings)
                )
            if not self.audio.available or len(self.audio.sounds) != 21:
                raise RuntimeError(
                    "Packaged audio validation failed; expected all 21 original cues and working dummy playback"
                )
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Warcraft Survivors — Milestone 5")
    parser.add_argument(
        "--zone",
        choices=("elwynn", "duskwood", "stranglethorn", "plaguelands", "icecrown"),
        default="elwynn",
    )
    parser.add_argument("--seed", type=int, default=int(time.time()))
    parser.add_argument("--demo", action="store_true", help="Start playing immediately")
    parser.add_argument(
        "--class",
        dest="class_id",
        choices=("paladin", "warrior", "mage", "hunter", "warlock", "priest"),
        default="paladin",
    )
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument(
        "--encounter-smoke",
        action="store_true",
        help="Bounded headless boss QA; requires --smoke-test",
    )
    parser.add_argument(
        "--progression-smoke",
        "--screen-smoke",
        choices=(
            "main",
            "classes",
            "zones",
            "settings",
            "progression",
            "talents",
            "shop",
            "achievements",
            "unlocks",
        ),
        help="Bounded headless progression UI QA; requires --smoke-test",
    )
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--save-dir", type=Path)
    parser.add_argument("--debug", action="store_true", help="Source-only developer tools")
    parser.add_argument(
        "--release", action="store_true", help="Enforce release protection in source runs"
    )
    args = parser.parse_args()
    if args.encounter_smoke and not args.smoke_test:
        parser.error("Encounter QA requires --smoke-test")
    if args.progression_smoke and (not args.smoke_test or args.encounter_smoke):
        parser.error("Progression QA requires --smoke-test and cannot combine with encounter QA")
    if args.debug and not debug_allowed(True, args.release):
        parser.error("Developer tools are disabled in release and packaged builds")
    if args.headless or args.smoke_test:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    save_dir = args.save_dir or (Path("artifacts/smoke/save") if args.smoke_test else None)
    save = SaveStore(save_dir / "save.json" if save_dir else None)
    if args.smoke_test:
        save.data["settings"]["fullscreen"] = False
    app = App(save, args.seed, args.debug, args.release)
    app.selected_class = args.class_id
    app.selected_zone = args.zone
    if args.progression_smoke:
        app.goto(args.progression_smoke)
    if args.encounter_smoke:
        app.start_run()
        assert app.sim is not None
        app.sim.time = 1799.5
        app.sim.director.seek(1799.5)
        app.sim.spawner.wave_start = app.sim.director.wave(1799.5).start
        app.sim.debug_used = True
        app.sim.player.invulnerable = True
    app.run(
        args.frames or (180 if args.smoke_test else 0),
        (args.demo or args.smoke_test) and not args.encounter_smoke and not args.progression_smoke,
        args.screenshot,
        args.smoke_test,
    )
    if args.encounter_smoke:
        assert app.sim is not None and app.sim.boss is not None
        assert app.sim.time == 1800 and app.sim.boss_time > 0 and not app.sim.won


if __name__ == "__main__":
    main()
