# ui_hud.py
"""
Manages the Heads-Up Display (HUD) elements, including a persistent log.
"""
import pygame
from typing import Optional, List

from .ui_theme import (
    HUD_BACKGROUND_COLOR,
    HUD_TEXT_COLOR,
    FONT_MEDIUM,
    FONT_XSMALL,
    OXFORD_BLUE,
    YALE_BLUE,
    IMPERIAL_RED,
    PLATINUM,
    RICH_BLACK,
    EMERALD_GREEN,
    GOLDEN_YELLOW,
    draw_text,
)

# --- Constants ---
MAX_LOG_MESSAGES: int = 7  # Max number of messages in the persistent log
FPS = 60  # Frames per second for test mode

# --- HUD State Variables ---
ui_log_messages: List[str] = []  # For persistent log display


def add_message_to_log(message: str):
    """Adds a message to the persistent UI log."""
    global ui_log_messages
    # Simple word wrapping for log messages (optional, basic version)
    # This could be more sophisticated if needed.
    log_line_max_width_approx = SCREEN_WIDTH // 2 - 30  # Approx width of log area

    words = message.split(" ")
    wrapped_message_lines = []
    current_line = ""
    for word in words:
        if FONT_XSMALL.size(current_line + " " + word)[0] < log_line_max_width_approx:
            current_line += " " + word if current_line else word
        else:
            wrapped_message_lines.append(current_line)
            current_line = word
    if current_line:  # Add any remaining part of the message
        wrapped_message_lines.append(current_line)

    for line in wrapped_message_lines:
        ui_log_messages.append(line)

    while len(ui_log_messages) > MAX_LOG_MESSAGES:
        ui_log_messages.pop(0)  # Remove the oldest message(s) to maintain max length


def show_event_message(
    message: str,
):  # duration_frames and add_to_log parameters removed
    """
    Adds a message to the persistent UI log.
    Temporary prominent display is removed in favor of the log.
    """
    add_message_to_log(message)


def update_hud_timers():
    """
    Placeholder for future timer updates if any are added back to the HUD.
    Currently, no HUD-specific timers are active after removing the temporary pop-up.
    """
    pass  # No timers to update for now


