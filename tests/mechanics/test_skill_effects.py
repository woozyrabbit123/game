import unittest
from unittest.mock import Mock, patch

# Assuming enums and classes are accessible for type hinting and instantiation
from src.core.enums import SkillID, DrugName, DrugQuality, RegionName, ContactID
from src.core.player_inventory import PlayerInventory
from src.core.region import Region
from src.game_state import GameState
# Import narco_configs directly to access its attributes like SKILL_DEFINITIONS
from src import narco_configs

class TestStreetSmartsSkillEffects(unittest.TestCase):

    def setUp(self):
        # Mock GameState
        self.mock_game_state = Mock(spec=GameState)
        self.mock_game_state.current_crypto_prices = {} # Mock crypto prices if needed for net worth
        self.mock_game_state.active_seasonal_event_effects_active = {} # No seasonal effects by default
        self.mock_game_state.active_turf_wars = {} # No turf wars by default

        # Mock PlayerInventory
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_player_inventory.unlocked_skills = set()

        # Mock Region
        self.mock_region = Mock(spec=Region)
        self.mock_region.name = RegionName.DOWNTOWN # Example region
        self.mock_region.drug_market_data = {
            DrugName.COKE: {
                'base_buy_price': 1000.0,
                'base_sell_price': 1200.0, # Assuming sell is higher for simplicity here
                'tier': 3,
                'player_buy_impact_modifier': 1.0,
                'player_sell_impact_modifier': 1.0,
                'rival_demand_modifier': 1.0,
                'rival_supply_modifier': 1.0,
                'available_qualities': {
                    DrugQuality.STANDARD: {
                        'quantity_available': 100,
                        'previous_buy_price': 1000.0,
                        'previous_sell_price': 1200.0,
                    }
                }
            }
        }
        # Mock the methods that get_buy_price/get_sell_price depend on
        self.mock_region._get_heat_price_multiplier = Mock(return_value=1.0) # No heat effect
        
        # Mock Drug class behavior within Region methods if necessary, or simplify Region's methods
        # For now, assuming temp_drug.get_quality_multiplier returns 1.0 for standard quality
        # This might need adjustment if Drug class is complex.
        # The Region class creates a temp Drug object. We can mock that if needed.
        # Or, ensure the mocked region.drug_market_data has enough info.

        # Mock narco_configs (specifically SKILL_DEFINITIONS for effect_value)
        # We are testing the *application* of the effect, so the values are important.
        self.original_skill_definitions = narco_configs.SKILL_DEFINITIONS
        narco_configs.SKILL_DEFINITIONS = {
            SkillID.ADVANCED_MARKET_ANALYSIS: {
                "name": "Advanced Market Analysis", "cost": 2, "tier": 2, "category": "Street Smarts",
                "description": "Improves buy/sell prices by 2.5%.",
                "effect_value": 0.025, # 2.5%
                "prerequisites": [SkillID.MARKET_INTUITION]
            },
            SkillID.MASTER_NEGOTIATOR: {
                "name": "Master Negotiator", "cost": 3, "tier": 3, "category": "Street Smarts",
                "description": "Significantly improves buy/sell prices by 5%.",
                "effect_value": 0.05, # 5%
                "prerequisites": [SkillID.ADVANCED_MARKET_ANALYSIS]
            },
             SkillID.MARKET_INTUITION: { # Prereq
                "name": "Market Intuition", "cost": 1, "tier": 1, "category": "Street Smarts",
                "description": "Shows trends.", "prerequisites": []
            }
        }
        # Mock temp Drug object's get_quality_multiplier if it's complex
        # For simplicity, assuming standard quality has a multiplier of 1.0
        # and region.py's internal Drug instantiation will work with mocked data.

    def tearDown(self):
        # Restore original narco_configs
        narco_configs.SKILL_DEFINITIONS = self.original_skill_definitions

    def test_advanced_market_analysis_buy_price(self):
        self.mock_player_inventory.unlocked_skills = {SkillID.ADVANCED_MARKET_ANALYSIS.value}
        
        # Act
        # The get_buy_price now takes player_inventory and game_state
        price = self.mock_region.get_buy_price(DrugName.COKE, DrugQuality.STANDARD, self.mock_player_inventory, self.mock_game_state)
        
        # Assert
        expected_price = 1000.0 * (1.0 - 0.025) # 2.5% discount
        self.assertAlmostEqual(price, expected_price, places=2)

    def test_advanced_market_analysis_sell_price(self):
        self.mock_player_inventory.unlocked_skills = {SkillID.ADVANCED_MARKET_ANALYSIS.value}
        price = self.mock_region.get_sell_price(DrugName.COKE, DrugQuality.STANDARD, self.mock_player_inventory, self.mock_game_state)
        expected_price = 1200.0 * (1.0 + 0.025) # 2.5% bonus
        self.assertAlmostEqual(price, expected_price, places=2)

    def test_master_negotiator_buy_price(self):
        # Assumes Master Negotiator effects stack with or include Advanced Market Analysis due to prerequisites
        self.mock_player_inventory.unlocked_skills = {
            SkillID.MARKET_INTUITION.value, # Prereq for AMA
            SkillID.ADVANCED_MARKET_ANALYSIS.value, # Prereq for MN
            SkillID.MASTER_NEGOTIATOR.value
        }
        price = self.mock_region.get_buy_price(DrugName.COKE, DrugQuality.STANDARD, self.mock_player_inventory, self.mock_game_state)
        # Effects are additive in current region.py implementation: 0.025 + 0.05 = 0.075
        expected_price = 1000.0 * (1.0 - (0.025 + 0.05)) 
        self.assertAlmostEqual(price, expected_price, places=2)

    def test_master_negotiator_sell_price(self):
        self.mock_player_inventory.unlocked_skills = {
            SkillID.MARKET_INTUITION.value,
            SkillID.ADVANCED_MARKET_ANALYSIS.value,
            SkillID.MASTER_NEGOTIATOR.value
        }
        price = self.mock_region.get_sell_price(DrugName.COKE, DrugQuality.STANDARD, self.mock_player_inventory, self.mock_game_state)
        expected_price = 1200.0 * (1.0 + (0.025 + 0.05))
        self.assertAlmostEqual(price, expected_price, places=2)

    def test_no_street_smarts_skills_buy_price(self):
        self.mock_player_inventory.unlocked_skills = set() # No relevant skills
        price = self.mock_region.get_buy_price(DrugName.COKE, DrugQuality.STANDARD, self.mock_player_inventory, self.mock_game_state)
        self.assertAlmostEqual(price, 1000.0, places=2)

    def test_no_street_smarts_skills_sell_price(self):
        self.mock_player_inventory.unlocked_skills = set()
        price = self.mock_region.get_sell_price(DrugName.COKE, DrugQuality.STANDARD, self.mock_player_inventory, self.mock_game_state)
        self.assertAlmostEqual(price, 1200.0, places=2)


