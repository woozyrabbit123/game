# views/police_stop_view.py
"""
Handles drawing the Police Stop Event view.
"""
import pygame
from typing import List, Dict, Optional

from ..ui_theme import FONT_LARGE, FONT_MEDIUM, FONT_SMALL, YALE_BLUE, PLATINUM, IMPERIAL_RED, draw_text
from ..ui_components import Button

SCREEN_WIDTH = 1024 # Consider shared constants

def draw_police_stop_event_view(
    surface: pygame.Surface, 
    police_stop_event_data: Optional[Dict], 
    event_buttons: List[Button]
    ):
    draw_text(surface, "Police Stop!", SCREEN_WIDTH // 2, 100, font=FONT_LARGE, color=IMPERIAL_RED, center_aligned=True)

    message_y = 200
    if police_stop_event_data:
        description = police_stop_event_data.get("outcome_message", "You've been pulled over by the police!")
        options_available = police_stop_event_data.get("options_available", True)

        if not options_available: # Outcome phase
            draw_text(surface, description, SCREEN_WIDTH // 2, message_y, font=FONT_MEDIUM, color=PLATINUM, center_aligned=True, max_width=SCREEN_WIDTH - 100)
        else: # Initial phase
            draw_text(surface, description, SCREEN_WIDTH // 2, message_y, font=FONT_MEDIUM, color=PLATINUM, center_aligned=True, max_width=SCREEN_WIDTH - 100)
            message_y += FONT_MEDIUM.get_linesize() * 2
            draw_text(surface, "What do you do?", SCREEN_WIDTH // 2, message_y, font=FONT_SMALL, color=PLATINUM, center_aligned=True)

    mouse_pos = pygame.mouse.get_pos()
    for button in event_buttons:
        button.draw(surface, mouse_pos)
