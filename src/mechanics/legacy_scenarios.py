# src/mechanics/legacy_scenarios.py
"""
Functions to check if any of the game's mid-game legacy scenarios have been met
and to apply their bonuses.
"""
from typing import TYPE_CHECKING, Optional, Dict, Any, List

from ..core.enums import SkillID, ContactID, RegionName, CryptoCoin # Added RegionName, CryptoCoin
from .. import narco_configs as game_configs # For config constants

if TYPE_CHECKING:
    from ..core.player_inventory import PlayerInventory
    from ..game_state import GameState

# Helper to calculate crypto portfolio value (similar to win_conditions)
def _calculate_crypto_portfolio_value(player_inventory: "PlayerInventory", game_state: "GameState") -> float:
    crypto_value = 0.0
    for coin, balance in player_inventory.crypto_wallet.items():
        crypto_value += balance * game_state.current_crypto_prices.get(coin, 0.0)
    
    staked_dc_amount = player_inventory.staked_drug_coin.get("staked_amount", 0.0)
    pending_dc_rewards = player_inventory.staked_drug_coin.get("pending_rewards", 0.0)
    dc_price = game_state.current_crypto_prices.get(CryptoCoin.DRUG_COIN, 0.0)
    crypto_value += (staked_dc_amount + pending_dc_rewards) * dc_price
    return crypto_value

def check_regional_baron(player_inventory: "PlayerInventory", game_state: "GameState", game_configs_module: Any) -> Optional[str]:
    """
    Checks for the Regional Baron legacy scenario.
    Returns the name of the scenario if achieved, else None.
    """
    if "Regional Baron" in game_state.achieved_legacy_scenarios:
        return None

    regions_dominated_count = 0
    for region_name, profit in game_state.player_sales_profit_by_region.items():
        if profit >= game_configs_module.REGIONAL_BARON_SALES_THRESHOLD_PER_REGION:
            regions_dominated_count += 1
    
    if regions_dominated_count >= game_configs_module.REGIONAL_BARON_REGIONS_REQUIRED:
        return "Regional Baron"
    return None

def check_crypto_whale(player_inventory: "PlayerInventory", game_state: "GameState", game_configs_module: Any) -> Optional[str]:
    """
    Checks for the Crypto Whale legacy scenario.
    Returns the name of the scenario if achieved, else None.
    """
    if "Crypto Whale" in game_state.achieved_legacy_scenarios:
        return None

    portfolio_value = _calculate_crypto_portfolio_value(player_inventory, game_state)
    
    if portfolio_value >= game_configs_module.CRYPTO_WHALE_PORTFOLIO_VALUE_MIDGAME and \
       player_inventory.large_crypto_transactions_completed >= game_configs_module.CRYPTO_WHALE_MIN_LARGE_TRANSACTIONS:
        return "Crypto Whale"
    return None

def check_the_cleaner(player_inventory: "PlayerInventory", game_state: "GameState", game_configs_module: Any) -> Optional[str]:
    """
    Checks for The Cleaner legacy scenario.
    Returns the name of the scenario if achieved, else None.
    """
    if "The Cleaner" in game_state.achieved_legacy_scenarios:
        return None

    if player_inventory.total_laundered_cash < game_configs_module.THE_CLEANER_TOTAL_LAUNDERED_THRESHOLD:
        return None

    tech_contact_trust = player_inventory.contact_trusts.get(ContactID.TECH_CONTACT, 0)
    if tech_contact_trust < game_configs_module.THE_CLEANER_MIN_TECH_CONTACT_TRUST:
        return None

    total_heat = 0
    num_regions = 0
    if game_state.all_regions:
        for region in game_state.all_regions.values():
            total_heat += region.current_heat
            num_regions += 1
    average_heat = total_heat / num_regions if num_regions > 0 else float('inf') # Avoid division by zero; high if no regions

    if average_heat >= game_configs_module.THE_CLEANER_MAX_AVG_HEAT_MIDGAME:
        return None
        
    return "The Cleaner"

# Dictionary to hold all scenario check functions
LEGACY_SCENARIO_CHECKS: Dict[str, Callable[["PlayerInventory", "GameState", Any], Optional[str]]] = {
    "Regional Baron": check_regional_baron,
    "Crypto Whale": check_crypto_whale,
    "The Cleaner": check_the_cleaner,
}

def apply_legacy_scenario_bonus(
    scenario_name: str, 
    player_inventory: "PlayerInventory", 
    game_state: "GameState", 
    game_configs_module: Any
) -> List[str]:
    """Applies the bonus for achieving a legacy scenario and returns UI messages."""
    ui_messages = []
    if scenario_name == "Regional Baron":
        reward = game_configs_module.LEGACY_SCENARIO_CASH_REWARD
        player_inventory.cash += reward
        ui_messages.append(f"Legacy Achieved: Regional Baron! +${reward:,.0f} cash.")
    elif scenario_name == "Crypto Whale":
        reward = game_configs_module.LEGACY_SCENARIO_SKILL_POINTS_REWARD
        player_inventory.skill_points += reward
        ui_messages.append(f"Legacy Achieved: Crypto Whale! +{reward} Skill Point(s).")
    elif scenario_name == "The Cleaner":
        reduction = game_configs_module.THE_CLEANER_HEAT_REDUCTION_BONUS
        for region in game_state.all_regions.values():
            region.modify_heat(-reduction)
        ui_messages.append(f"Legacy Achieved: The Cleaner! Heat reduced by {reduction} in all regions.")
    
    if scenario_name not in game_state.achieved_legacy_scenarios:
         game_state.achieved_legacy_scenarios.append(scenario_name)
         
    return ui_messages

[end of src/mechanics/legacy_scenarios.py]
