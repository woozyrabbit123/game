"""
This module implements the main application logic for the Pygame UI.

It includes functions for managing game state, handling user input,
and rendering the user interface.
"""

import pygame
import sys
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
from .. import (
    game_configs as game_configs_module,
)  # To access game_configs directly for MUGGING_EVENT_CHANCE

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
from .ui_components import Button
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

# --- Pygame Setup (Screen, Clock) ---
pygame.font.init()
pygame.init()
screen = pygame.display.set_mode((UI_CONSTANTS.SCREEN_WIDTH, UI_CONSTANTS.SCREEN_HEIGHT))
pygame.display.set_caption("Project Narco-Syndicate")
clock = pygame.time.Clock()

# --- Game State & UI Variables ---
current_view: str = "main_menu"
main_menu_buttons: List[Button] = []
market_view_buttons: List[Button] = []
market_buy_sell_buttons: List[Button] = []
inventory_view_buttons: List[Button] = []
travel_view_buttons: List[Button] = []
tech_contact_view_buttons: List[Button] = []
skills_view_buttons: List[Button] = []
upgrades_view_buttons: List[Button] = []
transaction_input_buttons: List[Button] = []
blocking_event_popup_buttons: List[Button] = []
game_over_buttons: List[Button] = []
informant_view_buttons: List[Button] = []
active_buttons_list_current_view: List[Button] = []


current_transaction_type: Optional[str] = None
drug_for_transaction: Optional[DrugName] = None
quality_for_transaction: Optional[DrugQuality] = None
price_for_transaction: float = 0.0
available_for_transaction: int = 0
quantity_input_string: str = ""
input_box_rect = pygame.Rect(
    UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.MARKET_INPUT_BOX_X_OFFSET,
    UI_CONSTANTS.MARKET_INPUT_BOX_Y_POS,
    UI_CONSTANTS.MARKET_INPUT_BOX_WIDTH,
    UI_CONSTANTS.MARKET_INPUT_BOX_HEIGHT
)

tech_transaction_in_progress: Optional[str] = None
coin_for_tech_transaction: Optional[CryptoCoin] = None
tech_input_string: str = ""
tech_input_box_rect = pygame.Rect(
    UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.TECH_INPUT_BOX_X_OFFSET,
    UI_CONSTANTS.TECH_INPUT_BOX_Y_POS,
    UI_CONSTANTS.TECH_INPUT_BOX_WIDTH,
    UI_CONSTANTS.TECH_INPUT_BOX_HEIGHT
)

active_prompt_message: Optional[str] = None
prompt_message_timer: int = 0
# PROMPT_DURATION_FRAMES is now in UI_CONSTANTS

active_blocking_event_data: Optional[Dict] = None
game_over_message: Optional[str] = None

game_state_data_cache: Optional[GameState] = None  # Updated type hint
game_configs_data_cache: Optional[Any] = None  # Module: game_configs
player_inventory_cache: Optional[PlayerInventory] = None


