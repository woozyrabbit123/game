# views/informant_view.py
"""
Handles drawing the Informant interaction view.
"""
import pygame
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.player_inventory import PlayerInventory
    # from game_configs import GameConfigs # Passed as game_configs_data

from ui_theme import (
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL,
    YALE_BLUE, PLATINUM, TEXT_COLOR, GOLDEN_YELLOW, LIGHT_GREY,
    draw_text
)
from ui_components import Button

SCREEN_WIDTH = 1024 # Consider shared constants

def draw_informant_view(
    surface: pygame.Surface, 
    player_inv: 'PlayerInventory', 
    informant_buttons: List[Button],
    game_configs_data: any # For INFORMANT_MAX_TRUST
    ):
    draw_text(surface, "Shady Informant", SCREEN_WIDTH // 2, 50, font=FONT_LARGE, color=YALE_BLUE, center_aligned=True)

    y_offset = 100
    line_height = 30

    # Display Player Cash
    cash_text = f"Your Cash: ${player_inv.cash:,.2f}"
    draw_text(surface, cash_text, SCREEN_WIDTH // 2, y_offset, font=FONT_MEDIUM, color=TEXT_COLOR, center_aligned=True)
    y_offset += line_height

    # Display Informant Trust
    max_trust = getattr(game_configs_data, 'INFORMANT_MAX_TRUST', 100) # Default if not found
    trust_text = f"Informant Trust: {player_inv.informant_trust} / {max_trust}"
    # Change color based on trust level
    trust_color = GOLDEN_YELLOW
    if player_inv.informant_trust < max_trust / 3:
        trust_color = LIGHT_GREY
    elif player_inv.informant_trust < max_trust * 2 / 3:
        trust_color = PLATINUM
        
    draw_text(surface, trust_text, SCREEN_WIDTH // 2, y_offset, font=FONT_MEDIUM, color=trust_color, center_aligned=True)
    y_offset += line_height * 1.5 # Extra spacing before buttons

    # Buttons are passed in and include their positions set by setup_buttons
    # Their drawing is handled by the main loop after this function, or can be done here:
    mouse_pos = pygame.mouse.get_pos()
    for button in informant_buttons:
        button.draw(surface, mouse_pos)
