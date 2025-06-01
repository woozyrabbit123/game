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
        self.mock_game_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT = 0.10
        # For heat tests:
        self.mock_game_configs.HEAT_FROM_SELLING_DRUG_TIER = {1: 1, 2: 2, 3: 4, 4: 8} # Example tiers
        # Need to ensure PLAYER_MARKET_IMPACT_UNITS_BASE and PLAYER_MARKET_IMPACT_FACTOR_PER_10_UNITS are on mock_game_configs if not using game_configs directly
        self.mock_game_configs.PLAYER_MARKET_IMPACT_UNITS_BASE = 10
        self.mock_game_configs.PLAYER_MARKET_IMPACT_FACTOR_PER_10_UNITS = 0.02
        self.mock_game_configs.PLAYER_SELL_IMPACT_MODIFIER_FLOOR = 0.75


        self.region.modify_heat = MagicMock() # Mock the method on the instance

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

    def test_apply_player_sell_impact_heat_generation_base(self):
        quantity_sold = 20 # Sells 20 units
        # Drug tier is 3 (from setUp), heat per unit for tier 3 is 4. Expected heat = 20 * 4 = 80.
        expected_heat = 80

        apply_player_sell_impact(self.player_inv, self.region, self.drug_name, quantity_sold, self.mock_game_configs)

        self.region.modify_heat.assert_called_once_with(expected_heat)

    def test_apply_player_sell_impact_heat_generation_with_compartmentalization(self):
        self.player_inv.unlocked_skills.add(SkillID.COMPARTMENTALIZATION.value)
        quantity_sold = 20 # Sells 20 units
        # Drug tier 3, heat per unit 4. Base heat = 20 * 4 = 80.
        # Reduction: 0.10 (COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT from setUp mock)
        # Expected heat = 80 * (1 - 0.10) = 80 * 0.9 = 72.
        expected_heat = 72

        apply_player_sell_impact(self.player_inv, self.region, self.drug_name, quantity_sold, self.mock_game_configs)

        self.region.modify_heat.assert_called_once_with(expected_heat)

    def test_apply_player_sell_impact_heat_generation_zero_if_config_missing(self):
        # Test that if HEAT_FROM_SELLING_DRUG_TIER is missing, no heat is generated (or default logic applies)
        # For this, we use a fresh mock_game_configs that doesn't have HEAT_FROM_SELLING_DRUG_TIER
        minimal_mock_game_configs = MagicMock()
        minimal_mock_game_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT = 0.10
        minimal_mock_game_configs.PLAYER_MARKET_IMPACT_UNITS_BASE = 10
        minimal_mock_game_configs.PLAYER_MARKET_IMPACT_FACTOR_PER_10_UNITS = 0.02
        minimal_mock_game_configs.PLAYER_SELL_IMPACT_MODIFIER_FLOOR = 0.75
        # minimal_mock_game_configs.HEAT_FROM_SELLING_DRUG_TIER = {} # Explicitly empty or missing

        apply_player_sell_impact(self.player_inv, self.region, self.drug_name, 20, minimal_mock_game_configs)

        # modify_heat might be called with 0 if generated_heat is 0, or not called if check `if generated_heat > 0` prevents it.
        # Current implementation of apply_player_sell_impact has `if generated_heat > 0: region.modify_heat(...)`
        # And if HEAT_FROM_SELLING_DRUG_TIER is missing, .get(drug_tier, 1) might default to 1 if tier is not in map,
        # or if HEAT_FROM_SELLING_DRUG_TIER itself is not on game_configs_data.
        # The hasattr check in apply_player_sell_impact prevents it from running if HEAT_FROM_SELLING_DRUG_TIER is missing.
        self.region.modify_heat.assert_not_called()


# TODO: Add TestRivalMarketImpact and TestHeatDecay classes below
from src.core.ai_rival import AIRival # For TestRivalMarketImpact
from src.mechanics.market_impact import process_rival_turn # Function to test

