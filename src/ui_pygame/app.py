"""
This module implements the main application logic for the Pygame UI.

It includes functions for managing game state, handling user input,
and rendering the user interface.
"""
import pygame
import sys
import functools # For partial functions
import random # For police stop simulation
from typing import Optional, Dict, List, Tuple, Callable, Any # For type hinting

from ..core.enums import DrugName, DrugQuality, RegionName, CryptoCoin
from ..core.player_inventory import PlayerInventory 
from ..core.region import Region
from ..mechanics import market_impact, event_manager

from .ui_theme import (
    RICH_BLACK, OXFORD_BLUE, YALE_BLUE, SILVER_LAKE_BLUE, PLATINUM, GHOST_WHITE,
    IMPERIAL_RED, EMERALD_GREEN, GOLDEN_YELLOW, NEON_BLUE,
    DARK_GREY, MEDIUM_GREY, LIGHT_GREY, VERY_LIGHT_GREY,
    BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_DISABLED_COLOR,
    BUTTON_TEXT_COLOR, BUTTON_DISABLED_TEXT_COLOR, TEXT_COLOR,
    TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR, TEXT_INPUT_TEXT_COLOR,
    HUD_BACKGROUND_COLOR, HUD_TEXT_COLOR, HUD_ACCENT_COLOR,
    FONT_XLARGE, FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_XSMALL, FONT_LARGE_BOLD,
    draw_text, draw_panel, draw_input_box
)
from .ui_components import Button
from .ui_hud import draw_hud as draw_hud_external, show_event_message as show_event_message_external, update_hud_timers as update_hud_timers_external, add_message_to_log 
from .views.main_menu_view import draw_main_menu as draw_main_menu_external
from .views.market_view import draw_market_view as draw_market_view_external, draw_transaction_input_view as draw_transaction_input_view_external
from .views.inventory_view import draw_inventory_view as draw_inventory_view_external
from .views.travel_view import draw_travel_view as draw_travel_view_external
from .views.tech_contact_view import draw_tech_contact_view as draw_tech_contact_view_external
from .views.skills_view import draw_skills_view as draw_skills_view_external
from .views.upgrades_view import draw_upgrades_view as draw_upgrades_view_external
from .views.blocking_event_popup_view import draw_blocking_event_popup as draw_blocking_event_popup_external
from .views.game_over_view import draw_game_over_view as draw_game_over_view_external
from .views.informant_view import draw_informant_view as draw_informant_view_external


# --- Constants ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
UPGRADE_ITEM_X_START = 50 
UPGRADE_ITEM_WIDTH = SCREEN_WIDTH - 2 * UPGRADE_ITEM_X_START 
UPGRADE_BUTTON_WIDTH = 170 
UPGRADE_BUTTON_HEIGHT = 40 
STD_BUTTON_WIDTH = 200
STD_BUTTON_HEIGHT = 50
STD_BUTTON_SPACING = 10


# --- Pygame Setup (Screen, Clock) ---
pygame.font.init() 
pygame.init() 
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
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
input_box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 200, 200, 40) 

tech_transaction_in_progress: Optional[str] = None 
coin_for_tech_transaction: Optional[CryptoCoin] = None
tech_input_string: str = "" 
tech_input_box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 125, 200, 250, 40)

active_prompt_message: Optional[str] = None
prompt_message_timer: int = 0
PROMPT_DURATION_FRAMES = 120 

active_blocking_event_data: Optional[Dict] = None 
game_over_message: Optional[str] = None 

game_state_data_cache: Optional[any] = None 
game_configs_data_cache: Optional[any] = None 
player_inventory_cache: Optional[PlayerInventory] = None


# --- Daily Updates Function ---
def perform_daily_updates(game_state_data: any, player_inventory_data: PlayerInventory, game_configs_data: any):
    """Performs daily updates for the game state, player inventory, and game configurations."""
    global game_over_message 
    if game_over_message is not None: return 

    if not player_inventory_data.debt_payment_1_paid and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_1_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_1_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_1_AMOUNT; player_inventory_data.debt_payment_1_paid = True
            show_event_message_external("Debt Payment 1 made!"); add_message_to_log("Paid $25k (Debt 1).")
        else: game_over_message = "GAME OVER: Failed Debt Payment 1!"; add_message_to_log(game_over_message); return
    if player_inventory_data.debt_payment_1_paid and not player_inventory_data.debt_payment_2_paid and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_2_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_2_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_2_AMOUNT; player_inventory_data.debt_payment_2_paid = True
            show_event_message_external("Debt Payment 2 made!"); add_message_to_log("Paid $30k (Debt 2).")
        else: game_over_message = "GAME OVER: Failed Debt Payment 2!"; add_message_to_log(game_over_message); return
    if player_inventory_data.debt_payment_1_paid and player_inventory_data.debt_payment_2_paid and not player_inventory_data.debt_payment_3_paid and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_3_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_3_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_3_AMOUNT; player_inventory_data.debt_payment_3_paid = True
            show_event_message_external("Final debt paid! You are free!"); add_message_to_log("Paid $20k (Final Debt). You are FREE!")
        else: game_over_message = "GAME OVER: Failed Final Debt Payment!"; add_message_to_log(game_over_message); return

    if hasattr(game_state_data, 'all_regions'): [ (r.restock_market(), market_impact.decay_regional_heat(r), market_impact.decay_player_market_impact(r), market_impact.decay_rival_market_impact(r, game_state_data.current_day), event_manager.update_active_events(r, game_state_data.current_day)) for r in game_state_data.all_regions.values() if hasattr(r, 'restock_market') ]
    if hasattr(game_state_data, 'update_daily_crypto_prices'): game_state_data.update_daily_crypto_prices(game_configs_data.CRYPTO_VOLATILITY, game_configs_data.CRYPTO_MIN_PRICE)

    if hasattr(player_inventory_data, 'staked_drug_coin') and player_inventory_data.staked_drug_coin.get('staked_amount',0) > 0 and hasattr(game_configs_data, 'DC_STAKING_DAILY_RETURN_PERCENT'):
        reward = player_inventory_data.staked_drug_coin['staked_amount'] * game_configs_data.DC_STAKING_DAILY_RETURN_PERCENT
        player_inventory_data.staked_drug_coin['pending_rewards'] = player_inventory_data.staked_drug_coin.get('pending_rewards',0) + reward
        if reward > 1e-5: show_event_message_external(f"Accrued {reward:.4f} DC rewards. Collect at Tech Contact.")

    if hasattr(player_inventory_data, 'pending_laundered_sc_arrival_day') and player_inventory_data.pending_laundered_sc_arrival_day is not None and game_state_data.current_day >= player_inventory_data.pending_laundered_sc_arrival_day:
        amount = player_inventory_data.pending_laundered_sc; player_inventory_data.add_crypto(CryptoCoin.STABLE_COIN, amount);
        show_event_message_external(f"{amount:.2f} SC (laundered) arrived."); add_message_to_log(f"Laundered cash arrived: {amount:.2f} SC.")
        player_inventory_data.pending_laundered_sc=0.0; player_inventory_data.pending_laundered_sc_arrival_day=None

    if hasattr(game_state_data, 'current_player_region') and hasattr(event_manager, 'trigger_random_market_event'):
        event_manager.trigger_random_market_event(game_state_data.current_player_region, game_state_data.current_day, player_inventory_data, getattr(game_state_data, 'ai_rivals',[]), show_event_message_external)

    if hasattr(game_state_data, 'ai_rivals'): [ market_impact.process_rival_turn(r, game_state_data.all_regions, game_state_data.current_day, game_configs_data, show_event_message_external) for r in game_state_data.ai_rivals if not r.is_busted ]

    if player_inventory_data.cash < game_configs_data.BANKRUPTCY_THRESHOLD:
        game_over_message = "GAME OVER: You have gone bankrupt!"
        add_message_to_log(f"{game_over_message} Cash: ${player_inventory_data.cash:.2f}, Threshold: ${game_configs_data.BANKRUPTCY_THRESHOLD:.2f}")
        return

