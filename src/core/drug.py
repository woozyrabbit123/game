from .enums import DrugQuality

class Drug:
    def __init__(self, name: str, tier: int, base_buy_price: float, base_sell_price: float,
                 quality: DrugQuality = DrugQuality.STANDARD):
        self.name = name
        self.tier = tier
        self.base_buy_price = base_buy_price
        self.base_sell_price = base_sell_price
        self.quality = quality if tier > 1 else DrugQuality.STANDARD

    def get_quality_multiplier(self, price_type: str) -> float:
        if price_type == "buy":
            if self.quality == DrugQuality.CUT:
                return 0.7
            elif self.quality == DrugQuality.STANDARD:
                return 1.0
            elif self.quality == DrugQuality.PURE:
                return 1.5
        elif price_type == "sell":
            if self.quality == DrugQuality.CUT:
                return 0.75
            elif self.quality == DrugQuality.STANDARD:
                return 1.0
            elif self.quality == DrugQuality.PURE:
                return 1.6
        # Default for unknown price_type or if quality somehow not in enum (though last line handles it)
        return 1.0