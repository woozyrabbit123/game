import unittest
from unittest.mock import Mock, patch
import random

from src.core.enums import EventType, DrugName, RegionName, Quality # Assuming Quality is DrugQuality
from src.core.player_inventory import PlayerInventory
from src.game_state import GameState
from src.core.region import Region
from src.mechanics.daily_updates import _try_trigger_opportunity_event # Helper from daily_updates
from src import narco_configs # To access OPPORTUNITY_EVENTS_DEFINITIONS

class TestTryTriggerOpportunityEvent(unittest.TestCase):

    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_player_inventory.items = { # Make sure player has some drugs for URGENT_DELIVERY
            DrugName.COKE: {DrugQuality.STANDARD: 20}
        }
        self.mock_player_inventory.get_quantity = Mock(return_value=20)


        self.mock_game_state = Mock(spec=GameState)
        self.mock_game_state.current_day = 1
        
        mock_region_downtown = Mock(spec=Region)
        mock_region_downtown.name = RegionName.DOWNTOWN
        mock_region_docks = Mock(spec=Region)
        mock_region_docks.name = RegionName.DOCKS
        # Mock get_sell_price for URGENT_DELIVERY reward calculation
        mock_region_docks.get_sell_price = Mock(return_value=1000.0)


        self.mock_game_state.get_current_player_region = Mock(return_value=mock_region_downtown)
        self.mock_game_state.all_regions = {
            RegionName.DOWNTOWN: mock_region_downtown,
            RegionName.DOCKS: mock_region_docks # For URGENT_DELIVERY target
        }


        self.mock_game_configs = Mock()
        self.mock_game_configs.OPPORTUNITY_EVENT_BASE_CHANCE = 1.0 # Ensure trigger for testing
        self.mock_game_configs.MINIMUM_DRUG_PRICE = 1.0 # For URGENT_DELIVERY fallback

        # Use a copy of the actual definitions for safety, but mock if they are too complex
        self.mock_game_configs.OPPORTUNITY_EVENTS_DEFINITIONS = {
            EventType.RIVAL_STASH_LEAKED: {
                "name": "Rival's Stash Leaked",
                "description_template": "Stash of {drug_name} ({quantity} units) found.",
                "choices": [{"text": "Steal"}, {"text": "Ignore"}]
            },
            EventType.URGENT_DELIVERY: {
                "name": "Urgent Delivery",
                "description_template": "Deliver {quantity} {drug_name} to {target_region_name} for ${reward_per_unit:.2f} premium.",
                "choices": [{"id": "accept_delivery", "text": "Accept"}, {"text": "Decline"}]
            },
            EventType.EXPERIMENTAL_DRUG_BATCH: {
                "name": "Experimental Drug Batch",
                "description_template": "Buy {quantity} experimental {drug_name} for ${cost:.2f}.",
                "choices": [{"text": "Buy"}, {"text": "Pass"}]
            }
        }
        # Ensure necessary drug enums are available if not mocked deeply
        # For simplicity, assuming DrugName.COKE, etc. are accessible

    @patch('random.random', return_value=0.0) # Ensure base chance triggers
    @patch('random.choice') # To control which event is chosen
    def test_trigger_rival_stash_leaked(self, mock_random_choice, mock_random_roll):
        mock_random_choice.return_value = EventType.RIVAL_STASH_LEAKED
        # Mock further random choices within the event population if necessary
        patch('random.choice', side_effect=[EventType.RIVAL_STASH_LEAKED, DrugName.COKE]).start() # event type, then drug name
        patch('random.randint', return_value=20).start() # quantity for description

        event_data = _try_trigger_opportunity_event(self.mock_game_state, self.mock_player_inventory, self.mock_game_configs)
        
        self.assertIsNotNone(event_data)
        self.assertEqual(event_data["title"], "Rival's Stash Leaked")
        self.assertTrue(DrugName.COKE.value in event_data["messages"][0])
        self.assertTrue("20 units" in event_data["messages"][0])
        self.assertEqual(event_data["event_type_id"], EventType.RIVAL_STASH_LEAKED.value)
        self.assertTrue(event_data["is_opportunity_event"])
        self.assertEqual(len(event_data["choices"]), 2)
        self.assertEqual(event_data["runtime_params"]["drug_name"], DrugName.COKE)
        self.assertEqual(event_data["runtime_params"]["quantity"], 20)
        patch.stopall()

    @patch('random.random', return_value=0.0)
    @patch('random.choice') # To control event and drug/region choices
    def test_trigger_urgent_delivery(self, mock_random_choice, mock_random_roll):
        # Order of random.choice: event type, drug from player inv, quality, target region
        # Ensure player_inventory.items is set up for this
        self.mock_player_inventory.items = {DrugName.COKE: {DrugQuality.STANDARD: 25}}
        self.mock_player_inventory.get_quantity = Mock(return_value=25) # Mock to return enough quantity

        # Side effect for random.choice:
        # 1. EventType.URGENT_DELIVERY
        # 2. DrugName.COKE (from player's inventory for delivery)
        # 3. DrugQuality.STANDARD (quality the player has)
        # 4. A target region (e.g., DOCKS from the mocked all_regions)
        mock_random_choice.side_effect = [
            EventType.URGENT_DELIVERY, 
            DrugName.COKE, 
            DrugQuality.STANDARD,
            self.mock_game_state.all_regions[RegionName.DOCKS]
        ]
        patch('random.randint', return_value=10).start() # quantity_needed for delivery
        patch('random.uniform', return_value=0.3).start() # For reward_premium_per_unit calculation

        event_data = _try_trigger_opportunity_event(self.mock_game_state, self.mock_player_inventory, self.mock_game_configs)
        
        self.assertIsNotNone(event_data)
        self.assertEqual(event_data["title"], "Urgent Delivery")
        self.assertTrue("10 units" in event_data["messages"][0])
        self.assertTrue(DrugName.COKE.value in event_data["messages"][0])
        self.assertTrue(RegionName.DOCKS.value in event_data["messages"][0])
        self.assertEqual(event_data["runtime_params"]["drug_name"], DrugName.COKE)
        self.assertEqual(event_data["runtime_params"]["quantity"], 10)
        self.assertEqual(event_data["choices"][0]["text"], "Accept (Need 10 Coke)")
        patch.stopall()

    def test_no_trigger_if_chance_fails(self):
        with patch('random.random', return_value=0.9): # Higher than OPPORTUNITY_EVENT_BASE_CHANCE
            event_data = _try_trigger_opportunity_event(self.mock_game_state, self.mock_player_inventory, self.mock_game_configs)
            self.assertIsNone(event_data)

