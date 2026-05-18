# LevelKit Platform

LevelKit Platform is a minimal-dependency, content-first 2D platformer framework for school students.

It keeps the same teaching philosophy as LevelKit Text:

- students mainly edit content files
- teachers install a small, stable framework once
- the engine handles technical systems such as physics, collisions, combat, and transitions

## 1. Minimum Viable Package Stack

Recommended stack:

- Python 3.13 recommended
- Python 3.11-3.13 supported target
- `pygame`
- Python standard library (`json`, `dataclasses`, `importlib`, `pathlib`, `math`)

Why this stack:

- `pygame` is the only major dependency and is widely used in schools
- it covers windowing, input, sound, fonts, timing, and drawing in one package
- the rest of the framework can stay in plain Python with no extra tooling burden
- installation stays simple: `python3 -m pip install -r requirements.txt`

This is the minimum viable classroom stack because adding map editors, physics libraries, or external UI frameworks would make setup and debugging harder for teachers.

## 2. Full Folder Structure

```text
LevelKit Platform/
├── README.md
├── check_project.py
├── levelkit.py
├── requirements.txt
├── run_game.py
├── docs/
│   ├── 01_play_the_game.md
│   ├── 02_build_a_level.md
│   ├── 03_make_an_enemy.md
│   ├── 04_make_a_pickup.md
│   ├── 05_add_dialogue.md
│   ├── 06_add_sprites.md
│   ├── 07_add_events.md
│   ├── 08_program_player_controls.md
│   ├── 09_program_collision_rules.md
│   └── advanced_engine_reference.md
└── levelkit_platform/
    ├── engine/
    │   ├── __init__.py
    │   ├── animation.py
    │   ├── assets.py
    │   ├── camera.py
    │   ├── combat.py
    │   ├── content_loader.py
    │   ├── entities.py
    │   ├── game.py
    │   ├── hud.py
    │   ├── level.py
    │   ├── settings.py
    │   └── transition.py
    └── content/
        ├── __init__.py
        ├── README.md
        ├── game_config.py
        ├── assets/
        │   ├── audio/
        │   │   └── .gitkeep
        │   ├── sprites/
        │   │   └── .gitkeep
        │   └── ui/
        │       └── .gitkeep
        ├── characters/
        │   ├── __init__.py
        │   ├── forest_slime.py
        │   ├── guide_npc.py
        │   └── player_knight.py
        ├── dialogue/
        │   ├── __init__.py
        │   └── story.py
        ├── collision_rules.py
        ├── events.py
        ├── player_controls.py
        ├── items/
        │   ├── __init__.py
        │   └── starter_items.py
        └── levels/
            ├── __init__.py
            ├── cavern.py
            └── meadow.py
        └── templates/
            ├── new_dialogue.py
            ├── new_enemy.py
            ├── new_events.py
            ├── new_npc.py
            ├── new_pickup.py
            └── new_player.py
```

## 3. Engine Files vs Student-Editable Files

Engine-owned files:

- `levelkit_platform/engine/*`
- these contain the game loop, renderer, physics, camera, collisions, room transitions, animation support, combat core, projectiles, health rules, and HUD rules

Student-editable files:

- `levelkit_platform/content/game_config.py`
- `levelkit_platform/content/levels/*.py`
- `levelkit_platform/content/characters/*.py`
- `levelkit_platform/content/items/*.py`
- `levelkit_platform/content/dialogue/*.py`
- `levelkit_platform/content/assets/*`

Rule of thumb:

- if a student is designing game content, they edit `content`
- if a file changes how the engine works internally, it belongs in `engine`

## 4. Representation of Levels, Characters, and Items

Levels:

- lightweight Python modules that export a `LEVEL` dictionary
- each level contains:
  - room name
  - tile size
  - color theme
  - player spawn
  - platforms and solid tiles
  - hazards
  - exits to other rooms
  - enemy placements
  - NPC placements
  - pickup placements
  - checkpoints
  - win zones

Characters:

