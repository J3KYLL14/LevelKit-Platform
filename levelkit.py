"""Beginner-friendly helpers for LevelKit Platform content files.

These functions create the same dictionaries the engine already understands.
Students can start with readable options, then move to exact dictionary values
when they are ready.
"""

from __future__ import annotations

import re
from collections.abc import Callable


SPEEDS = {
    "still": 0,
    "slow": 70,
    "normal": 140,
    "fast": 220,
}

PLAYER_SPEEDS = {
    "slow": 180,
    "normal": 220,
    "fast": 280,
}

JUMPS = {
    "none": 0,
    "low": 820,
    "normal": 1020,
    "high": 1180,
}

SIZES = {
    "tiny": (18, 18),
    "small": (28, 28),
    "normal": (34, 44),
    "large": (48, 56),
}

PATROLS = {
    "none": 0,
    "short": 120,
    "long": 260,
}

COLORS = {
    "blue": (110, 190, 255),
    "green": (120, 220, 120),
    "gold": (230, 210, 140),
    "red": (220, 90, 90),
    "pink": (222, 72, 132),
    "yellow": (255, 214, 94),
    "white": (240, 240, 240),
}

EVENT_HOOKS = {
    "pickup": [],
    "enter_level": [],
}


def clear_event_hooks():
    for hooks in EVENT_HOOKS.values():
        hooks.clear()


def _id_from_name(name):
    value = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return value or "thing"


def _preset(value, presets, label):
    if isinstance(value, str):
        if value not in presets:
            choices = ", ".join(sorted(presets))
            raise ValueError(f"{label} must be one of: {choices}. You used {value!r}.")
        return presets[value]
    return value


def _color(value):
    if isinstance(value, str):
        return _preset(value, COLORS, "color")
    return value


def _animations(animations=None, **named):
    result = dict(animations or {})
    result.update({key: value for key, value in named.items() if value})
    return result


def character(
    name,
    *,
    role,
    id=None,
    size="normal",
    color="blue",
    health=1,
    speed="normal",
    gravity=1700,
    jump="none",
    attack=None,
    ai=None,
    dialogue_id=None,
    sprite=None,
    animations=None,
    idle=None,
    walk=None,
    jump_animation=None,
    fall=None,
):
    data = {
        "id": id or _id_from_name(name),
        "name": name,
        "role": role,
        "size": _preset(size, SIZES, "size"),
        "color": _color(color),
        "health": health,
        "speed": _preset(speed, PLAYER_SPEEDS if role == "player" else SPEEDS, "speed"),
        "gravity": gravity,
        "jump_power": _preset(jump, JUMPS, "jump"),
    }
    if attack:
        data["attack"] = dict(attack)
    if ai:
        data["ai"] = dict(ai)
    if dialogue_id:
        data["dialogue_id"] = dialogue_id
    if sprite:
        data["sprite"] = sprite
    animation_data = _animations(
        animations,
        idle=idle,
        walk=walk,
        jump=jump_animation,
        fall=fall,
    )
    if animation_data:
        data["animations"] = animation_data
    return data


def player(
    name,
    *,
    id=None,
    size=(34, 46),
    color="blue",
    health=5,
    speed="normal",
    jump="normal",
    melee_damage=1,
    projectile_damage=1,
    projectile_color=(250, 225, 120),
    sprite=None,
    animations=None,
    idle=None,
    walk=None,
    jump_animation=None,
    fall=None,
):
    return character(
        name,
        id=id,
        role="player",
        size=size,
        color=color,
        health=health,
        speed=speed,
        jump=jump,
        sprite=sprite,
        animations=animations,
        idle=idle,
        walk=walk,
        jump_animation=jump_animation,
        fall=fall,
        attack={
            "melee_damage": melee_damage,
            "melee_cooldown": 0.35,
            "projectile_damage": projectile_damage,
            "projectile_cooldown": 0.55,
            "projectile_speed": 420,
            "projectile_color": projectile_color,
        },
    )


def enemy(
    name,
    *,
    id=None,
    size=(34, 28),
    color="green",
    health=2,
    speed="slow",
    touch_damage=1,
    patrol="short",
    sprite=None,
    animations=None,
    idle=None,
    walk=None,
    jump_animation=None,
    fall=None,
):
    patrol_distance = _preset(patrol, PATROLS, "patrol")
    ai = {"patrol_distance": patrol_distance} if patrol_distance else {}
    return character(
        name,
        id=id,
        role="enemy",
        size=size,
        color=color,
        health=health,
        speed=speed,
        jump="none",
        sprite=sprite,
        animations=animations,
        idle=idle,
        walk=walk,
        jump_animation=jump_animation,
        fall=fall,
        attack={"touch_damage": touch_damage},
        ai=ai,
    )


def npc(
    name,
    *,
    id=None,
    dialogue_id,
    size=(34, 44),
    color="gold",
    sprite=None,
    animations=None,
    idle=None,
):
    return character(
        name,
        id=id,
        role="npc",
        size=size,
        color=color,
        health=1,
        speed="still",
        gravity=0,
        jump="none",
        dialogue_id=dialogue_id,
        sprite=sprite,
        animations=animations,
        idle=idle,
    )


def item(
    name,
    *,
    id=None,
    pickup_type="quest",
    size=(20, 20),
    color="yellow",
    inventory=True,
    effect=None,
    amount=None,
    sprite=None,
):
    data = {
        "id": id or _id_from_name(name),
        "name": name,
        "pickup_type": pickup_type,
        "size": _preset(size, SIZES, "size"),
        "color": _color(color),
        "inventory": inventory,
    }
    if effect:
        data["effect"] = effect
    if amount is not None:
        data["amount"] = amount
    if sprite:
        data["sprite"] = sprite
    return data


def healing_item(name, *, id=None, heals=1, size=(18, 18), color="pink", sprite=None):
    return item(
        name,
        id=id,
        pickup_type="healing",
        size=size,
        color=color,
        inventory=False,
        effect="heal",
        amount=heals,
        sprite=sprite,
    )


def quest_item(name, *, id=None, size=(20, 20), color="yellow", sprite=None):
    return item(name, id=id, pickup_type="quest", size=size, color=color, inventory=True, sprite=sprite)


def dialogue(**entries):
    return dict(entries)


def say(game, text, speaker="LevelKit"):
    game.say(text, speaker=speaker)


def when_pickup(item_id, *, say=None, heal=None, give_item=None, function: Callable | None = None):
    EVENT_HOOKS["pickup"].append(
        {
            "item_id": item_id,
            "say": say,
            "heal": heal,
            "give_item": give_item,
            "function": function,
        }
    )


def when_enter_level(level_id, *, say=None, function: Callable | None = None):
    EVENT_HOOKS["enter_level"].append(
        {
            "level_id": level_id,
            "say": say,
            "function": function,
        }
    )
