"""
Manages the overall state of the game.

This module includes the `GameState` class, which is responsible for
tracking game progress, current day, player's current region, AI rivals,
cryptocurrency prices, and initializing the game world (regions and markets).
It provides methods to update and access various aspects of the game state.
"""

import random
from typing import Dict, List, Optional, Any, Tuple

from .core.enums import CryptoCoin, DrugQuality, DrugName, RegionName  # Added DrugName
from .core.ai_rival import AIRival
from .core.region import (
    Region,
)  # Assuming Region class has a 'name' attribute and a 'to_dict()' method
from . import game_configs


class GameState:
    """
    Represents and manages the overall state of the game.

    Attributes:
        current_crypto_prices (Dict[CryptoCoin, float]): Current prices of cryptocurrencies.
        ai_rivals (List[AIRival]): A list of AI rival objects in the game.
        all_regions (Dict[RegionName, Region]): A dictionary of all game regions,
            keyed by RegionName.
        current_player_region (Optional[Region]): The region object where the player
            is currently located.
        informant_unavailable_until_day (Optional[int]): Day until which the informant
            is unavailable due to a previous betrayal or event.
        current_day (int): The current day in the game.
    """

    def __init__(self) -> None:
        """Initializes the GameState, setting up core attributes and the game world."""
        self.current_crypto_prices: Dict[CryptoCoin, float] = {}
        self.ai_rivals: List[AIRival] = []
        self.all_regions: Dict[RegionName, Region] = {}
        self.current_player_region: Optional[Region] = None
        self.informant_unavailable_until_day: Optional[int] = None
        self.current_day: int = 1

        # Initialize core game state and world regions
        self._initialize_core_state()
        self._initialize_world_regions()

    def _initialize_core_state(self) -> None:
        """
        Initializes or resets core game attributes.

        This includes setting initial cryptocurrency prices, clearing the list of AI rivals,
        resetting informant availability, and setting the current day to 1.
        """
        self.current_crypto_prices = {} # Initialize as empty before safe population
        if hasattr(game_configs, "CRYPTO_PRICES_INITIAL") and isinstance(game_configs.CRYPTO_PRICES_INITIAL, dict):
            for coin_enum, price in game_configs.CRYPTO_PRICES_INITIAL.items():
                if not isinstance(coin_enum, CryptoCoin):
                    print(f"Warning: Invalid key in CRYPTO_PRICES_INITIAL: {coin_enum}. Expected CryptoCoin enum. Skipping.")
                    continue
                if not isinstance(price, (int, float)):
                    print(f"Warning: Invalid price value for {coin_enum.value} in CRYPTO_PRICES_INITIAL: {price}. Expected number. Skipping.")
                    continue
                self.current_crypto_prices[coin_enum] = float(price)
        else:
            print("Error: CRYPTO_PRICES_INITIAL not found in game_configs or is not a dictionary. Crypto prices not initialized.")
            # Optionally, populate with some hardcoded emergency defaults or raise error
            # For example: self.current_crypto_prices = {CryptoCoin.BITCOIN: 100.0}

        self.ai_rivals = []
        self.informant_unavailable_until_day = None  # Optional[int]
        self.current_day = 1  # int

    def initialize_crypto_prices(self, initial_prices: Dict[CryptoCoin, float]) -> None:
        """
        Sets the initial prices for cryptocurrencies.

        This method can be used to override default initial prices or to set prices
        if they were not configured during the GameState's main initialization.

        Args:
            initial_prices: A dictionary mapping CryptoCoin enums to their starting float prices.
        """
        self.current_crypto_prices = {} # Clear before setting
        if not isinstance(initial_prices, dict):
            print(f"Error: initialize_crypto_prices expects a dictionary, got {type(initial_prices)}. Prices not set.")
            return

        for coin_enum, price in initial_prices.items():
            if not isinstance(coin_enum, CryptoCoin):
                print(f"Warning: Invalid key in provided initial_prices: {coin_enum}. Expected CryptoCoin enum. Skipping.")
                continue
            if not isinstance(price, (int, float)):
                print(f"Warning: Invalid price value for {coin_enum.value} in provided initial_prices: {price}. Expected number. Skipping.")
                continue
            self.current_crypto_prices[coin_enum] = float(price)


    def update_daily_crypto_prices(
        self,
        volatility_map: Dict[CryptoCoin, float],
        min_prices_map: Dict[CryptoCoin, float],
    ) -> None:
        """
        Updates cryptocurrency prices for the current day based on their volatility.

        Each coin's price changes randomly within its defined volatility range.
        Prices are ensured to not fall below specified minimums.

        Args:
            volatility_map: A dictionary mapping CryptoCoin enums to their volatility factor (float).
            min_prices_map: A dictionary mapping CryptoCoin enums to their minimum possible price (float).
        """
        if not self.current_crypto_prices:
            print(
                "Warning: Crypto prices were not initialized before update. Initializing with defaults."
            )
            self.current_crypto_prices = game_configs.CRYPTO_PRICES_INITIAL.copy()

        for (
            coin,
            price,
        ) in self.current_crypto_prices.items():  # coin is CryptoCoin, price is float
            if coin in volatility_map:  # volatility_map is Dict[CryptoCoin, float]
                change_percent: float = random.uniform(
                    -volatility_map[coin], volatility_map[coin]
                )
                new_price: float = price * (1 + change_percent)

                default_min_price = 0.01 # Default if not in game_configs
                if hasattr(game_configs, "DEFAULT_MIN_CRYPTO_PRICE"):
                    default_min_price = game_configs.DEFAULT_MIN_CRYPTO_PRICE

                min_price: float = min_prices_map.get(
                    coin, default_min_price
                )
                new_price = max(min_price, new_price)
                self.current_crypto_prices[coin] = round(new_price, 2)

    def _initialize_world_regions(self) -> None:
        """
        Initializes all game regions, including their names and drug markets.
        TODO: Move region_definitions to game_configs.py for better modularity and easier modification.
        """
        import sys # For stderr
        print("Warning: Region definitions are currently hardcoded in GameState._initialize_world_regions. Consider moving to game_configs.py.", file=sys.stderr)

        # Region definitions, including available drugs, their base prices, demand factors,
        # and initial stock ranges for different qualities, are configured here.
        This method populates the `self.all_regions` dictionary.
        """
        # Structure: (RegionName Enum, String Name, List of DrugDefinitionTuple)
        # DrugDefinitionTuple: (DrugName str, BasePrice, MaxPrice, DemandFactor, QualitiesStockRanges)
        # QualitiesStockRanges: {DrugQuality_Enum: (min_stock, max_stock)}
        DrugDefinitionTuple = Tuple[
            str, int, int, int, Dict[DrugQuality, Tuple[int, int]]
        ]
        RegionDefinitionTuple = Tuple[RegionName, str, List[DrugDefinitionTuple]]

        region_definitions: List[RegionDefinitionTuple] = [
            (
                RegionName.DOWNTOWN,
                RegionName.DOWNTOWN.value,
                [
                    (
                        "Weed",
                        50,
                        80,
                        1,
                        {DrugQuality.STANDARD: (100, 200)},
                    ),  # DrugName will be converted to Enum or used as str
                    (
                        "Pills",
                        100,
                        150,
                        2,
                        {DrugQuality.STANDARD: (40, 80), DrugQuality.CUT: (60, 120)},
                    ),
                    (
                        "Coke",
                        1000,
                        1500,
                        3,
                        {
                            DrugQuality.PURE: (10, 25),
                            DrugQuality.STANDARD: (15, 50),
                            DrugQuality.CUT: (20, 60),
                        },
                    ),
                ],
            ),
            (
                RegionName.DOCKS,
                RegionName.DOCKS.value,
                [
                    ("Weed", 40, 70, 1, {DrugQuality.STANDARD: (100, 300)}),
                    (
                        "Speed",
                        120,
                        180,
                        2,
                        {DrugQuality.STANDARD: (30, 90), DrugQuality.CUT: (50, 100)},
                    ),
                    (
                        "Heroin",
                        600,
                        900,
                        3,
                        {DrugQuality.PURE: (5, 15), DrugQuality.STANDARD: (10, 30)},
                    ),
                ],
            ),
            (
                RegionName.SUBURBS,
                RegionName.SUBURBS.value,
                [
                    ("Weed", 60, 100, 1, {DrugQuality.STANDARD: (20, 60)}),
                    (
                        "Pills",
                        110,
                        170,
                        2,
                        {DrugQuality.STANDARD: (20, 50), DrugQuality.PURE: (5, 15)},
                    ),
                ],
            ),
            (
                RegionName.INDUSTRIAL,
                RegionName.INDUSTRIAL.value,
                [
                    ("Weed", 45, 75, 1, {DrugQuality.STANDARD: (150, 250)}),
                    (
                        "Speed",
                        110,
                        170,
                        2,
                        {
                            DrugQuality.STANDARD: (40, 100),
                            DrugQuality.CUT: (60, 140),
                            DrugQuality.PURE: (10, 30),
                        },
                    ),
                    (
                        "Coke",
                        950,
                        1400,
                        3,
                        {
                            DrugQuality.PURE: (8, 20),
                            DrugQuality.STANDARD: (12, 40),
                            DrugQuality.CUT: (18, 55),
                        },
                    ),
                ],
            ),
            (
                RegionName.COMMERCIAL,
                RegionName.COMMERCIAL.value,
                [
                    ("Weed", 55, 90, 1, {DrugQuality.STANDARD: (80, 150)}),
                    (
                        "Pills",
                        105,
                        160,
                        2,
                        {
                            DrugQuality.STANDARD: (25, 60),
                            DrugQuality.PURE: (8, 20),
                            DrugQuality.CUT: (40, 80),
                        },
                    ),
                    (
                        "Heroin",
                        580,
                        850,
                        3,
                        {
                            DrugQuality.PURE: (3, 12),
                            DrugQuality.STANDARD: (8, 25),
                            DrugQuality.CUT: (15, 40),
                        },
                    ),
                ],
            ),
            (
                RegionName.UNIVERSITY_HILLS,
                RegionName.UNIVERSITY_HILLS.value,
                [
                    ("Weed", 70, 110, 1, {DrugQuality.STANDARD: (50, 100)}),
                    (
                        "Pills",
                        120,
                        180,
                        2,
                        {DrugQuality.STANDARD: (30, 60), DrugQuality.PURE: (10, 20)},
                    ),
                    (
                        "Speed",
                        130,
                        190,
                        2,
                        {DrugQuality.CUT: (40, 80), DrugQuality.STANDARD: (20, 50)},
                    ),
                ],
            ),
            (
                RegionName.RIVERSIDE,
                RegionName.RIVERSIDE.value,
                [
                    ("Weed", 40, 65, 1, {DrugQuality.STANDARD: (120, 250)}),
                    (
                        "Heroin",
                        550,
                        800,
                        3,
                        {DrugQuality.STANDARD: (10, 25), DrugQuality.CUT: (15, 35)},
                    ),
                ],
            ),
            (
                RegionName.AIRPORT_DISTRICT,
                RegionName.AIRPORT_DISTRICT.value,
                [
                    (
                        "Coke",
                        1100,
                        1600,
                        3,
                        {DrugQuality.PURE: (15, 30), DrugQuality.STANDARD: (20, 40)},
                    ),
                    (
                        "Speed",
                        150,
                        220,
                        2,
                        {DrugQuality.PURE: (20, 40), DrugQuality.STANDARD: (30, 60)},
                    ),
                ],
            ),
            (
                RegionName.OLD_TOWN,
                RegionName.OLD_TOWN.value,
                [
                    (
                        "Pills",
                        90,
                        140,
                        2,
                        {DrugQuality.STANDARD: (50, 100), DrugQuality.CUT: (70, 130)},
                    ),
                    (
                        "Heroin",
                        620,
                        920,
                        3,
                        {
                            DrugQuality.CUT: (20, 50),
                            DrugQuality.STANDARD: (10, 30),
                            DrugQuality.PURE: (5, 10),
                        },
                    ),
                ],
            ),
        ]

        self.all_regions: Dict[RegionName, Region] = {}  # Clear any existing regions
        for region_idx, region_data_tuple in enumerate(region_definitions):
            try:
                if len(region_data_tuple) != 3:
                    print(f"Warning: Malformed region definition at index {region_idx}. Expected 3 elements, got {len(region_data_tuple)}. Skipping.", file=sys.stderr)
                    continue

                region_enum, region_name_str, drugs_data = region_data_tuple

                if not isinstance(region_enum, RegionName):
                     print(f"Warning: Invalid RegionName enum for entry {region_idx} ('{region_name_str}'). Skipping.", file=sys.stderr)
                     continue
                if not isinstance(region_name_str, str):
                    print(f"Warning: Region name for {region_enum.value} is not a string. Skipping.", file=sys.stderr)
                    continue
                if not isinstance(drugs_data, list):
                    print(f"Warning: Drugs data for {region_name_str} is not a list. Skipping drug initialization for this region.", file=sys.stderr)
                    drugs_data = [] # Process region with no drugs

                try:
                    region: Region = Region(region_name_str)
                except ValueError as e_region_name:
                    print(f"Warning: Could not initialize region with name '{region_name_str}' due to invalid RegionName enum value. Error: {e_region_name}. Skipping.", file=sys.stderr)
                    continue

            except (TypeError, ValueError, IndexError) as e_region_unpack: # Catch errors from unpacking region_data_tuple
                print(f"Error unpacking region definition at index {region_idx}: '{region_data_tuple}'. Error: {e_region_unpack}. Skipping.", file=sys.stderr)
                continue
            except Exception as e_outer:
                print(f"Error processing region definition at index {region_idx}: {region_data_tuple}. Error: {e_outer}. Skipping.", file=sys.stderr)
                continue

            for drug_idx, drug_def_tuple in enumerate(drugs_data):
                try:
                    if len(drug_def_tuple) != 5:
                        print(f"Warning: Malformed drug definition for region {region_name_str} at drug index {drug_idx}. Expected 5 elements, got {len(drug_def_tuple)}. Skipping this drug.", file=sys.stderr)
                        continue

                    drug_name_str, base_price, max_price, demand_factor, qualities_stock_ranges = drug_def_tuple

                    if not isinstance(drug_name_str, str) or \
                       not isinstance(base_price, (int, float)) or \
                       not isinstance(max_price, (int, float)) or \
                       not isinstance(demand_factor, int) or \
                       not isinstance(qualities_stock_ranges, dict):
                        print(f"Warning: Type mismatch in drug definition fields for '{drug_name_str}' in region {region_name_str}. Skipping this drug.", file=sys.stderr)
                        continue

                    # Validate DrugName (Region.initialize_drug_market will also do this, but good for early catch)
                    try:
                        DrugName(drug_name_str)
                    except ValueError:
                        print(f"Warning: Invalid drug name string '{drug_name_str}' in region {region_name_str}. Skipping this drug.", file=sys.stderr)
                        continue

                    quality_stock_map: Dict[DrugQuality, int] = {}
                    for quality_enum, stock_range_tuple in qualities_stock_ranges.items():
                        if not isinstance(quality_enum, DrugQuality) or \
                           not (isinstance(stock_range_tuple, tuple) and len(stock_range_tuple) == 2 and \
                                isinstance(stock_range_tuple[0], int) and isinstance(stock_range_tuple[1], int)):
                            print(f"Warning: Malformed quality_stock_ranges for drug '{drug_name_str}', quality '{quality_enum}' in region {region_name_str}. Skipping this quality.", file=sys.stderr)
                            continue
                        min_val, max_val = stock_range_tuple
                        if min_val < 0 or max_val < 0 or min_val > max_val : # Added more checks for stock validity
                             print(f"Warning: Invalid min/max stock ({min_val},{max_val}) for drug '{drug_name_str}', quality '{quality_enum}' in region {region_name_str}. Using (0,0).", file=sys.stderr)
                             min_val, max_val = 0,0 # Corrected to assign 0,0
                        quality_stock_map[quality_enum] = random.randint(min_val, max_val)

                    region.initialize_drug_market(
                        drug_name_str,
                        base_price,
                        max_price,
                        demand_factor,
                        quality_stock_map,
                    )
                except (TypeError, ValueError, IndexError) as e_drug: # Catch errors from unpacking or processing drug_def_tuple
                    print(f"Error processing drug definition tuple '{drug_def_tuple}' in region {region_name_str}. Error: {e_drug}. Skipping this drug.", file=sys.stderr)
                    continue
                except Exception as e_drug_other:
                     print(f"Unexpected error processing drug definition '{drug_def_tuple}' in region {region_name_str}. Error: {e_drug_other}. Skipping this drug.", file=sys.stderr)
                     continue
            self.all_regions[region_enum] = region

        # After all regions and their markets are initialized, restock them
        for region_obj in self.all_regions.values():
                base_price,
                max_price,
                demand_factor,
                qualities_stock_ranges,
            ) in drugs_data:
                # Generate random stock for each quality based on its min/max range
                quality_stock_map: Dict[DrugQuality, int] = {
                    quality_enum: random.randint(min_val, max_val)
                    for quality_enum, (
                        min_val,
                        max_val,
                    ) in qualities_stock_ranges.items()
                }
                # Region.initialize_drug_market might take DrugName (enum) or str. Assuming str for now.
                region.initialize_drug_market(
                    drug_name_str,
                    base_price,
                    max_price,
                    demand_factor,
                    quality_stock_map,
                )
            self.all_regions[region_enum] = region  # Store with Enum as key

        # After all regions and their markets are initialized, restock them
        for region_obj in self.all_regions.values():  # region_obj is Region
            if hasattr(region_obj, "restock_market"):  # Check if method exists
                region_obj.restock_market()
            else:
                print(
                    f"Warning: Region {region_obj.name} does not have a restock_market method."
                )

    def set_current_player_region(self, region_name: RegionName) -> None:
        """
        Sets the player's current location to the specified region.

        Args:
            region_name: The RegionName enum member representing the destination region.
        """
        if region_name in self.all_regions:
            self.current_player_region = self.all_regions[region_name]
        else:
            # This could raise an error or log a warning, depending on desired strictness
            print(
                f"Warning: Attempted to set current region to an unknown or uninitialized region: {region_name}"
            )

    def get_current_player_region(self) -> Optional[Region]:
        """
        Retrieves the Region object for the player's current location.

        Returns:
            Optional[Region]: The current Region object, or None if not set.
        """
        return self.current_player_region

    def get_all_regions(self) -> Dict[RegionName, Region]:
        """
        Retrieves a dictionary of all regions in the game.

        Returns:
            Dict[RegionName, Region]: A dictionary mapping RegionName enums to Region objects.
        """
        return self.all_regions

    def get_game_state_summary(self) -> Dict[str, Any]:
        """
        Provides a summary of the current game state.

        This can be useful for UI displays, saving game progress, or debugging.
        The summary includes the current day, player location, crypto prices,
        AI rival count, informant status, and a list of all region names.

        Returns:
            Dict[str, Any]: A dictionary containing key aspects of the game state.
        """
        player_region_name_str: Optional[str] = None
        if self.current_player_region and hasattr(self.current_player_region, "name"):
            # Assuming Region.name is an Enum, so .value gives the string
            player_region_name_str = (
                self.current_player_region.name.value
                if hasattr(self.current_player_region.name, "value")
                else str(self.current_player_region.name)
            )

        # For 'all_regions', create a summary (e.g., names or simplified dicts)
        # rather than returning full Region objects directly in a summary.
        all_regions_summary: Dict[str, str] = {
            # Assuming region.name is an Enum, so .value gives the string
            name_enum.value: (
                region.name.value if hasattr(region.name, "value") else str(region.name)
            )
            for name_enum, region in self.all_regions.items()
        }

        return {
            "current_day": self.current_day,
            "current_player_region_name": player_region_name_str,
            "crypto_prices": self.current_crypto_prices.copy(),  # Return a copy for safety
            "ai_rivals_count": len(self.ai_rivals),
            "informant_unavailable_until_day": self.informant_unavailable_until_day,
            "all_region_names": list(all_regions_summary.keys()),
        }


# Placeholder for testing the GameState class structure.
# This would typically be part of your main application setup or test suite.
if __name__ == "__main__":
    # Create a GameState instance. This will call __init__ and internal initializers.
    game: GameState = GameState()

    # Example: Set player's starting region using the RegionName enum
    start_region_enum: RegionName = RegionName.DOWNTOWN
    game.set_current_player_region(start_region_enum)

    print(f"--- Initial Game State ---")
    print(f"Current day: {game.current_day}")

    player_region: Optional[Region] = game.get_current_player_region()
    if player_region:  # Check if a region is set
        # Assuming Region.name is an Enum, accessing .value for the string name
        player_region_name_val = (
            player_region.name.value
            if hasattr(player_region.name, "value")
            else str(player_region.name)
        )
        print(f"Current player region: {player_region_name_val}")
    else:
        print("Current player region: None")

    print(f"Crypto prices: {game.current_crypto_prices}")

    # Simulate advancing a day and updating crypto prices
    game.current_day += 1
    # Ensure game_configs has these attributes defined for the update function
    # Corrected attribute name to CRYPTO_MIN_PRICE as per game_configs.py
    if hasattr(game_configs, "CRYPTO_VOLATILITY") and hasattr(
        game_configs, "CRYPTO_MIN_PRICE"
    ):
        game.update_daily_crypto_prices(
            game_configs.CRYPTO_VOLATILITY, game_configs.CRYPTO_MIN_PRICE
        )
    else:
        print(
            "Warning: CRYPTO_VOLATILITY or CRYPTO_MIN_PRICE not found in game_configs. Skipping crypto update for simulation."
        )

    print(f"\n--- Game State After One Day ---")
    print(f"Current day: {game.current_day}")
    print(f"Updated crypto prices: {game.current_crypto_prices}")

    # Get and print the game state summary
    summary: Dict[str, Any] = game.get_game_state_summary()
    print(f"\n--- Game State Summary ---")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Example of how a specific region's data might be accessed (if needed)
    # print("\n--- Accessing Specific Region Data (Example) ---")
    # if RegionName.DOWNTOWN in game.all_regions:
    #     downtown_region = game.all_regions[RegionName.DOWNTOWN]
    #     print(f"Data for {downtown_region.name.value if hasattr(downtown_region.name, 'value') else str(downtown_region.name)}:")
    #     # This part is highly dependent on the structure of your Region and DrugMarket classes
    #     # For example, if Region has a method to describe its market:
    #     # if hasattr(downtown_region, 'describe_market'):
    #     #     downtown_region.describe_market()
    # else:
    #     print(f"{RegionName.DOWNTOWN.value} not found in initialized regions.")
