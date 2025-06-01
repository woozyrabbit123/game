from typing import Dict, List, Optional, Set
from .enums import DrugQuality, DrugName, CryptoCoin, SkillID

class PlayerInventory:
    def __init__(self, max_capacity: int = None, starting_cash: float = None):
        # Use lazy imports to avoid circular dependency
        if max_capacity is None or starting_cash is None:
            from ..game_configs import PLAYER_STARTING_CASH, PLAYER_MAX_CAPACITY
            max_capacity = max_capacity or PLAYER_MAX_CAPACITY
            starting_cash = starting_cash or PLAYER_STARTING_CASH
            
        self.items: Dict[DrugName, Dict[DrugQuality, int]] = {} # Keyed by DrugName enum
        self.max_capacity = max_capacity
        self.current_load = 0
        self.cash = starting_cash
        self.capacity_upgrades_purchased: int = 0 # Reinstated
        self.skill_points: int = 0
        self.unlocked_skills: Set[str] = set() # Use set for efficient add/check
        self.informant_trust: int = 0 # Assuming INFORMANT_MAX_TRUST is used elsewhere for display
        
        self.crypto_wallet: Dict[CryptoCoin, float] = {} # Keyed by CryptoCoin enum
        # Initialize wallet for all known crypto coins
        for coin in CryptoCoin:
            self.crypto_wallet[coin] = 0.0
            
        self.staked_drug_coin: Dict[str, float] = {'staked_amount': 0.0, 'pending_rewards': 0.0} 
        
        self.pending_laundered_sc: float = 0.0
        self.pending_laundered_sc_arrival_day: Optional[int] = None
        
        self.has_secure_phone: bool = False
        self.ghost_network_access: int = 0 # Days of access remaining
        self.heat: int = 0 # Player's overall heat level

        self.debt_payment_1_paid: bool = False
        self.debt_payment_2_paid: bool = False
        self.debt_payment_3_paid: bool = False

    def unlock_skill(self, skill_id_str: str, cost: int) -> bool:
        """Attempts to unlock a skill for the player."""
        if self.skill_points >= cost:
            self.skill_points -= cost
            self.unlocked_skills.add(skill_id_str) # Add string skill ID
            return True
        return False

    def _recalculate_current_load(self):
        total = 0
        for qualities in self.items.values():
            for quantity in qualities.values():
                total += quantity
        self.current_load = total

    def add_drug(self, drug_name: DrugName, quality: DrugQuality, quantity_to_add: int) -> bool:
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

    def remove_drug(self, drug_name: DrugName, quality: DrugQuality, quantity_to_remove: int) -> bool:
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

    def get_drug_item(self, drug_name: DrugName, quality: DrugQuality) -> Optional[Dict]:
        if drug_name in self.items and quality in self.items[drug_name]:
            return {
                "drug_name": drug_name, 
                "quality": quality,   
                "quantity": self.items[drug_name][quality]
            }
        return None

    def get_quantity(self, drug_name: DrugName, quality: DrugQuality) -> int:
        return self.items.get(drug_name, {}).get(quality, 0)

    def get_drug_quantity(self, drug_name: DrugName, quality: DrugQuality) -> int:
        """Return the quantity of a specific drug and quality in inventory."""
        return self.items.get(drug_name, {}).get(quality, 0)

    def add_crypto(self, coin: CryptoCoin, amount: float):
        if amount <= 0: return
        self.crypto_wallet[coin] = self.crypto_wallet.get(coin, 0.0) + amount

    def remove_crypto(self, coin: CryptoCoin, amount: float) -> bool:
        if amount <= 0: return False
        if self.crypto_wallet.get(coin, 0.0) >= amount:
            self.crypto_wallet[coin] -= amount
            return True
        return False

    def get_available_space(self) -> int:
        return self.max_capacity - self.current_load

    def get_inventory_summary(self) -> Dict[DrugName, Dict[DrugQuality, int]]: 
        return self.items 

    def formatted_summary(self) -> str: 
        summary_parts = []
        summary_parts.append(f"Cash: ${self.cash:,.2f}")
        summary_parts.append(f"Load: {self.current_load}/{self.max_capacity}")
        summary_parts.append(f"Heat: {self.heat}") 
        summary_parts.append(f"Skill Points: {self.skill_points}")
        
        drug_lines = ["Drugs:"]
        if self.items:
            for drug, qualities in self.items.items(): 
                for qual, qty in qualities.items(): 
                    drug_lines.append(f"  {drug.value} ({qual.name}): {qty}")
        else:
            drug_lines.append("  None")
        summary_parts.append("\n".join(drug_lines))

        crypto_lines = ["Crypto:"]
        wallet_empty = True
        if self.crypto_wallet:
            for coin, amt in self.crypto_wallet.items(): 
                if amt > 0 : 
                    crypto_lines.append(f"  {coin.value}: {amt:.4f}")
                    wallet_empty = False
        
        if self.staked_drug_coin['staked_amount'] > 0 or self.staked_drug_coin['pending_rewards'] > 0:
            crypto_lines.append(f"  Staked DC: {self.staked_drug_coin['staked_amount']:.4f}")
            if self.staked_drug_coin['pending_rewards'] > 0:
                 crypto_lines.append(f"  Pending DC Rewards: {self.staked_drug_coin['pending_rewards']:.4f}")
            wallet_empty = False
        
        if wallet_empty:
            crypto_lines.append("  None")
        summary_parts.append("\n".join(crypto_lines))

        if self.pending_laundered_sc_arrival_day is not None:
            summary_parts.append(f"\nLaundering: {self.pending_laundered_sc:.2f} SC arriving Day {self.pending_laundered_sc_arrival_day}.")
        
        special_unlocks = []
        # Checking skills by their string ID from SKILL_DEFINITIONS keys
        if "GHOST_NETWORK_ACCESS_SKILL" in self.unlocked_skills: # Example skill ID
            special_unlocks.append("Ghost Network Access (Skill)")
        if "DIGITAL_ARSENAL_SKILL" in self.unlocked_skills: # Example skill ID
            special_unlocks.append("Digital Arsenal (Skill)")

        # Checking direct attributes for items/status
        if self.has_secure_phone:
            special_unlocks.append("Secure Phone")
        if self.ghost_network_access > 0 :
             special_unlocks.append(f"Ghost Network Access ({self.ghost_network_access} days)")

        if special_unlocks:
            summary_parts.append("\nSpecial Access/Items:")
            for item_name in special_unlocks:
                summary_parts.append(f"  - {item_name}")
        
        return "\n".join(summary_parts)