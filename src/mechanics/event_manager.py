import random
from typing import List, Optional, Callable, Any # Added Callable, Any

from ..core.region import Region
from ..core.market_event import MarketEvent
from ..core.enums import DrugQuality, DrugName # Added DrugName
from ..core.player_inventory import PlayerInventory
from ..core.ai_rival import AIRival
from .. import game_configs # Import whole module for access to new constants
# from ..game_configs import EVENT_TRIGGER_CHANCE # Keep this if still used directly, or access via game_configs.EVENT_TRIGGER_CHANCE


def _create_and_add_demand_spike(region: Region, current_day: int):
    potential_targets = []
    for drug_name, drug_data in region.drug_market_data.items():
        if drug_data.get("tier", 0) in [2, 3]:
            for quality_key in drug_data.get("available_qualities", {}).keys():
                potential_targets.append((drug_name, quality_key))
    if not potential_targets:
        return

    target_drug_name, target_quality = random.choice(potential_targets)
    for ev in region.active_market_events:
        if ev.target_drug_name == target_drug_name and ev.target_quality == target_quality and ev.event_type == "DEMAND_SPIKE":
            return

    event = MarketEvent(
        event_type="DEMAND_SPIKE",
        target_drug_name=target_drug_name,
        target_quality=target_quality,
        sell_price_multiplier=random.uniform(1.2, 1.8),
        buy_price_multiplier=random.uniform(1.0, 1.3),
        duration_remaining_days=random.randint(2, 4),
        start_day=current_day
    )
    region.active_market_events.append(event)
    print(f"\nMarket Buzz: Demand for {target_quality.name} {target_drug_name} is surging in {region.name} for {event.duration_remaining_days} days!")


