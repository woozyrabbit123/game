# tests/mechanics/test_event_manager.py
import unittest
from unittest.mock import MagicMock, patch
import random
import math

from src.mechanics.event_manager import (
    _handle_mugging_event,
    _handle_forced_fire_sale_event,
    trigger_random_market_event,
    _create_and_add_demand_spike, # Import other handlers being tested
    _create_and_add_supply_disruption,
    _create_and_add_police_crackdown,
    _create_and_add_cheap_stash,
    _create_and_add_the_setup,
    _create_and_add_rival_busted,
    _create_and_add_drug_market_crash,
    _create_and_add_black_market_event
)
from src.core.player_inventory import PlayerInventory
from src.core.region import Region
from src.core.enums import RegionName, DrugName, DrugQuality, EventType
from src.core.ai_rival import AIRival # Import for rival busted test
from src import game_configs # To access event chances and parameters

class TestEventManagerDirectHandlers(unittest.TestCase):
    def setUp(self):
        self.player_inv = PlayerInventory()
        self.region = Region(RegionName.DOWNTOWN.value)
        self.mock_show_event = MagicMock()
        self.mock_add_log = MagicMock()

        self.mock_configs = MagicMock()
        self.mock_configs.MUGGING_EVENT_CHANCE = 0.10
        self.mock_configs.FORCED_FIRE_SALE_CHANCE = 0.02
        self.mock_configs.FORCED_FIRE_SALE_QUANTITY_PERCENT = 0.15
        self.mock_configs.FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT = 0.30
        self.mock_configs.FORCED_FIRE_SALE_MIN_CASH_GAIN = 50.0
        self.mock_configs.BLACK_MARKET_CHANCE = 0.0
        self.mock_configs.EVENT_TRIGGER_CHANCE = 0.0

        # Add other specific game_configs attributes used by event creators
        self.mock_configs.SUPPLY_DISRUPTION_EVENT_DURATION_DAYS = 2
        self.mock_configs.SUPPLY_DISRUPTION_STOCK_REDUCTION_PERCENT = 0.75
        self.mock_configs.MIN_STOCK_AFTER_DISRUPTION = 1
        self.mock_configs.DRUG_CRASH_EVENT_DURATION_DAYS = 2
        self.mock_configs.DRUG_CRASH_PRICE_REDUCTION_PERCENT = 0.60
        self.mock_configs.MINIMUM_DRUG_PRICE = 1.0
        self.mock_configs.BLACK_MARKET_MIN_QUANTITY = 20
        self.mock_configs.BLACK_MARKET_MAX_QUANTITY = 50
        self.mock_configs.BLACK_MARKET_PRICE_REDUCTION_PERCENT = 0.50
        self.mock_configs.BLACK_MARKET_EVENT_DURATION_DAYS = 1

        # Clear any drug market data from previous tests or ensure clean setup
        self.region.drug_market_data.clear()


    def test_handle_mugging_event_successful(self):
        self.player_inv.cash = 1000
        initial_cash = self.player_inv.cash

        with patch('random.uniform', return_value=0.20):
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

    def test_handle_forced_fire_sale_successful(self):
        # Initialize drug for this test specifically
        self.region.initialize_drug_market(DrugName.COKE, 1000, 1200, 3, {DrugQuality.STANDARD: 100})
        self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 100)
        self.player_inv.cash = 0
        initial_quantity = self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD)

        self.region.get_sell_price = MagicMock(return_value=1000)

        with patch('random.choice', return_value={'name': DrugName.COKE, 'quality': DrugQuality.STANDARD, 'quantity': initial_quantity}):
            occurred = _handle_forced_fire_sale_event(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)

        self.assertTrue(occurred)

        expected_sold_qty = math.ceil(initial_quantity * self.mock_configs.FORCED_FIRE_SALE_QUANTITY_PERCENT)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), initial_quantity - expected_sold_qty)

        normal_price = 1000
        sale_price = normal_price * (1 - self.mock_configs.FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT)
        sale_price = round(max(0.01, sale_price),2)
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
    @patch('src.mechanics.event_manager._create_and_add_black_market_event')
    @patch('src.mechanics.event_manager._handle_forced_fire_sale_event') # Mock fire sale too
    @patch('random.random')
    def test_trigger_random_event_calls_mugging(self, mock_random, mock_handle_fire_sale, mock_black_market, mock_handle_mugging):
        mock_random.side_effect = [
            self.mock_configs.BLACK_MARKET_CHANCE + 0.1,
            self.mock_configs.MUGGING_EVENT_CHANCE - 0.01,
            self.mock_configs.FORCED_FIRE_SALE_CHANCE + 0.1,
            self.mock_configs.EVENT_TRIGGER_CHANCE + 0.1
        ]
        mock_black_market.return_value = None
        mock_handle_fire_sale.return_value = False

        trigger_random_market_event(self.region, 1, self.player_inv, [], self.mock_show_event, self.mock_configs, self.mock_add_log)
        mock_handle_mugging.assert_called_once_with(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)

    @patch('src.mechanics.event_manager._handle_forced_fire_sale_event')
    @patch('src.mechanics.event_manager._handle_mugging_event')
    @patch('src.mechanics.event_manager._create_and_add_black_market_event')
    @patch('random.random')
    def test_trigger_random_event_calls_fire_sale(self, mock_random, mock_black_market, mock_handle_mugging, mock_handle_fire_sale):
        mock_random.side_effect = [
            self.mock_configs.BLACK_MARKET_CHANCE + 0.1,
            self.mock_configs.MUGGING_EVENT_CHANCE + 0.1,
            self.mock_configs.FORCED_FIRE_SALE_CHANCE - 0.01,
            self.mock_configs.EVENT_TRIGGER_CHANCE + 0.1
        ]
        mock_black_market.return_value = None
        mock_handle_mugging.return_value = False

        trigger_random_market_event(self.region, 1, self.player_inv, [], self.mock_show_event, self.mock_configs, self.mock_add_log)
        mock_handle_fire_sale.assert_called_once_with(self.player_inv, self.region, self.mock_configs, self.mock_show_event, self.mock_add_log)

    # Helper to set up region market for testing event target selection
    def _initialize_region_with_drugs(self, tier1_present=True, tier2_present=True, tier3_present=True):
        self.region.drug_market_data.clear()
        if tier1_present:
            # Provide initial_stocks for predictability; Tier 1 has default internal stock if not provided
            self.region.initialize_drug_market(DrugName.WEED, 50, 80, 1, initial_stocks={DrugQuality.STANDARD: 100})
        if tier2_present:
            self.region.initialize_drug_market(DrugName.PILLS, 100, 150, 2, initial_stocks={DrugQuality.STANDARD: 50, DrugQuality.CUT: 50})
        if tier3_present:
            self.region.initialize_drug_market(DrugName.COKE, 1000, 1500, 3, initial_stocks={DrugQuality.STANDARD: 20, DrugQuality.PURE: 20})

    @patch('random.choice')
    @patch('random.uniform')
    @patch('random.randint')
    def test_create_demand_spike(self, mock_randint, mock_uniform, mock_choice):
        self._initialize_region_with_drugs()
        mock_choice.return_value = (DrugName.COKE, DrugQuality.PURE)
        mock_uniform.side_effect = [1.6, 1.25]
        mock_randint.return_value = 3

        _create_and_add_demand_spike(self.region, current_day=1)

        self.assertEqual(len(self.region.active_market_events), 1)
        event = self.region.active_market_events[0]
        self.assertEqual(event.event_type, EventType.DEMAND_SPIKE)
        self.assertEqual(event.target_drug_name, DrugName.COKE)
        self.assertEqual(event.target_quality, DrugQuality.PURE)
        self.assertAlmostEqual(event.sell_price_multiplier, 1.6)
        self.assertAlmostEqual(event.buy_price_multiplier, 1.25)
        self.assertEqual(event.duration_remaining_days, 3)
        self.assertEqual(event.start_day, 1)

    @patch('random.choice')
    def test_create_supply_disruption(self, mock_choice):
        self._initialize_region_with_drugs(tier1_present=False)
        # Ensure specific drug for choice has stock
        self.region.drug_market_data[DrugName.COKE]["available_qualities"][DrugQuality.PURE]["quantity_available"] = 10
        mock_choice.return_value = (DrugName.COKE, DrugQuality.PURE)

        _create_and_add_supply_disruption(self.region, 1, 0, self.mock_configs, self.mock_show_event, self.mock_add_log)

        self.assertEqual(len(self.region.active_market_events), 1)
        event = self.region.active_market_events[0]
        self.assertEqual(event.event_type, EventType.SUPPLY_DISRUPTION)
        self.assertEqual(event.target_drug_name, DrugName.COKE)
        self.assertEqual(event.target_quality, DrugQuality.PURE)
        self.assertEqual(event.duration_remaining_days, self.mock_configs.SUPPLY_DISRUPTION_EVENT_DURATION_DAYS)
        self.assertAlmostEqual(event.stock_reduction_factor, 1.0 - self.mock_configs.SUPPLY_DISRUPTION_STOCK_REDUCTION_PERCENT)
        self.assertEqual(event.min_stock_after_event, self.mock_configs.MIN_STOCK_AFTER_DISRUPTION)
        self.mock_show_event.assert_called_once()
        self.mock_add_log.assert_called_once()

    @patch('random.randint')
    def test_create_police_crackdown(self, mock_randint):
        mock_randint.side_effect = [3, 20]
        initial_heat = self.region.current_heat
        _create_and_add_police_crackdown(self.region, 1)

        self.assertEqual(len(self.region.active_market_events), 1)
        event = self.region.active_market_events[0]
        self.assertEqual(event.event_type, EventType.POLICE_CRACKDOWN)
        self.assertEqual(event.duration_remaining_days, 3)
        self.assertEqual(event.heat_increase_amount, 20)
        self.assertEqual(self.region.current_heat, initial_heat + 20)

    @patch('random.choice')
    @patch('random.uniform')
    @patch('random.randint')
    def test_create_cheap_stash(self, mock_randint, mock_uniform, mock_choice):
        self._initialize_region_with_drugs()
        mock_choice.return_value = (DrugName.WEED, DrugQuality.STANDARD)
        mock_uniform.return_value = 0.7
        mock_randint.side_effect = [2, 100]

        _create_and_add_cheap_stash(self.region, 1)

        self.assertEqual(len(self.region.active_market_events), 1)
        event = self.region.active_market_events[0]
        self.assertEqual(event.event_type, EventType.CHEAP_STASH)
        self.assertEqual(event.target_drug_name, DrugName.WEED)
        self.assertEqual(event.target_quality, DrugQuality.STANDARD)
        self.assertAlmostEqual(event.buy_price_multiplier, 0.7)
        self.assertEqual(event.duration_remaining_days, 2)
        self.assertEqual(event.temporary_stock_increase, 100)

    @patch('random.choice')
    @patch('random.randint')
    @patch('random.uniform')
    def test_create_the_setup_buy_deal(self, mock_uniform, mock_randint, mock_choice):
        self._initialize_region_with_drugs(tier1_present=False)
        self.player_inv.cash = 100000

        mock_choice.side_effect = [
            True,
            (DrugName.COKE, 3),
            DrugQuality.PURE
        ]
        mock_randint.return_value = 50
        mock_uniform.return_value = 0.3

        _create_and_add_the_setup(self.region, 1, self.player_inv)

        self.assertEqual(len(self.region.active_market_events), 1)
        event = self.region.active_market_events[0]
        self.assertEqual(event.event_type, EventType.THE_SETUP)
        self.assertTrue(event.is_buy_deal)
        self.assertEqual(event.deal_drug_name, DrugName.COKE)
        self.assertEqual(event.deal_quality, DrugQuality.PURE)
        self.assertEqual(event.deal_quantity, 50)

        base_buy_price = self.region.drug_market_data[DrugName.COKE]['base_buy_price']
        # Assuming DrugQuality.PURE has a buy multiplier of 1.5 from Drug class logic
        quality_mult_buy = 1.5
        expected_deal_price = base_buy_price * quality_mult_buy * 0.3
        self.assertAlmostEqual(event.deal_price_per_unit, expected_deal_price)

    @patch('random.choice')
    @patch('random.randint')
    def test_create_rival_busted(self, mock_randint, mock_choice):
        rival1 = AIRival("RivalX", DrugName.WEED, RegionName.DOCKS, 0.5, 0.5)
        rival2 = AIRival("RivalY", DrugName.PILLS, RegionName.SUBURBS, 0.5, 0.5)
        ai_rivals_list = [rival1, rival2]

        mock_choice.return_value = rival1
        mock_randint.return_value = 7

        _create_and_add_rival_busted(self.region, 1, ai_rivals_list)

        self.assertEqual(len(self.region.active_market_events), 1)
        event = self.region.active_market_events[0]
        self.assertEqual(event.event_type, EventType.RIVAL_BUSTED)
        self.assertEqual(event.target_drug_name, "RivalX")
        self.assertEqual(event.duration_remaining_days, 7)
        self.assertTrue(rival1.is_busted)
        self.assertEqual(rival1.busted_days_remaining, 7)

    @patch('random.choice')
    def test_create_drug_market_crash(self, mock_choice):
        self._initialize_region_with_drugs()
        self.region.drug_market_data[DrugName.COKE]["available_qualities"][DrugQuality.PURE]["quantity_available"] = 10
        mock_choice.return_value = (DrugName.COKE, DrugQuality.PURE)

        _create_and_add_drug_market_crash(self.region, 1, self.mock_configs, self.mock_show_event, self.mock_add_log)

        self.assertEqual(len(self.region.active_market_events), 1)
        event = self.region.active_market_events[0]
        self.assertEqual(event.event_type, EventType.DRUG_MARKET_CRASH)
        self.assertEqual(event.target_drug_name, DrugName.COKE)
        self.assertEqual(event.target_quality, DrugQuality.PURE)
        self.assertEqual(event.duration_remaining_days, self.mock_configs.DRUG_CRASH_EVENT_DURATION_DAYS)
        self.assertAlmostEqual(event.price_reduction_factor, 1.0 - self.mock_configs.DRUG_CRASH_PRICE_REDUCTION_PERCENT)
        self.assertAlmostEqual(event.minimum_price_after_crash, self.mock_configs.MINIMUM_DRUG_PRICE)
        self.mock_show_event.assert_called_once()
        self.mock_add_log.assert_called_once()

    @patch('random.choice')
    @patch('random.randint')
    def test_create_black_market_event(self, mock_randint, mock_choice):
        self._initialize_region_with_drugs()
        mock_choice.return_value = (DrugName.WEED, DrugQuality.STANDARD)
        mock_randint.return_value = 30

        _create_and_add_black_market_event(self.region, 1, self.player_inv, self.mock_show_event)

        self.assertEqual(len(self.region.active_market_events), 1)
        event = self.region.active_market_events[0]
        self.assertEqual(event.event_type, EventType.BLACK_MARKET_OPPORTUNITY)
        self.assertEqual(event.target_drug_name, DrugName.WEED)
        self.assertEqual(event.target_quality, DrugQuality.STANDARD)
        self.assertAlmostEqual(event.buy_price_multiplier, 1.0 - self.mock_configs.BLACK_MARKET_PRICE_REDUCTION_PERCENT)
        self.assertEqual(event.duration_remaining_days, self.mock_configs.BLACK_MARKET_EVENT_DURATION_DAYS)
        self.assertEqual(event.black_market_quantity_available, 30)
        self.mock_show_event.assert_called_once()

if __name__ == '__main__':
    unittest.main()
