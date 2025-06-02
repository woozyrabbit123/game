"""
Manages market impact from player and AI actions, and heat decay.

This module includes functions to:
- Apply market price/stock impact based on player buy/sell actions.
- Decay player-specific market impacts over time.
- Process AI rival turns, allowing them to influence their primary markets.
- Decay AI rival market impacts over time.
- Decay regional heat levels, potentially modified by player skills.
"""

import random
from enum import Enum  # Added Enum for isinstance checks
from typing import Any, Callable, Dict, Optional  # TYPE_CHECKING, cast, RegionName removed

from .. import narco_configs as game_configs # Import the whole module to access its attributes
from ..core.ai_rival import AIRival
from ..core.enums import DrugName, SkillID, RegionName # RegionName added
from ..core.player_inventory import PlayerInventory
from ..core.region import Region


def apply_player_buy_impact(
    region: Region, drug_name_enum: DrugName, quantity_bought: int
) -> None:
    """
    Applies market impact to a drug when the player buys it.

    Increases the 'player_buy_impact_modifier' for the drug in the region,
    making subsequent buys potentially more expensive. The impact is capped.

    Args:
        region: The Region where the purchase occurred.
        drug_name_enum: The DrugName of the drug purchased.
        quantity_bought: The quantity of the drug purchased.
    """
    if drug_name_enum not in region.drug_market_data:
        return

    impact_factor: float = (
        quantity_bought / game_configs.PLAYER_MARKET_IMPACT_UNITS_BASE
    ) * game_configs.PLAYER_MARKET_IMPACT_FACTOR_PER_10_UNITS
    current_modifier: float = region.drug_market_data[drug_name_enum].get(
        "player_buy_impact_modifier", 1.0
    )
    new_modifier: float = min(current_modifier + impact_factor, game_configs.PLAYER_BUY_IMPACT_MODIFIER_CAP)
    region.drug_market_data[drug_name_enum]["player_buy_impact_modifier"] = new_modifier


def apply_player_sell_impact(
    player_inv: PlayerInventory,
    region: Region,
    drug_name_enum: DrugName,
    quantity_sold: int,
    game_configs_data: Any,
    game_state: Optional[Any] = None, # Added game_state parameter
) -> None:
    """
    Applies market impact to a drug when the player sells it.

    Decreases the 'player_sell_impact_modifier' for the drug in the region,
    making subsequent sells potentially less profitable. The impact is capped.
    If the player has the Compartmentalization skill, the impact is reduced.
    Also applies seasonal event heat modifiers.

    Args:
        player_inv: The PlayerInventory object (to check for skills).
        region: The Region where the sale occurred.
        drug_name_enum: The DrugName of the drug sold.
        quantity_sold: The quantity of the drug sold.
        game_configs_data: The game configuration module or object.
        game_state: The current GameState object, for seasonal effects.
    """
    if drug_name_enum not in region.drug_market_data:
        return

    impact_factor: float = (
        quantity_sold / game_configs.PLAYER_MARKET_IMPACT_UNITS_BASE
    ) * game_configs.PLAYER_MARKET_IMPACT_FACTOR_PER_10_UNITS

    if SkillID.COMPARTMENTALIZATION.value in player_inv.unlocked_skills:
        reduction_percent: float = (
            game_configs_data.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT # Assuming this is the correct constant for now
        )
        impact_factor *= 1 - reduction_percent

    current_modifier: float = region.drug_market_data[drug_name_enum].get(
        "player_sell_impact_modifier", 1.0
    )
    new_modifier: float = max(
        current_modifier - impact_factor, game_configs.PLAYER_SELL_IMPACT_MODIFIER_FLOOR
    )  # Cap minimum modifier
    region.drug_market_data[drug_name_enum][
        "player_sell_impact_modifier"
    ] = new_modifier

    # Add heat generation logic
    # Ensure game_configs_data has HEAT_FROM_SELLING_DRUG_TIER and SKILL_DEFINITIONS (for COMPARTMENTALIZATION)
    if hasattr(game_configs_data, "HEAT_FROM_SELLING_DRUG_TIER") and \
       hasattr(game_configs_data, "SKILL_DEFINITIONS") and \
       hasattr(game_configs_data, "COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT"):

        drug_tier: int = region.drug_market_data[drug_name_enum].get("tier", 1)
        heat_per_unit: int = game_configs_data.HEAT_FROM_SELLING_DRUG_TIER.get(drug_tier, 1)

        generated_heat: float = float(quantity_sold * heat_per_unit)

        # Apply Compartmentalization skill effect
        if SkillID.COMPARTMENTALIZATION.value in player_inv.unlocked_skills:
            reduction_percent: float = game_configs_data.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT
            generated_heat *= (1.0 - reduction_percent)

        # Apply Seasonal Event heat modifier
        # This requires game_state to be passed to this function, or effects fetched differently.
        # For now, assuming game_state is accessible via player_inv or game_configs_data (if it holds a ref)
        # Apply Seasonal Event heat modifier
        if game_state and game_state.seasonal_event_effects_active:
            heat_multiplier_effect = game_state.seasonal_event_effects_active.get("base_heat_increase_on_sale_multiplier")
            if isinstance(heat_multiplier_effect, (float, int)): # Ensure it's a number
                 generated_heat *= heat_multiplier_effect

        if generated_heat > 0:
            region.modify_heat(int(round(generated_heat)))


