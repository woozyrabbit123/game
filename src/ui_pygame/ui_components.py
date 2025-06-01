# ui_components.py
"""
This module provides reusable UI components for the Pygame application.

Currently, it includes a Button class, but could be expanded to include
other elements like sliders, text input_box_rect, checkboxes, etc.
"""
from typing import Optional, Callable, Tuple  # For type hinting
import pygame
from .ui_theme import (
    BUTTON_COLOR,
    BUTTON_HOVER_COLOR,
    BUTTON_DISABLED_COLOR,
    NEON_BLUE,
    BUTTON_TEXT_COLOR,
    BUTTON_DISABLED_TEXT_COLOR,
    FONT_SMALL,
    OXFORD_BLUE,
    draw_text as draw_text_theme_func,
)  # Renamed to avoid conflict


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

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        action: Optional[Callable[[], None]] = None,
        is_enabled: bool = True,
        font: Optional[pygame.font.Font] = None,
        color: Optional[Tuple[int, int, int]] = None,
        hover_color: Optional[Tuple[int, int, int]] = None,
        disabled_color: Optional[Tuple[int, int, int]] = None,
        pressed_color: Optional[Tuple[int, int, int]] = None,
        text_color: Optional[Tuple[int, int, int]] = None,
        disabled_text_color: Optional[Tuple[int, int, int]] = None,
        tooltip: Optional[str] = None,
    ) -> None:
        """
        Initializes the Button object.

        Args:
            x (int): The x-coordinate of the top-left corner of the button.
            y (int): The y-coordinate of the top-left corner of the button.
            width (int): The width of the button.
            height (int): The height of the button.
            text (str): The text to display on the button.
            action (Callable[[], None], optional): The function to execute when the button is clicked.
            is_enabled (bool, optional): Sets the initial enabled state of the button. Defaults to True.
            font (pygame.font.Font, optional): The font for the button text. Defaults to FONT_SMALL.
            color (Tuple[int, int, int], optional): Background color for the normal state.
            hover_color (Tuple[int, int, int], optional): Background color for the hover state.
            disabled_color (Tuple[int, int, int], optional): Background color for the disabled state.
            pressed_color (Tuple[int, int, int], optional): Background color for the pressed state. Defaults to NEON_BLUE.
            text_color (Tuple[int, int, int], optional): Text color for the normal state.
            disabled_text_color (Tuple[int, int, int], optional): Text color for the disabled state.
            tooltip (str, optional): Tooltip text. Defaults to None.
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.action: Optional[Callable[[], None]] = action
        self.is_enabled: bool = is_enabled
        self.font: pygame.font.Font = font or FONT_SMALL

        self.color: Tuple[int, int, int] = color or BUTTON_COLOR
        self.hover_color: Tuple[int, int, int] = hover_color or BUTTON_HOVER_COLOR
        self.disabled_color: Tuple[int, int, int] = (
            disabled_color or BUTTON_DISABLED_COLOR
        )
        self.pressed_color: Tuple[int, int, int] = pressed_color or NEON_BLUE

        self.text_color: Tuple[int, int, int] = text_color or BUTTON_TEXT_COLOR
        self.disabled_text_color: Tuple[int, int, int] = (
            disabled_text_color or BUTTON_DISABLED_TEXT_COLOR
        )

        self.tooltip: Optional[str] = tooltip
        self.is_hovered: bool = False
        self.is_pressed: bool = False

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """
        Draws the button on the given surface.

        It changes the button's appearance based on its state (normal, hovered,
        pressed, disabled) and displays a tooltip if available and hovered.

        Args:
            surface (pygame.Surface): The Pygame surface to draw the button on.
            mouse_pos (tuple): The current (x, y) position of the mouse cursor.
        """
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.is_enabled

        current_bg_color: Tuple[int, int, int] = self.color
        current_text_color: Tuple[int, int, int] = self.text_color

        if not self.is_enabled:
            current_bg_color = self.disabled_color
            current_text_color = self.disabled_text_color
        elif self.is_pressed:
            current_bg_color = self.pressed_color
        elif self.is_hovered:
            current_bg_color = self.hover_color

        if self.is_enabled and not self.is_pressed:
            shadow_rect: pygame.Rect = self.rect.move(2, 2)
            pygame.draw.rect(surface, (10, 10, 15), shadow_rect, border_radius=5)

        pygame.draw.rect(surface, current_bg_color, self.rect, border_radius=5)

        border_color_val: Tuple[int, int, int] = (
            self.hover_color if self.is_enabled else self.disabled_color
        )
        if self.is_pressed and self.is_enabled:
            border_color_val = self.color
        pygame.draw.rect(surface, border_color_val, self.rect, 2, border_radius=5)
        pygame.draw.rect(surface, border_color_val, self.rect, 1, border_radius=3)

        if self.text != "":
            text_surface_render: pygame.Surface = self.font.render(
                self.text, True, current_text_color
            )
            text_rect_render: pygame.Rect = text_surface_render.get_rect(
                center=self.rect.center
            )
            if self.is_pressed and self.is_enabled:
                text_rect_render.move_ip(1, 1)
            surface.blit(text_surface_render, text_rect_render)

        if self.is_hovered and self.tooltip:
            tooltip_font_render: pygame.font.Font = (
                FONT_SMALL  # Assuming FONT_SMALL is a loaded font
            )
            tooltip_text_surface_render: pygame.Surface = tooltip_font_render.render(
                self.tooltip, True, BUTTON_TEXT_COLOR
            )

            tooltip_bg_width_val: int = tooltip_text_surface_render.get_width() + 10
            tooltip_bg_height_val: int = tooltip_text_surface_render.get_height() + 6
            tooltip_bg_surface_render: pygame.Surface = pygame.Surface(
                (tooltip_bg_width_val, tooltip_bg_height_val), pygame.SRCALPHA
            )
            tooltip_bg_surface_render.fill((*OXFORD_BLUE, 220))

            text_x_in_bg_val: int = (
                tooltip_bg_width_val - tooltip_text_surface_render.get_width()
            ) // 2
            text_y_in_bg_val: int = (
                tooltip_bg_height_val - tooltip_text_surface_render.get_height()
            ) // 2
            tooltip_bg_surface_render.blit(
                tooltip_text_surface_render, (text_x_in_bg_val, text_y_in_bg_val)
            )

            tooltip_final_rect_render: pygame.Rect = (
                tooltip_bg_surface_render.get_rect()
            )
            tooltip_final_rect_render.topleft = (mouse_pos[0] + 15, mouse_pos[1] + 20)

            screen_rect_render: pygame.Rect = surface.get_rect()
            tooltip_final_rect_render.clamp_ip(
                screen_rect_render
            )  # Use clamp_ip to keep it within screen

            surface.blit(tooltip_bg_surface_render, tooltip_final_rect_render)

    def handle_event(self, event: pygame.event.Event) -> bool:
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
            return False  # Button is disabled, so it cannot handle events

        if event.type == pygame.MOUSEBUTTONDOWN:
            if (
                event.button == 1 and self.is_hovered
            ):  # Left mouse button clicked while hovered
                self.is_pressed = True
                if self.action:
                    self.action()  # Execute the button's action
                return True  # Event was handled (button click)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button released
                # The action is typically called on MOUSEBUTTONDOWN.
                # If the action were to be called on MOUSEBUTTONUP (on click release),
                # it would be here, potentially with an additional check:
                # if self.is_pressed and self.is_hovered and self.action:
                #    self.action()
                self.is_pressed = False  # Release the pressed state
                # Optionally, could return True here if self.is_hovered to indicate the click completed on this button

        return (
            False  # Event not handled in a way that consumes it from further processing
        )
