import unittest
from unittest.mock import patch, MagicMock

# Adjust imports based on actual project structure
import src.ui_pygame.state # Ensure the module is loaded for patching
from src.ui_pygame.actions import action_travel_to_region, action_confirm_transaction # Ensure action_confirm_transaction is imported
from src.core.player_inventory import PlayerInventory
from src.core.enums import SkillID # Added for skill tests
from src.core.region import Region
import math # Added for skill effect calculations
from src.core.enums import RegionName, DrugName, DrugQuality # Assuming DrugName, DrugQuality might be needed by PlayerInventory or Region indirectly
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
        self.patch_update_crypto = patch('src.game_state.update_daily_crypto_prices') # Corrected
        self.patch_update_events = patch('src.mechanics.event_manager.update_active_events') # Corrected

        self.mock_show_event_message = self.patch_show_event_message.start()
        self.mock_setup_buttons = self.patch_setup_buttons.start()
        self.mock_check_police_stop = self.patch_check_police_stop.start()
        self.mock_update_crypto = self.patch_update_crypto.start()
        self.mock_update_events = self.patch_update_events.start()

    def tearDown(self):
        self.patch_show_event_message.stop()
        self.patch_setup_buttons.stop()
        self.patch_check_police_stop.stop()
        self.patch_update_crypto.stop()
        self.patch_update_events.stop()

    @patch('src.ui_pygame.state', new_callable=MagicMock) # Corrected: mock the 'state' module directly
    def test_travel_successful(self, mock_ui_state): # Renamed arg to avoid confusion with mock_actions_state
        initial_cash = 100
        travel_cost = game_configs.TRAVEL_COST_CASH # Use the actual constant

        # Configure the mock_actions_state
        # This mock represents the 'state' module/object used within actions.py
        mock_ui_state.player_inventory_cache = PlayerInventory() # Adjusted
        mock_ui_state.player_inventory_cache.cash = initial_cash

        mock_ui_state.game_state_data_cache = MockGameState(self.source_region)
        # mock_ui_state.game_state_data_cache.current_player_region = self.source_region
        # mock_ui_state.game_state_data_cache.current_day = 1

        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = travel_cost
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


    @patch('src.ui_pygame.state', new_callable=MagicMock) # Corrected: mock the 'state' module directly
    def test_travel_insufficient_cash(self, mock_ui_state): # Renamed arg
        initial_cash = 20
        travel_cost = game_configs.TRAVEL_COST_CASH

        mock_ui_state.player_inventory_cache = PlayerInventory() # Adjusted
        mock_ui_state.player_inventory_cache.cash = initial_cash

        mock_ui_state.game_state_data_cache = MockGameState(self.source_region)
        # mock_ui_state.game_state_data_cache.current_player_region = self.source_region
        # mock_ui_state.game_state_data_cache.current_day = 1

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
        # Mock region's drug market data if needed for HEAT_FROM_SELLING_DRUG_TIER
        # Ensure drug_to_sell (DrugName enum) is used as key if region expects enums
        mock_region.drug_market_data[drug_to_sell] = {
            "tier": 1,
            "available_qualities": {quality_to_sell: {"quantity_available": 1000}},
            "player_sell_impact_modifier": 1.0, # Add missing key
            "player_buy_impact_modifier": 1.0   # Add missing key
        }

        mock_ui_state.game_state_data_cache = MockGameState(mock_region) # MockGameState from existing tests

        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER = {1: 2} # Heat per unit for Tier 1 drug
        # Ensure game_configs_module is imported at the top of the test file if using it like this
        # For consistency with the GDD, using game_configs_module directly here for the percentage
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
        mock_ui_state.player_inventory_cache.heat = 10 # Initial heat
        mock_ui_state.player_inventory_cache.cash = 100 # Enough for travel
        mock_ui_state.player_inventory_cache.unlocked_skills.add(SkillID.GHOST_PROTOCOL.value)

        mock_source_region = Region(RegionName.DOWNTOWN.value)
        mock_dest_region = Region(RegionName.SUBURBS.value)
        mock_ui_state.game_state_data_cache = MockGameState(mock_source_region)
        mock_ui_state.game_state_data_cache.all_regions = {RegionName.SUBURBS: mock_dest_region}


        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = 50
        # Using game_configs for these, as they are defined there
        mock_ui_state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY = game_configs.BASE_DAILY_HEAT_DECAY
        mock_ui_state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = game_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
        mock_ui_state.game_configs_data_cache.CRYPTO_VOLATILITY = {} # for update_daily_crypto_prices
        mock_ui_state.game_configs_data_cache.CRYPTO_MIN_PRICE = {}  # for update_daily_crypto_prices


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


if __name__ == '__main__':
    unittest.main()
