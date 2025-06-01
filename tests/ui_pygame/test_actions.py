import unittest
from unittest.mock import patch, MagicMock

# Adjust imports based on actual project structure
import src.ui_pygame.state # Ensure the module is loaded for patching
from src.ui_pygame.actions import (
    action_travel_to_region,
    action_confirm_transaction,
    action_confirm_tech_operation # Added this import
)
from src.core.player_inventory import PlayerInventory
from src.core.enums import SkillID # Added for skill tests
from src.core.region import Region
from src.game_state import GameState # Added for GameState spec
import math # Added for skill effect calculations
from src.core.enums import RegionName, DrugName, DrugQuality, CryptoCoin # Added CryptoCoin
from src import game_configs # For TRAVEL_COST_CASH

# Mock the global state object if action_travel_to_region depends on it
# This is a common pattern if 'state' is a module or a global instance
# For this example, we'll assume 'state' is implicitly available or passed
# If 'state' is 'src.ui_pygame.state', then mock that.

class MockGameState:
    def __init__(self, current_region, day=1):
        self.current_player_region = current_region
        self.current_day = day # Used by action_travel_to_region internally via state.campaign_day
        self.difficulty_level = 1
        # Mock other attributes if action_travel_to_region reads them from game_state object
        self.current_crypto_prices = {}
        self.ai_rivals = []
        self.all_regions = {}


class MockPygameState:
    def __init__(self, initial_cash, current_region_obj, travel_cost):
        self.player_inventory_cache = PlayerInventory("TestPlayer")
        self.player_inventory_cache.cash = initial_cash

        self.game_state_data_cache = MockGameState(current_region_obj)
        # self.game_state_data_cache.current_player_region = current_region_obj
        # self.game_state_data_cache.current_day = 1 # Keep track of day for travel logic

        self.game_configs_data_cache = MagicMock()
        self.game_configs_data_cache.TRAVEL_COST_CASH = travel_cost
        self.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER = {} # example, add if needed
        self.game_configs_data_cache.CRYPTO_VOLATILITY = {}
        self.game_configs_data_cache.CRYPTO_MIN_PRICE = {}


        # campaign_day and phase_thresholds are directly on 'state' in actions.py
        self.campaign_day = 1
        self.phase_thresholds = [45, 70, 100, 120]
        self.campaign_phase = 1


