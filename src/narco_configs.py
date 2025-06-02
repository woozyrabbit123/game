"""
Game configuration constants and settings.

This module defines various constants used throughout the game, including
player defaults, upgrade costs, event parameters, market dynamics,
skill definitions, and cryptocurrency settings.
These configurations control the balance and features of the game.
"""

# TEST_CONFIG_VAR = True # Commenting this out as it was for testing
from typing import Dict, List, Union, Tuple, Any # Added Union for EventConfigValues, Tuple for definitions, Any for AI_RIVAL_DEFINITIONS
from .core.enums import CryptoCoin, DrugQuality, DrugName, RegionName, SkillID

# --- Global Game Settings and Constants ---

# Player Defaults
PLAYER_STARTING_CASH: float = 5000.0  #: Initial cash available to the player.
PLAYER_MAX_CAPACITY: int = 150  #: Base maximum carrying capacity for the player.
PLAYER_STARTING_REGION_NAME: RegionName = RegionName.DOWNTOWN #: Initial region where the player starts.
TRAVEL_COST_CASH: int = 50  #: Cost in cash to travel between regions.
BANKRUPTCY_THRESHOLD: int = -1000  #: Cash level below which the player goes bankrupt.

# --- AI Rival Definitions ---
AI_RIVAL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "The Chemist",
        "primary_drug": DrugName.PILLS,
        "primary_region_name": RegionName.DOWNTOWN,
        "aggression": 0.6,
        "activity_level": 0.7,
    },
    {
        "name": "Silas",
        "primary_drug": DrugName.COKE,
        "primary_region_name": RegionName.DOWNTOWN,
        "aggression": 0.8,
        "activity_level": 0.5,
    },
    {
        "name": "Dockmaster Jones",
        "primary_drug": DrugName.SPEED,
        "primary_region_name": RegionName.DOCKS,
        "aggression": 0.5,
        "activity_level": 0.6,
    },
    {
        "name": "Mama Rosa",
        "primary_drug": DrugName.WEED,
        "primary_region_name": RegionName.SUBURBS,
        "aggression": 0.4,
        "activity_level": 0.8,
    },
    {
        "name": "Sergei",
        "primary_drug": DrugName.HEROIN,
        "primary_region_name": RegionName.DOCKS,
        "aggression": 0.7,
        "activity_level": 0.6,
    },
]

# OpSec Upgrades
SECURE_PHONE_COST: float = 5000.0  #: Cost to purchase a secure phone.
SECURE_PHONE_HEAT_REDUCTION_PERCENT: float = (
    0.25  #: Percentage reduction in heat from crypto transactions with a secure phone.
)
GHOST_NETWORK_ACCESS_COST_DC: float = (
    10000.0  #: Cost in DrugCoin (DC) to access the Ghost Network.
)

# Upgrades Constants
CAPACITY_UPGRADE_COST_INITIAL: float = (
    1000.0  #: Initial cost for the first capacity upgrade.
)
CAPACITY_UPGRADE_COST_MULTIPLIER: float = (
    2.5  #: Multiplier for subsequent capacity upgrade costs.
)
CAPACITY_UPGRADE_AMOUNT: int = 50  #: Amount by which capacity increases per upgrade.

CAPACITY_LEVELS: List[int] = [  #: Defines the capacity at each upgrade level.
    PLAYER_MAX_CAPACITY + CAPACITY_UPGRADE_AMOUNT,
    PLAYER_MAX_CAPACITY + (2 * CAPACITY_UPGRADE_AMOUNT),
    PLAYER_MAX_CAPACITY + (3 * CAPACITY_UPGRADE_AMOUNT),
    PLAYER_MAX_CAPACITY + (4 * CAPACITY_UPGRADE_AMOUNT),
]

CAPACITY_COSTS: List[float] = [  #: Defines the cost for each capacity upgrade level.
    CAPACITY_UPGRADE_COST_INITIAL,
    CAPACITY_UPGRADE_COST_INITIAL * 2.5,
    CAPACITY_UPGRADE_COST_INITIAL * 5.0,
    CAPACITY_UPGRADE_COST_INITIAL * 8.0,
]

# Money Laundering
LAUNDERING_FEE_PERCENT: float = 0.10  #: Percentage fee charged for laundering money.
LAUNDERING_DELAY_DAYS: int = (
    3  #: Number of days it takes for laundered money to become available.
)

