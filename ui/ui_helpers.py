from typing import Optional
from core.enums import DrugQuality

def parse_drug_quality(quality_str: str) -> Optional[DrugQuality]:
    """Convert a string to DrugQuality enum value"""
    try:
        return DrugQuality[quality_str.upper()]
    except (KeyError, AttributeError):
        return None

# def print_market_header(target_window, region_name: str, show_trend: bool = False):
#     """Print the market display header with optional trend column"""
#     trend_col = " T " if show_trend else ""
#     header = f"{'*':<1}{trend_col}{'Drug':<9} {'Quality':<9} {'Buy Price':<10} {'Sell Price':<11} {'Stock':<10}"
#     target_window.addstr(0, 0, header, curses.color_pair(2) | curses.A_BOLD)
#     target_window.addstr(1, 0, "-" * len(header), curses.color_pair(2))

# def display_daily_status_header(header_win, current_day: int, player_inventory, 
#                               debt_payment_1_paid: bool, debt_payment_2_paid: bool, 
#                               debt_payment_3_paid: bool):
#     """Display the daily status header with game state information"""
#     header_win.clear()
#     header_win.bkgd(' ', curses.color_pair(2))
#     header_win.addstr(0, 0, f"=== Day {current_day} === Location: {player_inventory.current_region.name if hasattr(player_inventory, 'current_region') else '?'} ===", curses.color_pair(2) | curses.A_BOLD)
#     # Debt status
#     debt_status = []
#     if not debt_payment_1_paid:
#         debt_status.append(f"Debt Payment 1: $25000.00 due Day 15")
#     if debt_payment_1_paid and not debt_payment_2_paid:
#         debt_status.append(f"Debt Payment 2: $30000.00 due Day 30")
#     if debt_payment_1_paid and debt_payment_2_paid and not debt_payment_3_paid:
#         debt_status.append(f"Debt Payment 3: $20000.00 due Day 45")
#     if debt_status:
#         header_win.addstr(1, 0, "Debt Status: " + ", ".join(debt_status), curses.color_pair(2))
#     # Crypto prices
#     header_win.addstr(2, 0, "Crypto Prices:", curses.color_pair(2) | curses.A_BOLD)
#     # Assume game_state.current_crypto_prices is available
#     import game_state
#     for idx, (coin, price) in enumerate(sorted(game_state.current_crypto_prices.items())):
#         header_win.addstr(3, idx * 15, f"{coin}: ${price:.2f}", curses.color_pair(2))
#     if getattr(player_inventory, 'pending_laundered_sc_arrival_day', None) is not None:
#         header_win.addstr(4, 0, f"Pending: {player_inventory.pending_laundered_sc:.4f} SC arriving Day {player_inventory.pending_laundered_sc_arrival_day}", curses.color_pair(2))
#     header_win.noutrefresh()
