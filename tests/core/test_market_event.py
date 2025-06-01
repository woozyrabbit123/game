import unittest
from src.core.market_event import MarketEvent
from src.core.enums import EventType, DrugName, DrugQuality

class TestMarketEvent(unittest.TestCase):

    def test_event_initialization_minimal(self):
        event = MarketEvent(
            event_type=EventType.POLICE_CRACKDOWN,
            target_drug_name=None,
            target_quality=None,
            sell_price_multiplier=1.0,
            buy_price_multiplier=1.0,
            duration_remaining_days=3,
            start_day=1
        )
        self.assertEqual(event.event_type, EventType.POLICE_CRACKDOWN)
        self.assertIsNone(event.target_drug_name)
        self.assertEqual(event.duration_remaining_days, 3)
        self.assertEqual(event.start_day, 1)
        # Check some other optionals are indeed None or default
        self.assertIsNone(event.heat_increase_amount)
        self.assertIsNone(event.deal_drug_name)

    def test_demand_spike_event(self):
        event = MarketEvent(
            event_type=EventType.DEMAND_SPIKE,
            target_drug_name=DrugName.COKE,
            target_quality=DrugQuality.PURE,
            sell_price_multiplier=1.5,
            buy_price_multiplier=1.2,
            duration_remaining_days=2,
            start_day=5
        )
        self.assertEqual(event.event_type, EventType.DEMAND_SPIKE)
        self.assertEqual(event.target_drug_name, DrugName.COKE)
        self.assertEqual(event.target_quality, DrugQuality.PURE)
        self.assertAlmostEqual(event.sell_price_multiplier, 1.5)
        self.assertAlmostEqual(event.buy_price_multiplier, 1.2)
        self.assertEqual(event.duration_remaining_days, 2)
        self.assertEqual(event.start_day, 5)

    def test_the_setup_event_buy_deal(self):
        event = MarketEvent(
            event_type=EventType.THE_SETUP,
            target_drug_name=None, # Not used for THE_SETUP's primary effect
            target_quality=None,
            sell_price_multiplier=1.0, # Base multipliers not used for deal itself
            buy_price_multiplier=1.0,
            duration_remaining_days=1,
            start_day=10,
            deal_drug_name=DrugName.HEROIN,
            deal_quality=DrugQuality.STANDARD,
            deal_quantity=50,
            deal_price_per_unit=200.0,
            is_buy_deal=True
        )
        self.assertEqual(event.event_type, EventType.THE_SETUP)
        self.assertEqual(event.deal_drug_name, DrugName.HEROIN)
        self.assertEqual(event.deal_quality, DrugQuality.STANDARD)
        self.assertEqual(event.deal_quantity, 50)
        self.assertAlmostEqual(event.deal_price_per_unit, 200.0)
        self.assertTrue(event.is_buy_deal)
        self.assertEqual(event.duration_remaining_days, 1)

    def test_rival_busted_event(self):
        # For RIVAL_BUSTED, target_drug_name stores the rival's name (string)
        # The type hint Optional[DrugName] is slightly off for this specific case,
        # but the class stores whatever is passed.
        rival_name_str = "El Jefe"
        event = MarketEvent(
            event_type=EventType.RIVAL_BUSTED,
            target_drug_name=rival_name_str, # Passing string here
            target_quality=None,
            sell_price_multiplier=1.0,
            buy_price_multiplier=1.0,
            duration_remaining_days=7,
            start_day=2
        )
        self.assertEqual(event.event_type, EventType.RIVAL_BUSTED)
        self.assertEqual(event.target_drug_name, rival_name_str) # Verifies it stores the string
        self.assertEqual(event.duration_remaining_days, 7)

    def test_supply_disruption_event(self):
        event = MarketEvent(
            event_type=EventType.SUPPLY_DISRUPTION,
            target_drug_name=DrugName.SPEED,
            target_quality=DrugQuality.CUT,
            sell_price_multiplier=1.0, # Not directly used by price, but by stock effect
            buy_price_multiplier=1.0,
            duration_remaining_days=3,
            start_day=1,
            stock_reduction_factor=0.25,
            min_stock_after_event=10
        )
        self.assertEqual(event.event_type, EventType.SUPPLY_DISRUPTION)
        self.assertEqual(event.target_drug_name, DrugName.SPEED)
        self.assertEqual(event.target_quality, DrugQuality.CUT)
        self.assertAlmostEqual(event.stock_reduction_factor, 0.25)
        self.assertEqual(event.min_stock_after_event, 10)

    def test_black_market_opportunity_event(self):
        event = MarketEvent(
            event_type=EventType.BLACK_MARKET_OPPORTUNITY,
            target_drug_name=DrugName.WEED,
            target_quality=DrugQuality.STANDARD,
            sell_price_multiplier=1.0, # Not relevant for BMO sell
            buy_price_multiplier=0.5,
            duration_remaining_days=1,
            start_day=12,
            black_market_quantity_available=100
        )
        self.assertEqual(event.event_type, EventType.BLACK_MARKET_OPPORTUNITY)
        self.assertEqual(event.target_drug_name, DrugName.WEED)
        self.assertEqual(event.target_quality, DrugQuality.STANDARD)
        self.assertAlmostEqual(event.buy_price_multiplier, 0.5)
        self.assertEqual(event.black_market_quantity_available, 100)

    def test_event_str_method(self):
        event = MarketEvent(
            event_type=EventType.DEMAND_SPIKE,
            target_drug_name=DrugName.COKE,
            target_quality=DrugQuality.PURE,
            sell_price_multiplier=1.5,
            buy_price_multiplier=1.2,
            duration_remaining_days=2,
            start_day=5
        )
        event_string = str(event)
        self.assertIn("DEMAND_SPIKE", event_string)
        self.assertIn("PURE Coke", event_string) # Corrected: DrugName.value is capitalized
        self.assertIn("Days Left: 2", event_string)
        self.assertIn("B_Mult: 1.20", event_string)
        self.assertIn("S_Mult: 1.50", event_string)

        setup_event = MarketEvent(
            event_type=EventType.THE_SETUP, target_drug_name=None, target_quality=None,
            sell_price_multiplier=1.0, buy_price_multiplier=1.0, duration_remaining_days=1, start_day=10,
            deal_drug_name=DrugName.HEROIN, deal_quality=DrugQuality.STANDARD,
            deal_quantity=50, deal_price_per_unit=200.0, is_buy_deal=False # Sell deal
        )
        setup_string = str(setup_event)
        self.assertIn("THE_SETUP", setup_string)
        self.assertIn("Offer: Sell 50 STANDARD Heroin @ $200.00", setup_string) # Corrected: DrugName.value is capitalized


if __name__ == '__main__':
    unittest.main()