# Tech Contact
TECH_CONTACT_FEE_PERCENT: float = (
    0.05  #: Percentage fee charged by the Tech Contact for services.
)

# Debt Collector
DEBT_PAYMENT_1_AMOUNT: float = 25000.0  #: Amount for the first debt payment.
DEBT_PAYMENT_1_DUE_DAY: int = 15  #: Day on which the first debt payment is due.
DEBT_PAYMENT_2_AMOUNT: float = 30000.0  #: Amount for the second debt payment.
DEBT_PAYMENT_2_DUE_DAY: int = 30  #: Day on which the second debt payment is due.
DEBT_PAYMENT_3_AMOUNT: float = 20000.0  #: Amount for the third debt payment.
DEBT_PAYMENT_3_DUE_DAY: int = 45  #: Day on which the third debt payment is due.

# --- Specific Event Parameter Configurations ---
#: Configuration for various market and player events.
EventConfigValues = Union[float, int]  #: Type alias for values in EVENT_CONFIGS.
EVENT_CONFIGS: Dict[str, Dict[str, EventConfigValues]] = {
    "DEMAND_SPIKE": {  #: Parameters for the Demand Spike event.
        "SELL_PRICE_MULT_MIN": 1.2,
        "SELL_PRICE_MULT_MAX": 1.8,
        "BUY_PRICE_MULT_MIN": 1.0,
        "BUY_PRICE_MULT_MAX": 1.3,
        "DURATION_DAYS_MIN": 2,
        "DURATION_DAYS_MAX": 4,
    },
    "POLICE_CRACKDOWN": {  #: Parameters for the Police Crackdown event.
        "DURATION_DAYS_MIN": 2,
        "DURATION_DAYS_MAX": 4,
        "HEAT_INCREASE_MIN": 10,
        "HEAT_INCREASE_MAX": 30,
    },
    "CHEAP_STASH": {
        "BUY_PRICE_MULT_MIN": 0.6,
        "BUY_PRICE_MULT_MAX": 0.8,
        "DURATION_DAYS_MIN": 1,
        "DURATION_DAYS_MAX": 2,
        "TEMP_STOCK_INCREASE_MIN": 50,
        "TEMP_STOCK_INCREASE_MAX": 150,
    },
    "THE_SETUP": {  #: Parameters for The Setup event (special deal).
        "DEAL_QUANTITY_MIN": 20,
        "DEAL_QUANTITY_MAX": 100,
        "BUY_DEAL_PRICE_MULT_MIN": 0.2,
        "BUY_DEAL_PRICE_MULT_MAX": 0.4,
        "SELL_DEAL_PRICE_MULT_MIN": 2.0,
        "SELL_DEAL_PRICE_MULT_MAX": 3.5,
        "DURATION_DAYS": 1,
    },
    "RIVAL_BUSTED": {  #: Parameters for the Rival Busted event.
        "DURATION_DAYS_MIN": 5,
        "DURATION_DAYS_MAX": 10,
    },
    "SUPPLY_DISRUPTION": {  #: Parameters for the Supply Disruption event.
        "DURATION_DAYS": 2,
        "STOCK_REDUCTION_PERCENT": 0.75,
        "MIN_STOCK_AFTER_EVENT": 1,
    },
    "DRUG_MARKET_CRASH": {  #: Parameters for the Drug Market Crash event.
        "DURATION_DAYS": 2,
        "PRICE_REDUCTION_PERCENT": 0.60,
        "MINIMUM_PRICE_AFTER_CRASH": 1.0,
    },
    "BLACK_MARKET_OPPORTUNITY": {  #: Parameters for the Black Market Opportunity event.
        "MIN_QUANTITY": 20,
        "MAX_QUANTITY": 50,
        "PRICE_REDUCTION_PERCENT": 0.50,
        "DURATION_DAYS": 1,
    },
}

# --- Event Chances ---
EVENT_TRIGGER_CHANCE: float = (
    0.20  #: Base chance for a random market event to trigger each day.
)
MUGGING_EVENT_CHANCE: float = 0.10  #: Chance for a mugging event to occur.

# Black Market Event
BLACK_MARKET_CHANCE: float = 0.04  #: Chance for a black market opportunity to appear.
BLACK_MARKET_PRICE_REDUCTION_PERCENT: float = (
    0.50  #: Discount percentage for drugs on the black market.
)
BLACK_MARKET_EVENT_DURATION_DAYS: int = 1  #: Duration of black market opportunities.
BLACK_MARKET_MIN_QUANTITY: int = (
    20  #: Minimum quantity of drugs available in a black market deal.
)
BLACK_MARKET_MAX_QUANTITY: int = (
    50  #: Maximum quantity of drugs available in a black market deal.
)