class TestPygameActions(unittest.TestCase):

    def setUp(self):
        self.source_region = Region(RegionName.DOWNTOWN.value)
        self.dest_region = Region(RegionName.SUBURBS.value)

        # Patch all external dependencies of action_travel_to_region
        self.patch_show_event_message = patch('src.ui_pygame.ui_hud.show_event_message') # Corrected
        self.patch_setup_buttons = patch('src.ui_pygame.setup_ui.setup_buttons')
        self.patch_check_police_stop = patch('src.mechanics.event_manager.check_and_trigger_police_stop', return_value=False) # Corrected
        self.patch_update_crypto = patch('src.game_state.GameState.update_daily_crypto_prices') # Target GameState method
        self.patch_update_events = patch('src.mechanics.event_manager.update_active_events')

        # For add_message_to_log - Patch where it's looked up in actions.py
        self.patch_add_message_to_log = patch('src.ui_pygame.actions.add_message_to_log')

        # Patch for market_impact used in action_confirm_transaction
        self.patch_market_impact = patch('src.ui_pygame.actions.market_impact')

        self.mock_show_event_message = self.patch_show_event_message.start()
        self.mock_setup_buttons = self.patch_setup_buttons.start()
        self.mock_market_impact = self.patch_market_impact.start()
        self.mock_check_police_stop = self.patch_check_police_stop.start()
        self.mock_update_crypto = self.patch_update_crypto.start()
        self.mock_update_events = self.patch_update_events.start()

        self.mock_add_message_to_log = self.patch_add_message_to_log.start()
        # Removed side_effect for debugging


    def tearDown(self):
        self.patch_show_event_message.stop()
        self.patch_setup_buttons.stop()
        self.patch_check_police_stop.stop()
        self.patch_update_crypto.stop()
        self.patch_update_events.stop()
        self.patch_market_impact.stop()
        self.patch_add_message_to_log.stop() # Added

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_travel_successful(self, mock_ui_state):
        initial_cash = 100
        travel_cost = game_configs.TRAVEL_COST_CASH # Use the actual constant

        # Configure the mock_actions_state
        # This mock represents the 'state' module/object used within actions.py
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash

        # Use MagicMock spec for GameState
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_player_region = self.source_region # Direct attribute for this mock
        mock_ui_state.game_state_data_cache.current_day = 1
        # If action_travel_to_region calls get_current_player_region():
        # mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=self.source_region)


        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = travel_cost
        # Ensure all necessary configs are on this mock if used by the action
        mock_ui_state.game_configs_data_cache.CRYPTO_VOLATILITY = {}
        mock_ui_state.game_configs_data_cache.CRYPTO_MIN_PRICE = {}
        mock_ui_state.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER = {}


        mock_ui_state.campaign_day = 1
        mock_ui_state.phase_thresholds = [45, 70, 100, 120]
        mock_ui_state.campaign_phase = 1
        mock_ui_state.current_view = "travel" # Initial view


        # Call the action
        action_travel_to_region(self.dest_region,
                                mock_ui_state.player_inventory_cache,
                                mock_ui_state.game_state_data_cache)

        # Assertions
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash - travel_cost)
        self.assertEqual(mock_ui_state.game_state_data_cache.current_player_region, self.dest_region)
        self.assertEqual(mock_ui_state.campaign_day, 2) # Day should advance
        self.mock_show_event_message.assert_called_with(f"Traveled from {self.source_region.name.value} to {self.dest_region.name.value}.")
        self.mock_check_police_stop.assert_called_once()
        self.mock_update_crypto.assert_called_once()
        self.mock_update_events.assert_called_once()
        self.assertEqual(mock_ui_state.current_view, "market")


    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_travel_insufficient_cash(self, mock_ui_state):
        initial_cash = 20
        travel_cost = game_configs.TRAVEL_COST_CASH

        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash

        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_player_region = self.source_region
        mock_ui_state.game_state_data_cache.current_day = 1
        # mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=self.source_region)


        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = travel_cost

        mock_ui_state.campaign_day = 1


        original_day = mock_ui_state.campaign_day

        action_travel_to_region(self.dest_region,
                                mock_ui_state.player_inventory_cache,
                                mock_ui_state.game_state_data_cache)

        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash) # Cash unchanged
        self.assertEqual(mock_ui_state.game_state_data_cache.current_player_region, self.source_region) # Region unchanged
        self.assertEqual(mock_ui_state.campaign_day, original_day) # Day unchanged
        self.mock_show_event_message.assert_called_with("Not enough cash to travel.")
        self.mock_check_police_stop.assert_not_called() # Should not proceed to police check


    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_sell_with_compartmentalization(self, mock_ui_state):
        # Setup mock_ui_state similar to other tests in this class
        initial_cash = 100
        drug_to_sell = DrugName.WEED
        quality_to_sell = DrugQuality.STANDARD
        quantity_sold = 10
        sell_price = 10

        # Configure PlayerInventory and GameState within mock_ui_state
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.add_drug(drug_to_sell, quality_to_sell, quantity_sold)
        mock_ui_state.player_inventory_cache.unlocked_skills.add(SkillID.COMPARTMENTALIZATION.value)

        mock_region = Region(RegionName.DOWNTOWN.value)
        mock_region.drug_market_data[drug_to_sell] = {
            "tier": 1,
            "available_qualities": {quality_to_sell: {"quantity_available": 1000}},
            "player_sell_impact_modifier": 1.0,
            "player_buy_impact_modifier": 1.0
        }
        # Ensure region is initialized with this drug (example)
        # This might require calling region.initialize_drug_market in a more structured way if tests become complex
        # For now, direct dict manipulation is used by existing tests.

        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_region) # Ensure this is mocked

        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER = {1: 2}
        mock_ui_state.game_configs_data_cache.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT = game_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT


        # Setup transaction state on mock_ui_state
        mock_ui_state.current_transaction_type = "sell"
        mock_ui_state.drug_for_transaction = drug_to_sell
        mock_ui_state.quality_for_transaction = quality_to_sell
        mock_ui_state.price_for_transaction = sell_price
        mock_ui_state.available_for_transaction = quantity_sold # Selling all of it
        mock_ui_state.quantity_input_string = str(quantity_sold)

        initial_region_heat = mock_region.current_heat

        action_confirm_transaction(mock_ui_state.player_inventory_cache, mock_region, mock_ui_state.game_state_data_cache)

        base_heat_generated = mock_ui_state.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER[1] * quantity_sold
        expected_heat = math.ceil(base_heat_generated * (1 - mock_ui_state.game_configs_data_cache.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT))

        self.assertEqual(mock_region.current_heat, initial_region_heat + expected_heat)

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_travel_with_ghost_protocol(self, mock_ui_state):
        # Setup mock_ui_state
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.heat = 10
        mock_ui_state.player_inventory_cache.cash = 100
        mock_ui_state.player_inventory_cache.unlocked_skills.add(SkillID.GHOST_PROTOCOL.value)

        mock_source_region = Region(RegionName.DOWNTOWN.value)
        mock_dest_region = Region(RegionName.SUBURBS.value)

        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        # mock_ui_state.game_state_data_cache.current_player_region = mock_source_region # if accessed directly
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_source_region) # if accessed via method
        mock_ui_state.game_state_data_cache.all_regions = {RegionName.SUBURBS: mock_dest_region}


        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = 50
        mock_ui_state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY = game_configs.BASE_DAILY_HEAT_DECAY
        mock_ui_state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = game_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
        mock_ui_state.game_configs_data_cache.CRYPTO_VOLATILITY = {}
        mock_ui_state.game_configs_data_cache.CRYPTO_MIN_PRICE = {}


        mock_ui_state.campaign_day = 1
        mock_ui_state.phase_thresholds = [45, 70, 100, 120]
        mock_ui_state.campaign_phase = 1

        initial_player_heat = mock_ui_state.player_inventory_cache.heat

        action_travel_to_region(mock_dest_region, mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache)

        base_decay = mock_ui_state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY
        boost = mock_ui_state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
        expected_decay = base_decay + math.floor(base_decay * boost)
        final_heat = max(0, initial_player_heat - expected_decay)

        self.assertEqual(mock_ui_state.player_inventory_cache.heat, final_heat)

    # --- Tests for action_confirm_transaction (Buy Scenarios) ---

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_buy_successful(self, mock_ui_state):
        initial_cash = 5000
        drug_price = 100
        buy_quantity = 10
        market_stock = 50
        drug_to_buy = DrugName.WEED
        quality_to_buy = DrugQuality.STANDARD
        drug_tier = 1 # For market impact and heat (though heat not for buy)

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.max_capacity = 100 # Enough space

        # Region
        mock_current_region = Region(RegionName.DOWNTOWN.value)
        mock_current_region.initialize_drug_market(
            drug_to_buy, base_buy_price=drug_price, base_sell_price=drug_price + 20, tier=drug_tier,
            initial_stocks={quality_to_buy: market_stock}
        )
        # Ensure player_buy_impact_modifier exists
        mock_current_region.drug_market_data[drug_to_buy]['player_buy_impact_modifier'] = 1.0


        # GameState
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        # No specific configs needed for basic buy beyond what region uses internally

        # Transaction state on mock_ui_state
        mock_ui_state.current_transaction_type = "buy"
        mock_ui_state.drug_for_transaction = drug_to_buy
        mock_ui_state.quality_for_transaction = quality_to_buy
        mock_ui_state.price_for_transaction = drug_price
        mock_ui_state.available_for_transaction = market_stock
        mock_ui_state.quantity_input_string = str(buy_quantity)
        mock_ui_state.active_popup_message = None # To check success/error message

        # Mock the market_impact module function if it's called directly
        # self.mock_market_impact is already set up in setUp/tearDown
        self.mock_market_impact.apply_player_buy_impact = MagicMock()


        action_confirm_transaction(
            mock_ui_state.player_inventory_cache,
            mock_current_region, # Pass the region instance directly
            mock_ui_state.game_state_data_cache
        )

        # Assertions
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash - (drug_price * buy_quantity))
        self.assertEqual(mock_ui_state.player_inventory_cache.get_quantity(drug_to_buy, quality_to_buy), buy_quantity)

        expected_market_stock_after = market_stock - buy_quantity
        self.assertEqual(mock_current_region.drug_market_data[drug_to_buy]["available_qualities"][quality_to_buy]["quantity_available"], expected_market_stock_after)

        # Corrected assertion based on actual function call in actions.py
        self.mock_market_impact.apply_player_buy_impact.assert_called_once_with(mock_current_region, drug_to_buy.value, buy_quantity)

        # action_confirm_transaction calls show_event_message_external (which is ui_hud.show_event_message)
        # Format from actions.py: f"Bought {quantity} {drug_enum.value} ({state.quality_for_transaction.name})."
        self.mock_show_event_message.assert_called_once_with(f"Bought {buy_quantity} {drug_to_buy.value} ({quality_to_buy.name}).")
        self.assertEqual(mock_ui_state.quantity_input_string, "") # Input cleared to empty string
        # Note: drug_for_transaction and other related fields (quality, price, available)
        # are NOT cleared by the current implementation of action_confirm_transaction.
        # self.assertIsNone(mock_ui_state.drug_for_transaction) # This would fail.

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_buy_insufficient_cash(self, mock_ui_state):
        initial_cash = 50
        drug_price = 100
        buy_quantity = 10 # Total cost = 1000
        market_stock = 50
        drug_to_buy = DrugName.WEED
        quality_to_buy = DrugQuality.STANDARD

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        initial_drug_quantity = mock_ui_state.player_inventory_cache.get_quantity(drug_to_buy, quality_to_buy)


        # Region
        mock_current_region = Region(RegionName.DOWNTOWN.value)
        mock_current_region.initialize_drug_market(
            drug_to_buy, base_buy_price=drug_price, base_sell_price=drug_price + 20, tier=1,
            initial_stocks={quality_to_buy: market_stock}
        )
        initial_market_stock = mock_current_region.drug_market_data[drug_to_buy]["available_qualities"][quality_to_buy]["quantity_available"]


        # GameState
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs - not strictly needed for this error path
        mock_ui_state.game_configs_data_cache = MagicMock()

        # Transaction state on mock_ui_state
        mock_ui_state.current_transaction_type = "buy"
        mock_ui_state.drug_for_transaction = drug_to_buy
        mock_ui_state.quality_for_transaction = quality_to_buy
        mock_ui_state.price_for_transaction = drug_price
        mock_ui_state.available_for_transaction = market_stock
        mock_ui_state.quantity_input_string = str(buy_quantity)
        # Ensure current_view is one that doesn't skip the final clear of quantity_input_string
        mock_ui_state.current_view = "market_buy_input"


        # Mock market_impact (should not be called)
        self.mock_market_impact.apply_player_buy_impact = MagicMock()

        action_confirm_transaction(
            mock_ui_state.player_inventory_cache,
            mock_current_region,
            mock_ui_state.game_state_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with("Error: Not enough cash.")
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash) # Cash unchanged
        self.assertEqual(mock_ui_state.player_inventory_cache.get_quantity(drug_to_buy, quality_to_buy), initial_drug_quantity) # Inventory unchanged
        self.assertEqual(mock_current_region.drug_market_data[drug_to_buy]["available_qualities"][quality_to_buy]["quantity_available"], initial_market_stock) # Market stock unchanged

        self.mock_market_impact.apply_player_buy_impact.assert_not_called()
        # quantity_input_string should be cleared even on this error, as per code structure
        self.assertEqual(mock_ui_state.quantity_input_string, "")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_buy_insufficient_stock(self, mock_ui_state):
        initial_cash = 5000
        drug_price = 100
        market_stock_available = 5
        buy_quantity_attempt = 10 # Attempting to buy more than available
        drug_to_buy = DrugName.WEED
        quality_to_buy = DrugQuality.STANDARD

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        initial_drug_quantity_player = mock_ui_state.player_inventory_cache.get_quantity(drug_to_buy, quality_to_buy)

        # Region
        mock_current_region = Region(RegionName.DOWNTOWN.value)
        mock_current_region.initialize_drug_market(
            drug_to_buy, base_buy_price=drug_price, base_sell_price=drug_price + 20, tier=1,
            initial_stocks={quality_to_buy: market_stock_available}
        )
        # Ensure player_buy_impact_modifier exists, though not strictly needed for error path
        mock_current_region.drug_market_data[drug_to_buy]['player_buy_impact_modifier'] = 1.0


        # GameState
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs - not strictly needed for this error path
        mock_ui_state.game_configs_data_cache = MagicMock()

        # Transaction state on mock_ui_state
        mock_ui_state.current_transaction_type = "buy"
        mock_ui_state.drug_for_transaction = drug_to_buy
        mock_ui_state.quality_for_transaction = quality_to_buy
        mock_ui_state.price_for_transaction = drug_price
        mock_ui_state.available_for_transaction = market_stock_available
        mock_ui_state.quantity_input_string = str(buy_quantity_attempt)
        mock_ui_state.current_view = "market_buy_input"


        # Mock market_impact (should not be called)
        self.mock_market_impact.apply_player_buy_impact = MagicMock()

        action_confirm_transaction(
            mock_ui_state.player_inventory_cache,
            mock_current_region,
            mock_ui_state.game_state_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with("Error: Not enough market stock.")
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash) # Cash unchanged
        self.assertEqual(mock_ui_state.player_inventory_cache.get_quantity(drug_to_buy, quality_to_buy), initial_drug_quantity_player) # Inventory unchanged
        self.assertEqual(mock_current_region.drug_market_data[drug_to_buy]["available_qualities"][quality_to_buy]["quantity_available"], market_stock_available) # Market stock unchanged

        self.mock_market_impact.apply_player_buy_impact.assert_not_called()
        self.assertEqual(mock_ui_state.quantity_input_string, "") # quantity_input_string cleared

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_buy_insufficient_space(self, mock_ui_state):
        initial_cash = 5000
        drug_price = 100
        market_stock_available = 50
        buy_quantity_attempt = 10
        drug_to_buy = DrugName.WEED
        quality_to_buy = DrugQuality.STANDARD

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.max_capacity = 5 # Set low capacity
        # Player starts with 0 items, attempting to buy 10 will exceed capacity of 5.
        initial_drug_quantity_player = mock_ui_state.player_inventory_cache.get_quantity(drug_to_buy, quality_to_buy)


        # Region
        mock_current_region = Region(RegionName.DOWNTOWN.value)
        mock_current_region.initialize_drug_market(
            drug_to_buy, base_buy_price=drug_price, base_sell_price=drug_price + 20, tier=1,
            initial_stocks={quality_to_buy: market_stock_available}
        )
        initial_market_stock = mock_current_region.drug_market_data[drug_to_buy]["available_qualities"][quality_to_buy]["quantity_available"]


        # GameState
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()

        # Transaction state on mock_ui_state
        mock_ui_state.current_transaction_type = "buy"
        mock_ui_state.drug_for_transaction = drug_to_buy
        mock_ui_state.quality_for_transaction = quality_to_buy
        mock_ui_state.price_for_transaction = drug_price
        mock_ui_state.available_for_transaction = market_stock_available
        mock_ui_state.quantity_input_string = str(buy_quantity_attempt)
        mock_ui_state.current_view = "market_buy_input"


        # Mock market_impact (should not be called)
        self.mock_market_impact.apply_player_buy_impact = MagicMock()

        action_confirm_transaction(
            mock_ui_state.player_inventory_cache,
            mock_current_region,
            mock_ui_state.game_state_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with("Error: Not enough space.")
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash)
        self.assertEqual(mock_ui_state.player_inventory_cache.get_quantity(drug_to_buy, quality_to_buy), initial_drug_quantity_player)
        self.assertEqual(mock_current_region.drug_market_data[drug_to_buy]["available_qualities"][quality_to_buy]["quantity_available"], initial_market_stock)

        self.mock_market_impact.apply_player_buy_impact.assert_not_called()
        self.assertEqual(mock_ui_state.quantity_input_string, "")

    # --- Tests for action_confirm_transaction (Sell Scenarios - Edge Cases) ---

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_sell_insufficient_quantity(self, mock_ui_state):
        initial_cash = 100
        player_has_quantity = 5
        sell_quantity_attempt = 10 # Attempting to sell more than player has
        drug_to_sell = DrugName.WEED
        quality_to_sell = DrugQuality.STANDARD
        sell_price = 10

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.add_drug(drug_to_sell, quality_to_sell, player_has_quantity)

        # Region
        mock_current_region = Region(RegionName.DOWNTOWN.value)
        # Market stock not directly relevant for player selling error, but good to have consistent setup
        mock_current_region.initialize_drug_market(
            drug_to_sell, base_buy_price=sell_price - 5, base_sell_price=sell_price, tier=1,
            initial_stocks={quality_to_sell: 100}
        )
        initial_market_stock = mock_current_region.drug_market_data[drug_to_sell]["available_qualities"][quality_to_sell]["quantity_available"]


        # GameState
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs - not strictly needed for this error path
        mock_ui_state.game_configs_data_cache = MagicMock()

        # Transaction state on mock_ui_state
        mock_ui_state.current_transaction_type = "sell"
        mock_ui_state.drug_for_transaction = drug_to_sell
        mock_ui_state.quality_for_transaction = quality_to_sell
        mock_ui_state.price_for_transaction = sell_price
        mock_ui_state.available_for_transaction = player_has_quantity # This is player's stock
        mock_ui_state.quantity_input_string = str(sell_quantity_attempt)
        mock_ui_state.current_view = "market_sell_input"


        # Mock market_impact.apply_player_sell_impact (should not be called)
        self.mock_market_impact.apply_player_sell_impact = MagicMock()


        action_confirm_transaction(
            mock_ui_state.player_inventory_cache,
            mock_current_region,
            mock_ui_state.game_state_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with("Error: Not enough to sell.")
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash) # Cash unchanged
        self.assertEqual(mock_ui_state.player_inventory_cache.get_quantity(drug_to_sell, quality_to_sell), player_has_quantity) # Player inventory unchanged
        self.assertEqual(mock_current_region.drug_market_data[drug_to_sell]["available_qualities"][quality_to_sell]["quantity_available"], initial_market_stock) # Market stock unchanged

        self.mock_market_impact.apply_player_sell_impact.assert_not_called()
        self.assertEqual(mock_ui_state.quantity_input_string, "") # quantity_input_string cleared

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_sell_heat_no_skill(self, mock_ui_state):
        initial_cash = 100
        drug_to_sell = DrugName.WEED
        quality_to_sell = DrugQuality.STANDARD
        quantity_sold = 10
        sell_price = 10
        drug_tier = 1

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.add_drug(drug_to_sell, quality_to_sell, quantity_sold + 5) # Have more than selling
        mock_ui_state.player_inventory_cache.unlocked_skills.clear() # Ensure no skills

        # Region
        mock_current_region = Region(RegionName.DOWNTOWN.value)
        mock_current_region.initialize_drug_market(
            drug_to_sell, base_buy_price=sell_price -5, base_sell_price=sell_price, tier=drug_tier,
            initial_stocks={quality_to_sell: 100}
        )
        # Ensure necessary keys for sell impact and heat calculation
        mock_current_region.drug_market_data[drug_to_sell]['player_sell_impact_modifier'] = 1.0
        mock_current_region.drug_market_data[drug_to_sell]['player_buy_impact_modifier'] = 1.0
        initial_region_heat = mock_current_region.current_heat


        # GameState
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        heat_per_unit_tier1 = 2
        mock_ui_state.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER = {drug_tier: heat_per_unit_tier1}
        mock_ui_state.game_configs_data_cache.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT = game_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT # Still need this defined

        # Transaction state on mock_ui_state
        mock_ui_state.current_transaction_type = "sell"
        mock_ui_state.drug_for_transaction = drug_to_sell
        mock_ui_state.quality_for_transaction = quality_to_sell
        mock_ui_state.price_for_transaction = sell_price
        mock_ui_state.available_for_transaction = quantity_sold + 5 # Player's stock
        mock_ui_state.quantity_input_string = str(quantity_sold)
        mock_ui_state.current_view = "market" # To ensure quantity_input_string is cleared


        # Mock market_impact.apply_player_sell_impact
        self.mock_market_impact.apply_player_sell_impact = MagicMock()

        action_confirm_transaction(
            mock_ui_state.player_inventory_cache,
            mock_current_region,
            mock_ui_state.game_state_data_cache
        )

        # Assertions
        expected_cash = initial_cash + (sell_price * quantity_sold)
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, expected_cash)
        self.assertEqual(mock_ui_state.player_inventory_cache.get_quantity(drug_to_sell, quality_to_sell), 5) # Remaining stock

        self.mock_market_impact.apply_player_sell_impact.assert_called_once()

        base_heat_generated = heat_per_unit_tier1 * quantity_sold
        # No skill, so full heat applies
        self.assertEqual(mock_current_region.current_heat, initial_region_heat + base_heat_generated)

        self.mock_show_event_message.assert_called_once_with(f"Sold {quantity_sold} {drug_to_sell.value}. Heat +{base_heat_generated} in {mock_current_region.name.value}.")
        self.assertEqual(mock_ui_state.quantity_input_string, "")

    # --- Tests for action_confirm_tech_operation ---

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_buy_crypto_successful(self, mock_ui_state):
        initial_cash = 1000.0
        crypto_price = 10.0
        buy_amount_crypto = 5.0 # Amount of crypto to buy
        fee_percent = 0.01 # 1%
        heat_per_transaction = 5

        coin_to_buy = CryptoCoin.DRUG_COIN

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.unlocked_skills.clear()
        mock_ui_state.player_inventory_cache.has_secure_phone = False

        # GameState
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.name = RegionName.DOWNTOWN # or .value if needed by message
        mock_current_region.modify_heat = MagicMock()

        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_crypto_prices = {coin_to_buy: crypto_price}
        mock_ui_state.game_state_data_cache.current_day = 1
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION = heat_per_transaction
        mock_ui_state.game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT = 0.25 # Example
        mock_ui_state.game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT = 0.5 # Example
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {
            'CRYPTO_TRADE': {'fee_buy_sell': fee_percent}
        }
        # LAUNDERING_DELAY_DAYS not needed for this specific test

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.coin_for_tech_transaction = coin_to_buy
        mock_ui_state.tech_input_string = str(buy_amount_crypto)
        mock_ui_state.current_view = "tech_contact" # Initial view before action changes it


        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache # Pass the mock_configs directly
        )

        # Assertions
        expected_cost_of_crypto = buy_amount_crypto * crypto_price
        expected_fee = expected_cost_of_crypto * fee_percent
        expected_total_cash_deduction = expected_cost_of_crypto + expected_fee

        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.cash, initial_cash - expected_total_cash_deduction)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(coin_to_buy, 0), buy_amount_crypto)

        # Heat (no skills, no phone)
        mock_current_region.modify_heat.assert_called_once_with(heat_per_transaction)

        expected_message = f"Bought {buy_amount_crypto:.4f} {coin_to_buy.value}. Heat +{heat_per_transaction} in {mock_current_region.name.value}."
        self.mock_show_event_message.assert_called_once_with(expected_message)

        self.assertEqual(mock_ui_state.tech_input_string, "") # Input cleared
        self.assertIsNone(mock_ui_state.tech_transaction_in_progress) # Transaction state cleared
        self.assertEqual(mock_ui_state.current_view, "tech_contact") # View reset

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_buy_crypto_insufficient_cash(self, mock_ui_state):
        initial_cash = 1.0 # Very low cash
        crypto_price = 10.0
        buy_amount_crypto = 5.0 # Cost = 50 + fee
        fee_percent = 0.01
        coin_to_buy = CryptoCoin.DRUG_COIN

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        initial_crypto_amount = mock_ui_state.player_inventory_cache.crypto_wallet.get(coin_to_buy, 0)

        # GameState (Region mock for heat, not strictly needed for this error path but good for consistency)
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.modify_heat = MagicMock()
        mock_current_region.name = RegionName.DOWNTOWN # Set the name attribute
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_crypto_prices = {coin_to_buy: crypto_price}
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {
            'CRYPTO_TRADE': {'fee_buy_sell': fee_percent}
        }
        # Other configs like HEAT_FROM_CRYPTO_TRANSACTION are not essential for this error path

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.coin_for_tech_transaction = coin_to_buy
        mock_ui_state.tech_input_string = str(buy_amount_crypto)
        # current_view does not strictly matter here as the function should return early

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with("Error: Not enough cash.")
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash) # Cash unchanged
        self.assertEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(coin_to_buy, 0), initial_crypto_amount) # Crypto unchanged
        mock_current_region.modify_heat.assert_not_called()
        self.assertEqual(mock_ui_state.tech_input_string, "") # Input is cleared on this error

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_sell_crypto_successful(self, mock_ui_state):
        initial_cash = 100.0
        initial_crypto_amount = 10.0
        crypto_price = 10.0
        sell_amount_crypto = 5.0
        fee_percent = 0.01 # 1%
        heat_per_transaction = 5

        coin_to_sell = CryptoCoin.DRUG_COIN

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.crypto_wallet = {coin_to_sell: initial_crypto_amount}
        mock_ui_state.player_inventory_cache.unlocked_skills.clear()
        mock_ui_state.player_inventory_cache.has_secure_phone = False

        # GameState
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.name = RegionName.DOWNTOWN
        mock_current_region.modify_heat = MagicMock()

        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_crypto_prices = {coin_to_sell: crypto_price}
        mock_ui_state.game_state_data_cache.current_day = 1 # Not strictly needed but good for consistency
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION = heat_per_transaction
        mock_ui_state.game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT = 0.25
        mock_ui_state.game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT = 0.5
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {
            'CRYPTO_TRADE': {'fee_buy_sell': fee_percent}
        }

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "sell_crypto"
        mock_ui_state.coin_for_tech_transaction = coin_to_sell
        mock_ui_state.tech_input_string = str(sell_amount_crypto)
        mock_ui_state.current_view = "tech_contact"


        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        expected_crypto_value = sell_amount_crypto * crypto_price
        expected_fee = expected_crypto_value * fee_percent
        expected_cash_gain = expected_crypto_value - expected_fee

        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.cash, initial_cash + expected_cash_gain)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(coin_to_sell, 0), initial_crypto_amount - sell_amount_crypto)

        mock_current_region.modify_heat.assert_called_once_with(heat_per_transaction)

        expected_message = f"Sold {sell_amount_crypto:.4f} {coin_to_sell.value}. Heat +{heat_per_transaction} in {mock_current_region.name.value}."
        self.mock_show_event_message.assert_called_once_with(expected_message)

        self.assertEqual(mock_ui_state.tech_input_string, "")
        self.assertIsNone(mock_ui_state.tech_transaction_in_progress)
        self.assertEqual(mock_ui_state.current_view, "tech_contact")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_sell_crypto_insufficient_crypto(self, mock_ui_state):
        initial_cash = 100.0
        player_has_crypto_amount = 2.0
        crypto_price = 10.0
        sell_amount_attempt = 5.0 # Attempting to sell more
        coin_to_sell = CryptoCoin.DRUG_COIN

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.crypto_wallet = {coin_to_sell: player_has_crypto_amount}

        # GameState
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.name = RegionName.DOWNTOWN
        mock_current_region.modify_heat = MagicMock()
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_crypto_prices = {coin_to_sell: crypto_price}
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = { # Needed for fee calculation, though error is earlier
            'CRYPTO_TRADE': {'fee_buy_sell': 0.01}
        }

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "sell_crypto"
        mock_ui_state.coin_for_tech_transaction = coin_to_sell
        mock_ui_state.tech_input_string = str(sell_amount_attempt)

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with("Error: Not enough crypto.")
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash)
        self.assertEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(coin_to_sell, 0), player_has_crypto_amount)
        mock_current_region.modify_heat.assert_not_called()
        self.assertEqual(mock_ui_state.tech_input_string, "") # Input is cleared

    # --- Laundering Tests ---
    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_launder_cash_successful(self, mock_ui_state):
        initial_cash = 10000.0
        launder_amount = 5000.0
        launder_fee_percent = 0.05 # 5%
        current_day = 5
        laundering_delay = 3

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.pending_laundered_sc = 0.0 # Ensure it starts at 0
        mock_ui_state.player_inventory_cache.pending_laundered_sc_arrival_day = None


        # GameState
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.name = RegionName.DOWNTOWN
        mock_current_region.modify_heat = MagicMock()
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_day = current_day
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {
            'LAUNDER_CASH': {'fee': launder_fee_percent}
        }
        mock_ui_state.game_configs_data_cache.LAUNDERING_DELAY_DAYS = laundering_delay
        # Heat for laundering is calculated differently, not using HEAT_FROM_CRYPTO_TRANSACTION directly

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "launder_cash"
        mock_ui_state.tech_input_string = str(launder_amount)
        mock_ui_state.current_view = "tech_contact"


        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        expected_fee = launder_amount * launder_fee_percent
        expected_total_cash_deduction = launder_amount + expected_fee

        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.cash, initial_cash - expected_total_cash_deduction)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.pending_laundered_sc, launder_amount)
        self.assertEqual(mock_ui_state.player_inventory_cache.pending_laundered_sc_arrival_day, current_day + laundering_delay)

        expected_heat = int(launder_amount * 0.05)
        mock_current_region.modify_heat.assert_called_once_with(expected_heat)

        expected_message = f"Laundered ${launder_amount:,.2f}. Fee ${expected_fee:,.2f}. Arrives day {current_day + laundering_delay}. Heat +{expected_heat} in {mock_current_region.name.value}."
        self.mock_show_event_message.assert_called_once_with(expected_message)

        self.assertEqual(mock_ui_state.tech_input_string, "")
        self.assertIsNone(mock_ui_state.tech_transaction_in_progress)
        self.assertEqual(mock_ui_state.current_view, "tech_contact")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_launder_cash_insufficient_cash(self, mock_ui_state):
        initial_cash = 100.0 # Not enough to launder 5000 + fee
        launder_amount_attempt = 5000.0
        launder_fee_percent = 0.05

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        initial_pending_sc = mock_ui_state.player_inventory_cache.pending_laundered_sc
        initial_arrival_day = mock_ui_state.player_inventory_cache.pending_laundered_sc_arrival_day

        # GameState
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.name = RegionName.DOWNTOWN
        mock_current_region.modify_heat = MagicMock()
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_day = 1 # Not critical for this error path
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {
            'LAUNDER_CASH': {'fee': launder_fee_percent}
        }
        mock_ui_state.game_configs_data_cache.LAUNDERING_DELAY_DAYS = 3 # Not critical for this error path

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "launder_cash"
        mock_ui_state.tech_input_string = str(launder_amount_attempt)

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with("Error: Not enough cash for amount + fee.")
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash)
        self.assertEqual(mock_ui_state.player_inventory_cache.pending_laundered_sc, initial_pending_sc)
        self.assertEqual(mock_ui_state.player_inventory_cache.pending_laundered_sc_arrival_day, initial_arrival_day)
        mock_current_region.modify_heat.assert_not_called()
        self.assertEqual(mock_ui_state.tech_input_string, "") # Input is cleared on this error

    # --- Staking Tests ---
    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_stake_dc_successful(self, mock_ui_state):
        initial_dc_in_wallet = 100.0
        stake_amount = 50.0
        initial_staked_amount = 10.0

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.crypto_wallet = {CryptoCoin.DRUG_COIN: initial_dc_in_wallet}
        mock_ui_state.player_inventory_cache.staked_drug_coin = {'staked_amount': initial_staked_amount, 'pending_rewards': 0.0}

        # GameState & GameConfigs - minimal needed for this operation
        mock_current_region = MagicMock(spec=Region); mock_current_region.name = RegionName.DOWNTOWN # For potential messages
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)
        mock_ui_state.game_configs_data_cache = MagicMock() # No specific configs used by stake action directly

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "stake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.DRUG_COIN # Important for the action
        mock_ui_state.tech_input_string = str(stake_amount)
        mock_ui_state.current_view = "tech_contact"


        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0), initial_dc_in_wallet - stake_amount)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['staked_amount'], initial_staked_amount + stake_amount)

        self.mock_show_event_message.assert_called_once_with(f"Staked {stake_amount:.4f} DC.")

        self.assertEqual(mock_ui_state.tech_input_string, "")
        self.assertIsNone(mock_ui_state.tech_transaction_in_progress)
        self.assertEqual(mock_ui_state.current_view, "tech_contact")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_stake_dc_insufficient_dc(self, mock_ui_state):
        initial_dc_in_wallet = 10.0
        stake_amount_attempt = 50.0 # Attempting to stake more than in wallet
        initial_staked_amount = 5.0

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.crypto_wallet = {CryptoCoin.DRUG_COIN: initial_dc_in_wallet}
        mock_ui_state.player_inventory_cache.staked_drug_coin = {'staked_amount': initial_staked_amount, 'pending_rewards': 0.0}

        # GameState & GameConfigs - minimal
        mock_current_region = MagicMock(spec=Region); mock_current_region.name = RegionName.DOWNTOWN
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region) # For message context
        mock_ui_state.game_configs_data_cache = MagicMock()

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "stake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.DRUG_COIN
        mock_ui_state.tech_input_string = str(stake_amount_attempt)

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with(f"Error: Not enough {CryptoCoin.DRUG_COIN.value} or wrong coin.")
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0), initial_dc_in_wallet)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['staked_amount'], initial_staked_amount)
        self.assertEqual(mock_ui_state.tech_input_string, "") # Input is cleared on this error path

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_unstake_dc_successful(self, mock_ui_state):
        initial_dc_in_wallet = 5.0
        initial_staked_amount = 100.0
        initial_pending_rewards = 10.0
        unstake_amount = 50.0

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.crypto_wallet = {CryptoCoin.DRUG_COIN: initial_dc_in_wallet}
        mock_ui_state.player_inventory_cache.staked_drug_coin = {
            'staked_amount': initial_staked_amount,
            'pending_rewards': initial_pending_rewards
        }

        # GameState & GameConfigs - minimal
        mock_current_region = MagicMock(spec=Region); mock_current_region.name = RegionName.DOWNTOWN
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)
        mock_ui_state.game_configs_data_cache = MagicMock()

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "unstake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.DRUG_COIN
        mock_ui_state.tech_input_string = str(unstake_amount)
        mock_ui_state.current_view = "tech_contact"

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['staked_amount'], initial_staked_amount - unstake_amount)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['pending_rewards'], 0.0)

        expected_dc_in_wallet = initial_dc_in_wallet + unstake_amount + initial_pending_rewards
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0), expected_dc_in_wallet)

        self.mock_show_event_message.assert_called_once_with(f"Unstaked {unstake_amount:.4f} DC. Rewards collected: {initial_pending_rewards:.4f} DC.")

        self.assertEqual(mock_ui_state.tech_input_string, "")
        self.assertIsNone(mock_ui_state.tech_transaction_in_progress)
        self.assertEqual(mock_ui_state.current_view, "tech_contact")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_unstake_dc_insufficient_staked(self, mock_ui_state):
        initial_dc_in_wallet = 5.0
        initial_staked_amount = 20.0
        initial_pending_rewards = 5.0
        unstake_amount_attempt = 50.0 # Attempt to unstake more than available

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.crypto_wallet = {CryptoCoin.DRUG_COIN: initial_dc_in_wallet}
        mock_ui_state.player_inventory_cache.staked_drug_coin = {
            'staked_amount': initial_staked_amount,
            'pending_rewards': initial_pending_rewards
        }

        # GameState & GameConfigs - minimal
        mock_current_region = MagicMock(spec=Region); mock_current_region.name = RegionName.DOWNTOWN
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)
        mock_ui_state.game_configs_data_cache = MagicMock()

        # Tech operation state on mock_ui_state
        mock_ui_state.tech_transaction_in_progress = "unstake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.DRUG_COIN
        mock_ui_state.tech_input_string = str(unstake_amount_attempt)

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        # Assertions
        self.mock_show_event_message.assert_called_once_with(f"Error: Not enough staked {CryptoCoin.DRUG_COIN.value} or wrong coin.")
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0), initial_dc_in_wallet)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['staked_amount'], initial_staked_amount)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['pending_rewards'], initial_pending_rewards)
        self.assertEqual(mock_ui_state.tech_input_string, "") # Input is cleared

    # --- Heat Reduction Tests (using buy_crypto as example) ---
    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_buy_crypto_heat_with_skill(self, mock_ui_state):
        initial_cash = 1000.0
        crypto_price = 10.0
        buy_amount_crypto = 5.0
        fee_percent = 0.01
        base_heat_per_transaction = 10 # Higher base heat for clearer reduction
        digital_footprint_reduction = 0.25

        coin_to_buy = CryptoCoin.BITCOIN # Using a different coin for variety

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.unlocked_skills.add(SkillID.DIGITAL_FOOTPRINT.value) # Has the skill
        mock_ui_state.player_inventory_cache.has_secure_phone = False

        # GameState
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.name = RegionName.DOWNTOWN
        mock_current_region.modify_heat = MagicMock()
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_crypto_prices = {coin_to_buy: crypto_price}
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION = base_heat_per_transaction
        mock_ui_state.game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT = digital_footprint_reduction
        mock_ui_state.game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT = 0.5 # Define but not used by player
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {'CRYPTO_TRADE': {'fee_buy_sell': fee_percent}}

        # Tech operation state
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.coin_for_tech_transaction = coin_to_buy
        mock_ui_state.tech_input_string = str(buy_amount_crypto)

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        expected_heat = math.ceil(base_heat_per_transaction * (1 - digital_footprint_reduction))
        mock_current_region.modify_heat.assert_called_once_with(expected_heat)
        # Other assertions (cash, crypto, message) can be added if desired for full success validation,
        # but the focus here is on heat. For brevity, only heat is asserted.
        expected_message = f"Bought {buy_amount_crypto:.4f} {coin_to_buy.value}. Heat +{expected_heat} in {mock_current_region.name.value}."
        self.mock_show_event_message.assert_called_once_with(expected_message)

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_buy_crypto_heat_with_phone(self, mock_ui_state):
        initial_cash = 1000.0
        crypto_price = 10.0
        buy_amount_crypto = 5.0
        fee_percent = 0.01
        base_heat_per_transaction = 10
        secure_phone_reduction = 0.5

        coin_to_buy = CryptoCoin.ETHEREUM

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.unlocked_skills.clear()
        mock_ui_state.player_inventory_cache.has_secure_phone = True # Has the phone

        # GameState
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.name = RegionName.DOWNTOWN
        mock_current_region.modify_heat = MagicMock()
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_crypto_prices = {coin_to_buy: crypto_price}
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION = base_heat_per_transaction
        mock_ui_state.game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT = 0.25 # Define but not used
        mock_ui_state.game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT = secure_phone_reduction
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {'CRYPTO_TRADE': {'fee_buy_sell': fee_percent}}

        # Tech operation state
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.coin_for_tech_transaction = coin_to_buy
        mock_ui_state.tech_input_string = str(buy_amount_crypto)

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        expected_heat = math.ceil(base_heat_per_transaction * (1 - secure_phone_reduction))
        mock_current_region.modify_heat.assert_called_once_with(expected_heat)
        expected_message = f"Bought {buy_amount_crypto:.4f} {coin_to_buy.value}. Heat +{expected_heat} in {mock_current_region.name.value}."
        self.mock_show_event_message.assert_called_once_with(expected_message)

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_buy_crypto_heat_with_skill_and_phone(self, mock_ui_state):
        initial_cash = 1000.0
        crypto_price = 10.0
        buy_amount_crypto = 5.0
        fee_percent = 0.01
        base_heat_per_transaction = 20 # Higher base for more noticeable reduction
        digital_footprint_reduction = 0.25
        secure_phone_reduction = 0.5

        coin_to_buy = CryptoCoin.MONERO

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.unlocked_skills.add(SkillID.DIGITAL_FOOTPRINT.value) # Has skill
        mock_ui_state.player_inventory_cache.has_secure_phone = True # Has phone

        # GameState
        mock_current_region = MagicMock(spec=Region)
        mock_current_region.name = RegionName.DOWNTOWN
        mock_current_region.modify_heat = MagicMock()
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_crypto_prices = {coin_to_buy: crypto_price}
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=mock_current_region)

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION = base_heat_per_transaction
        mock_ui_state.game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT = digital_footprint_reduction
        mock_ui_state.game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT = secure_phone_reduction
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {'CRYPTO_TRADE': {'fee_buy_sell': fee_percent}}

        # Tech operation state
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.coin_for_tech_transaction = coin_to_buy
        mock_ui_state.tech_input_string = str(buy_amount_crypto)

        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )

        heat_after_skill = base_heat_per_transaction * (1 - digital_footprint_reduction)
        heat_after_phone = heat_after_skill * (1 - secure_phone_reduction)
        expected_heat = math.ceil(heat_after_phone)

        mock_current_region.modify_heat.assert_called_once_with(expected_heat)
        expected_message = f"Bought {buy_amount_crypto:.4f} {coin_to_buy.value}. Heat +{expected_heat} in {mock_current_region.name.value}."
        self.mock_show_event_message.assert_called_once_with(expected_message)

    # --- More tests for action_travel_to_region ---

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_travel_police_stop_occurs(self, mock_ui_state):
        initial_cash = 100
        travel_cost = game_configs.TRAVEL_COST_CASH

        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash

        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.current_player_region = self.source_region # Old attribute style for mock
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=self.source_region) # Method style
        mock_ui_state.game_state_data_cache.current_day = 1
        mock_ui_state.game_state_data_cache.all_regions = {self.dest_region.name: self.dest_region}


        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = travel_cost
        # Ensure other configs needed by travel are present, even if not central to this test
        mock_ui_state.game_configs_data_cache.CRYPTO_VOLATILITY = {}
        mock_ui_state.game_configs_data_cache.CRYPTO_MIN_PRICE = {}
        mock_ui_state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY = 1 # Example
        mock_ui_state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = 0.1 # Example


        mock_ui_state.campaign_day = 1 # Matches game_state_data_cache.current_day for consistency

        self.mock_check_police_stop.return_value = True # Police stop OCCURS

        action_travel_to_region(
            self.dest_region,
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache
        )

        # Assertions
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash - travel_cost) # Cash deducted
        # In action_travel_to_region, game_state.set_current_player_region(dest_region_obj.name) is called
        mock_ui_state.game_state_data_cache.set_current_player_region.assert_called_once_with(self.dest_region.name)
        self.assertEqual(mock_ui_state.game_state_data_cache.current_day, 2) # Day advanced

        self.mock_show_event_message.assert_called_with("Police stop! Event triggered.") # Check correct message
        self.assertEqual(mock_ui_state.current_view, "blocking_event_popup") # View changed

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_travel_heat_decay_no_skill(self, mock_ui_state):
        initial_cash = 100
        initial_heat = 10
        base_daily_decay = 2 # Using a slightly higher decay for clearer test
        travel_cost = game_configs.TRAVEL_COST_CASH

        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.heat = initial_heat
        mock_ui_state.player_inventory_cache.unlocked_skills.clear() # No skills

        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=self.source_region)
        mock_ui_state.game_state_data_cache.current_day = 1
        mock_ui_state.game_state_data_cache.all_regions = {self.dest_region.name: self.dest_region}
        # set_current_player_region will be called, no need to mock specific return unless checking its arg

        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = travel_cost
        mock_ui_state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY = base_daily_decay
        mock_ui_state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = 0.15 # Defined but not used by player
        mock_ui_state.game_configs_data_cache.CRYPTO_VOLATILITY = {}
        mock_ui_state.game_configs_data_cache.CRYPTO_MIN_PRICE = {}

        mock_ui_state.campaign_day = 1

        self.mock_check_police_stop.return_value = False # No police stop

        action_travel_to_region(
            self.dest_region,
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache
        )

        expected_heat = max(0, initial_heat - base_daily_decay)
        self.assertEqual(mock_ui_state.player_inventory_cache.heat, expected_heat)

        expected_log_message = (
            f"Player daily heat decay: {base_daily_decay} (Base: {base_daily_decay}). "
            f"Player heat reduced from {initial_heat} to {expected_heat}."
        )
        # Check if add_message_to_log was called with the expected message
        # This requires add_message_to_log to be patched in setUp, which it is now.

        self.mock_add_message_to_log.assert_any_call(expected_log_message)

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_travel_laundered_cash_arrives(self, mock_ui_state):
        initial_cash = 100
        travel_cost = game_configs.TRAVEL_COST_CASH
        laundered_amount = 5000.0
        initial_stable_coin_balance = 50.0
        current_day_start = 1

        # Player Inventory
        mock_ui_state.player_inventory_cache = PlayerInventory()
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.pending_laundered_sc = laundered_amount
        # Arrival day is set to the day *after* travel completes
        mock_ui_state.player_inventory_cache.pending_laundered_sc_arrival_day = current_day_start + 1
        mock_ui_state.player_inventory_cache.laundered_crypto_type = CryptoCoin.BITCOIN # Use a valid coin
        mock_ui_state.player_inventory_cache.crypto_wallet = {CryptoCoin.BITCOIN: initial_stable_coin_balance}
        # Explicitly set laundered_crypto_type or rely on getattr default in action.py
        # For this test, let's assume it defaults to STABLE_COIN if not set, or set it:
        # mock_ui_state.player_inventory_cache.laundered_crypto_type = CryptoCoin.STABLE_COIN


        # GameState
        mock_ui_state.game_state_data_cache = MagicMock(spec=GameState)
        mock_ui_state.game_state_data_cache.get_current_player_region = MagicMock(return_value=self.source_region)
        mock_ui_state.game_state_data_cache.current_day = current_day_start
        mock_ui_state.game_state_data_cache.all_regions = {self.dest_region.name: self.dest_region}

        # Game Configs
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = travel_cost
        # Other travel-related configs that are accessed by the function
        mock_ui_state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY = 1
        mock_ui_state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = 0.0
        mock_ui_state.game_configs_data_cache.CRYPTO_VOLATILITY = {}
        mock_ui_state.game_configs_data_cache.CRYPTO_MIN_PRICE = {}


        mock_ui_state.campaign_day = current_day_start # Sync with game_state_data_cache
        self.mock_check_police_stop.return_value = False # No police stop

        action_travel_to_region(
            self.dest_region,
            mock_ui_state.player_inventory_cache,
            mock_ui_state.game_state_data_cache
        )

        # Assertions
        # Travel effects
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash - travel_cost)
        self.assertEqual(mock_ui_state.game_state_data_cache.current_day, current_day_start + 1)
        mock_ui_state.game_state_data_cache.set_current_player_region.assert_called_once_with(self.dest_region.name)

        # Laundering effects
        expected_bitcoin_balance = initial_stable_coin_balance + laundered_amount
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(CryptoCoin.BITCOIN, 0), expected_bitcoin_balance)
        self.assertEqual(mock_ui_state.player_inventory_cache.pending_laundered_sc, 0.0)
        self.assertIsNone(mock_ui_state.player_inventory_cache.pending_laundered_sc_arrival_day)


if __name__ == '__main__':
    unittest.main()
