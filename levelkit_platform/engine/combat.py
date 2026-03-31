import pygame


class AttackHitbox:
    def __init__(self, owner, rect, damage, lifetime, team):
        self.owner = owner
        self.rect = rect
        self.damage = damage
        self.lifetime = lifetime
        self.team = team
        self.hit_targets = set()

    def update(self, dt):
        self.lifetime -= dt

    @property
    def expired(self):
        return self.lifetime <= 0


class Projectile:
    def __init__(self, rect, velocity, damage, team, color, lifetime=1.4):
        self.rect = pygame.Rect(rect)
        self.velocity = pygame.Vector2(velocity)
        self.damage = damage
        self.team = team
        self.color = color
        self.lifetime = lifetime

    def update(self, dt, solids):
        self.lifetime -= dt
        self.rect.x += int(self.velocity.x * dt)
        for solid in solids:
            if self.rect.colliderect(solid):
                self.lifetime = 0
                return
        self.rect.y += int(self.velocity.y * dt)
        for solid in solids:
            if self.rect.colliderect(solid):
                self.lifetime = 0
                return

    @property
    def expired(self):
        return self.lifetime <= 0
