"""
Manages the player's inventory, including drugs, cash, crypto, skills,
and status.
"""
from typing import Dict, List, Optional, Set, Union, TYPE_CHECKING

from .enums import CryptoCoin, DrugName, DrugQuality, SkillID


if TYPE_CHECKING:
    pass


class PlayerInventory:
    """
    Represents the player's inventory and status.

    Includes drugs, cash, crypto holdings, skills, heat, debt, and upgrades.

    Attributes:
        items: Player's drug inventory. Outer dict key is DrugName, inner dict
               key is DrugQuality, value is quantity.
        max_capacity: Maximum drug units player can carry.
        current_load: Current drug units player is carrying.
        cash: Player's current cash.
        capacity_upgrades_purchased: Number of capacity upgrades bought.
        skill_points: Available skill points.
        unlocked_skills: Set of SkillID values (strings) for unlocked skills.
        informant_trust: Current trust level with the informant.
        crypto_wallet: Player's cryptocurrency holdings.
        staked_drug_coin: Info about staked DrugCoin ('staked_amount',
                          'pending_rewards').
        pending_laundered_sc: Amount of StableCoin (SC) being laundered.
        pending_laundered_sc_arrival_day: Day laundered SC will arrive.
        has_secure_phone: True if Secure Phone upgrade purchased.
        ghost_network_access: Days of Ghost Network access remaining (feature TBD).
        heat: Player's current overall heat level.
        debt_payment_1_paid: Status of the first debt payment.
        debt_payment_2_paid: Status of the second debt payment.
        debt_payment_3_paid: Status of the third debt payment.
    """

    def __init__(
        self, max_capacity: Optional[int] = None, starting_cash: Optional[float] = None
    ) -> None:
        """
        Initializes the PlayerInventory.

        Args:
            max_capacity: Optional initial max drug carrying capacity.
                          Defaults to PLAYER_MAX_CAPACITY from game_configs.
            starting_cash: Optional initial cash.
                           Defaults to PLAYER_STARTING_CASH from game_configs.
        """
        if max_capacity is None or starting_cash is None:
            # Lazy import: avoid circular dependency if PlayerInventory is
            # imported by game_configs indirectly.
            from ..narco_configs import PLAYER_STARTING_CASH, PLAYER_MAX_CAPACITY

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
        self.unlocked_skills: Set[str] = set()  # Storing SkillID.value (str)
        self.informant_trust: int = 0

        self.crypto_wallet: Dict[CryptoCoin, float] = {}
        for coin_enum_member in CryptoCoin:
            self.crypto_wallet[coin_enum_member] = 0.0

        self.staked_drug_coin: Dict[str, float] = {
            'staked_amount': 0.0,
            'pending_rewards': 0.0,
        }

        self.pending_laundered_sc: float = 0.0
        self.pending_laundered_sc_arrival_day: Optional[int] = None

        self.has_secure_phone: bool = False
        self.ghost_network_access: int = 0  # Days of access, feature TBD
        self.heat: int = 0

        self.debt_payment_1_paid: bool = False
        self.debt_payment_2_paid: bool = False
        self.debt_payment_3_paid: bool = False

    def unlock_skill(self, skill_id_str: str, cost: int) -> bool:
        """
        Unlocks a skill if player has enough skill points.

        Args:
            skill_id_str: The string value of the SkillID to unlock.
            cost: The skill point cost.

        Returns:
            True if skill unlocked, False otherwise.
        """
        if self.skill_points >= cost:
            self.skill_points -= cost
            self.unlocked_skills.add(skill_id_str)
            return True
        return False

    def _recalculate_current_load(self) -> None:
        """Recalculates the player's current drug inventory load."""
        total = 0  # type: int
        for qualities in self.items.values():
            for quantity in qualities.values():
                total += quantity
        self.current_load = total

    def add_drug(
        self, drug_name: DrugName, quality: DrugQuality, quantity_to_add: int
    ) -> bool:
        """
        Adds a drug to inventory if space and valid quantity.

        Args:
            drug_name: The DrugName of the drug.
            quality: The DrugQuality of the drug.
            quantity_to_add: Amount to add.

        Returns:
            True if added, False otherwise (no space, invalid quantity).
        """
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

    def remove_drug(
        self, drug_name: DrugName, quality: DrugQuality, quantity_to_remove: int
    ) -> bool:
        """
        Removes a drug from inventory if sufficient quantity exists.

        Args:
            drug_name: The DrugName of the drug.
            quality: The DrugQuality of the drug.
            quantity_to_remove: Amount to remove.

        Returns:
            True if removed, False otherwise (not enough items, invalid qty).
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
        Retrieves details of a drug item in inventory.

        Args:
            drug_name: DrugName of the drug.
            quality: DrugQuality of the drug.

        Returns:
            Dict with 'drug_name', 'quality', 'quantity' if found, else None.
        """
        if drug_name in self.items and quality in self.items[drug_name]:
            item_data: Dict[str, Union[DrugName, DrugQuality, int]] = {
                'drug_name': drug_name,
                'quality': quality,
                'quantity': self.items[drug_name][quality],
            }
            return item_data
        return None

    def get_quantity(self, drug_name: DrugName, quality: DrugQuality) -> int:
        """Gets quantity of a drug/quality. Alias for get_drug_quantity."""
        return self.items.get(drug_name, {}).get(quality, 0)

    def get_drug_quantity(self, drug_name: DrugName, quality: DrugQuality) -> int:
        """
        Returns quantity of a drug and quality in inventory.

        Args:
            drug_name: DrugName of the drug.
            quality: DrugQuality of the drug.

        Returns:
            Quantity (int) of drug/quality, or 0 if not found.
        """
        return self.items.get(drug_name, {}).get(quality, 0)

    def add_crypto(self, coin: CryptoCoin, amount: float) -> None:
        """
        Adds crypto to the player's wallet.

        Args:
            coin: CryptoCoin enum for the cryptocurrency.
            amount: Amount to add (must be positive).
        """
        if amount <= 0:
            return
        self.crypto_wallet[coin] = self.crypto_wallet.get(coin, 0.0) + amount

    def remove_crypto(self, coin: CryptoCoin, amount: float) -> bool:
        """
        Removes crypto from player's wallet.

        Args:
            coin: CryptoCoin enum for the cryptocurrency.
            amount: Amount to remove (must be positive).

        Returns:
            True if successful, False otherwise (not enough balance, invalid
            amount).
        """
        if amount <= 0:
            return False
        if self.crypto_wallet.get(coin, 0.0) >= amount:
            self.crypto_wallet[coin] -= amount
            return True
        return False

    def get_available_space(self) -> int:
        """Returns the remaining available space in player's inventory."""
        return self.max_capacity - self.current_load

    def get_inventory_summary(self) -> Dict[DrugName, Dict[DrugQuality, int]]:
        """Returns the raw drug items dictionary."""
        return self.items

    def formatted_summary(self) -> str:
        """
        Generates a formatted string summary of inventory and status.

        Includes cash, load, heat, skills, drugs, crypto, laundering, etc.

        Returns:
            Multi-line string summarizing player status.
        """
        summary_parts: List[str] = [
            f'Cash: ${self.cash:,.2f}',
            f'Load: {self.current_load}/{self.max_capacity}',
            f'Heat: {self.heat}',
            f'Skill Points: {self.skill_points}'
        ]

        drug_lines: List[str] = ['Drugs:']
        if self.items:
            for drug, qualities in self.items.items():
                for qual, qty in qualities.items():
                    drug_lines.append(f'  {drug.value} ({qual.name}): {qty}')
        else:
            drug_lines.append('  None')
        summary_parts.append('\n'.join(drug_lines))

        crypto_lines: List[str] = ['Crypto:']
        wallet_empty = True
        if self.crypto_wallet:
            for coin, amt in self.crypto_wallet.items():
                if amt > 1e-9:  # Use epsilon for float comparison
                    crypto_lines.append(f'  {coin.value}: {amt:.4f}')
                    wallet_empty = False

        staked_amount = self.staked_drug_coin.get('staked_amount', 0.0)
        pending_rewards = self.staked_drug_coin.get('pending_rewards', 0.0)
        if staked_amount > 1e-9 or pending_rewards > 1e-9:
            crypto_lines.append(f'  Staked DC: {staked_amount:.4f}')
            if pending_rewards > 1e-9:
                crypto_lines.append(
                    f'  Pending DC Rewards: {pending_rewards:.4f}'
                )
            wallet_empty = False

        if wallet_empty:
            crypto_lines.append('  None')
        summary_parts.append('\n'.join(crypto_lines))

        if self.pending_laundered_sc_arrival_day is not None:
            summary_parts.append(
                f'\nLaundering: {self.pending_laundered_sc:.2f} SC '
                f'arriving Day {self.pending_laundered_sc_arrival_day}.'
            )

        special_unlocks: List[str] = []
        if SkillID.GHOST_NETWORK_ACCESS.value in self.unlocked_skills:
            special_unlocks.append('Ghost Network Access (Skill)')
        # Example:
        # if SkillID.SOME_OTHER_SKILL.value in self.unlocked_skills:
        #     special_unlocks.append('Some Other Skill Name')

        if self.has_secure_phone:
            special_unlocks.append('Secure Phone')
        if self.ghost_network_access > 0:
            special_unlocks.append(
                f'Ghost Network Access ({self.ghost_network_access} days)'
            )

        if special_unlocks:
            summary_parts.append('\nSpecial Access/Items:')
            for item_name in special_unlocks:
                summary_parts.append(f'  - {item_name}')

        return '\n'.join(summary_parts)

    def process_buy_drug(
            self, drug_name: DrugName, quality: DrugQuality,
            quantity: int, cost: float
    ) -> bool:
        """
        Processes buying drug: checks cash/space, adds drug, deducts cash.

        Args:
            drug_name: DrugName of the drug.
            quality: DrugQuality of the drug.
            quantity: Amount to buy.
            cost: Total cost.

        Returns:
            True if purchase successful, False otherwise.
        """
        if self.cash < cost:
            # print('Debug: Not enough cash in process_buy_drug')
            return False
        if self.current_load + quantity > self.max_capacity:
            # print('Debug: Not enough space in process_buy_drug')
            return False

        if self.add_drug(drug_name, quality, quantity):
            self.cash -= cost
            return True
        # print('Debug: add_drug failed in process_buy_drug')
        return False

    def process_sell_drug(
            self, drug_name: DrugName, quality: DrugQuality,
            quantity: int, revenue: float
    ) -> bool:
        """
        Processes selling drug: checks quantity, removes drug, adds cash.

        Args:
            drug_name: DrugName of the drug.
            quality: DrugQuality of the drug.
            quantity: Amount to sell.
            revenue: Total revenue from sale.

        Returns:
            True if sale successful, False otherwise.
        """
        if self.get_drug_quantity(drug_name, quality) < quantity:
            # print('Debug: Not enough drugs to sell in process_sell_drug')
            return False
        
        if self.remove_drug(drug_name, quality, quantity):
            self.cash += revenue
            return True
        # print('Debug: remove_drug failed in process_sell_drug')
        return False