# Forced Fire Sale Event
FORCED_FIRE_SALE_CHANCE: float = 0.02  #: Chance for a forced fire sale event.
FORCED_FIRE_SALE_QUANTITY_PERCENT: float = (
    0.15  #: Percentage of a random drug stash player is forced to sell.
)
FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT: float = (
    0.30  #: Price reduction penalty during a forced fire sale.
)
FORCED_FIRE_SALE_MIN_CASH_GAIN: float = (
    50.0  #: Minimum cash player gains from a forced fire sale.
)

# Other Market Events
DRUG_CRASH_EVENT_CHANCE: float = 0.05  #: Chance for a specific drug market to crash.
DRUG_CRASH_PRICE_REDUCTION_PERCENT: float = (
    0.60  #: Percentage by which prices drop during a crash.
)
DRUG_CRASH_EVENT_DURATION_DAYS: int = 2  #: Duration of a drug market crash.
MINIMUM_DRUG_PRICE: float = 1.0  #: Absolute minimum price a drug can reach.
SUPPLY_DISRUPTION_CHANCE: float = 0.04  #: Chance for a supply disruption for a drug.
SUPPLY_DISRUPTION_STOCK_REDUCTION_PERCENT: float = (
    0.75  #: Percentage by which stock is reduced during a disruption.
)
SUPPLY_DISRUPTION_EVENT_DURATION_DAYS: int = 2  #: Duration of a supply disruption.
MIN_STOCK_AFTER_DISRUPTION: int = 1  #: Minimum stock level after a disruption.

# --- Heat System & Police Stops ---
BASE_DAILY_HEAT_DECAY: int = (
    1  #: Amount of heat that decays naturally each day per region.
)
HEAT_PRICE_INCREASE_THRESHOLDS: Dict[int, float] = (
    {  #: Heat thresholds and corresponding price multipliers.
        0: 1.0,
        21: 1.05,
        51: 1.10,
        81: 1.15,
    }
)
HEAT_STOCK_REDUCTION_THRESHOLDS_T2_T3: Dict[int, float] = (
    {  #: Heat thresholds and stock reduction factors for Tier 2/3 drugs.
        0: 1.0,
        31: 0.75,
        61: 0.50,
        91: 0.25,
    }
)
HEAT_FROM_SELLING_DRUG_TIER: Dict[int, int] = {
    1: 1,
    2: 2,
    3: 4,
    4: 8,
}  #: Heat generated per unit sold, by drug tier.
HEAT_FROM_CRYPTO_TRANSACTION: int = 1  #: Base heat generated from a crypto transaction.
POLICE_STOP_HEAT_THRESHOLD: int = (
    50  #: Heat level at which police stops become more likely.
)
DIGITAL_ARSENAL_WARNING_HEAT_THRESHOLD: int = (
    80  #: Heat threshold for Digital Arsenal warning.
)
POLICE_STOP_CONFISCATION_CHANCE: float = (
    0.25  #: Chance of all drugs being confiscated if searched and over contraband threshold.
)
POLICE_STOP_CONTRABAND_THRESHOLD_UNITS: int = (
    10  #: Units of drugs player must carry to risk confiscation if searched.
)

POLICE_STOP_BASE_CHANCE: float = 0.10  #: Base chance of a police stop occurring.
POLICE_STOP_CHANCE_PER_HEAT_POINT_ABOVE_THRESHOLD: float = (
    0.01  #: Additional chance of police stop per heat point above threshold.
)

# --- Skill System ---
SKILL_POINTS_PER_X_DAYS: int = (
    7  #: Number of days after which a skill point is awarded.
)
SKILL_MARKET_INTUITION_COST: int = 1  #: Cost in skill points for Market Intuition.
SKILL_COMPARTMENTALIZATION_COST: int = 3
COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT: float = 0.10
SKILL_GHOST_PROTOCOL_COST: int = 5
GHOST_PROTOCOL_DECAY_BOOST_PERCENT: float = 0.15
SKILL_DIGITAL_FOOTPRINT_COST: int = 2
SKILL_MARKET_ANALYST_COST: int = 2
DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT: float = 0.25
SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT: float = (
    0.25  # Additional reduction when both phone and skill are active
)

