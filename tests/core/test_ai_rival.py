import unittest
from src.core.ai_rival import AIRival
from src.core.enums import DrugName, RegionName

class TestAIRival(unittest.TestCase):

    def test_ai_rival_initialization(self):
        rival_name = "Test Rival"
        primary_drug = DrugName.COKE
        primary_region = RegionName.DOWNTOWN
        aggression_level = 0.75
        activity = 0.5

        rival = AIRival(
            name=rival_name,
            primary_drug=primary_drug,
            primary_region_name=primary_region,
            aggression=aggression_level,
            activity_level=activity
        )

        self.assertEqual(rival.name, rival_name)
        self.assertEqual(rival.primary_drug, primary_drug)
        self.assertEqual(rival.primary_region_name, primary_region)
        self.assertAlmostEqual(rival.aggression, aggression_level)
        self.assertAlmostEqual(rival.activity_level, activity)
        self.assertFalse(rival.is_busted, "Default is_busted should be False")
        self.assertEqual(rival.busted_days_remaining, 0, "Default busted_days_remaining should be 0")

    def test_ai_rival_busted_state_settable(self):
        rival = AIRival("BustMe", DrugName.HEROIN, RegionName.DOCKS, 0.5, 0.5)

        rival.is_busted = True
        rival.busted_days_remaining = 5

        self.assertTrue(rival.is_busted)
        self.assertEqual(rival.busted_days_remaining, 5)

        rival.is_busted = False
        # Corrected typo from 'basted_days_remaining' to 'busted_days_remaining'
        rival.busted_days_remaining = 0

        self.assertFalse(rival.is_busted)
        self.assertEqual(rival.busted_days_remaining, 0)


if __name__ == '__main__':
    unittest.main()
