from __future__ import annotations

import pygame

from .assets import AssetLibrary
from .camera import Camera
from .combat import AttackHitbox, Projectile
from .content_loader import load_content_module, load_definitions, load_dialogue, load_event_hooks, load_game_config, load_levels
from .entities import Actor
from .hud import draw_center_message, draw_dialogue, draw_hud
from .input import KeyboardInput, MouseInput
from .level import build_actor, build_level
from .settings import BACKGROUND_COLOR, FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from .transition import FadeTransition
from .validation import validate_game_content


class Game:
    def __init__(self, starting_level=None, starting_spawn=None):
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
        self.event_hooks = load_event_hooks()
        self.player_controls = load_content_module("player_controls")
        self.collision_rules = load_content_module("collision_rules")
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
        self.show_help = False
        self.show_debug_stats = False
        self.show_collision_boxes = False
        self.show_object_ids = False
        self.checkpoint = {
            "level_id": starting_level or self.config["starting_level"],
            "spawn_id": starting_spawn or self.config["starting_spawn"],
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
        self._run_enter_level_hooks(level_id)

    def say(self, text, speaker="LevelKit"):
        self.current_dialogue = (speaker, text)

    def _run_enter_level_hooks(self, level_id):
        for hook in self.event_hooks.get("enter_level", []):
            if hook.get("level_id") != level_id:
                continue
            if hook.get("say"):
                self.say(hook["say"])
            if hook.get("function"):
                hook["function"](self, level_id)

    def _run_pickup_hooks(self, pickup):
        for hook in self.event_hooks.get("pickup", []):
            if hook.get("item_id") != pickup.item_id:
                continue
            if hook.get("heal"):
                self.player.health = min(self.player.max_health, self.player.health + hook["heal"])
            if hook.get("give_item"):
                self.inventory.append(hook["give_item"])
            if hook.get("say"):
                self.say(hook["say"])
            if hook.get("function"):
                hook["function"](self, pickup)

    def damage_player(self, amount):
        self.player.take_damage(amount)

    def set_checkpoint(self, checkpoint_rect):
        self.checkpoint = {
            "level_id": self.current_level_id,
            "spawn_id": "checkpoint",
        }
        self.current_level.player_spawn["checkpoint"] = {
            "x": checkpoint_rect.x,
            "y": checkpoint_rect.y - self.player.rect.h,
        }

    def collect_pickup(self, pickup):
        if pickup.data.get("inventory", True):
            self.inventory.append(pickup.item_id)
        if pickup.data.get("effect") == "heal":
            self.player.health = min(
                self.player.max_health,
                self.player.health + pickup.data.get("amount", 1),
            )
        self._run_pickup_hooks(pickup)
        if pickup in self.current_level.pickups:
            self.current_level.pickups.remove(pickup)

    def win(self):
        self.status = "won"

    def go_to(self, level_id, spawn_id="default"):
        if not self.transition.active:
            self.transition.start((level_id, spawn_id))

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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                self.show_help = not self.show_help
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                self.show_debug_stats = not self.show_debug_stats
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                self.show_collision_boxes = not self.show_collision_boxes
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                self.show_object_ids = not self.show_object_ids
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
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

    def _update_player(self, dt, keyboard, mouse):
        if self.status != "playing":
            return
        actions = self.player_controls.control_player(self.player, keyboard, mouse, dt) or {}

        self.player.velocity.y += self.player.gravity * dt
        self._move_actor(self.player, dt, self.current_level.solids)
        if not self.player.grounded:
            self.player.state.set("jump" if self.player.velocity.y < 0 else "fall")
        elif abs(self.player.velocity.x) > 0:
            self.player.state.set("walk")
        else:
            self.player.state.set("idle")

        if actions.get("melee") and self.player.melee_cooldown <= 0:
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

        if actions.get("shoot") and self.player.shoot_cooldown <= 0:
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
        if not enemy.grounded:
            enemy.state.set("jump" if enemy.velocity.y < 0 else "fall")
        elif abs(enemy.velocity.x) > 0:
            enemy.state.set("walk")
        else:
            enemy.state.set("idle")
        if enemy.rect.colliderect(self.player.rect):
            self.player.take_damage(enemy.attack.get("touch_damage", 1))

    def _update_actor_animation(self, actor, dt):
        animation = actor.animations.get(actor.state.state) if actor.animations else None
        if animation:
            actor.state.update(
                dt,
                frame_time=animation.get("frame_time", 0.12),
                frame_count=animation.get("frames", 1),
            )

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
                self.collision_rules.player_hits_hazard(self, self.player, hazard)

        for checkpoint in self.current_level.checkpoints:
            if self.player.rect.colliderect(checkpoint):
                self.collision_rules.player_reaches_checkpoint(self, self.player, checkpoint)

        for pickup in list(self.current_level.pickups):
            if self.player.rect.colliderect(pickup.rect):
                self.collision_rules.player_collects_pickup(self, self.player, pickup)

        if self.current_dialogue and pressed_interact:
            self.current_dialogue = None
            return

        for npc in self.current_level.npcs:
            if self.player.rect.colliderect(npc.rect.inflate(24, 12)) and pressed_interact:
                self.collision_rules.player_talks_to_npc(self, self.player, npc)

        for win_zone in self.current_level.win_zones:
            if self.player.rect.colliderect(win_zone):
                self.collision_rules.player_reaches_win_zone(self, self.player, win_zone)

        if self.player.health <= 0 or self.player.rect.top > self.current_level.world_size[1] + 200:
            self.status = "lost"

        if not self.transition.active:
            for exit_zone in self.current_level.exits:
                if self.player.rect.colliderect(exit_zone.rect):
                    self.collision_rules.player_hits_exit(self, self.player, exit_zone)
                    break

    def update(self, dt, pressed_interact):
        self.player.update_timers(dt)
        keyboard = KeyboardInput(pygame.key.get_pressed())
        mouse = MouseInput(pygame.mouse.get_pressed(3), pygame.mouse.get_pos())
        self._update_player(dt, keyboard, mouse)
        self._update_actor_animation(self.player, dt)
        for enemy in self.current_level.enemies:
            enemy.update_timers(dt)
            self._update_enemy(enemy, dt)
            self._update_actor_animation(enemy, dt)
        for npc in self.current_level.npcs:
            npc.state.set("idle")
            self._update_actor_animation(npc, dt)
        self._update_combat(dt)
        self._update_world_state(pressed_interact)
        target = self.transition.update(dt)
        if target:
            self.load_level(*target)
        self.camera.update(self.player.rect, *self.current_level.world_size)

    def _draw_debug_panel(self, lines, x=12, y=104, width=360):
        if not lines:
            return
        height = 18 + len(lines) * 18
        panel = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (10, 14, 24), panel, border_radius=8)
        pygame.draw.rect(self.screen, (98, 170, 255), panel, width=1, border_radius=8)
        for index, line in enumerate(lines):
            surface = self.assets.font_small.render(line, True, (245, 245, 245))
            self.screen.blit(surface, (panel.x + 10, panel.y + 9 + index * 18))

    def _draw_collision_boxes(self):
        for rect in self.current_level.solids:
            pygame.draw.rect(self.screen, (190, 205, 230), self.camera.apply(rect), width=1)
        for rect in self.current_level.hazards:
            pygame.draw.rect(self.screen, (255, 90, 90), self.camera.apply(rect), width=2)
        for rect in self.current_level.checkpoints:
            pygame.draw.rect(self.screen, (110, 220, 150), self.camera.apply(rect), width=2)
        for exit_zone in self.current_level.exits:
            pygame.draw.rect(self.screen, (98, 170, 255), self.camera.apply(exit_zone.rect), width=2)
        for rect in self.current_level.win_zones:
            pygame.draw.rect(self.screen, (255, 214, 96), self.camera.apply(rect), width=2)
        for pickup in self.current_level.pickups:
            pygame.draw.rect(self.screen, (255, 150, 210), self.camera.apply(pickup.rect), width=1)
        for npc in self.current_level.npcs:
            pygame.draw.rect(self.screen, (230, 210, 140), self.camera.apply(npc.rect), width=1)
        for enemy in self.current_level.enemies:
            pygame.draw.rect(self.screen, (255, 120, 120), self.camera.apply(enemy.rect), width=1)
        pygame.draw.rect(self.screen, (255, 255, 255), self.camera.apply(self.player.rect), width=2)

    def _draw_object_ids(self):
        labels = []
        for pickup in self.current_level.pickups:
            labels.append((pickup.item_id, pickup.rect))
        for enemy in self.current_level.enemies:
            labels.append((enemy.actor_id, enemy.rect))
        for npc in self.current_level.npcs:
            labels.append((npc.npc_id, npc.rect))
        for index, exit_zone in enumerate(self.current_level.exits, start=1):
            labels.append((f"exit_{index}: {exit_zone.target_level}", exit_zone.rect))
        for text, rect in labels:
            screen_rect = self.camera.apply(rect)
            surface = self.assets.font_small.render(text, True, (245, 245, 245))
            self.screen.blit(surface, (screen_rect.x, max(0, screen_rect.y - 16)))

    def draw_debug(self):
        if self.show_collision_boxes:
            self._draw_collision_boxes()
        if self.show_object_ids:
            self._draw_object_ids()
        if self.show_debug_stats:
            self._draw_debug_panel(
                [
                    f"Level: {self.current_level_id}",
                    f"Player: x {self.player.rect.x}, y {self.player.rect.y}",
                    f"Velocity: {int(self.player.velocity.x)}, {int(self.player.velocity.y)}",
                    f"Grounded: {self.player.grounded}",
                    f"Status: {self.status}",
                ]
            )
        if self.show_help:
            self._draw_debug_panel(
                [
                    "F1 help on/off",
                    "F2 player stats on/off",
                    "F3 collision boxes on/off",
                    "F4 object ids on/off",
                    "F5 restart from checkpoint",
                ],
                x=self.screen.get_width() - 340,
                y=104,
                width=328,
            )

    def draw_level(self):
        self.screen.fill(self.current_level.background or BACKGROUND_COLOR)
        for solid, sprite in zip(self.current_level.solids, self.current_level.solid_sprites):
            self.assets.draw_sprite_or_rect(self.screen, self.camera.apply(solid), (78, 94, 124), sprite)
        for hazard, sprite in zip(self.current_level.hazards, self.current_level.hazard_sprites):
            self.assets.draw_sprite_or_rect(self.screen, self.camera.apply(hazard), (180, 42, 42), sprite)
        for checkpoint, sprite in zip(self.current_level.checkpoints, self.current_level.checkpoint_sprites):
            self.assets.draw_sprite_or_rect(
                self.screen,
                self.camera.apply(checkpoint),
                (100, 220, 140),
                sprite,
                border_radius=4,
            )
        for exit_zone in self.current_level.exits:
            if exit_zone.sprite:
                self.assets.draw_sprite_or_rect(
                    self.screen,
                    self.camera.apply(exit_zone.rect),
                    (98, 170, 255),
                    exit_zone.sprite,
                )
        for win_zone, sprite in zip(self.current_level.win_zones, self.current_level.win_zone_sprites):
            rect = self.camera.apply(win_zone)
            if sprite:
                self.assets.draw_sprite_or_rect(self.screen, rect, (255, 206, 84), sprite)
            else:
                pygame.draw.rect(self.screen, (255, 206, 84), rect, width=3)
        for pickup in self.current_level.pickups:
            self.assets.draw_sprite_or_rect(
                self.screen,
                self.camera.apply(pickup.rect),
                pickup.color,
                pickup.sprite,
                border_radius=6,
            )
        for npc in self.current_level.npcs:
            self.assets.draw_actor(self.screen, npc, self.camera.apply(npc.rect))
        for enemy in self.current_level.enemies:
            self.assets.draw_actor(self.screen, enemy, self.camera.apply(enemy.rect))
        self.assets.draw_actor(self.screen, self.player, self.camera.apply(self.player.rect))
        for projectile in self.projectiles:
            pygame.draw.rect(self.screen, projectile.color, self.camera.apply(projectile.rect), border_radius=4)
        for hitbox in self.hitboxes:
            pygame.draw.rect(self.screen, (255, 255, 255), self.camera.apply(hitbox.rect), width=1)

        self.draw_debug()
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


def main(starting_level=None, starting_spawn=None):
    Game(starting_level=starting_level, starting_spawn=starting_spawn).run()
