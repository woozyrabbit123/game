# views/tech_contact_view.py
"""
Handles drawing the Tech Contact view and its sub-views for coin selection and amount input.
"""
import pygame
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.player_inventory import PlayerInventory
    from ...core.region import Region 
    from ...game_state import GameState 
    from ...game_configs import GameConfigs 

from ...core.enums import CryptoCoin

from ..ui_theme import (
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_XSMALL, YALE_BLUE, PLATINUM, TEXT_COLOR, NEON_BLUE, MEDIUM_GREY, LIGHT_GREY,
    IMPERIAL_RED, EMERALD_GREEN, GOLDEN_YELLOW,
    TEXT_INPUT_TEXT_COLOR, TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR,
    draw_text, draw_input_box
)
from ..ui_components import Button

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

def _draw_tech_shared_info(surface: pygame.Surface, player_inventory_data: 'PlayerInventory', game_state_data: 'GameState'):
    # Shared info container
    info_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, 150)
    pygame.draw.rect(surface, (8, 18, 35), info_rect)
    pygame.draw.rect(surface, YALE_BLUE, info_rect, 1)
    
    # Info header
    info_header_rect = pygame.Rect(50, 130, SCREEN_WIDTH - 100, 30)
    pygame.draw.rect(surface, (25, 35, 55), info_header_rect)
    pygame.draw.rect(surface, YALE_BLUE, info_header_rect, 1)
    draw_text(surface, "ACCOUNT OVERVIEW", SCREEN_WIDTH // 2, 145, 
              font=FONT_MEDIUM, color=PLATINUM, center_aligned=True)
    
    y_offset = 180
    line_height = 25
    
    col1_x = 60
    col2_x = SCREEN_WIDTH // 2 + 20
    current_y_col1 = y_offset
    current_y_col2 = y_offset
    
    # Cash section with background
    cash_rect = pygame.Rect(col1_x - 10, current_y_col1 - 5, 200, 25)
    pygame.draw.rect(surface, (12, 22, 38), cash_rect)
    draw_text(surface, f"Cash: ${player_inventory_data.cash:,.2f}", col1_x, current_y_col1, font=FONT_MEDIUM, color=GOLDEN_YELLOW)
    current_y_col1 += line_height
    
    # Crypto holdings header
    crypto_header_rect = pygame.Rect(col1_x - 10, current_y_col1 - 5, 200, 20)
    pygame.draw.rect(surface, (15, 25, 40), crypto_header_rect)
    draw_text(surface, "Crypto Holdings:", col1_x, current_y_col1, font=FONT_MEDIUM, color=PLATINUM)
    current_y_col1 += line_height
    
    wallet_empty = True
    if player_inventory_data.crypto_wallet:
        for i, (coin, amount) in enumerate(player_inventory_data.crypto_wallet.items()):
            if amount > 0.00001: # Only show if substantial amount
                wallet_empty = False
                price = game_state_data.current_crypto_prices.get(coin, 0)
                value_usd = amount * price
                # Alternating backgrounds for crypto holdings
                if i % 2 == 0:
                    crypto_row_rect = pygame.Rect(col1_x, current_y_col1 - 5, 190, 20)
                    pygame.draw.rect(surface, (12, 22, 38), crypto_row_rect)
                draw_text(surface, f"  {coin.value}: {amount:.4f} (${value_usd:,.2f})", col1_x + 10, current_y_col1, font=FONT_SMALL, color=NEON_BLUE)
                current_y_col1 += line_height

    # Display Staked DC and Pending Rewards in second column
    staking_header_rect = pygame.Rect(col2_x - 10, current_y_col2 - 5, 200, 20)
    pygame.draw.rect(surface, (15, 25, 40), staking_header_rect)
    draw_text(surface, "Staking Information:", col2_x, current_y_col2, font=FONT_MEDIUM, color=PLATINUM)
    current_y_col2 += line_height    
    staked_amount = player_inventory_data.staked_drug_coin.get('staked_amount', 0.0)
    pending_rewards = player_inventory_data.staked_drug_coin.get('pending_rewards', 0.0)
    
    if staked_amount > 0:
        staked_rect = pygame.Rect(col2_x, current_y_col2 - 5, 190, 20)
        pygame.draw.rect(surface, (12, 22, 38), staked_rect)
        draw_text(surface, f"Staked DC: {staked_amount:.4f}", col2_x + 10, current_y_col2, font=FONT_SMALL, color=NEON_BLUE)
        current_y_col2 += line_height
    
    if pending_rewards > 0.00001: # Only show if substantial rewards
        pending_rect = pygame.Rect(col2_x, current_y_col2 - 5, 190, 20)
        pygame.draw.rect(surface, (12, 22, 38), pending_rect)
        draw_text(surface, f"Pending DC Rewards: {pending_rewards:.4f}", col2_x + 10, current_y_col2, font=FONT_SMALL, color=GOLDEN_YELLOW) # Use GOLDEN_YELLOW for pending
        current_y_col2 += line_height
        
    if staked_amount == 0 and pending_rewards == 0: # If no staking activity
        no_staking_rect = pygame.Rect(col2_x, current_y_col2 - 5, 190, 20)
        pygame.draw.rect(surface, (12, 22, 38), no_staking_rect)
        draw_text(surface, "No staking activity", col2_x + 10, current_y_col2, font=FONT_SMALL, color=MEDIUM_GREY)
        current_y_col2 += line_height

    if wallet_empty and staked_amount == 0 and pending_rewards == 0: # If truly nothing in crypto
        no_crypto_rect = pygame.Rect(col1_x, current_y_col1 - 5, 190, 20)
        pygame.draw.rect(surface, (12, 22, 38), no_crypto_rect)
        draw_text(surface, "  None", col1_x + 10, current_y_col1, font=FONT_SMALL, color=MEDIUM_GREY)
        current_y_col1 += line_height


    current_y_col1 += line_height # Add some spacing before next section
    draw_text(surface, f"Ghost Network Access: {player_inventory_data.ghost_network_access} days", col1_x, current_y_col1, font=FONT_MEDIUM, color=TEXT_COLOR)
    current_y_col1 += line_height
    draw_text(surface, f"Secure Phone: {'Yes' if player_inventory_data.has_secure_phone else 'No'}", col1_x, current_y_col1, font=FONT_MEDIUM, color=TEXT_COLOR)

    col2_x = SCREEN_WIDTH // 2 + 20
    current_y_col2 = y_offset
    draw_text(surface, "Live Crypto Prices:", col2_x, current_y_col2, font=FONT_MEDIUM, color=PLATINUM); current_y_col2 += line_height
    if game_state_data.current_crypto_prices:
        for coin, price in game_state_data.current_crypto_prices.items():
             draw_text(surface, f"  {coin.value}: ${price:,.2f}", col2_x + 10, current_y_col2, font=FONT_SMALL, color=NEON_BLUE); current_y_col2 += line_height
    else:
        draw_text(surface, "  Prices unavailable.", col2_x + 10, current_y_col2, font=FONT_SMALL, color=MEDIUM_GREY); current_y_col2 += line_height
    
    return max(current_y_col1, current_y_col2) 

