# views/market_view.py
"""
Handles drawing the Market view and related transaction input popups.
"""
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ...core.player_inventory import PlayerInventory
    from ...core.region import Region

from ...core.enums import DrugName, DrugQuality # Keep for type hints if any
from ..ui_components import Button
from ..ui_theme import (
    DARK_GREY, EMERALD_GREEN, FONT_LARGE, FONT_MEDIUM, FONT_SMALL,
    GHOST_WHITE, GOLDEN_YELLOW, IMPERIAL_RED, MEDIUM_GREY, OXFORD_BLUE,
    PLATINUM, SILVER_LAKE_BLUE, TEXT_COLOR, YALE_BLUE,
    TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR, TEXT_INPUT_TEXT_COLOR, # For popup
    draw_input_box, draw_text, # Keep draw_text for specific rendering
)
from ..ui_base_elements import (
    draw_view_background,
    draw_main_container,
    draw_view_title,
    draw_content_panel,
    draw_panel_header, # For the column headers' background
    draw_column_headers, # For drawing the actual column header text
)
from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT


# Layout constants
TITLE_Y = 40
CONTENT_PANEL_Y = 120 # Market data container starts here
CONTENT_PANEL_HEIGHT = SCREEN_HEIGHT - 200 # Original market_rect height
COLUMN_HEADER_BAR_Y = CONTENT_PANEL_Y + 10 # Y for the rect behind headers
COLUMN_HEADER_TEXT_Y = COLUMN_HEADER_BAR_Y + 10 # Y for the text of headers
DRUG_LIST_START_Y = COLUMN_HEADER_TEXT_Y + 40 # Start Y for the drug items list

# Helper functions for trend icons (specific to this view, keep them here)
def _calculate_trend_icon(
    current_price: Optional[float], previousPrice: Optional[float]
) -> Tuple[str, Tuple[int, int, int]]:
    if (
        current_price is not None
        and previousPrice is not None
        and current_price > 0
        and previousPrice > 0
    ):
        if current_price > previousPrice * 1.02:
            return "↑", EMERALD_GREEN
        elif current_price < previousPrice * 0.98:
            return "↓", IMPERIAL_RED
        else:
            return "=", TEXT_COLOR
    return "-", MEDIUM_GREY

def _get_price_movement_indicator(
    current_p: Optional[float], prev_p: Optional[float]
) -> Tuple[str, Tuple[int, int, int]]:
    if current_p is not None and prev_p is not None and current_p > 0 and prev_p > 0:
        if current_p > prev_p * 1.015: return "↑", EMERALD_GREEN
        elif current_p < prev_p * 0.985: return "↓", IMPERIAL_RED
        else: return "―", TEXT_COLOR
    return " ", MEDIUM_GREY


