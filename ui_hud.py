# ui_hud.py
"""
Manages the Heads-Up Display (HUD) elements, including a persistent log.
"""
import pygame
from typing import Optional, List 

from ui_theme import (
    HUD_BACKGROUND_COLOR, HUD_TEXT_COLOR, FONT_MEDIUM, FONT_XSMALL, 
    OXFORD_BLUE, YALE_BLUE, IMPERIAL_RED, PLATINUM, # Added PLATINUM for log text
    draw_text
)

# --- Constants ---
MAX_LOG_MESSAGES: int = 7 # Max number of messages in the persistent log

# --- HUD State Variables ---
ui_log_messages: List[str] = [] # For persistent log display

def add_message_to_log(message: str):
    """Adds a message to the persistent UI log."""
    global ui_log_messages
    # Simple word wrapping for log messages (optional, basic version)
    # This could be more sophisticated if needed.
    log_line_max_width_approx = SCREEN_WIDTH // 2 - 30 # Approx width of log area
    
    words = message.split(' ')
    wrapped_message_lines = []
    current_line = ""
    for word in words:
        if FONT_XSMALL.size(current_line + " " + word)[0] < log_line_max_width_approx:
            current_line += " " + word if current_line else word
        else:
            wrapped_message_lines.append(current_line)
            current_line = word
    if current_line: # Add any remaining part of the message
        wrapped_message_lines.append(current_line)
    
    for line in wrapped_message_lines:
        ui_log_messages.append(line)

    while len(ui_log_messages) > MAX_LOG_MESSAGES:
        ui_log_messages.pop(0) # Remove the oldest message(s) to maintain max length

def show_event_message(message: str): # duration_frames and add_to_log parameters removed
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
    pass # No timers to update for now


def draw_hud(surface: pygame.Surface, player_inventory_data: Optional[any], current_region_data: Optional[any], game_state_data: Optional[any]):
    """
    Draws the main game HUD, including the persistent log.
    """
    global ui_log_messages # SCREEN_WIDTH needs to be defined if not passed

    hud_bar_height = 60
    screen_width = surface.get_width()
    screen_height = surface.get_height()
    
    hud_bar_y_start = screen_height - hud_bar_height

    s = pygame.Surface((screen_width, hud_bar_height), pygame.SRCALPHA)
    s.fill((*HUD_BACKGROUND_COLOR, 200)) 
    surface.blit(s, (0, hud_bar_y_start))

    hud_text_y_center = hud_bar_y_start + (hud_bar_height // 2) 

    if game_state_data and hasattr(game_state_data, 'current_day'): 
        draw_text(surface, f"Day: {game_state_data.current_day}", 30, hud_text_y_center, font=FONT_MEDIUM, color=HUD_TEXT_COLOR, center_aligned=False, right_aligned=False) # Explicitly set alignment
    
    if player_inventory_data:
        if hasattr(player_inventory_data, 'cash'):
            draw_text(surface, f"Cash: ${player_inventory_data.cash:,.2f}", 180, hud_text_y_center, font=FONT_MEDIUM, color=HUD_TEXT_COLOR, center_aligned=False, right_aligned=False)
        
        if hasattr(player_inventory_data, 'current_load') and hasattr(player_inventory_data, 'max_capacity'):
            load_color = IMPERIAL_RED if player_inventory_data.current_load > player_inventory_data.max_capacity else HUD_TEXT_COLOR
            # For right-aligned text with draw_text, provide the right x-coordinate
            load_text_str = f"Load: {player_inventory_data.current_load}/{player_inventory_data.max_capacity}"
            text_width = FONT_MEDIUM.size(load_text_str)[0]
            draw_text(surface, load_text_str, screen_width - 30, hud_text_y_center, font=FONT_MEDIUM, color=load_color, center_aligned=False, right_aligned=True)


    if current_region_data and hasattr(current_region_data, 'name') and hasattr(current_region_data.name, 'value'): 
        # For center-aligned text with draw_text, provide center x-coordinate
        draw_text(surface, f"Region: {current_region_data.name.value}", screen_width // 2, hud_text_y_center, font=FONT_MEDIUM, color=HUD_TEXT_COLOR, center_aligned=True)


    # Draw Persistent Log Area
    log_line_height = FONT_XSMALL.get_linesize() + 2
    log_area_height = log_line_height * MAX_LOG_MESSAGES + 10 
    log_area_y_start = hud_bar_y_start - log_area_height - 5 
    log_line_x = 15
    
    log_bg_width = screen_width // 2 # Define width for the log background
    log_bg_rect = pygame.Rect(5, log_area_y_start - 5, log_bg_width, log_area_height) 
    log_bg_surface = pygame.Surface((log_bg_rect.width, log_bg_rect.height), pygame.SRCALPHA)
    log_bg_surface.fill((*OXFORD_BLUE, 180)) 
    surface.blit(log_bg_surface, log_bg_rect.topleft)
    pygame.draw.rect(surface, YALE_BLUE, log_bg_rect, 1) 

    current_log_y = log_area_y_start 
    for msg in ui_log_messages: # Display top-down
        # The draw_text in ui_theme.py handles basic word wrapping if max_width is given
        draw_text(surface, msg, log_line_x, current_log_y, 
                  font=FONT_XSMALL, color=PLATINUM, max_width=log_bg_width - 10) 
        current_log_y += log_line_height # Move to next line for next message

# Example usage (for testing this module standalone, if needed):
# Define SCREEN_WIDTH if running standalone for the log_line_max_width_approx in add_message_to_log
SCREEN_WIDTH = 1024 
if __name__ == '__main__':
    pygame.init()
    screen_height_test = 768
    screen_test = pygame.display.set_mode((SCREEN_WIDTH, screen_height_test)) # Use global SCREEN_WIDTH
    pygame.display.set_caption("HUD Test with Log")
    clock_test = pygame.time.Clock()

    class MockPlayerInventory:
        cash = 12345.67; current_load = 25; max_capacity = 100
    class MockRegion:
        class MockRegionName: value = "Test Region Alpha"
        name = MockRegionName()
    class MockGameState: current_day = 42
    
    mock_player_inv = MockPlayerInventory(); mock_region = MockRegion(); mock_game_state = MockGameState()

    add_message_to_log("Log started. This is a slightly longer welcome message to test wrapping if it happens to be implemented effectively.")
    add_message_to_log("Day 1: A new beginning...")
    show_event_message("This is an event message that will go to the log.")

    running_test = True; msg_counter = 0
    while running_test:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running_test = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    msg_counter +=1; show_event_message(f"Another event! ({msg_counter}) This one is also a bit long to see how text behaves.")
                if event.key == pygame.K_l:
                    msg_counter +=1; add_message_to_log(f"A specific log entry. ({msg_counter})")
        
        update_hud_timers() 
        screen_test.fill(RICH_BLACK) 
        draw_hud(screen_test, mock_player_inv, mock_region, mock_game_state)
        pygame.display.flip()
        clock_test.tick(FPS)
    pygame.quit()
