"""V2 progression profiles, V1 migration, safe recovery and transactional purchases."""

from __future__ import annotations

import copy
import json
import math
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .achievements import COUNT_MAPS, NEW_COUNTS, apply_summary, complete, progress
from .meta import RunLoadout, build_loadout, load_progression, talent_reason
from .meta import class_level as class_level
from .rewards import calculate_rewards
from .run_events import RunSummary

SAVE_VERSION = 2
CLASS_IDS = tuple(cid for cid, c in load_progression().classes.items() if c.playable)


class FutureSave(ValueError):
    pass


def save_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share")))
    return root / "WarcraftSurvivors" / "save.json"


def nonnegative(value: Any, maximum: int = 10**9) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        return 0
    return max(0, min(maximum, value))


def mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


class SaveStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or save_path()
        self.notice = ""
        self.read_only = False
        self.data = self.defaults()
        self.load()

    @staticmethod
    def defaults() -> dict[str, Any]:
        meta = load_progression()
        return dict(
            version=SAVE_VERSION,
            revision=0,
            gold=0,
            unlocked_classes=[cid for cid, entry in meta.classes.items() if not entry.achievement],
            unlocked_zones=list(meta.zones),
            classes={
                cid: dict(xp=0, level=1, talent_points=0, talents={}, starting_ability="")
                for cid in meta.classes
            },
            shared={},
            achievements=[],
            achievement_progress={},
            achievement_completed_at={},
            settled_runs=[],
            settings=dict(
                fullscreen=False,
                sound=True,
                debug=False,
                effects_quality="medium",
                screen_shake=False,
                music_volume=0.35,
                sound_volume=0.7,
                effects_density=1.0,
                resolution="1280x720",
            ),
            stats=dict(
                runs=0,
                kills=0,
                wins=0,
                best_time=0,
                run_kills=0,
                elites=0,
                evolved=0,
                bosses=0,
                boss_kills={"hogger": 0},
                class_wins={cid: 0 for cid in CLASS_IDS},
                class_runs={cid: 0 for cid in CLASS_IDS},
                **{name: {} for name in COUNT_MAPS},
                **{name: 0 for name in NEW_COUNTS},
                evolved_spells=[],
            ),
        )

    @classmethod
    def validate(cls, raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict) or isinstance(raw.get("version"), bool):
            raise ValueError("Invalid save root")
        version = raw.get("version")
        if isinstance(version, int) and version > SAVE_VERSION:
            raise FutureSave("Newer save version")
        if version not in (1, SAVE_VERSION):
            raise ValueError("Unsupported save version")
        meta = load_progression()
        data = cls.defaults()
        data["gold"] = nonnegative(raw.get("gold"))
        data["revision"] = nonnegative(raw.get("revision"))
        for cid in meta.classes:
            old = mapping(mapping(raw.get("classes")).get(cid))
            xp = nonnegative(old.get("xp"))
            wanted = mapping(old.get("talents"))
            clean: dict[str, int] = {}
            tree = meta.trees.get(cid, {})
            # Replay a valid point allocation in topological order. Invalid/over-budget
            # or obsolete ranks are refunded, never destroying earned class XP.
            for tid, talent in tree.items():
                for _ in range(nonnegative(wanted.get(tid), talent.max_rank)):
                    if version == 1 and any(
                        clean.get(parent, 0) < rank
                        for parent, rank in talent.legacy_requires.items()
                    ):
                        break
                    if talent_reason(tree, xp, clean, tid):
                        break
                    clean[tid] = clean.get(tid, 0) + 1
            selected = old.get("starting_ability", "")
            if "preparation" not in clean or selected not in tree["preparation"].starting_options:
                selected = ""
            level = class_level(xp)
            data["classes"][cid] = dict(
                xp=xp,
                level=level,
                talent_points=level - 1 - sum(clean.values()),
                talents=clean,
                starting_ability=selected,
            )
        old_shared = mapping(raw.get("shared"))
        data["shared"] = {
            sid: nonnegative(old_shared.get(sid), u.max_rank)
            for sid, u in meta.shared.items()
            if nonnegative(old_shared.get(sid), u.max_rank)
        }
        achievements = raw.get("achievements", [])
        if isinstance(achievements, list):
            data["achievements"] = list(
                dict.fromkeys(
                    a for a in achievements if isinstance(a, str) and a in meta.achievements
                )
            )
        settings = mapping(raw.get("settings"))
        for key in ("fullscreen", "sound", "screen_shake"):
            if isinstance(settings.get(key), bool):
                data["settings"][key] = settings[key]
        # A saved preference can never opt into developer controls.
        quality = settings.get("effects_quality")
        if quality in ("low", "medium", "high"):
            data["settings"]["effects_quality"] = quality
        for key in ("music_volume", "sound_volume", "effects_density"):
            value = settings.get(key)
            if (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
            ):
                data["settings"][key] = max(0.0, min(1.0, value))
        if settings.get("resolution") in ("1280x720", "1600x900", "1920x1080", "2560x1440"):
            data["settings"]["resolution"] = settings["resolution"]
        stats = mapping(raw.get("stats"))
        for key in (
            "runs",
            "kills",
            "wins",
            "best_time",
            "run_kills",
            "elites",
            "evolved",
            "bosses",
        ):
            data["stats"][key] = nonnegative(stats.get(key))
        for metric in ("class_runs", "class_wins"):
            old = mapping(stats.get(metric))
            data["stats"][metric] = {cid: nonnegative(old.get(cid)) for cid in CLASS_IDS}
        boss_kills = mapping(stats.get("boss_kills"))
        data["stats"]["boss_kills"] = {
            key: nonnegative(value)
            for key, value in boss_kills.items()
            if isinstance(key, str) and 0 < len(key) <= 64
        }
        for name in COUNT_MAPS:
            data["stats"][name] = {
                key: nonnegative(value)
                for key, value in mapping(stats.get(name)).items()
                if isinstance(key, str) and 0 < len(key) <= 96
            }
        for name in NEW_COUNTS:
            data["stats"][name] = nonnegative(stats.get(name))
        from .content import load_content

        gameplay = load_content()
        evolved = stats.get("evolved_spells", [])
        data["stats"]["evolved_spells"] = (
            sorted(
                set(aid for aid in evolved if isinstance(aid, str) and aid in gameplay.abilities)
            )
            if isinstance(evolved, list)
            else []
        )
        settled = raw.get("settled_runs", [])
        data["settled_runs"] = (
            list(
                dict.fromkeys(rid for rid in settled if isinstance(rid, str) and 0 < len(rid) <= 64)
            )
            if isinstance(settled, list)
            else []
        )
        for aid in data["achievements"]:
            stamp = mapping(raw.get("achievement_completed_at")).get(aid)
            try:
                valid = (
                    isinstance(stamp, str)
                    and len(stamp) <= 40
                    and datetime.fromisoformat(stamp).utcoffset() is not None
                )
            except ValueError:
                valid = False
            data["achievement_completed_at"][aid] = stamp if valid else None
        if version == 1:
            # Only infer facts that existing completion records prove.
            data["stats"]["elites"] = max(
                data["stats"]["elites"], int("elite" in data["achievements"])
            )
            data["stats"]["evolved"] = max(
                data["stats"]["evolved"], int("evolution" in data["achievements"])
            )
            data["stats"]["bosses"] = max(
                data["stats"]["bosses"],
                data["stats"]["wins"],
                int("victory" in data["achievements"]),
            )
            data["stats"]["run_kills"] = max(
                data["stats"]["run_kills"], 100 if "centurion" in data["achievements"] else 0
            )
            data["stats"]["boss_kills"]["hogger"] = data["stats"]["bosses"]
        if "victory" in data["achievements"]:
            data["stats"]["boss_kills"]["hogger"] = max(
                1, data["stats"]["boss_kills"].get("hogger", 0)
            )
        if "boss_zone_kills" not in stats:
            # Earlier builds place each shipped boss in exactly one known zone.
            for zid, zone in gameplay.zones.items():
                for bid in zone.boss_pool:
                    if sum(bid in z.boss_pool for z in gameplay.zones.values()) == 1:
                        data["stats"]["boss_zone_kills"][f"{zid}:{bid}"] = data["stats"][
                            "boss_kills"
                        ].get(bid, 0)
        data["achievement_progress"] = {
            aid: cls.achievement_value(data, aid) for aid in meta.achievements
        }
        # Registry gates are authoritative, not an editable arbitrary unlock list.
        data["unlocked_classes"] = [
            cid
            for cid, c in meta.classes.items()
            if not c.achievement or c.achievement in data["achievements"]
        ]
        zones = raw.get("unlocked_zones", [])
        data["unlocked_zones"] = (
            list(
                dict.fromkeys(
                    list(meta.zones) + [z for z in zones if isinstance(z, str) and z in meta.zones]
                )
            )
            if isinstance(zones, list)
            else list(meta.zones)
        )
        return data

    @staticmethod
    def achievement_value(data: dict[str, Any], aid: str) -> int:
        return progress(data, load_progression().achievements[aid])

    def preserve_corrupt(self) -> None:
        if self.path.exists() and not self.path.with_suffix(".corrupt").exists():
            try:
                shutil.copy2(self.path, self.path.with_suffix(".corrupt"))
            except OSError:
                pass

    def load(self) -> None:
        for candidate in (self.path, self.path.with_suffix(".bak"), self.path.with_suffix(".tmp")):
            if not candidate.exists():
                continue
            try:
                raw = json.loads(candidate.read_text("utf-8"))
                self.data = self.validate(raw)
                if candidate != self.path:
                    self.notice = (
                        "Recovered your backup save."
                        if candidate.suffix == ".bak"
                        else "Recovered an interrupted save."
                    )
                elif raw["version"] == 1:
                    self.notice = "Migrated your progression; obsolete talent ranks were refunded."
                return
            except FutureSave:
                self.read_only = True
                self.notice = "This profile uses a newer game version. Original save kept; saving and purchases disabled."
                return
            except (OSError, ValueError, TypeError):
                if candidate == self.path:
                    self.preserve_corrupt()
                self.notice = "Save could not be read. Using safe defaults."

    @staticmethod
    def write_json(path: Path, data: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())

    @staticmethod
    def replace(source: Path, destination: Path) -> None:
        # Windows scanners can briefly hold an otherwise writable file. Keep
        # retries bounded; other failures still roll purchases back immediately.
        for attempt in range(3):
            try:
                os.replace(source, destination)
                return
            except PermissionError:
                if attempt == 2:
                    raise
                time.sleep(0.02)

    def write(self) -> bool:
        if self.read_only:
            return False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            clean = self.validate(self.data)
            clean["revision"] += 1
            temporary = self.path.with_suffix(".tmp")
            self.write_json(temporary, clean)
            if self.path.exists():
                try:
                    previous = self.validate(json.loads(self.path.read_text("utf-8")))
                    backup_tmp = self.path.with_suffix(".bak.tmp")
                    self.write_json(backup_tmp, previous)
                    self.replace(backup_tmp, self.path.with_suffix(".bak"))
                except FutureSave:
                    self.read_only = True
                    self.notice = "A newer save was found; original kept and saving disabled."
                    return False
                except (ValueError, TypeError):
                    self.preserve_corrupt()
            self.replace(temporary, self.path)
            self.data = clean
            return True
        except (OSError, ValueError, TypeError):
            self.notice = "Progress could not be saved. Check access to your local save folder."
            return False

    def commit_purchase(self, before: dict[str, Any]) -> bool:
        if self.write():
            return True
        self.data = before
        return False

    def shared_cost(self, sid: str) -> int | None:
        u = load_progression().shared.get(sid)
        rank = self.data["shared"].get(sid, 0)
        return u.costs[rank] if u and rank < u.max_rank else None

    def shared_reason(self, sid: str) -> str:
        if self.read_only:
            return self.notice
        u = load_progression().shared.get(sid)
        cost = self.shared_cost(sid)
        if not u:
            return "Unknown upgrade."
        if cost is None:
            return "Fully trained."
        if u.achievement and u.achievement not in self.data["achievements"]:
            return (
                "Requires achievement: " + load_progression().achievements[u.achievement].name + "."
            )
        if sum(self.data["shared"].values()) < u.requires_ranks:
            return f"Requires {u.requires_ranks} shared upgrade ranks."
        if self.data["gold"] < cost:
            return f"Requires {cost} gold."
        return ""

    def buy_shared(self, sid: str) -> bool:
        if self.shared_reason(sid):
            return False
        cost = self.shared_cost(sid)
        assert cost is not None
        before = copy.deepcopy(self.data)
        self.data["gold"] -= cost
        self.data["shared"][sid] = self.data["shared"].get(sid, 0) + 1
        return self.commit_purchase(before)

    def talent_points(self, cid: str) -> int:
        c = self.data["classes"].get(cid)
        return max(0, class_level(c["xp"]) - 1 - sum(c["talents"].values())) if c else 0

    def talent_reason(self, cid: str, tid: str) -> str:
        tree = load_progression().trees.get(cid)
        if self.read_only:
            return self.notice
        if not tree or not self.class_available(cid):
            return "Class is unavailable."
        c = self.data["classes"][cid]
        return talent_reason(tree, c["xp"], c["talents"], tid)

    def buy_talent(self, cid: str, tid: str) -> bool:
        if self.talent_reason(cid, tid):
            return False
        before = copy.deepcopy(self.data)
        talents = self.data["classes"][cid]["talents"]
        talents[tid] = talents.get(tid, 0) + 1
        return self.commit_purchase(before)

    def respec_cost(self, cid: str) -> int:
        c = self.data["classes"].get(cid, {})
        return int(50 + 5 * sum(c.get("talents", {}).values()))

    def respec(self, cid: str) -> bool:
        c = self.data["classes"].get(cid)
        if (
            self.read_only
            or cid not in load_progression().trees
            or not c
            or not c["talents"]
            or self.data["gold"] < self.respec_cost(cid)
        ):
            return False
        before = copy.deepcopy(self.data)
        self.data["gold"] -= self.respec_cost(cid)
        c["talents"].clear()
        c["starting_ability"] = ""
        return self.commit_purchase(before)

    def select_starting(self, cid: str, aid: str) -> bool:
        c = self.data["classes"].get(cid)
        tree = load_progression().trees.get(cid)
        if (
            self.read_only
            or not c
            or not tree
            or (
                aid
                and (
                    not c["talents"].get("preparation")
                    or aid not in tree["preparation"].starting_options
                )
            )
        ):
            return False
        before = copy.deepcopy(self.data)
        c["starting_ability"] = aid
        return self.commit_purchase(before)

    def loadout(self, cid: str) -> RunLoadout:
        if not self.class_available(cid):
            raise ValueError("Class is unavailable")
        return build_loadout(self.validate(self.data), cid)

    def class_available(self, cid: str) -> bool:
        c = load_progression().classes.get(cid)
        return bool(c and c.playable and cid in self.data["unlocked_classes"])

    def reward_run(
        self,
        cid: str,
        kills: int,
        elites: int,
        seconds: float,
        won: bool,
        gold: int,
        evolved: int,
        class_xp_kills: int | None = None,
        gold_bonus: float = 0,
        boss_id: str = "hogger",
        summary: RunSummary | None = None,
    ) -> dict[str, Any]:
        if not self.class_available(cid):
            raise ValueError("Class is not playable and unlocked")
        if summary is not None:
            if not isinstance(summary.run_id, str) or not 0 < len(summary.run_id) <= 64:
                raise ValueError("Invalid run identity")
            if summary.run_id in self.data["settled_runs"]:
                return dict(
                    gold=0,
                    class_xp=0,
                    achievements=[],
                    unlocks=[],
                    saved=self.write(),
                    points=0,
                    duplicate=True,
                )
            # Validate the entire summary before changing gold, XP or counters.
            apply_summary(copy.deepcopy(self.data), summary, seconds, won)
        if not math.isfinite(gold_bonus) or not 0 <= gold_bonus <= 1:
            raise ValueError("Invalid gold bonus")
        if won and (not isinstance(boss_id, str) or not 0 < len(boss_id) <= 64):
            raise ValueError("A victory requires a final boss identity")
        rewards = calculate_rewards(
            kills,
            elites,
            seconds,
            won,
            gold,
            evolved,
            load_progression().achievements,
            class_xp_kills,
        )
        meta = load_progression()
        earned = math.floor(rewards.gold * (1 + gold_bonus))
        old_level = class_level(self.data["classes"][cid]["xp"])
        self.data["classes"][cid]["xp"] += rewards.class_xp
        stats = self.data["stats"]
        stats["runs"] += 1
        stats["kills"] += kills
        stats["wins"] += int(won)
        stats["best_time"] = max(stats["best_time"], int(seconds))
        stats["run_kills"] = max(stats["run_kills"], kills)
        stats["elites"] += elites
        stats["evolved"] += evolved
        stats["bosses"] += int(won)
        if won:
            stats["boss_kills"][boss_id] = stats["boss_kills"].get(boss_id, 0) + 1
        stats["class_runs"][cid] += 1
        stats["class_wins"][cid] += int(won)
        if summary is not None:
            apply_summary(self.data, summary, seconds, won)
            self.data["settled_runs"].append(summary.run_id)
        elif won:
            from .content import load_content

            matching = [
                zid for zid, zone in load_content().zones.items() if boss_id in zone.boss_pool
            ]
            if len(matching) == 1:
                key = f"{matching[0]}:{boss_id}"
                stats["boss_zone_kills"][key] = stats["boss_zone_kills"].get(key, 0) + 1
        fresh, achievement_gold = complete(self.data)
        earned += achievement_gold
        old_unlocks = set(self.data["unlocked_classes"])
        self.data["unlocked_classes"] = [
            key
            for key, c in meta.classes.items()
            if not c.achievement or c.achievement in self.data["achievements"]
        ]
        unlocks = [key for key in self.data["unlocked_classes"] if key not in old_unlocks]
        self.data["gold"] += earned
        saved = self.write()
        return dict(
            gold=earned,
            class_xp=rewards.class_xp,
            achievements=fresh,
            unlocks=unlocks,
            saved=saved,
            points=class_level(self.data["classes"][cid]["xp"]) - old_level,
        )
