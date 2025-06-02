# tests/core/test_player_inventory.py
import unittest
from src.core.player_inventory import PlayerInventory
from src.core.enums import DrugName, DrugQuality, CryptoCoin, SkillID # Added DrugName, CryptoCoin
# Assuming game_configs might be needed for default values if not mocking them all
from src import narco_configs as game_configs

class TestPlayerInventorySkills(unittest.TestCase): # This class remains as is
    def setUp(self):
        self.player_inv = PlayerInventory()
        # Grant some skill points for testing
        self.player_inv.skill_points = 10

        self.skill_compart_id = SkillID.COMPARTMENTALIZATION.value
        self.skill_compart_cost = 3

        self.skill_ghost_id = SkillID.GHOST_PROTOCOL.value
        self.skill_ghost_cost = 5

    def test_unlock_skill_successful(self):
        initial_sp = self.player_inv.skill_points
        unlocked = self.player_inv.unlock_skill(self.skill_compart_id, self.skill_compart_cost)

        self.assertTrue(unlocked)
        self.assertEqual(self.player_inv.skill_points, initial_sp - self.skill_compart_cost)
        self.assertIn(self.skill_compart_id, self.player_inv.unlocked_skills)

    def test_unlock_skill_insufficient_points(self):
        self.player_inv.skill_points = 2
        initial_sp = self.player_inv.skill_points

        unlocked = self.player_inv.unlock_skill(self.skill_compart_id, self.skill_compart_cost)

        self.assertFalse(unlocked)
        self.assertEqual(self.player_inv.skill_points, initial_sp)
        self.assertNotIn(self.skill_compart_id, self.player_inv.unlocked_skills)

    def test_unlock_multiple_skills(self):
        initial_sp = self.player_inv.skill_points

        unlocked1 = self.player_inv.unlock_skill(self.skill_compart_id, self.skill_compart_cost)
        self.assertTrue(unlocked1)
        self.assertEqual(self.player_inv.skill_points, initial_sp - self.skill_compart_cost)
        self.assertIn(self.skill_compart_id, self.player_inv.unlocked_skills)

        unlocked2 = self.player_inv.unlock_skill(self.skill_ghost_id, self.skill_ghost_cost)
        self.assertTrue(unlocked2)
        self.assertEqual(self.player_inv.skill_points, initial_sp - self.skill_compart_cost - self.skill_ghost_cost)
        self.assertIn(self.skill_ghost_id, self.player_inv.unlocked_skills)

    def test_unlock_skill_already_unlocked(self):
        self.player_inv.unlock_skill(self.skill_compart_id, self.skill_compart_cost)
        sp_after_first_unlock = self.player_inv.skill_points

        unlocked_again = self.player_inv.unlock_skill(self.skill_compart_id, self.skill_compart_cost)

        # Current behavior: unlock_skill does not check if already unlocked, so it will succeed and deduct points again if possible.
        if self.player_inv.skill_points >= self.skill_compart_cost: # Check if points were enough for a second unlock
             self.assertTrue(unlocked_again, "unlock_skill should return True if points are sufficient, even if skill is already unlocked.")
             self.assertEqual(self.player_inv.skill_points, sp_after_first_unlock - self.skill_compart_cost, "Skill points should be deducted again with current implementation.")
        else:
            # This case would happen if skill_points were not enough for the second unlock.
            self.assertFalse(unlocked_again, "unlock_skill should return False if points are insufficient for second unlock.")
            self.assertEqual(self.player_inv.skill_points, sp_after_first_unlock, "Skill points should not change if second unlock attempt fails due to insufficient points.")

        self.assertIn(self.skill_compart_id, self.player_inv.unlocked_skills)

        # Note for future refactoring of PlayerInventory.unlock_skill:
        # If unlock_skill were changed to prevent re-unlocking or re-deducting points for an already unlocked skill:
        # - It should ideally return False (or True for a "no-op success" but False is clearer for "action not performed").
        # - The assertEqual for skill_points would then be:
        #   self.assertEqual(self.player_inv.skill_points, sp_after_first_unlock, "Skill points should NOT change on attempting to re-unlock an already unlocked skill.")

