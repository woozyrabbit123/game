from typing import Optional
from ...core.enums import DrugQuality


def parse_drug_quality(quality_str: str) -> Optional[DrugQuality]:
    """Convert a string to DrugQuality enum value"""
    try:
        return DrugQuality[quality_str.upper()]
    except (KeyError, AttributeError):
        return None

# Forward declarations for type hinting if curses is not available in all environments
if False: # Prevent runtime import, for type checking only
    import curses

from ...game_state import GameState # For type hinting GameState
from ...core.player_inventory import PlayerInventory # For type hinting PlayerInventory
from ...core.region import Region # For type hinting Region
# Import constants for debt amounts and due days
from ...narco_configs import (
    DEBT_PAYMENT_1_AMOUNT, DEBT_PAYMENT_1_DUE_DAY,
    DEBT_PAYMENT_2_AMOUNT, DEBT_PAYMENT_2_DUE_DAY,
    DEBT_PAYMENT_3_AMOUNT, DEBT_PAYMENT_3_DUE_DAY
)


def display_daily_status_header(
    header_win: "curses._CursesWindow",
    game_state: "GameState",
    player_inventory: "PlayerInventory",
) -> None:
    """Display the daily status header with game state information"""
    header_win.clear()
    # header_win.bkgd(' ', curses.color_pair(2)) # bkgd might not be what we want if using pairs correctly

    max_y, max_x = header_win.getmaxyx()

    current_player_region_obj: Optional["Region"] = game_state.get_current_player_region()
    current_region_name_str: str = "Unknown"
    if current_player_region_obj and hasattr(current_player_region_obj, 'name'):
        current_region_name_str = current_player_region_obj.name.value if hasattr(current_player_region_obj.name, 'value') else str(current_player_region_obj.name)

    current_heat_val: int = current_player_region_obj.current_heat if current_player_region_obj else 0

    status_line1 = f"Day: {game_state.current_day} | Cash: ${player_inventory.cash:,.2f} | Region: {current_region_name_str} | Load: {player_inventory.current_load}/{player_inventory.max_capacity}"
    status_line2 = f"Heat: {current_heat_val}"

    debt_status_str = "Debt: "
    if player_inventory.debt_payment_3_paid:
        debt_status_str += "Cleared!"
    elif player_inventory.debt_payment_2_paid:
        debt_status_str += f"Final payment of ${DEBT_PAYMENT_3_AMOUNT:,.0f} due Day {DEBT_PAYMENT_3_DUE_DAY}."
    elif player_inventory.debt_payment_1_paid:
        debt_status_str += f"Payment 2 of ${DEBT_PAYMENT_2_AMOUNT:,.0f} due Day {DEBT_PAYMENT_2_DUE_DAY}."
    else:
        debt_status_str += f"Payment 1 of ${DEBT_PAYMENT_1_AMOUNT:,.0f} due Day {DEBT_PAYMENT_1_DUE_DAY}."

    # Centering the status lines
    start_x_line1: int = max(0, (max_x - len(status_line1)) // 2)
    start_x_line2: int = max(0, (max_x - len(status_line2)) // 2)
    start_x_debt: int = max(0, (max_x - len(debt_status_str)) // 2)

    # Assuming color pair 2 is for header text, ensure it's initialized in main_curses_app
    # curses.color_pair(2) should be defined with foreground and background
    header_win.attron(curses.color_pair(2))
    if max_y > 1 and start_x_line1 >=0 : header_win.addstr(1, start_x_line1, status_line1)
    if max_y > 2 and start_x_line2 >=0 : header_win.addstr(2, start_x_line2, status_line2)
    if max_y > 3 and start_x_debt >=0 : header_win.addstr(3, start_x_debt, debt_status_str)
    header_win.attroff(curses.color_pair(2))

    header_win.border()
    header_win.noutrefresh()