# --- Daily Updates Function ---
def perform_daily_updates(
    game_state_data: GameState,
    player_inventory_data: PlayerInventory,
    game_configs_data: Any,
) -> None:
    global game_over_message, active_blocking_event_data, current_view  # Added current_view
    if game_over_message is not None:
        return

    # Debt payments
    if (
        not player_inventory_data.debt_payment_1_paid
        and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_1_DUE_DAY
    ):
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_1_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_1_AMOUNT
            player_inventory_data.debt_payment_1_paid = True
            show_event_message_external("Debt Payment 1 made!")
            add_message_to_log("Paid $25k (Debt 1).")
        else:
            game_over_message = "GAME OVER: Failed Debt Payment 1!"
            add_message_to_log(game_over_message)
            current_view = "game_over"
            return
    if (
        player_inventory_data.debt_payment_1_paid
        and not player_inventory_data.debt_payment_2_paid
        and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_2_DUE_DAY
    ):
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_2_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_2_AMOUNT
            player_inventory_data.debt_payment_2_paid = True
            show_event_message_external("Debt Payment 2 made!")
            add_message_to_log("Paid $30k (Debt 2).")
        else:
            game_over_message = "GAME OVER: Failed Debt Payment 2!"
            add_message_to_log(game_over_message)
            current_view = "game_over"
            return
    if (
        player_inventory_data.debt_payment_1_paid
        and player_inventory_data.debt_payment_2_paid
        and not player_inventory_data.debt_payment_3_paid
        and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_3_DUE_DAY
    ):
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_3_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_3_AMOUNT
            player_inventory_data.debt_payment_3_paid = True
            show_event_message_external("Final debt paid! You are free!")
            add_message_to_log("Paid $20k (Final Debt). You are FREE!")
            # Potentially set game_over_message to a win message here
        else:
            game_over_message = "GAME OVER: Failed Final Debt Payment!"
            add_message_to_log(game_over_message)
            current_view = "game_over"
            return

    # Regional updates
    current_player_region: Optional[Region] = (
        game_state_data.get_current_player_region()
    )
    for r_name, r_obj in game_state_data.all_regions.items():  # r_obj is Region
        if hasattr(r_obj, "restock_market"):
            r_obj.restock_market()
        market_impact.decay_regional_heat(
            r_obj, 1.0, player_inventory_data, game_configs_data
        )
        market_impact.decay_player_market_impact(r_obj)
        market_impact.decay_rival_market_impact(r_obj, game_state_data.current_day)
        event_manager.update_active_events(r_obj)

    game_state_data.update_daily_crypto_prices(
        game_configs_data.CRYPTO_VOLATILITY, game_configs_data.CRYPTO_MIN_PRICE
    )

    # Staking rewards
    if (
        hasattr(player_inventory_data, "staked_drug_coin")
        and player_inventory_data.staked_drug_coin.get("staked_amount", 0.0) > 0
        and hasattr(game_configs_data, "DC_STAKING_DAILY_RETURN_PERCENT")
    ):
        reward: float = (
            player_inventory_data.staked_drug_coin["staked_amount"]
            * game_configs_data.DC_STAKING_DAILY_RETURN_PERCENT
        )
        player_inventory_data.staked_drug_coin["pending_rewards"] = (
            player_inventory_data.staked_drug_coin.get("pending_rewards", 0.0) + reward
        )
        if reward > 1e-5:
            show_event_message_external(
                f"Accrued {reward:.4f} DC rewards. Collect at Tech Contact."
            )

    # Laundering arrival
    if (
        hasattr(player_inventory_data, "pending_laundered_sc_arrival_day")
        and player_inventory_data.pending_laundered_sc_arrival_day is not None
        and game_state_data.current_day
        >= player_inventory_data.pending_laundered_sc_arrival_day
    ):
        amount_laundered: float = player_inventory_data.pending_laundered_sc
        stable_coin_enum = getattr(
            CryptoCoin, "STABLE_COIN", CryptoCoin.DRUG_COIN
        )  # Fallback
        player_inventory_data.add_crypto(stable_coin_enum, amount_laundered)
        show_event_message_external(f"{amount_laundered:.2f} SC (laundered) arrived.")
        add_message_to_log(f"Laundered cash arrived: {amount_laundered:.2f} SC.")
        player_inventory_data.pending_laundered_sc = 0.0
        player_inventory_data.pending_laundered_sc_arrival_day = None

    # Event Triggering
    if current_player_region and hasattr(
        event_manager, "trigger_random_market_event"
    ):  # current_player_region defined earlier
        triggered_event_log_msg: Optional[str] = (
            event_manager.trigger_random_market_event(
                region=current_player_region,
                game_state=game_state_data,  # Pass full game_state object
                player_inventory=player_inventory_data,
                ai_rivals=game_state_data.ai_rivals,
                show_event_message_callback=show_event_message_external,
                game_configs_data=game_configs_data,  # Pass the module
                add_to_log_callback=add_message_to_log,
            )
        )
        if triggered_event_log_msg:  # triggered_event_log_msg is Optional[str]
            add_message_to_log(triggered_event_log_msg)

    # Process AI Rivals
    for rival_instance in game_state_data.ai_rivals:  # rival_instance is AIRival
        market_impact.process_rival_turn(
            rival=rival_instance,
            all_regions_dict=game_state_data.all_regions,
            current_turn_number=game_state_data.current_day,
            game_configs=game_configs_data,  # Pass module
            add_to_log_cb=add_message_to_log,
            show_on_screen_cb=show_event_message_external,
        )

    # Mugging Event Check
    if (
        current_player_region
        and random.random() < game_configs_data.MUGGING_EVENT_CHANCE
        and game_over_message is None
        and active_blocking_event_data is None
        and not any(
            isinstance(ev, MarketEvent) and ev.event_type == EventType.MUGGING
            for ev in current_player_region.active_market_events
        )
    ):  # type: ignore
        title_mug: str = "Mugged!"
        messages_mug: List[str] = []
        cash_loss_percentage: float = random.uniform(
            game_configs_data.MUGGING_CASH_LOSS_PERCENT_MIN,
            game_configs_data.MUGGING_CASH_LOSS_PERCENT_MAX
        )
        cash_lost: float = player_inventory_data.cash * cash_loss_percentage
        cash_lost = min(cash_lost, player_inventory_data.cash) # Ensure not losing more than they have
        player_inventory_data.cash -= cash_lost
        messages_mug.append(f"You were ambushed by thugs!")
        messages_mug.append(f"They managed to steal ${cash_lost:,.2f} from you.")
        outcome_log_mug: str = f"Mugging event: Lost ${cash_lost:,.2f}."
        active_blocking_event_data = {
            "title": title_mug,
            "messages": messages_mug,
            "button_text": "Damn it!",
        }
        add_message_to_log(outcome_log_mug)

    # Informant Betrayal Event Check
    betrayal_chance_val: float = getattr(
        game_configs_data,
        "INFORMANT_BETRAYAL_CHANCE",
        getattr(game_configs_module, "INFORMANT_BETRAYAL_CHANCE", 0.03),
    )
    trust_threshold_val: int = getattr(
        game_configs_data,
        "INFORMANT_TRUST_THRESHOLD_FOR_BETRAYAL",
        getattr(game_configs_module, "INFORMANT_TRUST_THRESHOLD_FOR_BETRAYAL", 20),
    )
    unavailable_days_val: int = getattr(
        game_configs_data,
        "INFORMANT_BETRAYAL_UNAVAILABLE_DAYS",
        getattr(game_configs_module, "INFORMANT_BETRAYAL_UNAVAILABLE_DAYS", 7),
    )
    current_informant_trust: int = getattr(
        player_inventory_data, "informant_trust", 100
    )
    informant_available_check_day: Optional[int] = (
        game_state_data.informant_unavailable_until_day
    )

    if (
        current_player_region
        and not any(
            isinstance(ev, MarketEvent)
            and ev.event_type == EventType.INFORMANT_BETRAYAL
            for ev in current_player_region.active_market_events
        )
        and current_informant_trust < trust_threshold_val
        and random.random() < betrayal_chance_val
        and game_over_message is None
        and active_blocking_event_data is None
        and (
            informant_available_check_day is None
            or game_state_data.current_day >= informant_available_check_day
        )
    ):
        game_state_data.informant_unavailable_until_day = (
            game_state_data.current_day + unavailable_days_val # unavailable_days_val from getattr above
        )
        original_trust: int = current_informant_trust
        player_inventory_data.informant_trust = max(0, current_informant_trust - game_configs_data.INFORMANT_BETRAYAL_TRUST_LOSS)
        trust_lost: int = original_trust - player_inventory_data.informant_trust
        heat_increase_betrayal: int = game_configs_data.INFORMANT_BETRAYAL_HEAT_INCREASE
        region_name_for_log_betrayal: str = getattr(
            current_player_region.name, "value", str(current_player_region.name)
        )
        current_player_region.modify_heat(heat_increase_betrayal)
        title_betrayal: str = "Informant Betrayal!"
        messages_betrayal: List[str] = [
            "Your informant sold you out to the authorities!",
            f"They will be unavailable for {unavailable_days_val} days.",
            f"Your trust with them has decreased by {trust_lost}.",
            f"Heat in {region_name_for_log_betrayal} has increased by {heat_increase_betrayal}.",
        ]
        active_blocking_event_data = {
            "title": title_betrayal,
            "messages": messages_betrayal,
            "button_text": "Damn it!",
        }
        log_message_betrayal: str = (
            f"Informant betrayal: Unavailable {unavailable_days_val}d. Trust -{trust_lost}. Heat +{heat_increase_betrayal} in {region_name_for_log_betrayal}."
        )
        add_message_to_log(log_message_betrayal)

    # Forced Fire Sale Event Check
    active_ffs_event: Optional[MarketEvent] = None
    if current_player_region:
        for (
            event_item
        ) in current_player_region.active_market_events:  # event_item is MarketEvent
            if event_item.event_type == EventType.FORCED_FIRE_SALE:
                active_ffs_event = event_item
                break
    if (
        current_player_region
        and active_ffs_event
        and game_over_message is None
        and active_blocking_event_data is None
    ):
        total_player_drugs_quantity: int = 0
        if hasattr(player_inventory_data, "items") and player_inventory_data.items:
            for qualities_dict in player_inventory_data.items.values():
                for item_details_dict in qualities_dict.values():
                    total_player_drugs_quantity += item_details_dict  # type: ignore # Assuming quantity is int
        if total_player_drugs_quantity > 0:
            ffs_qty_percent: float = getattr(
                game_configs_data, "FORCED_FIRE_SALE_QUANTITY_PERCENT", 0.15
            )
            ffs_penalty_percent: float = getattr(
                game_configs_data, "FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT", 0.30
            )
            ffs_min_cash_gain: float = getattr(
                game_configs_data, "FORCED_FIRE_SALE_MIN_CASH_GAIN", 50.0
            )
            drugs_sold_details_list: List[str] = []
            total_cash_gained_ffs: float = 0.0
            total_units_sold_ffs: int = 0
            player_drug_items_ffs: List[Dict[str, Any]] = []
            if hasattr(player_inventory_data, "items") and player_inventory_data.items:
                for (
                    drug_name_enum_key,
                    qualities_dict_val,
                ) in player_inventory_data.items.items():
                    for (
                        quality_enum_key,
                        quantity_val_ffs,
                    ) in qualities_dict_val.items():
                        if quantity_val_ffs > 0:
                            player_drug_items_ffs.append(
                                {
                                    "name_enum": drug_name_enum_key,
                                    "quality_enum": quality_enum_key,
                                    "current_qty": quantity_val_ffs,
                                }
                            )
            for drug_item_data_ffs in player_drug_items_ffs:
                drug_name_val_ffs: DrugName = drug_item_data_ffs["name_enum"]
                quality_val_ffs: DrugQuality = drug_item_data_ffs["quality_enum"]
                current_qty_ffs: int = drug_item_data_ffs["current_qty"]
                qty_to_sell_ffs: int = min(
                    math.ceil(current_qty_ffs * ffs_qty_percent), current_qty_ffs
                )
                if qty_to_sell_ffs > 0:
                    market_sell_price_ffs: float = current_player_region.get_sell_price(
                        drug_name_val_ffs, quality_val_ffs
                    )
                    if market_sell_price_ffs <= 0:
                        continue
                    discounted_price_ffs: float = round(
                        max(game_configs_data.FORCED_SALE_MIN_PRICE_PER_UNIT, market_sell_price_ffs * (1.0 - ffs_penalty_percent)),
                        2,
                    )
                    cash_from_sale_ffs: float = qty_to_sell_ffs * discounted_price_ffs
                    total_cash_gained_ffs += cash_from_sale_ffs
                    player_inventory_data.remove_drug(
                        drug_name_val_ffs, quality_val_ffs, qty_to_sell_ffs
                    )
                    total_units_sold_ffs += qty_to_sell_ffs
                    drugs_sold_details_list.append(
                        f"{qty_to_sell_ffs} {drug_name_val_ffs.value} ({quality_val_ffs.name})"
                    )
            if total_units_sold_ffs > 0 and total_cash_gained_ffs < ffs_min_cash_gain:
                total_cash_gained_ffs = ffs_min_cash_gain
            if total_units_sold_ffs > 0:
                player_inventory_data.cash += total_cash_gained_ffs
            if total_units_sold_ffs > 0:
                heat_increase_ffs_val: int = game_configs_data.FORCED_FIRE_SALE_HEAT_INCREASE
                region_name_log_ffs_val: str = getattr(
                    current_player_region.name, "value", str(current_player_region.name)
                )
                current_player_region.modify_heat(heat_increase_ffs_val)
                ffs_title_val: str = "Forced Fire Sale!"
                sold_summary_str: str = (
                    ", ".join(drugs_sold_details_list)
                    if drugs_sold_details_list
                    else "assets"
                )
                ffs_messages_list: List[str] = [
                    "Unforeseen situation forces quick liquidation!",
                    f"Sold: {sold_summary_str}.",
                    f"Total cash gained: ${total_cash_gained_ffs:,.2f}.",
                    f"Heat in {region_name_log_ffs_val} +{heat_increase_ffs_val}.",
                ]
                active_blocking_event_data = {
                    "title": ffs_title_val,
                    "messages": ffs_messages_list,
                    "button_text": "Got it.",
                }
                add_message_to_log(
                    f"Forced Fire Sale: Sold {sold_summary_str}. Cash +${total_cash_gained_ffs:,.2f}. Heat +{heat_increase_ffs_val} in {region_name_log_ffs_val}."
                )
            elif total_player_drugs_quantity > 0:
                add_message_to_log("Forced Fire Sale triggered, but no drugs sold.")

    # Bankruptcy check
    if player_inventory_data.cash < game_configs_data.BANKRUPTCY_THRESHOLD:
        game_over_message = "GAME OVER: You have gone bankrupt!"
        add_message_to_log(
            f"{game_over_message} Cash: ${player_inventory_data.cash:.2f}, Threshold: ${game_configs_data.BANKRUPTCY_THRESHOLD:.2f}"
        )
        current_view = "game_over"
        return


