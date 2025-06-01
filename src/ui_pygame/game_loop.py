"""
Main game loop for Project Narco-Syndicate Pygame UI.
Split from app.py for modularity.
"""

from . import state
from .constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    RICH_BLACK,
    IMPERIAL_RED,
    GOLDEN_YELLOW,
    EMERALD_GREEN,
    FONT_MEDIUM,
    draw_text,
)
from .actions import (
    action_cancel_transaction,
    action_confirm_transaction,
    action_confirm_tech_operation,
    action_open_main_menu,
)
from .setup_ui import setup_buttons
from .ui_hud import (
    draw_hud as draw_hud_external,
    show_event_message as show_event_message_external,
    update_hud_timers as update_hud_timers_external,
    add_message_to_log,
)
from .views.main_menu_view import draw_main_menu as draw_main_menu_external
from .views.market_view import (
    draw_market_view as draw_market_view_external,
    draw_transaction_input_view as draw_transaction_input_view_external,
)
from .views.inventory_view import draw_inventory_view as draw_inventory_view_external
from .views.travel_view import draw_travel_view as draw_travel_view_external
from .views.tech_contact_view import (
    draw_tech_contact_view as draw_tech_contact_view_external,
)
from .views.skills_view import draw_skills_view as draw_skills_view_external
from .views.upgrades_view import draw_upgrades_view as draw_upgrades_view_external
from .views.blocking_event_popup_view import (
    draw_blocking_event_popup as draw_blocking_event_popup_external,
)
from .views.game_over_view import draw_game_over_view as draw_game_over_view_external
from .views.informant_view import draw_informant_view as draw_informant_view_external
from src.game_state import GameState  # Import GameState for type hinting
from src.core.player_inventory import PlayerInventory  # Import for type hinting
from src.core.region import Region  # Import for type hinting
from src.game_state import update_daily_crypto_prices
from src.game_configs import (
    CRYPTO_VOLATILITY,
    CRYPTO_MIN_PRICE,
)  # These are specific values, not the module
from src.mechanics.event_manager import update_active_events
from typing import Any, Optional  # For type hinting


