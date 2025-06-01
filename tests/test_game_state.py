import unittest
from unittest.mock import patch, call
import random # For mocking random.uniform

# Assuming src is in PYTHONPATH or tests are run from root
from src import game_state
from src import game_configs # To access config constants
from src.core.enums import CryptoCoin, RegionName # Added RegionName

class TestGameState(unittest.TestCase):

    def setUp(self):
        # Reset global state variables in game_state module before each test
        # to ensure test isolation.
        game_state.current_crypto_prices = {}
        game_state.ai_rivals = []
        game_state.all_regions = {}
        game_state.informant_unavailable_until_day = None
        # It's also good practice to make a copy of relevant game_configs
        # if tests might modify them, though these tests primarily read.
        self.crypto_initial = game_configs.CRYPTO_PRICES_INITIAL.copy()
        self.crypto_volatility = game_configs.CRYPTO_VOLATILITY.copy()
        self.crypto_min_prices = game_configs.CRYPTO_MIN_PRICE.copy()

    def test_initialize_game_state(self):
        game_state.initialize_game_state()

        self.assertEqual(game_state.current_crypto_prices, self.crypto_initial)
        # Ensure it's a copy, not the same object
        self.assertIsNot(game_state.current_crypto_prices, game_configs.CRYPTO_PRICES_INITIAL)
        self.assertEqual(game_state.ai_rivals, [])
        self.assertIsNone(game_state.informant_unavailable_until_day)

    @patch('random.uniform')
    def test_update_daily_crypto_prices_increases_and_decreases(self, mock_uniform):
        # Initialize with known prices
        game_state.current_crypto_prices = {
            CryptoCoin.BITCOIN: 100.0,
            CryptoCoin.ETHEREUM: 50.0
        }
        # Mock random.uniform to return specific values for predictable changes
        # First call for BITCOIN (e.g., +10%), second for ETHEREUM (e.g., -5%)
        mock_uniform.side_effect = [0.10, -0.05]

        volatility = {CryptoCoin.BITCOIN: 0.2, CryptoCoin.ETHEREUM: 0.1} # Example volatilities
        min_prices = {CryptoCoin.BITCOIN: 10.0, CryptoCoin.ETHEREUM: 5.0}

        game_state.update_daily_crypto_prices(volatility, min_prices)

        # BITCOIN: 100.0 * (1 + 0.10) = 110.0
        self.assertAlmostEqual(game_state.current_crypto_prices[CryptoCoin.BITCOIN], 110.0)
        # ETHEREUM: 50.0 * (1 - 0.05) = 47.5
        self.assertAlmostEqual(game_state.current_crypto_prices[CryptoCoin.ETHEREUM], 47.5)

        # Check that random.uniform was called with correct volatility ranges
        expected_calls = [
            call(-volatility[CryptoCoin.BITCOIN], volatility[CryptoCoin.BITCOIN]),
            call(-volatility[CryptoCoin.ETHEREUM], volatility[CryptoCoin.ETHEREUM])
        ]
        mock_uniform.assert_has_calls(expected_calls)

    @patch('random.uniform')
    def test_update_daily_crypto_prices_respects_min_price(self, mock_uniform):
        game_state.current_crypto_prices = {CryptoCoin.BITCOIN: 12.0}
        # Make random.uniform return a large negative change that would go below min
        mock_uniform.return_value = -0.50

        volatility = {CryptoCoin.BITCOIN: 0.6} # High volatility for test
        min_prices = {CryptoCoin.BITCOIN: 10.0}

        game_state.update_daily_crypto_prices(volatility, min_prices)

        # Price should be capped at min_price (10.0)
        # 12.0 * (1 - 0.50) = 6.0, but min is 10.0
        self.assertAlmostEqual(game_state.current_crypto_prices[CryptoCoin.BITCOIN], 10.0)

    def test_update_daily_crypto_prices_no_initial_prices(self):
        # Ensure current_crypto_prices is empty
        game_state.current_crypto_prices = {}

        with patch('builtins.print') as mock_print: # To capture the warning
            game_state.update_daily_crypto_prices(self.crypto_volatility, self.crypto_min_prices)

        mock_print.assert_called_with("Warning: Crypto prices accessed before initialization.")
        self.assertEqual(game_state.current_crypto_prices, {}) # Should remain empty

    def test_update_daily_crypto_prices_coin_not_in_volatility_map(self):
        # Initialize with a coin that won't be in the volatility map passed to the function
        game_state.current_crypto_prices = {CryptoCoin.BITCOIN: 100.0, CryptoCoin.MONERO: 75.0}

        # Volatility map only for BITCOIN
        volatility = {CryptoCoin.BITCOIN: 0.1}
        min_prices = {CryptoCoin.BITCOIN: 10.0, CryptoCoin.MONERO: 15.0}

        with patch('random.uniform', return_value=0.05) as mock_rand_uniform:
             game_state.update_daily_crypto_prices(volatility, min_prices)

        # BITCOIN should change, MONERO should not
        self.assertAlmostEqual(game_state.current_crypto_prices[CryptoCoin.BITCOIN], 105.0)
        self.assertAlmostEqual(game_state.current_crypto_prices[CryptoCoin.MONERO], 75.0) # Unchanged
        mock_rand_uniform.assert_called_once_with(-0.1, 0.1) # Only called for Bitcoin


    @patch('src.game_state.initialize_regions')
    @patch('src.game_state.initialize_game_state')
    def test_initialize_global_state_calls_sub_initializers(self, mock_init_game_state, mock_init_regions):
        # This test ensures that initialize_global_state calls its component initializers.
        game_state.initialize_global_state(game_configs)

        mock_init_game_state.assert_called_once()
        mock_init_regions.assert_called_once()

    def test_initialize_global_state_integration(self):
        # This test checks the actual effects of initialize_global_state.
        # Reset state variables first
        game_state.current_crypto_prices = {}
        game_state.all_regions = {}
        game_state.ai_rivals = [] # Ensure all relevant globals are reset
        game_state.informant_unavailable_until_day = 10 # Give it a non-None value to check reset

        game_state.initialize_global_state(game_configs)

        # Check effects of initialize_game_state()
        self.assertEqual(game_state.current_crypto_prices, game_configs.CRYPTO_PRICES_INITIAL)
        self.assertIsNot(game_state.current_crypto_prices, game_configs.CRYPTO_PRICES_INITIAL) # Should be a copy
        self.assertEqual(game_state.ai_rivals, [])
        self.assertIsNone(game_state.informant_unavailable_until_day) # Should be reset by initialize_game_state

        # Check effects of initialize_regions()
        self.assertTrue(len(game_state.all_regions) > 0) # Regions should be initialized
        # Example check for a specific region (assuming DOWNTOWN is always initialized)
        self.assertIn(RegionName.DOWNTOWN, game_state.all_regions)
        self.assertTrue(game_state.all_regions[RegionName.DOWNTOWN].drug_market_data)


if __name__ == '__main__':
    unittest.main()
