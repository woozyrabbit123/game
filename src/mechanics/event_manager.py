import random
import math # For math.floor
from typing import List, Optional, Callable, Any, Union
from enum import Enum # Added Enum for isinstance checks

from ..core.region import Region
from ..core.market_event import MarketEvent
from ..core.enums import DrugQuality, DrugName, EventType, SkillID
from ..core.player_inventory import PlayerInventory
from ..core.ai_rival import AIRival
# It's better to import GameState if it's going to be used as a type hint
# from ..game_state import GameState # Placeholder if needed
from .. import game_configs


def _create_and_add_demand_spike(region: Region, current_day: int):
    potential_targets = []
    # drug_name from region.drug_market_data.items() is already DrugName enum
    for drug_name_enum, drug_data in region.drug_market_data.items():
        if drug_data.get("tier", 0) in [2, 3]:
            for quality_key in drug_data.get("available_qualities", {}).keys():
                potential_targets.append((drug_name_enum, quality_key))
    if not potential_targets:
        return

    target_drug_name_enum, target_quality = random.choice(potential_targets)
    for ev in region.active_market_events:
        # Assuming ev.target_drug_name is already Optional[DrugName] from previous refactor
        if ev.target_drug_name == target_drug_name_enum and \
           ev.target_quality == target_quality and \
           ev.event_type == EventType.DEMAND_SPIKE: # Use EventType
            return

    event = MarketEvent(
        event_type=EventType.DEMAND_SPIKE, # Use EventType
        target_drug_name=target_drug_name_enum, # Pass DrugName enum directly
        target_quality=target_quality,
        sell_price_multiplier=random.uniform(1.2, 1.8),
        buy_price_multiplier=random.uniform(1.0, 1.3),
        duration_remaining_days=random.randint(2, 4),
        start_day=current_day
    )
    region.active_market_events.append(event)
    # Use .value for messages if target_drug_name_enum is an enum
    drug_name_str = target_drug_name_enum.value if isinstance(target_drug_name_enum, DrugName) else target_drug_name_enum
    region_name_str = region.name.value if isinstance(region.name, Enum) else region.name # Assuming region.name could be RegionName enum
    print(f"\nMarket Buzz: Demand for {target_quality.name} {drug_name_str} is surging in {region_name_str} for {event.duration_remaining_days} days!")


def _create_and_add_supply_disruption(
    region: Region,
    current_day: int,
    player_heat: int, # From 'main' branch
    game_configs: Any,
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None]
):
    potential_targets = []
    # drug_name_enum from region.drug_market_data.items() is already DrugName enum
    for drug_name_enum, drug_data in region.drug_market_data.items():
        if drug_data.get("tier", 0) in [2, 3]:
            for quality_key in drug_data.get("available_qualities", {}).keys():
                if region.get_available_stock(drug_name_enum, quality_key, player_heat) > 0:
                    potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
        add_to_log_callback(f"SupplyDisruption: No potential (Tier 2/3) drug targets in {region_name_str} for event.")
        return

    target_drug_name_enum, target_quality_enum = random.choice(potential_targets)

    for ev in region.active_market_events:
        if ev.event_type == EventType.SUPPLY_DISRUPTION and \
           ev.target_drug_name == target_drug_name_enum and \
           ev.target_quality == target_quality_enum:
            drug_name_str = target_drug_name_enum.value if isinstance(target_drug_name_enum, DrugName) else target_drug_name_enum
            region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
            add_to_log_callback(f"SupplyDisruption: Event already active for {drug_name_str} ({target_quality_enum.name}) in {region_name_str}.")
            return

    duration = game_configs.SUPPLY_DISRUPTION_EVENT_DURATION_DAYS
    reduction_factor = 1.0 - game_configs.SUPPLY_DISRUPTION_STOCK_REDUCTION_PERCENT
    min_stock = game_configs.MIN_STOCK_AFTER_DISRUPTION

    event = MarketEvent(
        event_type=EventType.SUPPLY_DISRUPTION, # Use EventType
        target_drug_name=target_drug_name_enum, # Pass DrugName enum directly
        target_quality=target_quality_enum,
        sell_price_multiplier=1.0, # Not used directly, effect applied via stock_reduction_factor
        buy_price_multiplier=1.0, # Not used directly
        duration_remaining_days=duration,
        start_day=current_day,
        stock_reduction_factor=reduction_factor,
        min_stock_after_event=min_stock
    )
    region.active_market_events.append(event)

    msg = f"Supply Alert! {target_drug_name_enum.value} ({target_quality_enum.name}) in {region.name.value} is now scarce due to a supply chain disruption for {duration} days!"
    show_event_message_callback(msg)
    add_to_log_callback(msg)


