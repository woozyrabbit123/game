"""
Manages the player's inventory, including drugs, cash, crypto, skills, and status.
"""

from typing import Dict, List, Optional, Set, Union, TYPE_CHECKING
from .enums import DrugQuality, DrugName, CryptoCoin, SkillID

if TYPE_CHECKING:
    pass


class PlayerInventory:
    """
    Represents the player's inventory and status.

    This includes drugs carried, cash, cryptocurrency holdings, unlocked skills,
    current heat level, debt status, and various upgrades.

    Attributes:
        items (Dict[DrugName, Dict[DrugQuality, int]]): Player's drug inventory.
            Outer dict key is DrugName, inner dict key is DrugQuality, value is quantity.
        max_capacity (int): Maximum number of drug units player can carry.
        current_load (int): Current number of drug units player is carrying.
        cash (float): Player's current cash amount.
        capacity_upgrades_purchased (int): Number of capacity upgrades bought.
        skill_points (int): Available skill points for unlocking new skills.
        unlocked_skills (Set[str]): Set of SkillID values (strings) for unlocked skills.
        informant_trust (int): Current trust level with the informant.
        crypto_wallet (Dict[CryptoCoin, float]): Player's cryptocurrency holdings.
        staked_drug_coin (Dict[str, float]): Information about staked DrugCoin.
            Includes 'staked_amount' and 'pending_rewards'.
        pending_laundered_sc (float): Amount of StableCoin (SC) currently being laundered.
        pending_laundered_sc_arrival_day (Optional[int]): Day when laundered SC will arrive.
        has_secure_phone (bool): True if player has purchased the Secure Phone upgrade.
        ghost_network_access (int): Days of Ghost Network access remaining (not fully implemented).
        heat (int): Player's current overall heat level.
        debt_payment_1_paid (bool): Status of the first debt payment.
        debt_payment_2_paid (bool): Status of the second debt payment.
        debt_payment_3_paid (bool): Status of the third debt payment.
    """

    def __init__(
        self, max_capacity: Optional[int] = None, starting_cash: Optional[float] = None
    ) -> None:
        """
        Initializes the PlayerInventory.

        Args:
            max_capacity: Optional initial maximum drug carrying capacity.
                          Defaults to PLAYER_MAX_CAPACITY from game_configs.
            starting_cash: Optional initial cash amount.
                           Defaults to PLAYER_STARTING_CASH from game_configs.
        """
        if max_capacity is None or starting_cash is None:
            # Lazy import to avoid circular dependency if this class is imported by game_configs indirectly
            from ..game_configs import PLAYER_STARTING_CASH, PLAYER_MAX_CAPACITY

            max_capacity = (
                max_capacity if max_capacity is not None else PLAYER_MAX_CAPACITY
            )
            starting_cash = (
                starting_cash if starting_cash is not None else PLAYER_STARTING_CASH
            )

        self.items: Dict[DrugName, Dict[DrugQuality, int]] = {}
        self.max_capacity: int = (
            max_capacity if max_capacity is not None else 0
        )  # Ensure max_capacity is int
        self.current_load: int = 0
        self.cash: float = (
            starting_cash if starting_cash is not None else 0.0
        )  # Ensure starting_cash is float
        self.capacity_upgrades_purchased: int = 0
        self.skill_points: int = 0
        self.unlocked_skills: Set[str] = set()  # Storing SkillID.value (string)
        self.informant_trust: int = 0

        self.crypto_wallet: Dict[CryptoCoin, float] = {}
        for coin_enum_member in CryptoCoin:  # coin_enum_member is CryptoCoin
            self.crypto_wallet[coin_enum_member] = 0.0

        self.staked_drug_coin: Dict[str, float] = {
            "staked_amount": 0.0,
            "pending_rewards": 0.0,
        }

        self.pending_laundered_sc: float = 0.0
        self.pending_laundered_sc_arrival_day: Optional[int] = None

        self.has_secure_phone: bool = False
        self.ghost_network_access: int = 0
        self.heat: int = 0

        self.debt_payment_1_paid: bool = False
        self.debt_payment_2_paid: bool = False
        self.debt_payment_3_paid: bool = False

    def unlock_skill(self, skill_id_str: str, cost: int) -> bool:
        """
        Attempts to unlock a skill for the player.

        Args:
            skill_id_str: The string value of the SkillID to unlock (e.g., SkillID.MARKET_INTUITION.value).
            cost: The cost in skill points to unlock the skill.

        Returns:
            True if the skill was successfully unlocked, False otherwise (e.g., not enough points).
        """
        if self.skill_points >= cost:
            self.skill_points -= cost
            self.unlocked_skills.add(skill_id_str)
            return True
        return False

    def _recalculate_current_load(self) -> None:
        """Recalculates the player's current drug inventory load."""
        total: int = 0
        for qualities in self.items.values():
            for quantity in qualities.values():
                total += quantity
        self.current_load = total

    def add_drug(
        self, drug_name: DrugName, quality: DrugQuality, quantity_to_add: int
    ) -> bool:
        """
        Adds a specified quantity of a drug with a specific quality to the inventory.

        Args:
            drug_name: The DrugName enum of the drug to add.
            quality: The DrugQuality enum of the drug.
            quantity_to_add: The amount of the drug to add.

        Returns:
            True if the drug was successfully added, False otherwise (e.g., not enough space, invalid quantity).
        """
        available_space: int = self.max_capacity - self.current_load
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

    def remove_drug(
        self, drug_name: DrugName, quality: DrugQuality, quantity_to_remove: int
    ) -> bool:
        """
        Removes a specified quantity of a drug with a specific quality from the inventory.

        Args:
            drug_name: The DrugName enum of the drug to remove.
            quality: The DrugQuality enum of the drug.
            quantity_to_remove: The amount of the drug to remove.

        Returns:
            True if the drug was successfully removed, False otherwise (e.g., not enough items, invalid quantity).
        """
        if quantity_to_remove <= 0:
            return False
        if (
            drug_name not in self.items
            or quality not in self.items[drug_name]
            or self.items[drug_name][quality] < quantity_to_remove
        ):
            return False

        self.items[drug_name][quality] -= quantity_to_remove
        if self.items[drug_name][quality] == 0:
            del self.items[drug_name][quality]
        if not self.items[drug_name]:
            del self.items[drug_name]

        self._recalculate_current_load()
        return True

    def get_drug_item(
        self, drug_name: DrugName, quality: DrugQuality
    ) -> Optional[Dict[str, Union[DrugName, DrugQuality, int]]]:
        """
        Retrieves details of a specific drug item in the inventory.

        Args:
            drug_name: The DrugName enum of the drug.
            quality: The DrugQuality enum of the drug.

        Returns:
            A dictionary with "drug_name", "quality", and "quantity" if found,
            otherwise None.
        """
        if drug_name in self.items and quality in self.items[drug_name]:
            item_data: Dict[str, Union[DrugName, DrugQuality, int]] = {
                "drug_name": drug_name,
                "quality": quality,
                "quantity": self.items[drug_name][quality],
            }
            return item_data
        return None

    def get_quantity(self, drug_name: DrugName, quality: DrugQuality) -> int:
        """Gets the quantity of a specific drug and quality. Alias for get_drug_quantity."""
        return self.items.get(drug_name, {}).get(quality, 0)

    def get_drug_quantity(self, drug_name: DrugName, quality: DrugQuality) -> int:
        """
        Returns the quantity of a specific drug and quality in inventory.

        Args:
            drug_name: The DrugName enum of the drug.
            quality: The DrugQuality enum of the drug.

        Returns:
            The quantity (int) of the specified drug and quality, or 0 if not found.
        """
        return self.items.get(drug_name, {}).get(quality, 0)

    def add_crypto(self, coin: CryptoCoin, amount: float) -> None:
        """
        Adds a specified amount of cryptocurrency to the player's wallet.

        Args:
            coin: The CryptoCoin enum member representing the cryptocurrency.
            amount: The amount to add (must be positive).
        """
        if amount <= 0:
            return
        self.crypto_wallet[coin] = self.crypto_wallet.get(coin, 0.0) + amount

    def remove_crypto(self, coin: CryptoCoin, amount: float) -> bool:
        """
        Removes a specified amount of cryptocurrency from the player's wallet.

        Args:
            coin: The CryptoCoin enum member representing the cryptocurrency.
            amount: The amount to remove (must be positive).

        Returns:
            True if the cryptocurrency was successfully removed, False otherwise
            (e.g., not enough balance, invalid amount).
        """
        if amount <= 0:
            return False
        if self.crypto_wallet.get(coin, 0.0) >= amount:
            self.crypto_wallet[coin] -= amount
            return True
        return False

    def get_available_space(self) -> int:
        """Returns the remaining available space in the player's inventory."""
        return self.max_capacity - self.current_load

    def get_inventory_summary(self) -> Dict[DrugName, Dict[DrugQuality, int]]:
        """Returns the raw drug items dictionary."""
        return self.items

    def formatted_summary(self) -> str:
        """
        Generates a formatted string summary of the player's inventory and status.

        Includes cash, load, heat, skill points, drugs, crypto, laundering status,
        and special unlocks/items.

        Returns:
            A multi-line string summarizing the player's inventory and status.
        """
        summary_parts: List[str] = []
        summary_parts.append(f"Cash: ${self.cash:,.2f}")
        summary_parts.append(f"Load: {self.current_load}/{self.max_capacity}")
        summary_parts.append(f"Heat: {self.heat}")
        summary_parts.append(f"Skill Points: {self.skill_points}")

        drug_lines: List[str] = ["Drugs:"]
        if self.items:
            for (
                drug,
                qualities,
            ) in (
                self.items.items()
            ):  # drug is DrugName, qualities is Dict[DrugQuality, int]
                for qual, qty in qualities.items():  # qual is DrugQuality, qty is int
                    drug_lines.append(f"  {drug.value} ({qual.name}): {qty}")
        else:
            drug_lines.append("  None")
        summary_parts.append("\n".join(drug_lines))

        crypto_lines: List[str] = ["Crypto:"]
        wallet_empty: bool = True
        if self.crypto_wallet:
            for (
                coin,
                amt,
            ) in self.crypto_wallet.items():  # coin is CryptoCoin, amt is float
                if amt > 0:
                    crypto_lines.append(f"  {coin.value}: {amt:.4f}")
                    wallet_empty = False

        if (
            self.staked_drug_coin["staked_amount"] > 0
            or self.staked_drug_coin["pending_rewards"] > 0
        ):
            crypto_lines.append(
                f"  Staked DC: {self.staked_drug_coin['staked_amount']:.4f}"
            )
            if self.staked_drug_coin["pending_rewards"] > 0:
                crypto_lines.append(
                    f"  Pending DC Rewards: {self.staked_drug_coin['pending_rewards']:.4f}"
                )
            wallet_empty = False

        if wallet_empty:
            crypto_lines.append("  None")
        summary_parts.append("\n".join(crypto_lines))

        if self.pending_laundered_sc_arrival_day is not None:
            summary_parts.append(
                f"\nLaundering: {self.pending_laundered_sc:.2f} SC arriving Day {self.pending_laundered_sc_arrival_day}."
            )

        special_unlocks: List[str] = []
        # Checking skills by their string ID (SkillID.value)
        # Actual SkillID values should be used here if available from game_configs or enums
        if SkillID.GHOST_NETWORK_ACCESS.value in self.unlocked_skills:
            special_unlocks.append("Ghost Network Access (Skill)")
        # Example for another skill, assuming "DIGITAL_ARSENAL" is a value in SkillID enum
        # if SkillID.DIGITAL_ARSENAL.value in self.unlocked_skills:
        #     special_unlocks.append("Digital Arsenal (Skill)")

        # Checking direct attributes for items/status
        if self.has_secure_phone:
            special_unlocks.append("Secure Phone")
        if self.ghost_network_access > 0:
            special_unlocks.append(
                f"Ghost Network Access ({self.ghost_network_access} days)"
            )

        if special_unlocks:
            summary_parts.append("\nSpecial Access/Items:")
            for item_name in special_unlocks:  # item_name is str
                summary_parts.append(f"  - {item_name}")

        return "\n".join(summary_parts)

    def process_buy_drug(self, drug_name: DrugName, quality: DrugQuality, quantity: int, cost: float) -> bool:
        """
        Processes buying a drug: checks cash, space, adds drug, deducts cash.

        Args:
            drug_name: The DrugName of the drug to buy.
            quality: The DrugQuality of the drug.
            quantity: The amount of the drug to buy.
            cost: The total cost of the transaction.

        Returns:
            True if the purchase was successful, False otherwise.
        """
        if self.cash < cost:
            # print("Debug: Not enough cash in process_buy_drug") # Optional debug
            return False
        if self.current_load + quantity > self.max_capacity:
            # print("Debug: Not enough space in process_buy_drug") # Optional debug
            return False

        if self.add_drug(drug_name, quality, quantity): # add_drug already recalculates load
            self.cash -= cost
            return True
        else:
            # This case should ideally not be reached if space check above is correct,
            # unless add_drug has other failure conditions not covered by space.
            # print("Debug: add_drug failed within process_buy_drug despite checks") # Optional debug
            return False

    def process_sell_drug(self, drug_name: DrugName, quality: DrugQuality, quantity: int, revenue: float) -> bool:
        """
        Processes selling a drug: checks quantity, removes drug, adds cash.

        Args:
            drug_name: The DrugName of the drug to sell.
            quality: The DrugQuality of the drug.
            quantity: The amount of the drug to sell.
            revenue: The total revenue from the sale.

        Returns:
            True if the sale was successful, False otherwise.
        """
        if self.get_drug_quantity(drug_name, quality) < quantity:
            # print("Debug: Not enough drugs to sell in process_sell_drug") # Optional debug
            return False
        
        if self.remove_drug(drug_name, quality, quantity): # remove_drug already recalculates load
            self.cash += revenue
            return True
        else:
            # This case should ideally not be reached if quantity check is correct.
            # print("Debug: remove_drug failed within process_sell_drug despite checks") # Optional debug
            return False