def set_active_prompt_message(message: str, duration_frames: int = PROMPT_DURATION_FRAMES):
    """Sets a message to be displayed temporarily on the screen."""
    global active_prompt_message, prompt_message_timer
    active_prompt_message = message; prompt_message_timer = duration_frames

# --- Action Functions (Callbacks for buttons) ---
def action_open_main_menu(): global current_view; current_view = "main_menu"
def action_open_market(): global current_view; current_view = "market"
def action_open_inventory(): global current_view; current_view = "inventory"
def action_open_travel(): global current_view; current_view = "travel"
def action_open_tech_contact(): global current_view; current_view = "tech_contact"
def action_open_skills(): global current_view; current_view = "skills"
def action_open_upgrades(): global current_view; current_view = "upgrades"
def action_open_informant(): global current_view; current_view = "informant"
def action_close_blocking_event_popup(): global active_blocking_event_data, current_view; active_blocking_event_data = None; current_view = "main_menu"

def action_travel_to_region(destination_region: Region, player_inv: PlayerInventory, game_state: any):
    global current_view, game_state_data_cache, player_inventory_cache, game_configs_data_cache, active_blocking_event_data, game_over_message
    if game_over_message is not None: return 
    add_message_to_log(f"Attempting to travel to {destination_region.name.value}.")
    original_day_before_travel = game_state.current_day 
    game_state.current_player_region = destination_region 
    game_state.current_day += 1 
    add_message_to_log(f"Advanced day to {game_state.current_day}.")
    perform_daily_updates(game_state_data_cache, player_inventory_cache, game_configs_data_cache)
    if game_over_message is not None: current_view = "game_over"; add_message_to_log("Game over triggered during travel daily updates."); return
    if game_state.current_day % game_configs_data_cache.SKILL_POINTS_PER_X_DAYS == 0 and game_state.current_day > original_day_before_travel:
        player_inv.skill_points +=1;
        show_event_message_external(f"Day advanced. +1 Skill Point. Total: {player_inv.skill_points}")
        add_message_to_log(f"Awarded skill point. Total: {player_inv.skill_points}")

    region_heat = destination_region.current_heat; threshold = game_configs_data_cache.POLICE_STOP_HEAT_THRESHOLD; base_chance = game_configs_data_cache.POLICE_STOP_BASE_CHANCE; per_point_increase = game_configs_data_cache.POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD
    calculated_chance = base_chance; 
    if region_heat >= threshold: calculated_chance += (region_heat - threshold) * per_point_increase
    final_police_stop_chance = max(0.0, min(calculated_chance, 0.95))
    add_message_to_log(f"Police stop chance in {destination_region.name.value}: {final_police_stop_chance:.2f} (Heat: {region_heat})")

    if random.random() < final_police_stop_chance:
        add_message_to_log("Police stop triggered.")
        show_event_message_external(f"Arriving in {destination_region.name.value}... flashing lights!")
        stop_type = random.random()
        if stop_type < 0.33:
            active_blocking_event_data = {'title': "Police Stop!", 'messages': [f"Pulled over by {destination_region.name.value} PD.", "They give you a stern look and a warning."], 'button_text': "Continue"}
            add_message_to_log("Police stop: Warning.")
        elif stop_type < 0.66:
            fine = min(player_inv.cash, random.randint(100,500)*(1+destination_region.current_heat//20)); player_inv.cash -= fine
            active_blocking_event_data = {'title': "Police Stop - Fine!", 'messages': ["Police stop for 'random' check.", f"Minor infraction. Fined ${fine:,.0f}."], 'button_text': "Pay Fine"}
            show_event_message_external(f"Paid fine of ${fine:,.0f}.")
            add_message_to_log(f"Police stop: Fined ${fine:,.0f}. Cash remaining: ${player_inv.cash:.2f}")
            if player_inv.cash < game_configs_data_cache.BANKRUPTCY_THRESHOLD:
                game_over_message = "GAME OVER: A hefty fine bankrupted you!"
                add_message_to_log(f"{game_over_message} Cash: ${player_inv.cash:.2f}")
        else:
            total_contraband_units = sum(drug_item['quantity'] for drug_item in player_inv.drugs.values())
            add_message_to_log(f"Police stop: Searched. Carrying {total_contraband_units} units of contraband.")
            if total_contraband_units > game_configs_data_cache.POLICE_STOP_CONTRABAND_THRESHOLD_UNITS and \
               random.random() < game_configs_data_cache.POLICE_STOP_CONFISCATION_CHANCE:
                player_inv.drugs.clear()
                player_inv.current_load = sum(item.get('weight', 0) * item.get('quantity', 0) for item in player_inv.other_items.values()) # Recalculate load based on non-drug items if any
                active_blocking_event_data = {'title': "Police Stop - Major Bust!", 'messages': ["Police are suspicious, search vehicle!", "They found your stash! All drugs confiscated!"], 'button_text': "Damn!"}
                add_message_to_log("Police Stop: Searched and all drugs confiscated.")
            elif total_contraband_units > 0:
                 active_blocking_event_data = {'title': "Police Stop - Searched!", 'messages': ["Police are suspicious, search vehicle!", "You had some contraband, but they missed it this time!" if total_contraband_units > game_configs_data_cache.POLICE_STOP_CONTRABAND_THRESHOLD_UNITS else "Luckily, you were clean enough... this time."], 'button_text': "Phew!"}
                 add_message_to_log("Police stop: Searched, but no major confiscation this time.")
            else:
                 active_blocking_event_data = {'title': "Police Stop - Searched!", 'messages': ["Police are suspicious, search vehicle!", "Luckily, you were clean... this time."], 'button_text': "Phew!"}
                 add_message_to_log("Police stop: Searched, found nothing significant.")
        current_view = "blocking_event_popup"
    else:
        show_event_message_external(f"Arrived safely in {destination_region.name.value}.")
        add_message_to_log(f"Arrived safely in {destination_region.name.value}.")
        current_view = "main_menu"

def action_ask_informant_rumor(player_inv: PlayerInventory, game_configs: any, game_state: any):
    cost = game_configs.INFORMANT_TIP_COST_RUMOR
    if player_inv.cash >= cost:
        player_inv.cash -= cost
        player_inv.informant_trust = min(player_inv.informant_trust + game_configs.INFORMANT_TRUST_GAIN_PER_TIP, game_configs.INFORMANT_MAX_TRUST)
        rumors = ["Heard The Chemist is planning a big move in Downtown soon.", "Silas is looking for extra muscle, might be risky.", f"Word is, {random.choice(list(DrugName)).value} prices might spike in {random.choice(list(RegionName)).value}.", "Cops are cracking down in The Docks, lay low.", "Someone saw a new shipment of high-quality Pills arriving at Suburbia."]
        rumor = random.choice(rumors)
        show_event_message_external(f"Informant whispers: '{rumor}'")
        add_message_to_log(f"Paid informant ${cost:.0f} for a rumor: {rumor}")
    else:
        set_active_prompt_message(f"Error: Not enough cash. Need ${cost:.0f}."); add_message_to_log(f"Failed to buy rumor: Insufficient cash. Needed ${cost:.0f}, Has ${player_inv.cash:.0f}")
    setup_buttons(game_state, player_inv, game_configs, game_state.current_player_region)

def action_ask_informant_rival_status(player_inv: PlayerInventory, game_configs: any, game_state: any):
    cost = game_configs.INFORMANT_TIP_COST_RIVAL_INFO
    if player_inv.cash >= cost:
        player_inv.cash -= cost
        player_inv.informant_trust = min(player_inv.informant_trust + game_configs.INFORMANT_TRUST_GAIN_PER_TIP, game_configs.INFORMANT_MAX_TRUST)
        info_parts = []
        if hasattr(game_state, 'ai_rivals') and game_state.ai_rivals:
            active_rivals = [r.name for r in game_state.ai_rivals if not r.is_busted]
            busted_rivals = [(r.name, r.busted_days_remaining) for r in game_state.ai_rivals if r.is_busted]
            if active_rivals: info_parts.append(f"Active: {', '.join(active_rivals)}.")
            else: info_parts.append("No active rivals on my radar.")
            if busted_rivals: info_parts.append(f"Busted: {', '.join([f'{name}({days}d left)' for name, days in busted_rivals])}.")
        else: info_parts.append("No news on rivals right now.")
        final_info = " ".join(info_parts)
        show_event_message_external(f"Informant on rivals: {final_info}")
        add_message_to_log(f"Paid informant ${cost:.0f} for rival status: {final_info}")
    else:
        set_active_prompt_message(f"Error: Not enough cash. Need ${cost:.0f}."); add_message_to_log(f"Failed to buy rival info: Insufficient cash. Needed ${cost:.0f}, Has ${player_inv.cash:.0f}")
    setup_buttons(game_state, player_inv, game_configs, game_state.current_player_region)

def _initiate_market_transaction(trans_type: str, drug: DrugName, quality: DrugQuality, price: float, available: int):
    """Helper function to set up state for a market buy/sell transaction."""
    global current_view, current_transaction_type, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, quantity_input_string
    current_view = f"market_{trans_type}_input"
    current_transaction_type = trans_type
    drug_for_transaction = drug; quality_for_transaction = quality; price_for_transaction = price; available_for_transaction = available
    quantity_input_string = ""
    set_active_prompt_message(f"Enter quantity to {trans_type}.", duration_frames=PROMPT_DURATION_FRAMES * 2)
    add_message_to_log(f"Initiating market transaction: {trans_type} {drug.value} ({quality.name}) at ${price:.2f}, {available} available.")

def action_initiate_buy(drug: DrugName, quality: DrugQuality, price: float, available: int):
    _initiate_market_transaction("buy", drug, quality, price, available)

def action_initiate_sell(drug: DrugName, quality: DrugQuality, price: float, available: int):
    _initiate_market_transaction("sell", drug, quality, price, available)

def action_confirm_transaction(player_inv: PlayerInventory, market_region: Region, game_state: any):
    global quantity_input_string, current_transaction_type, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, current_view, game_configs_data_cache
    original_quantity_input = quantity_input_string
    if not quantity_input_string.isdigit():
        errmsg = "Error: Quantity must be a positive number." # Changed from "must be a number"
        set_active_prompt_message(errmsg); add_message_to_log(f"Transaction failed: {errmsg} Input: '{original_quantity_input}'")
        quantity_input_string = ""; setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, market_region); return
    quantity = int(quantity_input_string)
    if quantity <= 0:
        errmsg = "Error: Quantity must be a positive number."
        set_active_prompt_message(errmsg); add_message_to_log(f"Transaction failed: {errmsg} Input: {quantity}")
        quantity_input_string = ""; setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, market_region); return

    if current_transaction_type == "buy":
        cost = quantity * price_for_transaction
        if cost > player_inv.cash:
            errmsg = "Error: Not enough cash."
            set_active_prompt_message(errmsg); add_message_to_log(f"Buy failed: {errmsg} Needed ${cost:.2f}, Has ${player_inv.cash:.2f}")
        elif quantity > available_for_transaction:
            errmsg = "Error: Not enough market stock."
            set_active_prompt_message(errmsg); add_message_to_log(f"Buy failed: {errmsg} Requested {quantity}, Available {available_for_transaction}")
        elif player_inv.current_load + quantity > player_inv.max_capacity:
            errmsg = "Error: Not enough inventory space."
            set_active_prompt_message(errmsg); add_message_to_log(f"Buy failed: {errmsg} Current load {player_inv.current_load}, Requesting {quantity}, Capacity {player_inv.max_capacity}")
        else:
            player_inv.cash -= cost; player_inv.add_drug(drug_for_transaction, quality_for_transaction, quantity)
            market_region.update_stock_on_buy(drug_for_transaction, quality_for_transaction, quantity)
            market_impact.apply_player_buy_impact(market_region, drug_for_transaction.value, quantity) 
            log_msg = f"Bought {quantity} {drug_for_transaction.value} ({quality_for_transaction.name}) for ${cost:.2f}."
            show_event_message_external(log_msg); add_message_to_log(log_msg)
            current_view = "market"
    elif current_transaction_type == "sell":
        player_has = player_inv.get_drug_quantity(drug_for_transaction, quality_for_transaction)
        if quantity > player_has:
            errmsg = "Error: Not enough items to sell."
            set_active_prompt_message(errmsg); add_message_to_log(f"Sell failed: {errmsg} Requested {quantity}, Has {player_has} of {drug_for_transaction.value} ({quality_for_transaction.name})")
        else:
            revenue = quantity * price_for_transaction
            player_inv.cash += revenue; player_inv.remove_drug(drug_for_transaction, quality_for_transaction, quantity)
            market_region.update_stock_on_sell(drug_for_transaction, quality_for_transaction, quantity)
            drug_tier = market_region.drug_market_data[drug_for_transaction].get('tier',1)
            heat_per_unit = game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER.get(drug_tier,1)
            total_heat = heat_per_unit * quantity; market_region.modify_heat(total_heat)
            market_impact.apply_player_sell_impact(market_region, drug_for_transaction.value, quantity) 
            log_msg = f"Sold {quantity} {drug_for_transaction.value} ({quality_for_transaction.name}) for ${revenue:.2f}. Heat +{total_heat} in {market_region.name.value}."
            show_event_message_external(log_msg); add_message_to_log(log_msg)
            current_view = "market"
    quantity_input_string = ""
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, market_region)

