import pygame
import sys
import functools # For partial functions
import random # For police stop simulation
from typing import Optional, Dict, List, Tuple # For type hinting

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
from .views.informant_view import draw_informant_view as draw_informant_view_external # New import


# --- Constants ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
UPGRADE_ITEM_X_START = 50 
UPGRADE_ITEM_WIDTH = SCREEN_WIDTH - 2 * UPGRADE_ITEM_X_START 
UPGRADE_BUTTON_WIDTH = 170 
UPGRADE_BUTTON_HEIGHT = 40 


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
informant_view_buttons: List[Button] = [] # New list for Informant view


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
# ... (perform_daily_updates as before) ...
def perform_daily_updates(game_state_data: any, player_inventory_data: PlayerInventory, game_configs_data: any):
    global game_over_message 
    if game_over_message is not None: return 
    if not player_inventory_data.debt_payment_1_paid and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_1_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_1_AMOUNT: player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_1_AMOUNT; player_inventory_data.debt_payment_1_paid = True; show_event_message_external("Debt Payment 1 made!"); add_message_to_log("Paid $25k (Debt 1).")
        else: game_over_message = "GAME OVER: Failed Debt Payment 1!"; add_message_to_log(game_over_message); return
    if player_inventory_data.debt_payment_1_paid and not player_inventory_data.debt_payment_2_paid and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_2_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_2_AMOUNT: player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_2_AMOUNT; player_inventory_data.debt_payment_2_paid = True; show_event_message_external("Debt Payment 2 made!"); add_message_to_log("Paid $30k (Debt 2).")
        else: game_over_message = "GAME OVER: Failed Debt Payment 2!"; add_message_to_log(game_over_message); return
    if player_inventory_data.debt_payment_1_paid and player_inventory_data.debt_payment_2_paid and not player_inventory_data.debt_payment_3_paid and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_3_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_3_AMOUNT: player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_3_AMOUNT; player_inventory_data.debt_payment_3_paid = True; show_event_message_external("Final debt paid! You are free!"); add_message_to_log("Paid $20k (Final Debt). You are FREE!")
        else: game_over_message = "GAME OVER: Failed Final Debt Payment!"; add_message_to_log(game_over_message); return
    if hasattr(game_state_data, 'all_regions'): [ (r.restock_market(), market_impact.decay_regional_heat(r), market_impact.decay_player_market_impact(r), market_impact.decay_rival_market_impact(r, game_state_data.current_day), event_manager.update_active_events(r, game_state_data.current_day)) for r in game_state_data.all_regions.values() if hasattr(r, 'restock_market') ] # TODO: Event manager messages
    if hasattr(game_state_data, 'update_daily_crypto_prices'): game_state_data.update_daily_crypto_prices(game_configs_data.CRYPTO_VOLATILITY, game_configs_data.CRYPTO_MIN_PRICE)
    if hasattr(player_inventory_data, 'staked_drug_coin') and player_inventory_data.staked_drug_coin.get('staked_amount',0) > 0 and hasattr(game_configs_data, 'DC_STAKING_DAILY_RETURN_PERCENT'):
        reward = player_inventory_data.staked_drug_coin['staked_amount'] * game_configs_data.DC_STAKING_DAILY_RETURN_PERCENT
        player_inventory_data.staked_drug_coin['pending_rewards'] = player_inventory_data.staked_drug_coin.get('pending_rewards',0) + reward
        if reward > 1e-5: show_event_message_external(f"Accrued {reward:.4f} DC rewards. Collect at Tech Contact.")
    if hasattr(player_inventory_data, 'pending_laundered_sc_arrival_day') and player_inventory_data.pending_laundered_sc_arrival_day is not None and game_state_data.current_day >= player_inventory_data.pending_laundered_sc_arrival_day:
        amount = player_inventory_data.pending_laundered_sc; player_inventory_data.add_crypto(CryptoCoin.STABLE_COIN, amount); show_event_message_external(f"{amount:.2f} SC (laundered) arrived."); player_inventory_data.pending_laundered_sc=0.0; player_inventory_data.pending_laundered_sc_arrival_day=None
    if hasattr(game_state_data, 'current_player_region') and hasattr(event_manager, 'trigger_random_market_event'): event_manager.trigger_random_market_event(game_state_data.current_player_region, game_state_data.current_day, player_inventory_data, getattr(game_state_data, 'ai_rivals',[]), show_event_message_external)
    if hasattr(game_state_data, 'ai_rivals'): [ market_impact.process_rival_turn(r, game_state_data.all_regions, game_state_data.current_day, game_configs_data, show_event_message_external) for r in game_state_data.ai_rivals if not r.is_busted ]

def set_active_prompt_message(message: str, duration_frames: int = PROMPT_DURATION_FRAMES):
    global active_prompt_message, prompt_message_timer
    active_prompt_message = message; prompt_message_timer = duration_frames

# --- Action Functions ---
def action_open_main_menu(): global current_view; current_view = "main_menu"
def action_open_market(): global current_view; current_view = "market"
def action_open_inventory(): global current_view; current_view = "inventory"
def action_open_travel(): global current_view; current_view = "travel"
def action_open_tech_contact(): global current_view; current_view = "tech_contact"
def action_open_skills(): global current_view; current_view = "skills"
def action_open_upgrades(): global current_view; current_view = "upgrades"
def action_open_informant(): global current_view; current_view = "informant" # New action

def action_close_blocking_event_popup():
    global active_blocking_event_data, current_view
    active_blocking_event_data = None; current_view = "main_menu" 

