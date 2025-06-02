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
    ContactID, 
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
from .views.generic_contact_view import draw_generic_contact_view as draw_generic_contact_view_external # Import new view
from . import constants as UI_CONSTANTS 


logger = get_logger(__name__)

pygame.font.init()
pygame.init()
screen = pygame.display.set_mode((UI_CONSTANTS.SCREEN_WIDTH, UI_CONSTANTS.SCREEN_HEIGHT))
pygame.display.set_caption("Project Narco-Syndicate")
clock = pygame.time.Clock()

game_state_data_cache: Optional[GameState] = None
game_configs_data_cache: Optional[Any] = None
player_inventory_cache: Optional[PlayerInventory] = None
ui_manager: Optional[UIManager] = None

from ..mechanics.daily_updates import perform_daily_updates as perform_daily_updates_mechanics, DailyUpdateResult
from ..mechanics.win_conditions import WIN_CONDITION_CHECKS
from ..mechanics.legacy_scenarios import LEGACY_SCENARIO_CHECKS, apply_legacy_scenario_bonus


def action_open_main_menu() -> None:
    ui_manager.current_view = "main_menu"

def action_open_market() -> None:
    ui_manager.current_view = "market"

def action_open_inventory() -> None:
    ui_manager.current_view = "inventory"

def action_open_travel() -> None:
    ui_manager.current_view = "travel"

def action_open_tech_contact() -> None:
    ui_manager.current_view = "tech_contact"

def action_open_skills() -> None:
    ui_manager.current_view = "skills"

def action_open_upgrades() -> None:
    ui_manager.current_view = "upgrades"

def action_open_informant() -> None:
    ui_manager.current_view = "informant"

def action_meet_corrupt_official() -> None:
    add_message_to_log("Attempting to meet Corrupt Official.")
    ui_manager.current_view = "corrupt_official_contact"

def action_meet_forger() -> None:
    add_message_to_log("Attempting to meet The Forger.")
    ui_manager.current_view = "forger_contact"

def action_meet_logistics_expert() -> None:
    add_message_to_log("Attempting to meet Logistics Expert.")
    ui_manager.current_view = "logistics_expert_contact"

def action_close_blocking_event_popup() -> None:
    ui_manager.active_blocking_event_data = None
    ui_manager.current_view = "main_menu"

def action_exit_game() -> None:
    pygame.quit()
    sys.exit()


# --- Quest Specific Actions ---
def action_accept_quest(quest_id_str: str):
    quest_id = QuestID(quest_id_str) # Convert string back to enum
    if quest_manager.accept_quest(player_inventory_cache, game_state_data_cache, quest_id):
        quest_def = quest_manager.get_quest_definition(quest_id)
        show_event_message_external(f"Quest Accepted: {quest_def['title']}")
        add_message_to_log(f"Quest Accepted: {quest_def['title']}")
    else:
        show_event_message_external("Failed to accept quest.") # Should ideally not happen if button is shown correctly
        add_message_to_log(f"Failed to accept quest: {quest_id_str}")
    ui_manager.current_view = "main_menu" # Go back to main menu or contact view

def action_decline_quest(quest_id_str: str):
    quest_id = QuestID(quest_id_str)
    quest_manager.decline_quest(player_inventory_cache, game_state_data_cache, quest_id)
    quest_def = quest_manager.get_quest_definition(quest_id)
    show_event_message_external(f"Quest Declined: {quest_def['title']}")
    add_message_to_log(f"Quest Declined: {quest_def['title']}")
    ui_manager.current_view = "main_menu"

def action_complete_quest_stage(quest_id_str: str):
    quest_id = QuestID(quest_id_str)
    messages = quest_manager.complete_quest_stage(player_inventory_cache, game_state_data_cache, quest_id)
    for msg in messages:
        show_event_message_external(msg)
        add_message_to_log(f"Quest '{quest_id.value}' stage completion: {msg}")
    # Potentially change view or refresh buttons if quest completion alters available actions
    # For now, assume it might return to contact view or main menu via UIManager logic
    # If the quest is now fully complete, it won't be offered again / active quest dialogue changes.
    # We might need to refresh the contact view to show new state.
    # For simplicity, let's assume current view is fine or will be reset by UIManager.
    # If on contact view, need to ensure UIManager re-evaluates quest state for button display.
    if ui_manager.current_view.endswith("_contact"): # If currently in a contact view
        ui_manager.setup_buttons_for_current_view() # Re-setup buttons for current contact view
    else:
        ui_manager.current_view = "main_menu"


def action_search_for_supplies():
    quest_id = QuestID.FORGER_SUPPLY_RUN
    active_quest_data = player_inventory_cache.active_quests.get(quest_id)
    if not active_quest_data or active_quest_data.get("current_stage") != 1:
        show_event_message_external("No active supply run.")
        return

    quest_def = quest_manager.get_quest_definition(quest_id)
    stage_data = quest_manager.get_quest_stage_data(quest_def, 1)
    target_region_name = stage_data.get("target_region_name")
    current_player_region = game_state_data_cache.get_current_player_region()

    if not current_player_region or current_player_region.name != target_region_name:
        show_event_message_external(f"You need to be in {target_region_name.value if target_region_name else 'the target region'} to find supplies.")
        return

    # Simple success for now
    item_name = stage_data.get("objective_item")
    quantity_needed = stage_data.get("objective_quantity")
    
    if quest_manager.acquire_special_item(player_inventory_cache, item_name, quantity_needed):
        show_event_message_external(f"You found all {quantity_needed} units of {item_name}!")
        add_message_to_log(f"Acquired {quantity_needed} {item_name} for quest {quest_id.value}.")
        # The "Search for Supplies" button on main menu should now disappear as condition changes
        # (or could be made to only give once)
    else:
        # This path shouldn't be hit if acquire_special_item always returns True
        show_event_message_external(f"Failed to acquire {item_name}.")


