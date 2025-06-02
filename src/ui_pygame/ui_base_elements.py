# src/ui_pygame/ui_base_elements.py
"""
Shared UI drawing functions for Pygame views to reduce duplication.
"""
import pygame
from typing import Tuple, Optional

from .ui_theme import (
    FONT_LARGE,
    FONT_MEDIUM,
    FONT_MEDIUM_BOLD,
    IMPERIAL_RED,
    GOLDEN_YELLOW,
    YALE_BLUE,
    SILVER_LAKE_BLUE, # Added for market title variant
    draw_text,
)
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT


def draw_view_background(surface: pygame.Surface, color: Tuple[int, int, int] = (5, 15, 30)):
    """Fills the background of a view."""
    surface.fill(color)


def draw_main_container(
    surface: pygame.Surface,
    x: int = 20,
    y: int = 20,
    width_offset: int = 40,
    height_offset: int = 40,
    container_color: Tuple[int, int, int] = (15, 25, 45),
    border_color: Tuple[int, int, int] = YALE_BLUE,
    border_width: int = 3,
):
    """Draws the main bordered container for a view."""
    container_rect = pygame.Rect(x, y, SCREEN_WIDTH - width_offset, SCREEN_HEIGHT - height_offset)
    pygame.draw.rect(surface, container_color, container_rect)
    pygame.draw.rect(surface, border_color, container_rect, border_width)
    return container_rect # Return for potential use (e.g. content alignment)


def draw_view_title(
    surface: pygame.Surface,
    title_text: str,
    x: int = 40,
    y: int = 40,
    width_offset: int = 80,
    height: int = 60,
    bg_color: Tuple[int, int, int] = (10, 20, 40),
    border_color: Tuple[int, int, int] = YALE_BLUE, # Default, can be overridden
    border_width: int = 2,
    text_font: Optional[pygame.font.Font] = None, # Allow overriding font
    text_color: Tuple[int, int, int] = GOLDEN_YELLOW,
):
    """Draws the main title bar with text for a view."""
    if text_font is None:
        text_font = FONT_LARGE # Default if not provided

    title_rect = pygame.Rect(x, y, SCREEN_WIDTH - width_offset, height)
    pygame.draw.rect(surface, bg_color, title_rect)
    pygame.draw.rect(surface, border_color, title_rect, border_width)

    text_x = title_rect.centerx
    text_y = title_rect.centery
    draw_text(
        surface,
        title_text.upper(), # Ensure title is uppercase as per existing views
        text_x,
        text_y,
        font=text_font,
        color=text_color,
        center_aligned=True,
    )
    return title_rect # Return for potential use


def draw_resource_bar(
    surface: pygame.Surface,
    text_content: str,
    y_offset: int,
    x: int = 40,
    width_offset: int = 80, # Screen_width - this value
    height: int = 50,
    rect_color: Tuple[int, int, int] = (8, 18, 35),
    border_color: Tuple[int, int, int] = YALE_BLUE,
    border_width: int = 1,
    text_font: Optional[pygame.font.Font] = None, # Allow overriding
    text_color: Tuple[int, int, int] = GOLDEN_YELLOW,
    center_text: bool = True,
):
    """Draws a generic bar for displaying resources like cash or skill points."""
    if text_font is None:
        text_font = FONT_MEDIUM_BOLD # Default if not provided

    bar_rect = pygame.Rect(x, y_offset, SCREEN_WIDTH - width_offset, height)
    pygame.draw.rect(surface, rect_color, bar_rect)
    pygame.draw.rect(surface, border_color, bar_rect, border_width)

    text_x = bar_rect.centerx if center_text else bar_rect.x + 15
    text_y = bar_rect.centery
    draw_text(
        surface,
        text_content,
        text_x,
        text_y,
        font=text_font,
        color=text_color,
        center_aligned=center_text,
    )
    return bar_rect # Return for potential use


