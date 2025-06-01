# views/blocking_event_popup_view.py
"""
Handles drawing a generic blocking event popup.
"""
import pygame
from typing import List, Dict, Optional

from ..ui_theme import (
    FONT_LARGE,
    FONT_MEDIUM,
    FONT_SMALL,
    YALE_BLUE,
    PLATINUM,
    TEXT_COLOR,
    OXFORD_BLUE,
    RICH_BLACK,  # Added RICH_BLACK for overlay
    draw_text,
    draw_panel,  # Assuming draw_panel is available
)
from ..ui_components import Button

# Constants for popup dimensions (can be adjusted)
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

POPUP_WIDTH_RATIO = 0.6
POPUP_HEIGHT_RATIO = 0.5  # Adjusted for potentially more text


def draw_blocking_event_popup(
    surface: pygame.Surface, event_data: Optional[Dict], buttons: List[Button]
):
    if not event_data:
        return

    # 1. Draw a semi-transparent overlay
    overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay_color = (*RICH_BLACK, 200)  # Dark, semi-transparent
    overlay_surface.fill(overlay_color)
    surface.blit(overlay_surface, (0, 0))

    # 2. Define popup box dimensions
    popup_width = SCREEN_WIDTH * POPUP_WIDTH_RATIO
    popup_height = SCREEN_HEIGHT * POPUP_HEIGHT_RATIO
    popup_x = (SCREEN_WIDTH - popup_width) / 2
    popup_y = (SCREEN_HEIGHT - popup_height) / 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    # 3. Draw popup box (panel)
    # Assuming draw_panel takes: surface, rect, panel_color, border_color, border_width
    draw_panel(surface, popup_rect, OXFORD_BLUE, YALE_BLUE, 2)

    # 4. Display title
    title = event_data.get("title", "Event")
    title_y = popup_y + 30  # Increased padding
    title_font = FONT_LARGE  # Use a larger font for title
    draw_text(
        surface,
        title,
        popup_rect.centerx,
        title_y,
        font=title_font,
        color=PLATINUM,
        center_aligned=True,
    )

    # 5. Display messages
    messages = event_data.get("messages", ["No details."])
    message_start_y = (
        title_y + title_font.get_linesize() + 20
    )  # Start messages below title
    line_spacing = FONT_SMALL.get_linesize() + 5

    max_message_width = popup_width - 60  # Padding inside the popup

    current_message_y = message_start_y
    for message_line in messages:
        # draw_text from ui_theme handles basic word wrapping if max_width is provided
        # It returns the y-coordinate after the drawn text, useful for multi-line messages
        current_message_y = draw_text(
            surface,
            message_line,
            popup_x + 30,
            current_message_y,
            font=FONT_SMALL,
            color=TEXT_COLOR,
            max_width=max_message_width,
        )
        current_message_y += (
            line_spacing // 2
        )  # Add a bit of space between distinct message entries or paragraphs

    # 6. Buttons are drawn by the main loop via setup_buttons,
    #    but their positions were calculated based on popup_rect in setup_buttons.
    #    So, just draw them here if they are passed.
    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.draw(surface, mouse_pos)
