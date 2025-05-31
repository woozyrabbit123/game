import random
from typing import Dict, List, Optional

from .enums import DrugQuality, DrugName # Added DrugName
from .drug import Drug
from .market_event import MarketEvent
from ..game_configs import (HEAT_PRICE_INCREASE_THRESHOLDS, 
                         HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3)


class Region:
    def __init__(self, name: str):
        self.name = name
        self.drug_market_data: Dict[str, Dict] = {}
        self.active_market_events: List[MarketEvent] = []
        self.current_heat: int = 0

    def modify_heat(self, amount: int):
        self.current_heat += amount
        self.current_heat = max(0, self.current_heat)

    def initialize_drug_market(self, drug_name: str, base_buy_price: float,
                              base_sell_price: float, tier: int,
                              initial_stocks: Optional[Dict[DrugQuality, int]] = None):
        self.drug_market_data[drug_name] = {
            "base_buy_price": base_buy_price,
            "base_sell_price": base_sell_price,
            "tier": tier,
            "player_buy_impact_modifier": 1.0,
            "player_sell_impact_modifier": 1.0,
            "rival_demand_modifier": 1.0,
            "rival_supply_modifier": 1.0,
            "last_rival_activity_turn": -1,
            "available_qualities": {}
        }
        drug_data = self.drug_market_data[drug_name]
        qualities_to_init = [DrugQuality.STANDARD] if tier == 1 else [DrugQuality.CUT, DrugQuality.STANDARD, DrugQuality.PURE]
        for quality in qualities_to_init:
            stock = 0
            if initial_stocks and quality in initial_stocks: stock = initial_stocks[quality]
            elif tier == 1 and quality == DrugQuality.STANDARD: stock = 10000
            elif tier > 1:
                if quality == DrugQuality.PURE: stock = random.randint(0, 50)
                elif quality == DrugQuality.STANDARD: stock = random.randint(0, 100)
                else: stock = random.randint(0, 200)
            drug_data["available_qualities"][quality] = { "quantity_available": stock, "previous_buy_price": None, "previous_sell_price": None }

    def _get_heat_price_multiplier(self) -> float:
        for threshold, multiplier in sorted(HEAT_PRICE_INCREASE_THRESHOLDS.items(), reverse=True):
            if self.current_heat >= threshold: return multiplier
        return 1.0

    def _get_heat_stock_reduction_factor(self) -> float:
        for threshold, factor in sorted(HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3.items(), reverse=True):
            if self.current_heat >= threshold: return factor
        return 1.0

    def get_buy_price(self, drug_name: str, quality: DrugQuality) -> float:
        if drug_name not in self.drug_market_data or quality not in self.drug_market_data[drug_name]["available_qualities"]: return 0.0
        drug_data_quality = self.drug_market_data[drug_name]["available_qualities"][quality]
        drug_data_market = self.drug_market_data[drug_name]
        if drug_data_quality["quantity_available"] <= 0:
            is_event_driven_price = False
            for event in self.active_market_events:
                if event.target_drug_name == drug_name and event.target_quality == quality and event.event_type == "DEMAND_SPIKE": is_event_driven_price = True; break
            if not is_event_driven_price: return 0.0
        temp_drug = Drug(drug_name, drug_data_market["tier"], drug_data_market["base_buy_price"], drug_data_market["base_sell_price"], quality)
        base_price = drug_data_market["base_buy_price"]; quality_mult = temp_drug.get_quality_multiplier("buy")
        player_mod = drug_data_market["player_buy_impact_modifier"]; rival_mod = drug_data_market["rival_demand_modifier"]
        price_before_event_and_heat = base_price * quality_mult * player_mod * rival_mod
        
        current_previous_buy = drug_data_quality.get("previous_buy_price")
        if current_previous_buy is None or abs(current_previous_buy - price_before_event_and_heat) > 1e-2 : # Update if None or changed
            drug_data_quality["previous_buy_price"] = price_before_event_and_heat

        heat_multiplier = self._get_heat_price_multiplier()
        calculated_price = price_before_event_and_heat * heat_multiplier

        crash_event_applied = False
        # Check for DRUG_MARKET_CRASH first
        for event in self.active_market_events:
            if event.event_type == "DRUG_MARKET_CRASH":
                # Ensure target_drug_name is not None and has a 'value' attribute (like an enum)
                if hasattr(event.target_drug_name, 'value') and \
                   event.target_drug_name.value == drug_name and \
                   event.target_quality == quality and \
                   hasattr(event, 'price_reduction_factor') and event.price_reduction_factor is not None and \
                   hasattr(event, 'minimum_price_after_crash') and event.minimum_price_after_crash is not None:

                    calculated_price *= event.price_reduction_factor
                    calculated_price = max(calculated_price, event.minimum_price_after_crash)
                    crash_event_applied = True
                    break # Crash event handled and takes precedence

        if not crash_event_applied:
            # Apply other general event multipliers if no crash event for this specific drug/quality
            for event in self.active_market_events:
                matches_drug = False
                if hasattr(event.target_drug_name, 'value'): # Enum check
                    if event.target_drug_name.value == drug_name:
                        matches_drug = True
                elif isinstance(event.target_drug_name, str): # String check (for older/other event types)
                    if event.target_drug_name == drug_name:
                        matches_drug = True

                if matches_drug and event.target_quality == quality:
                    # Apply general buy_price_multiplier from other event types
                    if event.buy_price_multiplier != 1.0:
                        calculated_price *= event.buy_price_multiplier
                    # Assuming one relevant non-crash event, or first one found applies.
                    break
        return round(max(0, calculated_price), 2)

    def get_sell_price(self, drug_name: str, quality: DrugQuality) -> float:
        if drug_name not in self.drug_market_data or quality not in self.drug_market_data[drug_name]["available_qualities"]: return 0.0
        drug_data_quality = self.drug_market_data[drug_name]["available_qualities"][quality]
        drug_data_market = self.drug_market_data[drug_name]
        temp_drug = Drug(drug_name, drug_data_market["tier"], drug_data_market["base_buy_price"], drug_data_market["base_sell_price"], quality)
        base_price = drug_data_market["base_sell_price"]; quality_mult = temp_drug.get_quality_multiplier("sell")
        player_mod = drug_data_market["player_sell_impact_modifier"]; rival_mod = drug_data_market["rival_supply_modifier"]
        calculated_price = base_price * quality_mult * player_mod * rival_mod
        
        current_previous_sell = drug_data_quality.get("previous_sell_price")
        if current_previous_sell is None or abs(current_previous_sell - calculated_price) > 1e-2:
            drug_data_quality["previous_sell_price"] = calculated_price

        crash_event_applied = False
        # Check for DRUG_MARKET_CRASH first
        for event in self.active_market_events:
            if event.event_type == "DRUG_MARKET_CRASH":
                if hasattr(event.target_drug_name, 'value') and \
                   event.target_drug_name.value == drug_name and \
                   event.target_quality == quality and \
                   hasattr(event, 'price_reduction_factor') and event.price_reduction_factor is not None and \
                   hasattr(event, 'minimum_price_after_crash') and event.minimum_price_after_crash is not None:

                    calculated_price *= event.price_reduction_factor
                    calculated_price = max(calculated_price, event.minimum_price_after_crash)
                    crash_event_applied = True
                    break # Crash event handled and takes precedence

        if not crash_event_applied:
            # Apply other general event multipliers if no crash event for this specific drug/quality
            for event in self.active_market_events:
                matches_drug = False
                if hasattr(event.target_drug_name, 'value'): # Enum check
                    if event.target_drug_name.value == drug_name:
                        matches_drug = True
                elif isinstance(event.target_drug_name, str): # String check
                    if event.target_drug_name == drug_name:
                        matches_drug = True

                if matches_drug and event.target_quality == quality:
                    # Apply general sell_price_multiplier from other event types
                    if event.sell_price_multiplier != 1.0:
                        calculated_price *= event.sell_price_multiplier
                    # Assuming one relevant non-crash event, or first one found applies.
                    break
        return round(max(0, calculated_price), 2)

    def get_available_stock(self, drug_name: str, quality: DrugQuality) -> int:
        if (drug_name not in self.drug_market_data or
            quality not in self.drug_market_data[drug_name]["available_qualities"]):
            return 0

        # Base stock after restock_market (which includes heat effects and CHEAP_STASH)
        base_stock = self.drug_market_data[drug_name]["available_qualities"][quality]["quantity_available"]

        # Apply SUPPLY_CHAIN_DISRUPTION if active
        for event in self.active_market_events:
            if event.event_type == "SUPPLY_CHAIN_DISRUPTION" and \
               event.target_drug_name == drug_name and \
               event.target_quality == quality and \
               hasattr(event, 'stock_reduction_factor') and event.stock_reduction_factor is not None and \
               hasattr(event, 'min_stock_after_event') and event.min_stock_after_event is not None:

                # Apply the reduction factor
                modified_stock = int(base_stock * event.stock_reduction_factor)
                # Ensure stock does not go below the event's specified minimum
                final_stock = max(modified_stock, event.min_stock_after_event)
                return final_stock # Event applies, return modified stock

        return base_stock # No relevant supply disruption event, return base stock

    def update_stock_on_buy(self, drug_name: str, quality: DrugQuality, quantity_bought: int):
        if (drug_name not in self.drug_market_data or quality not in self.drug_market_data[drug_name]["available_qualities"]): return
        stock_data = self.drug_market_data[drug_name]["available_qualities"][quality]; stock_data["quantity_available"] = max(0, stock_data["quantity_available"] - quantity_bought)

    def restock_market(self):
        for drug_name, drug_data_market in self.drug_market_data.items():
            tier = drug_data_market["tier"]
            for quality_enum_member, drug_data_quality in list(drug_data_market.get("available_qualities", {}).items()):
                current_stock = 0
                if tier == 1 and quality_enum_member == DrugQuality.STANDARD: current_stock = 10000
                elif tier > 1 :
                    if quality_enum_member == DrugQuality.PURE: current_stock = random.randint(10, 100)
                    elif quality_enum_member == DrugQuality.STANDARD: current_stock = random.randint(20, 200)
                    else: current_stock = random.randint(30, 300)
                if tier > 1: current_stock = int(current_stock * self._get_heat_stock_reduction_factor())

                # Apply CHEAP_STASH if active - this adds to the heat-adjusted base stock
                for event in self.active_market_events:
                    if event.event_type == "CHEAP_STASH" and \
                       event.target_drug_name == drug_name and \
                       event.target_quality == quality_enum_member and \
                       event.temporary_stock_increase is not None:
                        current_stock += event.temporary_stock_increase
                        break # Assuming only one CHEAP_STASH event can apply per drug/quality

                drug_data_quality["quantity_available"] = max(0, current_stock)

        for drug_name, drug_data_market in self.drug_market_data.items():
            for quality_enum_member, drug_data_quality in drug_data_market.get("available_qualities", {}).items():
                # Prime previous prices with current prices after restock if they are still None
                if drug_data_quality["previous_buy_price"] is None:
                    drug_data_quality["previous_buy_price"] = self.get_buy_price(drug_name, quality_enum_member)
                if drug_data_quality["previous_sell_price"] is None:
                    drug_data_quality["previous_sell_price"] = self.get_sell_price(drug_name, quality_enum_member)