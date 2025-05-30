import random
import math
from typing import List, Dict, Tuple, Optional 

from core.region import Region
from core.player_inventory import PlayerInventory
from core.ai_rival import AIRival
from core.enums import DrugQuality
from core.market_event import MarketEvent 

from ui.ui_helpers import parse_drug_quality, print_market_header
from mechanics.market_impact import (apply_player_buy_impact, apply_player_sell_impact,
                                     decay_player_market_impact, process_rival_turn, 
                                     decay_rival_market_impact, decay_regional_heat)
import game_state 
from game_configs import ( # Import all necessary configs
    CAPACITY_UPGRADE_COST_INITIAL, CAPACITY_UPGRADE_COST_MULTIPLIER, CAPACITY_UPGRADE_AMOUNT, 
    SKILL_POINTS_PER_X_DAYS, SKILL_MARKET_INTUITION_COST, SKILL_DIGITAL_FOOTPRINT_COST, # Added OpSec Skill
    INFORMANT_TIP_COST, INFORMANT_TRUST_GAIN_PER_TIP, INFORMANT_MAX_TRUST,
    CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE, TECH_CONTACT_FEE_PERCENT, 
    HEAT_FROM_SELLING_DRUG_TIER, HEAT_FROM_CRYPTO_TRANSACTION,
    POLICE_STOP_HEAT_THRESHOLD, POLICE_STOP_BASE_CHANCE, POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD,
    BRIBE_BASE_COST_PERCENT_OF_CASH, BRIBE_MIN_COST,
    BRIBE_SUCCESS_CHANCE_BASE, BRIBE_SUCCESS_CHANCE_HEAT_PENALTY,
    CONFISCATION_CHANCE_ON_SEARCH, CONFISCATION_PERCENTAGE_MIN, CONFISCATION_PERCENTAGE_MAX, 
    JAIL_TIME_DAYS_BASE, JAIL_TIME_HEAT_MULTIPLIER, JAIL_CHANCE_HEAT_THRESHOLD, 
    JAIL_CHANCE_IF_HIGH_TIER_DRUGS_FOUND,
    GHOST_NETWORK_ACCESS_COST_DC, DIGITAL_ARSENAL_COST_DC, 
    DC_STAKING_DAILY_RETURN_PERCENT, 
    CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT, CORRUPT_OFFICIAL_BASE_BRIBE_COST, 
    CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT,
    LAUNDERING_FEE_PERCENT, LAUNDERING_DELAY_DAYS, MAX_ACTIVE_LAUNDERING_OPERATIONS, 
    SETUP_EVENT_STING_CHANCE_BASE, SETUP_EVENT_STING_CHANCE_HEAT_MODIFIER,
    DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT, SECURE_PHONE_COST, # New OpSec
    SECURE_PHONE_HEAT_REDUCTION_PERCENT, SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT # New OpSec
)


# ... (handle_police_stop_event, check_and_trigger_police_stop, handle_view_inventory, handle_buy_drug, handle_sell_drug as before - no direct changes needed in their existing logic for these new features, but handle_sell_drug already has heat generation)
# Minor correction in handle_police_stop_event for passing crypto map to recursive handle_advance_day
def handle_police_stop_event(region: Region, player_inventory: PlayerInventory, all_regions: Dict[str, Region], current_day: int, ai_rivals: List[AIRival], crypto_volatility_map: Dict[str, float], crypto_min_prices_map: Dict[str, float]) -> Optional[int]: # ... (as before)
    separator = "="*40; print("\n" + separator); print("!!! POLICE STOP !!!".center(len(separator))); print("Red and blue lights flash! You're pulled over.".center(len(separator))); print(f"(Current heat in {region.name}: {region.current_heat})".center(len(separator))); print(separator)
    new_current_day_after_jail = None
    while True:
        print("\nYour options:"); print("  1. Attempt to Bribe Officer"); print("  2. Comply (Allow Search)"); choice = input("What do you do? (1-2): ").strip()
        if choice == "1":
            bribe_cost = round(max(BRIBE_MIN_COST, player_inventory.cash * BRIBE_BASE_COST_PERCENT_OF_CASH), 2)
            if player_inventory.cash < bribe_cost: print(f"\nYou barely have ${player_inventory.cash:.2f}. Not enough for a bribe of ${bribe_cost:.2f}. You're forced to comply."); choice = "2"
            else:
                bribe_confirm = input(f"Offer a bribe of ${bribe_cost:.2f}? This is risky... (yes/no): ").strip().lower()
                if bribe_confirm == "yes":
                    player_inventory.cash -= bribe_cost; print(f"\nYou slip the officer ${bribe_cost:.2f}...")
                    heat_points_above_threshold = max(0, region.current_heat - POLICE_STOP_HEAT_THRESHOLD); penalty = heat_points_above_threshold * BRIBE_SUCCESS_CHANCE_HEAT_PENALTY
                    bribe_success_actual_chance = max(0.1, min(0.9, BRIBE_SUCCESS_CHANCE_BASE - penalty))
                    if random.random() < bribe_success_actual_chance: print("The officer smirks, pockets the cash, and waves you on. 'Just a routine check. Drive safe.'"); print(separator + "\n"); return None
                    else: print("'Trying to bribe an officer of the law, huh?' The officer scoffs. 'That just made things worse! Out of the vehicle!'"); choice = "2" 
                else: print("You decide against the bribe. 'Alright officer, what seems to be the problem?'"); choice = "2"
        if choice == "2":
            print("\nThe officer searches your vehicle and belongings thoroughly...")
            drugs_found_during_search = False
            if not player_inventory.items or random.random() > CONFISCATION_CHANCE_ON_SEARCH : print("Surprisingly, they don't find anything illicit. 'Alright, you're free to go. Stay out of trouble.'"); print(separator + "\n"); return None
            else:
                print("'Aha! What do we have here? Looks like your lucky day just ran out.'"); drugs_found_during_search = True
                # ... (confiscation logic as before) ...
                drug_to_confiscate_name = random.choice(list(player_inventory.items.keys())); qualities_of_drug = player_inventory.items[drug_to_confiscate_name]; quality_to_confiscate = random.choice(list(qualities_of_drug.keys()))
                current_quantity = qualities_of_drug[quality_to_confiscate]; confiscation_percentage = random.uniform(CONFISCATION_PERCENTAGE_MIN, CONFISCATION_PERCENTAGE_MAX)
                quantity_to_confiscate = math.ceil(current_quantity * confiscation_percentage); quantity_to_confiscate = max(1, quantity_to_confiscate) if current_quantity > 0 else 0; quantity_to_confiscate = min(current_quantity, quantity_to_confiscate)
                if quantity_to_confiscate > 0:
                    player_inventory.remove_drug(drug_to_confiscate_name, quality_to_confiscate, quantity_to_confiscate)
                    print(f"CONFISCATED: {quantity_to_confiscate} units of {quality_to_confiscate.name} {drug_to_confiscate_name}.")
                    heat_increase_on_bust = random.randint(5, 15); region.modify_heat(heat_increase_on_bust); print(f"This incident has drawn more attention in {region.name}. (Heat +{heat_increase_on_bust})")
                else: print("They rummage through your things but don't confiscate anything specific this time. 'Watch yourself.'")

                if drugs_found_during_search:
                    current_chance_of_jail = 0.0 # ... (jail chance logic as before) ...
                    if region.current_heat >= JAIL_CHANCE_HEAT_THRESHOLD: current_chance_of_jail += 0.2
                    has_high_tier_drugs = False
                    for drug_name_inv, qualities_inv in player_inventory.items.items():
                        drug_tier = 0; # ... (get tier logic)
                        if drug_name_inv in region.drug_market_data : drug_tier = region.drug_market_data.get(drug_name_inv, {}).get("tier", 0)
                        else: 
                            for r_obj in all_regions.values():
                                if drug_name_inv in r_obj.drug_market_data: drug_tier = r_obj.drug_market_data.get(drug_name_inv, {}).get("tier",0); break
                        if drug_tier >= 3 and any(qualities_inv.values()): has_high_tier_drugs = True; break
                    if has_high_tier_drugs: current_chance_of_jail += JAIL_CHANCE_IF_HIGH_TIER_DRUGS_FOUND
                    current_chance_of_jail = min(current_chance_of_jail, 0.75)

                    if random.random() < current_chance_of_jail:
                        days_in_jail = JAIL_TIME_DAYS_BASE + int((region.current_heat - JAIL_CHANCE_HEAT_THRESHOLD) * JAIL_TIME_HEAT_MULTIPLIER); days_in_jail = max(JAIL_TIME_DAYS_BASE, days_in_jail)
                        print(f"\nThis is serious! You're arrested and sentenced to {days_in_jail} days in jail!"); print("You lose time while locked up...")
                        temp_current_day = current_day
                        for i in range(days_in_jail):
                            print(f"...Day {temp_current_day + 1} passes in a blur...")
                            # Pass all required args, including crypto maps
                            temp_current_day = handle_advance_day(all_regions, temp_current_day, region, ai_rivals, player_inventory, crypto_volatility_map, crypto_min_prices_map, is_jailed_turn=True)
                        new_current_day_after_jail = temp_current_day 
                        print(f"You're finally released. It's Day {new_current_day_after_jail}."); print(separator + "\n"); return new_current_day_after_jail
                print("You got off with a warning and a hefty 'fine' (confiscation), but they'll be watching you."); print(separator + "\n"); return None
        else: print("Invalid choice. The officer is waiting...")
    return None