def _create_and_add_police_crackdown(region: Region, current_day: int):
    for ev in region.active_market_events:
        if ev.event_type == EventType.POLICE_CRACKDOWN: # Use EventType
            return

    duration = random.randint(2, 4)
    heat_amount = random.randint(10, 30)
    event = MarketEvent(
        event_type=EventType.POLICE_CRACKDOWN, # Use EventType
        target_drug_name=None,
        target_quality=None,
        sell_price_multiplier=1.0, # No direct price effect from this event type
        buy_price_multiplier=1.0, # No direct price effect from this event type
        duration_remaining_days=duration,
        start_day=current_day,
        heat_increase_amount=heat_amount
    )
    region.active_market_events.append(event)
    region.modify_heat(heat_amount)
    region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
    print(f"\nPolice Alert: Increased police activity and crackdowns reported in {region_name_str} for {duration} days! (Heat +{heat_amount})")


def _create_and_add_cheap_stash(region: Region, current_day: int): # Renamed from _create_and_add_cheap_stash_opportunity in subtask
    potential_targets = []
    # drug_name_enum from region.drug_market_data.items() is already DrugName enum
    for drug_name_enum, drug_data in region.drug_market_data.items():
        if drug_data.get("tier", 0) in [1, 2]:
            for quality_key in drug_data.get("available_qualities", {}).keys():
                potential_targets.append((drug_name_enum, quality_key))
    if not potential_targets:
        return

    # Parameter name changed to deal_drug_name in subtask for CHEAP_STASH,
    # but CHEAP_STASH is a market condition for a *target* drug, not a player *deal* like THE_SETUP.
    # So, I'll keep it as target_drug_name_enum here.
    target_drug_name_enum, target_quality = random.choice(potential_targets)
    for ev in region.active_market_events:
        if ev.target_drug_name == target_drug_name_enum and \
           ev.target_quality == target_quality and \
           ev.event_type == EventType.CHEAP_STASH: # Use EventType
            return
    
    event = MarketEvent(
        event_type=EventType.CHEAP_STASH, # Use EventType
        target_drug_name=target_drug_name_enum, # Pass DrugName enum
        target_quality=target_quality,
        sell_price_multiplier=1.0, # CHEAP_STASH primarily affects buy price for player
        buy_price_multiplier=random.uniform(0.6, 0.8),
        duration_remaining_days=random.randint(1, 2),
        start_day=current_day,
        temporary_stock_increase=random.randint(50, 150)
    )
    region.active_market_events.append(event)
    drug_name_str = target_drug_name_enum.value if isinstance(target_drug_name_enum, DrugName) else target_drug_name_enum
    region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
    print(f"\nMarket Whisper: Heard about a cheap stash of {target_quality.name} {drug_name_str} in {region_name_str}! Available for {event.duration_remaining_days} day(s). (Discounted buy price, extra stock)")


