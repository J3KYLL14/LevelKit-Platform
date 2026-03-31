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
- installation stays simple: `pip install -r requirements.txt`

This is the minimum viable classroom stack because adding map editors, physics libraries, or external UI frameworks would make setup and debugging harder for teachers.

## 2. Full Folder Structure

```text
LevelKit Platform/
├── README.md
├── requirements.txt
├── run_game.py
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
        ├── items/
        │   ├── __init__.py
        │   └── starter_items.py
        └── levels/
            ├── __init__.py
            ├── room_cavern.py
            └── room_meadow.py
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
/usr/local/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_game.py
```

Important:

- `pygame` is installed per Python version
- if you run the game with Python 3.14 but installed `pygame` under Python 3.13, the import will fail
- for this project, use the same interpreter for venv creation, package install, and launch

## Student Workflow

Students mainly work in:

- `levelkit_platform/content/levels`
- `levelkit_platform/content/characters`
- `levelkit_platform/content/items`
- `levelkit_platform/content/dialogue`
- `levelkit_platform/content/assets`

Example tasks:

- add a new room by copying a level file and changing the `LEVEL` dictionary
- add a new enemy by creating a character file with a new `CHARACTER`
- add a new pickup by editing an item file
- change story text in the dialogue files

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

## Lightweight Level Designer

Students can also build level layouts visually with the included editor:

```bash
python level_designer.py meadow
```

What it supports:

- draw solids, hazards, checkpoints, exits, and win zones
- place spawns, pickups, enemies, and NPCs
- save changes back into the level Python file with `S`

Controls:

- `Tab` switches editing mode
- drag with left mouse to draw rectangle-based elements
- left click places point-based elements
- right click erases the thing under the cursor
- `[` and `]` cycle which enemy, NPC, or item is being placed

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
