import pygame


class Camera:
    def __init__(self, width, height):
        self.rect = pygame.Rect(0, 0, width, height)

    def update(self, target_rect, level_width, level_height):
        self.rect.centerx = target_rect.centerx
        self.rect.centery = target_rect.centery
        self.rect.clamp_ip(pygame.Rect(0, 0, level_width, level_height))

    def apply(self, rect):
        return rect.move(-self.rect.x, -self.rect.y)
