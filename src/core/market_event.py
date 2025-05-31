from typing import Optional
from .enums import DrugQuality, DrugName, EventType

class MarketEvent:
    def __init__(self, event_type: EventType, target_drug_name: Optional[DrugName], # For RIVAL_BUSTED, this is rival's name
                 target_quality: Optional[DrugQuality],
                 sell_price_multiplier: float, buy_price_multiplier: float,
                 duration_remaining_days: int, start_day: int,
                 heat_increase_amount: Optional[int] = None,
                 temporary_stock_increase: Optional[int] = None,
                 deal_drug_name: Optional[DrugName] = None, deal_quality: Optional[DrugQuality] = None,
                 deal_quantity: Optional[int] = None, deal_price_per_unit: Optional[float] = None,
                 is_buy_deal: bool = True,
                 # Fields for Supply Chain Disruption / Drug Market Crash
                 price_reduction_factor: Optional[float] = None,
                 minimum_price_after_crash: Optional[float] = None,
                 stock_reduction_factor: Optional[float] = None,
                 min_stock_after_event: Optional[int] = None,
                 # Fields for Black Market event
                 black_market_quantity_available: Optional[int] = None):
        self.event_type: EventType = event_type
        self.target_drug_name: Optional[DrugName] = target_drug_name
        self.target_quality: Optional[DrugQuality] = target_quality
        self.sell_price_multiplier: float = sell_price_multiplier
        self.buy_price_multiplier: float = buy_price_multiplier
        self.duration_remaining_days: int = duration_remaining_days
        self.start_day: int = start_day
        self.heat_increase_amount: Optional[int] = heat_increase_amount
        self.temporary_stock_increase: Optional[int] = temporary_stock_increase
        self.deal_drug_name: Optional[DrugName] = deal_drug_name
        self.deal_quality: Optional[DrugQuality] = deal_quality
        self.deal_quantity: Optional[int] = deal_quantity
        self.deal_price_per_unit: Optional[float] = deal_price_per_unit
        self.is_buy_deal: bool = is_buy_deal
        # Supply Chain Disruption / Drug Market Crash fields
        self.price_reduction_factor: Optional[float] = price_reduction_factor
        self.minimum_price_after_crash: Optional[float] = minimum_price_after_crash
        self.stock_reduction_factor: Optional[float] = stock_reduction_factor
        self.min_stock_after_event: Optional[int] = min_stock_after_event
        # Black Market event field
        self.black_market_quantity_available: Optional[int] = black_market_quantity_available

    def __str__(self):
        details = f"Event: {self.event_type.value}"
        if self.event_type == EventType.RIVAL_BUSTED and self.target_drug_name:
            details += f" (Target: {self.target_drug_name.value if self.target_drug_name else 'N/A'})" # Rival's name stored in target_drug_name
        elif self.event_type == EventType.BLACK_MARKET_OPPORTUNITY and self.target_drug_name and self.target_quality:
            details += f" for {self.target_quality.name} {self.target_drug_name.value if self.target_drug_name else 'N/A'}"
            if self.black_market_quantity_available is not None:
                details += f" (Qty: {self.black_market_quantity_available})"
            details += f", Buy_Mult: {self.buy_price_multiplier:.2f}"
        elif self.target_drug_name and self.target_quality:
            details += f" for {self.target_quality.name} {self.target_drug_name.value if self.target_drug_name else 'N/A'}"
        elif self.event_type == EventType.THE_SETUP and self.deal_drug_name and self.deal_quality:
             action = "Buy" if self.is_buy_deal else "Sell"
             details += f" (Offer: {action} {self.deal_quantity} {self.deal_quality.name} {self.deal_drug_name.value if self.deal_drug_name else 'N/A'} @ ${self.deal_price_per_unit:.2f})"

        details += f", Days Left: {self.duration_remaining_days}"
        if self.event_type == EventType.DEMAND_SPIKE or self.event_type == EventType.CHEAP_STASH and self.event_type != EventType.BLACK_MARKET_OPPORTUNITY:
            details += f", B_Mult: {self.buy_price_multiplier:.2f}"
        if self.event_type == EventType.DEMAND_SPIKE:
            details += f", S_Mult: {self.sell_price_multiplier:.2f}"
        if self.heat_increase_amount is not None:
            details += f", Heat Inc: {self.heat_increase_amount}"
        if self.temporary_stock_increase is not None:
            details += f", Stock Inc: +{self.temporary_stock_increase}"
        return details