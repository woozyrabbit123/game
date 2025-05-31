"""Game state management module."""
import random
from typing import Dict, List

from .core.enums import CryptoCoin, DrugQuality, RegionName
from .core.ai_rival import AIRival
from .core.region import Region
from . import game_configs

# Initialize with placeholder values, will be properly set at game start
current_crypto_prices: Dict[CryptoCoin, float] = {}
ai_rivals: List[AIRival] = []
all_regions: Dict[RegionName, Region] = {}
current_player_region: Region = None
informant_unavailable_until_day: Optional[int] = None

def get_game_state():
    """Get the current game state."""
    return {
        'crypto_prices': current_crypto_prices,
        'ai_rivals': ai_rivals,
        'informant_unavailable_until_day': informant_unavailable_until_day
    }

def initialize_game_state():
    """Initialize the game state with default values."""
    global current_crypto_prices, ai_rivals, informant_unavailable_until_day
    current_crypto_prices = game_configs.CRYPTO_PRICES_INITIAL.copy()
    ai_rivals = []
    informant_unavailable_until_day = None

def initialize_crypto_prices(initial_prices: Dict[CryptoCoin, float]): # Use CryptoCoin as key type
    """Sets the initial prices for cryptocurrencies."""
    global current_crypto_prices
    current_crypto_prices = initial_prices.copy()

def update_daily_crypto_prices(volatility_map: Dict[CryptoCoin, float], min_prices_map: Dict[CryptoCoin, float]): # Use CryptoCoin
    """Updates cryptocurrency prices based on their volatility."""
    global current_crypto_prices
    if not current_crypto_prices: 
        print("Warning: Crypto prices accessed before initialization.")
        return

    for coin, price in current_crypto_prices.items():
        if coin in volatility_map:
            change_percent = random.uniform(-volatility_map[coin], volatility_map[coin])
            new_price = price * (1 + change_percent)
            min_price = min_prices_map.get(coin, 0.01) 
            new_price = max(min_price, new_price) 
            current_crypto_prices[coin] = round(new_price, 2)

def initialize_regions():
    """Initialize all game regions with their drug markets."""
    global all_regions
    
    # Initialize Downtown region
    downtown = Region(RegionName.DOWNTOWN.value)
    downtown.initialize_drug_market("Weed", 50, 80, 1, {
        DrugQuality.STANDARD: random.randint(100,200)
    })
    downtown.initialize_drug_market("Pills", 100, 150, 2, { 
        DrugQuality.STANDARD: random.randint(40,80), 
        DrugQuality.CUT: random.randint(60,120)
    })
    downtown.initialize_drug_market("Coke", 1000, 1500, 3, { 
        DrugQuality.PURE: random.randint(10,25), 
        DrugQuality.STANDARD: random.randint(15,50), 
        DrugQuality.CUT: random.randint(20,60)
    })
    all_regions[RegionName.DOWNTOWN] = downtown

    # Initialize The Docks region
    the_docks = Region(RegionName.DOCKS.value)
    the_docks.initialize_drug_market("Weed", 40, 70, 1, {
        DrugQuality.STANDARD: random.randint(100,300)
    })
    the_docks.initialize_drug_market("Speed", 120, 180, 2, { 
        DrugQuality.STANDARD: random.randint(30,90), 
        DrugQuality.CUT: random.randint(50,100)
    })
    the_docks.initialize_drug_market("Heroin", 600, 900, 3, { 
        DrugQuality.PURE: random.randint(5,15), 
        DrugQuality.STANDARD: random.randint(10,30)
    })
    all_regions[RegionName.DOCKS] = the_docks

    # Initialize Suburbia region
    suburbia = Region(RegionName.SUBURBS.value)
    suburbia.initialize_drug_market("Weed", 60, 100, 1, {
        DrugQuality.STANDARD: random.randint(20,60)
    })
    suburbia.initialize_drug_market("Pills", 110, 170, 2, {
        DrugQuality.STANDARD: random.randint(20,50), 
        DrugQuality.PURE: random.randint(5,15) 
    })
    all_regions[RegionName.SUBURBS] = suburbia

    # Initialize Industrial District region
    industrial = Region(RegionName.INDUSTRIAL.value)
    industrial.initialize_drug_market("Weed", 45, 75, 1, {
        DrugQuality.STANDARD: random.randint(150,250)
    })
    industrial.initialize_drug_market("Speed", 110, 170, 2, { 
        DrugQuality.STANDARD: random.randint(40,100), 
        DrugQuality.CUT: random.randint(60,140),
        DrugQuality.PURE: random.randint(10,30)
    })
    industrial.initialize_drug_market("Coke", 950, 1400, 3, { 
        DrugQuality.PURE: random.randint(8,20), 
        DrugQuality.STANDARD: random.randint(12,40), 
        DrugQuality.CUT: random.randint(18,55)
    })
    all_regions[RegionName.INDUSTRIAL] = industrial

    # Initialize Commercial District region  
    commercial = Region(RegionName.COMMERCIAL.value)
    commercial.initialize_drug_market("Weed", 55, 90, 1, {
        DrugQuality.STANDARD: random.randint(80,150)
    })
    commercial.initialize_drug_market("Pills", 105, 160, 2, { 
        DrugQuality.STANDARD: random.randint(25,60), 
        DrugQuality.PURE: random.randint(8,20),
        DrugQuality.CUT: random.randint(40,80)
    })
    commercial.initialize_drug_market("Heroin", 580, 850, 3, { 
        DrugQuality.PURE: random.randint(3,12), 
        DrugQuality.STANDARD: random.randint(8,25),
        DrugQuality.CUT: random.randint(15,40)
    })
    all_regions[RegionName.COMMERCIAL] = commercial
    
    # Initialize all region markets
    for region in all_regions.values():
        region.restock_market()

def initialize_global_state(game_configs_module):
    """Initialize all game state components."""
    # Ensure game_configs is available if not already by direct import
    # This is more of a structural note; actual import should be at module top.
    # from . import game_configs # Ensure it's available if passed as module
    initialize_game_state()
    initialize_regions()
    
def set_current_player_region(region: Region):
    """Set the current player region."""
    global current_player_region
    current_player_region = region