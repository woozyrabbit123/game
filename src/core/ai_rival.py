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
        primary_drug (DrugName): The drug this rival primarily deals in.
        primary_region_name (RegionName): The region where this rival primarily operates.
        aggression (float): A factor determining how aggressively the rival acts (e.g., 0.0 to 1.0).
        activity_level (float): A factor determining how frequently the rival acts (e.g., 0.0 to 1.0).
        is_busted (bool): True if the rival is currently busted and out of action, False otherwise.
        busted_days_remaining (int): Number of days remaining for the rival to be busted.
    """

    def __init__(
        self,
        name: str,
        primary_drug: "DrugName",
        primary_region_name: "RegionName",
        aggression: float,
        activity_level: float,
    ) -> None:
        """
        Initializes an AI Rival.

        Args:
            name: The name of the rival.
            primary_drug: The DrugName enum member for the rival's main drug.
            primary_region_name: The RegionName enum member for the rival's main region.
            aggression: Rival's aggression level (0.0-1.0).
            activity_level: Rival's activity level (0.0-1.0).
        """
        self.name: str = name
        self.primary_drug: "DrugName" = primary_drug
        self.primary_region_name: "RegionName" = primary_region_name
        self.aggression: float = aggression
        self.activity_level: float = activity_level
        self.is_busted: bool = False
        self.busted_days_remaining: int = 0
