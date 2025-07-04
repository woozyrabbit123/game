"""
Defines the MarketEvent class, representing dynamic occurrences affecting
drug markets or player.
"""
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

from .enums import DrugQuality, DrugName, EventType


if TYPE_CHECKING:
    pass


@dataclass
class MarketEvent:
    """
    Represents a market event affecting drug prices, stock, or regional heat.

    Events have a type, can target specific drugs/qualities, and have various
    multipliers or effects that last for a certain duration.
    """
    event_type: EventType
    # For RIVAL_BUSTED, target_drug_name can be a string (rival's name).
    # Using Any for now to accommodate this.
    # Ideally, this would be Union[Optional[DrugName], str] or separate fields.
    target_drug_name: Optional[Any]  # Was Optional[DrugName]
    target_quality: Optional[DrugQuality]
    sell_price_multiplier: float
    buy_price_multiplier: float
    duration_remaining_days: int
    start_day: int
    heat_increase_amount: Optional[int] = None
    temporary_stock_increase: Optional[int] = None
    deal_drug_name: Optional[DrugName] = None
    deal_quality: Optional[DrugQuality] = None
    deal_quantity: Optional[int] = None
    deal_price_per_unit: Optional[float] = None
    is_buy_deal: bool = True  # Default for THE_SETUP event
    # Fields for Supply Chain Disruption / Drug Market Crash
    price_reduction_factor: Optional[float] = None
    minimum_price_after_crash: Optional[float] = None
    stock_reduction_factor: Optional[float] = None
    min_stock_after_event: Optional[int] = None
    # Black Market event field
    black_market_quantity_available: Optional[int] = None

    def __str__(self) -> str:
        """Returns a string representation of the market event."""
        details: str = f'Event: {self.event_type.value}'
        target_drug_str = ''
        if isinstance(self.target_drug_name, DrugName):
            target_drug_str = self.target_drug_name.value
        elif isinstance(self.target_drug_name, str): # For RIVAL_BUSTED
            target_drug_str = self.target_drug_name

        if self.event_type == EventType.RIVAL_BUSTED and target_drug_str:
            details += f' (Target: {target_drug_str})'
        elif (
            self.event_type == EventType.BLACK_MARKET_OPPORTUNITY
            and target_drug_str and self.target_quality
        ):
            details += f' for {self.target_quality.name} {target_drug_str}'
            if self.black_market_quantity_available is not None:
                details += f' (Qty: {self.black_market_quantity_available})'
            details += f', Buy_Mult: {self.buy_price_multiplier:.2f}'
        elif target_drug_str and self.target_quality:
            details += f' for {self.target_quality.name} {target_drug_str}'
        elif (
            self.event_type == EventType.THE_SETUP
            and self.deal_drug_name and self.deal_quality
        ):
            action = 'Buy' if self.is_buy_deal else 'Sell'
            deal_drug_val = self.deal_drug_name.value if self.deal_drug_name else 'N/A'
            details += (
                f' (Offer: {action} {self.deal_quantity} '
                f'{self.deal_quality.name} {deal_drug_val} '
                f'@ ${self.deal_price_per_unit:.2f})'
            )

        details += f', Days Left: {self.duration_remaining_days}'
        if (self.event_type == EventType.DEMAND_SPIKE or
                (self.event_type == EventType.CHEAP_STASH and
                 self.event_type != EventType.BLACK_MARKET_OPPORTUNITY)):
            details += f', B_Mult: {self.buy_price_multiplier:.2f}'
        if self.event_type == EventType.DEMAND_SPIKE:
            details += f', S_Mult: {self.sell_price_multiplier:.2f}'
        if self.heat_increase_amount is not None:
            details += f', Heat Inc: {self.heat_increase_amount}'
        if self.temporary_stock_increase is not None:
            details += f', Stock Inc: +{self.temporary_stock_increase}'
        return details
