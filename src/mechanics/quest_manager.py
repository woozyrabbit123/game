# src/mechanics/quest_manager.py
"""
Manages player quests, including offering, accepting, advancing, and completing quests.
"""
from typing import TYPE_CHECKING, Optional, List, Dict, Any
import random # For item acquisition chance if needed

from ..core.enums import QuestID, ContactID, RegionName # Assuming these enums exist
from .. import narco_configs as game_configs # For QUEST_DEFINITIONS

if TYPE_CHECKING:
    from ..core.player_inventory import PlayerInventory
    from ..game_state import GameState


def get_quest_definition(quest_id: QuestID) -> Optional[Dict[str, Any]]:
    return game_configs.QUEST_DEFINITIONS.get(quest_id)

def get_quest_stage_data(quest_def: Dict[str, Any], stage_num: int) -> Optional[Dict[str, Any]]:
    return quest_def.get("stages", {}).get(stage_num)

def can_offer_quest(player_inventory: "PlayerInventory", game_state: "GameState", quest_id: QuestID, contact_id: ContactID) -> bool:
    """Checks if a specific quest can be offered by a contact."""
    quest_def = get_quest_definition(quest_id)
    if not quest_def:
        return False
    if quest_def["contact_id"] != contact_id:
        return False
    if quest_id in player_inventory.active_quests or quest_id in player_inventory.completed_quests:
        return False
    
    min_trust = quest_def.get("min_trust_to_start", 0)
    current_trust = player_inventory.contact_trusts.get(contact_id, 0)
    if current_trust < min_trust:
        return False
        
    # TODO: Add other prerequisites like level, other completed quests, items etc.
    return True

def offer_quests_for_contact(player_inventory: "PlayerInventory", game_state: "GameState", contact_id: ContactID) -> List[QuestID]:
    """Returns a list of QuestIDs that the given contact can currently offer the player."""
    available_quests: List[QuestID] = []
    for quest_id_enum in QuestID: # Iterate over all defined QuestIDs
        if can_offer_quest(player_inventory, game_state, quest_id_enum, contact_id):
            available_quests.append(quest_id_enum)
    return available_quests
    
def accept_quest(player_inventory: "PlayerInventory", game_state: "GameState", quest_id: QuestID) -> bool:
    """Marks a quest as active for the player, setting it to the first progression stage (usually 1)."""
    quest_def = get_quest_definition(quest_id)
    if not quest_def or quest_id in player_inventory.active_quests or quest_id in player_inventory.completed_quests:
        return False # Cannot accept if not defined, already active, or completed
    
    # Typically, stage 0 is the offer. Stage 1 is the first "in-progress" stage.
    initial_stage = 1 
    if 0 not in quest_def.get("stages", {}): # If no explicit stage 0, maybe starts at 1
        initial_stage = min(k for k in quest_def.get("stages", {}).keys() if isinstance(k, int) and k >=0) if quest_def.get("stages") else 1


    player_inventory.active_quests[quest_id] = {
        "current_stage": initial_stage, # Start at stage 1 (after offer)
        "quest_id_str": quest_id.value, # Store string value for easier serialization if needed
        # Store any other dynamic quest data needed, e.g., specific target generated at accept time
    }
    # Example: If quest needs specific items, this is where you might initialize tracking for them
    # if quest_def.get("stages", {}).get(initial_stage, {}).get("objective_item"):
    #     player_inventory.special_items[quest_def["stages"][initial_stage]["objective_item"]] = 0

    return True

def decline_quest(player_inventory: "PlayerInventory", game_state: "GameState", quest_id: QuestID) -> None:
    """Handles quest declination. Currently no major state change."""
    # quest_def = get_quest_definition(quest_id)
    # if quest_def:
    #     contact_id = quest_def["contact_id"]
    #     # Optional: Minor trust penalty for declining frequent offers, or cooldown before re-offering
    #     # player_inventory.contact_trusts[contact_id] = max(0, player_inventory.contact_trusts.get(contact_id, 0) - 1)
    pass

def get_active_quest_dialogue(player_inventory: "PlayerInventory", quest_id: QuestID) -> Optional[str]:
    """Gets the current dialogue/description for an active quest based on its stage."""
    if quest_id not in player_inventory.active_quests:
        return None
    
    quest_def = get_quest_definition(quest_id)
    active_quest_data = player_inventory.active_quests[quest_id]
    current_stage_num = active_quest_data.get("current_stage", -1)
    stage_data = get_quest_stage_data(quest_def, current_stage_num)

    if not stage_data:
        return "Quest stage data not found."

    description_template = stage_data.get("description_template", "No description for this stage.")
    
    # Populate template with dynamic data
    format_params = {
        "quantity": stage_data.get("objective_quantity"),
        "target_region_name": stage_data.get("target_region_name").value if stage_data.get("target_region_name") else "Unknown Region",
        # Add more params as needed by different quests
    }
    return description_template.format(**format_params)


