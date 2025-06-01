"""
Manages the triggering and updating of market and player-related events.

This module includes functions to:
- Create specific types of market events (e.g., demand spikes, police crackdowns).
- Randomly trigger market events based on configured chances.
- Update the status and duration of active events each day.
- Handle specific player-affecting events like muggings or forced sales.
"""

import math
import random
import sys  # For stderr logging
from enum import Enum
from typing import Any, Callable, List, Optional, Tuple, Union

from .. import game_configs
from ..core.ai_rival import AIRival
from ..core.enums import DrugName, DrugQuality, EventType  # SkillID removed
from ..core.market_event import MarketEvent
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..game_state import GameState
# Specific config imports - these are numerous, consider accessing via game_configs object
from ..game_configs import (
    EVENT_TIER_TARGET_CHEAP_STASH,
    EVENT_TIER_TARGET_DEMAND_SPIKE,
    EVENT_TIER_TARGET_SUPPLY_DISRUPTION,
    EVENT_TIER_TARGET_THE_SETUP,
    FORCED_SALE_MIN_PRICE_PER_UNIT,  # Added based on usage
    FORCED_SALE_MIN_QUANTITY_TO_SELL,  # Added based on usage
    MARKET_EVENT_WEIGHTS,
    SETUP_EVENT_MIN_CASH_FACTOR_FOR_BUY_DEAL,
    SETUP_EVENT_MIN_PRICE_PER_UNIT,
    SETUP_EVENT_MIN_QUANTITY_FACTOR_FOR_SELL_DEAL,
)


def _create_and_add_demand_spike(
    region: Region, game_state_instance: GameState
) -> None:
    """
    Creates and adds a Demand Spike event to a region if conditions are met.

    A demand spike increases the buy and sell price for a randomly chosen
    Tier 2 or Tier 3 drug/quality combination for a limited duration.

    Args:
        region: The Region object where the event might occur.
        game_state_instance: The current GameState object.
    """
    current_day: int = game_state_instance.current_day
    potential_targets: List[Tuple[DrugName, DrugQuality]] = []
    # drug_name_enum from region.drug_market_data.items() is already DrugName enum
    for (
        drug_name_enum,
        drug_data,
    ) in region.drug_market_data.items():  # drug_data is Dict[str, Any]
        if drug_data.get("tier", 0) in EVENT_TIER_TARGET_DEMAND_SPIKE:  # tier is int
            for quality_key in drug_data.get(
                "available_qualities", {}
            ).keys():  # quality_key is DrugQuality
                if isinstance(
                    quality_key, DrugQuality
                ):  # Ensure it's DrugQuality before appending
                    potential_targets.append((drug_name_enum, quality_key))
    if not potential_targets:
        return

    target_drug_name_enum: DrugName
    target_quality: DrugQuality
    target_drug_name_enum, target_quality = random.choice(potential_targets)

    for ev in region.active_market_events:  # ev is MarketEvent
        if (
            ev.target_drug_name == target_drug_name_enum
            and ev.target_quality == target_quality
            and ev.event_type == EventType.DEMAND_SPIKE
        ):
            return

    try:
        event_cfg = game_configs.EVENT_CONFIGS["DEMAND_SPIKE"]
        sell_price_mult_min = event_cfg["SELL_PRICE_MULT_MIN"]
        sell_price_mult_max = event_cfg["SELL_PRICE_MULT_MAX"]
        buy_price_mult_min = event_cfg["BUY_PRICE_MULT_MIN"]
        buy_price_mult_max = event_cfg["BUY_PRICE_MULT_MAX"]
        duration_days_min = event_cfg["DURATION_DAYS_MIN"]
        duration_days_max = event_cfg["DURATION_DAYS_MAX"]

        if not all(isinstance(v, (int, float)) for v in [sell_price_mult_min, sell_price_mult_max, buy_price_mult_min, buy_price_mult_max]) or \
           not all(isinstance(v, int) for v in [duration_days_min, duration_days_max]):
            print("Error: Invalid type for one or more DEMAND_SPIKE parameters in game_configs.EVENT_CONFIGS. Event not created.", file=sys.stderr)
            return
    except KeyError as e:
        print(f"Error: Missing configuration for DEMAND_SPIKE event parameter: {e}. Event not created.", file=sys.stderr)
        return

    event: MarketEvent = MarketEvent(
        event_type=EventType.DEMAND_SPIKE,
        target_drug_name=target_drug_name_enum,
        target_quality=target_quality,
        sell_price_multiplier=random.uniform(sell_price_mult_min, sell_price_mult_max),
        buy_price_multiplier=random.uniform(buy_price_mult_min, buy_price_mult_max),
        duration_remaining_days=random.randint(duration_days_min, duration_days_max),
        start_day=current_day,
    )
    region.active_market_events.append(event)
    drug_name_str: str = (
        target_drug_name_enum.value
        if isinstance(target_drug_name_enum, DrugName)
        else str(target_drug_name_enum)
    )
    region_name_str: str = (
        region.name.value if isinstance(region.name, Enum) else str(region.name)
    )
    print(
        f"\nMarket Buzz: Demand for {target_quality.name} {drug_name_str} is surging in {region_name_str} for {event.duration_remaining_days} days!"
    )


