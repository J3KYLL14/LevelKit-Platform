from levelkit_platform.engine.content_loader import (
    load_content_module,
    load_definitions,
    load_dialogue,
    load_event_hooks,
    load_game_config,
    load_levels,
)
from levelkit_platform.engine.errors import PlainEnglishError
from levelkit_platform.engine.validation import validate_game_content


VALID_ROLES = {"player", "enemy", "npc"}
VALID_PICKUP_TYPES = {"quest", "healing", "key", "score", "custom"}


def add(issue_list, message):
    issue_list.append(message)


def require(mapping, keys, label, issues):
    for key in keys:
        if key not in mapping:
            add(issues, f"{label} is missing '{key}'. Add that value to the content file.")


def validate_character(character_id, character, issues):
    require(character, ["id", "name", "role", "size", "color"], f"Character '{character_id}'", issues)
    role = character.get("role")
    if role and role not in VALID_ROLES:
        add(issues, f"Character '{character_id}' has role '{role}'. Use player, enemy, or npc.")
    size = character.get("size")
    if size and (not isinstance(size, tuple) or len(size) != 2):
        add(issues, f"Character '{character_id}' has an invalid size. Use a pair like (34, 44).")
    if role == "player":
        attack = character.get("attack", {})
        for key in ["melee_damage", "melee_cooldown", "projectile_damage", "projectile_cooldown", "projectile_speed"]:
            if key not in attack:
                add(issues, f"Player '{character_id}' is missing attack setting '{key}'. Use levelkit.player() to fill this in.")
    if role == "npc" and not character.get("dialogue_id"):
        add(issues, f"NPC '{character_id}' does not have dialogue_id. Add one so the player can talk to them.")


def validate_item(item_id, item, issues):
    require(item, ["id", "name", "pickup_type", "size", "color"], f"Item '{item_id}'", issues)
    pickup_type = item.get("pickup_type")
    if pickup_type and pickup_type not in VALID_PICKUP_TYPES:
        add(issues, f"Item '{item_id}' has pickup_type '{pickup_type}'. Use one of: {', '.join(sorted(VALID_PICKUP_TYPES))}.")
    if item.get("effect") == "heal" and "amount" not in item:
        add(issues, f"Item '{item_id}' heals the player but has no amount. Add amount=1 or use healing_item().")


def validate_level(level_id, level, levels, characters, items, issues):
    require(level, ["id", "name", "world_size", "spawns"], f"Level '{level_id}'", issues)
    if "default" not in level.get("spawns", {}):
        add(issues, f"Level '{level_id}' has no default spawn. Add a spawn called 'default'.")
    for key in ["solids", "hazards", "checkpoints", "win_zones", "exits"]:
        for index, rect in enumerate(level.get(key, []), start=1):
            require(rect, ["x", "y", "w", "h"], f"{key} #{index} in level '{level_id}'", issues)
    for index, exit_zone in enumerate(level.get("exits", []), start=1):
        target_level = exit_zone.get("target_level")
        target_spawn = exit_zone.get("target_spawn", "default")
        if target_level not in levels:
            add(issues, f"Exit #{index} in level '{level_id}' points to missing level '{target_level}'.")
        elif target_spawn not in levels[target_level].get("spawns", {}):
            add(issues, f"Exit #{index} in level '{level_id}' points to missing spawn '{target_spawn}' in '{target_level}'.")
    for placement in level.get("pickups", []):
        item_id = placement.get("item_id")
        if item_id not in items:
            add(issues, f"Level '{level_id}' places pickup '{item_id}', but that item does not exist.")
    for placement in level.get("enemies", []):
        character_id = placement.get("character_id")
        if character_id not in characters:
            add(issues, f"Level '{level_id}' places enemy '{character_id}', but that character does not exist.")
        elif characters[character_id].get("role") != "enemy":
            add(issues, f"Level '{level_id}' places '{character_id}' as an enemy, but its role is not enemy.")
    for placement in level.get("npcs", []):
        character_id = placement.get("character_id")
        if character_id not in characters:
            add(issues, f"Level '{level_id}' places NPC '{character_id}', but that character does not exist.")
        elif characters[character_id].get("role") != "npc":
            add(issues, f"Level '{level_id}' places '{character_id}' as an NPC, but its role is not npc.")


def validate_hooks(hooks, levels, items, issues):
    for hook in hooks.get("pickup", []):
        item_id = hook.get("item_id")
        if item_id not in items:
            add(issues, f"An event hook watches pickup '{item_id}', but that item does not exist.")
    for hook in hooks.get("enter_level", []):
        level_id = hook.get("level_id")
        if level_id not in levels:
            add(issues, f"An event hook watches level '{level_id}', but that level does not exist.")


def validate_student_programming_modules(issues):
    try:
        controls = load_content_module("player_controls")
        collisions = load_content_module("collision_rules")
    except (PlainEnglishError, ValueError, KeyError) as err:
        add(issues, str(err))
        return
    if not hasattr(controls, "control_player"):
        add(issues, "player_controls.py needs a function called control_player(player, keyboard, mouse, dt).")
    for function_name in [
        "player_hits_hazard",
        "player_reaches_checkpoint",
        "player_collects_pickup",
        "player_talks_to_npc",
        "player_reaches_win_zone",
        "player_hits_exit",
    ]:
        if not hasattr(collisions, function_name):
            add(issues, f"collision_rules.py needs a function called {function_name}.")


def collect_issues():
    issues = []
    try:
        config = load_game_config()
        characters = load_definitions("characters", "CHARACTER")
        items = load_definitions("items", "ITEMS")
        dialogue = load_dialogue()
        hooks = load_event_hooks()
        levels, _ = load_levels()
    except (PlainEnglishError, ValueError, KeyError) as err:
        return [str(err)]

    try:
        validate_game_content(config, levels, characters, items, dialogue)
    except PlainEnglishError as err:
        add(issues, str(err))

    require(config, ["game_title", "player_character_id", "starting_level", "starting_spawn"], "game_config.py", issues)
    if config.get("player_character_id") not in characters:
        add(issues, f"game_config.py uses player '{config.get('player_character_id')}', but that character does not exist.")
    if config.get("starting_level") not in levels:
        add(issues, f"game_config.py starts on level '{config.get('starting_level')}', but that level does not exist.")
    elif config.get("starting_spawn") not in levels[config["starting_level"]].get("spawns", {}):
        add(issues, f"game_config.py starts at spawn '{config.get('starting_spawn')}', but that spawn is missing.")

    for character_id, character in characters.items():
        validate_character(character_id, character, issues)
        dialogue_id = character.get("dialogue_id")
        if dialogue_id and dialogue_id not in dialogue:
            add(issues, f"Character '{character_id}' uses dialogue '{dialogue_id}', but that dialogue does not exist.")
    for item_id, item_data in items.items():
        validate_item(item_id, item_data, issues)
    for level_id, level in levels.items():
        validate_level(level_id, level, levels, characters, items, issues)
    validate_hooks(hooks, levels, items, issues)
    validate_student_programming_modules(issues)
    return issues


def main():
    issues = collect_issues()
    if not issues:
        print("LevelKit project check passed. No issues found.")
        return 0
    print(f"{len(issues)} issue{'s' if len(issues) != 1 else ''} found:\n")
    for index, issue in enumerate(issues, start=1):
        print(f"{index}. {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
