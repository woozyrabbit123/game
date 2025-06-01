import unittest
from unittest.mock import MagicMock, patch, call
import random # For patching random.randint, random.uniform, random.choice

# Game Core Objects
from src.game_state import GameState
from src.core.player_inventory import PlayerInventory
from src.core.region import Region
from src.core.market_event import MarketEvent
from src.core.ai_rival import AIRival # Added import

# Enums
from src.core.enums import EventType, DrugName, DrugQuality, RegionName

# Game Configurations
from src import game_configs # Direct import to access EVENT_CONFIGS

# Functions to test
from src.mechanics.event_manager import (
    _create_and_add_demand_spike,
    _create_and_add_police_crackdown,
    _create_and_add_cheap_stash,
    _create_and_add_the_setup, # Assuming this exists and is data-driven
    _create_and_add_rival_busted, # Assuming this exists
    trigger_random_market_event
)

class TestEventManager(unittest.TestCase):

    def setUp(self):
        """Set up common mock objects for testing event manager functions."""
        self.mock_game_state = MagicMock(spec=GameState)
        self.mock_player_inventory = MagicMock(spec=PlayerInventory)
        self.mock_region = MagicMock(spec=Region)

        # Configure common attributes for GameState mock
        self.mock_game_state.current_day = 1
        self.mock_game_state.ai_rivals = []
        self.mock_game_state.player_inventory = self.mock_player_inventory
        # self.mock_game_state.all_regions = {RegionName.DOWNTOWN: self.mock_region} # Example, might not be needed if region is passed directly
        # self.mock_game_state.get_current_player_region = MagicMock(return_value=self.mock_region) # Might not be needed

        # Configure common attributes for Region mock
        self.mock_region.name = RegionName.DOWNTOWN # Enum member
        self.mock_region.drug_market_data = {} # Will be populated per test
        self.mock_region.active_market_events = []
        # Mock the method used by event creators to add events to the region
        self.mock_region.add_market_event = MagicMock(side_effect=lambda event: self.mock_region.active_market_events.append(event))


        # Configure common attributes for PlayerInventory mock
        self.mock_player_inventory.cash = 1000.0
        self.mock_player_inventory.heat = 0
        # Mock methods that might be called, e.g. by THE_SETUP event
        self.mock_player_inventory.has_drug = MagicMock(return_value=True) # Assume player has drugs for THE_SETUP selling part
        self.mock_player_inventory.get_quantity = MagicMock(return_value=50) # Example quantity for THE_SETUP

        # Mock callbacks
        self.mock_show_event_message_callback = MagicMock()
        self.mock_add_to_log_callback = MagicMock()

    def tearDown(self):
        """Reset active_market_events for the mock_region after each test."""
        if self.mock_region: # Ensure mock_region was initialized
            self.mock_region.active_market_events = []


    # --- Test Individual Event Creation Functions ---

    @patch('random.choice') # For choosing drug and quality
    @patch('random.uniform') # For sell_price_multiplier and buy_price_multiplier
    @patch('random.randint') # For duration_days
    def test_create_demand_spike_uses_config(self, mock_randint, mock_uniform, mock_choice):
        """Test _create_and_add_demand_spike uses game_configs.EVENT_CONFIGS."""
        # --- Setup Mocks and Test Data ---
        # Mock random.choice to select a specific drug and quality
        # Ensure the chosen drug is Tier 2 or 3 as per typical Demand Spike logic
        mock_drug_name = DrugName.COKE # Tier 3
        mock_drug_quality = DrugQuality.PURE
        # random.choice is called once on a list of (drug_name, quality) tuples
        mock_choice.return_value = (mock_drug_name, mock_drug_quality)

        # Mock random.randint for duration
        expected_duration = 3 # Example duration
        mock_randint.return_value = expected_duration

        # Mock random.uniform for multipliers
        # Demand Spike typically affects sell price more, buy price less or not at all
        expected_sell_multiplier = 1.5
        expected_buy_multiplier = 1.1
        mock_uniform.side_effect = [expected_sell_multiplier, expected_buy_multiplier]

        # Ensure the region's drug market has the chosen drug
        self.mock_region.drug_market_data = {
            mock_drug_name: {
                "tier": 3, # Important for Demand Spike eligibility
                "available_qualities": {mock_drug_quality: {"quantity_available": 100}}
            }
        }
        self.mock_region.active_market_events = [] # Ensure it's clean

        # --- Call the function ---
        # Assuming the function signature is (region, game_state)
        _create_and_add_demand_spike(self.mock_region, self.mock_game_state)

        # --- Assertions ---
        self.assertEqual(len(self.mock_region.active_market_events), 1)
        created_event = self.mock_region.active_market_events[0]

        self.assertEqual(created_event.event_type, EventType.DEMAND_SPIKE)
        self.assertEqual(created_event.target_drug_name, mock_drug_name)
        self.assertEqual(created_event.target_quality, mock_drug_quality)

        # Assert duration matches mocked randint and config range
        cfg = game_configs.EVENT_CONFIGS["DEMAND_SPIKE"]
        self.assertEqual(created_event.duration_remaining_days, expected_duration)
        mock_randint.assert_called_once_with(cfg["DURATION_DAYS_MIN"], cfg["DURATION_DAYS_MAX"])

        # Assert multipliers match mocked uniform and config range
        self.assertEqual(created_event.sell_price_multiplier, expected_sell_multiplier)
        self.assertEqual(created_event.buy_price_multiplier, expected_buy_multiplier)

        expected_calls_uniform = [
            call(cfg["SELL_PRICE_MULT_MIN"], cfg["SELL_PRICE_MULT_MAX"]),
            call(cfg["BUY_PRICE_MULT_MIN"], cfg["BUY_PRICE_MULT_MAX"]),
        ]
        self.assertEqual(mock_uniform.call_args_list, expected_calls_uniform)

        # The function directly appends to region.active_market_events.
        # The check self.assertEqual(len(self.mock_region.active_market_events), 1)
        # and subsequent checks on created_event's attributes confirm the addition and correctness.
        # No separate add_market_event method is called by this specific function.

    @patch('random.randint') # For duration_days and heat_increase_amount
    def test_create_police_crackdown_uses_config(self, mock_randint):
        """Test _create_and_add_police_crackdown uses game_configs.EVENT_CONFIGS."""
        # --- Setup Mocks and Test Data ---
        expected_duration = 5
        expected_heat_increase = 20
        mock_randint.side_effect = [expected_duration, expected_heat_increase]

        self.mock_region.active_market_events = []
        self.mock_region.modify_heat = MagicMock() # Mock to check if heat is modified

        # --- Call the function ---
        # Signature: _create_and_add_police_crackdown(region: Region, current_day: int)
        # current_day is obtained from game_state in the actual trigger, but passed directly here
        _create_and_add_police_crackdown(self.mock_region, self.mock_game_state.current_day)

        # --- Assertions ---
        self.assertEqual(len(self.mock_region.active_market_events), 1)
        created_event = self.mock_region.active_market_events[0]

        self.assertEqual(created_event.event_type, EventType.POLICE_CRACKDOWN)
        self.assertIsNone(created_event.target_drug_name) # Police crackdown is region-wide
        self.assertIsNone(created_event.target_quality)

        cfg = game_configs.EVENT_CONFIGS["POLICE_CRACKDOWN"]
        self.assertEqual(created_event.duration_remaining_days, expected_duration)
        self.assertEqual(created_event.heat_increase_amount, expected_heat_increase)

        expected_calls_randint = [
            call(cfg["DURATION_DAYS_MIN"], cfg["DURATION_DAYS_MAX"]),
            call(cfg["HEAT_INCREASE_MIN"], cfg["HEAT_INCREASE_MAX"]),
        ]
        self.assertEqual(mock_randint.call_args_list, expected_calls_randint)

        # Verify region's heat was modified
        self.mock_region.modify_heat.assert_called_once_with(expected_heat_increase)

    @patch('random.choice') # For choosing drug and quality
    @patch('random.uniform') # For buy_price_multiplier
    @patch('random.randint') # For duration_days and temporary_stock_increase
    def test_create_cheap_stash_uses_config(self, mock_randint, mock_uniform, mock_choice):
        """Test _create_and_add_cheap_stash uses game_configs.EVENT_CONFIGS."""
        # --- Setup Mocks and Test Data ---
        mock_drug_name = DrugName.WEED # Tier 1
        mock_drug_quality = DrugQuality.STANDARD
        mock_choice.return_value = (mock_drug_name, mock_drug_quality) # random.choice selects this tuple

        expected_buy_multiplier = 0.7
        mock_uniform.return_value = expected_buy_multiplier

        expected_duration = 2
        expected_stock_increase = 100
        mock_randint.side_effect = [expected_duration, expected_stock_increase]

        self.mock_region.drug_market_data = {
            mock_drug_name: {
                "tier": 1, # Eligible for Cheap Stash
                "available_qualities": {mock_drug_quality: {"quantity_available": 50}}
            }
        }
        self.mock_region.active_market_events = []

        # --- Call the function ---
        # Signature: _create_and_add_cheap_stash(region: Region, current_day: int)
        _create_and_add_cheap_stash(self.mock_region, self.mock_game_state.current_day)

        # --- Assertions ---
        self.assertEqual(len(self.mock_region.active_market_events), 1)
        created_event = self.mock_region.active_market_events[0]

        self.assertEqual(created_event.event_type, EventType.CHEAP_STASH)
        self.assertEqual(created_event.target_drug_name, mock_drug_name)
        self.assertEqual(created_event.target_quality, mock_drug_quality)

        cfg = game_configs.EVENT_CONFIGS["CHEAP_STASH"]
        self.assertEqual(created_event.buy_price_multiplier, expected_buy_multiplier)
        mock_uniform.assert_called_once_with(cfg["BUY_PRICE_MULT_MIN"], cfg["BUY_PRICE_MULT_MAX"])

        self.assertEqual(created_event.duration_remaining_days, expected_duration)
        self.assertEqual(created_event.temporary_stock_increase, expected_stock_increase)

        expected_calls_randint = [
            call(cfg["DURATION_DAYS_MIN"], cfg["DURATION_DAYS_MAX"]),
            call(cfg["TEMP_STOCK_INCREASE_MIN"], cfg["TEMP_STOCK_INCREASE_MAX"]),
        ]
        self.assertEqual(mock_randint.call_args_list, expected_calls_randint)

    @patch('src.core.drug.Drug') # Target where Drug is defined
    @patch('random.choice') # For is_buy_deal, drug selection, quality selection
    @patch('random.uniform') # For deal_price_multiplier
    @patch('random.randint') # For deal_quantity
    def test_create_the_setup_buy_deal_uses_config(self, mock_randint, mock_uniform, mock_choice, MockDrug):
        """Test _create_and_add_the_setup for a BUY deal uses game_configs.EVENT_CONFIGS."""
        # --- Setup Mocks and Test Data ---
        is_buy_deal = True
        mock_deal_drug_name = DrugName.COKE # Tier 3
        mock_deal_drug_tier = 3
        mock_deal_quality = DrugQuality.PURE

        # random.choice side_effect order:
        # 1. is_buy_deal
        # 2. (deal_drug_name_enum, tier) from possible_deal_drugs
        # 3. deal_quality from available_qualities
        mock_choice.side_effect = [
            is_buy_deal,
            (mock_deal_drug_name, mock_deal_drug_tier),
            mock_deal_quality
        ]

        expected_deal_quantity = 30
        mock_randint.return_value = expected_deal_quantity

        expected_price_multiplier_from_config = 0.3 # e.g., player buys at 30% of modified base
        mock_uniform.return_value = expected_price_multiplier_from_config

        # Mock the Drug class's get_quality_multiplier
        # It's called for both 'buy' and 'sell' in the function
        mock_drug_instance = MockDrug.return_value
        def quality_multiplier_side_effect(type_str):
            if type_str == "buy":
                return 1.2 # Example for PURE COKE (buy)
            elif type_str == "sell":
                return 1.1 # Example for PURE COKE (sell)
            return 1.0 # Default
        mock_drug_instance.get_quality_multiplier.side_effect = quality_multiplier_side_effect
        quality_mult_buy_expected = 1.2


        base_buy_price = 1000
        self.mock_region.drug_market_data = {
            mock_deal_drug_name: {
                "tier": mock_deal_drug_tier,
                "base_buy_price": base_buy_price,
                "base_sell_price": 1500, # Not used for buy deal price calc
                "available_qualities": {mock_deal_quality: {"quantity_available": 50}}
            }
        }
        self.mock_player_inventory.cash = 100000 # Ensure enough cash for the deal
        self.mock_region.active_market_events = []

        # --- Call the function ---
        # Signature: _create_and_add_the_setup(region: Region, current_day: int, player_inventory: PlayerInventory)
        _create_and_add_the_setup(self.mock_region, self.mock_game_state.current_day, self.mock_player_inventory)

        # --- Assertions ---
        self.assertEqual(len(self.mock_region.active_market_events), 1)
        created_event = self.mock_region.active_market_events[0]

        self.assertEqual(created_event.event_type, EventType.THE_SETUP)
        self.assertEqual(created_event.deal_drug_name, mock_deal_drug_name)
        self.assertEqual(created_event.deal_quality, mock_deal_quality)
        self.assertEqual(created_event.deal_quantity, expected_deal_quantity)
        self.assertEqual(created_event.is_buy_deal, is_buy_deal)

        cfg = game_configs.EVENT_CONFIGS["THE_SETUP"]
        mock_randint.assert_called_once_with(cfg["DEAL_QUANTITY_MIN"], cfg["DEAL_QUANTITY_MAX"])
        mock_uniform.assert_called_once_with(cfg["BUY_DEAL_PRICE_MULT_MIN"], cfg["BUY_DEAL_PRICE_MULT_MAX"])

        # Verify Drug class was instantiated and get_quality_multiplier was called
        MockDrug.assert_called_once_with(mock_deal_drug_name.value, mock_deal_drug_tier, base_buy_price, 1500, mock_deal_quality)

        expected_get_quality_multiplier_calls = [call("buy"), call("sell")]
        mock_drug_instance.get_quality_multiplier.assert_has_calls(expected_get_quality_multiplier_calls, any_order=True)
        # Ensure it was called exactly twice if that's the expectation
        self.assertEqual(mock_drug_instance.get_quality_multiplier.call_count, 2)


        expected_deal_price = round(max(1.0, base_buy_price * quality_mult_buy_expected * expected_price_multiplier_from_config),2)
        self.assertEqual(created_event.deal_price_per_unit, expected_deal_price)

        self.assertEqual(created_event.duration_remaining_days, cfg["DURATION_DAYS"])

    @patch('random.choice') # For selecting the rival
    @patch('random.randint') # For busted_days_remaining
    def test_create_rival_busted_uses_config(self, mock_randint, mock_choice):
        """Test _create_and_add_rival_busted uses game_configs.EVENT_CONFIGS."""
        # --- Setup Mocks and Test Data ---
        mock_rival = MagicMock(spec=AIRival)
        mock_rival.name = "TestRivalLeader" # Ensure it's a unique name for clarity
        mock_rival.is_busted = False
        # busted_days_remaining will be set by the function

        self.mock_game_state.ai_rivals = [mock_rival]
        mock_choice.return_value = mock_rival # random.choice will select this rival

        expected_duration = 7
        mock_randint.return_value = expected_duration

        self.mock_region.active_market_events = []

        # --- Call the function ---
        # Signature: _create_and_add_rival_busted(region: Region, current_day: int, ai_rivals: List[AIRival])
        _create_and_add_rival_busted(self.mock_region, self.mock_game_state.current_day, self.mock_game_state.ai_rivals)

        # --- Assertions ---
        self.assertEqual(len(self.mock_region.active_market_events), 1)
        created_event = self.mock_region.active_market_events[0]

        self.assertEqual(created_event.event_type, EventType.RIVAL_BUSTED)
        # For RIVAL_BUSTED, target_drug_name stores the rival's name
        self.assertEqual(created_event.target_drug_name, mock_rival.name)
        self.assertIsNone(created_event.target_quality)

        cfg = game_configs.EVENT_CONFIGS["RIVAL_BUSTED"]
        self.assertEqual(created_event.duration_remaining_days, expected_duration)
        mock_randint.assert_called_once_with(cfg["DURATION_DAYS_MIN"], cfg["DURATION_DAYS_MAX"])

        # Verify rival's state
        self.assertTrue(mock_rival.is_busted)
        self.assertEqual(mock_rival.busted_days_remaining, expected_duration)

    # --- Test trigger_random_market_event ---

    @patch('src.mechanics.event_manager._create_and_add_black_market_event') # To prevent it from running
    @patch('src.mechanics.event_manager._handle_mugging_event') # To prevent it from running
    @patch('src.mechanics.event_manager._handle_forced_fire_sale_event') # To prevent it from running
    @patch('random.choice') # To control the selection from weighted_event_list
    @patch('random.random') # To control various probability checks
    @patch('src.mechanics.event_manager._create_and_add_demand_spike')
    @patch('src.mechanics.event_manager._create_and_add_supply_disruption')
    @patch('src.mechanics.event_manager._create_and_add_police_crackdown')
    @patch('src.mechanics.event_manager._create_and_add_cheap_stash')
    @patch('src.mechanics.event_manager._create_and_add_the_setup')
    @patch('src.mechanics.event_manager._create_and_add_rival_busted')
    @patch('src.mechanics.event_manager._create_and_add_drug_market_crash')
    def test_trigger_random_market_event_demand_spike_branch(
        self, mock_create_drug_market_crash, mock_create_rival_busted, mock_create_the_setup,
        mock_create_cheap_stash, mock_create_police_crackdown, mock_create_supply_disruption,
        mock_create_demand_spike, mock_random_random, mock_random_choice,
        mock_handle_forced_fire_sale, mock_handle_mugging, mock_create_black_market):
        """Test trigger_random_market_event calls _create_and_add_demand_spike."""

        # Prevent independent events from firing
        mock_create_black_market.return_value = None
        mock_handle_mugging.return_value = False
        mock_handle_forced_fire_sale.return_value = False

        # Setup mock_random_random:
        # 1. Black Market Chance: > game_configs.BLACK_MARKET_CHANCE (no trigger)
        # 2. Mugging Chance: > game_configs.MUGGING_EVENT_CHANCE (no trigger)
        # 3. Forced Fire Sale Chance: > game_configs.FORCED_FIRE_SALE_CHANCE (no trigger)
        # 4. Event Trigger Chance: < game_configs.EVENT_TRIGGER_CHANCE (trigger standard event block)
        mock_random_random.side_effect = [
            game_configs.BLACK_MARKET_CHANCE + 0.1,
            game_configs.MUGGING_EVENT_CHANCE + 0.1,
            game_configs.FORCED_FIRE_SALE_CHANCE + 0.1,
            game_configs.EVENT_TRIGGER_CHANCE - 0.01
        ]

        # Setup mock_random_choice to select DEMAND_SPIKE
        # This assumes DEMAND_SPIKE is a valid choice in the weighted list
        mock_random_choice.return_value = EventType.DEMAND_SPIKE

        # Call the function
        trigger_random_market_event(
            self.mock_region,
            self.mock_game_state, # Pass the full GameState mock
            self.mock_player_inventory,
            self.mock_game_state.ai_rivals,
            self.mock_show_event_message_callback,
            game_configs, # Pass the actual game_configs module
            self.mock_add_to_log_callback
        )

        # Assert that _create_and_add_demand_spike was called
        # The signature for _create_and_add_demand_spike is (region, game_state_instance)
        mock_create_demand_spike.assert_called_once_with(self.mock_region, self.mock_game_state)

        # Assert other creation functions were NOT called (optional, but good for specificity)
        mock_create_supply_disruption.assert_not_called()
        mock_create_police_crackdown.assert_not_called()
        mock_create_cheap_stash.assert_not_called()
        mock_create_the_setup.assert_not_called()
        mock_create_rival_busted.assert_not_called()
        mock_create_drug_market_crash.assert_not_called()


if __name__ == '__main__':
    unittest.main()
