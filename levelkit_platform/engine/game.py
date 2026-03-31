from __future__ import annotations

import pygame

from .assets import AssetLibrary
from .camera import Camera
from .combat import AttackHitbox, Projectile
from .content_loader import load_definitions, load_dialogue, load_game_config, load_levels
from .entities import Actor
from .hud import draw_center_message, draw_dialogue, draw_hud
from .level import build_actor, build_level
from .settings import BACKGROUND_COLOR, FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from .transition import FadeTransition
from .validation import validate_game_content


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("LevelKit Platform")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.assets = AssetLibrary()
        self.assets.init()
        self.config = load_game_config()
        self.character_defs = load_definitions("characters", "CHARACTER")
        self.item_defs = load_definitions("items", "ITEMS")
        self.dialogue = load_dialogue()
        self.level_defs, _ = load_levels()
        validate_game_content(
            self.config,
            self.level_defs,
            self.character_defs,
            self.item_defs,
            self.dialogue,
        )
        self.player_def = self.character_defs[self.config["player_character_id"]]
        self.player = build_actor(self.player_def, {"x": 0, "y": 0})
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.transition = FadeTransition()
        self.projectiles = []
        self.hitboxes = []
        self.inventory = []
        self.current_dialogue = None
        self.current_level = None
        self.current_level_id = None
        self.checkpoint = {
            "level_id": self.config["starting_level"],
            "spawn_id": self.config["starting_spawn"],
        }
        self.status = "playing"
        self.load_level(self.checkpoint["level_id"], self.checkpoint["spawn_id"])

    def load_level(self, level_id, spawn_id="default"):
        self.current_level_id = level_id
        self.current_level = build_level(
            self.level_defs[level_id], self.character_defs, self.item_defs
        )
        spawn = self.current_level.player_spawn[spawn_id]
        self.player.rect.topleft = (spawn["x"], spawn["y"])
        self.player.velocity.update(0, 0)
        self.projectiles.clear()
        self.hitboxes.clear()
        self.current_dialogue = None

    def respawn(self):
        self.player.health = self.player.max_health
        self.status = "playing"
        self.load_level(self.checkpoint["level_id"], self.checkpoint["spawn_id"])

    def _handle_events(self):
        pressed_interact = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                pressed_interact = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.status != "playing":
                self.respawn()
        return True, pressed_interact

    def _move_actor(self, actor: Actor, dt, solids):
        actor.grounded = False
        actor.rect.x += int(actor.velocity.x * dt)
        for solid in solids:
            if actor.rect.colliderect(solid):
                if actor.velocity.x > 0:
                    actor.rect.right = solid.left
                elif actor.velocity.x < 0:
                    actor.rect.left = solid.right
                actor.velocity.x = 0

        actor.rect.y += int(actor.velocity.y * dt)
        for solid in solids:
            if actor.rect.colliderect(solid):
                if actor.velocity.y > 0:
                    actor.rect.bottom = solid.top
                    actor.grounded = True
                elif actor.velocity.y < 0:
                    actor.rect.top = solid.bottom
                actor.velocity.y = 0

    def _update_player(self, dt, keys):
        if self.status != "playing":
            return
        move_axis = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_axis -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_axis += 1
        self.player.velocity.x = move_axis * self.player.speed
        if move_axis:
            self.player.facing = 1 if move_axis > 0 else -1
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.player.grounded:
            self.player.velocity.y = -self.player.jump_power
            self.player.grounded = False

        self.player.velocity.y += self.player.gravity * dt
        self._move_actor(self.player, dt, self.current_level.solids)

        if keys[pygame.K_j] and self.player.melee_cooldown <= 0:
            self.player.melee_cooldown = self.player.attack["melee_cooldown"]
            hitbox_rect = pygame.Rect(0, 0, 38, 28)
            hitbox_rect.midleft = self.player.rect.midright
            if self.player.facing < 0:
                hitbox_rect.midright = self.player.rect.midleft
            self.hitboxes.append(
                AttackHitbox(
                    owner=self.player,
                    rect=hitbox_rect,
                    damage=self.player.attack["melee_damage"],
                    lifetime=0.12,
                    team="player",
                )
            )

        if keys[pygame.K_k] and self.player.shoot_cooldown <= 0:
            self.player.shoot_cooldown = self.player.attack["projectile_cooldown"]
            projectile_rect = pygame.Rect(self.player.rect.centerx, self.player.rect.centery - 6, 18, 12)
            speed = self.player.attack["projectile_speed"] * self.player.facing
            self.projectiles.append(
                Projectile(
                    projectile_rect,
                    (speed, 0),
                    self.player.attack["projectile_damage"],
                    "player",
                    self.player.attack.get("projectile_color", (255, 232, 120)),
                )
            )

    def _update_enemy(self, enemy, dt):
        patrol = enemy.ai.get("patrol_distance", 0)
        if patrol:
            enemy.velocity.x = enemy.speed * enemy.facing
        enemy.velocity.y += enemy.gravity * dt
        old_x = enemy.rect.x
        self._move_actor(enemy, dt, self.current_level.solids)
        if enemy.rect.x == old_x and enemy.velocity.x == 0:
            enemy.facing *= -1
        if patrol:
            start = enemy.ai.setdefault("spawn_x", enemy.rect.x)
            if abs(enemy.rect.x - start) >= patrol:
                enemy.facing *= -1
        if enemy.rect.colliderect(self.player.rect):
            self.player.take_damage(enemy.attack.get("touch_damage", 1))

    def _update_combat(self, dt):
        for hitbox in self.hitboxes:
            hitbox.update(dt)
            for enemy in self.current_level.enemies:
                if enemy.alive and enemy.rect.colliderect(hitbox.rect) and enemy not in hitbox.hit_targets:
                    enemy.take_damage(hitbox.damage)
                    hitbox.hit_targets.add(enemy)
        self.hitboxes = [hitbox for hitbox in self.hitboxes if not hitbox.expired]

        for projectile in self.projectiles:
            projectile.update(dt, self.current_level.solids)
            if projectile.team == "player":
                for enemy in self.current_level.enemies:
                    if enemy.alive and enemy.rect.colliderect(projectile.rect):
                        enemy.take_damage(projectile.damage)
                        projectile.lifetime = 0
            elif self.player.rect.colliderect(projectile.rect):
                self.player.take_damage(projectile.damage)
                projectile.lifetime = 0
        self.projectiles = [projectile for projectile in self.projectiles if not projectile.expired]
        self.current_level.enemies = [enemy for enemy in self.current_level.enemies if enemy.alive]

    def _update_world_state(self, pressed_interact):
        for hazard in self.current_level.hazards:
            if self.player.rect.colliderect(hazard):
                self.player.take_damage(1)

        for checkpoint in self.current_level.checkpoints:
            if self.player.rect.colliderect(checkpoint):
                self.checkpoint = {
                    "level_id": self.current_level_id,
                    "spawn_id": "checkpoint",
                }
                self.current_level.player_spawn["checkpoint"] = {"x": checkpoint.x, "y": checkpoint.y - 48}

        for pickup in list(self.current_level.pickups):
            if self.player.rect.colliderect(pickup.rect):
                if pickup.data.get("inventory", True):
                    self.inventory.append(pickup.item_id)
                if pickup.data.get("effect") == "heal":
                    self.player.health = min(self.player.max_health, self.player.health + pickup.data.get("amount", 1))
                self.current_level.pickups.remove(pickup)

        if self.current_dialogue and pressed_interact:
            self.current_dialogue = None
            return

        for npc in self.current_level.npcs:
            if self.player.rect.colliderect(npc.rect.inflate(24, 12)) and pressed_interact:
                self.current_dialogue = (npc.name, self.dialogue[npc.dialogue_id])

        for win_zone in self.current_level.win_zones:
            if self.player.rect.colliderect(win_zone):
                self.status = "won"

        if self.player.health <= 0 or self.player.rect.top > self.current_level.world_size[1] + 200:
            self.status = "lost"

        if not self.transition.active:
            for exit_zone in self.current_level.exits:
                if self.player.rect.colliderect(exit_zone.rect):
                    self.transition.start((exit_zone.target_level, exit_zone.target_spawn))
                    break

    def update(self, dt, pressed_interact):
        self.player.update_timers(dt)
        keys = pygame.key.get_pressed()
        self._update_player(dt, keys)
        for enemy in self.current_level.enemies:
            enemy.update_timers(dt)
            self._update_enemy(enemy, dt)
        self._update_combat(dt)
        self._update_world_state(pressed_interact)
        target = self.transition.update(dt)
        if target:
            self.load_level(*target)
        self.camera.update(self.player.rect, *self.current_level.world_size)

    def draw_level(self):
        self.screen.fill(self.current_level.background or BACKGROUND_COLOR)
        for solid in self.current_level.solids:
            pygame.draw.rect(self.screen, (78, 94, 124), self.camera.apply(solid))
        for hazard in self.current_level.hazards:
            pygame.draw.rect(self.screen, (180, 42, 42), self.camera.apply(hazard))
        for checkpoint in self.current_level.checkpoints:
            pygame.draw.rect(self.screen, (100, 220, 140), self.camera.apply(checkpoint), border_radius=4)
        for win_zone in self.current_level.win_zones:
            pygame.draw.rect(self.screen, (255, 206, 84), self.camera.apply(win_zone), width=3)
        for pickup in self.current_level.pickups:
            pygame.draw.rect(self.screen, pickup.color, self.camera.apply(pickup.rect), border_radius=6)
        for npc in self.current_level.npcs:
            pygame.draw.rect(self.screen, npc.color, self.camera.apply(npc.rect), border_radius=8)
        for enemy in self.current_level.enemies:
            pygame.draw.rect(self.screen, enemy.color, self.camera.apply(enemy.rect), border_radius=8)
        pygame.draw.rect(self.screen, self.player.color, self.camera.apply(self.player.rect), border_radius=8)
        for projectile in self.projectiles:
            pygame.draw.rect(self.screen, projectile.color, self.camera.apply(projectile.rect), border_radius=4)
        for hitbox in self.hitboxes:
            pygame.draw.rect(self.screen, (255, 255, 255), self.camera.apply(hitbox.rect), width=1)

        draw_hud(self.screen, self.assets, self.player, self.inventory, self.current_level.name)
        if self.current_dialogue:
            draw_dialogue(self.screen, self.assets, *self.current_dialogue)
        if self.status == "won":
            draw_center_message(self.screen, self.assets, "You win! Press R to restart.")
        elif self.status == "lost":
            draw_center_message(self.screen, self.assets, "You were defeated. Press R.")
        self.transition.draw(self.screen)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running, pressed_interact = self._handle_events()
            self.update(dt, pressed_interact)
            self.draw_level()
            pygame.display.flip()
        pygame.quit()


def main():
    Game().run()
