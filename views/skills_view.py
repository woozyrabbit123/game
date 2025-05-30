# views/skills_view.py
"""
Handles drawing the Skills view.
"""
import pygame
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.player_inventory import PlayerInventory
    # from game_state import GameState
    # from game_configs import GameConfigs

from ui_theme import (
    FONT_LARGE, FONT_MEDIUM, FONT_MEDIUM_BOLD, YALE_BLUE, IMPERIAL_RED, GOLDEN_YELLOW,
    draw_text
)
from ui_components import Button

SCREEN_WIDTH = 1024 # Consider shared constants

def draw_skills_view(
    surface: pygame.Surface, 
    player_inventory_data: 'PlayerInventory', 
    # game_state_data: any, # Not directly used in this drawing function
    game_configs_data: any, # For SKILL_DEFINITIONS (though setup_buttons also uses it)
    skills_buttons: List[Button] # Back button and dynamically created Unlock buttons
    ):
    draw_text(surface, "Unlock Skills", SCREEN_WIDTH // 2, 30, font=FONT_LARGE, color=YALE_BLUE, center_aligned=True)
    
    # This check might be redundant if setup_buttons already handles it,
    # but good for robustness if this function were called in other contexts.
    if not hasattr(game_configs_data, 'SKILL_DEFINITIONS') or not game_configs_data.SKILL_DEFINITIONS:
        draw_text(surface, "SKILL_DEFINITIONS missing!", SCREEN_WIDTH // 2, 100, font=FONT_MEDIUM, color=IMPERIAL_RED, center_aligned=True)
        # Still draw back button if it's the only one
        mouse_pos = pygame.mouse.get_pos()
        for btn in skills_buttons: 
            if btn.text == "Back": # A common pattern for a standalone back button
                btn.draw(surface, mouse_pos)
        return

    draw_text(surface, f"Available Skill Points: {player_inventory_data.skill_points}", SCREEN_WIDTH // 2, 70, font=FONT_MEDIUM_BOLD, color=GOLDEN_YELLOW, center_aligned=True)
    
    # The detailed text for each skill (name, description, cost) is drawn by setup_buttons in pygame_ui.py
    # This function's main job now is to draw the title, skill points, and the buttons themselves.
    
    mouse_pos = pygame.mouse.get_pos()
    for button in skills_buttons: # These include "Unlock" buttons and the "Back" button
        button.draw(surface, mouse_pos)