def _create_and_add_supply_disruption(
    region: Region,
    current_day: int,
    game_state_instance: GameState,
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None],
) -> None:
    """
    Creates and adds a Supply Disruption event to a region.

    This event reduces the available stock of a specific drug and quality.

    Args:
        region: The Region to affect.
        current_day: The current game day.
        game_state_instance: The current GameState.
        show_event_message_callback: Callback to display messages to the player.
        add_to_log_callback: Callback to add messages to the game log.
    """
    potential_targets: List[Tuple[DrugName, DrugQuality]] = []
    for (
        drug_name_enum,
        drug_data,
    ) in region.drug_market_data.items():  # drug_data is Dict[str, Any]
        if drug_data.get("tier", 0) in EVENT_TIER_TARGET_SUPPLY_DISRUPTION:
            for quality_key in drug_data.get(
                "available_qualities", {}
            ).keys():  # quality_key is DrugQuality
                if isinstance(quality_key, DrugQuality):  # Ensure it's DrugQuality
                    if (
                        region.get_available_stock(
                            drug_name_enum, quality_key, game_state_instance
                        )
                        > 0
                    ):
                        potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        region_name_str: str = (
            region.name.value if isinstance(region.name, Enum) else str(region.name)
        )
        add_to_log_callback(
            f"SupplyDisruption: No potential (Tier 2/3) drug targets in {region_name_str} for event."
        )
        return

    target_drug_name_enum: DrugName
    target_quality_enum: DrugQuality
    target_drug_name_enum, target_quality_enum = random.choice(potential_targets)

    for ev in region.active_market_events:  # ev is MarketEvent
        if (
            ev.event_type == EventType.SUPPLY_DISRUPTION
            and ev.target_drug_name == target_drug_name_enum
            and ev.target_quality == target_quality_enum
        ):
            drug_name_str: str = (
                target_drug_name_enum.value
                if isinstance(target_drug_name_enum, DrugName)
                else str(target_drug_name_enum)
            )
            region_name_str: str = (
                region.name.value if isinstance(region.name, Enum) else str(region.name)
            )
            add_to_log_callback(
                f"SupplyDisruption: Event already active for {drug_name_str} ({target_quality_enum.name}) in {region_name_str}."
            )
            return

    try:
        cfg = game_configs.EVENT_CONFIGS["SUPPLY_DISRUPTION"]
        duration = cfg["DURATION_DAYS"]
        stock_reduction_percent = cfg["STOCK_REDUCTION_PERCENT"]
        min_stock = cfg["MIN_STOCK_AFTER_EVENT"]

        if not isinstance(duration, int) or not isinstance(stock_reduction_percent, (int, float)) or not isinstance(min_stock, int):
            print("Error: Invalid type for one or more SUPPLY_DISRUPTION parameters in game_configs.EVENT_CONFIGS. Event not created.", file=sys.stderr)
            return
        reduction_factor: float = 1.0 - float(stock_reduction_percent)

    except KeyError as e:
        print(f"Error: Missing configuration for SUPPLY_DISRUPTION event parameter: {e}. Event not created.", file=sys.stderr)
        return

    event: MarketEvent = MarketEvent(
        event_type=EventType.SUPPLY_DISRUPTION,
        target_drug_name=target_drug_name_enum,
        target_quality=target_quality_enum,
        sell_price_multiplier=1.0, # Default, not impactful for this event type
        buy_price_multiplier=1.0,  # Default
        duration_remaining_days=int(duration),
        start_day=current_day,
        stock_reduction_factor=reduction_factor,
        min_stock_after_event=int(min_stock),
    )
    region.active_market_events.append(event)

    msg: str = f"Supply Alert! {target_drug_name_enum.value} ({target_quality_enum.name}) in {region.name.value} is now scarce due to a supply chain disruption for {duration} days!"  # type: ignore
    show_event_message_callback(msg)
    add_to_log_callback(msg)


def _create_and_add_police_crackdown(region: Region, current_day: int) -> None:
    """
    Creates and adds a Police Crackdown event to a region.

    This event increases regional heat for its duration.

    Args:
        region: The Region to affect.
        current_day: The current game day.
    """
    for ev in region.active_market_events:
        if ev.event_type == EventType.POLICE_CRACKDOWN:
            return

    try:
        event_cfg = game_configs.EVENT_CONFIGS["POLICE_CRACKDOWN"]
        duration_days_min = event_cfg["DURATION_DAYS_MIN"]
        duration_days_max = event_cfg["DURATION_DAYS_MAX"]
        heat_increase_min = event_cfg["HEAT_INCREASE_MIN"]
        heat_increase_max = event_cfg["HEAT_INCREASE_MAX"]

        if not all(isinstance(v, int) for v in [duration_days_min, duration_days_max, heat_increase_min, heat_increase_max]):
            print("Error: Invalid type for one or more POLICE_CRACKDOWN parameters in game_configs.EVENT_CONFIGS. Event not created.", file=sys.stderr)
            return
    except KeyError as e:
        print(f"Error: Missing configuration for POLICE_CRACKDOWN event parameter: {e}. Event not created.", file=sys.stderr)
        return

    duration: int = random.randint(duration_days_min, duration_days_max)
    heat_amount: int = random.randint(heat_increase_min, heat_increase_max)
    event: MarketEvent = MarketEvent(
        event_type=EventType.POLICE_CRACKDOWN,
        target_drug_name=None,
        target_quality=None,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
        duration_remaining_days=duration,
        start_day=current_day,
        heat_increase_amount=heat_amount,
    )
    region.active_market_events.append(event)
    region.modify_heat(heat_amount)
    region_name_str: str = (
        region.name.value if isinstance(region.name, Enum) else str(region.name)
    )
    print(
        f"\nPolice Alert: Increased police activity and crackdowns reported in {region_name_str} for {duration} days! (Heat +{heat_amount})"
    )


