from __future__ import annotations

from dataclasses import dataclass

import pygame

from .entities import NPC, Actor, Pickup


@dataclass
class ExitZone:
    rect: pygame.Rect
    target_level: str
    target_spawn: str
    sprite: str | None = None


@dataclass
class LevelState:
    level_id: str
    name: str
    background: tuple[int, int, int]
    world_size: tuple[int, int]
    player_spawn: dict
    solids: list[pygame.Rect]
    solid_sprites: list[str | None]
    hazards: list[pygame.Rect]
    hazard_sprites: list[str | None]
    exits: list[ExitZone]
    checkpoints: list[pygame.Rect]
    checkpoint_sprites: list[str | None]
    win_zones: list[pygame.Rect]
    win_zone_sprites: list[str | None]
    pickups: list[Pickup]
    enemies: list[Actor]
    npcs: list[NPC]


def make_rect(data):
    return pygame.Rect(data["x"], data["y"], data["w"], data["h"])


def make_sprite_list(level_def, key):
    return [item.get("sprite") for item in level_def.get(key, [])]


def build_actor(defn, spawn):
    rect = pygame.Rect(spawn["x"], spawn["y"], defn["size"][0], defn["size"][1])
    return Actor(
        actor_id=defn["id"],
        role=defn["role"],
        rect=rect,
        color=tuple(defn["color"]),
        max_health=defn.get("health", 1),
        speed=defn.get("speed", 0),
        gravity=defn.get("gravity", 1600),
        jump_power=defn.get("jump_power", 0),
        attack=dict(defn.get("attack", {})),
        dialogue_id=defn.get("dialogue_id"),
        ai=dict(defn.get("ai", {})),
        sprite=spawn.get("sprite") or defn.get("sprite"),
        animations=dict(defn.get("animations", {})),
    )


def build_level(level_def, character_defs, item_defs):
    solids = [make_rect(rect) for rect in level_def.get("solids", [])]
    hazards = [make_rect(rect) for rect in level_def.get("hazards", [])]
    exits = [
        ExitZone(
            rect=make_rect(exit_data),
            target_level=exit_data["target_level"],
            target_spawn=exit_data.get("target_spawn", "default"),
            sprite=exit_data.get("sprite"),
        )
        for exit_data in level_def.get("exits", [])
    ]
    checkpoints = [make_rect(rect) for rect in level_def.get("checkpoints", [])]
    win_zones = [make_rect(rect) for rect in level_def.get("win_zones", [])]

    pickups = []
    for placement in level_def.get("pickups", []):
        item = item_defs[placement["item_id"]]
        pickups.append(
            Pickup(
                item_id=item["id"],
                rect=pygame.Rect(
                    placement["x"],
                    placement["y"],
                    item["size"][0],
                    item["size"][1],
                ),
                color=tuple(item["color"]),
                data=item,
                sprite=placement.get("sprite") or item.get("sprite"),
            )
        )

    enemies = []
    for placement in level_def.get("enemies", []):
        enemies.append(build_actor(character_defs[placement["character_id"]], placement))

    npcs = []
    for placement in level_def.get("npcs", []):
        char_def = character_defs[placement["character_id"]]
        npcs.append(
            NPC(
                npc_id=char_def["id"],
                rect=pygame.Rect(
                    placement["x"],
                    placement["y"],
                    char_def["size"][0],
                    char_def["size"][1],
                ),
                color=tuple(char_def["color"]),
                dialogue_id=char_def["dialogue_id"],
                name=char_def["name"],
                sprite=placement.get("sprite") or char_def.get("sprite"),
                animations=dict(char_def.get("animations", {})),
            )
        )

    return LevelState(
        level_id=level_def["id"],
        name=level_def["name"],
        background=tuple(level_def.get("background", (18, 24, 38))),
        world_size=tuple(level_def["world_size"]),
        player_spawn=level_def["spawns"],
        solids=solids,
        solid_sprites=make_sprite_list(level_def, "solids"),
        hazards=hazards,
        hazard_sprites=make_sprite_list(level_def, "hazards"),
        exits=exits,
        checkpoints=checkpoints,
        checkpoint_sprites=make_sprite_list(level_def, "checkpoints"),
        win_zones=win_zones,
        win_zone_sprites=make_sprite_list(level_def, "win_zones"),
        pickups=pickups,
        enemies=enemies,
        npcs=npcs,
    )
