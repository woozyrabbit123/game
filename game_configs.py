from typing import Dict, List
from core.enums import CryptoCoin # Import CryptoCoin

# Global game settings and constants

# Player Defaults
PLAYER_STARTING_CASH: float = 5000.0
PLAYER_MAX_CAPACITY: int = 150 # This is the base capacity

# Upgrades Constants
CAPACITY_UPGRADE_COST_INITIAL: float = 1000.0
# CAPACITY_UPGRADE_COST_MULTIPLIER: float = 1.5 # Not directly used if costs are explicit list
CAPACITY_UPGRADE_AMOUNT: int = 50 # Base increment amount

CAPACITY_LEVELS: List[int] = [
    PLAYER_MAX_CAPACITY + CAPACITY_UPGRADE_AMOUNT,      # Level 1: 200
    PLAYER_MAX_CAPACITY + (2 * CAPACITY_UPGRADE_AMOUNT), # Level 2: 250
    PLAYER_MAX_CAPACITY + (3 * CAPACITY_UPGRADE_AMOUNT), # Level 3: 300
    PLAYER_MAX_CAPACITY + (4 * CAPACITY_UPGRADE_AMOUNT)  # Level 4: 350
]
CAPACITY_COSTS: List[float] = [
    CAPACITY_UPGRADE_COST_INITIAL, # Cost for Level 1
    CAPACITY_UPGRADE_COST_INITIAL * 2.5,  # Cost for Level 2
    CAPACITY_UPGRADE_COST_INITIAL * 5.0,  # Cost for Level 3
    CAPACITY_UPGRADE_COST_INITIAL * 8.0   # Cost for Level 4
]
# Note: SECURE_PHONE_COST and SECURE_PHONE_HEAT_REDUCTION_PERCENT are defined further down under OpSec Upgrades

# Debt Collector
DEBT_PAYMENT_1_AMOUNT: float = 25000.0
DEBT_PAYMENT_1_DUE_DAY: int = 15
DEBT_PAYMENT_2_AMOUNT: float = 30000.0
DEBT_PAYMENT_2_DUE_DAY: int = 30
DEBT_PAYMENT_3_AMOUNT: float = 20000.0
DEBT_PAYMENT_3_DUE_DAY: int = 45

# Event Chances
EVENT_TRIGGER_CHANCE: float = 0.20

# Heat System
HEAT_PRICE_INCREASE_THRESHOLDS: Dict[int, float] = {0: 1.0, 21: 1.05, 51: 1.10, 81: 1.15}
HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3: Dict[int, float] = {0: 1.0, 31: 0.75, 61: 0.50, 91: 0.25}
HEAT_FROM_SELLING_DRUG_TIER: Dict[int, int] = {1: 1, 2: 2, 3: 4, 4: 8}
HEAT_FROM_CRYPTO_TRANSACTION: int = 1

# Skill System
SKILL_POINTS_PER_X_DAYS: int = 7
SKILL_MARKET_INTUITION_COST: int = 1
SKILL_DIGITAL_FOOTPRINT_COST: int = 2 
DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT: float = 0.25 # Moved and updated for SKILL_DEFINITIONS

SKILL_DEFINITIONS = {
    "MARKET_INTUITION": {
        "name": "Market Intuition",
        "cost": SKILL_MARKET_INTUITION_COST,
        "description": "Shows market price trends for drugs."
    },
    "DIGITAL_FOOTPRINT": {
        "name": "Digital Footprint",
        "cost": SKILL_DIGITAL_FOOTPRINT_COST,
        "description": f"Reduces heat from crypto transactions by {DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT*100:.0f}%."
    }
}

UPGRADE_DEFINITIONS = {
    "SECURE_PHONE": {
        "name": "Secure Phone",
        "cost": SECURE_PHONE_COST, # Defined under OpSec Upgrades section
        "description": f"Reduces crypto heat by {SECURE_PHONE_HEAT_REDUCTION_PERCENT*100:.0f}%. Stacks with Digital Footprint."
    },
    "EXPANDED_CAPACITY": {
        "name": "Expanded Capacity",
        "costs": CAPACITY_COSTS, 
        "capacity_levels": CAPACITY_LEVELS,
        "description_template": "Increases inventory capacity to {next_capacity}. Cost: ${next_cost:,.0f}.", # Used by UI to format
        "description_maxed": "Inventory capacity is fully upgraded."
    }
}

