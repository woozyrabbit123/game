import pygame
import sys
import functools # For partial
from typing import List, Optional, Dict, Tuple, Callable, Any

from ..core.enums import (
    DrugName, DrugQuality, RegionName, CryptoCoin, SkillID, EventType, 
    ContactID, QuestID # Added ContactID, QuestID
)
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..game_state import GameState
from src import narco_configs # Renamed for clarity and direct access
from ..mechanics import quest_manager # Import quest_manager

from .ui_theme import (
    FONT_XLARGE, FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_XSMALL, FONT_LARGE_BOLD,
    BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_DISABLED_COLOR,
    BUTTON_TEXT_COLOR, BUTTON_DISABLED_TEXT_COLOR,
    TEXT_COLOR, TEXT_INPUT_BG_COLOR, TEXT_INPUT_BORDER_COLOR, TEXT_INPUT_TEXT_COLOR,
    HUD_BACKGROUND_COLOR, HUD_TEXT_COLOR, HUD_ACCENT_COLOR,
    RICH_BLACK, OXFORD_BLUE, YALE_BLUE, SILVER_LAKE_BLUE, PLATINUM, GHOST_WHITE,
    IMPERIAL_RED, EMERALD_GREEN, GOLDEN_YELLOW, NEON_BLUE, DARK_GREY, MEDIUM_GREY,
    LIGHT_GREY, VERY_LIGHT_GREY
)
from .ui_components import Button
from . import constants as UI_CONSTANTS


# Placeholder for action functions if any are defined directly here (most should come from app_actions)
def placeholder_action():
    print("Placeholder action triggered in UIManager")