def draw_market_view(
    surface: pygame.Surface,
    market_region_data: "Region",
    player_inventory_data: "PlayerInventory",
    market_buttons: List[Button], # Main buttons like "Back"
    market_item_buttons: List[Button], # Buy/Sell buttons for each drug
    game_state_data: Optional[Any] = None, # Added game_state_data for seasonal events & skills
):
    draw_view_background(surface)
    draw_main_container(surface) # Default height_offset=40 is correct for market view

    region_name_str = (
        market_region_data.name.value
        if market_region_data and hasattr(market_region_data.name, "value")
        else str(market_region_data.name) if market_region_data and market_region_data.name else "Unknown Region"
    )
    draw_view_title(
        surface,
        f"DRUG MARKET - {region_name_str.upper()}",
        border_color=SILVER_LAKE_BLUE, # Market view uses a specific title border
    )

    # Market data container panel
    # Original market_rect: Rect(40, 120, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 200)
    content_panel_rect = draw_content_panel(
        surface,
        CONTENT_PANEL_Y,
        CONTENT_PANEL_HEIGHT,
        border_color=MEDIUM_GREY, # Market view uses MEDIUM_GREY for this panel border
    )

    # Column headers background bar (using draw_panel_header with custom params)
    # Original header_rect: Rect(50, header_y - 10, SCREEN_WIDTH - 100, 35)
    # header_y was 140. So this is 130.
    draw_panel_header(
        surface,
        header_text="", # No main text for this bar, it's just a background
        y_offset=COLUMN_HEADER_BAR_Y, # Original: header_y - 10 = 140 - 10 = 130
        height=35,
        x=content_panel_rect.x + 10, # original x was 50, panel_x is 40
        width_offset=100, # SCREEN_WIDTH - 100
        bg_color=OXFORD_BLUE, # Specific color for this header bar
        border_color=YALE_BLUE,
        center_text=False # Not applicable as text is empty
    )

    # Column headers text (using the new draw_column_headers)
    col_xs = {"drug": 70, "buy": 280, "sell": 380, "stock": 480, "trend": 580, "actions": 650}
    headers_config = [
        {"text": "DRUG (QUALITY)", "x": col_xs["drug"], "color": PLATINUM},
        {"text": "BUY PRICE", "x": col_xs["buy"], "color": EMERALD_GREEN},
        {"text": "SELL PRICE", "x": col_xs["sell"], "color": EMERALD_GREEN},
        {"text": "STOCK", "x": col_xs["stock"], "color": PLATINUM},
    ]
    if "MARKET_INTUITION" in player_inventory_data.unlocked_skills:
        headers_config.append({"text": "TREND", "x": col_xs["trend"], "color": GOLDEN_YELLOW})
    headers_config.append({"text": "ACTIONS", "x": col_xs["actions"] + 35, "color": PLATINUM})

    draw_column_headers(surface, headers_config, COLUMN_HEADER_TEXT_Y, font=FONT_MEDIUM)


    # --- Drug List Rendering (largely kept from original, with adjustments for panel relative coords) ---
    current_y_offset = DRUG_LIST_START_Y
    line_height = 35

    if not market_region_data or not market_region_data.drug_market_data:
        # No data message - this could also be a shared function if common enough
        # For now, keep it specific. Use panel relative coords for positioning.
        no_data_rect_x = content_panel_rect.centerx - 150
        no_data_rect_y = current_y_offset + 20
        no_data_rect = pygame.Rect(no_data_rect_x, no_data_rect_y, 300, 50)
        pygame.draw.rect(surface, DARK_GREY, no_data_rect)
        pygame.draw.rect(surface, IMPERIAL_RED, no_data_rect, 2)
        draw_text(
            surface, "NO DRUGS TRADED HERE",
            no_data_rect.centerx, no_data_rect.centery,
            font=FONT_MEDIUM, color=IMPERIAL_RED, center_aligned=True,
        )
    else:
        show_trend_icons = "MARKET_INTUITION" in player_inventory_data.unlocked_skills
        button_pair_index = 0
        mouse_pos = pygame.mouse.get_pos()
        # Ensure items are drawn within the content panel boundaries
        # X positions for drug list items should be relative to content_panel_rect.x or absolute as before
        # Y positions should not exceed content_panel_rect.bottom

        sorted_drug_names = sorted(
            market_region_data.drug_market_data.keys(), key=lambda d: d.value
        )
        row_count = 0
        for drug_name in sorted_drug_names:
            drug_data_dict = market_region_data.drug_market_data[drug_name]
            qualities_available = drug_data_dict.get("available_qualities", {})
            if not qualities_available: continue

            for quality_enum in sorted(qualities_available.keys(), key=lambda q: q.value):
                if current_y_offset > content_panel_rect.bottom - line_height - 10: # Check against panel bottom
                    break

                # Alternating row background, relative to panel
                row_bg_x = content_panel_rect.x + 10
                row_bg_width = content_panel_rect.width - 20
                row_rect = pygame.Rect(row_bg_x, current_y_offset - 8, row_bg_width, 30)
                row_color = (12, 22, 38) if row_count % 2 == 0 else (8, 18, 35) # Theme colors
                pygame.draw.rect(surface, row_color, row_rect)

                buy_price = market_region_data.get_buy_price(drug_name, quality_enum, player_inventory_data, game_state_data)
                sell_price = market_region_data.get_sell_price(drug_name, quality_enum, player_inventory_data, game_state_data)
                stock = market_region_data.get_available_stock(drug_name, quality_enum, game_state_data) # Already correct


                # Drug name - X positions (col_xs) are absolute screen positions
                draw_text(surface, f"{drug_name.value} ({quality_enum.name.capitalize()})", col_xs["drug"], current_y_offset, font=FONT_SMALL, color=GHOST_WHITE)

                # Prices
                buy_text = f"${buy_price:.2f}" if buy_price > 0 else "---"
                buy_color = EMERALD_GREEN if buy_price > 0 else IMPERIAL_RED
                buy_price_surf = FONT_SMALL.render(buy_text, True, buy_color)
                surface.blit(buy_price_surf, (col_xs["buy"], current_y_offset))
                buy_price_width = buy_price_surf.get_width()

                sell_text = f"${sell_price:.2f}" if sell_price > 0 else "---"
                sell_color = EMERALD_GREEN if sell_price > 0 else IMPERIAL_RED
                sell_price_surf = FONT_SMALL.render(sell_text, True, sell_color)
                surface.blit(sell_price_surf, (col_xs["sell"], current_y_offset))
                sell_price_width = sell_price_surf.get_width()

                if "MARKET_ANALYST" in player_inventory_data.unlocked_skills:
                    prev_buy = drug_data_dict["available_qualities"][quality_enum].get("previous_buy_price")
                    prev_sell = drug_data_dict["available_qualities"][quality_enum].get("previous_sell_price")
                    buy_ind_char, buy_ind_color = _get_price_movement_indicator(buy_price, prev_buy)
                    sell_ind_char, sell_ind_color = _get_price_movement_indicator(sell_price, prev_sell)
                    draw_text(surface, buy_ind_char, col_xs["buy"] + buy_price_width + 5, current_y_offset, font=FONT_SMALL, color=buy_ind_color)
                    draw_text(surface, sell_ind_char, col_xs["sell"] + sell_price_width + 5, current_y_offset, font=FONT_SMALL, color=sell_ind_color)

                # Stock
                stock_color = EMERALD_GREEN if stock > 100 else GOLDEN_YELLOW if stock > 10 else IMPERIAL_RED
                draw_text(surface, str(stock), col_xs["stock"], current_y_offset, font=FONT_SMALL, color=stock_color)

                if show_trend_icons:
                    prev_price_trend = drug_data_dict["available_qualities"][quality_enum].get("previous_sell_price")
                    icon, trend_color = _calculate_trend_icon(sell_price, prev_price_trend)
                    draw_text(surface, icon, col_xs["trend"], current_y_offset, font=FONT_MEDIUM, color=trend_color)

                # Action buttons
                buy_button_idx = button_pair_index * 2
                sell_button_idx = button_pair_index * 2 + 1
                if sell_button_idx < len(market_item_buttons):
                    btn_buy = market_item_buttons[buy_button_idx]
                    btn_sell = market_item_buttons[sell_button_idx]
                    btn_buy.rect.topleft = (col_xs["actions"], current_y_offset - 10)
                    btn_sell.rect.topleft = (col_xs["actions"] + 75, current_y_offset - 10)
                    btn_buy.draw(surface, mouse_pos)
                    btn_sell.draw(surface, mouse_pos)

                button_pair_index += 1
                current_y_offset += line_height
                row_count +=1
            
            if current_y_offset > content_panel_rect.bottom - line_height - 10: break


    mouse_pos_for_back = pygame.mouse.get_pos() # Recalculate for back buttons if mouse moved
    for button in market_buttons: # "Back" button etc.
        button.draw(surface, mouse_pos_for_back)


