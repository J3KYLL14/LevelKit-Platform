from pathlib import Path

import pygame

from .settings import ROOT_DIR


ASSET_DIR = ROOT_DIR / "levelkit_platform" / "content" / "assets"


class AssetLibrary:
    """Small asset helper that falls back to generated surfaces."""

    def __init__(self):
        self.font_small = None
        self.font_medium = None
        self.font_large = None
        self._image_cache = {}

    def init(self):
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_medium = pygame.font.SysFont(None, 30)
        self.font_large = pygame.font.SysFont(None, 42)

    @staticmethod
    def make_block(size, color):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill(color)
        return surface

    def load_image(self, asset_path):
        if not asset_path:
            return None
        if asset_path in self._image_cache:
            return self._image_cache[asset_path]

        path = Path(asset_path)
        if not path.is_absolute():
            path = ASSET_DIR / path
        if not path.exists():
            self._image_cache[asset_path] = None
            return None

        try:
            image = pygame.image.load(str(path))
            if pygame.display.get_surface():
                image = image.convert_alpha()
        except pygame.error:
            image = None
        self._image_cache[asset_path] = image
        return image

    def draw_sprite_or_rect(self, surface, rect, color, sprite_path=None, flip_x=False, border_radius=0):
        image = self.load_image(sprite_path)
        if image:
            if image.get_size() != rect.size:
                image = pygame.transform.scale(image, rect.size)
            if flip_x:
                image = pygame.transform.flip(image, True, False)
            surface.blit(image, rect)
        else:
            pygame.draw.rect(surface, color, rect, border_radius=border_radius)

    def draw_actor(self, surface, actor, rect):
        animation = actor.animations.get(actor.state.state) if actor.animations else None
        if animation:
            sprite_path = animation.get("sprite") or actor.sprite
            image = self.load_image(sprite_path)
            frame_count = max(1, int(animation.get("frames", 1)))
            if image:
                frame_w = max(1, image.get_width() // frame_count)
                frame_h = image.get_height()
                frame_index = actor.state.frame % frame_count
                frame = image.subsurface(pygame.Rect(frame_index * frame_w, 0, frame_w, frame_h))
                if frame.get_size() != rect.size:
                    frame = pygame.transform.scale(frame, rect.size)
                if actor.facing < 0:
                    frame = pygame.transform.flip(frame, True, False)
                surface.blit(frame, rect)
                return
        self.draw_sprite_or_rect(
            surface,
            rect,
            actor.color,
            actor.sprite,
            flip_x=actor.facing < 0,
            border_radius=8,
        )
