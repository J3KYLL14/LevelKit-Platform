# Student Content Guide

The files in this folder are safe for students to edit.

## Safe to change

- `game_config.py`
- `levels/*.py`
- `characters/*.py`
- `items/*.py`
- `dialogue/*.py`
- anything inside `assets/`

## Usually do not change

- anything in `levelkit_platform/engine`

## Content pattern

Most files export plain Python dictionaries or lists.

That means students can:

- copy an existing file
- rename ids
- change numbers, colors, dialogue, and placements
- create new rooms, enemies, pickups, and story moments

without editing the engine.

## Building levels visually

For level layout, start with the visual designer instead of typing coordinates:

```bash
python level_designer.py meadow
```

Use the Level dropdown to switch rooms. Edit the W and H boxes to change the room width and height. Use the Component dropdown to choose what to create, then use the Object dropdown when that component has choices, such as pickups, enemies, NPCs, or exit targets. Use the Sprite dropdown thumbnails to choose a sprite, an object's default sprite, or `Placeholder colour` for the new object. Draw platforms, hazards, exits, checkpoints, and win zones, or click to place spawns, pickups, enemies, and NPCs. Use Select to click an existing object, drag it, nudge it with arrow keys, delete it, resize rectangle objects with handles, copy it, paste it, duplicate it, or update its object and sprite dropdown choices. Undo with `Ctrl+Z` / `Cmd+Z` and redo with `Ctrl+Y` / `Cmd+Shift+Z`. Use Issues to read plain-English validation warnings and Boxes to show collision boxes. The designer snaps new edits to a 32px grid so common 32x32 sprite sheets fit naturally. If a room is larger than the visible canvas, use the bottom and right scrollbars or click the minimap. Save writes the same `levels/*.py` files that can still be edited by hand later. Playtest saves and launches the current level.

## Using sprites

Put sprite images in:

```text
assets/sprites/
```

Then add a `sprite` field to a character or item:

```python
"sprite": "sprites/forest_slime.png",
```

## Programming game content

Beginner content files should use the helpers from `levelkit.py`.

Students should write real game logic in:

- `player_controls.py`: keys and mouse buttons that control the player
- `collision_rules.py`: what happens after collisions are detected

Enemy:

```python
from levelkit import enemy


CHARACTER = enemy(
    "Forest Slime",
    id="forest_slime",
    health=2,
    speed="slow",
    touch_damage=1,
    patrol="short",
)
```

Pickup:

```python
from levelkit import healing_item, quest_item


ITEMS = [
    quest_item("Sun Orb", id="sun_orb"),
    healing_item("Healing Berry", id="berry", heals=1),
]
```

Events:

```python
from levelkit import when_enter_level, when_pickup


when_enter_level("meadow", say="Welcome to the meadow.")
when_pickup("sun_orb", say="You found the Sun Orb!")
```

Useful choices:

- `speed`: `still`, `slow`, `normal`, `fast`
- `jump`: `none`, `low`, `normal`, `high`
- `patrol`: `none`, `short`, `long`
- `size`: `tiny`, `small`, `normal`, `large`

Check the project with:

```bash
python check_project.py
```

## Programming player controls

Edit `player_controls.py`.

```python
def control_player(player, keyboard, mouse, dt):
    player.velocity.x = 0

    if keyboard.left:
        player.velocity.x = -player.speed

    if keyboard.right:
        player.velocity.x = player.speed

    if keyboard.space and player.grounded:
        player.velocity.y = -player.jump_power

    return {
        "melee": keyboard.j or mouse.left,
        "shoot": keyboard.k or mouse.right,
    }
```

Useful input names:

- `keyboard.left`, `keyboard.right`, `keyboard.up`, `keyboard.down`
- `keyboard.space`, `keyboard.shift`
- `keyboard.a`, `keyboard.d`, `keyboard.w`, `keyboard.s`
- `keyboard.j`, `keyboard.k`, `keyboard.e`, `keyboard.r`
- `mouse.left`, `mouse.right`, `mouse.middle`
- `mouse.x`, `mouse.y`, `mouse.position`

## Programming collision outcomes

Edit `collision_rules.py`.

```python
def player_hits_hazard(game, player, hazard):
    game.damage_player(1)


def player_collects_pickup(game, player, pickup):
    game.collect_pickup(pickup)
```

The engine detects which rectangles touch. Students decide what happens next.

The `size` field still controls how large the sprite appears in the game. If the sprite is missing, LevelKit draws the normal colored rectangle instead.

The visual designer also lists images from `assets/sprites/` in its Sprite dropdown and saves the selected sprite onto new level objects. If the selected object has a default sprite, that default appears as the first Sprite dropdown option.

Characters can define horizontal sprite-sheet animations:

```python
"animations": {
    "idle": {"sprite": "sprites/player_idle.png", "frames": 4, "frame_time": 0.15},
    "walk": {"sprite": "sprites/player_walk.png", "frames": 6, "frame_time": 0.10},
}
```

The engine currently switches actor animations between `idle`, `walk`, `jump`, and `fall`.

Level files do not need a `room_` prefix or suffix. Simple names such as `meadow.py`, `cavern.py`, and `boss.py` work.
