"""
Defines various enumerations used throughout the game.

These enums provide a controlled set of values for game concepts like
drug quality, drug names, region names, cryptocurrency types, skill IDs,
and event types, improving code clarity and preventing errors from typos.
"""

from enum import Enum


class DrugQuality(Enum):
    """Represents the quality of a drug (e.g., affecting price and effects)."""

    CUT = 1
    STANDARD = 2
    PURE = 3


class DrugName(Enum):
    """Lists all available drug names in the game."""

    WEED = 'Weed'
    PILLS = 'Pills'
    COKE = 'Coke'
    SPEED = 'Speed'
    HEROIN = 'Heroin'


class RegionName(Enum):
    """Lists all explorable region names in the game."""

    DOWNTOWN = 'Downtown'
    SUBURBS = 'Suburbs'
    INDUSTRIAL = 'Industrial District'
    DOCKS = 'Docks'
    COMMERCIAL = 'Commercial District'
    UNIVERSITY_HILLS = 'University Hills'
    RIVERSIDE = 'Riverside'
    AIRPORT_DISTRICT = 'Airport District'
    OLD_TOWN = 'Old Town'


class CryptoCoin(Enum):
    """Lists all types of cryptocurrencies available in the game."""

    BITCOIN = 'Bitcoin'
    ETHEREUM = 'Ethereum'
    MONERO = 'Monero'
    ZCASH = 'ZCash'
    DRUG_COIN = 'DrugCoin'


class SkillID(Enum):
    """Unique identifiers for player skills."""

    MARKET_INTUITION = 'MARKET_INTUITION'  #: See market price trends.
    DIGITAL_FOOTPRINT = (
        'DIGITAL_FOOTPRINT'  #: Reduce heat from crypto transactions.
    )
    COMPARTMENTALIZATION = 'COMPARTMENTALIZATION'  #: Reduce heat from sales.
    GHOST_PROTOCOL = 'GHOST_PROTOCOL'  #: Increase daily heat decay.
    MARKET_ANALYST = 'MARKET_ANALYST'  #: See daily price change indicators.
    GHOST_NETWORK_ACCESS = (
        'GHOST_NETWORK_ACCESS'  #: Access special crypto shop.
    )

    # Street Smarts Tier 2 & 3
    ADVANCED_MARKET_ANALYSIS = 'ADVANCED_MARKET_ANALYSIS' # Street Smarts T2
    MASTER_NEGOTIATOR = 'MASTER_NEGOTIATOR' # Street Smarts T3

    # Network Tier 1, 2 & 3
    BASIC_CONNECTIONS = 'BASIC_CONNECTIONS' # Network T1
    EXPANDED_NETWORK = 'EXPANDED_NETWORK' # Network T2
    SYNDICATE_INFLUENCE = 'SYNDICATE_INFLUENCE' # Network T3

    # OpSec Tiers are already defined:
    # DIGITAL_FOOTPRINT is OpSec T1
    # COMPARTMENTALIZATION is OpSec T2
    # GHOST_PROTOCOL is OpSec T3


class ContactID(Enum):
    """Unique identifiers for player contacts."""
    INFORMANT = "INFORMANT"
    TECH_CONTACT = "TECH_CONTACT"
    CORRUPT_OFFICIAL = "CORRUPT_OFFICIAL"
    THE_FORGER = "THE_FORGER"
    LOGISTICS_EXPERT = "LOGISTICS_EXPERT"

class QuestID(Enum):
    """Unique identifiers for player quests."""
    FORGER_SUPPLY_RUN = "FORGER_SUPPLY_RUN"
    # Add other quest IDs here as they are created


class EventType(Enum):
    """Defines the types of events that can occur in the game market or to the player."""

    DEMAND_SPIKE = 'DEMAND_SPIKE'  #: Drug's demand and price temporarily increase.
    SUPPLY_DISRUPTION = 'SUPPLY_DISRUPTION'  #: Drug's stock temporarily reduced.
    POLICE_CRACKDOWN = 'POLICE_CRACKDOWN'  #: Increased police presence and heat.
    CHEAP_STASH = 'CHEAP_STASH'  #: Opportunity to buy a drug cheaply.
    THE_SETUP = 'THE_SETUP'  #: A risky but potentially profitable deal.
    RIVAL_BUSTED = 'RIVAL_BUSTED'  #: An AI rival is temporarily out of action.
    DRUG_MARKET_CRASH = 'DRUG_MARKET_CRASH'  #: Drug's price plummets temporarily.
    MUGGING = 'MUGGING'  #: Player gets mugged and loses cash or items.
    INFORMANT_BETRAYAL = (
        'INFORMANT_BETRAYAL'  #: Informant betrays player, negative consequences.
    )
    BLACK_MARKET_OPPORTUNITY = (
        'BLACK_MARKET_OPPORTUNITY'  #: Buy drugs at a significant discount.
    )
    FORCED_FIRE_SALE = (
        'FORCED_FIRE_SALE'  #: Player forced to sell drugs at a penalty.
    )
    TURF_WAR = 'TURF_WAR' #: Conflict between factions affecting a region.

    # New Opportunity Events
    RIVAL_STASH_LEAKED = 'RIVAL_STASH_LEAKED' #: Opportunity to steal from a rival.
    URGENT_DELIVERY = 'URGENT_DELIVERY' #: Opportunity for a high-paying quick delivery.
    EXPERIMENTAL_DRUG_BATCH = 'EXPERIMENTAL_DRUG_BATCH' #: Opportunity to buy a risky new drug batch.