class TestPlayerInventoryGeneral(unittest.TestCase):
    def setUp(self):
        self.initial_cash = 1000.0
        self.initial_capacity = 100
        self.player_inv = PlayerInventory(max_capacity=self.initial_capacity, starting_cash=self.initial_cash)

    def test_initialization_defaults(self):
        inv_default = PlayerInventory()
        self.assertEqual(inv_default.cash, game_configs.PLAYER_STARTING_CASH)
        self.assertEqual(inv_default.max_capacity, game_configs.PLAYER_MAX_CAPACITY)
        self.assertEqual(inv_default.current_load, 0)
        self.assertEqual(inv_default.skill_points, 0)
        self.assertEqual(inv_default.unlocked_skills, set())

        for coin in CryptoCoin:
            self.assertIn(coin, inv_default.crypto_wallet)
            self.assertEqual(inv_default.crypto_wallet[coin], 0.0)

    def test_initialization_custom(self):
        self.assertEqual(self.player_inv.cash, self.initial_cash)
        self.assertEqual(self.player_inv.max_capacity, self.initial_capacity)
        self.assertEqual(self.player_inv.current_load, 0)

    def test_add_drug_successful(self):
        added = self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 10)
        self.assertTrue(added)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), 10)
        self.assertEqual(self.player_inv.current_load, 10)

        added_again = self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 5)
        self.assertTrue(added_again)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), 15)
        self.assertEqual(self.player_inv.current_load, 15)

        added_other_drug = self.player_inv.add_drug(DrugName.WEED, DrugQuality.CUT, 20)
        self.assertTrue(added_other_drug)
        self.assertEqual(self.player_inv.get_quantity(DrugName.WEED, DrugQuality.CUT), 20)
        self.assertEqual(self.player_inv.current_load, 35)

    def test_add_drug_zero_or_negative_quantity(self):
        added_zero = self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 0)
        self.assertFalse(added_zero)
        self.assertEqual(self.player_inv.current_load, 0)

        added_negative = self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, -5)
        self.assertFalse(added_negative)
        self.assertEqual(self.player_inv.current_load, 0)

    def test_add_drug_exceed_capacity(self):
        self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, self.initial_capacity - 10)
        self.assertEqual(self.player_inv.current_load, self.initial_capacity - 10)

        added_exceed = self.player_inv.add_drug(DrugName.WEED, DrugQuality.CUT, 20)
        self.assertFalse(added_exceed)
        self.assertEqual(self.player_inv.get_quantity(DrugName.WEED, DrugQuality.CUT), 0)
        self.assertEqual(self.player_inv.current_load, self.initial_capacity - 10)

        added_exact = self.player_inv.add_drug(DrugName.HEROIN, DrugQuality.PURE, 10)
        self.assertTrue(added_exact)
        self.assertEqual(self.player_inv.current_load, self.initial_capacity)

    def test_remove_drug_successful(self):
        self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 20)
        removed = self.player_inv.remove_drug(DrugName.COKE, DrugQuality.STANDARD, 5)
        self.assertTrue(removed)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), 15)
        self.assertEqual(self.player_inv.current_load, 15)

        removed_all = self.player_inv.remove_drug(DrugName.COKE, DrugQuality.STANDARD, 15)
        self.assertTrue(removed_all)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), 0)
        self.assertNotIn(DrugName.COKE, self.player_inv.items)
        self.assertEqual(self.player_inv.current_load, 0)

    def test_remove_drug_zero_or_negative_quantity(self):
        self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 10)
        removed_zero = self.player_inv.remove_drug(DrugName.COKE, DrugQuality.STANDARD, 0)
        self.assertFalse(removed_zero)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), 10)

        removed_negative = self.player_inv.remove_drug(DrugName.COKE, DrugQuality.STANDARD, -5)
        self.assertFalse(removed_negative)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), 10)

    def test_remove_drug_not_present_or_insufficient(self):
        removed_non_existent_drug = self.player_inv.remove_drug(DrugName.SPEED, DrugQuality.STANDARD, 5)
        self.assertFalse(removed_non_existent_drug)

        self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 5)
        removed_non_existent_quality = self.player_inv.remove_drug(DrugName.COKE, DrugQuality.CUT, 2)
        self.assertFalse(removed_non_existent_quality)

        removed_too_many = self.player_inv.remove_drug(DrugName.COKE, DrugQuality.STANDARD, 10)
        self.assertFalse(removed_too_many)
        self.assertEqual(self.player_inv.get_quantity(DrugName.COKE, DrugQuality.STANDARD), 5)

    def test_get_drug_item_and_quantity(self):
        self.assertIsNone(self.player_inv.get_drug_item(DrugName.WEED, DrugQuality.STANDARD))
        self.assertEqual(self.player_inv.get_quantity(DrugName.WEED, DrugQuality.STANDARD), 0)

        self.player_inv.add_drug(DrugName.WEED, DrugQuality.STANDARD, 25)
        item = self.player_inv.get_drug_item(DrugName.WEED, DrugQuality.STANDARD)
        self.assertIsNotNone(item)
        self.assertEqual(item['drug_name'], DrugName.WEED)
        self.assertEqual(item['quality'], DrugQuality.STANDARD)
        self.assertEqual(item['quantity'], 25)
        self.assertEqual(self.player_inv.get_quantity(DrugName.WEED, DrugQuality.STANDARD), 25)
        self.assertEqual(self.player_inv.get_drug_quantity(DrugName.WEED, DrugQuality.STANDARD), 25)

    def test_add_crypto_successful(self):
        self.player_inv.add_crypto(CryptoCoin.BITCOIN, 1.5)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.BITCOIN], 1.5)

        self.player_inv.add_crypto(CryptoCoin.BITCOIN, 0.5)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.BITCOIN], 2.0)

    def test_add_crypto_zero_or_negative_amount(self):
        self.player_inv.add_crypto(CryptoCoin.ETHEREUM, 0)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.ETHEREUM], 0.0)

        self.player_inv.add_crypto(CryptoCoin.ETHEREUM, -0.5)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.ETHEREUM], 0.0)

    def test_remove_crypto_successful(self):
        self.player_inv.add_crypto(CryptoCoin.MONERO, 5.0)
        removed = self.player_inv.remove_crypto(CryptoCoin.MONERO, 2.0)
        self.assertTrue(removed)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.MONERO], 3.0)

        removed_all = self.player_inv.remove_crypto(CryptoCoin.MONERO, 3.0)
        self.assertTrue(removed_all)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.MONERO], 0.0)

    def test_remove_crypto_zero_or_negative_amount(self):
        self.player_inv.add_crypto(CryptoCoin.ZCASH, 1.0)
        removed_zero = self.player_inv.remove_crypto(CryptoCoin.ZCASH, 0)
        self.assertFalse(removed_zero)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.ZCASH], 1.0)

        removed_negative = self.player_inv.remove_crypto(CryptoCoin.ZCASH, -0.5)
        self.assertFalse(removed_negative)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.ZCASH], 1.0)

    def test_remove_crypto_insufficient_or_not_present(self):
        removed_non_existent = self.player_inv.remove_crypto(CryptoCoin.DRUG_COIN, 0.1)
        self.assertFalse(removed_non_existent)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.DRUG_COIN], 0.0)

        self.player_inv.add_crypto(CryptoCoin.BITCOIN, 0.5)
        removed_too_much = self.player_inv.remove_crypto(CryptoCoin.BITCOIN, 1.0)
        self.assertFalse(removed_too_much)
        self.assertEqual(self.player_inv.crypto_wallet[CryptoCoin.BITCOIN], 0.5)

    def test_get_available_space(self):
        self.assertEqual(self.player_inv.get_available_space(), self.initial_capacity)
        self.player_inv.add_drug(DrugName.COKE, DrugQuality.STANDARD, 10)
        self.assertEqual(self.player_inv.get_available_space(), self.initial_capacity - 10)

    def test_recalculate_current_load(self):
        self.player_inv.items = {
            DrugName.COKE: {DrugQuality.STANDARD: 10, DrugQuality.PURE: 5},
            DrugName.WEED: {DrugQuality.CUT: 20}
        }
        self.player_inv._recalculate_current_load()
        self.assertEqual(self.player_inv.current_load, 35)

    def test_get_inventory_summary_returns_items_dict(self):
        self.player_inv.add_drug(DrugName.SPEED, DrugQuality.PURE, 7)
        summary_dict = self.player_inv.get_inventory_summary()
        self.assertEqual(summary_dict, self.player_inv.items)
        self.assertIn(DrugName.SPEED, summary_dict)
        self.assertIn(DrugQuality.PURE, summary_dict[DrugName.SPEED])
        self.assertEqual(summary_dict[DrugName.SPEED][DrugQuality.PURE], 7)

    def test_formatted_summary_runs(self):
        self.player_inv.add_drug(DrugName.HEROIN, DrugQuality.CUT, 12)
        self.player_inv.add_crypto(CryptoCoin.BITCOIN, 2.3456)
        self.player_inv.skill_points = 5
        self.player_inv.heat = 50
        summary_str = ""
        try:
            summary_str = self.player_inv.formatted_summary()
        except Exception as e:
            self.fail(f"formatted_summary() raised an exception: {e}")

        self.assertIsInstance(summary_str, str)
        self.assertTrue(len(summary_str) > 0)
        self.assertIn(f"Cash: ${self.player_inv.cash:,.2f}", summary_str)
        self.assertIn(f"Load: {self.player_inv.current_load}/{self.player_inv.max_capacity}", summary_str)
        self.assertIn("Heroin (CUT): 12", summary_str)
        self.assertIn("Bitcoin: 2.3456", summary_str)
        self.assertIn("Skill Points: 5", summary_str)
        self.assertIn("Heat: 50", summary_str)

