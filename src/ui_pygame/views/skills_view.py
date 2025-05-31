# views/skills_view.py
"""
Handles drawing the Skills view.
"""
import pygame
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.player_inventory import PlayerInventory
    # from game_state import GameState
    # from game_configs import GameConfigs

from ..ui_theme import (
    FONT_LARGE, FONT_MEDIUM, FONT_MEDIUM_BOLD, FONT_SMALL, FONT_XSMALL, YALE_BLUE, IMPERIAL_RED, GOLDEN_YELLOW, PLATINUM,
    draw_text
)
from ..ui_components import Button

SCREEN_WIDTH = 1024 # Consider shared constants

def draw_skills_view(
    surface: pygame.Surface,
    player_inventory_data: 'PlayerInventory',
    game_state_data: any,  # Added to match caller, not used
    game_configs_data: any, # For SKILL_DEFINITIONS (though setup_buttons also uses it)
    skills_buttons: List[Button] # Back button and dynamically created Unlock buttons
    ):
    # Clear background with gradient effect
    surface.fill((5, 15, 30))  # Dark blue background
    
    # Draw main container with border
    main_container = pygame.Rect(20, 20, SCREEN_WIDTH - 40, 728)
    pygame.draw.rect(surface, (15, 25, 45), main_container)
    pygame.draw.rect(surface, YALE_BLUE, main_container, 3)
    
    # Title section with background
    title_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, 60)
    pygame.draw.rect(surface, (10, 20, 40), title_rect)
    pygame.draw.rect(surface, (70, 130, 180), title_rect, 2)
    
    draw_text(surface, "UNLOCK SKILLS", SCREEN_WIDTH // 2, 70, 
              font=FONT_LARGE, color=GOLDEN_YELLOW, center_aligned=True)
    
    # This check might be redundant if setup_buttons already handles it,
    # but good for robustness if this function were called in other contexts.
    if not hasattr(game_configs_data, 'SKILL_DEFINITIONS') or not game_configs_data.SKILL_DEFINITIONS:
        error_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, 60)
        pygame.draw.rect(surface, (40, 20, 20), error_rect)
        pygame.draw.rect(surface, IMPERIAL_RED, error_rect, 2)
        draw_text(surface, "SKILL_DEFINITIONS missing!", SCREEN_WIDTH // 2, 150, 
                  font=FONT_MEDIUM, color=IMPERIAL_RED, center_aligned=True)
        # Still draw back button if it's the only one
        mouse_pos = pygame.mouse.get_pos()
        for btn in skills_buttons: 
            if btn.text == "Back": # A common pattern for a standalone back button
                btn.draw(surface, mouse_pos)
        return

    # Skill points section
    points_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, 50)
    pygame.draw.rect(surface, (8, 18, 35), points_rect)
    pygame.draw.rect(surface, YALE_BLUE, points_rect, 1)
    
    draw_text(surface, f"Available Skill Points: {player_inventory_data.skill_points}", 
              SCREEN_WIDTH // 2, 145, font=FONT_MEDIUM_BOLD, color=GOLDEN_YELLOW, center_aligned=True)
    
    # Skills section
    skills_rect = pygame.Rect(40, 190, SCREEN_WIDTH - 80, 500)
    pygame.draw.rect(surface, (8, 18, 35), skills_rect)
    pygame.draw.rect(surface, YALE_BLUE, skills_rect, 1)
    
    # Skills header
    skills_header_rect = pygame.Rect(50, 200, SCREEN_WIDTH - 100, 30)
    pygame.draw.rect(surface, (25, 35, 55), skills_header_rect)
    pygame.draw.rect(surface, YALE_BLUE, skills_header_rect, 1)
    draw_text(surface, "AVAILABLE SKILLS", SCREEN_WIDTH // 2, 215, 
              font=FONT_MEDIUM, color=PLATINUM, center_aligned=True)

    skill_y_start_text = 240  # Initial Y position for the first skill's text block
    skill_item_v_spacing = 80 # Vertical spacing between skill items
    text_x_start = 60         # Left padding for text
    cost_x_pos = text_x_start + 380 # X position for cost text (adjust as needed)
    # Max width for description, considering button on the right
    # Approx: SCREEN_WIDTH - left_margin - right_margin - button_width - padding_for_button
    description_max_width = SCREEN_WIDTH - text_x_start - 60 - 170 - 20


    if hasattr(game_configs_data, 'SKILL_DEFINITIONS'):
        for idx, (skill_id, skill_def) in enumerate(game_configs_data.SKILL_DEFINITIONS.items()):
            current_skill_base_y = skill_y_start_text + (idx * skill_item_v_spacing)

            # Draw Skill Name
            draw_text(surface, skill_def['name'], text_x_start, current_skill_base_y,
                      font=FONT_MEDIUM_BOLD, color=PLATINUM)

            # Draw Skill Cost
            cost_text = f"Cost: {skill_def['cost']} SP"
            # Check if skill is already unlocked to change cost text color/style
            is_unlocked = skill_id in player_inventory_data.unlocked_skills
            cost_color = GOLDEN_YELLOW
            if is_unlocked:
                cost_text = "Unlocked"
                cost_color = (100, 180, 100) # A light green for unlocked

            draw_text(surface, cost_text, cost_x_pos, current_skill_base_y,
                      font=FONT_SMALL, color=cost_color)

            # Draw Skill Description
            draw_text(surface, skill_def['description'], text_x_start, current_skill_base_y + 25,
                      font=FONT_XSMALL, color=PLATINUM, max_width=description_max_width)

            # Separator line (optional)
            if idx < len(game_configs_data.SKILL_DEFINITIONS) - 1:
                 line_y = current_skill_base_y + skill_item_v_spacing - 15
                 pygame.draw.line(surface, YALE_BLUE, (text_x_start, line_y), (SCREEN_WIDTH - text_x_start - 60, line_y), 1)


    mouse_pos = pygame.mouse.get_pos()
    for button in skills_buttons: # These include "Unlock" buttons and the "Back" button
        button.draw(surface, mouse_pos)
