"""
Defines the Drug class, representing a specific drug item with its attributes.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .. import narco_configs as game_configs  # Import the narco_configs module
from .enums import DrugQuality

if TYPE_CHECKING:
    pass


@dataclass
class Drug:
    """
    Represents a drug item in the game.

    Each drug has a name, tier (rarity/value), base prices, and quality.
    The quality affects its actual buy and sell prices.
    """
    name: str
    tier: int
    base_buy_price: float
    base_sell_price: float
    quality: DrugQuality = DrugQuality.STANDARD

    def __post_init__(self) -> None:
        """
        Post-initialization logic.
        If tier is 1, quality is forced to STANDARD, overriding any provided
        quality.
        """
        if self.tier == 1:
            self.quality = DrugQuality.STANDARD

    def get_quality_multiplier(self, price_type: str) -> float:
        """
        Calculates the price multiplier based on the drug's quality.

        This multiplier is applied to the base price to determine the actual
        buy or sell price. PURE quality generally increases value, while CUT
        quality decreases it.

        Args:
            price_type: A string indicating 'buy' or 'sell'.

        Returns:
            The quality-based price multiplier. Returns default if price_type
            is unknown or quality is invalid.
        """
        if price_type == 'buy':
            if self.quality == DrugQuality.CUT:
                return game_configs.QUALITY_MULT_CUT_BUY
            elif self.quality == DrugQuality.STANDARD:
                return game_configs.QUALITY_MULT_STANDARD_BUY
            elif self.quality == DrugQuality.PURE:
                return game_configs.QUALITY_MULT_PURE_BUY
        elif price_type == 'sell':
            if self.quality == DrugQuality.CUT:
                return game_configs.QUALITY_MULT_CUT_SELL
            elif self.quality == DrugQuality.STANDARD:
                return game_configs.QUALITY_MULT_STANDARD_SELL
            elif self.quality == DrugQuality.PURE:
                return game_configs.QUALITY_MULT_PURE_SELL
        return game_configs.QUALITY_MULT_DEFAULT