def check_and_trigger_police_stop(current_region: Region, player_inventory: PlayerInventory, all_regions: Dict[str, Region], current_day: int, ai_rivals: List[AIRival], crypto_volatility_map: Dict[str, float], crypto_min_prices_map: Dict[str, float]) -> Optional[int]: # ... (as before)
    if current_region.current_heat < POLICE_STOP_HEAT_THRESHOLD: return None
    heat_above_threshold = current_region.current_heat - POLICE_STOP_HEAT_THRESHOLD
    chance_of_stop = POLICE_STOP_BASE_CHANCE + (heat_above_threshold * POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD)
    chance_of_stop = max(0.05, min(chance_of_stop, 0.75)) 
    if random.random() < chance_of_stop:
        return handle_police_stop_event(current_region, player_inventory, all_regions, current_day, ai_rivals, crypto_volatility_map, crypto_min_prices_map)
    return None
def handle_view_inventory(player_inventory: PlayerInventory, content_pad, log_win, input_win):
    import curses
    content_pad.clear()
    max_y, max_x = content_pad.getmaxyx()
    pad_line = 0
    content_pad.addstr(pad_line, 0, "--- Player Inventory ---", curses.color_pair(2) | curses.A_BOLD)
    pad_line += 1
    summary_lines = player_inventory.formatted_summary().split("\n")
    for line in summary_lines:
        content_pad.addstr(pad_line, 0, line, curses.color_pair(1))
        pad_line += 1
    # Scrolling logic
    scroll_y = 0
    visible_height = 20  # Or dynamically calculate based on window size
    max_scroll = max(0, pad_line - visible_height)
    while True:
        content_pad.noutrefresh(scroll_y, 0, 6, 0, 6 + visible_height - 1, max_x - 1)
        log_win.noutrefresh()
        input_win.clear()
        input_win.addstr(0, 0, "Up/Down: Scroll  Q: Quit", curses.color_pair(6))
        input_win.refresh()
        curses.doupdate()
        key = input_win.getkey()
        if key.lower() == 'q' or key == '\n':
            break
        elif key in ['KEY_DOWN', 'j'] and scroll_y < max_scroll:
            scroll_y += 1
        elif key in ['KEY_UP', 'k'] and scroll_y > 0:
            scroll_y -= 1