# Transaction input view - This is more of a modal popup, less structure from main views
# It might not benefit as much from ui_base_elements meant for full views.
# Keep its drawing logic self-contained for now.
def draw_transaction_input_view(
    surface: pygame.Surface, transaction_buttons: List[Button], ui_state: Dict
):
    # This popup doesn't use the standard view background or main container.
    # It's typically drawn *over* the existing market view, often with a semi-transparent overlay.
    # For now, assuming it's drawn on a fresh surface or a dedicated part of the screen.
    # If it's a modal, it would need its own background panel.

    # Example: Draw a panel for the popup
    popup_width = 400
    popup_height = 300
    popup_x = (SCREEN_WIDTH - popup_width) // 2
    popup_y = (SCREEN_HEIGHT - popup_height) // 2
    
    # Draw a semi-transparent overlay for the whole screen first if it's a modal
    # overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    # overlay.fill((0, 0, 0, 180)) # Dark semi-transparent
    # surface.blit(overlay, (0,0))

    popup_panel_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
    pygame.draw.rect(surface, OXFORD_BLUE, popup_panel_rect) # Popup background
    pygame.draw.rect(surface, YALE_BLUE, popup_panel_rect, 2) # Popup border


    quantity_input_string = ui_state.get("quantity_input_string", "")
    drug_for_transaction = ui_state.get("drug_for_transaction")
    quality_for_transaction = ui_state.get("quality_for_transaction")
    price_for_transaction = ui_state.get("price_for_transaction", 0.0)
    available_for_transaction = ui_state.get("available_for_transaction", 0)
    current_transaction_type = ui_state.get("current_transaction_type", "N/A")
    active_prompt_message = ui_state.get("active_prompt_message")
    # prompt_message_timer = ui_state.get("prompt_message_timer", 0) # Not used directly in draw
    input_box_rect_config = ui_state.get("input_box_rect") # This is likely a config, not the final rect

    title = f"{current_transaction_type.upper()} TRANSACTION"
    draw_text(surface, title, popup_panel_rect.centerx, popup_panel_rect.top + 25,
              font=FONT_MEDIUM, color=GOLDEN_YELLOW, center_aligned=True)

    info_y = popup_panel_rect.top + 60
    if drug_for_transaction and quality_for_transaction:
        drug_name_str = getattr(drug_for_transaction, "value", str(drug_for_transaction))
        quality_name_str = quality_for_transaction.name.capitalize()
        draw_text(surface, f"Item: {drug_name_str} ({quality_name_str})",
                  popup_panel_rect.centerx, info_y, font=FONT_SMALL, color=PLATINUM, center_aligned=True)
        info_y += 25
        draw_text(surface, f"Price: ${price_for_transaction:.2f}",
                  popup_panel_rect.centerx, info_y, font=FONT_SMALL, color=TEXT_COLOR, center_aligned=True)
        info_y += 20
        max_label = "Your Stock" if current_transaction_type == "sell" else "Market Stock"
        draw_text(surface, f"{max_label}: {available_for_transaction}",
                  popup_panel_rect.centerx, info_y, font=FONT_SMALL, color=TEXT_COLOR, center_aligned=True)
        info_y += 30

        # Input box - position based on config, but centered in popup
        if input_box_rect_config: # Assuming input_box_rect_config is like (x,y,w,h)
            # Use width/height from config, but center X and use current info_y for Y
            input_w = input_box_rect_config[2]
            input_h = input_box_rect_config[3]
            input_x = popup_panel_rect.centerx - input_w // 2
            actual_input_box_rect = pygame.Rect(input_x, info_y, input_w, input_h)
            
            draw_input_box(surface, actual_input_box_rect, quantity_input_string, FONT_MEDIUM,
                           TEXT_INPUT_TEXT_COLOR, TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR,
                           is_active=True, cursor_visible=True, cursor_pos=len(quantity_input_string))
            info_y += input_h + 10 # Space after input box

        if active_prompt_message: # Removed timer check, draw if message exists
            prompt_color = IMPERIAL_RED if "Error" in active_prompt_message or "Not enough" in active_prompt_message else EMERALD_GREEN
            draw_text(surface, active_prompt_message, popup_panel_rect.centerx, info_y,
                      font=FONT_SMALL, color=prompt_color, center_aligned=True, max_width=popup_width - 20)

    mouse_pos = pygame.mouse.get_pos()
    # Buttons in the popup need their positions updated to be relative to the popup panel
    # This should ideally be handled when the buttons are created/configured for this popup state.
    # For now, assuming their rects are already correct for being inside the popup.
    for button in transaction_buttons:
        button.draw(surface, mouse_pos)

[end of src/ui_pygame/views/market_view.py]