def action_cancel_transaction():
    global current_view, quantity_input_string, tech_input_string, tech_transaction_in_progress, active_prompt_message
    add_message_to_log(f"Transaction cancelled. Was type: {current_transaction_type or tech_transaction_in_progress}, View: {current_view}")
    if current_view in ["market_buy_input", "market_sell_input"]: current_view = "market"
    elif current_view in ["tech_input_coin_select", "tech_input_amount"]: current_view = "tech_contact"
    quantity_input_string = ""; tech_input_string = ""; tech_transaction_in_progress = None; active_prompt_message = None
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_unlock_skill(skill_id: str, player_inv: PlayerInventory, game_configs: any):
    if skill_id in player_inv.unlocked_skills:
        set_active_prompt_message("Skill already unlocked."); add_message_to_log(f"Skill unlock failed: {skill_id} already unlocked.")
        return
    skill_def = game_configs.SKILL_DEFINITIONS.get(skill_id)
    if not skill_def:
        set_active_prompt_message("Error: Skill data unavailable."); add_message_to_log(f"Skill unlock failed: Definition for {skill_id} not found.")
        return
    cost = skill_def['cost']
    if player_inv.skill_points >= cost:
        player_inv.skill_points -= cost; player_inv.unlocked_skills.add(skill_id)
        msg = f"Skill Unlocked: {skill_def['name']}"
        show_event_message_external(msg); add_message_to_log(msg)
    else:
        set_active_prompt_message("Error: Not enough skill points."); add_message_to_log(f"Skill unlock failed for {skill_id}: Need {cost}, Has {player_inv.skill_points}")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_purchase_capacity_upgrade(player_inv: PlayerInventory, game_configs: any):
    upgrade_def = game_configs.UPGRADE_DEFINITIONS.get("EXPANDED_CAPACITY")
    if not upgrade_def:
        set_active_prompt_message("Error: Upgrade data unavailable."); add_message_to_log("Capacity upgrade failed: Definition not found.")
        return
    num_purchased = player_inv.capacity_upgrades_purchased
    max_levels = len(upgrade_def['costs'])
    if num_purchased >= max_levels:
        set_active_prompt_message("Capacity fully upgraded."); add_message_to_log("Capacity upgrade failed: Already max level.")
        return
    cost = upgrade_def['costs'][num_purchased]; next_cap = upgrade_def['capacity_levels'][num_purchased]
    if player_inv.cash >= cost: 
        player_inv.cash -= cost; player_inv.max_capacity = next_cap
        player_inv.capacity_upgrades_purchased += 1
        msg = f"Capacity upgraded to {next_cap} units!"
        show_event_message_external(msg); add_message_to_log(msg)
    else:
        set_active_prompt_message(f"Error: Not enough cash. Need ${cost:,.0f}."); add_message_to_log(f"Capacity upgrade failed: Need ${cost:,.0f}, Has ${player_inv.cash:,.0f}")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_purchase_secure_phone(player_inv: PlayerInventory, game_configs: any):
    if player_inv.has_secure_phone:
        set_active_prompt_message("Secure Phone already owned."); add_message_to_log("Secure phone purchase failed: Already owned.")
        return
    upgrade_def = game_configs.UPGRADE_DEFINITIONS.get("SECURE_PHONE") 
    if not upgrade_def:
        set_active_prompt_message("Error: Upgrade data unavailable."); add_message_to_log("Secure phone purchase failed: Definition not found.")
        return
    cost = upgrade_def['cost']
    if player_inv.cash >= cost:
        player_inv.cash -= cost; player_inv.has_secure_phone = True
        msg = "Secure Phone purchased!"
        show_event_message_external(msg); add_message_to_log(msg)
    else:
        set_active_prompt_message(f"Error: Not enough cash. Need ${cost:,0f}."); add_message_to_log(f"Secure phone purchase failed: Need ${cost:,0f}, Has ${player_inv.cash:,.0f}")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)
    
