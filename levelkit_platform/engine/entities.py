from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from .animation import AnimationState


@dataclass
class Actor:
    actor_id: str
    role: str
    rect: pygame.Rect
    color: tuple[int, int, int]
    max_health: int
    speed: float
    gravity: float
    jump_power: float
    facing: int = 1
    velocity: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    health: int = 0
    grounded: bool = False
    invulnerable_timer: float = 0.0
    melee_cooldown: float = 0.0
    shoot_cooldown: float = 0.0
    attack: dict = field(default_factory=dict)
    dialogue_id: str | None = None
    ai: dict = field(default_factory=dict)
    sprite: str | None = None
    animations: dict = field(default_factory=dict)
    state: AnimationState = field(default_factory=AnimationState)

    def __post_init__(self):
        if not self.health:
            self.health = self.max_health

    def update_timers(self, dt):
        self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        self.melee_cooldown = max(0.0, self.melee_cooldown - dt)
        self.shoot_cooldown = max(0.0, self.shoot_cooldown - dt)

    @property
    def alive(self):
        return self.health > 0

    def take_damage(self, amount):
        if self.invulnerable_timer > 0 or not self.alive:
            return False
        self.health = max(0, self.health - amount)
        self.invulnerable_timer = 0.5
        return True


@dataclass
class Pickup:
    item_id: str
    rect: pygame.Rect
    color: tuple[int, int, int]
    data: dict
    sprite: str | None = None


@dataclass
class NPC:
    npc_id: str
    rect: pygame.Rect
    color: tuple[int, int, int]
    dialogue_id: str
    name: str
    sprite: str | None = None
    animations: dict = field(default_factory=dict)
    facing: int = 1
    state: AnimationState = field(default_factory=AnimationState)