class TestRivalMarketImpact(unittest.TestCase):
    def setUp(self):
        self.rival = AIRival(name="Test Rival", primary_drug=DrugName.SPEED, primary_region_name=RegionName.DOCKS, aggression=0.7, activity_level=0.8)
        self.region = Region(RegionName.DOCKS.value)
        self.region.drug_market_data[DrugName.SPEED] = {
            "base_buy_price": 100, "base_sell_price": 150, "tier": 2,
            "available_qualities": {DrugQuality.STANDARD: {"quantity_available": 100}},
            "player_buy_impact_modifier": 1.0, "player_sell_impact_modifier": 1.0,
            "rival_demand_modifier": 1.0, "rival_supply_modifier": 1.0,
            "last_rival_activity_turn": -1
        }

        self.all_regions_dict = {RegionName.DOCKS: self.region}

        self.mock_game_configs = MagicMock()
        # Add any game_configs attributes that process_rival_turn might use, e.g., for impact calculation
        self.mock_game_configs.RIVAL_BASE_IMPACT_MAGNITUDE = 0.05
        self.mock_game_configs.RIVAL_AGGRESSION_IMPACT_SCALE = 0.15
        self.mock_game_configs.RIVAL_DEMAND_MODIFIER_CAP = 2.0
        self.mock_game_configs.RIVAL_SUPPLY_MODIFIER_FLOOR = 0.5
        self.mock_game_configs.RIVAL_COOLDOWN_MIN_DAYS = 1 # From game_configs.py
        self.mock_game_configs.RIVAL_COOLDOWN_MAX_DAYS = 3 # From game_configs.py


    def test_process_rival_turn_busted_decrements_days(self):
        self.rival.is_busted = True
        self.rival.busted_days_remaining = 3
        process_rival_turn(self.rival, self.all_regions_dict, 10, self.mock_game_configs)
        self.assertEqual(self.rival.busted_days_remaining, 2)
        self.assertTrue(self.rival.is_busted)

    def test_process_rival_turn_busted_becomes_unbusted(self):
        self.rival.is_busted = True
        self.rival.busted_days_remaining = 1
        process_rival_turn(self.rival, self.all_regions_dict, 10, self.mock_game_configs)
        self.assertEqual(self.rival.busted_days_remaining, 0)
        self.assertFalse(self.rival.is_busted)

    @unittest.mock.patch('random.random') # Mock random.random for activity check
    def test_process_rival_turn_inactive_due_to_activity_level(self, mock_random_random):
        self.rival.activity_level = 0.5
        mock_random_random.return_value = 0.6 # Greater than activity_level, so inactive

        initial_demand_mod = self.region.drug_market_data[DrugName.SPEED]["rival_demand_modifier"]
        process_rival_turn(self.rival, self.all_regions_dict, 10, self.mock_game_configs)

        self.assertEqual(self.region.drug_market_data[DrugName.SPEED]["rival_demand_modifier"], initial_demand_mod) # No change

    @unittest.mock.patch('random.randint') # Mock random.randint for cooldown
    def test_process_rival_turn_inactive_due_to_cooldown(self, mock_random_randint):
        self.rival.last_action_day = 9 # Acted on day 9
        mock_random_randint.return_value = 3 # Cooldown is 3 days

        initial_demand_mod = self.region.drug_market_data[DrugName.SPEED]["rival_demand_modifier"]
        # Current turn is 10. 10 - 9 = 1. 1 < 3, so should be in cooldown.
        process_rival_turn(self.rival, self.all_regions_dict, 10, self.mock_game_configs)

        self.assertEqual(self.region.drug_market_data[DrugName.SPEED]["rival_demand_modifier"], initial_demand_mod)

    @unittest.mock.patch('random.random') # For rival action choice (buy/sell)
    def test_process_rival_turn_buying_action(self, mock_action_choice):
        self.rival.aggression = 0.8 # High aggression, likely to buy
        mock_action_choice.return_value = 0.2 # Less than aggression, so rival buys

        initial_demand_mod = self.region.drug_market_data[DrugName.SPEED]["rival_demand_modifier"]
        process_rival_turn(self.rival, self.all_regions_dict, 10, self.mock_game_configs)

        self.assertGreater(self.region.drug_market_data[DrugName.SPEED]["rival_demand_modifier"], initial_demand_mod)
        self.assertEqual(self.region.drug_market_data[DrugName.SPEED]["last_rival_activity_turn"], 10)

    @unittest.mock.patch('random.random') # For rival action choice
    def test_process_rival_turn_selling_action(self, mock_action_choice):
        self.rival.aggression = 0.2 # Low aggression, likely to sell
        mock_action_choice.return_value = 0.8 # Greater than aggression, so rival sells

        initial_supply_mod = self.region.drug_market_data[DrugName.SPEED]["rival_supply_modifier"]
        process_rival_turn(self.rival, self.all_regions_dict, 10, self.mock_game_configs)

        self.assertLess(self.region.drug_market_data[DrugName.SPEED]["rival_supply_modifier"], initial_supply_mod)
        self.assertEqual(self.region.drug_market_data[DrugName.SPEED]["last_rival_activity_turn"], 10)

