"""
Defines the Region class, representing a geographical area in the game.

Each region has its own drug market, heat level, and can host various
market events.
"""
import math
import random
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

# Third-party imports would go here if any (none currently)

# Local application imports
from .. import narco_configs # Modified to import module
from .drug import Drug
from .enums import DrugName, DrugQuality, EventType, RegionName, SkillID # Added SkillID
from .market_event import MarketEvent


if TYPE_CHECKING:
    from ..game_state import GameState  # noqa: F401 - Used for type hinting


class Region:
    # Note: player_inventory is passed to get_buy_price and get_sell_price for skill checks.
    # game_state will now also be passed for seasonal event checks.
    """
    Represents a distinct geographical region in the game world.

    Each region has its own drug market, heat level, and active market events.
    Player can travel between regions, with each offering different drug prices
    and availability.

    Attributes:
        name: Enum representing the name of this region.
        drug_market_data: Data for drugs in this region's market.
                          Keys are DrugName enums. Inner dict contains base prices,
                          tier, modifiers, and available qualities.
        active_market_events: List of MarketEvent objects active in this region.
        current_heat: Current police attention (heat) level in this region.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a Region instance.

        Args:
            name: String name of the region, converted to RegionName enum.
        """
        self.name: RegionName = RegionName(name) if isinstance(name, str) else name
        self.drug_market_data: Dict[DrugName, Dict[str, Any]] = {}
        self.active_market_events: List[MarketEvent] = []
        self.current_heat: int = 0

    def modify_heat(self, amount: int) -> None:
        """
        Modifies the current heat level of the region. Heat cannot go < 0.

        Args:
            amount: Amount to change heat by (can be negative).
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
        Initializes/updates a drug in the region's market.

        Sets base prices, tier, impact modifiers, and initial stock for its
        available qualities.

        Args:
            drug_name: DrugName enum or string name of the drug.
            base_buy_price: Base price for buying this drug.
            base_sell_price: Base price for selling this drug.
            tier: Tier of the drug (1-4).
            initial_stocks: Optional dict of initial stock quantities for
                            different DrugQuality levels.
        """
        drug_name_enum = (
            DrugName(drug_name) if isinstance(drug_name, str) else drug_name
        )
        self.drug_market_data[drug_name_enum] = {
            'base_buy_price': base_buy_price,
            'base_sell_price': base_sell_price,
            'tier': tier,
            'player_buy_impact_modifier': 1.0,
            'player_sell_impact_modifier': 1.0,
            'rival_demand_modifier': 1.0,
            'rival_supply_modifier': 1.0,
            'last_rival_activity_turn': -1,
            'available_qualities': {},
        }
        drug_data = self.drug_market_data[drug_name_enum]
        qualities_to_init = (
            [DrugQuality.STANDARD]
            if tier == 1
            else [DrugQuality.CUT, DrugQuality.STANDARD, DrugQuality.PURE]
        )

        for quality_enum_member in qualities_to_init:
            stock = 0
            if initial_stocks and quality_enum_member in initial_stocks:
                stock = initial_stocks[quality_enum_member]
            elif tier == 1 and quality_enum_member == DrugQuality.STANDARD:
                stock = narco_configs.TIER1_STANDARD_INITIAL_STOCK
            elif tier > 1:
                if quality_enum_member == DrugQuality.PURE:
                    stock = random.randint(*narco_configs.TIER_GT1_PURE_STOCK_RANGE)
                elif quality_enum_member == DrugQuality.STANDARD:
                    stock = random.randint(*narco_configs.TIER_GT1_STANDARD_STOCK_RANGE)
                else:  # CUT
                    stock = random.randint(*narco_configs.TIER_GT1_CUT_STOCK_RANGE)

            drug_data['available_qualities'][quality_enum_member] = {
                'quantity_available': stock,
                'previous_buy_price': None,
                'previous_sell_price': None,
            }

    def _get_heat_price_multiplier(self) -> float:
        """Calculates price multiplier based on current regional heat."""
        for threshold, multiplier in sorted(
            narco_configs.HEAT_PRICE_INCREASE_THRESHOLDS.items(), reverse=True
        ):
            if self.current_heat >= threshold:
                return multiplier
        return 1.0

    def _get_heat_stock_reduction_factor(self) -> float:
        """Calculates stock reduction factor from heat for Tier 2/3 drugs."""
        for threshold, factor in sorted(
            narco_configs.HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3.items(), reverse=True
        ):
            if self.current_heat >= threshold:
                return factor
        return 1.0

    def get_buy_price(self, drug_name: DrugName, quality: DrugQuality, player_inventory: Optional[Any] = None, game_state: Optional["GameState"] = None) -> float: # Add game_state
        """
        Calculates current buy price for a drug/quality in this region.

        Considers base price, quality, player/rival impact, heat, events, player skills, and seasonal events.

        Args:
            drug_name: The DrugName of the drug.
            quality: The DrugQuality of the drug.
            player_inventory: Player's inventory, to check for skills. Optional for compatibility.
            game_state: Current game state, to check for seasonal event effects. Optional for compatibility.

        Returns:
            Calculated current buy price. Returns 0.0 if not available.
        """
        market_data = self.drug_market_data.get(drug_name)
        if not market_data or quality not in market_data.get('available_qualities', {}):
            return 0.0

        quality_data = market_data['available_qualities'][quality]

        # If quantity is zero, only event-driven prices allow buying
        if quality_data.get('quantity_available', 0) <= 0:
            event_driven_price = False
            for event in self.active_market_events:
                if (event.event_type == EventType.DEMAND_SPIKE and
                        event.target_drug_name == drug_name and
                        event.target_quality == quality):
                    event_driven_price = True
                    break
            if not event_driven_price:
                return 0.0

        temp_drug = Drug(
            drug_name.value, market_data['tier'],
            market_data['base_buy_price'], market_data['base_sell_price'],
            quality
        )
        
        base_price = market_data.get('base_buy_price')
        if base_price is None:  # Should not happen with proper initialization
            print(f'Error: Drug {drug_name.value} in {self.name.value} '
                  f'missing base_buy_price.')
            return 0.0

        quality_mult = temp_drug.get_quality_multiplier('buy')
        player_mod = market_data.get('player_buy_impact_modifier', 1.0)
        rival_mod = market_data.get('rival_demand_modifier', 1.0)
        price_before_event_heat = base_price * quality_mult * player_mod * rival_mod

        # Store price before heat and general events for trend calculation
        current_prev_buy = quality_data.get('previous_buy_price')
        if current_prev_buy is None or \
           abs(current_prev_buy - price_before_event_heat) > 1e-2:
            quality_data['previous_buy_price'] = price_before_event_heat

        heat_mult = self._get_heat_price_multiplier()
        calculated_price = price_before_event_heat * heat_mult

        # Apply Black Market event first if active (overrides other price mods)
        for event in self.active_market_events:
            if (event.event_type == EventType.BLACK_MARKET_OPPORTUNITY and
                    event.target_drug_name == drug_name and
                    event.target_quality == quality and
                    getattr(event, 'black_market_quantity_available', 0) > 0 and
                    event.duration_remaining_days > 0):
                # Ensure buy_price_multiplier is valid
                buy_mult = getattr(event, 'buy_price_multiplier', 1.0)
                return round(max(0, calculated_price * buy_mult), 2)

        # Apply general price-modifying events (Crash, Demand Spike, Cheap Stash)
        # Note: CRASH should probably take precedence or be exclusive.
        crash_event_applied = False
        for event in self.active_market_events:
            if (event.event_type == EventType.DRUG_MARKET_CRASH and
                    event.target_drug_name == drug_name and
                    event.target_quality == quality and
                    event.price_reduction_factor is not None and
                    event.minimum_price_after_crash is not None):
                calculated_price *= event.price_reduction_factor
                calculated_price = max(calculated_price,
                                       event.minimum_price_after_crash)
                crash_event_applied = True
                break  # Assuming only one crash event applies

        if not crash_event_applied:
            for event in self.active_market_events:
                if ((event.event_type == EventType.DEMAND_SPIKE or
                     event.event_type == EventType.CHEAP_STASH) and
                        event.target_drug_name == drug_name and
                        event.target_quality == quality and
                        event.buy_price_multiplier != 1.0):
                    calculated_price *= event.buy_price_multiplier
                    break  # Assuming one such event is dominant

        # Apply Street Smarts skill effects for buying (player gets a discount)
        if player_inventory and hasattr(player_inventory, 'unlocked_skills'):
            price_modifier_buy = 0.0
            if SkillID.ADVANCED_MARKET_ANALYSIS.value in player_inventory.unlocked_skills:
                skill_effect = narco_configs.SKILL_DEFINITIONS[SkillID.ADVANCED_MARKET_ANALYSIS].get('effect_value', 0.0)
                if isinstance(skill_effect, (float, int)): price_modifier_buy += skill_effect
            if SkillID.MASTER_NEGOTIATOR.value in player_inventory.unlocked_skills:
                skill_effect = narco_configs.SKILL_DEFINITIONS[SkillID.MASTER_NEGOTIATOR].get('effect_value', 0.0)
                if isinstance(skill_effect, (float, int)): price_modifier_buy += skill_effect
            
            if price_modifier_buy > 0:
                calculated_price *= (1.0 - price_modifier_buy)

        # Apply Seasonal Event effects for drug buy prices
        if game_state and game_state.seasonal_event_effects_active:
            buy_price_effects = game_state.seasonal_event_effects_active.get("drug_price_buy_multiplier", {})
            drug_specific_mult = buy_price_effects.get(drug_name.value) # Check for specific drug
            all_drugs_mult = buy_price_effects.get("ALL") # Check for "ALL" drugs

            if drug_specific_mult is not None:
                calculated_price *= drug_specific_mult
            elif all_drugs_mult is not None:
                calculated_price *= all_drugs_mult

        # Apply Turf War effects for drug buy prices
        if game_state and self.name in game_state.active_turf_wars:
            war_data = game_state.active_turf_wars[self.name]
            for affected_drug_detail in war_data.get("affected_drugs", []):
                if affected_drug_detail["drug_name"] == drug_name:
                    calculated_price *= affected_drug_detail.get("turf_war_buy_price_factor", 1.0)
                    break 
                
        return round(max(0, calculated_price), 2)

    def get_sell_price(self, drug_name: DrugName, quality: DrugQuality, player_inventory: Optional[Any] = None, game_state: Optional["GameState"] = None) -> float: # Add game_state
        """
        Calculates current sell price for a drug/quality in this region.

        Considers base price, quality, player/rival impact, events, player skills, and seasonal events.
        Heat typically doesn't directly affect player's sell price here.

        Args:
            drug_name: The DrugName of the drug.
            quality: The DrugQuality of the drug.
            player_inventory: Player's inventory, to check for skills. Optional for compatibility.
            game_state: Current game state, to check for seasonal event effects. Optional for compatibility.

        Returns:
            Calculated current sell price. Returns 0.0 if not sellable.
        """
        market_data = self.drug_market_data.get(drug_name)
        if not market_data or quality not in market_data.get('available_qualities', {}):
            return 0.0

        quality_data = market_data['available_qualities'][quality]

        temp_drug = Drug(
            drug_name.value, market_data['tier'],
            market_data['base_buy_price'], market_data['base_sell_price'],
            quality
        )

        base_price = market_data.get('base_sell_price')
        if base_price is None:  # Should not happen
            print(f'Error: Drug {drug_name.value} in {self.name.value} '
                  f'missing base_sell_price.')
            return 0.0

        quality_mult = temp_drug.get_quality_multiplier('sell')
        player_mod = market_data.get('player_sell_impact_modifier', 1.0)
        rival_mod = market_data.get('rival_supply_modifier', 1.0)
        calculated_price = base_price * quality_mult * player_mod * rival_mod

        # Store price before general events for trend calculation
        current_prev_sell = quality_data.get('previous_sell_price')
        if current_prev_sell is None or \
           abs(current_prev_sell - calculated_price) > 1e-2:
            quality_data['previous_sell_price'] = calculated_price

        crash_event_applied = False
        for event in self.active_market_events:
            if (event.event_type == EventType.DRUG_MARKET_CRASH and
                    event.target_drug_name == drug_name and
                    event.target_quality == quality and
                    event.price_reduction_factor is not None and
                    event.minimum_price_after_crash is not None):
                calculated_price *= event.price_reduction_factor
                calculated_price = max(calculated_price,
                                       event.minimum_price_after_crash)
                crash_event_applied = True
                break

        if not crash_event_applied:
            for event in self.active_market_events:
                if (event.event_type == EventType.DEMAND_SPIKE and
                        event.target_drug_name == drug_name and
                        event.target_quality == quality and
                        event.sell_price_multiplier != 1.0):
                    calculated_price *= event.sell_price_multiplier
                    break

        # Apply Street Smarts skill effects for selling (player gets a bonus)
        if player_inventory and hasattr(player_inventory, 'unlocked_skills'):
            price_modifier_sell = 0.0
            if SkillID.ADVANCED_MARKET_ANALYSIS.value in player_inventory.unlocked_skills:
                skill_effect = narco_configs.SKILL_DEFINITIONS[SkillID.ADVANCED_MARKET_ANALYSIS].get('effect_value', 0.0)
                if isinstance(skill_effect, (float, int)): price_modifier_sell += skill_effect
            if SkillID.MASTER_NEGOTIATOR.value in player_inventory.unlocked_skills:
                skill_effect = narco_configs.SKILL_DEFINITIONS[SkillID.MASTER_NEGOTIATOR].get('effect_value', 0.0)
                if isinstance(skill_effect, (float, int)): price_modifier_sell += skill_effect

            if price_modifier_sell > 0:
                calculated_price *= (1.0 + price_modifier_sell)

        # Apply Seasonal Event effects for drug sell prices
        if game_state and game_state.seasonal_event_effects_active:
            sell_price_effects = game_state.seasonal_event_effects_active.get("drug_price_sell_multiplier", {})
            drug_specific_mult = sell_price_effects.get(drug_name.value)
            all_drugs_mult = sell_price_effects.get("ALL")

            if drug_specific_mult is not None:
                calculated_price *= drug_specific_mult
            elif all_drugs_mult is not None:
                calculated_price *= all_drugs_mult

        # Apply Turf War effects for drug sell prices
        if game_state and self.name in game_state.active_turf_wars:
            war_data = game_state.active_turf_wars[self.name]
            for affected_drug_detail in war_data.get("affected_drugs", []):
                if affected_drug_detail["drug_name"] == drug_name:
                    calculated_price *= affected_drug_detail.get("turf_war_sell_price_factor", 1.0)
                    break

        return round(max(0, calculated_price), 2)

    def get_available_stock( # Signature changed to accept game_state directly
        self,
        drug_name: DrugName,
        quality: DrugQuality,
        game_state: Optional["GameState"], # Changed from game_state_instance to game_state
    ) -> int:
        """
        Calculates available stock for a drug/quality.

        Considers base stock, regional heat (for Tier 2/3 drugs), 
        Supply Disruption events, and Turf Wars.

        Args:
            drug_name: DrugName of the drug.
            quality: DrugQuality of the drug.
            game_state: Current GameState object, for seasonal/turf war effects.

        Returns:
            Calculated available stock (int).
        """
        market_data = self.drug_market_data.get(drug_name)
        if not market_data or quality not in market_data.get('available_qualities', {}):
            return 0

        # The F841 warning for player_heat: player_heat is not used in this version
        # of the logic, which relies on regional heat via
        # _get_heat_stock_reduction_factor. If player_heat were to be used,
        # this section would need to be revised. For now, direct assignment is removed.
        # player_heat = 0
        # if hasattr(game_state_instance, 'player_inventory') and \
        #    game_state_instance.player_inventory is not None and \
        #    hasattr(game_state_instance.player_inventory, 'heat'):
        #     player_heat = game_state_instance.player_inventory.heat
        # else:
        #     print(
        #         f'Warning: Player heat not accessible in '
        #         f'Region.get_available_stock for {self.name.value}'
        #     )

        base_stock = market_data['available_qualities'][quality].get(
            'quantity_available', 0
        )
        modified_stock = float(base_stock)  # Start with float for multipliers
        drug_tier = market_data.get('tier')

        if drug_tier is not None and drug_tier in [2, 3]:
            # Uses self.current_heat (regional heat)
            reduction_multiplier_heat = self._get_heat_stock_reduction_factor()
            modified_stock *= reduction_multiplier_heat

        modified_stock = math.floor(modified_stock)  # Convert to int after multipliers

        for event in self.active_market_events:
            if (event.event_type == EventType.SUPPLY_DISRUPTION and
                    event.target_drug_name == drug_name and
                    event.target_quality == quality and
                    event.stock_reduction_factor is not None and
                    event.min_stock_after_event is not None):
                modified_stock = math.floor(
                    modified_stock * event.stock_reduction_factor
                )
                modified_stock = max(modified_stock,
                                       event.min_stock_after_event)
        
        # Apply Turf War effects for drug availability
        if game_state and self.name in game_state.active_turf_wars:
            war_data = game_state.active_turf_wars[self.name]
            for affected_drug_detail in war_data.get("affected_drugs", []):
                if affected_drug_detail["drug_name"] == drug_name:
                    modified_stock *= affected_drug_detail.get("turf_war_availability_factor", 1.0)
                    break
                    
        return max(0, int(math.floor(modified_stock))) # Ensure floor before int conversion

    def update_stock_on_buy(
        self, drug_name: DrugName, quality: DrugQuality, quantity_bought: int
    ) -> None:
        """
        Updates drug stock in market after player buys.

        Args:
            drug_name: DrugName of the drug bought.
            quality: DrugQuality of the drug.
            quantity_bought: Quantity player bought.
        """
        market_data = self.drug_market_data.get(drug_name)
        if not market_data or quality not in market_data.get('available_qualities', {}):
            return

        stock_data = market_data['available_qualities'][quality]
        current_qty = stock_data.get('quantity_available', 0)
        stock_data['quantity_available'] = max(0, current_qty - quantity_bought)

    def update_stock_on_sell(
        self, drug_name: DrugName, quality: DrugQuality, quantity: int
    ) -> None:
        """
        Updates drug stock in market after player sells.
        Note: Market dynamics might differ for player sales vs restock.

        Args:
            drug_name: DrugName of the drug sold.
            quality: DrugQuality of the drug.
            quantity: Quantity player sold.
        """
        market_data = self.drug_market_data.get(drug_name)
        if not market_data or quality not in market_data.get('available_qualities', {}):
            return

        stock_data = market_data['available_qualities'][quality]
        current_qty = stock_data.get('quantity_available', 0)
        # Current logic: player selling reduces available market stock.
        # This might represent market "absorbing" capacity or a temporary removal.
        stock_data['quantity_available'] = max(0, current_qty - quantity)

    def restock_market(self) -> None:
        """
        Restocks the drug market for the region.

        Resets drug quantities to default random ranges, applies CHEAP_STASH
        event effects, and primes previous prices if not set.
        """
        for drug_name_enum, drug_market_data_val in self.drug_market_data.items():
            tier = drug_market_data_val.get('tier')
            if tier is None:
                continue

            available_qualities = drug_market_data_val.get('available_qualities', {})
            for quality_enum, quality_data in list(available_qualities.items()):
                current_stock = 0
                if tier == 1 and quality_enum == DrugQuality.STANDARD:
                    current_stock = narco_configs.TIER1_STANDARD_INITIAL_STOCK
                elif tier > 1:
                    if quality_enum == DrugQuality.PURE:
                        current_stock = random.randint(*narco_configs.TIER_GT1_PURE_STOCK_RANGE)
                    elif quality_enum == DrugQuality.STANDARD:
                        current_stock = random.randint(*narco_configs.TIER_GT1_STANDARD_STOCK_RANGE)
                    else:  # CUT
                        current_stock = random.randint(*narco_configs.TIER_GT1_CUT_STOCK_RANGE)

                # Apply CHEAP_STASH event modifications
                for event in self.active_market_events:
                    if (event.event_type == EventType.CHEAP_STASH and
                            event.target_drug_name == drug_name_enum and
                            event.target_quality == quality_enum and
                            event.temporary_stock_increase is not None):
                        current_stock += event.temporary_stock_increase
                        break

                quality_data['quantity_available'] = max(0, current_stock)

        # Prime previous prices if they haven't been set (e.g., first turn)
        for drug_name_enum, drug_market_data_val in self.drug_market_data.items():
            available_qualities = drug_market_data_val.get('available_qualities', {})
            for quality_enum, quality_data in available_qualities.items():
                if quality_data.get('previous_buy_price') is None:
                    quality_data['previous_buy_price'] = self.get_buy_price(
                        drug_name_enum, quality_enum
                    )
                if quality_data.get('previous_sell_price') is None:
                    quality_data['previous_sell_price'] = self.get_sell_price(
                        drug_name_enum, quality_enum
                    )
