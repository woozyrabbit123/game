#!/usr/bin/env python3
"""
Pygame UI launcher for Project Narco-Syndicate.
This script launches the pygame-based graphical interface.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.player_inventory import PlayerInventory
from src.core.ai_rival import AIRival
from src.core.enums import DrugName, RegionName
import src.game_state as game_state
import src.game_configs as game_configs

def main():
    print("Starting Project Narco-Syndicate (Pygame UI)...")
    
    # Initialize core game components
    player_inv = PlayerInventory()    # Initialize game state
    game_state.initialize_global_state(game_configs)    # Initialize AI Rivals
    ai_rivals_list = [
        AIRival(name="The Chemist", primary_drug=DrugName.PILLS, primary_region_name=RegionName.DOWNTOWN, aggression=0.6, activity_level=0.7),
        AIRival(name="Silas", primary_drug=DrugName.COKE, primary_region_name=RegionName.DOWNTOWN, aggression=0.8, activity_level=0.5),
        AIRival(name="Dockmaster Jones", primary_drug=DrugName.SPEED, primary_region_name=RegionName.DOCKS, aggression=0.5, activity_level=0.6),
        AIRival(name="Mama Rosa", primary_drug=DrugName.WEED, primary_region_name=RegionName.SUBURBS, aggression=0.4, activity_level=0.8),
        AIRival(name="Sergei", primary_drug=DrugName.HEROIN, primary_region_name=RegionName.DOCKS, aggression=0.7, activity_level=0.6)
    ]
    game_state.ai_rivals = ai_rivals_list

    # Set initial region
    if game_state.all_regions:
        try:
            current_region_instance = game_state.all_regions[RegionName.DOWNTOWN]
        except KeyError:
            current_region_instance = list(game_state.all_regions.values())[0]
        game_state.set_current_player_region(current_region_instance)
    else:
        print("Fatal Error: Regions not initialized in game_state. Exiting.")
        sys.exit(1)

    # Launch Pygame UI
    try:
        from src.ui_pygame.app import game_loop
        print("Launching game window...")
        game_loop(player_inv, current_region_instance, game_state, game_configs)
    except ImportError as e:
        print(f"Pygame UI module not found or Pygame not installed correctly: {e}")
    except Exception as e:
        print(f"An error occurred while running the Pygame UI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
