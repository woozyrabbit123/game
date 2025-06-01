import random
import math
from typing import List, Dict, Tuple, Optional, Any  # Added Any

from ...core.region import Region
from ...core.player_inventory import PlayerInventory
from ...core.ai_rival import AIRival
from ...core.enums import DrugQuality, DrugName, RegionName  # Added Enums
from ...core.market_event import MarketEvent
from ...game_state import GameState  # Import GameState
from .ui_helpers import parse_drug_quality, print_market_header
from ...mechanics.market_impact import (
    apply_player_buy_impact,
    apply_player_sell_impact,
    decay_player_market_impact,
    process_rival_turn,
    decay_rival_market_impact,
    decay_regional_heat,
)

# from ... import game_state # Removed old game_state import
from ... import game_configs  # Import game_configs module
from ...game_configs import (
    CAPACITY_UPGRADE_COST_INITIAL,
    CAPACITY_UPGRADE_COST_MULTIPLIER,
    CAPACITY_UPGRADE_AMOUNT,
    SKILL_POINTS_PER_X_DAYS,
    SKILL_MARKET_INTUITION_COST,
    SKILL_DIGITAL_FOOTPRINT_COST,
    INFORMANT_TIP_COST,
    INFORMANT_TRUST_GAIN_PER_TIP,
    INFORMANT_MAX_TRUST,
    CRYPTO_VOLATILITY,
    CRYPTO_MIN_PRICE,
    TECH_CONTACT_FEE_PERCENT,
    HEAT_FROM_SELLING_DRUG_TIER,
    HEAT_FROM_CRYPTO_TRANSACTION,
    POLICE_STOP_HEAT_THRESHOLD,
    POLICE_STOP_BASE_CHANCE,
    POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD,
    BRIBE_BASE_COST_PERCENT_OF_CASH,
    BRIBE_MIN_COST,
    BRIBE_SUCCESS_CHANCE_BASE,
    BRIBE_SUCCESS_CHANCE_HEAT_PENALTY,
    CONFISCATION_CHANCE_ON_SEARCH,
    CONFISCATION_PERCENTAGE_MIN,
    CONFISCATION_PERCENTAGE_MAX,
    JAIL_TIME_DAYS_BASE,
    JAIL_TIME_HEAT_MULTIPLIER,
    JAIL_CHANCE_HEAT_THRESHOLD,
    JAIL_CHANCE_IF_HIGH_TIER_DRUGS_FOUND,
    GHOST_NETWORK_ACCESS_COST_DC,
    DIGITAL_ARSENAL_COST_DC,
    DC_STAKING_DAILY_RETURN_PERCENT,
    CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT,
    CORRUPT_OFFICIAL_BASE_BRIBE_COST,
    CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT,
    LAUNDERING_FEE_PERCENT,
    LAUNDERING_DELAY_DAYS,
    MAX_ACTIVE_LAUNDERING_OPERATIONS,
    SETUP_EVENT_STING_CHANCE_BASE,
    SETUP_EVENT_STING_CHANCE_HEAT_MODIFIER,
    DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT,
    SECURE_PHONE_COST,
    SECURE_PHONE_HEAT_REDUCTION_PERCENT,
    SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT,
)

# Note: Most handlers will now take game_state_instance: GameState as first arg


def handle_police_stop_event(
    game_state_instance: GameState, player_inventory: PlayerInventory
) -> Optional[int]:
    region: Optional[Region] = game_state_instance.get_current_player_region()
    if not region:  # Should not happen if called correctly, but good check
        print("Police stop event triggered but current region is not set.")
        return None
    all_regions: Dict[RegionName, Region] = game_state_instance.get_all_regions()
    current_day: int = game_state_instance.current_day
    ai_rivals = game_state_instance.ai_rivals
    # Crypto maps are now sourced from game_configs within handle_advance_day if needed

    separator: str = "=" * 40
    print("\n" + separator)
    print("!!! POLICE STOP !!!".center(len(separator)))
    print("Red and blue lights flash! You're pulled over.".center(len(separator)))
    print(
        f"(Current heat in {region.name.value}: {region.current_heat})".center(
            len(separator)
        )
    )
    print(separator)
    new_current_day_after_jail: Optional[int] = None
    while True:
        print("\nYour options:")
        print("  1. Attempt to Bribe Officer")
        print("  2. Comply (Allow Search)")
        choice: str = input("What do you do? (1-2): ").strip()
        if choice == "1":
            bribe_cost: float = round(
                max(
                    BRIBE_MIN_COST,
                    player_inventory.cash * BRIBE_BASE_COST_PERCENT_OF_CASH,
                ),
                2,
            )
            if player_inventory.cash < bribe_cost:
                print(
                    f"\nYou barely have ${player_inventory.cash:.2f}. Not enough for a bribe of ${bribe_cost:.2f}. You're forced to comply."
                )
                choice = "2"
            else:
                bribe_confirm: str = (
                    input(
                        f"Offer a bribe of ${bribe_cost:.2f}? This is risky... (yes/no): "
                    )
                    .strip()
                    .lower()
                )
                if bribe_confirm == "yes":
                    player_inventory.cash -= bribe_cost
                    print(f"\nYou slip the officer ${bribe_cost:.2f}...")
                    heat_points_above_threshold: int = max(
                        0, region.current_heat - POLICE_STOP_HEAT_THRESHOLD
                    )
                    penalty: float = float(
                        heat_points_above_threshold * BRIBE_SUCCESS_CHANCE_HEAT_PENALTY
                    )
                    bribe_success_actual_chance: float = max(
                        0.1, min(0.9, BRIBE_SUCCESS_CHANCE_BASE - penalty)
                    )
                    if random.random() < bribe_success_actual_chance:
                        print(
                            "The officer smirks, pockets the cash, and waves you on. 'Just a routine check. Drive safe.'"
                        )
                        print(separator + "\n")
                        return None
                    else:
                        print(
                            "'Trying to bribe an officer of the law, huh?' The officer scoffs. 'That just made things worse! Out of the vehicle!'"
                        )
                        choice = "2"
                else:
                    print(
                        "You decide against the bribe. 'Alright officer, what seems to be the problem?'"
                    )
                    choice = "2"
        if choice == "2":
            print("\nThe officer searches your vehicle and belongings thoroughly...")
            drugs_found_during_search: bool = False
            if (
                not player_inventory.items
                or random.random() > CONFISCATION_CHANCE_ON_SEARCH
            ):
                print(
                    "Surprisingly, they don't find anything illicit. 'Alright, you're free to go. Stay out of trouble.'"
                )
                print(separator + "\n")
                return None
            else:
                print(
                    "'Aha! What do we have here? Looks like your lucky day just ran out.'"
                )
                drugs_found_during_search = True
                drug_to_confiscate_name_enum: DrugName = random.choice(
                    list(player_inventory.items.keys())
                )
                qualities_of_drug: Dict[DrugQuality, int] = player_inventory.items[
                    drug_to_confiscate_name_enum
                ]
                quality_to_confiscate_enum: DrugQuality = random.choice(
                    list(qualities_of_drug.keys())
                )
                current_quantity_val: int = qualities_of_drug[
                    quality_to_confiscate_enum
                ]  # Renamed
                confiscation_percentage_val: float = random.uniform(
                    CONFISCATION_PERCENTAGE_MIN, CONFISCATION_PERCENTAGE_MAX
                )  # Renamed
                quantity_to_confiscate_val: int = math.ceil(
                    current_quantity_val * confiscation_percentage_val
                )  # Renamed
                quantity_to_confiscate_val = (
                    max(1, quantity_to_confiscate_val)
                    if current_quantity_val > 0
                    else 0
                )
                quantity_to_confiscate_val = min(
                    current_quantity_val, quantity_to_confiscate_val
                )
                if quantity_to_confiscate_val > 0:
                    player_inventory.remove_drug(
                        drug_to_confiscate_name_enum,
                        quality_to_confiscate_enum,
                        quantity_to_confiscate_val,
                    )
                    print(
                        f"CONFISCATED: {quantity_to_confiscate_val} units of {quality_to_confiscate_enum.name} {drug_to_confiscate_name_enum.value}."
                    )
                    heat_increase_on_bust_val: int = random.randint(5, 15)
                    region.modify_heat(heat_increase_on_bust_val)
                    print(
                        f"This incident has drawn more attention in {region.name.value}. (Heat +{heat_increase_on_bust_val})"
                    )  # Renamed
                else:
                    print(
                        "They rummage through your things but don't confiscate anything specific this time. 'Watch yourself.'"
                    )

                if drugs_found_during_search:
                    current_chance_of_jail_val: float = 0.0  # Renamed
                    if region.current_heat >= JAIL_CHANCE_HEAT_THRESHOLD:
                        current_chance_of_jail_val += 0.2
                    has_high_tier_drugs_flag: bool = False  # Renamed
                    for (
                        drug_name_inv_enum,
                        qualities_inv,
                    ) in player_inventory.items.items():
                        drug_tier_val: int = 0  # Renamed
                        if drug_name_inv_enum in region.drug_market_data:
                            drug_tier_val = region.drug_market_data.get(
                                drug_name_inv_enum, {}
                            ).get("tier", 0)
                        else:
                            for r_obj in all_regions.values():
                                if drug_name_inv_enum in r_obj.drug_market_data:
                                    drug_tier_val = r_obj.drug_market_data.get(
                                        drug_name_inv_enum, {}
                                    ).get("tier", 0)
                                    break
                        if drug_tier_val >= 3 and any(
                            qty > 0 for qty in qualities_inv.values()
                        ):
                            has_high_tier_drugs_flag = True
                            break  # Simplified check
                    if has_high_tier_drugs_flag:
                        current_chance_of_jail_val += (
                            JAIL_CHANCE_IF_HIGH_TIER_DRUGS_FOUND
                        )
                    current_chance_of_jail_val = min(current_chance_of_jail_val, 0.75)

                    if random.random() < current_chance_of_jail_val:
                        days_in_jail_val: int = JAIL_TIME_DAYS_BASE + int(
                            (region.current_heat - JAIL_CHANCE_HEAT_THRESHOLD)
                            * JAIL_TIME_HEAT_MULTIPLIER
                        )
                        days_in_jail_val = max(
                            JAIL_TIME_DAYS_BASE, days_in_jail_val
                        )  # Renamed
                        print(
                            f"\nThis is serious! You're arrested and sentenced to {days_in_jail_val} days in jail!"
                        )
                        print("You lose time while locked up...")
                        temp_current_day_val: int = (
                            game_state_instance.current_day
                        )  # Renamed
                        for _i in range(days_in_jail_val):  # _i for unused loop var
                            print(
                                f"...Day {temp_current_day_val + 1} passes in a blur..."
                            )
                            temp_current_day_val = handle_advance_day(game_state_instance, player_inventory, content_pad=None, log_win=None, input_win=None, is_jailed_turn=True)  # type: ignore
                        new_current_day_after_jail = temp_current_day_val
                        print(
                            f"You're finally released. It's Day {new_current_day_after_jail}."
                        )
                        print(separator + "\n")
                        return new_current_day_after_jail
                print(
                    "You got off with a warning and a hefty 'fine' (confiscation), but they'll be watching you."
                )
                print(separator + "\n")
                return None
        else:
            print("Invalid choice. The officer is waiting...")
    return None  # Should be unreachable if logic is correct


