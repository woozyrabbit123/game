import random
from typing import Dict

from core.region import Region 
from core.ai_rival import AIRival # Assuming AIRival class is in core.ai_rival

def apply_player_buy_impact(region: Region, drug_name: str, quantity_bought: int):
    if drug_name not in region.drug_market_data: return
    impact_factor = (quantity_bought / 10) * 0.02; current_modifier = region.drug_market_data[drug_name]["player_buy_impact_modifier"]
    new_modifier = min(current_modifier + impact_factor, 1.25); region.drug_market_data[drug_name]["player_buy_impact_modifier"] = new_modifier

def apply_player_sell_impact(region: Region, drug_name: str, quantity_sold: int):
    if drug_name not in region.drug_market_data: return
    impact_factor = (quantity_sold / 10) * 0.02; current_modifier = region.drug_market_data[drug_name]["player_sell_impact_modifier"]
    new_modifier = max(current_modifier - impact_factor, 0.75); region.drug_market_data[drug_name]["player_sell_impact_modifier"] = new_modifier

def decay_player_market_impact(region: Region):
    for drug_name, data in region.drug_market_data.items():
        buy_mod = data["player_buy_impact_modifier"]
        if buy_mod > 1.0: data["player_buy_impact_modifier"] = max(1.0, buy_mod - 0.01)
        sell_mod = data["player_sell_impact_modifier"]
        if sell_mod < 1.0: data["player_sell_impact_modifier"] = min(1.0, sell_mod + 0.01)

def process_rival_turn(rival: AIRival, all_regions_dict: Dict[str, Region], current_turn_number: int):
    if rival.is_busted: return # Busted rivals don't act
    if rival.primary_region_name not in all_regions_dict: return
    region = all_regions_dict[rival.primary_region_name]
    if rival.primary_drug not in region.drug_market_data: return
    activity_chance = rival.activity_level * 0.7
    if random.random() < activity_chance:
        drug_data = region.drug_market_data[rival.primary_drug]
        if random.random() < rival.aggression: 
            impact = 0.1 + (rival.aggression * 0.2); current_mod = drug_data["rival_demand_modifier"]
            new_mod = min(current_mod * (1 + impact), 2.5); drug_data["rival_demand_modifier"] = new_mod
        else: 
            impact = 0.1 + ((1 - rival.aggression) * 0.2); current_mod = drug_data["rival_supply_modifier"]
            new_mod = max(current_mod * (1 - impact), 0.4); drug_data["rival_supply_modifier"] = new_mod
        drug_data["last_rival_activity_turn"] = current_turn_number

def decay_rival_market_impact(region: Region, current_turn_number: int):
    for drug_name, data in region.drug_market_data.items():
        if data.get("last_rival_activity_turn", -1) == -1: continue
        turns_since_activity = current_turn_number - data["last_rival_activity_turn"]
        if turns_since_activity > 3: 
            if data["rival_demand_modifier"] > 1.0: data["rival_demand_modifier"] = max(1.0, data["rival_demand_modifier"] - 0.05)
            elif data["rival_demand_modifier"] < 1.0: data["rival_demand_modifier"] = min(1.0, data["rival_demand_modifier"] + 0.05)
            if data["rival_supply_modifier"] < 1.0: data["rival_supply_modifier"] = min(1.0, data["rival_supply_modifier"] + 0.05)
            elif data["rival_supply_modifier"] > 1.0: data["rival_supply_modifier"] = max(1.0, data["rival_supply_modifier"] - 0.05)

def decay_regional_heat(region: Region):
    if region.current_heat > 0:
        region.modify_heat(-1)