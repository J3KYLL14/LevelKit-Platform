import pygame


class FadeTransition:
    def __init__(self, duration=0.6):
        self.duration = duration
        self.timer = 0.0
        self.active = False
        self.midpoint_triggered = False
        self.pending_target = None

    def start(self, target):
        self.timer = 0.0
        self.active = True
        self.midpoint_triggered = False
        self.pending_target = target

    def update(self, dt):
        if not self.active:
            return None
        self.timer += dt
        progress = self.timer / self.duration
        if progress >= 0.5 and not self.midpoint_triggered:
            self.midpoint_triggered = True
            return self.pending_target
        if progress >= 1.0:
            self.active = False
            self.pending_target = None
        return None

    def draw(self, screen):
        if not self.active:
            return
        progress = self.timer / self.duration
        alpha = int(255 * (1 - abs(1 - (2 * progress))))
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, max(0, min(255, alpha))))
        screen.blit(overlay, (0, 0))
