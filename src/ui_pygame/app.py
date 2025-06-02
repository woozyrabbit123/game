"""
This module implements the main application logic for the Pygame UI.

It includes functions for managing game state, handling user input,
and rendering the user interface.
"""

import pygame
import sys
from src.utils.logger import get_logger
from .ui_manager import UIManager
import functools  # For partial functions
import random  # For police stop simulation
import math  # Added for math.ceil
from typing import Optional, Dict, List, Tuple, Callable, Any  # For type hinting

from ..core.enums import (
    DrugName,
    DrugQuality,
    RegionName,
    CryptoCoin,
    SkillID,
    EventType,
)
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..core.market_event import MarketEvent  # Added for isinstance checks
from ..game_state import GameState  # Added GameState import
from ..mechanics import market_impact, event_manager
from ..mechanics.encounter_mechanics import calculate_police_encounter_chance # Import new function
from src import narco_configs as game_configs_module # To access game_configs directly for MUGGING_EVENT_CHANCE

from .ui_theme import (
    RICH_BLACK,
    OXFORD_BLUE,
    YALE_BLUE,
    SILVER_LAKE_BLUE,
    PLATINUM,
    GHOST_WHITE,
    IMPERIAL_RED,
    EMERALD_GREEN,
    GOLDEN_YELLOW,
    NEON_BLUE,
    DARK_GREY,
    MEDIUM_GREY,
    LIGHT_GREY,
    VERY_LIGHT_GREY,
    BUTTON_COLOR,
    BUTTON_HOVER_COLOR,
    BUTTON_DISABLED_COLOR,
    BUTTON_TEXT_COLOR,
    BUTTON_DISABLED_TEXT_COLOR,
    TEXT_COLOR,
    TEXT_INPUT_BG_COLOR,
    TEXT_INPUT_BORDER_COLOR,
    TEXT_INPUT_TEXT_COLOR,
    HUD_BACKGROUND_COLOR,
    HUD_TEXT_COLOR,
    HUD_ACCENT_COLOR,
    FONT_XLARGE,
    FONT_LARGE,
    FONT_MEDIUM,
    FONT_SMALL,
    FONT_XSMALL,
    FONT_LARGE_BOLD,
    draw_text,
    draw_panel,
    draw_input_box,
)
# from .ui_components import Button # No longer directly used in app.py
from .ui_hud import (
    draw_hud as draw_hud_external,
    show_event_message as show_event_message_external,
    update_hud_timers as update_hud_timers_external,
    add_message_to_log,
)
from .views.main_menu_view import draw_main_menu as draw_main_menu_external
from .views.market_view import (
    draw_market_view as draw_market_view_external,
    draw_transaction_input_view as draw_transaction_input_view_external,
)
from .views.inventory_view import draw_inventory_view as draw_inventory_view_external
from .views.travel_view import draw_travel_view as draw_travel_view_external
from .views.tech_contact_view import (
    draw_tech_contact_view as draw_tech_contact_view_external,
)
from .views.skills_view import draw_skills_view as draw_skills_view_external
from .views.upgrades_view import draw_upgrades_view as draw_upgrades_view_external
from .views.blocking_event_popup_view import (
    draw_blocking_event_popup as draw_blocking_event_popup_external,
)
from .views.game_over_view import draw_game_over_view as draw_game_over_view_external
from .views.informant_view import draw_informant_view as draw_informant_view_external
from . import constants as UI_CONSTANTS # Import the new UI constants module


# --- Constants ---
# Values are now in ui_pygame.constants

logger = get_logger(__name__)

# --- Pygame Setup (Screen, Clock) ---
pygame.font.init()
pygame.init()
screen = pygame.display.set_mode((UI_CONSTANTS.SCREEN_WIDTH, UI_CONSTANTS.SCREEN_HEIGHT))
pygame.display.set_caption("Project Narco-Syndicate")
clock = pygame.time.Clock()

# --- Game State & UI Variables ---
# These are now managed by UIManager instance
# current_view: str = "main_menu"
# main_menu_buttons: List[Button] = []
# market_view_buttons: List[Button] = []
# market_buy_sell_buttons: List[Button] = []
# inventory_view_buttons: List[Button] = []
# travel_view_buttons: List[Button] = []
# tech_contact_view_buttons: List[Button] = []
# skills_view_buttons: List[Button] = []
# upgrades_view_buttons: List[Button] = []
# transaction_input_buttons: List[Button] = []
# blocking_event_popup_buttons: List[Button] = []
# game_over_buttons: List[Button] = []
# informant_view_buttons: List[Button] = []
# active_buttons_list_current_view: List[Button] = []
#
# current_transaction_type: Optional[str] = None
# drug_for_transaction: Optional[DrugName] = None
# quality_for_transaction: Optional[DrugQuality] = None
# price_for_transaction: float = 0.0
# available_for_transaction: int = 0
# quantity_input_string: str = ""
# input_box_rect = pygame.Rect(
#     UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.MARKET_INPUT_BOX_X_OFFSET,
#     UI_CONSTANTS.MARKET_INPUT_BOX_Y_POS,
#     UI_CONSTANTS.MARKET_INPUT_BOX_WIDTH,
#     UI_CONSTANTS.MARKET_INPUT_BOX_HEIGHT
# )
#
# tech_transaction_in_progress: Optional[str] = None
# coin_for_tech_transaction: Optional[CryptoCoin] = None
# tech_input_string: str = ""
# tech_input_box_rect = pygame.Rect(
#     UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.TECH_INPUT_BOX_X_OFFSET,
#     UI_CONSTANTS.TECH_INPUT_BOX_Y_POS,
#     UI_CONSTANTS.TECH_INPUT_BOX_WIDTH,
#     UI_CONSTANTS.TECH_INPUT_BOX_HEIGHT
# )
#
# active_prompt_message: Optional[str] = None
# prompt_message_timer: int = 0
#
# active_blocking_event_data: Optional[Dict] = None
# game_over_message: Optional[str] = None

# Cached game data (still needed globally in app.py for actions to access)
game_state_data_cache: Optional[GameState] = None
game_configs_data_cache: Optional[Any] = None
player_inventory_cache: Optional[PlayerInventory] = None

# UIManager instance will be created in game_loop
ui_manager: Optional[UIManager] = None

# Import the new daily updates function
from ..mechanics.daily_updates import perform_daily_updates as perform_daily_updates_mechanics, DailyUpdateResult


# --- Action Functions (Callbacks for buttons) ---
# These functions will now primarily call methods on the ui_manager instance
# or perform game logic and then update ui_manager state.

def action_open_main_menu() -> None:
    ui_manager.action_open_main_menu()

def action_open_market() -> None:
    ui_manager.action_open_market()

def action_open_inventory() -> None:
    ui_manager.action_open_inventory()

def action_open_travel() -> None:
    ui_manager.action_open_travel()

def action_open_tech_contact() -> None:
    ui_manager.action_open_tech_contact()

def action_open_skills() -> None:
    ui_manager.action_open_skills()

def action_open_upgrades() -> None:
    ui_manager.action_open_upgrades()

def action_open_informant() -> None:
    ui_manager.action_open_informant()

def action_close_blocking_event_popup() -> None:
    ui_manager.action_close_blocking_event_popup()

