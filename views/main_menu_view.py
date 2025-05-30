# views/main_menu_view.py
"""
Handles drawing the Main Menu view.
"""
import pygame
from typing import List

from ui_theme import FONT_LARGE, YALE_BLUE, draw_text
from ui_components import Button

# Constants from pygame_ui.py, consider moving to a shared constants file or passing them
SCREEN_WIDTH = 1024 
# main_menu_buttons is a global in pygame_ui.py, passed here for drawing
# This highlights coupling that might be addressed in a deeper refactor.

def draw_main_menu(surface: pygame.Surface, buttons: List[Button]):
    """
    Draws the main menu.
    'buttons' is the list of main_menu_buttons from pygame_ui.py.
    """
    draw_text(surface, "Main Menu", SCREEN_WIDTH // 2, 50, font=FONT_LARGE, color=YALE_BLUE, center_aligned=True)
    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.draw(surface, mouse_pos)