def decay_player_market_impact(region: Region) -> None:
    """
    Gradually reduces player-specific market impacts over time.

    This function is called daily to slowly return player buy/sell impact
    modifiers towards the neutral value of 1.0.

    Args:
        region: The Region whose market impacts are to be decayed.
    """
    for drug_name, data in region.drug_market_data.items():
        buy_mod: float = data.get("player_buy_impact_modifier", 1.0)
        if buy_mod > 1.0:
            data["player_buy_impact_modifier"] = max(1.0, buy_mod - game_configs.PLAYER_MARKET_IMPACT_DECAY_RATE)

        sell_mod: float = data.get("player_sell_impact_modifier", 1.0)
        if sell_mod < 1.0:
            data["player_sell_impact_modifier"] = min(1.0, sell_mod + game_configs.PLAYER_MARKET_IMPACT_DECAY_RATE)


def process_rival_turn(
    rival: AIRival,
    all_regions_dict: Dict[RegionName, Region],
    current_turn_number: int,
    game_configs: Any,
    add_to_log_cb: Optional[Callable[[str], None]] = None,
    show_on_screen_cb: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Processes an AI rival's turn.

    Handles logic for a rival being busted, their activity level, cooldowns,
    and performing market actions (buy/sell) in their primary region,
    which influences rival-specific market modifiers.

    Args:
        rival: The AIRival object whose turn is being processed.
        all_regions_dict: A dictionary of all game regions.
        current_turn_number: The current game day/turn.
        game_configs: The game configuration module/object.
        add_to_log_cb: Optional callback to log messages.
        show_on_screen_cb: Optional callback to display messages to the player.
    """

    def _log(message: str) -> None:
        """Helper to log messages with rival context."""
        if add_to_log_cb:
            add_to_log_cb(f"[RIVAL: {rival.name}] {message}")

    if rival.is_busted:
        rival.busted_days_remaining -= 1
        if rival.busted_days_remaining <= 0:
            rival.is_busted = False
            _log(f"Is back in business after being busted!")
            if show_on_screen_cb:
                show_on_screen_cb(f"Rival Alert: {rival.name} is back on the streets!")
        return

    if random.random() > rival.activity_level:  # Check if rival acts this turn
        return

    last_action_day: int = getattr(rival, "last_action_day", 0)  # Get or default to 0
    cooldown_period: int = random.randint(game_configs.RIVAL_COOLDOWN_MIN_DAYS, game_configs.RIVAL_COOLDOWN_MAX_DAYS)
    if current_turn_number - last_action_day < cooldown_period and last_action_day != 0:
        return  # Rival is in cooldown

    setattr(rival, "last_action_day", current_turn_number)

    # Ensure primary_region_name is an enum member before accessing .value
    primary_region_name_str = (
        rival.primary_region_name.value
        if isinstance(rival.primary_region_name, Enum)
        else str(rival.primary_region_name)
    )
    if rival.primary_region_name not in all_regions_dict:
        _log(f"Primary region {primary_region_name_str} not found.")
        return

    region_obj: Region = all_regions_dict[rival.primary_region_name]

    if rival.primary_drug not in region_obj.drug_market_data:
        _log(
            f"Primary drug {rival.primary_drug.value} not found in {region_obj.name.value} market."
        )
        return

    drug_data: Dict[str, Any] = region_obj.drug_market_data[rival.primary_drug]

    # Simplified action: buy or sell their primary drug
    if (
        random.random() < rival.aggression
    ):  # True means rival is buying (increasing demand)
        impact_magnitude_buy: float = game_configs.RIVAL_BASE_IMPACT_MAGNITUDE + (rival.aggression * game_configs.RIVAL_AGGRESSION_IMPACT_SCALE)
        current_demand_mod: float = drug_data.get("rival_demand_modifier", 1.0)
        new_demand_mod: float = min(
            current_demand_mod * (1 + impact_magnitude_buy), game_configs.RIVAL_DEMAND_MODIFIER_CAP
        )  # Cap max demand effect
        drug_data["rival_demand_modifier"] = new_demand_mod
        _log(
            f"Is buying up {rival.primary_drug.value} in {region_obj.name.value}, increasing demand! (Modifier: {new_demand_mod:.2f})"
        )
    else:  # Rival is selling (increasing supply, which means reducing player's sell price via rival_supply_modifier)
        impact_magnitude_sell: float = game_configs.RIVAL_BASE_IMPACT_MAGNITUDE + ((1 - rival.aggression) * game_configs.RIVAL_AGGRESSION_IMPACT_SCALE)
        current_supply_mod: float = drug_data.get("rival_supply_modifier", 1.0)
        # Selling by rival effectively means more supply, so modifier should decrease from player perspective (harder to sell)
        new_supply_mod: float = max(
            current_supply_mod * (1 - impact_magnitude_sell), game_configs.RIVAL_SUPPLY_MODIFIER_FLOOR
        )  # Cap min supply effect
        drug_data["rival_supply_modifier"] = new_supply_mod
        _log(
            f"Is flooding {region_obj.name.value} with {rival.primary_drug.value}, increasing supply! (Modifier: {new_supply_mod:.2f})"
        )

    drug_data["last_rival_activity_turn"] = current_turn_number


def decay_rival_market_impact(region: Region, current_turn_number: int) -> None:
    """
    Gradually reduces AI rival-specific market impacts over time.

    If a rival hasn't been active in a market for a few turns, their
    demand/supply modifiers gradually return to neutral (1.0).

    Args:
        region: The Region whose rival market impacts are to be decayed.
        current_turn_number: The current game day/turn.
    """
    # decay_rate: float = 0.1  # This was game_configs.RIVAL_MARKET_IMPACT_SUPPLY_DECAY_MULTIPLIER
    for drug_name, data in region.drug_market_data.items():
        if data.get("last_rival_activity_turn", -1) == -1:
            continue  # Skip if no rival activity recorded

        turns_since_activity: int = (
            current_turn_number - data["last_rival_activity_turn"]
        )
        if turns_since_activity > game_configs.RIVAL_ACTIVITY_DECAY_THRESHOLD_DAYS:  # Start decaying after threshold
            current_demand_mod: float = data.get("rival_demand_modifier", 1.0)
            if current_demand_mod > 1.0:
                data["rival_demand_modifier"] = max(
                    1.0, current_demand_mod - game_configs.RIVAL_MARKET_IMPACT_DECAY_RATE # Flat decay for demand
                )
            # elif current_demand_mod < 1.0: # This case should ideally not happen if rivals only increase demand mod
                # data["rival_demand_modifier"] = min(
                #     1.0, current_demand_mod * (1 + game_configs.RIVAL_MARKET_IMPACT_SUPPLY_DECAY_MULTIPLIER) # Incorrect use of supply mult here
                # )

            current_supply_mod: float = data.get("rival_supply_modifier", 1.0)
            # Rival selling makes supply_mod < 1.0 (more supply from player perspective means harder to sell)
            # Rival buying could make supply_mod > 1.0 (less supply from player perspective means easier to sell)
            if current_supply_mod < 1.0:
                data["rival_supply_modifier"] = min(
                    1.0, current_supply_mod * (1 + game_configs.RIVAL_MARKET_IMPACT_SUPPLY_DECAY_MULTIPLIER)
                )  # Decay towards 1.0
            elif current_supply_mod > 1.0: # This case implies rival buying decreased available supply to player
                data["rival_supply_modifier"] = max(
                    1.0, current_supply_mod * (1 - game_configs.RIVAL_MARKET_IMPACT_SUPPLY_DECAY_MULTIPLIER) # Decay towards 1.0
                )


def decay_regional_heat(
    region: Region,
    factor: float = 1.0,
    player_inv: Optional[PlayerInventory] = None,
    game_configs: Optional[Any] = None,
) -> None:
    """
    Decays the regional heat level over time.

    The decay amount is a percentage of current heat, with a minimum decay.
    If the player has the Ghost Protocol skill, the decay rate is boosted.

    Args:
        region: The Region whose heat is to be decayed.
        factor: A multiplier for the decay amount (e.g., for specific game events).
        player_inv: Optional PlayerInventory to check for skills.
        game_configs: Optional game configuration module for skill effect values.
    """
    decay_percentage = game_configs.REGIONAL_HEAT_DECAY_PERCENTAGE if game_configs else 0.05
    decay_amount: int = int(region.current_heat * decay_percentage * factor)

    ghost_protocol_active = False
    ghost_protocol_boost = 0.0
    if player_inv and game_configs and SkillID.GHOST_PROTOCOL.value in player_inv.unlocked_skills:
        if hasattr(game_configs, "GHOST_PROTOCOL_DECAY_BOOST_PERCENT"):
            ghost_protocol_boost = game_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
            ghost_protocol_active = True

    if ghost_protocol_active:
        decay_amount = int(decay_amount * (1 + ghost_protocol_boost))

    min_decay = game_configs.MIN_REGIONAL_HEAT_DECAY_AMOUNT if game_configs else 1
    if region.current_heat > 0:
        region.modify_heat(-max(min_decay, decay_amount))
    if region.current_heat < 0: # Ensure heat doesn't go below 0
        region.current_heat = 0
