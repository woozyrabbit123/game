import random 
from typing import List, Dict 
import curses
import curses.textpad
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.game_configs import (
    PLAYER_STARTING_CASH, PLAYER_MAX_CAPACITY, 
    DEBT_PAYMENT_1_AMOUNT, DEBT_PAYMENT_1_DUE_DAY,
    DEBT_PAYMENT_2_AMOUNT, DEBT_PAYMENT_2_DUE_DAY,
    DEBT_PAYMENT_3_AMOUNT, DEBT_PAYMENT_3_DUE_DAY,
    CRYPTO_PRICES_INITIAL, CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE,
    DIGITAL_ARSENAL_WARNING_HEAT_THRESHOLD
)

from src.core.enums import DrugQuality, DrugName, RegionName, CryptoCoin
from src.core.player_inventory import PlayerInventory
from src.core.region import Region
from src.core.ai_rival import AIRival
from src.core.market_event import MarketEvent
from src.game_state import GameState # Updated import

from src.mechanics.event_manager import update_active_events, trigger_random_market_event # Keep, may need GameState
from src.ui_textual.components.text_ui_handlers import (
    handle_view_market, handle_view_inventory,
    handle_travel, handle_view_tech_contact, handle_skills_view, # These will need GameState
    handle_upgrades_view, handle_blocking_event_popup_view,
    handle_game_over_view, handle_informant_view,
    handle_buy_drug, handle_sell_drug, handle_advance_day,
    handle_view_skills, handle_view_upgrades,
    handle_talk_to_informant, handle_meet_corrupt_official
)
from src.ui_textual.components.ui_helpers import display_daily_status_header # Will need GameState
# import src.game_state as game_state # Old import removed


