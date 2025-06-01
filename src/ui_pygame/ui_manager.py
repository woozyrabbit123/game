import pygame
import sys
from typing import List, Optional, Dict, Tuple, Callable, Any

from ..core.enums import DrugName, DrugQuality, RegionName, CryptoCoin, SkillID, EventType
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..game_state import GameState
from .. import game_configs as game_configs_module # To avoid conflict if game_configs is passed as arg

from .ui_theme import (
    FONT_XLARGE, FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_XSMALL, FONT_LARGE_BOLD,
    BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_DISABLED_COLOR,
    BUTTON_TEXT_COLOR, BUTTON_DISABLED_TEXT_COLOR,
    TEXT_COLOR, TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR, TEXT_INPUT_TEXT_COLOR,
    HUD_BACKGROUND_COLOR, HUD_TEXT_COLOR, HUD_ACCENT_COLOR,
    RICH_BLACK, OXFORD_BLUE, YALE_BLUE, SILVER_LAKE_BLUE, PLATINUM, GHOST_WHITE,
    IMPERIAL_RED, EMERALD_GREEN, GOLDEN_YELLOW, NEON_BLUE, DARK_GREY, MEDIUM_GREY,
    LIGHT_GREY, VERY_LIGHT_GREY
) # Assuming ui_theme.py contains these
from .ui_components import Button # Assuming ui_components.py contains Button
from . import constants as UI_CONSTANTS # Assuming constants.py contains UI specific constants
# Import action functions that will be used by buttons.
# These will be bound to the UIManager instance or called with it as an argument later.
# For now, we might need to define placeholders or import them if they are already standalone.
# This part will be tricky and might need adjustment in the next step when integrating with app.py

# Placeholder for action functions - these will be properly connected later
def placeholder_action():
    print("Placeholder action triggered")

