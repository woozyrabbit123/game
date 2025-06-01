"""Game state management module."""
import random
from typing import Dict, List, Optional

from .core.enums import CryptoCoin, DrugQuality, RegionName
from .core.ai_rival import AIRival
from .core.region import Region # Assuming Region class has a 'name' attribute and a 'to_dict()' method
from . import game_configs

class GameState:
    def __init__(self):
        self.current_crypto_prices: Dict[CryptoCoin, float] = {}
        self.ai_rivals: List[AIRival] = []
        self.all_regions: Dict[RegionName, Region] = {}
        self.current_player_region: Optional[Region] = None
        self.informant_unavailable_until_day: Optional[int] = None
        self.current_day: int = 1

        # Initialize core game state and world regions
        self._initialize_core_state()
        self._initialize_world_regions()

    def _initialize_core_state(self):
        """Initializes or resets core game attributes like crypto prices, rivals, day."""
        self.current_crypto_prices = game_configs.CRYPTO_PRICES_INITIAL.copy()
        self.ai_rivals = []
        self.informant_unavailable_until_day = None
        self.current_day = 1

    def initialize_crypto_prices(self, initial_prices: Dict[CryptoCoin, float]):
        """
        Sets the initial prices for cryptocurrencies.
        Can be used to override defaults or set prices if not done at initialization.
        """
        self.current_crypto_prices = initial_prices.copy()

    def update_daily_crypto_prices(self, volatility_map: Dict[CryptoCoin, float], min_prices_map: Dict[CryptoCoin, float]):
        """Updates cryptocurrency prices based on their volatility."""
        if not self.current_crypto_prices:
            # This case should ideally be handled by ensuring _initialize_core_state is called in __init__
            print("Warning: Crypto prices were not initialized before update. Initializing with defaults.")
            self.current_crypto_prices = game_configs.CRYPTO_PRICES_INITIAL.copy()

        for coin, price in self.current_crypto_prices.items():
            if coin in volatility_map:
                change_percent = random.uniform(-volatility_map[coin], volatility_map[coin])
                new_price = price * (1 + change_percent)
                min_price = min_prices_map.get(coin, 0.01) # Ensure a minimum price
                new_price = max(min_price, new_price)
                self.current_crypto_prices[coin] = round(new_price, 2)

    def _initialize_world_regions(self):
        """
        Initialize all game regions with their drug markets.
        Region details (name, drugs, prices, stock) are defined here.
        This method populates self.all_regions.
        """
        # Structure: (Enum, String Name, List of Drugs)
        # Drug Structure: (Name, BasePrice, MaxPrice, DemandFactor, Qualities)
        # Qualities: {DrugQuality_Enum: (min_stock, max_stock)}
        region_definitions = [
            (RegionName.DOWNTOWN, RegionName.DOWNTOWN.value, [
                ("Weed", 50, 80, 1, {DrugQuality.STANDARD: (100,200)}),
                ("Pills", 100, 150, 2, {DrugQuality.STANDARD: (40,80), DrugQuality.CUT: (60,120)}),
                ("Coke", 1000, 1500, 3, {DrugQuality.PURE: (10,25), DrugQuality.STANDARD: (15,50), DrugQuality.CUT: (20,60)})
            ]),
            (RegionName.DOCKS, RegionName.DOCKS.value, [
                ("Weed", 40, 70, 1, {DrugQuality.STANDARD: (100,300)}),
                ("Speed", 120, 180, 2, {DrugQuality.STANDARD: (30,90), DrugQuality.CUT: (50,100)}),
                ("Heroin", 600, 900, 3, {DrugQuality.PURE: (5,15), DrugQuality.STANDARD: (10,30)})
            ]),
            (RegionName.SUBURBS, RegionName.SUBURBS.value, [
                ("Weed", 60, 100, 1, {DrugQuality.STANDARD: (20,60)}),
                ("Pills", 110, 170, 2, {DrugQuality.STANDARD: (20,50), DrugQuality.PURE: (5,15)})
            ]),
            (RegionName.INDUSTRIAL, RegionName.INDUSTRIAL.value, [
                ("Weed", 45, 75, 1, {DrugQuality.STANDARD: (150,250)}),
                ("Speed", 110, 170, 2, {DrugQuality.STANDARD: (40,100), DrugQuality.CUT: (60,140), DrugQuality.PURE: (10,30)}),
                ("Coke", 950, 1400, 3, {DrugQuality.PURE: (8,20), DrugQuality.STANDARD: (12,40), DrugQuality.CUT: (18,55)})
            ]),
            (RegionName.COMMERCIAL, RegionName.COMMERCIAL.value, [
                ("Weed", 55, 90, 1, {DrugQuality.STANDARD: (80,150)}),
                ("Pills", 105, 160, 2, {DrugQuality.STANDARD: (25,60), DrugQuality.PURE: (8,20), DrugQuality.CUT: (40,80)}),
                ("Heroin", 580, 850, 3, {DrugQuality.PURE: (3,12), DrugQuality.STANDARD: (8,25), DrugQuality.CUT: (15,40)})
            ]),
            (RegionName.UNIVERSITY_HILLS, RegionName.UNIVERSITY_HILLS.value, [
                ("Weed", 70, 110, 1, {DrugQuality.STANDARD: (50,100)}),
                ("Pills", 120, 180, 2, {DrugQuality.STANDARD: (30,60), DrugQuality.PURE: (10,20)}),
                ("Speed", 130, 190, 2, {DrugQuality.CUT: (40,80), DrugQuality.STANDARD: (20,50)})
            ]),
            (RegionName.RIVERSIDE, RegionName.RIVERSIDE.value, [
                ("Weed", 40, 65, 1, {DrugQuality.STANDARD: (120,250)}),
                ("Heroin", 550, 800, 3, {DrugQuality.STANDARD: (10,25), DrugQuality.CUT: (15,35)})
            ]),
            (RegionName.AIRPORT_DISTRICT, RegionName.AIRPORT_DISTRICT.value, [
                ("Coke", 1100, 1600, 3, {DrugQuality.PURE: (15,30), DrugQuality.STANDARD: (20,40)}),
                ("Speed", 150, 220, 2, {DrugQuality.PURE: (20,40), DrugQuality.STANDARD: (30,60)})
            ]),
            (RegionName.OLD_TOWN, RegionName.OLD_TOWN.value, [
                ("Pills", 90, 140, 2, {DrugQuality.STANDARD: (50,100), DrugQuality.CUT: (70,130)}),
                ("Heroin", 620, 920, 3, {DrugQuality.CUT: (20,50), DrugQuality.STANDARD: (10,30), DrugQuality.PURE: (5,10)})
            ])
        ]

        self.all_regions = {} # Clear any existing regions
        for region_enum, region_name_str, drugs_data in region_definitions:
            # Assuming Region constructor takes the string name (e.g., "Downtown")
            region = Region(region_name_str)
            for drug_name, base_price, max_price, demand_factor, qualities_stock_ranges in drugs_data:
                # Generate random stock for each quality based on its min/max range
                quality_stock_map = {
                    quality_enum: random.randint(min_val, max_val)
                    for quality_enum, (min_val, max_val) in qualities_stock_ranges.items()
                }
                region.initialize_drug_market(drug_name, base_price, max_price, demand_factor, quality_stock_map)
            self.all_regions[region_enum] = region # Store with Enum as key

        # After all regions and their markets are initialized, restock them
        for region_obj in self.all_regions.values():
            if hasattr(region_obj, 'restock_market'): # Check if method exists
                region_obj.restock_market()
            else:
                print(f"Warning: Region {region_obj.name} does not have a restock_market method.")


    def set_current_player_region(self, region_name: RegionName):
        """Sets the current player's region using the RegionName enum."""
        if region_name in self.all_regions:
            self.current_player_region = self.all_regions[region_name]
        else:
            # This could raise an error or log a warning, depending on desired strictness
            print(f"Warning: Attempted to set current region to an unknown or uninitialized region: {region_name}")

    def get_current_player_region(self) -> Optional[Region]:
        """Returns the current player's region object. Can be None if not set."""
        return self.current_player_region

    def get_all_regions(self) -> Dict[RegionName, Region]:
        """Returns a dictionary of all regions, keyed by RegionName enum."""
        return self.all_regions

    def get_game_state_summary(self) -> Dict: # Renamed from the original get_game_state
        """
        Get a summary of the current game state.
        Useful for UI display or saving game state.
        Assumes Region objects have a 'name' attribute for their string name.
        """
        player_region_name_str = self.current_player_region.name.value if self.current_player_region and self.current_player_region.name else None

        # For 'all_regions', create a summary (e.g., names or simplified dicts)
        # rather than returning full Region objects directly in a summary.
        all_regions_summary = {
            name_enum.value: region.name
            for name_enum, region in self.all_regions.items()
        }

        return {
            'current_day': self.current_day,
            'current_player_region_name': player_region_name_str,
            'crypto_prices': self.current_crypto_prices, # Consider if this needs deepcopy for safety
            'ai_rivals_count': len(self.ai_rivals), # Example: sending count instead of full objects
            'informant_unavailable_until_day': self.informant_unavailable_until_day,
            'all_region_names': list(all_regions_summary.keys()) # Or send all_regions_summary itself
        }

