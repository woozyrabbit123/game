"""
Main game loop for Project Narco-Syndicate Pygame UI.
Split from app.py for modularity.
"""

import sys # Moved to top
from typing import Any, Optional, Tuple, List # Added Tuple, List

import pygame # Moved to top

# Local application imports
from ..core.enums import CryptoCoin # For advance_day local import
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
# from ..game_configs import CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE # Accessed via game_configs_ext
from ..game_state import GameState
# from ..mechanics.event_manager import update_active_events # Accessed via event_manager object if needed, or direct call
from . import state # Main state module for this UI package
from .actions import (
    action_cancel_transaction,
    action_confirm_tech_operation, # Confirm tech op uses state
    action_confirm_transaction, # Confirm transaction uses state
    action_open_main_menu,
)
from .constants import ( # Assuming these are needed directly
    EMERALD_GREEN,
    FPS,
    FONT_MEDIUM, # FONT_MEDIUM used in this file
    GOLDEN_YELLOW,
    IMPERIAL_RED,
    RICH_BLACK,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    draw_text, # draw_text used in this file
)
from .setup_ui import setup_buttons
from .ui_hud import (
    add_message_to_log,
    draw_hud as draw_hud_external,
    show_event_message as show_event_message_external,
    update_hud_timers as update_hud_timers_external,
)
from .views.blocking_event_popup_view import \
    draw_blocking_event_popup as draw_blocking_event_popup_external
from .views.game_over_view import \
    draw_game_over_view as draw_game_over_view_external
from .views.informant_view import \
    draw_informant_view as draw_informant_view_external
from .views.inventory_view import \
    draw_inventory_view as draw_inventory_view_external
from .views.main_menu_view import \
    draw_main_menu as draw_main_menu_external
from .views.market_view import (
    draw_market_view as draw_market_view_external,
    draw_transaction_input_view as draw_transaction_input_view_external
)
from .views.skills_view import draw_skills_view as draw_skills_view_external
from .views.tech_contact_view import \
    draw_tech_contact_view as draw_tech_contact_view_external
from .views.travel_view import draw_travel_view as draw_travel_view_external
from .views.upgrades_view import \
    draw_upgrades_view as draw_upgrades_view_external