def set_active_prompt_message(
    message: str, duration_frames: int = UI_CONSTANTS.PROMPT_DURATION_FRAMES
) -> None:
    """Sets a message to be displayed temporarily on the screen."""
    global active_prompt_message, prompt_message_timer
    active_prompt_message = message
    prompt_message_timer = duration_frames


# --- Action Functions (Callbacks for buttons) ---
def action_open_main_menu() -> None:
    global current_view
    current_view = "main_menu"


def action_open_market() -> None:
    global current_view
    current_view = "market"


def action_open_inventory() -> None:
    global current_view
    current_view = "inventory"


def action_open_travel() -> None:
    global current_view
    current_view = "travel"


def action_open_tech_contact() -> None:
    global current_view
    current_view = "tech_contact"


def action_open_skills() -> None:
    global current_view
    current_view = "skills"


def action_open_upgrades() -> None:
    global current_view
    current_view = "upgrades"


def action_open_informant() -> None:
    global current_view
    current_view = "informant"


def action_close_blocking_event_popup() -> None:
    global active_blocking_event_data, current_view
    active_blocking_event_data = None
    current_view = "main_menu"


def action_travel_to_region(
    destination_region: Region,
    player_inv: PlayerInventory,
    game_state_instance: GameState,
) -> None:
    global current_view, game_state_data_cache, player_inventory_cache, game_configs_data_cache, active_blocking_event_data, game_over_message
    if game_over_message is not None:
        return
    add_message_to_log(
        f"Attempting to travel to {destination_region.name.value}."
    )  # Assuming destination_region.name is Enum
    original_day_before_travel: int = game_state_instance.current_day
    game_state_instance.set_current_player_region(
        destination_region.name
    )  # Assuming destination_region.name is RegionName enum
    game_state_instance.current_day += 1
    add_message_to_log(f"Advanced day to {game_state_instance.current_day}.")
    perform_daily_updates(
        game_state_data_cache, player_inventory_cache, game_configs_data_cache
    )
    if game_over_message is not None:
        current_view = "game_over"
        add_message_to_log("Game over during travel daily updates.")
        return

    if (
        game_state_instance.current_day
        % game_configs_data_cache.SKILL_POINTS_PER_X_DAYS
        == 0
        and game_state_instance.current_day > original_day_before_travel
    ):
        player_inv.skill_points += 1
        show_event_message_external(
            f"Day advanced. +1 Skill Point. Total: {player_inv.skill_points}"
        )
        add_message_to_log(f"Awarded skill point. Total: {player_inv.skill_points}")

    region_heat_val: int = destination_region.current_heat
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
            active_blocking_event_data = {
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
                player_inv.cash,
                float(
                    random.randint(game_configs_data_cache.POLICE_FINE_BASE_MIN, game_configs_data_cache.POLICE_FINE_BASE_MAX)
                    * (1 + destination_region.current_heat // game_configs_data_cache.POLICE_FINE_HEAT_DIVISOR)
                ),
            )
            player_inv.cash -= fine_val
            active_blocking_event_data = {
                "title": "Police Stop - Fine!",
                "messages": [
                    "Police stop for 'random' check.",
                    f"Minor infraction. Fined ${fine_val:,.0f}.",
                ],
                "button_text": "Pay Fine",
            }
            show_event_message_external(f"Paid fine of ${fine_val:,.0f}.")
            add_message_to_log(
                f"Police stop: Fined ${fine_val:,.0f}. Cash remaining: ${player_inv.cash:.2f}"
            )
            if player_inv.cash < game_configs_data_cache.BANKRUPTCY_THRESHOLD:
                game_over_message = "GAME OVER: A hefty fine bankrupted you!"
                add_message_to_log(f"{game_over_message} Cash: ${player_inv.cash:.2f}")
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
                player_inv.items.clear()
                player_inv.current_load = (
                    0  # Simplified, assumes only drugs contribute to load for this
                )
                active_blocking_event_data = {
                    "title": "Police Stop - Major Bust!",
                    "messages": ["Police search vehicle!", "All drugs confiscated!"],
                    "button_text": "Damn!",
                }
                add_message_to_log("Police Stop: Searched, all drugs confiscated.")
            elif total_contraband_units_val > 0:
                active_blocking_event_data = {
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
                active_blocking_event_data = {
                    "title": "Police Stop - Searched!",
                    "messages": ["Police search vehicle!", "Luckily, you were clean."],
                    "button_text": "Phew!",
                }
                add_message_to_log("Police stop: Searched, found nothing.")
        current_view = "blocking_event_popup"
    else:
        show_event_message_external(
            f"Arrived safely in {destination_region.name.value}."
        )
        add_message_to_log(f"Arrived safely in {destination_region.name.value}.")
        current_view = "main_menu"


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
        set_active_prompt_message(f"Error: Not enough cash. Need ${cost:.0f}.")
        add_message_to_log(f"Failed to buy rumor: Insufficient cash.")
    setup_buttons(
        game_state_instance,
        player_inv,
        game_configs,
        game_state_instance.get_current_player_region(),
    )


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
        set_active_prompt_message(f"Error: Not enough cash. Need ${cost:.0f}.")
        add_message_to_log(f"Failed to buy rival info: Insufficient cash.")
    setup_buttons(
        game_state_instance,
        player_inv,
        game_configs,
        game_state_instance.get_current_player_region(),
    )


def _initiate_market_transaction(
    trans_type: str, drug: DrugName, quality: DrugQuality, price: float, available: int
) -> None:
    """Helper function to set up state for a market buy/sell transaction."""
    global current_view, current_transaction_type, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, quantity_input_string
    current_view = f"market_{trans_type}_input"
    current_transaction_type = trans_type
    drug_for_transaction = drug
    quality_for_transaction = quality
    price_for_transaction = price
    available_for_transaction = available
    quantity_input_string = ""
    set_active_prompt_message(
        f"Enter quantity to {trans_type}.", duration_frames=UI_CONSTANTS.PROMPT_DURATION_FRAMES * 2
    )
    add_message_to_log(
        f"Initiating market transaction: {trans_type} {drug.value} ({quality.name}) at ${price:.2f}, {available} available."
    )


def action_initiate_buy(
    drug: DrugName, quality: DrugQuality, price: float, available: int
) -> None:
    _initiate_market_transaction("buy", drug, quality, price, available)


def action_initiate_sell(
    drug: DrugName, quality: DrugQuality, price: float, available: int
) -> None:
    _initiate_market_transaction("sell", drug, quality, price, available)


def action_confirm_transaction(
    player_inv: PlayerInventory, market_region: Region, game_state_instance: GameState
) -> None:
    global quantity_input_string, current_transaction_type, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, current_view, game_configs_data_cache, game_state_data_cache, player_inventory_cache  # Added game_state_data_cache, player_inventory_cache
    original_quantity_input: str = quantity_input_string
    errmsg: Optional[str] = None
    if not quantity_input_string.isdigit():
        errmsg = "Error: Quantity must be a positive number."
    quantity: int = int(quantity_input_string) if quantity_input_string.isdigit() else 0
    if not errmsg and quantity <= 0:
        errmsg = "Error: Quantity must be a positive number."

    if errmsg:
        set_active_prompt_message(errmsg)
        add_message_to_log(
            f"Transaction failed: {errmsg} Input: '{original_quantity_input}'"
        )
        quantity_input_string = ""
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            market_region,
        )
        return

    if ui_manager.current_transaction_type == "buy": # Use ui_manager
        cost: float = quantity * ui_manager.price_for_transaction # Use ui_manager

        # Call the new centralized processing method
        if player_inv.process_buy_drug(ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity, cost):
            market_region.update_stock_on_buy(
                ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity # Use ui_manager
            )
            # Pass game_configs_data_cache to apply_player_buy_impact if it needs it (based on its definition)
            # Assuming apply_player_buy_impact was refactored to take game_configs if needed, or it's implicitly available
            market_impact.apply_player_buy_impact(market_region, ui_manager.drug_for_transaction, quantity)
            for (
                event_item
            ) in market_region.active_market_events:  # event_item is MarketEvent
                if (
                    event_item.event_type == EventType.BLACK_MARKET_OPPORTUNITY
                    and event_item.target_drug_name == drug_for_transaction
                    and event_item.target_quality == quality_for_transaction
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
                f"Bought {quantity} {ui_manager.drug_for_transaction.value} ({ui_manager.quality_for_transaction.name}) for ${cost:.2f}." # Use ui_manager
            )
            show_event_message_external(log_msg)
            add_message_to_log(log_msg)
            ui_manager.current_view = "market" # Use ui_manager
        else:
            # Purchase failed (handled by process_buy_drug)
            errmsg = "Error: Transaction failed. Insufficient cash or inventory space."
            # No specific error message differentiation here for simplicity, PlayerInventory handles the checks.

    elif ui_manager.current_transaction_type == "sell": # Use ui_manager
        revenue: float = quantity * ui_manager.price_for_transaction # Use ui_manager

        # Call the new centralized processing method
        if player_inv.process_sell_drug(ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity, revenue):
            market_region.update_stock_on_sell(
                ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity # Use ui_manager
            )
            # apply_player_sell_impact now handles heat generation.
            # It requires player_inventory, region, drug_name, quantity, and game_configs.
            market_impact.apply_player_sell_impact( # Pass relevant args
                player_inv,
                market_region,
                drug_for_transaction,
                quantity,
                game_configs_data_cache,
            )
            log_msg: str = (
                f"Sold {quantity} {drug_for_transaction.value} ({quality_for_transaction.name}) for ${revenue:.2f}. Heat +{int(round(total_heat_val))} in {market_region.name.value}."
            )
            show_event_message_external(log_msg)
            add_message_to_log(log_msg)
            current_view = "market"
    if errmsg:
        set_active_prompt_message(errmsg)
        add_message_to_log(f"Transaction failed: {errmsg}")
    quantity_input_string = ""
    setup_buttons(
        game_state_data_cache,
        player_inventory_cache,
        game_configs_data_cache,
        market_region,
    )


def action_cancel_transaction() -> None:
    global current_view, quantity_input_string, tech_input_string, tech_transaction_in_progress, active_prompt_message, game_state_data_cache, player_inventory_cache, game_configs_data_cache
    add_message_to_log(
        f"Transaction cancelled. Was type: {current_transaction_type or tech_transaction_in_progress}, View: {current_view}"
    )
    if current_view in ["market_buy_input", "market_sell_input"]:
        current_view = "market"
    elif current_view in ["tech_input_coin_select", "tech_input_amount"]:
        current_view = "tech_contact"
    quantity_input_string = ""
    tech_input_string = ""
    tech_transaction_in_progress = None
    active_prompt_message = None
    if game_state_data_cache:  # Ensure cache is populated
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            game_state_data_cache.get_current_player_region(),
        )


