"""
Core mechanics for player encounters, such as police stops.

This module centralizes the logic for determining encounter chances,
bribe outcomes, and search results, separating it from UI-specific presentation.
"""
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from .. import game_configs
from ..core.enums import DrugName, DrugQuality
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..game_state import GameState


def calculate_police_encounter_chance(region: Region, game_configs_data: Any) -> float:
    """
    Calculates the chance of a police encounter in the given region.
    """
    if not region:
        return 0.0
    heat_level: int = region.current_heat
    base_chance: float = getattr(game_configs_data, "POLICE_STOP_BASE_CHANCE", 0.05)
    threshold: int = getattr(game_configs_data, "POLICE_STOP_HEAT_THRESHOLD", 50)
    per_point_increase: float = getattr(game_configs_data, "POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD", 0.01)
    max_chance: float = getattr(game_configs_data, "MAX_POLICE_STOP_CHANCE", 0.75) # Adjusted from 0.95 based on text_ui_handlers

    encounter_chance: float = base_chance
    if heat_level > threshold:
        encounter_chance += (heat_level - threshold) * per_point_increase

    return max(0.05, min(encounter_chance, max_chance)) # Ensure a minimum chance if heat is high enough, capped by max_chance


def resolve_bribe_attempt(player_inventory: PlayerInventory, region: Region, game_configs_data: Any) -> Dict[str, Any]:
    """
    Resolves a bribe attempt during a police stop.
    """
    bribe_min_cost_val = getattr(game_configs_data, "BRIBE_MIN_COST", 50.0)
    bribe_base_percent_val = getattr(game_configs_data, "BRIBE_BASE_COST_PERCENT_OF_CASH", 0.1)

    bribe_cost: float = round(
        max(
            bribe_min_cost_val,
            player_inventory.cash * bribe_base_percent_val,
        ),
        2,
    )

    if player_inventory.cash < bribe_cost:
        return {"bribe_successful": False, "message_key": "bribe_too_poor", "cost_paid": 0.0, "bribe_amount_demanded": bribe_cost}

    # Player offers bribe, so cash is deducted regardless of outcome for this part of logic
    # The UI handler will confirm if player wants to offer this amount.
    # This function assumes the offer is made.
    # player_inventory.cash -= bribe_cost # This should be done by the caller after confirming the amount

    heat_points_above_threshold: int = max(
        0, region.current_heat - getattr(game_configs_data, "POLICE_STOP_HEAT_THRESHOLD", 50)
    )
    penalty: float = float(
        heat_points_above_threshold * getattr(game_configs_data, "BRIBE_SUCCESS_CHANCE_HEAT_PENALTY", 0.005)
    )
    bribe_success_actual_chance: float = max(
        getattr(game_configs_data, "BRIBE_SUCCESS_MIN_CHANCE", 0.1),
        min(getattr(game_configs_data, "BRIBE_SUCCESS_MAX_CHANCE", 0.9), getattr(game_configs_data, "BRIBE_SUCCESS_CHANCE_BASE", 0.75) - penalty)
    )

    if random.random() < bribe_success_actual_chance:
        # Player cash reduction should happen here if successful, or if cost is non-refundable on attempt
        return {"bribe_successful": True, "message_key": "bribe_success", "cost_paid": bribe_cost, "bribe_amount_demanded": bribe_cost}
    else:
        return {"bribe_successful": False, "message_key": "bribe_fail_suspicious", "cost_paid": bribe_cost, "bribe_amount_demanded": bribe_cost}