def action_travel_to_region(destination_region: Region, player_inv: PlayerInventory, game_state: any):
    # ... (travel logic as before, ensure setup_buttons is called if view changes) ...
    global current_view, game_state_data_cache, player_inventory_cache, game_configs_data_cache, active_blocking_event_data, game_over_message
    if game_over_message is not None: return 
    original_day_before_travel = game_state.current_day 
    game_state.current_player_region = destination_region 
    game_state.current_day += 1 
    perform_daily_updates(game_state_data_cache, player_inventory_cache, game_configs_data_cache)
    if game_over_message is not None: current_view = "game_over"; return
    if game_state.current_day % game_configs_data_cache.SKILL_POINTS_PER_X_DAYS == 0 and game_state.current_day > original_day_before_travel: player_inv.skill_points +=1; show_event_message_external(f"Day advanced. +1 Skill Point. Total: {player_inv.skill_points}")
    region_heat = destination_region.current_heat; threshold = game_configs_data_cache.POLICE_STOP_HEAT_THRESHOLD; base_chance = game_configs_data_cache.POLICE_STOP_BASE_CHANCE; per_point_increase = game_configs_data_cache.POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD
    calculated_chance = base_chance; 
    if region_heat >= threshold: calculated_chance += (region_heat - threshold) * per_point_increase
    final_police_stop_chance = max(0.0, min(calculated_chance, 0.95))
    if random.random() < final_police_stop_chance:
        show_event_message_external(f"Arriving in {destination_region.name.value}... flashing lights!")
        if random.random() < 0.33: active_blocking_event_data = {'title': "Police Stop!", 'messages': [f"Pulled over by {destination_region.name.value} PD.", "They give you a stern look and a warning."], 'button_text': "Continue"}
        elif random.random() < 0.66: fine = min(player_inv.cash, random.randint(100,500)*(1+destination_region.current_heat//20)); player_inv.cash -= fine; active_blocking_event_data = {'title': "Police Stop - Fine!", 'messages': ["Police stop for 'random' check.", f"Minor infraction. Fined ${fine:,.0f}."], 'button_text': "Pay Fine"}; show_event_message_external(f"Paid fine of ${fine:,.0f}.")
        else: active_blocking_event_data = {'title': "Police Stop - Searched!", 'messages': ["Police are suspicious, search vehicle!", "Luckily, you were clean... this time.", "(Confiscation logic TBD)"], 'button_text': "Phew!"}
        current_view = "blocking_event_popup"
    else: show_event_message_external(f"Arrived safely in {destination_region.name.value}."); current_view = "main_menu"

def action_ask_informant_rumor(player_inv: PlayerInventory, game_configs: any, game_state: any):
    cost = game_configs.INFORMANT_TIP_COST_RUMOR
    if player_inv.cash >= cost:
        player_inv.cash -= cost
        player_inv.informant_trust = min(player_inv.informant_trust + game_configs.INFORMANT_TRUST_GAIN_PER_TIP, game_configs.INFORMANT_MAX_TRUST)
        # Simple simulated rumor logic for now
        rumors = [
            "Heard The Chemist is planning a big move in Downtown soon.",
            "Silas is looking for extra muscle, might be risky.",
            f"Word is, {random.choice(list(DrugName)).value} prices might spike in {random.choice(list(RegionName)).value}.",
            "Cops are cracking down in The Docks, lay low.",
            "Someone saw a new shipment of high-quality Pills arriving at Suburbia."
        ]
        rumor = random.choice(rumors)
        show_event_message_external(f"Informant whispers: '{rumor}'")
        add_message_to_log(f"Paid informant ${cost:.0f} for a rumor.")
    else:
        show_event_message_external(f"Not enough cash for a rumor. Need ${cost:.0f}.")
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
        else:
            info_parts.append("No news on rivals right now.")
        
        final_info = " ".join(info_parts)
        show_event_message_external(f"Informant on rivals: {final_info}")
        add_message_to_log(f"Paid informant ${cost:.0f} for rival status.")
    else:
        show_event_message_external(f"Not enough cash for rival info. Need ${cost:.0f}.")
    setup_buttons(game_state, player_inv, game_configs, game_state.current_player_region)

# ... (other action functions as before) ...
def action_initiate_buy(drug: DrugName, quality: DrugQuality, price: float, available: int):
    global current_view, current_transaction_type, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, quantity_input_string
    current_view = "market_buy_input"; current_transaction_type = "buy"; drug_for_transaction = drug; quality_for_transaction = quality; price_for_transaction = price; available_for_transaction = available; quantity_input_string = ""
    set_active_prompt_message("Enter quantity to buy.", duration_frames=PROMPT_DURATION_FRAMES*2)

def action_initiate_sell(drug: DrugName, quality: DrugQuality, price: float, available: int):
    global current_view, current_transaction_type, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, quantity_input_string
    current_view = "market_sell_input"; current_transaction_type = "sell"; drug_for_transaction = drug; quality_for_transaction = quality; price_for_transaction = price; available_for_transaction = available; quantity_input_string = ""
    set_active_prompt_message("Enter quantity to sell.", duration_frames=PROMPT_DURATION_FRAMES*2)

def action_confirm_transaction(player_inv: PlayerInventory, market_region: Region, game_state: any):
    global quantity_input_string, current_transaction_type, drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, current_view, game_configs_data_cache
    if not quantity_input_string.isdigit() or int(quantity_input_string) <= 0: set_active_prompt_message("Error: Invalid quantity."); quantity_input_string = ""; return
    quantity = int(quantity_input_string)
    if current_transaction_type == "buy":
        cost = quantity * price_for_transaction
        if cost > player_inv.cash: set_active_prompt_message("Error: Not enough cash.")
        elif quantity > available_for_transaction: set_active_prompt_message("Error: Not enough market stock.")
        elif player_inv.current_load + quantity > player_inv.max_capacity: set_active_prompt_message("Error: Not enough space.")
        else:
            player_inv.cash -= cost; player_inv.add_drug(drug_for_transaction, quality_for_transaction, quantity)
            market_region.update_stock_on_buy(drug_for_transaction, quality_for_transaction, quantity)
            market_impact.apply_player_buy_impact(market_region, drug_for_transaction.value, quantity) 
            show_event_message_external(f"Bought {quantity} {drug_for_transaction.value} ({quality_for_transaction.name}).")
            current_view = "market"
    elif current_transaction_type == "sell":
        if quantity > available_for_transaction: set_active_prompt_message("Error: Not enough to sell.")
        else:
            player_inv.cash += quantity*price_for_transaction; player_inv.remove_drug(drug_for_transaction, quality_for_transaction, quantity)
            market_region.update_stock_on_sell(drug_for_transaction, quality_for_transaction, quantity)
            drug_tier = market_region.drug_market_data[drug_for_transaction].get('tier',1); heat_per_unit = game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER.get(drug_tier,1)
            total_heat = heat_per_unit * quantity; market_region.modify_heat(total_heat)
            market_impact.apply_player_sell_impact(market_region, drug_for_transaction.value, quantity) 
            show_event_message_external(f"Sold {quantity} {drug_for_transaction.value}. Heat +{total_heat} in {market_region.name.value}.")
            current_view = "market"
    quantity_input_string = ""; setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, market_region)

def action_cancel_transaction():
    global current_view, quantity_input_string, tech_input_string, tech_transaction_in_progress, active_prompt_message
    if current_view in ["market_buy_input", "market_sell_input"]: current_view = "market"
    elif current_view in ["tech_input_coin_select", "tech_input_amount"]: current_view = "tech_contact"
    quantity_input_string = ""; tech_input_string = ""; tech_transaction_in_progress = None; active_prompt_message = None

def action_unlock_skill(skill_id: str, player_inv: PlayerInventory, game_configs: any):
    if skill_id in player_inv.unlocked_skills: set_active_prompt_message("Skill already unlocked."); return
    skill_def = game_configs.SKILL_DEFINITIONS.get(skill_id)
    if not skill_def: set_active_prompt_message("Error: Skill definition not found."); return
    if player_inv.skill_points >= skill_def['cost']: 
        player_inv.skill_points -= skill_def['cost']; player_inv.unlocked_skills.add(skill_id)
        show_event_message_external(f"Skill Unlocked: {skill_def['name']}")
    else: set_active_prompt_message("Not enough skill points.")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_purchase_capacity_upgrade(player_inv: PlayerInventory, game_configs: any):
    upgrade_def = game_configs.UPGRADE_DEFINITIONS.get("EXPANDED_CAPACITY")
    if not upgrade_def: set_active_prompt_message("Error: Upgrade definition not found."); return
    num_purchased = player_inv.capacity_upgrades_purchased
    max_levels = len(upgrade_def['costs'])
    if num_purchased >= max_levels: set_active_prompt_message("Capacity fully upgraded."); return
    cost = upgrade_def['costs'][num_purchased]; next_cap = upgrade_def['capacity_levels'][num_purchased]
    if player_inv.cash >= cost: 
        player_inv.cash -= cost; player_inv.max_capacity = next_cap
        if hasattr(player_inv, 'capacity_upgrades_purchased'): player_inv.capacity_upgrades_purchased += 1
        else: player_inv.capacity_upgrades_purchased = 1
        show_event_message_external(f"Capacity upgraded to {next_cap}!")
    else: set_active_prompt_message(f"Not enough cash. Need ${cost:,.0f}.")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_purchase_secure_phone(player_inv: PlayerInventory, game_configs: any):
    if player_inv.has_secure_phone: set_active_prompt_message("Secure Phone already owned."); return
    upgrade_def = game_configs.UPGRADE_DEFINITIONS.get("SECURE_PHONE") 
    if not upgrade_def: set_active_prompt_message("Error: Upgrade definition not found."); return
    if player_inv.cash >= upgrade_def['cost']: player_inv.cash -= upgrade_def['cost']; player_inv.has_secure_phone = True; show_event_message_external("Secure Comms Phone purchased!")
    else: set_active_prompt_message(f"Not enough cash. Need ${upgrade_def['cost']:,0f}.")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)
    
