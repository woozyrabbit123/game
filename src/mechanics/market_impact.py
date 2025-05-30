import random
from typing import Dict, Optional, Callable

from ..core.region import Region 
from ..core.ai_rival import AIRival 
from ..core.enums import DrugName, RegionName

def apply_player_buy_impact(region: Region, drug_name_str: str, quantity_bought: int):
    # Find DrugName enum member matching drug_name_str
    drug_name_enum = None
    for dn_enum in DrugName: # Iterate through DrugName enum members
        if dn_enum.value == drug_name_str: # Compare with enum's value
            drug_name_enum = dn_enum
            break
    if not drug_name_enum or drug_name_enum not in region.drug_market_data: return # Use enum for dict key
    
    impact_factor = (quantity_bought / 10) * 0.02
    current_modifier = region.drug_market_data[drug_name_enum]["player_buy_impact_modifier"]
    new_modifier = min(current_modifier + impact_factor, 1.25) 
    region.drug_market_data[drug_name_enum]["player_buy_impact_modifier"] = new_modifier

def apply_player_sell_impact(region: Region, drug_name_str: str, quantity_sold: int):
    drug_name_enum = None
    for dn_enum in DrugName: # Iterate through DrugName enum members
        if dn_enum.value == drug_name_str: # Compare with enum's value
            drug_name_enum = dn_enum
            break
    if not drug_name_enum or drug_name_enum not in region.drug_market_data: return # Use enum for dict key

    impact_factor = (quantity_sold / 10) * 0.02
    current_modifier = region.drug_market_data[drug_name_enum]["player_sell_impact_modifier"]
    new_modifier = max(current_modifier - impact_factor, 0.75) 
    region.drug_market_data[drug_name_enum]["player_sell_impact_modifier"] = new_modifier

def decay_player_market_impact(region: Region):
    for drug_name, data in region.drug_market_data.items():
        buy_mod = data["player_buy_impact_modifier"]
        if buy_mod > 1.0: data["player_buy_impact_modifier"] = max(1.0, buy_mod - 0.01)
        sell_mod = data["player_sell_impact_modifier"]
        if sell_mod < 1.0: data["player_sell_impact_modifier"] = min(1.0, sell_mod + 0.01)

def process_rival_turn(
    rival: AIRival, 
    all_regions_dict: Dict[RegionName, Region], # Changed key type to RegionName
    current_turn_number: int,
    game_configs: any, # Added game_configs
    log_message_callback: Optional[Callable[[str], None]] = None # Added callback for logging
    ):
    
    def _log(message):
        if log_message_callback:
            log_message_callback(f"[RIVAL: {rival.name}] {message}")
        # else: print(f"[RIVAL: {rival.name}] {message}") # Fallback to print if no callback

    if rival.is_busted: 
        rival.busted_days_remaining -= 1
        if rival.busted_days_remaining <= 0:
            rival.is_busted = False
            _log(f"Is back in business after being busted!")
        # else: _log(f"Is still busted for {rival.busted_days_remaining} more days.") # Optional: too verbose
        return

    if random.random() > rival.activity_level: # Check if rival acts this turn
        return 
    
    # Cooldown logic
    if hasattr(rival, 'last_action_day') and \
       current_turn_number - rival.last_action_day < random.randint(1,3) and \
       rival.last_action_day != 0 :
        return
        
    rival.last_action_day = current_turn_number

    if rival.primary_region_name not in all_regions_dict: 
        _log(f"Primary region {rival.primary_region_name} not found.") # Use .value if it's an enum and you want string
        return
    
    region = all_regions_dict[rival.primary_region_name] # Access with RegionName enum

    if rival.primary_drug not in region.drug_market_data: # rival.primary_drug is DrugName enum
        _log(f"Primary drug {rival.primary_drug.value} not found in {region.name.value} market.")
        return

    drug_data = region.drug_market_data[rival.primary_drug]

    # Simplified action: buy or sell their primary drug in their primary region
    if random.random() < rival.aggression: 
        impact_magnitude_buy = 0.05 + (rival.aggression * 0.15) 
        current_demand_mod = drug_data.get("rival_demand_modifier", 1.0)
        new_demand_mod = min(current_demand_mod * (1 + impact_magnitude_buy), 2.0) 
        drug_data["rival_demand_modifier"] = new_demand_mod
        _log(f"Is buying up {rival.primary_drug.value} in {region.name.value}, increasing demand! (Modifier: {new_demand_mod:.2f})")
    else: 
        impact_magnitude_sell = 0.05 + ((1 - rival.aggression) * 0.15) 
        current_supply_mod = drug_data.get("rival_supply_modifier", 1.0)
        new_supply_mod = max(current_supply_mod * (1 - impact_magnitude_sell), 0.5) 
        drug_data["rival_supply_modifier"] = new_supply_mod
        _log(f"Is flooding {region.name.value} with {rival.primary_drug.value}, increasing supply! (Modifier: {new_supply_mod:.2f})")
    
    drug_data["last_rival_activity_turn"] = current_turn_number

def decay_rival_market_impact(region: Region, current_turn_number: int):
    decay_rate = 0.1  # Define decay rate for rival market impact
    for drug_name, data in region.drug_market_data.items():
        if data.get("last_rival_activity_turn", -1) == -1: continue
        turns_since_activity = current_turn_number - data["last_rival_activity_turn"]
        if turns_since_activity > 3: 
            if data["rival_demand_modifier"] > 1.0: data["rival_demand_modifier"] = max(1.0, data["rival_demand_modifier"] - 0.05)
            elif data["rival_demand_modifier"] < 1.0: data["rival_demand_modifier"] = min(1.0, data["rival_demand_modifier"] * (1 + decay_rate))

            if data["rival_supply_modifier"] < 1.0:
                data["rival_supply_modifier"] = min(1.0, data["rival_supply_modifier"] * (1 + decay_rate))
            elif data["rival_supply_modifier"] > 1.0: # Should not happen with current sell logic
                data["rival_supply_modifier"] = max(1.0, data["rival_supply_modifier"] * (1 - decay_rate))

def decay_regional_heat(region: Region, factor: float = 1.0): # factor allows for modified decay (e.g. in jail)
    decay_amount = int(region.current_heat * 0.05 * factor) # Decay 5% of current heat
    if region.current_heat > 0:
        region.modify_heat(-max(1, decay_amount)) # Decay at least 1 point if heat > 0
    if region.current_heat < 0 : region.current_heat = 0 # Ensure heat doesn't go negative