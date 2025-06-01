"""
Constants for the Textual UI.

This module defines constants used for layout, styling (that isn't in CSS),
or other fixed values specific to the Textual version of the UI.
"""

# Dialog Dimensions
DIALOG_WIDTH: int = 60
# DIALOG_HEIGHT: int = 10 # Example, not currently used by multiple dialogs with fixed height

# Padding and Margins
STANDARD_PADDING: int = 1 # For general purpose padding (e.g., padding: 1 0, margin-bottom: 1)
DIALOG_BORDER_PADDING: int = 2 # For dialog content area (e.g., padding: 2)
BUTTON_MARGIN_LEFT: int = 1 # For buttons in horizontal layouts

# Input specific
INPUT_WIDTH_PERCENT: int = 100 # For width: 100%

# Example for log lines if a log widget has a fixed line count
# MAX_LOG_LINES = 100

# Example for input placeholder if it were globally consistent and not context-dependent
# DEFAULT_INPUT_PLACEHOLDER = "Enter command..."
