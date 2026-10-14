"""Layered cached raster art, chunked terrain and a readable fantasy interface."""

from __future__ import annotations

import math
import random
from collections import OrderedDict
from pathlib import Path

import pygame
from pygame import Rect, Surface, Vector2

from .asset_manager import AssetManager, Frame, facing
from .content import Content
from .manuals import manual_cooldown
from .presentation import Presentation
from .simulation import Simulation
from .world import CHUNK_SIZE, VIEW_SIZE, World

GOLD = (222, 186, 115)
CREAM = (239, 234, 213)
MUTED = (150, 171, 173)


class Renderer:
    def __init__(self, content: Content, asset_root: Path | None = None) -> None:
        self.content = content
        self.assets = AssetManager(asset_root)
        self.presentation = Presentation(self.assets.manifest.get("projectiles", {}))
        self.quality = "medium"
        self.activation_label = "Space / ability button"
        self.camera_shake = False
        self.panel_cache: dict[tuple[int, int, bool], Surface] = {}
        self.trees = [Frame(self.assets.image(f"tree_{i}"), (80, 180)) for i in range(3)]
        self.zone_props = {
            z.id: [Frame(self.assets.image(name), (96, 214)) for name in z.props]
            for z in content.zones.values()
        }
        self.tree_shadow = pygame.transform.scale(self.assets.image("shadow"), (88, 30))
        self.ground_bush = pygame.transform.scale(self.assets.image("bush"), (28, 22))
        self.canvas = Surface(VIEW_SIZE)
        self.fonts = {
            size: pygame.font.Font(None, size)
            for size in (15, 16, 17, 18, 19, 20, 22, 23, 24, 28, 30, 32, 34, 36, 48, 64, 86)
        }
        self.text_cache: OrderedDict[tuple[str, int, tuple[int, int, int]], Surface] = OrderedDict()
        self.chunks: OrderedDict[tuple[str, int, int, int], Surface] = OrderedDict()
        self.menu_background = self.make_background()
        self.veil = Surface(VIEW_SIZE, pygame.SRCALPHA)
        self.veil.fill((7, 12, 19, 205))

    def text(
        self,
        message: str,
        pos: tuple[float, float] | Vector2,
        size: int = 24,
        color: tuple[int, int, int] = CREAM,
        center: bool = False,
    ) -> None:
        key = (message, size, color)
        if key not in self.text_cache:
            if size not in self.fonts:
                self.fonts[size] = pygame.font.Font(None, size)
            self.text_cache[key] = self.fonts[size].render(message, True, color)
            if len(self.text_cache) > 512:
                self.text_cache.popitem(last=False)
        surf = self.text_cache[key]
        rect = (
            surf.get_rect(center=(round(pos[0]), round(pos[1])))
            if center
            else surf.get_rect(topleft=(round(pos[0]), round(pos[1])))
        )
        self.canvas.blit(surf, rect)

    def wrapped(
        self, message: str, rect: Rect, size: int = 24, color: tuple[int, int, int] = MUTED
    ) -> None:
        while True:
            if size not in self.fonts:
                self.fonts[size] = pygame.font.Font(None, size)
            lines: list[str] = []
            line = ""
            for word in message.split():
                trial = (line + " " + word).strip()
                if self.fonts[size].size(trial)[0] > rect.width and line:
                    lines.append(line)
                    line = word
                else:
                    line = trial
            if line:
                lines.append(line)
            if len(lines) * (size + 3) <= rect.height or size <= 16:
                break
            size -= 1
        for index, line in enumerate(lines):
            if index * (size + 3) + size > rect.height:
                break
            self.text(line, (rect.x, rect.y + index * (size + 3)), size, color)

    def panel(self, rect: Rect, selected: bool = False) -> None:
        key = (rect.width, rect.height, selected)
        if key not in self.panel_cache:
            image = Surface(rect.size, pygame.SRCALPHA)
            texture = self.assets.image("panel_material")
            for x in range(0, rect.width, 128):
                for y in range(0, rect.height, 128):
                    image.blit(texture, (x, y))
            border = GOLD if selected else (95, 105, 96)
            pygame.draw.rect(image, border, image.get_rect(), 2, border_radius=3)
            for x, y, sx, sy in (
                (5, 5, 1, 1),
                (rect.width - 6, 5, -1, 1),
                (5, rect.height - 6, 1, -1),
                (rect.width - 6, rect.height - 6, -1, -1),
            ):
                pygame.draw.line(image, border, (x, y), (x + sx * 12, y), 2)
                pygame.draw.line(image, border, (x, y), (x, y + sy * 12), 2)
            self.panel_cache[key] = image
        self.canvas.blit(self.panel_cache[key], rect)

    def button(
        self, rect: Rect, label: str, detail: str = "", selected: bool = False, enabled: bool = True
    ) -> None:
        self.panel(rect, selected)
        self.text(
            label,
            (rect.x + 22, rect.y + (15 if detail else max(5, (rect.height - 28) // 2))),
            28,
            CREAM if enabled else MUTED,
        )
        if detail:
            self.text(detail, (rect.x + 22, rect.y + 46), 20, MUTED)

    def make_background(self) -> Surface:
        surf = Surface(VIEW_SIZE)
        for y in range(VIEW_SIZE[1]):
            t = y / VIEW_SIZE[1]
            pygame.draw.line(
                surf, (round(14 - t * 5), round(29 - t * 10), round(39 - t * 14)), (0, y), (1280, y)
            )
        rng = random.Random(17)
        for layer in range(3):
            for x in range(-100, 1350, 100):
                original = self.assets.image(f"tree_{rng.randrange(3)}")
                height = (180, 260, 340)[layer] + rng.randrange(-30, 30)
                tree = pygame.transform.scale(
                    original, (round(original.get_width() * height / original.get_height()), height)
                )
                shade = (
                    (72, 92, 108, 255)
                    if layer == 0
                    else (112, 131, 133, 255)
                    if layer == 1
                    else (142, 158, 152, 255)
                )
                tree.fill(shade, special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(tree, (x, 480 + layer * 85 - height))
        mist = Surface(VIEW_SIZE, pygame.SRCALPHA)
        for y in range(720):
            pygame.draw.line(mist, (9, 17, 27, round(100 * (1 - y / 720))), (0, y), (1280, y))
        surf.blit(mist, (0, 0))
        return surf

    def backdrop(self, title: str, subtitle: str = "") -> None:
        self.canvas.blit(self.menu_background, (0, 0))
        self.text("WARCRAFT  /  SURVIVORS", (64, 36), 22, GOLD)
        self.text(title, (64, 74), 48)
        self.text(subtitle, (66, 122), 22, MUTED)
        pygame.draw.line(self.canvas, (71, 95, 92), (64, 158), (1216, 158))

    def chunk(self, x: int, y: int, world: World) -> Surface:
        key = (world.zone_id, world.seed, x, y)
        if key in self.chunks:
            self.chunks.move_to_end(key)
            return self.chunks[key]
        rng = random.Random(world.seed + x * 73856093 + y * 19349663)
        surf = Surface((CHUNK_SIZE, CHUNK_SIZE))
        for tx in range(0, CHUNK_SIZE, 16):
            for ty in range(0, CHUNK_SIZE, 16):
                pos = Vector2(x * 256 + tx, y * 256 + ty)
                road = world.on_road(pos)
                zone = self.content.zones[world.zone_id]
                name = (
                    f"{'road' if road else 'grass'}_{rng.randrange(4)}"
                    if world.zone_id == "elwynn"
                    else zone.road
                    if road
                    else zone.ground
                )
                texture = self.assets.image(name)
                count = texture.get_width() // 16
                surf.blit(
                    texture,
                    (tx, ty),
                    (rng.randrange(count) * 16, rng.randrange(count) * 16, 16, 16),
                )
        for _ in range(4):
            px, py = rng.randrange(16, 240), rng.randrange(16, 240)
            if world.zone_id == "elwynn" and not world.on_road(Vector2(x * 256 + px, y * 256 + py)):
                surf.blit(self.ground_bush, (px, py))
        self.chunks[key] = surf
        if len(self.chunks) > 70:
            self.chunks.popitem(last=False)
        return surf

    def bar(self, rect: Rect, fraction: float, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(self.canvas, (11, 21, 25), rect, border_radius=3)
        filled = rect.copy()
        filled.width = max(0, round(rect.width * min(1, max(0, fraction))))
        if filled.width:
            pygame.draw.rect(self.canvas, color, filled, border_radius=3)
        pygame.draw.rect(self.canvas, (89, 106, 103), rect, 1, border_radius=3)

    def draw_game(self, sim: Simulation, fps: float = 60, debug: bool = False) -> None:
        self.presentation.quality = self.quality
        self.presentation.observe(sim)
        p = sim.player
        camera = (
            sim.camera.pos + self.presentation.shake.offset()
            if self.camera_shake
            else sim.camera.pos
        )
        for x in range(int(camera.x // 256), int((camera.x + 1280) // 256) + 1):
            for y in range(int(camera.y // 256), int((camera.y + 720) // 256) + 1):
                self.canvas.blit(
                    self.chunk(x, y, sim.world), (x * 256 - camera.x, y * 256 - camera.y)
                )
        visible = Rect(-120, -200, 1520, 1120)
        for field in sim.combat.fields:
            pos = field.pos - camera
            if not visible.collidepoint(pos):
                continue
            ability = sim.content.ability(field.ability)
            if ability.kind == "beam" or field.repeat_arc:
                continue
            radius = field.radius
            if field.wave:
                from .combat import spell_stats

                radius *= min(
                    1,
                    field.age / spell_stats(ability, sim.player.spells[field.ability], p).duration,
                )
            frame = self.assets.scaled_effect(field.ability, field.age, radius * 2, opacity=145)
            self.canvas.blit(frame.image, frame.at(pos))
            if field.delay > 0:
                pygame.draw.circle(self.canvas, ability.color, pos, round(radius), 2)
                self.text("IMPACT", pos, 18, ability.color, True)
        visible_enemies = [
            e
            for e in sim.grid.nearby(camera + Vector2(640, 360), 960)
            if visible.collidepoint(e.pos - camera)
        ]
        # Gameplay telegraphs are drawn at every quality level, below actors.
        for hazard in sim.enemy_combat.attacks:
            a = sim.content.attacks[hazard.attack]
            pos = hazard.pos - camera
            if not visible.inflate(int(a.reach * 2), int(a.reach * 2)).collidepoint(pos):
                continue
            color = a.color
            fraction = 1 - hazard.warning / a.warning if hazard.warning > 0 else 1
            width = 2 if hazard.warning > 0 else 4
            if a.kind == "charge":
                end = pos + hazard.direction * a.reach
                normal = hazard.direction.rotate(90) * a.radius
                pygame.draw.polygon(
                    self.canvas,
                    color,
                    [pos + normal, end + normal, end - normal, pos - normal],
                    width,
                )
                pygame.draw.line(
                    self.canvas, color, pos, pos + hazard.direction * a.reach * fraction, 2
                )
            elif a.kind == "arc":
                points = [pos] + [
                    pos + hazard.direction.rotate(-a.angle / 2 + i * a.angle / 16) * a.radius
                    for i in range(17)
                ]
                pygame.draw.lines(self.canvas, (10, 18, 24), True, points, width + 2)
                pygame.draw.lines(self.canvas, color, True, points, width)
            elif a.kind == "missile":
                end = pos + hazard.direction * min(a.reach, 150)
                pygame.draw.line(self.canvas, color, pos, end, 2)
            else:
                radius = a.radius * (
                    min(1, hazard.age / a.duration) if a.kind == "ring" and hazard.started else 1
                ) + (a.growth * hazard.age if hazard.started else 0)
                if hazard.started and a.kind == "circle":
                    effect = (
                        a.effect + "_field"
                        if a.effect in {"hostile_frost", "hostile_poison", "hostile_shadow"}
                        else "impact_holy"
                    )
                    frame = self.assets.scaled_effect(effect, hazard.age, radius * 2, opacity=90)
                    self.canvas.blit(frame.image, frame.at(pos))
                pygame.draw.circle(self.canvas, (10, 18, 24), pos, max(1, round(radius)), width + 2)
                pygame.draw.circle(self.canvas, color, pos, max(1, round(radius)), width)
                if hazard.warning > 0:
                    pygame.draw.circle(
                        self.canvas, color, pos, max(1, round(a.radius * fraction)), 1
                    )
            if hazard.owner.elite or hazard.owner.boss_id:
                self.text(a.name.upper(), pos + Vector2(0, -a.radius - 20), 18, color, True)
        actors: list[tuple[float, Frame, Vector2]] = []
        shadows = []
        bars = []
        for obstacle in sim.world.grid.nearby(camera + Vector2(640, 360), 960):
            pos = obstacle.pos - camera
            if visible.collidepoint(pos):
                frame = (
                    self.trees[obstacle.style]
                    if sim.zone.id == "elwynn" and obstacle.style < 3
                    else self.zone_props[sim.zone.id][obstacle.style]
                )
                actors.append((pos.y, frame, pos))
                shadows.append((self.tree_shadow, (round(pos.x - 44), round(pos.y - 9))))
        for landmark in sim.zone.landmarks:
            pos = Vector2(landmark.x, landmark.y) - camera
            if visible.collidepoint(pos):
                if not landmark.radius:
                    frame = self.zone_props[sim.zone.id][landmark.style]
                    self.canvas.blit(frame.image, frame.at(pos))
                self.text(landmark.name, pos + Vector2(0, 24), 18, GOLD, True)
        shadow = self.assets.image("shadow")
        for enemy in visible_enemies:
            pos = enemy.pos - camera
            if not visible.collidepoint(pos):
                continue
            view = self.presentation.actors.get(enemy.id)
            direction = view.direction if view else "south"
            state = "cast" if enemy.busy > 0 else "walk" if view is None or view.moving else "idle"
            frame = self.assets.actor(
                enemy.sprite or enemy.kind,
                state,
                facing(enemy.facing) if enemy.busy > 0 else direction,
                enemy.cast_age if enemy.busy > 0 else sim.elapsed + enemy.id * 0.13,
                enemy.flash > 0,
            )
            actors.append((pos.y, frame, pos))
            shadows.append((shadow, (round(pos.x - 21), round(pos.y - 8))))
            if enemy.elite:
                self.text("ELITE", pos + Vector2(0, -80), 18, GOLD, True)
                pygame.draw.circle(self.canvas, GOLD, pos, round(enemy.radius + 4), 2)
            if not enemy.boss_id and enemy.health < enemy.max_health:
                bars.append(
                    (
                        Rect(round(pos.x - 15), round(pos.y - frame.anchor[1] - 7), 30, 4),
                        enemy.health / enemy.max_health,
                    )
                )
        for pet in sim.combat.companions:
            pos = pet.pos - camera
            if visible.collidepoint(pos):
                state = (
                    "cast"
                    if pet.attack_time > 0
                    else "walk"
                    if pet.moving or pet.life >= 0
                    else "idle"
                )
                frame = self.assets.actor(
                    pet.sprite,
                    state,
                    facing(pet.facing),
                    0.3 - pet.attack_time if pet.attack_time > 0 else sim.elapsed,
                    allied=True,
                )
                actors.append((pos.y, frame, pos))
                shadows.append((shadow, (round(pos.x - 21), round(pos.y - 8))))
                pygame.draw.ellipse(
                    self.canvas,
                    (110, 164, 171),
                    Rect(round(pos.x - 13), round(pos.y - 3), 26, 9),
                    1,
                )
                if pet.life >= 0:
                    self.text("SUMMON", pos + Vector2(0, 10), 15, (127, 213, 218), True)
        center = p.pos - camera
        shadows.append((shadow, (round(center.x - 21), round(center.y - 8))))
        self.canvas.blits(shadows)
        for pickup in sim.pickups.values():
            pos = pickup.pos - camera
            if visible.collidepoint(pos):
                frame = (
                    Frame(self.assets.image("chest"), (20, 18))
                    if pickup.kind == "chest"
                    else self.assets.scaled_effect("lay_on_hands", sim.elapsed, 32)
                    if pickup.kind in {"heal", "healing"}
                    else self.assets.effect(
                        "xp" if pickup.kind == "xp" else "gold", sim.elapsed, loop=True
                    )
                )
                self.canvas.blit(frame.image, frame.at(pos))
        for death in self.presentation.deaths:
            pos = death.pos - camera
            if visible.collidepoint(pos):
                frame = self.assets.actor(death.kind, "death", death.direction, death.age)
                actors.append((pos.y, frame, pos))
        self.canvas.blits(
            [(frame.image, frame.at(pos)) for _, frame, pos in sorted(actors, key=lambda a: a[0])]
        )
        state, clock = self.presentation.player_state(sim)
        frame = self.assets.actor(sim.class_id, state, facing(p.facing), clock, p.hurt_timer > 0)
        self.canvas.blit(frame.image, frame.at(center))
        for rect, fraction in bars:
            self.bar(rect, fraction, (185, 83, 68))
        for enemy in visible_enemies:
            pos = enemy.pos - camera
            if visible.collidepoint(pos) and enemy.statuses:
                for index, aid in enumerate(list(enemy.statuses)[:3]):
                    frame = self.assets.scaled_effect(aid, sim.elapsed, 24)
                    self.canvas.blit(frame.image, frame.at(pos + Vector2((index - 1) * 20, -70)))
                if len(enemy.statuses) > 3:
                    self.text(f"+{len(enemy.statuses) - 3}", pos + Vector2(35, -70), 16, MUTED)
        for hostile in sim.enemy_combat.projectiles:
            pos = hostile.pos - camera
            if visible.collidepoint(pos):
                frame = self.assets.projectile(
                    hostile.effect, 1, sim.elapsed, hostile.velocity.as_polar()[1] - 45
                )
                self.canvas.blit(frame.image, frame.at(pos))
        for shot in sim.projectiles:
            pos = shot.pos - camera
            if visible.collidepoint(pos):
                spell_state = p.spells.get(shot.ability)
                frame = self.assets.projectile(
                    shot.ability,
                    spell_state.rank if spell_state else 8,
                    sim.elapsed,
                    shot.velocity.as_polar()[1]
                    - 45
                    + sim.elapsed
                    * self.assets.manifest.get("projectiles", {})
                    .get(shot.ability, {})
                    .get("spin_degrees", 90),
                )
                self.canvas.blit(frame.image, frame.at(pos))
        self.canvas.blits(
            [
                (
                    self.assets.image(self.presentation.particles.particles[i].sprite),
                    (
                        round(self.presentation.particles.particles[i].pos.x - camera.x - 3),
                        round(self.presentation.particles.particles[i].pos.y - camera.y - 3),
                    ),
                )
                for i in self.presentation.particles.active
            ]
        )
        for visual in sim.visuals:
            pos = visual.pos - camera
            if visible.collidepoint(pos):
                visual_ability = (
                    self.content.ability(visual.effect)
                    if visual.effect in self.content.abilities
                    or visual.effect in self.content.evolutions
                    else None
                )
                diameter = (
                    visual.radius * 2
                    if visual_ability and visual_ability.kind in {"arc", "area", "field", "wave"}
                    else min(72, visual.radius * 2)
                )
                frame = (
                    self.assets.scaled_effect(
                        visual.effect,
                        visual.total - visual.life,
                        diameter,
                        visual.direction.as_polar()[1]
                        if visual.effect in self.assets.manifest.get("directional_effects", [])
                        else None,
                        opacity=165,
                    )
                    if visual.effect
                    else self.assets.effect("holy_impact", visual.total - visual.life, 18)
                )
                if visual.end is not None:
                    pygame.draw.line(
                        self.canvas,
                        tuple(c // 3 for c in visual.color),
                        pos,
                        visual.end - camera,
                        7,
                    )
                    pygame.draw.line(self.canvas, visual.color, pos, visual.end - camera, 3)
                self.canvas.blit(frame.image, frame.at(pos))
        if p.manual and p.manual.circle is not None:
            pos = p.manual.circle - camera
            if visible.collidepoint(pos):
                frame = self.assets.scaled_effect(p.manual.id, sim.elapsed, 100)
                self.canvas.blit(frame.image, frame.at(pos))
        if p.immune > 0 or p.guard > 0 or p.shield > 0 or p.buff_time > 0:
            effect = p.manual.id if p.manual else "eye_of_tyr"
            frame = self.assets.scaled_effect(effect, sim.elapsed, 96, opacity=180)
            self.canvas.blit(frame.image, frame.at(center))
        # Keep the champion's silhouette readable through overlapping late-game effects.
        state, clock = self.presentation.player_state(sim)
        frame = self.assets.actor(sim.class_id, state, facing(p.facing), clock, p.hurt_timer > 0)
        self.canvas.blit(frame.image, frame.at(center))
        for text in self.presentation.damage:
            pos = text.pos - camera + Vector2(0, -55 - text.age * 35)
            if visible.collidepoint(pos):
                self.text(str(text.amount), pos, 20, GOLD, True)
        self.hud(sim, fps, debug)
        if self.assets.warnings:
            self.text(
                f"Asset repair fallback active ({len(self.assets.warnings)} issues)",
                (640, 570),
                20,
                (244, 143, 107),
                True,
            )

    def hud(self, sim: Simulation, fps: float, debug: bool) -> None:
        p = sim.player
        self.panel(Rect(18, 16, 314, 110))
        self.text(
            f"{self.content.classes[sim.class_id].name}  /  LEVEL {p.level}", (34, 28), 24, GOLD
        )
        self.bar(Rect(34, 59, 282, 18), p.health / p.max_health, (175, 73, 82))
        self.text(f"{math.ceil(p.health)} / {math.ceil(p.max_health)}", (175, 68), 18, CREAM, True)
        self.bar(Rect(34, 87, 282, 8), p.xp / p.xp_required, (85, 183, 199))
        self.text(f"XP {p.xp:.0f} / {p.xp_required:.0f}", (34, 102), 18, MUTED)
        self.panel(Rect(532, 16, 216, 64))
        self.text(f"{int(sim.time) // 60:02}:{int(sim.time) % 60:02}", (640, 42), 36, CREAM, True)
        self.text(
            "FINAL ENCOUNTER" if sim.director.boss_spawned else sim.zone.name.upper(),
            (640, 69),
            18,
            GOLD,
            True,
        )
        if sim.director.boss_spawned and sim.boss and sim.boss.health > 0:
            self.panel(Rect(366, 94, 548, 61))
            self.text(
                self.content.bosses[sim.boss.boss_id].name.split(" - ")[0].upper()
                + ("  /  ENRAGED" if sim.boss.enraged else ""),
                (640, 107),
                22,
                GOLD,
                True,
            )
            self.bar(Rect(385, 123, 510, 18), sim.boss.health / sim.boss.max_health, (183, 63, 50))
            self.text(
                f"{math.ceil(sim.boss.health)} / {math.ceil(sim.boss.max_health)}",
                (640, 132),
                17,
                CREAM,
                True,
            )
            self.panel(Rect(550, 157, 180, 25))
            self.text(
                f"BOSS +{int(sim.boss_time) // 60:02}:{int(sim.boss_time) % 60:02}",
                (640, 169),
                18,
                MUTED,
                True,
            )
        else:
            wave = sim.director.wave(sim.time)
            self.panel(Rect(350, 84, 580, 26))
            self.text(f"WAVE {sim.wave_index + 1} / {wave.name}", (640, 94), 19, GOLD, True)
        self.panel(Rect(974, 16, 288, 68))
        self.text(f"{sim.kills} kills  /  {sim.gold} gold", (1000, 27), 24, CREAM)
        self.text("Esc / Start: pause", (1000, 56), 20, MUTED)
        self.panel(Rect(18, 618, 890, 84))
        for index, (aid, state) in enumerate(p.spells.items()):
            ability = self.content.ability(aid)
            x = 32 + index * 108
            frame = self.assets.scaled_effect(aid, 0, 36)
            self.canvas.blit(frame.image, frame.at(Vector2(x + 18, 643)))
            self.text("EVOLVED" if ability.evolved else f"R{state.rank}", (x + 40, 632), 16, GOLD)
            self.wrapped(ability.name, Rect(x, 663, 102, 35), 17, CREAM)
        self.panel(Rect(930, 618, 332, 84))
        if p.manual:
            manual = self.content.manuals[p.manual.id]
            self.text(f"{self.activation_label} · R{p.manual.rank}", (947, 629), 18, GOLD)
            self.text(manual.name, (947, 650), 23, CREAM)
            status = (
                f"{p.manual.timer:.1f}s"
                if p.manual.timer > 0
                else "RETURN"
                if p.manual.circle is not None
                else "READY"
            )
            self.text(status, (1210, 633), 20, GOLD, True)
            cooldown = manual_cooldown(manual, p.manual.rank, p)
            self.bar(Rect(947, 683, 294, 6), 1 - p.manual.timer / cooldown, (128, 193, 217))
        else:
            self.text("Manual slot empty", (947, 637), 24, MUTED)
            self.text("Discover a manual ability", (947, 670), 20, MUTED)
        if p.passives:
            self.text(
                "  /  ".join(f"{self.content.passives[k].name} {v}" for k, v in p.passives.items()),
                (30, 600),
                17,
                CREAM,
            )
        for index, (message, _) in enumerate(sim.messages):
            y = (185 if sim.director.boss_spawned else 146) + index * 31
            self.panel(Rect(300, y, 680, 29))
            self.wrapped(message, Rect(312, y + 5, 656, 22), 21, CREAM)
        if debug:
            self.text(
                f"{fps:.0f} FPS / {len(sim.enemies)} enemies / {len(sim.projectiles)} shots / {len(sim.combat.fields)} fields / {len(sim.combat.companions)} pets / {len(sim.pickups)} loot",
                (360, 200 if sim.director.boss_spawned else 116),
                20,
                CREAM,
            )
        statuses: list[str] = []
        if p.slow_time > 0:
            statuses.append(f"SLOWED {p.slow_time:.1f}s")
        if p.wound_time > 0:
            statuses.append(f"WOUNDED {p.wound_time:.1f}s")
        if p.immune > 0:
            statuses.append(f"IMMUNE {p.immune:.1f}s")
        if p.shield > 0:
            statuses.append(f"SHIELD {p.shield:.0f}")
        if p.guard > 0:
            statuses.append(f"GUARD {p.guard:.1f}s")
        if p.buff_time > 0:
            statuses.append(f"EMPOWERED {p.buff_time:.1f}s")
        if p.rally_time > 0:
            statuses.append(f"RALLY {p.rally_time:.1f}s")
        if statuses:
            self.panel(Rect(18, 130, 314, 48))
            self.wrapped(" / ".join(statuses), Rect(30, 138, 290, 35), 19, GOLD)