def try_advance_quest(player_inventory: "PlayerInventory", game_state: "GameState", quest_id: QuestID) -> bool:
    """
    Checks if the conditions to advance the given active quest are met.
    If so, advances its stage. This is a generic advance, specific completion logic is separate.
    """
    if quest_id not in player_inventory.active_quests:
        return False

    quest_def = get_quest_definition(quest_id)
    active_quest_data = player_inventory.active_quests[quest_id]
    current_stage_num = active_quest_data.get("current_stage", 0)
    current_stage_data = get_quest_stage_data(quest_def, current_stage_num)

    if not current_stage_data: return False

    # Example for FORGER_SUPPLY_RUN:
    if quest_id == QuestID.FORGER_SUPPLY_RUN and current_stage_num == 1:
        item_name = current_stage_data.get("objective_item")
        required_qty = current_stage_data.get("objective_quantity", 0)
        if player_inventory.special_items.get(item_name, 0) >= required_qty:
            # Conditions met to complete this stage (hand over items)
            return True # Indicate that completion can be attempted
    
    # Add more specific advancement/completion checks for other quests/stages here
    return False


def complete_quest_stage(player_inventory: "PlayerInventory", game_state: "GameState", quest_id: QuestID) -> List[str]:
    """
    Completes the current stage of a quest, applies rewards if it's a completion stage,
    and advances to the next stage or marks quest as complete.
    Returns UI messages.
    """
    ui_messages: List[str] = []
    if quest_id not in player_inventory.active_quests:
        ui_messages.append("Error: Quest not active.")
        return ui_messages

    quest_def = get_quest_definition(quest_id)
    active_quest_data = player_inventory.active_quests[quest_id]
    current_stage_num = active_quest_data.get("current_stage", 0)
    current_stage_data = get_quest_stage_data(quest_def, current_stage_num)

    if not current_stage_data:
        ui_messages.append("Error: Quest stage data missing.")
        return ui_messages

    # Specific logic for FORGER_SUPPLY_RUN completion (Stage 1 -> Stage 2)
    if quest_id == QuestID.FORGER_SUPPLY_RUN and current_stage_num == 1:
        item_name = current_stage_data.get("objective_item")
        required_qty = current_stage_data.get("objective_quantity", 0)
        if player_inventory.special_items.get(item_name, 0) >= required_qty:
            player_inventory.special_items[item_name] = player_inventory.special_items.get(item_name, 0) - required_qty
            if player_inventory.special_items[item_name] <= 0:
                del player_inventory.special_items[item_name]
            
            # Advance to completion stage (Stage 2 for this quest)
            next_stage_num = 2 
            active_quest_data["current_stage"] = next_stage_num
            completion_stage_data = get_quest_stage_data(quest_def, next_stage_num)
            
            if completion_stage_data and completion_stage_data.get("is_completion_stage"):
                ui_messages.append(completion_stage_data.get("description_template", "Quest updated."))
                rewards = completion_stage_data.get("rewards", {})
                if "cash_reward" in rewards:
                    player_inventory.cash += rewards["cash_reward"]
                    ui_messages.append(f"Received ${rewards['cash_reward']:.2f}.")
                if "trust_increase" in rewards:
                    trust_data = rewards["trust_increase"]
                    contact_to_update = trust_data["contact_id"]
                    trust_amount = trust_data["amount"]
                    current_contact_trust = player_inventory.contact_trusts.get(contact_to_update, 0)
                    player_inventory.contact_trusts[contact_to_update] = min(100, current_contact_trust + trust_amount)
                    ui_messages.append(f"Trust with {contact_to_update.name.replace('_',' ').title()} increased by {trust_amount}.")
                # Handle other rewards like unlocking services, items etc.
                
                player_inventory.completed_quests.append(quest_id)
                del player_inventory.active_quests[quest_id]
            else:
                 ui_messages.append("Supplies handed over. Quest updated.") # Should not happen if stage 2 is completion stage
        else:
            ui_messages.append("You don't have all the supplies yet.")
    else:
        ui_messages.append("Quest progression for this stage not yet defined.")

    return ui_messages


def acquire_special_item(player_inventory: "PlayerInventory", item_name: str, quantity: int = 1) -> bool:
    """Adds a special quest item to the player's inventory."""
    current_qty = player_inventory.special_items.get(item_name, 0)
    player_inventory.special_items[item_name] = current_qty + quantity
    return True

[end of src/mechanics/quest_manager.py]
