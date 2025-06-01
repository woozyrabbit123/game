from typing import Optional, Dict, List, Any
from ..core.enums import DrugName, DrugQuality, CryptoCoin
# Forward import Button if needed, or use 'Button' as string hint
# from .ui_components import Button # This might cause circular if Button needs UIManager

class UIManager:
    def __init__(self):
        self.current_view: str = "main_menu"

        # UI Element State
        self.main_menu_buttons: List[Any] = [] # Use Any for Button if import is tricky
        self.market_view_buttons: List[Any] = []
        self.market_buy_sell_buttons: List[Any] = []
        self.inventory_view_buttons: List[Any] = []
        self.travel_view_buttons: List[Any] = []
        self.tech_contact_view_buttons: List[Any] = []
        self.skills_view_buttons: List[Any] = []
        self.upgrades_view_buttons: List[Any] = []
        self.transaction_input_buttons: List[Any] = []
        self.blocking_event_popup_buttons: List[Any] = []
        self.game_over_buttons: List[Any] = []
        self.informant_view_buttons: List[Any] = []
        self.active_buttons_list_current_view: List[Any] = []

        # Transaction States
        self.current_transaction_type: Optional[str] = None
        self.drug_for_transaction: Optional[DrugName] = None
        self.quality_for_transaction: Optional[DrugQuality] = None
        self.price_for_transaction: float = 0.0
        self.available_for_transaction: int = 0
        self.quantity_input_string: str = ""

        # Tech Contact States
        self.tech_transaction_in_progress: Optional[str] = None
        self.coin_for_tech_transaction: Optional[CryptoCoin] = None
        self.tech_input_string: str = ""

        # UI Feedback & Popups
        self.active_prompt_message: Optional[str] = None
        self.prompt_message_timer: int = 0
        self.active_blocking_event_data: Optional[Dict[str, Any]] = None
        self.game_over_message: Optional[str] = None

        # Add methods here later to manage these states if needed
        # For example, a method to change view and update active buttons
        # def change_view(self, new_view: str, game_state, player_inv, game_configs, current_region):
        #     self.current_view = new_view
        #     # Potentially call a method to re-setup buttons here, or ensure app.py does it
        #     # This might involve passing more game state refs to UIManager or having callbacks
        #     pass
