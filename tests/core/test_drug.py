import unittest
from src.core.drug import Drug
from src.core.enums import DrugQuality, DrugName # DrugName might not be strictly needed but good for context

class TestDrug(unittest.TestCase):

    def test_drug_initialization_standard(self):
        drug = Drug(name="TestDrug", tier=2, base_buy_price=100.0, base_sell_price=150.0, quality=DrugQuality.STANDARD)
        self.assertEqual(drug.name, "TestDrug")
        self.assertEqual(drug.tier, 2)
        self.assertEqual(drug.base_buy_price, 100.0)
        self.assertEqual(drug.base_sell_price, 150.0)
        self.assertEqual(drug.quality, DrugQuality.STANDARD)

    def test_drug_initialization_tier1_forces_standard_quality(self):
        # Tier 1 drug should always be STANDARD quality, even if PURE is passed
        drug_tier1_pure = Drug(name="TestTier1Pure", tier=1, base_buy_price=50.0, base_sell_price=80.0, quality=DrugQuality.PURE)
        self.assertEqual(drug_tier1_pure.quality, DrugQuality.STANDARD, "Tier 1 drug did not default to STANDARD quality when PURE was input.")

        drug_tier1_cut = Drug(name="TestTier1Cut", tier=1, base_buy_price=50.0, base_sell_price=80.0, quality=DrugQuality.CUT)
        self.assertEqual(drug_tier1_cut.quality, DrugQuality.STANDARD, "Tier 1 drug did not default to STANDARD quality when CUT was input.")

        drug_tier1_standard = Drug(name="TestTier1Standard", tier=1, base_buy_price=50.0, base_sell_price=80.0, quality=DrugQuality.STANDARD)
        self.assertEqual(drug_tier1_standard.quality, DrugQuality.STANDARD)

        # Test with default quality for Tier 1
        drug_tier1_default = Drug(name="TestTier1Default", tier=1, base_buy_price=50.0, base_sell_price=80.0)
        self.assertEqual(drug_tier1_default.quality, DrugQuality.STANDARD)

    def test_drug_initialization_tier2_allows_specific_quality(self):
        drug_tier2_pure = Drug(name="TestTier2Pure", tier=2, base_buy_price=100.0, base_sell_price=150.0, quality=DrugQuality.PURE)
        self.assertEqual(drug_tier2_pure.quality, DrugQuality.PURE)

        drug_tier2_cut = Drug(name="TestTier2Cut", tier=2, base_buy_price=100.0, base_sell_price=150.0, quality=DrugQuality.CUT)
        self.assertEqual(drug_tier2_cut.quality, DrugQuality.CUT)

    def test_get_quality_multiplier_cut(self):
        drug = Drug(name="TestCut", tier=2, base_buy_price=100.0, base_sell_price=150.0, quality=DrugQuality.CUT)
        self.assertEqual(drug.get_quality_multiplier("buy"), 0.7)
        self.assertEqual(drug.get_quality_multiplier("sell"), 0.75)

    def test_get_quality_multiplier_standard(self):
        drug = Drug(name="TestStandard", tier=2, base_buy_price=100.0, base_sell_price=150.0, quality=DrugQuality.STANDARD)
        self.assertEqual(drug.get_quality_multiplier("buy"), 1.0)
        self.assertEqual(drug.get_quality_multiplier("sell"), 1.0)

    def test_get_quality_multiplier_pure(self):
        drug = Drug(name="TestPure", tier=2, base_buy_price=100.0, base_sell_price=150.0, quality=DrugQuality.PURE)
        self.assertEqual(drug.get_quality_multiplier("buy"), 1.5)
        self.assertEqual(drug.get_quality_multiplier("sell"), 1.6)

    def test_get_quality_multiplier_unknown_price_type(self):
        # Tests the fallback behavior for an undefined price_type string
        drug = Drug(name="TestUnknown", tier=2, base_buy_price=100.0, base_sell_price=150.0, quality=DrugQuality.STANDARD)
        self.assertEqual(drug.get_quality_multiplier("unknown"), 1.0, "Should default to 1.0 for unknown price type")

        drug_pure = Drug(name="TestPureUnknown", tier=2, base_buy_price=100.0, base_sell_price=150.0, quality=DrugQuality.PURE)
        self.assertEqual(drug_pure.get_quality_multiplier("other"), 1.0, "Should default to 1.0 for unknown price type even if PURE quality")

if __name__ == '__main__':
    unittest.main()