class UIManager:
    def __init__(self, game_state: GameState, player_inventory: PlayerInventory, game_configs: Any, app_actions: Dict[str, Callable]):
        self.game_state = game_state
        self.player_inventory = player_inventory
        self.game_configs = game_configs # This should be the direct narco_configs module
        self.app_actions = app_actions 

        self.current_view: str = "main_menu"
        self.active_buttons_list: List[Button] = []

        self.main_menu_buttons: List[Button] = []
        self.market_view_buttons: List[Button] = [] 
        self.market_item_buttons: List[Button] = [] 
        self.inventory_view_buttons: List[Button] = []
        self.travel_view_buttons: List[Button] = []
        self.tech_contact_view_buttons: List[Button] = []
        self.skills_view_buttons: List[Button] = []
        self.upgrades_view_buttons: List[Button] = []
        self.transaction_input_buttons: List[Button] = []
        self.blocking_event_popup_buttons: List[Button] = []
        self.game_over_buttons: List[Button] = []
        self.informant_view_buttons: List[Button] = []
        
        # For new generic contacts
        self.contact_specific_buttons: Dict[ContactID, List[Button]] = {}


        self.current_transaction_type: Optional[str] = None
        self.drug_for_transaction: Optional[DrugName] = None
        self.quality_for_transaction: Optional[DrugQuality] = None
        self.price_for_transaction: float = 0.0
        self.available_for_transaction: int = 0
        self.quantity_input_string: str = ""
        self.input_box_rect = pygame.Rect(
            UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.MARKET_INPUT_BOX_X_OFFSET,
            UI_CONSTANTS.MARKET_INPUT_BOX_Y_POS,
            UI_CONSTANTS.MARKET_INPUT_BOX_WIDTH,
            UI_CONSTANTS.MARKET_INPUT_BOX_HEIGHT
        )

        self.tech_transaction_in_progress: Optional[str] = None
        self.coin_for_tech_transaction: Optional[CryptoCoin] = None
        self.tech_input_string: str = ""
        self.tech_input_box_rect = pygame.Rect(
            UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.TECH_INPUT_BOX_X_OFFSET,
            UI_CONSTANTS.TECH_INPUT_BOX_Y_POS,
            UI_CONSTANTS.TECH_INPUT_BOX_WIDTH,
            UI_CONSTANTS.TECH_INPUT_BOX_HEIGHT
        )

        self.active_prompt_message: Optional[str] = None
        self.prompt_message_timer: int = 0
        self.active_blocking_event_data: Optional[Dict] = None
        self.game_over_message: Optional[str] = None

        self.setup_buttons_for_current_view()

    def set_active_prompt_message(self, message: str, duration_frames: int = UI_CONSTANTS.PROMPT_DURATION_FRAMES) -> None:
        self.active_prompt_message = message
        self.prompt_message_timer = duration_frames

    def _create_action_button(
        self, text: str, action: Callable[..., Any], x: int, y: int, width: int, height: int,
        action_args: Optional[Tuple[Any, ...]] = None, font: pygame.font.Font = FONT_MEDIUM,
        is_enabled: bool = True,
    ) -> Button:
        final_action = action
        if action_args is not None:
            # Use functools.partial for robustness with arguments, especially in loops
            final_action = functools.partial(action, *action_args)
        return Button(x, y, width, height, text, final_action, is_enabled=is_enabled, font=font)

    def _create_back_button(self, action: Optional[Callable[[], None]] = None, text: str = "Back") -> Button:
        final_action = action if action is not None else self.app_actions.get('open_main_menu', placeholder_action)
        return Button(
            UI_CONSTANTS.SCREEN_WIDTH - UI_CONSTANTS.STD_BUTTON_WIDTH - UI_CONSTANTS.LARGE_PADDING,
            UI_CONSTANTS.SCREEN_HEIGHT - UI_CONSTANTS.STD_BUTTON_HEIGHT - UI_CONSTANTS.LARGE_PADDING,
            UI_CONSTANTS.STD_BUTTON_WIDTH, UI_CONSTANTS.STD_BUTTON_HEIGHT, text, final_action, font=FONT_SMALL,
        )

    def _is_contact_available(self, contact_id: ContactID) -> bool:
        contact_def = self.game_configs.CONTACT_DEFINITIONS.get(contact_id)
        if not contact_def: return False
        contact_region = contact_def.get("region")
        if not contact_region: return True # Globally available if no region specified
        
        player_region = self.game_state.get_current_player_region()
        if player_region and player_region.name == contact_region:
            # Check if contact is temporarily unavailable due to turf war
            if player_region.name in self.game_state.active_turf_wars:
                war_data = self.game_state.active_turf_wars[player_region.name]
                if contact_id in war_data.get("affected_contacts", []):
                    return False # Contact is unavailable due to turf war
            return True
        return False

    def _setup_main_menu_buttons(self):
        self.main_menu_buttons.clear()
        button_width, button_height, spacing, start_x, start_y = (
            UI_CONSTANTS.STD_BUTTON_WIDTH, UI_CONSTANTS.STD_BUTTON_HEIGHT,
            UI_CONSTANTS.STD_BUTTON_SPACING,
            UI_CONSTANTS.SCREEN_WIDTH // 2 - UI_CONSTANTS.STD_BUTTON_WIDTH // 2, # Center calculation
            UI_CONSTANTS.MENU_START_Y,
        )
        
        actions_defs: List[Tuple[str, Callable[[], None], Optional[Callable[[GameState], bool]]]] = [
            ("Market", self.app_actions.get('open_market', placeholder_action), None),
            ("Inventory", self.app_actions.get('open_inventory', placeholder_action), None),
            ("Travel", self.app_actions.get('open_travel', placeholder_action), None),
            ("Tech Contact", self.app_actions.get('open_tech_contact', placeholder_action), lambda gs: self._is_contact_available(ContactID.TECH_CONTACT)),
            ("Meet Informant", self.app_actions.get('open_informant', placeholder_action), 
                lambda gs: self._is_contact_available(ContactID.INFORMANT) and \
                           (gs.informant_unavailable_until_day is None or gs.current_day >= gs.informant_unavailable_until_day)),
            ("Meet Corrupt Official", self.app_actions.get('meet_corrupt_official', placeholder_action), lambda gs: self._is_contact_available(ContactID.CORRUPT_OFFICIAL)),
            ("Meet The Forger", self.app_actions.get('meet_forger', placeholder_action), lambda gs: self._is_contact_available(ContactID.THE_FORGER)),
            ("Meet Logistics Expert", self.app_actions.get('meet_logistics_expert', placeholder_action), lambda gs: self._is_contact_available(ContactID.LOGISTICS_EXPERT)),
            ("Skills", self.app_actions.get('open_skills', placeholder_action), None),
            ("Upgrades", self.app_actions.get('open_upgrades', placeholder_action), None),
        ]

        active_forger_quest = self.player_inventory.active_quests.get(QuestID.FORGER_SUPPLY_RUN)
        if active_forger_quest and active_forger_quest.get("current_stage") == 1:
            quest_def = quest_manager.get_quest_definition(QuestID.FORGER_SUPPLY_RUN)
            stage_data = quest_manager.get_quest_stage_data(quest_def, 1) # Stage 1: In Progress
            if self.game_state.current_player_region and stage_data and \
               self.game_state.current_player_region.name == stage_data.get("target_region_name"):
                actions_defs.append(
                    ("Search for Supplies (Quest)", self.app_actions.get('search_for_supplies', placeholder_action), None)
                )
        
        col1_count: int = UI_CONSTANTS.MAIN_MENU_COL1_COUNT 
        num_buttons = len(actions_defs)
        if num_buttons > 8: # If more than 8 buttons, consider adjusting layout
             col1_count = (num_buttons + 1) // 2


        for i, (text_val, action_val, enabled_check_func) in enumerate(actions_defs):
            col_val, row_in_col_val = (0, i) if i < col1_count else (1, i - col1_count)
            x_pos_val: int = start_x + col_val * (button_width + spacing) # Simple two columns for now
            if num_buttons <= col1_count : x_pos_val = start_x # Center if only one column
            
            y_pos_val: int = start_y + row_in_col_val * (button_height + spacing)
            if col_val == 1 and row_in_col_val == 0: y_pos_val = start_y 
            
            is_enabled_val: bool = enabled_check_func(self.game_state) if enabled_check_func else True
            self.main_menu_buttons.append(
                self._create_action_button(text_val, action_val, x_pos_val, y_pos_val, button_width, button_height, is_enabled=is_enabled_val)
            )
        self.active_buttons_list = self.main_menu_buttons


    def _setup_blocking_event_popup_buttons(self):
        self.blocking_event_popup_buttons.clear()
        if self.active_blocking_event_data:
            popup_w_val = UI_CONSTANTS.SCREEN_WIDTH * UI_CONSTANTS.POPUP_WIDTH_RATIO
            popup_h_val = UI_CONSTANTS.SCREEN_HEIGHT * UI_CONSTANTS.POPUP_HEIGHT_RATIO
            popup_x_val = (UI_CONSTANTS.SCREEN_WIDTH - popup_w_val) / 2
            popup_y_val = (UI_CONSTANTS.SCREEN_HEIGHT - popup_h_val) / 2
            btn_w_val, btn_h_val = UI_CONSTANTS.POPUP_BUTTON_WIDTH, UI_CONSTANTS.POPUP_BUTTON_HEIGHT
            base_btn_y_val = popup_y_val + popup_h_val - btn_h_val - UI_CONSTANTS.POPUP_BUTTON_MARGIN_Y
            
            event_choices = self.active_blocking_event_data.get("choices")
            if event_choices and self.active_blocking_event_data.get("is_opportunity_event"):
                num_choices = len(event_choices)
                total_button_width = num_choices * btn_w_val + (num_choices - 1) * UI_CONSTANTS.STD_BUTTON_SPACING
                start_x_choices = popup_x_val + (popup_w_val - total_button_width) / 2
                
                for i, choice_data in enumerate(event_choices):
                    choice_text = choice_data.get("text", f"Option {i+1}")
                    is_enabled = True
                    if self.active_blocking_event_data.get("event_type_id") == EventType.URGENT_DELIVERY.value and choice_data.get("id") == "accept_delivery":
                        runtime_params = self.active_blocking_event_data.get("runtime_params", {})
                        req_drug = runtime_params.get("drug_name")
                        req_qual = runtime_params.get("quality")
                        req_qty = runtime_params.get("quantity")
                        if req_drug and req_qual and req_qty:
                            if self.player_inventory.get_quantity(req_drug, req_qual) < req_qty:
                                is_enabled = False
                                choice_text += " (Insufficient)"
                    action = functools.partial(self.app_actions.get('resolve_opportunity_event_choice', placeholder_action), choice_index=i)
                    btn_x_val = start_x_choices + i * (btn_w_val + UI_CONSTANTS.STD_BUTTON_SPACING)
                    self.blocking_event_popup_buttons.append(
                        self._create_action_button(choice_text, action, int(btn_x_val), int(base_btn_y_val), btn_w_val, btn_h_val, font=FONT_SMALL, is_enabled=is_enabled)
                    )
            else: 
                btn_txt_val: str = self.active_blocking_event_data.get("button_text", "Continue")
                btn_x_val = popup_x_val + (popup_w_val - btn_w_val) / 2
                self.blocking_event_popup_buttons.append(
                    self._create_action_button(btn_txt_val, self.app_actions.get('close_blocking_event_popup', placeholder_action), int(btn_x_val), int(base_btn_y_val), btn_w_val, btn_h_val, font=FONT_SMALL)
                )
        self.active_buttons_list = self.blocking_event_popup_buttons

    def _setup_generic_contact_view_buttons(self, contact_id: ContactID):
        button_list_attr_map = {
            ContactID.INFORMANT: self.informant_view_buttons,
            ContactID.TECH_CONTACT: self.tech_contact_view_buttons,
            ContactID.CORRUPT_OFFICIAL: self.contact_specific_buttons.setdefault(ContactID.CORRUPT_OFFICIAL, []),
            ContactID.THE_FORGER: self.contact_specific_buttons.setdefault(ContactID.THE_FORGER, []),
            ContactID.LOGISTICS_EXPERT: self.contact_specific_buttons.setdefault(ContactID.LOGISTICS_EXPERT, []),
        }
        current_contact_buttons = button_list_attr_map.get(contact_id)
        if current_contact_buttons is None: # Should not happen if map is comprehensive
            current_contact_buttons = [] 
            self.contact_specific_buttons[contact_id] = current_contact_buttons
        
        current_contact_buttons.clear()

        contact_def = self.game_configs.CONTACT_DEFINITIONS.get(contact_id)
        if not contact_def:
            current_contact_buttons.append(self._create_back_button())
            return

        button_width = UI_CONSTANTS.STD_BUTTON_WIDTH + 60 
        button_height = UI_CONSTANTS.STD_BUTTON_HEIGHT - 10
        spacing = UI_CONSTANTS.MENU_BUTTON_SPACING - 7
        start_y = UI_CONSTANTS.CONTACT_SERVICE_BUTTON_START_Y 
        start_x = UI_CONSTANTS.SCREEN_WIDTH // 2 - button_width // 2
        
        item_idx = 0 
        action_added = False

        # Quest Handling
        active_quest_for_this_contact: Optional[QuestID] = None
        active_quest_data_for_this_contact: Optional[Dict[str, Any]] = None
        for q_id, q_data in self.player_inventory.active_quests.items():
            q_def = quest_manager.get_quest_definition(q_id)
            if q_def and q_def.get("contact_id") == contact_id:
                active_quest_for_this_contact = q_id
                active_quest_data_for_this_contact = q_data
                break
        
        if active_quest_for_this_contact and active_quest_data_for_this_contact:
            quest_def = quest_manager.get_quest_definition(active_quest_for_this_contact)
            stage_num = active_quest_data_for_this_contact.get("current_stage", 0)
            stage_data = quest_manager.get_quest_stage_data(quest_def, stage_num)

            if stage_data and stage_data.get("completion_text") and \
               quest_manager.try_advance_quest(self.player_inventory, self.game_state, active_quest_for_this_contact):
                btn_text = stage_data["completion_text"]
                action = self.app_actions.get("complete_quest_stage", placeholder_action)
                args = (active_quest_for_this_contact.value,)
                current_contact_buttons.append(self._create_action_button(btn_text, action, start_x, start_y + item_idx * (button_height + spacing), button_width, button_height, action_args=args, font=FONT_SMALL))
                item_idx += 1
                action_added = True
        
        if not action_added: # If no active quest completion, check for new offers
            offered_quests = quest_manager.offer_quests_for_contact(self.player_inventory, self.game_state, contact_id)
            if offered_quests:
                quest_id_to_offer = offered_quests[0] # Offer one at a time
                quest_def = quest_manager.get_quest_definition(quest_id_to_offer)
                stage_0_data = quest_manager.get_quest_stage_data(quest_def, 0)
                if stage_0_data:
                    accept_text = stage_0_data.get("accept_text", "Accept Quest")
                    accept_action = self.app_actions.get("accept_quest", placeholder_action)
                    accept_args = (quest_id_to_offer.value,)
                    current_contact_buttons.append(self._create_action_button(accept_text, accept_action, start_x, start_y + item_idx * (button_height + spacing), button_width, button_height, action_args=accept_args, font=FONT_SMALL))
                    item_idx += 1
                    
                    decline_text = stage_0_data.get("decline_text", "Decline")
                    decline_action = self.app_actions.get("decline_quest", placeholder_action)
                    decline_args = (quest_id_to_offer.value,)
                    current_contact_buttons.append(self._create_action_button(decline_text, decline_action, start_x, start_y + item_idx * (button_height + spacing), button_width, button_height, action_args=decline_args, font=FONT_SMALL))
                    item_idx +=1
                    action_added = True # Quest offer buttons added

        # Regular Service Buttons (only if no quest actions were added for now, or design for both)
        if not action_added:
            services = contact_def.get("services", [])
            for service in services:
                service_id = service.get("id", f"service_{item_idx}")
                service_name = service.get("name", "Unknown Service")
                action_key_specific = f"contact_service_{contact_id.value.lower()}_{service_id.lower()}"
                action_args: Optional[Tuple[Any, ...]] = None
                
                service_action = self.app_actions.get(action_key_specific)
                if not service_action: # Fallback to generic handlers if specific not found
                    if contact_id == ContactID.TECH_CONTACT: # Tech contact uses initiate_tech_operation
                        service_action = self.app_actions.get('initiate_tech_operation', placeholder_action)
                        action_args = (service_id,) 
                    # Add other generic handlers if any
                    else:
                        service_action = placeholder_action # Default placeholder

                current_contact_buttons.append(
                    self._create_action_button(
                        text=service_name, action=service_action,
                        x=start_x, y=start_y + item_idx * (button_height + spacing),
                        width=button_width, height=button_height,
                        action_args=action_args, font=FONT_SMALL
                    )
                )
                item_idx += 1
        
        current_contact_buttons.append(self._create_back_button())


    def _setup_skills_view_buttons(self):
        self.skills_view_buttons.clear()
        skill_definitions = self.game_configs.SKILL_DEFINITIONS
        base_y = UI_CONSTANTS.SKILLS_BUTTON_START_Y 
        button_height = UI_CONSTANTS.STD_BUTTON_HEIGHT - 10
        button_width = UI_CONSTANTS.STD_BUTTON_WIDTH - 20
        button_x = UI_CONSTANTS.SCREEN_WIDTH - button_width - UI_CONSTANTS.LARGE_PADDING - 40 
        skill_item_v_spacing = 80 

        for idx, (skill_id_enum_key, skill_def) in enumerate(skill_definitions.items()):
            # Ensure skill_id_enum_key is an enum member if it's not already
            skill_id_enum = skill_id_enum_key if isinstance(skill_id_enum_key, SkillID) else SkillID(str(skill_id_enum_key))

            is_unlocked = skill_id_enum.value in self.player_inventory.unlocked_skills
            
            prerequisites = skill_def.get("prerequisites", [])
            prereqs_met = True
            if prerequisites:
                for prereq_id_enum_val in prerequisites:
                    # Ensure prereq_id_enum_val is an enum member before accessing .value
                    prereq_id = prereq_id_enum_val.value if isinstance(prereq_id_enum_val, SkillID) else str(prereq_id_enum_val)
                    if prereq_id not in self.player_inventory.unlocked_skills:
                        prereqs_met = False
                        break
            
            can_afford = self.player_inventory.skill_points >= skill_def["cost"]
            is_enabled = not is_unlocked and prereqs_met and can_afford
            
            button_text = "Unlock"
            if is_unlocked: button_text = "Unlocked"
            elif not prereqs_met: button_text = "Locked" 
            elif not can_afford: button_text = f"Cost: {skill_def['cost']}SP"

            action_func = self.app_actions.get('unlock_skill', placeholder_action)
            current_button_y = base_y + (idx * skill_item_v_spacing)

            self.skills_view_buttons.append(
                self._create_action_button(
                    text=button_text, action=action_func, x=button_x, y=current_button_y, 
                    width=button_width, height=button_height,
                    action_args=(skill_id_enum, self.player_inventory, self.game_configs), 
                    font=FONT_SMALL, is_enabled=is_enabled
                )
            )
        self.skills_view_buttons.append(self._create_back_button())

    def _setup_market_view_buttons(self): 
        self.market_view_buttons.clear()
        self.market_view_buttons.append(self._create_back_button())

    def setup_buttons_for_current_view(self) -> None:
        self.active_buttons_list.clear() # Clear generic active list first

        if self.current_view == "game_over":
            self._setup_game_over_buttons() # Assuming a dedicated method
            self.active_buttons_list = self.game_over_buttons
        elif self.current_view == "main_menu":
            self._setup_main_menu_buttons()
            self.active_buttons_list = self.main_menu_buttons
        elif self.current_view == "blocking_event_popup":
            self._setup_blocking_event_popup_buttons()
            self.active_buttons_list = self.blocking_event_popup_buttons
        elif self.current_view == "travel":
            self._setup_travel_view_buttons()
            self.active_buttons_list = self.travel_view_buttons
        elif self.current_view == "skills":
            self._setup_skills_view_buttons()
            self.active_buttons_list = self.skills_view_buttons
        elif self.current_view == "market":
            self._setup_market_view_buttons() 
            # Market item buttons are dynamic, added by draw_market_view, so handle active_list there or pass UIManager
            self.active_buttons_list = self.market_view_buttons # Base buttons, item buttons handled in draw loop
        elif self.current_view == "inventory":
            self.inventory_view_buttons.clear()
            self.inventory_view_buttons.append(self._create_back_button())
            self.active_buttons_list = self.inventory_view_buttons
        elif self.current_view == "informant":
            self._setup_generic_contact_view_buttons(ContactID.INFORMANT)
            self.active_buttons_list = self.informant_view_buttons
        elif self.current_view == "tech_contact":
            self._setup_generic_contact_view_buttons(ContactID.TECH_CONTACT)
            self.active_buttons_list = self.tech_contact_view_buttons
        elif self.current_view == "corrupt_official_contact":
            self._setup_generic_contact_view_buttons(ContactID.CORRUPT_OFFICIAL)
            self.active_buttons_list = self.contact_specific_buttons.get(ContactID.CORRUPT_OFFICIAL, [])
        elif self.current_view == "forger_contact":
            self._setup_generic_contact_view_buttons(ContactID.THE_FORGER)
            self.active_buttons_list = self.contact_specific_buttons.get(ContactID.THE_FORGER, [])
        elif self.current_view == "logistics_expert_contact":
            self._setup_generic_contact_view_buttons(ContactID.LOGISTICS_EXPERT)
            self.active_buttons_list = self.contact_specific_buttons.get(ContactID.LOGISTICS_EXPERT, [])
        
        # Placeholder for other views like upgrades, transaction_input etc.
        elif self.current_view == "upgrades": # Example
            self.upgrades_view_buttons.clear()
            # ... setup upgrade buttons ...
            self.upgrades_view_buttons.append(self._create_back_button())
            self.active_buttons_list = self.upgrades_view_buttons
        elif self.current_view in ["market_buy_input", "market_sell_input"]:
             self._setup_transaction_input_buttons()
             self.active_buttons_list = self.transaction_input_buttons
        elif self.current_view in ["tech_input_coin_select", "tech_input_amount"]:
            # Tech input often shares buttons with tech_contact or has specific confirm/cancel
            self._setup_tech_input_buttons() # Assumes this method exists
            self.active_buttons_list = self.tech_contact_view_buttons # Or a specific list for these views

        else: 
            # Fallback to avoid empty active_buttons_list if a view is missed
            temp_fallback_button = self._create_action_button("Back to Menu", self.app_actions.get('open_main_menu', placeholder_action), 50,50,200,50)
            self.active_buttons_list = [temp_fallback_button]
    
    def _setup_game_over_buttons(self):
        self.game_over_buttons.clear()
        popup_width_val = UI_CONSTANTS.SCREEN_WIDTH * UI_CONSTANTS.POPUP_WIDTH_RATIO
        popup_height_val = UI_CONSTANTS.SCREEN_HEIGHT * UI_CONSTANTS.POPUP_HEIGHT_RATIO
        btn_w_val, btn_h_val = UI_CONSTANTS.POPUP_BUTTON_WIDTH, UI_CONSTANTS.POPUP_BUTTON_HEIGHT
        popup_x_val = (UI_CONSTANTS.SCREEN_WIDTH - popup_width_val) / 2
        popup_y_val = (UI_CONSTANTS.SCREEN_HEIGHT - popup_height_val) / 2
        btn_x_val = popup_x_val + (popup_w_val - btn_w_val) / 2
        btn_y_val = popup_y_val + popup_h_val - btn_h_val - UI_CONSTANTS.POPUP_BUTTON_MARGIN_Y
        self.game_over_buttons.append(
            self._create_action_button("Exit Game", self.app_actions.get('exit_game', placeholder_action), int(btn_x_val), int(btn_y_val), btn_w_val, btn_h_val, font=FONT_MEDIUM)
        )

    def _setup_transaction_input_buttons(self):
        self.transaction_input_buttons.clear()
        confirm_text = self.current_transaction_type.capitalize() if self.current_transaction_type else "Confirm"
        # Centered buttons at bottom
        btn_width = 120
        btn_height = 40
        spacing = 20
        total_width = 2 * btn_width + spacing
        start_x = (UI_CONSTANTS.SCREEN_WIDTH - total_width) // 2
        btn_y = UI_CONSTANTS.SCREEN_HEIGHT - 100

        self.transaction_input_buttons.append(self._create_action_button(confirm_text, self.app_actions.get('confirm_transaction', placeholder_action), start_x, btn_y, btn_width, btn_height))
        self.transaction_input_buttons.append(self._create_action_button("Cancel", self.app_actions.get('cancel_transaction', placeholder_action), start_x + btn_width + spacing, btn_y, btn_width, btn_height))

    def _setup_tech_input_buttons(self):
        # This might vary based on if it's coin select or amount input.
        # For now, a generic confirm/cancel, assuming it's for amount input mostly.
        self.tech_contact_view_buttons.clear() # Tech contact buttons are often reused or form base
        
        btn_width = 120
        btn_height = 40
        spacing = 20
        total_width = 2 * btn_width + spacing
        start_x = (UI_CONSTANTS.SCREEN_WIDTH - total_width) // 2
        btn_y = UI_CONSTANTS.SCREEN_HEIGHT - 100 # Similar to transaction input

        if self.current_view == "tech_input_amount":
            self.tech_contact_view_buttons.append(self._create_action_button("Confirm", self.app_actions.get('confirm_tech_operation', placeholder_action), start_x, btn_y, btn_width, btn_height))
            self.tech_contact_view_buttons.append(self._create_action_button("Cancel", self.app_actions.get('cancel_transaction', placeholder_action), start_x + btn_width + spacing, btn_y, btn_width, btn_height))
        elif self.current_view == "tech_input_coin_select":
            # Buttons for each coin type are typically created here dynamically
            # For brevity, assuming they are added if this view is active
            # And a back/cancel button
            self.tech_contact_view_buttons.append(self._create_back_button(action=self.app_actions.get('open_tech_contact', placeholder_action), text="Cancel"))


    # Action Stubs (UIManager methods that call app_actions)
    def action_open_main_menu(self) -> None:
        self.current_view = "main_menu"
        # self.app_actions.get('open_main_menu', placeholder_action)() # app.py will set view, UIManager just reacts via setup_buttons

    # ... other action_open_VIEW methods similarly just set self.current_view ...
    # The actual call to app.py's action is done when the button is pressed.
    # UIManager's action_open_... methods are for internal view changes if needed,
    # but mostly the view change is initiated from app.py, and UIManager's setup_buttons
    # reacts to self.current_view being set by app.py.

[end of src/ui_pygame/ui_manager.py]
