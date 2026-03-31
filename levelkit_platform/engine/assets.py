import pygame


class AssetLibrary:
    """Small asset helper that falls back to generated surfaces."""

    def __init__(self):
        self.font_small = None
        self.font_medium = None
        self.font_large = None

    def init(self):
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_medium = pygame.font.SysFont(None, 30)
        self.font_large = pygame.font.SysFont(None, 42)

    @staticmethod
    def make_block(size, color):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill(color)
        return surface