def action_travel_to_region(
    destination_region: Region,
    player_inv: PlayerInventory, # Should be player_inventory_cache
    game_state_instance: GameState, # Should be game_state_data_cache
) -> None:
    # Use ui_manager for game_over_message, active_blocking_event_data, current_view
    if ui_manager.game_over_message is not None:
        return
    add_message_to_log(
        f"Attempting to travel to {destination_region.name.value}."
    )
    # original_day_before_travel: int = game_state_data_cache.current_day # Store before incrementing

    game_state_data_cache.set_current_player_region(destination_region.name)
    game_state_data_cache.current_day += 1
    add_message_to_log(f"Advanced day to {game_state_data_cache.current_day}.")

    # Call the new perform_daily_updates from mechanics
    daily_result: DailyUpdateResult = perform_daily_updates_mechanics(
        game_state_data_cache,
        player_inventory_cache,
        game_configs_data_cache
    )

    # Process results from daily_updates
    for msg in daily_result.ui_messages:
        # Decide if this should be a prompt or an event message based on context
        # For now, using existing show_event_message_external for general UI messages from daily_updates
        show_event_message_external(msg)
    for msg in daily_result.log_messages:
        add_message_to_log(msg)

    if daily_result.game_over_message and not ui_manager.game_over_message:
        ui_manager.game_over_message = daily_result.game_over_message
        ui_manager.current_view = "game_over"
        # ui_manager.setup_buttons_for_current_view() will be called by the main loop check
        return # Game over, no further actions in travel

    if daily_result.blocking_event_data and not ui_manager.active_blocking_event_data:
        ui_manager.active_blocking_event_data = daily_result.blocking_event_data
        ui_manager.current_view = "blocking_event_popup"
        # ui_manager.setup_buttons_for_current_view()
        # If a blocking event occurred, often we don't proceed to police stop, etc.
        # However, the old logic had police stop after daily updates.
        # For now, let's assume a blocking event from daily_updates takes precedence.
        # If a blocking event is set, we might return here or ensure police stop doesn't also set one.
        # This might need further refinement based on desired game flow.
        # For this refactor, if daily_updates sets a blocking event, we show that.
        ui_manager.setup_buttons_for_current_view() # Ensure buttons are updated for the popup
        return


    if daily_result.pending_laundered_sc_processed:
        player_inventory_cache.pending_laundered_sc = daily_result.new_pending_laundered_sc
        player_inventory_cache.pending_laundered_sc_arrival_day = daily_result.new_pending_laundered_sc_arrival_day

    if daily_result.informant_unavailable_until_day is not None: # If daily_updates determined this
        game_state_data_cache.informant_unavailable_until_day = daily_result.informant_unavailable_until_day

    # Skill point logic is now centralized in perform_daily_updates_mechanics
    # The old skill point check in action_travel_to_region is removed.

    # Police stop logic (remains in app.py for now, after daily updates are processed)
    # Only proceed if no game over or other blocking event from daily_updates occurred.
    if ui_manager.game_over_message or ui_manager.active_blocking_event_data:
        ui_manager.setup_buttons_for_current_view() # Ensure view is correctly set up if game over/blocking event
        return

    region_heat_val: int = destination_region.current_heat # Re-fetch as it might have changed
    threshold_val: int = game_configs_data_cache.POLICE_STOP_HEAT_THRESHOLD
    base_chance_val: float = game_configs_data_cache.POLICE_STOP_BASE_CHANCE
    # per_point_increase_val: float = ( # Original calculation replaced
    #     game_configs_data_cache.POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD
    # )
    # calculated_chance_val: float = base_chance_val
    # if region_heat_val >= threshold_val:
    #     calculated_chance_val += (
    #         region_heat_val - threshold_val
    #     ) * per_point_increase_val
    # final_police_stop_chance_val: float = max(0.0, min(calculated_chance_val, game_configs_data_cache.MAX_POLICE_STOP_CHANCE))

    # Use new centralized function
    final_police_stop_chance_val = calculate_police_encounter_chance(destination_region, game_configs_data_cache)

    add_message_to_log(
        f"Police stop chance in {destination_region.name.value}: {final_police_stop_chance_val:.2f} (Heat: {region_heat_val})"
    )

    if random.random() < final_police_stop_chance_val:
        add_message_to_log("Police stop triggered.")
        show_event_message_external(
            f"Arriving in {destination_region.name.value}... flashing lights!"
        )
        stop_type_val: float = random.random()
        if stop_type_val < game_configs_data_cache.POLICE_STOP_SEVERITY_THRESHOLD_WARNING:
            ui_manager.active_blocking_event_data = { # Update ui_manager
                "title": "Police Stop!",
                "messages": [
                    f"Pulled over by {destination_region.name.value} PD.",
                    "They give you a stern look and a warning.",
                ],
                "button_text": "Continue",
            }
            add_message_to_log("Police stop: Warning.")
        elif stop_type_val < game_configs_data_cache.POLICE_STOP_SEVERITY_THRESHOLD_FINE:
            fine_val: float = min(
                player_inv.cash, # Use player_inventory_cache
                float(
                    random.randint(game_configs_data_cache.POLICE_FINE_BASE_MIN, game_configs_data_cache.POLICE_FINE_BASE_MAX)
                    * (1 + destination_region.current_heat // game_configs_data_cache.POLICE_FINE_HEAT_DIVISOR)
                ),
            )
            player_inv.cash -= fine_val # Use player_inventory_cache
            ui_manager.active_blocking_event_data = { # Update ui_manager
                "title": "Police Stop - Fine!",
                "messages": [
                    "Police stop for 'random' check.",
                    f"Minor infraction. Fined ${fine_val:,.0f}.",
                ],
                "button_text": "Pay Fine",
            }
            show_event_message_external(f"Paid fine of ${fine_val:,.0f}.")
            add_message_to_log(
                f"Police stop: Fined ${fine_val:,.0f}. Cash remaining: ${player_inv.cash:.2f}" # Use player_inventory_cache
            )
            if player_inv.cash < game_configs_data_cache.BANKRUPTCY_THRESHOLD: # Use player_inventory_cache
                ui_manager.game_over_message = "GAME OVER: A hefty fine bankrupted you!" # Update ui_manager
                add_message_to_log(f"{ui_manager.game_over_message} Cash: ${player_inv.cash:.2f}") # Use player_inventory_cache
        else:
            # Assuming player_inv.drugs is Dict[DrugName, Dict[DrugQuality, int]] like player_inv.items
            total_contraband_units_val: int = sum(
                qty
                for qualities in player_inv.items.values()
                for qty in qualities.values()
            )
            add_message_to_log(
                f"Police stop: Searched. Carrying {total_contraband_units_val} units of contraband."
            )
            if (
                total_contraband_units_val
                > game_configs_data_cache.POLICE_STOP_CONTRABAND_THRESHOLD_UNITS
                and random.random()
                < game_configs_data_cache.POLICE_STOP_CONFISCATION_CHANCE
            ):
                player_inv.items.clear() # Use player_inventory_cache
                player_inv.current_load = ( # Use player_inventory_cache
                    0  # Simplified, assumes only drugs contribute to load for this
                )
                ui_manager.active_blocking_event_data = { # Update ui_manager
                    "title": "Police Stop - Major Bust!",
                    "messages": ["Police search vehicle!", "All drugs confiscated!"],
                    "button_text": "Damn!",
                }
                add_message_to_log("Police Stop: Searched, all drugs confiscated.")
            elif total_contraband_units_val > 0:
                ui_manager.active_blocking_event_data = { # Update ui_manager
                    "title": "Police Stop - Searched!",
                    "messages": [
                        "Police search vehicle!",
                        (
                            "You had contraband, but they missed it!"
                            if total_contraband_units_val
                            > game_configs_data_cache.POLICE_STOP_CONTRABAND_THRESHOLD_UNITS
                            else "Luckily, you were clean enough."
                        ),
                    ],
                    "button_text": "Phew!",
                }
                add_message_to_log("Police stop: Searched, no major confiscation.")
            else:
                ui_manager.active_blocking_event_data = { # Update ui_manager
                    "title": "Police Stop - Searched!",
                    "messages": ["Police search vehicle!", "Luckily, you were clean."],
                    "button_text": "Phew!",
                }
                add_message_to_log("Police stop: Searched, found nothing.")
        ui_manager.current_view = "blocking_event_popup" # Update ui_manager
    else:
        show_event_message_external(
            f"Arrived safely in {destination_region.name.value}."
        )
        add_message_to_log(f"Arrived safely in {destination_region.name.value}.")
        ui_manager.current_view = "main_menu" # Update ui_manager


def action_ask_informant_rumor(
    player_inv: PlayerInventory, game_configs: Any, game_state_instance: GameState
) -> None:
    cost: float = game_configs.INFORMANT_TIP_COST_RUMOR
    if player_inv.cash >= cost:
        player_inv.cash -= cost
        player_inv.informant_trust = min(
            player_inv.informant_trust + game_configs.INFORMANT_TRUST_GAIN_PER_TIP,
            game_configs.INFORMANT_MAX_TRUST,
        )
        rumors: List[str] = [
            "Heard The Chemist is planning a big move in Downtown soon.",
            "Silas is looking for extra muscle, might be risky.",
            f"Word is, {random.choice(list(DrugName)).value} prices might spike in {random.choice(list(RegionName)).value}.",
            "Cops are cracking down in The Docks, lay low.",
            "Someone saw a new shipment of high-quality Pills arriving at Suburbia.",
        ]
        rumor: str = random.choice(rumors)
        show_event_message_external(f"Informant whispers: '{rumor}'")
        add_message_to_log(f"Paid informant ${cost:.0f} for a rumor: {rumor}")
    else:
        ui_manager.set_active_prompt_message(f"Error: Not enough cash. Need ${cost:.0f}.")
        add_message_to_log(f"Failed to buy rumor: Insufficient cash.")
    ui_manager.setup_buttons_for_current_view() # Replaces setup_buttons
    # setup_buttons(
    #     game_state_instance, # Now game_state_data_cache
    #     player_inv, # Now player_inventory_cache
    #     game_configs, # Now game_configs_data_cache
    #     game_state_instance.get_current_player_region(),
    # )


def action_ask_informant_rival_status(
    player_inv: PlayerInventory, game_configs: Any, game_state_instance: GameState
) -> None:
    cost: float = game_configs.INFORMANT_TIP_COST_RIVAL_INFO
    if player_inv.cash >= cost:
        player_inv.cash -= cost
        player_inv.informant_trust = min(
            player_inv.informant_trust + game_configs.INFORMANT_TRUST_GAIN_PER_TIP,
            game_configs.INFORMANT_MAX_TRUST,
        )
        info_parts: List[str] = []
        if game_state_instance.ai_rivals:
            active_rivals_list: List[str] = [
                r.name for r in game_state_instance.ai_rivals if not r.is_busted
            ]
            busted_rivals_list: List[str] = [
                f"{r.name}({r.busted_days_remaining}d left)"
                for r in game_state_instance.ai_rivals
                if r.is_busted
            ]
            if active_rivals_list:
                info_parts.append(f"Active: {', '.join(active_rivals_list)}.")
            else:
                info_parts.append("No active rivals on my radar.")
            if busted_rivals_list:
                info_parts.append(f"Busted: {', '.join(busted_rivals_list)}.")
        else:
            info_parts.append("No news on rivals right now.")
        final_info_str: str = " ".join(info_parts)
        show_event_message_external(f"Informant on rivals: {final_info_str}")
        add_message_to_log(
            f"Paid informant ${cost:.0f} for rival status: {final_info_str}"
        )
    else:
        ui_manager.set_active_prompt_message(f"Error: Not enough cash. Need ${cost:.0f}.")
        add_message_to_log(f"Failed to buy rival info: Insufficient cash.")
    ui_manager.setup_buttons_for_current_view()
    # setup_buttons(
    #     game_state_instance,
    #     player_inv,
    #     game_configs,
    #     game_state_instance.get_current_player_region(),
    # )

# _initiate_market_transaction is removed, UIManager handles this state internally or via direct calls

def action_initiate_buy(
    drug: DrugName, quality: DrugQuality, price: float, available: int
) -> None:
    # Directly set state on ui_manager
    ui_manager.current_view = "market_buy_input"
    ui_manager.current_transaction_type = "buy"
    ui_manager.drug_for_transaction = drug
    ui_manager.quality_for_transaction = quality
    ui_manager.price_for_transaction = price
    ui_manager.available_for_transaction = available
    ui_manager.quantity_input_string = ""
    ui_manager.set_active_prompt_message(
        f"Enter quantity to buy.", duration_frames=UI_CONSTANTS.PROMPT_DURATION_FRAMES * 2
    )
    add_message_to_log(
        f"Initiating market transaction: buy {drug.value} ({quality.name}) at ${price:.2f}, {available} available."
    )
    ui_manager.setup_buttons_for_current_view()


def action_initiate_sell(
    drug: DrugName, quality: DrugQuality, price: float, available: int
) -> None:
    # Directly set state on ui_manager
    ui_manager.current_view = "market_sell_input"
    ui_manager.current_transaction_type = "sell"
    ui_manager.drug_for_transaction = drug
    ui_manager.quality_for_transaction = quality
    ui_manager.price_for_transaction = price
    ui_manager.available_for_transaction = available
    ui_manager.quantity_input_string = ""
    ui_manager.set_active_prompt_message(
        f"Enter quantity to sell.", duration_frames=UI_CONSTANTS.PROMPT_DURATION_FRAMES * 2
    )
    add_message_to_log(
        f"Initiating market transaction: sell {drug.value} ({quality.name}) at ${price:.2f}, {available} available."
    )
    ui_manager.setup_buttons_for_current_view()


def action_confirm_transaction(
    player_inv: PlayerInventory, # Should be player_inventory_cache
    market_region: Region, # Should be from game_state_data_cache.get_current_player_region()
    game_state_instance: GameState # Should be game_state_data_cache
) -> None:
    # Use ui_manager for UI state like quantity_input_string, current_transaction_type, etc.
    original_quantity_input: str = ui_manager.quantity_input_string
    errmsg: Optional[str] = None
    if not ui_manager.quantity_input_string.isdigit():
        errmsg = "Error: Quantity must be a positive number."
    quantity: int = int(ui_manager.quantity_input_string) if ui_manager.quantity_input_string.isdigit() else 0
    if not errmsg and quantity <= 0:
        errmsg = "Error: Quantity must be a positive number."

    if errmsg:
        ui_manager.set_active_prompt_message(errmsg)
        add_message_to_log(
            f"Transaction failed: {errmsg} Input: '{original_quantity_input}'"
        )
        ui_manager.quantity_input_string = ""
        ui_manager.setup_buttons_for_current_view() # Replaces setup_buttons
        return

    # Ensure player_inv, market_region, and game_state_instance are correctly sourced
    # For this function, they are passed as arguments, ensure the calling context (button action) does this correctly.
    # Most likely, these will be player_inventory_cache, game_state_data_cache.get_current_player_region(), game_state_data_cache

    if ui_manager.current_transaction_type == "buy":
        cost: float = quantity * ui_manager.price_for_transaction

        if player_inventory_cache.process_buy_drug(ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity, cost):
            market_region.update_stock_on_buy(
                ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity
            )
            market_impact.apply_player_buy_impact(market_region, ui_manager.drug_for_transaction, quantity)
            for event_item in market_region.active_market_events:
                if (
                    event_item.event_type == EventType.BLACK_MARKET_OPPORTUNITY
                    and event_item.target_drug_name == ui_manager.drug_for_transaction # Use ui_manager
                    and event_item.target_quality == ui_manager.quality_for_transaction # Use ui_manager
                    and event_item.black_market_quantity_available is not None
                    and event_item.black_market_quantity_available > 0
                ):
                    actual_reduction: int = min(
                        quantity, event_item.black_market_quantity_available
                    )
                    event_item.black_market_quantity_available = max(
                        0, event_item.black_market_quantity_available - actual_reduction
                    )
                    add_message_to_log(
                        f"Black Market: Purchased {actual_reduction} from event stock. Remaining: {event_item.black_market_quantity_available}."
                    )
                    break
            log_msg: str = (
                f"Bought {quantity} {ui_manager.drug_for_transaction.value} ({ui_manager.quality_for_transaction.name}) for ${cost:.2f}."
            )
            show_event_message_external(log_msg)
            add_message_to_log(log_msg)
            ui_manager.action_open_market() # Change view via ui_manager
        else:
            errmsg = "Error: Transaction failed. Insufficient cash or inventory space."

    elif ui_manager.current_transaction_type == "sell":
        revenue: float = quantity * ui_manager.price_for_transaction
        # Need total_heat_val for the log message, apply_player_sell_impact should return it or it needs to be calculated before
        # For now, assuming it's handled or will be adjusted. Placeholder for heat:
        # total_heat_val = market_impact.calculate_heat_from_sale(...) # This function doesn't exist, logic is inside apply_player_sell_impact

        # The original apply_player_sell_impact did not return heat. This needs to be refactored or log message adjusted.
        # For now, let's assume the log message might need to change or heat is obtained differently.
        # This is a pre-existing issue, not directly from UIManager refactor but highlighted by it.

        if player_inventory_cache.process_sell_drug(ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity, revenue):
            market_region.update_stock_on_sell(
                ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity
            )
            # The heat generation is handled by apply_player_sell_impact. We need to get that value for the log.
            # This is a simplification for now, the actual heat should be obtained from the impact function if possible.
            region_heat_before = market_region.current_heat
            market_impact.apply_player_sell_impact(
                player_inventory_cache,
                market_region,
                ui_manager.drug_for_transaction, # Use ui_manager
                quantity,
                game_configs_data_cache,
            )
            heat_generated = market_region.current_heat - region_heat_before
            log_msg: str = (
                f"Sold {quantity} {ui_manager.drug_for_transaction.value} ({ui_manager.quality_for_transaction.name}) for ${revenue:.2f}. Heat +{heat_generated} in {market_region.name.value}."
            )
            show_event_message_external(log_msg)
            add_message_to_log(log_msg)
            ui_manager.action_open_market() # Change view via ui_manager
    if errmsg:
        ui_manager.set_active_prompt_message(errmsg)
        add_message_to_log(f"Transaction failed: {errmsg}")
    ui_manager.quantity_input_string = ""
    ui_manager.setup_buttons_for_current_view() # Replaces setup_buttons


def action_cancel_transaction() -> None:
    # Use ui_manager for UI state
    add_message_to_log(
        f"Transaction cancelled. Was type: {ui_manager.current_transaction_type or ui_manager.tech_transaction_in_progress}, View: {ui_manager.current_view}"
    )
    if ui_manager.current_view in ["market_buy_input", "market_sell_input"]:
        ui_manager.action_open_market()
    elif ui_manager.current_view in ["tech_input_coin_select", "tech_input_amount"]:
        ui_manager.action_open_tech_contact()

    ui_manager.quantity_input_string = ""
    ui_manager.tech_input_string = ""
    ui_manager.tech_transaction_in_progress = None
    ui_manager.active_prompt_message = None # Clear prompt directly or via method
    ui_manager.setup_buttons_for_current_view() # Replaces setup_buttons


def action_unlock_skill(
    skill_id: SkillID, player_inv: PlayerInventory, game_configs: Any # These should be cache versions
) -> None:
    # Use ui_manager for prompts
    if skill_id.value in player_inventory_cache.unlocked_skills:
        ui_manager.set_active_prompt_message("Skill already unlocked.")
        add_message_to_log(f"Skill unlock failed: {skill_id.value} already unlocked.")
        return
    skill_def: Optional[Dict[str, Any]] = game_configs_data_cache.SKILL_DEFINITIONS.get(skill_id)
    if not skill_def:
        ui_manager.set_active_prompt_message("Error: Skill data unavailable.")
        add_message_to_log(
            f"Skill unlock failed: Definition for {skill_id.value} not found."
        )
        return
    cost_val: int = skill_def["cost"]
    if player_inventory_cache.skill_points >= cost_val:
        player_inventory_cache.skill_points -= cost_val
        player_inventory_cache.unlocked_skills.add(skill_id.value)
        msg_val: str = f"Skill Unlocked: {skill_def['name']}"
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        ui_manager.set_active_prompt_message("Error: Not enough skill points.")
        add_message_to_log(
            f"Skill unlock failed for {skill_id.value}: Need {cost_val}, Has {player_inventory_cache.skill_points}"
        )
    if game_state_data_cache: # This check might be redundant if cache is always populated
        ui_manager.setup_buttons_for_current_view() # Replaces setup_buttons


def action_purchase_capacity_upgrade(
    player_inv: PlayerInventory, game_configs: Any # Cache versions
) -> None:
    # Use ui_manager for prompts
    upgrade_def: Optional[Dict[str, Any]] = game_configs_data_cache.UPGRADE_DEFINITIONS.get(
        "EXPANDED_CAPACITY"
    )
    if not upgrade_def:
        ui_manager.set_active_prompt_message("Error: Upgrade data unavailable.")
        add_message_to_log("Capacity upgrade failed: Definition not found.")
        return
    num_purchased_val: int = player_inventory_cache.capacity_upgrades_purchased
    costs_list: List[float] = upgrade_def["costs"]
    capacity_levels_list: List[int] = upgrade_def["capacity_levels"]
    max_levels_val: int = len(costs_list)
    if num_purchased_val >= max_levels_val:
        ui_manager.set_active_prompt_message("Capacity fully upgraded.")
        add_message_to_log("Capacity upgrade failed: Already max level.")
        return
    cost_val: float = costs_list[num_purchased_val]
    next_cap_val: int = capacity_levels_list[num_purchased_val]
    if player_inventory_cache.cash >= cost_val:
        player_inventory_cache.cash -= cost_val
        player_inventory_cache.max_capacity = next_cap_val
        player_inventory_cache.capacity_upgrades_purchased += 1
        msg_val: str = f"Capacity upgraded to {next_cap_val} units!"
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        ui_manager.set_active_prompt_message(f"Error: Not enough cash. Need ${cost_val:,.0f}.")
        add_message_to_log(
            f"Capacity upgrade failed: Need ${cost_val:,.0f}, Has ${player_inventory_cache.cash:,.0f}"
        )
    if game_state_data_cache:
        ui_manager.setup_buttons_for_current_view()


def action_purchase_secure_phone(
    player_inv: PlayerInventory, game_configs: Any # Cache versions
) -> None:
    # Use ui_manager for prompts and view changes
    if player_inventory_cache.has_secure_phone:
        ui_manager.set_active_prompt_message("Secure Phone already owned.")
        add_message_to_log("Secure phone purchase failed: Already owned.")
        return
    upgrade_def: Optional[Dict[str, Any]] = game_configs_data_cache.UPGRADE_DEFINITIONS.get(
        "SECURE_PHONE"
    )
    if not upgrade_def:
        ui_manager.set_active_prompt_message("Error: Upgrade data unavailable.")
        add_message_to_log("Secure phone purchase failed: Definition not found.")
        return
    cost_val: float = upgrade_def["cost"]
    if player_inventory_cache.cash >= cost_val:
        player_inventory_cache.cash -= cost_val
        player_inventory_cache.has_secure_phone = True
        msg_val: str = "Secure Phone purchased!"
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        ui_manager.set_active_prompt_message(f"Error: Not enough cash. Need ${cost_val:,0f}.")
        add_message_to_log(
            f"Secure phone purchase failed: Need ${cost_val:,0f}, Has ${player_inventory_cache.cash:,.0f}"
        )
    ui_manager.action_open_tech_contact() # Change view via ui_manager
    if game_state_data_cache: # This check is likely redundant
        ui_manager.setup_buttons_for_current_view()


def action_collect_staking_rewards(player_inv: PlayerInventory) -> None: # Cache version
    # Use ui_manager for prompts
    rewards_to_collect_val: float = player_inventory_cache.staked_drug_coin.get(
        "pending_rewards", 0.0
    )
    if rewards_to_collect_val > 1e-9:
        player_inventory_cache.add_crypto(CryptoCoin.DRUG_COIN, rewards_to_collect_val)
        player_inventory_cache.staked_drug_coin["pending_rewards"] = 0.0
        msg_val: str = f"Collected {rewards_to_collect_val:.4f} DC staking rewards."
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        ui_manager.set_active_prompt_message("No staking rewards to collect.")
        add_message_to_log("Collect staking rewards: No rewards available.")
    if game_state_data_cache:
        ui_manager.setup_buttons_for_current_view()


def action_initiate_tech_operation(operation_type: str) -> None:
    # Use ui_manager for state and view changes
    add_message_to_log(f"Initiating tech operation: {operation_type}")
    ui_manager.tech_transaction_in_progress = operation_type
    ui_manager.tech_input_string = ""
    if operation_type == "collect_dc_rewards":
        action_collect_staking_rewards(player_inventory_cache) # player_inventory_cache is global
        # action_collect_staking_rewards calls setup_buttons itself.
        return
    elif operation_type in ["buy_crypto", "sell_crypto", "stake_dc", "unstake_dc"]:
        ui_manager.current_view = "tech_input_coin_select"
        ui_manager.set_active_prompt_message("Select cryptocurrency.")
    elif operation_type == "launder_cash":
        ui_manager.coin_for_tech_transaction = None # ui_manager state
        ui_manager.current_view = "tech_input_amount"
        ui_manager.set_active_prompt_message("Enter cash amount to launder.")
    elif operation_type == "buy_ghost_network":
        action_purchase_ghost_network(player_inventory_cache, game_configs_data_cache) # Caches are global
        # action_purchase_ghost_network calls setup_buttons itself.
        return
    if game_state_data_cache: # This check is likely redundant
        ui_manager.setup_buttons_for_current_view()


def action_tech_select_coin(coin: CryptoCoin) -> None:
    # Use ui_manager for state and view changes
    verb: str = (
        ui_manager.tech_transaction_in_progress.split("_")[0]
        if ui_manager.tech_transaction_in_progress
        else "transact"
    )
    add_message_to_log(f"Tech operation coin selected: {coin.value} for {verb}")
    ui_manager.coin_for_tech_transaction = coin
    ui_manager.current_view = "tech_input_amount"
    ui_manager.set_active_prompt_message(f"Enter amount of {coin.value} to {verb}.")
    if game_state_data_cache: # This check is likely redundant
        ui_manager.setup_buttons_for_current_view()


def action_purchase_ghost_network(
    player_inv: PlayerInventory, game_configs: Any # Cache versions
) -> None:
    # Use ui_manager for prompts and view changes
    skill_id_val: SkillID = SkillID.GHOST_NETWORK_ACCESS
    cost_dc_val: float = getattr(game_configs_data_cache, "GHOST_NETWORK_ACCESS_COST_DC", 50.0)
    if skill_id_val.value in player_inventory_cache.unlocked_skills:
        ui_manager.set_active_prompt_message("Ghost Network access already acquired.")
        add_message_to_log("Ghost Network purchase failed: Already acquired.")
    elif player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0) >= cost_dc_val:
        player_inventory_cache.remove_crypto(CryptoCoin.DRUG_COIN, cost_dc_val)
        player_inventory_cache.unlocked_skills.add(skill_id_val.value)
        msg_val: str = f"Ghost Network access purchased for {cost_dc_val:.2f} DC."
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        ui_manager.set_active_prompt_message(f"Error: Not enough DC. Need {cost_dc_val:.2f} DC.")
        add_message_to_log(
            f"Ghost Network purchase failed: Need {cost_dc_val:.2f} DC, Has {player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0):.2f} DC."
        )
    ui_manager.action_open_tech_contact() # Change view via ui_manager
    if game_state_data_cache: # This check is likely redundant
        ui_manager.setup_buttons_for_current_view()