def action_unlock_skill(
    skill_id: SkillID, player_inv: PlayerInventory, game_configs: Any
) -> None:
    global game_state_data_cache, player_inventory_cache, game_configs_data_cache
    if skill_id.value in player_inv.unlocked_skills:  # Check .value
        set_active_prompt_message("Skill already unlocked.")
        add_message_to_log(f"Skill unlock failed: {skill_id.value} already unlocked.")
        return
    skill_def: Optional[Dict[str, Any]] = game_configs.SKILL_DEFINITIONS.get(skill_id)
    if not skill_def:
        set_active_prompt_message("Error: Skill data unavailable.")
        add_message_to_log(
            f"Skill unlock failed: Definition for {skill_id.value} not found."
        )
        return
    cost_val: int = skill_def["cost"]
    if player_inv.skill_points >= cost_val:
        player_inv.skill_points -= cost_val
        player_inv.unlocked_skills.add(skill_id.value)  # Store .value
        msg_val: str = f"Skill Unlocked: {skill_def['name']}"
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        set_active_prompt_message("Error: Not enough skill points.")
        add_message_to_log(
            f"Skill unlock failed for {skill_id.value}: Need {cost_val}, Has {player_inv.skill_points}"
        )
    if game_state_data_cache:
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            game_state_data_cache.get_current_player_region(),
        )


def action_purchase_capacity_upgrade(
    player_inv: PlayerInventory, game_configs: Any
) -> None:
    global game_state_data_cache, player_inventory_cache, game_configs_data_cache
    upgrade_def: Optional[Dict[str, Any]] = game_configs.UPGRADE_DEFINITIONS.get(
        "EXPANDED_CAPACITY"
    )
    if not upgrade_def:
        set_active_prompt_message("Error: Upgrade data unavailable.")
        add_message_to_log("Capacity upgrade failed: Definition not found.")
        return
    num_purchased_val: int = player_inv.capacity_upgrades_purchased
    costs_list: List[float] = upgrade_def["costs"]  # type: ignore
    capacity_levels_list: List[int] = upgrade_def["capacity_levels"]  # type: ignore
    max_levels_val: int = len(costs_list)
    if num_purchased_val >= max_levels_val:
        set_active_prompt_message("Capacity fully upgraded.")
        add_message_to_log("Capacity upgrade failed: Already max level.")
        return
    cost_val: float = costs_list[num_purchased_val]
    next_cap_val: int = capacity_levels_list[num_purchased_val]
    if player_inv.cash >= cost_val:
        player_inv.cash -= cost_val
        player_inv.max_capacity = next_cap_val
        player_inv.capacity_upgrades_purchased += 1
        msg_val: str = f"Capacity upgraded to {next_cap_val} units!"
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        set_active_prompt_message(f"Error: Not enough cash. Need ${cost_val:,.0f}.")
        add_message_to_log(
            f"Capacity upgrade failed: Need ${cost_val:,.0f}, Has ${player_inv.cash:,.0f}"
        )
    if game_state_data_cache:
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            game_state_data_cache.get_current_player_region(),
        )


