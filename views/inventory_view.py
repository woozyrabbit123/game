# views/inventory_view.py
"""
Handles drawing the Inventory view.
"""
import pygame
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.player_inventory import PlayerInventory
    # from game_state import GameState # If specific parts of game_state are needed beyond what's passed

from core.enums import CryptoCoin # Assuming this is used for crypto display

from ui_theme import (
    FONT_LARGE, FONT_MEDIUM, FONT_MEDIUM_BOLD, FONT_SMALL, FONT_XSMALL,
    YALE_BLUE, PLATINUM, GOLDEN_YELLOW, TEXT_COLOR, NEON_BLUE, MEDIUM_GREY, LIGHT_GREY,
    draw_text
)
from ui_components import Button

SCREEN_WIDTH = 1024 # Consider moving to shared constants

def draw_inventory_view(
    surface: pygame.Surface, 
    player_inventory_data: 'PlayerInventory', 
    # game_state_data: any, # Not directly used by this drawing function
    inventory_buttons: List[Button] # For the "Back" button
    ):
    draw_text(surface, "Inventory", SCREEN_WIDTH // 2, 30, font=FONT_LARGE, color=YALE_BLUE, center_aligned=True)
    
    col1_x, col2_x, col3_x = 50, SCREEN_WIDTH // 2 - 100, SCREEN_WIDTH // 2 + 150
    y_start = 80
    y_offset = y_start
    line_height = 25

    # Column 1: Cash & Drugs
    draw_text(surface, f"Cash: ${player_inventory_data.cash:,.2f}", col1_x, y_offset, font=FONT_MEDIUM_BOLD, color=GOLDEN_YELLOW)
    y_offset += line_height * 1.5
    draw_text(surface, "Drugs on Hand:", col1_x, y_offset, font=FONT_MEDIUM, color=PLATINUM)
    y_offset += line_height
    if not player_inventory_data.drugs:
        draw_text(surface, "No drugs in inventory.", col1_x + 10, y_offset, font=FONT_SMALL, color=MEDIUM_GREY)
        y_offset += line_height
    else:
        for drug_inv_item in player_inventory_data.drugs:
            name_str = drug_inv_item.drug_name.value
            quality_str = drug_inv_item.quality.name.capitalize()
            draw_text(surface, f"{name_str} ({quality_str}): {drug_inv_item.quantity}", col1_x + 10, y_offset, font=FONT_SMALL, color=TEXT_COLOR)
            y_offset += line_height

    # Column 2: Crypto Wallet
    y_offset = y_start # Reset Y for second column
    draw_text(surface, "Crypto Wallet:", col2_x, y_offset, font=FONT_MEDIUM, color=PLATINUM)
    y_offset += line_height
    if not player_inventory_data.crypto_wallet:
        draw_text(surface, "No crypto assets.", col2_x + 10, y_offset, font=FONT_SMALL, color=MEDIUM_GREY)
        y_offset += line_height
    else:
        for coin, balance in player_inventory_data.crypto_wallet.items(): # coin is CryptoCoin enum
            draw_text(surface, f"{coin.value}: {balance:.4f}", col2_x + 10, y_offset, font=FONT_SMALL, color=NEON_BLUE)
            y_offset += line_height
            if coin == CryptoCoin.DRUG_COIN: 
                staked = player_inventory_data.staked_drug_coin.get('staked_amount', 0)
                pending = player_inventory_data.staked_drug_coin.get('pending_rewards', 0)
                if staked > 0 or pending > 0:
                    draw_text(surface, f"  Staked: {staked:.4f}", col2_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY)
                    y_offset += line_height * 0.8
                    draw_text(surface, f"  Pending: {pending:.4f}", col2_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY)
                    y_offset += line_height * 0.8 # Adjusted to ensure next item is not overlapping
    y_offset += line_height * 0.5 # Extra space if crypto items were listed

    # Column 3: Skills & Upgrades Summary
    y_offset = y_start # Reset Y for third column
    draw_text(surface, "Skills & Upgrades:", col3_x, y_offset, font=FONT_MEDIUM, color=PLATINUM)
    y_offset += line_height
    draw_text(surface, f"Skill Points: {player_inventory_data.skill_points}", col3_x + 10, y_offset, font=FONT_SMALL, color=TEXT_COLOR)
    y_offset += line_height
    if player_inventory_data.unlocked_skills:
        draw_text(surface, "Unlocked Skills:", col3_x + 10, y_offset, font=FONT_SMALL, color=TEXT_COLOR)
        y_offset += line_height
        for skill_id in player_inventory_data.unlocked_skills: # skill_id is str
            draw_text(surface, f"  - {skill_id.replace('_', ' ').title()}", col3_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY) # Prettify skill name
            y_offset += int(line_height * 0.8)
    else:
        draw_text(surface, "No skills unlocked.", col3_x + 10, y_offset, font=FONT_XSMALL, color=MEDIUM_GREY)
        y_offset += int(line_height * 0.8)
    
    y_offset += int(line_height * 0.5) # Extra space
    draw_text(surface, "Purchased Upgrades:", col3_x + 10, y_offset, font=FONT_SMALL, color=TEXT_COLOR)
    y_offset += line_height
    has_upgrades = False
    if player_inventory_data.max_capacity > getattr(player_inventory_data, 'BASE_MAX_CAPACITY', 50): # Check if capacity upgraded
         draw_text(surface, f"  - Expanded Capacity ({player_inventory_data.max_capacity})", col3_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY); y_offset += int(line_height *0.8); has_upgrades=True
    if player_inventory_data.has_secure_phone:
         draw_text(surface, "  - Secure Comms Phone", col3_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY); y_offset += int(line_height *0.8); has_upgrades=True
    if player_inventory_data.ghost_network_access > 0:
         draw_text(surface, f"  - Ghost Network ({player_inventory_data.ghost_network_access} days)", col3_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY); y_offset += int(line_height *0.8); has_upgrades=True
    if not has_upgrades:
        draw_text(surface, "No upgrades purchased.", col3_x + 20, y_offset, font=FONT_XSMALL, color=MEDIUM_GREY); y_offset += int(line_height *0.8)

    mouse_pos = pygame.mouse.get_pos()
    for button in inventory_buttons: # Back button
        button.draw(surface, mouse_pos)