def main_curses_app(stdscr):
    # --- Curses Initialization ---
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)   # Default
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLUE)  # Header
    curses.init_pair(3, curses.COLOR_GREEN, -1)   # Success
    curses.init_pair(4, curses.COLOR_RED, -1)     # Error/Warning
    curses.init_pair(5, curses.COLOR_CYAN, -1)    # Menu highlight
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Input

    # --- Window Layout ---
    max_y, max_x = stdscr.getmaxyx()
    header_height = 5
    log_height = 4
    input_height = 2
    content_height = max_y - (header_height + log_height + input_height)
    content_width = max_x

    header_win = curses.newwin(header_height, max_x, 0, 0)
    content_pad = curses.newpad(1000, content_width)
    log_win = curses.newwin(log_height, max_x, header_height + content_height, 0)
    input_win = curses.newwin(input_height, max_x, header_height + content_height + log_height, 0)

    # --- Game State Initialization ---
    game_state_instance = GameState()
    player_inventory = PlayerInventory(max_capacity=PLAYER_MAX_CAPACITY, starting_cash=PLAYER_STARTING_CASH)

    # Debt payment status - could be part of player_inventory or game_state_instance if needed elsewhere
    debt_payment_1_paid = False
    debt_payment_2_paid = False
    debt_payment_3_paid = False

    # Initialize AI rivals and assign to game_state_instance
    ai_rivals_list: List[AIRival] = [
        AIRival(name="The Chemist", primary_drug=DrugName.PILLS, primary_region_name=RegionName.DOWNTOWN,
                aggression=0.6, activity_level=0.7),
        AIRival(name="Silas", primary_drug=DrugName.COKE, primary_region_name=RegionName.DOWNTOWN,
                aggression=0.8, activity_level=0.5),
        AIRival(name="Dockmaster Jones", primary_drug=DrugName.SPEED, primary_region_name=RegionName.DOCKS,
                aggression=0.5, activity_level=0.6),
        AIRival(name="Shady Stan", primary_drug=DrugName.HEROIN, primary_region_name=RegionName.DOCKS,
                aggression=0.7, activity_level=0.4)
    ]
    game_state_instance.ai_rivals = ai_rivals_list

    # Set initial player region
    initial_region_name = RegionName.DOWNTOWN
    game_state_instance.set_current_player_region(initial_region_name)
    # current_player_region will be obtained via game_state_instance.get_current_player_region() when needed by handlers

    # --- Log Buffer ---
    log_buffer = []
    def add_log(msg, color=1):
        log_buffer.insert(0, (msg, color))
        if len(log_buffer) > log_height:
            log_buffer.pop()
        log_win.clear()
        for i, (m, c) in enumerate(reversed(log_buffer)):
            log_win.addstr(i, 0, m[:max_x-1], curses.color_pair(c))
        log_win.noutrefresh()

    # --- Main Loop ---
    try:
        while True:
            current_day = game_state_instance.current_day # Get current day from instance
            current_player_region_obj = game_state_instance.get_current_player_region() # Get current region object

            # --- Draw Header ---
            header_win.clear()
            display_daily_status_header(header_win, game_state_instance, player_inventory, debt_payment_1_paid, debt_payment_2_paid, debt_payment_3_paid)
            header_win.noutrefresh()

            # --- Debt Collector Payment Logic ---
            if not debt_payment_1_paid and current_day == DEBT_PAYMENT_1_DUE_DAY:
                log_win.clear()
                if player_inventory.cash >= DEBT_PAYMENT_1_AMOUNT:
                    player_inventory.cash -= DEBT_PAYMENT_1_AMOUNT
                    debt_payment_1_paid = True
                    log_win.addstr(0, 0, f"Debt Collector payment 1 made!", curses.color_pair(3))
                else:
                    log_win.addstr(0, 0, "GAME OVER: You failed to pay the Debt Collector!", curses.color_pair(4))
                    log_win.noutrefresh(); curses.doupdate()
                    input_win.clear(); input_win.addstr(0,0,"Press any key to exit.",curses.color_pair(4)); input_win.refresh(); input_win.getkey()
                    break
                log_win.noutrefresh(); curses.doupdate(); input_win.clear(); input_win.addstr(0,0,"Press any key to continue.",curses.color_pair(3)); input_win.refresh(); input_win.getkey()

            if debt_payment_1_paid and not debt_payment_2_paid and current_day == DEBT_PAYMENT_2_DUE_DAY:
                log_win.clear()
                if player_inventory.cash >= DEBT_PAYMENT_2_AMOUNT:
                    player_inventory.cash -= DEBT_PAYMENT_2_AMOUNT
                    debt_payment_2_paid = True
                    log_win.addstr(0, 0, f"Debt Collector payment 2 made!", curses.color_pair(3))
                else:
                    log_win.addstr(0, 0, "GAME OVER: You failed to pay the Debt Collector!", curses.color_pair(4))
                    log_win.noutrefresh(); curses.doupdate()
                    input_win.clear(); input_win.addstr(0,0,"Press any key to exit.",curses.color_pair(4)); input_win.refresh(); input_win.getkey()
                    break
                log_win.noutrefresh(); curses.doupdate(); input_win.clear(); input_win.addstr(0,0,"Press any key to continue.",curses.color_pair(3)); input_win.refresh(); input_win.getkey()

            if debt_payment_1_paid and debt_payment_2_paid and not debt_payment_3_paid and current_day == DEBT_PAYMENT_3_DUE_DAY:
                log_win.clear()
                if player_inventory.cash >= DEBT_PAYMENT_3_AMOUNT:
                    player_inventory.cash -= DEBT_PAYMENT_3_AMOUNT
                    debt_payment_3_paid = True
                    log_win.addstr(0, 0, f"Final Debt Collector payment made! You are free!", curses.color_pair(3) | curses.A_BOLD)
                    log_win.noutrefresh(); curses.doupdate(); input_win.clear(); input_win.addstr(0,0,"Press any key to celebrate and exit.",curses.color_pair(3)); input_win.refresh(); input_win.getkey()
                    break
                else:
                    log_win.addstr(0, 0, "GAME OVER: You failed to pay the Debt Collector!", curses.color_pair(4))
                    log_win.noutrefresh(); curses.doupdate(); input_win.clear(); input_win.addstr(0,0,"Press any key to exit.",curses.color_pair(4)); input_win.refresh(); input_win.getkey()
                    break

            # --- Main Menu Display ---
            content_pad.clear()
            menu_lines = [
                "1. View Market", "2. View Inventory", "3. Buy Drug", "4. Sell Drug", 
                "5. Travel",
                "6. Skills", "7. Upgrades", "8. Talk to Informant", "9. Meet Corrupt Official",
                "A. Advance Day",
                "0. Exit Game"
            ]
            # Dynamic menu items would also use game_state_instance
            # e.g. if any(event.event_type == "THE_SETUP" for event in current_player_region_obj.active_market_events):
            # e.g. if "GHOST_NETWORK_ACCESS" in player_inventory.unlocked_skills:

            for idx, line in enumerate(menu_lines):
                content_pad.addstr(idx, 0, line, curses.color_pair(5))
            
            sminrow_pad = header_height
            smaxrow_pad = max_y - log_height - input_height - 1 
            smincol_pad = 0
            smaxcol_pad = max_x - 1
            if smaxrow_pad < sminrow_pad: smaxrow_pad = sminrow_pad
            content_pad.noutrefresh(0, 0, sminrow_pad, smincol_pad, smaxrow_pad, smaxcol_pad)

            # --- Input ---
            input_win.clear()
            input_win.addstr(0, 0, "Enter choice: ", curses.color_pair(6))
            input_win.refresh()
            curses.echo()
            choice = input_win.getstr(0, 14, 10).decode().strip()
            curses.noecho()

            # --- Handle Choice (pass game_state_instance to handlers) ---
            if choice == "1":
                handle_view_market(game_state_instance, player_inventory, content_pad, log_win, input_win)
            elif choice == "2":
                handle_view_inventory(game_state_instance, player_inventory, content_pad, log_win, input_win) # Assuming inventory might need game_state for context
            elif choice == "3":
                handle_buy_drug(game_state_instance, player_inventory, content_pad, log_win, input_win)
            elif choice == "4":
                handle_sell_drug(game_state_instance, player_inventory, content_pad, log_win, input_win)
            elif choice == "5":
                handle_travel(game_state_instance, player_inventory, content_pad, log_win, input_win)
            elif choice == "A" or choice == "a":
                # Advance day logic is now primarily within GameState or called by a handler that uses GameState
                handle_advance_day(game_state_instance, player_inventory, content_pad, log_win, input_win)
                # game_state_instance.current_day += 1 # This should be handled by handle_advance_day or a method in GameState
            elif choice == "6":
                handle_view_skills(game_state_instance, player_inventory, content_pad, log_win, input_win)
            elif choice == "7":
                handle_view_upgrades(game_state_instance, player_inventory, content_pad, log_win, input_win)
            elif choice == "8":
                handle_talk_to_informant(game_state_instance, player_inventory, content_pad, log_win, input_win)
            elif choice == "9":
                handle_meet_corrupt_official(game_state_instance, player_inventory, content_pad, log_win, input_win)
            elif choice == "0":
                add_log("Exiting game. Goodbye!", 3)
                break
            else:
                add_log("Invalid choice.", 4)
            curses.doupdate()
    finally:
        curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main_curses_app)