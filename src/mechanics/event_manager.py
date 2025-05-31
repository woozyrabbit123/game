import random
from typing import List, Optional, Callable, Any # Added Callable, Any

from ..core.region import Region
from ..core.market_event import MarketEvent
from ..core.enums import DrugQuality, DrugName # Added DrugName
from ..core.player_inventory import PlayerInventory
from ..core.ai_rival import AIRival
from ..game_configs import EVENT_TRIGGER_CHANCE


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
    game_configs: Any,
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None]
):
    potential_targets = []
    for drug_name_str, drug_data in region.drug_market_data.items():
        if drug_data.get("tier", 0) in [2, 3]: # Only tier 2 or 3 drugs
            try:
                drug_name_enum = DrugName(drug_name_str) # Convert string to DrugName enum
            except ValueError:
                add_to_log_callback(f"SupplyDisruption: Skipped invalid drug name string '{drug_name_str}' in {region.name.value}.")
                continue

            for quality_key in drug_data.get("available_qualities", {}).keys():
                if region.get_available_stock(drug_name_enum, quality_key) > 0:
                    potential_targets.append((drug_name_enum, quality_key)) # Store enum

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
            if region.get_available_stock(drug_name_enum, quality_key) > 0: # Check stock for the specific drug (enum) and quality
                potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        add_to_log_callback(f"DrugMarketCrash: No potential drug targets in {region.name.value} for event.")
        return

    target_drug_name, target_quality = random.choice(potential_targets)

    # Check if a crash event for this specific drug/quality is already active in the region
    for ev in region.active_market_events:
        if (ev.event_type == "DRUG_MARKET_CRASH" and
            ev.target_drug_name == target_drug_name and # target_drug_name here will be DrugName enum instance
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


def trigger_random_market_event(
    region: Region,
    current_day: int,
    player_inventory: PlayerInventory,
    ai_rivals: List[AIRival],
    show_event_message_callback: Callable[[str], None],
    game_configs_data: Optional[Any] = None,
    add_to_log_callback: Optional[Callable[[str], None]] = None
):
    # Ensure callbacks are provided if we intend to use them, especially for new events
    if not game_configs_data or not add_to_log_callback:
        # Fallback or error for existing events if they were to use these,
        # but new events like DRUG_MARKET_CRASH require them.
        # For now, let old events print, and new one will fail if not provided.
        # A better solution would be to pass add_to_log_callback to all _create_and_add functions.
        print("Warning: game_configs_data or add_to_log_callback not provided to trigger_random_market_event.")
        # If these are absolutely essential for all paths, consider raising an error or returning.

    if random.random() < EVENT_TRIGGER_CHANCE: # This is the global trigger chance
        # Specific event chances can be handled inside if DRUG_CRASH_EVENT_CHANCE is meant to be separate
        # For now, adding to weighted list:
        event_choices = (["DEMAND_SPIKE"] * 3 + 
                         ["SUPPLY_CHAIN_DISRUPTION"] * 2 + 
                         ["POLICE_CRACKDOWN"] * 1 +
                         ["CHEAP_STASH"] * 2 +
                         ["THE_SETUP"] * 1 +
                         ["RIVAL_BUSTED"] * 1 +
                         ["DRUG_MARKET_CRASH"] * 1) # Added new event
        chosen_event_type = random.choice(event_choices)
        
        # TODO: Consider refactoring all _create_and_add functions to accept show_event_message_callback and add_to_log_callback
        if chosen_event_type == "DEMAND_SPIKE": _create_and_add_demand_spike(region, current_day) # Needs callbacks
        elif chosen_event_type == "SUPPLY_CHAIN_DISRUPTION":
            if game_configs_data and add_to_log_callback and show_event_message_callback:
                _create_and_add_supply_disruption(region, current_day, game_configs_data, show_event_message_callback, add_to_log_callback)
            else:
                print(f"Error: Could not trigger SUPPLY_CHAIN_DISRUPTION due to missing critical arguments.")
        elif chosen_event_type == "POLICE_CRACKDOWN": _create_and_add_police_crackdown(region, current_day) # Needs callbacks
        elif chosen_event_type == "CHEAP_STASH": _create_and_add_cheap_stash(region, current_day) # Needs callbacks
        elif chosen_event_type == "THE_SETUP": _create_and_add_the_setup(region, current_day, player_inventory) # Needs callbacks
        elif chosen_event_type == "RIVAL_BUSTED": _create_and_add_rival_busted(region, current_day, ai_rivals) # Needs callbacks
        elif chosen_event_type == "DRUG_MARKET_CRASH":
            if game_configs_data and add_to_log_callback and show_event_message_callback: # Ensure all needed args are present
                _create_and_add_drug_market_crash(region, current_day, game_configs_data, show_event_message_callback, add_to_log_callback)
            else:
                print(f"Error: Could not trigger DRUG_MARKET_CRASH due to missing game_configs_data, add_to_log_callback or show_event_message_callback.")


def update_active_events(region: Region):
    still_active_events = []
    for event in list(region.active_market_events):
        event.duration_remaining_days -= 1
        if event.duration_remaining_days > 0:
            still_active_events.append(event)
        else:
            drug_qual_name = ""
            # Constructing drug_qual_name to handle potential enums for drug names
            if event.target_drug_name and event.target_quality:
                name_to_display = event.target_drug_name.value if hasattr(event.target_drug_name, 'value') else event.target_drug_name
                drug_qual_name = f"{event.target_quality.name} {name_to_display}".strip()
            elif event.deal_drug_name and event.deal_quality: # For THE_SETUP or similar future events
                name_to_display = event.deal_drug_name.value if hasattr(event.deal_drug_name, 'value') else event.deal_drug_name
                drug_qual_name = f"{event.deal_quality.name} {name_to_display} deal".strip()
            elif event.event_type == "RIVAL_BUSTED" and event.target_drug_name: # Rival name is typically a string
                drug_qual_name = event.target_drug_name
            # Note: For POLICE_CRACKDOWN, drug_qual_name might remain empty, which is fine.

            region_name_display = region.name.value if hasattr(region.name, 'value') else region.name

            if event.event_type == "DEMAND_SPIKE":
                print(f"\nMarket Buzz: The demand spike for {drug_qual_name} has cooled off in {region_name_display}.")
            elif event.event_type == "SUPPLY_CHAIN_DISRUPTION":
                print(f"\nMarket Update: The supply chain disruption for {drug_qual_name} in {region_name_display} has ended. Availability should return to normal.")
            elif event.event_type == "POLICE_CRACKDOWN":
                print(f"\nPolice Update: The increased police scrutiny in {region_name_display} seems to have subsided.")
            elif event.event_type == "CHEAP_STASH":
                print(f"\nMarket Update: The cheap stash of {drug_qual_name} in {region_name_display} is gone.")
            elif event.event_type == "THE_SETUP":
                print(f"\nThe shady offer in {region_name_display} seems to have vanished...")
            elif event.event_type == "RIVAL_BUSTED":
                print(f"\nStreet Murmurs: Looks like {drug_qual_name} is back on the streets after their little 'vacation'.")
            elif event.event_type == "DRUG_MARKET_CRASH":
                # drug_qual_name should be correctly built by the logic above for target_drug_name (enum) and target_quality
                print(f"\nMarket Update: The market for {drug_qual_name} in {region_name_display} has recovered from the crash.")
            else:
                print(f"\nMarket Update: The event concerning {drug_qual_name if drug_qual_name else 'a situation'} in {region_name_display} has ended.")
    region.active_market_events = still_active_events