def action_collect_staking_rewards(player_inv: PlayerInventory): 
    rewards_to_collect = player_inv.staked_drug_coin.get('pending_rewards', 0.0)
    if rewards_to_collect > 0.00001: 
        player_inv.add_crypto(CryptoCoin.DRUG_COIN, rewards_to_collect)
        player_inv.staked_drug_coin['pending_rewards'] = 0.0
        show_event_message_external(f"Collected {rewards_to_collect:.4f} DC staking rewards.")
    else: show_event_message_external("No staking rewards to collect.")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_initiate_tech_operation(operation_type: str): 
    global current_view, tech_transaction_in_progress, coin_for_tech_transaction, tech_input_string
    tech_transaction_in_progress = operation_type; tech_input_string = ""
    if operation_type == "collect_dc_rewards": action_collect_staking_rewards(player_inventory_cache); return 
    elif operation_type in ["buy_crypto", "sell_crypto", "stake_dc", "unstake_dc"]: current_view = "tech_input_coin_select"; set_active_prompt_message("Select cryptocurrency.")
    elif operation_type == "launder_cash": coin_for_tech_transaction = None; current_view = "tech_input_amount"; set_active_prompt_message("Enter cash amount to launder.")
    elif operation_type == "buy_ghost_network": action_purchase_ghost_network(player_inventory_cache, game_configs_data_cache); return 
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_tech_select_coin(coin: CryptoCoin):
    global current_view, coin_for_tech_transaction, tech_transaction_in_progress
    coin_for_tech_transaction = coin; current_view = "tech_input_amount"; verb = tech_transaction_in_progress.split("_")[0]
    set_active_prompt_message(f"Enter amount of {coin.value} to {verb}.")
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_purchase_ghost_network(player_inv: PlayerInventory, game_configs: any):
    global current_view
    skill_id = "GHOST_NETWORK_ACCESS"; cost_dc = getattr(game_configs, 'GHOST_NETWORK_ACCESS_COST_DC', 50.0) 
    if skill_id in player_inv.unlocked_skills: show_event_message_external("Ghost Network Access already acquired.")
    elif player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0) >= cost_dc:
        player_inv.remove_crypto(CryptoCoin.DRUG_COIN, cost_dc); player_inv.unlocked_skills.add(skill_id)
        show_event_message_external(f"Ghost Network Access acquired for {cost_dc:.2f} DC!")
    else: show_event_message_external(f"Not enough DrugCoin. Need {cost_dc:.2f} DC.")
    current_view = "tech_contact"; setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def action_confirm_tech_operation(player_inv: PlayerInventory, game_state: any, game_configs: any):
    global tech_input_string, tech_transaction_in_progress, coin_for_tech_transaction, current_view, game_state_data_cache, game_configs_data_cache
    if not tech_input_string.replace('.', '', 1).isdigit() or float(tech_input_string) <= 0: 
        set_active_prompt_message("Error: Invalid amount.")
        tech_input_string = ""
        return
    
    amount = float(tech_input_string)
    base_heat = game_configs.HEAT_FROM_CRYPTO_TRANSACTION
    effective_heat = base_heat 
    # Apply skill/item reductions
    if "DIGITAL_FOOTPRINT" in player_inv.unlocked_skills: 
        effective_heat *= (1 - game_configs.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
    if player_inv.has_secure_phone: 
        effective_heat *= (1 - game_configs.SECURE_PHONE_HEAT_REDUCTION_PERCENT)
    effective_heat = int(round(effective_heat))
    current_player_region = game_state_data_cache.current_player_region
    region_name_str = current_player_region.name.value if hasattr(current_player_region.name, 'value') else current_player_region.name

    if tech_transaction_in_progress == "buy_crypto":
        price = game_state.current_crypto_prices.get(coin_for_tech_transaction,0)
        fee = amount * price * game_configs.TECH_CONTACT_SERVICES['CRYPTO_TRADE']['fee_buy_sell']
        if price == 0: 
            set_active_prompt_message("Error: Price unavailable.")
            return
        if player_inv.cash >= amount * price + fee: 
            player_inv.cash -= (amount * price + fee)
            player_inv.add_crypto(coin_for_tech_transaction, amount) 
            if effective_heat > 0: 
                current_player_region.modify_heat(effective_heat)
            show_event_message_external(f"Bought {amount:.4f} {coin_for_tech_transaction.value}. Heat +{effective_heat} in {region_name_str}.")
        else: 
            set_active_prompt_message("Error: Not enough cash.")
            tech_input_string = ""
            return
    elif tech_transaction_in_progress == "sell_crypto":
        price = game_state.current_crypto_prices.get(coin_for_tech_transaction,0)
        fee = amount * price * game_configs.TECH_CONTACT_SERVICES['CRYPTO_TRADE']['fee_buy_sell']
        if price == 0: 
            set_active_prompt_message("Error: Price unavailable.")
            return
        if player_inv.crypto_wallet.get(coin_for_tech_transaction,0) >= amount: 
            player_inv.remove_crypto(coin_for_tech_transaction, amount)
            player_inv.cash += (amount * price - fee) 
            if effective_heat > 0: 
                current_player_region.modify_heat(effective_heat)
            show_event_message_external(f"Sold {amount:.4f} {coin_for_tech_transaction.value}. Heat +{effective_heat} in {region_name_str}.")
        else: 
            set_active_prompt_message("Error: Not enough crypto.")
            tech_input_string = ""
            return
    elif tech_transaction_in_progress == "launder_cash":
        fee = amount * game_configs.TECH_CONTACT_SERVICES['LAUNDER_CASH']['fee']
        launder_heat = int(amount * 0.05) 
        if player_inv.cash >= (amount + fee): 
            player_inv.cash -= (amount + fee) 
            player_inv.pending_laundered_sc += amount
            player_inv.pending_laundered_sc_arrival_day = game_state.current_day + game_configs.LAUNDERING_DELAY_DAYS
            if launder_heat > 0: 
                current_player_region.modify_heat(launder_heat)
            show_event_message_external(f"Laundered ${amount:,.2f}. Fee ${fee:,.2f}. Arrives day {player_inv.pending_laundered_sc_arrival_day}. Heat +{launder_heat} in {region_name_str}.")
        else: 
            set_active_prompt_message("Error: Not enough cash for amount + fee.")
            tech_input_string = ""
            return
    elif tech_transaction_in_progress == "stake_dc":
        if coin_for_tech_transaction == CryptoCoin.DRUG_COIN and player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN,0) >= amount: 
            player_inv.remove_crypto(CryptoCoin.DRUG_COIN, amount)
            player_inv.staked_drug_coin['staked_amount'] += amount
            show_event_message_external(f"Staked {amount:.4f} DC.")
        else: 
            set_active_prompt_message(f"Error: Not enough {CryptoCoin.DRUG_COIN.value} or wrong coin.")
            tech_input_string = ""
            return
    elif tech_transaction_in_progress == "unstake_dc": 
        if coin_for_tech_transaction == CryptoCoin.DRUG_COIN and player_inv.staked_drug_coin['staked_amount'] >= amount:
            player_inv.staked_drug_coin['staked_amount'] -= amount
            pending = player_inv.staked_drug_coin['pending_rewards']
            player_inv.add_crypto(CryptoCoin.DRUG_COIN, amount + pending)
            player_inv.staked_drug_coin['pending_rewards'] = 0.0
            show_event_message_external(f"Unstaked {amount:.4f} DC. Rewards collected: {pending:.4f} DC.")
        else: 
            set_active_prompt_message(f"Error: Not enough staked {CryptoCoin.DRUG_COIN.value} or wrong coin.")
            tech_input_string = ""
            return
            
    current_view = "tech_contact"
    tech_input_string = ""
    tech_transaction_in_progress = None
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)

