import unittest
from src.core.enums import RegionName

class TestEnums(unittest.TestCase):
    def test_region_names_complete(self):
        expected_regions = [
            "Downtown", "Suburbs", "Industrial District", "Docks",
            "Commercial District", "University Hills", "Riverside",
            "Airport District", "Old Town"
        ]
        actual_region_values = [r.value for r in RegionName]
        self.assertEqual(len(actual_region_values), len(expected_regions))
        for region_name in expected_regions:
            self.assertIn(region_name, actual_region_values)

if __name__ == '__main__':
    unittest.main()
