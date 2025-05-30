# views/travel_view.py
"""
Handles drawing the Travel view.
"""
import pygame
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.player_inventory import PlayerInventory # Not directly used in drawing, but good for context
    from core.region import Region
    # from game_state import GameState # If specific parts of game_state are needed

from ui_theme import (
    FONT_LARGE, FONT_MEDIUM, YALE_BLUE, LIGHT_GREY,
    draw_text
)
from ui_components import Button

SCREEN_WIDTH = 1024 # Consider moving to shared constants

def draw_travel_view(
    surface: pygame.Surface, 
    current_region_data: 'Region', 
    # player_inventory_data: 'PlayerInventory', # Not directly used in this drawing function
    # game_state_data: any, # Not directly used in this drawing function
    travel_buttons: List[Button] # Contains buttons for destinations + Back button
    ):
    draw_text(surface, "Travel", SCREEN_WIDTH // 2, 30, font=FONT_LARGE, color=YALE_BLUE, center_aligned=True)
    
    current_region_name = "Unknown"
    if current_region_data and hasattr(current_region_data, 'name') and hasattr(current_region_data.name, 'value'):
        current_region_name = current_region_data.name.value
        
    draw_text(surface, f"Current Location: {current_region_name}", SCREEN_WIDTH // 2, 80, font=FONT_MEDIUM, color=LIGHT_GREY, center_aligned=True)
    
    mouse_pos = pygame.mouse.get_pos()
    for button in travel_buttons: # These are pre-configured in setup_buttons
        button.draw(surface, mouse_pos)