def draw_hud(
    surface: pygame.Surface,
    player_inventory_data: Optional[any],
    current_region_data: Optional[any],
    game_state_data: Optional[any],
):
    """
    Draws the main game HUD, including the persistent log.
    """
    global ui_log_messages

    screen_width = surface.get_width()
    screen_height = surface.get_height()

    # Improved HUD bar with gradient and border
    hud_bar_height = 80  # Increased height for better proportions
    hud_bar_y_start = screen_height - hud_bar_height

    # Draw HUD background with gradient effect
    hud_rect = pygame.Rect(0, hud_bar_y_start, screen_width, hud_bar_height)
    s = pygame.Surface((screen_width, hud_bar_height), pygame.SRCALPHA)
    s.fill((*OXFORD_BLUE, 220))
    surface.blit(s, (0, hud_bar_y_start))

    # Add border
    pygame.draw.rect(surface, YALE_BLUE, hud_rect, 2)

    # Divide HUD into sections with separators
    hud_text_y_center = hud_bar_y_start + (hud_bar_height // 2)
    section_width = screen_width // 4

    # Section separators
    for i in range(1, 4):
        sep_x = section_width * i
        pygame.draw.line(
            surface,
            YALE_BLUE,
            (sep_x, hud_bar_y_start + 10),
            (sep_x, hud_bar_y_start + hud_bar_height - 10),
            1,
        )

    # Day display with icon
    if game_state_data and hasattr(game_state_data, "current_day"):
        day_x = section_width // 2
        draw_text(
            surface,
            "DAY",
            day_x,
            hud_text_y_center - 15,
            font=FONT_XSMALL,
            color=GOLDEN_YELLOW,
            center_aligned=True,
        )
        draw_text(
            surface,
            f"{game_state_data.current_day}",
            day_x,
            hud_text_y_center + 5,
            font=FONT_MEDIUM,
            color=PLATINUM,
            center_aligned=True,
        )

    # Cash display with better formatting
    if player_inventory_data and hasattr(player_inventory_data, "cash"):
        cash_x = section_width + (section_width // 2)
        draw_text(
            surface,
            "CASH",
            cash_x,
            hud_text_y_center - 15,
            font=FONT_XSMALL,
            color=EMERALD_GREEN,
            center_aligned=True,
        )
        cash_text = f"${player_inventory_data.cash:,.0f}"
        draw_text(
            surface,
            cash_text,
            cash_x,
            hud_text_y_center + 5,
            font=FONT_MEDIUM,
            color=EMERALD_GREEN,
            center_aligned=True,
        )

    # Region display with better styling
    if current_region_data and hasattr(current_region_data, "name"):
        region_x = (section_width * 2) + (section_width // 2)
        draw_text(
            surface,
            "LOCATION",
            region_x,
            hud_text_y_center - 15,
            font=FONT_XSMALL,
            color=GOLDEN_YELLOW,
            center_aligned=True,
        )
        region_name = (
            current_region_data.name
            if isinstance(current_region_data.name, str)
            else current_region_data.name.value
        )
        draw_text(
            surface,
            region_name.upper(),
            region_x,
            hud_text_y_center + 5,
            font=FONT_MEDIUM,
            color=PLATINUM,
            center_aligned=True,
        )

    # Load display with progress bar effect
    if (
        player_inventory_data
        and hasattr(player_inventory_data, "current_load")
        and hasattr(player_inventory_data, "max_capacity")
    ):
        load_x = (section_width * 3) + (section_width // 2)
        load_percentage = (
            player_inventory_data.current_load / player_inventory_data.max_capacity
            if player_inventory_data.max_capacity > 0
            else 0
        )
        load_color = (
            IMPERIAL_RED
            if load_percentage > 0.9
            else GOLDEN_YELLOW if load_percentage > 0.7 else EMERALD_GREEN
        )

        draw_text(
            surface,
            "LOAD",
            load_x,
            hud_text_y_center - 15,
            font=FONT_XSMALL,
            color=load_color,
            center_aligned=True,
        )
        load_text = (
            f"{player_inventory_data.current_load}/{player_inventory_data.max_capacity}"
        )
        draw_text(
            surface,
            load_text,
            load_x,
            hud_text_y_center + 5,
            font=FONT_MEDIUM,
            color=load_color,
            center_aligned=True,
        )
    # Draw improved persistent log area
    log_line_height = FONT_XSMALL.get_linesize() + 4  # Increased spacing
    log_area_height = log_line_height * MAX_LOG_MESSAGES + 20  # Added padding
    log_area_y_start = hud_bar_y_start - log_area_height - 10  # More spacing from HUD
    log_line_x = 20

    # Log background with better styling
    log_bg_width = screen_width // 2 + 50  # Wider log area
    log_bg_rect = pygame.Rect(10, log_area_y_start - 10, log_bg_width, log_area_height)

    # Gradient background for log
    log_bg_surface = pygame.Surface(
        (log_bg_rect.width, log_bg_rect.height), pygame.SRCALPHA
    )
    log_bg_surface.fill((*OXFORD_BLUE, 200))
    surface.blit(log_bg_surface, log_bg_rect.topleft)

    # Log border and header
    pygame.draw.rect(surface, YALE_BLUE, log_bg_rect, 2)

    # Log header
    header_rect = pygame.Rect(log_bg_rect.x, log_bg_rect.y, log_bg_rect.width, 25)
    pygame.draw.rect(surface, YALE_BLUE, header_rect)
    draw_text(
        surface,
        "GAME LOG",
        log_bg_rect.centerx,
        header_rect.centery,
        font=FONT_XSMALL,
        color=PLATINUM,
        center_aligned=True,
    )

    # Log messages with alternating background
    current_log_y = log_area_y_start + 30
    for i, msg in enumerate(ui_log_messages):
        # Alternating row background
        if i % 2 == 0:
            row_rect = pygame.Rect(
                log_bg_rect.x + 2,
                current_log_y - 2,
                log_bg_rect.width - 4,
                log_line_height,
            )
            pygame.draw.rect(surface, (*RICH_BLACK, 100), row_rect)

        draw_text(
            surface,
            msg,
            log_line_x,
            current_log_y,
            font=FONT_XSMALL,
            color=PLATINUM,
            max_width=log_bg_width - 20,
        )
        current_log_y += log_line_height


# Example usage (for testing this module standalone, if needed):
# Define SCREEN_WIDTH if running standalone for the log_line_max_width_approx in add_message_to_log
SCREEN_WIDTH = 1024
if __name__ == "__main__":
    pygame.init()
    screen_height_test = 768
    screen_test = pygame.display.set_mode(
        (SCREEN_WIDTH, screen_height_test)
    )  # Use global SCREEN_WIDTH
    pygame.display.set_caption("HUD Test with Log")
    clock_test = pygame.time.Clock()

    class MockPlayerInventory:
        cash = 12345.67
        current_load = 25
        max_capacity = 100

    class MockRegion:
        class MockRegionName:
            value = "Test Region Alpha"

        name = MockRegionName()

    class MockGameState:
        current_day = 42

    mock_player_inv = MockPlayerInventory()
    mock_region = MockRegion()
    mock_game_state = MockGameState()

    add_message_to_log(
        "Log started. This is a slightly longer welcome message to test wrapping if it happens to be implemented effectively."
    )
    add_message_to_log("Day 1: A new beginning...")
    show_event_message("This is an event message that will go to the log.")

    running_test = True
    msg_counter = 0
    while running_test:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_test = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    msg_counter += 1
                    show_event_message(
                        f"Another event! ({msg_counter}) This one is also a bit long to see how text behaves."
                    )
                if event.key == pygame.K_l:
                    msg_counter += 1
                    add_message_to_log(f"A specific log entry. ({msg_counter})")

        update_hud_timers()
        screen_test.fill(RICH_BLACK)
        draw_hud(screen_test, mock_player_inv, mock_region, mock_game_state)
        pygame.display.flip()
        clock_test.tick(FPS)
    pygame.quit()
