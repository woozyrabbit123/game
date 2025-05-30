import pygame
import sys
from core.enums import DrugName, DrugQuality, RegionName # Added RegionName

# --- Constants ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
LIGHT_GREY = (200, 200, 200)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Project Narco-Syndicate")
clock = pygame.time.Clock()
font_small = pygame.font.Font(None, 24) # For smaller text
font_medium = pygame.font.Font(None, 32) # For general text
font_large = pygame.font.Font(None, 48) # For titles

# --- Game State ---
current_view = "main_menu" # Start with the main menu
main_menu_buttons = []
market_view_buttons = [] 
inventory_view_buttons = [] # Added
travel_view_buttons = []    # Added
tech_contact_view_buttons = [] # Added

# --- Button Class ---
class Button:
    def __init__(self, x, y, width, height, text='', color=LIGHT_GREY, hover_color=GREY, text_color=BLACK, action=None, font=font_medium):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.action = action
        self.font = font
        self.is_hovered = False

    def draw(self, surface):
        draw_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, draw_color, self.rect)
        if self.text != '':
            draw_text(self.text, self.font, self.text_color, surface, self.rect.centerx, self.rect.centery, center_aligned=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                if self.action:
                    self.action() # Execute the button's action
                return True # Indicates a click was handled
        return False

# --- UI Element Drawing Functions ---

def draw_text(text, font, color, surface, x, y, center_aligned=False):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    if center_aligned:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def _calculate_trend_icon(current_price, previous_price):
    """Helper to determine trend icon."""
    if current_price is not None and previous_price is not None and current_price > 0 and previous_price > 0:
        if current_price > previous_price * 1.02:
            return "↑", GREEN
        elif current_price < previous_price * 0.98:
            return "↓", RED
        else:
            return "=", WHITE
    return "-", GREY

def draw_main_menu(surface):
    """Draws the main menu."""
    draw_text("Main Menu", font_large, WHITE, surface, SCREEN_WIDTH // 2, 50, center_aligned=True)
    for button in main_menu_buttons:
        button.draw(surface)

def draw_market_view(surface, market_region_data, player_inventory_data, game_state_data):
    """Draws the market view with actual data."""
    region_name = market_region_data.name.value if market_region_data and market_region_data.name else "Unknown Region"
    draw_text(f"Market: {region_name}", font_large, WHITE, surface, SCREEN_WIDTH // 2, 30, center_aligned=True)

    # Column Headers
    header_y = 80
    col_xs = {"drug": 50, "buy": 350, "sell": 480, "stock": 610, "trend": 720}
    
    draw_text("Drug (Quality)", font_medium, LIGHT_GREY, surface, col_xs["drug"], header_y)
    draw_text("Buy", font_medium, LIGHT_GREY, surface, col_xs["buy"], header_y)
    draw_text("Sell", font_medium, LIGHT_GREY, surface, col_xs["sell"], header_y)
    draw_text("Stock", font_medium, LIGHT_GREY, surface, col_xs["stock"], header_y)
    draw_text("Trend", font_medium, LIGHT_GREY, surface, col_xs["trend"], header_y)

    y_offset = header_y + 40
    line_height = 30

    if not market_region_data or not market_region_data.drug_market_data:
        draw_text("No drugs traded in this market currently.", font_medium, WHITE, surface, SCREEN_WIDTH // 2, y_offset + 20, center_aligned=True)
    else:
        show_trend_icons = "MARKET_INTUITION" in player_inventory_data.unlocked_skills
        
        sorted_drug_names = sorted(market_region_data.drug_market_data.keys(), key=lambda d: d.value)

        for drug_name_enum in sorted_drug_names:
            drug_data_dict = market_region_data.drug_market_data[drug_name_enum]
            qualities_available = drug_data_dict.get("available_qualities", {})
            
            if not qualities_available:
                drug_display_name = drug_name_enum.value
                draw_text(f"{drug_display_name} (None listed)", font_small, WHITE, surface, col_xs["drug"], y_offset)
                draw_text("---", font_small, GREY, surface, col_xs["buy"], y_offset)
                draw_text("---", font_small, GREY, surface, col_xs["sell"], y_offset)
                draw_text("---", font_small, GREY, surface, col_xs["stock"], y_offset)
                if show_trend_icons:
                    draw_text("-", font_small, GREY, surface, col_xs["trend"], y_offset)
                y_offset += line_height
                continue

            sorted_qualities = sorted(qualities_available.keys(), key=lambda q: q.value)

            for quality_enum in sorted_qualities:
                quality_market_data = qualities_available[quality_enum]
                
                drug_display_name = drug_name_enum.value
                quality_display_name = quality_enum.name.capitalize()

                buy_price = market_region_data.get_buy_price(drug_name_enum, quality_enum)
                sell_price = market_region_data.get_sell_price(drug_name_enum, quality_enum)
                stock = market_region_data.get_available_stock(drug_name_enum, quality_enum)
                
                buy_price_str = f"${buy_price:.2f}" if buy_price > 0 else "---"
                sell_price_str = f"${sell_price:.2f}" if sell_price > 0 else "---"
                stock_str = str(stock) if stock > 0 else "0"

                draw_text(f"{drug_display_name} ({quality_display_name})", font_small, WHITE, surface, col_xs["drug"], y_offset)
                draw_text(buy_price_str, font_small, GREEN if buy_price > 0 else GREY, surface, col_xs["buy"], y_offset)
                draw_text(sell_price_str, font_small, GREEN if sell_price > 0 else GREY, surface, col_xs["sell"], y_offset)
                draw_text(stock_str, font_small, WHITE, surface, col_xs["stock"], y_offset)

                if show_trend_icons:
                    previous_sell_price = quality_market_data.get("previous_sell_price")
                    trend_icon, trend_color = _calculate_trend_icon(sell_price, previous_sell_price)
                    draw_text(trend_icon, font_small, trend_color, surface, col_xs["trend"], y_offset)
                else:
                    draw_text("-", font_small, GREY, surface, col_xs["trend"], y_offset)
                
                y_offset += line_height
                if y_offset > SCREEN_HEIGHT - 80: # Basic pagination/scroll prevention
                    draw_text("...", font_small, WHITE, surface, col_xs["drug"], y_offset)
                    break 
            if y_offset > SCREEN_HEIGHT - 80:
                break


    # Display player cash
    if player_inventory_data:
        draw_text(f"Cash: ${player_inventory_data.cash:,.2f}", font_medium, WHITE, surface, SCREEN_WIDTH - 250, SCREEN_HEIGHT - 40)
    draw_text(f"Day: {game_state_data.current_day}", font_medium, WHITE, surface, 50, SCREEN_HEIGHT - 40) # Use game_state_data
    # Add a back button for market view
    for button in market_view_buttons:
        button.draw(surface)

def draw_inventory_view(surface, player_inventory_data, game_state_data):
    """Draws the player inventory view."""
    draw_text("Inventory", font_large, WHITE, surface, SCREEN_WIDTH // 2, 30, center_aligned=True)
    y_offset = 80
    line_height = 25

    if player_inventory_data:
        draw_text(f"Cash: ${player_inventory_data.cash:,.2f}", font_medium, WHITE, surface, 50, y_offset)
        y_offset += 40
        draw_text(f"Capacity: {player_inventory_data.current_load}/{player_inventory_data.max_capacity}", font_medium, WHITE, surface, 50, y_offset)
        y_offset += 40

        draw_text("Drugs:", font_medium, LIGHT_GREY, surface, 50, y_offset)
        y_offset += 30
        if not player_inventory_data.items:
            draw_text("No drugs in inventory.", font_small, WHITE, surface, 70, y_offset)
            y_offset += line_height
        else:
            sorted_drug_names = sorted(player_inventory_data.items.keys(), key=lambda d: d.value)
            for drug_name_enum in sorted_drug_names:
                qualities = player_inventory_data.items[drug_name_enum]
                sorted_qualities = sorted(qualities.keys(), key=lambda q: q.value)
                for quality_enum in sorted_qualities:
                    quantity = qualities[quality_enum]
                    if quantity > 0:
                        draw_text(f"- {drug_name_enum.value} ({quality_enum.name.capitalize()}): {quantity}", font_small, WHITE, surface, 70, y_offset)
                        y_offset += line_height
        y_offset += 20 # Extra space
        
        draw_text("Crypto Wallet:", font_medium, LIGHT_GREY, surface, 50, y_offset)
        y_offset += 30
        if not player_inventory_data.crypto_wallet and getattr(player_inventory_data, 'staked_dc', 0) == 0:
            draw_text("Wallet empty and no DC staked.", font_small, WHITE, surface, 70, y_offset)
            y_offset += line_height
        else:
            if player_inventory_data.crypto_wallet:
                for coin, amount in sorted(player_inventory_data.crypto_wallet.items()):
                    draw_text(f"- {coin}: {amount:.4f}", font_small, WHITE, surface, 70, y_offset)
                    y_offset += line_height
            if getattr(player_inventory_data, 'staked_dc', 0) > 0:
                 draw_text(f"- Staked DC: {player_inventory_data.staked_dc:.4f}", font_small, WHITE, surface, 70, y_offset)
                 y_offset += line_height
        y_offset += 20

        draw_text("Skills & Upgrades:", font_medium, LIGHT_GREY, surface, 50, y_offset)
        y_offset += 30
        if player_inventory_data.unlocked_skills:
            for skill in sorted(player_inventory_data.unlocked_skills):
                 draw_text(f"- {skill.replace('_', ' ').title()}", font_small, WHITE, surface, 70, y_offset)
                 y_offset += line_height
        if getattr(player_inventory_data, 'has_secure_phone', False):
            draw_text("- Secure Phone", font_small, WHITE, surface, 70, y_offset)
            y_offset += line_height
        if not player_inventory_data.unlocked_skills and not getattr(player_inventory_data, 'has_secure_phone', False):
            draw_text("None acquired.", font_small, WHITE, surface, 70, y_offset)
            y_offset += line_height

    for button in inventory_view_buttons:
        button.draw(surface)

def draw_travel_view(surface, current_region_data, player_inventory_data, game_state_data):
    """Draws the travel view."""
    draw_text("Travel", font_large, WHITE, surface, SCREEN_WIDTH // 2, 30, center_aligned=True)
    current_region_name = current_region_data.name.value if current_region_data and hasattr(current_region_data, 'name') and current_region_data.name else "N/A"
    draw_text(f"Current Region: {current_region_name}", font_medium, LIGHT_GREY, surface, SCREEN_WIDTH // 2, 100, center_aligned=True)
    
    y_offset = 150
    line_height = 40
    button_width = 250
    button_height = 35

    # Create temporary buttons for regions for now - ideally, these would be persistent if the view is complex
    # Or, travel_view_buttons list would be populated dynamically here
    temp_travel_buttons = []
    if game_state_data and game_state_data.all_regions:
        for region_enum, region_obj in game_state_data.all_regions.items():
            if region_obj.name != current_region_data.name:
                # This is a simplified action; a real one would call game logic
                action = lambda r=region_obj: print(f"Travel to {r.name.value} selected (not implemented)") 
                # We would need a way to make these buttons part of the event loop or handle clicks directly
                # For now, just drawing text that looks like a button area
                # To make them clickable, they should be added to travel_view_buttons and handled in the event loop
                # For simplicity in this step, just drawing text.
                draw_text(f"Go to {region_obj.name.value}", font_medium, BLUE, surface, SCREEN_WIDTH // 2, y_offset, center_aligned=True)
                y_offset += line_height
    else:
        draw_text("No regions available to travel to.", font_small, WHITE, surface, SCREEN_WIDTH // 2, y_offset, center_aligned=True)

    for button in travel_view_buttons: # For the permanent "Back" button
        button.draw(surface)

def draw_tech_contact_view(surface, player_inventory_data, game_state_data, game_configs_data):
    """Draws the Tech Contact view. (Placeholder)"""
    draw_text("Tech Contact", font_large, WHITE, surface, SCREEN_WIDTH // 2, 30, center_aligned=True)
    
    y_offset = 100
    # Display current crypto prices from game_state_data
    if game_state_data and game_state_data.current_crypto_prices:
        draw_text("Current Crypto Prices:", font_medium, LIGHT_GREY, surface, 50, y_offset)
        y_offset += 30
        for coin, price in sorted(game_state_data.current_crypto_prices.items()):
            draw_text(f"- {coin}: ${price:.2f}", font_small, WHITE, surface, 70, y_offset)
            y_offset += 25
        y_offset += 20

    draw_text(f"Transaction Fee: {game_configs_data.TECH_CONTACT_FEE_PERCENT*100:.1f}%", font_small, WHITE, surface, 50, y_offset)
    y_offset += 30
    # Placeholder for Tech Contact options (Buy, Sell, Launder, Stake buttons)
    draw_text("Actions: Buy, Sell, Launder, Stake (Not implemented as buttons yet)", font_small, WHITE, surface, 50, y_offset)

    if player_inventory_data:
         draw_text(f"Cash: ${player_inventory_data.cash:,.2f}", font_medium, WHITE, surface, 50, SCREEN_HEIGHT - 80)

    for button in tech_contact_view_buttons:
        button.draw(surface)

# --- Action Functions for Buttons ---
def action_open_market():
    global current_view
    current_view = "market"

def action_open_inventory():
    global current_view
    current_view = "inventory" # Updated

def action_open_travel():
    global current_view
    current_view = "travel" # Updated

def action_visit_tech_contact():
    global current_view
    current_view = "tech_contact" # Updated

def action_end_day():
    global current_view
    # Implement end day logic here
    print("End Day action triggered (not implemented yet)")

def action_back_to_main_menu():
    global current_view
    current_view = "main_menu"

# --- Initialize Buttons ---
def setup_buttons():
    global main_menu_buttons, market_view_buttons, inventory_view_buttons, travel_view_buttons, tech_contact_view_buttons # Added new lists
    main_menu_buttons = [
        Button(SCREEN_WIDTH // 2 - 100, 150, 200, 50, "Market", action=action_open_market),
        Button(SCREEN_WIDTH // 2 - 100, 220, 200, 50, "Inventory", action=action_open_inventory),
        Button(SCREEN_WIDTH // 2 - 100, 290, 200, 50, "Travel", action=action_open_travel),
        Button(SCREEN_WIDTH // 2 - 100, 360, 200, 50, "Tech Contact", action=action_visit_tech_contact),
        Button(SCREEN_WIDTH // 2 - 100, 500, 200, 50, "End Day", color=RED, hover_color=(255,80,80), action=action_end_day),
    ]
    market_view_buttons = [
        Button(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 60, 100, 40, "Back", color=BLUE, hover_color=(100,100,255), text_color=WHITE, action=action_back_to_main_menu)
    ]
    inventory_view_buttons = [
        Button(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 60, 100, 40, "Back", color=BLUE, hover_color=(100,100,255), text_color=WHITE, action=action_back_to_main_menu)
    ]
    travel_view_buttons = [
        Button(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 60, 100, 40, "Back", color=BLUE, hover_color=(100,100,255), text_color=WHITE, action=action_back_to_main_menu)
    ]
    tech_contact_view_buttons = [
        Button(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 60, 100, 40, "Back", color=BLUE, hover_color=(100,100,255), text_color=WHITE, action=action_back_to_main_menu)
    ]

# --- Main Game Loop ---
def game_loop(player_inventory_data, market_region_data, game_state_data, game_configs_data): # Added game_state and game_configs
    global current_view 
    setup_buttons() 
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # If in a sub-menu, ESC goes to main menu, otherwise quits
                    if current_view != "main_menu":
                        current_view = "main_menu"
                    else:
                        running = False
            
            # Pass event to buttons of the current view
            if current_view == "main_menu":
                for button in main_menu_buttons:
                    button.handle_event(event)
            elif current_view == "market":
                for button in market_view_buttons:
                    button.handle_event(event)
            elif current_view == "inventory": # Added
                for button in inventory_view_buttons:
                    button.handle_event(event)
            elif current_view == "travel":    # Added
                for button in travel_view_buttons:
                    button.handle_event(event)
            elif current_view == "tech_contact": # Added
                for button in tech_contact_view_buttons:
                    button.handle_event(event)

        # --- Drawing ---
        screen.fill(BLACK)

        if current_view == "main_menu":
            draw_main_menu(screen)
        elif current_view == "market":
            draw_market_view(screen, market_region_data, player_inventory_data, game_state_data)
        elif current_view == "inventory": # Added
            draw_inventory_view(screen, player_inventory_data, game_state_data)
        elif current_view == "travel":    # Added
            draw_travel_view(screen, market_region_data, player_inventory_data, game_state_data)
        elif current_view == "tech_contact": # Added
            draw_tech_contact_view(screen, player_inventory_data, game_state_data, game_configs_data)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    # This is placeholder data for direct testing of pygame_ui.py
    from core.enums import RegionName 
    import collections

    class MockPlayerInventory:
        def __init__(self):
            self.cash = 10000.00
            self.items = {DrugName.WEED: {DrugQuality.STANDARD: 10, DrugQuality.PURE: 5}, DrugName.COKE: {DrugQuality.CUT: 20}} # Example items
            self.crypto_wallet = {"DC": 10.5, "SC": 1000.0, "VC": 0.5}
            self.staked_dc = 50.0
            self.unlocked_skills = ["MARKET_INTUITION", "DIGITAL_FOOTPRINT"]
            self.has_secure_phone = True
            self.max_capacity = 100
            self.current_load = 35

    class MockMarketRegionData: # This now more closely represents a single Region object
        def __init__(self):
            self.name = RegionName.BRONX 
            # self.current_day = 1 # Day is now in MockGameState
            self.drug_market_data = {
                DrugName.WEED: {"available_qualities": {
                    DrugQuality.CUT: {"buy_price": 50, "sell_price": 40, "stock": 100, "previous_sell_price": 38},
                    DrugQuality.STANDARD: {"buy_price": 100, "sell_price": 80, "stock": 50, "previous_sell_price": 75}
                }},
                DrugName.COKE: {"available_qualities": {
                    DrugQuality.STANDARD: {"buy_price": 400, "sell_price": 350, "stock": 0, "previous_sell_price": 360}, # Test zero stock
                    DrugQuality.PURE: {"buy_price": 500, "sell_price": 450, "stock": 20, "previous_sell_price": 460}
                }},
                DrugName.HEROIN: {"available_qualities": { # Test no previous price
                    DrugQuality.STANDARD: {"buy_price": 600, "sell_price": 550, "stock": 10}
                }},
                DrugName.SPEED: {} # Test drug with no listed qualities
            }
            self.active_market_events = []
        
        # Mocking methods from Region class that draw_market_view will use
        def get_available_stock(self, drug_name_enum, quality_enum):
            return self.drug_market_data.get(drug_name_enum, {}).get("available_qualities", {}).get(quality_enum, {}).get("stock", 0)

        def get_buy_price(self, drug_name_enum, quality_enum):
            return self.drug_market_data.get(drug_name_enum, {}).get("available_qualities", {}).get(quality_enum, {}).get("buy_price", 0)

        def get_sell_price(self, drug_name_enum, quality_enum):
            return self.drug_market_data.get(drug_name_enum, {}).get("available_qualities", {}).get(quality_enum, {}).get("sell_price", 0)

    class MockGameConfigs:
        def __init__(self):
            self.TECH_CONTACT_FEE_PERCENT = 0.05
            # Add other configs as needed by UI components
            self.SKILL_MARKET_INTUITION_COST = 1 # Example
            self.SKILL_DIGITAL_FOOTPRINT_COST = 1 # Example
            self.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT = 0.25 # Example
            self.SECURE_PHONE_COST = 1000 # Example
            self.SECURE_PHONE_HEAT_REDUCTION_PERCENT = 0.15 # Example
            self.SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT = 0.35 # Example
            self.GHOST_NETWORK_ACCESS_COST_DC = 5.0 # Example
            self.LAUNDERING_FEE_PERCENT = 0.1 # Example
            self.LAUNDERING_DELAY_DAYS = 3 # Example
            self.HEAT_FROM_CRYPTO_TRANSACTION = 5 # Example

    class MockGameState:
        def __init__(self):
            self.current_day = 1
            self.current_crypto_prices = {"DC": 50.0, "VC": 20.0, "SC": 1.0}
            # Mock all_regions as a dictionary {RegionName: MockMarketRegionData_instance}
            self.all_regions = {RegionName.BRONX: MockMarketRegionData()} # Add more mock regions if needed for travel view
            self.all_regions[RegionName.MANHATTAN] = MockMarketRegionData() # Example of another region
            self.all_regions[RegionName.MANHATTAN].name = RegionName.MANHATTAN # Make sure name is correct
            # self.player_location = RegionName.BRONX # Example, if needed

    mock_player_inventory = MockPlayerInventory()
    mock_market_region = mock_player_inventory.current_region if hasattr(mock_player_inventory, 'current_region') else MockMarketRegionData() # Or however current region is determined
    mock_game_state = MockGameState()
    mock_game_configs = MockGameConfigs()
    
    # When running pygame_ui.py directly, market_region_data is the current region.
    # For the travel view, it needs game_state.all_regions.
    # The draw_market_view uses market_region_data.current_day, which should now come from game_state_data.current_day.
    current_mock_region = mock_game_state.all_regions.get(RegionName.BRONX) # Default to Bronx for direct run

    game_loop(mock_player_inventory, current_mock_region, mock_game_state, mock_game_configs)