#: Definitions for player skills, including their names, costs, and descriptions.
SkillDefinitionValues = Union[str, int]  #: Type alias for values in SKILL_DEFINITIONS.
SKILL_DEFINITIONS: Dict[SkillID, Dict[str, SkillDefinitionValues]] = {
    SkillID.MARKET_INTUITION: {  #: Skill to see market price trends.
        "name": "Market Intuition",
        "cost": SKILL_MARKET_INTUITION_COST,
        "description": "Shows market price trends for drugs.",
    },
    SkillID.DIGITAL_FOOTPRINT: {
        "name": "Digital Footprint",
        "cost": SKILL_DIGITAL_FOOTPRINT_COST,
        "description": f"Reduces heat from crypto transactions by {DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT*100:.0f}%.",
    },
    SkillID.COMPARTMENTALIZATION: {  #: Skill to reduce heat from drug sales.
        "name": "Compartmentalization",
        "cost": SKILL_COMPARTMENTALIZATION_COST,
        "description": f"Reduces heat generated from drug sales by {COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT*100:.0f}%.",
    },
    SkillID.GHOST_PROTOCOL: {  #: Skill to increase daily heat decay.
        "name": "Ghost Protocol",
        "cost": SKILL_GHOST_PROTOCOL_COST,
        "description": f"Increases daily heat decay rate by {GHOST_PROTOCOL_DECAY_BOOST_PERCENT*100:.0f}%.",
    },
    SkillID.MARKET_ANALYST: {  #: Skill to show daily price change indicators.
        "name": "Market Analyst",
        "cost": SKILL_MARKET_ANALYST_COST,
        "description": "Shows if a drug's price has increased, decreased, or stayed stable since yesterday.",
    },
}

#: Definitions for purchasable upgrades.
UpgradeDefinitionValues = Union[
    str, float, List[float], List[int]
]  #: Type alias for values in UPGRADE_DEFINITIONS.
UPGRADE_DEFINITIONS: Dict[str, Dict[str, UpgradeDefinitionValues]] = {
    "SECURE_PHONE": {  #: Definition for the Secure Phone upgrade.
        "name": "Secure Phone",
        "cost": SECURE_PHONE_COST,
        "description": f"Reduces crypto heat by {SECURE_PHONE_HEAT_REDUCTION_PERCENT*100:.0f}%. Stacks with Digital Footprint.",
    },
    "EXPANDED_CAPACITY": {  #: Definition for Expanded Capacity upgrades.
        "name": "Expanded Capacity",
        "costs": CAPACITY_COSTS,
        "capacity_levels": CAPACITY_LEVELS,
        "description_template": "Increases inventory capacity to {next_capacity}. Cost: ${next_cost:,.0f}.",
        "description_maxed": "Inventory capacity is fully upgraded.",
    },
}

# --- Informant System ---
INFORMANT_TIP_COST_RUMOR: float = 50.0  #: Cost for a general rumor from the informant.
INFORMANT_TIP_COST_DRUG_INFO: float = 75.0  #: Cost for drug-specific information.
INFORMANT_TIP_COST_RIVAL_INFO: float = 100.0  #: Cost for information about rivals.
INFORMANT_TRUST_GAIN_PER_TIP: int = 5  #: Amount of trust gained per tip purchased.
INFORMANT_MAX_TRUST: int = 100  #: Maximum informant trust level.
INFORMANT_BETRAYAL_CHANCE: float = (
    0.03  #: Chance the informant betrays the player if trust is low.
)
INFORMANT_TRUST_THRESHOLD_FOR_BETRAYAL: int = (
    20  #: Informant trust must be at or below this for betrayal to be possible.
)
INFORMANT_BETRAYAL_UNAVAILABLE_DAYS: int = (
    7  #: Number of days informant is unavailable after a betrayal.
)
INFORMANT_BETRAYAL_HEAT_INCREASE: int = 5 #: Amount of heat generated in the region due to informant betrayal.