def _create_and_add_cheap_stash(region: Region, current_day: int) -> None:
    """
    Creates and adds a Cheap Stash event to a region.

    This event makes a specific drug/quality available at a lower buy price
    and temporarily increases its stock.

    Args:
        region: The Region to affect.
        current_day: The current game day.
    """
    potential_targets: List[Tuple[DrugName, DrugQuality]] = []
    for (
        drug_name_enum,
        drug_data,
    ) in region.drug_market_data.items():  # drug_data is Dict[str, Any]
        if drug_data.get("tier", 0) in EVENT_TIER_TARGET_CHEAP_STASH:
            for quality_key in drug_data.get(
                "available_qualities", {}
            ).keys():  # quality_key is DrugQuality
                if isinstance(quality_key, DrugQuality):
                    potential_targets.append((drug_name_enum, quality_key))
    if not potential_targets:
        return

    target_drug_name_enum: DrugName
    target_quality: DrugQuality
    target_drug_name_enum, target_quality = random.choice(potential_targets)

    for ev in region.active_market_events:  # ev is MarketEvent
        if (
            ev.target_drug_name == target_drug_name_enum
            and ev.target_quality == target_quality
            and ev.event_type == EventType.CHEAP_STASH
        ):
            return

    try:
        event_cfg = game_configs.EVENT_CONFIGS["CHEAP_STASH"]
        buy_price_mult_min = event_cfg["BUY_PRICE_MULT_MIN"]
        buy_price_mult_max = event_cfg["BUY_PRICE_MULT_MAX"]
        duration_days_min = event_cfg["DURATION_DAYS_MIN"]
        duration_days_max = event_cfg["DURATION_DAYS_MAX"]
        temp_stock_increase_min = event_cfg["TEMP_STOCK_INCREASE_MIN"]
        temp_stock_increase_max = event_cfg["TEMP_STOCK_INCREASE_MAX"]

        if not isinstance(buy_price_mult_min, (int, float)) or \
           not isinstance(buy_price_mult_max, (int, float)) or \
           not all(isinstance(v, int) for v in [duration_days_min, duration_days_max, temp_stock_increase_min, temp_stock_increase_max]):
            print("Error: Invalid type for one or more CHEAP_STASH parameters in game_configs.EVENT_CONFIGS. Event not created.", file=sys.stderr)
            return
    except KeyError as e:
        print(f"Error: Missing configuration for CHEAP_STASH event parameter: {e}. Event not created.", file=sys.stderr)
        return

    event: MarketEvent = MarketEvent(
        event_type=EventType.CHEAP_STASH,
        target_drug_name=target_drug_name_enum,
        target_quality=target_quality,
        sell_price_multiplier=1.0,
        buy_price_multiplier=random.uniform(buy_price_mult_min, buy_price_mult_max),
        duration_remaining_days=random.randint(duration_days_min, duration_days_max),
        start_day=current_day,
        temporary_stock_increase=random.randint(
            temp_stock_increase_min, temp_stock_increase_max
        ),
    )
    region.active_market_events.append(event)
    drug_name_str: str = (
        target_drug_name_enum.value
        if isinstance(target_drug_name_enum, DrugName)
        else str(target_drug_name_enum)
    )
    region_name_str: str = (
        region.name.value if isinstance(region.name, Enum) else str(region.name)
    )
    print(
        f"\nMarket Whisper: Heard about a cheap stash of {target_quality.name} {drug_name_str} in {region_name_str}! Available for {event.duration_remaining_days} day(s). (Discounted buy price, extra stock)"
    )


def _create_and_add_the_setup(
    region: Region, current_day: int, player_inventory: PlayerInventory
) -> None:
    """
    Creates and adds a "The Setup" event to a region.

    This event presents a risky but potentially lucrative buy or sell deal to the player.

    Args:
        region: The Region where the event occurs.
        current_day: The current game day.
        player_inventory: The PlayerInventory object.
    """
    for ev in region.active_market_events:  # ev is MarketEvent
        if ev.event_type == EventType.THE_SETUP:
            return

    is_buy_deal: bool = random.choice([True, False])
    possible_deal_drugs: List[Tuple[DrugName, int]] = [
        (drug_name_enum, data["tier"])
        for drug_name_enum, data in region.drug_market_data.items()  # data is Dict[str, Any]
        if data.get("tier") in EVENT_TIER_TARGET_THE_SETUP and data.get("available_qualities")
    ]
    if not possible_deal_drugs:
        return

    deal_drug_name_enum: DrugName
    tier: int
    deal_drug_name_enum, tier = random.choice(possible_deal_drugs)

    if not region.drug_market_data[deal_drug_name_enum].get("available_qualities"):
        return

    deal_quality: DrugQuality = random.choice(
        list(region.drug_market_data[deal_drug_name_enum]["available_qualities"].keys())
    )

    try:
        event_cfg = game_configs.EVENT_CONFIGS["THE_SETUP"]
        deal_quantity_min = event_cfg["DEAL_QUANTITY_MIN"]
        deal_quantity_max = event_cfg["DEAL_QUANTITY_MAX"]
        buy_deal_price_mult_min = event_cfg["BUY_DEAL_PRICE_MULT_MIN"]
        buy_deal_price_mult_max = event_cfg["BUY_DEAL_PRICE_MULT_MAX"]
        sell_deal_price_mult_min = event_cfg["SELL_DEAL_PRICE_MULT_MIN"]
        sell_deal_price_mult_max = event_cfg["SELL_DEAL_PRICE_MULT_MAX"]
        duration_days = event_cfg["DURATION_DAYS"]

        if not all(isinstance(v, int) for v in [deal_quantity_min, deal_quantity_max, duration_days]) or \
           not all(isinstance(v, (int,float)) for v in [buy_deal_price_mult_min, buy_deal_price_mult_max, sell_deal_price_mult_min, sell_deal_price_mult_max]):
            print("Error: Invalid type for one or more THE_SETUP parameters in game_configs.EVENT_CONFIGS. Event not created.", file=sys.stderr)
            return
    except KeyError as e:
        print(f"Error: Missing configuration for THE_SETUP event parameter: {e}. Event not created.", file=sys.stderr)
        return

    deal_quantity: int = random.randint(deal_quantity_min, deal_quantity_max)
    base_buy_price: float = region.drug_market_data[deal_drug_name_enum]["base_buy_price"]
    base_sell_price: float = region.drug_market_data[deal_drug_name_enum]["base_sell_price"]

    from ..core.drug import Drug
    temp_drug_for_mult: Drug = Drug(deal_drug_name_enum.value, tier, base_buy_price, base_sell_price, deal_quality)
    quality_mult_buy: float = temp_drug_for_mult.get_quality_multiplier("buy")
    quality_mult_sell: float = temp_drug_for_mult.get_quality_multiplier("sell")
    deal_price_per_unit: float

    if is_buy_deal:
        deal_price_per_unit = base_buy_price * quality_mult_buy * random.uniform(buy_deal_price_mult_min, buy_deal_price_mult_max)
        if player_inventory.cash < deal_price_per_unit * deal_quantity * getattr(game_configs, "SETUP_EVENT_MIN_CASH_FACTOR_FOR_BUY_DEAL", 0.5): # Use getattr for safety
            return
    else:  # Sell deal
        deal_price_per_unit = base_sell_price * quality_mult_sell * random.uniform(sell_deal_price_mult_min, sell_deal_price_mult_max)
        has_any_of_drug: bool = any(player_inventory.get_quantity(deal_drug_name_enum, qc) > 0 for qc in player_inventory.items.get(deal_drug_name_enum, {}))
        if not has_any_of_drug and player_inventory.get_quantity(deal_drug_name_enum, deal_quality) < deal_quantity * getattr(game_configs, "SETUP_EVENT_MIN_QUANTITY_FACTOR_FOR_SELL_DEAL", 0.25): # Use getattr
            return

    deal_price_per_unit = round(max(getattr(game_configs, "SETUP_EVENT_MIN_PRICE_PER_UNIT", 1.0), deal_price_per_unit), 2) # Use getattr

    event: MarketEvent = MarketEvent(
        event_type=EventType.THE_SETUP,
        target_drug_name=None,
        target_quality=None,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
        duration_remaining_days=duration_days,
        start_day=current_day,
        deal_drug_name=deal_drug_name_enum,
        deal_quality=deal_quality,
        deal_quantity=deal_quantity,
        deal_price_per_unit=deal_price_per_unit,
        is_buy_deal=is_buy_deal,
    )
    region.active_market_events.append(event)
    region_name_str: str = (
        region.name.value if isinstance(region.name, Enum) else str(region.name)
    )
    print(
        f"\nMarket Murmurs: A shady character in {region_name_str} wants to make you an offer... It sounds too good to be true. (Check 'Respond to Opportunities')"
    )