# --- Main Game Loop Actions ---
def action_resolve_opportunity_event_choice(choice_index: int):
    """Resolves the player's choice for an opportunity event."""
    event_data = ui_manager.active_blocking_event_data # This holds the opportunity event details
    if not event_data or not event_data.get("is_opportunity_event"):
        add_message_to_log("Error: No active opportunity event to resolve or invalid event data.")
        ui_manager.active_blocking_event_data = None # Clear it to be safe
        ui_manager.current_view = "main_menu" # Go back to main menu
        return

    choices = event_data.get("choices", [])
    if choice_index >= len(choices):
        add_message_to_log(f"Error: Invalid choice index {choice_index} for event {event_data.get('title')}.")
        ui_manager.active_blocking_event_data = None
        ui_manager.current_view = "main_menu"
        return

    selected_choice = choices[choice_index]
    outcomes = selected_choice.get("outcomes", [])
    runtime_params = event_data.get("runtime_params", {}) # Get runtime params
    
    # Determine outcome based on chance
    resolved_outcome = None
    if outcomes:
        if len(outcomes) == 1 and "chance" not in outcomes[0]:
            resolved_outcome = outcomes[0]
        else:
            roll = random.random()
            cumulative_chance = 0.0
            for outcome_data in outcomes:
                cumulative_chance += outcome_data.get("chance", 1.0) # Default to 1.0 if no chance specified
                if roll < cumulative_chance:
                    resolved_outcome = outcome_data
                    break
        if not resolved_outcome: # Fallback if chances don't sum to 1 or other issue
             resolved_outcome = outcomes[0] if outcomes else {"type": "nothing", "message": "Nothing particular happens."}


    outcome_type = resolved_outcome.get("type")
    outcome_params = resolved_outcome.get("params", {})
    outcome_message_template = resolved_outcome.get("message", "...")

    # Apply outcome effects
    log_details = [f"Opportunity Event '{event_data.get('title')}', Choice '{selected_choice.get('text')}'. Outcome: {outcome_type}"]
    
    # Prepare message format dictionary
    message_format_params = runtime_params.copy() # Start with runtime params
    message_format_params["region_name"] = game_state_data_cache.get_current_player_region().name.value if game_state_data_cache.get_current_player_region() else "this area"


    if outcome_type == "give_drugs":
        drug_name = runtime_params.get("drug_name", DrugName.PILLS) # Fallback, should be in runtime_params for RIVAL_STASH
        quantity_range = outcome_params.get("quantity_range", (5,10))
        quantity = random.randint(*quantity_range)
        quality = DrugQuality.STANDARD # Default for now
        
        if player_inventory_cache.add_drug(drug_name, quality, quantity):
            message_format_params["quantity_stolen"] = quantity
            message_format_params["drug_name_stolen"] = drug_name.value
            log_details.append(f"Gave {quantity} {drug_name.value} ({quality.name}).")
        else:
            outcome_message_template = "You found the stash, but had no room to carry it!"
            log_details.append(f"Attempted to give {quantity} {drug_name.value}, but no inventory space.")

    elif outcome_type == "change_heat":
        amount_range = outcome_params.get("amount_range", (5,10))
        amount = random.randint(*amount_range)
        if game_state_data_cache.current_player_region:
            game_state_data_cache.current_player_region.modify_heat(amount)
            message_format_params["heat_change"] = amount
            log_details.append(f"Heat changed by {amount} in {game_state_data_cache.current_player_region.name.value}.")

    elif outcome_type == "lose_cash":
        amount_range = outcome_params.get("amount_range", (100,200))
        amount = random.randint(*amount_range)
        actual_lost = min(player_inventory_cache.cash, float(amount))
        player_inventory_cache.cash -= actual_lost
        message_format_params["cash_lost"] = f"${actual_lost:,.0f}"
        log_details.append(f"Lost ${actual_lost:,.0f}.")

    elif outcome_type == "resolve_delivery": # Specific to URGENT_DELIVERY
        # Requires runtime_params: drug_name, quality, quantity, target_region_name, reward_per_unit, total_base_value
        if player_inventory_cache.get_quantity(runtime_params["drug_name"], runtime_params["quality"]) >= runtime_params["quantity"]:
            player_inventory_cache.remove_drug(runtime_params["drug_name"], runtime_params["quality"], runtime_params["quantity"])
            total_premium = runtime_params["quantity"] * runtime_params["reward_per_unit"]
            # Assume base value is also given, or add it to reward_per_unit before calculating total_premium
            # For now, total_premium is just the bonus over normal sale.
            # The event could also give the full sale price + premium. Let's assume it's just the premium.
            player_inventory_cache.cash += total_premium 
            # If it's full sale price + premium, it would be: player_inventory_cache.cash += runtime_params["total_base_value"] + total_premium
            message_format_params["total_premium"] = f"${total_premium:,.2f}"
            log_details.append(f"Urgent delivery completed. Drugs: {runtime_params['quantity']} {runtime_params['drug_name'].value}. Premium: ${total_premium:.2f}")
        else:
            outcome_message_template = "You accepted, but didn't have the required drugs!"
            log_details.append("Urgent delivery failed: Insufficient drugs.")
            
    elif outcome_type == "give_drugs_experimental": # Specific to EXPERIMENTAL_DRUG_BATCH
        cost = runtime_params.get("cost", 0)
        if player_inventory_cache.cash >= cost:
            player_inventory_cache.cash -= cost
            base_quantity = runtime_params.get("quantity_base", 10)
            quantity_multiplier = outcome_params.get("quantity_multiplier", 1.0)
            quality_outcome = outcome_params.get("quality_outcome", DrugQuality.STANDARD)
            drug_name_exp = runtime_params.get("drug_name", DrugName.PILLS)
            
            quantity_received = int(base_quantity * quantity_multiplier)
            
            if player_inventory_cache.add_drug(drug_name_exp, quality_outcome, quantity_received):
                message_format_params["quantity_received"] = quantity_received
                message_format_params["drug_name"] = drug_name_exp.value
                log_details.append(f"Bought experimental batch: {quantity_received} {drug_name_exp.value} ({quality_outcome.name}) for ${cost:.2f}.")
                if "side_effect_heat" in outcome_params and game_state_data_cache.current_player_region:
                    heat_increase = outcome_params["side_effect_heat"]
                    game_state_data_cache.current_player_region.modify_heat(heat_increase)
                    message_format_params["heat_increase"] = heat_increase
                    log_details.append(f"Side effect: Heat +{heat_increase} in {game_state_data_cache.current_player_region.name.value}")
            else:
                outcome_message_template = "You bought the batch, but had no room for the drugs!"
                player_inventory_cache.cash += cost # Refund
                log_details.append(f"Experimental batch purchase failed: No inventory space. Cost ${cost:.2f} refunded.")
        else:
            outcome_message_template = "You wanted to buy, but couldn't afford the batch."
            log_details.append(f"Experimental batch purchase failed: Not enough cash. Needed ${cost:.2f}.")


    final_message = outcome_message_template.format(**message_format_params)
    show_event_message_external(final_message)
    add_message_to_log(". ".join(log_details))

    ui_manager.active_blocking_event_data = None # Clear the event
    ui_manager.current_view = "main_menu" # Or the view before the popup
    # ui_manager.setup_buttons_for_current_view() # Let main loop handle this due to view change


