import unittest
from unittest.mock import Mock, patch

from src.core.enums import RegionName # Assuming RegionName is used in some event data
from src.game_state import GameState
# Import the seasonal event manager functions
from src.mechanics.seasonal_events_manager import (
    start_seasonal_event,
    end_seasonal_event,
    check_and_update_seasonal_events
)
# Directly import narco_configs to be patched or used as a base for mock_game_configs
from src import narco_configs 

class TestSeasonalEventsManager(unittest.TestCase):

    def setUp(self):
        self.mock_game_state = Mock(spec=GameState)
        self.mock_game_state.current_day = 1
        self.mock_game_state.current_seasonal_event = None
        self.mock_game_state.seasonal_event_effects_active = {}
        self.mock_game_state.seasonal_event_name_map = {} # For storing friendly names

        self.mock_game_configs = Mock()
        # Define a sample SEASONAL_EVENTS structure for testing
        self.mock_game_configs.SEASONAL_EVENTS = {
            "SPRING_CLEANING": {
                "name": "Spring Cleaning",
                "start_day": 5,
                "end_day": 10,
                "message_on_start": "Spring Cleaning starts!",
                "message_on_end": "Spring Cleaning ends.",
                "effects": {"heat_modifier": -0.1}
            },
            "SUMMER_HEAT": {
                "name": "Summer Heat",
                "start_day": 11, # Starts right after spring cleaning for one test case
                "end_day": 15,
                "message_on_start": "Summer Heat is on!",
                "effects": {"price_multiplier": 1.1}
            }
        }

    def test_start_seasonal_event(self):
        event_id = "SPRING_CLEANING"
        event_data = self.mock_game_configs.SEASONAL_EVENTS[event_id]
        
        message = start_seasonal_event(self.mock_game_state, event_id, event_data)
        
        self.assertEqual(self.mock_game_state.current_seasonal_event, event_id)
        self.assertEqual(self.mock_game_state.seasonal_event_effects_active, event_data["effects"])
        self.assertEqual(message, event_data["message_on_start"])

    def test_end_seasonal_event(self):
        event_id = "SPRING_CLEANING"
        event_data = self.mock_game_configs.SEASONAL_EVENTS[event_id]
        
        # Simulate event was active
        self.mock_game_state.current_seasonal_event = event_id
        self.mock_game_state.seasonal_event_effects_active = event_data["effects"]
        self.mock_game_state.seasonal_event_name_map[event_id] = event_data["name"]


        message = end_seasonal_event(self.mock_game_state, event_id, event_data)
        
        self.assertIsNone(self.mock_game_state.current_seasonal_event)
        self.assertEqual(self.mock_game_state.seasonal_event_effects_active, {})
        self.assertEqual(message, event_data["message_on_end"])

    def test_check_and_update_no_event_to_start_or_end(self):
        self.mock_game_state.current_day = 1 # No event scheduled
        message = check_and_update_seasonal_events(self.mock_game_state, self.mock_game_configs)
        self.assertIsNone(message)
        self.assertIsNone(self.mock_game_state.current_seasonal_event)

    def test_check_and_update_event_starts(self):
        self.mock_game_state.current_day = 5 # Spring Cleaning start day
        
        message = check_and_update_seasonal_events(self.mock_game_state, self.mock_game_configs)
        
        self.assertEqual(message, self.mock_game_configs.SEASONAL_EVENTS["SPRING_CLEANING"]["message_on_start"])
        self.assertEqual(self.mock_game_state.current_seasonal_event, "SPRING_CLEANING")
        self.assertEqual(self.mock_game_state.seasonal_event_effects_active, self.mock_game_configs.SEASONAL_EVENTS["SPRING_CLEANING"]["effects"])

    def test_check_and_update_event_continues(self):
        self.mock_game_state.current_day = 7
        # Manually set an event as active
        event_id = "SPRING_CLEANING"
        event_data = self.mock_game_configs.SEASONAL_EVENTS[event_id]
        self.mock_game_state.current_seasonal_event = event_id
        self.mock_game_state.seasonal_event_effects_active = event_data["effects"]
        
        message = check_and_update_seasonal_events(self.mock_game_state, self.mock_game_configs)
        
        self.assertIsNone(message) # No start/end message as event continues
        self.assertEqual(self.mock_game_state.current_seasonal_event, "SPRING_CLEANING") # Still active

    def test_check_and_update_event_ends(self):
        self.mock_game_state.current_day = 11 # Day after Spring Cleaning ends
        # Manually set an event as active
        event_id = "SPRING_CLEANING"
        event_data = self.mock_game_configs.SEASONAL_EVENTS[event_id]
        self.mock_game_state.current_seasonal_event = event_id
        self.mock_game_state.seasonal_event_effects_active = event_data["effects"]
        self.mock_game_state.seasonal_event_name_map[event_id] = event_data["name"]

        message = check_and_update_seasonal_events(self.mock_game_state, self.mock_game_configs)
        
        self.assertEqual(message, event_data["message_on_end"])
        self.assertIsNone(self.mock_game_state.current_seasonal_event)
        self.assertEqual(self.mock_game_state.seasonal_event_effects_active, {})

    def test_check_and_update_event_ends_and_new_one_starts(self):
        self.mock_game_state.current_day = 11 
        # Spring Cleaning was active
        event_id_ended = "SPRING_CLEANING"
        event_data_ended = self.mock_game_configs.SEASONAL_EVENTS[event_id_ended]
        self.mock_game_state.current_seasonal_event = event_id_ended
        self.mock_game_state.seasonal_event_effects_active = event_data_ended["effects"]
        self.mock_game_state.seasonal_event_name_map[event_id_ended] = event_data_ended["name"]
        
        # Summer Heat starts on day 11
        event_id_starts = "SUMMER_HEAT"
        event_data_starts = self.mock_game_configs.SEASONAL_EVENTS[event_id_starts]

        # The manager should first process the end, then the start.
        # The current implementation returns only one message. If an event ends and another
        # starts on the same day, the start message of the new event will be returned.
        message = check_and_update_seasonal_events(self.mock_game_state, self.mock_game_configs)
        
        self.assertEqual(message, event_data_starts["message_on_start"])
        self.assertEqual(self.mock_game_state.current_seasonal_event, event_id_starts)
        self.assertEqual(self.mock_game_state.seasonal_event_effects_active, event_data_starts["effects"])


if __name__ == '__main__':
    unittest.main()
[end of tests/mechanics/test_seasonal_events_manager.py]
