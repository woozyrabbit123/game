# ui_components.py
"""
Contains reusable UI components like Buttons.
"""
import pygame
from ui_theme import (BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_DISABLED_COLOR, NEON_BLUE, # Added NEON_BLUE for pressed state
                      BUTTON_TEXT_COLOR, BUTTON_DISABLED_TEXT_COLOR, FONT_SMALL, OXFORD_BLUE, # Added OXFORD_BLUE for tooltip BG
                      draw_text) # draw_text is imported but not used by Button directly

class Button:
    """Simple clickable button class with visual feedback for press."""
    def __init__(self, x, y, width, height, text, action=None, is_enabled=True, font=None,
                 color=None, hover_color=None, disabled_color=None, pressed_color=None, # Added pressed_color
                 text_color=None, disabled_text_color=None, tooltip=None):
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
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.is_enabled

        current_bg_color = self.color
        current_text_color = self.text_color

        if not self.is_enabled:
            current_bg_color = self.disabled_color
            current_text_color = self.disabled_text_color
        elif self.is_pressed: # Check before is_hovered
            current_bg_color = self.pressed_color
            # Text color could also change when pressed, e.g., self.text_color or a specific pressed_text_color
        elif self.is_hovered:
            current_bg_color = self.hover_color
        
        pygame.draw.rect(surface, current_bg_color, self.rect, border_radius=3) # Added slight border_radius
        # Simple border, color could depend on state too
        border_color = self.hover_color if self.is_enabled else self.disabled_color 
        if self.is_pressed and self.is_enabled : border_color = self.color # Example: Invert border on press
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=3)


        if self.text != '':
            text_surface = self.font.render(self.text, True, current_text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            if self.is_pressed and self.is_enabled: # Optional: text offset for pressed feel
                 text_rect.move_ip(1, 1)
            surface.blit(text_surface, text_rect)

        if self.is_hovered and self.tooltip:
            tooltip_font = FONT_SMALL # Or a dedicated FONT_XSMALL for tooltips
            # Basic tooltip rendering
            tooltip_text_surface = tooltip_font.render(self.tooltip, True, BUTTON_TEXT_COLOR) # White text
            # Get width of text to add padding for background
            tooltip_bg_width = tooltip_text_surface.get_width() + 10 
            tooltip_bg_height = tooltip_text_surface.get_height() + 6
            
            tooltip_bg_surface = pygame.Surface((tooltip_bg_width, tooltip_bg_height), pygame.SRCALPHA)
            tooltip_bg_surface.fill((*OXFORD_BLUE, 220)) # Semi-transparent dark blue background
            
            text_x_in_bg = (tooltip_bg_width - tooltip_text_surface.get_width()) // 2
            text_y_in_bg = (tooltip_bg_height - tooltip_text_surface.get_height()) // 2
            tooltip_bg_surface.blit(tooltip_text_surface, (text_x_in_bg, text_y_in_bg))

            # Position tooltip near cursor
            tooltip_final_rect = tooltip_bg_surface.get_rect()
            tooltip_final_rect.topleft = (mouse_pos[0] + 15, mouse_pos[1] + 20) 
            
            # Ensure tooltip doesn't go off-screen (simple check)
            screen_rect = surface.get_rect()
            if tooltip_final_rect.right > screen_rect.right:
                tooltip_final_rect.right = screen_rect.right - 5
            if tooltip_final_rect.bottom > screen_rect.bottom:
                tooltip_final_rect.bottom = screen_rect.bottom - 5
                
            surface.blit(tooltip_bg_surface, tooltip_final_rect)


    def handle_event(self, event):
        if not self.is_enabled:
            return False # Ignore events if disabled

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
                if self.action:
                    self.action() 
                    # Note: Action is called on MOUSEBUTTONDOWN. 
                    # If action causes view change, button might not show pressed state if not redrawn before next event cycle.
                return True 
        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                # Action is typically called on MOUSEBUTTONDOWN. 
                # If it were on MOUSEBUTTONUP, it would be here:
                # if self.is_pressed and self.is_hovered and self.action: # Check is_hovered for action on UP
                #    self.action()
                self.is_pressed = False # Always release pressed state on mouse up
                # if self.is_hovered: return True # Optional: consume event if it was a click on this button
        
        # Update hover state based on current mouse position (usually done in draw, but can be here too)
        # self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos()) and self.is_enabled
        # However, mouse_pos is passed to draw, so is_hovered is updated there.

        return False # Event not handled by this button in a way that stops further processing / requires immediate redraw