from src.mechanics.market_impact import decay_regional_heat # Function to test

class TestHeatDecay(unittest.TestCase):
    def setUp(self):
        self.region = Region(RegionName.DOWNTOWN.value)
        self.player_inv = PlayerInventory()

        self.mock_game_configs = MagicMock()
        self.mock_game_configs.REGIONAL_HEAT_DECAY_PERCENTAGE = 0.05 # 5%
        self.mock_game_configs.MIN_REGIONAL_HEAT_DECAY_AMOUNT = 1
        self.mock_game_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = 0.15 # 15% boost

    def test_decay_regional_heat_basic_percentage(self):
        self.region.current_heat = 100
        decay_regional_heat(self.region, 1.0, self.player_inv, self.mock_game_configs)
        # Expected: 100 - (100 * 0.05 * 1.0) = 100 - 5 = 95
        self.assertEqual(self.region.current_heat, 95)

    def test_decay_regional_heat_minimum_decay(self):
        self.region.current_heat = 10 # 5% of 10 is 0.5, which is less than min_decay of 1
        decay_regional_heat(self.region, 1.0, self.player_inv, self.mock_game_configs)
        # Expected: 10 - 1 = 9
        self.assertEqual(self.region.current_heat, 9)

        self.region.current_heat = 1 # Min decay should still apply
        decay_regional_heat(self.region, 1.0, self.player_inv, self.mock_game_configs)
        self.assertEqual(self.region.current_heat, 0)


    def test_decay_regional_heat_with_ghost_protocol_skill(self):
        self.player_inv.unlocked_skills.add(SkillID.GHOST_PROTOCOL.value)
        self.region.current_heat = 100

        decay_regional_heat(self.region, 1.0, self.player_inv, self.mock_game_configs)
        # Base decay amount: 100 * 0.05 = 5
        # Boosted decay amount: 5 * (1 + 0.15) = 5 * 1.15 = 5.75
        # Expected heat: 100 - floor(5.75) = 100 - 5 = 95 (if int() truncates)
        # The function uses int(decay_amount), which truncates. So 5.75 becomes 5.
        # Let's recheck the function: decay_amount: int = int(region.current_heat * 0.05 * factor)
        # decay_amount = int(decay_amount * (1 + boost_percentage))
        # So, 5.0 becomes int(5.0 * 1.15) = int(5.75) = 5.
        # Then region.modify_heat(-max(1, 5)) -> heat = 100 - 5 = 95
        # This seems like the boost might not be effective if it's floored too early.
        # Let's assume the logic in decay_regional_heat is:
        # base_decay = region.current_heat * decay_percentage * factor
        # boosted_decay = base_decay * (1 + boost_percentage)
        # final_decay_amount = int(boosted_decay)
        # modify_heat(-max(min_amount, final_decay_amount))
        # If base_decay is 5.0, boosted_decay = 5.75, final_decay_amount = 5. Result 95.
        # If the intention is for boost to be more effective, calculations should maintain float longer.
        # Sticking to testing current implementation:
        self.assertEqual(self.region.current_heat, 95)

        # Test with heat where boost might make a difference past floor
        self.region.current_heat = 200
        # Base decay: 200 * 0.05 = 10
        # Boosted: 10 * 1.15 = 11.5
        # Final amount: int(11.5) = 11
        # Expected: 200 - 11 = 189
        decay_regional_heat(self.region, 1.0, self.player_inv, self.mock_game_configs)
        self.assertEqual(self.region.current_heat, 189)


    def test_decay_regional_heat_not_below_zero(self):
        self.region.current_heat = 5
        decay_regional_heat(self.region, 1.0, self.player_inv, self.mock_game_configs) # Min decay is 1, so 5-1=4
        self.assertEqual(self.region.current_heat, 4)

        self.region.current_heat = 0
        decay_regional_heat(self.region, 1.0, self.player_inv, self.mock_game_configs) # Already 0
        self.assertEqual(self.region.current_heat, 0)

        self.region.current_heat = 1 # Min decay will take it to 0
        decay_regional_heat(self.region, 1.0, self.player_inv, self.mock_game_configs)
        self.assertEqual(self.region.current_heat, 0)

    def test_decay_regional_heat_with_factor(self):
        self.region.current_heat = 100
        decay_regional_heat(self.region, 2.0, self.player_inv, self.mock_game_configs) # Double decay factor
        # Expected: 100 - int(100 * 0.05 * 2.0) = 100 - 10 = 90
        self.assertEqual(self.region.current_heat, 90)

if __name__ == '__main__':
    unittest.main()
