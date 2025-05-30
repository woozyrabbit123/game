# ui_theme.py
"""
Contains the visual theme for the Pygame UI, including colors and fonts.
"""

import pygame

# Initialize Pygame Font Module (if not already initialized)
# It's generally safe to call this multiple times.
pygame.font.init()

# --- Colors ---
# Primary Palette
RICH_BLACK = (0, 10, 20)        # Main background
OXFORD_BLUE = (10, 25, 48)      # Slightly lighter background, panel headers
YALE_BLUE = (20, 50, 90)        # Accent, button backgrounds
SILVER_LAKE_BLUE = (89, 122, 182) # Button hover/active
PLATINUM = (220, 220, 225)      # Primary text
GHOST_WHITE = (248, 248, 255)   # Brighter text, icons

# Accent Colors
IMPERIAL_RED = (230, 57, 70)      # Warnings, negative changes
EMERALD_GREEN = (80, 200, 120)    # Positive changes, confirmations
GOLDEN_YELLOW = (255, 190, 0)     # Highlight, important info
NEON_BLUE = (0, 191, 255)         # Tech, crypto elements

# Greyscale
DARK_GREY = (50, 50, 50)
MEDIUM_GREY = (100, 100, 100)
LIGHT_GREY = (180, 180, 180)
VERY_LIGHT_GREY = (230, 230, 230)


# UI Element Colors
BUTTON_COLOR = YALE_BLUE
BUTTON_HOVER_COLOR = SILVER_LAKE_BLUE
BUTTON_DISABLED_COLOR = MEDIUM_GREY
BUTTON_TEXT_COLOR = PLATINUM
BUTTON_DISABLED_TEXT_COLOR = LIGHT_GREY

TEXT_COLOR = PLATINUM
TEXT_INPUT_BG_COLOR = OXFORD_BLUE
TEXT_INPUT_BORDER_COLOR = SILVER_LAKE_BLUE
TEXT_INPUT_TEXT_COLOR = PLATINUM

HUD_BACKGROUND_COLOR = OXFORD_BLUE
HUD_TEXT_COLOR = PLATINUM
HUD_ACCENT_COLOR = GOLDEN_YELLOW

SCROLLBAR_BG_COLOR = OXFORD_BLUE
SCROLLBAR_THUMB_COLOR = YALE_BLUE
SCROLLBAR_HOVER_THUMB_COLOR = SILVER_LAKE_BLUE


# --- Fonts ---
try:
    FONT_NAME_MAIN = "Arial" # "Consolas", "Courier New"
    FONT_NAME_UI = "Arial"   # A slightly more decorative or distinct UI font if desired

    FONT_SIZE_XLARGE = 48
    FONT_SIZE_LARGE = 36
    FONT_SIZE_MEDIUM = 24
    FONT_SIZE_SMALL = 18
    FONT_SIZE_XSMALL = 14

    FONT_XLARGE = pygame.font.SysFont(FONT_NAME_MAIN, FONT_SIZE_XLARGE)
    FONT_LARGE = pygame.font.SysFont(FONT_NAME_MAIN, FONT_SIZE_LARGE)
    FONT_MEDIUM = pygame.font.SysFont(FONT_NAME_MAIN, FONT_SIZE_MEDIUM)
    FONT_SMALL = pygame.font.SysFont(FONT_NAME_UI, FONT_SIZE_SMALL)
    FONT_XSMALL = pygame.font.SysFont(FONT_NAME_UI, FONT_SIZE_XSMALL)

    # Bold versions
    FONT_LARGE_BOLD = pygame.font.SysFont(FONT_NAME_MAIN, FONT_SIZE_LARGE, bold=True)
    FONT_MEDIUM_BOLD = pygame.font.SysFont(FONT_NAME_MAIN, FONT_SIZE_MEDIUM, bold=True)
    FONT_SMALL_BOLD = pygame.font.SysFont(FONT_NAME_UI, FONT_SIZE_SMALL, bold=True)

except Exception as e:
    print(f"Error loading custom fonts: {e}. Using default Pygame font.")
    FONT_XLARGE = pygame.font.Font(None, FONT_SIZE_XLARGE + 6) # Default font tends to be smaller
    FONT_LARGE = pygame.font.Font(None, FONT_SIZE_LARGE + 4)
    FONT_MEDIUM = pygame.font.Font(None, FONT_SIZE_MEDIUM + 2)
    FONT_SMALL = pygame.font.Font(None, FONT_SIZE_SMALL)
    FONT_XSMALL = pygame.font.Font(None, FONT_SIZE_XSMALL)

    FONT_LARGE_BOLD = pygame.font.Font(None, FONT_SIZE_LARGE + 4) # Pygame's default font doesn't have simple bold
    FONT_MEDIUM_BOLD = pygame.font.Font(None, FONT_SIZE_MEDIUM + 2)
    FONT_SMALL_BOLD = pygame.font.Font(None, FONT_SIZE_SMALL)

# --- UI Helper Functions related to Theme ---

def draw_text(surface, text, x, y, font=FONT_MEDIUM, color=TEXT_COLOR, center_aligned=False, right_aligned=False, max_width=None):
    """Draws text on a surface, optionally centered or right-aligned, with word wrap."""
    if max_width:
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())

        line_height = font.get_linesize()
        for i, line_text in enumerate(lines):
            text_surface = font.render(line_text, True, color)
            text_rect = text_surface.get_rect()
            if center_aligned:
                text_rect.centerx = x
            elif right_aligned:
                text_rect.right = x
            else:
                text_rect.left = x
            text_rect.top = y + (i * line_height)
            surface.blit(text_surface, text_rect)
        return y + (len(lines) * line_height) # Return the y-coordinate after the last line
    else:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center_aligned:
            text_rect.center = (x, y)
        elif right_aligned:
            text_rect.topright = (x,y)
        else:
            text_rect.topleft = (x, y)
        surface.blit(text_surface, text_rect)
        return text_rect.bottom # Return the y-coordinate after the text

def draw_panel(surface, rect, color, border_color, border_width=1):
    """Draws a panel with a border."""
    pygame.draw.rect(surface, color, rect)
    if border_width > 0:
        pygame.draw.rect(surface, border_color, rect, border_width)

def draw_input_box(surface, rect, text, font, text_color, bg_color, border_color, is_active=False, cursor_visible=False, cursor_pos=0):
    """Draws a text input box."""
    pygame.draw.rect(surface, bg_color, rect)
    pygame.draw.rect(surface, border_color if is_active else MEDIUM_GREY, rect, 1)

    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(centery=rect.centery)
    text_rect.left = rect.left + 5
    surface.blit(text_surface, text_rect)

    if is_active and cursor_visible:
        cursor_x_offset = font.size(text[:cursor_pos])[0]
        cursor_y = rect.centery
        pygame.draw.line(surface, text_color, (rect.left + 5 + cursor_x_offset, cursor_y - font.get_height() // 2 + 2),
                                               (rect.left + 5 + cursor_x_offset, cursor_y + font.get_height() // 2 - 2), 1)
