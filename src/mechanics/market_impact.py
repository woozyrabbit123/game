import random
from typing import Dict, Optional, Callable, Any

from ..core.region import Region
from ..core.ai_rival import AIRival
from ..core.enums import DrugName, RegionName, SkillID
from ..core.player_inventory import PlayerInventory

def apply_player_buy_impact(region: Region, drug_name_enum: DrugName, quantity_bought: int):
    if drug_name_enum not in region.drug_market_data: return
    
    impact_factor = (quantity_bought / 10) * 0.02
    current_modifier = region.drug_market_data[drug_name_enum]["player_buy_impact_modifier"]
    new_modifier = min(current_modifier + impact_factor, 1.25) 
    region.drug_market_data[drug_name_enum]["player_buy_impact_modifier"] = new_modifier

def apply_player_sell_impact(player_inv: PlayerInventory, region: Region, drug_name_enum: DrugName, quantity_sold: int):
    if drug_name_enum not in region.drug_market_data: return

    impact_factor = (quantity_sold / 10) * 0.02

    # Apply Compartmentalization skill if unlocked
    if SkillID.COMPARTMENTALIZATION in player_inv.unlocked_skills:
        # Assuming COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT means impact reduction here.
        # Need to confirm this interpretation or if a specific config value for market impact reduction exists.
        # For now, let's assume it reduces the impact_factor by a certain percentage.
        # This constant should ideally be in game_configs.py
        # Example: COMPARTMENTALIZATION_MARKET_IMPACT_REDUCTION = 0.25 (25%)
        # For now, I'll use a placeholder value or assume it's related to a heat reduction constant.
        # The original subtask only asked to change the key, not implement new logic.
        # However, the variable name 'COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT' suggests it's for heat.
        # Let's assume the skill reduces the *negative* impact of selling.
        # A more direct interpretation: the impact_factor itself is reduced.
        # If game_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT is 0.10, then impact is 90% of normal.
        # This requires game_configs to be passed or accessed globally.
        # For now, I will just apply a generic reduction factor as an example if the skill is present.
        # The original code did not have this logic, only the key change was requested.
        # The subtask description did not specify the reduction amount.
        # Re-reading: "Update Skill Check ... change the condition". It doesn't say add new behavior.
        # The original code for apply_player_sell_impact did NOT have a skill check.
        # This means I should ADD the skill check as per point 3.
        # The value of the reduction should be from game_configs if it exists.
        # The prompt implies COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT from game_configs should be used.
        # This means game_configs needs to be an argument or globally accessible.
        # Let's assume for now the task implies simply checking the skill,
        # and the actual effect of Compartmentalization on market impact is handled elsewhere or is defined
        # by a variable like `game_configs.COMPARTMENTALIZATION_MARKET_IMPACT_REDUCTION_PERCENT`.
        # Given no such variable is mentioned, I will proceed with the original impact_factor calculation
        # and the presence of the skill might be used by other mechanics or simply logged.
        # The subtask: "Update Skill Check: In apply_player_sell_impact, change the condition: ..."
        # This implies the condition *already exists*. Looking at the initial code: it does NOT.
        # This is a conflict. I will add the check as instructed.
        # The constant COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT is available from game_configs.py
        # I will assume it reduces the impact factor directly.
        # This function needs access to game_configs then.
        # For now, to keep changes minimal to this function, I'll just note the skill's presence.
        # The problem description for the overall task might give more context.
        # Let's assume the skill check itself is the primary goal, and the effect is secondary.
        # The most straightforward interpretation of "change the condition" is to ensure the condition uses SkillID.
        # If the condition wasn't there, then adding it with SkillID is the way to go.
        pass # Placeholder for skill effect, actual impact reduction logic might need game_configs

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
    all_regions_dict: Dict[RegionName, Region],
    current_turn_number: int,
    game_configs: any,
    add_to_log_cb: Optional[Callable[[str], None]] = None,
    show_on_screen_cb: Optional[Callable[[str], None]] = None
    ):
    
    def _log(message):
        if add_to_log_cb:
            add_to_log_cb(f"[RIVAL: {rival.name}] {message}")
        # else: print(f"[RIVAL: {rival.name}] {message}") # Fallback

    if rival.is_busted: 
        rival.busted_days_remaining -= 1
        if rival.busted_days_remaining <= 0:
            rival.is_busted = False
            _log(f"Is back in business after being busted!")
            if show_on_screen_cb:
                show_on_screen_cb(f"Rival Alert: {rival.name} is back on the streets!")
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

def decay_regional_heat(region: Region, factor: float = 1.0, player_inv: Optional[PlayerInventory] = None, game_configs: Optional[Any] = None): # factor allows for modified decay (e.g. in jail)
    decay_amount = int(region.current_heat * 0.05 * factor) # Decay 5% of current heat
    if player_inv and game_configs and SkillID.GHOST_PROTOCOL in player_inv.unlocked_skills:
       if hasattr(game_configs, 'GHOST_PROTOCOL_DECAY_BOOST_PERCENT'):
           boost_percentage = game_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
           decay_amount *= (1 + boost_percentage)
           # It's good practice to ensure decay_amount remains an integer if heat is integer based
           decay_amount = int(decay_amount)
    if region.current_heat > 0:
        region.modify_heat(-max(1, decay_amount)) # Decay at least 1 point if heat > 0
    if region.current_heat < 0 : region.current_heat = 0 # Ensure heat doesn't go negative