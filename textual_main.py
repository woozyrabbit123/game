from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import VerticalScroll, Horizontal, Vertical, ScrollableContainer # Added ScrollableContainer
from textual.widgets import Log # For a better log display

# Import game logic components
from core.player_inventory import PlayerInventory
from core.region import Region
from core.enums import DrugQuality # For region init
import game_state # For crypto prices
# Import specific game configs needed in this file
from game_configs import (
    PLAYER_STARTING_CASH, PLAYER_MAX_CAPACITY, CRYPTO_PRICES_INITIAL,
    HEAT_FROM_SELLING_DRUG_TIER, CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE, 
    POLICE_STOP_HEAT_THRESHOLD,
    # Skill related configs
    SKILL_MARKET_INTUITION_COST, SKILL_DIGITAL_FOOTPRINT_COST,
    DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT,
    # Upgrade related configs
    CAPACITY_UPGRADE_COST_INITIAL, CAPACITY_UPGRADE_COST_MULTIPLIER, 
    CAPACITY_UPGRADE_AMOUNT, SECURE_PHONE_COST, SECURE_PHONE_HEAT_REDUCTION_PERCENT,
    GHOST_NETWORK_ACCESS_COST_DC,
    # Laundering configs
    LAUNDERING_FEE_PERCENT, LAUNDERING_DELAY_DAYS, HEAT_FROM_CRYPTO_TRANSACTION,
    SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT, TECH_CONTACT_FEE_PERCENT, # Added TECH_CONTACT_FEE_PERCENT
    DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT # For heat calculation
)
import random # For region init

# Import custom widgets
from narco_widgets import (
    StatusBar, MainMenu, MarketView, InventoryView, 
    BuyDrugScreen, SellDrugScreen, TravelView, SkillsView, UpgradesView,
    TechContactView, LaunderCashScreen, BuyCryptoScreen # Added BuyCryptoScreen
)

# Need to import game logic for police stops
from ui.text_ui_handlers import check_and_trigger_police_stop, handle_police_stop_event # Assuming these can be adapted or used

