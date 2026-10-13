"""Eligible, weighted rewards; slot caps and chest context are revalidated on selection."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .content import Content
from .entities import ManualState, Player, SpellState

SPELL_SLOTS = 8
PASSIVE_SLOTS = 8


@dataclass(frozen=True)
class Choice:
    kind: str
    id: str
    name: str
    description: str
    rank: int
    weight: float


REWARDS = (
    Choice("reward", "heal", "Second Wind", "Restore 35% of maximum health.", 0, 1),
    Choice("reward", "gold", "Gold Cache", "Add 30 gold to this run's score.", 0, 1),
    Choice("reward", "power", "Battle Focus", "Double automatic damage for ten seconds.", 0, 1),
    Choice("reward", "ward", "Guardian Ward", "Gain a 20% health shield for six seconds.", 0, 1),
)


def evolution_eligible(content: Content, player: Player) -> list[str]:
    return [
        aid
        for aid, state in player.spells.items()
        if aid in content.abilities
        and state.rank == 8
        and (evo := content.abilities[aid].evolution) is not None
        and player.passive(evo.passive) > 0
    ]


def eligible(content: Content, class_id: str, player: Player, chest: bool = False) -> list[Choice]:
    choices = []
    if chest:
        for aid in evolution_eligible(content, player):
            evo = content.abilities[aid].evolution
            assert evo is not None
            choices.append(Choice("evolution", aid, evo.name, evo.description, 8, 4))
    else:
        equipped_bases = {content.ability(aid).base_id or aid for aid in player.spells}
        for aid in content.classes[class_id].abilities:
            ability = content.abilities[aid]
            state = player.spells.get(aid)
            if state is None:
                if len(player.spells) >= SPELL_SLOTS or aid in equipped_bases:
                    continue
                evo_hint = (
                    f" Evolve: Rank 8 + {content.passives[ability.evolution.passive].name} + elite chest."
                    if ability.evolution
                    else ""
                )
                choices.append(
                    Choice("spell", aid, ability.name, ability.description + evo_hint, 1, 1.4)
                )
            elif state.rank < 8:
                new_rank = ability.ranks[state.rank]
                description = f"{ability.description} {new_rank.damage:g} damage / {new_rank.cooldown:g}s / {new_rank.radius:g} reach / {new_rank.count} effects / {new_rank.pierce} pierce."
                if ability.evolution:
                    description += f" Evolve with {content.passives[ability.evolution.passive].name} at Rank 8."
                if state.rank + 1 >= ability.mechanics.radial_rank:
                    description += " Radial volley."
                choices.append(Choice("spell", aid, ability.name, description, state.rank + 1, 2.3))
            if state and state.rank >= 4 and not state.modifiers:
                choices.extend(
                    (
                        Choice(
                            "modifier",
                            aid + ":force",
                            ability.name + " · Force",
                            "Choose one branch: +30% damage, +15% cooldown. Blocks Reach branch.",
                            0,
                            0.55,
                        ),
                        Choice(
                            "modifier",
                            aid + ":reach",
                            ability.name + " · Reach",
                            "Choose one branch: +30% attack area. Blocks Force branch.",
                            0,
                            0.55,
                        ),
                    )
                )
        for pid, passive in content.passives.items():
            rank = player.passive(pid)
            if rank < passive.max_rank and (rank or len(player.passives) < PASSIVE_SLOTS):
                choices.append(
                    Choice(
                        "passive",
                        pid,
                        passive.name,
                        passive.description + " " + passive.applicability,
                        rank + 1,
                        1.2,
                    )
                )
        for mid in content.classes[class_id].manuals:
            manual = content.manuals[mid]
            if player.manual is None:
                choices.append(Choice("manual", mid, manual.name, manual.description, 1, 0.75))
            elif player.manual.id == mid and player.manual.rank < 3:
                choices.append(
                    Choice(
                        "manual",
                        mid,
                        manual.name,
                        manual.ranks[player.manual.rank].description,
                        player.manual.rank + 1,
                        1.2,
                    )
                )
    count = 3 if chest else 3 + int(player.meta.get("choices") > 0)
    if len(choices) < count:
        choices.extend(REWARDS[:count])
    return choices


def roll(
    content: Content,
    class_id: str,
    player: Player,
    rng: random.Random,
    chest: bool = False,
    excluded: list[Choice] | None = None,
) -> list[Choice]:
    pool = eligible(content, class_id, player, chest)
    count = 3 if chest else 3 + int(player.meta.get("choices") > 0)
    alternatives = [c for c in pool if c not in (excluded or [])]
    if excluded and len(alternatives) >= count:
        pool = alternatives
    result = []
    evolutions = [c for c in pool if c.kind == "evolution"]
    if chest and evolutions:
        evolution = rng.choices(evolutions, weights=[c.weight for c in evolutions], k=1)[0]
        result.append(evolution)
        pool.remove(evolution)
    for _ in range(min(count - len(result), len(pool))):
        choice = rng.choices(pool, weights=[c.weight for c in pool], k=1)[0]
        result.append(choice)
        pool.remove(choice)
    return result


def apply(
    content: Content, class_id: str, player: Player, choice: Choice, chest: bool = False
) -> int:
    if choice not in eligible(content, class_id, player, chest):
        raise ValueError("Upgrade is no longer eligible")
    if choice.kind == "spell":
        state = player.spells.setdefault(choice.id, SpellState())
        state.rank = choice.rank
    elif choice.kind == "evolution":
        ability = content.abilities[choice.id]
        assert ability.evolution is not None
        state = player.spells.pop(choice.id)
        state.timer = 0
        player.spells[ability.evolution.id] = state
    elif choice.kind == "modifier":
        aid, modifier = choice.id.split(":")
        player.spells[aid].modifiers.add(modifier)
    elif choice.kind == "manual":
        if player.manual is None:
            player.manual = ManualState(choice.id)
        player.manual.rank = choice.rank
    elif choice.kind == "passive":
        player.passives[choice.id] = choice.rank
        if choice.id == "health":
            player.max_health += 20
            player.health = min(player.max_health, player.health + 20)
    elif choice.id == "heal":
        player.health = min(player.max_health, player.health + player.max_health * 0.35)
    elif choice.id == "power":
        player.power = 10
    elif choice.id == "gold":
        return 30
    elif choice.id == "ward":
        player.shield = max(player.shield, player.max_health * 0.2)
        player.shield_time = 6
    return 0
