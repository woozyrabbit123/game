# ui_components.py
"""
This module provides reusable UI components for the Pygame application.

Currently, it includes a Button class, but could be expanded to include
other elements like sliders, text input_box_rect, checkboxes, etc.
"""
import pygame
from .ui_theme import (BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_DISABLED_COLOR, NEON_BLUE, # Added NEON_BLUE for pressed state
                      BUTTON_TEXT_COLOR, BUTTON_DISABLED_TEXT_COLOR, FONT_SMALL, OXFORD_BLUE, # Added OXFORD_BLUE for tooltip BG
                      draw_text) # draw_text is imported but not used by Button directly

class Button:
    """
    A simple clickable button class with visual feedback for hover and press states.

    Attributes:
        rect (pygame.Rect): The rectangular area of the button.
        text (str): The text displayed on the button.
        action (callable, optional): The function to call when the button is clicked. Defaults to None.
        is_enabled (bool): Whether the button is active and can be interacted with. Defaults to True.
        font (pygame.font.Font): The font used for the button text.
        color (tuple): The background color of the button in its normal state.
        hover_color (tuple): The background color when the mouse hovers over the button.
        disabled_color (tuple): The background color when the button is disabled.
        pressed_color (tuple): The background color when the button is pressed.
        text_color (tuple): The color of the button text in its normal state.
        disabled_text_color (tuple): The color of the button text when disabled.
        tooltip (str, optional): Text to display as a tooltip when hovering over the button. Defaults to None.
        is_hovered (bool): True if the mouse is currently hovering over the button, False otherwise.
        is_pressed (bool): True if the button is currently being pressed, False otherwise.
    """
    def __init__(self, x, y, width, height, text, action=None, is_enabled=True, font=None,
                 color=None, hover_color=None, disabled_color=None, pressed_color=None, # Added pressed_color
                 text_color=None, disabled_text_color=None, tooltip=None):
        """
        Initializes the Button object.

        Args:
            x (int): The x-coordinate of the top-left corner of the button.
            y (int): The y-coordinate of the top-left corner of the button.
            width (int): The width of the button.
            height (int): The height of the button.
            text (str): The text to display on the button.
            action (callable, optional): The function to execute when the button is clicked.
            is_enabled (bool, optional): Sets the initial enabled state of the button. Defaults to True.
            font (pygame.font.Font, optional): The font for the button text. Defaults to FONT_SMALL.
            color (tuple, optional): Background color for the normal state.
            hover_color (tuple, optional): Background color for the hover state.
            disabled_color (tuple, optional): Background color for the disabled state.
            pressed_color (tuple, optional): Background color for the pressed state. Defaults to NEON_BLUE.
            text_color (tuple, optional): Text color for the normal state.
            disabled_text_color (tuple, optional): Text color for the disabled state.
            tooltip (str, optional): Tooltip text. Defaults to None.
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.is_enabled = is_enabled
        self.font = font or FONT_SMALL 

        self.color = color or BUTTON_COLOR
        self.hover_color = hover_color or BUTTON_HOVER_COLOR
        self.disabled_color = disabled_color or BUTTON_DISABLED_COLOR
        self.pressed_color = pressed_color or NEON_BLUE # Use NEON_BLUE as default pressed color
        
        self.text_color = text_color or BUTTON_TEXT_COLOR
        self.disabled_text_color = disabled_text_color or BUTTON_DISABLED_TEXT_COLOR
        
        self.tooltip = tooltip
        self.is_hovered = False
        self.is_pressed = False # New attribute for pressed state
    
    def draw(self, surface, mouse_pos):
        """
        Draws the button on the given surface.

        It changes the button's appearance based on its state (normal, hovered,
        pressed, disabled) and displays a tooltip if available and hovered.

        Args:
            surface (pygame.Surface): The Pygame surface to draw the button on.
            mouse_pos (tuple): The current (x, y) position of the mouse cursor.
        """
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.is_enabled

        current_bg_color = self.color
        current_text_color = self.text_color

        # Determine background and text color based on button state
        if not self.is_enabled:
            current_bg_color = self.disabled_color
            current_text_color = self.disabled_text_color
        elif self.is_pressed:
            current_bg_color = self.pressed_color
        elif self.is_hovered:
            current_bg_color = self.hover_color
        
        # Draw button shadow (if enabled and not pressed)
        if self.is_enabled and not self.is_pressed:
            shadow_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2, self.rect.width, self.rect.height)
            pygame.draw.rect(surface, (10, 10, 15), shadow_rect, border_radius=5) # Dark shadow color
        
        # Draw the main button rectangle
        pygame.draw.rect(surface, current_bg_color, self.rect, border_radius=5)
        
        # Draw button border
        border_color = self.hover_color if self.is_enabled else self.disabled_color 
        if self.is_pressed and self.is_enabled: 
            border_color = self.color # Use normal color for border when pressed for contrast
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=5) # Outer border
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=3) # Inner border for slight 3D effect


        # Render and blit the button text
        if self.text != '':
            text_surface = self.font.render(self.text, True, current_text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            if self.is_pressed and self.is_enabled: # Optional: offset text slightly when pressed
                 text_rect.move_ip(1, 1)
            surface.blit(text_surface, text_rect)

        # Render and blit the tooltip if hovered and tooltip text exists
        if self.is_hovered and self.tooltip:
            tooltip_font = FONT_SMALL
            tooltip_text_surface = tooltip_font.render(self.tooltip, True, BUTTON_TEXT_COLOR)

            # Create a slightly larger background surface for the tooltip text
            tooltip_bg_width = tooltip_text_surface.get_width() + 10 
            tooltip_bg_height = tooltip_text_surface.get_height() + 6
            tooltip_bg_surface = pygame.Surface((tooltip_bg_width, tooltip_bg_height), pygame.SRCALPHA) # SRCAplha for transparency
            tooltip_bg_surface.fill((*OXFORD_BLUE, 220)) # Semi-transparent background
            
            # Center the text on the tooltip background
            text_x_in_bg = (tooltip_bg_width - tooltip_text_surface.get_width()) // 2
            text_y_in_bg = (tooltip_bg_height - tooltip_text_surface.get_height()) // 2
            tooltip_bg_surface.blit(tooltip_text_surface, (text_x_in_bg, text_y_in_bg))

            # Position tooltip near the cursor
            tooltip_final_rect = tooltip_bg_surface.get_rect()
            tooltip_final_rect.topleft = (mouse_pos[0] + 15, mouse_pos[1] + 20) 
            
            # Ensure tooltip stays within screen boundaries
            screen_rect = surface.get_rect()
            if tooltip_final_rect.right > screen_rect.right:
                tooltip_final_rect.right = screen_rect.right - 5
            if tooltip_final_rect.bottom > screen_rect.bottom:
                tooltip_final_rect.bottom = screen_rect.bottom - 5
                
            surface.blit(tooltip_bg_surface, tooltip_final_rect)


    def handle_event(self, event):
        """
        Handles mouse events for the button.

        Checks for mouse button down and up events to trigger the button's action
        and update its pressed state.

        Args:
            event (pygame.event.Event): The Pygame event to process.

        Returns:
            bool: True if the event was handled by this button (i.e., a click occurred),
                  False otherwise.
        """
        if not self.is_enabled:
            return False # Button is disabled, so it cannot handle events

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered: # Left mouse button clicked while hovered
                self.is_pressed = True
                if self.action:
                    self.action() # Execute the button's action
                return True # Event was handled (button click)
        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Left mouse button released
                # The action is typically called on MOUSEBUTTONDOWN.
                # If the action were to be called on MOUSEBUTTONUP (on click release),
                # it would be here, potentially with an additional check:
                # if self.is_pressed and self.is_hovered and self.action:
                #    self.action()
                self.is_pressed = False # Release the pressed state
                # Optionally, could return True here if self.is_hovered to indicate the click completed on this button
        
        return False # Event not handled in a way that consumes it from further processing
