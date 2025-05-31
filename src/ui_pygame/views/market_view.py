# views/market_view.py
"""
Handles drawing the Market view and related transaction input popups.
"""
import pygame
from typing import List, Optional, Dict, Tuple, TYPE_CHECKING

from ...core.enums import DrugName, DrugQuality 
if TYPE_CHECKING: 
    from ...core.player_inventory import PlayerInventory
    from ...core.region import Region

from ..ui_theme import (
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_XSMALL, YALE_BLUE, PLATINUM, TEXT_COLOR, MEDIUM_GREY, EMERALD_GREEN, IMPERIAL_RED,
    TEXT_INPUT_TEXT_COLOR, TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR, SILVER_LAKE_BLUE, GOLDEN_YELLOW, OXFORD_BLUE, 
    DARK_GREY, GHOST_WHITE, draw_text, draw_input_box
)
from ..ui_components import Button

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768 

def _calculate_trend_icon(current_price: Optional[float], previousPrice: Optional[float]) -> Tuple[str, Tuple[int, int, int]]:
    if current_price is not None and previousPrice is not None and current_price > 0 and previousPrice > 0:
        if current_price > previousPrice * 1.02: return "↑", EMERALD_GREEN
        elif current_price < previousPrice * 0.98: return "↓", IMPERIAL_RED
        else: return "=", TEXT_COLOR
    return "-", MEDIUM_GREY

# Helper function for Market Analyst skill
def _get_price_movement_indicator(current_p: Optional[float], prev_p: Optional[float]) -> Tuple[str, Tuple[int, int, int]]:
    if current_p is not None and prev_p is not None and current_p > 0 and prev_p > 0:
        # Using a slightly larger tolerance for more meaningful changes
        if current_p > prev_p * 1.015:  # Price increased by more than 1.5%
            return "↑", EMERALD_GREEN  # Up arrow
        elif current_p < prev_p * 0.985: # Price decreased by more than 1.5%
            return "↓", IMPERIAL_RED    # Down arrow
        else:
            return "―", TEXT_COLOR     # Stable dash / hyphen-minus
    return " ", MEDIUM_GREY # No data, not applicable, or price is zero


