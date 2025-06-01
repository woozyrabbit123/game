# views/upgrades_view.py
"""
Handles drawing the Upgrades view.
"""
import pygame
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.player_inventory import PlayerInventory

    # from game_state import GameState # Not directly used here
    # from game_configs import GameConfigs # Passed as game_configs_data

from ..ui_theme import (
    FONT_LARGE,
    FONT_MEDIUM,
    FONT_MEDIUM_BOLD,
    FONT_SMALL,
    TEXT_COLOR,
    YALE_BLUE,
    IMPERIAL_RED,
    GOLDEN_YELLOW,
    PLATINUM,
    LIGHT_GREY,
    EMERALD_GREEN,
    draw_text,
)
from ..ui_components import Button

SCREEN_WIDTH = 1024
UPGRADE_ITEM_X_START = 50
UPGRADE_ITEM_WIDTH = SCREEN_WIDTH - 2 * UPGRADE_ITEM_X_START
UPGRADE_BUTTON_WIDTH = 170
UPGRADE_BUTTON_HEIGHT = 40


def draw_upgrades_view(
    surface: pygame.Surface,
    player_inventory_data: "PlayerInventory",
    game_state_data: any,  # Added to match caller (not used)
    game_configs_data: any,
    upgrades_buttons: List[Button],
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

    draw_text(
        surface,
        "PURCHASE UPGRADES",
        SCREEN_WIDTH // 2,
        70,
        font=FONT_LARGE,
        color=GOLDEN_YELLOW,
        center_aligned=True,
    )

    # Cash section
    cash_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, 50)
    pygame.draw.rect(surface, (8, 18, 35), cash_rect)
    pygame.draw.rect(surface, YALE_BLUE, cash_rect, 1)

    draw_text(
        surface,
        f"Current Cash: ${player_inventory_data.cash:,.2f}",
        SCREEN_WIDTH // 2,
        145,
        font=FONT_MEDIUM_BOLD,
        color=GOLDEN_YELLOW,
        center_aligned=True,
    )

    if (
        not hasattr(game_configs_data, "UPGRADE_DEFINITIONS")
        or not game_configs_data.UPGRADE_DEFINITIONS
    ):
        error_rect = pygame.Rect(40, 190, SCREEN_WIDTH - 80, 60)
        pygame.draw.rect(surface, (40, 20, 20), error_rect)
        pygame.draw.rect(surface, IMPERIAL_RED, error_rect, 2)
        draw_text(
            surface,
            "UPGRADE_DEFINITIONS missing!",
            SCREEN_WIDTH // 2,
            220,
            font=FONT_MEDIUM,
            color=IMPERIAL_RED,
            center_aligned=True,
        )
        # Draw only the back button if definitions are missing
        mouse_pos = pygame.mouse.get_pos()
        for btn in upgrades_buttons:
            if "Back" in btn.text:  # A bit fragile, but common for back buttons
                btn.draw(surface, mouse_pos)
        return

    # Upgrades section
    upgrades_rect = pygame.Rect(40, 190, SCREEN_WIDTH - 80, 500)
    pygame.draw.rect(surface, (8, 18, 35), upgrades_rect)
    pygame.draw.rect(surface, YALE_BLUE, upgrades_rect, 1)

    # Upgrades header
    upgrades_header_rect = pygame.Rect(50, 200, SCREEN_WIDTH - 100, 30)
    pygame.draw.rect(surface, (25, 35, 55), upgrades_header_rect)
    pygame.draw.rect(surface, YALE_BLUE, upgrades_header_rect, 1)
    draw_text(
        surface,
        "AVAILABLE UPGRADES",
        SCREEN_WIDTH // 2,
        215,
        font=FONT_MEDIUM,
        color=PLATINUM,
        center_aligned=True,
    )

    upgrade_y_offset = 250
    line_height_small = FONT_SMALL.get_linesize() + 2
    item_spacing = 80  # Space between upgrade items

    # --- Expanded Capacity Upgrade ---
    capacity_def = game_configs_data.UPGRADE_DEFINITIONS.get("EXPANDED_CAPACITY")
    if capacity_def:
        num_purchased = player_inventory_data.capacity_upgrades_purchased
        max_levels = len(capacity_def["costs"])

        draw_text(
            surface,
            capacity_def["name"],
            UPGRADE_ITEM_X_START,
            upgrade_y_offset,
            font=FONT_MEDIUM_BOLD,
            color=PLATINUM,
        )
        current_text_y = upgrade_y_offset + line_height_small + 5
        draw_text(
            surface,
            f"Current Max Capacity: {player_inventory_data.max_capacity}",
            UPGRADE_ITEM_X_START + 15,
            current_text_y,
            font=FONT_SMALL,
            color=LIGHT_GREY,
        )
        current_text_y += line_height_small

        if num_purchased < max_levels:
            next_cost = capacity_def["costs"][num_purchased]
            next_capacity_val = capacity_def["capacity_levels"][num_purchased]
            # Using the description_template from game_configs
            description = capacity_def["description_template"].format(
                next_capacity=next_capacity_val, next_cost=next_cost
            )
            draw_text(
                surface,
                description,
                UPGRADE_ITEM_X_START + 15,
                current_text_y,
                font=FONT_SMALL,
                color=TEXT_COLOR,
                max_width=UPGRADE_ITEM_WIDTH - UPGRADE_BUTTON_WIDTH - 30,
            )
        else:
            draw_text(
                surface,
                capacity_def["description_maxed"],
                UPGRADE_ITEM_X_START + 15,
                current_text_y,
                font=FONT_SMALL,
                color=EMERALD_GREEN,
                max_width=UPGRADE_ITEM_WIDTH - UPGRADE_BUTTON_WIDTH - 30,
            )

        upgrade_y_offset += item_spacing

    # --- Secure Phone Upgrade ---
    phone_def = game_configs_data.UPGRADE_DEFINITIONS.get("SECURE_PHONE")
    if phone_def:
        draw_text(
            surface,
            phone_def["name"],
            UPGRADE_ITEM_X_START,
            upgrade_y_offset,
            font=FONT_MEDIUM_BOLD,
            color=PLATINUM,
        )
        current_text_y = upgrade_y_offset + line_height_small + 5

        description = phone_def["description"]
        if player_inventory_data.has_secure_phone:
            description += " (Owned)"
            draw_text(
                surface,
                description,
                UPGRADE_ITEM_X_START + 15,
                current_text_y,
                font=FONT_SMALL,
                color=EMERALD_GREEN,
                max_width=UPGRADE_ITEM_WIDTH - UPGRADE_BUTTON_WIDTH - 30,
            )
        else:
            description += f" Cost: ${phone_def['cost']:,.0f}"
            draw_text(
                surface,
                description,
                UPGRADE_ITEM_X_START + 15,
                current_text_y,
                font=FONT_SMALL,
                color=TEXT_COLOR,
                max_width=UPGRADE_ITEM_WIDTH - UPGRADE_BUTTON_WIDTH - 30,
            )

        upgrade_y_offset += item_spacing

    # ... Add drawing for other upgrades similarly ...

    # Draw all buttons (Purchase buttons for each item, and Back button)
    # Their positions should have been set correctly in setup_buttons
    mouse_pos = pygame.mouse.get_pos()
    for button in upgrades_buttons:
        button.draw(surface, mouse_pos)