class TestNetworkSkillEffects(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_player_inventory.unlocked_skills = set()
        self.mock_player_inventory.cash = 1000.0
        self.mock_player_inventory.contact_trusts = {ContactID.INFORMANT: 50, ContactID.CORRUPT_OFFICIAL: 20}

        self.mock_game_state = Mock(spec=GameState)
        self.mock_game_state.current_day = 1
        self.mock_game_state.ai_rivals = [] # No rivals for these tests
        # Mock current region for corrupt official bribe
        self.mock_current_region = Mock(spec=Region)
        self.mock_current_region.name = RegionName.DOWNTOWN
        self.mock_current_region.current_heat = 50
        self.mock_game_state.get_current_player_region = Mock(return_value=self.mock_current_region)


        # Store original and then mock narco_configs for skill definitions and costs
        self.original_skill_definitions = narco_configs.SKILL_DEFINITIONS
        self.original_informant_tip_cost_rumor = narco_configs.INFORMANT_TIP_COST_RUMOR
        self.original_informant_trust_gain = narco_configs.INFORMANT_TRUST_GAIN_PER_TIP
        self.original_corrupt_official_base_bribe_cost = narco_configs.CORRUPT_OFFICIAL_BASE_BRIBE_COST
        self.original_corrupt_official_bribe_cost_per_heat = narco_configs.CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT
        self.original_corrupt_official_heat_reduction = narco_configs.CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT


        narco_configs.SKILL_DEFINITIONS = {
            SkillID.BASIC_CONNECTIONS: {"effect_value": narco_configs.BASIC_CONNECTIONS_TRUST_GAIN_BONUS}, # Actual value from configs
            SkillID.EXPANDED_NETWORK: {"effect_value": narco_configs.EXPANDED_NETWORK_TIP_COST_REDUCTION},
            SkillID.SYNDICATE_INFLUENCE: {"effect_value": narco_configs.SYNDICATE_INFLUENCE_FREE_BRIBE_CHANCE},
        }
        narco_configs.INFORMANT_TIP_COST_RUMOR = 50.0
        narco_configs.INFORMANT_TRUST_GAIN_PER_TIP = 5
        narco_configs.CORRUPT_OFFICIAL_BASE_BRIBE_COST = 1000.0
        narco_configs.CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT = 10.0
        narco_configs.CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT = 20


        # Patch app.py's global caches directly for action functions to use
        # This is a bit of a workaround for testing app.py functions directly
        self.app_patchers = {
            'player_inventory_cache': patch('src.ui_pygame.app.player_inventory_cache', self.mock_player_inventory),
            'game_state_data_cache': patch('src.ui_pygame.app.game_state_data_cache', self.mock_game_state),
            'game_configs_data_cache': patch('src.ui_pygame.app.game_configs_data_cache', narco_configs), # Use our mocked narco_configs
            'ui_manager': patch('src.ui_pygame.app.ui_manager', Mock()) # Mock ui_manager to avoid UI side effects
        }
        for p in self.app_patchers.values():
            p.start()

    def tearDown(self):
        narco_configs.SKILL_DEFINITIONS = self.original_skill_definitions
        narco_configs.INFORMANT_TIP_COST_RUMOR = self.original_informant_tip_cost_rumor
        narco_configs.INFORMANT_TRUST_GAIN_PER_TIP = self.original_informant_trust_gain
        narco_configs.CORRUPT_OFFICIAL_BASE_BRIBE_COST = self.original_corrupt_official_base_bribe_cost
        narco_configs.CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT = self.original_corrupt_official_bribe_cost_per_heat
        narco_configs.CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT = self.original_corrupt_official_heat_reduction

        for p in self.app_patchers.values():
            p.stop()

    def test_basic_connections_informant_trust(self):
        from src.ui_pygame.app import action_ask_informant_rumor # Import action here
        self.mock_player_inventory.unlocked_skills = {SkillID.BASIC_CONNECTIONS.value}
        initial_trust = self.mock_player_inventory.contact_trusts[ContactID.INFORMANT]
        
        action_ask_informant_rumor(self.mock_player_inventory, narco_configs, self.mock_game_state)
        
        expected_trust_gain = narco_configs.INFORMANT_TRUST_GAIN_PER_TIP + narco_configs.BASIC_CONNECTIONS_TRUST_GAIN_BONUS
        self.assertEqual(self.mock_player_inventory.contact_trusts[ContactID.INFORMANT], initial_trust + expected_trust_gain)

    def test_expanded_network_informant_cost(self):
        from src.ui_pygame.app import action_ask_informant_rumor
        self.mock_player_inventory.unlocked_skills = {SkillID.EXPANDED_NETWORK.value}
        initial_cash = self.mock_player_inventory.cash
        
        action_ask_informant_rumor(self.mock_player_inventory, narco_configs, self.mock_game_state)
        
        cost_multiplier = 1.0 - narco_configs.EXPANDED_NETWORK_TIP_COST_REDUCTION
        expected_cost = narco_configs.INFORMANT_TIP_COST_RUMOR * cost_multiplier
        self.assertAlmostEqual(self.mock_player_inventory.cash, initial_cash - expected_cost)

    @patch('random.random')
    def test_syndicate_influence_free_bribe(self, mock_random):
        from src.ui_pygame.app import action_confirm_corrupt_official_bribe # Action that applies bribe
        self.mock_player_inventory.unlocked_skills = {SkillID.SYNDICATE_INFLUENCE.value}
        initial_cash = self.mock_player_inventory.cash
        
        mock_random.return_value = 0.05 # Ensure free bribe triggers (chance is 0.15)
        action_confirm_corrupt_official_bribe(ContactID.CORRUPT_OFFICIAL, "REDUCE_HEAT")
        
        self.assertEqual(self.mock_player_inventory.cash, initial_cash) # Cash should not change

    @patch('random.random')
    def test_syndicate_influence_paid_bribe(self, mock_random):
        from src.ui_pygame.app import action_confirm_corrupt_official_bribe
        self.mock_player_inventory.unlocked_skills = {SkillID.SYNDICATE_INFLUENCE.value}
        initial_cash = self.mock_player_inventory.cash
        
        mock_random.return_value = 0.20 # Ensure free bribe does NOT trigger
        
        expected_cost = narco_configs.CORRUPT_OFFICIAL_BASE_BRIBE_COST + \
                        (self.mock_current_region.current_heat * narco_configs.CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT)
        
        action_confirm_corrupt_official_bribe(ContactID.CORRUPT_OFFICIAL, "REDUCE_HEAT")
        
        self.assertAlmostEqual(self.mock_player_inventory.cash, initial_cash - expected_cost)


class TestOpSecSkillEffects(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_player_inventory.unlocked_skills = set()

        self.mock_region = Mock(spec=Region)
        self.mock_region.current_heat = 50
        self.mock_region.drug_market_data = { # Needed for apply_player_sell_impact
            DrugName.COKE: { 'tier': 3 }
        }


        self.mock_game_state = Mock(spec=GameState) # For seasonal event check in apply_player_sell_impact
        self.mock_game_state.seasonal_event_effects_active = {}


        # Store original and then mock narco_configs
        self.original_skill_definitions = narco_configs.SKILL_DEFINITIONS
        self.original_compartmentalization_reduction = narco_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT
        self.original_ghost_protocol_boost = narco_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
        self.original_heat_from_selling_drug_tier = narco_configs.HEAT_FROM_SELLING_DRUG_TIER
        self.original_regional_heat_decay_percentage = narco_configs.REGIONAL_HEAT_DECAY_PERCENTAGE
        self.original_min_regional_heat_decay = narco_configs.MIN_REGIONAL_HEAT_DECAY_AMOUNT


        narco_configs.SKILL_DEFINITIONS = {
            SkillID.COMPARTMENTALIZATION: {"effect_value": 0.10}, # Example value, real one from configs
            SkillID.GHOST_PROTOCOL: {"effect_value": 0.15}, # Example value
        }
        # Ensure these specific config values are set for the test
        narco_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT = 0.10
        narco_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = 0.15
        narco_configs.HEAT_FROM_SELLING_DRUG_TIER = {1:1, 2:2, 3:4, 4:8}
        narco_configs.REGIONAL_HEAT_DECAY_PERCENTAGE = 0.05
        narco_configs.MIN_REGIONAL_HEAT_DECAY_AMOUNT = 1


    def tearDown(self):
        narco_configs.SKILL_DEFINITIONS = self.original_skill_definitions
        narco_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT = self.original_compartmentalization_reduction
        narco_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = self.original_ghost_protocol_boost
        narco_configs.HEAT_FROM_SELLING_DRUG_TIER = self.original_heat_from_selling_drug_tier
        narco_configs.REGIONAL_HEAT_DECAY_PERCENTAGE = self.original_regional_heat_decay_percentage
        narco_configs.MIN_REGIONAL_HEAT_DECAY_AMOUNT = self.original_min_regional_heat_decay

    def test_compartmentalization_heat_reduction(self):
        from src.mechanics.market_impact import apply_player_sell_impact
        self.mock_player_inventory.unlocked_skills = {SkillID.COMPARTMENTALIZATION.value}
        initial_heat = self.mock_region.current_heat
        quantity_sold = 10
        drug_tier = self.mock_region.drug_market_data[DrugName.COKE]['tier'] # Tier 3
        base_heat_per_unit = narco_configs.HEAT_FROM_SELLING_DRUG_TIER[drug_tier] # = 4
        
        # Expected heat without skill: 10 * 4 = 40
        # Expected heat with skill (10% reduction): 40 * 0.9 = 36
        expected_heat_increase = round(base_heat_per_unit * quantity_sold * (1.0 - narco_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT))

        apply_player_sell_impact(self.mock_player_inventory, self.mock_region, DrugName.COKE, quantity_sold, narco_configs, self.mock_game_state)
        
        # modify_heat is called on the region mock
        # We need to sum up all calls to modify_heat if it's called multiple times,
        # or ensure it's called once with the correct net amount.
        # The function apply_player_sell_impact calls region.modify_heat once with the calculated heat.
        final_heat = self.mock_region.current_heat
        self.assertEqual(final_heat, initial_heat + expected_heat_increase)


    def test_ghost_protocol_heat_decay(self):
        from src.mechanics.market_impact import decay_regional_heat
        self.mock_player_inventory.unlocked_skills = {SkillID.GHOST_PROTOCOL.value}
        self.mock_region.current_heat = 100 # Start with a high heat to see decay
        
        base_decay_amount = int(self.mock_region.current_heat * narco_configs.REGIONAL_HEAT_DECAY_PERCENTAGE) # 100 * 0.05 = 5
        boosted_decay_amount = int(base_decay_amount * (1 + narco_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT)) # 5 * 1.15 = 5.75 -> 5
        expected_decay = max(narco_configs.MIN_REGIONAL_HEAT_DECAY_AMOUNT, boosted_decay_amount) # max(1, 5) = 5

        decay_regional_heat(self.mock_region, 1.0, self.mock_player_inventory, narco_configs)
        
        self.assertEqual(self.mock_region.current_heat, 100 - expected_decay)

    def test_no_opsec_skills_sell_heat(self):
        from src.mechanics.market_impact import apply_player_sell_impact
        self.mock_player_inventory.unlocked_skills = set()
        initial_heat = self.mock_region.current_heat
        quantity_sold = 10
        drug_tier = self.mock_region.drug_market_data[DrugName.COKE]['tier']
        base_heat_per_unit = narco_configs.HEAT_FROM_SELLING_DRUG_TIER[drug_tier]
        expected_heat_increase = round(base_heat_per_unit * quantity_sold)

        apply_player_sell_impact(self.mock_player_inventory, self.mock_region, DrugName.COKE, quantity_sold, narco_configs, self.mock_game_state)
        final_heat = self.mock_region.current_heat
        self.assertEqual(final_heat, initial_heat + expected_heat_increase)

    def test_no_opsec_skills_heat_decay(self):
        from src.mechanics.market_impact import decay_regional_heat
        self.mock_player_inventory.unlocked_skills = set()
        self.mock_region.current_heat = 100
        
        base_decay_amount = int(self.mock_region.current_heat * narco_configs.REGIONAL_HEAT_DECAY_PERCENTAGE)
        expected_decay = max(narco_configs.MIN_REGIONAL_HEAT_DECAY_AMOUNT, base_decay_amount)

        decay_regional_heat(self.mock_region, 1.0, self.mock_player_inventory, narco_configs)
        self.assertEqual(self.mock_region.current_heat, 100 - expected_decay)


if __name__ == '__main__':
    unittest.main()
[end of tests/mechanics/test_skill_effects.py]