def _create_and_add_rival_busted(
    region: Region, current_day: int, ai_rivals: List[AIRival]
) -> None:
    """
    Creates and adds a Rival Busted event.

    Marks a random active AI rival as 'busted', making them inactive for a duration.
    The event is added to the specified region's event list for player notification.

    Args:
        region: The Region to which this event notification is added (often player's current region).
        current_day: The current game day.
        ai_rivals: The list of all AIRival objects in the game.
    """
    eligible_rivals: List[AIRival] = [r for r in ai_rivals if not r.is_busted]
    if not eligible_rivals:
        return

    busted_rival: AIRival = random.choice(eligible_rivals)

    for ev in region.active_market_events:  # ev is MarketEvent
        if ev.event_type == EventType.RIVAL_BUSTED and ev.target_drug_name == busted_rival.name:  # type: ignore # target_drug_name is Optional[DrugName] but here it's a string for rival name
            return

    busted_rival.is_busted = True
    try:
        event_cfg = game_configs.EVENT_CONFIGS["RIVAL_BUSTED"]
        duration_days_min = event_cfg["DURATION_DAYS_MIN"]
        duration_days_max = event_cfg["DURATION_DAYS_MAX"]
        if not all(isinstance(v, int) for v in [duration_days_min, duration_days_max]):
            print("Error: Invalid type for RIVAL_BUSTED duration parameters. Event not fully processed.", file=sys.stderr)
            # Proceed with bust but maybe default duration or log error further
            busted_rival.busted_days_remaining = 5 # Fallback
        else:
            busted_rival.busted_days_remaining = random.randint(duration_days_min, duration_days_max)
    except KeyError as e:
        print(f"Error: Missing configuration for RIVAL_BUSTED event parameter: {e}. Using default bust duration.", file=sys.stderr)
        busted_rival.busted_days_remaining = 5 # Fallback

    event: MarketEvent = MarketEvent(
        event_type=EventType.RIVAL_BUSTED,
        target_drug_name=busted_rival.name,  # type: ignore # Store rival name as str here
        target_quality=None,
        sell_price_multiplier=1.0,
        buy_price_multiplier=1.0,
        duration_remaining_days=busted_rival.busted_days_remaining,
        start_day=current_day,
    )
    region.active_market_events.append(event)
    print(
        f"\nMajor News: Notorious dealer {busted_rival.name} has been BUSTED by authorities! They'll be out of action for about {busted_rival.busted_days_remaining} days."
    )


