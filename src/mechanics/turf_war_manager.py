# src/mechanics/turf_war_manager.py
"""
Manages Turf War events in regions.
"""
import random
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Set

from ..core.enums import RegionName, DrugName, ContactID
from .. import narco_configs as game_configs # For TURF_WAR_CONFIG

if TYPE_CHECKING:
    from ..game_state import GameState
    from ..core.region import Region
    from ..core.player_inventory import PlayerInventory # For contact trust if needed

def try_start_turf_war(game_state: "GameState", region: "Region", player_inventory: "PlayerInventory") -> Optional[str]:
    """
    Checks if a turf war should start in the given region.
    If so, initializes it and returns a start message.
    """
    if region.name in game_state.active_turf_wars: # A turf war is already active here
        return None

    config = game_configs.TURF_WAR_CONFIG
    if random.random() < config["base_chance_per_day_per_region"]:
        # A turf war starts!
        duration = random.randint(config["min_duration_days"], config["max_duration_days"])
        end_day = game_state.current_day + duration
        
        heat_increase = random.randint(config["heat_increase_on_start_min"], config["heat_increase_on_start_max"])
        region.modify_heat(heat_increase)

        # Select affected drugs (from those available in the region)
        available_drugs_in_region = [
            drug_name for drug_name in region.drug_market_data.keys() 
            if region.drug_market_data[drug_name].get('available_qualities') 
        ]
        if not available_drugs_in_region:
            return None # No drugs to fight over

        num_drugs_to_affect = min(config["affected_drug_count"], len(available_drugs_in_region))
        affected_drugs_details: List[Dict[str, Any]] = []
        
        # Ensure we don't try to pick more drugs than available
        chosen_drug_names = random.sample(available_drugs_in_region, num_drugs_to_affect)

        for drug_name_enum in chosen_drug_names:
            volatility_mult = random.uniform(config["price_volatility_multiplier_min"], config["price_volatility_multiplier_max"])
            # Determine if price goes up or down (50/50 chance for buy/sell independently or linked)
            # Simplified: Let's say buy prices generally go up, sell prices might go up or down due to instability
            buy_price_factor = volatility_mult 
            sell_price_factor = 1.0 + random.uniform(- (volatility_mult-1)/2 , (volatility_mult-1) ) # More variance for sell

            availability_factor = 1.0
            if random.random() < config.get("availability_reduction_chance", 0.5): # Default to 0.5 if not in config
                 availability_factor = random.uniform(
                     config["availability_reduction_factor_min"], 
                     config["availability_reduction_factor_max"]
                 )

            affected_drugs_details.append({
                "drug_name": drug_name_enum,
                "original_buy_impact_mod": region.drug_market_data[drug_name_enum].get('player_buy_impact_modifier', 1.0),
                "original_sell_impact_mod": region.drug_market_data[drug_name_enum].get('player_sell_impact_modifier', 1.0),
                "turf_war_buy_price_factor": buy_price_factor,
                "turf_war_sell_price_factor": sell_price_factor,
                "turf_war_availability_factor": availability_factor
            })
        
        # Determine affected contacts (placeholder - needs list of contacts in a region)
        # For now, no specific contact effect other than a general message.
        # A more complex system would make specific contacts unavailable.
        # Example: if ContactID.INFORMANT is in region.contacts_present and random.random() < contact_unavailable_chance:
        #    affected_contacts.add(ContactID.INFORMANT)
        
        affected_contacts_set: Set[ContactID] = set() # Store ContactID enums
        # Example: Iterate through contacts known to be in this region
        for contact_id, contact_def in game_configs.CONTACT_DEFINITIONS.items():
            if contact_def.get("region") == region.name: # Check if contact is primarily in this region
                if random.random() < config["contact_unavailable_chance"]:
                    affected_contacts_set.add(contact_id)


        turf_war_data = {
            "end_day": end_day,
            "affected_drugs": affected_drugs_details,
            "affected_contacts": list(affected_contacts_set), # Convert set to list for storage if needed
            "original_heat": region.current_heat - heat_increase # Store heat before this turf war's increase
        }
        game_state.active_turf_wars[region.name] = turf_war_data
        
        drug_names_str = ", ".join([d["drug_name"].value for d in affected_drugs_details])
        start_message = config["message_on_start_template"].format(region_name=region.name.value, drug_names_str=drug_names_str)
        
        # Log detailed info
        # logger.info(f"Turf War started in {region.name.value} until day {end_day}. Heat +{heat_increase}. Affected drugs: {drug_names_str}. Details: {turf_war_data}")
        return start_message
    return None

def update_active_turf_wars(game_state: "GameState") -> Optional[str]:
    """
    Checks active turf wars and ends them if their duration is over.
    Returns an end message if a war ends.
    """
    ended_war_message = None
    regions_to_end_war: List[RegionName] = []

    for region_name, war_data in game_state.active_turf_wars.items():
        if game_state.current_day > war_data["end_day"]:
            regions_to_end_war.append(region_name)
            
            # Construct end message (assuming region_name is an Enum)
            region_display_name = region_name.value if isinstance(region_name, RegionName) else str(region_name)
            ended_war_message = game_configs.TURF_WAR_CONFIG["message_on_end_template"].format(region_name=region_display_name)
            # Log end
            # logger.info(f"Turf War ended in {region_display_name}.")
            # For simplicity, effects like price/availability modifiers will naturally phase out
            # as the turf war data is removed from active_turf_wars.
            # If specific restoration of pre-war state was needed, it would happen here.
            # e.g., region.current_heat = war_data.get("original_heat", region.current_heat) # Restore heat option
            
    for region_name_key in regions_to_end_war:
        if region_name_key in game_state.active_turf_wars:
            del game_state.active_turf_wars[region_name_key]
            
    return ended_war_message

[end of src/mechanics/turf_war_manager.py]
