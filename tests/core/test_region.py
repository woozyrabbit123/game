import unittest
from unittest.mock import MagicMock, patch
import random # To be able to mock random.randint
import math # For math.floor

from src.core.region import Region
from src.core.enums import RegionName, DrugName, DrugQuality, EventType
from src.core.drug import Drug # Needed for Drug instances if not mocking fully
from src.core.market_event import MarketEvent
from src.game_state import GameState # Added for GameState mock
from src.core.player_inventory import PlayerInventory # Added for PlayerInventory mock
# Import game_configs directly to access its dictionaries if Region uses them
from src import narco_configs as game_configs

class TestRegion(unittest.TestCase):
    def setUp(self):
        self.region_name_enum = RegionName.DOWNTOWN
        self.region = Region(self.region_name_enum.value)

        # Mocks for GameState and PlayerInventory integration
        self.mock_game_state = MagicMock(spec=GameState)
        self.mock_player_inventory = MagicMock(spec=PlayerInventory)
        self.mock_game_state.player_inventory = self.mock_player_inventory
        # Default heat for player inventory, can be overridden in tests
        self.mock_player_inventory.heat = 0

        # Mock game_configs being used by the Region instance for heat thresholds
        # This assumes Region directly accesses game_configs.HEAT_PRICE_INCREASE_THRESHOLDS etc.
        # If it's passed in or set differently, adjust mocking.
        # For now, we rely on the module-level import in region.py

        # Default drug setup for many tests
        self.drug_name = DrugName.COKE
        self.quality_standard = DrugQuality.STANDARD
        self.quality_pure = DrugQuality.PURE
        self.quality_cut = DrugQuality.CUT
        self.base_buy = 1000
        self.base_sell = 1500
        self.tier = 3

        # Simplified initial stock for predictability, random will be mocked where needed
        self.initial_stocks_predictable = {
            DrugQuality.CUT: 100,
            DrugQuality.STANDARD: 150,
            DrugQuality.PURE: 50
        }
        with patch('random.randint', return_value=50): # Mock randint for predictable init stock
             self.region.initialize_drug_market(
                self.drug_name, self.base_buy, self.base_sell, self.tier,
                initial_stocks=self.initial_stocks_predictable
            )
        # Reset active events for each test
        self.region.active_market_events = []


    def test_region_initialization(self):
        self.assertEqual(self.region.name, self.region_name_enum)
        self.assertEqual(self.region.current_heat, 0)
        self.assertEqual(len(self.region.active_market_events), 0)
        self.assertIn(self.drug_name, self.region.drug_market_data)

    def test_modify_heat(self):
        self.region.modify_heat(20)
        self.assertEqual(self.region.current_heat, 20)
        self.region.modify_heat(-10)
        self.assertEqual(self.region.current_heat, 10)
        self.region.modify_heat(-30) # Should go to 0, not negative
        self.assertEqual(self.region.current_heat, 0)

    def test_initialize_drug_market_tier1_forces_standard(self):
        with patch('random.randint', return_value=100) as mock_rand: # Tier 1 uses fixed stock
            self.region.initialize_drug_market(DrugName.WEED, 50, 80, 1)

        weed_market = self.region.drug_market_data[DrugName.WEED]
        self.assertIn(DrugQuality.STANDARD, weed_market["available_qualities"])
        self.assertEqual(len(weed_market["available_qualities"]), 1)
        self.assertEqual(weed_market["available_qualities"][DrugQuality.STANDARD]["quantity_available"], 10000) # Default for Tier 1
        mock_rand.assert_not_called() # Should not be called for Tier 1 STANDARD stock

    def test_initialize_drug_market_tier_gt_1_random_stocks(self):
        # Test that randint is called for Tier > 1 if no initial_stocks provided
        region2 = Region(RegionName.SUBURBS.value) # Use a valid RegionName
        with patch('random.randint') as mock_rand:
            # Iteration order is CUT, STANDARD, PURE
            # To get PURE=10, STANDARD=20, CUT=30, side_effect should be [30, 20, 10]
            mock_rand.side_effect = [30, 20, 10]
            region2.initialize_drug_market(DrugName.SPEED, 100, 150, 2) # Tier 2

        self.assertEqual(mock_rand.call_count, 3)
        speed_market = region2.drug_market_data[DrugName.SPEED]
        self.assertEqual(speed_market["available_qualities"][DrugQuality.CUT]["quantity_available"], 30)
        self.assertEqual(speed_market["available_qualities"][DrugQuality.STANDARD]["quantity_available"], 20)
        self.assertEqual(speed_market["available_qualities"][DrugQuality.PURE]["quantity_available"], 10)

    def test_get_heat_price_multiplier(self):
        self.region.current_heat = 0
        self.assertAlmostEqual(self.region._get_heat_price_multiplier(), 1.0)
        # Using actual thresholds from game_configs
        threshold_mid = list(game_configs.HEAT_PRICE_INCREASE_THRESHOLDS.keys())[1] # e.g. 21
        multiplier_mid = game_configs.HEAT_PRICE_INCREASE_THRESHOLDS[threshold_mid]
        self.region.current_heat = threshold_mid
        self.assertAlmostEqual(self.region._get_heat_price_multiplier(), multiplier_mid)

        threshold_high = list(game_configs.HEAT_PRICE_INCREASE_THRESHOLDS.keys())[-1] # e.g. 81
        multiplier_high = game_configs.HEAT_PRICE_INCREASE_THRESHOLDS[threshold_high]
        self.region.current_heat = threshold_high + 10 # Above highest threshold
        self.assertAlmostEqual(self.region._get_heat_price_multiplier(), multiplier_high)

    # --- Price Tests ---
    def test_get_buy_price_base_and_quality(self):
        # STANDARD quality
        price_standard = self.region.get_buy_price(self.drug_name, self.quality_standard)
        expected_standard = self.base_buy * 1.0 # Drug quality multiplier for STANDARD buy is 1.0
        self.assertAlmostEqual(price_standard, expected_standard)
        self.assertIsNotNone(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["previous_buy_price"])


        # PURE quality
        price_pure = self.region.get_buy_price(self.drug_name, self.quality_pure)
        expected_pure = self.base_buy * 1.5 # Drug quality multiplier for PURE buy is 1.5
        self.assertAlmostEqual(price_pure, expected_pure)

        # CUT quality
        price_cut = self.region.get_buy_price(self.drug_name, self.quality_cut)
        expected_cut = self.base_buy * 0.7 # Drug quality multiplier for CUT buy is 0.7
        self.assertAlmostEqual(price_cut, expected_cut)

    def test_get_buy_price_with_heat(self):
        self.region.current_heat = list(game_configs.HEAT_PRICE_INCREASE_THRESHOLDS.keys())[1] # e.g. 21
        heat_mult = game_configs.HEAT_PRICE_INCREASE_THRESHOLDS[self.region.current_heat]

        price_standard = self.region.get_buy_price(self.drug_name, self.quality_standard)
        expected_standard = self.base_buy * 1.0 * heat_mult
        self.assertAlmostEqual(price_standard, expected_standard)

    def test_get_buy_price_event_black_market(self):
        event_mult = 0.5
        self.region.active_market_events.append(MarketEvent(
            event_type=EventType.BLACK_MARKET_OPPORTUNITY,
            target_drug_name=self.drug_name,
            target_quality=self.quality_standard,
            sell_price_multiplier=1.0, # Added default
            buy_price_multiplier=event_mult,
            duration_remaining_days=1,
            start_day=1, # Added default
            black_market_quantity_available=10
        ))
        price = self.region.get_buy_price(self.drug_name, self.quality_standard)
        expected = self.base_buy * 1.0 * event_mult # Assumes no heat for simplicity here
        self.assertAlmostEqual(price, expected)

    def test_get_buy_price_event_drug_market_crash(self):
        reduction_factor = 0.6
        min_price_after_crash = 50
        self.region.active_market_events.append(MarketEvent(
            event_type=EventType.DRUG_MARKET_CRASH,
            target_drug_name=self.drug_name,
            target_quality=self.quality_standard,
            sell_price_multiplier=1.0, # Added default
            buy_price_multiplier=1.0, # Added default
            duration_remaining_days=1,
            start_day=1, # Added default
            price_reduction_factor=reduction_factor,
            minimum_price_after_crash=min_price_after_crash
        ))
        price = self.region.get_buy_price(self.drug_name, self.quality_standard)
        expected_before_min = self.base_buy * 1.0 * reduction_factor
        expected = max(expected_before_min, min_price_after_crash)
        self.assertAlmostEqual(price, expected)

    def test_get_buy_price_event_demand_spike(self):
        event_mult = 1.2 # Demand spike might slightly increase buy price if player is buying
        self.region.active_market_events.append(MarketEvent(
            event_type=EventType.DEMAND_SPIKE,
            target_drug_name=self.drug_name,
            target_quality=self.quality_standard,
            sell_price_multiplier=1.0, # Added default
            buy_price_multiplier=event_mult,
            duration_remaining_days=1,
            start_day=1 # Added default
        ))
        price = self.region.get_buy_price(self.drug_name, self.quality_standard)
        expected = self.base_buy * 1.0 * event_mult
        self.assertAlmostEqual(price, expected)

    def test_get_sell_price_base_and_quality(self):
        price_standard = self.region.get_sell_price(self.drug_name, self.quality_standard)
        expected_standard = self.base_sell * 1.0 # STANDARD sell mult is 1.0
        self.assertAlmostEqual(price_standard, expected_standard)
        self.assertIsNotNone(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["previous_sell_price"])

        price_pure = self.region.get_sell_price(self.drug_name, self.quality_pure)
        expected_pure = self.base_sell * 1.6 # PURE sell mult is 1.6
        self.assertAlmostEqual(price_pure, expected_pure)

    # --- Stock Tests ---
    def test_get_available_stock_base(self):
        # This test now uses the mock_game_state
        self.mock_player_inventory.heat = 0
        stock = self.region.get_available_stock(self.drug_name, self.quality_standard, self.mock_game_state)
        self.assertEqual(stock, self.initial_stocks_predictable[self.quality_standard])

    def test_get_available_stock_with_heat_reduction_tier3(self):
        # Tier 3 drug (Coke)
        # Test regional heat impact
        regional_heat_value = list(game_configs.HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3.keys())[1] # e.g. 31
        self.region.current_heat = regional_heat_value # Set regional heat
        self.mock_player_inventory.heat = 0 # Ensure player heat is not a factor for this test's direct logic

        heat_reduction_factor = game_configs.HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3[regional_heat_value]

        stock = self.region.get_available_stock(self.drug_name, self.quality_standard, self.mock_game_state)
        expected_stock = math.floor(self.initial_stocks_predictable[self.quality_standard] * heat_reduction_factor)
        self.assertEqual(stock, expected_stock)
        self.region.current_heat = 0 # Reset for other tests

    def test_get_available_stock_with_supply_disruption(self):
        self.mock_player_inventory.heat = 0 # Player heat set to 0
        self.region.current_heat = 0    # Regional heat set to 0
        reduction_factor = 0.5
        min_stock_after = 10
        self.region.active_market_events.append(MarketEvent(
            event_type=EventType.SUPPLY_DISRUPTION,
            target_drug_name=self.drug_name,
            target_quality=self.quality_standard,
            sell_price_multiplier=1.0, # Added default
            buy_price_multiplier=1.0, # Added default
            duration_remaining_days=1,
            start_day=1, # Added default
            stock_reduction_factor=reduction_factor,
            min_stock_after_event=min_stock_after
        ))
        stock = self.region.get_available_stock(self.drug_name, self.quality_standard, self.mock_game_state)
        base_stock = self.initial_stocks_predictable[self.quality_standard]
        expected_stock = max(int(base_stock * reduction_factor), min_stock_after)
        self.assertEqual(stock, expected_stock)

    # --- New Tests for GameState integration in get_available_stock ---

    def test_get_available_stock_no_heat_no_event_gs(self):
        """Test with GameState: no heat, no event."""
        self.mock_player_inventory.heat = 0
        self.region.active_market_events = []
        # Ensure using the default Tier 3 drug for this test
        self.region.drug_market_data[self.drug_name]["tier"] = 3

        stock = self.region.get_available_stock(self.drug_name, self.quality_standard, self.mock_game_state)
        # For Tier 3 drug with 0 heat, no heat reduction should apply from player_heat
        self.assertEqual(stock, self.initial_stocks_predictable[self.quality_standard])

    def test_get_available_stock_with_regional_heat_reduction_gs(self): # Renamed test
        """Test with GameState: regional heat reduction for Tier 2/3 drug."""
        self.region.current_heat = 60 # Set regional heat
        self.mock_player_inventory.heat = 0 # Ensure player heat is not the one being tested here
        self.region.drug_market_data[self.drug_name]["tier"] = 2
        self.region.active_market_events = []

        stock = self.region.get_available_stock(self.drug_name, self.quality_standard, self.mock_game_state)

        heat_reduction_factor = 1.0
        # This calculation should use self.region.current_heat as per _get_heat_stock_reduction_factor
        for threshold, factor in sorted(game_configs.HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3.items(), reverse=True):
            if self.region.current_heat >= threshold:
                heat_reduction_factor = factor
                break

        expected_stock = math.floor(self.initial_stocks_predictable[self.quality_standard] * heat_reduction_factor)
        self.assertEqual(stock, expected_stock)
        self.region.drug_market_data[self.drug_name]["tier"] = self.tier # Reset tier
        self.region.current_heat = 0 # Reset regional heat

    def test_get_available_stock_with_supply_disruption_event_gs(self):
        """Test with GameState: supply disruption event."""
        self.mock_player_inventory.heat = 0
        self.region.current_heat = 0 # Ensure no regional heat interference
        self.region.drug_market_data[self.drug_name]["tier"] = 3

        event_reduction_factor = 0.5
        min_stock_after_event = 10
        disruption_event = MarketEvent(
            event_type=EventType.SUPPLY_DISRUPTION,
            target_drug_name=self.drug_name,
            target_quality=self.quality_standard,
            sell_price_multiplier=1.0, buy_price_multiplier=1.0, # Defaults
            duration_remaining_days=2, start_day=1, # Defaults
            stock_reduction_factor=event_reduction_factor,
            min_stock_after_event=min_stock_after_event
        )
        self.region.active_market_events = [disruption_event]

        stock = self.region.get_available_stock(self.drug_name, self.quality_standard, self.mock_game_state)

        base_stock = self.initial_stocks_predictable[self.quality_standard]
        # Heat is 0, so no heat reduction on base_stock
        expected_stock_after_event = math.floor(base_stock * event_reduction_factor)
        expected_stock = max(expected_stock_after_event, min_stock_after_event)
        self.assertEqual(stock, expected_stock)

    def test_get_available_stock_heat_and_event_combined_gs(self):
        """Test with GameState: combined regional heat and supply disruption."""
        self.region.current_heat = 60 # Set regional heat
        self.mock_player_inventory.heat = 0 # Player heat should not interfere if logic is regional
        self.region.drug_market_data[self.drug_name]["tier"] = 2

        event_reduction_factor = 0.5
        min_stock_after_event = 10
        disruption_event = MarketEvent(
            event_type=EventType.SUPPLY_DISRUPTION,
            target_drug_name=self.drug_name,
            target_quality=self.quality_standard,
            sell_price_multiplier=1.0, buy_price_multiplier=1.0,
            duration_remaining_days=2, start_day=1,
            stock_reduction_factor=event_reduction_factor,
            min_stock_after_event=min_stock_after_event
        )
        self.region.active_market_events = [disruption_event]

        stock = self.region.get_available_stock(self.drug_name, self.quality_standard, self.mock_game_state)

        # 1. Calculate heat reduction based on regional heat
        heat_reduction_factor_for_calc = 1.0
        for threshold, factor in sorted(game_configs.HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3.items(), reverse=True):
            if self.region.current_heat >= threshold: # Using regional heat
                heat_reduction_factor_for_calc = factor
                break

        stock_after_heat = math.floor(self.initial_stocks_predictable[self.quality_standard] * heat_reduction_factor_for_calc)

        # 2. Calculate event reduction on heat-adjusted stock
        stock_after_event_reduction = math.floor(stock_after_heat * event_reduction_factor)
        final_expected_stock = max(stock_after_event_reduction, min_stock_after_event)

        self.assertEqual(stock, final_expected_stock)
        self.region.drug_market_data[self.drug_name]["tier"] = self.tier # Reset tier
        self.region.current_heat = 0 # Reset regional heat


    # --- Stock Update Tests ---
    def test_update_stock_on_buy(self):
        initial_stock = self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["quantity_available"]
        self.region.update_stock_on_buy(self.drug_name, self.quality_standard, 20)
        self.assertEqual(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["quantity_available"], initial_stock - 20)

        # Buy more than available - should go to 0
        self.region.update_stock_on_buy(self.drug_name, self.quality_standard, initial_stock) # try to buy remaining stock + 20 more
        self.assertEqual(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["quantity_available"], 0)


    def test_update_stock_on_sell(self):
        # Selling to market decreases available quantity (market gets saturated/police notice)
        initial_stock = self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["quantity_available"]
        self.region.update_stock_on_sell(self.drug_name, self.quality_standard, 30)
        self.assertEqual(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["quantity_available"], initial_stock - 30)

    # --- Restock Market ---
    @patch('random.randint')
    def test_restock_market_tier_gt_1(self, mock_randint):
        # Set specific stocks to see them change
        self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_pure]["quantity_available"] = 5
        self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["quantity_available"] = 5
        self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_cut]["quantity_available"] = 5

        # Expected random values for CUT, STANDARD, PURE for self.drug_name (COKE, Tier 3)
        # To get PURE=20, STANDARD=30, CUT=40, side_effect should be [40, 30, 20]
        mock_randint.side_effect = [40, 30, 20]

        self.region.restock_market()

        self.assertEqual(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_cut]["quantity_available"], 40)
        self.assertEqual(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["quantity_available"], 30)
        self.assertEqual(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_pure]["quantity_available"], 20)
        mock_randint.assert_called()

    @patch('random.randint')
    def test_restock_market_with_cheap_stash_event(self, mock_randint):
        mock_randint.side_effect = [20, 30, 40] # PURE, STANDARD, CUT for COKE (Tier 3)

        stash_increase = 50
        self.region.active_market_events.append(MarketEvent(
            event_type=EventType.CHEAP_STASH,
            target_drug_name=self.drug_name,
            target_quality=self.quality_standard,
            sell_price_multiplier=1.0, # Added default
            buy_price_multiplier=1.0, # Added default (CHEAP_STASH uses its own logic for buy price effect)
            duration_remaining_days=1,
            start_day=1, # Added default
            temporary_stock_increase=stash_increase
        ))

        self.region.restock_market()
        # Standard stock would be 30 (from mock_randint) + 50 from cheap stash
        self.assertEqual(self.region.drug_market_data[self.drug_name]["available_qualities"][self.quality_standard]["quantity_available"], 30 + stash_increase)


if __name__ == '__main__':
    unittest.main()
