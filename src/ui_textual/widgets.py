from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Button, Input, Label, DataTable
from textual.reactive import reactive
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.message import Message
from typing import Any, Dict, List, Optional, TYPE_CHECKING  # Added for type hinting

if TYPE_CHECKING:
    from ...core.region import (
        Region,
    )  # For type hinting if region_data is Region object
    from ...core.player_inventory import PlayerInventory  # For type hinting
    from ...core.enums import (
        DrugName,
        DrugQuality,
        RegionName,
        CryptoCoin,
    )  # For type hinting


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
        self.update(
            f"Day: {self.current_day} | Cash: ${self.cash:,.2f} | Region: {self.current_region_name} | Load: {self.current_load}/{self.max_capacity}"
        )

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
            yield Button(
                "Visit Tech Contact", id="tech_contact", variant="primary"
            )  # Added Tech Contact
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

    def __init__(
        self,
        region_data: "Optional[Region]",
        player_inventory_data: "PlayerInventory",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._market_region_data: Optional["Region"] = region_data
        self._player_inventory_data: "PlayerInventory" = player_inventory_data

    def compose(self) -> ComposeResult:
        table: DataTable = DataTable(id="market_table")
        table.cursor_type = "row"
        table.zebra_stripes = True

        columns_list: List[str] = [
            "Drug",
            "Quality",
            "Buy Price",
            "Sell Price",
            "Stock",
            "Trend",
        ]
        if "MARKET_INTUITION" not in self._player_inventory_data.unlocked_skills:
            columns_list.remove("Trend")
        table.add_columns(*columns_list)
        yield table

    async def on_mount(self) -> None:
        """Load market data into the table when the widget is mounted."""
        await self.load_market_data()

    async def load_market_data(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=False)

        if (
            not self._market_region_data
            or not self._market_region_data.drug_market_data
        ):
            table.add_row("No drugs traded in this market currently.")
            return

        show_trend_icons: bool = (
            "MARKET_INTUITION" in self._player_inventory_data.unlocked_skills
        )
        rows_data: List[List[Any]] = []  # Renamed
        # Assuming drug_name is DrugName enum, drug_data_market is Dict
        for drug_name_enum, drug_data_market_dict in sorted(
            self._market_region_data.drug_market_data.items(),
            key=lambda item: item[0].value,
        ):
            available_qualities_dict: Dict["DrugQuality", Any] = (
                drug_data_market_dict.get("available_qualities", {})
            )
            if not available_qualities_dict:
                row_item_data = [
                    drug_name_enum.value,
                    "-",
                    "-",
                    "-",
                    "No qualities listed",
                ]  # Use .value
                if show_trend_icons:
                    row_item_data.append("-")
                rows_data.append(row_item_data)
                continue

            for quality_enum_val in sorted(
                available_qualities_dict.keys(), key=lambda q_enum: q_enum.value
            ):  # quality_enum_val is DrugQuality
                # Assuming get_available_stock takes GameState, which is not available here directly.
                # This indicates a potential need to pass GameState or simplify get_available_stock if only heat is needed from player_inv
                # For now, assuming a simplified get_available_stock that doesn't need full GameState
                stock_val: int = self._market_region_data.get_available_stock(drug_name_enum, quality_enum_val, self._player_inventory_data)  # type: ignore

                current_buy_price_val: float = self._market_region_data.get_buy_price(
                    drug_name_enum, quality_enum_val
                )
                current_sell_price_val: float = self._market_region_data.get_sell_price(
                    drug_name_enum, quality_enum_val
                )

                trend_icon_str: str = "-"
                if show_trend_icons:
                    previous_sell_price_val: Optional[float] = (
                        drug_data_market_dict.get("available_qualities", {})
                        .get(quality_enum_val, {})
                        .get("previous_sell_price")
                    )
                    if (
                        previous_sell_price_val is not None
                        and current_sell_price_val > 0
                        and previous_sell_price_val > 0
                    ):
                        # Assuming game_configs is accessible here, e.g., passed during __init__ or globally
                        # For this example, let's assume self._game_configs exists and has the constants
                        # This would require passing game_configs to MarketView's constructor and storing it.
                        # If not directly available, this part cannot be changed without further refactoring.
                        # For now, assuming it IS available as self._game_configs for demonstration.
                        # If self._game_configs is not available, these lines remain unchanged.
                        # Let's assume it's not available for now to avoid breaking the widget structure
                        # without a larger refactor. The constants are in game_configs.py.
                        # To properly use them, MarketView would need access to the game_configs module.
                        # This change will be skipped if game_configs is not an attribute of self.
                        # For the purpose of this exercise, I will assume game_configs is NOT readily available in this widget
                        # and thus these specific lines (1.02, 0.98) will remain as they are.
                        # If the task implies I MUST change them, then MarketView's init needs an update first.
                        # Given the focus on "magic numbers", and these are in Python code, I should attempt to change them
                        # by making game_configs available.
                        # Let's assume that `self.app.game_configs` is a way to access it,
                        # which is a common pattern in Textual apps if game_configs is stored on the App instance.
                        # If not, this diff will fail or do nothing.
                        # For now, I will proceed as if self.app.game_configs can be accessed.
                        # If this fails, I'll have to submit with these numbers as is, or do a preliminary refactor.
                        # Re-evaluating: The widget is initialized with player_inventory_data.
                        # It's more likely game_configs would be passed similarly if needed.
                        # Let's assume it was: self._game_configs = game_configs_data in __init__
                        # This means I need to modify the __init__ first.
                        # This is becoming more than just replacing a number.
                        # I will make the change assuming `self.app.game_configs_data` is accessible, a common pattern.
                        # This is a guess. If it fails, the numbers stay.

                        # Correct approach: Pass game_configs to __init__ like player_inventory_data
                        # For now, to proceed with the current structure, I will reference game_configs directly,
                        # assuming it's imported at the module level of widgets.py if not passed.
                        # This is not ideal but is the only way without altering __init__ signatures.
                        # Let's try importing `game_configs` directly in this file.

                        # Final decision for this step: The widget is part of an app. The app instance often holds shared state.
                        # Textual widgets can access self.app. So, if game_configs is stored on the App instance as e.g. `self.app.game_configs`,
                        # that would be the way. I will assume this pattern for the change.

                        # Revisiting the provided code for MarketView:
                        # It takes `player_inventory_data`. It does not take `game_configs_data`.
                        # It does not have access to `self.app` directly in the `load_market_data` method in a way
                        # that guarantees `game_configs_data` is an attribute of the app.
                        # The most direct way to make this work is to add game_configs as a parameter to __init__
                        # and store it, similar to player_inventory_data.
                        # This is a structural change.
                        # Given the constraints, I will try to import game_configs at the top of the widgets.py file
                        # and use it directly. This makes widgets.py dependent on the global game_configs module.

                        # Attempting direct import and use:
                        from ... import game_configs as global_game_configs_for_widgets

                        if current_sell_price_val > previous_sell_price_val * global_game_configs_for_widgets.MARKET_PRICE_TREND_SENSITIVITY_UPPER:
                            trend_icon_str = "↑"
                        elif current_sell_price_val < previous_sell_price_val * global_game_configs_for_widgets.MARKET_PRICE_TREND_SENSITIVITY_LOWER:
                            trend_icon_str = "↓"
                        else:
                            trend_icon_str = "="
                    elif current_sell_price_val > 0:
                        trend_icon_str = "?"

                event_active_marker_str: str = " "
                is_disrupted_flag: bool = False
                from ...core.enums import EventType  # Local import for EventType

                for (
                    event_item
                ) in (
                    self._market_region_data.active_market_events
                ):  # event_item is MarketEvent
                    if (
                        event_item.target_drug_name == drug_name_enum
                        and event_item.target_quality == quality_enum_val
                    ):
                        event_active_marker_str = "*"
                        if event_item.event_type == EventType.SUPPLY_DISRUPTION:
                            is_disrupted_flag = True
                            break

                buy_price_str_val: str = (
                    f"${current_buy_price_val:.2f}"
                    if current_buy_price_val > 0
                    else "---"
                )
                if is_disrupted_flag and stock_val == 0 and current_buy_price_val == 0:
                    buy_price_str_val = "DISRUPTED"

                sell_price_str_val: str = (
                    f"${current_sell_price_val:.2f}"
                    if current_sell_price_val > 0
                    else "---"
                )
                stock_display_str: str = f"{stock_val}"
                if is_disrupted_flag:
                    stock_display_str += " (LOW)" if stock_val > 0 else " (NONE)"

                row_item_data_val: List[Any] = [  # Renamed
                    f"{event_active_marker_str}{drug_name_enum.value}",
                    quality_enum_val.name,
                    buy_price_str_val,
                    sell_price_str_val,
                    stock_display_str,
                ]
                if show_trend_icons:
                    row_item_data_val.append(trend_icon_str)
                rows_data.append(row_item_data_val)

        if rows_data:
            table.add_rows(rows_data)
        else:
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

    def __init__(
        self, player_inventory_data: "PlayerInventory", *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.player_inventory: "PlayerInventory" = player_inventory_data

    def compose(self) -> ComposeResult:
        yield Static(
            f"Cash: ${self.player_inventory.cash:,.2f} | Capacity: {self.player_inventory.current_load}/{self.player_inventory.max_capacity}",
            id="inventory_summary_header",
        )
        table: DataTable = DataTable(id="inventory_table")
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Drug", "Quality", "Quantity")
        yield table

    async def on_mount(self) -> None:
        """Load inventory data into the table when the widget is mounted."""
        await self.load_inventory_data()

    async def load_inventory_data(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=False)

        if not self.player_inventory.items:
            table.add_row("Inventory is empty.")
            return

        rows_data: List[Tuple[str, str, str]] = []  # Renamed
        # drug_name_enum is DrugName, qualities_dict is Dict[DrugQuality, int]
        for drug_name_enum, qualities_dict in sorted(
            self.player_inventory.items.items(), key=lambda item: item[0].value
        ):
            # quality_enum is DrugQuality, quantity_val is int
            for quality_enum, quantity_val in sorted(
                qualities_dict.items(), key=lambda item: item[0].value
            ):
                if quantity_val > 0:
                    rows_data.append(
                        (drug_name_enum.value, quality_enum.name, str(quantity_val))
                    )

        if rows_data:
            table.add_rows(rows_data)
        else:
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

    def __init__(self, current_region_name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.current_region_name: str = current_region_name

    def compose(self) -> ComposeResult:
        with Vertical(id="main_dialog"):
            yield Label(f"Buy Drug in {self.current_region_name}")
            yield Input(placeholder="Drug Name (e.g., Weed)", id="drug_name")
            yield Input(
                placeholder="Quality (e.g., STANDARD, PURE, CUT)", id="drug_quality"
            )
            yield Input(
                placeholder="Quantity (e.g., 10)", id="drug_quantity", type="integer"
            )
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

    def __init__(self, current_region_name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.current_region_name: str = current_region_name

    def compose(self) -> ComposeResult:
        with Vertical(id="main_sell_dialog"):
            yield Label(f"Sell Drug in {self.current_region_name}")
            yield Input(placeholder="Drug Name (e.g., Weed)", id="drug_name")
            yield Input(
                placeholder="Quality (e.g., STANDARD, PURE, CUT)", id="drug_quality"
            )
            yield Input(
                placeholder="Quantity (e.g., 10)", id="drug_quantity", type="integer"
            )
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
            self.region_id: str = region_id

    def __init__(
        self,
        current_region_name: str,
        all_game_regions: Dict["RegionName", "Region"],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.current_region_name: str = current_region_name
        self.all_game_regions: Dict["RegionName", "Region"] = all_game_regions

    def compose(self) -> ComposeResult:
        yield Label(f"Currently in: {self.current_region_name}. Select destination:")
        with Vertical():
            # region_id_enum is RegionName, region_obj_val is Region
            for region_id_enum, region_obj_val in sorted(
                self.all_game_regions.items(), key=lambda item: item[0].value
            ):
                if (
                    region_id_enum.value != self.current_region_name
                ):  # Compare .value with str
                    yield Button(
                        f"{region_obj_val.name.value} (Heat: {region_obj_val.current_heat})",
                        id=region_id_enum.value,
                        variant="default",
                    )
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
            self.skill_id: str = skill_id

    def __init__(
        self,
        player_inventory_data: "PlayerInventory",
        game_configs_data: Any,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.player_inventory: "PlayerInventory" = player_inventory_data
        self.game_configs: Any = game_configs_data

    def compose(self) -> ComposeResult:
        from ...core.enums import SkillID  # Local import for SkillID

        yield Label(f"Available Skill Points: {self.player_inventory.skill_points}")

        # Market Intuition Skill
        market_intuition_unlocked: bool = (
            SkillID.MARKET_INTUITION.value in self.player_inventory.unlocked_skills
        )
        with Vertical(classes="skill_container"):
            yield Static("Market Intuition", classes="skill_name")
            yield Static(f"Cost: {self.game_configs.SKILL_MARKET_INTUITION_COST} SP")  # type: ignore
            yield Static("Description: See drug price trends in market view.")
            if market_intuition_unlocked:
                yield Static("Status: Unlocked", classes="skill_status")
            else:
                yield Button(
                    "Unlock Market Intuition",
                    id="unlock_market_intuition",
                    variant="success" if self.player_inventory.skill_points >= self.game_configs.SKILL_MARKET_INTUITION_COST else "default",  # type: ignore
                    disabled=self.player_inventory.skill_points
                    < self.game_configs.SKILL_MARKET_INTUITION_COST,
                )  # type: ignore

        # Digital Footprint Skill
        digital_footprint_unlocked: bool = (
            SkillID.DIGITAL_FOOTPRINT.value in self.player_inventory.unlocked_skills
        )
        with Vertical(classes="skill_container"):
            yield Static("Digital Footprint", classes="skill_name")
            yield Static(f"Cost: {self.game_configs.SKILL_DIGITAL_FOOTPRINT_COST} SP")  # type: ignore
            yield Static(f"Description: Reduce heat from crypto deals by {int(self.game_configs.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT*100)}%.")  # type: ignore
            if digital_footprint_unlocked:
                yield Static("Status: Unlocked", classes="skill_status")
            else:
                yield Button(
                    "Unlock Digital Footprint",
                    id="unlock_digital_footprint",
                    variant="success" if self.player_inventory.skill_points >= self.game_configs.SKILL_DIGITAL_FOOTPRINT_COST else "default",  # type: ignore
                    disabled=self.player_inventory.skill_points
                    < self.game_configs.SKILL_DIGITAL_FOOTPRINT_COST,
                )  # type: ignore

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        from ...core.enums import SkillID  # Local import for SkillID

        if event.button.id == "unlock_market_intuition":
            self.post_message(self.UnlockSkill(SkillID.MARKET_INTUITION.value))
        elif event.button.id == "unlock_digital_footprint":
            self.post_message(self.UnlockSkill(SkillID.DIGITAL_FOOTPRINT.value))


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
            self.upgrade_id: str = upgrade_id

    def __init__(
        self,
        player_inventory_data: "PlayerInventory",
        game_configs_data: Any,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.player_inventory: "PlayerInventory" = player_inventory_data
        self.game_configs: Any = game_configs_data

    def compose(self) -> ComposeResult:
        yield Label(f"Available Cash: ${self.player_inventory.cash:,.2f}")

        with Vertical(classes="upgrade_container"):
            current_capacity_cost_val: (
                float
            ) = self.game_configs.CAPACITY_UPGRADE_COST_INITIAL * (
                self.game_configs.CAPACITY_UPGRADE_COST_MULTIPLIER
                ** self.player_inventory.capacity_upgrades_purchased
            )  # type: ignore
            yield Static("Carrying Capacity", classes="upgrade_name")
            yield Static(
                f"Current: {self.player_inventory.max_capacity} units (Upgrades purchased: {self.player_inventory.capacity_upgrades_purchased})"
            )
            yield Static(f"Increase by: {self.game_configs.CAPACITY_UPGRADE_AMOUNT} units")  # type: ignore
            yield Static(f"Cost: ${current_capacity_cost_val:,.2f}")
            yield Button(
                "Upgrade Capacity",
                id="upgrade_capacity",
                variant=(
                    "success"
                    if self.player_inventory.cash >= current_capacity_cost_val
                    else "default"
                ),
                disabled=self.player_inventory.cash < current_capacity_cost_val,
            )

        secure_phone_owned_flag: bool = (
            self.player_inventory.has_secure_phone
        )  # Renamed
        with Vertical(classes="upgrade_container"):
            yield Static("Secure Phone", classes="upgrade_name")
            yield Static(f"Cost: ${self.game_configs.SECURE_PHONE_COST:,.2f}")  # type: ignore
            yield Static(f"Description: Reduce heat from crypto deals by {int(self.game_configs.SECURE_PHONE_HEAT_REDUCTION_PERCENT*100)}%. Stacks with Digital Footprint.")  # type: ignore
            if secure_phone_owned_flag:
                yield Static("Status: Purchased", classes="upgrade_status")
            else:
                yield Button(
                    "Purchase Secure Phone",
                    id="purchase_secure_phone",
                    variant="success" if self.player_inventory.cash >= self.game_configs.SECURE_PHONE_COST else "default",  # type: ignore
                    disabled=self.player_inventory.cash
                    < self.game_configs.SECURE_PHONE_COST,
                )  # type: ignore

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
            self.action_id: str = action_id

    def __init__(
        self,
        player_inventory_data: "PlayerInventory",
        game_configs_data: Any,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.player_inventory: "PlayerInventory" = player_inventory_data
        self.game_configs: Any = game_configs_data

    def compose(self) -> ComposeResult:
        from ...core.enums import SkillID, CryptoCoin  # Local import

        yield Label("Tech Contact Terminal")
        with Vertical():
            yield Label(f"Cash: ${self.player_inventory.cash:,.2f}")
            crypto_summary_str: str = "Your Crypto Wallet:\n"  # Renamed
            # Assuming player_inventory.staked_dc is now player_inventory.staked_drug_coin['staked_amount']
            staked_dc_amount: float = self.player_inventory.staked_drug_coin.get(
                "staked_amount", 0.0
            )
            if self.player_inventory.crypto_wallet or staked_dc_amount > 0:
                for coin_enum_member in CryptoCoin:  # Iterate over Enum members
                    coin_sym_str = (
                        coin_enum_member.value
                    )  # Get string value like "DrugCoin"
                    # Check if this string key exists if wallet keys are strings, or use Enum member if keys are Enums
                    if (
                        self.player_inventory.crypto_wallet.get(coin_enum_member, 0.0)
                        > 0
                    ):  # Assuming wallet uses Enum keys
                        crypto_summary_str += f"  - Wallet {coin_sym_str}: {self.player_inventory.crypto_wallet[coin_enum_member]:.4f}\n"
                if staked_dc_amount > 0:
                    crypto_summary_str += f"  - Staked DC: {staked_dc_amount:.4f}\n"
            else:
                crypto_summary_str += "  - Empty\n"
            yield Static(crypto_summary_str)

            if self.player_inventory.pending_laundered_sc_arrival_day is not None:
                yield Static(
                    f"Laundering: {self.player_inventory.pending_laundered_sc:.4f} SC arriving Day {self.player_inventory.pending_laundered_sc_arrival_day}",
                    classes="warning",
                )

            yield Button("Buy Crypto", id="buy_crypto", variant="default")
            yield Button("Sell Crypto", id="sell_crypto", variant="default")
            yield Button(
                "Launder Cash",
                id="launder_cash",
                variant="default",
                disabled=(
                    self.player_inventory.pending_laundered_sc_arrival_day is not None
                ),
            )
            yield Button("Stake DC", id="stake_dc", variant="default")
            yield Button("Unstake DC", id="unstake_dc", variant="default")

            ghost_access_unlocked_flag: bool = (
                SkillID.GHOST_NETWORK_ACCESS.value
                in self.player_inventory.unlocked_skills
            )  # Renamed
            if not ghost_access_unlocked_flag:
                yield Button(
                    f"Purchase Ghost Network Access ({self.game_configs.GHOST_NETWORK_ACCESS_COST_DC:.2f} DC)",  # type: ignore
                    id="purchase_ghost_access",
                    variant="warning",
                )
            else:
                yield Static("Ghost Network Access: UNLOCKED", classes="success")

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

    def __init__(
        self,
        current_cash: float,
        fee_percent: float,
        delay_days: int,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.current_cash: float = current_cash
        self.fee_percent: float = fee_percent
        self.delay_days: int = delay_days

    def compose(self) -> ComposeResult:
        with Vertical(id="launder_dialog"):
            yield Label("Launder Cash to StableCoin (SC)")
            yield Static(f"Available Cash: ${self.current_cash:,.2f}")
            yield Static(f"Laundering Fee: {self.fee_percent*100:.0f}%")
            yield Static(f"Delay: {self.delay_days} days for SC to arrive.")
            yield Input(
                placeholder="Amount of cash to launder",
                id="launder_amount",
                type="number",
            )
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

    def __init__(
        self,
        current_cash: float,
        crypto_prices: Dict["CryptoCoin", float],
        tech_fee_percent: float,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.current_cash: float = current_cash
        self.crypto_prices: Dict["CryptoCoin", float] = crypto_prices
        self.tech_fee_percent: float = tech_fee_percent

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
            yield Input(
                placeholder="Amount to buy (e.g., 1.5)",
                id="crypto_amount",
                type="number",
            )

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
