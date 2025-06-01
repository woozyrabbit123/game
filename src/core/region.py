"""
Defines the Region class, representing a geographical area in the game.

Each region has its own drug market, heat level, and can host various market events.
"""

import random
import math
from typing import Dict, List, Optional, Union, Any, TYPE_CHECKING

from .enums import DrugQuality, DrugName, EventType, RegionName
from .drug import Drug
from .market_event import MarketEvent

# from ..game_state import GameState # Removed direct import
# from typing import TYPE_CHECKING # Already imported above
from ..game_configs import (
    HEAT_PRICE_INCREASE_THRESHOLDS,
    HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3,
    TIER1_STANDARD_INITIAL_STOCK, # Added
    TIER_GT1_PURE_STOCK_RANGE,    # Added
    TIER_GT1_STANDARD_STOCK_RANGE, # Added
    TIER_GT1_CUT_STOCK_RANGE       # Added
)

if TYPE_CHECKING:
    from ..game_state import GameState


class Region:
    """
    Represents a distinct geographical region in the game world.

    Each region maintains its own drug market, heat level, and list of
    active market events. Player can travel between regions, and each
    region offers different drug prices and availability.

    Attributes:
        name (RegionName): The enum member representing the name of this region.
        drug_market_data (Dict[DrugName, Dict[str, Any]]): Data for drugs available
            in this region's market. Keys are DrugName enums. Inner dictionary
            contains base prices, tier, price modifiers, and available qualities.
        active_market_events (List[MarketEvent]): A list of MarketEvent objects
            currently active in this region.
        current_heat (int): The current police attention (heat) level in this region.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a Region instance.

        Args:
            name: The string name of the region, which will be converted to a
                  RegionName enum member.
        """
        self.name: RegionName = RegionName(name) if isinstance(name, str) else name
        self.drug_market_data: Dict[DrugName, Dict[str, Any]] = {}
        self.active_market_events: List[MarketEvent] = []
        self.current_heat: int = 0

    def modify_heat(self, amount: int) -> None:
        """
        Modifies the current heat level of the region.

        Heat cannot go below zero.

        Args:
            amount: The amount by which to change the heat level (can be negative).
        """
        self.current_heat += amount
        self.current_heat = max(0, self.current_heat)

    def initialize_drug_market(
        self,
        drug_name: Union[DrugName, str],
        base_buy_price: float,
        base_sell_price: float,
        tier: int,
        initial_stocks: Optional[Dict[DrugQuality, int]] = None,
    ) -> None:
        """
        Initializes or updates a specific drug in the region's market.

        Sets up its base prices, tier, price impact modifiers, and initial stock
        levels for its available qualities.

        Args:
            drug_name: The DrugName enum or string name of the drug.
            base_buy_price: The base price for buying this drug.
            base_sell_price: The base price for selling this drug.
            tier: The tier of the drug (1-4).
            initial_stocks: An optional dictionary specifying initial stock quantities
                            for different DrugQuality levels.
        """
        drug_name_enum: DrugName = (
            DrugName(drug_name) if isinstance(drug_name, str) else drug_name
        )
        self.drug_market_data[drug_name_enum] = {
            "base_buy_price": base_buy_price,
            "base_sell_price": base_sell_price,  # float
            "tier": tier,  # int
            "player_buy_impact_modifier": 1.0,  # float
            "player_sell_impact_modifier": 1.0,  # float
            "rival_demand_modifier": 1.0,  # float
            "rival_supply_modifier": 1.0,  # float
            "last_rival_activity_turn": -1,  # int
            "available_qualities": {},
        }
        drug_data: Dict[str, Any] = self.drug_market_data[drug_name_enum]
        qualities_to_init: List[DrugQuality] = (
            [DrugQuality.STANDARD]
            if tier == 1
            else [DrugQuality.CUT, DrugQuality.STANDARD, DrugQuality.PURE]
        )

        if (
            "available_qualities" not in drug_data
        ):  # Should always be true due to above initialization
            drug_data["available_qualities"] = {}

        for quality_enum_member in qualities_to_init:
            stock: int = 0
            if initial_stocks and quality_enum_member in initial_stocks:
                stock = initial_stocks[quality_enum_member]
            elif tier == 1 and quality_enum_member == DrugQuality.STANDARD:
                stock = TIER1_STANDARD_INITIAL_STOCK
            elif tier > 1:
                if quality_enum_member == DrugQuality.PURE:
                    stock = random.randint(*TIER_GT1_PURE_STOCK_RANGE)
                elif quality_enum_member == DrugQuality.STANDARD:
                    stock = random.randint(*TIER_GT1_STANDARD_STOCK_RANGE)
                else: # CUT
                    stock = random.randint(*TIER_GT1_CUT_STOCK_RANGE)

            drug_data["available_qualities"][quality_enum_member] = {
                "quantity_available": stock,
                "previous_buy_price": None,
                "previous_sell_price": None,
            }

    def _get_heat_price_multiplier(self) -> float:
        """Calculates price multiplier based on current regional heat."""
        for threshold, multiplier in sorted(
            HEAT_PRICE_INCREASE_THRESHOLDS.items(), reverse=True
        ):
            if self.current_heat >= threshold:
                return multiplier
        return 1.0

    def _get_heat_stock_reduction_factor(self) -> float:
        """Calculates stock reduction factor based on current regional heat for Tier 2/3 drugs."""
        for threshold, factor in sorted(
            HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3.items(), reverse=True
        ):
            if self.current_heat >= threshold:
                return factor
        return 1.0

    def get_buy_price(self, drug_name: DrugName, quality: DrugQuality) -> float:
        """
        Calculates the current buy price for a specific drug and quality in this region.

        Considers base price, quality, player impact, rival impact, heat, and active market events.

        Args:
            drug_name: The DrugName enum of the drug.
            quality: The DrugQuality enum of the drug.

        Returns:
            The calculated current buy price as a float. Returns 0.0 if not available.
        """
        if (
            drug_name not in self.drug_market_data
            or quality
            not in self.drug_market_data[drug_name].get("available_qualities", {})
        ):
            return 0.0

        drug_data_quality: Dict[str, Any] = self.drug_market_data[drug_name][
            "available_qualities"
        ][quality]
        drug_data_market: Dict[str, Any] = self.drug_market_data[drug_name]

        if drug_data_quality.get("quantity_available", 0) <= 0:
            is_event_driven_price: bool = False
            for event_item in self.active_market_events:  # event_item is MarketEvent
                if (
                    event_item.event_type == EventType.DEMAND_SPIKE
                    and event_item.target_drug_name == drug_name
                    and event_item.target_quality == quality
                ):
                    is_event_driven_price = True
                    break
            if not is_event_driven_price:
                return 0.0

        temp_drug: Drug = Drug(
            drug_name.value,
            drug_data_market["tier"],
            drug_data_market["base_buy_price"],
            drug_data_market["base_sell_price"],
            quality,
        )
        
        base_price: Optional[float] = drug_data_market.get("base_buy_price")
        tier_val: Optional[int] = drug_data_market.get("tier")

        if base_price is None or tier_val is None:
            # This indicates a problem with how the drug was initialized in the market
            print(f"Error: Drug {drug_name.value} in region {self.name.value} is missing critical data (base_price or tier).")
            return 0.0 # Cannot calculate price

        quality_mult: float = temp_drug.get_quality_multiplier("buy")
        player_mod: float = drug_data_market.get("player_buy_impact_modifier", 1.0) # Default to 1.0 if missing
        rival_mod: float = drug_data_market["rival_demand_modifier"]
        price_before_event_and_heat: float = (
            base_price * quality_mult * player_mod * rival_mod
        )

        current_previous_buy: Optional[float] = drug_data_quality.get(
            "previous_buy_price"
        )
        if (
            current_previous_buy is None
            or abs(current_previous_buy - price_before_event_and_heat) > 1e-2
        ):
            drug_data_quality["previous_buy_price"] = price_before_event_and_heat

        heat_multiplier: float = self._get_heat_price_multiplier()
        calculated_price: float = price_before_event_and_heat * heat_multiplier

        for event in self.active_market_events:  # event is MarketEvent
            if (
                event.event_type == EventType.BLACK_MARKET_OPPORTUNITY
                and event.target_drug_name == drug_name
                and event.target_quality == quality
                and getattr(event, "black_market_quantity_available", 0) > 0
                and event.duration_remaining_days > 0
            ):
                return round(max(0, calculated_price * event.buy_price_multiplier), 2)

        crash_event_applied: bool = False
        for event in self.active_market_events:  # event is MarketEvent
            if (
                event.event_type == EventType.DRUG_MARKET_CRASH
                and event.target_drug_name == drug_name
                and event.target_quality == quality
                and hasattr(event, "price_reduction_factor")
                and event.price_reduction_factor is not None
                and hasattr(event, "minimum_price_after_crash")
                and event.minimum_price_after_crash is not None
            ):
                calculated_price *= event.price_reduction_factor
                calculated_price = max(
                    calculated_price, event.minimum_price_after_crash
                )
                crash_event_applied = True
                break

        if not crash_event_applied:
            for event in self.active_market_events:  # event is MarketEvent
                if (
                    (
                        event.event_type == EventType.DEMAND_SPIKE
                        or event.event_type == EventType.CHEAP_STASH
                    )
                    and event.target_drug_name == drug_name
                    and event.target_quality == quality
                ):
                    if event.buy_price_multiplier != 1.0:
                        calculated_price *= event.buy_price_multiplier
                    break
        return round(max(0, calculated_price), 2)

    def get_sell_price(self, drug_name: DrugName, quality: DrugQuality) -> float:
        """
        Calculates the current sell price for a specific drug and quality in this region.

        Considers base price, quality, player impact, rival impact, and active market events.
        Note: Heat typically doesn't directly affect player's sell price in this model but could.

        Args:
            drug_name: The DrugName enum of the drug.
            quality: The DrugQuality enum of the drug.

        Returns:
            The calculated current sell price as a float. Returns 0.0 if not sellable.
        """
        if (
            drug_name not in self.drug_market_data
            or quality
            not in self.drug_market_data[drug_name].get("available_qualities", {})
        ):
            return 0.0

        drug_data_quality: Dict[str, Any] = self.drug_market_data[drug_name][
            "available_qualities"
        ][quality]
        drug_data_market: Dict[str, Any] = self.drug_market_data[drug_name]
        temp_drug: Drug = Drug(
            drug_name.value,
            drug_data_market["tier"],
            drug_data_market["base_buy_price"],
            drug_data_market["base_sell_price"],
            quality,
        )
        base_price: float = drug_data_market["base_sell_price"]
        quality_mult: float = temp_drug.get_quality_multiplier("sell")
        player_mod: float = drug_data_market["player_sell_impact_modifier"]
        rival_mod: float = drug_data_market["rival_supply_modifier"]
        calculated_price: float = base_price * quality_mult * player_mod * rival_mod

        current_previous_sell: Optional[float] = drug_data_quality.get(
            "previous_sell_price"
        )
        if (
            current_previous_sell is None
            or abs(current_previous_sell - calculated_price) > 1e-2
        ):
            drug_data_quality["previous_sell_price"] = calculated_price

        crash_event_applied: bool = False
        for event in self.active_market_events:  # event is MarketEvent
            if (
                event.event_type == EventType.DRUG_MARKET_CRASH
                and event.target_drug_name == drug_name
                and event.target_quality == quality
                and hasattr(event, "price_reduction_factor")
                and event.price_reduction_factor is not None
                and hasattr(event, "minimum_price_after_crash")
                and event.minimum_price_after_crash is not None
            ):
                calculated_price *= event.price_reduction_factor
                calculated_price = max(
                    calculated_price, event.minimum_price_after_crash
                )
                crash_event_applied = True
                break

        if not crash_event_applied:
            for event in self.active_market_events:  # event is MarketEvent
                if (
                    event.event_type == EventType.DEMAND_SPIKE
                    and event.target_drug_name == drug_name
                    and event.target_quality == quality
                ):
                    if event.sell_price_multiplier != 1.0:
                        calculated_price *= event.sell_price_multiplier
                    break
        return round(max(0, calculated_price), 2)

    def get_available_stock(
        self,
        drug_name: DrugName,
        quality: DrugQuality,
        game_state_instance: "GameState",
    ) -> int:
        """
        Calculates the currently available stock for a specific drug and quality.

        Considers base stock and effects from player's heat level (for Tier 2/3 drugs)
        and active market events like Supply Disruption.

        Args:
            drug_name: The DrugName enum of the drug.
            quality: The DrugQuality enum of the drug.
            game_state_instance: The current GameState object, used to access player heat.
                                 Note: This dependency might be refactored in the future
                                 if only player heat is needed.

        Returns:
            The calculated available stock (int).
        """
        if (
            drug_name not in self.drug_market_data
            or quality
            not in self.drug_market_data[drug_name].get("available_qualities", {})
        ):
            return 0

        player_heat: int = 0
        # Safely access player_inventory and then heat attribute
        if (
            hasattr(game_state_instance, "player_inventory")
            and game_state_instance.player_inventory is not None
            and hasattr(game_state_instance.player_inventory, "heat")
        ):
            player_heat = game_state_instance.player_inventory.heat
        else:
            # This warning helps identify if GameState or PlayerInventory is not structured as expected.
            print(
                f"Warning: Player heat not accessible via game_state_instance in Region.get_available_stock for {self.name.value}"
            )

        base_stock: int = self.drug_market_data[drug_name]["available_qualities"][
            quality
        ].get("quantity_available", 0)
        modified_stock: int = base_stock
        drug_tier: Optional[int] = self.drug_market_data[drug_name].get("tier")

        if drug_tier is not None and drug_tier in [
            2,
            3,
        ]:  # Tier 2 and 3 drugs affected by heat based stock reduction
            reduction_multiplier_heat: float = (
                self._get_heat_stock_reduction_factor()
            )  # Uses self.current_heat (regional heat)
            # The original code used player_heat here. Clarified to use regional heat as per _get_heat_stock_reduction_factor.
            # If player_heat should be used, _get_heat_stock_reduction_factor needs player_heat as arg.
            # For now, assuming regional heat is intended for regional stock availability.
            modified_stock = math.floor(modified_stock * reduction_multiplier_heat)
            modified_stock = max(0, modified_stock)

        for event in self.active_market_events:
            if (
                event.event_type == EventType.SUPPLY_DISRUPTION
                and event.target_drug_name == drug_name
                and event.target_quality == quality
                and event.stock_reduction_factor is not None
                and event.min_stock_after_event is not None
            ):
                modified_stock = int(
                    float(modified_stock) * event.stock_reduction_factor
                )
                modified_stock = max(modified_stock, event.min_stock_after_event)
        return modified_stock

    def update_stock_on_buy(
        self, drug_name: DrugName, quality: DrugQuality, quantity_bought: int
    ) -> None:
        """
        Updates the stock of a drug in the market after the player buys.

        Args:
            drug_name: The DrugName enum of the drug bought.
            quality: The DrugQuality enum of the drug.
            quantity_bought: The quantity the player bought.
        """
        if (
            drug_name not in self.drug_market_data
            or quality
            not in self.drug_market_data[drug_name].get("available_qualities", {})
        ):
            return
        stock_data: Dict[str, Any] = self.drug_market_data[drug_name][
            "available_qualities"
        ][quality]
        current_qty: int = stock_data.get("quantity_available", 0)
        stock_data["quantity_available"] = max(0, current_qty - quantity_bought)

    def update_stock_on_sell(
        self, drug_name: DrugName, quality: DrugQuality, quantity: int
    ) -> None:
        """
        Updates the stock of a drug in the market after the player sells.
        Note: This might represent the market absorbing the sold drugs, not necessarily
        increasing stock available for player to buy again immediately. Market dynamics
        might differ based on game design for player sales vs. market restock.

        Args:
            drug_name: The DrugName enum of the drug sold.
            quality: The DrugQuality enum of the drug.
            quantity: The quantity the player sold.
        """
        if drug_name in self.drug_market_data and quality in self.drug_market_data[
            drug_name
        ].get("available_qualities", {}):
            stock_data: Dict[str, Any] = self.drug_market_data[drug_name][
                "available_qualities"
            ][quality]
            current_qty: int = stock_data.get("quantity_available", 0)
            # Current logic decreases stock on player sell. This might represent market "absorbing capacity"
            # or could be changed to increase stock if design implies player sells *to* the market stock.
            stock_data["quantity_available"] = max(0, current_qty - quantity)

    def restock_market(self) -> None:
        """
        Restocks the drug market for the region.

        Resets drug quantities to their default random ranges.
        Also applies effects of CHEAP_STASH events and primes previous prices
        if they haven't been set yet.
        """
        for (
            drug_name_enum,
            drug_data_market_val,
        ) in (
            self.drug_market_data.items()
        ):  # drug_name_enum is DrugName, drug_data_market_val is Dict[str,Any]
            tier: Optional[int] = drug_data_market_val.get("tier")

            if tier is None:
                continue  # Should not happen if initialized correctly

            available_qualities_dict: Dict[DrugQuality, Dict[str, Any]] = (
                drug_data_market_val.get("available_qualities", {})
            )

            for quality_enum_member, drug_data_quality_val in list(
                available_qualities_dict.items()
            ):  # quality_enum_member is DrugQuality, drug_data_quality_val is Dict[str,Any]
                current_stock: int = 0
                if tier == 1 and quality_enum_member == DrugQuality.STANDARD:
                    current_stock = TIER1_STANDARD_INITIAL_STOCK
                elif tier > 1:
                    if quality_enum_member == DrugQuality.PURE:
                        current_stock = random.randint(*TIER_GT1_PURE_STOCK_RANGE)
                    elif quality_enum_member == DrugQuality.STANDARD:
                        current_stock = random.randint(*TIER_GT1_STANDARD_STOCK_RANGE)
                    else: # CUT
                        current_stock = random.randint(*TIER_GT1_CUT_STOCK_RANGE)

                for event in self.active_market_events:  # event is MarketEvent
                    if (
                        event.event_type == EventType.CHEAP_STASH
                        and event.target_drug_name == drug_name_enum
                        and event.target_quality == quality_enum_member
                        and event.temporary_stock_increase is not None
                    ):
                        current_stock += event.temporary_stock_increase
                        break

                drug_data_quality_val["quantity_available"] = max(0, current_stock)

        for drug_name_enum, drug_data_market_val in self.drug_market_data.items():
            available_qualities_dict_restock: Dict[DrugQuality, Dict[str, Any]] = (
                drug_data_market_val.get("available_qualities", {})
            )
            for (
                quality_enum_member,
                drug_data_quality_val_restock,
            ) in available_qualities_dict_restock.items():
                if drug_data_quality_val_restock.get("previous_buy_price") is None:
                    drug_data_quality_val_restock["previous_buy_price"] = (
                        self.get_buy_price(drug_name_enum, quality_enum_member)
                    )
                if drug_data_quality_val_restock.get("previous_sell_price") is None:
                    drug_data_quality_val_restock["previous_sell_price"] = (
                        self.get_sell_price(drug_name_enum, quality_enum_member)
                    )