def action_purchase_secure_phone(
    player_inv: PlayerInventory, game_configs: Any
) -> None:
    global current_view, game_state_data_cache, player_inventory_cache, game_configs_data_cache
    if player_inv.has_secure_phone:
        set_active_prompt_message("Secure Phone already owned.")
        add_message_to_log("Secure phone purchase failed: Already owned.")
        return
    upgrade_def: Optional[Dict[str, Any]] = game_configs.UPGRADE_DEFINITIONS.get(
        "SECURE_PHONE"
    )
    if not upgrade_def:
        set_active_prompt_message("Error: Upgrade data unavailable.")
        add_message_to_log("Secure phone purchase failed: Definition not found.")
        return
    cost_val: float = upgrade_def["cost"]  # type: ignore
    if player_inv.cash >= cost_val:
        player_inv.cash -= cost_val
        player_inv.has_secure_phone = True
        msg_val: str = "Secure Phone purchased!"
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        set_active_prompt_message(f"Error: Not enough cash. Need ${cost_val:,0f}.")
        add_message_to_log(
            f"Secure phone purchase failed: Need ${cost_val:,0f}, Has ${player_inv.cash:,.0f}"
        )
    current_view = "tech_contact"
    if game_state_data_cache:
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            game_state_data_cache.get_current_player_region(),
        )


def action_collect_staking_rewards(player_inv: PlayerInventory) -> None:
    global game_state_data_cache, player_inventory_cache, game_configs_data_cache
    rewards_to_collect_val: float = player_inv.staked_drug_coin.get(
        "pending_rewards", 0.0
    )
    if rewards_to_collect_val > 1e-9:  # Use a small epsilon for float comparison
        player_inv.add_crypto(CryptoCoin.DRUG_COIN, rewards_to_collect_val)
        player_inv.staked_drug_coin["pending_rewards"] = 0.0
        msg_val: str = f"Collected {rewards_to_collect_val:.4f} DC staking rewards."
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        set_active_prompt_message("No staking rewards to collect.")
        add_message_to_log("Collect staking rewards: No rewards available.")
    if game_state_data_cache:
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            game_state_data_cache.get_current_player_region(),
        )


def action_initiate_tech_operation(operation_type: str) -> None:
    global current_view, tech_transaction_in_progress, coin_for_tech_transaction, tech_input_string, game_state_data_cache, player_inventory_cache, game_configs_data_cache
    add_message_to_log(f"Initiating tech operation: {operation_type}")
    tech_transaction_in_progress = operation_type
    tech_input_string = ""
    if operation_type == "collect_dc_rewards":
        action_collect_staking_rewards(player_inventory_cache)
        return  # type: ignore
    elif operation_type in ["buy_crypto", "sell_crypto", "stake_dc", "unstake_dc"]:
        current_view = "tech_input_coin_select"
        set_active_prompt_message("Select cryptocurrency.")
    elif operation_type == "launder_cash":
        coin_for_tech_transaction = None
        current_view = "tech_input_amount"
        set_active_prompt_message("Enter cash amount to launder.")
    elif operation_type == "buy_ghost_network":
        action_purchase_ghost_network(player_inventory_cache, game_configs_data_cache)
        return  # type: ignore
    if game_state_data_cache:
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            game_state_data_cache.get_current_player_region(),
        )


def action_tech_select_coin(coin: CryptoCoin) -> None:
    global current_view, coin_for_tech_transaction, tech_transaction_in_progress, game_state_data_cache, player_inventory_cache, game_configs_data_cache
    verb: str = (
        tech_transaction_in_progress.split("_")[0]
        if tech_transaction_in_progress
        else "transact"
    )
    add_message_to_log(f"Tech operation coin selected: {coin.value} for {verb}")
    coin_for_tech_transaction = coin
    current_view = "tech_input_amount"
    set_active_prompt_message(f"Enter amount of {coin.value} to {verb}.")
    if game_state_data_cache:
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            game_state_data_cache.get_current_player_region(),
        )


def action_purchase_ghost_network(
    player_inv: PlayerInventory, game_configs: Any
) -> None:
    global current_view, game_state_data_cache, player_inventory_cache, game_configs_data_cache
    skill_id_val: SkillID = SkillID.GHOST_NETWORK_ACCESS
    cost_dc_val: float = getattr(game_configs, "GHOST_NETWORK_ACCESS_COST_DC", 50.0)
    if skill_id_val.value in player_inv.unlocked_skills:  # Check .value
        set_active_prompt_message("Ghost Network access already acquired.")
        add_message_to_log("Ghost Network purchase failed: Already acquired.")
    elif player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0) >= cost_dc_val:
        player_inv.remove_crypto(CryptoCoin.DRUG_COIN, cost_dc_val)
        player_inv.unlocked_skills.add(skill_id_val.value)  # Store .value
        msg_val: str = f"Ghost Network access purchased for {cost_dc_val:.2f} DC."
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        set_active_prompt_message(f"Error: Not enough DC. Need {cost_dc_val:.2f} DC.")
        add_message_to_log(
            f"Ghost Network purchase failed: Need {cost_dc_val:.2f} DC, Has {player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0):.2f} DC."
        )
    current_view = "tech_contact"
    if game_state_data_cache:
        setup_buttons(
            game_state_data_cache,
            player_inventory_cache,
            game_configs_data_cache,
            game_state_data_cache.get_current_player_region(),
        )


def _validate_tech_amount(input_str: str) -> Optional[float]:
    original_input_val: str = input_str
    if not input_str.replace(".", "", 1).isdigit():
        errmsg_val: str = "Error: Invalid amount. Must be a number."
        set_active_prompt_message(errmsg_val)
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: '{original_input_val}'"
        )
        return None
    try:
        amount_val: float = float(input_str)
    except ValueError:
        errmsg_val: str = "Error: Could not convert amount to number."
        set_active_prompt_message(errmsg_val)
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: '{original_input_val}'"
        )
        return None
    if amount_val <= 1e-9:  # Epsilon for float comparison
        errmsg_val: str = "Error: Amount must be a positive number."
        set_active_prompt_message(errmsg_val)
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: {amount_val}"
        )
        return None
    return amount_val


def _calculate_tech_heat(player_inv: PlayerInventory, game_configs: Any) -> int:
    base_heat_val: int = game_configs.HEAT_FROM_CRYPTO_TRANSACTION
    effective_heat_val: float = float(
        base_heat_val
    )  # Start as float for multiplications
    if SkillID.DIGITAL_FOOTPRINT.value in player_inv.unlocked_skills:  # Check .value
        effective_heat_val *= (
            1.0 - game_configs.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT
        )
    if player_inv.has_secure_phone:
        effective_heat_val *= 1.0 - game_configs.SECURE_PHONE_HEAT_REDUCTION_PERCENT
    return int(round(effective_heat_val))