def _create_and_add_drug_market_crash(
    region: Region,
    current_day: int,
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None],
) -> None:
    """
    Creates and adds a Drug Market Crash event to a region.

    This event significantly reduces the price of a specific drug/quality.

    Args:
        region: The Region to affect.
        current_day: The current game day.
        show_event_message_callback: Callback for player messages.
        add_to_log_callback: Callback for game log.
    """
    potential_targets: List[Tuple[DrugName, DrugQuality]] = []
    for (
        drug_name_enum,
        drug_data,
    ) in region.drug_market_data.items():  # drug_data is Dict[str, Any]
        for quality_key in drug_data.get(
            "available_qualities", {}
        ).keys():  # quality_key is DrugQuality
            if isinstance(quality_key, DrugQuality):
                # Create a dummy GameState for get_available_stock as player_heat is not relevant for this event trigger
                class DummyGameState(
                    GameState
                ):  # Inherit from GameState for type compatibility
                    def __init__(
                        self,
                    ):  # Basic init to satisfy GameState requirements if any
                        super().__init__()  # Call parent init
                        self.player_inventory = (
                            PlayerInventory()
                        )  # Ensure player_inventory exists

                dummy_gs = DummyGameState()
                if (
                    region.get_available_stock(drug_name_enum, quality_key, dummy_gs)
                    > 0
                ):
                    potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        region_name_str: str = (
            region.name.value if isinstance(region.name, Enum) else str(region.name)
        )
        add_to_log_callback(
            f"DrugMarketCrash: No potential drug targets in {region_name_str} for event."
        )
        return

    target_drug_name_enum: DrugName
    target_quality_enum: DrugQuality
    target_drug_name_enum, target_quality_enum = random.choice(potential_targets)

    for ev in region.active_market_events:  # ev is MarketEvent
        if (
            ev.event_type == EventType.DRUG_MARKET_CRASH
            and ev.target_drug_name == target_drug_name_enum
            and ev.target_quality == target_quality_enum
        ):
            drug_name_str: str = target_drug_name_enum.value
            region_name_str: str = (
                region.name.value if isinstance(region.name, Enum) else str(region.name)
            )
            add_to_log_callback(
                f"DrugMarketCrash: Event already active for {drug_name_str} ({target_quality_enum.name}) in {region_name_str}."
            )
            return

    try:
        cfg = game_configs.EVENT_CONFIGS["DRUG_MARKET_CRASH"]
        duration = cfg["DURATION_DAYS"]
        reduction_percent = cfg["PRICE_REDUCTION_PERCENT"]
        min_price = cfg["MINIMUM_PRICE_AFTER_CRASH"]

        if not isinstance(duration, int) or \
           not isinstance(reduction_percent, (int, float)) or \
           not isinstance(min_price, (int, float)):
            print("Error: Invalid type for one or more DRUG_MARKET_CRASH parameters. Event not created.", file=sys.stderr)
            return
    except KeyError as e:
        print(f"Error: Missing configuration for DRUG_MARKET_CRASH event parameter: {e}. Event not created.", file=sys.stderr)
        return

    event: MarketEvent = MarketEvent(
        event_type=EventType.DRUG_MARKET_CRASH,
        target_drug_name=target_drug_name_enum,
        target_quality=target_quality_enum,
        sell_price_multiplier=1.0, # Default
        buy_price_multiplier=1.0,   # Default
        duration_remaining_days=int(duration),
        start_day=current_day,
        price_reduction_factor=(1.0 - float(reduction_percent)),
        minimum_price_after_crash=float(min_price),
    )
    region.active_market_events.append(event)

    drug_name_str: str = target_drug_name_enum.value
    region_name_str: str = (
        region.name.value if isinstance(region.name, Enum) else str(region.name)
    )
    msg: str = f"Market Crash! Prices for {drug_name_str} ({target_quality_enum.name}) have plummeted in {region_name_str} for {duration} days!"  # type: ignore
    show_event_message_callback(msg)
    add_to_log_callback(msg)


def _create_and_add_black_market_event(
    region: Region,
    current_day: int,
    player_inventory: PlayerInventory,
    show_event_message_callback: Optional[Callable[[str], None]] = None,
) -> Optional[str]:
    """
    Creates and adds a Black Market Opportunity event to a region.

    This event offers a specific drug/quality at a significant discount for a short period.

    Args:
        region: The Region to affect.
        current_day: The current game day.
        player_inventory: The PlayerInventory (used for context, not directly modified here).
        show_event_message_callback: Optional callback for player messages.

    Returns:
        Optional[str]: A log message if the event is created, otherwise None.
    """
    potential_targets: List[Tuple[DrugName, DrugQuality]] = []
    for (
        drug_name_enum,
        drug_data,
    ) in region.drug_market_data.items():  # drug_data is Dict[str, Any]
        for quality_key in drug_data.get(
            "available_qualities", {}
        ).keys():  # quality_key is DrugQuality
            if isinstance(quality_key, DrugQuality):
                potential_targets.append((drug_name_enum, quality_key))

    if not potential_targets:
        return None

    chosen_drug_name_enum: DrugName
    chosen_quality: DrugQuality
    chosen_drug_name_enum, chosen_quality = random.choice(potential_targets)

    is_specific_event_active: bool = any(
        ev.event_type == EventType.BLACK_MARKET_OPPORTUNITY
        and ev.target_drug_name == chosen_drug_name_enum
        and ev.target_quality == chosen_quality
        for ev in region.active_market_events  # ev is MarketEvent
    )
    if is_specific_event_active:
        return None

    try:
        cfg = game_configs.EVENT_CONFIGS["BLACK_MARKET_OPPORTUNITY"]
        min_qty = cfg["MIN_QUANTITY"]
        max_qty = cfg["MAX_QUANTITY"]
        price_reduction_perc = cfg["PRICE_REDUCTION_PERCENT"]
        duration_days = cfg["DURATION_DAYS"]

        if not all(isinstance(v, int) for v in [min_qty, max_qty, duration_days]) or \
           not isinstance(price_reduction_perc, (int, float)):
            print("Error: Invalid type for one or more BLACK_MARKET_OPPORTUNITY parameters. Event not created.", file=sys.stderr)
            return None # Explicitly return None
    except KeyError as e:
        print(f"Error: Missing configuration for BLACK_MARKET_OPPORTUNITY event parameter: {e}. Event not created.", file=sys.stderr)
        return None # Explicitly return None

    quantity: int = random.randint(min_qty, max_qty)

    event: MarketEvent = MarketEvent(
        event_type=EventType.BLACK_MARKET_OPPORTUNITY,
        target_drug_name=chosen_drug_name_enum,
        target_quality=chosen_quality,
        buy_price_multiplier=(1.0 - price_reduction_perc),
        sell_price_multiplier=1.0,
        duration_remaining_days=duration_days,
        start_day=current_day,
        black_market_quantity_available=quantity,
    )
    region.active_market_events.append(event)

    drug_name_str: str = chosen_drug_name_enum.value
    region_name_str: str = (
        region.name.value if isinstance(region.name, Enum) else str(region.name)
    )
    log_message: str = (
        f"Black Market Alert! {drug_name_str} ({chosen_quality.name}) in {region_name_str} "
        f"available at {price_reduction_perc*100:.0f}% discount. "
        f"Qty: {quantity}, for {duration_days} day(s). "
        f"Effective Buy Price Multiplier: {event.buy_price_multiplier:.2f}"
    )

    if show_event_message_callback:
        show_event_message_callback(log_message)

    return log_message


