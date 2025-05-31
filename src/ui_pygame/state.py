"""
State and global variables for Project Narco-Syndicate Pygame UI.
Split from app.py for modularity.
"""
from typing import Optional, Dict, List, Any
from .ui_components import Button
from ..core.enums import DrugName, DrugQuality, RegionName, CryptoCoin
from ..core.player_inventory import PlayerInventory
from ..core.region import Region

# --- Game State & UI Variables ---
current_view: str = "main_menu"
main_menu_buttons: List[Button] = []
market_view_buttons: List[Button] = []
market_buy_sell_buttons: List[Button] = []
inventory_view_buttons: List[Button] = []
travel_view_buttons: List[Button] = []
tech_contact_view_buttons: List[Button] = []
skills_view_buttons: List[Button] = []
upgrades_view_buttons: List[Button] = []
transaction_input_buttons: List[Button] = []
blocking_event_popup_buttons: List[Button] = []
game_over_buttons: List[Button] = []
informant_view_buttons: List[Button] = []

current_transaction_type: Optional[str] = None
drug_for_transaction: Optional[DrugName] = None
quality_for_transaction: Optional[DrugQuality] = None
price_for_transaction: float = 0.0
available_for_transaction: int = 0
quantity_input_string: str = ""
input_box_rect = None  # Will be set in UI setup

tech_transaction_in_progress: Optional[str] = None
coin_for_tech_transaction: Optional[CryptoCoin] = None
tech_input_string: str = ""
tech_input_box_rect = None  # Will be set in UI setup

active_prompt_message: Optional[str] = None
prompt_message_timer: int = 0

active_blocking_event_data: Optional[Dict] = None
game_over_message: Optional[str] = None

game_state_data_cache: Optional[Any] = None
game_configs_data_cache: Optional[Any] = None
player_inventory_cache: Optional[PlayerInventory] = None
