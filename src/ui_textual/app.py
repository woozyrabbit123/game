from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import VerticalScroll, Horizontal, Vertical, ScrollableContainer 
from textual.widgets import Log 

from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..core.enums import DrugQuality, DrugName, RegionName, CryptoCoin
from ..game_state import GameState # Updated import
from .. import game_configs # Import the module itself
# from ..game_configs import ( # Specific imports also fine, but module is often passed
#     PLAYER_STARTING_CASH, PLAYER_MAX_CAPACITY, CRYPTO_PRICES_INITIAL,
#     HEAT_FROM_SELLING_DRUG_TIER, CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE,
#     POLICE_STOP_HEAT_THRESHOLD, SKILL_MARKET_INTUITION_COST, SKILL_DIGITAL_FOOTPRINT_COST,
#     DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT, CAPACITY_UPGRADE_COST_INITIAL,
#     CAPACITY_UPGRADE_COST_MULTIPLIER, CAPACITY_UPGRADE_AMOUNT, SECURE_PHONE_COST,
#     SECURE_PHONE_HEAT_REDUCTION_PERCENT, GHOST_NETWORK_ACCESS_COST_DC,
#     LAUNDERING_FEE_PERCENT, LAUNDERING_DELAY_DAYS, HEAT_FROM_CRYPTO_TRANSACTION,
#     SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT, TECH_CONTACT_FEE_PERCENT
# )
import random 
from ..core.ai_rival import AIRival
import sys

# Import custom widgets (assuming these are for a Textual version, not directly used by pygame_ui launch)
# from narco_widgets import ( ... ) 
# from ui.text_ui_handlers import check_and_trigger_police_stop, handle_police_stop_event

# This main script is now primarily for launching the Pygame UI.
# The Textual App class (NarcoApp) is not used when pygame_ui.py is the main UI.

if __name__ == "__main__":
    # --- Initialize Core Game Components ---
    player_inv = PlayerInventory() 
    game_state_instance = GameState() # Instantiate GameState
    # game_configs_module remains game_configs (imported module)

    # Initialization of game state (regions, crypto prices, etc.) is now handled by GameState constructor.
    
    # Initialize AI Rivals
    ai_rivals_list = [
        AIRival(name="The Chemist", primary_drug=DrugName.PILLS, primary_region_name=RegionName.DOWNTOWN, aggression=0.6, activity_level=0.7),
        AIRival(name="Silas", primary_drug=DrugName.COKE, primary_region_name=RegionName.DOWNTOWN, aggression=0.8, activity_level=0.5),
        AIRival(name="Dockmaster Jones", primary_drug=DrugName.SPEED, primary_region_name=RegionName.DOCKS, aggression=0.5, activity_level=0.6),
        AIRival(name="Mama Rosa", primary_drug=DrugName.WEED, primary_region_name=RegionName.SUBURBS, aggression=0.4, activity_level=0.8),
        AIRival(name="Sergei", primary_drug=DrugName.HEROIN, primary_region_name=RegionName.DOCKS, aggression=0.7, activity_level=0.6)
    ]
    game_state_instance.ai_rivals = ai_rivals_list

    # Set initial player region
    initial_region_name = RegionName.DOWNTOWN
    game_state_instance.set_current_player_region(initial_region_name)
    current_region_instance = game_state_instance.get_current_player_region()

    if not current_region_instance:
        print(f"Fatal Error: Initial region {initial_region_name.value} could not be set or found. Exiting.")
        sys.exit(1)

    # --- Launch Pygame UI ---
    try:
        from ..ui_pygame.app import game_loop
        # Pass the GameState instance and the game_configs module
        game_loop(player_inv, current_region_instance, game_state_instance, game_configs)
    except ImportError as e:
        print(f"Pygame UI module not found or Pygame not installed correctly: {e}")
    except Exception as e:
        print(f"An error occurred while running the Pygame UI: {e}")
        import traceback
        traceback.print_exc()
