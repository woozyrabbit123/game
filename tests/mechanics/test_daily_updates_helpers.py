import unittest
from unittest.mock import Mock, patch

from src.core.player_inventory import PlayerInventory
from src.game_state import GameState
from src.mechanics.daily_updates import _handle_debt_payments # Import the specific helper
# Assuming narco_configs is where DEBT_PAYMENT_X_AMOUNT and _DUE_DAY are
from src import narco_configs 

class TestHandleDebtPayments(unittest.TestCase):

    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_game_state = Mock(spec=GameState)
        
        # Mock game_configs directly for debt amounts and due days
        # We are testing the helper function's logic, not narco_configs itself
        self.mock_game_configs = Mock()
        self.mock_game_configs.DEBT_PAYMENT_1_AMOUNT = 25000.0
        self.mock_game_configs.DEBT_PAYMENT_1_DUE_DAY = 15
        self.mock_game_configs.DEBT_PAYMENT_2_AMOUNT = 30000.0
        self.mock_game_configs.DEBT_PAYMENT_2_DUE_DAY = 30
        self.mock_game_configs.DEBT_PAYMENT_3_AMOUNT = 20000.0
        self.mock_game_configs.DEBT_PAYMENT_3_DUE_DAY = 45

    def test_no_debt_due_yet(self):
        self.mock_game_state.current_day = 10
        self.mock_player_inventory.debt_payment_1_paid = False
        self.mock_player_inventory.cash = 50000.0

        game_over_msg, ui_msgs, log_msgs = _handle_debt_payments(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        self.assertIsNone(game_over_msg)
        self.assertEqual(len(ui_msgs), 0)
        self.assertFalse(self.mock_player_inventory.debt_payment_1_paid)

    def test_debt_1_due_enough_cash(self):
        self.mock_game_state.current_day = 15
        self.mock_player_inventory.debt_payment_1_paid = False
        self.mock_player_inventory.cash = 30000.0
        initial_cash = self.mock_player_inventory.cash

        game_over_msg, ui_msgs, log_msgs = _handle_debt_payments(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        self.assertIsNone(game_over_msg)
        self.assertTrue("Debt Payment 1 made!" in ui_msgs)
        self.assertTrue(self.mock_player_inventory.debt_payment_1_paid)
        self.assertEqual(self.mock_player_inventory.cash, initial_cash - self.mock_game_configs.DEBT_PAYMENT_1_AMOUNT)

    def test_debt_1_due_not_enough_cash(self):
        self.mock_game_state.current_day = 15
        self.mock_player_inventory.debt_payment_1_paid = False
        self.mock_player_inventory.cash = 10000.0

        game_over_msg, ui_msgs, log_msgs = _handle_debt_payments(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        self.assertIsNotNone(game_over_msg)
        self.assertTrue("GAME OVER: Failed Debt Payment 1!" in game_over_msg)
        self.assertFalse(self.mock_player_inventory.debt_payment_1_paid)

    def test_debt_2_due_after_debt_1_paid_enough_cash(self):
        self.mock_game_state.current_day = 30
        self.mock_player_inventory.debt_payment_1_paid = True # Debt 1 already paid
        self.mock_player_inventory.debt_payment_2_paid = False
        self.mock_player_inventory.cash = 40000.0
        initial_cash = self.mock_player_inventory.cash

        game_over_msg, ui_msgs, log_msgs = _handle_debt_payments(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        self.assertIsNone(game_over_msg)
        self.assertTrue("Debt Payment 2 made!" in ui_msgs)
        self.assertTrue(self.mock_player_inventory.debt_payment_2_paid)
        self.assertEqual(self.mock_player_inventory.cash, initial_cash - self.mock_game_configs.DEBT_PAYMENT_2_AMOUNT)

    def test_debt_3_due_all_paid_game_not_over(self): # Actually, paying final debt is a win condition, not game over
        self.mock_game_state.current_day = 45
        self.mock_player_inventory.debt_payment_1_paid = True
        self.mock_player_inventory.debt_payment_2_paid = True
        self.mock_player_inventory.debt_payment_3_paid = False
        self.mock_player_inventory.cash = 50000.0
        initial_cash = self.mock_player_inventory.cash

        game_over_msg, ui_msgs, log_msgs = _handle_debt_payments(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        self.assertIsNone(game_over_msg) # Paying final debt is not game over, it's a potential win path.
        self.assertTrue("Final debt paid! You are free!" in ui_msgs)
        self.assertTrue(self.mock_player_inventory.debt_payment_3_paid)
        self.assertEqual(self.mock_player_inventory.cash, initial_cash - self.mock_game_configs.DEBT_PAYMENT_3_AMOUNT)
    
    def test_debt_payment_skipped_if_already_paid(self):
        self.mock_game_state.current_day = 16 # Day after first payment due
        self.mock_player_inventory.debt_payment_1_paid = True # Already paid
        self.mock_player_inventory.cash = 5000.0 # Not enough for first payment, but shouldn't matter
        initial_cash = self.mock_player_inventory.cash

        game_over_msg, ui_msgs, log_msgs = _handle_debt_payments(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        self.assertIsNone(game_over_msg)
        self.assertEqual(len(ui_msgs), 0) # No new payment messages
        self.assertEqual(self.mock_player_inventory.cash, initial_cash) # Cash unchanged


class TestProcessStakingRewards(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_player_inventory.staked_drug_coin = {'staked_amount': 0.0, 'pending_rewards': 0.0}
        
        self.mock_game_configs = Mock()
        self.mock_game_configs.DC_STAKING_DAILY_RETURN_PERCENT = 0.001 # 0.1%

    def test_staking_rewards_accrue(self):
        from src.mechanics.daily_updates import _process_staking_rewards
        self.mock_player_inventory.staked_drug_coin['staked_amount'] = 1000.0
        self.mock_player_inventory.staked_drug_coin['pending_rewards'] = 0.5
        
        ui_msgs = _process_staking_rewards(self.mock_player_inventory, self.mock_game_configs)
        
        expected_reward = 1000.0 * 0.001 # 1.0
        self.assertAlmostEqual(self.mock_player_inventory.staked_drug_coin['pending_rewards'], 0.5 + expected_reward)
        self.assertTrue(any(f"Accrued {expected_reward:.4f} DC rewards" in msg for msg in ui_msgs))

    def test_no_staked_amount_no_rewards(self):
        from src.mechanics.daily_updates import _process_staking_rewards
        self.mock_player_inventory.staked_drug_coin['staked_amount'] = 0.0
        self.mock_player_inventory.staked_drug_coin['pending_rewards'] = 0.0

        ui_msgs = _process_staking_rewards(self.mock_player_inventory, self.mock_game_configs)
        
        self.assertEqual(self.mock_player_inventory.staked_drug_coin['pending_rewards'], 0.0)
        self.assertEqual(len(ui_msgs), 0)

    def test_staking_config_missing_no_rewards(self):
        from src.mechanics.daily_updates import _process_staking_rewards
        self.mock_player_inventory.staked_drug_coin['staked_amount'] = 1000.0
        del self.mock_game_configs.DC_STAKING_DAILY_RETURN_PERCENT # Simulate missing config

        ui_msgs = _process_staking_rewards(self.mock_player_inventory, self.mock_game_configs)
        
        self.assertEqual(self.mock_player_inventory.staked_drug_coin['pending_rewards'], 0.0) # Rewards should not change
        self.assertEqual(len(ui_msgs), 0)


class TestProcessLaunderingArrival(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_player_inventory.pending_laundered_sc = 0.0
        self.mock_player_inventory.pending_laundered_sc_arrival_day = None
        # Mock add_crypto method for PlayerInventory
        self.mock_player_inventory.add_crypto = Mock()

        self.mock_game_state = Mock(spec=GameState)
        self.mock_game_state.current_day = 10

    def test_laundering_arrival_correct_day(self):
        from src.mechanics.daily_updates import _process_laundering_arrival
        from src.core.enums import CryptoCoin # Import for STABLE_COIN reference

        self.mock_player_inventory.pending_laundered_sc = 5000.0
        self.mock_player_inventory.pending_laundered_sc_arrival_day = 10
        
        ui_msgs, log_msgs, processed, new_sc, new_day = _process_laundering_arrival(
            self.mock_game_state, self.mock_player_inventory
        )
        
        self.assertTrue(processed)
        self.mock_player_inventory.add_crypto.assert_called_once_with(CryptoCoin.STABLE_COIN, 5000.0)
        self.assertEqual(new_sc, 0.0)
        self.assertIsNone(new_day)
        self.assertTrue(any("5000.00 SC (laundered) arrived" in msg for msg in ui_msgs))

    def test_laundering_not_due_yet(self):
        from src.mechanics.daily_updates import _process_laundering_arrival
        self.mock_player_inventory.pending_laundered_sc = 5000.0
        self.mock_player_inventory.pending_laundered_sc_arrival_day = 12
        
        ui_msgs, log_msgs, processed, new_sc, new_day = _process_laundering_arrival(
            self.mock_game_state, self.mock_player_inventory
        )
        
        self.assertFalse(processed)
        self.mock_player_inventory.add_crypto.assert_not_called()
        self.assertEqual(new_sc, 5000.0) # Should remain unchanged
        self.assertEqual(new_day, 12)    # Should remain unchanged
        self.assertEqual(len(ui_msgs), 0)

    def test_no_pending_laundering(self):
        from src.mechanics.daily_updates import _process_laundering_arrival
        self.mock_player_inventory.pending_laundered_sc = 0.0
        self.mock_player_inventory.pending_laundered_sc_arrival_day = None
        
        ui_msgs, log_msgs, processed, new_sc, new_day = _process_laundering_arrival(
            self.mock_game_state, self.mock_player_inventory
        )
        
        self.assertFalse(processed)
        self.mock_player_inventory.add_crypto.assert_not_called()
        self.assertEqual(new_sc, 0.0)
        self.assertIsNone(new_day)
        self.assertEqual(len(ui_msgs), 0)

    def test_laundering_arrival_day_passed(self):
        from src.mechanics.daily_updates import _process_laundering_arrival
        from src.core.enums import CryptoCoin

        self.mock_player_inventory.pending_laundered_sc = 3000.0
        self.mock_player_inventory.pending_laundered_sc_arrival_day = 8 # Arrived 2 days ago
        
        ui_msgs, log_msgs, processed, new_sc, new_day = _process_laundering_arrival(
            self.mock_game_state, self.mock_player_inventory
        )
        
        self.assertTrue(processed)
        self.mock_player_inventory.add_crypto.assert_called_once_with(CryptoCoin.STABLE_COIN, 3000.0)
        self.assertEqual(new_sc, 0.0)
        self.assertIsNone(new_day)
        self.assertTrue(any("3000.00 SC (laundered) arrived" in msg for msg in ui_msgs))


class TestAwardSkillPoints(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_player_inventory.skill_points = 0
        
        self.mock_game_state = Mock(spec=GameState)
        
        self.mock_game_configs = Mock()
        self.mock_game_configs.SKILL_POINTS_PER_X_DAYS = 7

    def test_skill_point_awarded_on_correct_day(self):
        from src.mechanics.daily_updates import _award_skill_points
        self.mock_game_state.current_day = 7
        initial_skill_points = self.mock_player_inventory.skill_points

        ui_msgs, log_msgs, total_skill_pts = _award_skill_points(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        
        self.assertEqual(self.mock_player_inventory.skill_points, initial_skill_points + 1)
        self.assertEqual(total_skill_pts, initial_skill_points + 1)
        self.assertTrue(any("+1 Skill Point" in msg for msg in ui_msgs))

    def test_skill_point_not_awarded_on_incorrect_day(self):
        from src.mechanics.daily_updates import _award_skill_points
        self.mock_game_state.current_day = 6
        initial_skill_points = self.mock_player_inventory.skill_points

        ui_msgs, log_msgs, total_skill_pts = _award_skill_points(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        
        self.assertEqual(self.mock_player_inventory.skill_points, initial_skill_points)
        self.assertEqual(total_skill_pts, initial_skill_points)
        self.assertEqual(len(ui_msgs), 0)

    def test_skill_point_awarded_on_multiples_of_interval(self):
        from src.mechanics.daily_updates import _award_skill_points
        self.mock_game_state.current_day = 14
        initial_skill_points = self.mock_player_inventory.skill_points

        ui_msgs, log_msgs, total_skill_pts = _award_skill_points(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        
        self.assertEqual(self.mock_player_inventory.skill_points, initial_skill_points + 1)
        self.assertEqual(total_skill_pts, initial_skill_points + 1)

    def test_skill_point_not_awarded_on_day_zero(self): # Day 0 is not a multiple
        from src.mechanics.daily_updates import _award_skill_points
        self.mock_game_state.current_day = 0
        initial_skill_points = self.mock_player_inventory.skill_points

        ui_msgs, log_msgs, total_skill_pts = _award_skill_points(
            self.mock_game_state, self.mock_player_inventory, self.mock_game_configs
        )
        
        self.assertEqual(self.mock_player_inventory.skill_points, initial_skill_points)
        self.assertEqual(len(ui_msgs), 0)


class TestCheckForBankruptcy(unittest.TestCase):
    def setUp(self):
        self.mock_player_inventory = Mock(spec=PlayerInventory)
        self.mock_game_configs = Mock()
        self.mock_game_configs.BANKRUPTCY_THRESHOLD = -1000

    def test_bankruptcy_triggered_when_cash_below_threshold(self):
        from src.mechanics.daily_updates import _check_for_bankruptcy
        self.mock_player_inventory.cash = -1001.0
        
        game_over_msg, log_msgs = _check_for_bankruptcy(self.mock_player_inventory, self.mock_game_configs)
        
        self.assertIsNotNone(game_over_msg)
        self.assertTrue("GAME OVER: You have gone bankrupt!" in game_over_msg)
        self.assertTrue(any(f"Cash: ${self.mock_player_inventory.cash:.2f}" in msg for msg in log_msgs))

    def test_no_bankruptcy_when_cash_at_threshold(self):
        from src.mechanics.daily_updates import _check_for_bankruptcy
        self.mock_player_inventory.cash = -1000.0
        
        game_over_msg, log_msgs = _check_for_bankruptcy(self.mock_player_inventory, self.mock_game_configs)
        
        self.assertIsNone(game_over_msg)
        self.assertEqual(len(log_msgs), 0)

    def test_no_bankruptcy_when_cash_above_threshold(self):
        from src.mechanics.daily_updates import _check_for_bankruptcy
        self.mock_player_inventory.cash = 500.0
        
        game_over_msg, log_msgs = _check_for_bankruptcy(self.mock_player_inventory, self.mock_game_configs)
        
        self.assertIsNone(game_over_msg)
        self.assertEqual(len(log_msgs), 0)


if __name__ == '__main__':
    unittest.main()
[end of tests/mechanics/test_daily_updates_helpers.py]
