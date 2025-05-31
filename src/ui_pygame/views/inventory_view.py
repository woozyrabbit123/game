# views/inventory_view.py
"""
Handles drawing the Inventory view.
"""
import pygame
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.player_inventory import PlayerInventory
    # from game_state import GameState # If specific parts of game_state are needed beyond what's passed

from ...core.enums import CryptoCoin # Assuming this is used for crypto display

from ..ui_theme import (
    FONT_LARGE, FONT_MEDIUM, FONT_MEDIUM_BOLD, FONT_SMALL, FONT_XSMALL,
    YALE_BLUE, PLATINUM, GOLDEN_YELLOW, TEXT_COLOR, NEON_BLUE, MEDIUM_GREY, LIGHT_GREY,
    draw_text
)
from ..ui_components import Button

SCREEN_WIDTH = 1024 # Consider moving to shared constants

def draw_inventory_view(
    surface: pygame.Surface, 
    player_inventory_data: 'PlayerInventory', 
    inventory_buttons: List[Button]
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
    
    draw_text(surface, "INVENTORY", SCREEN_WIDTH // 2, 70, 
              font=FONT_LARGE, color=GOLDEN_YELLOW, center_aligned=True)
    
    # Main content container
    content_rect = pygame.Rect(40, 120, SCREEN_WIDTH - 80, 580)
    pygame.draw.rect(surface, (8, 18, 35), content_rect)
    pygame.draw.rect(surface, YALE_BLUE, content_rect, 1)
    
    col1_x, col2_x, col3_x = 70, SCREEN_WIDTH // 2 - 80, SCREEN_WIDTH // 2 + 170
    y_start = 140
    y_offset = y_start
    line_height = 25

    # Column 1 Header
    header1_rect = pygame.Rect(60, 130, 300, 30)
    pygame.draw.rect(surface, (25, 35, 55), header1_rect)
    pygame.draw.rect(surface, YALE_BLUE, header1_rect, 1)
    draw_text(surface, "CASH & DRUGS", col1_x + 100, 145, font=FONT_MEDIUM, color=PLATINUM, center_aligned=True)    # Column 2 Header  
    header2_rect = pygame.Rect(380, 130, 280, 30)
    pygame.draw.rect(surface, (25, 35, 55), header2_rect)
    pygame.draw.rect(surface, YALE_BLUE, header2_rect, 1)
    draw_text(surface, "CRYPTO WALLET", col2_x + 90, 145, font=FONT_MEDIUM, color=PLATINUM, center_aligned=True)
    
    # Column 3 Header
    header3_rect = pygame.Rect(680, 130, 280, 30)
    pygame.draw.rect(surface, (25, 35, 55), header3_rect)
    pygame.draw.rect(surface, YALE_BLUE, header3_rect, 1)
    draw_text(surface, "SKILLS & UPGRADES", col3_x + 90, 145, font=FONT_MEDIUM, color=PLATINUM, center_aligned=True)

    # Column 1: Cash & Drugs with improved styling
    y_offset += 30
    draw_text(surface, f"Cash: ${player_inventory_data.cash:,.2f}", col1_x, y_offset, font=FONT_MEDIUM_BOLD, color=GOLDEN_YELLOW)
    y_offset += line_height * 1.2
    if not player_inventory_data.items:
        no_drugs_rect = pygame.Rect(col1_x - 10, y_offset - 5, 280, 25)
        pygame.draw.rect(surface, (20, 30, 50), no_drugs_rect)
        draw_text(surface, "No drugs in inventory.", col1_x, y_offset, font=FONT_SMALL, color=MEDIUM_GREY)
        y_offset += line_height
    else:
        item_count = 0
        for drug_name, qualities in player_inventory_data.items.items():
            for quality, quantity in qualities.items():
                if item_count % 2 == 0:
                    row_rect = pygame.Rect(col1_x - 10, y_offset - 5, 280, 20)
                    pygame.draw.rect(surface, (12, 22, 38), row_rect)
                name_str = drug_name.value
                quality_str = quality.name.capitalize()
                draw_text(surface, f"{name_str} ({quality_str}): {quantity}", col1_x, y_offset, font=FONT_SMALL, color=TEXT_COLOR)
                y_offset += line_height
                item_count += 1

    # Column 2: Crypto Wallet with improved styling
    y_offset = y_start + 30 # Reset Y for second column
    if not player_inventory_data.crypto_wallet:
        no_crypto_rect = pygame.Rect(col2_x, y_offset - 5, 250, 25)
        pygame.draw.rect(surface, (20, 30, 50), no_crypto_rect)
        draw_text(surface, "No crypto assets.", col2_x + 10, y_offset, font=FONT_SMALL, color=MEDIUM_GREY)
        y_offset += line_height
    else:
        for i, (coin, balance) in enumerate(player_inventory_data.crypto_wallet.items()): # coin is CryptoCoin enum
            # Alternating row backgrounds for crypto
            if i % 2 == 0:
                crypto_row_rect = pygame.Rect(col2_x, y_offset - 5, 250, 20)
                pygame.draw.rect(surface, (12, 22, 38), crypto_row_rect)
            
            draw_text(surface, f"{coin.value}: {balance:.4f}", col2_x + 10, y_offset, font=FONT_SMALL, color=NEON_BLUE)
            y_offset += line_height
            if coin == CryptoCoin.DRUG_COIN: 
                staked = player_inventory_data.staked_drug_coin.get('staked_amount', 0)
                pending = player_inventory_data.staked_drug_coin.get('pending_rewards', 0)
                if staked > 0 or pending > 0:
                    staked_rect = pygame.Rect(col2_x + 10, y_offset - 5, 230, 15)
                    pygame.draw.rect(surface, (8, 15, 25), staked_rect)
                    draw_text(surface, f"  Staked: {staked:.4f}", col2_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY)
                    y_offset += line_height * 0.8
                    pending_rect = pygame.Rect(col2_x + 10, y_offset - 5, 230, 15)
                    pygame.draw.rect(surface, (8, 15, 25), pending_rect)
                    draw_text(surface, f"  Pending: {pending:.4f}", col2_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY)
                    y_offset += line_height * 0.8 # Adjusted to ensure next item is not overlapping
    y_offset += line_height * 0.5 # Extra space if crypto items were listed

    # Column 3: Skills & Upgrades Summary with improved styling
    y_offset = y_start + 30 # Reset Y for third column
    
    # Skills section
    skills_header_rect = pygame.Rect(col3_x, y_offset - 5, 250, 25)
    pygame.draw.rect(surface, (20, 30, 50), skills_header_rect)
    draw_text(surface, f"Skill Points: {player_inventory_data.skill_points}", col3_x + 10, y_offset, font=FONT_MEDIUM_BOLD, color=GOLDEN_YELLOW)
    y_offset += line_height * 1.2
    
    if player_inventory_data.unlocked_skills:
        unlocked_label_rect = pygame.Rect(col3_x, y_offset - 5, 250, 20)
        pygame.draw.rect(surface, (15, 25, 40), unlocked_label_rect)
        draw_text(surface, "Unlocked Skills:", col3_x + 10, y_offset, font=FONT_SMALL, color=PLATINUM)
        y_offset += line_height
        for i, skill_id in enumerate(player_inventory_data.unlocked_skills): # skill_id is str
            if i % 2 == 0:
                skill_row_rect = pygame.Rect(col3_x + 10, y_offset - 5, 230, 18)
                pygame.draw.rect(surface, (12, 22, 38), skill_row_rect)
            draw_text(surface, f"  - {skill_id.value.replace('_', ' ').title()}", col3_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY) # Prettify skill name
            y_offset += int(line_height * 0.8)
    else:
        no_skills_rect = pygame.Rect(col3_x, y_offset - 5, 250, 20)
        pygame.draw.rect(surface, (15, 25, 40), no_skills_rect)
        draw_text(surface, "No skills unlocked.", col3_x + 10, y_offset, font=FONT_XSMALL, color=MEDIUM_GREY)
        y_offset += int(line_height * 0.8)
    
    y_offset += int(line_height * 0.5) # Extra space
    upgrades_label_rect = pygame.Rect(col3_x, y_offset - 5, 250, 20)
    pygame.draw.rect(surface, (15, 25, 40), upgrades_label_rect)
    draw_text(surface, "Purchased Upgrades:", col3_x + 10, y_offset, font=FONT_SMALL, color=PLATINUM)
    y_offset += line_height
    has_upgrades = False
    upgrade_count = 0
    if player_inventory_data.max_capacity > getattr(player_inventory_data, 'BASE_MAX_CAPACITY', 50): # Check if capacity upgraded
        if upgrade_count % 2 == 0:
            upgrade_row_rect = pygame.Rect(col3_x + 10, y_offset - 5, 230, 18)
            pygame.draw.rect(surface, (12, 22, 38), upgrade_row_rect)
        draw_text(surface, f"  - Expanded Capacity ({player_inventory_data.max_capacity})", col3_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY)
        y_offset += int(line_height *0.8)
        has_upgrades = True
        upgrade_count += 1
    if player_inventory_data.has_secure_phone:
        if upgrade_count % 2 == 0:
            upgrade_row_rect = pygame.Rect(col3_x + 10, y_offset - 5, 230, 18)
            pygame.draw.rect(surface, (12, 22, 38), upgrade_row_rect)
        draw_text(surface, "  - Secure Comms Phone", col3_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY)
        y_offset += int(line_height *0.8)
        has_upgrades = True
        upgrade_count += 1
    if player_inventory_data.ghost_network_access > 0:
        if upgrade_count % 2 == 0:
            upgrade_row_rect = pygame.Rect(col3_x + 10, y_offset - 5, 230, 18)
            pygame.draw.rect(surface, (12, 22, 38), upgrade_row_rect)
        draw_text(surface, f"  - Ghost Network ({player_inventory_data.ghost_network_access} days)", col3_x + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY)
        y_offset += int(line_height *0.8)
        has_upgrades = True
        upgrade_count += 1
    if not has_upgrades:
        no_upgrades_rect = pygame.Rect(col3_x + 10, y_offset - 5, 230, 18)
        pygame.draw.rect(surface, (12, 22, 38), no_upgrades_rect)
        draw_text(surface, "No upgrades purchased.", col3_x + 20, y_offset, font=FONT_XSMALL, color=MEDIUM_GREY)
        y_offset += int(line_height *0.8)

    mouse_pos = pygame.mouse.get_pos()
    for button in inventory_buttons: # Back button
        button.draw(surface, mouse_pos)