def trigger_random_market_event(
    region: Region,
    game_state: GameState,
    player_inventory: PlayerInventory,
    ai_rivals: List[AIRival],
    show_event_message_callback: Callable[[str], None],
    game_configs_data: Any,
    add_to_log_callback: Callable[[str], None],
) -> Optional[str]:
    """
    Triggers a random market event in the specified region based on configured chances.

    This function considers various event types, their weights, and specific conditions
    for triggering (e.g., Black Market, Mugging, standard market events).

    Args:
        region: The Region where the event may be triggered.
        game_state: The current GameState object.
        player_inventory: The PlayerInventory object.
        ai_rivals: A list of AIRival objects.
        show_event_message_callback: Callback to display messages to the player.
        game_configs_data: The game configuration module/object.
        add_to_log_callback: Callback to add messages to the game log.

    Returns:
        Optional[str]: A log message if a black market event was specifically created,
                       otherwise None for other events (which message themselves) or no event.
    """
    current_day: int = game_state.current_day

    black_market_message: Optional[str] = None
    if (
        random.random() < game_configs_data.BLACK_MARKET_CHANCE
    ):  # Access attribute from module
        black_market_message = _create_and_add_black_market_event(
            region, current_day, player_inventory, show_event_message_callback
        )

    mugging_event_chance = getattr(game_configs_data, "MUGGING_EVENT_CHANCE", 0.10) # Default if not found
    if random.random() < mugging_event_chance:
        _handle_mugging_event( # Removed assignment to mugging_occurred as it's not used
            player_inventory,
            region,
            game_configs_data, # Pass the whole module/object
            show_event_message_callback,
            add_to_log_callback,
        )

    forced_fire_sale_chance = getattr(game_configs_data, "FORCED_FIRE_SALE_CHANCE", 0.02) # Default if not found
    if random.random() < forced_fire_sale_chance:
        _handle_forced_fire_sale_event( # Removed assignment to forced_sale_occurred
            player_inventory,
            region,
            game_configs_data, # Pass the whole module/object
            show_event_message_callback,
            add_to_log_callback,
        )

    if (
        black_market_message # This is Optional[str]
    ):  # Return this message if it occurred, regardless of others for now
        return black_market_message

    if (
        random.random() < game_configs_data.EVENT_TRIGGER_CHANCE
    ):  # Access attribute from module
        event_creation_functions: Dict[EventType, Callable[..., None]] = {
            EventType.DEMAND_SPIKE: _create_and_add_demand_spike,
            EventType.SUPPLY_DISRUPTION: _create_and_add_supply_disruption,  # type: ignore # Signature mismatch, needs fixing if used
            EventType.POLICE_CRACKDOWN: _create_and_add_police_crackdown,
            EventType.CHEAP_STASH: _create_and_add_cheap_stash,
            EventType.THE_SETUP: _create_and_add_the_setup,
            EventType.RIVAL_BUSTED: _create_and_add_rival_busted,
            EventType.DRUG_MARKET_CRASH: _create_and_add_drug_market_crash,  # type: ignore # Signature mismatch
        }

        weighted_event_list: List[EventType] = []
        for event_type_str, weight_val in MARKET_EVENT_WEIGHTS.items():
            try:
                event_type_enum = EventType(event_type_str) # Convert string from config to Enum
                weighted_event_list.extend([event_type_enum] * weight_val)
            except ValueError:
                # Log or handle the case where a string in MARKET_EVENT_WEIGHTS is not a valid EventType
                add_to_log_callback(f"Warning: Invalid EventType string '{event_type_str}' in MARKET_EVENT_WEIGHTS config.")

        if not weighted_event_list:
            return None

        chosen_event_type_enum: EventType = random.choice(weighted_event_list)
        creation_func = event_creation_functions[chosen_event_type_enum]

        # Adjust calls based on specific function signatures
        if chosen_event_type_enum == EventType.DEMAND_SPIKE:
            creation_func(region, game_state)  # type: ignore
        elif chosen_event_type_enum == EventType.SUPPLY_DISRUPTION:
            creation_func(region, current_day, game_state, show_event_message_callback, add_to_log_callback)  # type: ignore
        elif chosen_event_type_enum == EventType.POLICE_CRACKDOWN:
            creation_func(region, current_day)  # type: ignore
        elif chosen_event_type_enum == EventType.CHEAP_STASH:
            creation_func(region, current_day)  # type: ignore
        elif chosen_event_type_enum == EventType.THE_SETUP:
            creation_func(region, current_day, player_inventory)  # type: ignore
        elif chosen_event_type_enum == EventType.RIVAL_BUSTED:
            creation_func(region, current_day, ai_rivals)  # type: ignore
        elif chosen_event_type_enum == EventType.DRUG_MARKET_CRASH:
            creation_func(region, current_day, show_event_message_callback, add_to_log_callback)  # type: ignore
        return None
    return None