- lightweight Python modules that export a `CHARACTER` dictionary
- player, enemy, and NPC definitions reuse the same structure where possible
- definitions include:
  - id and display name
  - role (`player`, `enemy`, `npc`)
  - size and color
  - health, speed, gravity, jump power
  - attack settings
  - optional dialogue id
  - simple AI flags for enemies

Items:

- lightweight Python modules that export one or more item dictionaries in an `ITEMS` list
- items describe:
  - id and name
  - pickup type
  - color and size
  - inventory behavior
  - optional effects such as healing or keys

## 5. Recommended Student Content Format

Recommended approach:

- use lightweight Python modules with plain dictionaries as the default
- allow simple subclasses later only for advanced extension

Why:

- dictionaries are easier for students to read than engine inheritance trees
- Python modules still allow comments, constants, and shared values
- students can stay in a structured format without learning JSON syntax limitations
- teachers can gradually introduce simple subclasses later for advanced classes

So the default content model is:

- Python file
- exports a few named dictionaries and lists
- no engine rewrites required

## 6. Staged Implementation Plan

Stage 1:

- create the engine package
- implement the window, loop, input, gravity, jumping, collisions, camera, fade transition, HUD, and room loading

Stage 2:

- add combat core for melee hitboxes and projectile entities
- add damage, health, respawn, hazards, checkpoints, and a basic win state

Stage 3:

- add student content loaders for levels, characters, items, and dialogue
- create sample rooms, player, enemy, NPC, and pickup definitions

Stage 4:

- add placeholder asset folders and a content guide
- make the project runnable without any external art by using colored rectangles and built-in fonts

Stage 5:

- classroom polish
- document which files students can edit safely
- keep sample content small and readable

## 7. Generated Framework Files

The framework files below are implemented in this repository and produce a runnable Version 1 sample.

## Install

```bash
python3 -m pip install -r requirements.txt
python3 run_game.py
```

Important:

- `pygame` is installed per Python version
- if you run the game with Python 3.14 but installed `pygame` under Python 3.13, the import will fail
- for this project, use the same interpreter for package install and launch
- a virtual environment is optional; LevelKit does not require one

If your Python installation asks for user-level packages, use:

```bash
python3 -m pip install --user -r requirements.txt
python3 run_game.py
```

## Student Workflow

Students mainly work in:

- `levelkit_platform/content/levels`
- `levelkit_platform/content/characters`
- `levelkit_platform/content/items`
- `levelkit_platform/content/dialogue`
- `levelkit_platform/content/assets`

Example tasks:

- build or change a room visually with the level designer
- add a new enemy by creating a character file with a new `CHARACTER`
- add a new pickup by editing an item file
- change story text in the dialogue files

## Visual Level Builder

The preferred beginner workflow is visual:

```bash
python level_designer.py meadow
```

Students can then:

- choose the level from the Level dropdown
- edit the W and H boxes to change the room width and height
- choose a component such as Select, Solid, Hazard, Exit, Spawn, Pickup, Enemy, NPC, or Erase from the Component dropdown
- choose an object from the Object dropdown when that component has options, such as `berry` or `sun_orb` for pickups
- choose a sprite from the Sprite dropdown, or use `Placeholder colour`
- drag to create rectangle-based objects such as platforms, hazards, exits, checkpoints, and win zones
- click to place point-based objects such as spawns, pickups, enemies, and NPCs
- use Select to click an existing object, drag it to a new grid position, or change its object or sprite from the dropdowns
- drag the resize handles on selected rectangle objects to change their width and height
- copy, paste, or duplicate selected objects with the toolbar buttons or `Ctrl` / `Cmd` shortcuts
- use the Issues button to see plain-English validation messages for common level mistakes
- use the collision box toggle to show the exact rectangles the game will use for interactions
- undo and redo changes with the toolbar buttons, `Ctrl+Z` / `Cmd+Z`, and `Ctrl+Y` / `Cmd+Shift+Z`
- use the right and bottom scrollbars when the room is larger than the visible canvas
- click or drag the minimap to jump around large rooms
- right click to erase an object
- click Save to write the room back to `levelkit_platform/content/levels`
- click Playtest to save and launch the game from the current level

