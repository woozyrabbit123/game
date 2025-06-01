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

    WEED = "Weed"
    PILLS = "Pills"
    COKE = "Coke"
    SPEED = "Speed"
    HEROIN = "Heroin"


class RegionName(Enum):
    """Lists all explorable region names in the game."""

    DOWNTOWN = "Downtown"
    SUBURBS = "Suburbs"
    INDUSTRIAL = "Industrial District"
    DOCKS = "Docks"
    COMMERCIAL = "Commercial District"
    UNIVERSITY_HILLS = "University Hills"
    RIVERSIDE = "Riverside"
    AIRPORT_DISTRICT = "Airport District"
    OLD_TOWN = "Old Town"


class CryptoCoin(Enum):
    """Lists all types of cryptocurrencies available in the game."""

    BITCOIN = "Bitcoin"
    ETHEREUM = "Ethereum"
    MONERO = "Monero"
    ZCASH = "ZCash"
    DRUG_COIN = "DrugCoin"


class SkillID(Enum):
    """Unique identifiers for player skills."""

    MARKET_INTUITION = "MARKET_INTUITION"  #: Skill to see market price trends.
    DIGITAL_FOOTPRINT = (
        "DIGITAL_FOOTPRINT"  #: Skill to reduce heat from crypto transactions.
    )
    COMPARTMENTALIZATION = "COMPARTMENTALIZATION"
    GHOST_PROTOCOL = "GHOST_PROTOCOL"
    MARKET_ANALYST = "MARKET_ANALYST"  #: Skill to see daily price change indicators.
    GHOST_NETWORK_ACCESS = (
        "GHOST_NETWORK_ACCESS"  #: Skill to access special crypto shop.
    )


class EventType(Enum):
    """Defines the types of events that can occur in the game market or to the player."""

    DEMAND_SPIKE = "DEMAND_SPIKE"  #: A drug's demand and price temporarily increase.
    SUPPLY_DISRUPTION = "SUPPLY_DISRUPTION"  #: A drug's stock is temporarily reduced.
    POLICE_CRACKDOWN = "POLICE_CRACKDOWN"
    CHEAP_STASH = "CHEAP_STASH"
    THE_SETUP = "THE_SETUP"
    RIVAL_BUSTED = "RIVAL_BUSTED"  #: An AI rival is temporarily out of action.
    DRUG_MARKET_CRASH = "DRUG_MARKET_CRASH"  #: A drug's price plummets temporarily.
    MUGGING = "MUGGING"  #: Player gets mugged and loses cash or items.
    INFORMANT_BETRAYAL = "INFORMANT_BETRAYAL"  #: Informant betrays the player, causing negative consequences.
    BLACK_MARKET_OPPORTUNITY = "BLACK_MARKET_OPPORTUNITY"  #: Opportunity to buy drugs at a significant discount.
    FORCED_FIRE_SALE = (
        "FORCED_FIRE_SALE"  #: Player is forced to sell some drugs at a penalty.
    )