def resolve_search_outcome(player_inventory: PlayerInventory, region: Region, game_state: GameState, game_configs_data: Any) -> Dict[str, Any]:
    """
    Resolves the outcome of a police search.
    Logic adapted from text_ui_handlers.handle_police_stop_event.
    """
    drugs_confiscated_details: List[str] = []
    fine_paid: float = 0.0 # Fines are not in the text_ui_handlers version of search, but keeping variable
    jail_days: int = 0
    heat_increase: int = 0
    message_key: str = "search_clean"

    # In text_ui_handlers, this was random.random() > CONFISCATION_CHANCE_ON_SEARCH for "no find"
    # So, random.random() < CONFISCATION_CHANCE_ON_SEARCH means they *do* find something IF inventory is not empty.
    confiscation_base_chance = getattr(game_configs_data, "CONFISCATION_CHANCE_ON_SEARCH", 0.5) # Chance to *start* confiscation if items exist

    if not player_inventory.items or random.random() > confiscation_base_chance :
        message_key = "search_clean"
        # No specific heat increase here in original text_ui_handlers logic for just being searched and clean
        return {"drugs_confiscated_details": [], "fine_paid": 0.0, "jail_days": 0, "heat_increase": 0, "message_key": message_key}

    # Drugs found, proceed with confiscation & jail checks
    message_key = "search_drugs_found_confiscation" # Default if found

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
    ]

    conf_perc_min = getattr(game_configs_data, "CONFISCATION_PERCENTAGE_MIN", 0.1)
    conf_perc_max = getattr(game_configs_data, "CONFISCATION_PERCENTAGE_MAX", 0.5)
    confiscation_percentage_val: float = random.uniform(conf_perc_min, conf_perc_max)

    quantity_to_confiscate_val: int = math.ceil(
        current_quantity_val * confiscation_percentage_val
    )
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
        drugs_confiscated_details.append(f"{quantity_to_confiscate_val} units of {quality_to_confiscate_enum.name} {drug_to_confiscate_name_enum.value}")

        heat_inc_conf_min = getattr(game_configs_data, "HEAT_INCREASE_CONFISCATION_MIN", 5)
        heat_inc_conf_max = getattr(game_configs_data, "HEAT_INCREASE_CONFISCATION_MAX", 15)
        heat_increase = random.randint(heat_inc_conf_min, heat_inc_conf_max)
    else:
        message_key = "search_drugs_found_no_confiscation" # Found but nothing taken (e.g. if only 1 unit and % was low)


    # Jail Check (only if drugs were found and potentially confiscated)
    current_chance_of_jail_val: float = 0.0
    jail_heat_thresh = getattr(game_configs_data, "JAIL_CHANCE_HEAT_THRESHOLD", 70) # Example value

    if region.current_heat >= jail_heat_thresh:
        current_chance_of_jail_val += getattr(game_configs_data, "JAIL_CHANCE_BASE_IF_HEAT_THRESHOLD_MET", 0.2)

    has_high_tier_drugs_flag: bool = False
    # Determine if high-tier drugs are present (original logic was a bit complex here)
    # Simplified: check if any drug of tier 3+ is present
    for drug_name_inv_enum, qualities_inv in player_inventory.items.items():
        # Need to get tier for drug_name_inv_enum. This requires access to game_configs.DRUG_DATA or region data.
        # For simplicity, let's assume tier 3+ drugs are COKE, HEROIN for this check.
        # This should ideally come from a more robust tier checking mechanism.
        if drug_name_inv_enum in [DrugName.COKE, DrugName.HEROIN] and any(qty > 0 for qty in qualities_inv.values()):
            has_high_tier_drugs_flag = True
            break

    if has_high_tier_drugs_flag:
        current_chance_of_jail_val += getattr(game_configs_data, "JAIL_CHANCE_IF_HIGH_TIER_DRUGS_FOUND", 0.25)

    current_chance_of_jail_val = min(current_chance_of_jail_val, getattr(game_configs_data, "JAIL_CHANCE_MAX", 0.75))

    if random.random() < current_chance_of_jail_val:
        days_in_jail_base = getattr(game_configs_data, "JAIL_TIME_DAYS_BASE", 1)
        days_in_jail_heat_mult = getattr(game_configs_data, "JAIL_TIME_HEAT_MULTIPLIER", 0.1) # Days per heat point over threshold

        days_in_jail_val: int = days_in_jail_base + int(
            max(0, region.current_heat - jail_heat_thresh) * days_in_jail_heat_mult
        )
        days_in_jail_val = max(days_in_jail_base, days_in_jail_val)
        jail_days = days_in_jail_val

        message_key = "search_drugs_lost_jailed" if drugs_confiscated_details else "search_jailed_no_confiscation"
        heat_increase += getattr(game_configs_data, "HEAT_INCREASE_JAIL", 10) # Additional heat for jail time

        # Optional: cash loss in jail (not in original text_ui_handlers)
        # cash_loss_in_jail_percent = getattr(game_configs_data, "CASH_LOSS_IN_JAIL_PERCENT", 0.10)
        # cash_lost_jail = player_inventory.cash * cash_loss_in_jail_percent
        # player_inventory.cash -= cash_lost_jail
        # drugs_confiscated_details.append(f"${cash_lost_jail:,.2f} 'bail/fees'")

    region.modify_heat(heat_increase)

    return {
        "drugs_confiscated_details": drugs_confiscated_details,
        "fine_paid": fine_paid, # Still 0 based on text_ui_handlers logic for search
        "jail_days": jail_days,
        "heat_increase": heat_increase,
        "message_key": message_key
    }