Directly editing coordinates in `levels/*.py` still works, but it should be the advanced path rather than the first path for students.

## Beginner Game Programming

Students can program game content with the small `levelkit.py` helper API instead of writing full engine dictionaries immediately.

Students should also program player controls and collision outcomes directly:

- `levelkit_platform/content/player_controls.py`: what keys and mouse buttons make the player do
- `levelkit_platform/content/collision_rules.py`: what happens after the engine detects a collision

That keeps the hard engine algorithms inside the framework, while still requiring students to write meaningful game logic.

Enemy example:

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

Item example:

```python
from levelkit import healing_item, quest_item


ITEMS = [
    quest_item("Sun Orb", id="sun_orb"),
    healing_item("Healing Berry", id="berry", heals=1),
]
```

Useful beginner choices include:

- `speed`: `still`, `slow`, `normal`, `fast`
- `jump`: `none`, `low`, `normal`, `high`
- `patrol`: `none`, `short`, `long`
- `size`: `tiny`, `small`, `normal`, `large`

Check student work with:

```bash
python check_project.py
```

It reports multiple plain-English issues, such as missing dialogue, missing item IDs, invalid roles, or exits that point to missing levels.

## Player Controls

Students edit `levelkit_platform/content/player_controls.py`.

```python
def control_player(player, keyboard, mouse, dt):
    player.velocity.x = 0

    if keyboard.left:
        player.velocity.x = -player.speed
        player.facing = -1

    if keyboard.right:
        player.velocity.x = player.speed
        player.facing = 1

    if keyboard.space and player.grounded:
        player.velocity.y = -player.jump_power
        player.grounded = False

    return {
        "melee": keyboard.j or mouse.left,
        "shoot": keyboard.k or mouse.right,
    }
```

Common input names:

- `keyboard.left`, `keyboard.right`, `keyboard.up`, `keyboard.down`
- `keyboard.space`, `keyboard.shift`
- `keyboard.a`, `keyboard.d`, `keyboard.w`, `keyboard.s`
- `keyboard.j`, `keyboard.k`, `keyboard.e`, `keyboard.r`
- `mouse.left`, `mouse.right`, `mouse.middle`
- `mouse.x`, `mouse.y`, `mouse.position`

More detail is in `docs/08_program_player_controls.md`.

## Collision Rules

Students edit `levelkit_platform/content/collision_rules.py`.

```python
def player_hits_hazard(game, player, hazard):
    game.damage_player(1)


def player_collects_pickup(game, player, pickup):
    game.collect_pickup(pickup)
```

The engine detects the collision; students program the outcome.

More detail is in `docs/09_program_collision_rules.md`.

## Events

Simple event hooks live in `levelkit_platform/content/events.py`.

```python
from levelkit import when_enter_level, when_pickup


when_enter_level("meadow", say="Welcome to the meadow.")
when_pickup("sun_orb", say="You found the Sun Orb!")
```

Advanced students can pass a function to run custom Python when an event happens.

## Runtime Debug Tools

While the game is running:

- `F1`: show debug help
- `F2`: show player position, velocity, grounded state, and game status
- `F3`: show collision boxes
- `F4`: show object IDs
- `F5`: restart from the current checkpoint

## Sprites

Students can use image files instead of colored rectangles by placing them in:

```text
levelkit_platform/content/assets/sprites/
```

The visual level builder lists those images in the Sprite dropdown. Choose a component, choose an object when available, choose a sprite, then draw or place the object. The selected sprite is saved into the level file for solids, hazards, checkpoints, exits, win zones, spawns, pickups, enemies, and NPCs.

The designer grid is 32 pixels, which lines up cleanly with common 32x32 tile and sprite-sheet artwork. Existing coordinates still load exactly as written; new drawing and movement snaps to the 32px grid.

Students can also add a default `sprite` field to a character or item definition:

```python
CHARACTER = {
    "id": "forest_slime",
    "name": "Forest Slime",
    "role": "enemy",
    "size": (34, 28),
    "color": (120, 220, 120),
    "sprite": "sprites/forest_slime.png",
}
```

