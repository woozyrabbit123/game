# views/inventory_view.py
"""
Handles drawing the Inventory view using shared UI elements.
"""
from typing import List, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ...core.player_inventory import PlayerInventory

from ...core.enums import CryptoCoin, SkillID # Added SkillID for pretty printing
from ..ui_components import Button
from ..ui_theme import (
    FONT_MEDIUM, FONT_MEDIUM_BOLD, FONT_SMALL, FONT_XSMALL,
    GOLDEN_YELLOW, LIGHT_GREY, MEDIUM_GREY, NEON_BLUE, PLATINUM, TEXT_COLOR, YALE_BLUE,
    draw_text, # Keep for specific item rendering
)
from ..ui_base_elements import (
    draw_view_background,
    draw_main_container,
    draw_view_title,
    draw_content_panel, # Main panel for all 3 columns
    # draw_panel_header, # Can be used for individual column headers
)
from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT

# Layout constants
TITLE_Y = 40
CONTENT_PANEL_Y = 120
CONTENT_PANEL_HEIGHT = 580 # Original content_rect height
COLUMN_HEADER_Y = CONTENT_PANEL_Y + 10 # Y for the rect behind column headers
COLUMN_HEADER_TEXT_Y = COLUMN_HEADER_Y + 15 # Y for the text of column headers
COLUMN_CONTENT_START_Y = COLUMN_HEADER_TEXT_Y + 25 # Y for items within columns

# Column X positions (absolute, as in original)
COL1_X_START = 70
COL2_X_START = SCREEN_WIDTH // 2 - 80
COL3_X_START = SCREEN_WIDTH // 2 + 170

# Column widths (approximate, for drawing header rects)
COL1_WIDTH = 300
COL2_WIDTH = 280
COL3_WIDTH = 280


def _draw_column_header_panel(surface: pygame.Surface, text: str, x: int, y: int, width: int):
    """Helper to draw a single column header with its background."""
    header_rect = pygame.Rect(x - 10, y -10 , width, 30) # x-10 to match original header rects starting at 60, 380, 680
    pygame.draw.rect(surface, (25, 35, 55), header_rect) # bg_color from original
    pygame.draw.rect(surface, YALE_BLUE, header_rect, 1) # border
    draw_text(surface, text, header_rect.centerx, header_rect.centery,
              font=FONT_MEDIUM, color=PLATINUM, center_aligned=True)


