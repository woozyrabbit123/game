# tests/mechanics/test_event_manager.py
import unittest
from unittest.mock import MagicMock, patch
import random
import math

from src.mechanics.event_manager import _handle_mugging_event, _handle_forced_fire_sale_event, trigger_random_market_event
from src.core.player_inventory import PlayerInventory
from src.core.region import Region
from src.core.enums import RegionName, DrugName, DrugQuality, EventType
from src import game_configs # To access event chances and parameters

class TestEventManagerDirectHandlers(unittest.TestCase):
    def setUp(self):
        self.player_inv = PlayerInventory()
        self.region = Region(RegionName.DOWNTOWN.value) # Ensure region has a name
        self.mock_show_event = MagicMock()
        self.mock_add_log = MagicMock()

        # Mock game_configs_data with necessary attributes
        self.mock_configs = MagicMock()
        self.mock_configs.MUGGING_EVENT_CHANCE = 0.10 # Example
        self.mock_configs.FORCED_FIRE_SALE_CHANCE = 0.02
        self.mock_configs.FORCED_FIRE_SALE_QUANTITY_PERCENT = 0.15
        self.mock_configs.FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT = 0.30
        self.mock_configs.FORCED_FIRE_SALE_MIN_CASH_GAIN = 50.0
        # Add other config values if needed by other events in trigger_random_market_event
        self.mock_configs.BLACK_MARKET_CHANCE = 0.0 # Disable other events for specific tests
        self.mock_configs.EVENT_TRIGGER_CHANCE = 0.0 # Disable other events for specific tests


    def test_handle_mugging_event_successful(self):
        self.player_inv.cash = 1000
        initial_cash = self.player_inv.cash

        with patch('random.uniform', return_value=0.20): # Mock random percentage (20%)
            occurred = _handle_mugging_event(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)

        self.assertTrue(occurred)
        expected_lost = math.floor(initial_cash * 0.20)
        self.assertEqual(self.player_inv.cash, initial_cash - expected_lost)
        self.mock_show_event.assert_called_once()
        self.mock_add_log.assert_called_once()
        self.assertIn(f"lost ${expected_lost:,.0f}", self.mock_show_event.call_args[0][0])

    def test_handle_mugging_event_no_cash(self):
        self.player_inv.cash = 0
        occurred = _handle_mugging_event(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)
        self.assertFalse(occurred)
        self.assertEqual(self.player_inv.cash, 0)
        self.mock_show_event.assert_not_called()
        # add_to_log_callback might be called with "fizzled" - check specific implementation if needed

    def test_handle_forced_fire_sale_successful(self):
        self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 100)
        self.player_inv.cash = 0
        initial_quantity = self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD)

        # Mock region's get_sell_price
        self.region.get_sell_price = MagicMock(return_value=1000) # Mock price for Coke Standard

        with patch('random.choice', return_value={'name': DrugName.COKE, 'quality': DrugQuality.STANDARD, 'quantity': initial_quantity}):
            occurred = _handle_forced_fire_sale_event(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)

        self.assertTrue(occurred)

        expected_sold_qty = math.ceil(initial_quantity * self.mock_configs.FORCED_FIRE_SALE_QUANTITY_PERCENT)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), initial_quantity - expected_sold_qty)

        normal_price = 1000
        sale_price = normal_price * (1 - self.mock_configs.FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT)
        sale_price = round(max(0.01, sale_price),2) # Match rounding in main code
        calculated_gain = expected_sold_qty * sale_price
        expected_gain = max(calculated_gain, self.mock_configs.FORCED_FIRE_SALE_MIN_CASH_GAIN)

        self.assertEqual(self.player_inv.cash, round(expected_gain, 2))
        self.mock_show_event.assert_called_once()
        self.mock_add_log.assert_called_once()
        self.assertIn("forced into a fire sale", self.mock_show_event.call_args[0][0])

    def test_handle_forced_fire_sale_no_drugs(self):
        self.player_inv.cash = 100
        occurred = _handle_forced_fire_sale_event(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)
        self.assertFalse(occurred)
        self.assertEqual(self.player_inv.cash, 100)
        self.mock_show_event.assert_not_called()
        self.mock_add_log.assert_called_with("ForcedFireSale Event: Player has no drugs to sell. Event fizzled.")

    @patch('src.mechanics.event_manager._handle_mugging_event')
    @patch('src.mechanics.event_manager._create_and_add_black_market_event') # Also mock black market to control its chance
    @patch('random.random')
    def test_trigger_random_event_calls_mugging(self, mock_random, mock_black_market, mock_handle_mugging):
        # Order of random calls: black_market, mugging, fire_sale, standard_event_trigger
        mock_random.side_effect = [
            self.mock_configs.BLACK_MARKET_CHANCE + 0.1,     # No black market
            self.mock_configs.MUGGING_EVENT_CHANCE - 0.01,    # Mugging happens
            self.mock_configs.FORCED_FIRE_SALE_CHANCE + 0.1,  # No fire sale
            self.mock_configs.EVENT_TRIGGER_CHANCE + 0.1      # No standard event
        ]
        mock_black_market.return_value = None # Black market event returns a message string or None

        trigger_random_market_event(self.region, 1, self.player_inv, [], self.mock_show_event, self.mock_configs, self.mock_add_log)
        mock_handle_mugging.assert_called_once_with(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)

    @patch('src.mechanics.event_manager._handle_forced_fire_sale_event')
    @patch('src.mechanics.event_manager._handle_mugging_event') # Mock mugging as well
    @patch('src.mechanics.event_manager._create_and_add_black_market_event') # Mock black market
    @patch('random.random')
    def test_trigger_random_event_calls_fire_sale(self, mock_random, mock_black_market, mock_handle_mugging, mock_handle_fire_sale):
        # Order of random calls: black_market, mugging, fire_sale, standard_event_trigger
        mock_random.side_effect = [
            self.mock_configs.BLACK_MARKET_CHANCE + 0.1,     # No black market
            self.mock_configs.MUGGING_EVENT_CHANCE + 0.1,     # No mugging
            self.mock_configs.FORCED_FIRE_SALE_CHANCE - 0.01, # Fire sale happens
            self.mock_configs.EVENT_TRIGGER_CHANCE + 0.1      # No standard event
        ]
        mock_black_market.return_value = None
        mock_handle_mugging.return_value = False # Mugging did not occur

        trigger_random_market_event(self.region, 1, self.player_inv, [], self.mock_show_event, self.mock_configs, self.mock_add_log)
        mock_handle_fire_sale.assert_called_once_with(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)

if __name__ == '__main__':
    unittest.main()