def action_collect_staking_rewards(player_inv: PlayerInventory): 
    rewards_to_collect = player_inv.staked_drug_coin.get('pending_rewards', 0.0)
    if rewards_to_collect > 1e-9:
        player_inv.add_crypto(CryptoCoin.DRUG_COIN, rewards_to_collect)
        player_inv.staked_drug_coin['pending_rewards'] = 0.0
        msg = f"Collected {rewards_to_collect:.4f} DC staking rewards."
        show_event_message_external(msg); add_message_to_log(msg)
    else:
        set_active_prompt_message("No staking rewards to collect."); add_message_to_log("Collect staking rewards: No rewards available.")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_initiate_tech_operation(operation_type: str): 
    global current_view, tech_transaction_in_progress, coin_for_tech_transaction, tech_input_string
    add_message_to_log(f"Initiating tech operation: {operation_type}")
    tech_transaction_in_progress = operation_type; tech_input_string = ""
    if operation_type == "collect_dc_rewards": action_collect_staking_rewards(player_inventory_cache); return 
    elif operation_type in ["buy_crypto", "sell_crypto", "stake_dc", "unstake_dc"]: current_view = "tech_input_coin_select"; set_active_prompt_message("Select cryptocurrency.")
    elif operation_type == "launder_cash": coin_for_tech_transaction = None; current_view = "tech_input_amount"; set_active_prompt_message("Enter cash amount to launder.")
    elif operation_type == "buy_ghost_network": action_purchase_ghost_network(player_inventory_cache, game_configs_data_cache); return 
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_tech_select_coin(coin: CryptoCoin):
    global current_view, coin_for_tech_transaction, tech_transaction_in_progress
    verb = tech_transaction_in_progress.split("_")[0]
    add_message_to_log(f"Tech operation coin selected: {coin.value} for {verb}")
    coin_for_tech_transaction = coin; current_view = "tech_input_amount";
    set_active_prompt_message(f"Enter amount of {coin.value} to {verb}.")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_purchase_ghost_network(player_inv: PlayerInventory, game_configs: any):
    global current_view
    skill_id = "GHOST_NETWORK_ACCESS"; cost_dc = getattr(game_configs, 'GHOST_NETWORK_ACCESS_COST_DC', 50.0) 
    if skill_id in player_inv.unlocked_skills:
        set_active_prompt_message("Ghost Network access already acquired."); add_message_to_log("Ghost Network purchase failed: Already acquired.")
    elif player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0) >= cost_dc:
        player_inv.remove_crypto(CryptoCoin.DRUG_COIN, cost_dc); player_inv.unlocked_skills.add(skill_id)
        msg = f"Ghost Network access purchased for {cost_dc:.2f} DC."
        show_event_message_external(msg); add_message_to_log(msg)
    else:
        set_active_prompt_message(f"Error: Not enough DC. Need {cost_dc:.2f} DC."); add_message_to_log(f"Ghost Network purchase failed: Need {cost_dc:.2f} DC, Has {player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0):.2f} DC.")
    current_view = "tech_contact"; setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def _validate_tech_amount(input_str: str) -> Optional[float]:
    original_input = input_str
    if not input_str.replace('.', '', 1).isdigit():
        errmsg = "Error: Invalid amount. Must be a number."
        set_active_prompt_message(errmsg); add_message_to_log(f"Tech op validation failed: {errmsg} Input: '{original_input}'")
        return None
    try: amount = float(input_str)
    except ValueError:
        errmsg = "Error: Could not convert amount to number."
        set_active_prompt_message(errmsg); add_message_to_log(f"Tech op validation failed: {errmsg} Input: '{original_input}'")
        return None
    if amount <= 1e-9:
        errmsg = "Error: Amount must be a positive number."
        set_active_prompt_message(errmsg); add_message_to_log(f"Tech op validation failed: {errmsg} Input: {amount}")
        return None
    return amount