class TestResolveOpportunityEventChoice(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_player_inventory.cash = 1000.0
        self.mock_player_inventory.unlocked_skills = set()
        self.mock_player_inventory.contact_trusts = {}
        self.mock_player_inventory.items = {}
        self.mock_player_inventory.special_items = {}
        self.mock_player_inventory.add_drug = Mock(return_value=True)
        self.mock_player_inventory.remove_drug = Mock(return_value=True)
        self.mock_player_inventory.get_quantity = Mock(return_value=0) # Default to 0

        self.mock_game_state = Mock(spec=GameState)
        self.mock_region = Mock(spec=Region)
        self.mock_region.name = RegionName.DOWNTOWN
        self.mock_region.current_heat = 10
        self.mock_region.modify_heat = Mock()
        self.mock_game_state.get_current_player_region = Mock(return_value=self.mock_region)
        
        self.mock_ui_manager = Mock()
        self.mock_ui_manager.active_blocking_event_data = None # This will be set per test

        # Patch app.py's global caches and ui_manager
        self.patchers = [
            patch('src.ui_pygame.app.player_inventory_cache', self.mock_player_inventory),
            patch('src.ui_pygame.app.game_state_data_cache', self.mock_game_state),
            patch('src.ui_pygame.app.game_configs_data_cache', narco_configs), # Use actual configs for some parts
            patch('src.ui_pygame.app.ui_manager', self.mock_ui_manager),
            patch('src.ui_pygame.app.show_event_message_external', Mock()), # Mock UI calls
            patch('src.ui_pygame.app.add_message_to_log', Mock()) # Mock logging
        ]
        for p in self.patchers:
            p.start()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_resolve_rival_stash_leaked_success(self):
        from src.ui_pygame.app import action_resolve_opportunity_event_choice
        
        event_def = narco_configs.OPPORTUNITY_EVENTS_DEFINITIONS[EventType.RIVAL_STASH_LEAKED]
        self.mock_ui_manager.active_blocking_event_data = {
            "event_type_id": EventType.RIVAL_STASH_LEAKED.value,
            "title": event_def["name"],
            "messages": [event_def["description_template"].format(drug_name="TestCoke", quantity=10)],
            "choices": event_def["choices"],
            "is_opportunity_event": True,
            "runtime_params": {"drug_name": DrugName.COKE, "quantity": 10, "region_name": RegionName.DOWNTOWN.value}
        }
        
        # Force outcome 0 (give_drugs)
        with patch('random.random', return_value=0.1): # Chance for outcome 0 is 0.6
            with patch('random.randint', return_value=15) as mock_randint: # Quantity stolen
                action_resolve_opportunity_event_choice(choice_index=0) # Attempt to steal

        self.mock_player_inventory.add_drug.assert_called_once_with(DrugName.COKE, DrugQuality.STANDARD, 15)
        self.assertIsNone(self.mock_ui_manager.active_blocking_event_data) # Event should be cleared
        self.assertEqual(self.mock_ui_manager.current_view, "main_menu")

    def test_resolve_urgent_delivery_success(self):
        from src.ui_pygame.app import action_resolve_opportunity_event_choice
        
        event_def = narco_configs.OPPORTUNITY_EVENTS_DEFINITIONS[EventType.URGENT_DELIVERY]
        runtime_params = {
            "drug_name": DrugName.WEED, 
            "quality": DrugQuality.STANDARD,
            "quantity": 5, 
            "target_region_name": RegionName.DOCKS,
            "reward_per_unit": 10.0,
            "total_base_value": 250.0 # 5 * 50 (example base price)
        }
        self.mock_ui_manager.active_blocking_event_data = {
            "event_type_id": EventType.URGENT_DELIVERY.value,
            "title": event_def["name"],
            "messages": [event_def["description_template"].format(**runtime_params)],
            "choices": event_def["choices"],
            "is_opportunity_event": True,
            "runtime_params": runtime_params
        }
        self.mock_player_inventory.get_quantity = Mock(return_value=10) # Player has enough
        initial_cash = self.mock_player_inventory.cash

        action_resolve_opportunity_event_choice(choice_index=0) # Accept delivery

        self.mock_player_inventory.remove_drug.assert_called_once_with(DrugName.WEED, DrugQuality.STANDARD, 5)
        expected_cash_gain = 5 * 10.0 # quantity * reward_per_unit (premium)
        self.assertAlmostEqual(self.mock_player_inventory.cash, initial_cash + expected_cash_gain)


if __name__ == '__main__':
    unittest.main()
[end of tests/mechanics/test_opportunity_events.py]
