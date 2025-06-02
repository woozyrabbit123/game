# src/mechanics/seasonal_events_manager.py
"""
Manages seasonal events in the game.
"""
from typing import TYPE_CHECKING, Optional, Dict, Any, Tuple

if TYPE_CHECKING:
    from ..game_state import GameState
    from ..narco_configs import SEASONAL_EVENTS # Assuming this will be defined

def start_seasonal_event(game_state: "GameState", event_id: str, event_data: Dict[str, Any]) -> Optional[str]:
    """
    Starts a seasonal event.
    Updates game_state and returns the start message.
    """
    game_state.current_seasonal_event = event_id
    game_state.seasonal_event_effects_active = event_data.get("effects", {})
    # Log the activation of effects
    # logger.info(f"Seasonal event '{event_data.get('name', event_id)}' started. Active effects: {game_state.seasonal_event_effects_active}")
    return event_data.get("message_on_start")

def end_seasonal_event(game_state: "GameState", event_id: str, event_data: Dict[str, Any]) -> Optional[str]:
    """
    Ends a seasonal event.
    Clears event from game_state and returns the end message.
    """
    ended_event_name = game_state.seasonal_event_name_map.get(event_id, event_id) # Get friendly name
    game_state.current_seasonal_event = None
    game_state.seasonal_event_effects_active = {}
    # logger.info(f"Seasonal event '{ended_event_name}' ended.")
    return event_data.get("message_on_end")

def check_and_update_seasonal_events(game_state: "GameState", game_configs: Any) -> Optional[str]:
    """
    Checks the current game day against seasonal event start/end days.
    Starts or ends events as appropriate.
    Returns any message (start or end) to be displayed.
    """
    current_day = game_state.current_day
    active_event_id = game_state.current_seasonal_event
    message_to_show = None

    # Check if an active event needs to end
    if active_event_id:
        event_data = game_configs.SEASONAL_EVENTS.get(active_event_id)
        if not event_data or current_day > event_data.get("end_day", -1):
            message_to_show = end_seasonal_event(game_state, active_event_id, event_data if event_data else {})
            active_event_id = None # Clear it so a new event can start on the same day if needed

    # Check if a new event should start (only if no event is currently active or one just ended)
    if not active_event_id:
        for event_id, event_config in game_configs.SEASONAL_EVENTS.items():
            if event_config.get("start_day", -1) == current_day:
                message_to_show = start_seasonal_event(game_state, event_id, event_config)
                game_state.seasonal_event_name_map[event_id] = event_config.get("name", event_id) # Store friendly name
                break # Only start one event per day
    
    return message_to_show

[end of src/mechanics/seasonal_events_manager.py]