# --- Player-specific Random Event Parameters ---
MUGGING_CASH_LOSS_PERCENT_MIN: float = 0.05  #: Minimum percentage of cash lost during a mugging.
MUGGING_CASH_LOSS_PERCENT_MAX: float = 0.15  #: Maximum percentage of cash lost during a mugging.
SETUP_EVENT_HEAT_MIN: int = 15  #: Minimum heat generated from participating in a setup event.
SETUP_EVENT_HEAT_MAX: int = 40  #: Maximum heat generated from participating in a setup event.
SETUP_EVENT_MIN_CASH_FACTOR_FOR_BUY_DEAL: float = 0.5  #: Player must have cash >= deal_value * this_factor for a buy deal.
SETUP_EVENT_MIN_QUANTITY_FACTOR_FOR_SELL_DEAL: float = 0.25  #: Player must have quantity >= deal_quantity * this_factor for a sell deal.
SETUP_EVENT_MIN_PRICE_PER_UNIT: float = 1.0  #: Minimum price per unit for a setup event deal.
FORCED_SALE_MIN_QUANTITY_TO_SELL: int = 1  #: Minimum quantity of a drug to be sold in a forced sale.
FORCED_SALE_MIN_PRICE_PER_UNIT: float = 0.01  #: Minimum price per unit in a forced sale.
FORCED_FIRE_SALE_HEAT_INCREASE: int = 10 #: Heat increase from a forced fire sale event handled in UI app.

# --- Police Interaction ---
MAX_POLICE_STOP_CHANCE: float = 0.95  #: Maximum probability for a police stop event.
POLICE_STOP_SEVERITY_THRESHOLD_WARNING: float = 0.33  #: Random value below this results in a warning for Pygame UI.
POLICE_STOP_SEVERITY_THRESHOLD_FINE: float = 0.66  #: Random value below this (and above warning) results in a fine for Pygame UI.
POLICE_FINE_BASE_MIN: int = 100  #: Minimum base amount for a police fine for Pygame UI.
POLICE_FINE_BASE_MAX: int = 500  #: Maximum base amount for a police fine for Pygame UI.
POLICE_FINE_HEAT_DIVISOR: int = 20  #: Regional heat is divided by this to scale fine amounts for Pygame UI.

# Police Encounter Mechanics (used by Textual UI encounter logic, may be merged/harmonized with above later)
BRIBE_SUCCESS_MIN_CHANCE: float = 0.1  #: Minimum chance a bribe can succeed.
BRIBE_SUCCESS_MAX_CHANCE: float = 0.9  #: Maximum chance a bribe can succeed.
HEAT_INCREASE_CONFISCATION_MIN: int = 5  #: Min heat increase if drugs are confiscated.
HEAT_INCREASE_CONFISCATION_MAX: int = 15 #: Max heat increase if drugs are confiscated.
JAIL_CHANCE_BASE_IF_HEAT_THRESHOLD_MET: float = 0.2  #: Base chance of jail if heat is already high.
JAIL_CHANCE_MAX: float = 0.75  #: Maximum chance of being jailed during a police stop.
# Note: Other constants like BRIBE_MIN_COST, POLICE_STOP_HEAT_THRESHOLD etc. are assumed to exist from previous steps.
BRIBE_MIN_COST: float = 50.0 #: Minimum cost for a bribe.
BRIBE_BASE_COST_PERCENT_OF_CASH: float = 0.10 #: Bribe cost as a percentage of player's current cash.
BRIBE_SUCCESS_CHANCE_BASE: float = 0.60 #: Base chance for a bribe to succeed.
BRIBE_SUCCESS_CHANCE_HEAT_PENALTY: float = 0.01 #: Penalty to bribe success chance per heat point over threshold.
CONFISCATION_PERCENTAGE_MIN: float = 0.10 # Min percentage of a drug stack that can be confiscated.
CONFISCATION_PERCENTAGE_MAX: float = 0.50 # Max percentage of a drug stack that can be confiscated.
JAIL_TIME_DAYS_BASE: int = 3 # Base number of days player spends in jail.
JAIL_TIME_HEAT_MULTIPLIER: float = 0.1 # Additional days in jail per point of heat over threshold.
JAIL_CHANCE_HEAT_THRESHOLD: int = 70 # Heat threshold above which jail becomes a higher risk.
JAIL_CHANCE_IF_HIGH_TIER_DRUGS_FOUND: float = 0.25 # Additional chance of jail if high-tier drugs are found.


# --- Laundering ---
LAUNDERING_HEAT_FACTOR_PER_CASH_UNIT: float = 0.0005  #: Heat generated per unit of cash laundered (e.g., 0.05 for $100). If this seems high, adjust. Example: 100k cash * 0.0005 = 50 heat.