def draw_missing_definitions_error(
    surface: pygame.Surface,
    definition_name: str, # e.g., "SKILL_DEFINITIONS"
    y_offset: int,
    x: int = 40,
    width_offset: int = 80, # Screen_width - this value
    height: int = 60,
    rect_color: Tuple[int, int, int] = (40, 20, 20),
    border_color: Tuple[int, int, int] = IMPERIAL_RED,
    border_width: int = 2,
    text_font: Optional[pygame.font.Font] = None, # Allow overriding
    text_color: Tuple[int, int, int] = IMPERIAL_RED,
):
    """Displays an error message if game definitions are missing."""
    if text_font is None:
        text_font = FONT_MEDIUM # Default if not provided

    error_rect = pygame.Rect(x, y_offset, SCREEN_WIDTH - width_offset, height)
    pygame.draw.rect(surface, rect_color, error_rect)
    pygame.draw.rect(surface, border_color, error_rect, border_width)

    draw_text(
        surface,
        f"{definition_name.upper()} missing or empty!", # Standardized message
        error_rect.centerx,
        error_rect.centery,
        font=text_font,
        color=text_color,
        center_aligned=True,
    )
    return error_rect # Return for potential use

def draw_content_panel(
    surface: pygame.Surface,
    y_offset: int,
    height: int,
    x: int = 40,
    width_offset: int = 80, # Screen_width - this value
    panel_color: Tuple[int, int, int] = (8, 18, 35),
    border_color: Tuple[int, int, int] = YALE_BLUE,
    border_width: int = 1,
):
    """Draws a generic panel for content sections within a view."""
    panel_rect = pygame.Rect(x, y_offset, SCREEN_WIDTH - width_offset, height)
    pygame.draw.rect(surface, panel_color, panel_rect)
    pygame.draw.rect(surface, border_color, panel_rect, border_width)
    return panel_rect

def draw_panel_header(
    surface: pygame.Surface,
    header_text: str,
    y_offset: int, # Y position of the header rect itself
    height: int = 30,
    x: int = 50, # Slightly indented from main content panel x
    width_offset: int = 100, # Screen_width - this value
    bg_color: Tuple[int, int, int] = (25, 35, 55),
    border_color: Tuple[int, int, int] = YALE_BLUE,
    border_width: int = 1,
    text_font: Optional[pygame.font.Font] = None,
    text_color: Tuple[int, int, int] = PLATINUM, # from ui_theme
    center_text: bool = True,
):
    """Draws a header bar for a content panel."""
    if text_font is None:
        text_font = FONT_MEDIUM # Default

    header_rect = pygame.Rect(x, y_offset, SCREEN_WIDTH - width_offset, height)
    pygame.draw.rect(surface, bg_color, header_rect)
    pygame.draw.rect(surface, border_color, header_rect, border_width)

    text_x = header_rect.centerx if center_text else header_rect.x + 10
    text_y = header_rect.centery
    draw_text(
        surface,
        header_text.upper(),
        text_x,
        text_y,
        font=text_font,
        color=text_color,
        center_aligned=center_text,
    )
    return header_rect

# Example of a more specific shared element, if simple enough
def draw_column_headers(
    surface: pygame.Surface,
    headers: list[dict], # e.g. [{"text": "DRUG", "x": 70, "color": PLATINUM}, ...]
    y_pos: int,
    font: Optional[pygame.font.Font] = None,
):
    """Draws a set of column headers."""
    if font is None:
        font = FONT_MEDIUM # Default

    for header_info in headers:
        draw_text(
            surface,
            header_info["text"],
            header_info["x"],
            y_pos,
            font=font,
            color=header_info.get("color", PLATINUM), # Default to PLATINUM
            center_aligned=header_info.get("center_aligned", False)
        )

# Note: A generic list drawing function is likely too complex due to
# varying item data structures, layouts, and interactive elements (buttons per item).
# It's better to handle list drawing within each specific view, but they can
# utilize the more primitive functions above (like draw_text, panel, etc.).

[end of src/ui_pygame/ui_base_elements.py]
