import random
from typing import Dict

# Initialize with placeholder values, will be properly set at game start
current_crypto_prices: Dict[str, float] = {}

def initialize_crypto_prices(initial_prices: Dict[str, float]):
    """Sets the initial prices for cryptocurrencies."""
    global current_crypto_prices
    current_crypto_prices = initial_prices.copy()

def update_daily_crypto_prices(volatility_map: Dict[str, float], min_prices_map: Dict[str, float]):
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