# Placeholder for testing the GameState class structure.
# This would typically be part of your main application setup or test suite.
if __name__ == '__main__':
    # Create a GameState instance. This will call __init__ and internal initializers.
    game = GameState()
    
    # Example: Set player's starting region using the RegionName enum
    start_region_enum = RegionName.DOWNTOWN
    game.set_current_player_region(start_region_enum)
    
    print(f"--- Initial Game State ---")
    print(f"Current day: {game.current_day}")
    
    player_region = game.get_current_player_region()
    if player_region: # Check if a region is set
        print(f"Current player region: {player_region.name}") # Assumes Region has a 'name' attribute
    else:
        print("Current player region: None")

    print(f"Crypto prices: {game.current_crypto_prices}")

    # Simulate advancing a day and updating crypto prices
    game.current_day += 1
    # Ensure game_configs has these attributes defined for the update function
    if hasattr(game_configs, 'CRYPTO_VOLATILITY') and hasattr(game_configs, 'CRYPTO_MIN_PRICES'):
        game.update_daily_crypto_prices(game_configs.CRYPTO_VOLATILITY, game_configs.CRYPTO_MIN_PRICES)
    else:
        print("Warning: CRYPTO_VOLATILITY or CRYPTO_MIN_PRICES not found in game_configs. Skipping crypto update for simulation.")

    print(f"\n--- Game State After One Day ---")
    print(f"Current day: {game.current_day}")
    print(f"Updated crypto prices: {game.current_crypto_prices}")

    # Get and print the game state summary
    summary = game.get_game_state_summary()
    print(f"\n--- Game State Summary ---")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Example of how a specific region's data might be accessed (if needed)
    # print("\n--- Accessing Specific Region Data (Example) ---")
    # if RegionName.DOWNTOWN in game.all_regions:
    #     downtown_region = game.all_regions[RegionName.DOWNTOWN]
    #     print(f"Data for {downtown_region.name}:")
    #     # This part is highly dependent on the structure of your Region and DrugMarket classes
    #     # For example, if Region has a method to describe its market:
    #     # if hasattr(downtown_region, 'describe_market'):
    #     #     downtown_region.describe_market()
    # else:
    #     print(f"{RegionName.DOWNTOWN.value} not found in initialized regions.")