def update_active_events(region: Region) -> None:
    new_active_events: List[MarketEvent] = []
    for event in list(region.active_market_events):  # event is MarketEvent
        event.duration_remaining_days -= 1
        is_expired: bool = False
        expiry_reason: str = "Duration ended"

        if event.duration_remaining_days <= 0:
            is_expired = True

        current_event_type: Union[EventType, str] = event.event_type
        if not isinstance(current_event_type, EventType):
            try:
                current_event_type = EventType(str(current_event_type))
            except ValueError:
                pass

        if current_event_type == EventType.BLACK_MARKET_OPPORTUNITY:
            if (
                hasattr(event, "black_market_quantity_available")
                and event.black_market_quantity_available is not None
                and event.black_market_quantity_available <= 0
            ):
                if not is_expired:
                    expiry_reason = "Stock depleted"
                is_expired = True

        if not is_expired:
            new_active_events.append(event)
        else:
            subject_name: str = ""
            deal_drug_str: Optional[str] = (
                event.deal_drug_name.value if event.deal_drug_name else None
            )
            target_drug_str: Optional[str] = event.target_drug_name.value if event.target_drug_name else None  # type: ignore[attr-defined] # if target_drug_name is str for RIVAL_BUSTED

            if (
                event.deal_drug_name
                and event.deal_quality
                and current_event_type == EventType.THE_SETUP
            ):
                subject_name = f"{event.deal_quality.name} {deal_drug_str} deal"
            elif event.target_drug_name and event.target_quality:  # type: ignore[attr-defined]
                subject_name = f"{event.target_quality.name} {target_drug_str}".strip()
            elif current_event_type == EventType.RIVAL_BUSTED and event.target_drug_name:  # type: ignore[attr-defined] # Rival name is string
                subject_name = str(event.target_drug_name)

            region_name_display: str = (
                region.name.value if isinstance(region.name, Enum) else str(region.name)
            )
            log_base: str = f"\nMarket Update in {region_name_display}: "
            event_type_display: str = (
                current_event_type.value
                if isinstance(current_event_type, EventType)
                else str(current_event_type)
            )

            message_map: Dict[EventType, str] = {
                EventType.DEMAND_SPIKE: f"The demand spike for {subject_name} has cooled off ({expiry_reason}).",
                EventType.SUPPLY_DISRUPTION: f"The supply chain disruption for {subject_name} has ended. Availability should return to normal. ({expiry_reason}).",
                EventType.POLICE_CRACKDOWN: f"The increased police scrutiny seems to have subsided ({expiry_reason}).",
                EventType.CHEAP_STASH: f"The cheap stash of {subject_name} is gone ({expiry_reason}).",
                EventType.THE_SETUP: f"The shady offer regarding {subject_name} has vanished ({expiry_reason}).",
                EventType.RIVAL_BUSTED: f"Looks like {subject_name} is back on the streets ({expiry_reason}).",
                EventType.DRUG_MARKET_CRASH: f"The market for {subject_name} has recovered from the crash ({expiry_reason}).",
                EventType.BLACK_MARKET_OPPORTUNITY: f"The black market opportunity for {subject_name} has ended ({expiry_reason}).",
            }
            # Ensure current_event_type is hashable (Enum member) for dict lookup
            final_event_type_for_map = (
                current_event_type
                if isinstance(current_event_type, EventType)
                else EventType(event_type_display)
            )

            default_message: str = (
                f"The event concerning {subject_name if subject_name else 'a ' + event_type_display} has ended ({expiry_reason})."
            )
            print(log_base + message_map.get(final_event_type_for_map, default_message))

    region.active_market_events = new_active_events


def check_and_trigger_police_stop(region: Region, player_inventory: PlayerInventory, game_state: GameState) -> bool:  # type: ignore
    """
    Checks for and potentially triggers a police stop event based on regional heat.

    Note: The original implementation of this function in some versions might be a placeholder.
    This docstring assumes it would perform a check and return True if a stop is triggered.

    Args:
        region: The current Region object.
        player_inventory: The PlayerInventory object.
        game_state: The current GameState object.

    Returns:
        True if a police stop event was triggered, False otherwise.
    """
    # Placeholder implementation detail:
    # Actual logic would involve:
    # 1. Calculating chance of police stop based on region.current_heat,
    #    POLICE_STOP_HEAT_THRESHOLD, POLICE_STOP_BASE_CHANCE, etc.
    # 2. If random chance met, call a handler like handle_police_stop_event().
    # 3. Return True if stop occurred, False otherwise.
    # The provided code in the prompt had this as a placeholder always returning False.
    # For the purpose of docstring generation, we assume it *could* trigger an event.
    return False


def _handle_mugging_event(
    player_inventory: PlayerInventory,
    region: Region,
    game_configs_data: Any,
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None],
) -> bool:
    """
    Handles the logic for a mugging event. Player loses a percentage of their cash.

    Args:
        player_inventory: The player's inventory.
        region: The region where the mugging occurs.
        game_configs_data: Game configuration data (module or object).
        show_event_message_callback: Callback to display messages to the player.
        add_to_log_callback: Callback to add messages to the game log.

    Returns:
        True if the mugging successfully occurred and cash was lost, False otherwise.
    """
    if player_inventory.cash <= 0:
        return False

    min_loss_pct = getattr(game_configs_data, "MUGGING_CASH_LOSS_PERCENT_MIN", 0.05)
    max_loss_pct = getattr(game_configs_data, "MUGGING_CASH_LOSS_PERCENT_MAX", 0.15)
    if not isinstance(min_loss_pct, (int,float)) or not isinstance(max_loss_pct, (int,float)):
        print(f"Warning: Invalid MUGGING_CASH_LOSS_PERCENT values in game_configs. Using defaults.", file=sys.stderr)
        min_loss_pct = 0.05
        max_loss_pct = 0.15

    percentage_lost: float = random.uniform(min_loss_pct, max_loss_pct)
    cash_lost: int = math.floor(player_inventory.cash * percentage_lost)

    if cash_lost <= 0:
        return False

    player_inventory.cash -= cash_lost

    region_name_str: str = (
        region.name.value if isinstance(region.name, Enum) else str(region.name)
    )
    message: str = (
        f"Street Danger! You were mugged in {region_name_str} and lost ${cash_lost:,.0f}!"
    )

    show_event_message_callback(message)
    add_to_log_callback(
        f"Mugging Event: Player lost ${cash_lost:,.0f} in {region_name_str}. Player cash now: ${player_inventory.cash:,.0f}"
    )
    return True


