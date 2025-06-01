"""
Defines the AIRival class, representing an AI-controlled opponent in the game.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .enums import DrugName, RegionName


class AIRival:
    """
    Represents an AI-controlled rival in the game.

    Attributes:
        name (str): The name of the AI rival.
        primary_drug (DrugName): Drug this rival primarily deals in.
        primary_region_name (RegionName): Region where this rival primarily operates.
        aggression (float): Aggressiveness factor (e.g., 0.0 to 1.0).
        activity_level (float): Activity frequency factor (e.g., 0.0 to 1.0).
        is_busted (bool): True if busted and out of action, False otherwise.
        busted_days_remaining (int): Days rival remains busted.
    """

    def __init__(
        self,
        name: str,
        primary_drug: 'DrugName',
        primary_region_name: 'RegionName',
        aggression: float,
        activity_level: float,
    ) -> None:
        """
        Initializes an AI Rival.

        Args:
            name: The name of the rival.
            primary_drug: DrugName enum for the rival's main drug.
            primary_region_name: RegionName enum for the rival's main region.
            aggression: Rival's aggression level (0.0-1.0).
            activity_level: Rival's activity level (0.0-1.0).
        """
        self.name: str = name
        self.primary_drug: 'DrugName' = primary_drug
        self.primary_region_name: 'RegionName' = primary_region_name
        self.aggression: float = aggression
        self.activity_level: float = activity_level
        self.is_busted: bool = False
        self.busted_days_remaining: int = 0