def _create_and_add_the_setup(region: Region, current_day: int, player_inventory: PlayerInventory):
    for ev in region.active_market_events:
        if ev.event_type == EventType.THE_SETUP: # Use EventType
            return

    is_buy_deal = random.choice([True, False])
    possible_deal_drugs = [
        (drug_name_enum, data["tier"]) # drug_name_enum is already DrugName
        for drug_name_enum, data in region.drug_market_data.items()
        if data["tier"] in [2, 3] and data.get("available_qualities")
    ]
    if not possible_deal_drugs:
        return

    deal_drug_name_enum, tier = random.choice(possible_deal_drugs)
    # deal_drug_name_enum is already DrugName enum
    if not region.drug_market_data[deal_drug_name_enum].get("available_qualities"):
        return

    deal_quality = random.choice(list(region.drug_market_data[deal_drug_name_enum]["available_qualities"].keys()))
    deal_quantity = random.randint(20, 100)
    base_buy_price = region.drug_market_data[deal_drug_name_enum]["base_buy_price"]
    base_sell_price = region.drug_market_data[deal_drug_name_enum]["base_sell_price"]

    from ..core.drug import Drug # Corrected import path
    # Pass .value of enum if Drug constructor expects string
    temp_drug_for_mult = Drug(deal_drug_name_enum.value, tier, base_buy_price, base_sell_price, deal_quality)
    quality_mult_buy = temp_drug_for_mult.get_quality_multiplier("buy")
    quality_mult_sell = temp_drug_for_mult.get_quality_multiplier("sell")
    
    if is_buy_deal:
        deal_price_per_unit = base_buy_price * quality_mult_buy * random.uniform(0.2, 0.4)
        # Check player cash against potential deal cost
        if player_inventory.cash < deal_price_per_unit * (deal_quantity / 2): # Heuristic: player might not afford half
            return
    else: # Sell deal
        deal_price_per_unit = base_sell_price * quality_mult_sell * random.uniform(2.0, 3.5)
        # Check if player has at least some of the drug to sell (even if not the full quantity)
        has_any_of_drug = False
        # player_inventory.items keys should be DrugName enums if fully refactored
        for qual_check in player_inventory.items.get(deal_drug_name_enum, {}):
            if player_inventory.get_quantity(deal_drug_name_enum, qual_check) > 0:
                has_any_of_drug = True
                break
        if not has_any_of_drug and player_inventory.get_quantity(deal_drug_name_enum, deal_quality) < deal_quantity / 4: # Heuristic
            return

    deal_price_per_unit = round(max(1.0, deal_price_per_unit), 2)
    event = MarketEvent(
        event_type=EventType.THE_SETUP, # Use EventType
        target_drug_name=None, # THE_SETUP is a deal, not a market-wide effect on a target drug
        target_quality=None,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
        duration_remaining_days=1, # Usually a one-time opportunity
        start_day=current_day,
        deal_drug_name=deal_drug_name_enum, # Pass DrugName enum
        deal_quality=deal_quality,
        deal_quantity=deal_quantity,
        deal_price_per_unit=deal_price_per_unit,
        is_buy_deal=is_buy_deal
    )
    region.active_market_events.append(event)
    region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
    print(f"\nMarket Murmurs: A shady character in {region_name_str} wants to make you an offer... It sounds too good to be true. (Check 'Respond to Opportunities')")


def _create_and_add_rival_busted(region: Region, current_day: int, ai_rivals: List[AIRival]):
    eligible_rivals = [r for r in ai_rivals if not r.is_busted]
    if not eligible_rivals:
        return

    busted_rival = random.choice(eligible_rivals)
    
    for ev in region.active_market_events:
        if ev.event_type == EventType.RIVAL_BUSTED and ev.target_drug_name == busted_rival.name: # target_drug_name for RIVAL_BUSTED is string (rival's name)
            return

    busted_rival.is_busted = True
    busted_rival.busted_days_remaining = random.randint(5, 10)

    event = MarketEvent(
        event_type=EventType.RIVAL_BUSTED, # Use EventType
        target_drug_name=busted_rival.name, # This remains a string (rival's name)
        target_quality=None, # No specific drug quality for this event type
        sell_price_multiplier=1.0, # No direct price effect
        buy_price_multiplier=1.0,  # No direct price effect
        duration_remaining_days=busted_rival.busted_days_remaining,
        start_day=current_day
    )
    # This event is informational; add it to the current region's event list for player visibility.
    # If it should be global news, it might need to be handled differently or added to all regions.
    # For now, player hears about it if it happens to be "announced" in their current region.
    region.active_market_events.append(event) # Add to current region for notification
    print(f"\nMajor News: Notorious dealer {busted_rival.name} has been BUSTED by authorities! They'll be out of action for about {busted_rival.busted_days_remaining} days.")


