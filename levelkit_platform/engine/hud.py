import pygame

from .settings import TEXT_COLOR, UI_BORDER_COLOR, UI_PANEL_COLOR


def draw_hud(screen, assets, player, inventory, level_name):
    panel = pygame.Rect(12, 12, 280, 78)
    pygame.draw.rect(screen, UI_PANEL_COLOR, panel, border_radius=10)
    pygame.draw.rect(screen, UI_BORDER_COLOR, panel, width=2, border_radius=10)
    hp_text = assets.font_medium.render(
        f"HP: {player.health}/{player.max_health}", True, TEXT_COLOR
    )
    room_text = assets.font_small.render(level_name, True, TEXT_COLOR)
    inventory_text = assets.font_small.render(
        f"Items: {', '.join(inventory) if inventory else 'none'}", True, TEXT_COLOR
    )
    screen.blit(hp_text, (24, 22))
    screen.blit(room_text, (24, 50))
    screen.blit(inventory_text, (24, 68))


def draw_dialogue(screen, assets, speaker, text):
    box = pygame.Rect(60, screen.get_height() - 150, screen.get_width() - 120, 100)
    pygame.draw.rect(screen, UI_PANEL_COLOR, box, border_radius=12)
    pygame.draw.rect(screen, UI_BORDER_COLOR, box, width=2, border_radius=12)
    name_surface = assets.font_medium.render(speaker, True, TEXT_COLOR)
    text_surface = assets.font_small.render(text, True, TEXT_COLOR)
    screen.blit(name_surface, (box.x + 16, box.y + 12))
    screen.blit(text_surface, (box.x + 16, box.y + 50))


def draw_center_message(screen, assets, message):
    surface = assets.font_large.render(message, True, TEXT_COLOR)
    rect = surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(surface, rect)