def game_loop(
    player_inventory: PlayerInventory,
    initial_current_region: Optional[Region],
    game_state_ext: GameState,
    game_configs_ext: Any,
) -> None:
    import pygame
    import sys

    state.game_state_data_cache = game_state_ext
    state.game_configs_data_cache = game_configs_ext
    state.player_inventory_cache = player_inventory

    if not hasattr(state.game_state_data_cache, "current_player_region"):
        state.game_state_data_cache.current_player_region = initial_current_region

    setup_buttons(
        state.game_state_data_cache,
        state.player_inventory_cache,
        state.game_configs_data_cache,
        state.game_state_data_cache.current_player_region,
    )
    running = True

    # --- Campaign Structure & Day/Phase Progression ---
    # Add campaign day counter, phase logic, and win/loss conditions
    state.campaign_day = getattr(state, "campaign_day", 1)
    state.campaign_length = getattr(
        state, "campaign_length", 120
    )  # Default to Standard
    state.campaign_phase = getattr(state, "campaign_phase", 1)
    state.phase_thresholds = [45, 70, 100, 120]  # End days for each phase
    state.phase_names = [
        "Survival & Foundation",
        "Expansion & Diversification",
        "Consolidation & Specialization",
        "Legacy & Mastery",
    ]

    def advance_day() -> None:  # Added return type
        state.campaign_day += 1
        # Phase progression
        for i, threshold in enumerate(state.phase_thresholds):  # threshold is int
            if state.campaign_day <= threshold:  # campaign_day is int
                state.campaign_phase = i + 1
                break
        # Dynamic Difficulty Example
        state.game_state_data_cache.difficulty_level = (
            state.campaign_phase
        )  # difficulty_level may need to be defined in GameState
        # Event System Integration
        if (
            state.game_state_data_cache.current_player_region
        ):  # Ensure region is not None
            update_active_events(state.game_state_data_cache.current_player_region)
        # Crypto Market Update
        # update_daily_crypto_prices expects Dicts, ensure they are passed correctly if this function is used.
        # For now, assuming CRYPTO_VOLATILITY and CRYPTO_MIN_PRICE are correctly structured Dicts.
        # This function is from game_state.py and updates game_state_ext.current_crypto_prices
        if hasattr(state.game_state_data_cache, "update_daily_crypto_prices"):
            state.game_state_data_cache.update_daily_crypto_prices(CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE)  # type: ignore

        # Laundering Arrival
        inv_cache: PlayerInventory = state.player_inventory_cache  # type: ignore
        if (
            hasattr(inv_cache, "pending_laundered_sc_arrival_day")
            and inv_cache.pending_laundered_sc_arrival_day == state.campaign_day
        ):
            from src.core.enums import CryptoCoin  # Local import if not at top

            laundered_coin_type_str: str = getattr(
                inv_cache, "laundered_crypto_type", "DRUG_COIN"
            )  # Default to DRUG_COIN if SC not in enum
            laundered_coin_enum: CryptoCoin = (
                CryptoCoin[laundered_coin_type_str]
                if laundered_coin_type_str in CryptoCoin.__members__
                else CryptoCoin.DRUG_COIN
            )
            inv_cache.crypto_wallet[laundered_coin_enum] = (
                inv_cache.crypto_wallet.get(laundered_coin_enum, 0.0)
                + inv_cache.pending_laundered_sc
            )
            inv_cache.pending_laundered_sc = 0.0
            inv_cache.pending_laundered_sc_arrival_day = None

        # Win/Loss conditions
        if state.player_inventory_cache.cash < (state.game_configs_data_cache.BANKRUPTCY_THRESHOLD if hasattr(state.game_configs_data_cache, "BANKRUPTCY_THRESHOLD") else -1000):  # type: ignore
            state.game_over_message = "Bankruptcy! You lost all your money."
            state.current_view = "game_over"
        elif state.campaign_day > state.campaign_length:
            if state.player_inventory_cache.cash >= 1000000:
                state.game_over_message = (
                    "Congratulations! You achieved kingpin status."
                )
            else:
                state.game_over_message = "Campaign ended. You did not reach your goal."
            state.current_view = "game_over"

    running: bool = True  # Moved from above loop
    while running:
        current_player_region_for_frame: Optional[Region] = state.game_state_data_cache.current_player_region  # type: ignore
        previous_view: str = state.current_view
        mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()

        if state.game_over_message is not None and state.current_view != "game_over":
            previous_view = state.current_view  # type: ignore
            state.current_view = "game_over"  # type: ignore
            setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)  # type: ignore

        for event_pygame in pygame.event.get():  # Renamed event
            if event_pygame.type == pygame.QUIT:
                running = False

            if state.current_view == "game_over":
                for btn_game_over in state.game_over_buttons:  # Renamed btn
                    if btn_game_over.handle_event(event_pygame):
                        break
                if (
                    event_pygame.type == pygame.KEYDOWN
                    and event_pygame.key == pygame.K_RETURN
                ):
                    if state.game_over_buttons and state.game_over_buttons[0].action:
                        state.game_over_buttons[0].action()  # sys.exit()
                continue

            if state.current_view == "blocking_event_popup":
                for btn_popup in state.blocking_event_popup_buttons:  # Renamed button
                    if btn_popup.handle_event(event_pygame):
                        if previous_view != state.current_view:
                            setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)  # type: ignore
                        break
                if (
                    event_pygame.type == pygame.KEYDOWN
                    and event_pygame.key == pygame.K_RETURN
                ):
                    if (
                        state.blocking_event_popup_buttons
                        and state.blocking_event_popup_buttons[0].action
                    ):
                        state.blocking_event_popup_buttons[0].action()
                        if previous_view != state.current_view:
                            setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)  # type: ignore
                continue

            is_market_input_active_local: bool = (
                state.current_view == "market_buy_input"
                or state.current_view == "market_sell_input"
            )  # Renamed local var
            is_tech_input_active_local: bool = (
                state.current_view == "tech_input_amount"
            )  # Renamed local var
            is_quality_select_active_local: bool = (
                state.current_view == "market_quality_select"
            )  # Renamed local var

            if event_pygame.type == pygame.KEYDOWN:
                if event_pygame.key == pygame.K_ESCAPE:
                    if (
                        is_market_input_active_local
                        or is_tech_input_active_local
                        or is_quality_select_active_local
                    ):
                        action_cancel_transaction()
                    else:
                        action_open_main_menu()

                if is_market_input_active_local:
                    if event_pygame.key == pygame.K_RETURN:
                        action_confirm_transaction(state.player_inventory_cache, current_player_region_for_frame, state.game_state_data_cache)  # type: ignore
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        state.quantity_input_string = state.quantity_input_string[:-1]  # type: ignore
                    elif event_pygame.unicode.isdigit():
                        state.quantity_input_string += event_pygame.unicode  # type: ignore
                elif is_tech_input_active_local:
                    if event_pygame.key == pygame.K_RETURN:
                        action_confirm_tech_operation(state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache)  # type: ignore
                    elif event_pygame.key == pygame.K_BACKSPACE:
                        state.tech_input_string = state.tech_input_string[:-1]  # type: ignore
                    elif event_pygame.unicode.isdigit() or (event_pygame.unicode == "." and "." not in state.tech_input_string):  # type: ignore
                        state.tech_input_string += event_pygame.unicode  # type: ignore
                # No direct input for quality select; handled by buttons

            active_buttons_list_local: List[Any] = (
                []
            )  # Renamed local var, Any for Button type from state
            if state.current_view == "main_menu":
                active_buttons_list_local = state.main_menu_buttons  # type: ignore
            elif state.current_view == "market":
                active_buttons_list_local = state.market_view_buttons + state.market_buy_sell_buttons  # type: ignore
            elif state.current_view == "inventory":
                active_buttons_list_local = state.inventory_view_buttons  # type: ignore
            elif state.current_view == "travel":
                active_buttons_list_local = state.travel_view_buttons  # type: ignore
            elif state.current_view == "informant":
                active_buttons_list_local = state.informant_view_buttons  # type: ignore
            elif state.current_view in [
                "tech_contact",
                "tech_input_coin_select",
                "tech_input_amount",
            ]:
                active_buttons_list_local = state.tech_contact_view_buttons  # type: ignore
            elif state.current_view == "skills":
                active_buttons_list_local = state.skills_view_buttons  # type: ignore
            elif state.current_view == "upgrades":
                active_buttons_list_local = state.upgrades_view_buttons  # type: ignore
            elif state.current_view in ["market_buy_input", "market_sell_input"]:
                active_buttons_list_local = state.transaction_input_buttons  # type: ignore
            elif state.current_view == "market_quality_select":
                active_buttons_list_local = state.transaction_input_buttons  # type: ignore

            button_clicked_and_view_changed_flag: bool = False  # Renamed
            for btn_active_local in active_buttons_list_local:  # Renamed button
                if btn_active_local.handle_event(event_pygame):
                    if previous_view != state.current_view:
                        button_clicked_and_view_changed_flag = True
                        setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)  # type: ignore
                    break

            if (
                not button_clicked_and_view_changed_flag
                and previous_view != state.current_view
            ):
                setup_buttons(state.game_state_data_cache, state.player_inventory_cache, state.game_configs_data_cache, current_player_region_for_frame)  # type: ignore

        update_hud_timers_external()  # type: ignore
        if state.prompt_message_timer > 0:  # type: ignore
            state.prompt_message_timer -= 1  # type: ignore
            if state.prompt_message_timer <= 0:  # type: ignore
                state.active_prompt_message = None  # type: ignore

        screen_surface: pygame.Surface = pygame.display.get_surface()  # Renamed screen
        screen_surface.fill(RICH_BLACK)

        if state.current_view == "game_over":
            draw_game_over_view_external(screen_surface, state.game_over_message if state.game_over_message else "Game Over", state.game_over_buttons)  # type: ignore
        elif state.current_view == "main_menu":
            draw_main_menu_external(screen_surface, state.main_menu_buttons)  # type: ignore
        elif state.current_view == "market" and current_player_region_for_frame:
            draw_market_view_external(screen_surface, current_player_region_for_frame, state.player_inventory_cache, state.market_view_buttons, state.market_buy_sell_buttons)  # type: ignore
        elif state.current_view == "market_quality_select":
            from .views.market_view import draw_quality_select_view  # Local import

            draw_quality_select_view(screen_surface, state.transaction_input_buttons, state.drug_for_transaction)  # type: ignore
        elif state.current_view == "inventory":
            draw_inventory_view_external(screen_surface, state.player_inventory_cache, state.inventory_view_buttons)  # type: ignore
        elif state.current_view == "travel" and current_player_region_for_frame:
            draw_travel_view_external(screen_surface, current_player_region_for_frame, state.travel_view_buttons)  # type: ignore
        elif state.current_view == "informant":
            draw_informant_view_external(screen_surface, state.player_inventory_cache, state.informant_view_buttons, state.game_configs_data_cache)  # type: ignore
        elif state.current_view in [
            "tech_contact",
            "tech_input_coin_select",
            "tech_input_amount",
        ]:
            tech_ui_state_dict: Dict[str, Any] = {  # Renamed tech_ui_state
                "current_view": state.current_view,
                "tech_transaction_in_progress": state.tech_transaction_in_progress,  # type: ignore
                "coin_for_tech_transaction": state.coin_for_tech_transaction,
                "tech_input_string": state.tech_input_string,  # type: ignore
                "active_prompt_message": state.active_prompt_message,
                "prompt_message_timer": state.prompt_message_timer,  # type: ignore
                "tech_input_box_rect": state.tech_input_box_rect,  # type: ignore
            }
            draw_tech_contact_view_external(screen_surface, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.tech_contact_view_buttons, tech_ui_state_dict)  # type: ignore
        elif state.current_view == "skills":
            draw_skills_view_external(screen_surface, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.skills_view_buttons)  # type: ignore
        elif state.current_view == "upgrades":
            draw_upgrades_view_external(screen_surface, state.player_inventory_cache, state.game_state_data_cache, state.game_configs_data_cache, state.upgrades_view_buttons)  # type: ignore
        elif state.current_view in ["market_buy_input", "market_sell_input"]:
            transaction_ui_state_dict: Dict[str, Any] = (
                {  # Renamed transaction_ui_state
                    "quantity_input_string": state.quantity_input_string,
                    "drug_for_transaction": state.drug_for_transaction,  # type: ignore
                    "quality_for_transaction": state.quality_for_transaction,
                    "price_for_transaction": state.price_for_transaction,  # type: ignore
                    "available_for_transaction": state.available_for_transaction,
                    "current_transaction_type": state.current_transaction_type,  # type: ignore
                    "active_prompt_message": state.active_prompt_message,
                    "prompt_message_timer": state.prompt_message_timer,  # type: ignore
                    "input_box_rect": state.input_box_rect,  # type: ignore
                }
            )
            draw_transaction_input_view_external(screen_surface, state.transaction_input_buttons, transaction_ui_state_dict)  # type: ignore

        if state.current_view != "game_over" and state.current_view == "blocking_event_popup" and state.active_blocking_event_data:  # type: ignore
            draw_blocking_event_popup_external(screen_surface, state.active_blocking_event_data, state.blocking_event_popup_buttons)  # type: ignore

        if state.current_view != "game_over" and current_player_region_for_frame:
            draw_hud_external(screen_surface, state.player_inventory_cache, current_player_region_for_frame, state.game_state_data_cache)  # type: ignore
            day_phase_text_val: str = f"Day {state.campaign_day} / {state.campaign_length} | Phase: {state.phase_names[state.campaign_phase-1]}"  # type: ignore
            draw_text(
                screen_surface,
                day_phase_text_val,
                20,
                10,
                font=FONT_MEDIUM,
                color=GOLDEN_YELLOW,
                center_aligned=False,
            )

        if state.active_prompt_message and state.prompt_message_timer > 0 and state.current_view != "game_over" and state.current_view != "blocking_event_popup":  # type: ignore
            is_prompt_handled_by_view_local: bool = (  # Renamed
                state.current_view
                in ["market_buy_input", "market_sell_input", "tech_input_amount"]
            ) or (
                state.current_view == "tech_contact"
                and "active_prompt_message" in locals()
                and state.active_prompt_message
                and "Select cryptocurrency" not in state.active_prompt_message
                and "Enter amount" not in state.active_prompt_message
            )  # type: ignore
            if not is_prompt_handled_by_view_local:
                prompt_y_val: int = SCREEN_HEIGHT - 100  # Renamed
                if state.current_view == "tech_contact":
                    prompt_y_val = SCREEN_HEIGHT - 120
                prompt_color_val: Tuple[int, int, int] = IMPERIAL_RED if "Error" in state.active_prompt_message or "Invalid" in state.active_prompt_message or "Not enough" in state.active_prompt_message else (GOLDEN_YELLOW if "Skill" in state.active_prompt_message else EMERALD_GREEN)  # type: ignore
                draw_text(screen_surface, state.active_prompt_message, SCREEN_WIDTH // 2, prompt_y_val, font=FONT_MEDIUM, color=prompt_color_val, center_aligned=True, max_width=SCREEN_WIDTH - 40)  # type: ignore

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

    pygame.quit()
    sys.exit()
