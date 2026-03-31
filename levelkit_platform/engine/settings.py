from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CONTENT_PACKAGE = "levelkit_platform.content"

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60
DEFAULT_TILE_SIZE = 48

BACKGROUND_COLOR = (18, 24, 38)
TEXT_COLOR = (245, 245, 245)
UI_PANEL_COLOR = (10, 14, 24)
UI_BORDER_COLOR = (100, 132, 180)

PLAYER_CONTROLS = {
    "left": "a",
    "right": "d",
    "jump": "space",
    "melee": "j",
    "shoot": "k",
    "interact": "e",
}