def action_confirm_tech_operation(
    player_inv: PlayerInventory, game_state: GameState, game_configs: Any
) -> None:
    global tech_input_string, tech_transaction_in_progress, coin_for_tech_transaction, current_view
    amount_val: Optional[float] = _validate_tech_amount(tech_input_string)
    if amount_val is None:
        tech_input_string = ""
        setup_buttons(
            game_state, player_inv, game_configs, game_state.get_current_player_region()
        )
        return

    effective_heat_val: int = _calculate_tech_heat(player_inv, game_configs)
    current_player_region_obj: Optional[Region] = game_state.get_current_player_region()
    region_name_str_val: str = (
        current_player_region_obj.name.value
        if current_player_region_obj
        and hasattr(current_player_region_obj.name, "value")
        else (
            current_player_region_obj.name
            if current_player_region_obj
            else "Unknown Region"
        )
    )

    success_flag: bool = False
    log_prefix_str: str = (
        f"Tech op '{tech_transaction_in_progress}' for {amount_val:.4f} {coin_for_tech_transaction.value if coin_for_tech_transaction else 'cash'}: "
    )
    msg_str: str = ""

    if tech_transaction_in_progress == "buy_crypto" and coin_for_tech_transaction:
        price_val: float = game_state.current_crypto_prices.get(
            coin_for_tech_transaction, 0.0
        )
        fee_val: float = (
            amount_val
            * price_val
            * game_configs.TECH_CONTACT_SERVICES["CRYPTO_TRADE"]["fee_buy_sell"]
        )
        total_cost_val: float = amount_val * price_val + fee_val
        if price_val <= 1e-9:
            msg_str = "Error: Price unavailable."
        elif player_inv.cash >= total_cost_val:
            player_inv.cash -= total_cost_val
            player_inv.add_crypto(coin_for_tech_transaction, amount_val)
            msg_str = f"Bought {amount_val:.4f} {coin_for_tech_transaction.value}. Heat +{effective_heat_val} in {region_name_str_val}."
            success_flag = True
        else:
            msg_str = f"Error: Not enough cash. Need ${total_cost_val:.2f}"
    elif tech_transaction_in_progress == "sell_crypto" and coin_for_tech_transaction:
        price_val: float = game_state.current_crypto_prices.get(
            coin_for_tech_transaction, 0.0
        )
        gross_proceeds_val: float = amount_val * price_val
        fee_val: float = (
            gross_proceeds_val
            * game_configs.TECH_CONTACT_SERVICES["CRYPTO_TRADE"]["fee_buy_sell"]
        )
        net_proceeds_val: float = gross_proceeds_val - fee_val
        if price_val <= 1e-9:
            msg_str = "Error: Price unavailable."
        elif player_inv.crypto_wallet.get(coin_for_tech_transaction, 0.0) >= amount_val:
            player_inv.remove_crypto(coin_for_tech_transaction, amount_val)
            player_inv.cash += net_proceeds_val
            msg_str = f"Sold {amount_val:.4f} {coin_for_tech_transaction.value}. Heat +{effective_heat_val} in {region_name_str_val}."
            success_flag = True
        else:
            msg_str = f"Error: Not enough {coin_for_tech_transaction.value}."
    elif tech_transaction_in_progress == "launder_cash":
        fee_val: float = (
            amount_val * game_configs.TECH_CONTACT_SERVICES["LAUNDER_CASH"]["fee"] # Assuming TECH_CONTACT_SERVICES is in game_configs
        )
        total_cost_val: float = amount_val + fee_val
        launder_heat_val: int = int(
            amount_val * game_configs.LAUNDERING_HEAT_FACTOR_PER_CASH_UNIT # Using new constant
        )
        if player_inv.cash >= total_cost_val:
            player_inv.cash -= total_cost_val
            player_inv.pending_laundered_sc = (
                player_inv.pending_laundered_sc + amount_val
                if hasattr(player_inv, "pending_laundered_sc")
                else amount_val
            )
            player_inv.pending_laundered_sc_arrival_day = (
                game_state.current_day + game_configs.LAUNDERING_DELAY_DAYS
            )
            msg_str = f"Laundered ${amount_val:,.2f}. Fee ${fee_val:,.2f}. Arrives day {player_inv.pending_laundered_sc_arrival_day}. Heat +{launder_heat_val} in {region_name_str_val}."
            effective_heat_val = (
                launder_heat_val  # Override crypto heat with specific laundering heat
            )
            success_flag = True
        else:
            msg_str = (
                f"Error: Not enough cash for amount + fee. Need ${total_cost_val:.2f}"
            )
    elif (
        tech_transaction_in_progress == "stake_dc"
        and coin_for_tech_transaction == CryptoCoin.DRUG_COIN
    ):
        if player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0) >= amount_val:
            player_inv.remove_crypto(CryptoCoin.DRUG_COIN, amount_val)
            player_inv.staked_drug_coin["staked_amount"] = (
                player_inv.staked_drug_coin.get("staked_amount", 0.0) + amount_val
            )
            msg_str = f"Staked {amount_val:.4f} DC."
            success_flag = True
        else:
            msg_str = f"Error: Not enough {CryptoCoin.DRUG_COIN.value}."
    elif (
        tech_transaction_in_progress == "unstake_dc"
        and coin_for_tech_transaction == CryptoCoin.DRUG_COIN
    ):
        if player_inv.staked_drug_coin.get("staked_amount", 0.0) >= amount_val:
            player_inv.staked_drug_coin["staked_amount"] -= amount_val
            pending_rewards_val: float = player_inv.staked_drug_coin.get(
                "pending_rewards", 0.0
            )
            player_inv.add_crypto(
                CryptoCoin.DRUG_COIN, amount_val + pending_rewards_val
            )
            player_inv.staked_drug_coin["pending_rewards"] = 0.0
            msg_str = f"Unstaked {amount_val:.4f} DC. Rewards collected: {pending_rewards_val:.4f} DC."
            success_flag = True
        else:
            msg_str = f"Error: Not enough staked {CryptoCoin.DRUG_COIN.value}."

    if success_flag:
        show_event_message_external(msg_str)
        add_message_to_log(log_prefix_str + msg_str)
        if (
            effective_heat_val > 0
            and tech_transaction_in_progress
            in ["buy_crypto", "sell_crypto", "launder_cash"]
            and current_player_region_obj
        ):
            current_player_region_obj.modify_heat(effective_heat_val)
            add_message_to_log(
                f"Applied heat: +{effective_heat_val} in {region_name_str_val} for {tech_transaction_in_progress}"
            )
        current_view = "tech_contact"
        tech_input_string = ""
        tech_transaction_in_progress = None
    else:
        set_active_prompt_message(msg_str if msg_str else "Error: Transaction failed.")
        add_message_to_log(
            log_prefix_str + (msg_str if msg_str else "Failed - Unknown reason.")
        )
        if amount_val is None:
            tech_input_string = ""  # Clear input if validation failed

    setup_buttons(game_state, player_inv, game_configs, current_player_region_obj)


# --- Button Creation Helper Functions & UI Setup ---
def _create_action_button(
    text: str,
    action: Callable[[], None],
    x: int,
    y: int,
    width: int,
    height: int,
    font: pygame.font.Font = FONT_MEDIUM,
    is_enabled: bool = True,
) -> Button:
    return Button(x, y, width, height, text, action, is_enabled=is_enabled, font=font)


def _create_back_button(
    action: Callable[[], None] = action_open_main_menu, text: str = "Back"
) -> Button:
    return Button(
        UI_CONSTANTS.SCREEN_WIDTH - UI_CONSTANTS.STD_BUTTON_WIDTH - UI_CONSTANTS.LARGE_PADDING,
        UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.STD_BUTTON_HEIGHT - UI_CONSTANTS.LARGE_PADDING,
        UI_CONSTANTS.STD_BUTTON_WIDTH,
        UI_CONSTANTS.STD_BUTTON_HEIGHT,
        text,
        action,
        font=FONT_SMALL, # FONT_SMALL is from ui_theme
    )


def _create_button_list_vertical(
    start_x: int,
    start_y: int,
    button_width: int,
    button_height: int,
    spacing: int,
    button_definitions: List[
        Tuple[str, Callable[[], None], Optional[Callable[[], bool]]]
    ],
) -> List[Button]:
    buttons_list: List[Button] = []
    for i, (text_val, action_val, enabled_check_val) in enumerate(button_definitions):
        y_pos_val: int = start_y + i * (button_height + spacing)
        is_enabled_val: bool = enabled_check_val() if enabled_check_val else True
        buttons_list.append(
            Button(
                start_x,
                y_pos_val,
                button_width,
                button_height,
                text_val,
                action_val,
                is_enabled=is_enabled_val,
                font=FONT_SMALL,
            )
        )
    return buttons_list


