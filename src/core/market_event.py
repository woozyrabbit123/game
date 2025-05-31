from typing import Optional
from .enums import DrugQuality

class MarketEvent:
    def __init__(self, event_type: str, target_drug_name: Optional[str], # For RIVAL_BUSTED, this is rival's name
                 target_quality: Optional[DrugQuality],
                 sell_price_multiplier: float, buy_price_multiplier: float,
                 duration_remaining_days: int, start_day: int,
                 heat_increase_amount: Optional[int] = None,
                 temporary_stock_increase: Optional[int] = None,
                 deal_drug_name: Optional[str] = None, deal_quality: Optional[DrugQuality] = None,
                 deal_quantity: Optional[int] = None, deal_price_per_unit: Optional[float] = None,
                 is_buy_deal: bool = True,
                 price_reduction_factor: Optional[float] = None,
                 minimum_price_after_crash: Optional[float] = None,
                 stock_reduction_factor: Optional[float] = None, # New
                 min_stock_after_event: Optional[int] = None): # New
        self.event_type: str = event_type
        self.target_drug_name: Optional[str] = target_drug_name 
        self.target_quality: Optional[DrugQuality] = target_quality
        self.sell_price_multiplier: float = sell_price_multiplier
        self.buy_price_multiplier: float = buy_price_multiplier
        self.duration_remaining_days: int = duration_remaining_days
        self.start_day: int = start_day
        self.heat_increase_amount: Optional[int] = heat_increase_amount
        self.temporary_stock_increase: Optional[int] = temporary_stock_increase
        self.deal_drug_name = deal_drug_name; self.deal_quality = deal_quality
        self.deal_quantity = deal_quantity; self.deal_price_per_unit = deal_price_per_unit
        self.is_buy_deal = is_buy_deal
        self.price_reduction_factor = price_reduction_factor
        self.minimum_price_after_crash = minimum_price_after_crash
        self.stock_reduction_factor = stock_reduction_factor
        self.min_stock_after_event = min_stock_after_event

    def __str__(self):
        details = f"Event: {self.event_type}"
        if self.event_type == "RIVAL_BUSTED" and self.target_drug_name:
            details += f" (Target: {self.target_drug_name})" # Rival's name stored in target_drug_name
        elif self.target_drug_name and self.target_quality:
            details += f" for {self.target_quality.name} {self.target_drug_name}"
        elif self.event_type == "THE_SETUP" and self.deal_drug_name and self.deal_quality:
             action = "Buy" if self.is_buy_deal else "Sell"
             details += f" (Offer: {action} {self.deal_quantity} {self.deal_quality.name} {self.deal_drug_name} @ ${self.deal_price_per_unit:.2f})"
        # ... (rest of __str__ as before) ...
        details += f", Days Left: {self.duration_remaining_days}"
        if self.event_type == "DEMAND_SPIKE" or self.event_type == "CHEAP_STASH": details += f", B_Mult: {self.buy_price_multiplier:.2f}"
        if self.event_type == "DEMAND_SPIKE": details += f", S_Mult: {self.sell_price_multiplier:.2f}"
        if self.heat_increase_amount is not None: details += f", Heat Inc: {self.heat_increase_amount}"
        if self.temporary_stock_increase is not None: details += f", Stock Inc: +{self.temporary_stock_increase}"
        return details