def _create_and_add_supply_disruption(
    region: Region,
    current_day: int,
    player_heat: int, # From 'main' branch
    game_configs: Any, # From 'supply-chain-disruption' branch
    show_event_message_callback: Callable[[str], None], # From 'supply-chain-disruption' branch
    add_to_log_callback: Callable[[str], None] # From 'supply-chain-disruption' branch
):
    potential_targets = []
    for drug_name_str, drug_data in region.drug_market_data.items():
        if drug_data.get("tier", 0) in [2, 3]: # Only tier 2 or 3 drugs (from 'supply-chain-disruption' branch)
            try:
                drug_name_enum = DrugName(drug_name_str) # Convert string to DrugName enum (from 'supply-chain-disruption' branch)
            except ValueError:
                add_to_log_callback(f"SupplyDisruption: Skipped invalid drug name string '{drug_name_str}' in {region.name.value}.")
                continue

            for quality_key in drug_data.get("available_qualities", {}).keys():
                # Pass player_heat to get_available_stock (from 'main' branch, applied to enum-converted drug name)
                if region.get_available_stock(drug_name_enum, quality_key, player_heat) > 0:
                    potential_targets.append((drug_name_enum, quality_key)) # Store enum (from 'supply-chain-disruption' branch)

    if not potential_targets:
        add_to_log_callback(f"SupplyDisruption: No potential (Tier 2/3) drug targets in {region.name.value} for event.")
        return

    target_drug_name_enum, target_quality_enum = random.choice(potential_targets)

    for ev in region.active_market_events:
        if (ev.event_type == "SUPPLY_CHAIN_DISRUPTION" and
            ev.target_drug_name == target_drug_name_enum.value and # Compare with .value
            ev.target_quality == target_quality_enum):
            add_to_log_callback(f"SupplyDisruption: Event already active for {target_drug_name_enum.value} ({target_quality_enum.name}) in {region.name.value}.")
            return

    duration = game_configs.SUPPLY_DISRUPTION_EVENT_DURATION_DAYS
    reduction_factor = 1.0 - game_configs.SUPPLY_DISRUPTION_STOCK_REDUCTION_PERCENT
    min_stock = game_configs.MIN_STOCK_AFTER_DISRUPTION

    event = MarketEvent(
        event_type="SUPPLY_CHAIN_DISRUPTION",
        target_drug_name=target_drug_name_enum.value, # Store string value of enum
        target_quality=target_quality_enum,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
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
        if ev.event_type == "POLICE_CRACKDOWN":
            return

    duration = random.randint(2, 4)
    heat_amount = random.randint(10, 30)
    event = MarketEvent(
        event_type="POLICE_CRACKDOWN",
        target_drug_name=None,
        target_quality=None,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
        duration_remaining_days=duration,
        start_day=current_day,
        heat_increase_amount=heat_amount
    )
    region.active_market_events.append(event)
    region.modify_heat(heat_amount)
    print(f"\nPolice Alert: Increased police activity and crackdowns reported in {region.name} for {duration} days! (Heat +{heat_amount})")


def _create_and_add_cheap_stash(region: Region, current_day: int):
    potential_targets = []
    for drug_name, drug_data in region.drug_market_data.items():
        if drug_data.get("tier", 0) in [1, 2]:
            for quality_key in drug_data.get("available_qualities", {}).keys():
                potential_targets.append((drug_name, quality_key))
    if not potential_targets:
        return

    target_drug_name, target_quality = random.choice(potential_targets)
    for ev in region.active_market_events:
        if ev.target_drug_name == target_drug_name and ev.target_quality == target_quality and ev.event_type == "CHEAP_STASH":
            return
    
    event = MarketEvent(
        event_type="CHEAP_STASH",
        target_drug_name=target_drug_name,
        target_quality=target_quality,
        sell_price_multiplier=1.0,
        buy_price_multiplier=random.uniform(0.6, 0.8),
        duration_remaining_days=random.randint(1, 2),
        start_day=current_day,
        temporary_stock_increase=random.randint(50, 150)
    )
    region.active_market_events.append(event)
    print(f"\nMarket Whisper: Heard about a cheap stash of {target_quality.name} {target_drug_name} in {region.name}! Available for {event.duration_remaining_days} day(s). (Discounted buy price, extra stock)")


def _create_and_add_the_setup(region: Region, current_day: int, player_inventory: PlayerInventory):
    for ev in region.active_market_events:
        if ev.event_type == "THE_SETUP":
            return

    is_buy_deal = random.choice([True, False])
    possible_deal_drugs = [
        (name, data["tier"])
        for name, data in region.drug_market_data.items()
        if data["tier"] in [2, 3] and data.get("available_qualities")
    ]
    if not possible_deal_drugs:
        return

    deal_drug_name, tier = random.choice(possible_deal_drugs)
    if not region.drug_market_data[deal_drug_name].get("available_qualities"):
        return

    deal_quality = random.choice(list(region.drug_market_data[deal_drug_name]["available_qualities"].keys()))
    deal_quantity = random.randint(20, 100)
    base_buy_price = region.drug_market_data[deal_drug_name]["base_buy_price"]
    base_sell_price = region.drug_market_data[deal_drug_name]["base_sell_price"]

    from core.drug import Drug  # Import here to avoid circular imports
    temp_drug_for_mult = Drug(deal_drug_name, tier, base_buy_price, base_sell_price, deal_quality)
    quality_mult_buy = temp_drug_for_mult.get_quality_multiplier("buy")
    quality_mult_sell = temp_drug_for_mult.get_quality_multiplier("sell")
    
    if is_buy_deal:
        deal_price_per_unit = base_buy_price * quality_mult_buy * random.uniform(0.2, 0.4)
        if player_inventory.cash < deal_price_per_unit * (deal_quantity / 2):
            return
    else:
        deal_price_per_unit = base_sell_price * quality_mult_sell * random.uniform(2.0, 3.5)
        has_any_of_drug = False
        for qual_check in player_inventory.items.get(deal_drug_name, {}):
            if player_inventory.get_quantity(deal_drug_name, qual_check) > 0:
                has_any_of_drug = True
                break
        if not has_any_of_drug and player_inventory.get_quantity(deal_drug_name, deal_quality) < deal_quantity / 4:
            return

    deal_price_per_unit = round(max(1.0, deal_price_per_unit), 2)
    event = MarketEvent(
        event_type="THE_SETUP",
        target_drug_name=None,
        target_quality=None,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
        duration_remaining_days=1,
        start_day=current_day,
        deal_drug_name=deal_drug_name,
        deal_quality=deal_quality,
        deal_quantity=deal_quantity,
        deal_price_per_unit=deal_price_per_unit,
        is_buy_deal=is_buy_deal
    )
    region.active_market_events.append(event)
    print(f"\nMarket Murmurs: A shady character in {region.name} wants to make you an offer... It sounds too good to be true. (Check 'Respond to Opportunities')")


def _create_and_add_rival_busted(region: Region, current_day: int, ai_rivals: List[AIRival]):
    eligible_rivals = [r for r in ai_rivals if not r.is_busted]
    if not eligible_rivals:
        return

    busted_rival = random.choice(eligible_rivals)
    
    # Avoid duplicate "RIVAL_BUSTED" events for the same rival if one is already active as a notification
    for ev in region.active_market_events: # Check current region for notification
        if ev.event_type == "RIVAL_BUSTED" and ev.target_drug_name == busted_rival.name:
            return
    # Could also check all_regions if the notification should be global and unique

    busted_rival.is_busted = True
    busted_rival.busted_days_remaining = random.randint(5, 10)

    event = MarketEvent(
        event_type="RIVAL_BUSTED",
        target_drug_name=busted_rival.name, # Store rival's name for the message
        target_quality=None,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
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
    for drug_name_enum, drug_data in region.drug_market_data.items():
        # Ensure drug_name_enum is an instance of DrugName enum for consistency
        if not isinstance(drug_name_enum, DrugName):
            # This case should ideally not happen if keys are consistently enums
            # If drug_name_enum is a string, try to convert, or skip
            try:
                drug_name_enum = DrugName(drug_name_enum)
            except ValueError:
                add_to_log_callback(f"DrugMarketCrash: Skipped invalid drug name key '{drug_name_enum}' in {region.name.value}.")
                continue # Skip if not a valid DrugName string

        for quality_key in drug_data.get("available_qualities", {}).keys():
            if region.get_available_stock(drug_name_enum, quality_key, 0) > 0: # Passing 0 for player_heat as it's not relevant for crash trigger logic here
                potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        add_to_log_callback(f"DrugMarketCrash: No potential drug targets in {region.name.value} for event.")
        return

    target_drug_name, target_quality = random.choice(potential_targets)

    # Check if a crash event for this specific drug/quality is already active in the region
    for ev in region.active_market_events:
        if (ev.event_type == "DRUG_MARKET_CRASH" and
            ev.target_drug_name == target_drug_name.value and # target_drug_name here will be DrugName enum instance
            ev.target_quality == target_quality):
            add_to_log_callback(f"DrugMarketCrash: Event already active for {target_drug_name.value} ({target_quality.name}) in {region.name.value}.")
            return

    duration = game_configs.DRUG_CRASH_EVENT_DURATION_DAYS
    reduction_percent = game_configs.DRUG_CRASH_PRICE_REDUCTION_PERCENT
    min_price = game_configs.MINIMUM_DRUG_PRICE

    event = MarketEvent(
        event_type="DRUG_MARKET_CRASH",
        target_drug_name=target_drug_name, # Store DrugName enum instance
        target_quality=target_quality,
        sell_price_multiplier=1.0, # Not used directly, effect applied via price_reduction_factor
        buy_price_multiplier=1.0,  # Not used directly
        duration_remaining_days=duration,
        start_day=current_day,
        price_reduction_factor=(1.0 - reduction_percent), # Store the factor to multiply by
        minimum_price_after_crash=min_price
    )
    region.active_market_events.append(event)

    # Use .value for DrugName enum when creating messages for user/log
    msg = f"Market Crash! Prices for {target_drug_name.value} ({target_quality.name}) have plummeted in {region.name.value} for {duration} days!"
    show_event_message_callback(msg)
    add_to_log_callback(msg)


def _create_and_add_black_market_event(region: Region, current_day: int, player_inventory: PlayerInventory, show_event_message_callback: Optional[Callable[[str], None]] = None):
    # This event is for a specific drug/quality, so we need to avoid stacking for that specific combination.
    potential_targets = []
    for drug_name_enum_or_str, drug_data in region.drug_market_data.items():
        try:
            drug_name_enum = DrugName(drug_name_enum_or_str) if not isinstance(drug_name_enum_or_str, DrugName) else drug_name_enum_or_str
        except ValueError:
            continue # Skip this drug if name is not valid

        for quality_key in drug_data.get("available_qualities", {}).keys():
            if isinstance(quality_key, DrugQuality):
                potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        return

    chosen_drug_name, chosen_quality = random.choice(potential_targets)

    # More specific check: if a black market for THIS drug/quality is already active
    is_specific_event_active = any(
        ev.event_type == "BLACK_MARKET_OPPORTUNITY" and
        ev.target_drug_name == chosen_drug_name.value and # MarketEvent stores drug name as string
        ev.target_quality == chosen_quality
        for ev in region.active_market_events
    )
    if is_specific_event_active:
        return

    quantity = random.randint(game_configs.BLACK_MARKET_MIN_QUANTITY, game_configs.BLACK_MARKET_MAX_QUANTITY)

    event = MarketEvent(
        event_type="BLACK_MARKET_OPPORTUNITY",
        target_drug_name=chosen_drug_name.value, # Store as string value
        target_quality=chosen_quality,
        buy_price_multiplier=(1.0 - game_configs.BLACK_MARKET_PRICE_REDUCTION_PERCENT),
        sell_price_multiplier=1.0, # Not for selling to black market in this design
        duration_remaining_days=game_configs.BLACK_MARKET_EVENT_DURATION_DAYS,
        start_day=current_day,
        black_market_quantity_available=quantity
    )
    region.active_market_events.append(event)

    log_message = (f"Black Market Alert! {chosen_drug_name.value} ({chosen_quality.name}) in {region.name} "
                   f"available at {game_configs.BLACK_MARKET_PRICE_REDUCTION_PERCENT*100:.0f}% discount. "
                   f"Qty: {quantity}, for {game_configs.BLACK_MARKET_EVENT_DURATION_DAYS} day(s). "
                   f"Effective Buy Price Multiplier: {event.buy_price_multiplier:.2f}")

    if show_event_message_callback:
         show_event_message_callback(log_message) # For on-screen timed message

    return log_message # Return the message for persistent logging by the caller


def trigger_random_market_event(
    region: Region,
    current_day: int,
    player_inventory: PlayerInventory,
    ai_rivals: List[AIRival],
    show_event_message_callback: Callable[[str], None], # Made non-Optional as new events require it
    game_configs_data: Any, # Made non-Optional as new events require it
    add_to_log_callback: Callable[[str], None] # Made non-Optional as new events require it
) -> Optional[str]:
    # Ensure callbacks are provided if we intend to use them, especially for new events
    # The signature now enforces this.

    # Independent chance for Black Market event (Jules 1)
    # This should be checked first, as it has an independent chance and returns a message.
    if random.random() < game_configs_data.BLACK_MARKET_CHANCE:
        # Pass the callback down
        return _create_and_add_black_market_event(region, current_day, player_inventory, show_event_message_callback)


    # Standard market events based on global EVENT_TRIGGER_CHANCE
    if random.random() < game_configs_data.EVENT_TRIGGER_CHANCE: # Use game_configs_data
        event_choices = (["DEMAND_SPIKE"] * 3 +
                         ["SUPPLY_CHAIN_DISRUPTION"] * 2 +
                         ["POLICE_CRACKDOWN"] * 1 +
                         ["CHEAP_STASH"] * 2 +
                         ["THE_SETUP"] * 1 +
                         ["RIVAL_BUSTED"] * 1 +
                         ["DRUG_MARKET_CRASH"] * 1) # Added new event (Jules 2)
        chosen_event_type = random.choice(event_choices)
        
        # All _create_and_add functions need to accept callbacks now for consistency
        # And player_heat needs to be passed to _create_and_add_supply_disruption
        if chosen_event_type == "DEMAND_SPIKE": _create_and_add_demand_spike(region, current_day)
        elif chosen_event_type == "SUPPLY_CHAIN_DISRUPTION":
            # Pass player_heat (from Jules 1 context in app.py) to _create_and_add_supply_disruption
            # Note: player_inventory.heat will be passed from app.py
            _create_and_add_supply_disruption(region, current_day, player_inventory.heat, game_configs_data, show_event_message_callback, add_to_log_callback)
        elif chosen_event_type == "POLICE_CRACKDOWN": _create_and_add_police_crackdown(region, current_day)
        elif chosen_event_type == "CHEAP_STASH": _create_and_add_cheap_stash(region, current_day)
        elif chosen_event_type == "THE_SETUP": _create_and_add_the_setup(region, current_day, player_inventory)
        elif chosen_event_type == "RIVAL_BUSTED": _create_and_add_rival_busted(region, current_day, ai_rivals)
        elif chosen_event_type == "DRUG_MARKET_CRASH":
            _create_and_add_drug_market_crash(region, current_day, game_configs_data, show_event_message_callback, add_to_log_callback)
        return None # Standard events currently use print, not returning messages for app.py log

    return None # No event triggered or no message to return for logging


def update_active_events(region: Region):
    new_active_events = []
    for event in list(region.active_market_events): # Iterate over a copy for safe removal
        event.duration_remaining_days -= 1

        is_expired = False
        expiry_reason = "Duration ended" # Default reason

        if event.duration_remaining_days <= 0:
            is_expired = True

        if event.event_type == "BLACK_MARKET_OPPORTUNITY":
            # Check if black_market_quantity_available attribute exists and if it's <= 0
            if hasattr(event, 'black_market_quantity_available') and \
               event.black_market_quantity_available <= 0:
                if not is_expired: # If not already expired by duration
                    expiry_reason = "Stock depleted"
                is_expired = True
        # For DRUG_MARKET_CRASH and SUPPLY_CHAIN_DISRUPTION, expiry is based on duration_remaining_days <= 0

        if not is_expired:
            new_active_events.append(event)
        else:
            # Logic for constructing a descriptive name for the event subject (drug/quality/rival)
            subject_name = ""
            # Prioritize deal_drug_name for THE_SETUP, otherwise target_drug_name
            if event.deal_drug_name and event.deal_quality and event.event_type == "THE_SETUP":
                name_to_display = event.deal_drug_name.value if hasattr(event.deal_drug_name, 'value') else event.deal_drug_name
                subject_name = f"{event.deal_quality.name} {name_to_display} deal"
            elif event.target_drug_name and event.target_quality:
                # Handle target_drug_name which could be an enum or string (like for RIVAL_BUSTED)
                name_to_display = event.target_drug_name.value if hasattr(event.target_drug_name, 'value') else event.target_drug_name
                subject_name = f"{event.target_quality.name} {name_to_display}".strip()
            elif event.event_type == "RIVAL_BUSTED" and event.target_drug_name: # Rival name is typically a string
                subject_name = event.target_drug_name
            # For POLICE_CRACKDOWN, subject_name might remain empty, which is fine.

            region_name_display = region.name.value if hasattr(region.name, 'value') else region.name

            log_base = f"\nMarket Update in {region_name_display}: " # Use the display name for region

            if event.event_type == "DEMAND_SPIKE":
                print(f"{log_base}The demand spike for {subject_name} has cooled off ({expiry_reason}).")
            elif event.event_type == "SUPPLY_CHAIN_DISRUPTION":
                print(f"{log_base}The supply chain disruption for {subject_name} has ended. Availability should return to normal. ({expiry_reason}).")
            elif event.event_type == "POLICE_CRACKDOWN":
                print(f"{log_base}The increased police scrutiny seems to have subsided ({expiry_reason}).")
            elif event.event_type == "CHEAP_STASH":
                print(f"{log_base}The cheap stash of {subject_name} is gone ({expiry_reason}).")
            elif event.event_type == "THE_SETUP":
                print(f"{log_base}The shady offer regarding {subject_name} has vanished ({expiry_reason}).")
            elif event.event_type == "RIVAL_BUSTED":
                 print(f"{log_base}Looks like {subject_name} is back on the streets ({expiry_reason}).")
            elif event.event_type == "DRUG_MARKET_CRASH":
                print(f"{log_base}The market for {subject_name} has recovered from the crash ({expiry_reason}).")
            elif event.event_type == "BLACK_MARKET_OPPORTUNITY":
                print(f"{log_base}The {subject_name} has ended ({expiry_reason}).")
            else:
                event_description = subject_name if subject_name else "an event"
                print(f"{log_base}The event concerning {event_description} has ended ({expiry_reason}).")

    region.active_market_events = new_active_events