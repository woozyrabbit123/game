from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import VerticalScroll, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Log,
)  # Not used in __main__ but kept for potential future use

# from ..core.player_inventory import PlayerInventory # No longer used due to __main__ block changes
# from ..core.region import Region # No longer used due to __main__ block changes
# from ..core.enums import (
#     DrugQuality,
#     DrugName,
#     RegionName,
#     CryptoCoin,
# )  # No longer used due to __main__ block changes
# from ..game_state import GameState # No longer used due to __main__ block changes
# from .. import game_configs  # No longer used due to __main__ block changes
# from typing import List, Optional, Any  # No longer used due to __main__ block changes

# from ..game_configs import (
#     PLAYER_STARTING_CASH, PLAYER_MAX_CAPACITY, CRYPTO_PRICES_INITIAL,
#     HEAT_FROM_SELLING_DRUG_TIER, CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE,
#     POLICE_STOP_HEAT_THRESHOLD, SKILL_MARKET_INTUITION_COST, SKILL_DIGITAL_FOOTPRINT_COST,
#     DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT, CAPACITY_UPGRADE_COST_INITIAL,
#     CAPACITY_UPGRADE_COST_MULTIPLIER, CAPACITY_UPGRADE_AMOUNT, SECURE_PHONE_COST,
#     SECURE_PHONE_HEAT_REDUCTION_PERCENT, GHOST_NETWORK_ACCESS_COST_DC,
#     LAUNDERING_FEE_PERCENT, LAUNDERING_DELAY_DAYS, HEAT_FROM_CRYPTO_TRANSACTION,
#     SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT, TECH_CONTACT_FEE_PERCENT
# )
# import random # No longer used due to __main__ block changes
# from ..core.ai_rival import AIRival # No longer used due to __main__ block changes
# import sys # No longer used due to __main__ block changes

# Import custom widgets (assuming these are for a Textual version, not directly used by pygame_ui launch)
# from narco_widgets import ( ... )
# from ui.text_ui_handlers import check_and_trigger_police_stop, handle_police_stop_event

# This main script is now primarily for launching the Pygame UI.

if __name__ == "__main__":
    # This script was previously launching the Pygame UI.
    # The Textual UI is not currently implemented.
    # To run the Pygame UI, use run_pygame.py.
    pass
    # --- Initialize Core Game Components ---
    # player_inv: PlayerInventory = PlayerInventory()
    # game_state_instance: GameState = GameState()
    # game_configs_module: Any = game_configs  # game_configs is the imported module

    # Initialization of game state (regions, crypto prices, etc.) is handled by GameState constructor.

    # Initialize AI Rivals
    # ai_rivals_list: List[AIRival] = []
    # for rival_def in game_configs_module.AI_RIVAL_DEFINITIONS:
    #     ai_rivals_list.append(
    #         AIRival(
    #             name=rival_def["name"],
    #             primary_drug=rival_def["primary_drug"], # Assuming these are already Enum members in game_configs
    #             primary_region_name=rival_def["primary_region_name"], # Assuming these are already Enum members
    #             aggression=rival_def["aggression"],
    #             activity_level=rival_def["activity_level"],
    #         )
    #     )
    # game_state_instance.ai_rivals = ai_rivals_list

    # Set initial player region
    # initial_region_name_enum: RegionName = game_configs_module.PLAYER_STARTING_REGION_NAME
    # game_state_instance.set_current_player_region(initial_region_name_enum)
    # current_region_instance: Optional[Region] = (
    #     game_state_instance.get_current_player_region()
    # )

    # if not current_region_instance:
    #     print(
    #         f"Fatal Error: Initial region {initial_region_name_enum.value} could not be set or found. Exiting."
    #     )
    #     sys.exit(1)

    # --- Launch Pygame UI ---
    # try:
    #     from ..ui_pygame.app import (
    #         game_loop,
    #     )  # game_loop is expected to be (PlayerInventory, Optional[Region], GameState, Any) -> None

    #     game_loop(
    #         player_inv,
    #         current_region_instance,
    #         game_state_instance,
    #         game_configs_module,
    #     )
    # except ImportError as e_import:  # Renamed e
    #     print(
    #         f"Pygame UI module not found or Pygame not installed correctly: {e_import}"
    #     )
    # except Exception as e_general:  # Renamed e
    #     print(f"An error occurred while running the Pygame UI: {e}")
    #     import traceback

    #     traceback.print_exc()