def _get_active_buttons(
    current_view_local: str,
    game_state: GameState,
    player_inv: PlayerInventory,
    game_configs: Any,
    current_region: Optional[Region],
) -> List[Button]:  # current_region can be None
    global main_menu_buttons, market_view_buttons, market_buy_sell_buttons, inventory_view_buttons, travel_view_buttons, tech_contact_view_buttons, skills_view_buttons, upgrades_view_buttons, transaction_input_buttons, blocking_event_popup_buttons, active_blocking_event_data, game_over_buttons, game_over_message, informant_view_buttons
    # Clear all button lists
    for btn_list in [
        main_menu_buttons,
        market_view_buttons,
        market_buy_sell_buttons,
        inventory_view_buttons,
        travel_view_buttons,
        tech_contact_view_buttons,
        skills_view_buttons,
        upgrades_view_buttons,
        transaction_input_buttons,
        blocking_event_popup_buttons,
        game_over_buttons,
        informant_view_buttons,
    ]:
        btn_list.clear()

    button_width, button_height, spacing, start_x, start_y = (
        UI_CONSTANTS.STD_BUTTON_WIDTH,
        UI_CONSTANTS.STD_BUTTON_HEIGHT,
        UI_CONSTANTS.STD_BUTTON_SPACING,
        UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.STD_BUTTON_WIDTH // 2,
        120, # TODO: Consider making this a constant e.g., UI_CONSTANTS.MENU_START_Y
    )
    current_player_region_obj: Optional[Region] = (
        game_state.get_current_player_region()
    )

    if current_view_local == "game_over":
        popup_width_val = UI_CONSTANTS.SCREEN_WIDTH * UI_CONSTANTS.POPUP_WIDTH_RATIO
        popup_height_val = UI_CONSTANTS.SCREEN_HEIGHT * UI_CONSTANTS.POPUP_HEIGHT_RATIO
        btn_w_val, btn_h_val = UI_CONSTANTS.POPUP_BUTTON_WIDTH, UI_CONSTANTS.POPUP_BUTTON_HEIGHT
        popup_x_val, popup_y_val = (UI_CONSTANTS.SCREEN_WIDTH - popup_width_val) / 2, (
            UI_CONSTANTS.SCREEN_HEIGHT - popup_height_val
        ) / 2
        btn_x_val, btn_y_val = (
            popup_x_val + (popup_width_val - btn_w_val) / 2,
            popup_y_val + popup_height_val - btn_h_val - UI_CONSTANTS.POPUP_BUTTON_MARGIN_Y,
        )
        game_over_buttons.append(
            _create_action_button(
                "Exit Game",
                lambda: sys.exit(),
                int(btn_x_val),
                int(btn_y_val),
                btn_w_val,
                btn_h_val,
                font=FONT_MEDIUM,
            )
        )
        return game_over_buttons

    if current_view_local == "main_menu":
        actions_defs: List[
            Tuple[str, Callable[[], None], Optional[Callable[[GameState], bool]]]
        ] = [  # Added GameState to lambda signature
            ("Market", action_open_market, None),
            ("Inventory", action_open_inventory, None),
            ("Travel", action_open_travel, None),
            ("Tech Contact", action_open_tech_contact, None),
            (
                "Meet Informant",
                action_open_informant,
                lambda gs: (
                    gs.informant_unavailable_until_day is None
                    or gs.current_day >= gs.informant_unavailable_until_day
                ),
            ),
            ("Skills", action_open_skills, None),
            ("Upgrades", action_open_upgrades, None),
        ]
        col1_count: int = UI_CONSTANTS.MAIN_MENU_COL1_COUNT
        for i, (text_val, action_val, enabled_check_func) in enumerate(actions_defs):
            col_val, row_in_col_val = (0, i) if i < col1_count else (1, i - col1_count)
            x_pos_val: int = start_x + col_val * (button_width + spacing)
            y_pos_val: int = start_y + row_in_col_val * (button_height + spacing)
            if col_val == 1 and row_in_col_val == 0: # If second column and first button in that column
                y_pos_val = start_y # Align with the top of the first column
            is_enabled_val: bool = (
                enabled_check_func(game_state) if enabled_check_func else True # Pass game_state to lambda
            )
            main_menu_buttons.append(
                _create_action_button(
                    text_val,
                    action_val,
                    x_pos_val,
                    y_pos_val,
                    button_width,
                    button_height,
                    is_enabled=is_enabled_val,
                )
            )
        return main_menu_buttons

    elif current_view_local == "blocking_event_popup":
        if active_blocking_event_data:
            popup_w_val = UI_CONSTANTS.SCREEN_WIDTH * UI_CONSTANTS.POPUP_WIDTH_RATIO # Adjusted to use POPUP_WIDTH_RATIO
            popup_h_val = UI_CONSTANTS.SCREEN_HEIGHT * UI_CONSTANTS.POPUP_HEIGHT_RATIO # Adjusted to use POPUP_HEIGHT_RATIO
            popup_x_val, popup_y_val = (UI_CONSTANTS.SCREEN_WIDTH - popup_w_val) / 2, (
                UI_CONSTANTS.SCREEN_HEIGHT - popup_h_val
            ) / 2
            btn_txt_val: str = active_blocking_event_data.get("button_text", "Continue")
            btn_w_val, btn_h_val = UI_CONSTANTS.POPUP_BUTTON_WIDTH, UI_CONSTANTS.POPUP_BUTTON_HEIGHT
            btn_x_val, btn_y_val = (
                popup_x_val + (popup_w_val - btn_w_val) / 2,
                popup_y_val + popup_h_val - btn_h_val - UI_CONSTANTS.POPUP_BUTTON_MARGIN_Y, # Used POPUP_BUTTON_MARGIN_Y
            )
            blocking_event_popup_buttons.append(
                _create_action_button(
                    btn_txt_val,
                    action_close_blocking_event_popup,
                    int(btn_x_val),
                    int(btn_y_val),
                    btn_w_val,
                    btn_h_val,
                    font=FONT_SMALL,
                )
            )
        return blocking_event_popup_buttons
    # ... (other views will follow similar pattern of type hinting local vars)
    elif current_view_local == "market" and current_player_region_obj:
        market_view_buttons.append(_create_back_button())
        # ... (rest of market button creation)
        return (
            market_view_buttons + market_buy_sell_buttons
        )  # Ensure market_buy_sell_buttons is also cleared and populated
    # Add other elif branches for different views as needed
    return []  # Default empty list


def setup_buttons(
    game_state: GameState,
    player_inv: PlayerInventory,
    game_configs: Any,
    current_region: Optional[Region],
) -> None:
    """Sets up the active buttons for the current view."""
    global active_buttons_list_current_view, current_view
    active_buttons_list_current_view = _get_active_buttons(current_view, game_state, player_inv, game_configs, current_region)  # type: ignore


