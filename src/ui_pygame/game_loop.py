"""
Main game loop for Project Narco-Syndicate Pygame UI.
Split from app.py for modularity.
"""
from . import state
from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, RICH_BLACK, IMPERIAL_RED, GOLDEN_YELLOW, EMERALD_GREEN, FONT_MEDIUM, draw_text
)
from .actions import action_cancel_transaction, action_confirm_transaction, action_confirm_tech_operation, action_open_main_menu
from .setup_ui import setup_buttons
from .ui_hud import (
    draw_hud as draw_hud_external,
    show_event_message as show_event_message_external,
    update_hud_timers as update_hud_timers_external,
    add_message_to_log
)
from .views.main_menu_view import draw_main_menu as draw_main_menu_external
from .views.market_view import draw_market_view as draw_market_view_external, draw_transaction_input_view as draw_transaction_input_view_external
from .views.inventory_view import draw_inventory_view as draw_inventory_view_external
from .views.travel_view import draw_travel_view as draw_travel_view_external
from .views.tech_contact_view import draw_tech_contact_view as draw_tech_contact_view_external
from .views.skills_view import draw_skills_view as draw_skills_view_external
from .views.upgrades_view import draw_upgrades_view as draw_upgrades_view_external
from .views.blocking_event_popup_view import draw_blocking_event_popup as draw_blocking_event_popup_external
from .views.game_over_view import draw_game_over_view as draw_game_over_view_external
from .views.informant_view import draw_informant_view as draw_informant_view_external
from src.game_state import update_daily_crypto_prices
from src.game_configs import CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE
from src.mechanics.event_manager import update_active_events


