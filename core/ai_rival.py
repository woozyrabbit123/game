class AIRival:
    def __init__(self, name: str, primary_drug: str, primary_region_name: str, 
                aggression: float, activity_level: float):
        self.name = name
        self.primary_drug = primary_drug
        self.primary_region_name = primary_region_name
        self.aggression = aggression
        self.activity_level = activity_level
        self.is_busted: bool = False # New attribute
        self.busted_days_remaining: int = 0 # New attribute