# views/skills_view.py
"""
Handles drawing the Skills view using shared UI elements.
"""
from typing import List, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ...core.player_inventory import PlayerInventory
    # from game_state import GameState # Not directly used in draw function
    # from game_configs import GameConfigs # Used for SKILL_DEFINITIONS

from ..ui_components import Button
from ..ui_theme import (
    FONT_MEDIUM_BOLD,
    FONT_SMALL,
    FONT_XSMALL,
    GOLDEN_YELLOW,
    PLATINUM,
    YALE_BLUE, # For separator line, keep specific theme colors here
    draw_text, # Keep direct draw_text for specific item rendering
)
from ..ui_base_elements import (
    draw_view_background,
    draw_main_container,
    draw_view_title,
    draw_resource_bar,
    draw_missing_definitions_error,
    draw_content_panel,
    draw_panel_header,
)
from ..constants import SCREEN_WIDTH # Use SCREEN_WIDTH from constants

# Define Y offsets for layout - makes adjustments easier
TITLE_Y = 40
RESOURCE_BAR_Y = 120
ERROR_MESSAGE_Y = 120 # Same as resource bar if definitions are missing
CONTENT_PANEL_Y = 190
CONTENT_HEADER_Y = 200 # Relative to screen, not panel
SKILL_LIST_START_Y_TEXT = CONTENT_HEADER_Y + 40 # Initial Y for the first skill's text, relative to screen


def draw_skills_view(
    surface: pygame.Surface,
    player_inventory_data: "PlayerInventory",
    game_state_data: any,  # Parameter kept for consistent interface, not used directly
    game_configs_data: any,
    skills_buttons: List[Button],
):
    draw_view_background(surface)
    # Skills view has a slightly different height for main container
    draw_main_container(surface, height_offset=SCREEN_WIDTH - 728 + 20) # Original was 728 height for a 1024 screen width.
                                                                     # SCREEN_HEIGHT is 768. So original was SCREEN_HEIGHT - 40.
                                                                     # The main_container in skills_view.py was:
                                                                     # main_container = pygame.Rect(20, 20, SCREEN_WIDTH - 40, 728)
                                                                     # SCREEN_HEIGHT (768) - 728 = 40. So height_offset=40 is correct.

    # Title uses a specific border color (70, 130, 180) which is a bit different from default YALE_BLUE or SILVER_LAKE_BLUE
    # Let's assume this specific color is part of "YALE_BLUE" family for now, or ui_theme could be expanded.
    # For now, using default YALE_BLUE as an approximation. If specific color is crucial, it should be in ui_theme.
    # The original color was (70, 130, 180) - closer to a light blue.
    # We'll pass YALE_BLUE for now, this can be refined if ui_theme is updated.
    draw_view_title(surface, "UNLOCK SKILLS", border_color=(70, 130, 180)) # Pass specific border color

    if (
        not hasattr(game_configs_data, "SKILL_DEFINITIONS")
        or not game_configs_data.SKILL_DEFINITIONS
    ):
        draw_missing_definitions_error(
            surface, "SKILL_DEFINITIONS", ERROR_MESSAGE_Y
        )
        # Still draw back button if it's the only one
        mouse_pos = pygame.mouse.get_pos()
        for btn in skills_buttons:
            if btn.text == "Back":
                btn.draw(surface, mouse_pos)
        return

    draw_resource_bar(
        surface,
        f"Available Skill Points: {player_inventory_data.skill_points}",
        RESOURCE_BAR_Y,
    )

    # Skills content panel
    # Original skills_rect: Rect(40, 190, SCREEN_WIDTH - 80, 500)
    # y=190, height=500
    content_panel_rect = draw_content_panel(surface, CONTENT_PANEL_Y, 500)

    # Skills header within the content panel
    # Original skills_header_rect: Rect(50, 200, SCREEN_WIDTH - 100, 30)
    # y=200. Panel starts at 190. Header x is 50 (panel x is 40).
    draw_panel_header(surface, "AVAILABLE SKILLS", CONTENT_HEADER_Y)


    # --- Skills List Rendering (Kept specific to this view) ---
    skill_item_v_spacing = 80  # Vertical spacing between skill items
    text_x_start = content_panel_rect.x + 20  # Left padding relative to panel
    cost_x_pos = text_x_start + 380
    description_max_width = content_panel_rect.width - 40 - 170 - 20 # Relative to panel width

    if hasattr(game_configs_data, "SKILL_DEFINITIONS"):
        # Adjust SKILL_LIST_START_Y_TEXT to be relative to where the header ends
        current_y_draw_offset = SKILL_LIST_START_Y_TEXT

        for idx, (skill_id, skill_def) in enumerate(
            game_configs_data.SKILL_DEFINITIONS.items()
        ):
            # Draw Skill Name
            draw_text(
                surface,
                skill_def["name"],
                text_x_start,
                current_y_draw_offset,
                font=FONT_MEDIUM_BOLD,
                color=PLATINUM,
            )

            # Draw Skill Cost
            cost_text = f"Cost: {skill_def['cost']} SP"
            is_unlocked = skill_id in player_inventory_data.unlocked_skills
            cost_color = GOLDEN_YELLOW
            if is_unlocked:
                cost_text = "Unlocked"
                cost_color = (100, 180, 100)  # Light green for unlocked

            draw_text(
                surface,
                cost_text,
                cost_x_pos, # This might need to be relative to panel or absolute
                current_y_draw_offset,
                font=FONT_SMALL,
                color=cost_color,
            )

            # Draw Skill Description
            draw_text(
                surface,
                skill_def["description"],
                text_x_start,
                current_y_draw_offset + 25,
                font=FONT_XSMALL,
                color=PLATINUM,
                max_width=description_max_width,
            )

            # Separator line
            if idx < len(game_configs_data.SKILL_DEFINITIONS) - 1:
                line_y = current_y_draw_offset + skill_item_v_spacing - 15
                pygame.draw.line(
                    surface,
                    YALE_BLUE,
                    (text_x_start, line_y),
                    (content_panel_rect.right - 20, line_y), # Draw line to panel edge
                    1,
                )
            
            current_y_draw_offset += skill_item_v_spacing


    mouse_pos = pygame.mouse.get_pos()
    for button in skills_buttons:
        button.draw(surface, mouse_pos)

[end of src/ui_pygame/views/skills_view.py]
