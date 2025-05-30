from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Button, Input, Label, DataTable # Added Input, Label, DataTable
from textual.reactive import reactive
from textual.containers import Vertical, Horizontal, ScrollableContainer # Added Vertical, Horizontal, ScrollableContainer
from textual.screen import Screen # Added Screen
from textual.message import Message # Added Message

class StatusBar(Static):
    """A widget to display game status information."""

    current_day = reactive(1)
    cash = reactive(0.0)
    current_region_name = reactive("Unknown")
    current_load = reactive(0)
    max_capacity = reactive(0)

    def on_mount(self) -> None:
        """Set up a regular update for the status bar text."""
        self.update_status_text()
        # self.set_interval(1, self.update_status_text) # Optional: if you want it to refresh periodically for other reasons

    def update_status_text(self) -> None:
        """Update the text of the status bar."""
        self.update(f"Day: {self.current_day} | Cash: ${self.cash:,.2f} | Region: {self.current_region_name} | Load: {self.current_load}/{self.max_capacity}")

    # Watch methods to automatically update when reactive variables change
    def watch_current_day(self, new_day: int) -> None:
        self.update_status_text()

    def watch_cash(self, new_cash: float) -> None:
        self.update_status_text()

    def watch_current_region_name(self, new_region: str) -> None:
        self.update_status_text()

    def watch_current_load(self, new_load: int) -> None:
        self.update_status_text()

    def watch_max_capacity(self, new_capacity: int) -> None:
        self.update_status_text()