def handle_buy_drug(region: Region, player_inventory: PlayerInventory, content_pad, log_win, input_win):
    import curses
    content_pad.clear()
    content_pad.addstr(0, 0, "--- Buy Drug ---", curses.color_pair(2) | curses.A_BOLD)
    content_pad.addstr(1, 0, "Enter drug to buy (name quality quantity, e.g., Coke PURE 10):", curses.color_pair(1))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "> ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    user_input_str = input_win.getstr(0, 2, 40).decode().strip()
    curses.noecho()
    user_input = user_input_str.split()
    if len(user_input) < 3:
        log_win.clear()
        log_win.addstr(0, 0, "Invalid format. Please use: DrugName Quality Quantity", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    drug_name_input = user_input[0]
    quality_input_str = user_input[1]
    quantity_input_str = user_input[2]
    canonical_drug_name = None
    for dn_market in region.drug_market_data.keys():
        if dn_market.lower() == drug_name_input.lower():
            canonical_drug_name = dn_market
            break
    if not canonical_drug_name:
        log_win.clear()
        log_win.addstr(0, 0, f"Drug '{drug_name_input}' not found in this market ({region.name}).", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    drug_name = canonical_drug_name
    quality = parse_drug_quality(quality_input_str)
    if quality is None:
        log_win.clear()
        log_win.addstr(0, 0, f"Invalid quality '{quality_input_str}'. Valid: PURE, STANDARD, CUT", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    try:
        quantity = int(quantity_input_str)
        if quantity <= 0:
            log_win.clear()
            log_win.addstr(0, 0, "Quantity must be positive.", curses.color_pair(4))
            log_win.noutrefresh()
            curses.doupdate()
            return
    except ValueError:
        log_win.clear()
        log_win.addstr(0, 0, "Invalid quantity. Must be a number.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    stock = region.get_available_stock(drug_name, quality)
    if stock < quantity:
        log_win.clear()
        log_win.addstr(0, 0, f"Insufficient stock. Only {stock} of {quality.name} {drug_name} available.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    buy_price = region.get_buy_price(drug_name, quality)
    if buy_price <= 0:
        log_win.clear()
        log_win.addstr(0, 0, f"{quality.name} {drug_name} is unavailable or cannot be bought at this price.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    if player_inventory.get_available_space() < quantity:
        log_win.clear()
        log_win.addstr(0, 0, f"Not enough inventory space. Available: {player_inventory.get_available_space()}", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    total_cost = buy_price * quantity
    if player_inventory.cash < total_cost:
        log_win.clear()
        log_win.addstr(0, 0, f"Not enough cash. Need: ${total_cost:.2f}, Have: ${player_inventory.cash:.2f}", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    if player_inventory.add_drug(drug_name, quality, quantity):
        region.update_stock_on_buy(drug_name, quality, quantity)
        player_inventory.cash -= total_cost
        log_win.clear()
        log_win.addstr(0, 0, f"Bought {quantity} units of {quality.name} {drug_name} for ${total_cost:.2f}", curses.color_pair(3))
        log_win.noutrefresh()
        curses.doupdate()
        apply_player_buy_impact(region, drug_name, quantity)
    else:
        log_win.clear()
        log_win.addstr(0, 0, f"Purchase of {quality.name} {drug_name} failed.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()

def handle_sell_drug(region: Region, player_inventory: PlayerInventory, content_pad, log_win, input_win):
    import curses
    content_pad.clear()
    content_pad.addstr(0, 0, "--- Sell Drug ---", curses.color_pair(2) | curses.A_BOLD)
    content_pad.addstr(1, 0, "Enter drug to sell (name quality quantity, e.g., Coke PURE 5):", curses.color_pair(1))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "> ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    user_input_str = input_win.getstr(0, 2, 40).decode().strip()
    curses.noecho()
    user_input = user_input_str.split()
    if len(user_input) < 3:
        log_win.clear()
        log_win.addstr(0, 0, "Invalid format. Please use: DrugName Quality Quantity", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    drug_name_input = user_input[0]
    quality_input_str = user_input[1]
    quantity_input_str = user_input[2]
    player_drug_name_match = None
    for inv_drug_name in player_inventory.items.keys():
        if inv_drug_name.lower() == drug_name_input.lower():
            player_drug_name_match = inv_drug_name
            break
    if not player_drug_name_match:
        log_win.clear()
        log_win.addstr(0, 0, f"You don't have any '{drug_name_input}' in your inventory.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    drug_name = player_drug_name_match
    quality = parse_drug_quality(quality_input_str)
    if quality is None:
        log_win.clear()
        log_win.addstr(0, 0, f"Invalid quality '{quality_input_str}'. Valid: PURE, STANDARD, CUT", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    try:
        quantity = int(quantity_input_str)
        if quantity <= 0:
            log_win.clear()
            log_win.addstr(0, 0, "Quantity must be positive.", curses.color_pair(4))
            log_win.noutrefresh()
            curses.doupdate()
            return
    except ValueError:
        log_win.clear()
        log_win.addstr(0, 0, "Invalid quantity. Must be a number.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    player_quantity = player_inventory.get_quantity(drug_name, quality)
    if player_quantity < quantity:
        log_win.clear()
        log_win.addstr(0, 0, f"Not enough {quality.name} {drug_name} in inventory. You have: {player_quantity}", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    market_drug_name_for_price = None
    drug_tier = 1
    if drug_name in region.drug_market_data:
        market_drug_name_for_price = drug_name
        drug_tier = region.drug_market_data[drug_name].get("tier", 1)
    else:
        for m_name, m_data in region.drug_market_data.items():
            if m_name.lower() == drug_name.lower():
                market_drug_name_for_price = m_name
                drug_tier = m_data.get("tier", 1)
                break
    if not market_drug_name_for_price:
        log_win.clear()
        log_win.addstr(0, 0, f"Market in {region.name} does not seem to trade {drug_name}.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    sell_price = region.get_sell_price(market_drug_name_for_price, quality)
    if sell_price <= 0:
        log_win.clear()
        log_win.addstr(0, 0, f"Market in {region.name} is not currently buying {quality.name} {drug_name} or offering $0.00 for it.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    if player_inventory.remove_drug(drug_name, quality, quantity):
        total_revenue = sell_price * quantity
        player_inventory.cash += total_revenue
        log_win.clear()
        log_win.addstr(0, 0, f"Sold {quantity} units of {quality.name} {drug_name} for ${total_revenue:.2f}", curses.color_pair(3))
        log_win.noutrefresh()
        curses.doupdate()
        apply_player_sell_impact(region, market_drug_name_for_price, quantity)
        heat_generated = quantity * HEAT_FROM_SELLING_DRUG_TIER.get(drug_tier, 1)
        if heat_generated > 0:
            region.modify_heat(heat_generated)
            if heat_generated > 5:
                log_win.addstr(1, 0, f"Your transaction in {region.name} attracted some attention... (Heat +{heat_generated})", curses.color_pair(4))
                log_win.noutrefresh()
                curses.doupdate()
    else:
        log_win.clear()
        log_win.addstr(0, 0, f"Sale of {quality.name} {drug_name} failed.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()

def handle_advance_day(all_game_regions: Dict[str, Region], current_day: int, current_player_region: Region, player_inventory: PlayerInventory, ai_rivals: List[AIRival], content_pad, log_win, input_win):
    import curses
    # Advance day logic (events, rival turns, laundering, etc.)
    # This is a simplified version; full logic should match your previous implementation
    content_pad.clear()
    content_pad.addstr(0, 0, f"--- Advancing to Day {current_day+1} ---", curses.color_pair(2) | curses.A_BOLD)
    pad_line = 1
    # Example: process laundering
    if getattr(player_inventory, 'pending_laundered_sc_arrival_day', None) is not None and player_inventory.pending_laundered_sc_arrival_day == current_day+1:
        player_inventory.crypto_wallet['SC'] = player_inventory.crypto_wallet.get('SC', 0.0) + player_inventory.pending_laundered_sc
        content_pad.addstr(pad_line, 0, f"Laundered {player_inventory.pending_laundered_sc:.4f} SC has arrived!", curses.color_pair(3))
        pad_line += 1
        player_inventory.pending_laundered_sc = 0.0
        player_inventory.pending_laundered_sc_arrival_day = None
    # TODO: Add event triggers, rival turns, etc. as in your full logic
    # Debt payment 3 logic (example, should be called from main loop as well):
    # if current_day+1 == DEBT_PAYMENT_3_DUE_DAY and not debt_payment_3_paid:
    #     if player_inventory.cash >= DEBT_PAYMENT_3_AMOUNT:
    #         player_inventory.cash -= DEBT_PAYMENT_3_AMOUNT
    #         debt_payment_3_paid = True
    #         log_win.clear()
    #         log_win.addstr(0, 0, "Final Debt Collector payment made! You are free!", curses.color_pair(3))
    #         log_win.addstr(1, 0, f"New carrying capacity: {player_inventory.max_capacity}", curses.color_pair(3))
    #     else:
    #         log_win.clear()
    #         log_win.addstr(0, 0, "GAME OVER: You failed to pay the Debt Collector!", curses.color_pair(4))
    #         log_win.noutrefresh()
    #         curses.doupdate()
    #         raise SystemExit
    content_pad.addstr(pad_line, 0, "Day advanced. Press any key to continue...", curses.color_pair(1))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    log_win.noutrefresh()
    input_win.clear()
    input_win.refresh()
    input_win.getkey()
def handle_travel(all_regions: Dict[str, Region], current_region: Region, current_day: int, player_inventory: PlayerInventory, ai_rivals: List[AIRival], crypto_volatility_map: Dict[str,float], crypto_min_prices_map: Dict[str,float]) -> Tuple[Region, int]: # ... (as before)
    stop_result_day = check_and_trigger_police_stop(current_region, player_inventory, all_regions, current_day, ai_rivals, crypto_volatility_map, crypto_min_prices_map)
    if stop_result_day is not None: print("Your attempt to travel was interrupted by police!"); return current_region, stop_result_day 
    print("\n--- Travel ---"); print(f"You are currently in: {current_region.name} (Heat: {current_region.current_heat})")
    available_destinations = []; print("Available destinations:"); idx = 1
    for region_name, region_obj in sorted(all_regions.items()):
        if region_name != current_region.name: print(f"{idx}. {region_name} (Heat: {region_obj.current_heat})"); available_destinations.append(region_name); idx += 1
    if not available_destinations: print("There are no other regions to travel to."); return current_region, current_day
    try:
        choice_input = input(f"Enter destination number (0 to cancel): ")
        if not choice_input.isdigit(): print("Invalid input. Please enter a number."); return current_region, current_day
        choice = int(choice_input)
        if choice == 0: print("Travel cancelled."); return current_region, current_day
        if 1 <= choice <= len(available_destinations):
            chosen_destination_name = available_destinations[choice-1]; print(f"\nTraveling to {chosen_destination_name}...")
            new_day_after_travel = handle_advance_day(all_regions, current_day, current_region, ai_rivals, player_inventory, crypto_volatility_map, crypto_min_prices_map, is_jailed_turn=False)
            new_current_region = all_regions[chosen_destination_name]
            print(f"You have arrived in {new_current_region.name}.")
            return new_current_region, new_day_after_travel
        else: print("Invalid destination number."); return current_region, current_day
    except ValueError: print("Invalid input. Please enter a number."); return current_region, current_day
    except Exception as e: print(f"An error occurred during travel: {str(e)}"); return current_region, current_day


def handle_talk_to_informant(current_region: Region, all_regions: Dict[str, Region], ai_rivals: List[AIRival], player_inventory: PlayerInventory, content_pad, log_win, input_win):
    import curses
    content_pad.clear()
    pad_line = 0
    content_pad.addstr(pad_line, 0, "--- Talk to Informant ---", curses.color_pair(2) | curses.A_BOLD)
    pad_line += 1
    content_pad.addstr(pad_line, 0, f"Informant Trust: {player_inventory.informant_trust}/{INFORMANT_MAX_TRUST}", curses.color_pair(1))
    pad_line += 1
    content_pad.addstr(pad_line, 0, f"Tip Cost: ${INFORMANT_TIP_COST:.2f}", curses.color_pair(1))
    pad_line += 1
    content_pad.addstr(pad_line, 0, "0. Back to Main Menu", curses.color_pair(5))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "Get a tip? (yes/0): ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    choice = input_win.getstr(0, 19, 10).decode().strip().lower()
    curses.noecho()
    if choice == "0":
        return
    if player_inventory.cash < INFORMANT_TIP_COST:
        log_win.clear()
        log_win.addstr(0, 0, "Not enough cash for a tip.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    player_inventory.cash -= INFORMANT_TIP_COST
    # Simulate tip types
    import random
    tip_types = ["market", "heat", "crypto", "rival", "busted_rival"]
    tip_type = random.choice(tip_types)
    intel_given = False
    if tip_type == "market":
        log_win.clear()
        log_win.addstr(0, 0, "Market is shifting. Watch for price spikes soon.", curses.color_pair(3))
        intel_given = True
    elif tip_type == "heat":
        log_win.clear()
        log_win.addstr(0, 0, f"Heat is rising in {current_region.name}. Stay low.", curses.color_pair(4))
        intel_given = True
    elif tip_type == "crypto":
        log_win.clear()
        log_win.addstr(0, 0, "Crypto prices are volatile. Might be a good time to trade.", curses.color_pair(3))
        intel_given = True
    elif tip_type == "rival":
        log_win.clear()
        log_win.addstr(0, 0, "A rival is making moves nearby. Be cautious.", curses.color_pair(4))
        intel_given = True
    elif tip_type == "busted_rival":
        busted_rivals = [r for r in ai_rivals if r.is_busted]
        if busted_rivals:
            log_win.clear()
            log_win.addstr(0, 0, f"{busted_rivals[0].name} is busted. Their turf is vulnerable!", curses.color_pair(3))
            intel_given = True
    if intel_given:
        player_inventory.informant_trust = min(INFORMANT_MAX_TRUST, player_inventory.informant_trust + INFORMANT_TRUST_GAIN_PER_TIP)
    else:
        log_win.clear()
        log_win.addstr(0, 0, "Nothing much on the wire today...", curses.color_pair(1))
    log_win.noutrefresh()
    curses.doupdate()

def handle_view_upgrades(player_inventory: PlayerInventory, content_pad, log_win, input_win):
    import curses
    content_pad.clear()
    pad_line = 0
    current_upgrade_cost = CAPACITY_UPGRADE_COST_INITIAL * (CAPACITY_UPGRADE_COST_MULTIPLIER ** player_inventory.capacity_upgrades_purchased)
    content_pad.addstr(pad_line, 0, "--- Upgrades ---", curses.color_pair(2) | curses.A_BOLD)
    pad_line += 1
    content_pad.addstr(pad_line, 0, f"1. Increase Carrying Capacity by {CAPACITY_UPGRADE_AMOUNT} units.", curses.color_pair(1))
    pad_line += 1
    content_pad.addstr(pad_line, 0, f"   Current Capacity: {player_inventory.max_capacity}", curses.color_pair(1))
    pad_line += 1
    content_pad.addstr(pad_line, 0, f"   Cost: ${current_upgrade_cost:.2f}", curses.color_pair(1))
    pad_line += 1
    phone_owned_str = "(Purchased)" if player_inventory.has_secure_phone else ""
    content_pad.addstr(pad_line, 0, f"2. Secure Phone (Cost: ${SECURE_PHONE_COST:.2f}) {phone_owned_str}", curses.color_pair(1))
    pad_line += 1
    content_pad.addstr(pad_line, 0, f"   - Reduces heat from crypto transactions by {int(SECURE_PHONE_HEAT_REDUCTION_PERCENT*100)}%. Stacks with Digital Footprint skill.", curses.color_pair(1))
    pad_line += 1
    content_pad.addstr(pad_line, 0, "0. Back to Main Menu", curses.color_pair(5))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "Enter choice: ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    choice = input_win.getstr(0, 14, 10).decode().strip()
    curses.noecho()
    if choice == "1":
        if player_inventory.cash >= current_upgrade_cost:
            player_inventory.cash -= current_upgrade_cost
            player_inventory.upgrade_capacity(CAPACITY_UPGRADE_AMOUNT)
            player_inventory.capacity_upgrades_purchased += 1
            log_win.clear()
            log_win.addstr(0, 0, "Capacity upgraded successfully!", curses.color_pair(3))
            log_win.addstr(1, 0, f"New carrying capacity: {player_inventory.max_capacity}", curses.color_pair(3))
        else:
            log_win.clear()
            log_win.addstr(0, 0, "Not enough cash for this upgrade.", curses.color_pair(4))
    elif choice == "2":
        if player_inventory.has_secure_phone:
            log_win.clear()
            log_win.addstr(0, 0, "You already own a Secure Phone.", curses.color_pair(4))
        elif player_inventory.cash >= SECURE_PHONE_COST:
            player_inventory.cash -= SECURE_PHONE_COST
            player_inventory.has_secure_phone = True
            log_win.clear()
            log_win.addstr(0, 0, "Secure Phone purchased! Your crypto dealings should be more private.", curses.color_pair(3))
        else:
            log_win.clear()
            log_win.addstr(0, 0, "Not enough cash to purchase the Secure Phone.", curses.color_pair(4))
    elif choice == "0":
        return
    else:
        log_win.clear()
        log_win.addstr(0, 0, "Invalid choice.", curses.color_pair(4))
    log_win.noutrefresh()
    curses.doupdate()

def handle_view_skills(player_inventory: PlayerInventory, content_pad, log_win, input_win):
    import curses
    content_pad.clear()
    pad_line = 0
    content_pad.addstr(pad_line, 0, "--- Skills ---", curses.color_pair(2) | curses.A_BOLD)
    pad_line += 1
    content_pad.addstr(pad_line, 0, f"Available Skill Points: {player_inventory.skill_points}", curses.color_pair(1))
    pad_line += 1
    # Market Intuition
    market_intuition_unlocked = "MARKET_INTUITION" in player_inventory.unlocked_skills
    content_pad.addstr(pad_line, 0, f"1. Market Intuition (Cost: {SKILL_MARKET_INTUITION_COST} SP) - See drug price trends in market view.", curses.color_pair(1))
    pad_line += 1
    if market_intuition_unlocked:
        content_pad.addstr(pad_line, 2, "(Already Unlocked)", curses.color_pair(3))
        pad_line += 1
    # Digital Footprint
    digital_footprint_unlocked = "DIGITAL_FOOTPRINT" in player_inventory.unlocked_skills
    content_pad.addstr(pad_line, 0, f"2. Digital Footprint (Cost: {SKILL_DIGITAL_FOOTPRINT_COST} SP) - Reduce heat from crypto deals by {int(DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT*100)}%.", curses.color_pair(1))
    pad_line += 1
    if digital_footprint_unlocked:
        content_pad.addstr(pad_line, 2, "(Already Unlocked)", curses.color_pair(3))
        pad_line += 1
    content_pad.addstr(pad_line, 0, "0. Back to Main Menu", curses.color_pair(5))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "Enter choice: ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    choice = input_win.getstr(0, 14, 10).decode().strip()
    curses.noecho()
    if choice == "1":
        if market_intuition_unlocked:
            log_win.clear()
            log_win.addstr(0, 0, "You have already learned Market Intuition.", curses.color_pair(4))
        elif player_inventory.skill_points >= SKILL_MARKET_INTUITION_COST:
            player_inventory.skill_points -= SKILL_MARKET_INTUITION_COST
            player_inventory.unlocked_skills.append("MARKET_INTUITION")
            log_win.clear()
            log_win.addstr(0, 0, "Skill Unlocked: Market Intuition!", curses.color_pair(3))
        else:
            log_win.clear()
            log_win.addstr(0, 0, "Not enough Skill Points to learn Market Intuition.", curses.color_pair(4))
    elif choice == "2":
        if digital_footprint_unlocked:
            log_win.clear()
            log_win.addstr(0, 0, "You have already learned Digital Footprint.", curses.color_pair(4))
        elif player_inventory.skill_points >= SKILL_DIGITAL_FOOTPRINT_COST:
            player_inventory.skill_points -= SKILL_DIGITAL_FOOTPRINT_COST
            player_inventory.unlocked_skills.append("DIGITAL_FOOTPRINT")
            log_win.clear()
            log_win.addstr(0, 0, "Skill Unlocked: Digital Footprint!", curses.color_pair(3))
        else:
            log_win.clear()
            log_win.addstr(0, 0, "Not enough Skill Points to learn Digital Footprint.", curses.color_pair(4))
    elif choice == "0":
        return
    else:
        log_win.clear()
        log_win.addstr(0, 0, "Invalid choice.", curses.color_pair(4))
    log_win.noutrefresh()
    curses.doupdate()

def handle_visit_tech_contact(player_inventory: PlayerInventory, current_crypto_prices_ref: Dict[str, float], current_region: Region, current_day: int):
    # ... (Crypto heat reduction, Laundering option added) ...
    print("\nYou meet your Tech Contact in a secure, undisclosed location. The air hums with servers.")
    while True:
        # ... (Display balances and prices as before) ...
        print("\n--- Tech Contact Terminal ---"); print(f"Your Cash: ${player_inventory.cash:.2f}"); print("Your Crypto Wallet:")
        if player_inventory.crypto_wallet or player_inventory.staked_dc > 0:
            for coin_symbol in ["DC", "VC", "SC"]: 
                if coin_symbol in player_inventory.crypto_wallet: print(f"  - Wallet {coin_symbol}: {player_inventory.crypto_wallet[coin_symbol]:.4f}")
            if player_inventory.staked_dc > 0: print(f"  - Staked DC: {player_inventory.staked_dc:.4f}")
        else: print("  - Empty")
        print("\nMarket Prices (per unit):")
        for coin, price in sorted(current_crypto_prices_ref.items()): print(f"  - {coin}: ${price:.2f}")
        print(f"\nTransaction Fee: {TECH_CONTACT_FEE_PERCENT*100:.1f}%")
        if player_inventory.pending_laundered_sc_arrival_day is not None: print(f"Laundering in progress: {player_inventory.pending_laundered_sc:.4f} SC arriving on Day {player_inventory.pending_laundered_sc_arrival_day}.")

        print("\nTech Contact Options:")
        menu_options = {"1": "Buy Crypto", "2": "Sell Crypto"}
        next_option_idx = 3
        
        if player_inventory.pending_laundered_sc_arrival_day is None and MAX_ACTIVE_LAUNDERING_OPERATIONS > 0 : # Check for active ops
             menu_options[str(next_option_idx)] = f"Launder Cash (Fee: {LAUNDERING_FEE_PERCENT*100:.0f}%, Delay: {LAUNDERING_DELAY_DAYS} days)"
        else:
             menu_options[str(next_option_idx)] = "Launder Cash (Unavailable or In Progress)"
        next_option_idx +=1

        is_ghost_access_unlocked = "GHOST_NETWORK_ACCESS" in player_inventory.unlocked_skills
        if not is_ghost_access_unlocked: menu_options[str(next_option_idx)] = f"Purchase Ghost Network Access ({GHOST_NETWORK_ACCESS_COST_DC:.2f} DC)"; next_option_idx+=1
        
        menu_options[str(next_option_idx)] = "Stake DC"; next_option_idx+=1
        menu_options[str(next_option_idx)] = "Unstake DC"
        
        for key, value in menu_options.items(): print(f"  {key}. {value}")
        print("  0. Leave"); choice = input("Choose action: ").strip()

        if choice == "1" or choice == "2": # Buy or Sell Crypto
            action_type = "Buy" if choice == "1" else "Sell"
            coin_options = ["DC", "VC", "SC"]
            coin_sym = input(f"Which crypto to {action_type.lower()}? ({'/'.join(coin_options)}): ").strip().upper()
            if coin_sym not in current_crypto_prices_ref: print("Invalid coin symbol."); continue
            price = current_crypto_prices_ref[coin_sym]
            if price <= 0: print(f"{coin_sym} price error."); continue

            if action_type == "Buy":
                # ... (Buy logic as before) ...
                try:
                    amount_str = input(f"How much {coin_sym} to buy? (Price: ${price:.2f}/unit): ");
                    if not amount_str: continue; quantity_to_buy = float(amount_str)
                    if quantity_to_buy <= 1e-4: print("Amount too small."); continue
                    sub_total_cost = quantity_to_buy * price; fee = sub_total_cost * TECH_CONTACT_FEE_PERCENT; total_cash_cost = sub_total_cost + fee
                    if player_inventory.cash < total_cash_cost: print(f"Not enough cash. Need ${total_cash_cost:.2f} (Fee: ${fee:.2f})."); continue
                    player_inventory.cash -= total_cash_cost; current_coin_balance = player_inventory.crypto_wallet.get(coin_sym, 0.0)
                    player_inventory.crypto_wallet[coin_sym] = current_coin_balance + quantity_to_buy
                    print(f"\nBought {quantity_to_buy:.4f} {coin_sym} for ${sub_total_cost:.2f} (Fee: ${fee:.2f}). Total: ${total_cash_cost:.2f}")
                    base_heat = HEAT_FROM_CRYPTO_TRANSACTION; effective_heat = base_heat
                    has_skill = "DIGITAL_FOOTPRINT" in player_inventory.unlocked_skills; has_phone = player_inventory.has_secure_phone
                    if has_skill and has_phone: effective_heat *= (1.0 - SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT)
                    elif has_skill: effective_heat *= (1.0 - DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
                    elif has_phone: effective_heat *= (1.0 - SECURE_PHONE_HEAT_REDUCTION_PERCENT)
                    effective_heat = int(round(effective_heat))
                    if effective_heat > 0: current_region.modify_heat(effective_heat); print(f"Crypto activity heat +{effective_heat} in {current_region.name}")
                except ValueError: print("Invalid amount.")
            else: # Sell
                # ... (Sell logic as before) ...
                if not player_inventory.crypto_wallet or coin_sym not in player_inventory.crypto_wallet: print(f"You don't own any {coin_sym}."); continue
                current_coin_balance = player_inventory.crypto_wallet[coin_sym]
                try:
                    amount_str = input(f"How much {coin_sym} to sell? (Available: {current_coin_balance:.4f}, Price: ${price:.2f}/unit): ")
                    if not amount_str: continue; quantity_to_sell = float(amount_str)
                    if quantity_to_sell <= 1e-4: print("Amount too small."); continue
                    if quantity_to_sell > current_coin_balance + 1e-9: print(f"Not enough {coin_sym}. You have {current_coin_balance:.4f}."); continue
                    sub_total_revenue = quantity_to_sell * price; fee = sub_total_revenue * TECH_CONTACT_FEE_PERCENT; total_cash_gain = sub_total_revenue - fee
                    if total_cash_gain < 0: print(f"Fee (${fee:.2f}) exceeds revenue. Sale cancelled."); continue
                    player_inventory.crypto_wallet[coin_sym] -= quantity_to_sell
                    if player_inventory.crypto_wallet[coin_sym] < 1e-9: del player_inventory.crypto_wallet[coin_sym]
                    player_inventory.cash += total_cash_gain
                    print(f"\nSold {quantity_to_sell:.4f} {coin_sym} for ${sub_total_revenue:.2f} (Fee: ${fee:.2f}). Received: ${total_cash_gain:.2f}")
                    base_heat = HEAT_FROM_CRYPTO_TRANSACTION; effective_heat = base_heat # ... (heat reduction logic as in buy)
                    has_skill = "DIGITAL_FOOTPRINT" in player_inventory.unlocked_skills; has_phone = player_inventory.has_secure_phone
                    if has_skill and has_phone: effective_heat *= (1.0 - SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT)
                    elif has_skill: effective_heat *= (1.0 - DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
                    elif has_phone: effective_heat *= (1.0 - SECURE_PHONE_HEAT_REDUCTION_PERCENT)
                    effective_heat = int(round(effective_heat))
                    if effective_heat > 0: current_region.modify_heat(effective_heat); print(f"Crypto activity heat +{effective_heat} in {current_region.name}")
                except ValueError: print("Invalid amount.")
        elif menu_options.get(choice) and "Launder Cash" in menu_options[choice]:
            if player_inventory.pending_laundered_sc_arrival_day is not None: print("Laundering operation already in progress."); continue
            try:
                amount_str = input(f"How much cash to launder? (Fee: {LAUNDERING_FEE_PERCENT*100:.0f}%, Delay: {LAUNDERING_DELAY_DAYS} days): $")
                if not amount_str: continue; amount_to_launder = float(amount_str)
                if amount_to_launder <= 0: print("Amount must be positive."); continue
                if amount_to_launder > player_inventory.cash: print("Not enough cash to launder."); continue
                fee = amount_to_launder * LAUNDERING_FEE_PERCENT; net_cash_for_conversion = amount_to_launder - fee
                sc_price = current_crypto_prices_ref.get("SC", 1.0);
                if sc_price <= 0: print("StableCoin price error."); continue
                sc_to_receive = net_cash_for_conversion / sc_price
                player_inventory.cash -= amount_to_launder; player_inventory.pending_laundered_sc = sc_to_receive
                player_inventory.pending_laundered_sc_arrival_day = current_day + LAUNDERING_DELAY_DAYS
                print(f"\nInitiated laundering of ${amount_to_launder:.2f}. You will receive approx. {sc_to_receive:.4f} SC on Day {player_inventory.pending_laundered_sc_arrival_day} (after ${fee:.2f} fee).")
                base_heat = HEAT_FROM_CRYPTO_TRANSACTION * 2 # Laundering is sketchier
                # ... (apply heat reduction for laundering, similar to buy/sell)
                effective_heat = base_heat; has_skill = "DIGITAL_FOOTPRINT" in player_inventory.unlocked_skills; has_phone = player_inventory.has_secure_phone
                if has_skill and has_phone: effective_heat *= (1.0 - SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT)
                elif has_skill: effective_heat *= (1.0 - DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
                elif has_phone: effective_heat *= (1.0 - SECURE_PHONE_HEAT_REDUCTION_PERCENT)
                effective_heat = int(round(effective_heat))
                if effective_heat > 0: current_region.modify_heat(effective_heat); print(f"Discreet cash movement still generated heat... (Heat +{effective_heat} in {current_region.name})")
            except ValueError: print("Invalid amount.")
        elif menu_options.get(choice) and "Ghost Network Access" in menu_options[choice] and not is_ghost_access_unlocked: # ... (as before)
            print(f"\nPurchase Ghost Network Access for {GHOST_NETWORK_ACCESS_COST_DC:.2f} DC?")
            confirm = input("Confirm purchase (yes/no): ").strip().lower()
            if confirm == "yes":
                dc_balance = player_inventory.crypto_wallet.get("DC", 0.0)
                if dc_balance >= GHOST_NETWORK_ACCESS_COST_DC:
                    player_inventory.crypto_wallet["DC"] -= GHOST_NETWORK_ACCESS_COST_DC
                    if player_inventory.crypto_wallet["DC"] < 1e-9 : del player_inventory.crypto_wallet["DC"]
                    player_inventory.unlocked_skills.append("GHOST_NETWORK_ACCESS")
                    print("Ghost Network Access Purchased! You can now access the Crypto-Only Shop from the main menu.")
                else: print(f"Insufficient DarkCoin. You have {dc_balance:.2f} DC.")
        elif menu_options.get(choice) and "Stake DC" in menu_options[choice] : # ... (as before)
            try:
                dc_in_wallet = player_inventory.crypto_wallet.get("DC", 0.0)
                amount_str = input(f"How much DC to stake? (Available in wallet: {dc_in_wallet:.4f}): ")
                if not amount_str: continue; amount_to_stake = float(amount_str)
                if amount_to_stake <= 0: print("Amount must be positive."); continue
                if amount_to_stake > dc_in_wallet + 1e-9: print("Not enough DC in wallet to stake."); continue
                player_inventory.crypto_wallet["DC"] -= amount_to_stake
                if player_inventory.crypto_wallet["DC"] < 1e-9: del player_inventory.crypto_wallet["DC"]
                player_inventory.staked_dc += amount_to_stake
                print(f"Successfully staked {amount_to_stake:.4f} DC. New staked balance: {player_inventory.staked_dc:.4f} DC.")
            except ValueError: print("Invalid amount.")
        elif menu_options.get(choice) and "Unstake DC" in menu_options[choice]: # ... (as before)
            if player_inventory.staked_dc <=0: print("You have no DC staked."); continue
            try:
                amount_str = input(f"How much DC to unstake? (Available staked: {player_inventory.staked_dc:.4f}): ")
                if not amount_str: continue; amount_to_unstake = float(amount_str)
                if amount_to_unstake <= 0: print("Amount must be positive."); continue
                if amount_to_unstake > player_inventory.staked_dc + 1e-9 : print("Cannot unstake more than you have staked."); continue
                player_inventory.staked_dc -= amount_to_unstake
                player_inventory.crypto_wallet["DC"] = player_inventory.crypto_wallet.get("DC", 0.0) + amount_to_unstake
                print(f"Successfully unstaked {amount_to_unstake:.4f} DC. New wallet balance: {player_inventory.crypto_wallet.get('DC',0.0):.4f} DC.")
            except ValueError: print("Invalid amount.")
        elif choice == "0": print("Leaving the Tech Contact..."); break
        else: print("Invalid choice.")


def handle_crypto_shop(player_inventory: PlayerInventory): # ... (as before)
    if "GHOST_NETWORK_ACCESS" not in player_inventory.unlocked_skills: print("\nAccess Denied. You need Ghost Network Access."); return
    print("\n--- Ghost Network Shop ---"); print("Welcome to the exclusive Crypto-Only Shop.")
    while True:
        print("\nShop Items (Prices in DarkCoin - DC):")
        digital_arsenal_owned = "DIGITAL_ARSENAL" in player_inventory.unlocked_skills; owned_str = "(Owned)" if digital_arsenal_owned else ""
        print(f"1. Digital Arsenal (Cost: {DIGITAL_ARSENAL_COST_DC:.2f} DC) {owned_str}"); print("   - Provides daily alerts on police crackdowns and high regional heat.")
        print("0. Exit Shop"); choice = input("Enter item number to purchase or 0 to exit: ").strip()
        if choice == "1":
            if digital_arsenal_owned: print("You already own the Digital Arsenal.")
            else:
                dc_balance = player_inventory.crypto_wallet.get("DC", 0.0)
                if dc_balance >= DIGITAL_ARSENAL_COST_DC:
                    player_inventory.crypto_wallet["DC"] -= DIGITAL_ARSENAL_COST_DC
                    if player_inventory.crypto_wallet["DC"] < 1e-9: del player_inventory.crypto_wallet["DC"]
                    player_inventory.unlocked_skills.append("DIGITAL_ARSENAL"); print("\nDigital Arsenal acquired! Check daily status for alerts.")
                else: print(f"Insufficient DarkCoin. You need {DIGITAL_ARSENAL_COST_DC:.2f} DC, have {dc_balance:.2f} DC.")
        elif choice == "0": print("Leaving the Ghost Network Shop."); break
        else: print("Invalid choice.")

def handle_meet_corrupt_official(current_region: Region, player_inventory: PlayerInventory, content_pad, log_win, input_win):
    import curses
    content_pad.clear()
    pad_line = 0
    content_pad.addstr(pad_line, 0, "--- Meet Corrupt Official ---", curses.color_pair(2) | curses.A_BOLD)
    pad_line += 1
    content_pad.addstr(pad_line, 0, f"Current Heat in {current_region.name}: {current_region.current_heat}", curses.color_pair(1))
    pad_line += 1
    base_cost = CORRUPT_OFFICIAL_BASE_BRIBE_COST + (current_region.current_heat * CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT)
    content_pad.addstr(pad_line, 0, f"Bribe Cost: ${base_cost:.2f}", curses.color_pair(1))
    pad_line += 1
    content_pad.addstr(pad_line, 0, "0. Back to Main Menu", curses.color_pair(5))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "Pay bribe? (yes/0): ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    choice = input_win.getstr(0, 17, 10).decode().strip().lower()
    curses.noecho()
    if choice == "0":
        return
    if player_inventory.cash < base_cost:
        log_win.clear()
        log_win.addstr(0, 0, "Not enough cash for the bribe.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    player_inventory.cash -= base_cost
    original_heat = current_region.current_heat
    current_region.modify_heat(-CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT)
    actual_reduction = original_heat - current_region.current_heat
    log_win.clear()
    log_win.addstr(0, 0, f"Arrangements made. Heat -{actual_reduction} in {current_region.name}. New heat: {current_region.current_heat}", curses.color_pair(3))
    log_win.noutrefresh()
    curses.doupdate()

def handle_respond_to_setup(current_region: Region, player_inventory: PlayerInventory, all_regions: Dict[str, Region], current_day: int, ai_rivals: List[AIRival], crypto_volatility_map: Dict[str,float], crypto_min_prices_map: Dict[str,float], content_pad=None, log_win=None, input_win=None) -> int:
    import curses
    setup_event = None
    event_to_remove_idx = -1
    for idx, event_obj in enumerate(current_region.active_market_events):
        if event_obj.event_type == "THE_SETUP":
            setup_event = event_obj
            event_to_remove_idx = idx
            break
    if not setup_event or not setup_event.deal_drug_name or not setup_event.deal_quality or setup_event.deal_quantity is None or setup_event.deal_price_per_unit is None:
        if log_win:
            log_win.clear()
            log_win.addstr(0, 0, "No current opportunities of that kind, or the offer is unclear.", curses.color_pair(4))
            log_win.noutrefresh()
            curses.doupdate()
        return current_day
    action_str = "Buy" if setup_event.is_buy_deal else "Sell"
    if content_pad:
        content_pad.clear()
        pad_line = 0
        content_pad.addstr(pad_line, 0, f"--- Shady Opportunity in {current_region.name} ---", curses.color_pair(2) | curses.A_BOLD)
        pad_line += 1
        content_pad.addstr(pad_line, 0, f"Offer: {action_str} {setup_event.deal_quantity} units of {setup_event.deal_quality.name} {setup_event.deal_drug_name}", curses.color_pair(1))
        pad_line += 1
        content_pad.addstr(pad_line, 0, f"       at ${setup_event.deal_price_per_unit:.2f} per unit.", curses.color_pair(1))
        pad_line += 1
        content_pad.addstr(pad_line, 0, "This could be very profitable... or very dangerous.", curses.color_pair(4))
        content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    if input_win:
        input_win.clear()
        input_win.addstr(0, 0, "Accept this deal? (yes/no): ", curses.color_pair(6))
        input_win.refresh()
        curses.echo()
        choice = input_win.getstr(0, 25, 10).decode().strip().lower()
        curses.noecho()
    else:
        choice = input("Accept this deal? (yes/no): ").strip().lower()
    if choice != "yes":
        if event_to_remove_idx != -1:
            current_region.active_market_events.pop(event_to_remove_idx)
        if log_win:
            log_win.clear()
            log_win.addstr(0, 0, "You walk away from the deal. Probably for the best.", curses.color_pair(1))
            log_win.noutrefresh()
            curses.doupdate()
        return current_day
    if event_to_remove_idx != -1:
        current_region.active_market_events.pop(event_to_remove_idx)
    if setup_event.is_buy_deal:
        total_cost = setup_event.deal_quantity * setup_event.deal_price_per_unit
        if player_inventory.cash < total_cost:
            if log_win:
                log_win.clear()
                log_win.addstr(0, 0, f"You don't have enough cash (${total_cost:.2f} needed). The 'contact' scoffs and leaves.", curses.color_pair(4))
                log_win.noutrefresh()
                curses.doupdate()
            return current_day
        if player_inventory.get_available_space() < setup_event.deal_quantity:
            if log_win:
                log_win.clear()
                log_win.addstr(0, 0, f"Not enough space in your inventory for {setup_event.deal_quantity} units. The deal is off.", curses.color_pair(4))
                log_win.noutrefresh()
                curses.doupdate()
            return current_day
    else:
        if player_inventory.get_quantity(setup_event.deal_drug_name, setup_event.deal_quality) < setup_event.deal_quantity:
            if log_win:
                log_win.clear()
                log_win.addstr(0, 0, f"You don't have {setup_event.deal_quantity} units of {setup_event.deal_quality.name} {setup_event.deal_drug_name} to sell. The 'contact' is not amused.", curses.color_pair(4))
                log_win.noutrefresh()
                curses.doupdate()
            return current_day
    # Sting check
    sting_chance = SETUP_EVENT_STING_CHANCE_BASE + (current_region.current_heat * SETUP_EVENT_STING_CHANCE_HEAT_MODIFIER)
    sting_chance = max(0.1, min(sting_chance, 0.9))
    import random
    if random.random() < sting_chance:
        if log_win:
            log_win.clear()
            log_win.addstr(0, 0, "!!! IT'S A STING !!! The 'deal' was a setup by the cops! They move in!", curses.color_pair(4) | curses.A_BOLD)
            log_win.noutrefresh()
            curses.doupdate()
        new_day_after_sting = handle_police_stop_event(current_region, player_inventory, all_regions, current_day, ai_rivals, crypto_volatility_map, crypto_min_prices_map)
        return new_day_after_sting if new_day_after_sting is not None else current_day
    # Legit deal
    if setup_event.is_buy_deal:
        total_cost = setup_event.deal_quantity * setup_event.deal_price_per_unit
        player_inventory.cash -= total_cost
        player_inventory.add_drug(setup_event.deal_drug_name, setup_event.deal_quality, setup_event.deal_quantity)
        apply_player_buy_impact(current_region, setup_event.deal_drug_name, setup_event.deal_quantity)
        if log_win:
            log_win.clear()
            log_win.addstr(0, 0, f"Successfully bought {setup_event.deal_quantity} units of {setup_event.deal_quality.name} {setup_event.deal_drug_name} for ${total_cost:.2f}.", curses.color_pair(3))
            log_win.noutrefresh()
            curses.doupdate()
    else:
        total_revenue = setup_event.deal_quantity * setup_event.deal_price_per_unit
        player_inventory.remove_drug(setup_event.deal_drug_name, setup_event.deal_quality, setup_event.deal_quantity)
        player_inventory.cash += total_revenue
        apply_player_sell_impact(current_region, setup_event.deal_drug_name, setup_event.deal_quantity)
        if log_win:
            log_win.clear()
            log_win.addstr(0, 0, f"Successfully sold {setup_event.deal_quantity} units of {setup_event.deal_quality.name} {setup_event.deal_drug_name} for ${total_revenue:.2f}.", curses.color_pair(3))
            log_win.noutrefresh()
            curses.doupdate()
    heat_from_deal = random.randint(15, 40)
    current_region.modify_heat(heat_from_deal)
    if log_win:
        log_win.addstr(1, 0, f"A deal this size doesn't go unnoticed... (Heat +{heat_from_deal} in {current_region.name})", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
    return current_day

def handle_view_market(region: Region, player_inventory: PlayerInventory, content_pad, log_win, input_win):
    import curses # Make sure curses is imported if not already at the top of the file
    # (Assuming print_market_header is available from ui_helpers and is curses-aware)
    # from .ui_helpers import print_market_header # If not already imported

    show_trend_icons = "MARKET_INTUITION" in player_inventory.unlocked_skills
    content_pad.clear() # Clear the pad for new content

    # Get pad dimensions (max_y, max_x of the pad itself, not the screen viewport)
    # pad_max_y, pad_max_x = content_pad.getmaxyx() # Not strictly needed for writing, but good for context

    # Get screen viewport dimensions (passed from main.py or determined dynamically)
    # These define where the pad content is displayed on the main screen (stdscr)
    # Example: if header_win is 5 lines, content_viewport_start_row = 5
    # content_viewport_height = stdscr.getmaxyx()[0] - header_height - log_height - input_height
    # For this example, let's assume these are passed or known:
    content_viewport_start_row = 5 # Screen row where pad display begins
    content_viewport_height = 15   # Number of lines visible for the pad on screen
    content_viewport_width = 79    # Width of the pad viewport on screen

    pad_current_line = 0 # Tracks the current line number on the pad itself

    # Draw title
    title_str = f"--- Market in {region.name} (Regional Heat: {region.current_heat}) ---"
    content_pad.addstr(pad_current_line, 0, title_str, curses.color_pair(2) | curses.A_BOLD)
    pad_current_line += 1

    # Draw market header (using the curses-aware version from ui_helpers)
    # print_market_header is expected to draw at pad_current_line and increment it
    # For this example, let's assume print_market_header draws 2 lines
    # and we pass pad_current_line to it, or it draws at its current cursor.
    # To be safe, let's manage pad_current_line explicitly here.
    temp_header_pad = content_pad.derwin(2, content_viewport_width, pad_current_line, 0)
    print_market_header(temp_header_pad, region.name, show_trend=show_trend_icons)
    temp_header_pad.noutrefresh() # Refresh the sub-pad if it was used directly
    # Or, if print_market_header writes directly to content_pad starting at pad_current_line:
    # print_market_header(content_pad.derwin(pad_current_line,0), region.name, show_trend=show_trend_icons) # this is complex
    # Simplest: Assume print_market_header writes to the passed window at its (0,0)
    # So, we create a sub-window/pad for it if it doesn't take y,x args.
    # For now, let's assume print_market_header itself handles drawing to content_pad at current y,x
    # and we manually increment pad_current_line after it.
    # If print_market_header is like: def print_market_header(target_window, ...): target_window.addstr(0,0,...) target_window.addstr(1,0,...)
    # then we need to manage its position carefully or make it write to a specific line.
    # Let's assume it writes starting at pad_current_line and takes 2 lines.
    # This part needs to align with how print_market_header is implemented.
    # For now, direct addstr for header for clarity here:
    trend_col_text = " T " if show_trend_icons else ""
    market_header_text = f"{'*':<1}{trend_col_text}{'Drug':<9} {'Quality':<9} {'Buy Price':<10} {'Sell Price':<11} {'Stock':<10}"
    content_pad.addstr(pad_current_line, 0, market_header_text, curses.color_pair(2) | curses.A_BOLD)
    pad_current_line += 1
    content_pad.addstr(pad_current_line, 0, "-" * len(market_header_text), curses.color_pair(2))
    pad_current_line += 1

    sorted_drug_names = sorted(region.drug_market_data.keys())
    market_data_lines_for_pad = [] # Store (text, color_pair) tuples

    if not sorted_drug_names:
        market_data_lines_for_pad.append(("No drugs traded in this market currently.", curses.color_pair(4)))
    else:
        for drug_name in sorted_drug_names:
            drug_data_market = region.drug_market_data[drug_name]
            available_qualities = drug_data_market.get("available_qualities", {})
            if available_qualities:
                for quality in sorted(available_qualities.keys(), key=lambda q: q.value):
                    stock = region.get_available_stock(drug_name, quality)
                    current_buy_price = region.get_buy_price(drug_name, quality)
                    current_sell_price = region.get_sell_price(drug_name, quality)
                    previous_sell_price = drug_data_market.get("available_qualities", {}).get(quality, {}).get("previous_sell_price", None)
                    trend_icon = " "
                    if show_trend_icons:
                        if previous_sell_price is not None and current_sell_price > 0 and previous_sell_price > 0:
                            if current_sell_price > previous_sell_price * 1.02: trend_icon = "↑"
                            elif current_sell_price < previous_sell_price * 0.98: trend_icon = "↓"
                            else: trend_icon = "="
                        elif current_sell_price > 0: trend_icon = "?"
                    event_active_marker = " "
                    is_disrupted = False
                    for event in region.active_market_events:
                        if event.target_drug_name == drug_name and event.target_quality == quality:
                            event_active_marker = "*"
                            if event.event_type == "SUPPLY_CHAIN_DISRUPTION": is_disrupted = True
                            break
                    actual_buy_price = current_buy_price if not (is_disrupted and stock == 0) else 0.0
                    buy_price_str = f"${actual_buy_price:<9.2f}" if actual_buy_price > 0 or (stock == 0 and event_active_marker == "*" and not is_disrupted) else "---".ljust(10)
                    sell_price_str = f"${current_sell_price:<10.2f}" if current_sell_price > 0 or event_active_marker == "*" else "---".ljust(11)
                    stock_display = f"{stock:<10}" if not is_disrupted else (f"{str(stock)} (LOW)".ljust(10) if stock > 0 else f"{stock} (NONE)".ljust(10))
                    drug_col_width = 9 if show_trend_icons else 10
                    quality_col_width = 9 if show_trend_icons else 10
                    line_text = f"{event_active_marker}{trend_icon:<2}{drug_name:<{drug_col_width}} {quality.name:<{quality_col_width}} {buy_price_str} {sell_price_str} {stock_display}"
                    color_to_use = curses.color_pair(1)
                    if event_active_marker == "*": color_to_use = curses.color_pair(3) | curses.A_BOLD
                    elif is_disrupted: color_to_use = curses.color_pair(4)
                    market_data_lines_for_pad.append((line_text, color_to_use))
            else:
                market_data_lines_for_pad.append((f"  {drug_name:<10} - No qualities listed.", curses.color_pair(4)))

    # Draw collected market data lines to the pad
    for text, color_attr in market_data_lines_for_pad:
        content_pad.addstr(pad_current_line, 0, text, color_attr)
        pad_current_line += 1

    # Active events section
    if region.active_market_events:
        content_pad.addstr(pad_current_line, 0, "", curses.color_pair(1)) # Blank line for spacing
        pad_current_line += 1
        content_pad.addstr(pad_current_line, 0, "Active Market Events:", curses.color_pair(2) | curses.A_BOLD)
        pad_current_line += 1
        for event in region.active_market_events:
            target_info = f"{event.target_quality.name} {event.target_drug_name}" if event.target_drug_name and event.target_quality else "Regional"
            if event.event_type == "THE_SETUP" and event.deal_drug_name and event.deal_quality:
                target_info = f"Offer: {'Buy' if event.is_buy_deal else 'Sell'} {event.deal_quantity} {event.deal_quality.name} {event.deal_drug_name} @ ${event.deal_price_per_unit:.2f}"
            event_line = f"  - {event.event_type.replace('_',' ').title()}: {target_info} (Days left: {event.duration_remaining_days})"
            content_pad.addstr(pad_current_line, 0, event_line, curses.color_pair(5))
            pad_current_line += 1

    # Scrolling logic
    current_scroll_pos = 0
    # pad_current_line is the total number of lines written to the pad
    max_scrollable_lines = max(0, pad_current_line - content_viewport_height)

    # Define screen viewport for the pad (pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol)
    # sminrow, smincol, smaxrow, smaxcol define the box on the physical screen.
    # pminrow, pmincol define the top-left corner of the pad content to display.
    # These should align with the main.py window layout.
    # Example: if header_win is 5 lines high, pad viewport starts at screen row 5.
    screen_viewport_sminrow = content_viewport_start_row
    screen_viewport_smincol = 0
    screen_viewport_smaxrow = content_viewport_start_row + content_viewport_height - 1
    screen_viewport_smaxcol = content_viewport_width -1 # Assuming pad is full width of viewport

    while True:
        content_pad.noutrefresh(current_scroll_pos, 0, screen_viewport_sminrow, screen_viewport_smincol, screen_viewport_smaxrow, screen_viewport_smaxcol)
        # log_win.noutrefresh() # Refresh log if it has separate messages
        input_win.clear()
        input_win.addstr(0, 0, "PgUp/PgDn/Up/Down: Scroll  Q/Enter: Quit", curses.color_pair(6))
        input_win.refresh()
        curses.doupdate()

        key_code = input_win.getch() # Use getch() for special keys
        key_name = curses.keyname(key_code).decode('utf-8')

        if key_name in ['q', 'Q', '\n', 'KEY_ENTER']:
            break
        elif key_name == 'KEY_DOWN' and current_scroll_pos < max_scrollable_lines:
            current_scroll_pos += 1
        elif key_name == 'KEY_UP' and current_scroll_pos > 0:
            current_scroll_pos -= 1
        elif key_name == 'KEY_NPAGE' and current_scroll_pos < max_scrollable_lines: # Page Down
            current_scroll_pos = min(current_scroll_pos + content_viewport_height, max_scrollable_lines)
        elif key_name == 'KEY_PPAGE' and current_scroll_pos > 0: # Page Up
            current_scroll_pos = max(current_scroll_pos - content_viewport_height, 0)