# --- Main Game Loop ---
def game_loop(
    player_inventory: PlayerInventory,
    initial_current_region: Optional[Region],
    game_state_ext: GameState,
    game_configs_ext: Any,
) -> None:
    """The main game loop."""
    global current_view, game_state_data_cache, game_configs_data_cache, player_inventory_cache, quantity_input_string, tech_input_string, active_prompt_message, prompt_message_timer, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, current_transaction_type, input_box_rect, tech_transaction_in_progress, coin_for_tech_transaction, tech_input_box_rect, active_blocking_event_data, game_over_message, game_over_buttons, active_buttons_list_current_view

    game_state_data_cache = game_state_ext
    game_configs_data_cache = game_configs_ext
    player_inventory_cache = player_inventory

    if (
        not hasattr(game_state_data_cache, "current_player_region")
        or game_state_data_cache.current_player_region is None
    ):  # Ensure current_player_region is set
        game_state_data_cache.current_player_region = (
            initial_current_region
            if initial_current_region
            else game_state_data_cache.get_current_player_region()
        )  # Fallback if initial is None

    # Ensure current_player_region is a Region object for setup_buttons
    # This check might be redundant if the above line guarantees a Region object or if get_current_player_region always returns one.
    # However, if initial_current_region could be None and get_current_player_region could also return None initially, this is a safeguard.
    # For type safety, ensure setup_buttons can handle Optional[Region] or that a valid Region is always passed.
    # For now, assuming game_state_data_cache.current_player_region will be valid after the above.
    setup_buttons(
        game_state_data_cache,
        player_inventory_cache,
        game_configs_data_cache,
        game_state_data_cache.current_player_region,
    )

    running: bool = True
    while running:
        current_player_region_for_frame: Optional[Region] = (
            game_state_data_cache.current_player_region
        )
        previous_view: str = current_view
        mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()

        if game_over_message is not None and current_view != "game_over":
            previous_view = current_view
            current_view = "game_over"
            setup_buttons(
                game_state_data_cache,
                player_inventory_cache,
                game_configs_data_cache,
                current_player_region_for_frame,
            )

        for event_pygame in pygame.event.get():  # Renamed event to avoid conflict
            if event_pygame.type == pygame.QUIT:
                running = False

            if current_view == "game_over":
                for btn_game_over in game_over_buttons:  # Renamed btn
                    if btn_game_over.handle_event(event_pygame):
                        break
                if (
                    event_pygame.type == pygame.KEYDOWN
                    and event_pygame.key == pygame.K_RETURN
                    and game_over_buttons
                    and game_over_buttons[0].action
                ):
                    game_over_buttons[0].action()  # sys.exit()
                continue

            if current_view == "blocking_event_popup":
                for btn_popup in blocking_event_popup_buttons:  # Renamed button
                    if btn_popup.handle_event(event_pygame):
                        if previous_view != current_view:
                            setup_buttons(
                                game_state_data_cache,
                                player_inventory_cache,
                                game_configs_data_cache,
                                current_player_region_for_frame,
                            )
                        break
                if (
                    event_pygame.type == pygame.KEYDOWN
                    and event_pygame.key == pygame.K_RETURN
                    and blocking_event_popup_buttons
                    and blocking_event_popup_buttons[0].action
                ):
                    blocking_event_popup_buttons[0].action()
                    if previous_view != current_view:
                        setup_buttons(
                            game_state_data_cache,
                            player_inventory_cache,
                            game_configs_data_cache,
                            current_player_region_for_frame,
                        )
                continue

            is_market_input_active_local: bool = (
                current_view == "market_buy_input"
                or current_view == "market_sell_input"
            )  # Renamed local var
            is_tech_input_active_local: bool = (
                current_view == "tech_input_amount"
            )  # Renamed local var
            if event_pygame.type == pygame.KEYDOWN:
                if event_pygame.key == pygame.K_ESCAPE:
                    if is_market_input_active_local or is_tech_input_active_local:
                        action_cancel_transaction()
                    else:
                        action_open_main_menu()
                if is_market_input_active_local:
                    if event_pygame.key == pygame.K_RETURN:
                        action_confirm_transaction(player_inventory_cache, current_player_region_for_frame, game_state_data_cache)  # type: ignore
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        quantity_input_string = quantity_input_string[:-1]
                    elif event_pygame.unicode.isdigit():
                        quantity_input_string += event_pygame.unicode
                elif is_tech_input_active_local:
                    if event_pygame.key == pygame.K_RETURN:
                        action_confirm_tech_operation(
                            player_inventory_cache,
                            game_state_data_cache,
                            game_configs_data_cache,
                        )
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        tech_input_string = tech_input_string[:-1]
                    elif event_pygame.unicode.isdigit() or (
                        event_pygame.unicode == "." and "." not in tech_input_string
                    ):
                        tech_input_string += event_pygame.unicode

            button_clicked_and_view_changed_flag: bool = False  # Renamed
            if current_view not in ["game_over", "blocking_event_popup"]:
                for btn_active in active_buttons_list_current_view:  # Renamed button
                    if btn_active.handle_event(event_pygame):
                        if previous_view != current_view:
                            button_clicked_and_view_changed_flag = True
                            setup_buttons(
                                game_state_data_cache,
                                player_inventory_cache,
                                game_configs_data_cache,
                                current_player_region_for_frame,
                            )
                        break
            if (
                not button_clicked_and_view_changed_flag
                and previous_view != current_view
            ):
                setup_buttons(
                    game_state_data_cache,
                    player_inventory_cache,
                    game_configs_data_cache,
                    current_player_region_for_frame,
                )

        update_hud_timers_external()
        if prompt_message_timer > 0:
            prompt_message_timer -= 1
        if prompt_message_timer <= 0:
            active_prompt_message = None

        screen.fill(RICH_BLACK)
        # Drawing logic based on current_view
        if current_view == "game_over":
            draw_game_over_view_external(
                screen,
                game_over_message if game_over_message else "Game Over",
                game_over_buttons,
            )
        elif current_view == "main_menu":
            draw_main_menu_external(screen, main_menu_buttons)
        elif current_view == "market" and current_player_region_for_frame:
            draw_market_view_external(screen, current_player_region_for_frame, player_inventory_cache, market_view_buttons, market_buy_sell_buttons)  # type: ignore
        elif current_view == "inventory":
            draw_inventory_view_external(screen, player_inventory_cache, inventory_view_buttons)  # type: ignore
        elif current_view == "travel" and current_player_region_for_frame:
            draw_travel_view_external(
                screen, current_player_region_for_frame, travel_view_buttons
            )
        elif current_view == "informant":
            draw_informant_view_external(screen, player_inventory_cache, informant_view_buttons, game_configs_data_cache)  # type: ignore
        elif current_view in [
            "tech_contact",
            "tech_input_coin_select",
            "tech_input_amount",
        ]:
            tech_ui_state_dict: Dict[str, Any] = {
                "current_view": current_view,
                "tech_transaction_in_progress": tech_transaction_in_progress,
                "coin_for_tech_transaction": coin_for_tech_transaction,
                "tech_input_string": tech_input_string,
                "active_prompt_message": active_prompt_message,
                "prompt_message_timer": prompt_message_timer,
                "tech_input_box_rect": tech_input_box_rect,
            }
            draw_tech_contact_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, tech_contact_view_buttons, tech_ui_state_dict)  # type: ignore
        elif current_view == "skills":
            draw_skills_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, skills_view_buttons)  # type: ignore
        elif current_view == "upgrades":
            draw_upgrades_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, upgrades_view_buttons)  # type: ignore
        elif current_view in ["market_buy_input", "market_sell_input"]:
            transaction_ui_state_dict: Dict[str, Any] = {
                "quantity_input_string": quantity_input_string,
                "drug_for_transaction": drug_for_transaction,
                "quality_for_transaction": quality_for_transaction,
                "price_for_transaction": price_for_transaction,
                "available_for_transaction": available_for_transaction,
                "current_transaction_type": current_transaction_type,
                "active_prompt_message": active_prompt_message,
                "prompt_message_timer": prompt_message_timer,
                "input_box_rect": input_box_rect,
            }
            draw_transaction_input_view_external(
                screen, transaction_input_buttons, transaction_ui_state_dict
            )

        if (
            current_view != "game_over"
            and current_view == "blocking_event_popup"
            and active_blocking_event_data
        ):
            draw_blocking_event_popup_external(
                screen, active_blocking_event_data, blocking_event_popup_buttons
            )

        if (
            current_view != "game_over" and current_player_region_for_frame
        ):  # Ensure region is not None for HUD
            draw_hud_external(screen, player_inventory_cache, current_player_region_for_frame, game_state_data_cache)  # type: ignore

        if (
            active_prompt_message
            and prompt_message_timer > 0
            and current_view not in ["game_over", "blocking_event_popup"]
        ):
            is_prompt_handled_local: bool = (
                current_view
                in ["market_buy_input", "market_sell_input", "tech_input_amount"]
            ) or (
                current_view == "tech_contact"
                and locals().get("tech_ui_state_dict", {}).get("active_prompt_message")
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
            )  # Added default "" for get
            if not is_prompt_handled_local:
                prompt_y_pos_val: int = UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.PROMPT_DEFAULT_Y_OFFSET
                if current_view == "tech_contact":
                    prompt_y_pos_val = UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.PROMPT_TECH_CONTACT_Y_OFFSET
                prompt_color_val: Tuple[int, int, int] = (
                    IMPERIAL_RED # From ui_theme
                    if any(
                        err_word in active_prompt_message
                        for err_word in ["Error", "Invalid", "Not enough"]
                    )
                    else (
                        GOLDEN_YELLOW
                        if "Skill" in active_prompt_message
                        else EMERALD_GREEN
                    )
                )
                draw_text(
                    screen,
                    active_prompt_message,
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