def handle_tech_transaction_input_confirm(input_value):
    global tech_transaction_in_progress, tech_input_string, active_prompt_message, player_inv, game_state, current_player_region, game_configs
    # ... (other global declarations if needed)
    try:
        amount = float(input_value)
        if amount <= 0: set_active_prompt_message("Amount must be positive."); tech_input_string = ""; return
    except ValueError: set_active_prompt_message("Invalid amount entered."); tech_input_string = ""; return

    # Heat calculation (example, adjust as per your game logic)
    base_heat = game_configs.HEAT_FROM_CRYPTO_TRANSACTION
    effective_heat = base_heat
    # Apply skill/item reductions if applicable
    # ... (your heat reduction logic here) ...
    effective_heat = int(round(effective_heat))
    
    # Ensure current_player_region is valid and has a name attribute for messages
    region_name_str = "Unknown Region"
    if hasattr(current_player_region, 'name') and hasattr(current_player_region.name, 'value'):
        region_name_str = current_player_region.name.value
    elif hasattr(current_player_region, 'name'):
        region_name_str = current_player_region.name 

    if tech_transaction_in_progress == "buy_crypto":
        price = game_state.current_crypto_prices.get(coin_for_tech_transaction,0)
        fee = amount * price * game_configs.TECH_CONTACT_SERVICES['CRYPTO_TRADE']['fee_buy_sell']
        if price == 0: set_active_prompt_message("Error: Price unavailable."); return
        if player_inv.cash >= amount * price + fee: 
            player_inv.cash -= (amount * price + fee)
            player_inv.add_crypto(coin_for_tech_transaction, amount)
            if effective_heat > 0 and hasattr(current_player_region, 'modify_heat'): 
                current_player_region.modify_heat(effective_heat)
            show_event_message_external(f"Bought {amount:.4f} {coin_for_tech_transaction.value}. Heat +{effective_heat} in {region_name_str}.")
        else: set_active_prompt_message("Error: Not enough cash."); tech_input_string = ""; return
    elif tech_transaction_in_progress == "sell_crypto":
        price = game_state.current_crypto_prices.get(coin_for_tech_transaction,0)
        fee = amount * price * game_configs.TECH_CONTACT_SERVICES['CRYPTO_TRADE']['fee_buy_sell']
        if price == 0: set_active_prompt_message("Error: Price unavailable."); return
        if player_inv.crypto_wallet.get(coin_for_tech_transaction,0) >= amount: 
            player_inv.remove_crypto(coin_for_tech_transaction, amount)
            player_inv.cash += (amount * price - fee)
            if effective_heat > 0 and hasattr(current_player_region, 'modify_heat'): 
                current_player_region.modify_heat(effective_heat)
            show_event_message_external(f"Sold {amount:.4f} {coin_for_tech_transaction.value}. Heat +{effective_heat} in {region_name_str}.")
        else: set_active_prompt_message("Error: Not enough crypto."); tech_input_string = ""; return
    elif tech_transaction_in_progress == "launder_cash":
        fee = amount * game_configs.TECH_CONTACT_SERVICES['LAUNDER_CASH']['fee']
        launder_heat = int(amount * 0.05) # Example heat for laundering
        if player_inv.cash >= (amount + fee): 
            player_inv.cash -= (amount + fee)
            player_inv.pending_laundered_sc += amount
            player_inv.pending_laundered_sc_arrival_day = game_state.current_day + game_configs.LAUNDERING_DELAY_DAYS
            if launder_heat > 0 and hasattr(current_player_region, 'modify_heat'): 
                current_player_region.modify_heat(launder_heat)
            show_event_message_external(f"Laundered ${amount:,.2f}. Fee ${fee:,.2f}. Arrives day {player_inv.pending_laundered_sc_arrival_day}. Heat +{launder_heat} in {region_name_str}.")
        else: set_active_prompt_message("Error: Not enough cash for amount + fee."); tech_input_string = ""; return
    elif tech_transaction_in_progress == "stake_dc":
        # Assuming coin_for_tech_transaction is set to CryptoCoin.DRUG_COIN for staking
        if player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN,0) >= amount: 
            player_inv.remove_crypto(CryptoCoin.DRUG_COIN, amount)
            player_inv.staked_drug_coin['staked_amount'] += amount
            show_event_message_external(f"Staked {amount:.4f} DC.")
        else: set_active_prompt_message(f"Error: Not enough {CryptoCoin.DRUG_COIN.value} or wrong coin."); tech_input_string = ""; return
    elif tech_transaction_in_progress == "unstake_dc": 
        # Assuming coin_for_tech_transaction is set to CryptoCoin.DRUG_COIN for unstaking
        if player_inv.staked_drug_coin['staked_amount'] >= amount:
            player_inv.staked_drug_coin['staked_amount'] -= amount
            pending_rewards = player_inv.staked_drug_coin.get('pending_rewards', 0.0) # Safely get pending_rewards
            player_inv.add_crypto(CryptoCoin.DRUG_COIN, amount + pending_rewards)
            player_inv.staked_drug_coin['pending_rewards'] = 0.0
            show_event_message_external(f"Unstaked {amount:.4f} DC. Rewards {pending_rewards:.4f} DC added to wallet.")
        else: set_active_prompt_message("Error: Not enough staked DC."); tech_input_string = ""; return
    
    # Reset after transaction
    tech_transaction_in_progress = None
    tech_input_string = ""
    active_prompt_message = None
    # Potentially switch view or update UI elements