def action_travel_to_region(
    destination_region: Region,
    player_inv_arg: PlayerInventory, 
    game_state_instance_arg: GameState, 
) -> None:
    if ui_manager.game_over_message is not None:
        return
    add_message_to_log(
        f"Attempting to travel to {destination_region.name.value}."
    )

    game_state_data_cache.set_current_player_region(destination_region.name)
    game_state_data_cache.current_day += 1
    add_message_to_log(f"Advanced day to {game_state_data_cache.current_day}.")

    daily_result: DailyUpdateResult = perform_daily_updates_mechanics(
        game_state_data_cache,
        player_inventory_cache,
        game_configs_data_cache
    )

    for msg in daily_result.ui_messages:
        show_event_message_external(msg)
    for msg in daily_result.log_messages:
        add_message_to_log(msg)

    if daily_result.game_over_message and not ui_manager.game_over_message:
        ui_manager.game_over_message = daily_result.game_over_message
        ui_manager.current_view = "game_over"
        return

    if daily_result.blocking_event_data and not ui_manager.active_blocking_event_data:
        ui_manager.active_blocking_event_data = daily_result.blocking_event_data
        ui_manager.current_view = "blocking_event_popup"
        return

    if daily_result.pending_laundered_sc_processed:
        player_inventory_cache.pending_laundered_sc = daily_result.new_pending_laundered_sc
        player_inventory_cache.pending_laundered_sc_arrival_day = daily_result.new_pending_laundered_sc_arrival_day

    if daily_result.informant_unavailable_until_day is not None:
        game_state_data_cache.informant_unavailable_until_day = daily_result.informant_unavailable_until_day

    if ui_manager.game_over_message or ui_manager.active_blocking_event_data:
        return

    if not game_state_data_cache.game_won:
        for condition_name, check_function in WIN_CONDITION_CHECKS.items():
            if check_function(player_inventory_cache, game_state_data_cache, game_configs_data_cache):
                game_state_data_cache.game_won = True
                game_state_data_cache.win_condition_achieved = condition_name
                ui_manager.game_over_message = f"YOU WON: {condition_name}!"
                add_message_to_log(f"Win condition met: {condition_name}")
                return 
    
    if not game_state_data_cache.game_won:
        for scenario_name_key, scenario_check_func in LEGACY_SCENARIO_CHECKS.items():
            if scenario_name_key not in game_state_data_cache.achieved_legacy_scenarios:
                achieved_scenario_name = scenario_check_func(player_inventory_cache, game_state_data_cache, game_configs_data_cache)
                if achieved_scenario_name:
                    bonus_messages = apply_legacy_scenario_bonus(
                        achieved_scenario_name, 
                        player_inventory_cache, 
                        game_state_data_cache, 
                        game_configs_data_cache
                    )
                    for msg in bonus_messages:
                        show_event_message_external(msg)
                        add_message_to_log(msg)

    if game_state_data_cache.game_won or ui_manager.game_over_message or ui_manager.active_blocking_event_data:
        return

    region_heat_val: int = destination_region.current_heat
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
            ui_manager.active_blocking_event_data = {
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
                player_inventory_cache.cash, 
                float(
                    random.randint(game_configs_data_cache.POLICE_FINE_BASE_MIN, game_configs_data_cache.POLICE_FINE_BASE_MAX)
                    * (1 + destination_region.current_heat // game_configs_data_cache.POLICE_FINE_HEAT_DIVISOR)
                ),
            )
            player_inventory_cache.cash -= fine_val
            ui_manager.active_blocking_event_data = {
                "title": "Police Stop - Fine!",
                "messages": [
                    "Police stop for 'random' check.",
                    f"Minor infraction. Fined ${fine_val:,.0f}.",
                ],
                "button_text": "Pay Fine",
            }
            show_event_message_external(f"Paid fine of ${fine_val:,.0f}.")
            add_message_to_log(
                f"Police stop: Fined ${fine_val:,.0f}. Cash remaining: ${player_inventory_cache.cash:.2f}"
            )
            if player_inventory_cache.cash < game_configs_data_cache.BANKRUPTCY_THRESHOLD:
                ui_manager.game_over_message = "GAME OVER: A hefty fine bankrupted you!"
                add_message_to_log(f"{ui_manager.game_over_message} Cash: ${player_inventory_cache.cash:.2f}")
        else:
            total_contraband_units_val: int = sum(
                qty for qualities in player_inventory_cache.items.values() for qty in qualities.values()
            )
            add_message_to_log(
                f"Police stop: Searched. Carrying {total_contraband_units_val} units of contraband."
            )
            if (
                total_contraband_units_val > game_configs_data_cache.POLICE_STOP_CONTRABAND_THRESHOLD_UNITS
                and random.random() < game_configs_data_cache.POLICE_STOP_CONFISCATION_CHANCE
            ):
                player_inventory_cache.items.clear() 
                player_inventory_cache.current_load = 0
                ui_manager.active_blocking_event_data = { 
                    "title": "Police Stop - Major Bust!",
                    "messages": ["Police search vehicle!", "All drugs confiscated!"],
                    "button_text": "Damn!",
                }
                add_message_to_log("Police Stop: Searched, all drugs confiscated.")
            elif total_contraband_units_val > 0:
                ui_manager.active_blocking_event_data = {
                    "title": "Police Stop - Searched!",
                    "messages": [
                        "Police search vehicle!",
                        (
                            "You had contraband, but they missed it!"
                            if total_contraband_units_val > game_configs_data_cache.POLICE_STOP_CONTRABAND_THRESHOLD_UNITS
                            else "Luckily, you were clean enough."
                        ),
                    ],
                    "button_text": "Phew!",
                }
                add_message_to_log("Police stop: Searched, no major confiscation.")
            else:
                ui_manager.active_blocking_event_data = {
                    "title": "Police Stop - Searched!",
                    "messages": ["Police search vehicle!", "Luckily, you were clean."],
                    "button_text": "Phew!",
                }
                add_message_to_log("Police stop: Searched, found nothing.")
        ui_manager.current_view = "blocking_event_popup"
    else:
        show_event_message_external(
            f"Arrived safely in {destination_region.name.value}."
        )
        add_message_to_log(f"Arrived safely in {destination_region.name.value}.")
        ui_manager.current_view = "main_menu"


def action_ask_informant_rumor(
    player_inv_arg: PlayerInventory, game_configs_arg: Any, game_state_instance_arg: GameState
) -> None:
    tip_cost_multiplier = 1.0
    if SkillID.EXPANDED_NETWORK.value in player_inventory_cache.unlocked_skills:
        tip_cost_multiplier -= game_configs_data_cache.SKILL_DEFINITIONS[SkillID.EXPANDED_NETWORK].get('effect_value', 0.0)

    cost: float = game_configs_data_cache.INFORMANT_TIP_COST_RUMOR * tip_cost_multiplier
    
    if player_inventory_cache.cash >= cost:
        player_inventory_cache.cash -= cost
        
        trust_gain = game_configs_data_cache.INFORMANT_TRUST_GAIN_PER_TIP
        if SkillID.BASIC_CONNECTIONS.value in player_inventory_cache.unlocked_skills:
            trust_gain += game_configs_data_cache.SKILL_DEFINITIONS[SkillID.BASIC_CONNECTIONS].get('effect_value', 0)
        
        current_trust = player_inventory_cache.contact_trusts.get(ContactID.INFORMANT, 0)
        player_inventory_cache.contact_trusts[ContactID.INFORMANT] = min(
            current_trust + trust_gain,
            game_configs_data_cache.INFORMANT_MAX_TRUST,
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

def action_ask_informant_rival_status(
    player_inv_arg: PlayerInventory, game_configs_arg: Any, game_state_instance_arg: GameState
) -> None:
    tip_cost_multiplier = 1.0
    if SkillID.EXPANDED_NETWORK.value in player_inventory_cache.unlocked_skills:
        tip_cost_multiplier -= game_configs_data_cache.SKILL_DEFINITIONS[SkillID.EXPANDED_NETWORK].get('effect_value', 0.0)
        
    cost: float = game_configs_data_cache.INFORMANT_TIP_COST_RIVAL_INFO * tip_cost_multiplier

    if player_inventory_cache.cash >= cost:
        player_inventory_cache.cash -= cost

        trust_gain = game_configs_data_cache.INFORMANT_TRUST_GAIN_PER_TIP
        if SkillID.BASIC_CONNECTIONS.value in player_inventory_cache.unlocked_skills:
            trust_gain += game_configs_data_cache.SKILL_DEFINITIONS[SkillID.BASIC_CONNECTIONS].get('effect_value', 0)

        current_trust = player_inventory_cache.contact_trusts.get(ContactID.INFORMANT, 0)
        player_inventory_cache.contact_trusts[ContactID.INFORMANT] = min(
            current_trust + trust_gain,
            game_configs_data_cache.INFORMANT_MAX_TRUST,
        )
        info_parts: List[str] = []
        if game_state_data_cache.ai_rivals:
            active_rivals_list: List[str] = [
                r.name for r in game_state_data_cache.ai_rivals if not r.is_busted
            ]
            busted_rivals_list: List[str] = [
                f"{r.name}({r.busted_days_remaining}d left)"
                for r in game_state_data_cache.ai_rivals
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

def action_ask_informant_drug_info( 
    player_inv_arg: PlayerInventory, game_configs_arg: Any, game_state_instance_arg: GameState
) -> None:
    tip_cost_multiplier = 1.0
    if SkillID.EXPANDED_NETWORK.value in player_inventory_cache.unlocked_skills:
        tip_cost_multiplier -= game_configs_data_cache.SKILL_DEFINITIONS[SkillID.EXPANDED_NETWORK].get('effect_value', 0.0)
    
    cost: float = game_configs_data_cache.INFORMANT_TIP_COST_DRUG_INFO * tip_cost_multiplier

    if player_inventory_cache.cash >= cost:
        player_inventory_cache.cash -= cost
        
        trust_gain = game_configs_data_cache.INFORMANT_TRUST_GAIN_PER_TIP
        if SkillID.BASIC_CONNECTIONS.value in player_inventory_cache.unlocked_skills:
            trust_gain += game_configs_data_cache.SKILL_DEFINITIONS[SkillID.BASIC_CONNECTIONS].get('effect_value', 0)
        
        current_trust = player_inventory_cache.contact_trusts.get(ContactID.INFORMANT, 0)
        player_inventory_cache.contact_trusts[ContactID.INFORMANT] = min(
            current_trust + trust_gain,
            game_configs_data_cache.INFORMANT_MAX_TRUST,
        )
        
        target_drug = random.choice(list(DrugName))
        target_region_obj = random.choice(list(game_state_data_cache.all_regions.values()))
        price_info_type = random.choice(["high", "low", "stable"])
        drug_info_msg = f"Looks like {target_drug.value} prices are {price_info_type} in {target_region_obj.name.value}."
        
        show_event_message_external(f"Informant on drugs: '{drug_info_msg}'")
        add_message_to_log(f"Paid informant ${cost:.0f} for drug info: {drug_info_msg}")
    else:
        ui_manager.set_active_prompt_message(f"Error: Not enough cash. Need ${cost:.0f}.")
        add_message_to_log(f"Failed to buy drug info: Insufficient cash.")

def action_confirm_corrupt_official_bribe(contact_id: ContactID, service_id: str) -> None:
    if contact_id != ContactID.CORRUPT_OFFICIAL or service_id != "REDUCE_HEAT":
        add_message_to_log(f"Error: Corrupt official action called with wrong ID: {contact_id}/{service_id}")
        return

    region = game_state_data_cache.get_current_player_region()
    if not region:
        ui_manager.set_active_prompt_message("Error: No current region data.")
        add_message_to_log("Corrupt official bribe failed: No current region.")
        return

    bribe_cost_base = game_configs_data_cache.CORRUPT_OFFICIAL_BASE_BRIBE_COST
    bribe_cost_heat_component = region.current_heat * game_configs_data_cache.CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT
    bribe_cost = bribe_cost_base + bribe_cost_heat_component

    # Apply seasonal event multiplier for corrupt official bribe cost
    if game_state_data_cache.seasonal_event_effects_active:
        cost_multiplier = game_state_data_cache.seasonal_event_effects_active.get("corrupt_official_bribe_cost_multiplier", 1.0)
        bribe_cost *= cost_multiplier
        if cost_multiplier != 1.0:
            add_message_to_log(f"Corrupt official bribe cost multiplied by {cost_multiplier:.2f} due to seasonal event.")
            
    free_bribe = False
    if SkillID.SYNDICATE_INFLUENCE.value in player_inventory_cache.unlocked_skills:
        if random.random() < game_configs_data_cache.SKILL_DEFINITIONS[SkillID.SYNDICATE_INFLUENCE].get('effect_value', 0.0):
            free_bribe = True
            bribe_cost = 0.0 
            
    if free_bribe:
        msg = f"Syndicate Influence pays off! The official waves off the payment."
        show_event_message_external(msg)
        add_message_to_log(msg)
        heat_reduced = game_configs_data_cache.CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT
        region.modify_heat(-heat_reduced)
        show_event_message_external(f"Regional heat reduced by {heat_reduced}.")
        add_message_to_log(f"Heat in {region.name.value} reduced by {heat_reduced}. New heat: {region.current_heat}")
        player_inventory_cache.contact_trusts[ContactID.CORRUPT_OFFICIAL] = min(
            player_inventory_cache.contact_trusts.get(ContactID.CORRUPT_OFFICIAL, 0) + 5, 100 
        )
    elif player_inventory_cache.cash >= bribe_cost:
        player_inventory_cache.cash -= bribe_cost
        heat_reduced = game_configs_data_cache.CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT
        region.modify_heat(-heat_reduced)
        msg = f"Paid corrupt official ${bribe_cost:,.0f}. Regional heat reduced by {heat_reduced}."
        show_event_message_external(msg)
        add_message_to_log(f"{msg} New heat in {region.name.value}: {region.current_heat}")
        player_inventory_cache.contact_trusts[ContactID.CORRUPT_OFFICIAL] = min(
            player_inventory_cache.contact_trusts.get(ContactID.CORRUPT_OFFICIAL, 0) + 10, 100
        )
    else:
        msg = f"Not enough cash to bribe the official. Need ${bribe_cost:,.0f}."
        ui_manager.set_active_prompt_message(msg)
        add_message_to_log(msg)
    
def action_initiate_buy(
    drug: DrugName, quality: DrugQuality, price: float, available: int
) -> None:
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

def action_initiate_sell(
    drug: DrugName, quality: DrugQuality, price: float, available: int
) -> None:
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

def action_confirm_transaction(
    player_inv_arg: PlayerInventory, 
    market_region_arg: Region, 
    game_state_instance_arg: GameState
) -> None:
    player_inv = player_inventory_cache
    market_region = game_state_data_cache.get_current_player_region()
    game_state_instance = game_state_data_cache

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
        return

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
                    and event_item.target_drug_name == ui_manager.drug_for_transaction 
                    and event_item.target_quality == ui_manager.quality_for_transaction 
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
            ui_manager.current_view = "market" 
        else:
            errmsg = "Error: Transaction failed. Insufficient cash or inventory space."

    elif ui_manager.current_transaction_type == "sell":
        revenue: float = quantity * ui_manager.price_for_transaction
        if player_inventory_cache.process_sell_drug(ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity, revenue):
            market_region.update_stock_on_sell(
                ui_manager.drug_for_transaction, ui_manager.quality_for_transaction, quantity
            )
            region_heat_before = market_region.current_heat
            market_impact.apply_player_sell_impact(
                player_inventory_cache,
                market_region,
                ui_manager.drug_for_transaction, 
                quantity,
                game_configs_data_cache,
                game_state_data_cache, # Pass game_state_data_cache
            )
            heat_generated = market_region.current_heat - region_heat_before
            
            # Legacy Scenario: Regional Baron - Update sales profit for the region
            current_profit_in_region = game_state_data_cache.player_sales_profit_by_region.get(market_region.name, 0.0)
            game_state_data_cache.player_sales_profit_by_region[market_region.name] = current_profit_in_region + revenue
            add_message_to_log(f"Updated sales profit for {market_region.name.value} by ${revenue:.2f}. New total: ${game_state_data_cache.player_sales_profit_by_region[market_region.name]:.2f}")

            log_msg: str = (
                f"Sold {quantity} {ui_manager.drug_for_transaction.value} ({ui_manager.quality_for_transaction.name}) for ${revenue:.2f}. Heat +{max(0, heat_generated)} in {market_region.name.value}."
            )
            show_event_message_external(log_msg)
            add_message_to_log(log_msg)
            ui_manager.current_view = "market"
    if errmsg:
        ui_manager.set_active_prompt_message(errmsg)
        add_message_to_log(f"Transaction failed: {errmsg}")
    ui_manager.quantity_input_string = ""


def action_cancel_transaction() -> None:
    add_message_to_log(
        f"Transaction cancelled. Was type: {ui_manager.current_transaction_type or ui_manager.tech_transaction_in_progress}, View: {ui_manager.current_view}"
    )
    if ui_manager.current_view in ["market_buy_input", "market_sell_input"]:
        ui_manager.current_view = "market"
    elif ui_manager.current_view in ["tech_input_coin_select", "tech_input_amount"]:
        ui_manager.current_view = "tech_contact"

    ui_manager.quantity_input_string = ""
    ui_manager.tech_input_string = ""
    ui_manager.tech_transaction_in_progress = None
    ui_manager.active_prompt_message = None

def action_unlock_skill(
    skill_id: SkillID, player_inv_arg: PlayerInventory, game_configs_arg: Any
) -> None:
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

    prerequisites = skill_def.get("prerequisites", [])
    missing_prereqs = []
    if prerequisites: 
        for prereq_skill_id_enum in prerequisites:
            if prereq_skill_id_enum.value not in player_inventory_cache.unlocked_skills:
                prereq_def = game_configs_data_cache.SKILL_DEFINITIONS.get(prereq_skill_id_enum)
                missing_prereqs.append(prereq_def['name'] if prereq_def else prereq_skill_id_enum.value)
    
    if missing_prereqs:
        ui_manager.set_active_prompt_message(f"Error: Missing prerequisites - {', '.join(missing_prereqs)}.")
        add_message_to_log(f"Skill unlock failed for {skill_id.value}: Missing prerequisites - {', '.join(missing_prereqs)}.")
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

def action_purchase_capacity_upgrade(
    player_inv_arg: PlayerInventory, game_configs_arg: Any
) -> None:
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

def action_purchase_secure_phone(
    player_inv_arg: PlayerInventory, game_configs_arg: Any
) -> None:
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
    ui_manager.current_view = "tech_contact"

def action_collect_staking_rewards(player_inv_arg: PlayerInventory) -> None:
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


def action_initiate_tech_operation(operation_type: str) -> None:
    add_message_to_log(f"Initiating tech operation: {operation_type}")
    ui_manager.tech_transaction_in_progress = operation_type
    ui_manager.tech_input_string = ""
    if operation_type == "collect_dc_rewards":
        action_collect_staking_rewards(player_inventory_cache)
        return
    elif operation_type in ["buy_crypto", "sell_crypto", "stake_dc", "unstake_dc"]:
        ui_manager.current_view = "tech_input_coin_select"
        ui_manager.set_active_prompt_message("Select cryptocurrency.")
    elif operation_type == "launder_cash":
        ui_manager.coin_for_tech_transaction = None
        ui_manager.current_view = "tech_input_amount"
        ui_manager.set_active_prompt_message("Enter cash amount to launder.")
    elif operation_type == "buy_ghost_network":
        action_purchase_ghost_network(player_inventory_cache, game_configs_data_cache)
        return

def action_tech_select_coin(coin: CryptoCoin) -> None:
    verb: str = (
        ui_manager.tech_transaction_in_progress.split("_")[0]
        if ui_manager.tech_transaction_in_progress
        else "transact"
    )
    add_message_to_log(f"Tech operation coin selected: {coin.value} for {verb}")
    ui_manager.coin_for_tech_transaction = coin
    ui_manager.current_view = "tech_input_amount"
    ui_manager.set_active_prompt_message(f"Enter amount of {coin.value} to {verb}.")


def action_purchase_ghost_network(
    player_inv_arg: PlayerInventory, game_configs_arg: Any
) -> None:
    skill_id_val: SkillID = SkillID.GHOST_NETWORK_ACCESS 
    cost_dc_val: float = getattr(game_configs_data_cache, "GHOST_NETWORK_ACCESS_COST_DC", 50.0)
    if SkillID.GHOST_NETWORK_ACCESS.value in player_inventory_cache.unlocked_skills:
        ui_manager.set_active_prompt_message("Ghost Network access already purchased.")
        add_message_to_log("Ghost Network purchase failed: Already purchased.")
    elif player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0) >= cost_dc_val:
        player_inventory_cache.remove_crypto(CryptoCoin.DRUG_COIN, cost_dc_val)
        player_inventory_cache.unlocked_skills.add(SkillID.GHOST_NETWORK_ACCESS.value) 
        msg_val: str = f"Ghost Network access purchased for {cost_dc_val:.2f} DC."
        show_event_message_external(msg_val)
        add_message_to_log(msg_val)
    else:
        ui_manager.set_active_prompt_message(f"Error: Not enough DC. Need {cost_dc_val:.2f} DC.")
        add_message_to_log(
            f"Ghost Network purchase failed: Need {cost_dc_val:.2f} DC, Has {player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0):.2f} DC."
        )
    ui_manager.current_view = "tech_contact"

def _validate_tech_amount(input_str: str) -> Optional[float]:
    original_input_val: str = input_str
    if not input_str.replace(".", "", 1).isdigit():
        errmsg_val: str = "Error: Invalid amount. Must be a number."
        ui_manager.set_active_prompt_message(errmsg_val)
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: '{original_input_val}'"
        )
        return None
    try:
        amount_val: float = float(input_str)
    except ValueError:
        errmsg_val: str = "Error: Could not convert amount to number."
        ui_manager.set_active_prompt_message(errmsg_val)
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: '{original_input_val}'"
        )
        return None
    if amount_val <= 1e-9: 
        errmsg_val: str = "Error: Amount must be a positive number."
        ui_manager.set_active_prompt_message(errmsg_val)
        add_message_to_log(
            f"Tech op validation failed: {errmsg_val} Input: {amount_val}"
        )
        return None
    return amount_val


