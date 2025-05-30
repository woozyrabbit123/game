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
from src.game_state import initialize_game_state, get_game_state

from src.mechanics.event_manager import update_active_events, trigger_random_market_event
from src.ui_textual.components.text_ui_handlers import (
    handle_view_market, handle_view_inventory,
    handle_travel, handle_view_tech_contact, handle_skills_view,
    handle_upgrades_view, handle_blocking_event_popup_view,
    handle_game_over_view, handle_informant_view,
    handle_buy_drug, handle_sell_drug, handle_advance_day,
    handle_view_skills, handle_view_upgrades,
    handle_talk_to_informant, handle_meet_corrupt_official
)
from src.ui_textual.components.ui_helpers import display_daily_status_header
import src.game_state as game_state


def main_curses_app(stdscr):
    # --- Curses Initialization ---
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    # Color pairs: (pair_number, fg, bg)
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
    content_pad = curses.newpad(1000, content_width)  # Large enough for scrolling
    log_win = curses.newwin(log_height, max_x, header_height + content_height, 0)
    input_win = curses.newwin(input_height, max_x, header_height + content_height + log_height, 0)

    # --- Game State Initialization ---
    current_day = 1
    player_inventory = PlayerInventory(max_capacity=PLAYER_MAX_CAPACITY, starting_cash=PLAYER_STARTING_CASH)
    debt_payment_1_paid = False
    debt_payment_2_paid = False
    debt_payment_3_paid = False
    game_state.initialize_crypto_prices(CRYPTO_PRICES_INITIAL)
    all_game_regions: Dict[str, Region] = {}
    # Initialize Downtown region
    downtown = Region("Downtown")
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
    all_game_regions["Downtown"] = downtown

    # Initialize The Docks region
    the_docks = Region("The Docks")
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
    all_game_regions["The Docks"] = the_docks

    # Initialize Suburbia region
    suburbia = Region("Suburbia")
    suburbia.initialize_drug_market("Weed", 60, 100, 1, {
        DrugQuality.STANDARD: random.randint(20,60)
    })
    suburbia.initialize_drug_market("Pills", 110, 170, 2, { 
        DrugQuality.STANDARD: random.randint(20,50), 
        DrugQuality.PURE: random.randint(5,15) 
    })
    all_game_regions["Suburbia"] = suburbia
    current_player_region = all_game_regions["Downtown"]    # Initialize all region markets
    for r_name, r_obj in all_game_regions.items():
        r_obj.restock_market()

    # Initialize AI rivals
    ai_rivals: List[AIRival] = [
        AIRival(name="The Chemist", primary_drug="Pills", primary_region_name="Downtown", 
                aggression=0.6, activity_level=0.7),
        AIRival(name="Silas", primary_drug="Coke", primary_region_name="Downtown", 
                aggression=0.8, activity_level=0.5),
        AIRival(name="Dockmaster Jones", primary_drug="Speed", primary_region_name="The Docks", 
                aggression=0.5, activity_level=0.6),
        AIRival(name="Shady Stan", primary_drug="Heroin", primary_region_name="The Docks", 
                aggression=0.7, activity_level=0.4)
    ]

    # --- Log Buffer ---
    log_buffer = []  # List of (msg, color_pair)
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
            # --- Draw Header ---
            header_win.clear()
            # Ensure player_inventory has current_region attribute before passing
            # This might need to be set when player_inventory is initialized or when region changes
            # For now, let's assume it's set correctly.
            display_daily_status_header(header_win, current_day, player_inventory, debt_payment_1_paid, debt_payment_2_paid, debt_payment_3_paid)
            header_win.noutrefresh()

            # --- Debt Collector Payment Logic ---
            # Payment 1
            if not debt_payment_1_paid and current_day == DEBT_PAYMENT_1_DUE_DAY:
                log_win.clear()
                if player_inventory.cash >= DEBT_PAYMENT_1_AMOUNT:
                    player_inventory.cash -= DEBT_PAYMENT_1_AMOUNT
                    debt_payment_1_paid = True
                    log_win.addstr(0, 0, f"Debt Collector payment 1 made!", curses.color_pair(3))
                else:
                    log_win.addstr(0, 0, "GAME OVER: You failed to pay the Debt Collector!", curses.color_pair(4))
                    log_win.noutrefresh()
                    curses.doupdate()
                    input_win.clear(); input_win.addstr(0,0,"Press any key to exit.",curses.color_pair(4)); input_win.refresh(); input_win.getkey()
                    break
                log_win.noutrefresh(); curses.doupdate(); input_win.clear(); input_win.addstr(0,0,"Press any key to continue.",curses.color_pair(3)); input_win.refresh(); input_win.getkey()
            # Payment 2
            if debt_payment_1_paid and not debt_payment_2_paid and current_day == DEBT_PAYMENT_2_DUE_DAY:
                log_win.clear()
                if player_inventory.cash >= DEBT_PAYMENT_2_AMOUNT:
                    player_inventory.cash -= DEBT_PAYMENT_2_AMOUNT
                    debt_payment_2_paid = True
                    log_win.addstr(0, 0, f"Debt Collector payment 2 made!", curses.color_pair(3))
                else:
                    log_win.addstr(0, 0, "GAME OVER: You failed to pay the Debt Collector!", curses.color_pair(4))
                    log_win.noutrefresh()
                    curses.doupdate()
                    input_win.clear(); input_win.addstr(0,0,"Press any key to exit.",curses.color_pair(4)); input_win.refresh(); input_win.getkey()
                    break
                log_win.noutrefresh(); curses.doupdate(); input_win.clear(); input_win.addstr(0,0,"Press any key to continue.",curses.color_pair(3)); input_win.refresh(); input_win.getkey()
            # Payment 3
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
                "5. Travel", # Added Travel
                "6. Skills", "7. Upgrades", "8. Talk to Informant", "9. Meet Corrupt Official",
                "A. Advance Day", # Changed Advance Day to 'A'
                "0. Exit Game"
            ]
            # Add dynamic options like "Respond to Opportunities" or "Crypto Shop" if applicable
            # Example:
            # if any(event.event_type == "THE_SETUP" for event in current_player_region.active_market_events):
            # menu_lines.append("R. Respond to Opportunities")
            # if "GHOST_NETWORK_ACCESS" in player_inventory.unlocked_skills:
            # menu_lines.append("S. Crypto-Only Shop")

            for idx, line in enumerate(menu_lines):
                content_pad.addstr(idx, 0, line, curses.color_pair(5))
            
            # Calculate valid screen viewport for content_pad
            # pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol
            # sminrow: screen row where pad display starts (after header)
            # smaxrow: screen row where pad display ends (before log and input)
            sminrow_pad = header_height
            smaxrow_pad = max_y - log_height - input_height - 1 
            smincol_pad = 0
            smaxcol_pad = max_x - 1
            
            # Ensure smaxrow_pad is not less than sminrow_pad
            if smaxrow_pad < sminrow_pad: 
                smaxrow_pad = sminrow_pad # Avoid error, though layout is compromised

            content_pad.noutrefresh(0, 0, sminrow_pad, smincol_pad, smaxrow_pad, smaxcol_pad)

            # --- Input ---
            input_win.clear()
            input_win.addstr(0, 0, "Enter choice: ", curses.color_pair(6))
            input_win.refresh()
            curses.echo()
            choice = input_win.getstr(0, 14, 10).decode().strip()
            curses.noecho()

            # --- Handle Choice ---
            if choice == "1":
                handle_view_market(current_player_region, player_inventory, content_pad, log_win, input_win)
            elif choice == "2":
                handle_view_inventory(player_inventory, content_pad, log_win, input_win)
            elif choice == "3":
                handle_buy_drug(current_player_region, player_inventory, content_pad, log_win, input_win)
            elif choice == "4":
                handle_sell_drug(current_player_region, player_inventory, content_pad, log_win, input_win)
            elif choice == "5":
                handle_travel(current_player_region, all_game_regions, player_inventory, content_pad, log_win, input_win)
            elif choice == "A" or choice == "a":
                handle_advance_day(all_game_regions, current_day, current_player_region, player_inventory, ai_rivals, content_pad, log_win, input_win)
                current_day += 1
            elif choice == "6":
                handle_view_skills(player_inventory, content_pad, log_win, input_win)
            elif choice == "7":
                handle_view_upgrades(player_inventory, content_pad, log_win, input_win)
            elif choice == "8":
                handle_talk_to_informant(current_player_region, all_game_regions, ai_rivals, player_inventory, content_pad, log_win, input_win)
            elif choice == "9":
                handle_meet_corrupt_official(current_player_region, player_inventory, content_pad, log_win, input_win)
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