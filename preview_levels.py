from pathlib import Path

import pygame

from levelkit_platform.engine.content_loader import load_definitions, load_levels
from levelkit_platform.engine.errors import PlainEnglishError


OUTPUT_DIR = Path("level_previews")
PREVIEW_WIDTH = 1200
PREVIEW_HEIGHT = 720
PADDING = 40

COLORS = {
    "solid": (88, 102, 132),
    "hazard": (214, 70, 70),
    "exit": (98, 170, 255),
    "checkpoint": (110, 220, 150),
    "win_zone": (255, 214, 96),
    "spawn": (255, 255, 255),
}


def scale_rect(rect_data, scale_x, scale_y):
    return pygame.Rect(
        int(rect_data["x"] * scale_x) + PADDING,
        int(rect_data["y"] * scale_y) + PADDING,
        max(2, int(rect_data["w"] * scale_x)),
        max(2, int(rect_data["h"] * scale_y)),
    )


def scale_point(point_data, scale_x, scale_y, size=12):
    return pygame.Rect(
        int(point_data["x"] * scale_x) + PADDING,
        int(point_data["y"] * scale_y) + PADDING,
        size,
        size,
    )


def draw_label(surface, font, text, pos, color=(245, 245, 245)):
    label = font.render(text, True, color)
    surface.blit(label, pos)


def render_level(level_def, character_defs, item_defs, font):
    world_width, world_height = level_def["world_size"]
    draw_width = PREVIEW_WIDTH - (PADDING * 2)
    draw_height = PREVIEW_HEIGHT - (PADDING * 2)
    scale_x = draw_width / world_width
    scale_y = draw_height / world_height

    surface = pygame.Surface((PREVIEW_WIDTH, PREVIEW_HEIGHT))
    surface.fill(level_def.get("background", (30, 30, 48)))

    world_rect = pygame.Rect(PADDING, PADDING, draw_width, draw_height)
    pygame.draw.rect(surface, (235, 235, 235), world_rect, width=2)

    for solid in level_def.get("solids", []):
        pygame.draw.rect(surface, COLORS["solid"], scale_rect(solid, scale_x, scale_y), border_radius=3)

    for hazard in level_def.get("hazards", []):
        pygame.draw.rect(surface, COLORS["hazard"], scale_rect(hazard, scale_x, scale_y), border_radius=3)

    for exit_zone in level_def.get("exits", []):
        rect = scale_rect(exit_zone, scale_x, scale_y)
        pygame.draw.rect(surface, COLORS["exit"], rect, width=3, border_radius=3)
        draw_label(surface, font, f"Exit -> {exit_zone['target_level']}", (rect.x, max(8, rect.y - 20)))

    for checkpoint in level_def.get("checkpoints", []):
        pygame.draw.rect(surface, COLORS["checkpoint"], scale_rect(checkpoint, scale_x, scale_y), border_radius=3)

    for win_zone in level_def.get("win_zones", []):
        rect = scale_rect(win_zone, scale_x, scale_y)
        pygame.draw.rect(surface, COLORS["win_zone"], rect, width=4, border_radius=3)
        draw_label(surface, font, "Win", (rect.x, max(8, rect.y - 20)))

    for spawn_id, spawn in level_def.get("spawns", {}).items():
        rect = scale_point(spawn, scale_x, scale_y)
        pygame.draw.rect(surface, COLORS["spawn"], rect, border_radius=6)
        draw_label(surface, font, f"Spawn: {spawn_id}", (rect.x + 16, rect.y - 2))

    for placement in level_def.get("pickups", []):
        item = item_defs[placement["item_id"]]
        rect = pygame.Rect(
            int(placement["x"] * scale_x) + PADDING,
            int(placement["y"] * scale_y) + PADDING,
            max(4, int(item["size"][0] * scale_x)),
            max(4, int(item["size"][1] * scale_y)),
        )
        pygame.draw.rect(surface, item["color"], rect, border_radius=5)
        draw_label(surface, font, item["id"], (rect.x + 14, rect.y - 2))

    for placement in level_def.get("enemies", []):
        character = character_defs[placement["character_id"]]
        rect = pygame.Rect(
            int(placement["x"] * scale_x) + PADDING,
            int(placement["y"] * scale_y) + PADDING,
            max(6, int(character["size"][0] * scale_x)),
            max(6, int(character["size"][1] * scale_y)),
        )
        pygame.draw.rect(surface, character["color"], rect, border_radius=6)
        draw_label(surface, font, placement["character_id"], (rect.x + 10, rect.y - 2))

    for placement in level_def.get("npcs", []):
        character = character_defs[placement["character_id"]]
        rect = pygame.Rect(
            int(placement["x"] * scale_x) + PADDING,
            int(placement["y"] * scale_y) + PADDING,
            max(6, int(character["size"][0] * scale_x)),
            max(6, int(character["size"][1] * scale_y)),
        )
        pygame.draw.rect(surface, character["color"], rect, border_radius=6)
        draw_label(surface, font, placement["character_id"], (rect.x + 10, rect.y - 2))

    draw_label(surface, pygame.font.SysFont(None, 38), level_def["name"], (PADDING, 10))
    draw_label(surface, font, f"World: {world_width} x {world_height}", (PREVIEW_WIDTH - 220, 16))

    legend_items = [
        ("Solid", COLORS["solid"]),
        ("Hazard", COLORS["hazard"]),
        ("Checkpoint", COLORS["checkpoint"]),
        ("Exit", COLORS["exit"]),
        ("Win Zone", COLORS["win_zone"]),
        ("Spawn", COLORS["spawn"]),
    ]
    legend_x = PADDING
    legend_y = PREVIEW_HEIGHT - 28
    for label, color in legend_items:
        pygame.draw.rect(surface, color, (legend_x, legend_y, 18, 18), border_radius=4)
        draw_label(surface, font, label, (legend_x + 24, legend_y))
        legend_x += 140

    return surface


def main():
    pygame.init()
    pygame.font.init()
    OUTPUT_DIR.mkdir(exist_ok=True)
    font = pygame.font.SysFont(None, 22)
    levels, _ = load_levels()
    character_defs = load_definitions("characters", "CHARACTER")
    item_defs = load_definitions("items", "ITEMS")

    for level_id, level_def in levels.items():
        surface = render_level(level_def, character_defs, item_defs, font)
        output_path = OUTPUT_DIR / f"{level_id}.png"
        pygame.image.save(surface, output_path)
        print(f"Saved {output_path}")

    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except PlainEnglishError as exc:
        raise SystemExit(str(exc)) from exc