def _validate_tech_amount(input_str: str) -> Optional[float]: # input_str from ui_manager.tech_input_string
    original_input_val: str = input_str
    if not input_str.replace(".", "", 1).isdigit():
        errmsg_val: str = "Error: Invalid amount. Must be a number."
        ui_manager.set_active_prompt_message(errmsg_val) # Use ui_manager
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: '{original_input_val}'"
        )
        return None
    try:
        amount_val: float = float(input_str)
    except ValueError:
        errmsg_val: str = "Error: Could not convert amount to number."
        ui_manager.set_active_prompt_message(errmsg_val) # Use ui_manager
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: '{original_input_val}'"
        )
        return None
    if amount_val <= 1e-9:  # Epsilon for float comparison
        errmsg_val: str = "Error: Amount must be a positive number."
        ui_manager.set_active_prompt_message(errmsg_val) # Use ui_manager
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: {amount_val}"
        )
        return None
    return amount_val


def _calculate_tech_heat(player_inv: PlayerInventory, game_configs: Any) -> int:
    base_heat_val: int = game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION # Use cache
    effective_heat_val: float = float(
        base_heat_val
    )
    if SkillID.DIGITAL_FOOTPRINT.value in player_inventory_cache.unlocked_skills: # Use cache
        effective_heat_val *= (
            1.0 - game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT # Use cache
        )
    if player_inventory_cache.has_secure_phone: # Use cache
        effective_heat_val *= 1.0 - game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT # Use cache
    return int(round(effective_heat_val))