# --- Informant System Additions ---
INFORMANT_BETRAYAL_TRUST_LOSS: int = 10 #: Amount of trust lost when an informant betrays the player.

# --- Crypto Shop / Digital Arsenal ---
DIGITAL_ARSENAL_COST_DC: float = 15000.0 #: Cost in DrugCoin for the Digital Arsenal feature.
DC_STAKING_DAILY_RETURN_PERCENT: float = 0.001 #: Daily return percentage for staked DrugCoin.

# --- Corrupt Official ---
CORRUPT_OFFICIAL_HEAT_REDUCTION_AMOUNT: int = 20 #: Amount of heat reduced by bribing the corrupt official.
CORRUPT_OFFICIAL_BASE_BRIBE_COST: float = 1000.0 #: Base cost to bribe the corrupt official.
CORRUPT_OFFICIAL_BRIBE_COST_PER_HEAT_POINT: float = 50.0 #: Additional bribe cost per point of regional heat.


# --- Event Tier Targets ---
EVENT_TIER_TARGET_DEMAND_SPIKE: List[int] = [2, 3]  #: Drug tiers eligible for Demand Spike event.
EVENT_TIER_TARGET_SUPPLY_DISRUPTION: List[int] = [2, 3]  #: Drug tiers eligible for Supply Disruption.
EVENT_TIER_TARGET_CHEAP_STASH: List[int] = [1, 2]  #: Drug tiers eligible for Cheap Stash event.
EVENT_TIER_TARGET_THE_SETUP: List[int] = [2, 3]  #: Drug tiers eligible for The Setup event.

# --- Market Event Weights ---
MARKET_EVENT_WEIGHTS: Dict[str, int] = {  #: Weights for determining random market event frequency.
    "DEMAND_SPIKE": 3,
    "SUPPLY_DISRUPTION": 2,
    "POLICE_CRACKDOWN": 1,
    "CHEAP_STASH": 2,
    "THE_SETUP": 1,
    "RIVAL_BUSTED": 1,
    "DRUG_MARKET_CRASH": 1,
}

# --- Cryptocurrency ---
CRYPTO_PRICES_INITIAL: Dict[CryptoCoin, float] = (
    {  #: Initial prices for cryptocurrencies.
        CryptoCoin.BITCOIN: 100.0,
        CryptoCoin.ETHEREUM: 50.0,
        CryptoCoin.MONERO: 75.0,
        CryptoCoin.ZCASH: 25.0,
    CryptoCoin.DRUG_COIN: 10.0,
    }
)

CRYPTO_VOLATILITY: Dict[CryptoCoin, float] = {  #: Volatility factors for cryptocurrencies.
    CryptoCoin.BITCOIN: 0.05,
    CryptoCoin.ETHEREUM: 0.08,
    CryptoCoin.MONERO: 0.10,
    CryptoCoin.ZCASH: 0.15,
    CryptoCoin.DRUG_COIN: 0.20,
}

CRYPTO_MIN_PRICE: Dict[CryptoCoin, float] = {  #: Minimum prices for cryptocurrencies.
    CryptoCoin.BITCOIN: 20.0,
    CryptoCoin.ETHEREUM: 10.0,
    CryptoCoin.MONERO: 15.0,
    CryptoCoin.ZCASH: 5.0,
    CryptoCoin.DRUG_COIN: 1.0,
}

# --- Drug Market Initial Stock Levels ---
TIER1_STANDARD_INITIAL_STOCK: int = 10000 #: Initial stock for Tier 1 STANDARD quality drugs.
TIER_GT1_PURE_STOCK_RANGE: Tuple[int, int] = (10, 50)      #: Min/max stock range for Tier >1 PURE drugs.
TIER_GT1_STANDARD_STOCK_RANGE: Tuple[int, int] = (20, 100) #: Min/max stock range for Tier >1 STANDARD drugs.
TIER_GT1_CUT_STOCK_RANGE: Tuple[int, int] = (30, 150)      #: Min/max stock range for Tier >1 CUT drugs.

# --- Drug Quality Multipliers ---
QUALITY_MULT_CUT_BUY: float = 0.7       #: Buy price multiplier for CUT quality drugs.
QUALITY_MULT_STANDARD_BUY: float = 1.0  #: Buy price multiplier for STANDARD quality drugs.
QUALITY_MULT_PURE_BUY: float = 1.5      #: Buy price multiplier for PURE quality drugs.

