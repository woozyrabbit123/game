from .enums import DrugName, RegionName # Import enums

class AIRival:
    def __init__(self, name: str, primary_drug: DrugName, primary_region_name: RegionName, 
                aggression: float, activity_level: float):
        self.name = name
        self.primary_drug = primary_drug # Should be DrugName enum
        self.primary_region_name = primary_region_name # Should be RegionName enum
        self.aggression = aggression
        self.activity_level = activity_level
        self.is_busted: bool = False # New attribute
        self.busted_days_remaining: int = 0 # New attribute