class TestPlayerInventoryTransactions(unittest.TestCase):
    def setUp(self):
        self.initial_cash = 200.0
        self.initial_capacity = 50
        self.player_inv = PlayerInventory(max_capacity=self.initial_capacity, starting_cash=self.initial_cash)
        self.drug_coke = DrugName.COKE
        self.quality_standard = DrugQuality.STANDARD

    def test_process_buy_drug_successful(self):
        drug_price = 10.0
        quantity_to_buy = 5
        cost = drug_price * quantity_to_buy

        can_buy = self.player_inv.process_buy_drug(self.drug_coke, self.quality_standard, quantity_to_buy, cost)

        self.assertTrue(can_buy)
        self.assertEqual(self.player_inv.cash, self.initial_cash - cost)
        self.assertEqual(self.player_inv.get_quantity(self.drug_coke, self.quality_standard), quantity_to_buy)
        self.assertEqual(self.player_inv.current_load, quantity_to_buy)

    def test_process_buy_drug_fail_insufficient_cash(self):
        drug_price = 50.0
        quantity_to_buy = 5 # Total cost 250
        cost = drug_price * quantity_to_buy

        can_buy = self.player_inv.process_buy_drug(self.drug_coke, self.quality_standard, quantity_to_buy, cost)

        self.assertFalse(can_buy)
        self.assertEqual(self.player_inv.cash, self.initial_cash) # Cash unchanged
        self.assertEqual(self.player_inv.get_quantity(self.drug_coke, self.quality_standard), 0) # Drug not added
        self.assertEqual(self.player_inv.current_load, 0) # Load unchanged

    def test_process_buy_drug_fail_insufficient_space(self):
        drug_price = 1.0
        quantity_to_buy = self.initial_capacity + 10 # Exceeds capacity
        cost = drug_price * quantity_to_buy

        can_buy = self.player_inv.process_buy_drug(self.drug_coke, self.quality_standard, quantity_to_buy, cost)

        self.assertFalse(can_buy)
        self.assertEqual(self.player_inv.cash, self.initial_cash) # Cash unchanged
        self.assertEqual(self.player_inv.get_quantity(self.drug_coke, self.quality_standard), 0) # Drug not added
        self.assertEqual(self.player_inv.current_load, 0) # Load unchanged

    def test_process_sell_drug_successful(self):
        # First, add some drugs to sell
        initial_quantity = 10
        add_cost = 0 # Not relevant for sell test, but add_drug needs cost if process_buy_drug was used
        self.player_inv.add_drug(self.drug_coke, self.quality_standard, initial_quantity)
        # Manually set cash if add_drug doesn't handle it or if it's simpler for setup
        self.player_inv.cash = self.initial_cash # Reset cash after adding drug for consistent test state

        drug_price = 15.0
        quantity_to_sell = 5
        revenue = drug_price * quantity_to_sell

        can_sell = self.player_inv.process_sell_drug(self.drug_coke, self.quality_standard, quantity_to_sell, revenue)

        self.assertTrue(can_sell)
        self.assertEqual(self.player_inv.cash, self.initial_cash + revenue)
        self.assertEqual(self.player_inv.get_quantity(self.drug_coke, self.quality_standard), initial_quantity - quantity_to_sell)
        self.assertEqual(self.player_inv.current_load, initial_quantity - quantity_to_sell)

    def test_process_sell_drug_fail_insufficient_quantity(self):
        # Player has no drugs initially
        drug_price = 15.0
        quantity_to_sell = 5
        revenue = drug_price * quantity_to_sell

        can_sell = self.player_inv.process_sell_drug(self.drug_coke, self.quality_standard, quantity_to_sell, revenue)

        self.assertFalse(can_sell)
        self.assertEqual(self.player_inv.cash, self.initial_cash) # Cash unchanged
        self.assertEqual(self.player_inv.get_quantity(self.drug_coke, self.quality_standard), 0) # No drugs
        self.assertEqual(self.player_inv.current_load, 0) # Load unchanged

if __name__ == '__main__':
    unittest.main()
