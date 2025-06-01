import unittest
from unittest.mock import patch, MagicMock

# Adjust imports based on actual project structure
import src.ui_pygame.state # Ensure the module is loaded for patching
from src.ui_pygame.actions import action_travel_to_region, action_confirm_transaction, action_confirm_tech_operation # Ensure all are imported
from src.core.player_inventory import PlayerInventory
from src.core.enums import SkillID, CryptoCoin # Added CryptoCoin
from src.core.region import Region
import math # Added for skill effect calculations
from src.core.enums import RegionName, DrugName, DrugQuality # Assuming DrugName, DrugQuality might be needed by PlayerInventory or Region indirectly
from src import game_configs # For TRAVEL_COST_CASH

class MockGameState:
    def __init__(self, current_region, day=1):
        self.current_player_region = current_region
        self.current_day = day
        self.difficulty_level = 1
        self.current_crypto_prices = {}
        self.ai_rivals = []
        self.all_regions = {}

class TestPygameActions(unittest.TestCase):

    def setUp(self):
        self.source_region = Region(RegionName.DOWNTOWN.value)
        self.dest_region = Region(RegionName.SUBURBS.value)

        self.patch_show_event_message = patch('src.ui_pygame.ui_hud.show_event_message')
        self.patch_setup_buttons = patch('src.ui_pygame.setup_ui.setup_buttons')
        self.patch_check_police_stop = patch('src.mechanics.event_manager.check_and_trigger_police_stop', return_value=False)
        self.patch_update_crypto = patch('src.game_state.update_daily_crypto_prices')
        self.patch_update_events = patch('src.mechanics.event_manager.update_active_events')
        self.patch_add_message_to_log = patch('src.ui_pygame.actions.add_message_to_log')

        self.mock_show_event_message = self.patch_show_event_message.start()
        self.mock_setup_buttons = self.patch_setup_buttons.start()
        self.mock_check_police_stop = self.patch_check_police_stop.start()
        self.mock_update_crypto = self.patch_update_crypto.start()
        self.mock_update_events = self.patch_update_events.start()
        self.mock_add_message_to_log = self.patch_add_message_to_log.start()

    def tearDown(self):
        self.patch_show_event_message.stop()
        self.patch_setup_buttons.stop()
        self.patch_check_police_stop.stop()
        self.patch_update_crypto.stop()
        self.patch_update_events.stop()
        self.patch_add_message_to_log.stop()

    def _setup_mock_ui_state_for_tech_ops(self, mock_ui_state):
        mock_ui_state.game_configs_data_cache = MagicMock()
        mock_ui_state.game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION = 2
        mock_ui_state.game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT = 0.25
        mock_ui_state.game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT = 0.25
        mock_ui_state.game_configs_data_cache.LAUNDERING_DELAY_DAYS = 3
        mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES = {
            'CRYPTO_TRADE': {'fee_buy_sell': 0.02},
            'LAUNDER_CASH': {'fee': 0.05}
        }
        mock_ui_state.game_configs_data_cache.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT = game_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT
        mock_ui_state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT = game_configs.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
        mock_ui_state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY = game_configs.BASE_DAILY_HEAT_DECAY
        mock_ui_state.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER = game_configs.HEAT_FROM_SELLING_DRUG_TIER
        mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH = game_configs.TRAVEL_COST_CASH
        mock_ui_state.game_configs_data_cache.CRYPTO_VOLATILITY = game_configs.CRYPTO_VOLATILITY
        mock_ui_state.game_configs_data_cache.CRYPTO_MIN_PRICE = game_configs.CRYPTO_MIN_PRICE

        mock_region_for_heat = Region(RegionName.DOWNTOWN.value)
        mock_region_for_heat.current_heat = 0
        mock_ui_state.game_state_data_cache = MockGameState(mock_region_for_heat)
        mock_ui_state.game_state_data_cache.current_crypto_prices = {
            CryptoCoin.BITCOIN: 1000.0, CryptoCoin.ETHEREUM: 100.0,
            CryptoCoin.DRUG_COIN: 10.0, CryptoCoin.MONERO: 50.0, CryptoCoin.ZCASH: 20.0
        }
        mock_ui_state.game_state_data_cache.current_day = 1
        mock_ui_state.player_inventory_cache = PlayerInventory()

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_travel_successful(self, mock_ui_state):
        initial_cash = 100
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.game_state_data_cache.current_player_region = self.source_region
        mock_ui_state.campaign_day = 1
        mock_ui_state.phase_thresholds = [45, 70, 100, 120]
        mock_ui_state.campaign_phase = 1
        mock_ui_state.current_view = "travel"
        action_travel_to_region(self.dest_region, mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache)
        travel_cost = mock_ui_state.game_configs_data_cache.TRAVEL_COST_CASH
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash - travel_cost)
        self.assertEqual(mock_ui_state.game_state_data_cache.current_player_region, self.dest_region)
        self.assertEqual(mock_ui_state.campaign_day, 2)
        self.mock_show_event_message.assert_called_with(f"Traveled from {self.source_region.name.value} to {self.dest_region.name.value}.")
        self.mock_check_police_stop.assert_called_once()
        self.mock_update_crypto.assert_called_once()
        self.mock_update_events.assert_called_once()
        self.assertEqual(mock_ui_state.current_view, "market")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_travel_insufficient_cash(self, mock_ui_state):
        initial_cash = 20
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.game_state_data_cache.current_player_region = self.source_region
        mock_ui_state.campaign_day = 1
        original_day = mock_ui_state.campaign_day
        action_travel_to_region(self.dest_region, mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache)
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, initial_cash)
        self.assertEqual(mock_ui_state.game_state_data_cache.current_player_region, self.source_region)
        self.assertEqual(mock_ui_state.campaign_day, original_day)
        self.mock_show_event_message.assert_called_with("Not enough cash to travel.")
        self.mock_check_police_stop.assert_not_called()

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_sell_with_compartmentalization(self, mock_ui_state):
        initial_cash = 100
        drug_to_sell = DrugName.WEED
        quality_to_sell = DrugQuality.STANDARD
        quantity_sold = 10
        sell_price = 10
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = initial_cash
        mock_ui_state.player_inventory_cache.add_drug(drug_to_sell, quality_to_sell, quantity_sold)
        mock_ui_state.player_inventory_cache.unlocked_skills.add(SkillID.COMPARTMENTALIZATION.value)
        mock_region = Region(RegionName.DOWNTOWN.value)
        mock_region.drug_market_data[drug_to_sell] = {
            "tier": 1, "available_qualities": {quality_to_sell: {"quantity_available": 1000}},
            "player_sell_impact_modifier": 1.0, "player_buy_impact_modifier": 1.0
        }
        mock_ui_state.game_state_data_cache.current_player_region = mock_region
        mock_ui_state.current_transaction_type = "sell"
        mock_ui_state.drug_for_transaction = drug_to_sell
        mock_ui_state.quality_for_transaction = quality_to_sell
        mock_ui_state.price_for_transaction = sell_price
        mock_ui_state.available_for_transaction = quantity_sold
        mock_ui_state.quantity_input_string = str(quantity_sold)
        initial_region_heat = mock_region.current_heat
        action_confirm_transaction(mock_ui_state.player_inventory_cache, mock_region, mock_ui_state.game_state_data_cache)
        base_heat_generated = mock_ui_state.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER[1] * quantity_sold
        expected_heat = math.ceil(base_heat_generated * (1 - mock_ui_state.game_configs_data_cache.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT))
        self.assertEqual(mock_region.current_heat, initial_region_heat + expected_heat)

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_travel_with_ghost_protocol(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.heat = 10
        mock_ui_state.player_inventory_cache.cash = 100
        mock_ui_state.player_inventory_cache.unlocked_skills.add(SkillID.GHOST_PROTOCOL.value)
        mock_source_region = Region(RegionName.DOWNTOWN.value)
        mock_dest_region = Region(RegionName.SUBURBS.value)
        mock_ui_state.game_state_data_cache.current_player_region = mock_source_region
        mock_ui_state.game_state_data_cache.all_regions = {RegionName.SUBURBS: mock_dest_region}
        mock_ui_state.campaign_day = 1
        mock_ui_state.phase_thresholds = [45, 70, 100, 120]
        mock_ui_state.campaign_phase = 1
        initial_player_heat = mock_ui_state.player_inventory_cache.heat
        action_travel_to_region(mock_dest_region, mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache)
        base_decay = mock_ui_state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY
        boost = mock_ui_state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
        expected_decay = base_decay + math.floor(base_decay * boost)
        final_heat = max(0, initial_player_heat - expected_decay)
        self.assertEqual(mock_ui_state.player_inventory_cache.heat, final_heat)

    @patch('src.ui_pygame.actions.market_impact.apply_player_buy_impact')
    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_transaction_buy_success(self, mock_ui_state, mock_apply_buy_impact):
        player_cash = 2000
        drug_price = 100
        buy_quantity = 10
        market_stock = 50
        player_max_capacity = 50
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = player_cash
        mock_ui_state.player_inventory_cache.max_capacity = player_max_capacity
        mock_ui_state.player_inventory_cache.current_load = 0
        mock_region = Region(RegionName.DOWNTOWN.value)
        mock_region.initialize_drug_market(DrugName.COKE, 80, 120, 1, {DrugQuality.STANDARD: market_stock})
        mock_ui_state.game_state_data_cache.current_player_region = mock_region
        mock_ui_state.current_transaction_type = "buy"
        mock_ui_state.drug_for_transaction = DrugName.COKE
        mock_ui_state.quality_for_transaction = DrugQuality.STANDARD
        mock_ui_state.price_for_transaction = drug_price
        mock_ui_state.available_for_transaction = market_stock
        mock_ui_state.quantity_input_string = str(buy_quantity)
        mock_ui_state.current_view = "market_buy_input"
        action_confirm_transaction(mock_ui_state.player_inventory_cache, mock_region, mock_ui_state.game_state_data_cache)
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, player_cash - (drug_price * buy_quantity))
        self.assertEqual(mock_ui_state.player_inventory_cache.get_quantity(DrugName.COKE, DrugQuality.STANDARD), buy_quantity)
        self.assertEqual(mock_ui_state.player_inventory_cache.current_load, buy_quantity)
        mock_apply_buy_impact.assert_called_once_with(mock_region, DrugName.COKE.value, buy_quantity)
        self.mock_show_event_message.assert_called_with(f"Bought {buy_quantity} {DrugName.COKE.value} ({DrugQuality.STANDARD.name}).")
        self.assertEqual(mock_ui_state.current_view, "market")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_transaction_buy_fail_no_cash(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = 50
        mock_region = mock_ui_state.game_state_data_cache.current_player_region
        mock_ui_state.current_transaction_type = "buy"
        mock_ui_state.drug_for_transaction = DrugName.COKE
        mock_ui_state.quality_for_transaction = DrugQuality.STANDARD
        mock_ui_state.price_for_transaction = 10
        mock_ui_state.available_for_transaction = 20
        mock_ui_state.quantity_input_string = "10"
        action_confirm_transaction(mock_ui_state.player_inventory_cache, mock_region, mock_ui_state.game_state_data_cache)
        self.assertEqual(mock_ui_state.player_inventory_cache.cash, 50)
        self.assertEqual(mock_ui_state.player_inventory_cache.get_quantity(DrugName.COKE, DrugQuality.STANDARD), 0)
        self.mock_show_event_message.assert_called_with("Error: Not enough cash.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_transaction_buy_fail_no_market_stock(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = 1000 # Sufficient cash
        mock_region = mock_ui_state.game_state_data_cache.current_player_region

        mock_ui_state.current_transaction_type = "buy"
        mock_ui_state.drug_for_transaction = DrugName.COKE
        mock_ui_state.quality_for_transaction = DrugQuality.STANDARD
        mock_ui_state.price_for_transaction = 100
        mock_ui_state.available_for_transaction = 5 # Market has only 5
        mock_ui_state.quantity_input_string = "10"   # Player wants 10

        action_confirm_transaction(mock_ui_state.player_inventory_cache, mock_region, mock_ui_state.game_state_data_cache)
        self.mock_show_event_message.assert_called_with("Error: Not enough market stock.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_transaction_buy_fail_no_capacity(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = 1000
        mock_ui_state.player_inventory_cache.max_capacity = 10
        mock_ui_state.player_inventory_cache.current_load = 5 # Only 5 space left

        mock_ui_state.current_transaction_type = "buy"
        mock_ui_state.drug_for_transaction = DrugName.COKE
        mock_ui_state.quality_for_transaction = DrugQuality.STANDARD
        mock_ui_state.price_for_transaction = 10
        mock_ui_state.available_for_transaction = 20
        mock_ui_state.quantity_input_string = "6" # Wants 6, only 5 space

        action_confirm_transaction(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache.current_player_region, mock_ui_state.game_state_data_cache)
        self.mock_show_event_message.assert_called_with("Error: Not enough space.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_invalid_amount_input(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.tech_input_string = "abc"
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_any_call("Error: Invalid amount.")
        mock_ui_state.tech_input_string = "0"
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_any_call("Error: Invalid amount.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_buy_crypto_success(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        player_cash = 2000.0
        crypto_to_buy = CryptoCoin.BITCOIN
        amount_to_buy = 1.0
        mock_ui_state.player_inventory_cache.cash = player_cash
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.coin_for_tech_transaction = crypto_to_buy
        mock_ui_state.tech_input_string = str(amount_to_buy)
        crypto_price = mock_ui_state.game_state_data_cache.current_crypto_prices[crypto_to_buy]
        fee_percent = mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES['CRYPTO_TRADE']['fee_buy_sell']
        action_confirm_tech_operation(
            mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache,
            mock_ui_state.game_configs_data_cache
        )
        expected_cost = crypto_price * amount_to_buy
        expected_fee = expected_cost * fee_percent
        expected_total_deduction = expected_cost + expected_fee
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.cash, player_cash - expected_total_deduction)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(crypto_to_buy,0), amount_to_buy)
        expected_heat = mock_ui_state.game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION
        self.assertEqual(mock_ui_state.game_state_data_cache.current_player_region.current_heat, expected_heat)
        self.mock_show_event_message.assert_called_once()

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_buy_crypto_fail_no_cash(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = 10
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.BITCOIN
        mock_ui_state.tech_input_string = "1.0"
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_called_with("Error: Not enough cash.")
        self.assertEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(CryptoCoin.BITCOIN, 0), 0)

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_buy_crypto_fail_price_unavailable(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.cash = 2000
        mock_ui_state.game_state_data_cache.current_crypto_prices[CryptoCoin.ETHEREUM] = 0
        mock_ui_state.tech_transaction_in_progress = "buy_crypto"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.ETHEREUM
        mock_ui_state.tech_input_string = "1.0"
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_called_with("Error: Price unavailable.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_sell_crypto_success(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        player_initial_cash = 100.0
        crypto_to_sell = CryptoCoin.ETHEREUM
        amount_to_sell = 2.0
        initial_crypto_amount = 5.0
        mock_ui_state.player_inventory_cache.cash = player_initial_cash
        mock_ui_state.player_inventory_cache.add_crypto(crypto_to_sell, initial_crypto_amount)
        mock_ui_state.player_inventory_cache.unlocked_skills.add(SkillID.DIGITAL_FOOTPRINT.value)
        mock_ui_state.player_inventory_cache.has_secure_phone = True
        mock_ui_state.tech_transaction_in_progress = "sell_crypto"
        mock_ui_state.coin_for_tech_transaction = crypto_to_sell
        mock_ui_state.tech_input_string = str(amount_to_sell)
        mock_region = mock_ui_state.game_state_data_cache.current_player_region
        initial_region_heat = mock_region.current_heat
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        crypto_price = mock_ui_state.game_state_data_cache.current_crypto_prices[crypto_to_sell]
        fee_percent = mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES['CRYPTO_TRADE']['fee_buy_sell']
        expected_revenue = crypto_price * amount_to_sell
        expected_fee = expected_revenue * fee_percent
        expected_cash_gain = expected_revenue - expected_fee
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.cash, player_initial_cash + expected_cash_gain)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(crypto_to_sell,0), initial_crypto_amount - amount_to_sell)
        base_heat = mock_ui_state.game_configs_data_cache.HEAT_FROM_CRYPTO_TRANSACTION
        heat_after_df = base_heat * (1 - mock_ui_state.game_configs_data_cache.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
        heat_after_phone = heat_after_df * (1 - mock_ui_state.game_configs_data_cache.SECURE_PHONE_HEAT_REDUCTION_PERCENT)
        expected_heat_added = round(heat_after_phone)
        self.assertEqual(mock_region.current_heat, initial_region_heat + expected_heat_added)
        self.mock_show_event_message.assert_called_once()

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_sell_crypto_fail_insufficient_crypto(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.add_crypto(CryptoCoin.BITCOIN, 0.5)
        mock_ui_state.tech_transaction_in_progress = "sell_crypto"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.BITCOIN
        mock_ui_state.tech_input_string = "1.0"
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_called_with("Error: Not enough crypto.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_launder_cash_success(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        player_initial_cash = 5000.0
        amount_to_launder = 1000.0
        mock_ui_state.player_inventory_cache.cash = player_initial_cash
        mock_ui_state.tech_transaction_in_progress = "launder_cash"
        mock_ui_state.tech_input_string = str(amount_to_launder)
        mock_region = mock_ui_state.game_state_data_cache.current_player_region
        initial_region_heat = mock_region.current_heat
        current_day = mock_ui_state.game_state_data_cache.current_day
        fee_percent = mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES['LAUNDER_CASH']['fee']
        delay_days = mock_ui_state.game_configs_data_cache.LAUNDERING_DELAY_DAYS
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        expected_fee = amount_to_launder * fee_percent
        expected_total_deduction = amount_to_launder + expected_fee
        expected_launder_heat = int(amount_to_launder * 0.05)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.cash, player_initial_cash - expected_total_deduction)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.pending_laundered_sc, amount_to_launder)
        self.assertEqual(mock_ui_state.player_inventory_cache.pending_laundered_sc_arrival_day, current_day + delay_days)
        self.assertEqual(mock_region.current_heat, initial_region_heat + expected_launder_heat)
        self.mock_show_event_message.assert_called_once()

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_launder_cash_fail_insufficient_cash(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        amount_to_launder = 1000
        fee = amount_to_launder * mock_ui_state.game_configs_data_cache.TECH_CONTACT_SERVICES['LAUNDER_CASH']['fee']
        mock_ui_state.player_inventory_cache.cash = amount_to_launder + fee - 1
        mock_ui_state.tech_transaction_in_progress = "launder_cash"
        mock_ui_state.tech_input_string = str(amount_to_launder)
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_called_with("Error: Not enough cash for amount + fee.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_stake_dc_success(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        initial_dc_wallet = 100.0
        amount_to_stake = 50.0
        mock_ui_state.player_inventory_cache.add_crypto(CryptoCoin.DRUG_COIN, initial_dc_wallet)
        mock_ui_state.tech_transaction_in_progress = "stake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.DRUG_COIN
        mock_ui_state.tech_input_string = str(amount_to_stake)
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0), initial_dc_wallet - amount_to_stake)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['staked_amount'], amount_to_stake)
        self.mock_show_event_message.assert_called_with(f"Staked {amount_to_stake:.4f} DC.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_stake_dc_fail_insufficient_dc(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.crypto_wallet[CryptoCoin.DRUG_COIN] = 5.0
        mock_ui_state.tech_transaction_in_progress = "stake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.DRUG_COIN
        mock_ui_state.tech_input_string = "10.0"
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_called_with(f"Error: Not enough {CryptoCoin.DRUG_COIN.value} or wrong coin.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_stake_dc_fail_wrong_coin(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.add_crypto(CryptoCoin.BITCOIN, 10.0)
        mock_ui_state.tech_transaction_in_progress = "stake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.BITCOIN
        mock_ui_state.tech_input_string = "5.0"
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_called_with(f"Error: Not enough {CryptoCoin.DRUG_COIN.value} or wrong coin.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_unstake_dc_success(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        initial_staked_dc = 100.0
        pending_rewards_dc = 10.0
        amount_to_unstake = 50.0
        initial_wallet_dc = 5.0
        mock_ui_state.player_inventory_cache.staked_drug_coin['staked_amount'] = initial_staked_dc
        mock_ui_state.player_inventory_cache.staked_drug_coin['pending_rewards'] = pending_rewards_dc
        mock_ui_state.player_inventory_cache.add_crypto(CryptoCoin.DRUG_COIN, initial_wallet_dc)
        mock_ui_state.tech_transaction_in_progress = "unstake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.DRUG_COIN
        mock_ui_state.tech_input_string = str(amount_to_unstake)
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['staked_amount'], initial_staked_dc - amount_to_unstake)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.staked_drug_coin['pending_rewards'], 0.0)
        self.assertAlmostEqual(mock_ui_state.player_inventory_cache.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0), initial_wallet_dc + amount_to_unstake + pending_rewards_dc)
        self.mock_show_event_message.assert_called_with(f"Unstaked {amount_to_unstake:.4f} DC. Rewards collected: {pending_rewards_dc:.4f} DC.")

    @patch('src.ui_pygame.state', new_callable=MagicMock)
    def test_action_confirm_tech_op_unstake_dc_fail_insufficient_staked(self, mock_ui_state):
        self._setup_mock_ui_state_for_tech_ops(mock_ui_state)
        mock_ui_state.player_inventory_cache.staked_drug_coin['staked_amount'] = 20.0
        mock_ui_state.tech_transaction_in_progress = "unstake_dc"
        mock_ui_state.coin_for_tech_transaction = CryptoCoin.DRUG_COIN
        mock_ui_state.tech_input_string = "25.0"
        action_confirm_tech_operation(mock_ui_state.player_inventory_cache, mock_ui_state.game_state_data_cache, mock_ui_state.game_configs_data_cache)
        self.mock_show_event_message.assert_called_with(f"Error: Not enough staked {CryptoCoin.DRUG_COIN.value} or wrong coin.")

if __name__ == '__main__':
    unittest.main()