def game_loop(
    player_inventory: PlayerInventory,
    initial_current_region: Optional[Region],
    game_state_ext: GameState,
    game_configs_ext: Any, # This is the game_configs module
) -> None:
    # pygame and sys are now top-level imports
    state.game_state_data_cache = game_state_ext
    state.game_configs_data_cache = game_configs_ext
    state.player_inventory_cache = player_inventory

    if not hasattr(state.game_state_data_cache, 'current_player_region') or \
       state.game_state_data_cache.current_player_region is None: # Ensure type consistency
        state.game_state_data_cache.current_player_region = initial_current_region

    setup_buttons(
        state.game_state_data_cache,
        state.player_inventory_cache,
        state.game_configs_data_cache,
        state.game_state_data_cache.current_player_region,
    )

    # --- Campaign Structure & Day/Phase Progression ---
    state.campaign_day = getattr(state, 'campaign_day', 1)
    state.campaign_length = getattr(state, 'campaign_length', 120)
    state.campaign_phase = getattr(state, 'campaign_phase', 1)
    state.phase_thresholds = [45, 70, 100, 120]
    state.phase_names = [
        'Survival & Foundation',
        'Expansion & Diversification',
        'Consolidation & Specialization',
        'Legacy & Mastery',
    ]

    def advance_day() -> None:
        state.campaign_day += 1
        for i, threshold in enumerate(state.phase_thresholds):
            if state.campaign_day <= threshold:
                state.campaign_phase = i + 1
                break

        current_gs_data_cache = state.game_state_data_cache
        if hasattr(current_gs_data_cache, 'difficulty_level'): # Check before assignment
            current_gs_data_cache.difficulty_level = state.campaign_phase

        if current_gs_data_cache and current_gs_data_cache.current_player_region:
            # Import locally or ensure event_manager is available if this file is main
            from ..mechanics.event_manager import update_active_events
            update_active_events(current_gs_data_cache.current_player_region)

        if hasattr(current_gs_data_cache, 'update_daily_crypto_prices') and \
           hasattr(game_configs_ext, 'CRYPTO_VOLATILITY') and \
           hasattr(game_configs_ext, 'CRYPTO_MIN_PRICE'):
            current_gs_data_cache.update_daily_crypto_prices(
                game_configs_ext.CRYPTO_VOLATILITY, game_configs_ext.CRYPTO_MIN_PRICE
            )

        inv_cache = state.player_inventory_cache
        if hasattr(inv_cache, 'pending_laundered_sc_arrival_day') and \
           inv_cache.pending_laundered_sc_arrival_day == state.campaign_day:

            laundered_coin_type_str = getattr(inv_cache, 'laundered_crypto_type', 'DRUG_COIN')
            laundered_coin_enum = CryptoCoin[laundered_coin_type_str] \
                if laundered_coin_type_str in CryptoCoin.__members__ else CryptoCoin.DRUG_COIN

            current_balance = inv_cache.crypto_wallet.get(laundered_coin_enum, 0.0)
            inv_cache.crypto_wallet[laundered_coin_enum] = current_balance + inv_cache.pending_laundered_sc
            inv_cache.pending_laundered_sc = 0.0
            inv_cache.pending_laundered_sc_arrival_day = None

        bankruptcy_threshold = getattr(game_configs_ext, 'BANKRUPTCY_THRESHOLD', -1000)
        if inv_cache.cash < bankruptcy_threshold:
            state.game_over_message = 'Bankruptcy! You lost all your money.'
            state.current_view = 'game_over'
        elif state.campaign_day > state.campaign_length:
            state.game_over_message = 'Campaign ended. You did not reach your goal.'
            if inv_cache.cash >= 1000000: # Example win condition
                state.game_over_message = 'Congratulations! You achieved kingpin status.'
            state.current_view = 'game_over'

    running = True
    while running:
        current_player_region_for_frame = state.game_state_data_cache.current_player_region
        previous_view = state.current_view
        mouse_pos = pygame.mouse.get_pos()

        if state.game_over_message is not None and state.current_view != 'game_over':
            previous_view = state.current_view
            state.current_view = 'game_over'
            setup_buttons(state.game_state_data_cache, state.player_inventory_cache,
                          state.game_configs_data_cache, current_player_region_for_frame)

        for event_pygame in pygame.event.get():
            if event_pygame.type == pygame.QUIT:
                running = False
                break # Exit event loop

            if state.current_view == 'game_over':
                for btn_game_over in state.game_over_buttons:
                    if btn_game_over.handle_event(event_pygame):
                        break
                if event_pygame.type == pygame.KEYDOWN and event_pygame.key == pygame.K_RETURN:
                    if state.game_over_buttons and state.game_over_buttons[0].action:
                        state.game_over_buttons[0].action() # sys.exit()
                continue

            if state.current_view == 'blocking_event_popup':
                for btn_popup in state.blocking_event_popup_buttons:
                    if btn_popup.handle_event(event_pygame):
                        if previous_view != state.current_view:
                            setup_buttons(state.game_state_data_cache, state.player_inventory_cache,
                                          state.game_configs_data_cache, current_player_region_for_frame)
                        break
                if event_pygame.type == pygame.KEYDOWN and event_pygame.key == pygame.K_RETURN:
                    if state.blocking_event_popup_buttons and state.blocking_event_popup_buttons[0].action:
                        state.blocking_event_popup_buttons[0].action()
                        if previous_view != state.current_view:
                            setup_buttons(state.game_state_data_cache, state.player_inventory_cache,
                                          state.game_configs_data_cache, current_player_region_for_frame)
                continue

            # Simplified input handling section
            is_market_input_active = state.current_view in ['market_buy_input', 'market_sell_input']
            is_tech_input_active = state.current_view == 'tech_input_amount'
            is_quality_select_active = state.current_view == 'market_quality_select'

            if event_pygame.type == pygame.KEYDOWN:
                if event_pygame.key == pygame.K_ESCAPE:
                    if is_market_input_active or is_tech_input_active or is_quality_select_active:
                        action_cancel_transaction()
                    else:
                        action_open_main_menu()
                # Input string modifications (example for market)
                elif is_market_input_active:
                    if event_pygame.key == pygame.K_RETURN:
                         if current_player_region_for_frame: # Ensure region is not None
                            action_confirm_transaction(state.player_inventory_cache, current_player_region_for_frame, state.game_state_data_cache)
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        state.quantity_input_string = state.quantity_input_string[:-1]
                    elif event_pygame.unicode.isdigit():
                        state.quantity_input_string += event_pygame.unicode
                elif is_tech_input_active: # Similar for tech input
                    if event_pygame.key == pygame.K_RETURN:
                        action_confirm_tech_operation(state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache)
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        state.tech_input_string = state.tech_input_string[:-1]
                    elif event_pygame.unicode.isdigit() or \
                         (event_pygame.unicode == '.' and '.' not in state.tech_input_string):
                        state.tech_input_string += event_pygame.unicode

            # Button event handling
            active_buttons = [] # Determine based on state.current_view
            # Example: if state.current_view == 'main_menu': active_buttons = state.main_menu_buttons
            # (This part needs to be fully fleshed out similar to the original logic)

            button_clicked_and_view_changed = False
            for btn in active_buttons: # Use the determined active_buttons list
                if btn.handle_event(event_pygame):
                    if previous_view != state.current_view:
                        button_clicked_and_view_changed = True
                        setup_buttons(state.game_state_data_cache, state.player_inventory_cache,
                                      state.game_configs_data_cache, current_player_region_for_frame)
                    break

            if not button_clicked_and_view_changed and previous_view != state.current_view:
                setup_buttons(state.game_state_data_cache, state.player_inventory_cache,
                              state.game_configs_data_cache, current_player_region_for_frame)

        if not running: # If running became false in event loop
            break

        update_hud_timers_external()
        if state.prompt_message_timer > 0:
            state.prompt_message_timer -= 1
            if state.prompt_message_timer <= 0:
                state.active_prompt_message = None

        screen_surface = pygame.display.get_surface()
        screen_surface.fill(RICH_BLACK)

        # Drawing logic (simplified, needs full restoration from original app.py structure)
        if state.current_view == 'game_over':
            draw_game_over_view_external(screen_surface, state.game_over_message or "Game Over", state.game_over_buttons)
        elif state.current_view == 'main_menu':
            draw_main_menu_external(screen_surface, state.main_menu_buttons)
        # ... Add all other view drawing conditions ...
        elif state.current_view == 'market' and current_player_region_for_frame:
            draw_market_view_external(screen_surface, current_player_region_for_frame, state.player_inventory_cache, state.market_view_buttons, state.market_buy_sell_buttons)
        elif state.current_view == 'market_quality_select' and current_player_region_for_frame:
             from .views.market_view import draw_quality_select_view # Local import
             draw_quality_select_view(screen_surface, state.transaction_input_buttons, state.drug_for_transaction)
        elif state.current_view == 'inventory':
            draw_inventory_view_external(screen_surface, state.player_inventory_cache, state.inventory_view_buttons)
        elif state.current_view == 'travel' and current_player_region_for_frame:
            draw_travel_view_external(screen_surface, current_player_region_for_frame, state.travel_view_buttons)
        elif state.current_view == 'informant':
            draw_informant_view_external(screen_surface, state.player_inventory_cache, state.informant_view_buttons, state.game_configs_data_cache)
        elif state.current_view in ['tech_contact', 'tech_input_coin_select', 'tech_input_amount']:
            tech_ui_state_dict = {
                "current_view": state.current_view, "tech_transaction_in_progress": state.tech_transaction_in_progress,
                "coin_for_tech_transaction": state.coin_for_tech_transaction, "tech_input_string": state.tech_input_string,
                "active_prompt_message": state.active_prompt_message, "prompt_message_timer": state.prompt_message_timer,
                "tech_input_box_rect": state.tech_input_box_rect,
            }
            draw_tech_contact_view_external(screen_surface, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.tech_contact_view_buttons, tech_ui_state_dict)
        elif state.current_view == 'skills':
            draw_skills_view_external(screen_surface, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.skills_view_buttons)
        elif state.current_view == 'upgrades':
            draw_upgrades_view_external(screen_surface, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.upgrades_view_buttons)
        elif state.current_view in ['market_buy_input', 'market_sell_input']:
            transaction_ui_state_dict = {
                "quantity_input_string": state.quantity_input_string, "drug_for_transaction": state.drug_for_transaction,
                "quality_for_transaction": state.quality_for_transaction, "price_for_transaction": state.price_for_transaction,
                "available_for_transaction": state.available_for_transaction, "current_transaction_type": state.current_transaction_type,
                "active_prompt_message": state.active_prompt_message, "prompt_message_timer": state.prompt_message_timer,
                "input_box_rect": state.input_box_rect,
            }
            draw_transaction_input_view_external(screen_surface, state.transaction_input_buttons, transaction_ui_state_dict)

        if state.current_view == 'blocking_event_popup' and state.active_blocking_event_data:
            draw_blocking_event_popup_external(screen_surface, state.active_blocking_event_data, state.blocking_event_popup_buttons)

        if state.current_view != 'game_over' and current_player_region_for_frame:
            draw_hud_external(screen_surface, state.player_inventory_cache, current_player_region_for_frame, state.game_state_data_cache)
            day_phase_text = f"Day {state.campaign_day} / {state.campaign_length} | Phase: {state.phase_names[state.campaign_phase-1]}"
            draw_text(screen_surface, day_phase_text, 20, 10, font=FONT_MEDIUM, color=GOLDEN_YELLOW, center_aligned=False)

        if state.active_prompt_message and state.prompt_message_timer > 0 and \
           state.current_view not in ['game_over', 'blocking_event_popup']:
            # Simplified prompt drawing logic
            prompt_color = IMPERIAL_RED if "Error" in state.active_prompt_message else EMERALD_GREEN
            draw_text(screen_surface, state.active_prompt_message, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                      font=FONT_MEDIUM, color=prompt_color, center_aligned=True, max_width=SCREEN_WIDTH - 40)

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

    pygame.quit()
    sys.exit()