def _calculate_tech_heat(player_inv: PlayerInventory, game_configs: Any) -> int:
    base_heat = game_configs.HEAT_FROM_CRYPTO_TRANSACTION; effective_heat = base_heat
    if "DIGITAL_FOOTPRINT" in player_inv.unlocked_skills: effective_heat *= (1 - game_configs.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
    if player_inv.has_secure_phone: effective_heat *= (1 - game_configs.SECURE_PHONE_HEAT_REDUCTION_PERCENT)
    return int(round(effective_heat))

def action_confirm_tech_operation(player_inv: PlayerInventory, game_state: any, game_configs: any):
    global tech_input_string, tech_transaction_in_progress, coin_for_tech_transaction, current_view
    amount = _validate_tech_amount(tech_input_string)
    if amount is None: tech_input_string = ""; setup_buttons(game_state, player_inv, game_configs, game_state.current_player_region); return
    effective_heat = _calculate_tech_heat(player_inv, game_configs)
    current_player_region = game_state.current_player_region
    region_name_str = current_player_region.name.value if hasattr(current_player_region.name, 'value') else current_player_region.name
    success = False; log_prefix = f"Tech op '{tech_transaction_in_progress}' for {amount:.4f} {coin_for_tech_transaction.value if coin_for_tech_transaction else 'cash'}: "

    if tech_transaction_in_progress == "buy_crypto":
        price = game_state.current_crypto_prices.get(coin_for_tech_transaction,0); fee = amount * price * game_configs.TECH_CONTACT_SERVICES['CRYPTO_TRADE']['fee_buy_sell']; total_cost = amount * price + fee
        if price <= 1e-9: set_active_prompt_message("Error: Price unavailable."); add_message_to_log(log_prefix + "Failed - Price unavailable.")
        elif player_inv.cash >= total_cost:
            player_inv.cash -= total_cost; player_inv.add_crypto(coin_for_tech_transaction, amount)
            msg = f"Bought {amount:.4f} {coin_for_tech_transaction.value}. Heat +{effective_heat} in {region_name_str}."
            show_event_message_external(msg); add_message_to_log(log_prefix + msg); success = True
        else: set_active_prompt_message("Error: Not enough cash."); add_message_to_log(log_prefix + f"Failed - Not enough cash. Need ${total_cost:.2f}, Has ${player_inv.cash:.2f}")
    elif tech_transaction_in_progress == "sell_crypto":
        price = game_state.current_crypto_prices.get(coin_for_tech_transaction,0); gross_proceeds = amount * price; fee = gross_proceeds * game_configs.TECH_CONTACT_SERVICES['CRYPTO_TRADE']['fee_buy_sell']; net_proceeds = gross_proceeds - fee
        if price <= 1e-9: set_active_prompt_message("Error: Price unavailable."); add_message_to_log(log_prefix + "Failed - Price unavailable.")
        elif player_inv.crypto_wallet.get(coin_for_tech_transaction,0) >= amount:
            player_inv.remove_crypto(coin_for_tech_transaction, amount); player_inv.cash += net_proceeds
            msg = f"Sold {amount:.4f} {coin_for_tech_transaction.value}. Heat +{effective_heat} in {region_name_str}."
            show_event_message_external(msg); add_message_to_log(log_prefix + msg); success = True
        else: set_active_prompt_message("Error: Not enough crypto."); add_message_to_log(log_prefix + f"Failed - Not enough {coin_for_tech_transaction.value}. Have {player_inv.crypto_wallet.get(coin_for_tech_transaction,0):.4f}, Need {amount:.4f}")
    elif tech_transaction_in_progress == "launder_cash":
        fee = amount * game_configs.TECH_CONTACT_SERVICES['LAUNDER_CASH']['fee']; total_cost = amount + fee; launder_heat = int(amount * 0.05)
        if player_inv.cash >= total_cost:
            player_inv.cash -= total_cost; player_inv.pending_laundered_sc += amount; player_inv.pending_laundered_sc_arrival_day = game_state.current_day + game_configs.LAUNDERING_DELAY_DAYS
            msg = f"Laundered ${amount:,.2f}. Fee ${fee:,.2f}. Arrives day {player_inv.pending_laundered_sc_arrival_day}. Heat +{launder_heat} in {region_name_str}."
            show_event_message_external(msg); add_message_to_log(log_prefix + msg); effective_heat = launder_heat; success = True
        else: set_active_prompt_message("Error: Not enough cash for amount + fee."); add_message_to_log(log_prefix + f"Failed - Not enough cash. Need ${total_cost:.2f}, Has ${player_inv.cash:.2f}")
    elif tech_transaction_in_progress == "stake_dc":
        if coin_for_tech_transaction == CryptoCoin.DRUG_COIN and player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN,0) >= amount: 
            player_inv.remove_crypto(CryptoCoin.DRUG_COIN, amount); player_inv.staked_drug_coin['staked_amount'] = player_inv.staked_drug_coin.get('staked_amount',0) + amount
            msg = f"Staked {amount:.4f} DC."; show_event_message_external(msg); add_message_to_log(log_prefix + msg); success = True
        else: set_active_prompt_message(f"Error: Not enough {CryptoCoin.DRUG_COIN.value} or wrong coin."); add_message_to_log(log_prefix + f"Failed - Not enough {CryptoCoin.DRUG_COIN.value} or wrong coin. Have {player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN,0):.4f}")
    elif tech_transaction_in_progress == "unstake_dc": 
        if coin_for_tech_transaction == CryptoCoin.DRUG_COIN and player_inv.staked_drug_coin.get('staked_amount',0) >= amount:
            player_inv.staked_drug_coin['staked_amount'] -= amount; pending = player_inv.staked_drug_coin.get('pending_rewards', 0.0)
            player_inv.add_crypto(CryptoCoin.DRUG_COIN, amount + pending); player_inv.staked_drug_coin['pending_rewards'] = 0.0
            msg = f"Unstaked {amount:.4f} DC. Rewards collected: {pending:.4f} DC."; show_event_message_external(msg); add_message_to_log(log_prefix + msg); success = True
        else: set_active_prompt_message(f"Error: Not enough staked {CryptoCoin.DRUG_COIN.value} or wrong coin."); add_message_to_log(log_prefix + f"Failed - Not enough staked {CryptoCoin.DRUG_COIN.value}. Have {player_inv.staked_drug_coin.get('staked_amount',0):.4f}")
    
    if success and effective_heat > 0 and tech_transaction_in_progress in ["buy_crypto", "sell_crypto", "launder_cash"]:
        current_player_region.modify_heat(effective_heat); add_message_to_log(f"Applied heat: +{effective_heat} in {region_name_str} for {tech_transaction_in_progress}")

    if success: current_view = "tech_contact"; tech_input_string = ""; tech_transaction_in_progress = None
    else:
        if amount is None : tech_input_string = ""
    setup_buttons(game_state, player_inv, game_configs, current_player_region)

# --- Button Creation Helper Functions & UI Setup ---
def _create_action_button(text: str, action: Callable, x: int, y: int, width: int, height: int, font: pygame.font.Font = FONT_MEDIUM, is_enabled: bool = True) -> Button:
    return Button(x, y, width, height, text, action, is_enabled=is_enabled, font=font)
def _create_back_button(action: Callable = action_open_main_menu, text: str = "Back") -> Button:
    return Button(SCREEN_WIDTH - STD_BUTTON_WIDTH - 20, SCREEN_HEIGHT - STD_BUTTON_HEIGHT - 20, STD_BUTTON_WIDTH, STD_BUTTON_HEIGHT, text, action, font=FONT_SMALL)
def _create_button_list_vertical(start_x: int, start_y: int, button_width: int, button_height: int, spacing: int, button_definitions: List[Tuple[str, Callable, Optional[Callable[[], bool]]]]) -> List[Button]:
    buttons = [];
    for i, (text, action, enabled_check) in enumerate(button_definitions):
        y_pos = start_y + i * (button_height + spacing)
        is_enabled = enabled_check() if enabled_check else True
        buttons.append(Button(start_x, y_pos, button_width, button_height, text, action, is_enabled=is_enabled, font=FONT_SMALL))
    return buttons

