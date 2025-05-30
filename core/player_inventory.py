from typing import Dict, List, Optional
from .enums import DrugQuality
from game_configs import INFORMANT_MAX_TRUST

class PlayerInventory:
    def __init__(self, max_capacity: int, starting_cash: float):
        self.items: Dict[str, Dict[DrugQuality, int]] = {}
        self.max_capacity = max_capacity
        self.current_load = 0
        self.cash = starting_cash
        self.capacity_upgrades_purchased: int = 0
        self.skill_points: int = 0
        self.unlocked_skills: List[str] = [] 
        self.informant_trust: int = 0
        self.crypto_wallet: Dict[str, float] = {}
        self.staked_dc: float = 0.0
        self.pending_laundered_sc: float = 0.0
        self.pending_laundered_sc_arrival_day: Optional[int] = None
        self.has_secure_phone: bool = False

    def _recalculate_current_load(self):
        total = 0
        for qualities in self.items.values():
            for quantity in qualities.values():
                total += quantity
        self.current_load = total

    def add_drug(self, drug_name: str, quality: DrugQuality, quantity_to_add: int) -> bool:
        available_space = self.max_capacity - self.current_load
        if quantity_to_add <= 0:
            return False
        if quantity_to_add > available_space:
            return False
        if drug_name not in self.items:
            self.items[drug_name] = {}
        if quality not in self.items[drug_name]:
            self.items[drug_name][quality] = 0
        self.items[drug_name][quality] += quantity_to_add
        self._recalculate_current_load()
        return True

    def remove_drug(self, drug_name: str, quality: DrugQuality, quantity_to_remove: int) -> bool:
        if quantity_to_remove <= 0:
            return False
        if (drug_name not in self.items or 
            quality not in self.items[drug_name] or 
            self.items[drug_name][quality] < quantity_to_remove):
            return False
        self.items[drug_name][quality] -= quantity_to_remove
        if self.items[drug_name][quality] == 0:
            del self.items[drug_name][quality]
        if not self.items[drug_name]:
            del self.items[drug_name]
        self._recalculate_current_load()
        return True

    def get_quantity(self, drug_name: str, quality: DrugQuality) -> int:
        if drug_name in self.items and quality in self.items[drug_name]:
            return self.items[drug_name][quality]
        return 0

    def get_available_space(self) -> int:
        return self.max_capacity - self.current_load

    def upgrade_capacity(self, additional_capacity: int):
        self.max_capacity += additional_capacity

    def get_inventory_summary(self) -> Dict[str, Dict[DrugQuality, int]]:
        return {
            drug_name: {
                quality: quantity
                for quality, quantity in qualities.items()
            }
            for drug_name, qualities in self.items.items()
        }

    def formatted_summary(self) -> str:
        summary_parts = []
        if not self.items:
            summary_parts.append("Drug Inventory: Empty")
        else:
            inventory_lines = ["Drug Inventory:"]
            for drug_name, qualities in sorted(self.items.items()):
                for quality, quantity in sorted(qualities.items(), key=lambda item: item[0].value):
                    inventory_lines.append(f"  - {drug_name} ({quality.name}): {quantity} units")
            summary_parts.append("\n".join(inventory_lines))

        summary_parts.append(f"\nCash (Street): ${self.cash:.2f}")
        summary_parts.append(f"Carrying: {self.current_load}/{self.max_capacity} units")
        summary_parts.append(f"Skill Points: {self.skill_points}")
        summary_parts.append(f"Informant Trust: {self.informant_trust}/{INFORMANT_MAX_TRUST}")

        crypto_lines = ["\nCrypto Holdings:"]
        wallet_empty = True
        if self.crypto_wallet:
            for coin, amount in sorted(self.crypto_wallet.items()):
                crypto_lines.append(f"  - Wallet {coin}: {amount:.4f}")
                wallet_empty = False
        if self.staked_dc > 0:
            crypto_lines.append(f"  - Staked DC: {self.staked_dc:.4f}")
            wallet_empty = False
        if wallet_empty:
            crypto_lines.append("  - Wallet Empty, Nothing Staked")
        summary_parts.append("\n".join(crypto_lines))

        if self.pending_laundered_sc_arrival_day is not None:
            summary_parts.append(f"\nLaundering Operation: {self.pending_laundered_sc:.4f} SC arriving on Day {self.pending_laundered_sc_arrival_day}.")
        
        special_unlocks = []
        if "GHOST_NETWORK_ACCESS" in self.unlocked_skills:
            special_unlocks.append("Ghost Network Access")
        if "DIGITAL_ARSENAL" in self.unlocked_skills:
            special_unlocks.append("Digital Arsenal")
        if self.has_secure_phone:
            special_unlocks.append("Secure Phone")
        
        if special_unlocks:
            summary_parts.append("\nSpecial Access/Items:")
            for item_name in special_unlocks:
                summary_parts.append(f"  - {item_name}")
        
        return "\n".join(summary_parts)