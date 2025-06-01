# views/travel_view.py
"""
Handles drawing the Travel view.
"""
from typing import List, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    # from ...core.player_inventory import PlayerInventory # Unused as arg type
    from ...core.region import Region

from .. import game_configs # Moved to top
from ..ui_components import Button
from ..ui_theme import ( # Alphabetized, LIGHT_GREY removed
    FONT_LARGE,
    FONT_MEDIUM,
    GOLDEN_YELLOW,
    PLATINUM,
    YALE_BLUE,
    draw_text,
)

SCREEN_WIDTH = 1024  # Consider moving to shared constants


def draw_travel_view(
    surface: pygame.Surface,
    current_region_data: "Region",
    travel_buttons: List[Button],
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
        "TRAVEL",
        SCREEN_WIDTH // 2,
        70,
        font=FONT_LARGE,
        color=GOLDEN_YELLOW,
        center_aligned=True,
    )

    # Current location section
    location_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, 50)
    pygame.draw.rect(surface, (8, 18, 35), location_rect)
    pygame.draw.rect(surface, YALE_BLUE, location_rect, 1)

    current_region_name = "Unknown"
    if (
        current_region_data
        and hasattr(current_region_data, "name")
        and hasattr(current_region_data.name, "value")
    ):
        current_region_name = current_region_data.name.value

    draw_text(
        surface,
        f"Current Location: {current_region_name}",
        SCREEN_WIDTH // 2,
        145,
        font=FONT_MEDIUM,
        color=PLATINUM,
        center_aligned=True,
    )

    # Destinations section
    destinations_rect = pygame.Rect(40, 190, SCREEN_WIDTH - 80, 500)
    pygame.draw.rect(surface, (8, 18, 35), destinations_rect)
    pygame.draw.rect(surface, YALE_BLUE, destinations_rect, 1)

    # Destinations header
    dest_header_rect = pygame.Rect(50, 200, SCREEN_WIDTH - 100, 30)
    pygame.draw.rect(surface, (25, 35, 55), dest_header_rect)
    pygame.draw.rect(surface, YALE_BLUE, dest_header_rect, 1)
    draw_text(
        surface,
        "AVAILABLE DESTINATIONS",
        SCREEN_WIDTH // 2,
        215,
        font=FONT_MEDIUM,
        color=PLATINUM,
        center_aligned=True,
    )

    # Display travel cost
    # from .. import game_configs # Moved to top

    travel_cost_text = f"(Travel Cost: ${game_configs.TRAVEL_COST_CASH})"
    draw_text(
        surface,
        travel_cost_text,
        SCREEN_WIDTH // 2,
        245,  # Adjust Y position as needed
        font=FONT_MEDIUM,
        color=GOLDEN_YELLOW,
        center_aligned=True,
    )

    mouse_pos = pygame.mouse.get_pos()
    for button in travel_buttons:  # These are pre-configured in setup_buttons
        button.draw(surface, mouse_pos)