class UIManager:
    def __init__(self, game_state: GameState, player_inventory: PlayerInventory, game_configs: Any):
        self.game_state = game_state
        self.player_inventory = player_inventory
        self.game_configs = game_configs

        # UI State Variables (previously global in app.py)
        self.current_view: str = "main_menu"
        self.active_buttons_list: List[Button] = []

        self.main_menu_buttons: List[Button] = []
        self.market_view_buttons: List[Button] = [] # General buttons for market view (e.g. back)
        self.market_item_buttons: List[Button] = [] # Specific buy/sell buttons for each drug
        self.inventory_view_buttons: List[Button] = []
        self.travel_view_buttons: List[Button] = []
        self.tech_contact_view_buttons: List[Button] = []
        self.skills_view_buttons: List[Button] = []
        self.upgrades_view_buttons: List[Button] = []
        self.transaction_input_buttons: List[Button] = []
        self.blocking_event_popup_buttons: List[Button] = []
        self.game_over_buttons: List[Button] = []
        self.informant_view_buttons: List[Button] = []

        # Transaction State
        self.current_transaction_type: Optional[str] = None
        self.drug_for_transaction: Optional[DrugName] = None
        self.quality_for_transaction: Optional[DrugQuality] = None
        self.price_for_transaction: float = 0.0
        self.available_for_transaction: int = 0
        self.quantity_input_string: str = ""
        self.input_box_rect = pygame.Rect(
            UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.MARKET_INPUT_BOX_X_OFFSET,
            UI_CONSTANTS.MARKET_INPUT_BOX_Y_POS,
            UI_CONSTANTS.MARKET_INPUT_BOX_WIDTH,
            UI_CONSTANTS.MARKET_INPUT_BOX_HEIGHT
        ) # Assuming these constants exist

        # Tech Contact Transaction State
        self.tech_transaction_in_progress: Optional[str] = None
        self.coin_for_tech_transaction: Optional[CryptoCoin] = None
        self.tech_input_string: str = ""
        self.tech_input_box_rect = pygame.Rect(
            UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.TECH_INPUT_BOX_X_OFFSET,
            UI_CONSTANTS.TECH_INPUT_BOX_Y_POS,
            UI_CONSTANTS.TECH_INPUT_BOX_WIDTH,
            UI_CONSTANTS.TECH_INPUT_BOX_HEIGHT
        ) # Assuming these constants exist

        # Messaging State
        self.active_prompt_message: Optional[str] = None
        self.prompt_message_timer: int = 0

        # Blocking Event and Game Over State
        self.active_blocking_event_data: Optional[Dict] = None
        self.game_over_message: Optional[str] = None

        # Initialize buttons for the starting view
        self.setup_buttons_for_current_view()

    def set_active_prompt_message(self, message: str, duration_frames: int = UI_CONSTANTS.PROMPT_DURATION_FRAMES) -> None:
        self.active_prompt_message = message
        self.prompt_message_timer = duration_frames

    # --- Button Creation Helper Functions (Moved from app.py) ---
    def _create_action_button(
        self,
        text: str,
        action: Callable[..., Any], # Action can take arguments
        action_args: Optional[Tuple[Any, ...]] = None,
        x: int,
        y: int,
        width: int,
        height: int,
        font: pygame.font.Font = FONT_MEDIUM, # FONT_MEDIUM from ui_theme
        is_enabled: bool = True,
    ) -> Button:
        # If action_args are provided, wrap the action in a lambda
        final_action = action
        if action_args is not None:
            final_action = lambda: action(*action_args)

        return Button(x, y, width, height, text, final_action, is_enabled=is_enabled, font=font)

    def _create_back_button(
        self,
        action: Optional[Callable[[], None]] = None, # Make action optional
        text: str = "Back"
    ) -> Button:
        # Default action will be set in _get_active_buttons or setup_buttons_for_current_view
        # For now, use a placeholder or a generic "go to main menu" action
        final_action = action if action is not None else self.action_open_main_menu
        return Button(
            UI_CONSTANTS.SCREEN_WIDTH - UI_CONSTANTS.STD_BUTTON_WIDTH - UI_CONSTANTS.LARGE_PADDING,
            UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.STD_BUTTON_HEIGHT - UI_CONSTANTS.LARGE_PADDING,
            UI_CONSTANTS.STD_BUTTON_WIDTH,
            UI_CONSTANTS.STD_BUTTON_HEIGHT,
            text,
            final_action, # Use the resolved action
            font=FONT_SMALL, # FONT_SMALL from ui_theme
        )

    def _create_button_list_vertical(
        self,
        start_x: int,
        start_y: int,
        button_width: int,
        button_height: int,
        spacing: int,
        button_definitions: List[
            Tuple[str, Callable[..., Any], Optional[Tuple[Any, ...]], Optional[Callable[[], bool]]]
        ], # Added action_args (Optional[Tuple]) to definition
    ) -> List[Button]:
        buttons_list: List[Button] = []
        for i, (text_val, action_val, action_args_val, enabled_check_val) in enumerate(button_definitions):
            y_pos_val: int = start_y + i * (button_height + spacing)
            is_enabled_val: bool = enabled_check_val() if enabled_check_val else True

            final_action = action_val
            if action_args_val is not None:
                # Need to be careful with lambda capture in loops if action_args_val changes
                # However, here action_val and action_args_val are distinct for each button definition
                final_action = lambda av=action_val, aa=action_args_val: av(*aa)

            buttons_list.append(
                Button(
                    start_x,
                    y_pos_val,
                    button_width,
                    button_height,
                    text_val,
                    final_action,
                    is_enabled=is_enabled_val,
                    font=FONT_SMALL, # FONT_SMALL from ui_theme
                )
            )
        return buttons_list

    # --- Action Stubs (to be connected to app.py actions or refactored) ---
    # These are placeholders. They will need to call methods in the main app.py or
    # app.py will call methods in UIManager. This will be part of the integration.
    def action_open_main_menu(self) -> None:
        self.current_view = "main_menu"
        self.setup_buttons_for_current_view()

    def action_open_market(self) -> None:
        self.current_view = "market"
        self.setup_buttons_for_current_view()

    def action_open_inventory(self) -> None:
        self.current_view = "inventory"
        self.setup_buttons_for_current_view()

    def action_open_travel(self) -> None:
        self.current_view = "travel"
        self.setup_buttons_for_current_view()

    def action_open_tech_contact(self) -> None:
        self.current_view = "tech_contact"
        self.setup_buttons_for_current_view()

    def action_open_skills(self) -> None:
        self.current_view = "skills"
        self.setup_buttons_for_current_view()

    def action_open_upgrades(self) -> None:
        self.current_view = "upgrades"
        self.setup_buttons_for_current_view()

    def action_open_informant(self) -> None:
        self.current_view = "informant"
        self.setup_buttons_for_current_view()

    def action_close_blocking_event_popup(self) -> None:
        self.active_blocking_event_data = None
        self.current_view = "main_menu" # Or previous view if stored
        self.setup_buttons_for_current_view()

    def action_exit_game(self) -> None:
        pygame.quit()
        sys.exit()

    # --- Main Button Setup Logic (Moved and adapted from app.py's _get_active_buttons) ---
    def setup_buttons_for_current_view(self) -> None:
        # Clear all specific button lists first
        for btn_list in [
            self.main_menu_buttons, self.market_view_buttons, self.market_item_buttons,
            self.inventory_view_buttons, self.travel_view_buttons, self.tech_contact_view_buttons,
            self.skills_view_buttons, self.upgrades_view_buttons, self.transaction_input_buttons,
            self.blocking_event_popup_buttons, self.game_over_buttons, self.informant_view_buttons,
        ]:
            btn_list.clear()

        button_width, button_height, spacing, start_x, start_y = (
            UI_CONSTANTS.STD_BUTTON_WIDTH, UI_CONSTANTS.STD_BUTTON_HEIGHT,
            UI_CONSTANTS.STD_BUTTON_SPACING,
            UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.STD_BUTTON_WIDTH // 2,
            120, # UI_CONSTANTS.MENU_START_Y
        )

        active_list = [] # This will be the list of buttons for the current view

        if self.current_view == "game_over":
            popup_width_val = UI_CONSTANTS.SCREEN_WIDTH * UI_CONSTANTS.POPUP_WIDTH_RATIO
            popup_height_val = UI_CONSTANTS.SCREEN_HEIGHT * UI_CONSTANTS.POPUP_HEIGHT_RATIO
            btn_w_val, btn_h_val = UI_CONSTANTS.POPUP_BUTTON_WIDTH, UI_CONSTANTS.POPUP_BUTTON_HEIGHT
            popup_x_val, popup_y_val = (UI_CONSTANTS.SCREEN_WIDTH - popup_width_val) / 2, (UI_CONSTANTS.SCREEN_HEIGHT - popup_height_val) / 2
            btn_x_val, btn_y_val = (popup_x_val + (popup_width_val - btn_w_val) / 2, popup_y_val + popup_height_val - btn_h_val - UI_CONSTANTS.POPUP_BUTTON_MARGIN_Y)
            self.game_over_buttons.append(
                self._create_action_button("Exit Game", self.action_exit_game, int(btn_x_val), int(btn_y_val), btn_w_val, btn_h_val, font=FONT_MEDIUM)
            )
            active_list = self.game_over_buttons

        elif self.current_view == "main_menu":
            actions_defs: List[Tuple[str, Callable[[], None], Optional[Callable[[GameState], bool]]]] = [
                ("Market", self.action_open_market, None),
                ("Inventory", self.action_open_inventory, None),
                ("Travel", self.action_open_travel, None),
                ("Tech Contact", self.action_open_tech_contact, None),
                ("Meet Informant", self.action_open_informant, lambda gs: (gs.informant_unavailable_until_day is None or gs.current_day >= gs.informant_unavailable_until_day)),
                ("Skills", self.action_open_skills, None),
                ("Upgrades", self.action_open_upgrades, None),
            ]
            col1_count: int = UI_CONSTANTS.MAIN_MENU_COL1_COUNT
            for i, (text_val, action_val, enabled_check_func) in enumerate(actions_defs):
                col_val, row_in_col_val = (0, i) if i < col1_count else (1, i - col1_count)
                x_pos_val: int = start_x + col_val * (button_width + spacing)
                y_pos_val: int = start_y + row_in_col_val * (button_height + spacing)
                if col_val == 1 and row_in_col_val == 0: y_pos_val = start_y
                is_enabled_val: bool = enabled_check_func(self.game_state) if enabled_check_func else True
                self.main_menu_buttons.append(
                    self._create_action_button(text_val, action_val, x_pos_val, y_pos_val, button_width, button_height, is_enabled=is_enabled_val)
                )
            active_list = self.main_menu_buttons

        elif self.current_view == "blocking_event_popup":
            if self.active_blocking_event_data:
                popup_w_val = UI_CONSTANTS.SCREEN_WIDTH * UI_CONSTANTS.POPUP_WIDTH_RATIO
                popup_h_val = UI_CONSTANTS.SCREEN_HEIGHT * UI_CONSTANTS.POPUP_HEIGHT_RATIO
                popup_x_val, popup_y_val = (UI_CONSTANTS.SCREEN_WIDTH - popup_w_val) / 2, (UI_CONSTANTS.SCREEN_HEIGHT - popup_h_val) / 2
                btn_txt_val: str = self.active_blocking_event_data.get("button_text", "Continue")
                btn_w_val, btn_h_val = UI_CONSTANTS.POPUP_BUTTON_WIDTH, UI_CONSTANTS.POPUP_BUTTON_HEIGHT
                btn_x_val, btn_y_val = (popup_x_val + (popup_w_val - btn_w_val) / 2, popup_y_val + popup_h_val - btn_h_val - UI_CONSTANTS.POPUP_BUTTON_MARGIN_Y)
                self.blocking_event_popup_buttons.append(
                    self._create_action_button(btn_txt_val, self.action_close_blocking_event_popup, int(btn_x_val), int(btn_y_val), btn_w_val, btn_h_val, font=FONT_SMALL)
                )
            active_list = self.blocking_event_popup_buttons

        elif self.current_view == "market":
            self.market_view_buttons.append(self._create_back_button())
            # Market item buttons (buy/sell for each drug) will be populated by the drawing function
            # or a more specific setup method for market view, as they depend on dynamic drug data.
            # For now, self.market_item_buttons will be populated elsewhere.
            active_list = self.market_view_buttons + self.market_item_buttons

        elif self.current_view == "inventory":
            self.inventory_view_buttons.append(self._create_back_button())
            active_list = self.inventory_view_buttons

        elif self.current_view == "travel":
            # Travel buttons are dynamic based on regions, will be set up by travel view logic
            self.travel_view_buttons.append(self._create_back_button(text="Cancel Travel"))
            active_list = self.travel_view_buttons

        elif self.current_view == "informant":
            self.informant_view_buttons.append(self._create_back_button())
            # Specific informant action buttons will be added here or by the informant view logic
            active_list = self.informant_view_buttons

        elif self.current_view in ["market_buy_input", "market_sell_input"]:
            # Buttons for confirm/cancel transaction
            confirm_text = self.current_transaction_type.capitalize() if self.current_transaction_type else "Confirm"
            # These actions will need to call methods in app.py that take UIManager as arg or UIManager calls app.py
            # For now, using placeholders or direct calls if simple enough
            self.transaction_input_buttons.append(self._create_action_button(confirm_text, placeholder_action, UI_CONSTANTS.SCREEN_WIDTH // 2 - 110, UI_CONSTANTS.SCREEN_HEIGHT - 100, 100, 40))
            self.transaction_input_buttons.append(self._create_action_button("Cancel", placeholder_action, UI_CONSTANTS.SCREEN_WIDTH // 2 + 10, UI_CONSTANTS.SCREEN_HEIGHT - 100, 100, 40))
            active_list = self.transaction_input_buttons

        # Add more elif branches for tech_contact, skills, upgrades, tech_input_coin_select, tech_input_amount
        # These will also need to create their respective buttons and add them to their lists (e.g., self.tech_contact_view_buttons)
        # and then set active_list.

        else: # Default or unknown view
            self.main_menu_buttons.append(self._create_action_button("Main Menu (Default)", self.action_open_main_menu, start_x, start_y, button_width, button_height))
            active_list = self.main_menu_buttons

        self.active_buttons_list = active_list

# Add other methods from app.py that primarily manage UI state or button logic as needed.
# For example, methods to handle input for transactions, update prompt messages, etc.
