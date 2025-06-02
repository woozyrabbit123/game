import unittest
from unittest.mock import MagicMock, patch, ANY

import pygame # Import pygame to allow specing Surface and for Rect
# Import the module to be tested
from src.ui_pygame import ui_base_elements
# Import ui_theme to access constants like fonts and colors used by base elements
from src.ui_pygame import ui_theme 
from src.ui_pygame import constants as UI_CONSTANTS


class TestUIBaseElements(unittest.TestCase):

    def setUp(self):
        # Create a mock surface for all tests
        self.mock_surface = MagicMock(spec=pygame.Surface)
        # Mock fonts that are directly used or passed to draw_text
        # If draw_text itself loads fonts, that would need deeper mocking or a real font.
        # Assuming FONT_LARGE, FONT_MEDIUM etc. are valid pygame.font.Font objects
        # For unit tests, we often just need to ensure they are passed correctly.
        ui_theme.FONT_LARGE = MagicMock(spec=pygame.font.Font)
        ui_theme.FONT_MEDIUM = MagicMock(spec=pygame.font.Font)
        ui_theme.FONT_MEDIUM_BOLD = MagicMock(spec=pygame.font.Font)
        ui_theme.FONT_SMALL = MagicMock(spec=pygame.font.Font)


    @patch('pygame.Surface.fill')
    def test_draw_view_background(self, mock_surface_fill):
        ui_base_elements.draw_view_background(self.mock_surface)
        mock_surface_fill.assert_called_once_with((5, 15, 30)) # Default color

        custom_color = (10, 20, 40)
        ui_base_elements.draw_view_background(self.mock_surface, color=custom_color)
        self.mock_surface.fill.assert_called_with(custom_color)


    @patch('pygame.draw.rect')
    def test_draw_main_container(self, mock_pygame_draw_rect):
        container_rect = ui_base_elements.draw_main_container(self.mock_surface)
        
        self.assertTrue(mock_pygame_draw_rect.called)
        self.assertEqual(mock_pygame_draw_rect.call_count, 2) # One for fill, one for border
        
        expected_rect = pygame.Rect(20, 20, UI_CONSTANTS.SCREEN_WIDTH - 40, UI_CONSTANTS.SCREEN_HEIGHT - 40)
        # Check if a rect similar to expected_rect was drawn.
        # The exact rect object might differ, so check properties or use ANY for rect arg.
        # Example: mock_pygame_draw_rect.assert_any_call(self.mock_surface, ANY, expected_rect, ANY)
        # For simplicity, just checking call count is often enough for this level of test.
        self.assertIsInstance(container_rect, pygame.Rect)
        self.assertEqual(container_rect, expected_rect)


    @patch('pygame.draw.rect')
    @patch('src.ui_pygame.ui_theme.draw_text') # Mocking our own draw_text
    def test_draw_view_title(self, mock_draw_text_internal, mock_pygame_draw_rect):
        title_text = "Test Title"
        title_rect = ui_base_elements.draw_view_title(self.mock_surface, title_text)

        self.assertTrue(mock_pygame_draw_rect.called)
        self.assertEqual(mock_pygame_draw_rect.call_count, 2)
        
        mock_draw_text_internal.assert_called_once_with(
            self.mock_surface,
            title_text.upper(),
            ANY, # Center X
            ANY, # Center Y
            font=ui_theme.FONT_LARGE,
            color=ui_theme.GOLDEN_YELLOW,
            center_aligned=True
        )
        self.assertIsInstance(title_rect, pygame.Rect)


    @patch('pygame.draw.rect')
    @patch('src.ui_pygame.ui_theme.draw_text')
    def test_draw_resource_bar(self, mock_draw_text_internal, mock_pygame_draw_rect):
        resource_text = "Cash: $1000"
        y_offset = 100
        bar_rect = ui_base_elements.draw_resource_bar(self.mock_surface, resource_text, y_offset)

        self.assertTrue(mock_pygame_draw_rect.called)
        self.assertEqual(mock_pygame_draw_rect.call_count, 2)
        
        mock_draw_text_internal.assert_called_once_with(
            self.mock_surface,
            resource_text,
            ANY, # Center X
            ANY, # Center Y
            font=ui_theme.FONT_MEDIUM_BOLD,
            color=ui_theme.GOLDEN_YELLOW,
            center_aligned=True
        )
        self.assertIsInstance(bar_rect, pygame.Rect)

    @patch('pygame.draw.rect')
    @patch('src.ui_pygame.ui_theme.draw_text')
    def test_draw_missing_definitions_error(self, mock_draw_text_internal, mock_pygame_draw_rect):
        definition_name = "SKILL_DEFINITIONS"
        y_offset = 150
        error_rect = ui_base_elements.draw_missing_definitions_error(self.mock_surface, definition_name, y_offset)

        self.assertTrue(mock_pygame_draw_rect.called)
        self.assertEqual(mock_pygame_draw_rect.call_count, 2)
        
        mock_draw_text_internal.assert_called_once_with(
            self.mock_surface,
            f"{definition_name.upper()} missing or empty!",
            ANY, # Center X
            ANY, # Center Y
            font=ui_theme.FONT_MEDIUM,
            color=ui_theme.IMPERIAL_RED,
            center_aligned=True
        )
        self.assertIsInstance(error_rect, pygame.Rect)

    @patch('pygame.draw.rect')
    def test_draw_content_panel(self, mock_pygame_draw_rect):
        y_offset = 200
        height = 300
        panel_rect = ui_base_elements.draw_content_panel(self.mock_surface, y_offset, height)

        self.assertTrue(mock_pygame_draw_rect.called)
        self.assertEqual(mock_pygame_draw_rect.call_count, 2)
        self.assertIsInstance(panel_rect, pygame.Rect)
        self.assertEqual(panel_rect.y, y_offset)
        self.assertEqual(panel_rect.height, height)


    @patch('pygame.draw.rect')
    @patch('src.ui_pygame.ui_theme.draw_text')
    def test_draw_panel_header(self, mock_draw_text_internal, mock_pygame_draw_rect):
        header_text = "Panel Header"
        y_offset = 250
        header_rect = ui_base_elements.draw_panel_header(self.mock_surface, header_text, y_offset)
        
        self.assertTrue(mock_pygame_draw_rect.called)
        self.assertEqual(mock_pygame_draw_rect.call_count, 2)
        
        mock_draw_text_internal.assert_called_once_with(
            self.mock_surface,
            header_text.upper(),
            ANY, # Center X
            ANY, # Center Y
            font=ui_theme.FONT_MEDIUM,
            color=ui_theme.PLATINUM,
            center_aligned=True
        )
        self.assertIsInstance(header_rect, pygame.Rect)

    @patch('src.ui_pygame.ui_theme.draw_text')
    def test_draw_column_headers(self, mock_draw_text_internal):
        headers_config = [
            {"text": "Header1", "x": 50, "color": ui_theme.PLATINUM},
            {"text": "Header2", "x": 150}, # Test default color
        ]
        y_pos = 300
        ui_base_elements.draw_column_headers(self.mock_surface, headers_config, y_pos)

        self.assertEqual(mock_draw_text_internal.call_count, 2)
        mock_draw_text_internal.assert_any_call(
            self.mock_surface, "Header1", 50, y_pos, font=ui_theme.FONT_MEDIUM, color=ui_theme.PLATINUM, center_aligned=False
        )
        mock_draw_text_internal.assert_any_call(
            self.mock_surface, "Header2", 150, y_pos, font=ui_theme.FONT_MEDIUM, color=ui_theme.PLATINUM, center_aligned=False
        )


if __name__ == '__main__':
    unittest.main()
[end of tests/ui_pygame/test_ui_base_elements.py]
