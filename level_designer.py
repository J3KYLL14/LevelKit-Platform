import copy
import pprint
import subprocess
import sys
from pathlib import Path

try:
    import pygame
except ModuleNotFoundError as exc:
    if exc.name == "pygame":
        raise SystemExit(
            "LevelKit Platform requires pygame, and pygame is not installed for this Python interpreter.\n"
            "Install it once for the Python you want to use, then run the designer with that same Python:\n"
            "  python3 -m pip install -r requirements.txt\n"
            "  python3 level_designer.py meadow\n"
            "A virtual environment is optional; LevelKit does not require one."
        ) from exc
    raise

from levelkit_platform.engine.assets import ASSET_DIR, AssetLibrary
from levelkit_platform.engine.content_loader import load_definitions, load_levels
from levelkit_platform.engine.errors import PlainEnglishError


WINDOW_SIZE = (1400, 900)
PADDING = 30
GRID_SIZE = 32
HEADER_HEIGHT = 64
UI_HEIGHT = 108
SCROLLBAR_SIZE = 16
MIN_WORLD_SIZE = (320, 240)
SPRITE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
NO_SPRITE_LABEL = "Placeholder colour"
HISTORY_LIMIT = 60
HANDLE_SIZE = 10
CLONE_OFFSET = GRID_SIZE
MODES = [
    "select",
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
MODE_LABELS = {
    "select": "Select",
    "solids": "Solid",
    "hazards": "Hazard",
    "checkpoints": "Checkpoint",
    "win_zones": "Win",
    "exits": "Exit",
    "spawns": "Spawn",
    "pickups": "Pickup",
    "enemies": "Enemy",
    "npcs": "NPC",
    "erase": "Erase",
}
MODE_COLORS = {
    "select": (98, 170, 255),
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
}
POINT_MODES = {"spawns", "pickups", "enemies", "npcs"}


class LevelDesigner:
    def __init__(self, level_id):
        pygame.init()
        pygame.display.set_caption("LevelKit Platform Level Designer")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.assets = AssetLibrary()
        self.assets.init()
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 34)
        self.levels, self.modules = load_levels()
        self.level_id = level_id
        self.level = copy.deepcopy(self.levels[level_id])
        self.level_module_path = Path(self.modules[level_id].__file__)
        self.character_defs = load_definitions("characters", "CHARACTER")
        self.item_defs = load_definitions("items", "ITEMS")
        self.sprite_options = self.load_sprite_options()
        self.mode_index = 0
        self.selection_index = 0
        self.sprite_index = 0
        self.drag_start = None
        self.selected_object = None
        self.move_drag = None
        self.resize_drag = None
        self.clipboard_object = None
        self.undo_stack = []
        self.redo_stack = []
        self.message = ""
        self.message_timer = 0.0
        self.level_dropdown_open = False
        self.component_dropdown_open = False
        self.object_dropdown_open = False
        self.sprite_dropdown_open = False
        self.pending_level_id = None
        self.dirty = False
        self.scroll_x = 0
        self.scroll_y = 0
        self.scroll_drag = None
        self.minimap_drag = False
        self.show_collision_boxes = False
        self.validation_panel_open = False
        self.active_size_field = None
        self.size_field_replace = False
        self.room_size_inputs = {}
        self.sync_room_size_inputs()

    @property
    def mode(self):
        return MODES[self.mode_index]

    def draw_area_size(self):
        return WINDOW_SIZE[0] - (PADDING * 2), WINDOW_SIZE[1] - HEADER_HEIGHT - UI_HEIGHT - PADDING

    def ui_top(self):
        return WINDOW_SIZE[1] - UI_HEIGHT

    def header_rect(self):
        return pygame.Rect(0, 0, WINDOW_SIZE[0], HEADER_HEIGHT)

    def base_canvas_rect(self):
        draw_w, draw_h = self.draw_area_size()
        return pygame.Rect(PADDING, HEADER_HEIGHT, draw_w, draw_h)

    def scroll_layout(self):
        base = self.base_canvas_rect()
        world_w, world_h = self.level["world_size"]
        need_h = world_w > base.w
        need_v = world_h > base.h
        for _ in range(2):
            view_w = base.w - (SCROLLBAR_SIZE if need_v else 0)
            view_h = base.h - (SCROLLBAR_SIZE if need_h else 0)
            need_h = world_w > view_w
            need_v = world_h > view_h

        view_w = base.w - (SCROLLBAR_SIZE if need_v else 0)
        view_h = base.h - (SCROLLBAR_SIZE if need_h else 0)
        viewport = pygame.Rect(base.x, base.y, view_w, view_h)
        hbar = pygame.Rect(base.x, viewport.bottom, viewport.w, SCROLLBAR_SIZE) if need_h else None
        vbar = pygame.Rect(viewport.right, base.y, SCROLLBAR_SIZE, viewport.h) if need_v else None
        return viewport, hbar, vbar

    def viewport_rect(self):
        return self.scroll_layout()[0]

    def max_scroll(self):
        viewport = self.viewport_rect()
        world_w, world_h = self.level["world_size"]
        return max(0, world_w - viewport.w), max(0, world_h - viewport.h)

    def clamp_scroll(self):
        max_x, max_y = self.max_scroll()
        self.scroll_x = max(0, min(self.scroll_x, max_x))
        self.scroll_y = max(0, min(self.scroll_y, max_y))

    def minimap_rect(self):
        viewport = self.viewport_rect()
        world_w, world_h = self.level["world_size"]
        max_w = 220
        max_h = 130
        scale = min(max_w / world_w, max_h / world_h, 1)
        width = max(80, int(world_w * scale))
        height = max(50, int(world_h * scale))
        return pygame.Rect(viewport.right - width - 16, viewport.y + 16, width, height)

    def minimap_scale(self):
        rect = self.minimap_rect()
        world_w, world_h = self.level["world_size"]
        return rect.w / world_w, rect.h / world_h

    def set_scroll_from_minimap(self, pos):
        rect = self.minimap_rect()
        scale_x, scale_y = self.minimap_scale()
        world_x = max(0, min(self.level["world_size"][0], int((pos[0] - rect.x) / scale_x)))
        world_y = max(0, min(self.level["world_size"][1], int((pos[1] - rect.y) / scale_y)))
        viewport = self.viewport_rect()
        self.scroll_x = world_x - viewport.w // 2
        self.scroll_y = world_y - viewport.h // 2
        self.clamp_scroll()

    def handle_minimap_down(self, pos):
        if self.minimap_rect().collidepoint(pos):
            self.minimap_drag = True
            self.set_scroll_from_minimap(pos)
            return True
        return False

    def handle_minimap_motion(self, pos):
        if not self.minimap_drag:
            return False
        self.set_scroll_from_minimap(pos)
        return True

    def snap_world(self, world_x, world_y):
        return (world_x // GRID_SIZE) * GRID_SIZE, (world_y // GRID_SIZE) * GRID_SIZE

    def screen_to_world(self, pos):
        viewport = self.viewport_rect()
        x = max(0, min(self.level["world_size"][0], int(pos[0] - viewport.x + self.scroll_x)))
        y = max(0, min(self.level["world_size"][1], int(pos[1] - viewport.y + self.scroll_y)))
        return self.snap_world(x, y)

    def world_to_screen_rect(self, rect_data):
        viewport = self.viewport_rect()
        return pygame.Rect(
            int(rect_data["x"] - self.scroll_x + viewport.x),
            int(rect_data["y"] - self.scroll_y + viewport.y),
            max(2, int(rect_data["w"])),
            max(2, int(rect_data["h"])),
        )

    def world_to_screen_point(self, point_data, size=12):
        viewport = self.viewport_rect()
        return pygame.Rect(
            int(point_data["x"] - self.scroll_x + viewport.x),
            int(point_data["y"] - self.scroll_y + viewport.y),
            size,
            size,
        )

    def world_to_screen_sized_point(self, point_data, size):
        viewport = self.viewport_rect()
        return pygame.Rect(
            int(point_data["x"] - self.scroll_x + viewport.x),
            int(point_data["y"] - self.scroll_y + viewport.y),
            max(4, int(size[0])),
            max(4, int(size[1])),
        )

    def selected_ids(self):
        mode = self.mode
        if mode == "select" and self.selected_object:
            mode = self.selected_object["key"]
        if mode == "exits":
            return sorted(candidate for candidate in self.levels if candidate != self.level_id)
        if mode == "pickups":
            return sorted(self.item_defs)
        if mode in {"enemies", "npcs"}:
            role = "enemy" if mode == "enemies" else "npc"
            return sorted(
                character_id
                for character_id, data in self.character_defs.items()
                if data["role"] == role
            )
        return []

    def load_sprite_options(self):
        sprite_dir = ASSET_DIR / "sprites"
        if not sprite_dir.exists():
            return []
        return sorted(
            path.relative_to(ASSET_DIR).as_posix()
            for path in sprite_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in SPRITE_EXTENSIONS
        )

    def sprite_choices(self):
        return [self.default_sprite_label()] + self.sprite_options

    def current_sprite(self):
        choices = self.sprite_choices()
        if not choices:
            return None
        self.sprite_index %= len(choices)
        selected = choices[self.sprite_index]
        if selected == self.default_sprite_label():
            return None
        return selected

    def current_sprite_label(self):
        return self.current_sprite() or self.default_sprite_label()

    def sprite_preview_path(self, index=None):
        if index is None:
            index = self.sprite_index
        if index == 0:
            return self.default_sprite()
        choices = self.sprite_choices()
        if 0 <= index < len(choices):
            return choices[index]
        return None

    def current_definition(self):
        selected = self.current_selection()
        if not selected:
            return None
        mode = self.mode
        if mode == "select" and self.selected_object:
            mode = self.selected_object["key"]
        if mode == "pickups":
            return self.item_defs.get(selected)
        if mode in {"enemies", "npcs"}:
            return self.character_defs.get(selected)
        return None

    def default_sprite(self):
        definition = self.current_definition()
        if not definition:
            return None
        return definition.get("sprite")

    def default_sprite_label(self):
        sprite = self.default_sprite()
        if sprite:
            return f"Default: {sprite}"
        return NO_SPRITE_LABEL

    def current_selection(self):
        ids = self.selected_ids()
        if not ids:
            return None
        self.selection_index %= len(ids)
        return ids[self.selection_index]

    def snapshot_level(self):
        return copy.deepcopy(self.level)

    def push_undo(self):
        self.undo_stack.append(self.snapshot_level())
        if len(self.undo_stack) > HISTORY_LIMIT:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def restore_snapshot(self, snapshot):
        self.level = copy.deepcopy(snapshot)
        self.selected_object = None
        self.drag_start = None
        self.move_drag = None
        self.resize_drag = None
        self.sync_room_size_inputs()
        self.clamp_scroll()
        self.dirty = True
        self.pending_level_id = None

    def undo(self):
        if not self.undo_stack:
            self.message = "Nothing to undo."
            self.message_timer = 2.0
            return
        self.redo_stack.append(self.snapshot_level())
        self.restore_snapshot(self.undo_stack.pop())
        self.message = "Undid last change."
        self.message_timer = 2.0

    def redo(self):
        if not self.redo_stack:
            self.message = "Nothing to redo."
            self.message_timer = 2.0
            return
        self.undo_stack.append(self.snapshot_level())
        self.restore_snapshot(self.redo_stack.pop())
        self.message = "Redid change."
        self.message_timer = 2.0

    def set_mode(self, mode):
        self.mode_index = MODES.index(mode)
        self.selection_index = 0
        self.sprite_index = 0
        self.drag_start = None
        self.move_drag = None
        self.resize_drag = None
        self.component_dropdown_open = False

    def adjust_selection(self, amount):
        ids = self.selected_ids()
        if ids:
            self.selection_index = (self.selection_index + amount) % len(ids)

    def mark_dirty(self):
        self.dirty = True
        self.pending_level_id = None

    def sync_room_size_inputs(self):
        world_w, world_h = self.level["world_size"]
        self.room_size_inputs = {"width": str(world_w), "height": str(world_h)}

    def size_field_rects(self):
        y = self.ui_top() + 14
        return {
            "width": pygame.Rect(828, y, 72, 32),
            "height": pygame.Rect(938, y, 72, 32),
        }

    def commit_size_field(self, field):
        raw_value = self.room_size_inputs.get(field, "")
        if not raw_value:
            self.sync_room_size_inputs()
            return
        value = int(raw_value)
        world_w, world_h = self.level["world_size"]
        if field == "width":
            world_w = max(MIN_WORLD_SIZE[0], value)
        else:
            world_h = max(MIN_WORLD_SIZE[1], value)
        new_size = (world_w, world_h)
        if tuple(self.level["world_size"]) != new_size:
            self.push_undo()
            self.level["world_size"] = new_size
            self.selected_object = None
            self.mark_dirty()
            self.clamp_scroll()
        self.sync_room_size_inputs()

    def commit_active_size_field(self):
        if self.active_size_field:
            self.commit_size_field(self.active_size_field)
            self.active_size_field = None
            self.size_field_replace = False

    def digit_from_key_event(self, event):
        unicode_value = getattr(event, "unicode", "")
        if unicode_value.isdigit():
            return unicode_value
        if pygame.K_0 <= event.key <= pygame.K_9:
            return str(event.key - pygame.K_0)
        if pygame.K_KP0 <= event.key <= pygame.K_KP9:
            return str(event.key - pygame.K_KP0)
        return None

    def level_dropdown_rect(self):
        return pygame.Rect(88, 17, 220, 30)

    def level_option_rects(self):
        base = self.level_dropdown_rect()
        level_ids = sorted(self.levels)
        return {
            level_id: pygame.Rect(base.x, base.bottom + (index * base.h), base.w, base.h)
            for index, level_id in enumerate(level_ids)
        }

    def component_dropdown_rect(self):
        return pygame.Rect(24, self.ui_top() + 14, 210, 32)

    def component_option_rects(self):
        base = self.component_dropdown_rect()
        return {
            mode: pygame.Rect(base.x, base.y - ((len(MODES) - index) * base.h), base.w, base.h)
            for index, mode in enumerate(MODES)
        }

    def object_dropdown_rect(self):
        return pygame.Rect(244, self.ui_top() + 14, 200, 32)

    def object_option_rects(self):
        base = self.object_dropdown_rect()
        ids = self.selected_ids()
        return {
            index: pygame.Rect(base.x, base.y - ((len(ids) - index) * base.h), base.w, base.h)
            for index, _ in enumerate(ids)
        }

    def sprite_dropdown_rect(self):
        return pygame.Rect(454, self.ui_top() + 14, 320, 32)

    def sprite_option_rects(self):
        base = self.sprite_dropdown_rect()
        choices = self.sprite_choices()
        return {
            index: pygame.Rect(base.x, base.y - ((len(choices) - index) * base.h), base.w, base.h)
            for index, _ in enumerate(choices)
        }

    def save_button_rect(self):
        return pygame.Rect(WINDOW_SIZE[0] - 120, self.ui_top() + 14, 96, 32)

    def playtest_button_rect(self):
        return pygame.Rect(WINDOW_SIZE[0] - 218, self.ui_top() + 14, 88, 32)

    def undo_button_rect(self):
        return pygame.Rect(1020, self.ui_top() + 14, 70, 32)

    def redo_button_rect(self):
        return pygame.Rect(1100, self.ui_top() + 14, 70, 32)

    def duplicate_button_rect(self):
        return pygame.Rect(322, self.ui_top() + 52, 82, 30)

    def copy_button_rect(self):
        return pygame.Rect(414, self.ui_top() + 52, 58, 30)

    def paste_button_rect(self):
        return pygame.Rect(482, self.ui_top() + 52, 62, 30)

    def collision_toggle_rect(self):
        return pygame.Rect(96, self.ui_top() + 52, 110, 30)

    def validation_toggle_rect(self):
        return pygame.Rect(216, self.ui_top() + 52, 96, 30)

    def reload_levels(self):
        self.levels, self.modules = load_levels()

    def switch_level(self, level_id):
        if level_id == self.level_id:
            self.level_dropdown_open = False
            return
        if self.dirty:
            self.pending_level_id = level_id
            self.level_dropdown_open = False
            self.message = "Unsaved changes. Click Save, then choose again. Press D to discard."
            self.message_timer = 4.0
            return

        self.reload_levels()
        self.level_id = level_id
        self.level = copy.deepcopy(self.levels[level_id])
        self.level_module_path = Path(self.modules[level_id].__file__)
        self.selection_index = 0
        self.drag_start = None
        self.selected_object = None
        self.move_drag = None
        self.resize_drag = None
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.scroll_x = 0
        self.scroll_y = 0
        self.sync_room_size_inputs()
        self.close_dropdowns()
        self.pending_level_id = None
        self.message = f"Loaded {self.level_module_path.name}"
        self.message_timer = 2.5

    def discard_and_switch_pending_level(self):
        if self.pending_level_id:
            target_level_id = self.pending_level_id
            self.dirty = False
            self.switch_level(target_level_id)

    def close_dropdowns(self):
        self.level_dropdown_open = False
        self.component_dropdown_open = False
        self.object_dropdown_open = False
        self.sprite_dropdown_open = False

    def handle_open_dropdown_click(self, pos):
        if self.level_dropdown_open:
            for level_id, rect in self.level_option_rects().items():
                if rect.collidepoint(pos):
                    self.switch_level(level_id)
                    return True
        if self.component_dropdown_open:
            for mode, rect in self.component_option_rects().items():
                if rect.collidepoint(pos):
                    self.set_mode(mode)
                    return True
        if self.object_dropdown_open:
            ids = self.selected_ids()
            for index, rect in self.object_option_rects().items():
                if rect.collidepoint(pos):
                    if self.mode == "select" and self.selected_object:
                        self.push_undo()
                    self.selection_index = index
                    if self.mode != "select":
                        self.sprite_index = 0
                    self.object_dropdown_open = False
                    if self.mode == "select" and self.selected_object:
                        self.apply_current_controls_to_selected()
                    return True
        if self.sprite_dropdown_open:
            choices = self.sprite_choices()
            for index, rect in self.sprite_option_rects().items():
                if rect.collidepoint(pos):
                    if self.mode == "select" and self.selected_object:
                        self.push_undo()
                    self.sprite_index = index
                    self.sprite_dropdown_open = False
                    if self.mode == "select" and self.selected_object:
                        self.apply_current_controls_to_selected()
                    return True

        if self.level_dropdown_open or self.component_dropdown_open or self.object_dropdown_open or self.sprite_dropdown_open:
            self.close_dropdowns()
            return True
        return False

    def handle_ui_click(self, pos):
        if self.handle_open_dropdown_click(pos):
            return True
        if self.level_dropdown_rect().collidepoint(pos):
            self.commit_active_size_field()
            self.close_dropdowns()
            self.level_dropdown_open = True
            return True
        if pos[1] < self.ui_top():
            return False
        if self.component_dropdown_rect().collidepoint(pos):
            self.commit_active_size_field()
            self.close_dropdowns()
            self.component_dropdown_open = True
            return True
        if self.object_dropdown_rect().collidepoint(pos):
            self.commit_active_size_field()
            self.close_dropdowns()
            if self.selected_ids():
                self.object_dropdown_open = True
            return True
        if self.sprite_dropdown_rect().collidepoint(pos):
            self.commit_active_size_field()
            self.sprite_options = self.load_sprite_options()
            self.close_dropdowns()
            self.sprite_dropdown_open = True
            return True
        for field, rect in self.size_field_rects().items():
            if rect.collidepoint(pos):
                if self.active_size_field and self.active_size_field != field:
                    self.commit_size_field(self.active_size_field)
                self.active_size_field = field
                self.size_field_replace = True
                self.close_dropdowns()
                return True
        self.commit_active_size_field()
        if self.undo_button_rect().collidepoint(pos):
            self.undo()
            return True
        if self.redo_button_rect().collidepoint(pos):
            self.redo()
            return True
        if self.duplicate_button_rect().collidepoint(pos):
            self.duplicate_selected()
            return True
        if self.copy_button_rect().collidepoint(pos):
            self.copy_selected()
            return True
        if self.paste_button_rect().collidepoint(pos):
            self.paste_clipboard()
            return True
        if self.collision_toggle_rect().collidepoint(pos):
            self.show_collision_boxes = not self.show_collision_boxes
            return True
        if self.validation_toggle_rect().collidepoint(pos):
            self.validation_panel_open = not self.validation_panel_open
            return True
        if self.playtest_button_rect().collidepoint(pos):
            self.playtest()
            return True
        if self.save_button_rect().collidepoint(pos):
            self.save()
            return True
        return True

    def scrollbar_thumb_rects(self):
        viewport, hbar, vbar = self.scroll_layout()
        world_w, world_h = self.level["world_size"]
        max_x, max_y = self.max_scroll()
        hthumb = None
        vthumb = None
        if hbar:
            thumb_w = max(40, int(hbar.w * viewport.w / world_w))
            thumb_x = hbar.x if max_x == 0 else hbar.x + int((hbar.w - thumb_w) * self.scroll_x / max_x)
            hthumb = pygame.Rect(thumb_x, hbar.y + 2, thumb_w, hbar.h - 4)
        if vbar:
            thumb_h = max(40, int(vbar.h * viewport.h / world_h))
            thumb_y = vbar.y if max_y == 0 else vbar.y + int((vbar.h - thumb_h) * self.scroll_y / max_y)
            vthumb = pygame.Rect(vbar.x + 2, thumb_y, vbar.w - 4, thumb_h)
        return hthumb, vthumb

    def set_scroll_from_bar_position(self, axis, pos):
        _, hbar, vbar = self.scroll_layout()
        hthumb, vthumb = self.scrollbar_thumb_rects()
        max_x, max_y = self.max_scroll()
        if axis == "x" and hbar and hthumb:
            usable = max(1, hbar.w - hthumb.w)
            thumb_x = max(hbar.x, min(pos[0], hbar.right - hthumb.w))
            self.scroll_x = int((thumb_x - hbar.x) * max_x / usable)
        elif axis == "y" and vbar and vthumb:
            usable = max(1, vbar.h - vthumb.h)
            thumb_y = max(vbar.y, min(pos[1], vbar.bottom - vthumb.h))
            self.scroll_y = int((thumb_y - vbar.y) * max_y / usable)
        self.clamp_scroll()

    def handle_scrollbar_down(self, pos):
        _, hbar, vbar = self.scroll_layout()
        hthumb, vthumb = self.scrollbar_thumb_rects()
        if hbar and hbar.collidepoint(pos):
            offset = pos[0] - hthumb.x if hthumb and hthumb.collidepoint(pos) else hthumb.w // 2
            self.scroll_drag = {"axis": "x", "offset": offset}
            self.set_scroll_from_bar_position("x", (pos[0] - offset, pos[1]))
            return True
        if vbar and vbar.collidepoint(pos):
            offset = pos[1] - vthumb.y if vthumb and vthumb.collidepoint(pos) else vthumb.h // 2
            self.scroll_drag = {"axis": "y", "offset": offset}
            self.set_scroll_from_bar_position("y", (pos[0], pos[1] - offset))
            return True
        return False

    def handle_scrollbar_motion(self, pos):
        if not self.scroll_drag:
            return False
        if self.scroll_drag["axis"] == "x":
            self.set_scroll_from_bar_position("x", (pos[0] - self.scroll_drag["offset"], pos[1]))
        else:
            self.set_scroll_from_bar_position("y", (pos[0], pos[1] - self.scroll_drag["offset"]))
        return True

    def object_world_rect(self, ref):
        if not ref:
            return None
        key = ref["key"]
        item = self.get_object(ref)
        if not item:
            return None
        if key in FILE_BY_KEY:
            return pygame.Rect(item["x"], item["y"], item["w"], item["h"])
        if key == "spawns":
            return pygame.Rect(item["x"], item["y"], GRID_SIZE, GRID_SIZE)
        id_key = "item_id" if key == "pickups" else "character_id"
        definitions = self.item_defs if key == "pickups" else self.character_defs
        definition = definitions.get(item[id_key], {})
        width, height = definition.get("size", (GRID_SIZE, GRID_SIZE))
        return pygame.Rect(item["x"], item["y"], width, height)

    def get_object(self, ref):
        if not ref:
            return None
        key = ref["key"]
        if key == "spawns":
            return self.level.get("spawns", {}).get(ref["name"])
        items = self.level.get(key, [])
        index = ref["index"]
        if 0 <= index < len(items):
            return items[index]
        return None

    def object_display_name(self, ref=None):
        ref = ref or self.selected_object
        if not ref:
            return "Nothing selected"
        key = ref["key"]
        if key == "spawns":
            return f"Spawn: {ref['name']}"
        item = self.get_object(ref)
        if key == "pickups" and item:
            return f"Pickup: {item.get('item_id', 'unknown')}"
        if key in {"enemies", "npcs"} and item:
            return f"{MODE_LABELS[key]}: {item.get('character_id', 'unknown')}"
        if key == "exits" and item:
            return f"Exit to: {item.get('target_level', 'unknown')}"
        return MODE_LABELS.get(key, key).title()

    def object_size_for_item(self, key, item):
        if key in FILE_BY_KEY:
            return item.get("w", GRID_SIZE), item.get("h", GRID_SIZE)
        if key == "spawns":
            return GRID_SIZE, GRID_SIZE
        id_key = "item_id" if key == "pickups" else "character_id"
        definitions = self.item_defs if key == "pickups" else self.character_defs
        definition = definitions.get(item.get(id_key), {})
        return definition.get("size", (GRID_SIZE, GRID_SIZE))

    def clamp_item_position(self, key, item):
        width, height = self.object_size_for_item(key, item)
        world_w, world_h = self.level["world_size"]
        item["x"] = max(0, min(item.get("x", 0), max(0, world_w - width)))
        item["y"] = max(0, min(item.get("y", 0), max(0, world_h - height)))

    def unique_spawn_name(self, base_name):
        candidate = f"{base_name}_copy"
        suffix = 2
        while candidate in self.level.get("spawns", {}):
            candidate = f"{base_name}_copy_{suffix}"
            suffix += 1
        return candidate

    def copy_selected(self):
        item = self.get_object(self.selected_object)
        if not item or not self.selected_object:
            self.message = "Select something before copying."
            self.message_timer = 2.0
            return False
        self.clipboard_object = {
            "key": self.selected_object["key"],
            "item": copy.deepcopy(item),
            "name": self.selected_object.get("name"),
        }
        self.message = f"Copied {self.object_display_name()}."
        self.message_timer = 2.0
        return True

    def paste_clipboard(self):
        if not self.clipboard_object:
            self.message = "Nothing has been copied yet."
            self.message_timer = 2.0
            return False
        key = self.clipboard_object["key"]
        item = copy.deepcopy(self.clipboard_object["item"])
        item["x"] = item.get("x", 0) + CLONE_OFFSET
        item["y"] = item.get("y", 0) + CLONE_OFFSET
        self.clamp_item_position(key, item)
        self.push_undo()
        if key == "spawns":
            spawn_name = self.unique_spawn_name(self.clipboard_object.get("name") or "spawn")
            self.level.setdefault("spawns", {})[spawn_name] = item
            self.selected_object = {"key": "spawns", "name": spawn_name}
        else:
            self.level.setdefault(key, []).append(item)
            self.selected_object = {"key": key, "index": len(self.level[key]) - 1}
        self.sync_controls_from_selected()
        self.mark_dirty()
        self.message = f"Pasted {self.object_display_name()}."
        self.message_timer = 2.0
        return True

    def duplicate_selected(self):
        if not self.copy_selected():
            return False
        return self.paste_clipboard()

    def can_resize_selected(self):
        return bool(self.selected_object and self.selected_object["key"] in FILE_BY_KEY)

    def selected_resize_handles(self):
        if not self.can_resize_selected():
            return {}
        rect = self.object_world_rect(self.selected_object)
        if not rect:
            return {}
        screen_rect = self.world_to_screen_rect({"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h})
        half = HANDLE_SIZE // 2
        centers = {
            "nw": screen_rect.topleft,
            "n": (screen_rect.centerx, screen_rect.top),
            "ne": screen_rect.topright,
            "e": (screen_rect.right, screen_rect.centery),
            "se": screen_rect.bottomright,
            "s": (screen_rect.centerx, screen_rect.bottom),
            "sw": screen_rect.bottomleft,
            "w": (screen_rect.left, screen_rect.centery),
        }
        return {
            name: pygame.Rect(center[0] - half, center[1] - half, HANDLE_SIZE, HANDLE_SIZE)
            for name, center in centers.items()
        }

    def resize_handle_at(self, pos):
        for name, rect in self.selected_resize_handles().items():
            if rect.collidepoint(pos):
                return name
        return None

    def resize_selected_to(self, world_pos):
        item = self.get_object(self.selected_object)
        if not item or not self.resize_drag:
            return
        original = self.resize_drag["original"]
        handle = self.resize_drag["handle"]
        world_w, world_h = self.level["world_size"]
        x, y = original["x"], original["y"]
        right = original["x"] + original["w"]
        bottom = original["y"] + original["h"]
        snapped_x, snapped_y = self.snap_world(*world_pos)

        if "w" in handle:
            x = max(0, min(snapped_x, right - GRID_SIZE))
        if "e" in handle:
            right = max(x + GRID_SIZE, min(snapped_x, world_w))
        if "n" in handle:
            y = max(0, min(snapped_y, bottom - GRID_SIZE))
        if "s" in handle:
            bottom = max(y + GRID_SIZE, min(snapped_y, world_h))

        item["x"] = x
        item["y"] = y
        item["w"] = max(GRID_SIZE, right - x)
        item["h"] = max(GRID_SIZE, bottom - y)

    def sync_controls_from_selected(self):
        item = self.get_object(self.selected_object)
        if not item:
            return
        ids = self.selected_ids()
        target_id = None
        key = self.selected_object["key"]
        if key == "exits":
            target_id = item.get("target_level")
        elif key == "pickups":
            target_id = item.get("item_id")
        elif key in {"enemies", "npcs"}:
            target_id = item.get("character_id")
        if target_id in ids:
            self.selection_index = ids.index(target_id)
        choices = self.sprite_choices()
        sprite = item.get("sprite")
        self.sprite_index = choices.index(sprite) if sprite in choices else 0

    def find_object_at(self, world_pos):
        probe = pygame.Rect(world_pos[0], world_pos[1], GRID_SIZE, GRID_SIZE)
        for key in ["npcs", "enemies", "pickups", "spawns", "exits", "win_zones", "checkpoints", "hazards", "solids"]:
            if key == "spawns":
                for spawn_name, spawn in reversed(list(self.level.get("spawns", {}).items())):
                    rect = pygame.Rect(spawn["x"], spawn["y"], GRID_SIZE, GRID_SIZE)
                    if rect.colliderect(probe):
                        return {"key": "spawns", "name": spawn_name}
                continue
            for index in range(len(self.level.get(key, [])) - 1, -1, -1):
                ref = {"key": key, "index": index}
                rect = self.object_world_rect(ref)
                if rect and rect.colliderect(probe):
                    return ref
        return None

    def move_selected_to(self, world_pos):
        item = self.get_object(self.selected_object)
        if not item or not self.move_drag:
            return
        world_w, world_h = self.level["world_size"]
        rect = self.object_world_rect(self.selected_object)
        offset_x, offset_y = self.move_drag["offset"]
        new_x, new_y = self.snap_world(world_pos[0] - offset_x, world_pos[1] - offset_y)
        item["x"] = max(0, min(new_x, max(0, world_w - rect.w)))
        item["y"] = max(0, min(new_y, max(0, world_h - rect.h)))

    def apply_current_controls_to_selected(self):
        item = self.get_object(self.selected_object)
        if not item:
            return
        key = self.selected_object["key"]
        changed = False
        sprite = self.current_sprite()
        if sprite:
            if item.get("sprite") != sprite:
                item["sprite"] = sprite
                changed = True
        elif item.pop("sprite", None) is not None:
            changed = True
        selection = self.current_selection()
        if selection:
            if key == "exits" and item.get("target_level") != selection:
                item["target_level"] = selection
                item["target_spawn"] = "default"
                changed = True
            elif key == "pickups" and item.get("item_id") != selection:
                item["item_id"] = selection
                changed = True
            elif key in {"enemies", "npcs"} and item.get("character_id") != selection:
                item["character_id"] = selection
                changed = True
        if changed:
            self.mark_dirty()

    def add_rect_item(self, start, end):
        x1, y1 = start
        x2, y2 = end
        x = min(x1, x2)
        y = min(y1, y2)
        w = max(GRID_SIZE, abs(x2 - x1) + GRID_SIZE)
        h = max(GRID_SIZE, abs(y2 - y1) + GRID_SIZE)
        target = self.level[FILE_BY_KEY[self.mode]]
        item = {"x": x, "y": y, "w": w, "h": h}
        sprite = self.current_sprite()
        if sprite:
            item["sprite"] = sprite
        if self.mode == "exits":
            item["target_level"] = self.current_selection() or self.level_id
            item["target_spawn"] = "default"
        self.push_undo()
        target.append(item)
        self.mark_dirty()

    def add_point_item(self, world_pos):
        if self.mode == "spawns":
            spawn_name = f"spawn_{len(self.level['spawns'])}"
            spawn = {"x": world_pos[0], "y": world_pos[1]}
            sprite = self.current_sprite()
            if sprite:
                spawn["sprite"] = sprite
            self.push_undo()
            self.level["spawns"][spawn_name] = spawn
        elif self.mode == "pickups":
            if not self.current_selection():
                self.message = "No pickup definitions found."
                self.message_timer = 2.5
                return
            item = {"item_id": self.current_selection(), "x": world_pos[0], "y": world_pos[1]}
            sprite = self.current_sprite()
            if sprite:
                item["sprite"] = sprite
            self.push_undo()
            self.level["pickups"].append(item)
        elif self.mode == "enemies":
            if not self.current_selection():
                self.message = "No enemy definitions found."
                self.message_timer = 2.5
                return
            item = {"character_id": self.current_selection(), "x": world_pos[0], "y": world_pos[1]}
            sprite = self.current_sprite()
            if sprite:
                item["sprite"] = sprite
            self.push_undo()
            self.level["enemies"].append(item)
        elif self.mode == "npcs":
            if not self.current_selection():
                self.message = "No NPC definitions found."
                self.message_timer = 2.5
                return
            item = {"character_id": self.current_selection(), "x": world_pos[0], "y": world_pos[1]}
            sprite = self.current_sprite()
            if sprite:
                item["sprite"] = sprite
            self.push_undo()
            self.level["npcs"].append(item)
        self.mark_dirty()

    def erase_at(self, world_pos):
        probe = pygame.Rect(world_pos[0], world_pos[1], GRID_SIZE, GRID_SIZE)
        for key in ["solids", "hazards", "checkpoints", "win_zones", "exits"]:
            for item in reversed(self.level.get(key, [])):
                rect = pygame.Rect(item["x"], item["y"], item["w"], item["h"])
                if rect.colliderect(probe):
                    self.push_undo()
                    self.level[key].remove(item)
                    self.selected_object = None
                    self.mark_dirty()
                    return
        for key in ["pickups", "enemies", "npcs"]:
            for item in reversed(self.level.get(key, [])):
                rect = pygame.Rect(item["x"], item["y"], GRID_SIZE, GRID_SIZE)
                if rect.colliderect(probe):
                    self.push_undo()
                    self.level[key].remove(item)
                    self.selected_object = None
                    self.mark_dirty()
                    return
        for spawn_name, spawn in list(self.level.get("spawns", {}).items()):
            rect = pygame.Rect(spawn["x"], spawn["y"], GRID_SIZE, GRID_SIZE)
            if rect.colliderect(probe) and spawn_name not in {"default", "from_cavern", "checkpoint"}:
                self.push_undo()
                del self.level["spawns"][spawn_name]
                self.selected_object = None
                self.mark_dirty()
                return

    def save(self):
        self.commit_active_size_field()
        text = (
            "# This file can be edited by hand or generated by level_designer.py.\n"
            "# Students should edit content files like this one, not the engine.\n\n"
            "LEVEL = "
            + pprint.pformat(self.level, sort_dicts=False, width=100)
            + "\n"
        )
        self.level_module_path.write_text(text)
        self.dirty = False
        if self.pending_level_id:
            pending_level_id = self.pending_level_id
            self.pending_level_id = None
            self.switch_level(pending_level_id)
            return
        self.message = f"Saved {self.level_module_path.name}"
        self.message_timer = 2.5

    def playtest(self):
        self.save()
        subprocess.Popen(
            [sys.executable, "run_game.py", "--level", self.level_id, "--spawn", "default"],
            cwd=Path(__file__).resolve().parent,
        )
        self.message = f"Playtesting {self.level_id}"
        self.message_timer = 2.5

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            mods = getattr(event, "mod", pygame.key.get_mods())
            command = bool(mods & (pygame.KMOD_CTRL | pygame.KMOD_META))
            if command and event.key == pygame.K_z:
                if mods & pygame.KMOD_SHIFT:
                    self.redo()
                else:
                    self.undo()
                return
            if command and event.key == pygame.K_y:
                self.redo()
                return
            if command and event.key == pygame.K_c:
                self.copy_selected()
                return
            if command and event.key == pygame.K_v:
                self.paste_clipboard()
                return
            if command and event.key == pygame.K_d:
                self.duplicate_selected()
                return
            if self.active_size_field:
                if event.key == pygame.K_RETURN:
                    self.commit_active_size_field()
                elif event.key == pygame.K_ESCAPE:
                    self.sync_room_size_inputs()
                    self.active_size_field = None
                    self.size_field_replace = False
                elif event.key == pygame.K_BACKSPACE:
                    if self.size_field_replace:
                        self.room_size_inputs[self.active_size_field] = ""
                        self.size_field_replace = False
                    else:
                        self.room_size_inputs[self.active_size_field] = self.room_size_inputs[self.active_size_field][:-1]
                else:
                    digit = self.digit_from_key_event(event)
                    if digit and len(self.room_size_inputs[self.active_size_field]) < 5:
                        if self.size_field_replace:
                            self.room_size_inputs[self.active_size_field] = digit
                            self.size_field_replace = False
                        else:
                            self.room_size_inputs[self.active_size_field] += digit
                return
            if event.key == pygame.K_TAB:
                self.mode_index = (self.mode_index + 1) % len(MODES)
                self.selection_index = 0
            elif event.key == pygame.K_LEFTBRACKET:
                self.selection_index -= 1
            elif event.key == pygame.K_RIGHTBRACKET:
                self.selection_index += 1
            elif event.key == pygame.K_s:
                self.save()
            elif event.key == pygame.K_c:
                self.show_collision_boxes = not self.show_collision_boxes
            elif event.key == pygame.K_v:
                self.validation_panel_open = not self.validation_panel_open
            elif event.key == pygame.K_d:
                self.discard_and_switch_pending_level()
            elif self.mode == "select" and event.key in {pygame.K_DELETE, pygame.K_BACKSPACE} and self.selected_object:
                rect = self.object_world_rect(self.selected_object)
                if rect:
                    self.erase_at((rect.x, rect.y))
            elif self.mode == "select" and self.selected_object and event.key in {pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT}:
                item = self.get_object(self.selected_object)
                rect = self.object_world_rect(self.selected_object)
                if item and rect:
                    dx = dy = 0
                    if event.key == pygame.K_LEFT:
                        dx = -GRID_SIZE
                    elif event.key == pygame.K_RIGHT:
                        dx = GRID_SIZE
                    elif event.key == pygame.K_UP:
                        dy = -GRID_SIZE
                    elif event.key == pygame.K_DOWN:
                        dy = GRID_SIZE
                    self.push_undo()
                    world_w, world_h = self.level["world_size"]
                    item["x"] = max(0, min(item["x"] + dx, max(0, world_w - rect.w)))
                    item["y"] = max(0, min(item["y"] + dy, max(0, world_h - rect.h)))
                    self.mark_dirty()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_ui_click(event.pos):
                return
            if self.handle_minimap_down(event.pos):
                return
            if self.handle_scrollbar_down(event.pos):
                return
            if not self.viewport_rect().collidepoint(event.pos):
                return
            world_pos = self.screen_to_world(event.pos)
            if self.mode == "select":
                handle = self.resize_handle_at(event.pos)
                if handle:
                    item = self.get_object(self.selected_object)
                    if item:
                        self.resize_drag = {
                            "handle": handle,
                            "original": copy.deepcopy(item),
                            "started": False,
                        }
                        self.move_drag = None
                    return
                self.selected_object = self.find_object_at(world_pos)
                if self.selected_object:
                    self.sync_controls_from_selected()
                    rect = self.object_world_rect(self.selected_object)
                    self.move_drag = {
                        "offset": (world_pos[0] - rect.x, world_pos[1] - rect.y),
                        "started": False,
                    }
                    self.resize_drag = None
                else:
                    self.move_drag = None
                    self.resize_drag = None
            elif self.mode in FILE_BY_KEY:
                self.drag_start = world_pos
            elif self.mode in POINT_MODES:
                self.add_point_item(world_pos)
            elif self.mode == "erase":
                self.erase_at(world_pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.minimap_drag:
                self.minimap_drag = False
                return
            if self.scroll_drag:
                self.scroll_drag = None
                return
            if self.drag_start and self.mode in FILE_BY_KEY:
                world_pos = self.screen_to_world(event.pos)
                self.add_rect_item(self.drag_start, world_pos)
            self.drag_start = None
            if self.move_drag:
                if self.move_drag.get("started"):
                    self.mark_dirty()
                self.move_drag = None
            if self.resize_drag:
                if self.resize_drag.get("started"):
                    self.mark_dirty()
                self.resize_drag = None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if not self.viewport_rect().collidepoint(event.pos):
                return
            self.erase_at(self.screen_to_world(event.pos))
        elif event.type == pygame.MOUSEMOTION:
            if self.handle_minimap_motion(event.pos):
                return
            if self.handle_scrollbar_motion(event.pos):
                return
            if self.move_drag and self.selected_object and self.viewport_rect().collidepoint(event.pos):
                if not self.move_drag.get("started"):
                    self.push_undo()
                    self.move_drag["started"] = True
                self.move_selected_to(self.screen_to_world(event.pos))
            if self.resize_drag and self.selected_object and self.viewport_rect().collidepoint(event.pos):
                if not self.resize_drag.get("started"):
                    self.push_undo()
                    self.resize_drag["started"] = True
                self.resize_selected_to(self.screen_to_world(event.pos))
        elif event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            max_x, max_y = self.max_scroll()
            if self.viewport_rect().collidepoint(mouse_pos) and (max_x or max_y):
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.scroll_x -= event.y * GRID_SIZE * 3
                else:
                    self.scroll_y -= event.y * GRID_SIZE * 3
                self.clamp_scroll()
            else:
                self.adjust_selection(event.y)

    def draw_rect_layer(self, key, color, outline=False):
        for item in self.level.get(key, []):
            rect = self.world_to_screen_rect(item)
            if item.get("sprite"):
                self.assets.draw_sprite_or_rect(self.screen, rect, color, item.get("sprite"), border_radius=3)
            elif outline:
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

    def draw_definition_layer(self, key, definitions, id_key):
        for item in self.level.get(key, []):
            definition = definitions.get(item[id_key], {})
            rect = self.world_to_screen_sized_point(item, definition.get("size", (GRID_SIZE, GRID_SIZE)))
            self.assets.draw_sprite_or_rect(
                self.screen,
                rect,
                definition.get("color", MODE_COLORS[key]),
                item.get("sprite") or definition.get("sprite"),
                border_radius=6,
            )
            self.screen.blit(
                self.font.render(item[id_key], True, (245, 245, 245)),
                (rect.x + 16, rect.y - 2),
            )

    def draw_collision_boxes(self):
        layers = ["solids", "hazards", "checkpoints", "win_zones", "exits", "pickups", "enemies", "npcs"]
        for key in layers:
            for index, _ in enumerate(self.level.get(key, [])):
                rect = self.object_world_rect({"key": key, "index": index})
                if not rect:
                    continue
                screen_rect = self.world_to_screen_rect({"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h})
                pygame.draw.rect(self.screen, (245, 245, 245), screen_rect, width=1)
                pygame.draw.rect(self.screen, MODE_COLORS.get(key, (98, 170, 255)), screen_rect.inflate(4, 4), width=1)
        for spawn_name in self.level.get("spawns", {}):
            rect = self.object_world_rect({"key": "spawns", "name": spawn_name})
            if not rect:
                continue
            screen_rect = self.world_to_screen_rect({"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h})
            pygame.draw.rect(self.screen, (245, 245, 245), screen_rect, width=1)
            pygame.draw.rect(self.screen, MODE_COLORS["spawns"], screen_rect.inflate(4, 4), width=1)

    def draw_selected_object(self):
        if not self.selected_object:
            return
        rect = self.object_world_rect(self.selected_object)
        if not rect:
            return
        screen_rect = self.world_to_screen_rect({"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h})
        pygame.draw.rect(self.screen, (245, 245, 245), screen_rect.inflate(8, 8), width=2, border_radius=4)
        pygame.draw.rect(self.screen, MODE_COLORS["select"], screen_rect.inflate(4, 4), width=2, border_radius=4)
        for handle_rect in self.selected_resize_handles().values():
            pygame.draw.rect(self.screen, (245, 245, 245), handle_rect, border_radius=2)
            pygame.draw.rect(self.screen, MODE_COLORS["select"], handle_rect, width=2, border_radius=2)

    def draw_button(self, rect, label, active=False, color=None):
        bg = (42, 51, 70) if active else (24, 31, 44)
        border = color or (92, 105, 132)
        pygame.draw.rect(self.screen, bg, rect, border_radius=5)
        pygame.draw.rect(self.screen, border, rect, width=2 if active else 1, border_radius=5)
        label_surface = self.font.render(label, True, (245, 245, 245))
        self.screen.blit(label_surface, label_surface.get_rect(center=rect.center))

    def draw_sprite_thumbnail(self, rect, sprite_path=None):
        pygame.draw.rect(self.screen, (42, 51, 70), rect, border_radius=3)
        image = self.assets.load_image(sprite_path) if sprite_path else None
        if image:
            thumb = pygame.transform.scale(image, rect.size)
            self.screen.blit(thumb, rect)
        else:
            pygame.draw.rect(self.screen, MODE_COLORS.get(self.mode, (98, 170, 255)), rect.inflate(-8, -8), border_radius=3)
        pygame.draw.rect(self.screen, (98, 170, 255), rect, width=1, border_radius=3)

    def draw_level_dropdown(self):
        rect = self.level_dropdown_rect()
        label = self.level_id
        if self.dirty:
            label += " *"
        self.screen.blit(self.font.render("Level:", True, (210, 218, 232)), (24, rect.y + 7))
        pygame.draw.rect(self.screen, (18, 24, 36), rect, border_radius=5)
        pygame.draw.rect(self.screen, (98, 170, 255), rect, width=2 if self.level_dropdown_open else 1, border_radius=5)
        self.screen.blit(self.font.render(label, True, (245, 245, 245)), (rect.x + 10, rect.y + 7))
        arrow = "^" if self.level_dropdown_open else "v"
        arrow_surface = self.font.render(arrow, True, (245, 245, 245))
        self.screen.blit(arrow_surface, (rect.right - 24, rect.y + 7))

        if self.level_dropdown_open:
            for level_id, option_rect in self.level_option_rects().items():
                active = level_id == self.level_id
                bg = (42, 51, 70) if active else (18, 24, 36)
                pygame.draw.rect(self.screen, bg, option_rect)
                pygame.draw.rect(self.screen, (74, 86, 112), option_rect, width=1)
                self.screen.blit(
                    self.font.render(level_id, True, (245, 245, 245)),
                    (option_rect.x + 10, option_rect.y + 7),
                )

    def draw_header(self):
        pygame.draw.rect(self.screen, (12, 16, 24), self.header_rect())
        self.draw_level_dropdown()
        title = "LevelKit: Platform Level Builder"
        title_surface = self.title_font.render(title, True, (245, 245, 245))
        self.screen.blit(title_surface, (WINDOW_SIZE[0] - title_surface.get_width() - 24, 16))

    def draw_component_dropdown(self):
        rect = self.component_dropdown_rect()
        label = f"Component: {MODE_LABELS[self.mode]}"
        pygame.draw.rect(self.screen, (18, 24, 36), rect, border_radius=5)
        pygame.draw.rect(self.screen, MODE_COLORS.get(self.mode, (98, 170, 255)), rect, width=2 if self.component_dropdown_open else 1, border_radius=5)
        self.screen.blit(self.font.render(label, True, (245, 245, 245)), (rect.x + 10, rect.y + 8))
        arrow = "^" if self.component_dropdown_open else "v"
        self.screen.blit(self.font.render(arrow, True, (245, 245, 245)), (rect.right - 24, rect.y + 8))

        if self.component_dropdown_open:
            for mode, option_rect in self.component_option_rects().items():
                active = mode == self.mode
                pygame.draw.rect(self.screen, (42, 51, 70) if active else (18, 24, 36), option_rect)
                pygame.draw.rect(self.screen, MODE_COLORS.get(mode, (74, 86, 112)), option_rect, width=2 if active else 1)
                self.screen.blit(
                    self.font.render(MODE_LABELS[mode], True, (245, 245, 245)),
                    (option_rect.x + 10, option_rect.y + 8),
                )

    def draw_object_dropdown(self):
        rect = self.object_dropdown_rect()
        selected = self.current_selection()
        label = f"Object: {selected if selected else 'Default'}"
        has_options = bool(self.selected_ids())
        pygame.draw.rect(self.screen, (18, 24, 36), rect, border_radius=5)
        border = (98, 170, 255) if has_options else (74, 86, 112)
        pygame.draw.rect(self.screen, border, rect, width=2 if self.object_dropdown_open else 1, border_radius=5)
        text_color = (245, 245, 245) if has_options else (160, 168, 184)
        self.screen.blit(self.font.render(label, True, text_color), (rect.x + 10, rect.y + 8))
        arrow = "^" if self.object_dropdown_open else "v"
        self.screen.blit(self.font.render(arrow, True, text_color), (rect.right - 24, rect.y + 8))

        if self.object_dropdown_open:
            ids = self.selected_ids()
            for index, option_rect in self.object_option_rects().items():
                active = ids[index] == selected
                pygame.draw.rect(self.screen, (42, 51, 70) if active else (18, 24, 36), option_rect)
                pygame.draw.rect(self.screen, (74, 86, 112), option_rect, width=1)
                self.screen.blit(
                    self.font.render(ids[index], True, (245, 245, 245)),
                    (option_rect.x + 10, option_rect.y + 8),
                )

    def draw_sprite_dropdown(self):
        rect = self.sprite_dropdown_rect()
        label = f"Sprite: {self.current_sprite_label()}"
        pygame.draw.rect(self.screen, (18, 24, 36), rect, border_radius=5)
        pygame.draw.rect(self.screen, (98, 170, 255), rect, width=2 if self.sprite_dropdown_open else 1, border_radius=5)
        text = self.font.render(label, True, (245, 245, 245))
        thumb_rect = pygame.Rect(rect.x + 8, rect.y + 4, 24, 24)
        self.draw_sprite_thumbnail(thumb_rect, self.sprite_preview_path())
        self.screen.blit(text, (rect.x + 40, rect.y + 8))
        arrow = "^" if self.sprite_dropdown_open else "v"
        self.screen.blit(self.font.render(arrow, True, (245, 245, 245)), (rect.right - 24, rect.y + 8))

        if self.sprite_dropdown_open:
            choices = self.sprite_choices()
            for index, option_rect in self.sprite_option_rects().items():
                active = index == self.sprite_index
                pygame.draw.rect(self.screen, (42, 51, 70) if active else (18, 24, 36), option_rect)
                pygame.draw.rect(self.screen, (74, 86, 112), option_rect, width=1)
                option_thumb = pygame.Rect(option_rect.x + 8, option_rect.y + 4, 24, 24)
                self.draw_sprite_thumbnail(option_thumb, self.sprite_preview_path(index))
                self.screen.blit(
                    self.font.render(choices[index], True, (245, 245, 245)),
                    (option_rect.x + 40, option_rect.y + 8),
                )

    def draw_size_fields(self):
        rects = self.size_field_rects()
        label_y = rects["width"].y + 7
        self.screen.blit(self.font.render("W", True, (210, 218, 232)), (rects["width"].x - 26, label_y + 1))
        self.screen.blit(self.font.render("H", True, (210, 218, 232)), (rects["height"].x - 24, label_y + 1))
        for field, rect in rects.items():
            active = field == self.active_size_field
            pygame.draw.rect(self.screen, (18, 24, 36), rect, border_radius=5)
            pygame.draw.rect(self.screen, (98, 170, 255) if active else (74, 86, 112), rect, width=2 if active else 1, border_radius=5)
            value = self.room_size_inputs.get(field, "")
            if active and self.size_field_replace and value:
                text_rect = pygame.Rect(rect.x + 6, rect.y + 4, rect.w - 12, rect.h - 8)
                pygame.draw.rect(self.screen, (42, 91, 150), text_rect, border_radius=3)
            self.screen.blit(self.font.render(value, True, (245, 245, 245)), (rect.x + 10, rect.y + 7))

    def draw_scrollbars(self):
        _, hbar, vbar = self.scroll_layout()
        hthumb, vthumb = self.scrollbar_thumb_rects()
        if hbar:
            pygame.draw.rect(self.screen, (18, 24, 36), hbar)
            pygame.draw.rect(self.screen, (74, 86, 112), hbar, width=1)
            pygame.draw.rect(self.screen, (98, 170, 255), hthumb, border_radius=4)
        if vbar:
            pygame.draw.rect(self.screen, (18, 24, 36), vbar)
            pygame.draw.rect(self.screen, (74, 86, 112), vbar, width=1)
            pygame.draw.rect(self.screen, (98, 170, 255), vthumb, border_radius=4)
        if hbar and vbar:
            corner = pygame.Rect(vbar.x, hbar.y, SCROLLBAR_SIZE, SCROLLBAR_SIZE)
            pygame.draw.rect(self.screen, (12, 16, 24), corner)

    def draw_minimap_rect_layer(self, minimap, key, color, outline=False):
        scale_x, scale_y = self.minimap_scale()
        for item in self.level.get(key, []):
            rect = pygame.Rect(
                minimap.x + int(item["x"] * scale_x),
                minimap.y + int(item["y"] * scale_y),
                max(2, int(item["w"] * scale_x)),
                max(2, int(item["h"] * scale_y)),
            )
            if outline:
                pygame.draw.rect(self.screen, color, rect, width=1)
            else:
                pygame.draw.rect(self.screen, color, rect)

    def draw_minimap_point_layer(self, minimap, key, color):
        scale_x, scale_y = self.minimap_scale()
        for item in self.level.get(key, []):
            rect = pygame.Rect(
                minimap.x + int(item["x"] * scale_x),
                minimap.y + int(item["y"] * scale_y),
                3,
                3,
            )
            pygame.draw.rect(self.screen, color, rect)

    def draw_minimap(self):
        minimap = self.minimap_rect()
        pygame.draw.rect(self.screen, (10, 14, 24), minimap, border_radius=4)
        pygame.draw.rect(self.screen, (98, 170, 255), minimap, width=1, border_radius=4)
        self.draw_minimap_rect_layer(minimap, "solids", MODE_COLORS["solids"])
        self.draw_minimap_rect_layer(minimap, "hazards", MODE_COLORS["hazards"])
        self.draw_minimap_rect_layer(minimap, "checkpoints", MODE_COLORS["checkpoints"])
        self.draw_minimap_rect_layer(minimap, "win_zones", MODE_COLORS["win_zones"], outline=True)
        self.draw_minimap_rect_layer(minimap, "exits", MODE_COLORS["exits"], outline=True)
        self.draw_minimap_point_layer(minimap, "pickups", MODE_COLORS["pickups"])
        self.draw_minimap_point_layer(minimap, "enemies", MODE_COLORS["enemies"])
        self.draw_minimap_point_layer(minimap, "npcs", MODE_COLORS["npcs"])

        for spawn in self.level.get("spawns", {}).values():
            scale_x, scale_y = self.minimap_scale()
            pygame.draw.rect(
                self.screen,
                MODE_COLORS["spawns"],
                (minimap.x + int(spawn["x"] * scale_x), minimap.y + int(spawn["y"] * scale_y), 3, 3),
            )

        viewport = self.viewport_rect()
        scale_x, scale_y = self.minimap_scale()
        view_rect = pygame.Rect(
            minimap.x + int(self.scroll_x * scale_x),
            minimap.y + int(self.scroll_y * scale_y),
            max(8, int(viewport.w * scale_x)),
            max(8, int(viewport.h * scale_y)),
        )
        pygame.draw.rect(self.screen, (245, 245, 245), view_rect, width=2)

    def validation_warnings(self):
        warnings = []
        world_rect = pygame.Rect(0, 0, *self.level["world_size"])
        seen_points = {}
        for key in ["pickups", "enemies", "npcs"]:
            id_key = "item_id" if key == "pickups" else "character_id"
            for item in self.level.get(key, []):
                identity = (key, item.get(id_key), item.get("x"), item.get("y"))
                seen_points.setdefault(identity, 0)
                seen_points[identity] += 1
                ref = {"key": key, "index": self.level[key].index(item)}
                rect = self.object_world_rect(ref)
                if rect and not world_rect.contains(rect):
                    warnings.append(
                        f"{MODE_LABELS[key]} '{item.get(id_key)}' is partly outside the room. Move it inside the white room border."
                    )
        for key, count in seen_points.items():
            if count > 1:
                _, object_id, x, y = key
                warnings.append(f"{count} copies of '{object_id}' are stacked at {x}, {y}. Move or delete the extras.")

        for spawn_name, spawn in self.level.get("spawns", {}).items():
            rect = pygame.Rect(spawn["x"], spawn["y"], GRID_SIZE, GRID_SIZE)
            if not world_rect.contains(rect):
                warnings.append(f"Spawn '{spawn_name}' is partly outside the room. Move it inside the white room border.")
            for hazard in self.level.get("hazards", []):
                if rect.colliderect(pygame.Rect(hazard["x"], hazard["y"], hazard["w"], hazard["h"])):
                    warnings.append(f"Spawn '{spawn_name}' overlaps a hazard. The player may take damage immediately.")

        for index, exit_zone in enumerate(self.level.get("exits", []), start=1):
            target_level = exit_zone.get("target_level")
            target_spawn = exit_zone.get("target_spawn", "default")
            if target_level not in self.levels:
                warnings.append(f"Exit {index} points to missing level '{target_level}'. Choose an existing level for this exit.")
                continue
            if target_spawn not in self.levels[target_level].get("spawns", {}):
                warnings.append(
                    f"Exit {index} points to missing spawn '{target_spawn}' in {target_level}. Add that spawn or pick another one."
                )

        for key in ["solids", "hazards", "checkpoints", "win_zones", "exits"]:
            for item in self.level.get(key, []):
                rect = pygame.Rect(item["x"], item["y"], item["w"], item["h"])
                if not world_rect.contains(rect):
                    warnings.append(
                        f"{MODE_LABELS[key]} rectangle is partly outside the room. Drag or resize it back inside the border."
                    )
        return warnings

    def fit_text(self, text, max_width):
        if self.font.size(text)[0] <= max_width:
            return text
        clipped = text
        while clipped and self.font.size(clipped + "...")[0] > max_width:
            clipped = clipped[:-1]
        return clipped + "..." if clipped else "..."

    def selected_property_lines(self):
        if not self.selected_object:
            return ["Select an object to view its properties."]
        item = self.get_object(self.selected_object)
        rect = self.object_world_rect(self.selected_object)
        if not item or not rect:
            return ["The selected object could not be found."]
        key = self.selected_object["key"]
        lines = [
            self.object_display_name(),
            f"Position: x {item.get('x', 0)}, y {item.get('y', 0)}",
            f"Size: {rect.w} x {rect.h}",
        ]
        if key in FILE_BY_KEY:
            lines.append("Drag to move. Drag handles to resize.")
        else:
            lines.append("Drag to move. Arrow keys nudge by one grid square.")
        if item.get("sprite"):
            lines.append(f"Sprite: {item['sprite']}")
        if key == "exits":
            lines.append(f"Target spawn: {item.get('target_spawn', 'default')}")
        elif key == "spawns":
            lines.append(f"Name: {self.selected_object.get('name', 'spawn')}")
        return lines

    def draw_selected_properties(self):
        if not self.selected_object:
            return
        viewport = self.viewport_rect()
        minimap = self.minimap_rect()
        lines = self.selected_property_lines()
        width = 330
        height = 34 + len(lines) * 22
        x = viewport.right - width - 16
        y = min(max(minimap.bottom + 12, viewport.y + 16), viewport.bottom - height - 16)
        panel = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (10, 14, 24), panel, border_radius=6)
        pygame.draw.rect(self.screen, (98, 170, 255), panel, width=1, border_radius=6)
        for index, line in enumerate(lines):
            color = (245, 245, 245) if index == 0 else (210, 218, 232)
            text = self.fit_text(line, panel.w - 24)
            self.screen.blit(self.font.render(text, True, color), (panel.x + 12, panel.y + 12 + index * 22))

    def draw_validation_panel(self):
        if not self.validation_panel_open:
            return
        warnings = self.validation_warnings()
        viewport = self.viewport_rect()
        panel = pygame.Rect(viewport.x + 16, viewport.bottom - 190, 560, 170)
        pygame.draw.rect(self.screen, (10, 14, 24), panel, border_radius=6)
        pygame.draw.rect(self.screen, (255, 214, 96), panel, width=1, border_radius=6)
        title = "Validation"
        self.screen.blit(self.font.render(title, True, (245, 245, 245)), (panel.x + 12, panel.y + 12))
        if not warnings:
            self.screen.blit(
                self.font.render("No issues found in this level.", True, (110, 220, 150)),
                (panel.x + 12, panel.y + 42),
            )
            return
        for index, warning in enumerate(warnings[:5], start=1):
            line = self.fit_text(f"{index}. {warning}", panel.w - 24)
            self.screen.blit(self.font.render(line, True, (255, 214, 96)), (panel.x + 12, panel.y + 24 + index * 22))
        if len(warnings) > 5:
            extra = f"+{len(warnings) - 5} more issues"
            self.screen.blit(self.font.render(extra, True, (255, 214, 96)), (panel.x + 12, panel.bottom - 28))

    def draw_ui(self):
        ui_top = self.ui_top()
        pygame.draw.rect(self.screen, (12, 16, 24), (0, ui_top, WINDOW_SIZE[0], UI_HEIGHT))

        mouse_pos = pygame.mouse.get_pos()
        world_label = None
        if self.viewport_rect().collidepoint(mouse_pos):
            mouse_world = self.screen_to_world(mouse_pos)
            world_text = f"cursor: {mouse_world[0]}, {mouse_world[1]} | grid: {GRID_SIZE}px"
            world_label = self.font.render(world_text, True, (210, 218, 232))

        self.draw_component_dropdown()
        self.draw_object_dropdown()
        self.draw_sprite_dropdown()
        self.draw_size_fields()
        self.draw_button(self.undo_button_rect(), "Undo", active=bool(self.undo_stack), color=(98, 170, 255))
        self.draw_button(self.redo_button_rect(), "Redo", active=bool(self.redo_stack), color=(98, 170, 255))
        self.draw_button(self.duplicate_button_rect(), "Duplicate", active=bool(self.selected_object), color=(98, 170, 255))
        self.draw_button(self.copy_button_rect(), "Copy", active=bool(self.selected_object), color=(98, 170, 255))
        self.draw_button(self.paste_button_rect(), "Paste", active=bool(self.clipboard_object), color=(98, 170, 255))
        self.draw_button(
            self.collision_toggle_rect(),
            f"Boxes: {'On' if self.show_collision_boxes else 'Off'}",
            active=self.show_collision_boxes,
            color=(255, 214, 96),
        )
        self.draw_button(
            self.validation_toggle_rect(),
            "Issues",
            active=self.validation_panel_open,
            color=(255, 214, 96),
        )
        self.draw_button(self.playtest_button_rect(), "Playtest", active=True, color=(98, 170, 255))
        self.draw_button(self.save_button_rect(), "Save", active=True, color=(110, 220, 150))

        instruction = "Select to move, resize, copy or duplicate. Right click erases."
        self.screen.blit(self.font.render(instruction, True, (210, 218, 232)), (560, ui_top + 58))
        if world_label:
            self.screen.blit(world_label, (WINDOW_SIZE[0] - world_label.get_width() - 24, ui_top + 58))
        if self.message_timer > 0:
            self.screen.blit(
                self.font.render(self.message, True, (110, 220, 150)),
                (WINDOW_SIZE[0] - 240, ui_top + 82),
            )
        else:
            warnings = self.validation_warnings()
            if warnings:
                warning_text = f"Warning: {warnings[0]}"
                if len(warnings) > 1:
                    warning_text += f" (+{len(warnings) - 1} more)"
                warning_surface = self.font.render(warning_text, True, (255, 214, 96))
                self.screen.blit(warning_surface, (24, ui_top + 82))

    def draw(self):
        self.screen.fill(self.level.get("background", (30, 30, 48)))
        self.clamp_scroll()
        viewport = self.viewport_rect()
        pygame.draw.rect(self.screen, self.level.get("background", (30, 30, 48)), viewport)
        pygame.draw.rect(self.screen, (240, 240, 240), viewport, width=2)

        previous_clip = self.screen.get_clip()
        self.screen.set_clip(viewport)
        world_rect = pygame.Rect(viewport.x - self.scroll_x, viewport.y - self.scroll_y, *self.level["world_size"])
        pygame.draw.rect(self.screen, (240, 240, 240), world_rect, width=2)

        start_x = (self.scroll_x // GRID_SIZE) * GRID_SIZE
        end_x = min(self.level["world_size"][0], self.scroll_x + viewport.w + GRID_SIZE)
        for x in range(start_x, end_x + GRID_SIZE, GRID_SIZE):
            sx = int(x - self.scroll_x + viewport.x)
            pygame.draw.line(self.screen, (70, 80, 100), (sx, viewport.y), (sx, viewport.bottom), 1)
        start_y = (self.scroll_y // GRID_SIZE) * GRID_SIZE
        end_y = min(self.level["world_size"][1], self.scroll_y + viewport.h + GRID_SIZE)
        for y in range(start_y, end_y + GRID_SIZE, GRID_SIZE):
            sy = int(y - self.scroll_y + viewport.y)
            pygame.draw.line(self.screen, (70, 80, 100), (viewport.x, sy), (viewport.right, sy), 1)

        self.draw_rect_layer("solids", MODE_COLORS["solids"])
        self.draw_rect_layer("hazards", MODE_COLORS["hazards"])
        self.draw_rect_layer("checkpoints", MODE_COLORS["checkpoints"])
        self.draw_rect_layer("win_zones", MODE_COLORS["win_zones"], outline=True)
        self.draw_rect_layer("exits", MODE_COLORS["exits"], outline=True)

        for spawn_name, spawn in self.level["spawns"].items():
            rect = self.world_to_screen_point(spawn)
            self.assets.draw_sprite_or_rect(
                self.screen,
                rect,
                MODE_COLORS["spawns"],
                spawn.get("sprite"),
                border_radius=6,
            )
            self.screen.blit(self.font.render(spawn_name, True, (245, 245, 245)), (rect.x + 16, rect.y - 2))

        self.draw_definition_layer("pickups", self.item_defs, "item_id")
        self.draw_definition_layer("enemies", self.character_defs, "character_id")
        self.draw_definition_layer("npcs", self.character_defs, "character_id")
        if self.show_collision_boxes:
            self.draw_collision_boxes()
        if self.mode == "select":
            self.draw_selected_object()

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

        self.screen.set_clip(previous_clip)
        self.draw_scrollbars()
        self.draw_minimap()
        self.draw_selected_properties()
        self.draw_validation_panel()
        self.draw_header()
        self.draw_ui()

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