def _get_active_buttons(current_view_local: str, game_state: Any, player_inv: PlayerInventory, game_configs: Any, current_region: Region) -> List[Button]:
    global main_menu_buttons, market_view_buttons, market_buy_sell_buttons, inventory_view_buttons, travel_view_buttons, tech_contact_view_buttons, skills_view_buttons, upgrades_view_buttons, transaction_input_buttons, blocking_event_popup_buttons, active_blocking_event_data, game_over_buttons, game_over_message, informant_view_buttons
    main_menu_buttons.clear(); market_view_buttons.clear(); market_buy_sell_buttons.clear(); inventory_view_buttons.clear(); travel_view_buttons.clear(); tech_contact_view_buttons.clear(); skills_view_buttons.clear(); upgrades_view_buttons.clear(); transaction_input_buttons.clear(); blocking_event_popup_buttons.clear(); game_over_buttons.clear(); informant_view_buttons.clear()
    button_width, button_height, spacing, start_x, start_y = STD_BUTTON_WIDTH, STD_BUTTON_HEIGHT, STD_BUTTON_SPACING, SCREEN_WIDTH // 2 - STD_BUTTON_WIDTH // 2, 120
    
    if current_view_local == "game_over":
        popup_width,popup_height,btn_w,btn_h = SCREEN_WIDTH*0.7,SCREEN_HEIGHT*0.5,150,40; popup_x,popup_y=(SCREEN_WIDTH-popup_width)/2,(SCREEN_HEIGHT-popup_height)/2; btn_x,btn_y=popup_x+(popup_width-btn_w)/2,popup_y+popup_height-btn_h-40
        game_over_buttons.append(_create_action_button("Exit Game",lambda:sys.exit(),btn_x,btn_y,btn_w,btn_h,font=FONT_MEDIUM)); return game_over_buttons

    if current_view_local == "main_menu":
        actions_defs = [("Market",action_open_market,None),("Inventory",action_open_inventory,None),("Travel",action_open_travel,None),("Tech Contact",action_open_tech_contact,None),("Meet Informant",action_open_informant,None),("Skills",action_open_skills,None),("Upgrades",action_open_upgrades,None)]
        col1_c = 4;
        for i,(text,action,_) in enumerate(actions_defs):
            col,row_in_col = (0,i) if i<col1_c else (1,i-col1_c); x_pos=start_x+col*(button_width+spacing); y_pos=start_y+row_in_col*(button_height+spacing)
            if col==1 and row_in_col==0: y_pos=start_y
            main_menu_buttons.append(_create_action_button(text,action,x_pos,y_pos,button_width,button_height))
        return main_menu_buttons # Corrected unindent
        
    elif current_view_local == "blocking_event_popup":
        if active_blocking_event_data:
            p_w_r,p_h_r = 0.6,0.5; p_w,p_h=SCREEN_WIDTH*p_w_r,SCREEN_HEIGHT*p_h_r; p_x,p_y=(SCREEN_WIDTH-p_w)/2,(SCREEN_HEIGHT-p_h)/2
            btn_txt=active_blocking_event_data.get('button_text','Continue'); btn_w,btn_h=150,40; btn_x,btn_y=p_x+(p_w-btn_w)/2,p_y+p_h-btn_h-20
            blocking_event_popup_buttons.append(_create_action_button(btn_txt,action_close_blocking_event_popup,btn_x,btn_y,btn_w,btn_h,font=FONT_SMALL)); return blocking_event_popup_buttons
    elif current_view_local == "informant":
        btn_w,btn_h,btn_sp=280,40,15; inf_x,inf_y=SCREEN_WIDTH//2-btn_w//2,200
        cost_r=game_configs.INFORMANT_TIP_COST_RUMOR; informant_view_buttons.append(_create_action_button(f"Ask Rumor (${cost_r:.0f})",functools.partial(action_ask_informant_rumor,player_inv,game_configs,game_state),inf_x,inf_y,btn_w,btn_h,font=FONT_SMALL,is_enabled=player_inv.cash>=cost_r))
        cost_rival=game_configs.INFORMANT_TIP_COST_RIVAL_INFO; informant_view_buttons.append(_create_action_button(f"Rival Status (${cost_rival:.0f})",functools.partial(action_ask_informant_rival_status,player_inv,game_configs,game_state),inf_x,inf_y+btn_h+btn_sp,btn_w,btn_h,font=FONT_SMALL,is_enabled=player_inv.cash>=cost_rival))
        informant_view_buttons.append(_create_back_button()); return informant_view_buttons
    elif current_view_local == "market":
        market_view_buttons.append(_create_back_button()); col_xs={"actions":650}; act_btn_w,act_btn_h=70,22
        if current_region and current_region.drug_market_data:
            sorted_drugs=sorted(current_region.drug_market_data.keys()); btn_y_off=105; line_h=28; cur_btn_y=btn_y_off
            for drug_n in sorted_drugs:
                drug_data=current_region.drug_market_data[drug_n]; qualities_avail=drug_data.get("available_qualities",{})
                if not qualities_avail: continue
                for qual_enum in sorted(qualities_avail.keys(),key=lambda q:q.value):
                    if cur_btn_y>SCREEN_HEIGHT-100:break
                    buy_p,sell_p=current_region.get_buy_price(drug_n,qual_enum),current_region.get_sell_price(drug_n,qual_enum)
                    mkt_stock=current_region.get_available_stock(drug_n,qual_enum); player_item=player_inv.get_drug_item(drug_n,qual_enum)
                    p_has_stock=player_item['quantity']if player_item else 0; can_buy=buy_p>0 and mkt_stock>0 and player_inv.cash>=buy_p; can_sell=sell_p>0 and p_has_stock>0
                    buy_x,sell_x=col_xs["actions"],col_xs["actions"]+act_btn_w+5
                    market_buy_sell_buttons.append(_create_action_button("Buy",functools.partial(action_initiate_buy,drug_n,qual_enum,buy_p,mkt_stock),buy_x,cur_btn_y-2,act_btn_w,act_btn_h,font=FONT_XSMALL,is_enabled=can_buy))
                    market_buy_sell_buttons.append(_create_action_button("Sell",functools.partial(action_initiate_sell,drug_n,qual_enum,sell_p,p_has_stock),sell_x,cur_btn_y-2,act_btn_w,act_btn_h,font=FONT_XSMALL,is_enabled=can_sell))
                    cur_btn_y+=line_h
                if cur_btn_y>SCREEN_HEIGHT-100:break
        return market_view_buttons+market_buy_sell_buttons
    elif current_view_local=="market_buy_input" or current_view_local=="market_sell_input":
        conf_y=input_box_rect.bottom+80
        transaction_input_buttons.append(_create_action_button("Confirm",functools.partial(action_confirm_transaction,player_inv,current_region,game_state),SCREEN_WIDTH//2-button_width-spacing//2,conf_y,button_width,button_height,font=FONT_SMALL))
        transaction_input_buttons.append(_create_action_button("Cancel",action_cancel_transaction,SCREEN_WIDTH//2+spacing//2,conf_y,button_width,button_height,font=FONT_SMALL)); return transaction_input_buttons
    elif current_view_local=="inventory": inventory_view_buttons.append(_create_back_button()); return inventory_view_buttons
    elif current_view_local=="travel":
        trav_defs=[]
        for r_enum in RegionName:
            if r_enum==current_region.name:continue
            dest_r_obj=game_state.all_regions[r_enum]; trav_cost=50
            trav_defs.append((f"{dest_r_obj.name.value} (${trav_cost})",functools.partial(action_travel_to_region,dest_r_obj,player_inv,game_state),lambda tc=trav_cost:player_inv.cash>=tc))
        travel_view_buttons.extend(_create_button_list_vertical(start_x,120,button_width,button_height,spacing,trav_defs)); travel_view_buttons.append(_create_back_button()); return travel_view_buttons
    elif current_view_local in ["tech_contact","tech_input_coin_select","tech_input_amount"]:
        tech_y_start=SCREEN_HEIGHT-STD_BUTTON_HEIGHT*4-STD_BUTTON_SPACING*4-20; tech_w,tech_h=220,40; tech_c1_x,tech_c2_x=50,SCREEN_WIDTH//2+50
        if current_view_local=="tech_contact":
            tech_contact_view_buttons.append(_create_action_button("Buy Crypto",functools.partial(action_initiate_tech_operation,"buy_crypto"),tech_c1_x,tech_y_start,tech_w,tech_h,font=FONT_SMALL))
            tech_contact_view_buttons.append(_create_action_button("Sell Crypto",functools.partial(action_initiate_tech_operation,"sell_crypto"),tech_c1_x,tech_y_start+tech_h+STD_BUTTON_SPACING,tech_w,tech_h,font=FONT_SMALL))
            tech_contact_view_buttons.append(_create_action_button("Launder Cash",functools.partial(action_initiate_tech_operation,"launder_cash"),tech_c1_x,tech_y_start+2*(tech_h+STD_BUTTON_SPACING),tech_w,tech_h,font=FONT_SMALL))
            tech_contact_view_buttons.append(_create_action_button("Stake DC",functools.partial(action_initiate_tech_operation,"stake_dc"),tech_c2_x,tech_y_start,tech_w,tech_h,font=FONT_SMALL)) # Changed
            tech_contact_view_buttons.append(_create_action_button("Unstake DC",functools.partial(action_initiate_tech_operation,"unstake_dc"),tech_c2_x,tech_y_start+tech_h+STD_BUTTON_SPACING,tech_w,tech_h,font=FONT_SMALL)) # Changed
            gh_skill_id="GHOST_NETWORK_ACCESS";has_gh=gh_skill_id in player_inv.unlocked_skills
            tech_contact_view_buttons.append(_create_action_button("Ghost Network Acquired"if has_gh else"Buy Ghost Network",functools.partial(action_initiate_tech_operation,"buy_ghost_network"),tech_c2_x,tech_y_start+2*(tech_h+STD_BUTTON_SPACING),tech_w,tech_h,font=FONT_SMALL,is_enabled=not has_gh))
            can_coll=player_inv.staked_drug_coin.get('pending_rewards',0.0)>1e-9;coll_btn_y=tech_y_start+3*(tech_h+STD_BUTTON_SPACING)
            tech_contact_view_buttons.append(_create_action_button("Collect Staking Rewards",functools.partial(action_initiate_tech_operation,"collect_dc_rewards"),tech_c1_x,coll_btn_y,tech_w,tech_h,font=FONT_SMALL,is_enabled=can_coll)) # Changed
            tech_contact_view_buttons.append(_create_back_button())
        elif current_view_local=="tech_input_coin_select":
            coin_defs=[]
            for c_enum in CryptoCoin:
                if tech_transaction_in_progress in["stake_dc","unstake_dc"]and c_enum!=CryptoCoin.DRUG_COIN:continue
                coin_defs.append((c_enum.value,functools.partial(action_tech_select_coin,c_enum),None))
            tech_contact_view_buttons.extend(_create_button_list_vertical(start_x,150,button_width,button_height,spacing,coin_defs))
            tech_contact_view_buttons.append(_create_action_button("Cancel",action_cancel_transaction,SCREEN_WIDTH//2-button_width//2,SCREEN_HEIGHT-button_height*2-spacing,button_width,button_height,font=FONT_SMALL))
        elif current_view_local=="tech_input_amount":
            conf_y=tech_input_box_rect.bottom+80
            tech_contact_view_buttons.append(_create_action_button("Confirm",functools.partial(action_confirm_tech_operation,player_inv,game_state,game_configs),SCREEN_WIDTH//2-button_width-spacing//2,conf_y,button_width,button_height,font=FONT_SMALL))
            tech_contact_view_buttons.append(_create_action_button("Cancel",action_cancel_transaction,SCREEN_WIDTH//2+spacing//2,conf_y,button_width,button_height,font=FONT_SMALL))
        return tech_contact_view_buttons
    elif current_view_local=="skills":
        skills_view_buttons.append(_create_back_button())
        if hasattr(game_configs,'SKILL_DEFINITIONS')and game_configs.SKILL_DEFINITIONS:
            skill_y_off=120;item_sp=80
            for skill_id,skill_d in game_configs.SKILL_DEFINITIONS.items():
                is_unl=skill_id in player_inv.unlocked_skills;can_unl=player_inv.skill_points>=skill_d['cost']and not is_unl
                skills_view_buttons.append(_create_action_button("Unlock",functools.partial(action_unlock_skill,skill_id,player_inv,game_configs),UPGRADE_ITEM_X_START+UPGRADE_ITEM_WIDTH-UPGRADE_BUTTON_WIDTH-10,skill_y_off+10,UPGRADE_BUTTON_WIDTH,UPGRADE_BUTTON_HEIGHT,font=FONT_SMALL,is_enabled=can_unl))
                skill_y_off+=item_sp
        return skills_view_buttons
    elif current_view_local=="upgrades":
        upgrades_view_buttons.append(_create_back_button())
        if hasattr(game_configs,'UPGRADE_DEFINITIONS')and game_configs.UPGRADE_DEFINITIONS:
            upg_y_off=120;item_sp=80
            cap_d=game_configs.UPGRADE_DEFINITIONS.get("EXPANDED_CAPACITY")
            if cap_d:
                num_pur=player_inv.capacity_upgrades_purchased;max_lvl=len(cap_d['costs']);can_upg_cap=num_pur<max_lvl
                cap_btn_txt="Maxed Out";is_cap_en=False
                if can_upg_cap:
                    next_cost,next_cap_lvl=cap_d['costs'][num_pur],cap_d['capacity_levels'][num_pur]
                    cap_btn_txt=f"Upgrade to {next_cap_lvl} capacity (${next_cost:,.0f})" # Changed
                    is_cap_en=player_inv.cash>=next_cost
                upgrades_view_buttons.append(_create_action_button(cap_btn_txt,functools.partial(action_purchase_capacity_upgrade,player_inv,game_configs),UPGRADE_ITEM_X_START+UPGRADE_ITEM_WIDTH-UPGRADE_BUTTON_WIDTH-10,upg_y_off+15,UPGRADE_BUTTON_WIDTH,UPGRADE_BUTTON_HEIGHT,font=FONT_XSMALL,is_enabled=is_cap_en))
                upg_y_off+=item_sp
            phone_d=game_configs.UPGRADE_DEFINITIONS.get("SECURE_PHONE")
            if phone_d:
                can_buy_ph=not player_inv.has_secure_phone and player_inv.cash>=phone_d['cost']
                upgrades_view_buttons.append(_create_action_button("Buy Secure Phone",functools.partial(action_purchase_secure_phone,player_inv,game_configs),UPGRADE_ITEM_X_START+UPGRADE_ITEM_WIDTH-UPGRADE_BUTTON_WIDTH-10,upg_y_off+15,UPGRADE_BUTTON_WIDTH,UPGRADE_BUTTON_HEIGHT,font=FONT_XSMALL,is_enabled=can_buy_ph)) # Changed
        return upgrades_view_buttons
    return[]

def setup_buttons(game_state: any, player_inv: PlayerInventory, game_configs: any, current_region: Region):
    """Sets up the active buttons for the current view."""
    global active_buttons_list_current_view, current_view
    active_buttons_list_current_view = _get_active_buttons(current_view, game_state, player_inv, game_configs, current_region)

# --- Main Game Loop ---
def game_loop(player_inventory: PlayerInventory, initial_current_region: Region, game_state_ext: any, game_configs_ext: any):
    """The main game loop."""
    global current_view, game_state_data_cache, game_configs_data_cache, player_inventory_cache, quantity_input_string, tech_input_string, active_prompt_message, prompt_message_timer, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, current_transaction_type, input_box_rect, tech_transaction_in_progress, coin_for_tech_transaction, tech_input_box_rect, active_blocking_event_data, game_over_message, game_over_buttons, active_buttons_list_current_view
    game_state_data_cache = game_state_ext; game_configs_data_cache = game_configs_ext; player_inventory_cache = player_inventory
    if not hasattr(game_state_data_cache, 'current_player_region'): game_state_data_cache.current_player_region = initial_current_region
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)
    running = True
    while running:
        current_player_region_for_frame = game_state_data_cache.current_player_region; previous_view = current_view; mouse_pos = pygame.mouse.get_pos()
        if game_over_message is not None and current_view != "game_over": previous_view = current_view; current_view = "game_over"; setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if current_view == "game_over":
                for btn in game_over_buttons:
                    if btn.handle_event(event): break 
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and game_over_buttons and game_over_buttons[0].action: game_over_buttons[0].action()
                continue 
            if current_view == "blocking_event_popup": 
                for button in blocking_event_popup_buttons:
                    if button.handle_event(event):
                        if previous_view != current_view: setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)
                        break 
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and blocking_event_popup_buttons and blocking_event_popup_buttons[0].action:
                    blocking_event_popup_buttons[0].action()
                    if previous_view != current_view: setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)
                continue
            is_market_input_active = current_view=="market_buy_input" or current_view=="market_sell_input"; is_tech_input_active = current_view=="tech_input_amount"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    if is_market_input_active or is_tech_input_active : action_cancel_transaction()
                    else: action_open_main_menu() 
                if is_market_input_active:
                    if event.key == pygame.K_RETURN: action_confirm_transaction(player_inventory_cache, current_player_region_for_frame, game_state_data_cache)
                    elif event.key == pygame.K_BACKSPACE: quantity_input_string = quantity_input_string[:-1]
                    elif event.unicode.isdigit(): quantity_input_string += event.unicode
                elif is_tech_input_active:
                    if event.key == pygame.K_RETURN: action_confirm_tech_operation(player_inventory_cache, game_state_data_cache, game_configs_data_cache)
                    elif event.key == pygame.K_BACKSPACE: tech_input_string = tech_input_string[:-1]
                    elif event.unicode.isdigit() or (event.unicode=='.' and '.' not in tech_input_string): tech_input_string += event.unicode
            button_clicked_and_view_changed = False
            if current_view not in ["game_over", "blocking_event_popup"]:
                for button in active_buttons_list_current_view:
                    if button.handle_event(event):
                        if previous_view != current_view: button_clicked_and_view_changed = True; setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)
                        break
            if not button_clicked_and_view_changed and previous_view != current_view : setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)
        update_hud_timers_external();
        if prompt_message_timer > 0: prompt_message_timer -= 1
        if prompt_message_timer <= 0: active_prompt_message = None
        screen.fill(RICH_BLACK) 
        if current_view == "game_over": draw_game_over_view_external(screen, game_over_message, game_over_buttons)
        elif current_view == "main_menu": draw_main_menu_external(screen, main_menu_buttons)
        elif current_view == "market": draw_market_view_external(screen, current_player_region_for_frame, player_inventory_cache, market_view_buttons, market_buy_sell_buttons)
        elif current_view == "inventory": draw_inventory_view_external(screen, player_inventory_cache, inventory_view_buttons) 
        elif current_view == "travel": draw_travel_view_external(screen, current_player_region_for_frame, travel_view_buttons) 
        elif current_view == "informant": draw_informant_view_external(screen, player_inventory_cache, informant_view_buttons, game_configs_data_cache)
        elif current_view in ["tech_contact", "tech_input_coin_select", "tech_input_amount"]: 
            tech_ui_state = { 'current_view': current_view, 'tech_transaction_in_progress': tech_transaction_in_progress, 'coin_for_tech_transaction': coin_for_tech_transaction, 'tech_input_string': tech_input_string, 'active_prompt_message': active_prompt_message, 'prompt_message_timer': prompt_message_timer, 'tech_input_box_rect': tech_input_box_rect }
            draw_tech_contact_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, tech_contact_view_buttons, tech_ui_state ) 
        elif current_view == "skills": draw_skills_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, skills_view_buttons) 
        elif current_view == "upgrades": draw_upgrades_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, upgrades_view_buttons) 
        elif current_view in ["market_buy_input", "market_sell_input"]: 
            transaction_ui_state = { 'quantity_input_string': quantity_input_string, 'drug_for_transaction': drug_for_transaction, 'quality_for_transaction': quality_for_transaction, 'price_for_transaction': price_for_transaction, 'available_for_transaction': available_for_transaction, 'current_transaction_type': current_transaction_type, 'active_prompt_message': active_prompt_message, 'prompt_message_timer': prompt_message_timer,  'input_box_rect': input_box_rect  }
            draw_transaction_input_view_external(screen, transaction_input_buttons, transaction_ui_state)
        if current_view != "game_over" and current_view == "blocking_event_popup" and active_blocking_event_data: draw_blocking_event_popup_external(screen, active_blocking_event_data, blocking_event_popup_buttons)
        if current_view != "game_over": draw_hud_external(screen, player_inventory_cache, current_player_region_for_frame, game_state_data_cache)
        if active_prompt_message and prompt_message_timer > 0 and current_view not in ["game_over", "blocking_event_popup"]:
            is_prompt_handled = ((current_view in ["market_buy_input", "market_sell_input", "tech_input_amount"]) or (current_view == "tech_contact" and locals().get('tech_ui_state',{}).get('active_prompt_message') and ("Select cryptocurrency" not in locals().get('tech_ui_state',{}).get('active_prompt_message') and "Enter amount" not in locals().get('tech_ui_state',{}).get('active_prompt_message'))))
            if not is_prompt_handled:
                prompt_y_pos = SCREEN_HEIGHT - 100;
                if current_view == "tech_contact": prompt_y_pos = SCREEN_HEIGHT - 120
                prompt_col = IMPERIAL_RED if any(err_word in active_prompt_message for err_word in ["Error", "Invalid", "Not enough"]) else (GOLDEN_YELLOW if "Skill" in active_prompt_message else EMERALD_GREEN)
                draw_text(screen, active_prompt_message, SCREEN_WIDTH // 2, prompt_y_pos, font=FONT_MEDIUM, color=prompt_col, center_aligned=True, max_width=SCREEN_WIDTH - 40)
        pygame.display.flip(); clock.tick(FPS)
    pygame.quit(); sys.exit()