def action_confirm_tech_operation(
    player_inv: PlayerInventory, game_state: GameState, game_configs: Any # These are cache versions
) -> None:
    # Use ui_manager for state and view changes
    amount_val: Optional[float] = _validate_tech_amount(ui_manager.tech_input_string) # Use ui_manager
    if amount_val is None:
        ui_manager.tech_input_string = ""
        ui_manager.setup_buttons_for_current_view() # Use ui_manager
        return

    effective_heat_val: int = _calculate_tech_heat(player_inventory_cache, game_configs_data_cache) # Use caches
    current_player_region_obj: Optional[Region] = game_state_data_cache.get_current_player_region() # Use cache
    region_name_str_val: str = (
        current_player_region_obj.name.value
        if current_player_region_obj
        and hasattr(current_player_region_obj.name, "value")
        else (
            str(current_player_region_obj.name) # Ensure str conversion if not an enum with .value
            if current_player_region_obj
            else "Unknown Region"
        )
    )

    success_flag: bool = False
    # Use ui_manager for state
    log_prefix_str: str = (
        f"Tech op '{ui_manager.tech_transaction_in_progress}' for {amount_val:.4f} {ui_manager.coin_for_tech_transaction.value if ui_manager.coin_for_tech_transaction else 'cash'}: "
    )
    msg_str: str = ""

    if ui_manager.tech_transaction_in_progress == "buy_crypto" and ui_manager.coin_for_tech_transaction:
        price_val: float = game_state_data_cache.current_crypto_prices.get( # Use cache
            ui_manager.coin_for_tech_transaction, 0.0
        )
        fee_val: float = (
            amount_val
            * price_val
            * game_configs_data_cache.TECH_CONTACT_SERVICES["CRYPTO_TRADE"]["fee_buy_sell"] # Use cache
        )
        total_cost_val: float = amount_val * price_val + fee_val
        if price_val <= 1e-9:
            msg_str = "Error: Price unavailable."
        elif player_inventory_cache.cash >= total_cost_val: # Use cache
            player_inventory_cache.cash -= total_cost_val # Use cache
            player_inventory_cache.add_crypto(ui_manager.coin_for_tech_transaction, amount_val) # Use cache
            msg_str = f"Bought {amount_val:.4f} {ui_manager.coin_for_tech_transaction.value}. Heat +{effective_heat_val} in {region_name_str_val}."
            success_flag = True
        else:
            msg_str = f"Error: Not enough cash. Need ${total_cost_val:.2f}"
    elif ui_manager.tech_transaction_in_progress == "sell_crypto" and ui_manager.coin_for_tech_transaction:
        price_val: float = game_state_data_cache.current_crypto_prices.get( # Use cache
            ui_manager.coin_for_tech_transaction, 0.0
        )
        gross_proceeds_val: float = amount_val * price_val
        fee_val: float = (
            gross_proceeds_val
            * game_configs_data_cache.TECH_CONTACT_SERVICES["CRYPTO_TRADE"]["fee_buy_sell"] # Use cache
        )
        net_proceeds_val: float = gross_proceeds_val - fee_val
        if price_val <= 1e-9:
            msg_str = "Error: Price unavailable."
        elif player_inventory_cache.crypto_wallet.get(ui_manager.coin_for_tech_transaction, 0.0) >= amount_val: # Use cache
            player_inventory_cache.remove_crypto(ui_manager.coin_for_tech_transaction, amount_val) # Use cache
            player_inventory_cache.cash += net_proceeds_val # Use cache
            msg_str = f"Sold {amount_val:.4f} {ui_manager.coin_for_tech_transaction.value}. Heat +{effective_heat_val} in {region_name_str_val}."
            success_flag = True
        else:
            msg_str = f"Error: Not enough {ui_manager.coin_for_tech_transaction.value}."
    elif ui_manager.tech_transaction_in_progress == "launder_cash":
        fee_val: float = (
            amount_val * game_configs_data_cache.TECH_CONTACT_SERVICES["LAUNDER_CASH"]["fee"] # Use cache
        )
        total_cost_val: float = amount_val + fee_val
        launder_heat_val: int = int(
            amount_val * game_configs_data_cache.LAUNDERING_HEAT_FACTOR_PER_CASH_UNIT # Use cache
        )
        if player_inventory_cache.cash >= total_cost_val: # Use cache
            player_inventory_cache.cash -= total_cost_val # Use cache
            player_inventory_cache.pending_laundered_sc = ( # Use cache
                player_inventory_cache.pending_laundered_sc + amount_val # Use cache
                if hasattr(player_inventory_cache, "pending_laundered_sc") # Use cache
                else amount_val
            )
            player_inventory_cache.pending_laundered_sc_arrival_day = ( # Use cache
                game_state_data_cache.current_day + game_configs_data_cache.LAUNDERING_DELAY_DAYS # Use cache
            )
            msg_str = f"Laundered ${amount_val:,.2f}. Fee ${fee_val:,.2f}. Arrives day {player_inventory_cache.pending_laundered_sc_arrival_day}. Heat +{launder_heat_val} in {region_name_str_val}." # Use cache
            effective_heat_val = (
                launder_heat_val
            )
            success_flag = True
        else:
            msg_str = (
                f"Error: Not enough cash for amount + fee. Need ${total_cost_val:.2f}"
            )
    elif (
        ui_manager.tech_transaction_in_progress == "stake_dc" # Use ui_manager
        and ui_manager.coin_for_tech_transaction == CryptoCoin.DRUG_COIN # Use ui_manager
    ):
        if player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0) >= amount_val: # Use cache
            player_inventory_cache.remove_crypto(CryptoCoin.DRUG_COIN, amount_val) # Use cache
            player_inventory_cache.staked_drug_coin["staked_amount"] = ( # Use cache
                player_inventory_cache.staked_drug_coin.get("staked_amount", 0.0) + amount_val # Use cache
            )
            msg_str = f"Staked {amount_val:.4f} DC."
            success_flag = True
        else:
            msg_str = f"Error: Not enough {CryptoCoin.DRUG_COIN.value}."
    elif (
        ui_manager.tech_transaction_in_progress == "unstake_dc" # Use ui_manager
        and ui_manager.coin_for_tech_transaction == CryptoCoin.DRUG_COIN # Use ui_manager
    ):
        if player_inventory_cache.staked_drug_coin.get("staked_amount", 0.0) >= amount_val: # Use cache
            player_inventory_cache.staked_drug_coin["staked_amount"] -= amount_val # Use cache
            pending_rewards_val: float = player_inventory_cache.staked_drug_coin.get( # Use cache
                "pending_rewards", 0.0
            )
            player_inventory_cache.add_crypto( # Use cache
                CryptoCoin.DRUG_COIN, amount_val + pending_rewards_val
            )
            player_inventory_cache.staked_drug_coin["pending_rewards"] = 0.0 # Use cache
            msg_str = f"Unstaked {amount_val:.4f} DC. Rewards collected: {pending_rewards_val:.4f} DC."
            success_flag = True
        else:
            msg_str = f"Error: Not enough staked {CryptoCoin.DRUG_COIN.value}."

    if success_flag:
        show_event_message_external(msg_str)
        add_message_to_log(log_prefix_str + msg_str)
        if (
            effective_heat_val > 0
            and ui_manager.tech_transaction_in_progress # Use ui_manager
            in ["buy_crypto", "sell_crypto", "launder_cash"]
            and current_player_region_obj
        ):
            current_player_region_obj.modify_heat(effective_heat_val)
            add_message_to_log(
                f"Applied heat: +{effective_heat_val} in {region_name_str_val} for {ui_manager.tech_transaction_in_progress}" # Use ui_manager
            )
        ui_manager.action_open_tech_contact() # Change view via ui_manager
        ui_manager.tech_input_string = ""
        ui_manager.tech_transaction_in_progress = None
    else:
        ui_manager.set_active_prompt_message(msg_str if msg_str else "Error: Transaction failed.") # Use ui_manager
        add_message_to_log(
            log_prefix_str + (msg_str if msg_str else "Failed - Unknown reason.")
        )
        if amount_val is None: # Input validation failed
            ui_manager.tech_input_string = ""  # Clear input

    ui_manager.setup_buttons_for_current_view() # Use ui_manager

