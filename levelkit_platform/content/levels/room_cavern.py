LEVEL = {
    "id": "cavern",
    "name": "Shadow Cavern",
    "background": (38, 38, 64),
    "world_size": (1560, 760),
    "spawns": {
        "default": {"x": 80, "y": 120},
        "checkpoint": {"x": 740, "y": 420},
    },
    "solids": [
        {"x": 0, "y": 520, "w": 540, "h": 140},
        {"x": 620, "y": 520, "w": 400, "h": 140},
        {"x": 1080, "y": 520, "w": 480, "h": 140},
        {"x": 0, "y": 160, "w": 180, "h": 24},
        {"x": 260, "y": 250, "w": 160, "h": 24},
        {"x": 540, "y": 360, "w": 160, "h": 24},
        {"x": 790, "y": 430, "w": 120, "h": 24},
        {"x": 1160, "y": 360, "w": 120, "h": 24},
    ],
    "hazards": [
        {"x": 540, "y": 560, "w": 80, "h": 40},
        {"x": 1020, "y": 560, "w": 60, "h": 40},
    ],
    "checkpoints": [
        {"x": 780, "y": 384, "w": 20, "h": 46},
    ],
    "pickups": [
        {"item_id": "berry", "x": 290, "y": 224},
    ],
    "enemies": [
        {"character_id": "forest_slime", "x": 320, "y": 492},
        {"character_id": "forest_slime", "x": 1260, "y": 332},
    ],
    "npcs": [],
    "exits": [
        {"x": 0, "y": 80, "w": 24, "h": 120, "target_level": "meadow", "target_spawn": "from_cavern"},
    ],
    "win_zones": [
        {"x": 1440, "y": 280, "w": 60, "h": 100},
    ],
}