def _create_and_add_drug_market_crash(
    region: Region,
    current_day: int,
    game_configs: Any, # For accessing DRUG_CRASH constants
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None]
):
    potential_targets = []
    # drug_name_enum from region.drug_market_data.items() is already DrugName enum
    for drug_name_enum, drug_data in region.drug_market_data.items():
        for quality_key in drug_data.get("available_qualities", {}).keys():
            # player_heat for get_available_stock is 0 as it's not relevant for crash trigger
            if region.get_available_stock(drug_name_enum, quality_key, 0) > 0:
                potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
        add_to_log_callback(f"DrugMarketCrash: No potential drug targets in {region_name_str} for event.")
        return

    target_drug_name_enum, target_quality_enum = random.choice(potential_targets)

    for ev in region.active_market_events:
        if ev.event_type == EventType.DRUG_MARKET_CRASH and \
           ev.target_drug_name == target_drug_name_enum and \
           ev.target_quality == target_quality_enum:
            # target_drug_name_enum is already DrugName, so .value for string representation
            drug_name_str = target_drug_name_enum.value
            region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
            add_to_log_callback(f"DrugMarketCrash: Event already active for {drug_name_str} ({target_quality_enum.name}) in {region_name_str}.")
            return

    duration = game_configs.DRUG_CRASH_EVENT_DURATION_DAYS
    reduction_percent = game_configs.DRUG_CRASH_PRICE_REDUCTION_PERCENT
    min_price = game_configs.MINIMUM_DRUG_PRICE

    event = MarketEvent(
        event_type=EventType.DRUG_MARKET_CRASH, # Use EventType
        target_drug_name=target_drug_name_enum, # Pass DrugName enum
        target_quality=target_quality_enum,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
        duration_remaining_days=duration,
        start_day=current_day,
        price_reduction_factor=(1.0 - reduction_percent),
        minimum_price_after_crash=min_price
    )
    region.active_market_events.append(event)

    # target_drug_name_enum is already DrugName, use .value for string representation
    drug_name_str = target_drug_name_enum.value
    region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
    msg = f"Market Crash! Prices for {drug_name_str} ({target_quality_enum.name}) have plummeted in {region_name_str} for {duration} days!"
    show_event_message_callback(msg)
    add_to_log_callback(msg)


def _create_and_add_black_market_event(region: Region, current_day: int, player_inventory: PlayerInventory, show_event_message_callback: Optional[Callable[[str], None]] = None):
    potential_targets = []
    # drug_name_enum is already DrugName from region.drug_market_data
    for drug_name_enum, drug_data in region.drug_market_data.items():
        for quality_key in drug_data.get("available_qualities", {}).keys():
            if isinstance(quality_key, DrugQuality): # Ensure quality_key is DrugQuality enum
                potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        return

    chosen_drug_name_enum, chosen_quality = random.choice(potential_targets)

    is_specific_event_active = any(
        ev.event_type == EventType.BLACK_MARKET_OPPORTUNITY and # Use EventType
        ev.target_drug_name == chosen_drug_name_enum and # Compare DrugName enum directly
        ev.target_quality == chosen_quality
        for ev in region.active_market_events
    )
    if is_specific_event_active:
        return

    quantity = random.randint(game_configs.BLACK_MARKET_MIN_QUANTITY, game_configs.BLACK_MARKET_MAX_QUANTITY)

    event = MarketEvent(
        event_type=EventType.BLACK_MARKET_OPPORTUNITY, # Use EventType
        target_drug_name=chosen_drug_name_enum, # Pass DrugName enum
        target_quality=chosen_quality,
        buy_price_multiplier=(1.0 - game_configs.BLACK_MARKET_PRICE_REDUCTION_PERCENT),
        sell_price_multiplier=1.0,
        duration_remaining_days=game_configs.BLACK_MARKET_EVENT_DURATION_DAYS,
        start_day=current_day,
        black_market_quantity_available=quantity
    )
    region.active_market_events.append(event)

    # chosen_drug_name_enum is DrugName, use .value for string
    drug_name_str = chosen_drug_name_enum.value
    region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
    log_message = (f"Black Market Alert! {drug_name_str} ({chosen_quality.name}) in {region_name_str} "
                   f"available at {game_configs.BLACK_MARKET_PRICE_REDUCTION_PERCENT*100:.0f}% discount. "
                   f"Qty: {quantity}, for {game_configs.BLACK_MARKET_EVENT_DURATION_DAYS} day(s). "
                   f"Effective Buy Price Multiplier: {event.buy_price_multiplier:.2f}")

    if show_event_message_callback:
         show_event_message_callback(log_message)

    return log_message


