import random
from typing import List, Optional

from core.region import Region
from core.market_event import MarketEvent
from core.enums import DrugQuality
from core.player_inventory import PlayerInventory
from core.ai_rival import AIRival
from game_configs import EVENT_TRIGGER_CHANCE


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


def _create_and_add_supply_disruption(region: Region, current_day: int):
    potential_targets = []
    for drug_name, drug_data in region.drug_market_data.items():
        for quality_key in drug_data.get("available_qualities", {}).keys():
            if region.get_available_stock(drug_name, quality_key) > 0:
                potential_targets.append((drug_name, quality_key))
    if not potential_targets:
        return

    target_drug_name, target_quality = random.choice(potential_targets)
    for ev in region.active_market_events:
        if ev.target_drug_name == target_drug_name and ev.target_quality == target_quality and ev.event_type == "SUPPLY_CHAIN_DISRUPTION":
            return

    event = MarketEvent(
        event_type="SUPPLY_CHAIN_DISRUPTION",
        target_drug_name=target_drug_name,
        target_quality=target_quality,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
        duration_remaining_days=random.randint(3, 6),
        start_day=current_day
    )
    region.active_market_events.append(event)
    print(f"\nMarket Alert: A supply chain disruption is affecting {target_quality.name} {target_drug_name} in {region.name} for {event.duration_remaining_days} days! Stock will be very low or unavailable.")


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


def trigger_random_market_event(region: Region, current_day: int, player_inventory: PlayerInventory, ai_rivals: List[AIRival]): # Added ai_rivals
    if random.random() < EVENT_TRIGGER_CHANCE:
        event_choices = (["DEMAND_SPIKE"] * 3 + 
                         ["SUPPLY_CHAIN_DISRUPTION"] * 2 + 
                         ["POLICE_CRACKDOWN"] * 1 +
                         ["CHEAP_STASH"] * 2 +
                         ["THE_SETUP"] * 1 +
                         ["RIVAL_BUSTED"] * 1) # Added RIVAL_BUSTED
        chosen_event_type = random.choice(event_choices)
        
        if chosen_event_type == "DEMAND_SPIKE": _create_and_add_demand_spike(region, current_day)
        elif chosen_event_type == "SUPPLY_CHAIN_DISRUPTION": _create_and_add_supply_disruption(region, current_day)
        elif chosen_event_type == "POLICE_CRACKDOWN": _create_and_add_police_crackdown(region, current_day)
        elif chosen_event_type == "CHEAP_STASH": _create_and_add_cheap_stash(region, current_day)
        elif chosen_event_type == "THE_SETUP": _create_and_add_the_setup(region, current_day, player_inventory)
        elif chosen_event_type == "RIVAL_BUSTED": _create_and_add_rival_busted(region, current_day, ai_rivals)


def update_active_events(region: Region):
    still_active_events = []
    for event in list(region.active_market_events):
        event.duration_remaining_days -= 1
        if event.duration_remaining_days > 0:
            still_active_events.append(event)
        else:
            drug_qual_name = ""
            if event.target_drug_name and event.target_quality:
                drug_qual_name = f"{event.target_quality.name} {event.target_drug_name}".strip()
            elif event.deal_drug_name and event.deal_quality:
                drug_qual_name = f"{event.deal_quality.name} {event.deal_drug_name} deal".strip()
            elif event.event_type == "RIVAL_BUSTED" and event.target_drug_name:
                drug_qual_name = event.target_drug_name

            if event.event_type == "DEMAND_SPIKE":
                print(f"\nMarket Buzz: The demand spike for {drug_qual_name} has cooled off in {region.name}.")
            elif event.event_type == "SUPPLY_CHAIN_DISRUPTION":
                print(f"\nMarket Update: The supply of {drug_qual_name} in {region.name} is stabilizing.")
            elif event.event_type == "POLICE_CRACKDOWN":
                print(f"\nPolice Update: The increased police scrutiny in {region.name} seems to have subsided.")
            elif event.event_type == "CHEAP_STASH":
                print(f"\nMarket Update: The cheap stash of {drug_qual_name} in {region.name} is gone.")
            elif event.event_type == "THE_SETUP":
                print(f"\nThe shady offer in {region.name} seems to have vanished...")
            elif event.event_type == "RIVAL_BUSTED":
                print(f"\nStreet Murmurs: Looks like {drug_qual_name} is back on the streets after their little 'vacation'.")
            else:
                print(f"\nMarket Update: The event concerning {drug_qual_name if drug_qual_name else 'a situation'} in {region.name} has ended.")
    region.active_market_events = still_active_events