def draw_tech_coin_select_view(
    surface: pygame.Surface, 
    tech_buttons: List[Button],
    ui_state: Dict
    ):
    # Clear background with gradient effect
    surface.fill((5, 15, 30))  # Dark blue background
    
    # Draw main container with border
    main_container = pygame.Rect(20, 20, SCREEN_WIDTH - 40, 728)
    pygame.draw.rect(surface, (15, 25, 45), main_container)
    pygame.draw.rect(surface, YALE_BLUE, main_container, 3)
    
    # Title section with background
    title_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, 60)
    pygame.draw.rect(surface, (10, 20, 40), title_rect)
    pygame.draw.rect(surface, (70, 130, 180), title_rect, 2)
    
    tech_transaction_in_progress = ui_state.get('tech_transaction_in_progress', "N/A")
    action_label = tech_transaction_in_progress.replace("_", " ").title()
    draw_text(surface, action_label, SCREEN_WIDTH // 2, 70, 
              font=FONT_LARGE, color=GOLDEN_YELLOW, center_aligned=True)
    
    # Instruction section
    instruction_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, 50)
    pygame.draw.rect(surface, (8, 18, 35), instruction_rect)
    pygame.draw.rect(surface, YALE_BLUE, instruction_rect, 1)
    
    draw_text(surface, "Choose a cryptocurrency for the transaction:", 
              SCREEN_WIDTH // 2, 145, font=FONT_MEDIUM, color=PLATINUM, center_aligned=True)
    
    mouse_pos = pygame.mouse.get_pos()
    for button in tech_buttons: 
        button.draw(surface, mouse_pos)

def draw_tech_amount_input_view(
    surface: pygame.Surface, 
    player_inventory_data: 'PlayerInventory', 
    game_state_data: 'GameState', 
    tech_buttons: List[Button],
    ui_state: Dict
    ):
    # Clear background with gradient effect
    surface.fill((5, 15, 30))  # Dark blue background
    
    # Draw main container with border
    main_container = pygame.Rect(20, 20, SCREEN_WIDTH - 40, 728)
    pygame.draw.rect(surface, (15, 25, 45), main_container)
    pygame.draw.rect(surface, YALE_BLUE, main_container, 3)
    
    # Title section with background
    title_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, 60)
    pygame.draw.rect(surface, (10, 20, 40), title_rect)
    pygame.draw.rect(surface, (70, 130, 180), title_rect, 2)
    
    tech_input_string = ui_state.get('tech_input_string', "")
    active_prompt_message = ui_state.get('active_prompt_message')
    prompt_message_timer = ui_state.get('prompt_message_timer', 0)
    tech_transaction_in_progress = ui_state.get('tech_transaction_in_progress', "N/A")
    coin_for_tech_transaction = ui_state.get('coin_for_tech_transaction') 
    tech_input_box_rect = ui_state.get('tech_input_box_rect') 

    action_verb = tech_transaction_in_progress.split('_')[0].capitalize()
    coin_name = coin_for_tech_transaction.value.upper() if coin_for_tech_transaction else "Crypto"
    title = f"{action_verb} {coin_name}"
    draw_text(surface, title, SCREEN_WIDTH // 2, 70, 
              font=FONT_LARGE, color=GOLDEN_YELLOW, center_aligned=True)
    
    # Account info section  
    info_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, 100)
    pygame.draw.rect(surface, (8, 18, 35), info_rect)
    pygame.draw.rect(surface, YALE_BLUE, info_rect, 1)
    
    info_y = 140
    draw_text(surface, f"Your Cash: ${player_inventory_data.cash:,.2f}", SCREEN_WIDTH // 2, info_y, 
              font=FONT_SMALL, color=GOLDEN_YELLOW, center_aligned=True)
    info_y += 25
    if coin_for_tech_transaction: 
        balance = player_inventory_data.crypto_wallet.get(coin_for_tech_transaction, 0.0)
        price = game_state_data.current_crypto_prices.get(coin_for_tech_transaction, 0)
        draw_text(surface, f"Your {coin_name}: {balance:.4f} (${balance * price:,.2f})", 
                  SCREEN_WIDTH // 2, info_y, font=FONT_SMALL, color=NEON_BLUE, center_aligned=True)
        info_y += 25
        draw_text(surface, f"Current {coin_name} Price: ${price:,.2f}", SCREEN_WIDTH // 2, info_y, font=FONT_SMALL, color=TEXT_COLOR, center_aligned=True); info_y += 25
    
    prompt_text = "Enter amount..."
    if "launder" in tech_transaction_in_progress: prompt_text = "Enter amount of cash to launder:"
    elif "buy" in tech_transaction_in_progress and coin_for_tech_transaction: prompt_text = f"Enter amount of {coin_name} to buy:"
    elif "sell" in tech_transaction_in_progress and coin_for_tech_transaction: prompt_text = f"Enter amount of {coin_name} to sell:"
    elif "stake" in tech_transaction_in_progress and coin_for_tech_transaction: prompt_text = f"Enter amount of {coin_name} to stake:"
    elif "unstake" in tech_transaction_in_progress and coin_for_tech_transaction: prompt_text = f"Enter amount of {coin_name} to unstake:"
    draw_text(surface, prompt_text, SCREEN_WIDTH // 2, info_y, font=FONT_SMALL, color=PLATINUM, center_aligned=True, max_width=SCREEN_WIDTH-40); info_y += 40

    if tech_input_box_rect:
        current_input_box_rect = pygame.Rect(tech_input_box_rect) 
        current_input_box_rect.top = info_y
        draw_input_box(surface, current_input_box_rect, tech_input_string, FONT_MEDIUM, 
                       TEXT_INPUT_TEXT_COLOR, TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR, 
                       is_active=True, cursor_visible=True, cursor_pos=len(tech_input_string))
        info_y += 60
    
    if active_prompt_message and prompt_message_timer > 0:
        prompt_color = IMPERIAL_RED if "Error" in active_prompt_message or "Invalid" in active_prompt_message or "Not enough" in active_prompt_message else EMERALD_GREEN
        draw_text(surface, active_prompt_message, SCREEN_WIDTH // 2, info_y, font=FONT_SMALL, color=prompt_color, center_aligned=True, max_width=SCREEN_WIDTH - 40)
        
    mouse_pos = pygame.mouse.get_pos()
    for button in tech_buttons: 
        button.draw(surface, mouse_pos)

def draw_tech_contact_view(
    surface: pygame.Surface, 
    player_inventory_data: 'PlayerInventory', 
    game_state_data: 'GameState', 
    game_configs_data: 'GameConfigs', 
    tech_buttons: List[Button], 
    ui_state: Dict 
    ):
    
    current_tech_view_state = ui_state.get('current_view', "tech_contact") 

    if current_tech_view_state == "tech_input_coin_select":
        draw_tech_coin_select_view(surface, tech_buttons, ui_state)
    elif current_tech_view_state == "tech_input_amount":
        draw_tech_amount_input_view(surface, player_inventory_data, game_state_data, tech_buttons, ui_state)
    else:
        # Clear background with gradient effect
        surface.fill((5, 15, 30))  # Dark blue background
        
        # Draw main container with border
        main_container = pygame.Rect(20, 20, SCREEN_WIDTH - 40, 728)
        pygame.draw.rect(surface, (15, 25, 45), main_container)
        pygame.draw.rect(surface, YALE_BLUE, main_container, 3)
        
        # Title section with background
        title_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, 60)
        pygame.draw.rect(surface, (10, 20, 40), title_rect)
        pygame.draw.rect(surface, (70, 130, 180), title_rect, 2)
        
        draw_text(surface, "TECH CONTACT", SCREEN_WIDTH // 2, 70, 
                  font=FONT_LARGE, color=GOLDEN_YELLOW, center_aligned=True)
        
        _draw_tech_shared_info(surface, player_inventory_data, game_state_data)
        
        active_prompt_message = ui_state.get('active_prompt_message')
        prompt_message_timer = ui_state.get('prompt_message_timer', 0)
        if active_prompt_message and prompt_message_timer > 0:
            # Message container
            msg_rect = pygame.Rect(40, SCREEN_HEIGHT - 140, SCREEN_WIDTH - 80, 60)
            msg_color = (40, 20, 20) if "Error" in active_prompt_message else (20, 40, 20)
            pygame.draw.rect(surface, msg_color, msg_rect)
            border_color = IMPERIAL_RED if "Error" in active_prompt_message else EMERALD_GREEN
            pygame.draw.rect(surface, border_color, msg_rect, 2)
            
            prompt_color = IMPERIAL_RED if "Error" in active_prompt_message else EMERALD_GREEN
            draw_text(surface, active_prompt_message, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 110, 
                      font=FONT_SMALL, color=prompt_color, center_aligned=True, max_width=SCREEN_WIDTH - 40)
        
        mouse_pos = pygame.mouse.get_pos()
        for button in tech_buttons: 
            button.draw(surface, mouse_pos)