def trigger_random_market_event(
    region: Region,
    current_day: int,
    player_inventory: PlayerInventory, # Assuming PlayerInventory provides .heat for some event creations
    ai_rivals: List[AIRival],
    show_event_message_callback: Callable[[str], None],
    game_configs_data: Any,
    add_to_log_callback: Callable[[str], None]
) -> Optional[str]:

    # Independent chance for Black Market event
    # We want this to potentially happen even if a black market event also occurs,
    # so we don't return immediately after black market if we add mugging.
    # Let's store the result of black market and then check mugging.

    black_market_message = None
    if random.random() < game_configs_data.BLACK_MARKET_CHANCE:
        black_market_message = _create_and_add_black_market_event(region, current_day, player_inventory, show_event_message_callback)

    # Independent chance for Mugging Event
    mugging_occurred = False
    if random.random() < game_configs_data.MUGGING_EVENT_CHANCE:
        # Pass necessary arguments. Assuming player_inventory.heat is available if needed by future mugging logic.
        # For now, _handle_mugging_event doesn't use player_inventory.heat
        mugging_occurred = _handle_mugging_event(player_inventory, region, game_configs_data, show_event_message_callback, add_to_log_callback)

    # Independent chance for Forced Fire Sale Event
    forced_sale_occurred = False
    if random.random() < game_configs_data.FORCED_FIRE_SALE_CHANCE:
        forced_sale_occurred = _handle_forced_fire_sale_event(
            player_inventory,
            region,
            game_configs_data,
            show_event_message_callback,
            add_to_log_callback
        )
        # This event also messages independently. No specific return value needed here
        # unless it should override other messages, which is not the case for now.

    # The black_market_message return should be the last thing before falling through to standard market events or default return
    if black_market_message:
        return black_market_message

    # Standard market events (original logic)
    if random.random() < game_configs_data.EVENT_TRIGGER_CHANCE:
        # ... (weighted event selection and execution logic) ...
        # This block should remain the same as in the previous step
        event_options_map = {
            EventType.DEMAND_SPIKE: (_create_and_add_demand_spike, 3),
            EventType.SUPPLY_DISRUPTION: (_create_and_add_supply_disruption, 2),
            EventType.POLICE_CRACKDOWN: (_create_and_add_police_crackdown, 1),
            EventType.CHEAP_STASH: (_create_and_add_cheap_stash, 2),
            EventType.THE_SETUP: (_create_and_add_the_setup, 1),
            EventType.RIVAL_BUSTED: (_create_and_add_rival_busted, 1),
            EventType.DRUG_MARKET_CRASH: (_create_and_add_drug_market_crash, 1)
            # Add EventType.FORCED_FIRE_SALE here with its creation function and weight
        }
        
        weighted_event_list = []
        for event_type_enum, (_, weight) in event_options_map.items():
            weighted_event_list.extend([event_type_enum] * weight)

        if not weighted_event_list:
            return None

        chosen_event_type_enum = random.choice(weighted_event_list)
        creation_func, _ = event_options_map[chosen_event_type_enum]

        # Call the chosen creation function
        # Some functions require more args than others, this needs careful handling
        # or a more generic signature for creation functions.
        # For now, specific calls based on type:
        if chosen_event_type_enum == EventType.DEMAND_SPIKE:
            creation_func(region, current_day)
        elif chosen_event_type_enum == EventType.SUPPLY_DISRUPTION:
            # Assuming player_inventory has 'heat' attribute. If not, this needs adjustment or mock.
            # For now, let's assume player_inventory.heat exists.
            player_heat = getattr(player_inventory, 'heat', 0) # Safely get heat
            creation_func(region, current_day, player_heat, game_configs_data, show_event_message_callback, add_to_log_callback)
        elif chosen_event_type_enum == EventType.POLICE_CRACKDOWN:
            creation_func(region, current_day)
        elif chosen_event_type_enum == EventType.CHEAP_STASH:
            creation_func(region, current_day)
        elif chosen_event_type_enum == EventType.THE_SETUP:
            creation_func(region, current_day, player_inventory)
        elif chosen_event_type_enum == EventType.RIVAL_BUSTED:
            creation_func(region, current_day, ai_rivals)
        elif chosen_event_type_enum == EventType.DRUG_MARKET_CRASH:
            creation_func(region, current_day, game_configs_data, show_event_message_callback, add_to_log_callback)
        # else:
            # add_to_log_callback(f"EventManager: Unhandled event type chosen: {chosen_event_type_enum.value}")
        return None # Event creation functions handle their own prints/messages
    return None


