"""Player-facing comparisons derived from rank data and the actual stat calculators."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .combat import COUNT_KINDS, EVOLUTION_DAMAGE_MULTIPLIER, incoming_damage, spell_stats
from .content import Ability, Content, Manual
from .entities import Player, SpellState
from .manuals import manual_cooldown, manual_duration
from .passive_effects import BASE_PICKUP_RADIUS, BONUS

if TYPE_CHECKING:
    from .upgrades import Choice


@dataclass(frozen=True)
class Value:
    label: str
    amount: float
    unit: str = ""

    def text(self) -> str:
        return number(self.amount) + self.unit


@dataclass(frozen=True)
class CardText:
    kind: str
    rank: str
    summary: str
    changes: tuple[str, ...]
    notes: tuple[str, ...] = ()
    basis: str = "Base rank values"


def number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def compare(old: tuple[Value, ...], new: tuple[Value, ...]) -> tuple[str, ...]:
    before = {v.label: v for v in old}
    result = []
    for value in new:
        previous = before.get(value.label)
        if previous is None:
            result.append(value.label + ": " + value.text())
        elif abs(previous.amount - value.amount) > 1e-6:
            result.append(value.label + ": " + number(previous.amount) + " to " + value.text())
    return tuple(result)


def automatic_summary(ability: Ability) -> str:
    # Keep accurate authored behavior prose; detailed rank milestones live below.
    return ability.description.split(". Rank ", 1)[0].rstrip(".") + "."


def evolution_effects(base: Ability, evolved: Ability) -> tuple[str, ...]:
    old, new = base.mechanics, evolved.mechanics
    effects = []
    if new.extra_pets > old.extra_pets:
        effects.append(f"Summons {new.extra_pets - old.extra_pets} additional companions.")
    if new.homing and not old.homing:
        effects.append("Shots seek enemies.")
    if new.follow and not old.follow:
        effects.append("The attack follows you.")
    if new.persistent and not old.persistent:
        effects.append("The area persists until replaced or the run ends.")
    if new.death_burst and not old.death_burst:
        effects.append("Marked enemies explode when they die.")
    if new.volley_count > old.volley_count:
        effects.append(
            f"Firebolts per Imp attack: {old.volley_count + 1} to {new.volley_count + 1}."
        )
    for label, before, after, unit in (
        ("Ricochets", old.bounce, new.bounce, ""),
        ("Extra chain targets", old.chain - 1, new.chain - 1, ""),
        ("Slow", old.slow * 100, new.slow * 100, "%"),
        ("Healing from damage dealt", old.heal * 100, new.heal * 100, "%"),
        ("Low-health damage bonus", old.execute * 100, new.execute * 100, "%"),
        ("Burn damage each second", old.dot * 100, new.dot * 100, "% of hit damage"),
    ):
        if after != before:
            effects.append(f"{label}: {number(before)} to {number(after)}{unit}.")
    if new.splash > old.splash:
        effects.append("Larger splash explosions." if old.splash else "Hits splash nearby enemies.")
    if new.pulse != old.pulse and evolved.kind in {"field", "beam", "orbit"}:
        effects.append(f"Damage interval: {number(old.pulse)} to {number(new.pulse)}s.")
    if new.angle > old.angle and evolved.kind == "arc":
        effects.append(f"Sweep angle: {number(old.angle)} to {number(new.angle)} degrees.")
    if new.shield > old.shield:
        effects.append(f"Shield strength: {number(new.shield * 100)}% of attack damage.")
    if new.knockback > old.knockback:
        effects.append("Pushes enemies farther away.")
    if evolved.kind != base.kind:
        effects.insert(
            0,
            "Becomes "
            + {"field": "a pulsing ground attack.", "wave": "an expanding damage ring."}.get(
                evolved.kind, "a transformed automatic attack."
            ),
        )
    return tuple(effects)


def evolution_summary(base: Ability, evolved: Ability) -> str:
    effects = evolution_effects(base, evolved)
    return f"+{number((EVOLUTION_DAMAGE_MULTIPLIER - 1) * 100)}% spell damage. " + (
        effects[0] if effects else automatic_summary(base)
    )


def automatic_values(ability: Ability, state: SpellState, player: Player) -> tuple[Value, ...]:
    s = spell_stats(ability, state, player)
    m = ability.mechanics
    values = []
    if ability.kind in COUNT_KINDS:
        label = {
            "projectile": "Shots per cast",
            "dot": "Targets marked",
            "chain": "Chain targets",
            "orbit": "Orbiting weapons",
            "companion": "Imps" if m.ranged else "Wolves",
            "charge": "Charging summons",
        }[ability.kind]
        values.append(Value(label, s.count + (m.chain - 1 if ability.kind == "chain" else 0)))
    if m.ranged:
        values.append(
            Value("Firebolts per Imp attack", m.volley_count + int(state.rank >= m.volley_rank))
        )
    values.append(
        Value(
            "Damage per tick"
            if ability.kind == "dot"
            else "Damage per pulse"
            if ability.kind in {"field", "beam"}
            else "Damage per hit",
            s.damage,
        )
    )
    values.append(
        Value(
            "Attack interval" if ability.kind == "companion" else "Cast interval", s.cooldown, "s"
        )
    )
    if ability.kind == "chain":
        radius = max(300, s.radius)
        reference = max(300, ability.ranks[0].radius)
    elif ability.kind == "dot":
        radius, reference = (
            s.radius * (1 + player.meta.spell(ability.base_id or ability.id, "spread")),
            ability.ranks[0].radius,
        )
    else:
        radius, reference = s.radius, ability.ranks[0].radius
    values.append(
        Value(
            "Spread / explosion radius"
            if ability.kind == "dot"
            else "Attack reach"
            if ability.kind in {"arc", "orbit", "beam", "chain"}
            else "Shot width"
            if ability.kind == "projectile" or m.ranged
            else "Area radius",
            100 * radius / reference,
            "% of Rank 1",
        )
    )
    if ability.kind == "projectile":
        values.append(Value("Extra targets pierced", s.pierce))
    if ability.kind in {"dot", "orbit", "charge", "wave", "beam", "field"} and not m.persistent:
        values.append(Value("Effect duration", s.duration, "s"))
    if ability.kind == "projectile":
        values.append(Value("Shot lifetime", max(3, s.duration), "s"))
    return tuple(values)


def automatic_notes(ability: Ability, state: SpellState, player: Player) -> tuple[str, ...]:
    m = ability.mechanics
    notes = []
    if m.radial_rank <= state.rank:
        notes.append("Fires in all directions.")
    if ability.kind in {"field", "beam", "orbit"}:
        notes.append(
            f"Damage interval: {number(m.pulse)}s; cast speed does not change this interval."
        )
    if ability.kind == "dot":
        notes.append("Damage interval: 1s; application also deals 20% of tick damage.")
        spread = (
            state.rank >= 5
            or m.spread_dot
            or player.meta.spell(ability.base_id or ability.id, "spread") > 0
        )
        notes.append(
            "Spreads when marks expire or their target dies."
            if spread
            else "Spread unlocks at Rank 5."
        )
    if m.ranged:
        flat_splash = player.meta.spell(ability.base_id or ability.id, "splash_flat")
        if (state.rank >= m.splash_rank and m.splash) or flat_splash:
            notes.append("Firebolts splash nearby enemies.")
        if state.rank >= m.dot_rank and m.dot:
            notes.append(f"Burning deals {number(m.dot * 100)}% of hit damage each second.")
        if state.rank < m.volley_rank:
            notes.append(f"Extra firebolt unlocks at Rank {m.volley_rank}.")
    elif m.dot and ability.kind != "dot":
        notes.append(f"Also burns for {number(m.dot * 100)}% of hit damage each second.")
    if ability.kind == "companion":
        notes.append("Untargetable companion; stays near you and attacks automatically.")
        if not m.ranged and state.rank >= m.leap_rank:
            notes.append("Can leap to nearby enemies.")
        opening = player.meta.spell(ability.base_id or ability.id, "opening")
        if opening:
            notes.append(
                f"Each newly summoned companion's first hit deals +{number(opening * 100)}% damage."
            )
        if player.pet_buff and player.buff_time > 0:
            notes.append(
                "Companion buff and first-strike bonuses apply on hit, beyond the listed stats."
            )
    if m.homing:
        notes.append("Shots seek enemies.")
    if m.slow:
        notes.append(f"Slows enemies by {number(m.slow * 100)}%; bosses resist control effects.")
    if m.execute:
        notes.append(f"Deals +{number(m.execute * 100)}% damage to enemies below 35% health.")
    if m.heal:
        notes.append(
            f"Recovers {number(m.heal * 100)}% of damage dealt, subject to the shared healing limit."
        )
    if m.persistent:
        notes.append("Persists until the run ends or the spell is replaced.")
    if m.delay:
        notes.append(f"Damage begins after {number(m.delay)}s.")
    return tuple(notes)


def rank_milestone(ability: Ability, current: int, next_rank: int, player: Player) -> str:
    m = ability.mechanics
    if current and current < m.radial_rank <= next_rank:
        return "Now fires in all directions."
    if current and ability.kind == "companion":
        if m.ranged and current < m.volley_rank <= next_rank:
            return f"Each Imp now fires {m.volley_count + 1} firebolts per attack" + (
                " and burns enemies." if next_rank >= m.dot_rank and m.dot else "."
            )
        if m.ranged and m.splash and current < m.splash_rank <= next_rank:
            return (
                "Firebolt explosions become larger."
                if player.meta.spell(ability.id, "splash_flat")
                else "Firebolts now splash nearby enemies."
            )
        if not m.ranged and current < m.leap_rank <= next_rank:
            return "Wolves can now leap to nearby enemies."
    if (
        current
        and ability.kind == "dot"
        and current < 5 <= next_rank
        and not m.spread_dot
        and not player.meta.spell(ability.id, "spread")
    ):
        return "Marks now spread when their target dies or they expire."
    return ""


def manual_values(manual: Manual, rank: int, player: Player) -> tuple[Value, ...]:
    r = manual.ranks[rank - 1]
    cooldown = manual_cooldown(manual, rank, player)
    duration = manual_duration(manual, rank, player)
    values = []
    if manual.kind in {"blink", "leap"}:
        values += [
            Value("Movement distance", 100 * r.distance / manual.ranks[0].distance, "% of Rank 1"),
            Value("Arrival immunity", 0.5 + 0.2 * (rank - 1), "s"),
        ]
    if manual.kind in {"leap", "fear"}:
        values.append(Value("Damage", r.power * (1 + BONUS["might"] * player.passive("might"))))
    if manual.kind == "immune":
        values.append(Value("Invulnerability", duration, "s"))
    elif manual.kind in {"buff", "rally", "guard", "shield", "fear"}:
        if manual.kind == "buff":
            values.append(Value("Damage bonus", r.power * 100, "%"))
        elif manual.kind == "rally":
            values.append(Value("Temporary max health", r.power * 100, "%"))
        elif manual.kind == "guard":
            armor = player.armor + BONUS["armor"] * player.passive("armor") + 0.5 * r.power
            values.append(
                Value("Armor after activation", 100 - incoming_damage(100, armor, 0), "%")
            )
            if manual.shield_fraction:
                values.append(
                    Value("Shield", manual.shield_fraction * player.max_health * r.power, " health")
                )
        elif manual.kind == "shield":
            values.append(Value("Shield", r.power, " health"))
        elif manual.kind == "fear":
            values.append(
                Value(
                    "Fear radius",
                    100
                    * r.distance
                    * (1 + BONUS["area"] * player.passive("area"))
                    / manual.ranks[0].distance,
                    "% of Rank 1",
                )
            )
        values.append(
            Value("Fear duration" if manual.kind == "fear" else "Effect duration", duration, "s")
        )
    elif manual.kind == "heal":
        values.append(
            Value(
                "Healing", min(1, r.power * (1 + player.meta.get("healing"))) * 100, "% max health"
            )
        )
        if r.power > 1 or manual.ranks[-1].power > 1:
            values.append(Value("Shield", max(0, r.power - 1) * player.max_health, " health"))
    elif manual.kind == "circle":
        values.append(Value("Return immunity", 0.5, "s"))
    values.append(
        Value("Cooldown after return" if manual.kind == "circle" else "Cooldown", cooldown, "s")
    )
    return tuple(values)


def passive_values(pid: str, rank: int) -> tuple[Value, ...]:
    specs = {
        "projectiles": ("Extra shots / targets / summons", BONUS["projectiles"], ""),
        "area": ("Attack radius bonus", BONUS["area"] * 100, "%"),
        "might": ("Automatic damage bonus", BONUS["might"] * 100, "%"),
        "haste": ("Cast / attack cooldown reduction", BONUS["haste"] * 100, "%"),
        "duration": ("Effect duration bonus", BONUS["duration"] * 100, "%"),
        "velocity": ("Shot travel speed bonus", BONUS["velocity"] * 100, "%"),
        "movement": ("Hero movement speed bonus", BONUS["movement"] * 100, "%"),
        "pickup": (
            "Attraction reach bonus",
            BONUS["pickup"] / BASE_PICKUP_RADIUS * 100,
            "% of base reach",
        ),
        "armor": ("Armor bonus", BONUS["armor"] * 100, " percentage points"),
        "health": ("Maximum health bonus", BONUS["health"], " health"),
        "regen": ("Health recovery", BONUS["regen"], "/s"),
        "piercing": ("Extra targets pierced", BONUS["piercing"], ""),
    }
    label, amount, unit = specs[pid]
    return (Value(label, amount * rank, unit),)


def evolution_requirements(
    content: Content, player: Player, aid: str, chest: bool = False
) -> tuple[str, ...]:
    ability = content.ability(aid)
    if ability.evolved:
        return ("Evolution already equipped; the original slot has been replaced.",)
    evo = ability.evolution
    if evo is None:
        return ("This spell has no evolution.",)
    rank = player.spells[aid].rank if aid in player.spells else 0
    passive = player.passive(evo.passive)
    return (
        "Evolution: " + evo.name,
        f"{ability.name}: Rank {rank}/8 · " + ("Complete" if rank == 8 else "Required"),
        f"{content.passives[evo.passive].name}: Rank {passive} · "
        + ("Owned" if passive else "Required at Rank 1+"),
        "Elite treasure chest: " + ("Open now" if chest else "Required"),
        "Ready to choose in a chest."
        if rank == 8 and passive
        else "Not ready; meet the spell and passive requirements.",
    )


def describe_choice(
    content: Content, player: Player, choice: Choice, activation: str = "Space / A"
) -> CardText:
    if choice.kind == "spell":
        a = content.ability(choice.id)
        current = player.spells.get(choice.id)
        next_state = replace(current, rank=choice.rank) if current else SpellState(choice.rank)
        old = automatic_values(a, current, player) if current else ()
        new = automatic_values(a, next_state, player)
        return CardText(
            "Equipped Ability"
            if current and current.rank == choice.rank
            else "Spell Upgrade"
            if current
            else "New Ability",
            f"Rank {current.rank} to {choice.rank} / 8"
            if current and current.rank < choice.rank
            else f"Rank {choice.rank} / 8" + (" · MAX" if choice.rank == 8 else ""),
            evolution_summary(content.abilities[a.base_id], a)
            if a.evolved
            else rank_milestone(a, current.rank if current else 0, choice.rank, player)
            or automatic_summary(a),
            compare(old, new),
            (evolution_effects(content.abilities[a.base_id], a) if a.evolved else ())
            + automatic_notes(a, next_state, player),
            "Effective now; conditional hit bonuses excluded. Sizes relative to base Rank 1.",
        )
    if choice.kind == "evolution":
        a = content.ability(choice.id)
        assert a.evolution
        evolved = content.ability(a.evolution.id)
        state = player.spells[choice.id]
        return CardText(
            "Evolution",
            "Rank 8 / 8 · replaces this spell",
            evolution_summary(a, evolved),
            compare(automatic_values(a, state, player), automatic_values(evolved, state, player)),
            evolution_effects(a, evolved) + automatic_notes(evolved, state, player),
            "Effective now; conditional hit bonuses excluded. Sizes relative to base Rank 1.",
        )
    if choice.kind == "modifier":
        aid, branch = choice.id.split(":")
        a, current = content.abilities[aid], player.spells[aid]
        changed = replace(current, modifiers=current.modifiers | {branch})
        return CardText(
            "Special Modifier",
            f"Rank {current.rank} / 8 · choose one branch",
            "More damage, but casts take longer. Blocks Reach."
            if branch == "force"
            else "Increases this spell's attack footprint. Blocks Force.",
            compare(automatic_values(a, current, player), automatic_values(a, changed, player)),
            (),
            "Effective now; conditional hit bonuses excluded. Sizes relative to base Rank 1.",
        )
    if choice.kind == "manual":
        manual = content.manuals[choice.id]
        current_rank = player.manual.rank if player.manual else 0
        notes = [f"Activate with {activation}."]
        if manual.root:
            notes.append(
                f"Cannot move; regenerates {number(manual.regen * 100)}% max health per second."
            )
        if manual.kind == "guard":
            notes.append("Total armor is capped at 75% before enemy armor penetration.")
        if manual.kind in {"guard", "shield", "heal"}:
            notes.append(
                "Keeps a stronger existing shield instead of replacing it with a weaker one."
            )
        if manual.kind == "fear":
            notes.append("Bosses cannot be feared; elite fear lasts at most 1.5s.")
        return CardText(
            "Manual Upgrade" if current_rank else "Manual Ability",
            f"Rank {current_rank} to {choice.rank} / 3" if current_rank else "Rank 1 / 3",
            manual.description,
            compare(
                manual_values(manual, current_rank, player) if current_rank else (),
                manual_values(manual, choice.rank, player),
            ),
            tuple(notes),
            "With your bonuses; armor/healing caps applied",
        )
    if choice.kind == "passive":
        p = content.passives[choice.id]
        current_rank = player.passive(choice.id)
        notes = [p.applicability]
        if choice.id == "health":
            notes.append("Also restores up to 20 health immediately.")
        if choice.id == "armor":
            notes.append("Total armor including other bonuses is capped at 75%.")
        return CardText(
            "Passive Upgrade",
            f"Rank {current_rank} to {choice.rank} / {p.max_rank}",
            p.description,
            compare(passive_values(p.id, current_rank), passive_values(p.id, choice.rank)),
            tuple(notes),
            "This passive's contribution; other bonuses stack separately",
        )
    return CardText(
        "Repeatable Reward", "No rank · reusable", choice.description, (), (), "Applies to this run"
    )
