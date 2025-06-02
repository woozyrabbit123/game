#!/usr/bin/env python3
"""
Pygame UI launcher for Project Narco-Syndicate.
This script launches the pygame-based graphical interface.
"""

import sys
from pathlib import Path
import traceback # Will remove if not needed after logging changes
from src.utils.logger import get_logger

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.player_inventory import PlayerInventory
from src.core.ai_rival import AIRival
from src.core.enums import DrugName, RegionName
from src.game_state import GameState  # Updated import
import src.narco_configs as game_configs


logger = get_logger(__name__)

def main():
    logger.info("Starting Project Narco-Syndicate (Pygame UI)...")

    # Initialize core game components
    player_inv = PlayerInventory()
    game_state_instance = GameState()  # Instantiate GameState

    # Initialize AI Rivals
    ai_rivals_list = [
        AIRival(
            name="The Chemist",
            primary_drug=DrugName.PILLS,
            primary_region_name=RegionName.DOWNTOWN,
            aggression=0.6,
            activity_level=0.7,
        ),
        AIRival(
            name="Silas",
            primary_drug=DrugName.COKE,
            primary_region_name=RegionName.DOWNTOWN,
            aggression=0.8,
            activity_level=0.5,
        ),
        AIRival(
            name="Dockmaster Jones",
            primary_drug=DrugName.SPEED,
            primary_region_name=RegionName.DOCKS,
            aggression=0.5,
            activity_level=0.6,
        ),
        AIRival(
            name="Mama Rosa",
            primary_drug=DrugName.WEED,
            primary_region_name=RegionName.SUBURBS,
            aggression=0.4,
            activity_level=0.8,
        ),
        AIRival(
            name="Sergei",
            primary_drug=DrugName.HEROIN,
            primary_region_name=RegionName.DOCKS,
            aggression=0.7,
            activity_level=0.6,
        ),
    ]
    game_state_instance.ai_rivals = ai_rivals_list

    # Set initial player region
    # Regions are initialized in GameState constructor.
    # We need to set the current player region and get the instance.
    initial_region_name = RegionName.DOWNTOWN  # Define the starting region name
    game_state_instance.set_current_player_region(initial_region_name)
    current_region_instance = game_state_instance.get_current_player_region()

    if not current_region_instance:
        # This should ideally not happen if initial_region_name is valid and regions are initialized.
        logger.critical(
            f"Initial region {initial_region_name.value} could not be set or found. Exiting."
        )
        sys.exit(1)

    # Launch Pygame UI
    try:
        from src.ui_pygame.app import game_loop

        logger.info("Launching game window...")
        # Pass the GameState instance to the game_loop
        game_loop(
            player_inv, current_region_instance, game_state_instance, game_configs
        )
    except ImportError as e:
        logger.error(f"Pygame UI module not found or Pygame not installed correctly: {e}")
    except Exception as e:
        logger.exception(f"An error occurred while running the Pygame UI: {e}")
        # import traceback # No longer needed
        # traceback.print_exc() # No longer needed


if __name__ == "__main__":
    main()
