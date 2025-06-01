"""
UI setup and button setup functions for Project Narco-Syndicate Pygame UI.
Split from app.py for modularity.
"""

from .ui_components import Button
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..core.enums import SkillID  # Added for skill buttons
from typing import Any

# All setup_buttons and related UI setup functions will be moved here from app.py
# This file will be filled in the next step.


def setup_buttons(
    game_state: Any,
    player_inv: PlayerInventory,
    game_configs: Any,
    current_region: Region,
):
    from . import state, actions
    from .constants import (
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        FONT_MEDIUM,
        FONT_SMALL,
        FONT_XSMALL,
    )
    import functools

    # Clear all button lists
    state.main_menu_buttons.clear()
    state.market_view_buttons.clear()
    state.market_buy_sell_buttons.clear()
    state.inventory_view_buttons.clear()
    state.travel_view_buttons.clear()
    state.tech_contact_view_buttons.clear()
    state.skills_view_buttons.clear()
    state.upgrades_view_buttons.clear()
    state.transaction_input_buttons.clear()
    state.blocking_event_popup_buttons.clear()
    state.game_over_buttons.clear()
    state.informant_view_buttons.clear()

    button_width, button_height = 200, 50
    spacing = 10
    start_x = SCREEN_WIDTH // 2 - button_width // 2

    if state.current_view == "main_menu":
        actions_list = [
            ("Market", actions.action_open_market),
            ("Inventory", actions.action_open_inventory),
            ("Travel", actions.action_open_travel),
            ("Tech Contact", actions.action_open_tech_contact),
            ("Meet Informant", actions.action_open_informant),
            ("Skills", actions.action_open_skills),
            ("Upgrades", actions.action_open_upgrades),
        ]
        cols = 2
        rows = (len(actions_list) + 1) // 2
        grid_width = cols * button_width + (cols - 1) * spacing
        grid_x = SCREEN_WIDTH // 2 - grid_width // 2
        grid_y = 220
        for idx, (text, action) in enumerate(actions_list):
            col = idx % cols
            row = idx // cols
            x = grid_x + col * (button_width + spacing)
            y = grid_y + row * (button_height + spacing)
            state.main_menu_buttons.append(
                Button(
                    x, y, button_width, button_height, text, action, font=FONT_MEDIUM
                )
            )

    elif state.current_view == "inventory":
        state.inventory_view_buttons.append(
            Button(
                SCREEN_WIDTH - button_width - 20,
                SCREEN_HEIGHT - button_height - 20,
                button_width,
                button_height,
                "Back",
                actions.action_open_main_menu,
                font=FONT_SMALL,
            )
        )

    elif state.current_view == "travel":
        from ..core.enums import RegionName

        travel_y_start = 120
        for i, region_enum in enumerate(RegionName):
            if region_enum.value == current_region.name:
                continue
            dest_region_obj = game_state.all_regions[region_enum]
            travel_cost = 50
            region_label = (
                region_enum.value
                if isinstance(region_enum.value, str)
                else str(region_enum)
            )
            btn_text = f"{region_label} (${travel_cost})"
            can_travel = player_inv.cash >= travel_cost
            state.travel_view_buttons.append(
                Button(
                    start_x,
                    travel_y_start + i * (button_height + spacing),
                    button_width,
                    button_height,
                    btn_text,
                    functools.partial(
                        actions.action_travel_to_region,
                        dest_region_obj,
                        player_inv,
                        game_state,
                    ),
                    is_enabled=can_travel,
                    font=FONT_SMALL,
                )
            )
        state.travel_view_buttons.append(
            Button(
                SCREEN_WIDTH - button_width - 20,
                SCREEN_HEIGHT - button_height - 20,
                button_width,
                button_height,
                "Back",
                actions.action_open_main_menu,
                font=FONT_SMALL,
            )
        )

    elif state.current_view == "market":
        from ..core.enums import DrugName, DrugQuality

        state.market_view_buttons.append(
            Button(
                SCREEN_WIDTH - button_width - 20,
                SCREEN_HEIGHT - button_height - 20,
                button_width,
                button_height,
                "Back",
                actions.action_open_main_menu,
                font=FONT_SMALL,
            )
        )
        col_xs = {"actions": 650}
        action_button_width = 70
        action_button_height = 22
        all_drugs = list(DrugName)
        all_qualities = list(DrugQuality)
        button_y_offset_start = 140 + 50
        line_h = 35
        current_button_y = button_y_offset_start
        for drug_enum in all_drugs:
            drug_name = drug_enum.value
            drug_data_dict = current_region.drug_market_data.get(drug_name, None)
            for quality_enum in all_qualities:
                if drug_data_dict and quality_enum in drug_data_dict.get(
                    "available_qualities", {}
                ):
                    buy_price = current_region.get_buy_price(drug_name, quality_enum)
                    sell_price = current_region.get_sell_price(drug_name, quality_enum)
                    market_stock = current_region.get_available_stock(
                        drug_name, quality_enum
                    )
                else:
                    buy_price = 0
                    sell_price = 0
                    market_stock = 0
                player_stock_item = player_inv.get_drug_item(drug_name, quality_enum)
                player_has_stock = (
                    player_stock_item["quantity"] if player_stock_item else 0
                )
                can_buy = (
                    buy_price > 0 and market_stock > 0 and player_inv.cash >= buy_price
                )
                can_sell = sell_price > 0 and player_has_stock > 0
                if drug_data_dict:
                    available_qualities = list(
                        drug_data_dict.get("available_qualities", {}).keys()
                    )
                    if (
                        len(available_qualities) == 1
                        and quality_enum in available_qualities
                    ):
                        buy_action = functools.partial(
                            actions.action_initiate_buy,
                            drug_enum,
                            quality_enum,
                            buy_price,
                            market_stock,
                        )
                    elif quality_enum in available_qualities:
                        buy_action = functools.partial(
                            actions.action_open_quality_select, drug_enum
                        )
                    else:
                        buy_action = None
                else:
                    buy_action = None
                if buy_action:
                    state.market_buy_sell_buttons.append(
                        Button(
                            col_xs["actions"],
                            current_button_y - 10,
                            action_button_width,
                            action_button_height,
                            "Buy",
                            buy_action,
                            is_enabled=can_buy,
                            font=FONT_XSMALL,
                        )
                    )
                else:
                    state.market_buy_sell_buttons.append(
                        Button(
                            col_xs["actions"],
                            current_button_y - 10,
                            action_button_width,
                            action_button_height,
                            "Buy",
                            lambda: None,
                            is_enabled=False,
                            font=FONT_XSMALL,
                        )
                    )
                state.market_buy_sell_buttons.append(
                    Button(
                        col_xs["actions"] + action_button_width + 5,
                        current_button_y - 10,
                        action_button_width,
                        action_button_height,
                        "Sell",
                        functools.partial(
                            actions.action_initiate_sell,
                            drug_enum,
                            quality_enum,
                            sell_price,
                            player_has_stock,
                        ),
                        is_enabled=can_sell,
                        font=FONT_XSMALL,
                    )
                )
                current_button_y += line_h
            if current_button_y > SCREEN_HEIGHT - 150:
                break

    elif state.current_view == "tech_contact":
        tech_btn_y_start = SCREEN_HEIGHT - button_height * 4 - spacing * 4 - 20
        tech_btn_width, tech_btn_height = 220, 40
        tech_col1_x = 50
        tech_col2_x = SCREEN_WIDTH // 2 + 50
        state.tech_contact_view_buttons.append(
            Button(
                tech_col1_x,
                tech_btn_y_start,
                tech_btn_width,
                tech_btn_height,
                "Buy Crypto",
                functools.partial(actions.action_initiate_tech_operation, "buy_crypto"),
                font=FONT_SMALL,
            )
        )
        state.tech_contact_view_buttons.append(
            Button(
                tech_col1_x,
                tech_btn_y_start + tech_btn_height + spacing,
                tech_btn_width,
                tech_btn_height,
                "Sell Crypto",
                functools.partial(
                    actions.action_initiate_tech_operation, "sell_crypto"
                ),
                font=FONT_SMALL,
            )
        )
        state.tech_contact_view_buttons.append(
            Button(
                tech_col1_x,
                tech_btn_y_start + 2 * (tech_btn_height + spacing),
                tech_btn_width,
                tech_btn_height,
                "Launder Cash",
                functools.partial(
                    actions.action_initiate_tech_operation, "launder_cash"
                ),
                font=FONT_SMALL,
            )
        )
        state.tech_contact_view_buttons.append(
            Button(
                tech_col2_x,
                tech_btn_y_start,
                tech_btn_width,
                tech_btn_height,
                "Stake DrugCoin",
                functools.partial(actions.action_initiate_tech_operation, "stake_dc"),
                font=FONT_SMALL,
            )
        )
        state.tech_contact_view_buttons.append(
            Button(
                tech_col2_x,
                tech_btn_y_start + tech_btn_height + spacing,
                tech_btn_width,
                tech_btn_height,
                "Unstake DrugCoin",
                functools.partial(actions.action_initiate_tech_operation, "unstake_dc"),
                font=FONT_SMALL,
            )
        )
        state.tech_contact_view_buttons.append(
            Button(
                SCREEN_WIDTH - button_width - 20,
                SCREEN_HEIGHT - button_height - 20,
                button_width,
                button_height,
                "Back",
                actions.action_open_main_menu,
                font=FONT_SMALL,
            )
        )

    elif state.current_view == "skills":
        state.skills_view_buttons.append(
            Button(
                SCREEN_WIDTH - button_width - 20,
                SCREEN_HEIGHT - button_height - 20,
                button_width,
                button_height,
                "Back",
                actions.action_open_main_menu,
                font=FONT_SMALL,
            )
        )

        skill_button_width = 150
        skill_button_height = 30
        # Positions need to align with how draw_skills_view lays out text
        skill_y_start_buttons = 240  # Matches text y in draw_skills_view
        skill_item_v_spacing = 80  # Matches text v_spacing in draw_skills_view
        button_x_pos = SCREEN_WIDTH - skill_button_width - 70  # Position to the right

        if hasattr(game_configs, "SKILL_DEFINITIONS"):
            for idx, (skill_id_enum, skill_def) in enumerate(
                game_configs.SKILL_DEFINITIONS.items()
            ):
                # skill_id_enum is the Enum member, e.g., SkillID.COMPARTMENTALIZATION
                # skill_def is the dictionary from SKILL_DEFINITIONS

                skill_id_str = (
                    skill_id_enum.value
                )  # Get the string value, e.g., "COMPARTMENTALIZATION"

                current_skill_button_y = (
                    skill_y_start_buttons
                    + (idx * skill_item_v_spacing)
                    - (skill_button_height // 4)
                )  # Adjust Y to align with skill name

                if skill_id_str not in player_inv.unlocked_skills:
                    can_unlock = player_inv.skill_points >= skill_def["cost"]
                    unlock_action = functools.partial(
                        actions.action_unlock_skill,
                        player_inv,  # player_inv_cache
                        skill_id_str,  # skill_id_str
                        skill_def["name"],  # skill_name_str
                        skill_def["cost"],  # skill_cost
                        game_state,  # game_state_cache
                        game_configs,  # game_configs_data_cache
                    )
                    state.skills_view_buttons.append(
                        Button(
                            button_x_pos,
                            current_skill_button_y,
                            skill_button_width,
                            skill_button_height,
                            f"Unlock ({skill_def['cost']} SP)",
                            unlock_action,
                            is_enabled=can_unlock,
                            font=FONT_XSMALL,  # Smaller font for these buttons
                        )
                    )
                # else: No button if already unlocked, view shows "Unlocked"

    elif state.current_view == "upgrades":
        state.upgrades_view_buttons.append(
            Button(
                SCREEN_WIDTH - button_width - 20,
                SCREEN_HEIGHT - button_height - 20,
                button_width,
                button_height,
                "Back",
                actions.action_open_main_menu,
                font=FONT_SMALL,
            )
        )

    elif state.current_view == "informant":
        state.informant_view_buttons.append(
            Button(
                SCREEN_WIDTH - button_width - 20,
                SCREEN_HEIGHT - button_height - 20,
                button_width,
                button_height,
                "Back",
                actions.action_open_main_menu,
                font=FONT_SMALL,
            )
        )

    elif state.current_view == "market_quality_select":
        # Show quality options for the selected drug
        from ..core.enums import DrugQuality

        qualities = [DrugQuality.CUT, DrugQuality.STANDARD, DrugQuality.PURE]
        button_width, button_height = 180, 50
        spacing = 20
        start_x = SCREEN_WIDTH // 2 - button_width // 2
        start_y = 220
        for i, quality in enumerate(qualities):

            def make_quality_action(q):
                def _action():
                    from . import actions, state

                    state.quality_for_transaction = q
                    # After selecting quality, go to buy input for that quality
                    # Use default buy price and stock for now (can be improved)
                    region = state.game_state_data_cache.current_player_region
                    drug_enum = state.drug_for_transaction
                    buy_price = region.get_buy_price(drug_enum.value, q)
                    market_stock = region.get_available_stock(drug_enum.value, q)
                    actions.action_initiate_buy(drug_enum, q, buy_price, market_stock)

                return _action

            btn_text = f"{quality.name.capitalize()}"
            state.transaction_input_buttons.append(
                Button(
                    start_x,
                    start_y + i * (button_height + spacing),
                    button_width,
                    button_height,
                    btn_text,
                    make_quality_action(quality),
                    font=FONT_MEDIUM,
                )
            )
        # Add cancel button
        state.transaction_input_buttons.append(
            Button(
                SCREEN_WIDTH - button_width - 20,
                SCREEN_HEIGHT - button_height - 20,
                button_width,
                button_height,
                "Cancel",
                actions.action_cancel_transaction,
                font=FONT_SMALL,
            )
        )