def game_loop(player_inventory, initial_current_region, game_state_ext, game_configs_ext):
    import pygame
    import sys
    state.game_state_data_cache = game_state_ext
    state.game_configs_data_cache = game_configs_ext
    state.player_inventory_cache = player_inventory

    if not hasattr(state.game_state_data_cache, 'current_player_region'):
        state.game_state_data_cache.current_player_region = initial_current_region

    setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, state.game_state_data_cache.current_player_region)
    running = True

    # --- Campaign Structure & Day/Phase Progression ---
    # Add campaign day counter, phase logic, and win/loss conditions
    state.campaign_day = getattr(state, 'campaign_day', 1)
    state.campaign_length = getattr(state, 'campaign_length', 120)  # Default to Standard
    state.campaign_phase = getattr(state, 'campaign_phase', 1)
    state.phase_thresholds = [45, 70, 100, 120]  # End days for each phase
    state.phase_names = [
        "Survival & Foundation",
        "Expansion & Diversification",
        "Consolidation & Specialization",
        "Legacy & Mastery"
    ]
    def advance_day():
        state.campaign_day += 1
        # Phase progression
        for i, threshold in enumerate(state.phase_thresholds):
            if state.campaign_day <= threshold:
                state.campaign_phase = i + 1
                break
        # --- Dynamic Difficulty Example ---
        state.game_state_data_cache.difficulty_level = state.campaign_phase
        # --- Event System Integration ---
        update_active_events(state.game_state_data_cache.current_player_region)
        # --- Crypto Market Update ---
        update_daily_crypto_prices(CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE)
        # --- Laundering Arrival ---
        inv = state.player_inventory_cache
        if hasattr(inv, 'pending_laundered_sc_arrival_day') and inv.pending_laundered_sc_arrival_day == state.campaign_day:
            inv.crypto_wallet[getattr(inv, 'laundered_crypto_type', 'SC')] = inv.crypto_wallet.get(getattr(inv, 'laundered_crypto_type', 'SC'), 0.0) + inv.pending_laundered_sc
            inv.pending_laundered_sc = 0.0
            inv.pending_laundered_sc_arrival_day = None
        # Win/Loss conditions
        if state.player_inventory_cache.cash < 0:
            state.game_over_message = "Bankruptcy! You lost all your money."
            state.current_view = "game_over"
        elif state.campaign_day > state.campaign_length:
            if state.player_inventory_cache.cash >= 1000000:  # Example win condition
                state.game_over_message = "Congratulations! You achieved kingpin status."
            else:
                state.game_over_message = "Campaign ended. You did not reach your goal."
            state.current_view = "game_over"
        # TODO: Add more win/loss/legacy logic as needed

    while running:
        current_player_region_for_frame = state.game_state_data_cache.current_player_region
        previous_view = state.current_view
        mouse_pos = pygame.mouse.get_pos()

        if state.game_over_message is not None and state.current_view != "game_over":
            previous_view = state.current_view
            state.current_view = "game_over"
            setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state.current_view == "game_over":
                for btn in state.game_over_buttons:
                    if btn.handle_event(event):
                        break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    if state.game_over_buttons and state.game_over_buttons[0].action:
                        state.game_over_buttons[0].action()
                continue

            if state.current_view == "blocking_event_popup":
                for button in state.blocking_event_popup_buttons:
                    if button.handle_event(event):
                        if previous_view != state.current_view:
                            setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)
                        break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    if state.blocking_event_popup_buttons and state.blocking_event_popup_buttons[0].action:
                        state.blocking_event_popup_buttons[0].action()
                        if previous_view != state.current_view:
                            setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)
                continue

            is_market_input_active = state.current_view == "market_buy_input" or state.current_view == "market_sell_input"
            is_tech_input_active = state.current_view == "tech_input_amount"
            is_quality_select_active = state.current_view == "market_quality_select"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if is_market_input_active or is_tech_input_active or is_quality_select_active:
                        action_cancel_transaction()
                    else:
                        action_open_main_menu()

                if is_market_input_active:
                    if event.key == pygame.K_RETURN:
                        action_confirm_transaction(state.player_inventory_cache, current_player_region_for_frame, state.game_state_data_cache)
                    elif event.key == pygame.K_BACKSPACE:
                        state.quantity_input_string = state.quantity_input_string[:-1]
                    elif event.unicode.isdigit():
                        state.quantity_input_string += event.unicode
                elif is_tech_input_active:
                    if event.key == pygame.K_RETURN:
                        action_confirm_tech_operation(state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache)
                    elif event.key == pygame.K_BACKSPACE:
                        state.tech_input_string = state.tech_input_string[:-1]
                    elif event.unicode.isdigit() or (event.unicode == '.' and '.' not in state.tech_input_string):
                        state.tech_input_string += event.unicode
                # No direct input for quality select; handled by buttons

            active_buttons_list = []
            if state.current_view == "main_menu":
                active_buttons_list = state.main_menu_buttons
            elif state.current_view == "market":
                active_buttons_list = state.market_view_buttons + state.market_buy_sell_buttons
            elif state.current_view == "inventory":
                active_buttons_list = state.inventory_view_buttons
            elif state.current_view == "travel":
                active_buttons_list = state.travel_view_buttons
            elif state.current_view == "informant":
                active_buttons_list = state.informant_view_buttons
            elif state.current_view in ["tech_contact", "tech_input_coin_select", "tech_input_amount"]:
                active_buttons_list = state.tech_contact_view_buttons
            elif state.current_view == "skills":
                active_buttons_list = state.skills_view_buttons
            elif state.current_view == "upgrades":
                active_buttons_list = state.upgrades_view_buttons
            elif state.current_view in ["market_buy_input", "market_sell_input"]:
                active_buttons_list = state.transaction_input_buttons
            elif state.current_view == "market_quality_select":
                active_buttons_list = state.transaction_input_buttons

            button_clicked_and_view_changed = False
            for button in active_buttons_list:
                if button.handle_event(event):
                    if previous_view != state.current_view:
                        button_clicked_and_view_changed = True
                        setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)
                    break

            if not button_clicked_and_view_changed and previous_view != state.current_view:
                setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)

        update_hud_timers_external()
        if state.prompt_message_timer > 0:
            state.prompt_message_timer -= 1
            if state.prompt_message_timer <= 0:
                state.active_prompt_message = None

        screen = pygame.display.get_surface()
        screen.fill(RICH_BLACK)

        if state.current_view == "game_over":
            draw_game_over_view_external(screen, state.game_over_message, state.game_over_buttons)
        elif state.current_view == "main_menu":
            draw_main_menu_external(screen, state.main_menu_buttons)
        elif state.current_view == "market":
            draw_market_view_external(screen, current_player_region_for_frame, state.player_inventory_cache, state.market_view_buttons, state.market_buy_sell_buttons)
        elif state.current_view == "market_quality_select":
            from .views.market_view import draw_quality_select_view
            draw_quality_select_view(screen, state.transaction_input_buttons, state.drug_for_transaction)
        elif state.current_view == "inventory":
            draw_inventory_view_external(screen, state.player_inventory_cache, state.inventory_view_buttons)
        elif state.current_view == "travel":
            draw_travel_view_external(screen, current_player_region_for_frame, state.travel_view_buttons)
        elif state.current_view == "informant":
            draw_informant_view_external(screen, state.player_inventory_cache, state.informant_view_buttons, state.game_configs_data_cache)
        elif state.current_view in ["tech_contact", "tech_input_coin_select", "tech_input_amount"]:
            tech_ui_state = {
                'current_view': state.current_view,
                'tech_transaction_in_progress': state.tech_transaction_in_progress,
                'coin_for_tech_transaction': state.coin_for_tech_transaction,
                'tech_input_string': state.tech_input_string,
                'active_prompt_message': state.active_prompt_message,
                'prompt_message_timer': state.prompt_message_timer,
                'tech_input_box_rect': state.tech_input_box_rect
            }
            draw_tech_contact_view_external(screen, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.tech_contact_view_buttons, tech_ui_state)
        elif state.current_view == "skills":
            draw_skills_view_external(screen, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.skills_view_buttons)
        elif state.current_view == "upgrades":
            draw_upgrades_view_external(screen, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.upgrades_view_buttons)
        elif state.current_view in ["market_buy_input", "market_sell_input"]:
            transaction_ui_state = {
                'quantity_input_string': state.quantity_input_string,
                'drug_for_transaction': state.drug_for_transaction,
                'quality_for_transaction': state.quality_for_transaction,
                'price_for_transaction': state.price_for_transaction,
                'available_for_transaction': state.available_for_transaction,
                'current_transaction_type': state.current_transaction_type,
                'active_prompt_message': state.active_prompt_message,
                'prompt_message_timer': state.prompt_message_timer,
                'input_box_rect': state.input_box_rect
            }
            draw_transaction_input_view_external(screen, state.transaction_input_buttons, transaction_ui_state)

        if state.current_view != "game_over" and state.current_view == "blocking_event_popup" and state.active_blocking_event_data:
            draw_blocking_event_popup_external(screen, state.active_blocking_event_data, state.blocking_event_popup_buttons)

        if state.current_view != "game_over":
            draw_hud_external(screen, state.player_inventory_cache, current_player_region_for_frame, state.game_state_data_cache)
            # Draw campaign day/phase at the top left
            day_phase_text = f"Day {state.campaign_day} / {state.campaign_length} | Phase: {state.phase_names[state.campaign_phase-1]}"
            draw_text(screen, day_phase_text, 20, 10, font=FONT_MEDIUM, color=GOLDEN_YELLOW, center_aligned=False)

        if state.active_prompt_message and state.prompt_message_timer > 0 and state.current_view != "game_over" and state.current_view != "blocking_event_popup":
            is_prompt_handled_by_view = (
                (state.current_view in ["market_buy_input", "market_sell_input", "tech_input_amount"]) or
                (state.current_view == "tech_contact" and 'active_prompt_message' in locals() and state.active_prompt_message and "Select cryptocurrency" not in state.active_prompt_message and "Enter amount" not in state.active_prompt_message)
            )
            if not is_prompt_handled_by_view:
                prompt_y = SCREEN_HEIGHT - 100
                if state.current_view == "tech_contact":
                    prompt_y = SCREEN_HEIGHT - 120
                prompt_color = IMPERIAL_RED if "Error" in state.active_prompt_message or "Invalid" in state.active_prompt_message or "Not enough" in state.active_prompt_message else (GOLDEN_YELLOW if "Skill" in state.active_prompt_message else EMERALD_GREEN)
                draw_text(screen, state.active_prompt_message, SCREEN_WIDTH // 2, prompt_y, font=FONT_MEDIUM, color=prompt_color, center_aligned=True, max_width=SCREEN_WIDTH - 40)

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

    pygame.quit()
    sys.exit()
