from enum import Enum

class DrugQuality(Enum):
    CUT = 1
    STANDARD = 2
    PURE = 3

class DrugName(Enum):
    WEED = "Weed"
    PILLS = "Pills"
    COKE = "Coke"
    SPEED = "Speed"
    HEROIN = "Heroin"

class RegionName(Enum):
    DOWNTOWN = "Downtown"
    SUBURBS = "Suburbs"
    INDUSTRIAL = "Industrial District"
    DOCKS = "Docks"
    COMMERCIAL = "Commercial District"

class CryptoCoin(Enum):
    BITCOIN = "Bitcoin"
    ETHEREUM = "Ethereum"
    MONERO = "Monero"
    ZCASH = "ZCash"
    DRUG_COIN = "DrugCoin"