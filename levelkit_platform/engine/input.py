import pygame


KEY_NAMES = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "space": pygame.K_SPACE,
    "enter": pygame.K_RETURN,
    "escape": pygame.K_ESCAPE,
    "shift": (pygame.K_LSHIFT, pygame.K_RSHIFT),
    "ctrl": (pygame.K_LCTRL, pygame.K_RCTRL),
    "cmd": (pygame.K_LMETA, pygame.K_RMETA),
    "a": pygame.K_a,
    "d": pygame.K_d,
    "w": pygame.K_w,
    "s": pygame.K_s,
    "j": pygame.K_j,
    "k": pygame.K_k,
    "e": pygame.K_e,
    "r": pygame.K_r,
}


class KeyboardInput:
    def __init__(self, pressed_keys):
        self._pressed_keys = pressed_keys

    def pressed(self, key_name):
        key = KEY_NAMES.get(key_name)
        if key is None:
            raise KeyError(f"Unknown key name '{key_name}'. Check docs/08_program_player_controls.md.")
        if isinstance(key, tuple):
            return any(self._pressed_keys[item] for item in key)
        return self._pressed_keys[key]

    def __getattr__(self, key_name):
        return self.pressed(key_name)


class MouseInput:
    def __init__(self, pressed_buttons, position):
        self.left = bool(pressed_buttons[0])
        self.middle = bool(pressed_buttons[1])
        self.right = bool(pressed_buttons[2])
        self.x, self.y = position
        self.position = position
