"""
Constants for Project Narco-Syndicate Pygame UI.
Split from app.py for modularity.
"""

# Re-exporting from ui_theme for convenience if needed,
# though direct imports from ui_theme in other modules are cleaner.
# Alphabetized:
from .ui_theme import (
    BUTTON_COLOR,
    BUTTON_DISABLED_COLOR,
    BUTTON_DISABLED_TEXT_COLOR,
    BUTTON_HOVER_COLOR,
    BUTTON_TEXT_COLOR,
    DARK_GREY,
    EMERALD_GREEN,
    FONT_LARGE,
    FONT_LARGE_BOLD,
    FONT_MEDIUM,
    FONT_SMALL,
    FONT_XLARGE,
    FONT_XSMALL,
    GHOST_WHITE,
    GOLDEN_YELLOW,
    HUD_ACCENT_COLOR,
    HUD_BACKGROUND_COLOR,
    HUD_TEXT_COLOR,
    IMPERIAL_RED,
    LIGHT_GREY,
    MEDIUM_GREY,
    NEON_BLUE,
    OXFORD_BLUE,
    PLATINUM,
    RICH_BLACK,
    SILVER_LAKE_BLUE,
    TEXT_COLOR,
    TEXT_INPUT_BG_COLOR,
    TEXT_INPUT_BORDER_COLOR,
    TEXT_INPUT_TEXT_COLOR,
    VERY_LIGHT_GREY,
    YALE_BLUE,
    draw_input_box,
    draw_panel,
    draw_text,
)

# Screen Dimensions
SCREEN_WIDTH: int = 1024
SCREEN_HEIGHT: int = 768

# Frames per second
FPS: int = 60

# Standard Button Sizes and Spacing
STD_BUTTON_WIDTH: int = 200
STD_BUTTON_HEIGHT: int = 50
STD_BUTTON_SPACING: int = 10

# Upgrade View Specifics
UPGRADE_ITEM_X_MARGIN: int = 50 # Replaces UPGRADE_ITEM_X_START
UPGRADE_ITEM_WIDTH: int = SCREEN_WIDTH - (2 * UPGRADE_ITEM_X_MARGIN)
UPGRADE_BUTTON_WIDTH: int = 170
UPGRADE_BUTTON_HEIGHT: int = 40

# Popup Specifics
POPUP_WIDTH_RATIO: float = 0.7  # Relative to screen width
POPUP_HEIGHT_RATIO: float = 0.5 # Relative to screen height
POPUP_BUTTON_WIDTH: int = 150
POPUP_BUTTON_HEIGHT: int = 40
POPUP_BUTTON_MARGIN_Y: int = 40 # Margin from bottom of popup

# Prompt Message
PROMPT_DURATION_FRAMES: int = 120
PROMPT_DEFAULT_Y_OFFSET: int = 100  # Offset from bottom of screen for general prompts
PROMPT_TECH_CONTACT_Y_OFFSET: int = 120 # Specific Y offset for tech contact view prompts

# Main Menu Layout
MAIN_MENU_COL1_COUNT: int = 4

# Input Box Defaults (can be overridden per instance)
DEFAULT_INPUT_BOX_WIDTH: int = 200
DEFAULT_INPUT_BOX_HEIGHT: int = 40

# Text Input Area (Buy/Sell Quantity)
MARKET_INPUT_BOX_X_OFFSET: int = 100 # From SCREEN_WIDTH // 2 - 100
MARKET_INPUT_BOX_Y_POS: int = 200
MARKET_INPUT_BOX_WIDTH: int = 200
MARKET_INPUT_BOX_HEIGHT: int = 40

# Tech Contact Input Area
TECH_INPUT_BOX_X_OFFSET: int = 125 # From SCREEN_WIDTH // 2 - 125
TECH_INPUT_BOX_Y_POS: int = 200 # Same Y as market for now
TECH_INPUT_BOX_WIDTH: int = 250
TECH_INPUT_BOX_HEIGHT: int = 40

# General Padding/Margins
SMALL_PADDING: int = 5
MEDIUM_PADDING: int = 10
LARGE_PADDING: int = 20


# Re-exporting from ui_theme for convenience if needed,
# though direct imports from ui_theme in other modules are cleaner.
# This block is now at the top.
