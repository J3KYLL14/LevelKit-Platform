from .errors import PlainEnglishError


def require_keys(mapping, keys, context):
    for key in keys:
        if key not in mapping:
            raise PlainEnglishError(
                f"{context} is missing the '{key}' value.\n"
                f"Plain English: that content file is incomplete and needs that field."
            )


def validate_game_content(config, levels, characters, items, dialogue):
    if config["player_character_id"] not in characters:
        raise PlainEnglishError(
            f"The player character id '{config['player_character_id']}' was not found.\n"
            f"Plain English: `game_config.py` points to a player that does not exist."
        )
    if config["starting_level"] not in levels:
        raise PlainEnglishError(
            f"The starting level '{config['starting_level']}' was not found.\n"
            f"Plain English: `game_config.py` points to a level that does not exist."
        )

    for level_id, level in levels.items():
        require_keys(level, ["id", "name", "world_size", "spawns"], f"Level '{level_id}'")
        if config["starting_level"] == level_id and config["starting_spawn"] not in level["spawns"]:
            raise PlainEnglishError(
                f"Level '{level_id}' does not have a spawn called '{config['starting_spawn']}'.\n"
                f"Plain English: the game is trying to start the player at a spawn point that is missing."
            )

        for exit_zone in level.get("exits", []):
            require_keys(exit_zone, ["x", "y", "w", "h", "target_level"], f"An exit in level '{level_id}'")
            if exit_zone["target_level"] not in levels:
                raise PlainEnglishError(
                    f"An exit in level '{level_id}' points to '{exit_zone['target_level']}', but that level does not exist.\n"
                    f"Plain English: one room is trying to send the player to a missing room."
                )

        for placement in level.get("pickups", []):
            require_keys(placement, ["item_id", "x", "y"], f"A pickup in level '{level_id}'")
            if placement["item_id"] not in items:
                raise PlainEnglishError(
                    f"Level '{level_id}' uses item '{placement['item_id']}', but that item was not found.\n"
                    f"Plain English: the level refers to a pickup that does not exist in the items folder."
                )

        for placement in level.get("enemies", []):
            require_keys(placement, ["character_id", "x", "y"], f"An enemy in level '{level_id}'")
            character_id = placement["character_id"]
            if character_id not in characters:
                raise PlainEnglishError(
                    f"Level '{level_id}' uses character '{character_id}', but that character was not found.\n"
                    f"Plain English: the level refers to an enemy that does not exist."
                )
            if characters[character_id]["role"] != "enemy":
                raise PlainEnglishError(
                    f"Level '{level_id}' uses character '{character_id}' as an enemy, but its role is '{characters[character_id]['role']}'.\n"
                    f"Plain English: that character file is not marked as an enemy."
                )

        for placement in level.get("npcs", []):
            require_keys(placement, ["character_id", "x", "y"], f"An NPC in level '{level_id}'")
            character_id = placement["character_id"]
            if character_id not in characters:
                raise PlainEnglishError(
                    f"Level '{level_id}' uses character '{character_id}', but that character was not found.\n"
                    f"Plain English: the level refers to an NPC that does not exist."
                )
            if characters[character_id]["role"] != "npc":
                raise PlainEnglishError(
                    f"Level '{level_id}' uses character '{character_id}' as an NPC, but its role is '{characters[character_id]['role']}'.\n"
                    f"Plain English: that character file is not marked as an NPC."
                )
            dialogue_id = characters[character_id].get("dialogue_id")
            if dialogue_id and dialogue_id not in dialogue:
                raise PlainEnglishError(
                    f"NPC '{character_id}' asks for dialogue '{dialogue_id}', but that dialogue entry was not found.\n"
                    f"Plain English: the NPC is pointing to story text that does not exist."
                )