# Informant System
INFORMANT_TIP_COST_RUMOR: float = 50.0 # Renamed from INFORMANT_TIP_COST for clarity
INFORMANT_TIP_COST_DRUG_INFO: float = 75.0 # New constant
INFORMANT_TIP_COST_RIVAL_INFO: float = 100.0 # New constant
INFORMANT_TRUST_GAIN_PER_TIP: int = 5
INFORMANT_MAX_TRUST: int = 100

# Cryptocurrency
CRYPTO_PRICES_INITIAL: Dict[CryptoCoin, float] = {
    CryptoCoin.DRUG_COIN: 100.0, 
    CryptoCoin.VOLATILITY_COIN: 50.0, 
    CryptoCoin.STABLE_COIN: 1.0
}
CRYPTO_VOLATILITY: Dict[CryptoCoin, float] = {
    CryptoCoin.DRUG_COIN: 0.05, 
    CryptoCoin.VOLATILITY_COIN: 0.20, 
    CryptoCoin.STABLE_COIN: 0.005
}
CRYPTO_MIN_PRICE: Dict[CryptoCoin, float] = {
    CryptoCoin.DRUG_COIN: 20.0, 
    CryptoCoin.VOLATILITY_COIN: 5.0, 
    CryptoCoin.STABLE_COIN: 0.98
}
DC_STAKING_DAILY_RETURN_PERCENT: float = 0.001

# Tech Contact
TECH_CONTACT_UNLOCK_DAY: int = 0 
TECH_CONTACT_FEE_PERCENT: float = 0.01

# Police Stop & Jail Event Configs
POLICE_STOP_HEAT_THRESHOLD: int = 50
POLICE_STOP_BASE_CHANCE: float = 0.10
POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD: float = 0.005
BRIBE_BASE_COST_PERCENT_OF_CASH: float = 0.10
BRIBE_MIN_COST: float = 200.0
BRIBE_SUCCESS_CHANCE_BASE: float = 0.80
BRIBE_SUCCESS_CHANCE_HEAT_PENALTY: float = 0.01
CONFISCATION_CHANCE_ON_SEARCH: float = 0.60
CONFISCATION_PERCENTAGE_MIN: float = 0.10
CONFISCATION_PERCENTAGE_MAX: float = 0.50
JAIL_TIME_DAYS_BASE: int = 3
JAIL_TIME_HEAT_MULTIPLIER: float = 0.1
JAIL_CHANCE_HEAT_THRESHOLD: int = 70
JAIL_CHANCE_IF_HIGH_TIER_DRUGS_FOUND: float = 0.3

# Crypto-Only Shop & Items
GHOST_NETWORK_ACCESS_COST_DC: float = 150.0
DIGITAL_ARSENAL_COST_DC: float = 50.0
DIGITAL_ARSENAL_WARNING_HEAT_THRESHOLD: int = 70

# Corrupt Official
CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT: int = 10
CORRUPT_OFFICIAL_BASE_BRIBE_COST: float = 500.0
CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT: float = 20.0

# Money Laundering
LAUNDERING_FEE_PERCENT: float = 0.15
LAUNDERING_DELAY_DAYS: int = 2
MAX_ACTIVE_LAUNDERING_OPERATIONS: int = 1

# "The Setup" Event
SETUP_EVENT_STING_CHANCE_BASE: float = 0.60
SETUP_EVENT_STING_CHANCE_HEAT_MODIFIER: float = 0.005

# OpSec Upgrades (New)
# DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT was moved to Skill System section and value changed
SECURE_PHONE_COST: float = 7500.0 # Used by UPGRADE_DEFINITIONS
SECURE_PHONE_HEAT_REDUCTION_PERCENT: float = 0.15 # Used by UPGRADE_DEFINITIONS. Adjusted as per earlier plan, to be distinct
SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT: float = 0.75 # This is likely a combined/calculated effect, not directly put in a definition.

TEST_CONSTANT: int = 123