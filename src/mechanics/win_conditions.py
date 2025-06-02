# src/mechanics/win_conditions.py
"""
Functions to check if any of the game's win conditions have been met.
"""
from typing import TYPE_CHECKING, Optional, Dict, Any

from ..core.enums import SkillID, ContactID, DrugName, DrugQuality, CryptoCoin
from .. import narco_configs as game_configs

if TYPE_CHECKING:
    from ..core.player_inventory import PlayerInventory
    from ..game_state import GameState


def _calculate_net_worth(player_inventory: "PlayerInventory", game_state: "GameState") -> float:
    """Calculates the player's total net worth."""
    cash_value = player_inventory.cash
    
    crypto_value = 0.0
    for coin, balance in player_inventory.crypto_wallet.items():
        crypto_value += balance * game_state.current_crypto_prices.get(coin, 0.0)
    
    # Add staked DrugCoin value (staked amount + pending rewards)
    staked_dc_amount = player_inventory.staked_drug_coin.get("staked_amount", 0.0)
    pending_dc_rewards = player_inventory.staked_drug_coin.get("pending_rewards", 0.0)
    dc_price = game_state.current_crypto_prices.get(CryptoCoin.DRUG_COIN, 0.0)
    crypto_value += (staked_dc_amount + pending_dc_rewards) * dc_price

    drug_stash_value = 0.0
    # Use base prices for drugs to avoid fluctuations from market conditions for net worth
    # This requires accessing REGION_DEFINITIONS to find a base price.
    # For simplicity, we'll find the first definition of a drug and use its base_buy_price.
    # A more robust approach would be to have a separate list of base values for each drug.
    
    # Create a quick lookup for drug base prices from the first region that defines them
    # This is a simplified approach for valuation.
    drug_base_prices: Dict[DrugName, float] = {}
    if hasattr(game_configs, 'REGION_DEFINITIONS'):
        for region_def in game_configs.REGION_DEFINITIONS:
            for drug_tuple in region_def[2]: # drug_def_tuple is (drug_name_str, base_price, max_price, ...)
                try:
                    drug_name_enum = DrugName(drug_tuple[0])
                    if drug_name_enum not in drug_base_prices:
                        drug_base_prices[drug_name_enum] = float(drug_tuple[1]) # base_price
                except ValueError:
                    continue # Invalid drug name string in config

    for drug_name_enum, qualities in player_inventory.items.items():
        base_price = drug_base_prices.get(drug_name_enum, 0.0) # Default to 0 if not found
        for quality, quantity in qualities.items():
            # Could apply quality multipliers here if desired, but using base price is simpler
            drug_stash_value += quantity * base_price 
            
    return cash_value + crypto_value + drug_stash_value


def check_target_net_worth(player_inventory: "PlayerInventory", game_state: "GameState", game_configs_module: Any) -> bool:
    """Checks for the Target Net Worth win condition."""
    net_worth = _calculate_net_worth(player_inventory, game_state)
    return net_worth >= game_configs_module.TARGET_NET_WORTH_AMOUNT

def check_cartel_crown(player_inventory: "PlayerInventory", game_state: "GameState", game_configs_module: Any) -> bool:
    """Checks for The Cartel Crown win condition (simplified)."""
    net_worth = _calculate_net_worth(player_inventory, game_state)
    if net_worth < game_configs_module.CARTEL_CROWN_NET_WORTH_AMOUNT:
        return False
    
    # Simplified: Check if MASTER_NEGOTIATOR skill is unlocked
    if SkillID.MASTER_NEGOTIATOR.value not in player_inventory.unlocked_skills:
        return False
        
    # Placeholder for regional dominance:
    # For now, just having the skill and net worth is enough.
    # A more complex check would involve game_state.player_regional_sales_profit or similar.
    # Example:
    # regions_dominated = 0
    # for region_name, profit in game_state.player_regional_sales_profit.items():
    #     if profit > SOME_THRESHOLD: # And potentially compare to AI rivals
    #         regions_dominated +=1
    # if regions_dominated < game_configs_module.CARTEL_CROWN_REGIONS_DOMINATED:
    #     return False
        
    return True

def check_digital_empire(player_inventory: "PlayerInventory", game_state: "GameState", game_configs_module: Any) -> bool:
    """Checks for the Digital Empire win condition."""
    crypto_value = 0.0
    for coin, balance in player_inventory.crypto_wallet.items():
        crypto_value += balance * game_state.current_crypto_prices.get(coin, 0.0)
    
    staked_dc_amount = player_inventory.staked_drug_coin.get("staked_amount", 0.0)
    pending_dc_rewards = player_inventory.staked_drug_coin.get("pending_rewards", 0.0)
    dc_price = game_state.current_crypto_prices.get(CryptoCoin.DRUG_COIN, 0.0)
    crypto_value += (staked_dc_amount + pending_dc_rewards) * dc_price
        
    if crypto_value < game_configs_module.DIGITAL_EMPIRE_CRYPTO_VALUE:
        return False
    
    if not (SkillID.GHOST_PROTOCOL.value in player_inventory.unlocked_skills and \
            SkillID.DIGITAL_FOOTPRINT.value in player_inventory.unlocked_skills):
        return False
        
    if not player_inventory.has_secure_phone:
        return False
        
    return True

def check_perfect_retirement(player_inventory: "PlayerInventory", game_state: "GameState", game_configs_module: Any) -> bool:
    """Checks for the Perfect Retirement win condition."""
    net_worth = _calculate_net_worth(player_inventory, game_state)
    if net_worth < game_configs_module.PERFECT_RETIREMENT_NET_WORTH_AMOUNT:
        return False
        
    if not (player_inventory.debt_payment_1_paid and \
            player_inventory.debt_payment_2_paid and \
            player_inventory.debt_payment_3_paid):
        return False
        
    # Average regional heat
    total_heat = 0
    num_regions = 0
    if game_state.all_regions:
        for region in game_state.all_regions.values():
            total_heat += region.current_heat
            num_regions += 1
    average_heat = total_heat / num_regions if num_regions > 0 else 0
    
    if average_heat >= game_configs_module.PERFECT_RETIREMENT_MAX_AVG_HEAT:
        return False
        
    informant_trust = player_inventory.contact_trusts.get(ContactID.INFORMANT, 0)
    if informant_trust < game_configs_module.PERFECT_RETIREMENT_MIN_INFORMANT_TRUST:
        return False
        
    return True

WIN_CONDITION_CHECKS = {
    "Target Net Worth": check_target_net_worth,
    "The Cartel Crown": check_cartel_crown,
    "Digital Empire": check_digital_empire,
    "Perfect Retirement": check_perfect_retirement,
}
[end of src/mechanics/win_conditions.py]