def update_active_events(region: Region):
    new_active_events = []
    for event in list(region.active_market_events): # Iterate over a copy
        event.duration_remaining_days -= 1
        is_expired = False
        expiry_reason = "Duration ended"

        if event.duration_remaining_days <= 0:
            is_expired = True

        current_event_type = event.event_type # Should be EventType enum
        if not isinstance(current_event_type, EventType): # Safety check if somehow it's string
             try: current_event_type = EventType(str(current_event_type))
             except ValueError: pass # Keep as string if not valid EventType

        if current_event_type == EventType.BLACK_MARKET_OPPORTUNITY:
            if hasattr(event, 'black_market_quantity_available') and event.black_market_quantity_available <= 0:
                if not is_expired: expiry_reason = "Stock depleted"
                is_expired = True

        if not is_expired:
            new_active_events.append(event)
        else:
            subject_name = ""
            # Ensure enums are converted to .value for display strings
            deal_drug_str = event.deal_drug_name.value if event.deal_drug_name else None
            target_drug_str = event.target_drug_name.value if event.target_drug_name else None

            if event.deal_drug_name and event.deal_quality and current_event_type == EventType.THE_SETUP:
                subject_name = f"{event.deal_quality.name} {deal_drug_str} deal"
            elif event.target_drug_name and event.target_quality:
                 subject_name = f"{event.target_quality.name} {target_drug_str}".strip()
            elif current_event_type == EventType.RIVAL_BUSTED and event.target_drug_name: # Rival name is string
                subject_name = str(event.target_drug_name)

            region_name_display = region.name.value if isinstance(region.name, Enum) else region.name
            log_base = f"\nMarket Update in {region_name_display}: "
            event_type_display = current_event_type.value if isinstance(current_event_type, EventType) else str(current_event_type)

            message_map = {
                EventType.DEMAND_SPIKE: f"The demand spike for {subject_name} has cooled off ({expiry_reason}).",
                EventType.SUPPLY_DISRUPTION: f"The supply chain disruption for {subject_name} has ended. Availability should return to normal. ({expiry_reason}).",
                EventType.POLICE_CRACKDOWN: f"The increased police scrutiny seems to have subsided ({expiry_reason}).",
                EventType.CHEAP_STASH: f"The cheap stash of {subject_name} is gone ({expiry_reason}).",
                EventType.THE_SETUP: f"The shady offer regarding {subject_name} has vanished ({expiry_reason}).",
                EventType.RIVAL_BUSTED: f"Looks like {subject_name} is back on the streets ({expiry_reason}).",
                EventType.DRUG_MARKET_CRASH: f"The market for {subject_name} has recovered from the crash ({expiry_reason}).",
                EventType.BLACK_MARKET_OPPORTUNITY: f"The black market opportunity for {subject_name} has ended ({expiry_reason})."
            }

            default_message = f"The event concerning {subject_name if subject_name else 'a ' + event_type_display} has ended ({expiry_reason})."
            print(log_base + message_map.get(current_event_type, default_message))

    region.active_market_events = new_active_events


# Placeholder for missing function - TODO: Implement actual police stop logic
def check_and_trigger_police_stop(region: 'Region', player_inventory: 'PlayerInventory', game_state: 'Any') -> bool:
    """
    Placeholder for police stop logic.
    Currently does nothing and always returns False (no event triggered).
    """
    # from ..core.region import Region # Avoid circular if Region is already imported
    # from ..core.player_inventory import PlayerInventory # Avoid circular
    # print(f"DEBUG: check_and_trigger_police_stop called for region {region.name if hasattr(region, 'name') else 'Unknown'}, player has {player_inventory.cash if hasattr(player_inventory, 'cash') else 'Unknown'} cash.")
    # Actual logic for determining if a police stop occurs would go here.
    # This would involve checking region heat, player status, game configs, etc.
    return False # Indicates no police stop event was triggered


def _handle_mugging_event(
    player_inventory: PlayerInventory,
    region: Region,
    game_configs_data: Any, # To access MUGGING_EVENT_CHANCE if needed here, or just rely on the caller
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None] # For logging
) -> bool:
    """
    Handles the logic for a mugging event.
    Player loses a percentage of their cash.
    """
    if player_inventory.cash <= 0: # Can't mug someone with no cash
        return False

    # Define percentage of cash lost (e.g., 10-25%)
    percentage_lost = random.uniform(0.10, 0.25)
    cash_lost = math.floor(player_inventory.cash * percentage_lost)

    if cash_lost <= 0: # If percentage is too small on low cash amounts
        return False

    player_inventory.cash -= cash_lost

    region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
    message = f"Street Danger! You were mugged in {region_name_str} and lost ${cash_lost:,.0f}!"

    show_event_message_callback(message)
    add_to_log_callback(f"Mugging Event: Player lost ${cash_lost:,.0f} in {region_name_str}. Player cash now: ${player_inventory.cash:,.0f}")

    # Create a short-lived event for event log if desired, or just rely on text log
    # For now, no MarketEvent object is created for mugging as it's immediate.
    return True