QUALITY_MULT_CUT_SELL: float = 0.75     #: Sell price multiplier for CUT quality drugs.
QUALITY_MULT_STANDARD_SELL: float = 1.0 #: Sell price multiplier for STANDARD quality drugs.
QUALITY_MULT_PURE_SELL: float = 1.6     #: Sell price multiplier for PURE quality drugs.
QUALITY_MULT_DEFAULT: float = 1.0       #: Default multiplier if type or quality is not matched.

# --- Market Impact and Decay ---
PLAYER_MARKET_IMPACT_UNITS_BASE: int = 10             #: Number of units that form the base for calculating impact factor.
PLAYER_MARKET_IMPACT_FACTOR_PER_10_UNITS: float = 0.02 #: Base factor for player market impact per 10 units bought/sold.
PLAYER_BUY_IMPACT_MODIFIER_CAP: float = 1.25          #: Maximum modifier for player buying impact (prices go up).
# --- Market View Specifics ---
MARKET_PRICE_TREND_SENSITIVITY_UPPER: float = 1.02  #: Percentage increase (e.g., 1.02 for +2%) for price to be considered trending up.
MARKET_PRICE_TREND_SENSITIVITY_LOWER: float = 0.98  #: Percentage decrease (e.g., 0.98 for -2%) for price to be considered trending down.
PLAYER_SELL_IMPACT_MODIFIER_FLOOR: float = 0.75         #: Minimum modifier for player selling impact (prices go down).
PLAYER_MARKET_IMPACT_DECAY_RATE: float = 0.01         #: Rate at which player market impact modifiers decay towards 1.0 daily.

RIVAL_BASE_IMPACT_MAGNITUDE: float = 0.05             #: Base magnitude for AI rival market impact.
RIVAL_AGGRESSION_IMPACT_SCALE: float = 0.15           #: Scaling factor for AI rival impact based on aggression.
RIVAL_DEMAND_MODIFIER_CAP: float = 2.0                #: Maximum demand modifier AI rivals can cause.
RIVAL_SUPPLY_MODIFIER_FLOOR: float = 0.5                #: Minimum supply modifier (from player's perspective) AI rivals can cause.
RIVAL_COOLDOWN_MIN_DAYS: int = 1                      #: Minimum cooldown days between AI rival actions.
RIVAL_COOLDOWN_MAX_DAYS: int = 3                      #: Maximum cooldown days between AI rival actions.
RIVAL_ACTIVITY_DECAY_THRESHOLD_DAYS: int = 3          #: Number of days of inactivity after which AI rival market impact starts to decay.
RIVAL_MARKET_IMPACT_DECAY_RATE: float = 0.05          #: Amount by which AI rival demand modifier decays towards 1.0.
RIVAL_MARKET_IMPACT_SUPPLY_DECAY_MULTIPLIER: float = 0.1 #: Multiplier for AI rival supply modifier decay (e.g., if modifier is 0.8, it becomes 0.8 * (1+0.1)).

REGIONAL_HEAT_DECAY_PERCENTAGE: float = 0.05          #: Daily percentage by which regional heat decays.
MIN_REGIONAL_HEAT_DECAY_AMOUNT: int = 1               #: Minimum amount by which regional heat decays if heat > 0.


# --- Region Definitions ---
# Structure: (RegionName Enum, String Name, List of DrugDefinitionTuple)
# DrugDefinitionTuple: (DrugName str, BasePrice, MaxPrice, DemandFactor, QualitiesStockRanges)
# QualitiesStockRanges: {DrugQuality_Enum: (min_stock, max_stock)}
DrugDefinitionTuple = Tuple[
    str, int, int, int, Dict[DrugQuality, Tuple[int, int]]
]
RegionDefinitionTuple = Tuple[RegionName, str, List[DrugDefinitionTuple]]