# Remove _create_action_button, _create_back_button, _create_button_list_vertical,
# _get_active_buttons, and setup_buttons as they are now in UIManager.

# --- Main Game Loop ---
def game_loop(
    player_inventory: PlayerInventory,
    initial_current_region: Optional[Region],
    game_state_ext: GameState,
    game_configs_ext: Any,
) -> None:
    """The main game loop."""
    # Global variables that are caches or references to core game logic
    global game_state_data_cache, game_configs_data_cache, player_inventory_cache
    # Global reference to the UIManager instance
    global ui_manager

    game_state_data_cache = game_state_ext
    game_configs_data_cache = game_configs_ext
    player_inventory_cache = player_inventory

    # Instantiate UIManager
    ui_manager = UIManager(game_state_data_cache, player_inventory_cache, game_configs_data_cache)

    # Initial setup of player region if not already set (UIManager __init__ calls setup_buttons_for_current_view)
    if (
        not hasattr(game_state_data_cache, "current_player_region")
        or game_state_data_cache.current_player_region is None
    ):
        game_state_data_cache.current_player_region = (
            initial_current_region
            if initial_current_region
            else game_state_data_cache.get_current_player_region() # Fallback
        )
        # If region changed, UIManager might need to re-setup buttons if not handled by its init based on game_state
        # However, UIManager's init calls setup_buttons_for_current_view which uses game_state.current_player_region
        # So this should be fine.

    # ui_manager.setup_buttons_for_current_view() # Called by UIManager constructor

    running: bool = True
    while running:
        current_player_region_for_frame: Optional[Region] = ( # This remains as it's from game_state_data_cache
            game_state_data_cache.current_player_region
        )
        previous_view: str = ui_manager.current_view # Use ui_manager
        mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()

        if ui_manager.game_over_message is not None and ui_manager.current_view != "game_over": # Use ui_manager
            previous_view = ui_manager.current_view # Use ui_manager
            ui_manager.current_view = "game_over"    # Use ui_manager
            ui_manager.setup_buttons_for_current_view() # Use ui_manager

        for event_pygame in pygame.event.get():
            if event_pygame.type == pygame.QUIT:
                running = False

            if ui_manager.current_view == "game_over": # Use ui_manager
                for btn_game_over in ui_manager.game_over_buttons: # Use ui_manager
                    if btn_game_over.handle_event(event_pygame):
                        break
                if (
                    event_pygame.type == pygame.KEYDOWN
                    and event_pygame.key == pygame.K_RETURN
                    and ui_manager.game_over_buttons # Use ui_manager
                    and ui_manager.game_over_buttons[0].action # Use ui_manager
                ):
                    ui_manager.game_over_buttons[0].action()
                continue

            if ui_manager.current_view == "blocking_event_popup": # Use ui_manager
                for btn_popup in ui_manager.blocking_event_popup_buttons: # Use ui_manager
                    if btn_popup.handle_event(event_pygame):
                        if previous_view != ui_manager.current_view: # Use ui_manager
                            ui_manager.setup_buttons_for_current_view() # Use ui_manager
                        break
                if (
                    event_pygame.type == pygame.KEYDOWN
                    and event_pygame.key == pygame.K_RETURN
                    and ui_manager.blocking_event_popup_buttons # Use ui_manager
                    and ui_manager.blocking_event_popup_buttons[0].action # Use ui_manager
                ):
                    ui_manager.blocking_event_popup_buttons[0].action() # Use ui_manager
                    if previous_view != ui_manager.current_view: # Use ui_manager
                        ui_manager.setup_buttons_for_current_view() # Use ui_manager
                continue

            is_market_input_active_local: bool = (
                ui_manager.current_view == "market_buy_input" # Use ui_manager
                or ui_manager.current_view == "market_sell_input" # Use ui_manager
            )
            is_tech_input_active_local: bool = (
                ui_manager.current_view == "tech_input_amount" # Use ui_manager
            )
            if event_pygame.type == pygame.KEYDOWN:
                if event_pygame.key == pygame.K_ESCAPE:
                    if is_market_input_active_local or is_tech_input_active_local:
                        action_cancel_transaction() # This function will use ui_manager internally
                    else:
                        action_open_main_menu() # This function will use ui_manager internally
                if is_market_input_active_local:
                    if event_pygame.key == pygame.K_RETURN:
                        # Ensure current_player_region_for_frame is valid if needed by confirm_transaction
                        if current_player_region_for_frame:
                             action_confirm_transaction(player_inventory_cache, current_player_region_for_frame, game_state_data_cache)
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        ui_manager.quantity_input_string = ui_manager.quantity_input_string[:-1] # Use ui_manager
                    elif event_pygame.unicode.isdigit():
                        ui_manager.quantity_input_string += event_pygame.unicode # Use ui_manager
                elif is_tech_input_active_local:
                    if event_pygame.key == pygame.K_RETURN:
                        action_confirm_tech_operation(
                            player_inventory_cache, # This is global cache
                            game_state_data_cache,    # This is global cache
                            game_configs_data_cache,  # This is global cache
                        )
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        ui_manager.tech_input_string = ui_manager.tech_input_string[:-1] # Use ui_manager
                    elif event_pygame.unicode.isdigit() or (
                        event_pygame.unicode == "." and "." not in ui_manager.tech_input_string # Use ui_manager
                    ):
                        ui_manager.tech_input_string += event_pygame.unicode # Use ui_manager

            button_clicked_and_view_changed_flag: bool = False
            if ui_manager.current_view not in ["game_over", "blocking_event_popup"]: # Use ui_manager
                for btn_active in ui_manager.active_buttons_list: # Use ui_manager
                    if btn_active.handle_event(event_pygame):
                        if previous_view != ui_manager.current_view: # Use ui_manager
                            button_clicked_and_view_changed_flag = True
                            ui_manager.setup_buttons_for_current_view() # Use ui_manager
                        break
            if (
                not button_clicked_and_view_changed_flag
                and previous_view != ui_manager.current_view # Use ui_manager
            ):
                ui_manager.setup_buttons_for_current_view() # Use ui_manager

        update_hud_timers_external() # This function does not depend on these globals
        if ui_manager.prompt_message_timer > 0: # Use ui_manager
            ui_manager.prompt_message_timer -= 1 # Use ui_manager
        if ui_manager.prompt_message_timer <= 0: # Use ui_manager
            ui_manager.active_prompt_message = None # Use ui_manager

        screen.fill(RICH_BLACK)
        # Drawing logic based on ui_manager.current_view
        if ui_manager.current_view == "game_over": # Use ui_manager
            draw_game_over_view_external(
                screen,
                ui_manager.game_over_message if ui_manager.game_over_message else "Game Over", # Use ui_manager
                ui_manager.game_over_buttons, # Use ui_manager
            )
        elif ui_manager.current_view == "main_menu": # Use ui_manager
            draw_main_menu_external(screen, ui_manager.main_menu_buttons) # Use ui_manager
        elif ui_manager.current_view == "market" and current_player_region_for_frame: # Use ui_manager
            draw_market_view_external(screen, current_player_region_for_frame, player_inventory_cache, ui_manager.market_view_buttons, ui_manager.market_item_buttons)  # Use ui_manager for buttons
        elif ui_manager.current_view == "inventory": # Use ui_manager
            draw_inventory_view_external(screen, player_inventory_cache, ui_manager.inventory_view_buttons) # Use ui_manager
        elif ui_manager.current_view == "travel" and current_player_region_for_frame: # Use ui_manager
            draw_travel_view_external(
                screen, current_player_region_for_frame, ui_manager.travel_view_buttons # Use ui_manager
            )
        elif ui_manager.current_view == "informant": # Use ui_manager
            draw_informant_view_external(screen, player_inventory_cache, ui_manager.informant_view_buttons, game_configs_data_cache)  # Use ui_manager for buttons
        elif ui_manager.current_view in [ # Use ui_manager
            "tech_contact",
            "tech_input_coin_select",
            "tech_input_amount",
        ]:
            tech_ui_state_dict: Dict[str, Any] = { # Construct with ui_manager attributes
                "current_view": ui_manager.current_view,
                "tech_transaction_in_progress": ui_manager.tech_transaction_in_progress,
                "coin_for_tech_transaction": ui_manager.coin_for_tech_transaction,
                "tech_input_string": ui_manager.tech_input_string,
                "active_prompt_message": ui_manager.active_prompt_message,
                "prompt_message_timer": ui_manager.prompt_message_timer,
                "tech_input_box_rect": ui_manager.tech_input_box_rect, # This was already a direct value, but good to note it's related to UIManager state now
            }
            draw_tech_contact_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, ui_manager.tech_contact_view_buttons, tech_ui_state_dict)  # Use ui_manager for buttons
        elif ui_manager.current_view == "skills": # Use ui_manager
            draw_skills_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, ui_manager.skills_view_buttons)  # Use ui_manager
        elif ui_manager.current_view == "upgrades": # Use ui_manager
            draw_upgrades_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, ui_manager.upgrades_view_buttons)  # Use ui_manager
        elif ui_manager.current_view in ["market_buy_input", "market_sell_input"]: # Use ui_manager
            transaction_ui_state_dict: Dict[str, Any] = { # Construct with ui_manager attributes
                "quantity_input_string": ui_manager.quantity_input_string,
                "drug_for_transaction": ui_manager.drug_for_transaction,
                "quality_for_transaction": ui_manager.quality_for_transaction,
                "price_for_transaction": ui_manager.price_for_transaction,
                "available_for_transaction": ui_manager.available_for_transaction,
                "current_transaction_type": ui_manager.current_transaction_type,
                "active_prompt_message": ui_manager.active_prompt_message,
                "prompt_message_timer": ui_manager.prompt_message_timer,
                "input_box_rect": ui_manager.input_box_rect, # This was already a direct value
            }
            draw_transaction_input_view_external(
                screen, ui_manager.transaction_input_buttons, transaction_ui_state_dict # Use ui_manager for buttons
            )

        if ( # Use ui_manager
            ui_manager.current_view != "game_over"
            and ui_manager.current_view == "blocking_event_popup"
            and ui_manager.active_blocking_event_data
        ):
            draw_blocking_event_popup_external(
                screen, ui_manager.active_blocking_event_data, ui_manager.blocking_event_popup_buttons # Use ui_manager
            )

        if ( # Use ui_manager
            ui_manager.current_view != "game_over" and current_player_region_for_frame
        ):
            draw_hud_external(screen, player_inventory_cache, current_player_region_for_frame, game_state_data_cache)

        if ( # Use ui_manager for all these
            ui_manager.active_prompt_message
            and ui_manager.prompt_message_timer > 0
            and ui_manager.current_view not in ["game_over", "blocking_event_popup"]
        ):
            is_prompt_handled_local: bool = ( # Use ui_manager
                ui_manager.current_view
                in ["market_buy_input", "market_sell_input", "tech_input_amount"]
            ) or ( # Use ui_manager
                ui_manager.current_view == "tech_contact"
                and locals().get("tech_ui_state_dict", {}).get("active_prompt_message") # tech_ui_state_dict now sources from ui_manager
                and (
                    "Select cryptocurrency"
                    not in locals()
                    .get("tech_ui_state_dict", {})
                    .get("active_prompt_message", "")
                    and "Enter amount"
                    not in locals()
                    .get("tech_ui_state_dict", {})
                    .get("active_prompt_message", "")
                )
            )
            if not is_prompt_handled_local:
                prompt_y_pos_val: int = UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.PROMPT_DEFAULT_Y_OFFSET
                if ui_manager.current_view == "tech_contact": # Use ui_manager
                    prompt_y_pos_val = UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.PROMPT_TECH_CONTACT_Y_OFFSET
                prompt_color_val: Tuple[int, int, int] = (
                    IMPERIAL_RED
                    if any(
                        err_word in ui_manager.active_prompt_message # Use ui_manager
                        for err_word in ["Error", "Invalid", "Not enough"]
                    )
                    else (
                        GOLDEN_YELLOW
                        if "Skill" in ui_manager.active_prompt_message # Use ui_manager
                        else EMERALD_GREEN
                    )
                )
                draw_text(
                    screen,
                    ui_manager.active_prompt_message, # Use ui_manager
                    SCREEN_WIDTH // 2,
                    prompt_y_pos_val,
                    font=FONT_MEDIUM, # From ui_theme
                    color=prompt_color_val,
                    center_aligned=True,
                    max_width=UI_CONSTANTS.SCREEN_WIDTH - (2 * UI_CONSTANTS.LARGE_PADDING), # Example use of padding
                )

        pygame.display.flip()
        clock.tick(UI_CONSTANTS.FPS)

    pygame.quit()
    sys.exit()
