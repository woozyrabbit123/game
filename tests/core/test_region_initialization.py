import unittest
from src.game_state import GameState  # Import GameState class
from src.core.enums import RegionName
from src.core.region import Region
# from src import game_configs # game_configs is imported by GameState

class TestRegionInitialization(unittest.TestCase):
    game_state_instance: GameState

    @classmethod
    def setUpClass(cls):
        """Set up a GameState instance for use in tests."""
        cls.game_state_instance = GameState()

    def test_all_regions_created(self):
        """Test that the correct number of regions are created."""
        self.assertEqual(len(self.game_state_instance.all_regions), 9)

    def test_region_names_are_keys(self):
        """Test that all RegionName enum members are keys in all_regions and are Region objects."""
        for region_enum_member in RegionName:
            self.assertIn(region_enum_member, self.game_state_instance.all_regions)
            self.assertIsInstance(self.game_state_instance.all_regions[region_enum_member], Region)

    def test_new_regions_market_data_initialized(self):
        """Test that newly added regions have their drug market data initialized."""
        new_region_enums = [
            RegionName.UNIVERSITY_HILLS,
            RegionName.RIVERSIDE,
            RegionName.AIRPORT_DISTRICT,
            RegionName.OLD_TOWN
        ]
        for region_enum in new_region_enums:
            region_obj = self.game_state_instance.all_regions.get(region_enum)
            self.assertIsNotNone(region_obj, f"Region {region_enum.value} should exist.")
            self.assertTrue(region_obj.drug_market_data, # type: ignore
                            f"Drug market data for {region_enum.value} should be initialized and not empty.")

if __name__ == '__main__':
    unittest.main()