def draw_inventory_view(
    surface: pygame.Surface,
    player_inventory_data: "PlayerInventory",
    inventory_buttons: List[Button], # Typically just the "Back" button
):
    draw_view_background(surface)
    # Inventory view also had main container height of 728.
    # SCREEN_HEIGHT (768) - 728 = 40. So height_offset=40 is correct.
    draw_main_container(surface, height_offset=40)

    # Using the same specific border color for the title as in skills/upgrades view
    draw_view_title(surface, "INVENTORY", border_color=(70, 130, 180))

    # Main content panel that will visually enclose all three columns
    # Original content_rect: Rect(40, 120, SCREEN_WIDTH - 80, 580)
    content_panel = draw_content_panel(surface, CONTENT_PANEL_Y, CONTENT_PANEL_HEIGHT)

    # Column Headers
    _draw_column_header_panel(surface, "CASH & DRUGS", COL1_X_START, COLUMN_HEADER_TEXT_Y, COL1_WIDTH)
    _draw_column_header_panel(surface, "CRYPTO WALLET", COL2_X_START, COLUMN_HEADER_TEXT_Y, COL2_WIDTH)
    _draw_column_header_panel(surface, "SKILLS & UPGRADES", COL3_X_START, COLUMN_HEADER_TEXT_Y, COL3_WIDTH)


    # --- Column 1: Cash & Drugs ---
    y_offset_col1 = COLUMN_CONTENT_START_Y
    line_height = FONT_SMALL.get_linesize() + 4 # Increased spacing slightly

    draw_text(surface, f"Cash: ${player_inventory_data.cash:,.2f}",
              COL1_X_START, y_offset_col1, font=FONT_MEDIUM_BOLD, color=GOLDEN_YELLOW)
    y_offset_col1 += line_height * 1.2

    if not player_inventory_data.items:
        pygame.draw.rect(surface, (20, 30, 50), (COL1_X_START - 10, y_offset_col1 - 5, COL1_WIDTH -20 , 25)) # BG for no drugs
        draw_text(surface, "No drugs in inventory.", COL1_X_START, y_offset_col1, font=FONT_SMALL, color=MEDIUM_GREY)
        y_offset_col1 += line_height
    else:
        item_count = 0
        for drug_name, qualities in sorted(player_inventory_data.items.items(), key=lambda item: item[0].value):
            for quality, quantity in sorted(qualities.items(), key=lambda item: item[0].value):
                if y_offset_col1 > content_panel.bottom - line_height: break
                if item_count % 2 == 0: # Alternating row background
                    pygame.draw.rect(surface, (12, 22, 38), (COL1_X_START - 10, y_offset_col1 - 5, COL1_WIDTH-20, 20))
                name_str = drug_name.value
                quality_str = quality.name.capitalize()
                draw_text(surface, f"{name_str} ({quality_str}): {quantity}",
                          COL1_X_START, y_offset_col1, font=FONT_SMALL, color=TEXT_COLOR)
                y_offset_col1 += line_height
                item_count += 1
            if y_offset_col1 > content_panel.bottom - line_height: break


    # --- Column 2: Crypto Wallet ---
    y_offset_col2 = COLUMN_CONTENT_START_Y
    if not player_inventory_data.crypto_wallet:
        pygame.draw.rect(surface, (20, 30, 50), (COL2_X_START, y_offset_col2 - 5, COL2_WIDTH - 20, 25)) # BG
        draw_text(surface, "No crypto assets.", COL2_X_START + 10, y_offset_col2, font=FONT_SMALL, color=MEDIUM_GREY)
        y_offset_col2 += line_height
    else:
        for i, (coin, balance) in enumerate(player_inventory_data.crypto_wallet.items()):
            if y_offset_col2 > content_panel.bottom - line_height: break
            if i % 2 == 0: # Alternating row
                 pygame.draw.rect(surface, (12, 22, 38), (COL2_X_START, y_offset_col2 - 5, COL2_WIDTH - 20, 20))
            draw_text(surface, f"{coin.value}: {balance:.4f}",
                      COL2_X_START + 10, y_offset_col2, font=FONT_SMALL, color=NEON_BLUE)
            y_offset_col2 += line_height

            if coin == CryptoCoin.DRUG_COIN: # Display staking info for DrugCoin
                staked = player_inventory_data.staked_drug_coin.get("staked_amount", 0)
                pending = player_inventory_data.staked_drug_coin.get("pending_rewards", 0)
                if staked > 0 or pending > 0:
                    if y_offset_col2 > content_panel.bottom - (line_height * 0.8 * 2): break # Check space for 2 more lines
                    pygame.draw.rect(surface, (8, 15, 25), (COL2_X_START + 10, y_offset_col2 - 5, COL2_WIDTH - 40, 15))
                    draw_text(surface, f"  Staked: {staked:.4f}", COL2_X_START + 20, y_offset_col2, font=FONT_XSMALL, color=LIGHT_GREY)
                    y_offset_col2 += int(line_height * 0.8)
                    pygame.draw.rect(surface, (8, 15, 25), (COL2_X_START + 10, y_offset_col2 - 5, COL2_WIDTH - 40, 15))
                    draw_text(surface, f"  Pending: {pending:.4f}", COL2_X_START + 20, y_offset_col2, font=FONT_XSMALL, color=LIGHT_GREY)
                    y_offset_col2 += int(line_height * 0.8)
            if y_offset_col2 > content_panel.bottom - line_height: break


    # --- Column 3: Skills & Upgrades ---
    y_offset_col3 = COLUMN_CONTENT_START_Y
    pygame.draw.rect(surface, (20, 30, 50), (COL3_X_START, y_offset_col3 - 5, COL3_WIDTH -20, 25)) # Section BG
    draw_text(surface, f"Skill Points: {player_inventory_data.skill_points}",
              COL3_X_START + 10, y_offset_col3, font=FONT_MEDIUM_BOLD, color=GOLDEN_YELLOW)
    y_offset_col3 += line_height * 1.2

    # Unlocked Skills
    if y_offset_col3 < content_panel.bottom - line_height:
        pygame.draw.rect(surface, (15, 25, 40), (COL3_X_START, y_offset_col3 - 5, COL3_WIDTH -20, 20)) # Sub-header BG
        draw_text(surface, "Unlocked Skills:", COL3_X_START + 10, y_offset_col3, font=FONT_SMALL, color=PLATINUM)
        y_offset_col3 += line_height

        if player_inventory_data.unlocked_skills:
            for i, skill_id_enum in enumerate(player_inventory_data.unlocked_skills):
                if y_offset_col3 > content_panel.bottom - (line_height * 0.8): break
                if i % 2 == 0: # Alternating row
                    pygame.draw.rect(surface, (12, 22, 38), (COL3_X_START + 10, y_offset_col3 - 5, COL3_WIDTH - 40, 18))
                skill_name = skill_id_enum.value.replace('_', ' ').title() if isinstance(skill_id_enum, SkillID) else str(skill_id_enum).replace('_', ' ').title()
                draw_text(surface, f"  - {skill_name}", COL3_X_START + 20, y_offset_col3, font=FONT_XSMALL, color=LIGHT_GREY)
                y_offset_col3 += int(line_height * 0.8)
        else:
            if y_offset_col3 < content_panel.bottom - (line_height * 0.8):
                pygame.draw.rect(surface, (12, 22, 38), (COL3_X_START + 10, y_offset_col3 - 5, COL3_WIDTH - 40, 18))
                draw_text(surface, "  No skills unlocked.", COL3_X_START + 20, y_offset_col3, font=FONT_XSMALL, color=MEDIUM_GREY)
                y_offset_col3 += int(line_height * 0.8)

    # Purchased Upgrades
    y_offset_col3 += int(line_height * 0.5) # Space before next section
    if y_offset_col3 < content_panel.bottom - line_height:
        pygame.draw.rect(surface, (15, 25, 40), (COL3_X_START, y_offset_col3 - 5, COL3_WIDTH -20, 20)) # Sub-header BG
        draw_text(surface, "Purchased Upgrades:", COL3_X_START + 10, y_offset_col3, font=FONT_SMALL, color=PLATINUM)
        y_offset_col3 += line_height
        
        has_any_upgrade = False
        upgrade_item_count = 0
        
        def _add_upgrade_line(text, y_offset, count):
            if y_offset > content_panel.bottom - (line_height * 0.8): return y_offset, count, False # No space
            if count % 2 == 0: # Alternating row
                 pygame.draw.rect(surface, (12, 22, 38), (COL3_X_START + 10, y_offset - 5, COL3_WIDTH - 40, 18))
            draw_text(surface, f"  - {text}", COL3_X_START + 20, y_offset, font=FONT_XSMALL, color=LIGHT_GREY)
            return y_offset + int(line_height * 0.8), count + 1, True

        if player_inventory_data.max_capacity > getattr(player_inventory_data, "BASE_MAX_CAPACITY", 50) :
            y_offset_col3, upgrade_item_count, drawn = _add_upgrade_line(f"Expanded Capacity ({player_inventory_data.max_capacity})", y_offset_col3, upgrade_item_count)
            if drawn: has_any_upgrade = True
        if player_inventory_data.has_secure_phone and (y_offset_col3 < content_panel.bottom - (line_height * 0.8)):
            y_offset_col3, upgrade_item_count, drawn = _add_upgrade_line("Secure Comms Phone", y_offset_col3, upgrade_item_count)
            if drawn: has_any_upgrade = True
        if player_inventory_data.ghost_network_access > 0 and (y_offset_col3 < content_panel.bottom - (line_height * 0.8)):
            y_offset_col3, upgrade_item_count, drawn = _add_upgrade_line(f"Ghost Network ({player_inventory_data.ghost_network_access} days)", y_offset_col3, upgrade_item_count)
            if drawn: has_any_upgrade = True

        if not has_any_upgrade and (y_offset_col3 < content_panel.bottom - (line_height * 0.8)):
            pygame.draw.rect(surface, (12, 22, 38), (COL3_X_START + 10, y_offset_col3 - 5, COL3_WIDTH - 40, 18))
            draw_text(surface, "  No upgrades purchased.", COL3_X_START + 20, y_offset_col3, font=FONT_XSMALL, color=MEDIUM_GREY)
            y_offset_col3 += int(line_height * 0.8)


    mouse_pos = pygame.mouse.get_pos()
    for button in inventory_buttons:
        button.draw(surface, mouse_pos)

[end of src/ui_pygame/views/inventory_view.py]