REGION_DEFINITIONS: List[RegionDefinitionTuple] = [
    (
        RegionName.DOWNTOWN,
        RegionName.DOWNTOWN.value,
        [
            (
                "Weed",
                50,
                80,
                1,
                {DrugQuality.STANDARD: (100, 200)},
            ),  # DrugName will be converted to Enum or used as str
            (
                "Pills",
                100,
                150,
                2,
                {DrugQuality.STANDARD: (40, 80), DrugQuality.CUT: (60, 120)},
            ),
            (
                "Coke",
                1000,
                1500,
                3,
                {
                    DrugQuality.PURE: (10, 25),
                    DrugQuality.STANDARD: (15, 50),
                    DrugQuality.CUT: (20, 60),
                },
            ),
        ],
    ),
    (
        RegionName.DOCKS,
        RegionName.DOCKS.value,
        [
            ("Weed", 40, 70, 1, {DrugQuality.STANDARD: (100, 300)}),
            (
                "Speed",
                120,
                180,
                2,
                {DrugQuality.STANDARD: (30, 90), DrugQuality.CUT: (50, 100)},
            ),
            (
                "Heroin",
                600,
                900,
                3,
                {DrugQuality.PURE: (5, 15), DrugQuality.STANDARD: (10, 30)},
            ),
        ],
    ),
    (
        RegionName.SUBURBS,
        RegionName.SUBURBS.value,
        [
            ("Weed", 60, 100, 1, {DrugQuality.STANDARD: (20, 60)}),
            (
                "Pills",
                110,
                170,
                2,
                {DrugQuality.STANDARD: (20, 50), DrugQuality.PURE: (5, 15)},
            ),
        ],
    ),
    (
        RegionName.INDUSTRIAL,
        RegionName.INDUSTRIAL.value,
        [
            ("Weed", 45, 75, 1, {DrugQuality.STANDARD: (150, 250)}),
            (
                "Speed",
                110,
                170,
                2,
                {
                    DrugQuality.STANDARD: (40, 100),
                    DrugQuality.CUT: (60, 140),
                    DrugQuality.PURE: (10, 30),
                },
            ),
            (
                "Coke",
                950,
                1400,
                3,
                {
                    DrugQuality.PURE: (8, 20),
                    DrugQuality.STANDARD: (12, 40),
                    DrugQuality.CUT: (18, 55),
                },
            ),
        ],
    ),
    (
        RegionName.COMMERCIAL,
        RegionName.COMMERCIAL.value,
        [
            ("Weed", 55, 90, 1, {DrugQuality.STANDARD: (80, 150)}),
            (
                "Pills",
                105,
                160,
                2,
                {
                    DrugQuality.STANDARD: (25, 60),
                    DrugQuality.PURE: (8, 20),
                    DrugQuality.CUT: (40, 80),
                },
            ),
            (
                "Heroin",
                580,
                850,
                3,
                {
                    DrugQuality.PURE: (3, 12),
                    DrugQuality.STANDARD: (8, 25),
                    DrugQuality.CUT: (15, 40),
                },
            ),
        ],
    ),
    (
        RegionName.UNIVERSITY_HILLS,
        RegionName.UNIVERSITY_HILLS.value,
        [
            ("Weed", 70, 110, 1, {DrugQuality.STANDARD: (50, 100)}),
            (
                "Pills",
                120,
                180,
                2,
                {DrugQuality.STANDARD: (30, 60), DrugQuality.PURE: (10, 20)},
            ),
            (
                "Speed",
                130,
                190,
                2,
                {DrugQuality.CUT: (40, 80), DrugQuality.STANDARD: (20, 50)},
            ),
        ],
    ),
    (
        RegionName.RIVERSIDE,
        RegionName.RIVERSIDE.value,
        [
            ("Weed", 40, 65, 1, {DrugQuality.STANDARD: (120, 250)}),
            (
                "Heroin",
                550,
                800,
                3,
                {DrugQuality.STANDARD: (10, 25), DrugQuality.CUT: (15, 35)},
            ),
        ],
    ),
    (
        RegionName.AIRPORT_DISTRICT,
        RegionName.AIRPORT_DISTRICT.value,
        [
            (
                "Coke",
                1100,
                1600,
                3,
                {DrugQuality.PURE: (15, 30), DrugQuality.STANDARD: (20, 40)},
            ),
            (
                "Speed",
                150,
                220,
                2,
                {DrugQuality.PURE: (20, 40), DrugQuality.STANDARD: (30, 60)},
            ),
        ],
    ),
    (
        RegionName.OLD_TOWN,
        RegionName.OLD_TOWN.value,
        [
            (
                "Pills",
                90,
                140,
                2,
                {DrugQuality.STANDARD: (50, 100), DrugQuality.CUT: (70, 130)},
            ),
            (
                "Heroin",
                620,
                920,
                3,
                {
                    DrugQuality.CUT: (20, 50),
                    DrugQuality.STANDARD: (10, 30),
                    DrugQuality.PURE: (5, 10),
                },
            ),
        ],
    ),
]
