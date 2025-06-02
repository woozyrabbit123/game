# src/ui_pygame/views/generic_contact_view.py
"""
Generic view for displaying contact information and services.
"""
from typing import List, Dict, Any, TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from ..ui_components import Button # Assuming Button class is in ui_components
    from ...core.enums import ContactID

from ..ui_base_elements import (
    draw_view_background,
    draw_main_container,
    draw_view_title,
    draw_content_panel,
    draw_panel_header,
    draw_text,
)
from ..ui_theme import FONT_MEDIUM, FONT_SMALL, PLATINUM, TEXT_COLOR, GOLDEN_YELLOW, YALE_BLUE
from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT


def draw_generic_contact_view(
    surface: pygame.Surface,
    contact_id: "ContactID", # To fetch details from game_configs
    contact_definition: Dict[str, Any], # The actual definition from CONTACT_DEFINITIONS
    contact_buttons: List["Button"], # Back button and service buttons
    player_trust: int, # Current trust level with this contact
):
    draw_view_background(surface)
    main_container_rect = draw_main_container(surface, height_offset=40)

    contact_name = contact_definition.get("name", "Unknown Contact")
    draw_view_title(surface, contact_name.upper(), border_color=(70, 130, 180))

    content_panel_y = 120
    content_panel_height = SCREEN_HEIGHT - content_panel_y - 70 # Space for back button
    content_panel_rect = draw_content_panel(surface, content_panel_y, content_panel_height)

    # Contact Description
    description_text = contact_definition.get("description", "No description available.")
    desc_y_start = content_panel_rect.top + 20
    draw_text(
        surface,
        description_text,
        content_panel_rect.centerx,
        desc_y_start,
        font=FONT_MEDIUM,
        color=PLATINUM,
        center_aligned=True,
        max_width=content_panel_rect.width - 40
    )

    # Trust Level
    trust_text = f"Trust: {player_trust}"
    trust_y = desc_y_start + FONT_MEDIUM.get_linesize() * (description_text.count('\n') + 2) # Adjust based on lines in desc
    draw_text(
        surface,
        trust_text,
        content_panel_rect.centerx,
        trust_y,
        font=FONT_SMALL,
        color=GOLDEN_YELLOW,
        center_aligned=True,
    )

    # Services Header
    services_header_y = trust_y + FONT_SMALL.get_linesize() + 20
    draw_panel_header(
        surface,
        "Available Services",
        services_header_y,
        x=content_panel_rect.x + 10,
        width_offset=(SCREEN_WIDTH - content_panel_rect.width) + 20, # Make header fit panel
    )

    # Service Buttons (should be created and positioned by UIManager)
    # The buttons are passed in `contact_buttons`. This view just draws them.
    # Their positions should be calculated in UIManager._setup_contact_view_buttons
    # based on the content_panel_rect and services_header_y.
    
    # Example y for first service button, to guide UIManager setup
    # first_service_button_y = services_header_y + FONT_MEDIUM.get_linesize() + 20

    mouse_pos = pygame.mouse.get_pos()
    for button in contact_buttons:
        button.draw(surface, mouse_pos)

[end of src/ui_pygame/views/generic_contact_view.py]
