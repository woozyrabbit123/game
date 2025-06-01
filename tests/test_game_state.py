import unittest
from unittest.mock import patch
import random

from src.game_state import GameState
from src.core.enums import RegionName, CryptoCoin, DrugName, DrugQuality
from src import game_configs

class TestGameState(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.game_state = GameState()

    def test_initialization(self):
        """Test the initial state of GameState."""
        self.assertEqual(self.game_state.current_day, 1)
        self.assertIsNone(self.game_state.current_player_region) # Default is None before explicit set
        self.assertEqual(self.game_state.ai_rivals, [])
        self.assertIsNone(self.game_state.informant_unavailable_until_day)

        # Check initial crypto prices (using one example coin)
        # Ensure the enum member is used as a key if CRYPTO_PRICES_INITIAL uses enum keys
        self.assertIn(CryptoCoin.DRUG_COIN, self.game_state.current_crypto_prices)
        self.assertEqual(self.game_state.current_crypto_prices[CryptoCoin.DRUG_COIN], game_configs.CRYPTO_PRICES_INITIAL[CryptoCoin.DRUG_COIN])

        # Check regions are initialized
        self.assertTrue(len(self.game_state.all_regions) > 0)
        self.assertIn(RegionName.DOWNTOWN, self.game_state.all_regions)

        # Check a sample region's market is initialized
        downtown_market = self.game_state.all_regions[RegionName.DOWNTOWN].drug_market_data
        self.assertIn(DrugName.WEED, downtown_market) # Assuming Weed is a DrugName enum member
        self.assertTrue(len(downtown_market[DrugName.WEED]["available_qualities"]) > 0)

    def test_initialize_crypto_prices_override(self):
        """Test overriding initial crypto prices."""
        dummy_prices = {
            CryptoCoin.DRUG_COIN: 150.0,
            CryptoCoin.BITCOIN: 25000.0, # Using BITCOIN instead of VOIDCOIN
            CryptoCoin.ETHEREUM: 1500.0, # Using ETHEREUM instead of STABLECOIN
            CryptoCoin.MONERO: 100.0     # Using MONERO instead of SHADOWBLITZ
        }
        self.game_state.initialize_crypto_prices(dummy_prices)
        self.assertEqual(self.game_state.current_crypto_prices, dummy_prices)
        # Reset to default for other tests if necessary, or ensure setUp re-initializes fully
        self.game_state._initialize_core_state() # Re-initialize to defaults for subsequent tests

    @patch('random.uniform')
    def test_update_daily_crypto_prices_logic(self, mock_uniform):
        """Test crypto price updates with controlled randomness and min price."""
        # Set a specific volatility and min price for testing
        test_coin = CryptoCoin.DRUG_COIN
        initial_price = 100.0
        self.game_state.current_crypto_prices = {test_coin: initial_price} # Set a known price

        volatility_map = {test_coin: 0.1} # 10% volatility
        min_prices_map = {test_coin: 10.0}

        # Scenario 1: Price increase
        mock_uniform.return_value = 0.05 # Simulate a 5% increase random factor
        expected_price_increase = initial_price * (1 + 0.05) # 100 * 1.05 = 105.0

        self.game_state.update_daily_crypto_prices(volatility_map, min_prices_map)
        self.assertAlmostEqual(self.game_state.current_crypto_prices[test_coin], expected_price_increase, places=2)

        # Scenario 2: Price decrease
        self.game_state.current_crypto_prices = {test_coin: initial_price} # Reset price
        mock_uniform.return_value = -0.05 # Simulate a 5% decrease random factor
        expected_price_decrease = initial_price * (1 - 0.05) # 100 * 0.95 = 95.0

        self.game_state.update_daily_crypto_prices(volatility_map, min_prices_map)
        self.assertAlmostEqual(self.game_state.current_crypto_prices[test_coin], expected_price_decrease, places=2)

        # Scenario 3: Price hits minimum
        self.game_state.current_crypto_prices = {test_coin: 10.5} # Price close to min
        mock_uniform.return_value = -0.1 # Simulate a 10% decrease, which would go below min
        # initial_price (10.5) * (1 - 0.1) = 9.45, but min is 10.0

        self.game_state.update_daily_crypto_prices(volatility_map, min_prices_map)
        self.assertEqual(self.game_state.current_crypto_prices[test_coin], min_prices_map[test_coin])

        # Scenario 4: Price tries to go below zero but stays at min_price (if min_price is > 0)
        self.game_state.current_crypto_prices = {test_coin: 0.5} # Very low price
        min_prices_map_low = {test_coin: 0.1} # Min price also low
        volatility_map_high = {test_coin: 0.9} # High volatility
        mock_uniform.return_value = -0.9 # Simulate a 90% decrease
        # 0.5 * (1-0.9) = 0.05, but min is 0.1
        self.game_state.update_daily_crypto_prices(volatility_map_high, min_prices_map_low)
        self.assertEqual(self.game_state.current_crypto_prices[test_coin], min_prices_map_low[test_coin])


    def test_set_and_get_current_player_region(self):
        """Test setting and getting the current player region."""
        self.game_state.set_current_player_region(RegionName.DOCKS)
        current_region = self.game_state.get_current_player_region()
        self.assertIsNotNone(current_region)
        self.assertEqual(current_region.name, RegionName.DOCKS) # Assuming Region object has a .name attribute which is RegionName enum

        self.game_state.set_current_player_region(RegionName.SUBURBS)
        current_region = self.game_state.get_current_player_region()
        self.assertIsNotNone(current_region)
        self.assertEqual(current_region.name, RegionName.SUBURBS)

    def test_get_all_regions(self):
        """Test retrieving all initialized regions."""
        all_regions = self.game_state.get_all_regions()
        self.assertIsInstance(all_regions, dict)
        self.assertEqual(len(all_regions), len(list(RegionName))) # Assuming all RegionName enums are initialized
        self.assertIn(RegionName.DOWNTOWN, all_regions)
        self.assertIn(RegionName.INDUSTRIAL, all_regions)
        self.assertEqual(all_regions[RegionName.DOWNTOWN].name, RegionName.DOWNTOWN)


    def test_get_game_state_summary(self):
        """Test the game state summary retrieval."""
        self.game_state.current_day = 5
        self.game_state.set_current_player_region(RegionName.COMMERCIAL)
        # Add a dummy rival for summary
        class MockAIRival:
            def __init__(self, name): self.name = name
        self.game_state.ai_rivals = [MockAIRival("TestRival")]
        self.game_state.informant_unavailable_until_day = 10

        summary = self.game_state.get_game_state_summary()

        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['current_day'], 5)
        self.assertEqual(summary['current_player_region_name'], RegionName.COMMERCIAL.value) # .value for string name
        self.assertEqual(summary['ai_rivals_count'], 1)
        self.assertEqual(summary['informant_unavailable_until_day'], 10)
        self.assertIn(CryptoCoin.DRUG_COIN, summary['crypto_prices'])
        self.assertTrue(len(summary['all_region_names']) > 0)
        self.assertIn(RegionName.DOWNTOWN.value, summary['all_region_names'])


if __name__ == '__main__':
    unittest.main()