Items use the same pattern:

```python
{
    "id": "berry",
    "name": "Healing Berry",
    "size": (18, 18),
    "color": (222, 72, 132),
    "sprite": "sprites/berry.png",
}
```

If the sprite file is missing or the `sprite` field is not set, the game falls back to the existing colored rectangle.

When a selected object has a default sprite, the first Sprite dropdown option shows that default. Choosing `Placeholder colour` means LevelKit uses the object color instead.

Characters can also define simple horizontal sprite-sheet animations:

```python
"animations": {
    "idle": {"sprite": "sprites/player_idle.png", "frames": 4, "frame_time": 0.15},
    "walk": {"sprite": "sprites/player_walk.png", "frames": 6, "frame_time": 0.10},
    "jump": {"sprite": "sprites/player_jump.png", "frames": 2, "frame_time": 0.12},
    "fall": {"sprite": "sprites/player_fall.png", "frames": 2, "frame_time": 0.12},
}
```

Each sheet should place frames side-by-side in one row.

## Level Visual Previews

Reading raw coordinates is hard for beginners, so the project includes a simple preview exporter:

```bash
python preview_levels.py
```

It generates color-coded PNG overview maps in `level_previews/` so students can see:

- platforms and solids
- hazards
- checkpoints
- exits
- win zones
- spawns
- enemies, NPCs, and pickups

This keeps level authoring content-first while making the placement data much easier to understand.

## Lightweight Level Designer Details

Students can also build level layouts visually with the included editor:

```bash
python level_designer.py meadow
```

What it supports:

- draw solids, hazards, checkpoints, exits, and win zones
- place spawns, pickups, enemies, and NPCs
- select existing objects, move them, and update their object or sprite choices
- choose sprites from `content/assets/sprites`
- see passive warnings for common layout mistakes such as duplicate pickups, missing exit spawns, or objects outside the room
- navigate large rooms with a minimap
- save changes back into the level Python file with the Save button or `S`
- launch the current level with Playtest

Controls:

- use the Level dropdown to switch rooms without relaunching the editor
- edit W/H to change `world_size`; press Enter or Save to apply the typed value
- use the Component dropdown or press `Tab` to switch editing mode
- use the Object dropdown to choose the pickup, enemy, NPC, or exit target where available
- use the Sprite dropdown to choose the sprite saved on newly created objects, or `Placeholder colour` for a plain rectangle
- in Select mode, use the Object and Sprite dropdowns to edit the selected object
- use the Sprite dropdown thumbnails to identify assets visually
- drag with left mouse to draw rectangle-based elements
- left click places point-based elements
- in Select mode, click an object to select it, drag to move it, press arrow keys to nudge it, or press Delete/Backspace to remove it
- use `Ctrl+Z` / `Cmd+Z` to undo and `Ctrl+Y` / `Cmd+Shift+Z` to redo
- right click erases the thing under the cursor
- drag the right or bottom scrollbar, or use the mouse wheel over the canvas to scroll
- click or drag on the minimap to move around the room

This is intentionally lightweight rather than a full game editor. It is designed to help students sketch and build rooms visually while keeping the framework simple and classroom-friendly.

Important design choice:

- the visual tool generates level code into the student content files in `levelkit_platform/content/levels`
- it does not write into the engine
- that keeps the engine stable and keeps student work in the part of the project they are supposed to own

## Plain-English Errors

When content files have problems, the framework now tries to explain them in plain English.

Examples:

- missing character ids
- missing item ids
- exits pointing to a room that does not exist
- NPCs pointing to missing dialogue
- Python syntax mistakes such as a missing comma

The goal is that students see a useful explanation first, with the technical detail included only as backup.

## Version 1 Features Included

- left and right movement
- jumping with gravity
- solid platform collision
- multiple rooms from a `levels` folder
- room-to-room transitions with fullscreen fade
- hazards
- enemies that damage the player
- melee and projectile attacks
- item pickups with inventory-ready tracking
- NPC interaction and dialogue
- checkpoint respawn
- win state and lose/reset behavior