def _handle_forced_fire_sale_event(
    player_inventory: PlayerInventory,
    region: Region,
    game_configs_data: Any,
    show_event_message_callback: Callable[[str], None],
    add_to_log_callback: Callable[[str], None],
) -> bool:
    """
    Handles the logic for a Forced Fire Sale event.
    Player is forced to sell a portion of a random drug stash at a penalty.

    Args:
        player_inventory: The player's inventory.
        region: The region where the fire sale occurs.
        game_configs_data: Game configuration data.
        show_event_message_callback: Callback for player messages.
        add_to_log_callback: Callback for game log.

    Returns:
        True if drugs were successfully sold in the fire sale, False otherwise.
    """
    eligible_drugs: List[Dict[str, Union[DrugName, DrugQuality, int]]] = []
    for drug_name_enum, qualities in player_inventory.items.items():
        for quality_enum, quantity_val in qualities.items():
            if quantity_val > 0:
                eligible_drugs.append(
                    {
                        "name": drug_name_enum,
                        "quality": quality_enum,
                        "quantity": quantity_val,
                    }
                )

    if not eligible_drugs:
        add_to_log_callback(
            "ForcedFireSale Event: Player has no drugs to sell. Event fizzled."
        )
        return False

    selected_drug_info: Dict[str, Union[DrugName, DrugQuality, int]] = random.choice(
        eligible_drugs
    )
    drug_name: DrugName = selected_drug_info["name"]  # type: ignore
    drug_quality: DrugQuality = selected_drug_info["quality"]  # type: ignore
    player_has_quantity: int = selected_drug_info["quantity"]  # type: ignore

    fs_qty_pct = getattr(game_configs_data, "FORCED_FIRE_SALE_QUANTITY_PERCENT", 0.15)
    fs_penalty_pct = getattr(game_configs_data, "FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT", 0.30)
    fs_min_cash_gain = getattr(game_configs_data, "FORCED_FIRE_SALE_MIN_CASH_GAIN", 50.0)
    fs_min_qty_sell = getattr(game_configs_data, "FORCED_SALE_MIN_QUANTITY_TO_SELL", 1) # From previous step
    fs_min_price_unit = getattr(game_configs_data, "FORCED_SALE_MIN_PRICE_PER_UNIT", 0.01) # From previous step

    if not all(isinstance(v, (int,float)) for v in [fs_qty_pct, fs_penalty_pct, fs_min_cash_gain, fs_min_qty_sell, fs_min_price_unit ]):
        print(f"Warning: Invalid type for one or more FORCED_FIRE_SALE parameters in game_configs. Event may not work as expected.", file=sys.stderr)
        # Could return False here if any are critical and wrongly typed. For now, proceed with defaults if getattr fails.

    quantity_to_sell_float: float = player_has_quantity * fs_qty_pct
    quantity_to_sell: int = math.ceil(quantity_to_sell_float)
    quantity_to_sell = max(fs_min_qty_sell, quantity_to_sell)
    quantity_to_sell = min(quantity_to_sell, player_has_quantity)

    if quantity_to_sell == 0:
        add_to_log_callback(
            f"ForcedFireSale Event: Calculated quantity to sell for {drug_name.value} ({drug_quality.name}) is zero. Event fizzled."
        )
        return False

    normal_sell_price: float = region.get_sell_price(drug_name, drug_quality)
    if normal_sell_price <= 0:
        add_message_to_log( # Using add_message_to_log for consistency if it's preferred over add_to_log_callback
            f"ForcedFireSale Event: Normal sell price for {drug_name.value} ({drug_quality.name}) in {region.name.value} is {normal_sell_price}. Event fizzled."
        )
        return False

    fire_sale_price: float = normal_sell_price * (1 - fs_penalty_pct)
    fire_sale_price = round(max(fs_min_price_unit, fire_sale_price), 2)

    calculated_cash_gain: float = quantity_to_sell * fire_sale_price
    final_cash_gain: float = calculated_cash_gain
    if calculated_cash_gain > 0: # Ensure min cash gain is applied only if there was some gain
        final_cash_gain = max(calculated_cash_gain, fs_min_cash_gain)
    final_cash_gain = round(final_cash_gain, 2)


    if final_cash_gain <= 0 and calculated_cash_gain <=0 : # Check if any gain at all
        add_to_log_callback(
            f"ForcedFireSale Event: Calculated cash gain for {drug_name.value} ({drug_quality.name}) is zero or less ({final_cash_gain}). Event fizzled."
        )
        return False

    player_inventory.remove_drug(drug_name, drug_quality, quantity_to_sell)
    player_inventory.cash += final_cash_gain

    region_name_str: str = (
        region.name.value if isinstance(region.name, Enum) else str(region.name)
    )
    drug_name_str: str = (
        drug_name.value if isinstance(drug_name, DrugName) else str(drug_name)
    )
    quality_name_str: str = (
        drug_quality.name
        if isinstance(drug_quality, DrugQuality)
        else str(drug_quality)
    )

    message: str = (
        f"Bad Luck! You were forced into a fire sale in {region_name_str}! "
        f"Sold {quantity_to_sell} units of {quality_name_str} {drug_name_str} "
        f"at ${fire_sale_price:,.2f}/unit (penalty applied). Total gain: ${final_cash_gain:,.2f}."
    )

    show_event_message_callback(message)
    log_msg: str = (
        f"ForcedFireSale Event: Player sold {quantity_to_sell} {quality_name_str} {drug_name_str} "
        f"in {region_name_str} for ${final_cash_gain:,.2f}. "
        f"Player cash now: ${player_inventory.cash:,.2f}"
    )
    add_to_log_callback(log_msg)
    return True
