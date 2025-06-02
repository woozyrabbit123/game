# views/upgrades_view.py
"""
Handles drawing the Upgrades view using shared UI elements.
"""
from typing import List, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ...core.player_inventory import PlayerInventory
    # from game_state import GameState
    # from game_configs import GameConfigs

from ..ui_components import Button
from ..ui_theme import (
    EMERALD_GREEN,
    FONT_MEDIUM_BOLD,
    FONT_SMALL,
    LIGHT_GREY,
    PLATINUM,
    TEXT_COLOR,
    # YALE_BLUE, # No longer directly used for lines, but kept if other specific elements need it
    draw_text, # Keep for specific item rendering
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
from ..constants import SCREEN_WIDTH

# Layout constants
TITLE_Y = 40
RESOURCE_BAR_Y = 120
ERROR_MESSAGE_Y = 190 # If definitions missing, it's below resource bar
CONTENT_PANEL_Y = 190
CONTENT_HEADER_Y = 200
UPGRADE_LIST_START_Y = CONTENT_HEADER_Y + 40 # Initial Y for the first upgrade's text block

# Constants from original file, make them relative to panel if possible
UPGRADE_ITEM_X_START_ORIGINAL = 50 # This will become padding inside the panel
# UPGRADE_ITEM_WIDTH_ORIGINAL = SCREEN_WIDTH - 2 * UPGRADE_ITEM_X_START_ORIGINAL # This is panel width effectively
UPGRADE_BUTTON_WIDTH = 170
# UPGRADE_BUTTON_HEIGHT = 40 # Not used in draw function directly


def draw_upgrades_view(
    surface: pygame.Surface,
    player_inventory_data: "PlayerInventory",
    game_state_data: any,  # Parameter kept for interface consistency
    game_configs_data: any,
    upgrades_buttons: List[Button],
):
    draw_view_background(surface)
    # Upgrades view also had main container height of 728.
    # SCREEN_HEIGHT (768) - 728 = 40. So height_offset=40 is correct.
    draw_main_container(surface, height_offset=40)

    # Using the same specific border color for the title as in skills_view
    draw_view_title(surface, "PURCHASE UPGRADES", border_color=(70, 130, 180))

    draw_resource_bar(
        surface,
        f"Current Cash: ${player_inventory_data.cash:,.2f}",
        RESOURCE_BAR_Y,
    )

    if (
        not hasattr(game_configs_data, "UPGRADE_DEFINITIONS")
        or not game_configs_data.UPGRADE_DEFINITIONS
    ):
        draw_missing_definitions_error(
            surface, "UPGRADE_DEFINITIONS", ERROR_MESSAGE_Y
        )
        # Still draw back button
        mouse_pos = pygame.mouse.get_pos()
        for btn in upgrades_buttons:
            if "Back" in btn.text:
                btn.draw(surface, mouse_pos)
        return

    # Upgrades content panel
    # Original upgrades_rect: Rect(40, 190, SCREEN_WIDTH - 80, 500)
    content_panel_rect = draw_content_panel(surface, CONTENT_PANEL_Y, 500)

    # Upgrades header
    # Original upgrades_header_rect: Rect(50, 200, SCREEN_WIDTH - 100, 30)
    draw_panel_header(surface, "AVAILABLE UPGRADES", CONTENT_HEADER_Y)

    # --- Upgrades List Rendering (Specific to this view) ---
    current_y_offset = UPGRADE_LIST_START_Y
    line_height_small = FONT_SMALL.get_linesize() + 2 # From ui_theme if possible, or keep as local const
    item_spacing = 80  # Space between upgrade items

    # Calculate X positions relative to the content panel
    item_render_x_start = content_panel_rect.x + 20 # Indent from panel edge
    # Max width for description, considering button on the right
    description_max_width = content_panel_rect.width - 40 - UPGRADE_BUTTON_WIDTH - 20


    # Helper to draw each upgrade item
    def _draw_upgrade_item(name, current_value_text, description_lines, y_pos):
        draw_text(
            surface,
            name,
            item_render_x_start,
            y_pos,
            font=FONT_MEDIUM_BOLD,
            color=PLATINUM,
        )
        current_text_y_item = y_pos + line_height_small + 5

        if current_value_text: # For capacity, where current value is shown
             draw_text(
                surface,
                current_value_text,
                item_render_x_start + 15,
                current_text_y_item,
                font=FONT_SMALL,
                color=LIGHT_GREY,
            )
             current_text_y_item += line_height_small

        for line_info in description_lines: # description_lines is a list of (text, color) tuples
            draw_text(
                surface,
                line_info[0], # Text
                item_render_x_start + 15,
                current_text_y_item,
                font=FONT_SMALL,
                color=line_info[1], # Color
                max_width=description_max_width,
            )
            current_text_y_item += line_height_small # Adjust for multiple lines if description is long
        return y_pos + item_spacing


    # --- Expanded Capacity Upgrade ---
    capacity_def = game_configs_data.UPGRADE_DEFINITIONS.get("EXPANDED_CAPACITY")
    if capacity_def:
        num_purchased = player_inventory_data.capacity_upgrades_purchased
        max_levels = len(capacity_def["costs"])
        
        current_cap_text = f"Current Max Capacity: {player_inventory_data.max_capacity}"
        desc_lines = []
        if num_purchased < max_levels:
            next_cost = capacity_def["costs"][num_purchased]
            next_capacity_val = capacity_def["capacity_levels"][num_purchased]
            description = capacity_def["description_template"].format(
                next_capacity=next_capacity_val, next_cost=next_cost
            )
            desc_lines.append((description, TEXT_COLOR))
        else:
            desc_lines.append((capacity_def["description_maxed"], EMERALD_GREEN))
        
        current_y_offset = _draw_upgrade_item(capacity_def["name"], current_cap_text, desc_lines, current_y_offset)

    # --- Secure Phone Upgrade ---
    phone_def = game_configs_data.UPGRADE_DEFINITIONS.get("SECURE_PHONE")
    if phone_def:
        desc_lines = []
        description = phone_def["description"]
        if player_inventory_data.has_secure_phone:
            description += " (Owned)"
            desc_lines.append((description, EMERALD_GREEN))
        else:
            description += f" Cost: ${phone_def['cost']:,.0f}"
            desc_lines.append((description, TEXT_COLOR))
        
        current_y_offset = _draw_upgrade_item(phone_def["name"], None, desc_lines, current_y_offset)
        
    # ... Add drawing for other upgrades similarly, calling _draw_upgrade_item ...
    # Example for GHOST_NETWORK access if it were structured like SECURE_PHONE
    ghost_def = game_configs_data.UPGRADE_DEFINITIONS.get("GHOST_NETWORK")
    if ghost_def:
        desc_lines = []
        description = ghost_def["description"]
        if player_inventory_data.ghost_network_access > 0: # Assuming >0 means active/purchased
            description += f" (Active: {player_inventory_data.ghost_network_access} days)"
            desc_lines.append((description, EMERALD_GREEN))
        else:
            description += f" Cost: ${ghost_def['cost']:,.0f}" # Assuming a 'cost' field
            desc_lines.append((description, TEXT_COLOR))
        current_y_offset = _draw_upgrade_item(ghost_def["name"], None, desc_lines, current_y_offset)


    mouse_pos = pygame.mouse.get_pos()
    for button in upgrades_buttons:
        button.draw(surface, mouse_pos)

[end of src/ui_pygame/views/upgrades_view.py]
