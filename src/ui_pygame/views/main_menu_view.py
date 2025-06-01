# views/main_menu_view.py
"""
Handles drawing the Main Menu view.
"""
import pygame
from typing import List

from ..ui_theme import (
    FONT_LARGE,
    FONT_MEDIUM,
    YALE_BLUE,
    PLATINUM,
    GOLDEN_YELLOW,
    SILVER_LAKE_BLUE,
    OXFORD_BLUE,
    draw_text,
)
from ..ui_components import Button

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


def draw_main_menu(surface: pygame.Surface, buttons: List[Button]):
    """
    Draws the main menu with modern professional styling.
    """
    # Clear background with gradient effect
    surface.fill((5, 15, 30))  # Dark blue background

    # Draw main container with border
    main_container = pygame.Rect(20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40)
    pygame.draw.rect(surface, (15, 25, 45), main_container)
    pygame.draw.rect(surface, YALE_BLUE, main_container, 3)

    # Title section with background
    title_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, 80)
    pygame.draw.rect(surface, (10, 20, 40), title_rect)
    pygame.draw.rect(surface, SILVER_LAKE_BLUE, title_rect, 2)

    # Game title with subtitle
    draw_text(
        surface,
        "PROJECT NARCO-SYNDICATE",
        SCREEN_WIDTH // 2,
        65,
        font=FONT_LARGE,
        color=GOLDEN_YELLOW,
        center_aligned=True,
    )
    draw_text(
        surface,
        "Drug Empire Simulation",
        SCREEN_WIDTH // 2,
        95,
        font=FONT_MEDIUM,
        color=PLATINUM,
        center_aligned=True,
    )

    # Menu container
    menu_rect = pygame.Rect(40, 140, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 180)
    pygame.draw.rect(surface, (8, 18, 35), menu_rect)
    pygame.draw.rect(surface, YALE_BLUE, menu_rect, 1)

    # Menu header
    header_rect = pygame.Rect(50, 150, SCREEN_WIDTH - 100, 35)
    pygame.draw.rect(surface, OXFORD_BLUE, header_rect)
    pygame.draw.rect(surface, YALE_BLUE, header_rect, 1)
    draw_text(
        surface,
        "MAIN MENU",
        SCREEN_WIDTH // 2,
        167,
        font=FONT_MEDIUM,
        color=PLATINUM,
        center_aligned=True,
    )

    # Draw buttons
    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.draw(surface, mouse_pos)