class NarcoApp(App):
    """A Textual app for Project Narco-Syndicate."""

    TITLE = "Project Narco-Syndicate"
    CSS_PATH = "narco_style.tcss"

    # Define key bindings: (key, action, description)
    BINDINGS = [
        ("a", "advance_day", "Advance Day"),
        ("q", "quit", "Quit") # Standard quit binding
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize game state here
        self.current_day = 1
        self.player_inventory = PlayerInventory(max_capacity=PLAYER_MAX_CAPACITY, starting_cash=PLAYER_STARTING_CASH)
        game_state.initialize_crypto_prices(CRYPTO_PRICES_INITIAL) # Initialize crypto prices
        self.all_game_regions = {}
        self._initialize_regions() # Helper method to setup regions
        self.current_player_region = self.all_game_regions.get("Downtown")
        # Initialize AI rivals if needed later
        # self.ai_rivals = self._initialize_ai_rivals()

    def _initialize_regions(self):
        # Downtown
        downtown = Region("Downtown")
        downtown.initialize_drug_market("Weed", 50, 80, 1, {DrugQuality.STANDARD: random.randint(100,200)})
        downtown.initialize_drug_market("Pills", 100, 150, 2, {DrugQuality.STANDARD: random.randint(40,80), DrugQuality.CUT: random.randint(60,120)})
        downtown.initialize_drug_market("Coke", 1000, 1500, 3, {DrugQuality.PURE: random.randint(10,25), DrugQuality.STANDARD: random.randint(15,50), DrugQuality.CUT: random.randint(20,60)})
        self.all_game_regions["Downtown"] = downtown
        # The Docks
        the_docks = Region("The Docks")
        the_docks.initialize_drug_market("Weed", 40, 70, 1, {DrugQuality.STANDARD: random.randint(100,300)})
        the_docks.initialize_drug_market("Speed", 120, 180, 2, {DrugQuality.STANDARD: random.randint(30,90), DrugQuality.CUT: random.randint(50,100)})
        the_docks.initialize_drug_market("Heroin", 600, 900, 3, {DrugQuality.PURE: random.randint(5,15), DrugQuality.STANDARD: random.randint(10,30)})
        self.all_game_regions["The Docks"] = the_docks
        # Suburbia
        suburbia = Region("Suburbia")
        suburbia.initialize_drug_market("Weed", 60, 100, 1, {DrugQuality.STANDARD: random.randint(20,60)})
        suburbia.initialize_drug_market("Pills", 110, 170, 2, {DrugQuality.STANDARD: random.randint(20,50), DrugQuality.PURE: random.randint(5,15) })
        self.all_game_regions["Suburbia"] = suburbia
        # Restock all markets initially
        for r_obj in self.all_game_regions.values():
            r_obj.restock_market()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal():
            yield MainMenu(id="main_menu")
            with Vertical(id="content_column"):
                yield StatusBar(id="status_bar")
                yield ScrollableContainer(Static("Welcome! Select an action.", id="main_content_text"), id="main_content_area")
                yield Log(id="event_log", classes="log_area", max_lines=10) # Added Log widget
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        status_bar = self.query_one(StatusBar)
        status_bar.current_day = self.current_day
        status_bar.cash = self.player_inventory.cash
        status_bar.current_region_name = self.current_player_region.name if self.current_player_region else "N/A"
        status_bar.current_load = self.player_inventory.current_load
        status_bar.max_capacity = self.player_inventory.max_capacity
        
        # self.focus() # Removed this line
        # If you want to set initial focus, pick a widget:
        # self.query_one(MainMenu).focus()

    def action_advance_day(self, is_jailed_turn: bool = False) -> None:
        """Called when the 'a' key is pressed or by travel."""
        self.current_day += 1
        # --- Perform game logic for advancing a day --- 
        # This should include: updating crypto, decaying market impacts, AI turns, event checks etc.
        # For now, just a simple example:
        game_state.update_daily_crypto_prices(CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE) # Assuming CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE are imported or accessible
        for region in self.all_game_regions.values():
            decay_player_market_impact(region)
            decay_rival_market_impact(region, self.current_day) # Assuming this function exists and is correct
            decay_regional_heat(region)
            region.restock_market() # Or a more nuanced daily update
            update_active_events(region) # Process active events
            # Trigger new random events (optional, could be less frequent)
            # if random.random() < EVENT_TRIGGER_CHANCE: # Assuming EVENT_TRIGGER_CHANCE is defined
            #     trigger_random_market_event(region, self.current_day, self.player_inventory, self.ai_rivals if hasattr(self, 'ai_rivals') else [])

        # Check for debt payments (simplified, more robust checks needed for specific due days)
        # This logic should ideally be more structured, perhaps in a dedicated game_loop_update method.

        # Update StatusBar
        status_bar = self.query_one(StatusBar)
        status_bar.current_day = self.current_day
        if not is_jailed_turn: # Only apply daily expenses if not jailed
            self.player_inventory.cash -= 1 
        status_bar.cash = self.player_inventory.cash
        status_bar.current_load = self.player_inventory.current_load
        status_bar.max_capacity = self.player_inventory.max_capacity

        event_log = self.query_one("#event_log", Log)
        if not is_jailed_turn:
            event_log.write_line(f"Advanced to Day {self.current_day}. Cash: ${self.player_inventory.cash:.2f}. Load: {self.player_inventory.current_load}/{self.player_inventory.max_capacity}")
        else:
            event_log.write_line(f"Day {self.current_day} passes in jail...")
        
        # Refresh current view if needed (e.g., MarketView)
        content_area = self.query_one("#main_content_area", ScrollableContainer)
        active_market_views = content_area.query(MarketView)
        if active_market_views and not is_jailed_turn: # Don't refresh market if jailed and just passing time
            self.call_later(active_market_views[0].load_market_data)

    async def on_main_menu_menu_item_selected(self, message: MainMenu.MenuItemSelected) -> None:
        """Handle menu item selection by swapping content or pushing screens."""
        content_area = self.query_one("#main_content_area", ScrollableContainer)
        event_log = self.query_one("#event_log", Log)

        if message.item_id == "buy_drug":
            if self.current_player_region:
                async def buy_drug_callback(data: tuple):
                    status_bar = self.query_one(StatusBar) # Fetch status_bar here
                    if data:
                        drug_name_input, quality_str, quantity = data
                        event_log.write_line(f"Attempting to buy: {quantity} of {quality_str} {drug_name_input}")

                        # Find canonical drug name (case-insensitive)
                        canonical_drug_name = None
                        for market_drug_name in self.current_player_region.drug_market_data.keys():
                            if market_drug_name.lower() == drug_name_input.lower():
                                canonical_drug_name = market_drug_name
                                break
                        
                        if not canonical_drug_name:
                            event_log.write_line(f"[ERROR] Drug '{drug_name_input}' not found in {self.current_player_region.name} market.")
                            return

                        quality_enum = parse_drug_quality(quality_str)
                        if not quality_enum:
                            event_log.write_line(f"[ERROR] Invalid drug quality: {quality_str}. Use PURE, STANDARD, or CUT.")
                            return
                        
                        # Check if quality is available for this drug in the market
                        if quality_enum not in self.current_player_region.drug_market_data.get(canonical_drug_name, {}).get("available_qualities", {}):
                            event_log.write_line(f"[ERROR] Quality '{quality_str}' not available for {canonical_drug_name} in this market.")
                            return

                        stock = self.current_player_region.get_available_stock(canonical_drug_name, quality_enum)
                        if stock < quantity:
                            event_log.write_line(f"[ERROR] Insufficient stock for {canonical_drug_name} ({quality_str}). Available: {stock}")
                            return

                        buy_price = self.current_player_region.get_buy_price(canonical_drug_name, quality_enum)
                        if buy_price <= 0:
                            event_log.write_line(f"[ERROR] {canonical_drug_name} ({quality_str}) currently not for sale or price is zero.")
                            return
                        
                        total_cost = buy_price * quantity
                        if self.player_inventory.cash < total_cost:
                            event_log.write_line(f"[ERROR] Not enough cash. Need ${total_cost:,.2f}, have ${self.player_inventory.cash:,.2f}.")
                            return
                        
                        if self.player_inventory.get_available_space() < quantity:
                            event_log.write_line(f"[ERROR] Not enough inventory space. Available: {self.player_inventory.get_available_space()}, need: {quantity}.")
                            return
                        
                        # Attempt the actual purchase
                        if self.player_inventory.add_drug(canonical_drug_name, quality_enum, quantity):
                            self.current_player_region.update_stock_on_buy(canonical_drug_name, quality_enum, quantity)
                            self.player_inventory.cash -= total_cost
                            apply_player_buy_impact(self.current_player_region, canonical_drug_name, quantity)
                            
                            event_log.write_line(f"[SUCCESS] Bought {quantity} of {quality_str} {canonical_drug_name} for ${total_cost:,.2f}.")
                            status_bar.cash = self.player_inventory.cash
                            status_bar.current_load = self.player_inventory.current_load
                            
                            active_market_views = content_area.query(MarketView)
                            if active_market_views:
                                await active_market_views[0].load_market_data()
                            active_inventory_views = content_area.query(InventoryView)
                            if active_inventory_views:
                                await active_inventory_views[0].load_inventory_data()
                        else:
                            event_log.write_line(f"[ERROR] Generic error adding {canonical_drug_name} to inventory.")
                    else:
                        event_log.write_line("[INFO] Buy drug action cancelled.")
                
                self.push_screen(BuyDrugScreen(current_region_name=self.current_player_region.name), buy_drug_callback)
            else:
                event_log.write_line("[ERROR] No current region selected to buy drugs.")
            return
        
        elif message.item_id == "sell_drug":
            if self.current_player_region:
                async def sell_drug_callback(data: tuple):
                    status_bar = self.query_one(StatusBar) # Fetch status_bar here
                    if data:
                        drug_name_input, quality_str, quantity = data
                        event_log.write_line(f"Attempting to sell: {quantity} of {quality_str} {drug_name_input}")

                        # Find canonical drug name (case-insensitive) from player inventory
                        canonical_drug_name_inv = None
                        for inv_drug_name in self.player_inventory.items.keys():
                            if inv_drug_name.lower() == drug_name_input.lower():
                                canonical_drug_name_inv = inv_drug_name
                                break
                        if not canonical_drug_name_inv:
                            event_log.write_line(f"[ERROR] Drug '{drug_name_input}' not found in your inventory.")
                            return

                        quality_enum = parse_drug_quality(quality_str)
                        if not quality_enum:
                            event_log.write_line(f"[ERROR] Invalid drug quality: {quality_str}. Use PURE, STANDARD, or CUT.")
                            return
                        
                        player_quantity = self.player_inventory.get_quantity(canonical_drug_name_inv, quality_enum)
                        if player_quantity == 0:
                            event_log.write_line(f"[ERROR] Quality '{quality_str}' for {canonical_drug_name_inv} not found in inventory.")
                            return
                        if player_quantity < quantity:
                            event_log.write_line(f"[ERROR] Not enough {quality_str} {canonical_drug_name_inv} in inventory. You have: {player_quantity}, trying to sell: {quantity}")
                            return

                        # Find corresponding market drug name (can be different casing)
                        market_drug_name_match = None
                        drug_tier = 1 # Default tier
                        for m_name, m_data in self.current_player_region.drug_market_data.items():
                            if m_name.lower() == canonical_drug_name_inv.lower():
                                market_drug_name_match = m_name
                                drug_tier = m_data.get("tier", 1)
                                break
                        if not market_drug_name_match:
                            event_log.write_line(f"[ERROR] Market in {self.current_player_region.name} does not trade {canonical_drug_name_inv}.")
                            return

                        sell_price = self.current_player_region.get_sell_price(market_drug_name_match, quality_enum)
                        if sell_price <= 0:
                            event_log.write_line(f"[ERROR] Market in {self.current_player_region.name} not buying {quality_str} {market_drug_name_match} or price is zero.")
                            return

                        total_revenue = sell_price * quantity
                        if self.player_inventory.remove_drug(canonical_drug_name_inv, quality_enum, quantity):
                            self.player_inventory.cash += total_revenue
                            apply_player_sell_impact(self.current_player_region, market_drug_name_match, quantity)
                            
                            heat_generated = quantity * HEAT_FROM_SELLING_DRUG_TIER.get(drug_tier, 1)
                            if heat_generated > 0:
                                self.current_player_region.modify_heat(heat_generated)
                                event_log.write_line(f"[INFO] Heat in {self.current_player_region.name} +{heat_generated} due to sale.")

                            event_log.write_line(f"[SUCCESS] Sold {quantity} of {quality_str} {canonical_drug_name_inv} for ${total_revenue:,.2f}.")
                            status_bar.cash = self.player_inventory.cash
                            status_bar.current_load = self.player_inventory.current_load
                            
                            active_market_views = content_area.query(MarketView)
                            if active_market_views:
                                await active_market_views[0].load_market_data()
                            active_inventory_views = content_area.query(InventoryView)
                            if active_inventory_views:
                                await active_inventory_views[0].load_inventory_data()
                        else:
                            event_log.write_line(f"[ERROR] Generic error removing {canonical_drug_name_inv} from inventory.")
                    else:
                        event_log.write_line("[INFO] Sell drug action cancelled.")
                self.push_screen(SellDrugScreen(current_region_name=self.current_player_region.name), sell_drug_callback)
            else:
                event_log.write_line("[ERROR] No current region selected to sell drugs.")
            return

        await content_area.remove_children()
        if message.item_id == "view_market":
            if self.current_player_region:
                market_view = MarketView(self.current_player_region, self.player_inventory)
                await content_area.mount(market_view)
            else:
                await content_area.mount(Static("No current region selected to view market."))
        elif message.item_id == "view_inventory":
            inventory_view = InventoryView(self.player_inventory)
            await content_area.mount(inventory_view)
        elif message.item_id == "travel":
            if self.current_player_region:
                travel_view = TravelView(self.current_player_region.name, self.all_game_regions)
                await content_area.mount(travel_view)
            else:
                await content_area.mount(Static("Cannot travel without a current region."))
        elif message.item_id == "skills":
            # Pass game_configs directly or the specific skill constants needed
            # For simplicity, passing the module; a more refined approach might pass a dict of skill data
            import game_configs # Make sure it's available
            skills_view = SkillsView(self.player_inventory, game_configs)
            await content_area.mount(skills_view)
        elif message.item_id == "upgrades":
            import game_configs # Make sure it's available
            upgrades_view = UpgradesView(self.player_inventory, game_configs)
            await content_area.mount(upgrades_view)
        elif message.item_id == "tech_contact":
            import game_configs # Ensure it's available for TechContactView
            # TechContactView might also need current crypto prices, pass from game_state
            tech_view = TechContactView(self.player_inventory, game_configs)
            await content_area.mount(tech_view)
        else:
            await content_area.mount(Static(f"Menu item '{message.item_id}' selected. (Not implemented yet)"))

    async def on_travel_view_region_selected(self, message: TravelView.RegionSelected) -> None:
        """Handle region selection from TravelView."""
        content_area = self.query_one("#main_content_area", ScrollableContainer)
        event_log = self.query_one("#event_log", Log)
        status_bar = self.query_one(StatusBar)

        if message.region_id == "cancel_travel":
            event_log.write_line("[INFO] Travel cancelled.")
            await content_area.remove_children()
            await content_area.mount(Static("Travel cancelled. Select an action."))
            return

        destination_region_id = message.region_id
        destination_region = self.all_game_regions.get(destination_region_id)

        if not destination_region:
            event_log.write_line(f"[ERROR] Invalid travel destination: {destination_region_id}")
            return

        event_log.write_line(f"Attempting to travel to {destination_region.name}...")

        # --- Police Stop Check --- (Needs adaptation for Textual)
        # The original check_and_trigger_police_stop and handle_police_stop_event use print/input.
        # This needs to be refactored into a Textual screen or a series of dialogs.
        # For now, we'll simulate it and assume no stop or a simple outcome.
        # In a real implementation, this would involve pushing a PoliceStopScreen if needed.
        
        # Simplified check for now:
        police_stop_occurred = False
        jailed_days = 0
        if self.current_player_region.current_heat >= POLICE_STOP_HEAT_THRESHOLD: # Assuming POLICE_STOP_HEAT_THRESHOLD is imported
            if random.random() < 0.3: # Simplified chance of police stop
                police_stop_occurred = True
                event_log.write_line("[WARNING] Police stop! (Simplified outcome for now)")
                # Simulate a small penalty or a few days lost if caught
                if random.random() < 0.5: # Chance of being jailed
                    jailed_days = random.randint(1,3)
                    event_log.write_line(f"[CRITICAL] Jailed for {jailed_days} days! (Simplified)")
                    for _ in range(jailed_days):
                        self.action_advance_day(is_jailed_turn=True) # Pass a flag if advance_day handles it
                else:
                    event_log.write_line("[INFO] Managed to talk your way out... this time.")
        
        if not police_stop_occurred or jailed_days == 0:
            event_log.write_line(f"Traveling to {destination_region.name}...")
            # Advance day for travel
            self.action_advance_day() # This already updates day, status bar etc.
            self.current_player_region = destination_region
            status_bar.current_region_name = self.current_player_region.name
            event_log.write_line(f"Arrived in {self.current_player_region.name}.")
            # Show market of new region
            await content_area.remove_children()
            market_view = MarketView(self.current_player_region, self.player_inventory)
            await content_area.mount(market_view)
        else:
            # If jailed, the day has already advanced. Update status bar for current state.
            status_bar.current_day = self.current_day
            status_bar.cash = self.player_inventory.cash
            status_bar.current_load = self.player_inventory.current_load
            await content_area.remove_children()
            await content_area.mount(Static(f"Released from jail. Back in {self.current_player_region.name}."))

    async def on_skills_view_unlock_skill(self, message: SkillsView.UnlockSkill) -> None:
        """Handle skill unlock attempts from SkillsView."""
        event_log = self.query_one("#event_log", Log)
        status_bar = self.query_one(StatusBar)
        content_area = self.query_one("#main_content_area", ScrollableContainer)
        skill_id_to_unlock = message.skill_id

        cost = 0
        skill_name = "Unknown Skill"

        if skill_id_to_unlock == "MARKET_INTUITION":
            cost = SKILL_MARKET_INTUITION_COST
            skill_name = "Market Intuition"
        elif skill_id_to_unlock == "DIGITAL_FOOTPRINT":
            cost = SKILL_DIGITAL_FOOTPRINT_COST
            skill_name = "Digital Footprint"
        # Add other skills here

        if skill_id_to_unlock in self.player_inventory.unlocked_skills:
            event_log.write_line(f"[INFO] Skill '{skill_name}' already unlocked.")
        elif self.player_inventory.skill_points >= cost:
            self.player_inventory.skill_points -= cost
            self.player_inventory.unlocked_skills.append(skill_id_to_unlock)
            event_log.write_line(f"[SUCCESS] Skill '{skill_name}' unlocked!")
            status_bar.current_load = self.player_inventory.current_load # Skill points don't affect load, but refresh other parts if needed
            # Refresh the SkillsView to show updated status and buttons
            await content_area.remove_children()
            import game_configs # Ensure it's available for re-mounting
            skills_view = SkillsView(self.player_inventory, game_configs)
            await content_area.mount(skills_view)
        else:
            event_log.write_line(f"[ERROR] Not enough skill points to unlock '{skill_name}'. Need {cost}, have {self.player_inventory.skill_points}.")
        
        # Update status bar if skill points changed (though not a direct display on statusbar currently)
        # No direct display of skill points on status_bar, but other stats might change indirectly.

    async def on_upgrades_view_purchase_upgrade(self, message: UpgradesView.PurchaseUpgrade) -> None:
        """Handle upgrade purchase attempts from UpgradesView."""
        event_log = self.query_one("#event_log", Log)
        status_bar = self.query_one(StatusBar)
        content_area = self.query_one("#main_content_area", ScrollableContainer)
        upgrade_id_to_purchase = message.upgrade_id

        if upgrade_id_to_purchase == "CAPACITY":
            cost = CAPACITY_UPGRADE_COST_INITIAL * (CAPACITY_UPGRADE_COST_MULTIPLIER ** self.player_inventory.capacity_upgrades_purchased)
            if self.player_inventory.cash >= cost:
                self.player_inventory.cash -= cost
                self.player_inventory.upgrade_capacity(CAPACITY_UPGRADE_AMOUNT)
                self.player_inventory.capacity_upgrades_purchased += 1
                event_log.write_line(f"[SUCCESS] Carrying capacity upgraded by {CAPACITY_UPGRADE_AMOUNT}! New capacity: {self.player_inventory.max_capacity}")
                status_bar.cash = self.player_inventory.cash
                status_bar.max_capacity = self.player_inventory.max_capacity
                # Refresh UpgradesView
                await content_area.remove_children()
                import game_configs
                upgrades_view = UpgradesView(self.player_inventory, game_configs)
                await content_area.mount(upgrades_view)
            else:
                event_log.write_line(f"[ERROR] Not enough cash for capacity upgrade. Need ${cost:,.2f}.")
        
        elif upgrade_id_to_purchase == "SECURE_PHONE":
            if self.player_inventory.has_secure_phone:
                event_log.write_line("[INFO] Secure Phone already purchased.")
            elif self.player_inventory.cash >= SECURE_PHONE_COST:
                self.player_inventory.cash -= SECURE_PHONE_COST
                self.player_inventory.has_secure_phone = True
                event_log.write_line("[SUCCESS] Secure Phone purchased!")
                status_bar.cash = self.player_inventory.cash
                # Refresh UpgradesView
                await content_area.remove_children()
                import game_configs
                upgrades_view = UpgradesView(self.player_inventory, game_configs)
                await content_area.mount(upgrades_view)
            else:
                event_log.write_line(f"[ERROR] Not enough cash for Secure Phone. Need ${SECURE_PHONE_COST:,.2f}.")
        elif upgrade_id_to_purchase == "GHOST_NETWORK_ACCESS":
            cost = GHOST_NETWORK_ACCESS_COST_DC
            dc_balance = self.player_inventory.crypto_wallet.get("DC", 0.0)
            if dc_balance >= cost:
                self.player_inventory.crypto_wallet["DC"] -= cost
                if self.player_inventory.crypto_wallet["DC"] < 1e-9: del self.player_inventory.crypto_wallet["DC"]
                self.player_inventory.unlocked_skills.append("GHOST_NETWORK_ACCESS")
                event_log.write_line("[SUCCESS] Ghost Network Access purchased!")
                # Refresh TechContactView to update button state
                await content_area.remove_children()
                import game_configs
                tech_view = TechContactView(self.player_inventory, game_configs)
                await content_area.mount(tech_view)
            else:
                event_log.write_line(f"[ERROR] Insufficient DC for Ghost Network Access. Need {cost:.2f}, have {dc_balance:.2f}.")

    async def on_tech_contact_view_tech_action_selected(self, message: TechContactView.TechActionSelected) -> None:
        """Handle actions selected from the TechContactView."""
        event_log = self.query_one("#event_log", Log)
        status_bar = self.query_one(StatusBar)
        content_area = self.query_one("#main_content_area", ScrollableContainer)
        action_id = message.action_id

        # event_log.write_line(f"Tech Contact action selected: {action_id}") # Can be too verbose

        if action_id == "buy_crypto":
            async def buy_crypto_callback(result):
                if result:
                    coin_symbol, quantity = result
                    price = game_state.current_crypto_prices[coin_symbol]
                    sub_total = quantity * price
                    fee = sub_total * TECH_CONTACT_FEE_PERCENT
                    total_cost = sub_total + fee
                    
                    self.player_inventory.cash -= total_cost
                    current_balance = self.player_inventory.crypto_wallet.get(coin_symbol, 0.0)
                    self.player_inventory.crypto_wallet[coin_symbol] = current_balance + quantity
                    
                    event_log.write_line(f"Bought {quantity:.4f} {coin_symbol} for ${sub_total:.2f} (Fee: ${fee:.2f}). Total: ${total_cost:.2f}")
                    
                    # Handle heat generation with reductions
                    base_heat = HEAT_FROM_CRYPTO_TRANSACTION
                    effective_heat = base_heat
                    has_skill = "DIGITAL_FOOTPRINT" in self.player_inventory.unlocked_skills
                    has_phone = self.player_inventory.has_secure_phone
                    
                    if has_skill and has_phone:
                        effective_heat *= (1.0 - SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT)
                    elif has_skill:
                        effective_heat *= (1.0 - DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
                    elif has_phone:
                        effective_heat *= (1.0 - SECURE_PHONE_HEAT_REDUCTION_PERCENT)
                    
                    effective_heat = int(round(effective_heat))
                    if effective_heat > 0:
                        self.current_region.modify_heat(effective_heat)
                        event_log.write_line(f"Crypto activity heat +{effective_heat} in {self.current_region.name}")
                    
                    # Update UI components
                    await content_area.query_one(TechContactView).remove()
                    tech_contact_view = TechContactView(player_inventory_data=self.player_inventory, game_configs_data=game_configs)
                    await content_area.mount(tech_contact_view)
                    await status_bar.update_status(self.player_inventory, self.current_region)
            
            screen = BuyCryptoScreen(
                current_cash=self.player_inventory.cash,
                crypto_prices=game_state.current_crypto_prices,
                tech_fee_percent=TECH_CONTACT_FEE_PERCENT
            )
            self.push_screen(screen, buy_crypto_callback)
            return # Prevent further processing

        elif action_id == "sell_crypto":
            event_log.write_line("Sell Crypto: Not yet implemented. Would push a new screen here.")
            pass
        elif action_id == "launder_cash":
            if self.player_inventory.pending_laundered_sc_arrival_day is not None:
                event_log.write_line("[ERROR] Laundering operation already in progress.")
                return

            async def launder_cash_callback(amount_to_launder: float):
                if amount_to_launder is not None and amount_to_launder > 0:
                    fee = amount_to_launder * LAUNDERING_FEE_PERCENT
                    net_cash_for_conversion = amount_to_launder - fee
                    # Ensure game_state.current_crypto_prices is accessible and SC price exists
                    sc_price = game_state.current_crypto_prices.get("SC", 1.0) 
                    if sc_price <= 0: sc_price = 1.0 # Fallback if SC price is invalid
                    
                    sc_to_receive = net_cash_for_conversion / sc_price
                    
                    self.player_inventory.cash -= amount_to_launder
                    self.player_inventory.pending_laundered_sc = sc_to_receive
                    self.player_inventory.pending_laundered_sc_arrival_day = self.current_day + LAUNDERING_DELAY_DAYS
                    
                    # Calculate and apply heat
                    base_heat = HEAT_FROM_CRYPTO_TRANSACTION * 2 # Laundering is sketchier
                    effective_heat = base_heat
                    has_skill = "DIGITAL_FOOTPRINT" in self.player_inventory.unlocked_skills
                    has_phone = self.player_inventory.has_secure_phone
                    if has_skill and has_phone:
                        effective_heat *= (1.0 - SKILL_PHONE_STACKING_HEAT_REDUCTION_PERCENT)
                    elif has_skill:
                        effective_heat *= (1.0 - DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT)
                    elif has_phone:
                        effective_heat *= (1.0 - SECURE_PHONE_HEAT_REDUCTION_PERCENT)
                    effective_heat = int(round(max(0, effective_heat))) # Ensure heat is not negative

                    if effective_heat > 0 and self.current_player_region:
                        self.current_player_region.modify_heat(effective_heat)
                        event_log.write_line(f"[INFO] Laundering generated +{effective_heat} heat in {self.current_player_region.name}.")
                    
                    event_log.write_line(f"[SUCCESS] Initiated laundering of ${amount_to_launder:,.2f}. Approx. {sc_to_receive:.4f} SC arriving on Day {self.player_inventory.pending_laundered_sc_arrival_day} (Fee: ${fee:,.2f}).")
                    status_bar.cash = self.player_inventory.cash
                    
                    # Refresh TechContactView to show updated pending status and disabled button
                    # This assumes TechContactView is still the primary content in content_area
                    # A more robust way might be to have TechContactView itself update reactively.
                    active_tech_views = content_area.query(TechContactView)
                    if active_tech_views:
                        # Re-compose or specifically update parts of TechContactView
                        # For simplicity, let's try to re-mount it if it's the current view
                        # This is a bit heavy-handed; ideally, TechContactView would update its own buttons/labels.
                        current_tech_view = active_tech_views[0]
                        await content_area.remove_children()
                        import game_configs
                        new_tech_view = TechContactView(self.player_inventory, game_configs)
                        await content_area.mount(new_tech_view)
                else:
                    event_log.write_line("[INFO] Laundering cash action cancelled or amount was zero.")

            self.push_screen(
                LaunderCashScreen(
                    current_cash=self.player_inventory.cash, 
                    fee_percent=LAUNDERING_FEE_PERCENT, 
                    delay_days=LAUNDERING_DELAY_DAYS
                ),
                launder_cash_callback
            )
            return # Screen pushed, main content area should not be cleared here by the menu handler

        elif action_id == "stake_dc":
            # TODO: Push a StakeDCScreen
            event_log.write_line("Stake DC: Not yet implemented.")
            pass
        elif action_id == "unstake_dc":
            # TODO: Push an UnstakeDCScreen
            event_log.write_line("Unstake DC: Not yet implemented.")
            pass
        elif action_id == "purchase_ghost_access":
            cost = GHOST_NETWORK_ACCESS_COST_DC
            dc_balance = self.player_inventory.crypto_wallet.get("DC", 0.0)
            if dc_balance >= cost:
                self.player_inventory.crypto_wallet["DC"] -= cost
                if self.player_inventory.crypto_wallet["DC"] < 1e-9: del self.player_inventory.crypto_wallet["DC"]
                self.player_inventory.unlocked_skills.append("GHOST_NETWORK_ACCESS")
                event_log.write_line("[SUCCESS] Ghost Network Access purchased!")
                # Refresh TechContactView to update button state
                await content_area.remove_children()
                import game_configs
                tech_view = TechContactView(self.player_inventory, game_configs)
                await content_area.mount(tech_view)
            else:
                event_log.write_line(f"[ERROR] Insufficient DC for Ghost Network Access. Need {cost:.2f}, have {dc_balance:.2f}.")

        # Fallback for actions that just display a view in the content_area
        # await content_area.remove_children() # This was moved up in the main on_menu_item_selected
        # if not (message.item_id == "buy_drug" or message.item_id == "sell_drug" or message.item_id == "launder_cash" ...):
        #    await content_area.mount(Static(f"Tech Contact Action '{action_id}' not fully implemented."))

if __name__ == "__main__":
    # app = NarcoApp() # Temporarily disable Textual app
    # app.run()
    
    # --- Initialize Core Game Components ---
    from core.player_inventory import PlayerInventory
    from core.region import Region, RegionName # Assuming RegionName is used for initialization
    from core.enums import DrugName, DrugQuality # Keep if used directly here, otherwise can be removed if only used by core modules
    import game_state # For current_day, current_crypto_prices, all_regions etc.
    import game_configs # For various game settings, skill costs, etc.

    # Initialize player inventory
    player_inv = PlayerInventory()
    player_inv.cash = 50000 
    player_inv.unlocked_skills.append("MARKET_INTUITION") # Example for testing
    # player_inv.has_secure_phone = True # Example for testing

    # Initialize game state (regions, day, crypto prices, etc.)
    game_state.initialize_global_state(game_configs) # Crucial for setting up regions, day 1 prices etc.
    
    # Set a current region for the player
    # For now, let's default to the first region initialized in game_state or a specific one.
    # Ensure game_state.all_regions is populated by initialize_global_state
    if game_state.all_regions:
        # Let's pick Bronx as the starting region, assuming it's defined in RegionName and initialized
        try:
            current_region_instance = game_state.all_regions[RegionName.BRONX]
        except KeyError:
            # Fallback to the first available region if Bronx is not found (e.g., if enum names differ)
            current_region_instance = list(game_state.all_regions.values())[0]
    else:
        # Fallback: Create a default region if game_state.all_regions is empty (should not happen if initialize_global_state works)
        print("Warning: game_state.all_regions is empty. Creating a default region.")
        current_region_instance = Region(RegionName.BRONX, game_configs=game_configs)
        current_region_instance.initialize_market_data_for_day(game_state.current_day, game_configs)

    # Ensure the current region's market data for the current day is initialized
    # initialize_global_state should handle this for all regions for day 1.
    # If we advance day, we'd call current_region_instance.initialize_market_data_for_day(game_state.current_day, game_configs)

    # --- Launch Pygame UI ---
    try:
        import pygame_ui
        # Pass the actual, live game state objects
        pygame_ui.game_loop(player_inv, current_region_instance, game_state, game_configs)
    except ImportError as e:
        print(f"Pygame UI module (pygame_ui.py) not found or Pygame not installed correctly: {e}")
    except Exception as e:
        print(f"An error occurred while running the Pygame UI: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback

# Need to import parse_drug_quality and apply_player_buy_impact if not already globally available
# For simplicity, assuming they are available or would be imported from core/ui_helpers and mechanics/market_impact
from core.enums import DrugQuality # Already imported
from ui.ui_helpers import parse_drug_quality # Make sure this is correct
from mechanics.market_impact import apply_player_buy_impact, apply_player_sell_impact # Make sure this is correct
# Ensure necessary imports for game logic used in action_advance_day are present
from game_configs import (
    PLAYER_STARTING_CASH, PLAYER_MAX_CAPACITY, CRYPTO_PRICES_INITIAL, 
    HEAT_FROM_SELLING_DRUG_TIER, CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE, POLICE_STOP_HEAT_THRESHOLD
)
from mechanics.market_impact import decay_player_market_impact, decay_rival_market_impact, decay_regional_heat
from mechanics.event_manager import update_active_events #, trigger_random_market_event (if uncommented)
