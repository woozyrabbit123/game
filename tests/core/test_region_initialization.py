import unittest
from src.game_state import initialize_regions, all_regions, current_player_region, current_day, initialize_global_state
from src.core.enums import RegionName
from src.core.region import Region # Required for type hinting if any, and for all_regions value types
from src import game_configs # To allow initialize_global_state to run

class TestRegionInitialization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Minimal setup to allow initialize_regions to run if it depends on global state
        # If initialize_global_state is needed, call it.
        # For now, assume initialize_regions can be called directly or after a minimal setup.
        # game_state.initialize_game_state() # If it sets up necessary globals
        initialize_regions()

    def test_all_regions_created(self):
        self.assertEqual(len(all_regions), 9)

    def test_region_names_are_keys(self):
        for region_enum_member in RegionName:
            self.assertIn(region_enum_member, all_regions)
            self.assertIsInstance(all_regions[region_enum_member], Region)

    def test_new_regions_market_data_initialized(self):
        new_region_enums = [
            RegionName.UNIVERSITY_HILLS,
            RegionName.RIVERSIDE,
            RegionName.AIRPORT_DISTRICT,
            RegionName.OLD_TOWN
        ]
        for region_enum in new_region_enums:
            self.assertTrue(all_regions[region_enum].drug_market_data,
                            f"Drug market data for {region_enum.value} should be initialized.")

if __name__ == '__main__':
    unittest.main()