def draw_market_view(
    surface: pygame.Surface, 
    market_region_data: 'Region', 
    player_inventory_data: 'PlayerInventory', 
    market_buttons: List[Button], 
    market_item_buttons: List[Button] 
    ):
    
    # Clear background with gradient effect
    surface.fill((5, 15, 30))  # Dark blue background
    
    # Draw main container with border
    main_container = pygame.Rect(20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40)
    pygame.draw.rect(surface, (15, 25, 45), main_container)
    pygame.draw.rect(surface, YALE_BLUE, main_container, 3)
    
    # Title section with background
    title_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, 60)
    pygame.draw.rect(surface, (10, 20, 40), title_rect)
    pygame.draw.rect(surface, SILVER_LAKE_BLUE, title_rect, 2)
    
    region_name_str = market_region_data.name.value if market_region_data and hasattr(market_region_data.name, 'value') else str(market_region_data.name) if market_region_data and market_region_data.name else "Unknown Region"
    draw_text(surface, f"DRUG MARKET - {region_name_str.upper()}", SCREEN_WIDTH // 2, 70, 
              font=FONT_LARGE, color=GOLDEN_YELLOW, center_aligned=True)
    
    # Market data container
    market_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 200)
    pygame.draw.rect(surface, (8, 18, 35), market_rect)
    pygame.draw.rect(surface, MEDIUM_GREY, market_rect, 1)
    
    # Column headers with background
    header_y = 140
    header_rect = pygame.Rect(50, header_y - 10, SCREEN_WIDTH - 100, 35)
    pygame.draw.rect(surface, OXFORD_BLUE, header_rect)
    pygame.draw.rect(surface, YALE_BLUE, header_rect, 1)
    
    # Improved column layout - more symmetric
    col_xs = {
        "drug": 70, 
        "buy": 280, 
        "sell": 380, 
        "stock": 480, 
        "trend": 580, 
        "actions": 650
    }
    
    # Headers with better styling
    draw_text(surface, "DRUG (QUALITY)", col_xs["drug"], header_y + 10, font=FONT_MEDIUM, color=PLATINUM)
    draw_text(surface, "BUY PRICE", col_xs["buy"], header_y + 10, font=FONT_MEDIUM, color=EMERALD_GREEN)
    draw_text(surface, "SELL PRICE", col_xs["sell"], header_y + 10, font=FONT_MEDIUM, color=EMERALD_GREEN)
    draw_text(surface, "STOCK", col_xs["stock"], header_y + 10, font=FONT_MEDIUM, color=PLATINUM)
    if "MARKET_INTUITION" in player_inventory_data.unlocked_skills: 
        draw_text(surface, "TREND", col_xs["trend"], header_y + 10, font=FONT_MEDIUM, color=GOLDEN_YELLOW)
    draw_text(surface, "ACTIONS", col_xs["actions"] + 35, header_y + 10, font=FONT_MEDIUM, color=PLATINUM)

    y_offset = header_y + 50
    line_height = 35  # Increased for better spacing

    if not market_region_data or not market_region_data.drug_market_data:
        # No data message with styling
        no_data_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, y_offset + 20, 300, 50)
        pygame.draw.rect(surface, DARK_GREY, no_data_rect)
        pygame.draw.rect(surface, IMPERIAL_RED, no_data_rect, 2)
        draw_text(surface, "NO DRUGS TRADED HERE", SCREEN_WIDTH // 2, y_offset + 45, 
                  font=FONT_MEDIUM, color=IMPERIAL_RED, center_aligned=True)
    else:
        show_trend_icons = "MARKET_INTUITION" in player_inventory_data.unlocked_skills
        button_pair_index = 0
        mouse_pos = pygame.mouse.get_pos()
        sorted_drug_names = sorted(market_region_data.drug_market_data.keys(), key=lambda d: d.value)
        
        row_count = 0
        for drug_name in sorted_drug_names:
            drug_data_dict = market_region_data.drug_market_data[drug_name]
            qualities_available = drug_data_dict.get("available_qualities", {})
            
            if not qualities_available:
                continue

            for quality_enum in sorted(qualities_available.keys(), key=lambda q: q.value):
                if y_offset > SCREEN_HEIGHT - 150: break
                
                # Alternating row background
                row_rect = pygame.Rect(50, y_offset - 8, SCREEN_WIDTH - 100, 30)
                row_color = (12, 22, 38) if row_count % 2 == 0 else (8, 18, 35)
                pygame.draw.rect(surface, row_color, row_rect)
                
                buy_price = market_region_data.get_buy_price(drug_name, quality_enum)
                sell_price = market_region_data.get_sell_price(drug_name, quality_enum)
                # Pass player_inventory_data.heat to get_available_stock
                stock = market_region_data.get_available_stock(drug_name, quality_enum, player_inventory_data.heat)

                # Drug name with quality styling
                drug_display = f"{drug_name} ({quality_enum.name.capitalize()})"
                draw_text(surface, drug_display, col_xs["drug"], y_offset, font=FONT_SMALL, color=GHOST_WHITE)
                
                # Price displays with better formatting
                buy_text = f"${buy_price:.2f}" if buy_price > 0 else "---"
                buy_color = EMERALD_GREEN if buy_price > 0 else IMPERIAL_RED
                # Draw buy price text
                buy_price_surface = FONT_SMALL.render(buy_text, True, buy_color)
                surface.blit(buy_price_surface, (col_xs["buy"], y_offset))
                buy_price_text_width = buy_price_surface.get_width()
                
                sell_color = EMERALD_GREEN if sell_price > 0 else IMPERIAL_RED
                # Define sell_text before using it
                sell_text = f"${sell_price:.2f}" if sell_price > 0 else "---"
                # Draw sell price text
                sell_price_surface = FONT_SMALL.render(sell_text, True, sell_color)
                surface.blit(sell_price_surface, (col_xs["sell"], y_offset))
                sell_price_text_width = sell_price_surface.get_width()

                # Market Analyst Skill: Price Movement Indicators
                if "MARKET_ANALYST" in player_inventory_data.unlocked_skills:
                    prev_buy_price = drug_data_dict["available_qualities"][quality_enum].get("previous_buy_price")
                    prev_sell_price = drug_data_dict["available_qualities"][quality_enum].get("previous_sell_price")

                    buy_indicator_char, buy_indicator_color = _get_price_movement_indicator(buy_price, prev_buy_price)
                    sell_indicator_char, sell_indicator_color = _get_price_movement_indicator(sell_price, prev_sell_price)

                    # Draw indicators next to the prices
                    indicator_offset_x = 5 # Small gap
                    draw_text(surface, buy_indicator_char, col_xs["buy"] + buy_price_text_width + indicator_offset_x, y_offset, font=FONT_SMALL, color=buy_indicator_color)
                    draw_text(surface, sell_indicator_char, col_xs["sell"] + sell_price_text_width + indicator_offset_x, y_offset, font=FONT_SMALL, color=sell_indicator_color)

                # Stock with color coding
                stock_color = EMERALD_GREEN if stock > 100 else GOLDEN_YELLOW if stock > 10 else IMPERIAL_RED
                draw_text(surface, str(stock), col_xs["stock"], y_offset, font=FONT_SMALL, color=stock_color)

                # Trend indicators
                if show_trend_icons:
                    prev_price = drug_data_dict["available_qualities"][quality_enum].get("previous_sell_price")
                    icon, trend_color = _calculate_trend_icon(sell_price, prev_price)
                    draw_text(surface, icon, col_xs["trend"], y_offset, font=FONT_MEDIUM, color=trend_color)
                
                # Action buttons with improved positioning
                buy_button_idx = button_pair_index * 2
                sell_button_idx = button_pair_index * 2 + 1

                if sell_button_idx < len(market_item_buttons):
                    button_buy = market_item_buttons[buy_button_idx]
                    button_sell = market_item_buttons[sell_button_idx]
                    
                    # Position buttons properly
                    button_buy.rect.top = y_offset - 10
                    button_sell.rect.top = y_offset - 10
                    button_buy.rect.left = col_xs["actions"]
                    button_sell.rect.left = col_xs["actions"] + 75

                    button_buy.draw(surface, mouse_pos)
                    button_sell.draw(surface, mouse_pos)
                
                button_pair_index += 1
                y_offset += line_height
                row_count += 1
                
            if y_offset > SCREEN_HEIGHT - 150: break
            
    # Draw all market buttons (including Back button)
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
        drug_name_str = getattr(drug_for_transaction, 'value', str(drug_for_transaction))
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
