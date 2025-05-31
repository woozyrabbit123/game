"""Game configuration constants and settings."""
from typing import Dict, List
from .core.enums import CryptoCoin, DrugQuality, DrugName, RegionName

# Global game settings and constants

# Player Defaults
PLAYER_STARTING_CASH: float = 5000.0
PLAYER_MAX_CAPACITY: int = 150 # This is the base capacity
BANKRUPTCY_THRESHOLD: int = -1000 # If cash falls below this, game over

# OpSec Upgrades
SECURE_PHONE_COST: float = 5000.0
SECURE_PHONE_HEAT_REDUCTION_PERCENT: float = 0.25
GHOST_NETWORK_ACCESS_COST_DC: float = 10000.0

# Upgrades Constants
CAPACITY_UPGRADE_COST_INITIAL: float = 1000.0
CAPACITY_UPGRADE_COST_MULTIPLIER: float = 2.5  # Multiplier for upgrade costs
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

# Money Laundering
LAUNDERING_FEE_PERCENT: float = 0.10
LAUNDERING_DELAY_DAYS: int = 3

# Tech Contact
TECH_CONTACT_FEE_PERCENT: float = 0.05

# Debt Collector
DEBT_PAYMENT_1_AMOUNT: float = 25000.0
DEBT_PAYMENT_1_DUE_DAY: int = 15
DEBT_PAYMENT_2_AMOUNT: float = 30000.0
DEBT_PAYMENT_2_DUE_DAY: int = 30
DEBT_PAYMENT_3_AMOUNT: float = 20000.0
DEBT_PAYMENT_3_DUE_DAY: int = 45

# Event Chances
EVENT_TRIGGER_CHANCE: float = 0.20
MUGGING_EVENT_CHANCE: float = 0.10

# Black Market Event
BLACK_MARKET_CHANCE: float = 0.04
BLACK_MARKET_PRICE_REDUCTION_PERCENT: float = 0.50  # Player buys at 50% of normal price
BLACK_MARKET_EVENT_DURATION_DAYS: int = 1
BLACK_MARKET_MIN_QUANTITY: int = 20
BLACK_MARKET_MAX_QUANTITY: int = 50

# Forced Fire Sale Event
FORCED_FIRE_SALE_CHANCE: float = 0.02
FORCED_FIRE_SALE_QUANTITY_PERCENT: float = 0.15  # Percentage of a single drug stash to be sold
FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT: float = 0.30  # Price is 30% lower than normal sell price
FORCED_FIRE_SALE_MIN_CASH_GAIN: float = 50.0 # Minimum cash player gets from the sale

# Heat System & Police Stops
HEAT_PRICE_INCREASE_THRESHOLDS: Dict[int, float] = {0: 1.0, 21: 1.05, 51: 1.10, 81: 1.15}
HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3: Dict[int, float] = {0: 1.0, 31: 0.75, 61: 0.50, 91: 0.25}
HEAT_FROM_SELLING_DRUG_TIER: Dict[int, int] = {1: 1, 2: 2, 3: 4, 4: 8}
HEAT_FROM_CRYPTO_TRANSACTION: int = 1
POLICE_STOP_HEAT_THRESHOLD: int = 50
DIGITAL_ARSENAL_WARNING_HEAT_THRESHOLD: int = 80
POLICE_STOP_CONFISCATION_CHANCE: float = 0.25 # Chance all drugs are confiscated if searched and over threshold
POLICE_STOP_CONTRABAND_THRESHOLD_UNITS: int = 10 # Units of drugs player must carry to risk confiscation if searched

# Skill System
SKILL_POINTS_PER_X_DAYS: int = 7
SKILL_MARKET_INTUITION_COST: int = 1
SKILL_DIGITAL_FOOTPRINT_COST: int = 2
SKILL_MARKET_ANALYST_COST: int = 2
DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT: float = 0.25
SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT: float = 0.25 # Additional reduction when both phone and skill are active

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
    },
    "MARKET_ANALYST": {
        "name": "Market Analyst",
        "cost": SKILL_MARKET_ANALYST_COST,
        "description": "Shows if a drug's price has increased, decreased, or stayed stable since yesterday."
    }
}

UPGRADE_DEFINITIONS = {
    "SECURE_PHONE": {
        "name": "Secure Phone",
        "cost": SECURE_PHONE_COST,
        "description": f"Reduces crypto heat by {SECURE_PHONE_HEAT_REDUCTION_PERCENT*100:.0f}%. Stacks with Digital Footprint."
    },
    "EXPANDED_CAPACITY": {
        "name": "Expanded Capacity",
        "costs": CAPACITY_COSTS, 
        "capacity_levels": CAPACITY_LEVELS,
        "description_template": "Increases inventory capacity to {next_capacity}. Cost: ${next_cost:,.0f}.",
        "description_maxed": "Inventory capacity is fully upgraded."
    }
}

# Informant System
INFORMANT_TIP_COST_RUMOR: float = 50.0
INFORMANT_TIP_COST_DRUG_INFO: float = 75.0
INFORMANT_TIP_COST_RIVAL_INFO: float = 100.0
INFORMANT_TRUST_GAIN_PER_TIP: int = 5
INFORMANT_MAX_TRUST: int = 100
INFORMANT_BETRAYAL_CHANCE: float = 0.03
INFORMANT_TRUST_THRESHOLD_FOR_BETRAYAL: int = 20  # Trust must be <= this for betrayal
INFORMANT_BETRAYAL_UNAVAILABLE_DAYS: int = 7 # Cooldown after a betrayal event

# Cryptocurrency
CRYPTO_PRICES_INITIAL: Dict[CryptoCoin, float] = {
    CryptoCoin.BITCOIN: 100.0, 
    CryptoCoin.ETHEREUM: 50.0, 
    CryptoCoin.MONERO: 75.0,
    CryptoCoin.ZCASH: 25.0
}

CRYPTO_VOLATILITY: Dict[CryptoCoin, float] = {
    CryptoCoin.BITCOIN: 0.05, 
    CryptoCoin.ETHEREUM: 0.08,
    CryptoCoin.MONERO: 0.10,
    CryptoCoin.ZCASH: 0.15
}

CRYPTO_MIN_PRICE: Dict[CryptoCoin, float] = {
    CryptoCoin.BITCOIN: 20.0, 
    CryptoCoin.ETHEREUM: 10.0,
    CryptoCoin.MONERO: 15.0,
    CryptoCoin.ZCASH: 5.0
}