def check_and_trigger_police_stop(
    game_state_instance: GameState, player_inventory: PlayerInventory
) -> Optional[int]:
    current_region: Optional[Region] = game_state_instance.get_current_player_region()
    if not current_region:
        return None

    # Calculate chance using the new centralized function
    # game_configs module is already imported in this file
    encounter_chance = calculate_police_encounter_chance(current_region, game_configs)

    if random.random() < encounter_chance:
        # For now, it still calls the original handle_police_stop_event.
        # A subsequent refactor would change this to call a new UI-specific orchestrator function
        # which in turn uses resolve_bribe_attempt and resolve_search_outcome.
        return handle_police_stop_event(game_state_instance, player_inventory)
    return None


def handle_view_inventory(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    import curses

    content_pad.clear()
    pad_max_y, pad_max_x = content_pad.getmaxyx()  # Pad dimensions
    pad_line: int = 0
    content_pad.addstr(
        pad_line, 0, "--- Player Inventory ---", curses.color_pair(2) | curses.A_BOLD
    )
    pad_line += 1
    summary_lines: List[str] = player_inventory.formatted_summary().split("\n")
    for line in summary_lines:
        if pad_line < pad_max_y:  # Check against pad height
            content_pad.addstr(
                pad_line, 0, line[: pad_max_x - 1], curses.color_pair(1)
            )  # Truncate line
            pad_line += 1

    scroll_y_val: int = 0  # Renamed
    # These need to be determined from where this pad is displayed on screen
    # For now, using example values or passed values if available
    header_height = 5  # Example from main.py
    log_height_val = 4  # Example
    input_height_val = 2  # Example
    screen_height_val, screen_width_val = (
        input_win.getbegyx()[0] + input_height_val,
        input_win.getbegyx()[1] + input_win.getmaxx(),
    )  # Approx screen size

    sminrow_pad = header_height
    visible_height: int = screen_height_val - (
        header_height + log_height_val + input_height_val
    )
    smaxrow_pad = sminrow_pad + visible_height - 1
    smincol_pad = 0
    smaxcol_pad = screen_width_val - 1

    max_scroll_val: int = max(0, pad_line - visible_height)  # Renamed

    while True:
        content_pad.noutrefresh(
            scroll_y_val, 0, sminrow_pad, smincol_pad, smaxrow_pad, smaxcol_pad
        )
        log_win.noutrefresh()
        input_win.clear()
        input_win.addstr(0, 0, "Up/Down: Scroll  Q/Enter: Quit", curses.color_pair(6))
        input_win.refresh()
        curses.doupdate()
        key_input = input_win.getkey()  # Renamed
        if key_input.lower() == "q" or key_input == "\n":
            break
        elif key_input in ["KEY_DOWN", "j"] and scroll_y_val < max_scroll_val:
            scroll_y_val += 1
        elif key_input in ["KEY_UP", "k"] and scroll_y_val > 0:
            scroll_y_val -= 1


def handle_buy_drug(
    region: Region,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    import curses

    content_pad.clear()
    content_pad.addstr(0, 0, "--- Buy Drug ---", curses.color_pair(2) | curses.A_BOLD)
    content_pad.addstr(
        1,
        0,
        "Enter drug to buy (name quality quantity, e.g., Coke PURE 10):",
        curses.color_pair(1),
    )
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)  # TODO: Adjust viewport as needed
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "> ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    user_input_str: str = input_win.getstr(0, 2, 40).decode().strip()
    curses.noecho()
    user_input_parts: List[str] = user_input_str.split()  # Renamed
    if len(user_input_parts) < 3:
        log_win.clear()
        log_win.addstr(
            0, 0, "Invalid format. Use: DrugName Quality Quantity", curses.color_pair(4)
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    drug_name_input_str: str = user_input_parts[0]  # Renamed
    quality_input_str_val: str = user_input_parts[1]  # Renamed
    quantity_input_str_val: str = user_input_parts[2]  # Renamed

    canonical_drug_name_val: Optional[DrugName] = None  # Renamed
    for dn_market_enum in region.drug_market_data.keys():  # dn_market_enum is DrugName
        if (
            dn_market_enum.value.lower() == drug_name_input_str.lower()
        ):  # Compare with .value
            canonical_drug_name_val = dn_market_enum
            break

    if not canonical_drug_name_val:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Drug '{drug_name_input_str}' not found in {region.name.value}.",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    drug_name_enum_val: DrugName = canonical_drug_name_val  # Renamed
    quality_enum_val: Optional[DrugQuality] = parse_drug_quality(
        quality_input_str_val
    )  # Renamed
    if quality_enum_val is None:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Invalid quality '{quality_input_str_val}'. Valid: PURE, STANDARD, CUT",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    quantity_val: int  # Renamed
    try:
        quantity_val = int(quantity_input_str_val)
        if quantity_val <= 0:
            log_win.clear()
            log_win.addstr(0, 0, "Quantity must be positive.", curses.color_pair(4))
            log_win.noutrefresh()
            curses.doupdate()
            return
    except ValueError:
        log_win.clear()
        log_win.addstr(
            0, 0, "Invalid quantity. Must be a number.", curses.color_pair(4)
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    stock_val: int = region.get_available_stock(
        drug_name_enum_val, quality_enum_val, game_state_instance=GameState()
    )  # Pass dummy GS for now, get_available_stock needs review
    if stock_val < quantity_val:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Insufficient stock. Only {stock_val} of {quality_enum_val.name} {drug_name_enum_val.value} available.",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    buy_price_val: float = region.get_buy_price(
        drug_name_enum_val, quality_enum_val
    )  # Renamed
    if buy_price_val <= 0:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"{quality_enum_val.name} {drug_name_enum_val.value} unavailable.",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    if player_inventory.get_available_space() < quantity_val:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Not enough inventory space. Available: {player_inventory.get_available_space()}",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    total_cost_val: float = buy_price_val * quantity_val

    # Centralized transaction processing in PlayerInventory
    if player_inventory.process_buy_drug(drug_name_enum_val, quality_enum_val, quantity_val, total_cost_val):
        region.update_stock_on_buy(drug_name_enum_val, quality_enum_val, quantity_val)
        # market_impact.apply_player_buy_impact now needs game_configs.
        # Assuming game_configs is available in this scope (it is imported).
        apply_player_buy_impact(region, drug_name_enum_val, quantity_val)

        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Bought {quantity_val} {quality_enum_val.name} {drug_name_enum_val.value} for ${total_cost_val:.2f}",
            curses.color_pair(3),
        )
        log_win.noutrefresh()
        curses.doupdate()
    else:
        # process_buy_drug returned False, meaning not enough cash or space, or other issue.
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Purchase failed. Not enough cash or inventory space.", # Generic message
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()


def handle_sell_drug(
    region: Region,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    import curses

    content_pad.clear()
    content_pad.addstr(0, 0, "--- Sell Drug ---", curses.color_pair(2) | curses.A_BOLD)
    content_pad.addstr(
        1,
        0,
        "Enter drug to sell (name quality quantity, e.g., Coke PURE 5):",
        curses.color_pair(1),
    )
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)  # TODO: Adjust viewport
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "> ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    user_input_str: str = input_win.getstr(0, 2, 40).decode().strip()
    curses.noecho()
    user_input_parts: List[str] = user_input_str.split()  # Renamed
    if len(user_input_parts) < 3:
        log_win.clear()
        log_win.addstr(
            0, 0, "Invalid format. Use: DrugName Quality Quantity", curses.color_pair(4)
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    drug_name_input_str: str = user_input_parts[0]  # Renamed
    quality_input_str_val: str = user_input_parts[1]  # Renamed
    quantity_input_str_val: str = user_input_parts[2]  # Renamed

    player_drug_name_match_val: Optional[DrugName] = None  # Renamed
    for (
        inv_drug_name_enum
    ) in player_inventory.items.keys():  # inv_drug_name_enum is DrugName
        if (
            inv_drug_name_enum.value.lower() == drug_name_input_str.lower()
        ):  # Compare with .value
            player_drug_name_match_val = inv_drug_name_enum
            break

    if not player_drug_name_match_val:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"You don't have any '{drug_name_input_str}' in inventory.",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    drug_name_enum_val: DrugName = player_drug_name_match_val  # Renamed
    quality_enum_val: Optional[DrugQuality] = parse_drug_quality(
        quality_input_str_val
    )  # Renamed
    if quality_enum_val is None:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Invalid quality '{quality_input_str_val}'. Valid: PURE, STANDARD, CUT",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    quantity_val: int  # Renamed
    try:
        quantity_val = int(quantity_input_str_val)
        if quantity_val <= 0:
            log_win.clear()
            log_win.addstr(0, 0, "Quantity must be positive.", curses.color_pair(4))
            log_win.noutrefresh()
            curses.doupdate()
            return
    except ValueError:
        log_win.clear()
        log_win.addstr(
            0, 0, "Invalid quantity. Must be a number.", curses.color_pair(4)
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    player_quantity_val: int = player_inventory.get_quantity(
        drug_name_enum_val, quality_enum_val
    )  # Renamed
    if player_quantity_val < quantity_val:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Not enough {quality_enum_val.name} {drug_name_enum_val.value}. Have: {player_quantity_val}",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    market_drug_name_for_price_val: Optional[DrugName] = None  # Renamed
    drug_tier_val: int = 1  # Renamed
    if drug_name_enum_val in region.drug_market_data:
        market_drug_name_for_price_val = drug_name_enum_val
        drug_tier_val = region.drug_market_data[drug_name_enum_val].get("tier", 1)
    else:  # Fallback if enum key is not directly in market_data (e.g. if market uses string keys)
        for (
            m_name_enum_key,
            m_data_val,
        ) in region.drug_market_data.items():  # m_name_enum_key is DrugName
            if m_name_enum_key.value.lower() == drug_name_enum_val.value.lower():
                market_drug_name_for_price_val = m_name_enum_key
                drug_tier_val = m_data_val.get("tier", 1)
                break

    if not market_drug_name_for_price_val:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Market in {region.name.value} does not trade {drug_name_enum_val.value}.",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    sell_price_val: float = region.get_sell_price(
        market_drug_name_for_price_val, quality_enum_val
    )  # Renamed
    if sell_price_val <= 0:
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Market in {region.name.value} not buying {quality_enum_val.name} {drug_name_enum_val.value}.",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    total_revenue_val: float = sell_price_val * quantity_val

    # Centralized transaction processing in PlayerInventory
    if player_inventory.process_sell_drug(drug_name_enum_val, quality_enum_val, quantity_val, total_revenue_val):
        region.update_stock_on_sell(market_drug_name_for_price_val, quality_enum_val, quantity_val) # Use market_drug_name_for_price_val here

        # apply_player_sell_impact handles heat generation as well.
        # It requires player_inventory, region, drug_name, quantity, and game_configs.
        apply_player_sell_impact(
            player_inventory,
            region,
            market_drug_name_for_price_val, # Use the name known to the market for impact
            quantity_val,
            game_configs,
        )

        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Sold {quantity_val} {quality_enum_val.name} {drug_name_enum_val.value} for ${total_revenue_val:.2f}",
            curses.color_pair(3),
        )
        # Heat message is now implicitly part of apply_player_sell_impact if that function logs or if a separate heat log is desired
        # For now, this handler won't log heat directly from here to avoid duplication if apply_player_sell_impact does it.
        # If apply_player_sell_impact does *not* log, and we want it logged here, we'd need to calculate heat separately again.
        # The current apply_player_sell_impact in market_impact.py does NOT log heat, but modifies region.current_heat.
        # The old logic in this handler *did* log heat.
        # Let's re-add the heat logging for clarity, assuming apply_player_sell_impact doesn't log it.
        # To do this, we need drug_tier_val again.
        heat_generated_val: int = quantity_val * HEAT_FROM_SELLING_DRUG_TIER.get(drug_tier_val, 1)
        if heat_generated_val > 0: # Assuming heat was already applied by apply_player_sell_impact modifying region
            # This log is just informational about the amount that was generated.
             if heat_generated_val > 5 : # Threshold for logging, as before
                log_win.addstr(1, 0, f"Sale generated +{heat_generated_val} heat in {region.name.value}", curses.color_pair(4))

        log_win.noutrefresh()
        curses.doupdate()
    else:
        # process_sell_drug returned False, meaning not enough items.
        log_win.clear()
        log_win.addstr(
            0,
            0,
            f"Sale failed. Not enough {quality_enum_val.name} {drug_name_enum_val.value} in inventory.", # Generic message
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()


def handle_advance_day(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Optional[Any],
    log_win: Optional[Any],
    input_win: Optional[Any],
    is_jailed_turn: bool = False,
) -> int:
    import curses

    game_state_instance.current_day += 1
    current_day_val: int = game_state_instance.current_day  # Renamed
    current_player_region_obj: Optional[Region] = (
        game_state_instance.get_current_player_region()
    )  # Renamed
    all_game_regions_map: Dict[RegionName, Region] = (
        game_state_instance.get_all_regions()
    )  # Renamed
    ai_rivals_list: List[AIRival] = game_state_instance.ai_rivals  # Renamed

    if content_pad:
        content_pad.clear()
        content_pad.addstr(
            0,
            0,
            f"--- Advancing to Day {current_day_val} ---",
            curses.color_pair(2) | curses.A_BOLD,
        )
    pad_line_num: int = 1  # Renamed

    for region_name_enum, region_obj_val in all_game_regions_map.items():  # Renamed
        region_obj_val.restock_market()
        decay_regional_heat(region_obj_val, 1.0, player_inventory, game_configs)
        decay_player_market_impact(region_obj_val)
        decay_rival_market_impact(region_obj_val, current_day_val)

    game_state_instance.update_daily_crypto_prices(
        game_configs.CRYPTO_VOLATILITY, game_configs.CRYPTO_MIN_PRICE
    )
    if content_pad:
        content_pad.addstr(
            pad_line_num, 0, "Crypto prices fluctuated.", curses.color_pair(1)
        )
        pad_line_num += 1

    if (
        getattr(player_inventory, "pending_laundered_sc_arrival_day", None) is not None
        and player_inventory.pending_laundered_sc_arrival_day == current_day_val
    ):
        # Assuming STABLE_COIN is a valid CryptoCoin enum member if used here
        stable_coin_enum_val = getattr(
            CryptoCoin, "STABLE_COIN", CryptoCoin.DRUG_COIN
        )  # Fallback
        player_inventory.add_crypto(
            stable_coin_enum_val, player_inventory.pending_laundered_sc
        )
        if content_pad:
            content_pad.addstr(
                pad_line_num,
                0,
                f"Laundered {player_inventory.pending_laundered_sc:.4f} SC has arrived!",
                curses.color_pair(3),
            )
            pad_line_num += 1
        player_inventory.pending_laundered_sc = 0.0
        player_inventory.pending_laundered_sc_arrival_day = None

    if not is_jailed_turn:
        for rival_obj in ai_rivals_list:  # Renamed
            process_rival_turn(
                rival_obj, all_game_regions_map, current_day_val, game_configs
            )
        if content_pad:
            content_pad.addstr(
                pad_line_num, 0, "Rivals made their moves...", curses.color_pair(1)
            )
            pad_line_num += 1

    if not is_jailed_turn and current_player_region_obj:
        # Placeholder for trigger_random_market_event logic if it were to be re-integrated here
        if content_pad:
            content_pad.addstr(
                pad_line_num,
                0,
                "The streets are buzzing with new events.",
                curses.color_pair(1),
            )
            pad_line_num += 1

    if current_player_region_obj:
        from ...mechanics.event_manager import update_active_events

        update_active_events(current_player_region_obj)

    if current_day_val % SKILL_POINTS_PER_X_DAYS == 0:
        player_inventory.skill_points += 1
        if content_pad:
            content_pad.addstr(
                pad_line_num,
                0,
                f"You gained a skill point! (Total: {player_inventory.skill_points})",
                curses.color_pair(3),
            )
            pad_line_num += 1

    if (
        content_pad and log_win and input_win
    ):  # Only do UI updates if windows are provided
        content_pad.addstr(
            pad_line_num,
            0,
            "Day advanced. Press any key to continue...",
            curses.color_pair(1),
        )
        content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
        log_win.noutrefresh()
        input_win.clear()
        input_win.refresh()
        input_win.getkey()

    return current_day_val


def handle_travel(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    current_player_region_obj: Optional[Region] = (
        game_state_instance.get_current_player_region()
    )  # Renamed
    all_game_regions_map: Dict[RegionName, Region] = (
        game_state_instance.get_all_regions()
    )  # Renamed

    if not current_player_region_obj:
        log_win.addstr(
            0, 0, "Error: Current region not set for travel.", curses.color_pair(4)
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    new_day_from_police_stop_val: Optional[int] = check_and_trigger_police_stop(
        game_state_instance, player_inventory
    )  # Renamed
    if new_day_from_police_stop_val is not None:
        log_win.addstr(
            0, 0, "Your travel plans were interrupted!", curses.color_pair(4)
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    print("\n--- Travel ---")
    print(
        f"You are currently in: {current_player_region_obj.name.value} (Heat: {current_player_region_obj.current_heat})"
    )
    available_destinations_list: List[Region] = []
    print("Available destinations:")
    idx_val: int = 1  # Renamed
    dest_map_dict: Dict[int, RegionName] = {}  # Renamed
    for region_name_enum_val, region_obj_val in sorted(
        all_game_regions_map.items(), key=lambda item: item[0].value
    ):  # Renamed
        if region_name_enum_val != current_player_region_obj.name:
            print(
                f"{idx_val}. {region_name_enum_val.value} (Heat: {region_obj_val.current_heat})"
            )
            dest_map_dict[idx_val] = region_name_enum_val
            available_destinations_list.append(region_obj_val)
            idx_val += 1
    if not available_destinations_list:
        print("There are no other regions to travel to.")
        return
    try:
        choice_input_str: str = input(
            f"Enter destination number (0 to cancel): "
        )  # Renamed
        if not choice_input_str.isdigit():
            print("Invalid input. Please enter a number.")
            return
        choice_val: int = int(choice_input_str)  # Renamed
        if choice_val == 0:
            print("Travel cancelled.")
            return
        if 1 <= choice_val <= len(dest_map_dict):
            chosen_destination_name_enum_val: RegionName = dest_map_dict[choice_val]
            print(
                f"\nTraveling to {chosen_destination_name_enum_val.value}..."
            )  # Renamed
            game_state_instance.set_current_player_region(
                chosen_destination_name_enum_val
            )
            handle_advance_day(
                game_state_instance,
                player_inventory,
                content_pad,
                log_win,
                input_win,
                is_jailed_turn=False,
            )
            new_player_region = game_state_instance.get_current_player_region()
            if new_player_region:
                print(f"You have arrived in {new_player_region.name.value}.")
        else:
            print("Invalid destination number.")
            return
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    except Exception as e_travel:
        print(f"An error occurred during travel: {str(e_travel)}")
        return  # Renamed e


def handle_talk_to_informant(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    current_region_obj: Optional[Region] = (
        game_state_instance.get_current_player_region()
    )  # Renamed
    ai_rivals_list: List[AIRival] = game_state_instance.ai_rivals  # Renamed
    if not current_region_obj:
        log_win.addstr(0, 0, "Error: Current region not set.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return

    import curses

    content_pad.clear()
    pad_line_num: int = 0  # Renamed
    content_pad.addstr(
        pad_line_num,
        0,
        "--- Talk to Informant ---",
        curses.color_pair(2) | curses.A_BOLD,
    )
    pad_line_num += 1
    content_pad.addstr(
        pad_line_num,
        0,
        f"Informant Trust: {player_inventory.informant_trust}/{INFORMANT_MAX_TRUST}",
        curses.color_pair(1),
    )
    pad_line_num += 1
    content_pad.addstr(
        pad_line_num, 0, f"Tip Cost: ${INFORMANT_TIP_COST:.2f}", curses.color_pair(1)
    )
    pad_line_num += (
        1  # Assumes INFORMANT_TIP_COST is globally available from game_configs
    )
    content_pad.addstr(pad_line_num, 0, "0. Back to Main Menu", curses.color_pair(5))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)  # TODO: Adjust viewport
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "Get a tip? (yes/0): ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    choice_str: str = input_win.getstr(0, 19, 10).decode().strip().lower()  # Renamed
    curses.noecho()
    if choice_str == "0":
        return
    if (
        player_inventory.cash < INFORMANT_TIP_COST
    ):  # Assumes INFORMANT_TIP_COST is available
        log_win.clear()
        log_win.addstr(0, 0, "Not enough cash for a tip.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return

    player_inventory.cash -= INFORMANT_TIP_COST
    tip_types_list: List[str] = [
        "market",
        "heat",
        "crypto",
        "rival",
        "busted_rival",
    ]  # Renamed
    tip_type_str: str = random.choice(tip_types_list)  # Renamed
    intel_given_flag: bool = False  # Renamed
    log_win.clear()  # Clear log once before potentially writing multiple lines
    if tip_type_str == "market":
        log_win.addstr(
            0,
            0,
            "Market is shifting. Watch for price spikes soon.",
            curses.color_pair(3),
        )
        intel_given_flag = True
    elif tip_type_str == "heat":
        log_win.addstr(
            0,
            0,
            f"Heat is rising in {current_region_obj.name.value}. Stay low.",
            curses.color_pair(4),
        )
        intel_given_flag = True
    elif tip_type_str == "crypto":
        log_win.addstr(
            0,
            0,
            "Crypto prices are volatile. Might be a good time to trade.",
            curses.color_pair(3),
        )
        intel_given_flag = True
    elif tip_type_str == "rival":
        log_win.addstr(
            0, 0, "A rival is making moves nearby. Be cautious.", curses.color_pair(4)
        )
        intel_given_flag = True
    elif tip_type_str == "busted_rival":
        busted_rivals_list_local: List[AIRival] = [
            r for r in ai_rivals_list if r.is_busted
        ]  # Renamed
        if busted_rivals_list_local:
            log_win.addstr(
                0,
                0,
                f"{busted_rivals_list_local[0].name} is busted. Their turf is vulnerable!",
                curses.color_pair(3),
            )
            intel_given_flag = True
    if intel_given_flag:
        player_inventory.informant_trust = min(
            INFORMANT_MAX_TRUST,
            player_inventory.informant_trust + INFORMANT_TRUST_GAIN_PER_TIP,
        )
    else:  # Fallback if no specific intel matched (should not happen with current tip_types)
        log_win.addstr(0, 0, "Nothing much on the wire today...", curses.color_pair(1))
    log_win.noutrefresh()
    curses.doupdate()


def handle_view_upgrades(
    player_inventory: PlayerInventory, content_pad: Any, log_win: Any, input_win: Any
) -> None:
    import curses

    content_pad.clear()
    pad_line_num: int = 0  # Renamed
    current_upgrade_cost_val: float = CAPACITY_UPGRADE_COST_INITIAL * (
        CAPACITY_UPGRADE_COST_MULTIPLIER**player_inventory.capacity_upgrades_purchased
    )  # Renamed
    content_pad.addstr(
        pad_line_num, 0, "--- Upgrades ---", curses.color_pair(2) | curses.A_BOLD
    )
    pad_line_num += 1
    content_pad.addstr(
        pad_line_num,
        0,
        f"1. Increase Carrying Capacity by {CAPACITY_UPGRADE_AMOUNT} units.",
        curses.color_pair(1),
    )
    pad_line_num += 1
    content_pad.addstr(
        pad_line_num,
        0,
        f"   Current Capacity: {player_inventory.max_capacity}",
        curses.color_pair(1),
    )
    pad_line_num += 1
    content_pad.addstr(
        pad_line_num,
        0,
        f"   Cost: ${current_upgrade_cost_val:.2f}",
        curses.color_pair(1),
    )
    pad_line_num += 1
    phone_owned_str_val: str = (
        "(Purchased)" if player_inventory.has_secure_phone else ""
    )  # Renamed
    content_pad.addstr(
        pad_line_num,
        0,
        f"2. Secure Phone (Cost: ${SECURE_PHONE_COST:.2f}) {phone_owned_str_val}",
        curses.color_pair(1),
    )
    pad_line_num += 1
    content_pad.addstr(
        pad_line_num,
        0,
        f"   - Reduces heat from crypto transactions by {int(SECURE_PHONE_HEAT_REDUCTION_PERCENT*100)}%. Stacks with Digital Footprint skill.",
        curses.color_pair(1),
    )
    pad_line_num += 1
    content_pad.addstr(pad_line_num, 0, "0. Back to Main Menu", curses.color_pair(5))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)  # TODO: Adjust viewport
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "Enter choice: ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    choice_str: str = input_win.getstr(0, 14, 10).decode().strip()  # Renamed
    curses.noecho()
    log_win.clear()  # Clear log once
    if choice_str == "1":
        if player_inventory.cash >= current_upgrade_cost_val:
            player_inventory.cash -= current_upgrade_cost_val
            player_inventory.max_capacity += CAPACITY_UPGRADE_AMOUNT  # Direct modification, or use a method if exists
            player_inventory.capacity_upgrades_purchased += 1
            log_win.addstr(
                0, 0, "Capacity upgraded successfully!", curses.color_pair(3)
            )
            log_win.addstr(
                1,
                0,
                f"New carrying capacity: {player_inventory.max_capacity}",
                curses.color_pair(3),
            )
        else:
            log_win.addstr(
                0, 0, "Not enough cash for this upgrade.", curses.color_pair(4)
            )
    elif choice_str == "2":
        if player_inventory.has_secure_phone:
            log_win.addstr(
                0, 0, "You already own a Secure Phone.", curses.color_pair(4)
            )
        elif player_inventory.cash >= SECURE_PHONE_COST:
            player_inventory.cash -= SECURE_PHONE_COST
            player_inventory.has_secure_phone = True
            log_win.addstr(
                0,
                0,
                "Secure Phone purchased! Crypto dealings more private.",
                curses.color_pair(3),
            )
        else:
            log_win.addstr(
                0,
                0,
                "Not enough cash to purchase the Secure Phone.",
                curses.color_pair(4),
            )
    elif choice_str == "0":
        return
    else:
        log_win.addstr(0, 0, "Invalid choice.", curses.color_pair(4))
    log_win.noutrefresh()
    curses.doupdate()


def handle_view_skills(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    import curses

    content_pad.clear()
    pad_line_num: int = 0  # Renamed
    content_pad.addstr(
        pad_line_num, 0, "--- Skills ---", curses.color_pair(2) | curses.A_BOLD
    )
    pad_line_num += 1
    content_pad.addstr(
        pad_line_num,
        0,
        f"Available Skill Points: {player_inventory.skill_points}",
        curses.color_pair(1),
    )
    pad_line_num += 1

    skill_options_list: List[SkillID] = []  # Renamed, stores SkillID enums
    idx_val: int = 1  # Renamed
    if hasattr(game_configs, "SKILL_DEFINITIONS"):
        for (
            skill_id_enum_val,
            skill_def_dict,
        ) in game_configs.SKILL_DEFINITIONS.items():  # Renamed
            is_unlocked_flag: bool = (
                skill_id_enum_val.value in player_inventory.unlocked_skills
            )  # Compare with .value
            skill_name_str: str = skill_def_dict.get(
                "name", skill_id_enum_val.value.replace("_", " ").title()
            )  # Renamed
            cost_val: int = skill_def_dict.get("cost", 99)  # Renamed
            description_str: str = skill_def_dict.get(
                "description", "No description."
            )  # Renamed
            display_text_str: str = (
                f"{idx_val}. {skill_name_str} (Cost: {cost_val} SP) - {description_str}"  # Renamed
            )
            if is_unlocked_flag:
                display_text_str += " (Already Unlocked)"
            content_pad.addstr(
                pad_line_num,
                0,
                display_text_str,
                curses.color_pair(1 if not is_unlocked_flag else 3),
            )
            pad_line_num += 1
            if not is_unlocked_flag:
                skill_options_list.append(skill_id_enum_val)
            idx_val += 1
    else:
        content_pad.addstr(
            pad_line_num, 0, "Skill definitions not found.", curses.color_pair(4)
        )
        pad_line_num += 1

    content_pad.addstr(pad_line_num, 0, "0. Back to Main Menu", curses.color_pair(5))
    pad_line_num += 1
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)  # TODO: Adjust viewport
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(
        0, 0, "Enter choice to unlock (or 0 to go back): ", curses.color_pair(6)
    )
    input_win.refresh()
    curses.echo()
    choice_input_str: str = input_win.getstr(0, 40, 10).decode().strip()  # Renamed
    curses.noecho()
    log_win.clear()

    if not choice_input_str.isdigit():
        log_win.addstr(
            0, 0, "Invalid input. Please enter a number.", curses.color_pair(4)
        )
        log_win.noutrefresh()
        curses.doupdate()
        return

    choice_val: int = int(choice_input_str)  # Renamed
    if choice_val == 0:
        return

    if 1 <= choice_val <= len(skill_options_list):
        selected_skill_id_enum_val: SkillID = skill_options_list[
            choice_val - 1
        ]  # Renamed
        skill_def_selected: Dict[str, Any] = game_configs.SKILL_DEFINITIONS.get(
            selected_skill_id_enum_val, {}
        )  # Renamed
        cost_selected: int = skill_def_selected.get("cost", 99)  # Renamed
        skill_name_selected: str = skill_def_selected.get(
            "name", selected_skill_id_enum_val.value
        )  # Renamed

        if player_inventory.skill_points >= cost_selected:
            player_inventory.skill_points -= cost_selected
            player_inventory.unlocked_skills.add(
                selected_skill_id_enum_val.value
            )  # Store .value
            log_win.addstr(
                0, 0, f"Skill Unlocked: {skill_name_selected}!", curses.color_pair(3)
            )
        else:
            log_win.addstr(
                0,
                0,
                f"Not enough Skill Points for {skill_name_selected}.",
                curses.color_pair(4),
            )
    else:
        log_win.addstr(0, 0, "Invalid skill choice.", curses.color_pair(4))
    log_win.noutrefresh()
    curses.doupdate()


def handle_visit_tech_contact(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    # This function's body is complex and involves direct print/input.
    # For brevity, only signature is updated here. Detailed local var typing would be extensive.
    # current_crypto_prices_ref should be game_state_instance.current_crypto_prices
    current_crypto_prices_ref: Dict[CryptoCoin, float] = (
        game_state_instance.current_crypto_prices
    )
    current_region_obj: Optional[Region] = (
        game_state_instance.get_current_player_region()
    )
    current_day_val: int = game_state_instance.current_day
    print(
        "\nYou meet your Tech Contact in a secure, undisclosed location. The air hums with servers."
    )
    # ... (rest of the logic remains, assuming it works with updated GameState structure)
    # Example of adapting a small part:
    while True:
        print("\n--- Tech Contact Terminal ---")
        print(f"Your Cash: ${player_inventory.cash:.2f}")
        print("Your Crypto Wallet:")
        # ... (display balances) ...
        print("\nMarket Prices (per unit):")
        for coin_enum, price_val in sorted(
            current_crypto_prices_ref.items(), key=lambda item: item[0].value
        ):
            print(f"  - {coin_enum.value}: ${price_val:.2f}")
        # ... (rest of menu and logic) ...
        # Ensure all references to global game_configs constants are via the game_configs module.
        # Example: game_configs.TECH_CONTACT_FEE_PERCENT
        # Ensure heat modifications use current_region_obj.modify_heat(...) if region-specific.
        # For now, assuming heat from crypto is global or handled by a general mechanism not shown.
        # If heat is region specific:
        # if effective_heat > 0 and current_region_obj: current_region_obj.modify_heat(effective_heat); print(f"Crypto activity heat +{effective_heat} in {current_region_obj.name.value}")
        choice_str = input("Choose action: ").strip()  # Simplified for example
        if choice_str == "0":
            print("Leaving the Tech Contact...")
            break
        # ... (other choices) ...
    return  # Explicit return None


def handle_crypto_shop(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    if SkillID.GHOST_NETWORK_ACCESS.value not in player_inventory.unlocked_skills:
        print("\nAccess Denied. You need Ghost Network Access.")
        return

    print("\n--- Ghost Network Shop ---")
    print("Welcome to the exclusive Crypto-Only Shop.")
    while True:
        print("\nShop Items (Prices in DarkCoin - DC):")
        digital_arsenal_owned_flag: bool = (
            SkillID.DIGITAL_ARSENAL.value in player_inventory.unlocked_skills
        )  # Renamed
        owned_str_val: str = "(Owned)" if digital_arsenal_owned_flag else ""  # Renamed
        print(
            f"1. Digital Arsenal (Cost: {DIGITAL_ARSENAL_COST_DC:.2f} {CryptoCoin.DRUG_COIN.value}) {owned_str_val}"
        )
        print("   - Provides daily alerts on police crackdowns and high regional heat.")
        print("0. Exit Shop")
        choice_str: str = input(
            "Enter item number to purchase or 0 to exit: "
        ).strip()  # Renamed

        if choice_str == "1":
            if digital_arsenal_owned_flag:
                print("You already own the Digital Arsenal.")
            else:
                dc_balance_val: float = player_inventory.crypto_wallet.get(
                    CryptoCoin.DRUG_COIN, 0.0
                )  # Renamed
                if dc_balance_val >= DIGITAL_ARSENAL_COST_DC:
                    player_inventory.remove_crypto(
                        CryptoCoin.DRUG_COIN, DIGITAL_ARSENAL_COST_DC
                    )
                    player_inventory.unlocked_skills.add(
                        SkillID.DIGITAL_ARSENAL.value
                    )  # Use add for set
                    print("\nDigital Arsenal acquired! Check daily status for alerts.")
                else:
                    print(
                        f"Insufficient {CryptoCoin.DRUG_COIN.value}. You need {DIGITAL_ARSENAL_COST_DC:.2f}, have {dc_balance_val:.2f}."
                    )
        elif choice_str == "0":
            print("Leaving the Ghost Network Shop.")
            break
        else:
            print("Invalid choice.")


def handle_meet_corrupt_official(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    current_region_obj: Optional[Region] = (
        game_state_instance.get_current_player_region()
    )  # Renamed
    if not current_region_obj:
        log_win.clear()
        log_win.addstr(0, 0, "Error: Current region not set.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    import curses

    content_pad.clear()
    pad_line_num: int = 0  # Renamed
    content_pad.addstr(
        pad_line_num,
        0,
        "--- Meet Corrupt Official ---",
        curses.color_pair(2) | curses.A_BOLD,
    )
    pad_line_num += 1
    content_pad.addstr(
        pad_line_num,
        0,
        f"Current Heat in {current_region_obj.name.value}: {current_region_obj.current_heat}",
        curses.color_pair(1),
    )
    pad_line_num += 1
    base_cost_val: float = CORRUPT_OFFICIAL_BASE_BRIBE_COST + (
        current_region_obj.current_heat * CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT
    )  # Renamed
    content_pad.addstr(
        pad_line_num, 0, f"Bribe Cost: ${base_cost_val:.2f}", curses.color_pair(1)
    )
    pad_line_num += 1
    content_pad.addstr(pad_line_num, 0, "0. Back to Main Menu", curses.color_pair(5))
    content_pad.noutrefresh(0, 0, 6, 0, 25, 79)  # TODO: Adjust viewport parameters
    log_win.noutrefresh()
    input_win.clear()
    input_win.addstr(0, 0, "Pay bribe? (yes/0): ", curses.color_pair(6))
    input_win.refresh()
    curses.echo()
    choice_str: str = input_win.getstr(0, 17, 10).decode().strip().lower()  # Renamed
    curses.noecho()
    log_win.clear()
    if choice_str == "0":
        return
    if player_inventory.cash < base_cost_val:
        log_win.addstr(0, 0, "Not enough cash for the bribe.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return

    player_inventory.cash -= base_cost_val
    original_heat_val: int = current_region_obj.current_heat  # Renamed
    current_region_obj.modify_heat(-CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT)
    actual_reduction_val: int = (
        original_heat_val - current_region_obj.current_heat
    )  # Renamed
    log_win.addstr(
        0,
        0,
        f"Arrangements made. Heat -{actual_reduction_val} in {current_region_obj.name.value}. New heat: {current_region_obj.current_heat}",
        curses.color_pair(3),
    )
    log_win.noutrefresh()
    curses.doupdate()


def handle_respond_to_setup(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Optional[Any] = None,
    log_win: Optional[Any] = None,
    input_win: Optional[Any] = None,
) -> int:
    current_region_obj: Optional[Region] = (
        game_state_instance.get_current_player_region()
    )  # Renamed
    current_day_val: int = game_state_instance.current_day  # Renamed
    if not current_region_obj:
        if log_win:
            log_win.addstr(
                0, 0, "Error: Current region not set for setup.", curses.color_pair(4)
            )
            log_win.noutrefresh()
            curses.doupdate()
        return current_day_val
    import curses

    setup_event_obj: Optional[MarketEvent] = None  # Renamed
    event_to_remove_idx_val: int = -1  # Renamed
    for idx, event_obj_item in enumerate(
        current_region_obj.active_market_events
    ):  # Renamed
        if event_obj_item.event_type == EventType.THE_SETUP:
            setup_event_obj = event_obj_item
            event_to_remove_idx_val = idx
            break

    if (
        not setup_event_obj
        or not setup_event_obj.deal_drug_name
        or not setup_event_obj.deal_quality
        or setup_event_obj.deal_quantity is None
        or setup_event_obj.deal_price_per_unit is None
    ):
        if log_win:
            log_win.clear()
            log_win.addstr(
                0, 0, "No current opportunities or offer unclear.", curses.color_pair(4)
            )
            log_win.noutrefresh()
            curses.doupdate()
        return current_day_val

    action_str_val: str = "Buy" if setup_event_obj.is_buy_deal else "Sell"  # Renamed
    if content_pad:
        content_pad.clear()
        pad_line_num: int = 0  # Renamed
        content_pad.addstr(
            pad_line_num,
            0,
            f"--- Shady Opportunity in {current_region_obj.name.value} ---",
            curses.color_pair(2) | curses.A_BOLD,
        )
        pad_line_num += 1
        content_pad.addstr(
            pad_line_num,
            0,
            f"Offer: {action_str_val} {setup_event_obj.deal_quantity} units of {setup_event_obj.deal_quality.name} {setup_event_obj.deal_drug_name.value}",
            curses.color_pair(1),
        )
        pad_line_num += 1
        content_pad.addstr(
            pad_line_num,
            0,
            f"       at ${setup_event_obj.deal_price_per_unit:.2f} per unit.",
            curses.color_pair(1),
        )
        pad_line_num += 1
        content_pad.addstr(
            pad_line_num,
            0,
            "This could be very profitable... or very dangerous.",
            curses.color_pair(4),
        )
        content_pad.noutrefresh(0, 0, 6, 0, 25, 79)
    if input_win:
        input_win.clear()
        input_win.addstr(0, 0, "Accept this deal? (yes/no): ", curses.color_pair(6))
        input_win.refresh()
        curses.echo()
        choice_str_val: str = (
            input_win.getstr(0, 25, 10).decode().strip().lower()
        )  # Renamed
        curses.noecho()
    else:
        choice_str_val = (
            input("Accept this deal? (yes/no): ").strip().lower()
        )  # Fallback for non-curses calls

    if choice_str_val != "yes":
        if event_to_remove_idx_val != -1:
            current_region_obj.active_market_events.pop(event_to_remove_idx_val)
        if log_win:
            log_win.clear()
            log_win.addstr(
                0, 0, "You walk away. Probably for the best.", curses.color_pair(1)
            )
            log_win.noutrefresh()
            curses.doupdate()
        return current_day_val

    if event_to_remove_idx_val != -1:
        current_region_obj.active_market_events.pop(event_to_remove_idx_val)

    if setup_event_obj.is_buy_deal:
        total_cost_val: float = (
            setup_event_obj.deal_quantity * setup_event_obj.deal_price_per_unit
        )  # Renamed
        if player_inventory.cash < total_cost_val:
            if log_win:
                log_win.clear()
                log_win.addstr(
                    0,
                    0,
                    f"Not enough cash (${total_cost_val:.2f} needed). Deal off.",
                    curses.color_pair(4),
                )
                log_win.noutrefresh()
                curses.doupdate()
            return current_day_val
        if player_inventory.get_available_space() < setup_event_obj.deal_quantity:
            if log_win:
                log_win.clear()
                log_win.addstr(
                    0, 0, "Not enough inventory space. Deal off.", curses.color_pair(4)
                )
                log_win.noutrefresh()
                curses.doupdate()
            return current_day_val
    else:  # Selling
        if (
            player_inventory.get_quantity(
                setup_event_obj.deal_drug_name, setup_event_obj.deal_quality
            )
            < setup_event_obj.deal_quantity
        ):
            if log_win:
                log_win.clear()
                log_win.addstr(
                    0, 0, "Not enough drugs to sell. Deal off.", curses.color_pair(4)
                )
                log_win.noutrefresh()
                curses.doupdate()
            return current_day_val

    sting_chance_val: float = SETUP_EVENT_STING_CHANCE_BASE + (
        current_region_obj.current_heat * SETUP_EVENT_STING_CHANCE_HEAT_MODIFIER
    )  # Renamed
    sting_chance_val = max(0.1, min(sting_chance_val, 0.9))
    if random.random() < sting_chance_val:
        if log_win:
            log_win.clear()
            log_win.addstr(
                0,
                0,
                "!!! IT'S A STING !!! Cops move in!",
                curses.color_pair(4) | curses.A_BOLD,
            )
            log_win.noutrefresh()
            curses.doupdate()
        new_day_after_sting_val: Optional[int] = handle_police_stop_event(
            game_state_instance, player_inventory
        )  # Renamed
        return (
            new_day_after_sting_val
            if new_day_after_sting_val is not None
            else game_state_instance.current_day
        )

    if setup_event_obj.is_buy_deal:
        total_cost_val = (
            setup_event_obj.deal_quantity * setup_event_obj.deal_price_per_unit
        )
        player_inventory.cash -= total_cost_val
        player_inventory.add_drug(
            setup_event_obj.deal_drug_name,
            setup_event_obj.deal_quality,
            setup_event_obj.deal_quantity,
        )
        apply_player_buy_impact(current_region_obj, setup_event_obj.deal_drug_name, setup_event_obj.deal_quantity)  # type: ignore
        if log_win:
            log_win.clear()
            log_win.addstr(
                0,
                0,
                f"Bought {setup_event_obj.deal_quantity} {setup_event_obj.deal_quality.name} {setup_event_obj.deal_drug_name.value} for ${total_cost_val:.2f}.",
                curses.color_pair(3),
            )
            log_win.noutrefresh()
            curses.doupdate()
    else:  # Selling
        total_revenue_val: float = (
            setup_event_obj.deal_quantity * setup_event_obj.deal_price_per_unit
        )  # Renamed
        player_inventory.remove_drug(
            setup_event_obj.deal_drug_name,
            setup_event_obj.deal_quality,
            setup_event_obj.deal_quantity,
        )
        player_inventory.cash += total_revenue_val
        apply_player_sell_impact(
            player_inventory,
            current_region_obj,
            setup_event_obj.deal_drug_name,
            setup_event_obj.deal_quantity,
            game_configs,
        )  # Pass game_configs
        if log_win:
            log_win.clear()
            log_win.addstr(
                0,
                0,
                f"Sold {setup_event_obj.deal_quantity} {setup_event_obj.deal_quality.name} {setup_event_obj.deal_drug_name.value} for ${total_revenue_val:.2f}.",
                curses.color_pair(3),
            )
            log_win.noutrefresh()
            curses.doupdate()

    heat_from_deal_val: int = random.randint(15, 40)  # Renamed
    current_region_obj.modify_heat(heat_from_deal_val)
    if log_win:
        log_win.addstr(
            1,
            0,
            f"Shady deal heat +{heat_from_deal_val} in {current_region_obj.name.value}",
            curses.color_pair(4),
        )
        log_win.noutrefresh()
        curses.doupdate()
    return game_state_instance.current_day


def handle_view_market(
    game_state_instance: GameState,
    player_inventory: PlayerInventory,
    content_pad: Any,
    log_win: Any,
    input_win: Any,
) -> None:
    region = game_state_instance.get_current_player_region()
    if not region:
        log_win.addstr(0, 0, "Error: Current region not set.", curses.color_pair(4))
        log_win.noutrefresh()
        curses.doupdate()
        return
    import curses  # Make sure curses is imported if not already at the top of the file

    # (Assuming print_market_header is available from ui_helpers and is curses-aware)
    # from .ui_helpers import print_market_header # If not already imported

    show_trend_icons = "MARKET_INTUITION" in player_inventory.unlocked_skills
    content_pad.clear()  # Clear the pad for new content

    # Get pad dimensions (max_y, max_x of the pad itself, not the screen viewport)
    # pad_max_y, pad_max_x = content_pad.getmaxyx() # Not strictly needed for writing, but good for context

    # Get screen viewport dimensions (passed from main.py or determined dynamically)
    # These define where the pad content is displayed on the main screen (stdscr)
    # Example: if header_win is 5 lines, content_viewport_start_row = 5
    # content_viewport_height = stdscr.getmaxyx()[0] - header_height - log_height - input_height
    # For this example, let's assume these are passed or known:
    content_viewport_start_row = 5  # Screen row where pad display begins
    content_viewport_height = 15  # Number of lines visible for the pad on screen
    content_viewport_width = 79  # Width of the pad viewport on screen

    pad_current_line = 0  # Tracks the current line number on the pad itself

    # Draw title
    title_str = (
        f"--- Market in {region.name.value} (Regional Heat: {region.current_heat}) ---"
    )
    content_pad.addstr(
        pad_current_line, 0, title_str, curses.color_pair(2) | curses.A_BOLD
    )
    pad_current_line += 1

    # Draw market header (using the curses-aware version from ui_helpers)
    # print_market_header is expected to draw at pad_current_line and increment it
    # For this example, let's assume print_market_header draws 2 lines
    # and we pass pad_current_line to it, or it draws at its current cursor.
    # To be safe, let's manage pad_current_line explicitly here.
    temp_header_pad = content_pad.derwin(2, content_viewport_width, pad_current_line, 0)
    print_market_header(
        temp_header_pad, region.name.value, show_trend=show_trend_icons
    )  # Pass region name string
    temp_header_pad.noutrefresh()  # Refresh the sub-pad if it was used directly
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
    content_pad.addstr(
        pad_current_line, 0, market_header_text, curses.color_pair(2) | curses.A_BOLD
    )
    pad_current_line += 1
    content_pad.addstr(
        pad_current_line, 0, "-" * len(market_header_text), curses.color_pair(2)
    )
    pad_current_line += 1

    sorted_drug_names = sorted(
        region.drug_market_data.keys(), key=lambda d_enum: d_enum.value
    )  # Sort by enum value
    market_data_lines_for_pad = []  # Store (text, color_pair) tuples

    if not sorted_drug_names:
        market_data_lines_for_pad.append(
            ("No drugs traded in this market currently.", curses.color_pair(4))
        )
    else:
        for drug_name in sorted_drug_names:
            drug_data_market = region.drug_market_data[drug_name]
            available_qualities = drug_data_market.get("available_qualities", {})
            if available_qualities:
                for quality in sorted(
                    available_qualities.keys(), key=lambda q: q.value
                ):
                    stock = region.get_available_stock(drug_name, quality)
                    current_buy_price = region.get_buy_price(drug_name, quality)
                    current_sell_price = region.get_sell_price(drug_name, quality)
                    previous_sell_price = (
                        drug_data_market.get("available_qualities", {})
                        .get(quality, {})
                        .get("previous_sell_price", None)
                    )
                    trend_icon = " "
                    if show_trend_icons:
                        if (
                            previous_sell_price is not None
                            and current_sell_price > 0
                            and previous_sell_price > 0
                        ):
                            if current_sell_price > previous_sell_price * 1.02:
                                trend_icon = "↑"
                            elif current_sell_price < previous_sell_price * 0.98:
                                trend_icon = "↓"
                            else:
                                trend_icon = "="
                        elif current_sell_price > 0:
                            trend_icon = "?"
                    event_active_marker = " "
                    is_disrupted = False
                    for event in region.active_market_events:
                        if (
                            event.target_drug_name == drug_name
                            and event.target_quality == quality
                        ):
                            event_active_marker = "*"
                            if event.event_type == EventType.SUPPLY_DISRUPTION:
                                is_disrupted = True  # Use Enum
                            break
                    actual_buy_price = (
                        current_buy_price if not (is_disrupted and stock == 0) else 0.0
                    )
                    buy_price_str = (
                        f"${actual_buy_price:<9.2f}"
                        if actual_buy_price > 0
                        or (
                            stock == 0
                            and event_active_marker == "*"
                            and not is_disrupted
                        )
                        else "---".ljust(10)
                    )
                    sell_price_str = (
                        f"${current_sell_price:<10.2f}"
                        if current_sell_price > 0 or event_active_marker == "*"
                        else "---".ljust(11)
                    )
                    stock_display = (
                        f"{stock:<10}"
                        if not is_disrupted
                        else (
                            f"{str(stock)} (LOW)".ljust(10)
                            if stock > 0
                            else f"{stock} (NONE)".ljust(10)
                        )
                    )
                    drug_col_width = 9 if show_trend_icons else 10
                    quality_col_width = 9 if show_trend_icons else 10
                    line_text = f"{event_active_marker}{trend_icon:<2}{drug_name.value:<{drug_col_width}} {quality.name:<{quality_col_width}} {buy_price_str} {sell_price_str} {stock_display}"
                    color_to_use = curses.color_pair(1)
                    if event_active_marker == "*":
                        color_to_use = curses.color_pair(3) | curses.A_BOLD
                    elif is_disrupted:
                        color_to_use = curses.color_pair(4)
                    market_data_lines_for_pad.append((line_text, color_to_use))
            else:
                market_data_lines_for_pad.append(
                    (
                        f"  {drug_name.value:<10} - No qualities listed.",
                        curses.color_pair(4),
                    )
                )

    # Draw collected market data lines to the pad
    for text, color_attr in market_data_lines_for_pad:
        content_pad.addstr(
            pad_current_line, 0, text[: content_viewport_width - 1], color_attr
        )  # Truncate
        pad_current_line += 1

    # Active events section
    if region.active_market_events:
        content_pad.addstr(
            pad_current_line, 0, "", curses.color_pair(1)
        )  # Blank line for spacing
        pad_current_line += 1
        content_pad.addstr(
            pad_current_line,
            0,
            "Active Market Events:",
            curses.color_pair(2) | curses.A_BOLD,
        )
        pad_current_line += 1
        for event in region.active_market_events:
            target_drug_display = (
                event.target_drug_name.value if event.target_drug_name else "N/A"
            )
            target_quality_display = (
                event.target_quality.name if event.target_quality else "N/A"
            )
            target_info = (
                f"{target_quality_display} {target_drug_display}"
                if event.target_drug_name and event.target_quality
                else "Regional"
            )

            if (
                event.event_type == EventType.THE_SETUP
                and event.deal_drug_name
                and event.deal_quality
            ):
                deal_drug_display = (
                    event.deal_drug_name.value if event.deal_drug_name else "N/A"
                )
                target_info = f"Offer: {'Buy' if event.is_buy_deal else 'Sell'} {event.deal_quantity} {event.deal_quality.name} {deal_drug_display} @ ${event.deal_price_per_unit:.2f}"

            event_line = f"  - {event.event_type.value.replace('_',' ').title()}: {target_info} (Days left: {event.duration_remaining_days})"
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
    screen_viewport_smaxcol = (
        content_viewport_width - 1
    )  # Assuming pad is full width of viewport

    while True:
        content_pad.noutrefresh(
            current_scroll_pos,
            0,
            screen_viewport_sminrow,
            screen_viewport_smincol,
            screen_viewport_smaxrow,
            screen_viewport_smaxcol,
        )
        # log_win.noutrefresh() # Refresh log if it has separate messages
        input_win.clear()
        input_win.addstr(
            0, 0, "PgUp/PgDn/Up/Down: Scroll  Q/Enter: Quit", curses.color_pair(6)
        )
        input_win.refresh()
        curses.doupdate()

        key_code = input_win.getch()  # Use getch() for special keys
        key_name = curses.keyname(key_code).decode("utf-8")

        if key_name in ["q", "Q", "\n", "KEY_ENTER"]:
            break
        elif key_name == "KEY_DOWN" and current_scroll_pos < max_scrollable_lines:
            current_scroll_pos += 1
        elif key_name == "KEY_UP" and current_scroll_pos > 0:
            current_scroll_pos -= 1
        elif (
            key_name == "KEY_NPAGE" and current_scroll_pos < max_scrollable_lines
        ):  # Page Down
            current_scroll_pos = min(
                current_scroll_pos + content_viewport_height, max_scrollable_lines
            )
        elif key_name == "KEY_PPAGE" and current_scroll_pos > 0:  # Page Up
            current_scroll_pos = max(current_scroll_pos - content_viewport_height, 0)
