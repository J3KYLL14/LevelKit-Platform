import copy
import pprint
import sys
from pathlib import Path

import pygame

from levelkit_platform.engine.content_loader import load_definitions, load_levels
from levelkit_platform.engine.errors import PlainEnglishError


WINDOW_SIZE = (1400, 900)
PADDING = 30
GRID_SIZE = 20
MODES = [
    "solids",
    "hazards",
    "checkpoints",
    "win_zones",
    "exits",
    "spawns",
    "pickups",
    "enemies",
    "npcs",
    "erase",
]
MODE_COLORS = {
    "solids": (88, 102, 132),
    "hazards": (214, 70, 70),
    "checkpoints": (110, 220, 150),
    "win_zones": (255, 214, 96),
    "exits": (98, 170, 255),
    "spawns": (255, 255, 255),
    "pickups": (255, 150, 210),
    "enemies": (255, 120, 120),
    "npcs": (230, 210, 140),
}
FILE_BY_KEY = {
    "solids": "solids",
    "hazards": "hazards",
    "checkpoints": "checkpoints",
    "win_zones": "win_zones",
    "exits": "exits",
    "pickups": "pickups",
    "enemies": "enemies",
    "npcs": "npcs",
}


class LevelDesigner:
    def __init__(self, level_id):
        pygame.init()
        pygame.display.set_caption("LevelKit Platform Level Designer")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 34)
        self.levels, self.modules = load_levels()
        self.level_id = level_id
        self.level = copy.deepcopy(self.levels[level_id])
        self.level_module_path = Path(self.modules[level_id].__file__)
        self.character_defs = load_definitions("characters", "CHARACTER")
        self.item_defs = load_definitions("items", "ITEMS")
        self.mode_index = 0
        self.selection_index = 0
        self.drag_start = None
        self.message = ""
        self.message_timer = 0.0

    @property
    def mode(self):
        return MODES[self.mode_index]

    def scale(self):
        world_w, world_h = self.level["world_size"]
        draw_w = WINDOW_SIZE[0] - (PADDING * 2)
        draw_h = WINDOW_SIZE[1] - 170
        return draw_w / world_w, draw_h / world_h

    def snap_world(self, world_x, world_y):
        return (world_x // GRID_SIZE) * GRID_SIZE, (world_y // GRID_SIZE) * GRID_SIZE

    def screen_to_world(self, pos):
        scale_x, scale_y = self.scale()
        x = max(0, min(self.level["world_size"][0], int((pos[0] - PADDING) / scale_x)))
        y = max(0, min(self.level["world_size"][1], int((pos[1] - PADDING) / scale_y)))
        return self.snap_world(x, y)

    def world_to_screen_rect(self, rect_data):
        scale_x, scale_y = self.scale()
        return pygame.Rect(
            int(rect_data["x"] * scale_x) + PADDING,
            int(rect_data["y"] * scale_y) + PADDING,
            max(2, int(rect_data["w"] * scale_x)),
            max(2, int(rect_data["h"] * scale_y)),
        )

    def world_to_screen_point(self, point_data, size=12):
        scale_x, scale_y = self.scale()
        return pygame.Rect(
            int(point_data["x"] * scale_x) + PADDING,
            int(point_data["y"] * scale_y) + PADDING,
            size,
            size,
        )

    def selected_ids(self):
        if self.mode == "pickups":
            return sorted(self.item_defs)
        if self.mode in {"enemies", "npcs"}:
            role = "enemy" if self.mode == "enemies" else "npc"
            return sorted(
                character_id
                for character_id, data in self.character_defs.items()
                if data["role"] == role
            )
        return []

    def current_selection(self):
        ids = self.selected_ids()
        if not ids:
            return None
        self.selection_index %= len(ids)
        return ids[self.selection_index]

    def add_rect_item(self, start, end):
        x1, y1 = start
        x2, y2 = end
        x = min(x1, x2)
        y = min(y1, y2)
        w = max(GRID_SIZE, abs(x2 - x1) + GRID_SIZE)
        h = max(GRID_SIZE, abs(y2 - y1) + GRID_SIZE)
        target = self.level[FILE_BY_KEY[self.mode]]
        item = {"x": x, "y": y, "w": w, "h": h}
        if self.mode == "exits":
            other_levels = [candidate for candidate in self.levels if candidate != self.level_id]
            item["target_level"] = other_levels[0] if other_levels else self.level_id
            item["target_spawn"] = "default"
        target.append(item)

    def add_point_item(self, world_pos):
        if self.mode == "spawns":
            spawn_name = f"spawn_{len(self.level['spawns'])}"
            self.level["spawns"][spawn_name] = {"x": world_pos[0], "y": world_pos[1]}
        elif self.mode == "pickups":
            self.level["pickups"].append(
                {"item_id": self.current_selection(), "x": world_pos[0], "y": world_pos[1]}
            )
        elif self.mode == "enemies":
            self.level["enemies"].append(
                {"character_id": self.current_selection(), "x": world_pos[0], "y": world_pos[1]}
            )
        elif self.mode == "npcs":
            self.level["npcs"].append(
                {"character_id": self.current_selection(), "x": world_pos[0], "y": world_pos[1]}
            )

    def erase_at(self, world_pos):
        probe = pygame.Rect(world_pos[0], world_pos[1], GRID_SIZE, GRID_SIZE)
        for key in ["solids", "hazards", "checkpoints", "win_zones", "exits"]:
            for item in reversed(self.level.get(key, [])):
                rect = pygame.Rect(item["x"], item["y"], item["w"], item["h"])
                if rect.colliderect(probe):
                    self.level[key].remove(item)
                    return
        for key in ["pickups", "enemies", "npcs"]:
            for item in reversed(self.level.get(key, [])):
                rect = pygame.Rect(item["x"], item["y"], GRID_SIZE, GRID_SIZE)
                if rect.colliderect(probe):
                    self.level[key].remove(item)
                    return
        for spawn_name, spawn in list(self.level.get("spawns", {}).items()):
            rect = pygame.Rect(spawn["x"], spawn["y"], GRID_SIZE, GRID_SIZE)
            if rect.colliderect(probe) and spawn_name not in {"default", "from_cavern", "checkpoint"}:
                del self.level["spawns"][spawn_name]
                return

    def save(self):
        text = (
            "# This file can be edited by hand or generated by level_designer.py.\n"
            "# Students should edit content files like this one, not the engine.\n\n"
            "LEVEL = "
            + pprint.pformat(self.level, sort_dicts=False, width=100)
            + "\n"
        )
        self.level_module_path.write_text(text)
        self.message = f"Saved {self.level_module_path.name}"
        self.message_timer = 2.5

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.mode_index = (self.mode_index + 1) % len(MODES)
                self.selection_index = 0
            elif event.key == pygame.K_LEFTBRACKET:
                self.selection_index -= 1
            elif event.key == pygame.K_RIGHTBRACKET:
                self.selection_index += 1
            elif event.key == pygame.K_s:
                self.save()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            world_pos = self.screen_to_world(event.pos)
            if self.mode in FILE_BY_KEY:
                self.drag_start = world_pos
            elif self.mode in {"spawns", "pickups", "enemies", "npcs"}:
                self.add_point_item(world_pos)
            elif self.mode == "erase":
                self.erase_at(world_pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_start and self.mode in FILE_BY_KEY:
                world_pos = self.screen_to_world(event.pos)
                self.add_rect_item(self.drag_start, world_pos)
            self.drag_start = None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.erase_at(self.screen_to_world(event.pos))

    def draw_rect_layer(self, key, color, outline=False):
        for item in self.level.get(key, []):
            rect = self.world_to_screen_rect(item)
            if outline:
                pygame.draw.rect(self.screen, color, rect, width=3, border_radius=3)
            else:
                pygame.draw.rect(self.screen, color, rect, border_radius=3)
            if key == "exits":
                self.screen.blit(
                    self.font.render(item["target_level"], True, (245, 245, 245)),
                    (rect.x, max(10, rect.y - 18)),
                )

    def draw_point_layer(self, key, color, label_key):
        for item in self.level.get(key, []):
            rect = self.world_to_screen_point(item)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            self.screen.blit(
                self.font.render(item[label_key], True, (245, 245, 245)),
                (rect.x + 16, rect.y - 2),
            )

    def draw(self):
        self.screen.fill(self.level.get("background", (30, 30, 48)))
        draw_w = WINDOW_SIZE[0] - (PADDING * 2)
        draw_h = WINDOW_SIZE[1] - 170
        frame = pygame.Rect(PADDING, PADDING, draw_w, draw_h)
        pygame.draw.rect(self.screen, (240, 240, 240), frame, width=2)

        scale_x, scale_y = self.scale()
        for x in range(0, self.level["world_size"][0] + GRID_SIZE, GRID_SIZE):
            sx = int(x * scale_x) + PADDING
            pygame.draw.line(self.screen, (70, 80, 100), (sx, PADDING), (sx, PADDING + draw_h), 1)
        for y in range(0, self.level["world_size"][1] + GRID_SIZE, GRID_SIZE):
            sy = int(y * scale_y) + PADDING
            pygame.draw.line(self.screen, (70, 80, 100), (PADDING, sy), (PADDING + draw_w, sy), 1)

        self.draw_rect_layer("solids", MODE_COLORS["solids"])
        self.draw_rect_layer("hazards", MODE_COLORS["hazards"])
        self.draw_rect_layer("checkpoints", MODE_COLORS["checkpoints"])
        self.draw_rect_layer("win_zones", MODE_COLORS["win_zones"], outline=True)
        self.draw_rect_layer("exits", MODE_COLORS["exits"], outline=True)

        for spawn_name, spawn in self.level["spawns"].items():
            rect = self.world_to_screen_point(spawn)
            pygame.draw.rect(self.screen, MODE_COLORS["spawns"], rect, border_radius=6)
            self.screen.blit(self.font.render(spawn_name, True, (245, 245, 245)), (rect.x + 16, rect.y - 2))

        self.draw_point_layer("pickups", MODE_COLORS["pickups"], "item_id")
        self.draw_point_layer("enemies", MODE_COLORS["enemies"], "character_id")
        self.draw_point_layer("npcs", MODE_COLORS["npcs"], "character_id")

        if self.drag_start and self.mode in FILE_BY_KEY:
            mouse_world = self.screen_to_world(pygame.mouse.get_pos())
            x1, y1 = self.drag_start
            x2, y2 = mouse_world
            preview = {
                "x": min(x1, x2),
                "y": min(y1, y2),
                "w": max(GRID_SIZE, abs(x2 - x1) + GRID_SIZE),
                "h": max(GRID_SIZE, abs(y2 - y1) + GRID_SIZE),
            }
            pygame.draw.rect(
                self.screen,
                MODE_COLORS[self.mode],
                self.world_to_screen_rect(preview),
                width=2,
                border_radius=3,
            )

        ui_top = WINDOW_SIZE[1] - 120
        pygame.draw.rect(self.screen, (12, 16, 24), (0, ui_top, WINDOW_SIZE[0], 120))
        title = f"{self.level['name']} | mode: {self.mode}"
        self.screen.blit(self.title_font.render(title, True, (245, 245, 245)), (24, ui_top + 12))
        help_text = "Tab: mode  |  drag: draw rects  |  click: place points  |  right click: erase  |  S: save"
        self.screen.blit(self.font.render(help_text, True, (220, 220, 220)), (24, ui_top + 48))
        selection = self.current_selection()
        if selection:
            self.screen.blit(
                self.font.render(f"[ / ] selection: {selection}", True, (220, 220, 220)),
                (24, ui_top + 76),
            )
        else:
            self.screen.blit(
                self.font.render("Current mode does not use item selection.", True, (220, 220, 220)),
                (24, ui_top + 76),
            )
        if self.message_timer > 0:
            self.screen.blit(
                self.font.render(self.message, True, (110, 220, 150)),
                (WINDOW_SIZE[0] - 240, ui_top + 18),
            )

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            self.message_timer = max(0.0, self.message_timer - dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    levels, _ = load_levels()
    level_id = sys.argv[1] if len(sys.argv) > 1 else sorted(levels)[0]
    if level_id not in levels:
        valid = ", ".join(sorted(levels))
        raise SystemExit(f"Unknown level '{level_id}'. Choose one of: {valid}")
    LevelDesigner(level_id).run()


if __name__ == "__main__":
    try:
        main()
    except PlainEnglishError as exc:
        raise SystemExit(str(exc)) from exc
