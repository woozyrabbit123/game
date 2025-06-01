import unittest
from unittest.mock import MagicMock

from src.mechanics.market_impact import apply_player_buy_impact, apply_player_sell_impact, decay_player_market_impact
from src.core.region import Region
from src.core.player_inventory import PlayerInventory
from src.core.enums import RegionName, DrugName, DrugQuality, SkillID
from src import game_configs # For direct access to constants if needed for setup or reference

class TestPlayerMarketImpact(unittest.TestCase):
    def setUp(self):
        self.player_inv = PlayerInventory()
        self.region = Region(RegionName.DOWNTOWN.value)

        self.drug_name = DrugName.COKE
        # Initialize market data for the drug in the region
        # Making sure to include player_buy_impact_modifier and player_sell_impact_modifier
        self.region.drug_market_data[self.drug_name] = {
            "base_buy_price": 1000,
            "base_sell_price": 1500,
            "tier": 3,
            "available_qualities": {
                DrugQuality.STANDARD: {"quantity_available": 100, "previous_buy_price": 1000, "previous_sell_price": 1500}
            },
            "player_buy_impact_modifier": 1.0,
            "player_sell_impact_modifier": 1.0,
            "rival_demand_modifier": 1.0,
            "rival_supply_modifier": 1.0,
            "market_active_since_turn": 0,
            "last_rival_activity_turn": -1
        }

        # Mock game_configs_data to be passed to apply_player_sell_impact
        self.mock_game_configs = MagicMock()
        self.mock_game_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT = 0.10 # Example value from game_configs

    def test_apply_player_buy_impact(self):
        initial_modifier = self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"]
        self.assertAlmostEqual(initial_modifier, 1.0)

        apply_player_buy_impact(self.region, self.drug_name, 50) # 50 units bought
        # Expected impact: (50/10) * 0.02 = 5 * 0.02 = 0.10
        # New modifier: 1.0 + 0.10 = 1.10
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"], 1.10)

        # Test cap at 1.25
        apply_player_buy_impact(self.region, self.drug_name, 200) # Large quantity (200/10)*0.02 = 0.4
        # Current is 1.10, 1.10 + 0.4 = 1.50, should be capped at 1.25
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"], 1.25)

        # Buy more, should remain capped
        apply_player_buy_impact(self.region, self.drug_name, 100)
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"], 1.25)


    def test_apply_player_sell_impact_no_skill(self):
        initial_modifier = self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"]
        self.assertAlmostEqual(initial_modifier, 1.0)

        apply_player_sell_impact(self.player_inv, self.region, self.drug_name, 50, self.mock_game_configs)
        # Expected impact: (50/10) * 0.02 = 0.10
        # New modifier: 1.0 - 0.10 = 0.90
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"], 0.90)

        # Test floor at 0.75
        apply_player_sell_impact(self.player_inv, self.region, self.drug_name, 200, self.mock_game_configs) # Large quantity
        # Current is 0.90. Impact: (200/10)*0.02 = 0.4. 0.90 - 0.4 = 0.50. Should be floored at 0.75
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"], 0.75)

        # Sell more, should remain floored
        apply_player_sell_impact(self.player_inv, self.region, self.drug_name, 100, self.mock_game_configs)
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"], 0.75)

    def test_apply_player_sell_impact_with_compartmentalization(self):
        self.player_inv.unlocked_skills.add(SkillID.COMPARTMENTALIZATION.value)
        initial_modifier = self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"] # Should be 1.0

        apply_player_sell_impact(self.player_inv, self.region, self.drug_name, 50, self.mock_game_configs)
        # Base impact_factor: (50/10) * 0.02 = 0.10
        # Reduced impact_factor: 0.10 * (1 - 0.10) = 0.10 * 0.9 = 0.09
        # New modifier: 1.0 - 0.09 = 0.91
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"], 0.91)

    def test_decay_player_market_impact(self):
        # Set modifiers away from 1.0
        self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"] = 1.15
        self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"] = 0.85

        decay_player_market_impact(self.region)
        # Expected buy: 1.15 - 0.01 = 1.14
        # Expected sell: 0.85 + 0.01 = 0.86
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"], 1.14)
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"], 0.86)

        # Test decay to 1.0 (boundary)
        self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"] = 1.005 # very close
        self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"] = 0.995 # very close
        decay_player_market_impact(self.region)
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"], 1.0) # max(1.0, 1.005 - 0.01) -> max(1.0, 0.995) -> 1.0
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"], 1.0) # min(1.0, 0.995 + 0.01) -> min(1.0, 1.005) -> 1.0

        # Test decay when already at 1.0 (should not change)
        self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"] = 1.0
        self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"] = 1.0
        decay_player_market_impact(self.region)
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_buy_impact_modifier"], 1.0)
        self.assertAlmostEqual(self.region.drug_market_data[self.drug_name]["player_sell_impact_modifier"], 1.0)

if __name__ == '__main__':
    unittest.main()