def _calculate_tech_heat(player_inv: PlayerInventory, game_configs: Any) -> int:
    base_heat_val: int = game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION
    effective_heat_val: float = float(base_heat_val)
    if SkillID.DIGITAL_FOOTPRINT.value in player_inventory_cache.unlocked_skills:
        effective_heat_val *= (1.0 - game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
    if player_inventory_cache.has_secure_phone:
        effective_heat_val *= 1.0 - game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT
    return int(round(effective_heat_val))


def action_confirm_tech_operation(
    player_inv_arg: PlayerInventory, game_state_arg: GameState, game_configs_arg: Any 
) -> None:
    amount_val: Optional[float] = _validate_tech_amount(ui_manager.tech_input_string)
    if amount_val is None:
        ui_manager.tech_input_string = ""
        return

    effective_heat_val: int = _calculate_tech_heat(player_inventory_cache, game_configs_data_cache)
    current_player_region_obj: Optional[Region] = game_state_data_cache.get_current_player_region()
    region_name_str_val: str = (
        current_player_region_obj.name.value
        if current_player_region_obj and hasattr(current_player_region_obj.name, "value")
        else str(current_player_region_obj.name) if current_player_region_obj else "Unknown Region"
    )

    success_flag: bool = False
    log_prefix_str: str = (
        f"Tech op '{ui_manager.tech_transaction_in_progress}' for {amount_val:.4f} {ui_manager.coin_for_tech_transaction.value if ui_manager.coin_for_tech_transaction else 'cash'}: "
    )
    msg_str: str = ""

    if ui_manager.tech_transaction_in_progress == "buy_crypto" and ui_manager.coin_for_tech_transaction:
        price_val: float = game_state_data_cache.current_crypto_prices.get(
            ui_manager.coin_for_tech_transaction, 0.0
        )
        fee_rate = game_configs_data_cache.TECH_CONTACT_SERVICES["CRYPTO_TRADE"]["fee_buy_sell"]
        fee_val: float = amount_val * price_val * fee_rate
        total_cost_val: float = amount_val * price_val + fee_val

        if price_val <= 1e-9:
            msg_str = "Error: Price unavailable."
        elif player_inventory_cache.cash >= total_cost_val:
            player_inventory_cache.cash -= total_cost_val
            player_inventory_cache.add_crypto(ui_manager.coin_for_tech_transaction, amount_val)
            msg_str = f"Bought {amount_val:.4f} {ui_manager.coin_for_tech_transaction.value}. Heat +{effective_heat_val} in {region_name_str_val}."
            success_flag = True
            # Legacy Scenario: Crypto Whale - Large Transaction Check
            if total_cost_val >= game_configs_data_cache.CRYPTO_WHALE_LARGE_TRANSACTION_THRESHOLD:
                if hasattr(player_inventory_cache, 'large_crypto_transactions_completed'):
                    player_inventory_cache.large_crypto_transactions_completed += 1
                else: 
                    player_inventory_cache.large_crypto_transactions_completed = 1
                add_message_to_log(f"Large crypto buy transaction completed. Count: {player_inventory_cache.large_crypto_transactions_completed}")
        else:
            msg_str = f"Error: Not enough cash. Need ${total_cost_val:.2f}"

    elif ui_manager.tech_transaction_in_progress == "sell_crypto" and ui_manager.coin_for_tech_transaction:
        price_val: float = game_state_data_cache.current_crypto_prices.get(
            ui_manager.coin_for_tech_transaction, 0.0
        )
        gross_proceeds_val: float = amount_val * price_val
        fee_rate = game_configs_data_cache.TECH_CONTACT_SERVICES["CRYPTO_TRADE"]["fee_buy_sell"]
        fee_val: float = gross_proceeds_val * fee_rate
        net_proceeds_val: float = gross_proceeds_val - fee_val
        if price_val <= 1e-9:
            msg_str = "Error: Price unavailable."
        elif player_inventory_cache.crypto_wallet.get(ui_manager.coin_for_tech_transaction, 0.0) >= amount_val:
            player_inventory_cache.remove_crypto(ui_manager.coin_for_tech_transaction, amount_val)
            player_inventory_cache.cash += net_proceeds_val
            msg_str = f"Sold {amount_val:.4f} {ui_manager.coin_for_tech_transaction.value}. Heat +{effective_heat_val} in {region_name_str_val}."
            success_flag = True
            # Legacy Scenario: Crypto Whale - Large Transaction Check
            if gross_proceeds_val >= game_configs_data_cache.CRYPTO_WHALE_LARGE_TRANSACTION_THRESHOLD:
                if hasattr(player_inventory_cache, 'large_crypto_transactions_completed'):
                    player_inventory_cache.large_crypto_transactions_completed += 1
                else:
                    player_inventory_cache.large_crypto_transactions_completed = 1
                add_message_to_log(f"Large crypto sell transaction completed. Count: {player_inventory_cache.large_crypto_transactions_completed}")
        else:
            msg_str = f"Error: Not enough {ui_manager.coin_for_tech_transaction.value}."

    elif ui_manager.tech_transaction_in_progress == "launder_cash":
        fee_rate = game_configs_data_cache.TECH_CONTACT_SERVICES["LAUNDER_CASH"]["fee"]
        fee_val: float = amount_val * fee_rate
        total_cost_val: float = amount_val + fee_val
        launder_heat_val: int = int(amount_val * game_configs_data_cache.LAUNDERING_HEAT_FACTOR_PER_CASH_UNIT)
        if player_inventory_cache.cash >= total_cost_val:
            player_inventory_cache.cash -= total_cost_val
            # Legacy Scenario: The Cleaner - Update total laundered cash
            if hasattr(player_inventory_cache, 'total_laundered_cash'):
                player_inventory_cache.total_laundered_cash += amount_val
            else:
                player_inventory_cache.total_laundered_cash = amount_val
            add_message_to_log(f"Total laundered cash updated to: ${player_inventory_cache.total_laundered_cash:,.2f}")
            
            player_inventory_cache.pending_laundered_sc = (
                player_inventory_cache.pending_laundered_sc + amount_val
                if hasattr(player_inventory_cache, "pending_laundered_sc")
                else amount_val
            )
            player_inventory_cache.pending_laundered_sc_arrival_day = (
                game_state_data_cache.current_day + game_configs_data_cache.LAUNDERING_DELAY_DAYS
            )
            msg_str = f"Laundered ${amount_val:,.2f}. Fee ${fee_val:,.2f}. Arrives day {player_inventory_cache.pending_laundered_sc_arrival_day}. Heat +{launder_heat_val} in {region_name_str_val}."
            effective_heat_val = launder_heat_val
            success_flag = True
        else:
            msg_str = f"Error: Not enough cash for amount + fee. Need ${total_cost_val:.2f}"

    elif ui_manager.tech_transaction_in_progress == "stake_dc" and ui_manager.coin_for_tech_transaction == CryptoCoin.DRUG_COIN:
        if player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0.0) >= amount_val:
            player_inventory_cache.remove_crypto(CryptoCoin.DRUG_COIN, amount_val)
            player_inventory_cache.staked_drug_coin["staked_amount"] = (
                player_inventory_cache.staked_drug_coin.get("staked_amount", 0.0) + amount_val
            )
            msg_str = f"Staked {amount_val:.4f} DC."
            success_flag = True
        else:
            msg_str = f"Error: Not enough {CryptoCoin.DRUG_COIN.value}."

    elif ui_manager.tech_transaction_in_progress == "unstake_dc" and ui_manager.coin_for_tech_transaction == CryptoCoin.DRUG_COIN:
        if player_inventory_cache.staked_drug_coin.get("staked_amount", 0.0) >= amount_val:
            player_inventory_cache.staked_drug_coin["staked_amount"] -= amount_val
            pending_rewards_val: float = player_inventory_cache.staked_drug_coin.get("pending_rewards", 0.0)
            player_inventory_cache.add_crypto(CryptoCoin.DRUG_COIN, amount_val + pending_rewards_val)
            player_inventory_cache.staked_drug_coin["pending_rewards"] = 0.0
            msg_str = f"Unstaked {amount_val:.4f} DC. Rewards collected: {pending_rewards_val:.4f} DC."
            success_flag = True
        else:
            msg_str = f"Error: Not enough staked {CryptoCoin.DRUG_COIN.value}."

    if success_flag:
        show_event_message_external(msg_str)
        add_message_to_log(log_prefix_str + msg_str)
        if (
            effective_heat_val > 0
            and ui_manager.tech_transaction_in_progress
            in ["buy_crypto", "sell_crypto", "launder_cash"]
            and current_player_region_obj
        ):
            current_player_region_obj.modify_heat(effective_heat_val)
            add_message_to_log(
                f"Applied heat: +{effective_heat_val} in {region_name_str_val} for {ui_manager.tech_transaction_in_progress}"
            )
        ui_manager.current_view = "tech_contact" # Go back to tech contact main
        ui_manager.tech_input_string = ""
        ui_manager.tech_transaction_in_progress = None
    else:
        ui_manager.set_active_prompt_message(msg_str if msg_str else "Error: Transaction failed.")
        add_message_to_log(
            log_prefix_str + (msg_str if msg_str else "Failed - Unknown reason.")
        )
        if amount_val is None: 
            ui_manager.tech_input_string = "" 

    # ui_manager.setup_buttons_for_current_view() # Let main loop handle


