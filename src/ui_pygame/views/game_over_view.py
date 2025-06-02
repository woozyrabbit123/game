# views/game_over_view.py
"""
Handles drawing the Game Over screen.
"""
from typing import List # Optional removed

import pygame

from ..ui_components import Button
from ..ui_theme import ( # Alphabetized, YALE_BLUE removed
    FONT_LARGE_BOLD,
    FONT_XLARGE,
    IMPERIAL_RED,
    OXFORD_BLUE,
    PLATINUM,
    RICH_BLACK,
    draw_panel,
    draw_text,
)

SCREEN_WIDTH = 1024  # Consider shared constants
SCREEN_HEIGHT = 768


def draw_game_over_view(surface: pygame.Surface, message: str, buttons: List[Button]):
    # Draw a semi-transparent overlay over the whole screen
    overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay_color = (*RICH_BLACK, 220)  # Darker, more opaque
    overlay_surface.fill(overlay_color)
    surface.blit(overlay_surface, (0, 0))

    # Define popup box dimensions
    popup_width = SCREEN_WIDTH * 0.7
    popup_height = SCREEN_HEIGHT * 0.5
    popup_x = (SCREEN_WIDTH - popup_width) / 2
    popup_y = (SCREEN_HEIGHT - popup_height) / 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    # Draw popup box
    draw_panel(
        surface, popup_rect, OXFORD_BLUE, IMPERIAL_RED, 3
    )  # Use IMPERIAL_RED for border

    # Display Game Over Title
    title_y = popup_y + 40
    title_text = "GAME OVER"
    title_color = IMPERIAL_RED
    if message.startswith("YOU WON:"):
        title_text = "VICTORY!"
        title_color = GOLDEN_YELLOW # Use a victory color

    draw_text(
        surface,
        title_text,
        popup_rect.centerx,
        title_y,
        font=FONT_XLARGE,
        color=title_color,
        center_aligned=True,
    )  # Larger font for title

    # Display the reason/message
    message_y = title_y + FONT_XLARGE.get_linesize() + 30
    draw_text(
        surface,
        message,
        popup_rect.centerx,
        message_y,
        font=FONT_LARGE_BOLD,
        color=PLATINUM,
        center_aligned=True,
        max_width=popup_width - 60,
    )

    # Buttons are drawn by the main loop via setup_buttons, but this function receives them to draw
    # This allows the main loop to control button drawing centrally if needed,
    # or this function could draw them if they were positioned relative to popup_rect.
    # For now, assuming buttons are passed and positioned correctly by setup_buttons.
    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.draw(surface, mouse_pos)
