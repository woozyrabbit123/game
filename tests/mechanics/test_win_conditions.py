import unittest
from unittest.mock import Mock, patch

from src.core.enums import SkillID, ContactID, RegionName, CryptoCoin, DrugName, DrugQuality
from src.core.player_inventory import PlayerInventory
from src.game_state import GameState
from src.core.region import Region # Needed for GameState.all_regions
from src import narco_configs # To access config constants and modify for tests
# Import the functions to be tested
from src.mechanics.win_conditions import (
    _calculate_net_worth,
    check_target_net_worth,
    check_cartel_crown,
    check_digital_empire,
    check_perfect_retirement
)

class TestCalculateNetWorth(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_game_state = Mock(spec=GameState)

        # Mock narco_configs for base drug prices if needed by _calculate_net_worth's strategy
        # For now, _calculate_net_worth uses a simplified approach with direct base prices
        # or finds them from REGION_DEFINITIONS.
        # We will mock REGION_DEFINITIONS for consistent drug pricing in tests.
        self.original_region_definitions = narco_configs.REGION_DEFINITIONS
        narco_configs.REGION_DEFINITIONS = [
            (RegionName.DOWNTOWN, RegionName.DOWNTOWN.value, [
                (DrugName.COKE.value, 1000, 1500, 3, {DrugQuality.STANDARD: (10,20)}), # base_price = 1000
                (DrugName.WEED.value, 50, 80, 1, {DrugQuality.STANDARD: (10,20)}),   # base_price = 50
            ])
        ]


    def tearDown(self):
        narco_configs.REGION_DEFINITIONS = self.original_region_definitions


    def test_net_worth_calculation_basic(self):
        self.mock_player_inventory.cash = 10000.0
        self.mock_player_inventory.crypto_wallet = {CryptoCoin.BITCOIN: 2.0, CryptoCoin.ETHEREUM: 10.0}
        self.mock_player_inventory.staked_drug_coin = {'staked_amount': 100.0, 'pending_rewards': 5.0}
        self.mock_player_inventory.items = {
            DrugName.COKE: {DrugQuality.STANDARD: 5}, # 5 * 1000 = 5000
            DrugName.WEED: {DrugQuality.PURE: 10}      # 10 * 50 = 500 (assuming pure uses base for simplicity here)
        }
        
        self.mock_game_state.current_crypto_prices = {
            CryptoCoin.BITCOIN: 20000.0, # 2 * 20000 = 40000
            CryptoCoin.ETHEREUM: 1000.0, # 10 * 1000 = 10000
            CryptoCoin.DRUG_COIN: 10.0     # (100+5) * 10 = 1050
        }
        # Total: 10000 (cash) + 40000 + 10000 + 1050 (crypto) + 5000 + 500 (drugs) = 66550
        expected_net_worth = 10000 + 40000 + 10000 + 1050 + 5000 + 500
        
        net_worth = _calculate_net_worth(self.mock_player_inventory, self.mock_game_state)
        self.assertAlmostEqual(net_worth, expected_net_worth)

    def test_net_worth_no_assets(self):
        self.mock_player_inventory.cash = 100.0
        self.mock_player_inventory.crypto_wallet = {}
        self.mock_player_inventory.staked_drug_coin = {}
        self.mock_player_inventory.items = {}
        self.mock_game_state.current_crypto_prices = {}
        
        net_worth = _calculate_net_worth(self.mock_player_inventory, self.mock_game_state)
        self.assertAlmostEqual(net_worth, 100.0)


class TestWinConditions(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_game_state = Mock(spec=GameState)
        self.mock_game_configs = Mock() # Will set specific thresholds per test

        # Common mocks for player inventory
        self.mock_player_inventory.unlocked_skills = set()
        self.mock_player_inventory.has_secure_phone = False
        self.mock_player_inventory.debt_payment_1_paid = False
        self.mock_player_inventory.debt_payment_2_paid = False
        self.mock_player_inventory.debt_payment_3_paid = False
        self.mock_player_inventory.contact_trusts = {ContactID.INFORMANT: 50}
        
        # Common mocks for game state
        self.mock_game_state.all_regions = {
            RegionName.DOWNTOWN: Mock(current_heat=10),
            RegionName.DOCKS: Mock(current_heat=20)
        }
        # Mock _calculate_net_worth to control its return value for win condition checks
        # This simplifies testing each win condition independently of net worth calculation details
        self.patcher_net_worth = patch('src.mechanics.win_conditions._calculate_net_worth')
        self.mock_calculate_net_worth = self.patcher_net_worth.start()


    def tearDown(self):
        self.patcher_net_worth.stop()

    def test_check_target_net_worth(self):
        self.mock_game_configs.TARGET_NET_WORTH_AMOUNT = 1000000.0
        
        self.mock_calculate_net_worth.return_value = 1000000.0
        self.assertTrue(check_target_net_worth(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))
        
        self.mock_calculate_net_worth.return_value = 999999.0
        self.assertFalse(check_target_net_worth(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))

    def test_check_cartel_crown(self):
        self.mock_game_configs.CARTEL_CROWN_NET_WORTH_AMOUNT = 5000000.0
        
        # Scenario 1: Meets all conditions
        self.mock_calculate_net_worth.return_value = 5000000.0
        self.mock_player_inventory.unlocked_skills = {SkillID.MASTER_NEGOTIATOR.value}
        self.assertTrue(check_cartel_crown(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))
        
        # Scenario 2: Net worth too low
        self.mock_calculate_net_worth.return_value = 4999999.0
        self.assertFalse(check_cartel_crown(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))
        
        # Scenario 3: Missing skill
        self.mock_calculate_net_worth.return_value = 5000000.0
        self.mock_player_inventory.unlocked_skills = set() # Missing MASTER_NEGOTIATOR
        self.assertFalse(check_cartel_crown(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))

    def test_check_digital_empire(self):
        self.mock_game_configs.DIGITAL_EMPIRE_CRYPTO_VALUE = 2000000.0
        # Mock _calculate_crypto_portfolio_value used by check_digital_empire
        with patch('src.mechanics.win_conditions._calculate_crypto_portfolio_value') as mock_calc_crypto:
            # Scenario 1: Meets all conditions
            mock_calc_crypto.return_value = 2000000.0
            self.mock_player_inventory.unlocked_skills = {SkillID.GHOST_PROTOCOL.value, SkillID.DIGITAL_FOOTPRINT.value}
            self.mock_player_inventory.has_secure_phone = True
            self.assertTrue(check_digital_empire(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))

            # Scenario 2: Crypto value too low
            mock_calc_crypto.return_value = 1999999.0
            self.assertFalse(check_digital_empire(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))

            # Scenario 3: Missing Ghost Protocol
            mock_calc_crypto.return_value = 2000000.0
            self.mock_player_inventory.unlocked_skills = {SkillID.DIGITAL_FOOTPRINT.value} # Missing Ghost
            self.assertFalse(check_digital_empire(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))
            
            # Scenario 4: Missing Secure Phone
            self.mock_player_inventory.unlocked_skills = {SkillID.GHOST_PROTOCOL.value, SkillID.DIGITAL_FOOTPRINT.value}
            self.mock_player_inventory.has_secure_phone = False
            self.assertFalse(check_digital_empire(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))


    def test_check_perfect_retirement(self):
        self.mock_game_configs.PERFECT_RETIREMENT_NET_WORTH_AMOUNT = 500000.0
        self.mock_game_configs.PERFECT_RETIREMENT_MAX_AVG_HEAT = 10
        self.mock_game_configs.PERFECT_RETIREMENT_MIN_INFORMANT_TRUST = 90

        # Scenario 1: Meets all conditions
        self.mock_calculate_net_worth.return_value = 500000.0
        self.mock_player_inventory.debt_payment_1_paid = True
        self.mock_player_inventory.debt_payment_2_paid = True
        self.mock_player_inventory.debt_payment_3_paid = True
        self.mock_game_state.all_regions = {RegionName.DOWNTOWN: Mock(current_heat=5), RegionName.DOCKS: Mock(current_heat=5)} # Avg heat = 5
        self.mock_player_inventory.contact_trusts = {ContactID.INFORMANT: 90}
        self.assertTrue(check_perfect_retirement(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))

        # Scenario 2: Debt not paid
        self.mock_player_inventory.debt_payment_3_paid = False
        self.assertFalse(check_perfect_retirement(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))
        self.mock_player_inventory.debt_payment_3_paid = True # Reset

        # Scenario 3: Average heat too high
        self.mock_game_state.all_regions[RegionName.DOCKS].current_heat = 30 # Avg heat = (5+30)/2 = 17.5
        self.assertFalse(check_perfect_retirement(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))
        self.mock_game_state.all_regions[RegionName.DOCKS].current_heat = 5 # Reset

        # Scenario 4: Informant trust too low
        self.mock_player_inventory.contact_trusts[ContactID.INFORMANT] = 89
        self.assertFalse(check_perfect_retirement(self.mock_player_inventory, self.mock_game_state, self.mock_game_configs))


if __name__ == '__main__':
    unittest.main()
[end of tests/mechanics/test_win_conditions.py]