# --- Main Game Loop ---
def game_loop(
    player_inventory: PlayerInventory,
    initial_current_region: Optional[Region],
    game_state_ext: GameState,
    game_configs_ext: Any,
) -> None:
    """The main game loop."""
    global game_state_data_cache, game_configs_data_cache, player_inventory_cache, ui_manager

    game_state_data_cache = game_state_ext
    game_configs_data_cache = game_configs_ext
    player_inventory_cache = player_inventory
    
    # Pass the app_actions dictionary to UIManager
    app_actions_map = {
        "open_main_menu": action_open_main_menu,
        "open_market": action_open_market,
        "open_inventory": action_open_inventory,
        "open_travel": action_open_travel,
        "open_tech_contact": action_open_tech_contact,
        "open_skills": action_open_skills,
        "open_upgrades": action_open_upgrades,
        "open_informant": action_open_informant,
        "meet_corrupt_official": action_meet_corrupt_official,
        "meet_forger": action_meet_forger,
        "meet_logistics_expert": action_meet_logistics_expert,
        "close_blocking_event_popup": action_close_blocking_event_popup,
        "exit_game": action_exit_game,
        "travel_to_region": action_travel_to_region,
        "ask_informant_rumor": action_ask_informant_rumor,
        "ask_informant_rival_status": action_ask_informant_rival_status,
        "ask_informant_drug_info": action_ask_informant_drug_info,
        "confirm_corrupt_official_bribe": action_confirm_corrupt_official_bribe,
        "initiate_buy": action_initiate_buy,
        "initiate_sell": action_initiate_sell,
        "confirm_transaction": action_confirm_transaction,
        "cancel_transaction": action_cancel_transaction,
        "unlock_skill": action_unlock_skill,
        "purchase_capacity_upgrade": action_purchase_capacity_upgrade,
        "purchase_secure_phone": action_purchase_secure_phone,
        "collect_staking_rewards": action_collect_staking_rewards,
        "initiate_tech_operation": action_initiate_tech_operation,
        "tech_select_coin": action_tech_select_coin,
        "purchase_ghost_network": action_purchase_ghost_network,
        "confirm_tech_operation": action_confirm_tech_operation,
        # Quest actions
        "accept_quest": action_accept_quest,
        "decline_quest": action_decline_quest,
        "complete_quest_stage": action_complete_quest_stage,
        "search_for_supplies": action_search_for_supplies,
        # Add any other specific contact service actions here if they are not generic
    }
    ui_manager = UIManager(game_state_data_cache, player_inventory_cache, game_configs_data_cache, app_actions_map)

    if not game_state_data_cache.current_player_region:
        # Ensure PLAYER_STARTING_REGION_NAME is correctly accessed from game_configs_module
        start_region = game_configs_module.PLAYER_STARTING_REGION_NAME
        game_state_data_cache.set_current_player_region(
            initial_current_region.name 
            if initial_current_region else start_region
        )
    
    ui_manager.setup_buttons_for_current_view() # Initial setup

    running: bool = True
    while running:
        current_player_region_for_frame: Optional[Region] = game_state_data_cache.current_player_region
        previous_view: str = ui_manager.current_view
        mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()

        if ui_manager.game_over_message is not None and ui_manager.current_view != "game_over":
            previous_view = ui_manager.current_view
            ui_manager.current_view = "game_over"
        
        if previous_view != ui_manager.current_view:
            ui_manager.setup_buttons_for_current_view()


        for event_pygame in pygame.event.get():
            if event_pygame.type == pygame.QUIT:
                running = False

            current_buttons_to_check = ui_manager.active_buttons_list
            if ui_manager.current_view == "market":
                 current_buttons_to_check = ui_manager.market_view_buttons + ui_manager.market_item_buttons

            for btn in current_buttons_to_check:
                if btn.handle_event(event_pygame):
                    # If button click changed view, setup_buttons will be called at start of next frame's logic
                    break 
            
            if event_pygame.type == pygame.KEYDOWN:
                if ui_manager.current_view == "game_over":
                    if event_pygame.key == pygame.K_RETURN and ui_manager.game_over_buttons and ui_manager.game_over_buttons[0].action:
                        ui_manager.game_over_buttons[0].action() 
                    continue 

                if ui_manager.current_view == "blocking_event_popup":
                    if event_pygame.key == pygame.K_RETURN and ui_manager.blocking_event_popup_buttons and ui_manager.blocking_event_popup_buttons[0].action:
                        ui_manager.blocking_event_popup_buttons[0].action()
                    continue

                is_market_input_active: bool = ui_manager.current_view in ["market_buy_input", "market_sell_input"]
                is_tech_input_active: bool = ui_manager.current_view == "tech_input_amount"

                if event_pygame.key == pygame.K_ESCAPE:
                    if is_market_input_active or is_tech_input_active:
                        action_cancel_transaction() 
                    else:
                        action_open_main_menu()
                
                if is_market_input_active:
                    if event_pygame.key == pygame.K_RETURN:
                        if current_player_region_for_frame: 
                             action_confirm_transaction(player_inventory_cache, current_player_region_for_frame, game_state_data_cache)
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        ui_manager.quantity_input_string = ui_manager.quantity_input_string[:-1]
                    elif event_pygame.unicode.isdigit():
                        ui_manager.quantity_input_string += event_pygame.unicode
                elif is_tech_input_active:
                    if event_pygame.key == pygame.K_RETURN:
                        action_confirm_tech_operation(player_inventory_cache, game_state_data_cache, game_configs_data_cache)
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        ui_manager.tech_input_string = ui_manager.tech_input_string[:-1]
                    elif event_pygame.unicode.isdigit() or (event_pygame.unicode == "." and "." not in ui_manager.tech_input_string):
                        ui_manager.tech_input_string += event_pygame.unicode
        
        if previous_view != ui_manager.current_view: # Check again after event loop in case an action changed view
            ui_manager.setup_buttons_for_current_view()


        update_hud_timers_external() 
        if ui_manager.prompt_message_timer > 0:
            ui_manager.prompt_message_timer -= 1
        if ui_manager.prompt_message_timer <= 0:
            ui_manager.active_prompt_message = None

        screen.fill(RICH_BLACK)
        if ui_manager.current_view == "game_over":
            draw_game_over_view_external(
                screen,
                ui_manager.game_over_message if ui_manager.game_over_message else "Game Over", 
                ui_manager.game_over_buttons, 
            )
        elif ui_manager.current_view == "main_menu":
            draw_main_menu_external(screen, ui_manager.main_menu_buttons)
        elif ui_manager.current_view == "market" and current_player_region_for_frame:
            draw_market_view_external(screen, current_player_region_for_frame, player_inventory_cache, ui_manager.market_view_buttons, ui_manager.market_item_buttons, game_state_data_cache)
        elif ui_manager.current_view == "inventory":
            draw_inventory_view_external(screen, player_inventory_cache, ui_manager.inventory_view_buttons)
        elif ui_manager.current_view == "travel" and current_player_region_for_frame:
            draw_travel_view_external(screen, current_player_region_for_frame, ui_manager.travel_view_buttons)
        
        elif ui_manager.current_view == "informant":
            contact_def = game_configs_data_cache.CONTACT_DEFINITIONS.get(ContactID.INFORMANT)
            if contact_def: 
                 draw_generic_contact_view_external(
                    screen, ContactID.INFORMANT, contact_def,
                    ui_manager.contact_specific_buttons.get(ContactID.INFORMANT, []),
                    player_inventory_cache.contact_trusts.get(ContactID.INFORMANT, 0)
                )
        elif ui_manager.current_view == "tech_contact" or \
             ui_manager.current_view == "tech_input_coin_select" or \
             ui_manager.current_view == "tech_input_amount":
            contact_def = game_configs_data_cache.CONTACT_DEFINITIONS.get(ContactID.TECH_CONTACT)
            tech_ui_state_dict: Dict[str, Any] = { 
                "current_view": ui_manager.current_view, 
                "tech_transaction_in_progress": ui_manager.tech_transaction_in_progress,
                "coin_for_tech_transaction": ui_manager.coin_for_tech_transaction,
                "tech_input_string": ui_manager.tech_input_string,
                "active_prompt_message": ui_manager.active_prompt_message,
                "prompt_message_timer": ui_manager.prompt_message_timer,
                "tech_input_box_rect": ui_manager.tech_input_box_rect,
            }
            if contact_def: 
                draw_tech_contact_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, 
                                                ui_manager.contact_specific_buttons.get(ContactID.TECH_CONTACT, []), tech_ui_state_dict)
        
        elif ui_manager.current_view == "skills":
            draw_skills_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, ui_manager.skills_view_buttons)
        elif ui_manager.current_view == "upgrades":
            draw_upgrades_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, ui_manager.upgrades_view_buttons)
        
        elif ui_manager.current_view == "corrupt_official_contact": 
            contact_def = game_configs_data_cache.CONTACT_DEFINITIONS.get(ContactID.CORRUPT_OFFICIAL)
            if contact_def:
                draw_generic_contact_view_external(
                    screen, ContactID.CORRUPT_OFFICIAL, contact_def,
                    ui_manager.contact_specific_buttons.get(ContactID.CORRUPT_OFFICIAL, []),
                    player_inventory_cache.contact_trusts.get(ContactID.CORRUPT_OFFICIAL, 0)
                )
        elif ui_manager.current_view == "forger_contact":
            contact_def = game_configs_data_cache.CONTACT_DEFINITIONS.get(ContactID.THE_FORGER)
            if contact_def:
                draw_generic_contact_view_external(
                    screen, ContactID.THE_FORGER, contact_def,
                    ui_manager.contact_specific_buttons.get(ContactID.THE_FORGER, []),
                    player_inventory_cache.contact_trusts.get(ContactID.THE_FORGER, 0)
                )
        elif ui_manager.current_view == "logistics_expert_contact":
            contact_def = game_configs_data_cache.CONTACT_DEFINITIONS.get(ContactID.LOGISTICS_EXPERT)
            if contact_def:
                draw_generic_contact_view_external(
                    screen, ContactID.LOGISTICS_EXPERT, contact_def,
                    ui_manager.contact_specific_buttons.get(ContactID.LOGISTICS_EXPERT, []),
                    player_inventory_cache.contact_trusts.get(ContactID.LOGISTICS_EXPERT, 0)
                )

        elif ui_manager.current_view in ["market_buy_input", "market_sell_input"]:
            transaction_ui_state_dict: Dict[str, Any] = { 
                "quantity_input_string": ui_manager.quantity_input_string,
                "drug_for_transaction": ui_manager.drug_for_transaction,
                "quality_for_transaction": ui_manager.quality_for_transaction,
                "price_for_transaction": ui_manager.price_for_transaction,
                "available_for_transaction": ui_manager.available_for_transaction,
                "current_transaction_type": ui_manager.current_transaction_type,
                "active_prompt_message": ui_manager.active_prompt_message,
                "prompt_message_timer": ui_manager.prompt_message_timer,
                "input_box_rect": ui_manager.input_box_rect,
            }
            draw_transaction_input_view_external(
                screen, ui_manager.transaction_input_buttons, transaction_ui_state_dict
            )

        if ( 
            ui_manager.current_view != "game_over"
            and ui_manager.current_view == "blocking_event_popup"
            and ui_manager.active_blocking_event_data
        ):
            draw_blocking_event_popup_external(
                screen, ui_manager.active_blocking_event_data, ui_manager.blocking_event_popup_buttons
            )

        if ( 
            ui_manager.current_view != "game_over" and current_player_region_for_frame
        ):
            draw_hud_external(screen, player_inventory_cache, current_player_region_for_frame, game_state_data_cache)

        if ( 
            ui_manager.active_prompt_message
            and ui_manager.prompt_message_timer > 0
            and ui_manager.current_view not in ["game_over", "blocking_event_popup"]
        ):
            is_prompt_handled_local: bool = ( 
                ui_manager.current_view
                in ["market_buy_input", "market_sell_input", "tech_input_amount"]
            ) or ( 
                ui_manager.current_view == "tech_contact"
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
            )
            if not is_prompt_handled_local:
                prompt_y_pos_val: int = UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.PROMPT_DEFAULT_Y_OFFSET
                if ui_manager.current_view == "tech_contact": 
                    prompt_y_pos_val = UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.PROMPT_TECH_CONTACT_Y_OFFSET
                prompt_color_val: Tuple[int, int, int] = (
                    IMPERIAL_RED
                    if any(
                        err_word in ui_manager.active_prompt_message 
                        for err_word in ["Error", "Invalid", "Not enough"]
                    )
                    else (
                        GOLDEN_YELLOW
                        if "Skill" in ui_manager.active_prompt_message 
                        else EMERALD_GREEN
                    )
                )
                draw_text(
                    screen,
                    ui_manager.active_prompt_message, 
                    UI_CONSTANTS.SCREEN_WIDTH // 2,
                    prompt_y_pos_val,
                    font=FONT_MEDIUM, 
                    color=prompt_color_val,
                    center_aligned=True,
                    max_width=UI_CONSTANTS.SCREEN_WIDTH - (2 * UI_CONSTANTS.LARGE_PADDING), 
                )

        pygame.display.flip()
        clock.tick(UI_CONSTANTS.FPS)

    pygame.quit()
    sys.exit()

[end of src/ui_pygame/app.py]