class MainMenu(Widget):
    """A main menu widget with buttons for game actions."""

    # Define a custom message for when a menu item is selected
    class MenuItemSelected(Message):
        def __init__(self, item_id: str) -> None:
            super().__init__()
            self.item_id = item_id

    def compose(self) -> ComposeResult:
        """Create the menu buttons."""
        # Using a Vertical container for layout within the MainMenu widget itself
        with Vertical():
            yield Button("View Market", id="view_market", variant="primary")
            yield Button("View Inventory", id="view_inventory", variant="primary")
            yield Button("Buy Drug", id="buy_drug", variant="primary")
            yield Button("Sell Drug", id="sell_drug", variant="primary")
            yield Button("Travel", id="travel", variant="primary")
            yield Button("Visit Tech Contact", id="tech_contact", variant="primary") # Added Tech Contact
            yield Button("Skills", id="skills", variant="primary")
            yield Button("Upgrades", id="upgrades", variant="primary")
            yield Button("Talk to Informant", id="informant", variant="primary")
            yield Button("Meet Corrupt Official", id="official", variant="primary")
            # "Advance Day" is a key binding for now, but could be a button too
            # yield Button("Advance Day", id="advance_day_button", variant="default") 
            # Dynamic options like "Respond to Opportunities" or "Crypto Shop" can be added later

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events and post a custom message."""
        if event.button.id:
            self.post_message(self.MenuItemSelected(event.button.id))

class MarketView(Widget):
    """A widget to display market data for a region."""

    DEFAULT_CSS = """
    MarketView {
        layout: vertical;
        overflow-y: auto;
    }
    DataTable {
        width: 100%;
        height: auto; /* DataTable will manage its own height based on rows */
    }
    """

    def __init__(self, region_data, player_inventory_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._market_region_data = region_data # Renamed
        self._player_inventory_data = player_inventory_data # Renamed

    def compose(self) -> ComposeResult:
        table = DataTable(id="market_table")
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Define columns
        columns = ["Drug", "Quality", "Buy Price", "Sell Price", "Stock", "Trend"]
        if "MARKET_INTUITION" not in self._player_inventory_data.unlocked_skills: # Use renamed var
            columns.remove("Trend")
        table.add_columns(*columns)
        yield table

    async def on_mount(self) -> None:
        """Load market data into the table when the widget is mounted."""
        await self.load_market_data()

    async def load_market_data(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=False)

        if not self._market_region_data or not self._market_region_data.drug_market_data:
            # Corrected: Add a single cell for the message
            table.add_row("No drugs traded in this market currently.") 
            return

        show_trend_icons = "MARKET_INTUITION" in self._player_inventory_data.unlocked_skills
        rows = []
        for drug_name, drug_data_market in sorted(self._market_region_data.drug_market_data.items()): # Use renamed var
            available_qualities = drug_data_market.get("available_qualities", {})
            if not available_qualities:
                row_data = [drug_name, "-", "-", "-", "No qualities listed"]
                if show_trend_icons: row_data.append("-")
                rows.append(row_data)
                continue

            for quality in sorted(available_qualities.keys(), key=lambda q: q.value):
                stock = self._market_region_data.get_available_stock(drug_name, quality) # Use renamed var
                current_buy_price = self._market_region_data.get_buy_price(drug_name, quality) # Use renamed var
                current_sell_price = self._market_region_data.get_sell_price(drug_name, quality) # Use renamed var
                
                trend_icon = "-"
                if show_trend_icons:
                    previous_sell_price = drug_data_market.get("available_qualities", {}).get(quality, {}).get("previous_sell_price", None)
                    if previous_sell_price is not None and current_sell_price > 0 and previous_sell_price > 0:
                        if current_sell_price > previous_sell_price * 1.02: trend_icon = "↑"
                        elif current_sell_price < previous_sell_price * 0.98: trend_icon = "↓"
                        else: trend_icon = "="
                    elif current_sell_price > 0: trend_icon = "?"
                
                event_active_marker = " "
                is_disrupted = False
                for event in self._market_region_data.active_market_events: # Use renamed var
                    if event.target_drug_name == drug_name and event.target_quality == quality:
                        event_active_marker = "*"
                        if event.event_type == "SUPPLY_CHAIN_DISRUPTION": is_disrupted = True
                        break
                
                buy_price_str = f"${current_buy_price:.2f}" if current_buy_price > 0 else "---"
                if is_disrupted and stock == 0 and current_buy_price == 0: buy_price_str = "DISRUPTED"
                
                sell_price_str = f"${current_sell_price:.2f}" if current_sell_price > 0 else "---"
                stock_display = f"{stock}" 
                if is_disrupted: stock_display += " (LOW)" if stock > 0 else " (NONE)"

                row_data = [
                    f"{event_active_marker}{drug_name}", 
                    quality.name, 
                    buy_price_str, 
                    sell_price_str, 
                    stock_display
                ]
                if show_trend_icons: row_data.append(trend_icon)
                rows.append(row_data)
        
        if rows:
            table.add_rows(rows)
        else:
            # This case might not be hit if the initial check handles empty drug_market_data
            # but if it can be, correct it too.
            table.add_row("Market data unavailable.") 

class InventoryView(Widget):
    """A widget to display player inventory."""

    DEFAULT_CSS = """
    InventoryView {
        layout: vertical;
        overflow-y: auto; /* If content might exceed widget bounds */
    }
    DataTable {
        width: 100%;
        height: auto; /* DataTable will manage its own height */
    }
    Static {
        padding: 1 2;
    }
    """

    def __init__(self, player_inventory_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_inventory = player_inventory_data

    def compose(self) -> ComposeResult:
        yield Static(f"Cash: ${self.player_inventory.cash:,.2f} | Capacity: {self.player_inventory.current_load}/{self.player_inventory.max_capacity}", id="inventory_summary_header")
        table = DataTable(id="inventory_table")
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Drug", "Quality", "Quantity")
        yield table
        # Potentially add other summary info like crypto wallet, skills, etc. as Static widgets below the table
        # For now, let's keep it focused on drug inventory.
        # crypto_summary = "\nCrypto Wallet:\n"
        # if self.player_inventory.crypto_wallet:
        #     for coin, amount in self.player_inventory.crypto_wallet.items():
        #         crypto_summary += f"  {coin}: {amount:.4f}\n"
        # else:
        #     crypto_summary += "  Empty\n"
        # yield Static(crypto_summary)

    async def on_mount(self) -> None:
        """Load inventory data into the table when the widget is mounted."""
        await self.load_inventory_data()

    async def load_inventory_data(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=False) # Clear rows but keep columns

        if not self.player_inventory.items:
            # Corrected: Add a single cell for the message
            table.add_row("Inventory is empty.") 
            return

        rows = []
        for drug_name, qualities in sorted(self.player_inventory.items.items()):
            for quality, quantity in sorted(qualities.items(), key=lambda item: item[0].value):
                if quantity > 0:
                    rows.append((drug_name, quality.name, str(quantity)))
        
        if rows:
            table.add_rows(rows)
        else:
            # Corrected: Add a single cell for the message
            table.add_row("Inventory is empty (all quantities zero).") 

class BuyDrugScreen(Screen):
    """A screen for buying drugs."""

    DEFAULT_CSS = """
    BuyDrugScreen {
        align: center middle;
    }

    #main_dialog {
        width: 60;
        height: auto;
        background: $surface;
        padding: 2;
        border: thick $primary-darken-2;
    }

    Label {
        padding: 1 0;
    }

    Input {
        margin-bottom: 1;
        width: 100%;
    }
    
    #buy_drug_buttons {
        width: 100%;
        align-horizontal: right;
        padding-top: 1;
    }

    #buy_drug_buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, current_region_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_region_name = current_region_name

    def compose(self) -> ComposeResult:
        with Vertical(id="main_dialog"):
            yield Label(f"Buy Drug in {self.current_region_name}")
            yield Input(placeholder="Drug Name (e.g., Weed)", id="drug_name")
            yield Input(placeholder="Quality (e.g., STANDARD, PURE, CUT)", id="drug_quality")
            yield Input(placeholder="Quantity (e.g., 10)", id="drug_quantity", type="integer")
            with Horizontal(id="buy_drug_buttons"):
                yield Button("Buy", variant="success", id="buy_submit")
                yield Button("Cancel", variant="error", id="buy_cancel")

    def on_mount(self) -> None:
        self.query_one("#drug_name", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "buy_submit":
            drug_name_input = self.query_one("#drug_name", Input)
            quality_input = self.query_one("#drug_quality", Input)
            quantity_input = self.query_one("#drug_quantity", Input)

            drug_name = drug_name_input.value
            quality_str = quality_input.value.upper()
            quantity_str = quantity_input.value

            # Basic validation
            errors = False
            if not drug_name:
                drug_name_input.border_title = "Required"
                drug_name_input.styles.border = ("heavy", "red")
                errors = True
            else:
                drug_name_input.border_title = None
                drug_name_input.styles.border = None 
            if not quality_str:
                quality_input.border_title = "Required"
                quality_input.styles.border = ("heavy", "red")
                errors = True
            else:
                quality_input.border_title = None
                quality_input.styles.border = None 
            if not quantity_str:
                quantity_input.border_title = "Required"
                quantity_input.styles.border = ("heavy", "red")
                errors = True
            else:
                quantity_input.border_title = None
                quantity_input.styles.border = None 
            
            if errors:
                self.app.bell()
                return

            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    quantity_input.border_title = "Must be > 0"
                    quantity_input.styles.border = ("heavy", "red")
                    self.app.bell()
                    return
                else:
                    quantity_input.border_title = None
                    quantity_input.styles.border = None 
            except ValueError:
                quantity_input.border_title = "Invalid number"
                quantity_input.styles.border = ("heavy", "red")
                self.app.bell()
                return
            
            self.dismiss((drug_name, quality_str, quantity))

        elif event.button.id == "buy_cancel":
            self.dismiss(None)

class SellDrugScreen(Screen):
    """A screen for selling drugs."""

    DEFAULT_CSS = """
    SellDrugScreen {
        align: center middle;
    }
    #main_sell_dialog {
        width: 60;
        height: auto;
        background: $surface;
        padding: 2;
        border: thick $primary-darken-2;
    }
    #main_sell_dialog Label {
        padding: 1 0;
    }
    #main_sell_dialog Input {
        margin-bottom: 1;
        width: 100%;
    }
    #sell_drug_buttons {
        width: 100%;
        align-horizontal: right;
        padding-top: 1;
    }
    #sell_drug_buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, current_region_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_region_name = current_region_name

    def compose(self) -> ComposeResult:
        with Vertical(id="main_sell_dialog"):
            yield Label(f"Sell Drug in {self.current_region_name}")
            yield Input(placeholder="Drug Name (e.g., Weed)", id="drug_name")
            yield Input(placeholder="Quality (e.g., STANDARD, PURE, CUT)", id="drug_quality")
            yield Input(placeholder="Quantity (e.g., 10)", id="drug_quantity", type="integer")
            with Horizontal(id="sell_drug_buttons"):
                yield Button("Sell", variant="success", id="sell_submit")
                yield Button("Cancel", variant="error", id="sell_cancel")

    def on_mount(self) -> None:
        self.query_one("#drug_name", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sell_submit":
            drug_name_input = self.query_one("#drug_name", Input)
            quality_input = self.query_one("#drug_quality", Input)
            quantity_input = self.query_one("#drug_quantity", Input)

            drug_name = drug_name_input.value
            quality_str = quality_input.value.upper()
            quantity_str = quantity_input.value

            errors = False
            if not drug_name:
                drug_name_input.border_title = "Required"
                drug_name_input.styles.border = ("heavy", "red")
                errors = True
            else:
                drug_name_input.border_title = None
                drug_name_input.styles.border = None 
            if not quality_str:
                quality_input.border_title = "Required"
                quality_input.styles.border = ("heavy", "red")
                errors = True
            else:
                quality_input.border_title = None
                quality_input.styles.border = None 
            if not quantity_str:
                quantity_input.border_title = "Required"
                quantity_input.styles.border = ("heavy", "red")
                errors = True
            else:
                quantity_input.border_title = None
                quantity_input.styles.border = None
            
            if errors:
                self.app.bell()
                return

            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    quantity_input.border_title = "Must be > 0"
                    quantity_input.styles.border = ("heavy", "red")
                    self.app.bell()
                    return
                else:
                    quantity_input.border_title = None
                    quantity_input.styles.border = None 
            except ValueError:
                quantity_input.border_title = "Invalid number"
                quantity_input.styles.border = ("heavy", "red")
                self.app.bell()
                return
            
            self.dismiss((drug_name, quality_str, quantity))

        elif event.button.id == "sell_cancel":
            self.dismiss(None)

class TravelView(Widget):
    """A widget to display travel options."""

    DEFAULT_CSS = """
    TravelView {
        padding: 1;
        overflow-y: auto;
    }
    TravelView Button {
        width: 100%;
        margin-bottom: 1;
    }
    TravelView Label {
        padding: 1 0;
        text-style: bold;
    }
    """

    # Define a custom message for when a region is selected for travel
    class RegionSelected(Message):
        def __init__(self, region_id: str) -> None:
            super().__init__()
            self.region_id = region_id

    def __init__(self, current_region_name: str, all_game_regions: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_region_name = current_region_name
        self.all_game_regions = all_game_regions

    def compose(self) -> ComposeResult:
        yield Label(f"Currently in: {self.current_region_name}. Select destination:")
        with Vertical():
            for region_id, region_obj in sorted(self.all_game_regions.items()):
                if region_id != self.current_region_name:
                    yield Button(f"{region_obj.name} (Heat: {region_obj.current_heat})", id=region_id, variant="default")
            yield Button("Cancel Travel", id="cancel_travel", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_travel":
            # Post a message that can be handled by the app to close this view
            # Or, if this view is always transient, the app can just remove it.
            # For now, let's assume the app will handle removing/replacing this view.
            self.post_message(self.RegionSelected("cancel_travel")) 
        elif event.button.id:
            self.post_message(self.RegionSelected(event.button.id))

class SkillsView(Widget):
    """A widget to display and unlock player skills."""

    DEFAULT_CSS = """
    SkillsView {
        padding: 1;
        overflow-y: auto;
    }
    SkillsView Label {
        margin-bottom: 1;
    }
    SkillsView .skill_container {
        border: round $primary-darken-1;
        padding: 1;
        margin-bottom: 1;
    }
    SkillsView .skill_name {
        text-style: bold;
    }
    SkillsView .skill_status {
        color: $success;
    }
    SkillsView Button {
        margin-top: 1;
    }
    """

    # Custom message for when a skill unlock is attempted
    class UnlockSkill(Message):
        def __init__(self, skill_id: str) -> None:
            super().__init__()
            self.skill_id = skill_id

    def __init__(self, player_inventory_data, game_configs_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_inventory = player_inventory_data
        self.game_configs = game_configs_data # To get skill costs, descriptions etc.

    def compose(self) -> ComposeResult:
        yield Label(f"Available Skill Points: {self.player_inventory.skill_points}")
        
        # Market Intuition Skill
        market_intuition_unlocked = "MARKET_INTUITION" in self.player_inventory.unlocked_skills
        with Vertical(classes="skill_container"):
            yield Static("Market Intuition", classes="skill_name")
            yield Static(f"Cost: {self.game_configs.SKILL_MARKET_INTUITION_COST} SP")
            yield Static("Description: See drug price trends in market view.")
            if market_intuition_unlocked:
                yield Static("Status: Unlocked", classes="skill_status")
            else:
                yield Button("Unlock Market Intuition", id="unlock_market_intuition", 
                             variant="success" if self.player_inventory.skill_points >= self.game_configs.SKILL_MARKET_INTUITION_COST else "default",
                             disabled=self.player_inventory.skill_points < self.game_configs.SKILL_MARKET_INTUITION_COST)

        # Digital Footprint Skill
        digital_footprint_unlocked = "DIGITAL_FOOTPRINT" in self.player_inventory.unlocked_skills
        with Vertical(classes="skill_container"):
            yield Static("Digital Footprint", classes="skill_name")
            yield Static(f"Cost: {self.game_configs.SKILL_DIGITAL_FOOTPRINT_COST} SP")
            yield Static(f"Description: Reduce heat from crypto deals by {int(self.game_configs.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT*100)}%.")
            if digital_footprint_unlocked:
                yield Static("Status: Unlocked", classes="skill_status")
            else:
                yield Button("Unlock Digital Footprint", id="unlock_digital_footprint", 
                             variant="success" if self.player_inventory.skill_points >= self.game_configs.SKILL_DIGITAL_FOOTPRINT_COST else "default",
                             disabled=self.player_inventory.skill_points < self.game_configs.SKILL_DIGITAL_FOOTPRINT_COST)
        
        # Add more skills here following the same pattern

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "unlock_market_intuition":
            self.post_message(self.UnlockSkill("MARKET_INTUITION"))
        elif event.button.id == "unlock_digital_footprint":
            self.post_message(self.UnlockSkill("DIGITAL_FOOTPRINT"))

class UpgradesView(Widget):
    """A widget to display and purchase player upgrades."""

    DEFAULT_CSS = """
    UpgradesView {
        padding: 1;
        overflow-y: auto;
    }
    UpgradesView Label {
        margin-bottom: 1;
    }
    UpgradesView .upgrade_container {
        border: round $primary-darken-1;
        padding: 1;
        margin-bottom: 1;
    }
    UpgradesView .upgrade_name {
        text-style: bold;
    }
    UpgradesView .upgrade_status {
        color: $success;
    }
    UpgradesView Button {
        margin-top: 1;
    }
    """

    class PurchaseUpgrade(Message):
        def __init__(self, upgrade_id: str) -> None:
            super().__init__()
            self.upgrade_id = upgrade_id

    def __init__(self, player_inventory_data, game_configs_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_inventory = player_inventory_data
        self.game_configs = game_configs_data

    def compose(self) -> ComposeResult:
        yield Label(f"Available Cash: ${self.player_inventory.cash:,.2f}")

        # Capacity Upgrade
        with Vertical(classes="upgrade_container"):
            current_capacity_cost = self.game_configs.CAPACITY_UPGRADE_COST_INITIAL * \
                                  (self.game_configs.CAPACITY_UPGRADE_COST_MULTIPLIER ** self.player_inventory.capacity_upgrades_purchased)
            yield Static("Carrying Capacity", classes="upgrade_name")
            yield Static(f"Current: {self.player_inventory.max_capacity} units (Upgrades purchased: {self.player_inventory.capacity_upgrades_purchased})")
            yield Static(f"Increase by: {self.game_configs.CAPACITY_UPGRADE_AMOUNT} units")
            yield Static(f"Cost: ${current_capacity_cost:,.2f}")
            yield Button("Upgrade Capacity", id="upgrade_capacity", 
                         variant="success" if self.player_inventory.cash >= current_capacity_cost else "default",
                         disabled=self.player_inventory.cash < current_capacity_cost)

        # Secure Phone Upgrade
        secure_phone_owned = self.player_inventory.has_secure_phone
        with Vertical(classes="upgrade_container"):
            yield Static("Secure Phone", classes="upgrade_name")
            yield Static(f"Cost: ${self.game_configs.SECURE_PHONE_COST:,.2f}")
            yield Static(f"Description: Reduce heat from crypto deals by {int(self.game_configs.SECURE_PHONE_HEAT_REDUCTION_PERCENT*100)}%. Stacks with Digital Footprint.")
            if secure_phone_owned:
                yield Static("Status: Purchased", classes="upgrade_status")
            else:
                yield Button("Purchase Secure Phone", id="purchase_secure_phone",
                             variant="success" if self.player_inventory.cash >= self.game_configs.SECURE_PHONE_COST else "default",
                             disabled=self.player_inventory.cash < self.game_configs.SECURE_PHONE_COST)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "upgrade_capacity":
            self.post_message(self.PurchaseUpgrade("CAPACITY"))
        elif event.button.id == "purchase_secure_phone":
            self.post_message(self.PurchaseUpgrade("SECURE_PHONE"))

class TechContactView(Widget):
    """A widget for interacting with the Tech Contact."""

    DEFAULT_CSS = """
    TechContactView {
        padding: 1;
        overflow-y: auto;
    }
    TechContactView > Vertical > Label {
        margin-bottom: 1;
        text-style: bold;
    }
    TechContactView Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    # Custom message for when a tech contact action is selected
    class TechActionSelected(Message):
        def __init__(self, action_id: str) -> None:
            super().__init__()
            self.action_id = action_id

    def __init__(self, player_inventory_data, game_configs_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_inventory = player_inventory_data
        self.game_configs = game_configs_data
        # We might need current crypto prices here too, passed from the app

    def compose(self) -> ComposeResult:
        yield Label("Tech Contact Terminal")
        with Vertical():
            yield Label(f"Cash: ${self.player_inventory.cash:,.2f}")
            # Display crypto wallet summary
            crypto_summary = "Your Crypto Wallet:\n"
            if self.player_inventory.crypto_wallet or self.player_inventory.staked_dc > 0:
                for coin_symbol in ["DC", "VC", "SC"]:
                    if coin_symbol in self.player_inventory.crypto_wallet:
                        crypto_summary += f"  - Wallet {coin_symbol}: {self.player_inventory.crypto_wallet[coin_symbol]:.4f}\n"
                if self.player_inventory.staked_dc > 0:
                    crypto_summary += f"  - Staked DC: {self.player_inventory.staked_dc:.4f}\n"
            else:
                crypto_summary += "  - Empty\n"
            yield Static(crypto_summary)

            if self.player_inventory.pending_laundered_sc_arrival_day is not None:
                yield Static(f"Laundering: {self.player_inventory.pending_laundered_sc:.4f} SC arriving Day {self.player_inventory.pending_laundered_sc_arrival_day}", classes="warning")

            yield Button("Buy Crypto", id="buy_crypto", variant="default")
            yield Button("Sell Crypto", id="sell_crypto", variant="default")
            yield Button("Launder Cash", id="launder_cash", variant="default", 
                         disabled=(self.player_inventory.pending_laundered_sc_arrival_day is not None))
            yield Button("Stake DC", id="stake_dc", variant="default")
            yield Button("Unstake DC", id="unstake_dc", variant="default")
            
            ghost_access_unlocked = "GHOST_NETWORK_ACCESS" in self.player_inventory.unlocked_skills
            if not ghost_access_unlocked:
                yield Button(f"Purchase Ghost Network Access ({self.game_configs.GHOST_NETWORK_ACCESS_COST_DC:.2f} DC)", 
                             id="purchase_ghost_access", variant="warning")
            else:
                yield Static("Ghost Network Access: UNLOCKED", classes="success")
                # Potentially add a button to go to Crypto-Only shop if it's a separate screen/view
                # For now, Ghost Network Access just enables the shop via main menu binding

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id:
            self.post_message(self.TechActionSelected(event.button.id))

class LaunderCashScreen(Screen):
    """A screen for laundering cash."""

    DEFAULT_CSS = """
    LaunderCashScreen {
        align: center middle;
    }
    #launder_dialog {
        width: 60;
        height: auto;
        background: $surface;
        padding: 2;
        border: thick $primary-darken-2;
    }
    #launder_dialog Label {
        padding: 1 0;
    }
    #launder_dialog Input {
        margin-bottom: 1;
        width: 100%;
    }
    #launder_buttons {
        width: 100%;
        align-horizontal: right;
        padding-top: 1;
    }
    #launder_buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, current_cash: float, fee_percent: float, delay_days: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_cash = current_cash
        self.fee_percent = fee_percent
        self.delay_days = delay_days

    def compose(self) -> ComposeResult:
        with Vertical(id="launder_dialog"):
            yield Label("Launder Cash to StableCoin (SC)")
            yield Static(f"Available Cash: ${self.current_cash:,.2f}")
            yield Static(f"Laundering Fee: {self.fee_percent*100:.0f}%")
            yield Static(f"Delay: {self.delay_days} days for SC to arrive.")
            yield Input(placeholder="Amount of cash to launder", id="launder_amount", type="number")
            with Horizontal(id="launder_buttons"):
                yield Button("Launder", variant="success", id="launder_submit")
                yield Button("Cancel", variant="error", id="launder_cancel")

    def on_mount(self) -> None:
        self.query_one("#launder_amount", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launder_submit":
            amount_input_widget = self.query_one("#launder_amount", Input)
            amount_str = amount_input_widget.value

            if not amount_str:
                amount_input_widget.border_title = "Required"
                amount_input_widget.styles.border = ("heavy", "red")
                self.app.bell()
                return
            try:
                amount_to_launder = float(amount_str)
                if amount_to_launder <= 0:
                    amount_input_widget.border_title = "Must be > 0"
                    amount_input_widget.styles.border = ("heavy", "red")
                    self.app.bell()
                    return
                if amount_to_launder > self.current_cash:
                    amount_input_widget.border_title = "Not enough cash"
                    amount_input_widget.styles.border = ("heavy", "red")
                    self.app.bell()
                    return
                amount_input_widget.border_title = None
                amount_input_widget.styles.border = None
            except ValueError:
                amount_input_widget.border_title = "Invalid amount"
                amount_input_widget.styles.border = ("heavy", "red")
                self.app.bell()
                return
            
            self.dismiss(amount_to_launder)

        elif event.button.id == "launder_cancel":
            self.dismiss(None)

class BuyCryptoScreen(Screen):
    """A screen for buying cryptocurrency."""

    DEFAULT_CSS = """
    BuyCryptoScreen {
        align: center middle;
    }

    #crypto_buy_dialog {
        width: 60;
        height: auto;
        background: $surface;
        padding: 2;
        border: thick $primary-darken-2;
    }

    #crypto_buy_dialog Label {
        padding: 1 0;
    }

    #crypto_buy_dialog Input {
        margin-bottom: 1;
        width: 100%;
    }

    #crypto_buy_dialog .info {
        color: $text-muted;
        padding: 0 1;
    }

    #crypto_buy_dialog .warning {
        color: $warning;
        background: $warning-background-lighten-2;
        padding: 1;
        border: round $warning;
    }

    #crypto_buy_buttons {
        width: 100%;
        align-horizontal: right;
        padding-top: 1;
    }

    #crypto_buy_buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, current_cash: float, crypto_prices: dict, tech_fee_percent: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_cash = current_cash
        self.crypto_prices = crypto_prices
        self.tech_fee_percent = tech_fee_percent

    def compose(self) -> ComposeResult:
        with Vertical(id="crypto_buy_dialog"):
            yield Label("Buy Cryptocurrency")
            yield Static(f"Available Cash: ${self.current_cash:,.2f}")
            yield Static(f"Transaction Fee: {self.tech_fee_percent*100:.1f}%")
            
            # Market prices section
            market_info = "Current Market Prices:\n"
            for coin, price in sorted(self.crypto_prices.items()):
                market_info += f"  - {coin}: ${price:.2f}/unit\n"
            yield Static(market_info, classes="info")
            
            yield Input(placeholder="Coin Symbol (e.g., DC, VC, SC)", id="coin_symbol")
            yield Input(placeholder="Amount to buy (e.g., 1.5)", id="crypto_amount", type="number")
            
            with Horizontal(id="crypto_buy_buttons"):
                yield Button("Buy", variant="success", id="crypto_buy_submit")
                yield Button("Cancel", variant="error", id="crypto_buy_cancel")

    def on_mount(self) -> None:
        self.query_one("#coin_symbol", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "crypto_buy_submit":
            coin_symbol_input = self.query_one("#coin_symbol", Input)
            amount_input = self.query_one("#crypto_amount", Input)

            coin_symbol = coin_symbol_input.value.upper()
            amount_str = amount_input.value

            errors = False
            # Validate coin symbol
            if not coin_symbol:
                coin_symbol_input.border_title = "Required"
                coin_symbol_input.styles.border = ("heavy", "red")
                errors = True
            elif coin_symbol not in self.crypto_prices:
                coin_symbol_input.border_title = "Invalid coin"
                coin_symbol_input.styles.border = ("heavy", "red")
                errors = True
            else:
                coin_symbol_input.border_title = None
                coin_symbol_input.styles.border = None

            # Validate amount
            if not amount_str:
                amount_input.border_title = "Required"
                amount_input.styles.border = ("heavy", "red")
                errors = True
            else:
                try:
                    amount = float(amount_str)
                    if amount <= 1e-4:  # Minimum amount check
                        amount_input.border_title = "Amount too small"
                        amount_input.styles.border = ("heavy", "red")
                        errors = True
                    else:
                        coin_price = self.crypto_prices[coin_symbol]
                        sub_total = amount * coin_price
                        fee = sub_total * self.tech_fee_percent
                        total_cost = sub_total + fee

                        if total_cost > self.current_cash:
                            amount_input.border_title = f"Need ${total_cost:,.2f}"
                            amount_input.styles.border = ("heavy", "red")
                            errors = True
                        else:
                            amount_input.border_title = None
                            amount_input.styles.border = None
                except ValueError:
                    amount_input.border_title = "Invalid number"
                    amount_input.styles.border = ("heavy", "red")
                    errors = True

            if errors:
                self.app.bell()
                return

            self.dismiss((coin_symbol, float(amount_str)))

        elif event.button.id == "crypto_buy_cancel":
            self.dismiss(None)
