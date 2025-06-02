# views/travel_view.py
"""
Handles drawing the Travel view using shared UI elements.
"""
from typing import List, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ...core.region import Region

from .. import game_configs # For TRAVEL_COST_CASH
from ..ui_components import Button # Buttons are passed in, not created here
from ..ui_theme import (
    FONT_MEDIUM, # For current location and travel cost text
    GOLDEN_YELLOW,
    PLATINUM,
    # YALE_BLUE, # No longer directly used, ui_base_elements handles border colors
    # draw_text, # ui_base_elements handles text drawing for its components
)
from ..ui_base_elements import (
    draw_view_background,
    draw_main_container,
    draw_view_title,
    draw_resource_bar, # Can be adapted for current location display
    draw_content_panel,
    draw_panel_header,
    draw_text, # Keep for specific text like travel cost
)
from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT # For layout calculations if needed

# Layout constants from original, adjust as needed
TITLE_Y = 40
CURRENT_LOCATION_BAR_Y = 120
CONTENT_PANEL_Y = 190
CONTENT_PANEL_HEIGHT = 500 # Original destinations_rect height
CONTENT_HEADER_Y = CONTENT_PANEL_Y + 10 # Original: 200
TRAVEL_COST_TEXT_Y = CONTENT_HEADER_Y + 30 + 30 # Below "Available Destinations" header + spacing


def draw_travel_view(
    surface: pygame.Surface,
    current_region_data: "Region", # Region object for the current location
    travel_buttons: List[Button],  # These are pre-configured destination buttons
):
    draw_view_background(surface)
    # Travel view also had main container height of 728.
    # SCREEN_HEIGHT (768) - 728 = 40. So height_offset=40 is correct.
    draw_main_container(surface, height_offset=40)

    # Using the same specific border color for the title as in other views
    draw_view_title(surface, "TRAVEL", border_color=(70, 130, 180))

    # Current location section (using draw_resource_bar for similar styling)
    current_region_name = "Unknown"
    if (
        current_region_data
        and hasattr(current_region_data, "name")
        and hasattr(current_region_data.name, "value")
    ):
        current_region_name = current_region_data.name.value

    draw_resource_bar(
        surface,
        f"Current Location: {current_region_name}",
        CURRENT_LOCATION_BAR_Y,
        text_font=FONT_MEDIUM, # Matching original font
        text_color=PLATINUM,   # Matching original color
    )

    # Destinations panel
    destinations_panel_rect = draw_content_panel(
        surface, CONTENT_PANEL_Y, CONTENT_PANEL_HEIGHT
    )

    # Destinations header within the panel
    draw_panel_header(
        surface,
        "AVAILABLE DESTINATIONS",
        CONTENT_HEADER_Y, # y position of the header rect
        x = destinations_panel_rect.x + 10, # relative to panel x
        width_offset = (SCREEN_WIDTH - destinations_panel_rect.width) + 20, # adjust width to fit panel
    )

    # Display travel cost (specific text, use direct draw_text)
    travel_cost_text = f"(Travel Cost: ${game_configs.TRAVEL_COST_CASH})"
    draw_text(
        surface,
        travel_cost_text,
        destinations_panel_rect.centerx, # Center in the destinations panel
        TRAVEL_COST_TEXT_Y,
        font=FONT_MEDIUM,
        color=GOLDEN_YELLOW,
        center_aligned=True,
    )

    # Draw travel buttons (positions are set in UIManager._setup_travel_view_buttons)
    # These buttons should be positioned within the destinations_panel_rect.
    # The button setup logic in UIManager needs to be aware of this panel's rect.
    mouse_pos = pygame.mouse.get_pos()
    for button in travel_buttons:
        button.draw(surface, mouse_pos)

[end of src/ui_pygame/views/travel_view.py]
