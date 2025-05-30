# views/market_view.py
"""
Handles drawing the Market view and related transaction input popups.
"""
import pygame
from typing import List, Optional, Dict, Tuple, TYPE_CHECKING

from core.enums import DrugName, DrugQuality 
if TYPE_CHECKING: 
    from core.player_inventory import PlayerInventory
    from core.region import Region

from ui_theme import (
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_XSMALL, YALE_BLUE, PLATINUM, TEXT_COLOR, MEDIUM_GREY, EMERALD_GREEN, IMPERIAL_RED,
    TEXT_INPUT_TEXT_COLOR, TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR,
    draw_text, draw_input_box
)
from ui_components import Button

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768 

def _calculate_trend_icon(current_price: Optional[float], previous_price: Optional[float]) -> Tuple[str, Tuple[int, int, int]]:
    if current_price is not None and previous_price is not None and current_price > 0 and previous_price > 0:
        if current_price > previous_price * 1.02: return "↑", EMERALD_GREEN
        elif current_price < previous_price * 0.98: return "↓", IMPERIAL_RED
        else: return "=", TEXT_COLOR
    return "-", MEDIUM_GREY


def draw_market_view(
    surface: pygame.Surface, 
    market_region_data: 'Region', 
    player_inventory_data: 'PlayerInventory', 
    market_buttons: List[Button], 
    market_item_buttons: List[Button] 
    ):
    region_name_str = market_region_data.name.value if market_region_data and market_region_data.name else "Unknown Region"
    draw_text(surface, f"Market: {region_name_str}", SCREEN_WIDTH // 2, 30, font=FONT_LARGE, color=YALE_BLUE, center_aligned=True)
    
    header_y = 70
    col_xs = {"drug": 30, "buy": 280, "sell": 380, "stock": 480, "trend": 560, "actions": 650}
    action_button_width = 70 # From setup_buttons in pygame_ui

    draw_text(surface, "Drug (Quality)", col_xs["drug"], header_y, font=FONT_MEDIUM, color=PLATINUM)
    draw_text(surface, "Buy", col_xs["buy"], header_y, font=FONT_MEDIUM, color=PLATINUM)
    draw_text(surface, "Sell", col_xs["sell"], header_y, font=FONT_MEDIUM, color=PLATINUM)
    draw_text(surface, "Stock", col_xs["stock"], header_y, font=FONT_MEDIUM, color=PLATINUM)
    if "MARKET_INTUITION" in player_inventory_data.unlocked_skills: 
        draw_text(surface, "Trend", col_xs["trend"], header_y, font=FONT_MEDIUM, color=PLATINUM)
    draw_text(surface, "Actions", col_xs["actions"] + 20, header_y, font=FONT_MEDIUM, color=PLATINUM)

    y_offset = header_y + 35
    line_height = 28 

    if not market_region_data or not market_region_data.drug_market_data:
        draw_text(surface, "No drugs traded here.", SCREEN_WIDTH // 2, y_offset + 20, font=FONT_MEDIUM, color=TEXT_COLOR, center_aligned=True)
    else:
        show_trend_icons = "MARKET_INTUITION" in player_inventory_data.unlocked_skills
        button_pair_index = 0 # Use pair index
        mouse_pos = pygame.mouse.get_pos()
        sorted_drug_names = sorted(market_region_data.drug_market_data.keys(), key=lambda d: d.value)

        for drug_name_enum in sorted_drug_names:
            drug_data_dict = market_region_data.drug_market_data[drug_name_enum]
            qualities_available = drug_data_dict.get("available_qualities", {})
            
            if not qualities_available:
                # Still need to draw the drug name even if no qualities, to maintain layout consistency if desired
                # For now, let's keep it as is, but this could be a point of refinement.
                # draw_text(surface, f"{drug_name_enum.value} (None)", col_xs["drug"], y_offset, font=FONT_SMALL, color=MEDIUM_GREY)
                # y_offset += line_height 
                # button_pair_index +=1 # If we were to draw placeholder buttons or ensure index consistency
                continue


            for quality_enum in sorted(qualities_available.keys(), key=lambda q: q.value):
                if y_offset > SCREEN_HEIGHT - 100: break 
                
                buy_price = market_region_data.get_buy_price(drug_name_enum, quality_enum)
                sell_price = market_region_data.get_sell_price(drug_name_enum, quality_enum)
                stock = market_region_data.get_available_stock(drug_name_enum, quality_enum)

                draw_text(surface, f"{drug_name_enum.value} ({quality_enum.name.capitalize()})", col_xs["drug"], y_offset, font=FONT_SMALL, color=TEXT_COLOR)
                draw_text(surface, f"${buy_price:.2f}" if buy_price > 0 else "---", col_xs["buy"], y_offset, font=FONT_SMALL, color=EMERALD_GREEN if buy_price > 0 else MEDIUM_GREY)
                draw_text(surface, f"${sell_price:.2f}" if sell_price > 0 else "---", col_xs["sell"], y_offset, font=FONT_SMALL, color=EMERALD_GREEN if sell_price > 0 else MEDIUM_GREY)
                draw_text(surface, str(stock), col_xs["stock"], y_offset, font=FONT_SMALL, color=TEXT_COLOR)

                if show_trend_icons:
                    prev_price = drug_data_dict["available_qualities"][quality_enum].get("previous_sell_price")
                    icon, trend_color = _calculate_trend_icon(sell_price, prev_price)
                    draw_text(surface, icon, col_xs["trend"], y_offset, font=FONT_SMALL, color=trend_color)
                
                buy_button_idx = button_pair_index * 2
                sell_button_idx = button_pair_index * 2 + 1

                if sell_button_idx < len(market_item_buttons):
                    button_buy = market_item_buttons[buy_button_idx]
                    button_sell = market_item_buttons[sell_button_idx]
                    
                    # Set correct Y position for this row's buttons
                    button_buy.rect.top = y_offset - 2 
                    button_sell.rect.top = y_offset - 2
                    
                    # Buttons are already positioned horizontally in setup_buttons
                    # button_buy.rect.left = col_xs["actions"] 
                    # button_sell.rect.left = col_xs["actions"] + action_button_width + 5

                    button_buy.draw(surface, mouse_pos)
                    button_sell.draw(surface, mouse_pos)
                
                button_pair_index += 1 # Increment for each drug/quality pair
                y_offset += line_height
            if y_offset > SCREEN_HEIGHT - 100: break # Break outer loop too if screen full
            
    mouse_pos_for_back = pygame.mouse.get_pos()
    for button in market_buttons: 
        button.draw(surface, mouse_pos_for_back)


def draw_transaction_input_view(
    surface: pygame.Surface, 
    transaction_buttons: List[Button],
    ui_state: Dict 
    ):
    
    quantity_input_string = ui_state.get('quantity_input_string', "")
    drug_for_transaction = ui_state.get('drug_for_transaction')
    quality_for_transaction = ui_state.get('quality_for_transaction')
    price_for_transaction = ui_state.get('price_for_transaction', 0.0)
    available_for_transaction = ui_state.get('available_for_transaction', 0)
    current_transaction_type = ui_state.get('current_transaction_type', "N/A")
    active_prompt_message = ui_state.get('active_prompt_message')
    prompt_message_timer = ui_state.get('prompt_message_timer', 0)
    input_box_rect = ui_state.get('input_box_rect') 

    title = f"Market: {current_transaction_type.upper()}"
    draw_text(surface, title, SCREEN_WIDTH // 2, 50, font=FONT_LARGE, color=YALE_BLUE, center_aligned=True)
    
    info_y = 120
    if drug_for_transaction and quality_for_transaction and input_box_rect:
        drug_name_str = drug_for_transaction.value 
        quality_name_str = quality_for_transaction.name.capitalize() 
        draw_text(surface, f"Item: {drug_name_str} ({quality_name_str})", SCREEN_WIDTH // 2, info_y, font=FONT_MEDIUM, color=PLATINUM, center_aligned=True)
        info_y += 30
        draw_text(surface, f"Price: ${price_for_transaction:.2f}", SCREEN_WIDTH // 2, info_y, font=FONT_SMALL, color=TEXT_COLOR, center_aligned=True)
        info_y += 25
        max_transact_label = "Your Stock" if current_transaction_type == "sell" else "Market Stock"
        draw_text(surface, f"{max_transact_label}: {available_for_transaction}", SCREEN_WIDTH // 2, info_y, font=FONT_SMALL, color=TEXT_COLOR, center_aligned=True)
        info_y += 40

        current_input_box_rect = pygame.Rect(input_box_rect) 
        current_input_box_rect.top = info_y 
        
        draw_input_box(surface, current_input_box_rect, quantity_input_string, FONT_MEDIUM, 
                       TEXT_INPUT_TEXT_COLOR, TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR, 
                       is_active=True, cursor_visible=True, cursor_pos=len(quantity_input_string)) 
        info_y += 60

        if active_prompt_message and prompt_message_timer > 0:
            prompt_color = IMPERIAL_RED if "Error" in active_prompt_message or "Not enough" in active_prompt_message else EMERALD_GREEN
            draw_text(surface, active_prompt_message, SCREEN_WIDTH // 2, info_y, font=FONT_SMALL, color=prompt_color, center_aligned=True, max_width=SCREEN_WIDTH - 40)
            
    mouse_pos = pygame.mouse.get_pos()
    for button in transaction_buttons: 
        button.draw(surface, mouse_pos)