# --- UI Setup Functions ---
def setup_buttons(game_state: any, player_inv: PlayerInventory, game_configs: any, current_region: Region):
    global main_menu_buttons, market_view_buttons, market_buy_sell_buttons, inventory_view_buttons, travel_view_buttons, tech_contact_view_buttons, skills_view_buttons, upgrades_view_buttons, transaction_input_buttons, blocking_event_popup_buttons, active_blocking_event_data, game_over_buttons, game_over_message, informant_view_buttons
    main_menu_buttons.clear(); market_view_buttons.clear(); market_buy_sell_buttons.clear(); inventory_view_buttons.clear()
    travel_view_buttons.clear(); tech_contact_view_buttons.clear(); skills_view_buttons.clear(); upgrades_view_buttons.clear()
    transaction_input_buttons.clear(); blocking_event_popup_buttons.clear(); game_over_buttons.clear(); informant_view_buttons.clear()
    button_width, button_height = 200, 50; spacing = 10; start_x, start_y = SCREEN_WIDTH // 2 - button_width // 2, 120 
    
    if current_view == "game_over":
        popup_width = SCREEN_WIDTH * 0.7; popup_height = SCREEN_HEIGHT * 0.5
        popup_x = (SCREEN_WIDTH - popup_width) / 2; popup_y = (SCREEN_HEIGHT - popup_height) / 2
        btn_w, btn_h = 150, 40; btn_x = popup_x + (popup_width - btn_w) / 2; btn_y = popup_y + popup_height - btn_h - 40 
        game_over_buttons.append(Button(btn_x, btn_y, btn_w, btn_h, "Exit Game", lambda: sys.exit(), font=FONT_MEDIUM))
        return 

    if current_view == "main_menu":
        actions = [("Market", action_open_market), ("Inventory", action_open_inventory), ("Travel", action_open_travel), 
                   ("Tech Contact", action_open_tech_contact), ("Meet Informant", action_open_informant), 
                   ("Skills", action_open_skills), ("Upgrades", action_open_upgrades)]
        for i, (text, action) in enumerate(actions): 
            y_pos = start_y + i * (button_height + spacing)
            if i >= 4: # Shift 2nd column of buttons up a bit
                y_pos = start_y + (i-4) * (button_height + spacing)
                if i == 4: y_pos = start_y # Reset y_pos for the first button in the new conceptual "column"
                main_menu_buttons.append(Button(start_x + button_width + spacing if i>=4 else start_x, y_pos, button_width, button_height, text, action, font=FONT_MEDIUM))
            else:
                 main_menu_buttons.append(Button(start_x, y_pos, button_width, button_height, text, action, font=FONT_MEDIUM))


    elif current_view == "blocking_event_popup":
        if active_blocking_event_data:
            popup_width_ratio = 0.6 ; popup_height_ratio = 0.5
            popup_width = SCREEN_WIDTH * popup_width_ratio; popup_height = SCREEN_HEIGHT * popup_height_ratio
            popup_x = (SCREEN_WIDTH - popup_width) / 2; popup_y = (SCREEN_HEIGHT - popup_height) / 2
            button_text = active_blocking_event_data.get('button_text', 'Continue'); btn_w, btn_h = 150, 40
            btn_x = popup_x + (popup_width - btn_w) / 2; btn_y = popup_y + popup_height - btn_h - 20
            blocking_event_popup_buttons.append(Button(btn_x, btn_y, btn_w, btn_h, button_text, action_close_blocking_event_popup, font=FONT_SMALL))
    elif current_view == "informant":
        btn_w, btn_h, btn_spacing = 280, 40, 15
        info_start_x = SCREEN_WIDTH // 2 - btn_w // 2
        info_start_y = 200 # Below cash and trust display
        
        cost_rumor = game_configs.INFORMANT_TIP_COST_RUMOR
        informant_view_buttons.append(Button(info_start_x, info_start_y, btn_w, btn_h, f"Ask Rumor (${cost_rumor:.0f})", 
            functools.partial(action_ask_informant_rumor, player_inv, game_configs, game_state), 
            is_enabled=player_inv.cash >= cost_rumor, font=FONT_SMALL))
        
        cost_rival = game_configs.INFORMANT_TIP_COST_RIVAL_INFO
        informant_view_buttons.append(Button(info_start_x, info_start_y + btn_h + btn_spacing, btn_w, btn_h, f"Rival Status (${cost_rival:.0f})", 
            functools.partial(action_ask_informant_rival_status, player_inv, game_configs, game_state), 
            is_enabled=player_inv.cash >= cost_rival, font=FONT_SMALL))
        
        informant_view_buttons.append(Button(SCREEN_WIDTH - button_width - 20, SCREEN_HEIGHT - button_height - 20, button_width, button_height, "Back", action_open_main_menu, font=FONT_SMALL))

    # ... (rest of setup_buttons for other views, largely unchanged)
    elif current_view == "market":
        market_view_buttons.append(Button(SCREEN_WIDTH - button_width - 20, SCREEN_HEIGHT - button_height - 20, button_width, button_height, "Back", action_open_main_menu, font=FONT_SMALL))
        col_xs = {"actions": 650}; action_button_width = 70; action_button_height = 22
        if current_region and current_region.drug_market_data:
            sorted_drug_names = sorted(current_region.drug_market_data.keys())
            button_y_offset_start = 105 ; line_h = 28 ; current_button_y = button_y_offset_start
            for drug_name in sorted_drug_names:
                drug_data_dict = current_region.drug_market_data[drug_name]; qualities_available = drug_data_dict.get("available_qualities", {})
                if not qualities_available: continue
                for quality_enum in sorted(qualities_available.keys(), key=lambda q: q.value):
                    if current_button_y > SCREEN_HEIGHT - 100: break
                    buy_price = current_region.get_buy_price(drug_name, quality_enum); sell_price = current_region.get_sell_price(drug_name, quality_enum)
                    market_stock = current_region.get_available_stock(drug_name, quality_enum); player_stock_item = player_inv.get_drug_item(drug_name, quality_enum)
                    player_has_stock = player_stock_item['quantity'] if player_stock_item else 0
                    can_buy = buy_price > 0 and market_stock > 0 and player_inv.cash >= buy_price; can_sell = sell_price > 0 and player_has_stock > 0
                    buy_btn_x = col_xs["actions"]; sell_btn_x = col_xs["actions"] + action_button_width + 5
                    market_buy_sell_buttons.append(Button(buy_btn_x, current_button_y -2, action_button_width, action_button_height, "Buy", functools.partial(action_initiate_buy, drug_name, quality_enum, buy_price, market_stock), is_enabled=can_buy, font=FONT_XSMALL))
                    market_buy_sell_buttons.append(Button(sell_btn_x, current_button_y -2, action_button_width, action_button_height, "Sell", functools.partial(action_initiate_sell, drug_name, quality_enum, sell_price, player_has_stock), is_enabled=can_sell, font=FONT_XSMALL))
                    current_button_y += line_h
                if current_button_y > SCREEN_HEIGHT - 100: break
    elif current_view == "market_buy_input" or current_view == "market_sell_input":
        confirm_y = input_box_rect.bottom + 80
        transaction_input_buttons.append(Button(SCREEN_WIDTH // 2 - button_width - spacing // 2, confirm_y, button_width, button_height, "Confirm", functools.partial(action_confirm_transaction, player_inv, current_region, game_state), font=FONT_SMALL))
        transaction_input_buttons.append(Button(SCREEN_WIDTH // 2 + spacing // 2, confirm_y, button_width, button_height, "Cancel", action_cancel_transaction, font=FONT_SMALL))
    elif current_view == "inventory": inventory_view_buttons.append(Button(SCREEN_WIDTH - button_width - 20, SCREEN_HEIGHT - button_height - 20, button_width, button_height, "Back", action_open_main_menu, font=FONT_SMALL))
    elif current_view == "travel":
        travel_y_start = 120
        for i, region_enum in enumerate(RegionName):
            if region_enum.value == current_region.name: continue
            dest_region_obj = game_state.all_regions[region_enum]; travel_cost = 50 
            btn_text = f"{dest_region_obj.name} (${travel_cost})"; can_travel = player_inv.cash >= travel_cost
            travel_view_buttons.append(Button(start_x, travel_y_start + i * (button_height + spacing), button_width, button_height, btn_text, functools.partial(action_travel_to_region, dest_region_obj, player_inv, game_state), is_enabled=can_travel, font=FONT_SMALL))
        travel_view_buttons.append(Button(SCREEN_WIDTH - button_width - 20, SCREEN_HEIGHT - button_height - 20, button_width, button_height, "Back", action_open_main_menu, font=FONT_SMALL))
    elif current_view == "tech_contact":
        tech_btn_y_start = SCREEN_HEIGHT - button_height * 4 - spacing * 4 - 20 
        tech_btn_width, tech_btn_height = 220, 40; tech_col1_x = 50; tech_col2_x = SCREEN_WIDTH // 2 + 50
        tech_contact_view_buttons.append(Button(tech_col1_x, tech_btn_y_start, tech_btn_width, tech_btn_height, "Buy Crypto", functools.partial(action_initiate_tech_operation, "buy_crypto"), font=FONT_SMALL))
        tech_contact_view_buttons.append(Button(tech_col1_x, tech_btn_y_start + tech_btn_height + spacing, tech_btn_width, tech_btn_height, "Sell Crypto", functools.partial(action_initiate_tech_operation, "sell_crypto"), font=FONT_SMALL))
        tech_contact_view_buttons.append(Button(tech_col1_x, tech_btn_y_start + 2*(tech_btn_height + spacing), tech_btn_width, tech_btn_height, "Launder Cash", functools.partial(action_initiate_tech_operation, "launder_cash"), font=FONT_SMALL))
        tech_contact_view_buttons.append(Button(tech_col2_x, tech_btn_y_start, tech_btn_width, tech_btn_height, "Stake DrugCoin", functools.partial(action_initiate_tech_operation, "stake_dc"), font=FONT_SMALL))
        tech_contact_view_buttons.append(Button(tech_col2_x, tech_btn_y_start + tech_btn_height + spacing, tech_btn_width, tech_btn_height, "Unstake DrugCoin", functools.partial(action_initiate_tech_operation, "unstake_dc"), font=FONT_SMALL))
        ghost_network_skill_id = "GHOST_NETWORK_ACCESS"
        has_ghost_network = ghost_network_skill_id in player_inv.unlocked_skills
        buy_ghost_text = "Ghost Network Acquired" if has_ghost_network else "Buy Ghost Network"
        tech_contact_view_buttons.append(Button(tech_col2_x, tech_btn_y_start + 2*(tech_btn_height + spacing), tech_btn_width, tech_btn_height, buy_ghost_text, functools.partial(action_initiate_tech_operation, "buy_ghost_network"), font=FONT_SMALL, is_enabled=not has_ghost_network))
        can_collect_rewards = player_inv.staked_drug_coin.get('pending_rewards', 0.0) > 0.00001
        collect_btn_y = tech_btn_y_start + 3*(tech_btn_height + spacing) 
        tech_contact_view_buttons.append(Button(tech_col1_x, collect_btn_y, tech_btn_width, tech_btn_height, "Collect DC Rewards", functools.partial(action_initiate_tech_operation, "collect_dc_rewards"), is_enabled=can_collect_rewards, font=FONT_SMALL))
        tech_contact_view_buttons.append(Button(SCREEN_WIDTH - button_width - 20, SCREEN_HEIGHT - button_height - 20, button_width, button_height, "Back", action_open_main_menu, font=FONT_SMALL))
    elif current_view == "tech_input_coin_select":
        cy = 150
        for i, coin in enumerate(CryptoCoin):
            if tech_transaction_in_progress in ["stake_dc", "unstake_dc"] and coin != CryptoCoin.DRUG_COIN: continue
            tech_contact_view_buttons.append(Button(start_x, cy + i * (button_height + spacing), button_width, button_height, coin.value, functools.partial(action_tech_select_coin, coin), font=FONT_SMALL))
        tech_contact_view_buttons.append(Button(SCREEN_WIDTH // 2 - button_width //2, SCREEN_HEIGHT - button_height*2 - spacing, button_width, button_height, "Cancel", action_cancel_transaction, font=FONT_SMALL))
    elif current_view == "tech_input_amount":
        confirm_y = tech_input_box_rect.bottom + 80
        tech_contact_view_buttons.append(Button(SCREEN_WIDTH // 2 - button_width - spacing // 2, confirm_y, button_width, button_height, "Confirm", functools.partial(action_confirm_tech_operation, player_inv, game_state, game_configs), font=FONT_SMALL))
        tech_contact_view_buttons.append(Button(SCREEN_WIDTH // 2 + spacing // 2, confirm_y, button_width, button_height, "Cancel", action_cancel_transaction, font=FONT_SMALL))
    elif current_view == "skills":
        skills_view_buttons.append(Button(SCREEN_WIDTH - button_width - 20, SCREEN_HEIGHT - button_height - 20, button_width, button_height, "Back", action_open_main_menu, font=FONT_SMALL))
        if hasattr(game_configs, 'SKILL_DEFINITIONS') and game_configs.SKILL_DEFINITIONS:
            skill_y_offset = 120; item_spacing = 80 
            for skill_id, skill_def in game_configs.SKILL_DEFINITIONS.items():
                is_unlocked = skill_id in player_inv.unlocked_skills; can_unlock = player_inv.skill_points >= skill_def['cost'] and not is_unlocked
                btn_x = UPGRADE_ITEM_X_START + UPGRADE_ITEM_WIDTH - UPGRADE_BUTTON_WIDTH - 10 
                skills_view_buttons.append(Button(btn_x, skill_y_offset + 10, UPGRADE_BUTTON_WIDTH, UPGRADE_BUTTON_HEIGHT, "Unlock", functools.partial(action_unlock_skill, skill_id, player_inv, game_configs), is_enabled=can_unlock, font=FONT_SMALL))
                skill_y_offset += item_spacing 
    elif current_view == "upgrades":
        upgrades_view_buttons.append(Button(SCREEN_WIDTH - button_width - 20, SCREEN_HEIGHT - button_height - 20, button_width, button_height, "Back", action_open_main_menu, font=FONT_SMALL))
        if hasattr(game_configs, 'UPGRADE_DEFINITIONS') and game_configs.UPGRADE_DEFINITIONS:
            upgrade_y_offset = 120; item_spacing = 80 
            cap_def = game_configs.UPGRADE_DEFINITIONS.get("EXPANDED_CAPACITY")
            if cap_def:
                num_purchased = player_inv.capacity_upgrades_purchased; max_levels = len(cap_def['costs'])
                can_upgrade_cap = num_purchased < max_levels
                cap_button_text = "Maxed Out"; is_cap_enabled = False
                if can_upgrade_cap:
                    next_cost = cap_def['costs'][num_purchased]; next_cap_lvl = cap_def['capacity_levels'][num_purchased]
                    cap_button_text = f"To {next_cap_lvl} (${next_cost:,.0f})"
                    is_cap_enabled = player_inv.cash >= next_cost
                btn_x = UPGRADE_ITEM_X_START + UPGRADE_ITEM_WIDTH - UPGRADE_BUTTON_WIDTH - 10
                upgrades_view_buttons.append(Button(btn_x, upgrade_y_offset + 15, UPGRADE_BUTTON_WIDTH, UPGRADE_BUTTON_HEIGHT, cap_button_text, functools.partial(action_purchase_capacity_upgrade, player_inv, game_configs), is_enabled=is_cap_enabled, font=FONT_XSMALL))
                upgrade_y_offset += item_spacing
            phone_def = game_configs.UPGRADE_DEFINITIONS.get("SECURE_PHONE")
            if phone_def:
                can_buy_phone = not player_inv.has_secure_phone and player_inv.cash >= phone_def['cost']
                btn_x = UPGRADE_ITEM_X_START + UPGRADE_ITEM_WIDTH - UPGRADE_BUTTON_WIDTH - 10
                upgrades_view_buttons.append(Button(btn_x, upgrade_y_offset + 15, UPGRADE_BUTTON_WIDTH, UPGRADE_BUTTON_HEIGHT, "Purchase Phone", functools.partial(action_purchase_secure_phone, player_inv, game_configs), is_enabled=can_buy_phone, font=FONT_XSMALL))

# --- Main Game Loop ---
# ... (game_loop as before, ensure it handles "game_over" view and "informant" view)
def game_loop(player_inventory: PlayerInventory, initial_current_region: Region, game_state_ext: any, game_configs_ext: any):
    global current_view, game_state_data_cache, game_configs_data_cache, player_inventory_cache
    global quantity_input_string, tech_input_string, active_prompt_message, prompt_message_timer
    global drug_for_transaction, quality_for_transaction, price_for_transaction, available_for_transaction, current_transaction_type, input_box_rect
    global tech_transaction_in_progress, coin_for_tech_transaction, tech_input_box_rect, active_blocking_event_data, game_over_message, game_over_buttons

    game_state_data_cache = game_state_ext
    game_configs_data_cache = game_configs_ext
    player_inventory_cache = player_inventory 

    if not hasattr(game_state_data_cache, 'current_player_region'): 
        game_state_data_cache.current_player_region = initial_current_region
    
    setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, game_state_data_cache.current_player_region)
    running = True
    
    while running:
        current_player_region_for_frame = game_state_data_cache.current_player_region
        previous_view = current_view
        mouse_pos = pygame.mouse.get_pos() 

        if game_over_message is not None and current_view != "game_over":
            previous_view = current_view 
            current_view = "game_over"
            setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if current_view == "game_over":
                for btn in game_over_buttons:
                    if btn.handle_event(event): break 
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN : 
                    if game_over_buttons and game_over_buttons[0].action: game_over_buttons[0].action()
                continue 

            if current_view == "blocking_event_popup": 
                for button in blocking_event_popup_buttons:
                    if button.handle_event(event):
                        if previous_view != current_view: 
                             setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)
                        break 
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: 
                    if blocking_event_popup_buttons and blocking_event_popup_buttons[0].action:
                        blocking_event_popup_buttons[0].action()
                        if previous_view != current_view:
                             setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)
                continue 

            is_market_input_active = current_view == "market_buy_input" or current_view == "market_sell_input"
            is_tech_input_active = current_view == "tech_input_amount"

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
                    elif event.unicode.isdigit() or (event.unicode == '.' and '.' not in tech_input_string): tech_input_string += event.unicode
            
            active_buttons_list = []
            if current_view == "main_menu": active_buttons_list = main_menu_buttons
            elif current_view == "market": active_buttons_list = market_view_buttons + market_buy_sell_buttons
            elif current_view == "inventory": active_buttons_list = inventory_view_buttons
            elif current_view == "travel": active_buttons_list = travel_view_buttons
            elif current_view == "informant": active_buttons_list = informant_view_buttons # New
            elif current_view in ["tech_contact", "tech_input_coin_select", "tech_input_amount"]: active_buttons_list = tech_contact_view_buttons
            elif current_view == "skills": active_buttons_list = skills_view_buttons
            elif current_view == "upgrades": active_buttons_list = upgrades_view_buttons
            elif current_view in ["market_buy_input", "market_sell_input"]: active_buttons_list = transaction_input_buttons

            button_clicked_and_view_changed = False
            for button in active_buttons_list:
                if button.handle_event(event): 
                    if previous_view != current_view: 
                        button_clicked_and_view_changed = True
                        setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame) 
                    break 
            
            if not button_clicked_and_view_changed and previous_view != current_view :
                 setup_buttons(game_state_data_cache, player_inventory_cache, game_configs_data_cache, current_player_region_for_frame)

        update_hud_timers_external() 
        if prompt_message_timer > 0:
            prompt_message_timer -= 1
            if prompt_message_timer <= 0: active_prompt_message = None

        screen.fill(RICH_BLACK) 

        if current_view == "game_over": draw_game_over_view_external(screen, game_over_message, game_over_buttons)
        elif current_view == "main_menu": draw_main_menu_external(screen, main_menu_buttons)
        elif current_view == "market": draw_market_view_external(screen, current_player_region_for_frame, player_inventory_cache, market_view_buttons, market_buy_sell_buttons)
        elif current_view == "inventory": draw_inventory_view_external(screen, player_inventory_cache, inventory_view_buttons) 
        elif current_view == "travel": draw_travel_view_external(screen, current_player_region_for_frame, travel_view_buttons) 
        elif current_view == "informant": draw_informant_view_external(screen, player_inventory_cache, informant_view_buttons, game_configs_data_cache) # New
        elif current_view in ["tech_contact", "tech_input_coin_select", "tech_input_amount"]: 
            tech_ui_state = { 'current_view': current_view, 'tech_transaction_in_progress': tech_transaction_in_progress, 'coin_for_tech_transaction': coin_for_tech_transaction, 'tech_input_string': tech_input_string, 'active_prompt_message': active_prompt_message, 'prompt_message_timer': prompt_message_timer, 'tech_input_box_rect': tech_input_box_rect }
            draw_tech_contact_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, tech_contact_view_buttons, tech_ui_state ) 
        elif current_view == "skills": draw_skills_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, skills_view_buttons) 
        elif current_view == "upgrades": draw_upgrades_view_external(screen, player_inventory_cache, game_state_data_cache, game_configs_data_cache, upgrades_view_buttons) 
        elif current_view in ["market_buy_input", "market_sell_input"]: 
            transaction_ui_state = { 'quantity_input_string': quantity_input_string, 'drug_for_transaction': drug_for_transaction, 'quality_for_transaction': quality_for_transaction, 'price_for_transaction': price_for_transaction, 'available_for_transaction': available_for_transaction, 'current_transaction_type': current_transaction_type, 'active_prompt_message': active_prompt_message, 'prompt_message_timer': prompt_message_timer,  'input_box_rect': input_box_rect  }
            draw_transaction_input_view_external(screen, transaction_input_buttons, transaction_ui_state)
        
        if current_view != "game_over" and current_view == "blocking_event_popup" and active_blocking_event_data: 
            draw_blocking_event_popup_external(screen, active_blocking_event_data, blocking_event_popup_buttons)
        
        if current_view != "game_over": 
            draw_hud_external(screen, player_inventory_cache, current_player_region_for_frame, game_state_data_cache) 
        
        if active_prompt_message and prompt_message_timer > 0 and current_view != "game_over" and current_view != "blocking_event_popup": 
            is_prompt_handled_by_view = ( (current_view in ["market_buy_input", "market_sell_input", "tech_input_amount"]) or (current_view == "tech_contact" and tech_ui_state.get('active_prompt_message') and "Select cryptocurrency" not in tech_ui_state.get('active_prompt_message') and "Enter amount" not in tech_ui_state.get('active_prompt_message') ) )
            if not is_prompt_handled_by_view:
                prompt_y = SCREEN_HEIGHT - 100; 
                if current_view == "tech_contact": prompt_y = SCREEN_HEIGHT - 120 
                prompt_color = IMPERIAL_RED if "Error" in active_prompt_message or "Invalid" in active_prompt_message or "Not enough" in active_prompt_message else (GOLDEN_YELLOW if "Skill" in active_prompt_message else EMERALD_GREEN)
                draw_text(screen, active_prompt_message, SCREEN_WIDTH // 2, prompt_y, font=FONT_MEDIUM, color=prompt_color, center_aligned=True, max_width=SCREEN_WIDTH - 40)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()