def _handle_forced_fire_sale_event(
    player_inventory: PlayerInventory,
    region: Region,
    game_configs_data: Any,
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None]
) -> bool:
    """
    Handles the logic for a Forced Fire Sale event.
    Player is forced to sell a portion of a random drug stash at a penalty.
    """
    eligible_drugs = []
    # player_inventory.items is Dict[DrugName, Dict[DrugQuality, int]]
    for drug_name_enum, qualities in player_inventory.items.items(): # Changed player_inventory.drugs to player_inventory.items
        for quality_enum, quantity in qualities.items():
            if quantity > 0:
                eligible_drugs.append({'name': drug_name_enum, 'quality': quality_enum, 'quantity': quantity})

    if not eligible_drugs:
        add_to_log_callback("ForcedFireSale Event: Player has no drugs to sell. Event fizzled.")
        return False

    selected_drug_info = random.choice(eligible_drugs)
    drug_name = selected_drug_info['name'] # This is DrugName enum
    drug_quality = selected_drug_info['quality'] # This is DrugQuality enum
    player_has_quantity = selected_drug_info['quantity']

    quantity_to_sell = math.ceil(player_has_quantity * game_configs_data.FORCED_FIRE_SALE_QUANTITY_PERCENT)
    quantity_to_sell = max(1, int(quantity_to_sell)) # Ensure at least 1 unit is considered if percentage is too low but > 0
    quantity_to_sell = min(quantity_to_sell, player_has_quantity) # Cannot sell more than player has

    if quantity_to_sell == 0 : # Should not happen if max(1, ..) but as a safe guard
         add_to_log_callback(f"ForcedFireSale Event: Calculated quantity to sell for {drug_name.value} ({drug_quality.name}) is zero. Event fizzled.")
         return False


    normal_sell_price = region.get_sell_price(drug_name, drug_quality)
    if normal_sell_price <= 0: # Cannot sell if market price is zero or less (e.g. drug not sold in region)
        add_to_log_callback(f"ForcedFireSale Event: Normal sell price for {drug_name.value} ({drug_quality.name}) in {region.name.value} is {normal_sell_price}. Event fizzled.")
        return False

    fire_sale_price = normal_sell_price * (1 - game_configs_data.FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT)
    fire_sale_price = round(max(0.01, fire_sale_price), 2) # Ensure price is not negative or zero, min 1 cent

    calculated_cash_gain = quantity_to_sell * fire_sale_price

    # Ensure minimum cash gain if the sale proceeds and is positive
    final_cash_gain = calculated_cash_gain
    if calculated_cash_gain > 0: # Only apply min gain if the sale would actually yield something
        final_cash_gain = max(calculated_cash_gain, game_configs_data.FORCED_FIRE_SALE_MIN_CASH_GAIN)

    final_cash_gain = round(final_cash_gain, 2)

    if final_cash_gain <= 0 and calculated_cash_gain <=0 : # If even with min gain, it's not profitable or results in zero.
        add_to_log_callback(f"ForcedFireSale Event: Calculated cash gain for {drug_name.value} ({drug_quality.name}) is zero or less ({final_cash_gain}). Event fizzled.")
        return False

    # Perform the transaction
    player_inventory.remove_drug(drug_name, drug_quality, quantity_to_sell)
    player_inventory.cash += final_cash_gain

    region_name_str = region.name.value if isinstance(region.name, Enum) else region.name
    drug_name_str = drug_name.value if isinstance(drug_name, DrugName) else str(drug_name)
    quality_name_str = drug_quality.name if isinstance(drug_quality, DrugQuality) else str(drug_quality)

    message = (f"Bad Luck! You were forced into a fire sale in {region_name_str}! "
               f"Sold {quantity_to_sell} units of {quality_name_str} {drug_name_str} "
               f"at ${fire_sale_price:,.2f}/unit (penalty applied). Total gain: ${final_cash_gain:,.2f}.")

    show_event_message_callback(message)
    log_msg = (f"ForcedFireSale Event: Player sold {quantity_to_sell} {quality_name_str} {drug_name_str} "
               f"in {region_name_str} for ${final_cash_gain:,.2f}. "
               f"Player cash now: ${player_inventory.cash:,.2f}")
    add_to_log_callback(log_msg)

    return True