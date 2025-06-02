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
from src.utils.logger import get_logger
from .core.ai_rival import AIRival
from .core.region import (
    Region,
)  # Assuming Region class has a 'name' attribute and a 'to_dict()' method
from src import narco_configs as game_configs


logger = get_logger(__name__)

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
        self.game_won: bool = False
        self.win_condition_achieved: Optional[str] = None
        
        # Attributes for Legacy Scenario tracking
        self.player_sales_profit_by_region: Dict[RegionName, float] = {name: 0.0 for name in RegionName}
        self.achieved_legacy_scenarios: List[str] = []
        # self.mid_game_average_heat: Optional[float] = None # This might be calculated on the fly or stored if needed for multiple checks

        # Seasonal Event Tracking
        self.current_seasonal_event: Optional[str] = None # Stores the ID/key of the active seasonal event
        self.seasonal_event_effects_active: Dict[str, Any] = {} # Stores the 'effects' dict of the active event
        self.seasonal_event_name_map: Dict[str, str] = {} # Maps event ID to friendly name for convenience

        # Turf War Tracking
        self.active_turf_wars: Dict[RegionName, Dict[str, Any]] = {}


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
                    logger.warning(f"Invalid key in CRYPTO_PRICES_INITIAL: {coin_enum}. Expected CryptoCoin enum. Skipping.")
                    continue
                if not isinstance(price, (int, float)):
                    logger.warning(f"Invalid price value for {coin_enum.value} in CRYPTO_PRICES_INITIAL: {price}. Expected number. Skipping.")
                    continue
                self.current_crypto_prices[coin_enum] = float(price)
        else:
            logger.error("CRYPTO_PRICES_INITIAL not found in game_configs or is not a dictionary. Crypto prices not initialized.")
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
            logger.error(f"initialize_crypto_prices expects a dictionary, got {type(initial_prices)}. Prices not set.")
            return

        for coin_enum, price in initial_prices.items():
            if not isinstance(coin_enum, CryptoCoin):
                logger.warning(f"Invalid key in provided initial_prices: {coin_enum}. Expected CryptoCoin enum. Skipping.")
                continue
            if not isinstance(price, (int, float)):
                logger.warning(f"Invalid price value for {coin_enum.value} in provided initial_prices: {price}. Expected number. Skipping.")
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
            logger.warning(
                "Crypto prices were not initialized before update. Initializing with defaults."
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
        Region definitions are now loaded from game_configs.
        """
        # The large region_definitions list and its type aliases (DrugDefinitionTuple, RegionDefinitionTuple)
        # have been moved to game_configs.py

        self.all_regions: Dict[RegionName, Region] = {}  # Clear any existing regions
        for region_idx, region_data_tuple in enumerate(game_configs.REGION_DEFINITIONS):
            try:
                if len(region_data_tuple) != 3:
                    logger.warning(f"Malformed region definition at index {region_idx}. Expected 3 elements, got {len(region_data_tuple)}. Skipping.")
                    continue

                region_enum, region_name_str, drugs_data = region_data_tuple

                if not isinstance(region_enum, RegionName):
                     logger.warning(f"Invalid RegionName enum for entry {region_idx} ('{region_name_str}'). Skipping.")
                     continue
                if not isinstance(region_name_str, str):
                    logger.warning(f"Region name for {region_enum.value} is not a string. Skipping.")
                    continue
                if not isinstance(drugs_data, list):
                    logger.warning(f"Drugs data for {region_name_str} is not a list. Skipping drug initialization for this region.")
                    drugs_data = [] # Process region with no drugs

                try:
                    region: Region = Region(region_name_str)
                except ValueError as e_region_name:
                    logger.warning(f"Could not initialize region with name '{region_name_str}' due to invalid RegionName enum value. Error: {e_region_name}. Skipping.")
                    continue

            except (TypeError, ValueError, IndexError) as e_region_unpack: # Catch errors from unpacking region_data_tuple
                logger.error(f"Error unpacking region definition at index {region_idx}: '{region_data_tuple}'. Error: {e_region_unpack}. Skipping.")
                continue
            except Exception as e_outer:
                logger.error(f"Error processing region definition at index {region_idx}: {region_data_tuple}. Error: {e_outer}. Skipping.")
                continue

            for drug_idx, drug_def_tuple in enumerate(drugs_data):
                try:
                    if len(drug_def_tuple) != 5:
                        logger.warning(f"Malformed drug definition for region {region_name_str} at drug index {drug_idx}. Expected 5 elements, got {len(drug_def_tuple)}. Skipping this drug.")
                        continue

                    drug_name_str, base_price, max_price, demand_factor, qualities_stock_ranges = drug_def_tuple

                    if not isinstance(drug_name_str, str) or \
                       not isinstance(base_price, (int, float)) or \
                       not isinstance(max_price, (int, float)) or \
                       not isinstance(demand_factor, int) or \
                       not isinstance(qualities_stock_ranges, dict):
                        logger.warning(f"Type mismatch in drug definition fields for '{drug_name_str}' in region {region_name_str}. Skipping this drug.")
                        continue

                    # Validate DrugName (Region.initialize_drug_market will also do this, but good for early catch)
                    try:
                        DrugName(drug_name_str)
                    except ValueError:
                        logger.warning(f"Invalid drug name string '{drug_name_str}' in region {region_name_str}. Skipping this drug.")
                        continue

                    quality_stock_map: Dict[DrugQuality, int] = {}
                    for quality_enum, stock_range_tuple in qualities_stock_ranges.items():
                        if not isinstance(quality_enum, DrugQuality) or \
                           not (isinstance(stock_range_tuple, tuple) and len(stock_range_tuple) == 2 and \
                                isinstance(stock_range_tuple[0], int) and isinstance(stock_range_tuple[1], int)):
                            logger.warning(f"Malformed quality_stock_ranges for drug '{drug_name_str}', quality '{quality_enum}' in region {region_name_str}. Skipping this quality.")
                            continue
                        min_val, max_val = stock_range_tuple
                        if min_val < 0 or max_val < 0 or min_val > max_val : # Added more checks for stock validity
                             logger.warning(f"Invalid min/max stock ({min_val},{max_val}) for drug '{drug_name_str}', quality '{quality_enum}' in region {region_name_str}. Using (0,0).")
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
                    logger.error(f"Error processing drug definition tuple '{drug_def_tuple}' in region {region_name_str}. Error: {e_drug}. Skipping this drug.")
                    continue
                except Exception as e_drug_other:
                     logger.error(f"Unexpected error processing drug definition '{drug_def_tuple}' in region {region_name_str}. Error: {e_drug_other}. Skipping this drug.")
                     continue
            self.all_regions[region_enum] = region

        # After all regions and their markets are initialized, restock them
        for region_obj in self.all_regions.values():  # region_obj is Region
            if hasattr(region_obj, "restock_market"):  # Check if method exists
                region_obj.restock_market()
            else:
                logger.warning(
                    f"Region {region_obj.name} does not have a restock_market method."
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
            logger.warning(
                f"Attempted to set current region to an unknown or uninitialized region: {region_name}"
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
            "game_won": self.game_won,
            "win_condition_achieved": self.win_condition_achieved,
        }


# Placeholder for testing the GameState class structure.
# This would typically be part of your main application setup or test suite.
if __name__ == "__main__":
    # Create a GameState instance. This will call __init__ and internal initializers.
    game: GameState = GameState()

    # Example: Set player's starting region using the RegionName enum
    start_region_enum: RegionName = RegionName.DOWNTOWN
    game.set_current_player_region(start_region_enum)

    logger.info(f"--- Initial Game State ---")
    logger.info(f"Current day: {game.current_day}")

    player_region: Optional[Region] = game.get_current_player_region()
    if player_region:  # Check if a region is set
        # Assuming Region.name is an Enum, accessing .value for the string name
        player_region_name_val = (
            player_region.name.value
            if hasattr(player_region.name, "value")
            else str(player_region.name)
        )
        logger.info(f"Current player region: {player_region_name_val}")
    else:
        logger.info("Current player region: None")

    logger.info(f"Crypto prices: {game.current_crypto_prices}")

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
        logger.warning(
            "CRYPTO_VOLATILITY or CRYPTO_MIN_PRICE not found in game_configs. Skipping crypto update for simulation."
        )

    logger.info(f"\n--- Game State After One Day ---")
    logger.info(f"Current day: {game.current_day}")
    logger.info(f"Updated crypto prices: {game.current_crypto_prices}")

    # Get and print the game state summary
    summary: Dict[str, Any] = game.get_game_state_summary()
    logger.info(f"\n--- Game State Summary ---")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")

    # Example of how a specific region's data might be accessed (if needed)
    # logger.info("\n--- Accessing Specific Region Data (Example) ---")
    # if RegionName.DOWNTOWN in game.all_regions:
    #     downtown_region = game.all_regions[RegionName.DOWNTOWN]
    #     logger.info(f"Data for {downtown_region.name.value if hasattr(downtown_region.name, 'value') else str(downtown_region.name)}:")
    #     # This part is highly dependent on the structure of your Region and DrugMarket classes
    #     # For example, if Region has a method to describe its market:
    #     # if hasattr(downtown_region, 'describe_market'):
    #     #     downtown_region.describe_market()
    # else:
    #     logger.warning(f"{RegionName.DOWNTOWN.value} not found in initialized regions.")
