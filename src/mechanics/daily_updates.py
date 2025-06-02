# src/mechanics/daily_updates.py
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from ..core.enums import CryptoCoin, EventType, SkillID, ContactID # Added ContactID
from ..core.market_event import MarketEvent
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..game_state import GameState
from ..mechanics import event_manager, market_impact
from . import seasonal_events_manager # Import the new manager


class DailyUpdateResult:
    def __init__(self):
        self.game_over_message: Optional[str] = None
        self.blocking_event_data: Optional[Dict] = None
        self.ui_messages: List[str] = []
        self.log_messages: List[str] = []
        self.skill_points_awarded_player_total: int = 0
        self.informant_unavailable_until_day: Optional[int] = None
        self.pending_laundered_sc_processed: bool = False
        self.new_pending_laundered_sc: float = 0.0 # Data for app.py to update player_inventory
        self.new_pending_laundered_sc_arrival_day: Optional[int] = None # Data for app.py to update player_inventory

# --- Helper Functions for Daily Updates ---

def _handle_debt_payments(
    game_state: GameState, player_inventory: PlayerInventory, game_configs: Any
) -> Tuple[Optional[str], List[str], List[str]]:
    """Handles daily debt payment checks."""
    game_over_msg = None
    ui_messages: List[str] = []
    log_messages: List[str] = []

    if not player_inventory.debt_payment_1_paid and game_state.current_day >= game_configs.DEBT_PAYMENT_1_DUE_DAY:
        if player_inventory.cash >= game_configs.DEBT_PAYMENT_1_AMOUNT:
            player_inventory.cash -= game_configs.DEBT_PAYMENT_1_AMOUNT
            player_inventory.debt_payment_1_paid = True
            ui_messages.append("Debt Payment 1 made!")
            log_messages.append(f"Paid ${game_configs.DEBT_PAYMENT_1_AMOUNT:,.0f} (Debt 1).")
        else:
            game_over_msg = "GAME OVER: Failed Debt Payment 1!"
            log_messages.append(game_over_msg)
            return game_over_msg, ui_messages, log_messages

    if player_inventory.debt_payment_1_paid and not player_inventory.debt_payment_2_paid and \
       game_state.current_day >= game_configs.DEBT_PAYMENT_2_DUE_DAY:
        if player_inventory.cash >= game_configs.DEBT_PAYMENT_2_AMOUNT:
            player_inventory.cash -= game_configs.DEBT_PAYMENT_2_AMOUNT
            player_inventory.debt_payment_2_paid = True
            ui_messages.append("Debt Payment 2 made!")
            log_messages.append(f"Paid ${game_configs.DEBT_PAYMENT_2_AMOUNT:,.0f} (Debt 2).")
        else:
            game_over_msg = "GAME OVER: Failed Debt Payment 2!"
            log_messages.append(game_over_msg)
            return game_over_msg, ui_messages, log_messages

    if player_inventory.debt_payment_1_paid and player_inventory.debt_payment_2_paid and \
       not player_inventory.debt_payment_3_paid and game_state.current_day >= game_configs.DEBT_PAYMENT_3_DUE_DAY:
        if player_inventory.cash >= game_configs.DEBT_PAYMENT_3_AMOUNT:
            player_inventory.cash -= game_configs.DEBT_PAYMENT_3_AMOUNT
            player_inventory.debt_payment_3_paid = True
            ui_messages.append("Final debt paid! You are free!")
            log_messages.append(f"Paid ${game_configs.DEBT_PAYMENT_3_AMOUNT:,.0f} (Final Debt). You are FREE!")
        else:
            game_over_msg = "GAME OVER: Failed Final Debt Payment!"
            log_messages.append(game_over_msg)
            return game_over_msg, ui_messages, log_messages
    
    return game_over_msg, ui_messages, log_messages

def _perform_regional_updates(game_state: GameState, player_inventory: PlayerInventory, game_configs: Any) -> None:
    """Performs daily updates for all regions."""
    for r_name, r_obj in game_state.all_regions.items():
        if hasattr(r_obj, "restock_market"): r_obj.restock_market()
        market_impact.decay_regional_heat(r_obj, 1.0, player_inventory, game_configs) # Pass player_inv and game_configs
        market_impact.decay_player_market_impact(r_obj)
        market_impact.decay_rival_market_impact(r_obj, game_state.current_day)
        event_manager.update_active_events(r_obj)

def _update_crypto_prices(game_state: GameState, game_configs: Any) -> None:
    """Updates daily crypto prices."""
    game_state.update_daily_crypto_prices(game_configs.CRYPTO_VOLATILITY, game_configs.CRYPTO_MIN_PRICE)

def _process_staking_rewards(
    player_inventory: PlayerInventory, game_configs: Any
) -> List[str]:
    """Processes daily staking rewards for DrugCoin."""
    ui_messages: List[str] = []
    if hasattr(player_inventory, "staked_drug_coin") and \
       player_inventory.staked_drug_coin.get("staked_amount", 0.0) > 0 and \
       hasattr(game_configs, "DC_STAKING_DAILY_RETURN_PERCENT"):
        reward = player_inventory.staked_drug_coin["staked_amount"] * game_configs.DC_STAKING_DAILY_RETURN_PERCENT
        player_inventory.staked_drug_coin["pending_rewards"] = player_inventory.staked_drug_coin.get("pending_rewards", 0.0) + reward
        if reward > 1e-5: # Only message if reward is significant
            ui_messages.append(f"Accrued {reward:.4f} DC rewards. Collect at Tech Contact.")
    return ui_messages

def _process_laundering_arrival(
    game_state: GameState, player_inventory: PlayerInventory
) -> Tuple[List[str], List[str], bool, float, Optional[int]]:
    """Processes arrival of laundered StreetCreds."""
    ui_messages: List[str] = []
    log_messages: List[str] = []
    processed_this_update = False
    new_pending_sc = player_inventory.pending_laundered_sc # Default to current if not updated
    new_arrival_day = player_inventory.pending_laundered_sc_arrival_day # Default to current

    if hasattr(player_inventory, "pending_laundered_sc_arrival_day") and \
       player_inventory.pending_laundered_sc_arrival_day is not None and \
       game_state.current_day >= player_inventory.pending_laundered_sc_arrival_day:
        
        amount_laundered = player_inventory.pending_laundered_sc
        stable_coin_enum = getattr(CryptoCoin, "STABLE_COIN", CryptoCoin.DRUG_COIN) # Fallback, though SC should exist
        player_inventory.add_crypto(stable_coin_enum, amount_laundered)
        
        ui_messages.append(f"{amount_laundered:.2f} SC (laundered) arrived.")
        log_messages.append(f"Laundered cash arrived: {amount_laundered:.2f} SC.")
        
        processed_this_update = True
        new_pending_sc = 0.0 # Reset for player_inventory
        new_arrival_day = None # Reset for player_inventory
        
    return ui_messages, log_messages, processed_this_update, new_pending_sc, new_arrival_day

def _trigger_random_market_event(
    game_state: GameState, player_inventory: PlayerInventory, game_configs: Any
) -> Tuple[List[str], List[str]]:
    """Triggers random market events in the current player region."""
    ui_messages: List[str] = []
    log_messages: List[str] = []

    def _capture_ui_msg(msg: str): ui_messages.append(msg)
    def _capture_log_msg(msg: str): log_messages.append(msg)

    current_player_region = game_state.get_current_player_region()
    if current_player_region and hasattr(event_manager, "trigger_random_market_event"):
        triggered_event_log_msg = event_manager.trigger_random_market_event(
            region=current_player_region, game_state=game_state,
            player_inventory=player_inventory, ai_rivals=game_state.ai_rivals,
            show_event_message_callback=_capture_ui_msg, game_configs_data=game_configs,
            add_to_log_callback=_capture_log_msg,
        )
        if triggered_event_log_msg: # This specific function returns a single log string or None
             if isinstance(triggered_event_log_msg, str): # Ensure it's a string
                log_messages.append(triggered_event_log_msg)
             elif isinstance(triggered_event_log_msg, list): # If it somehow returns a list
                log_messages.extend(triggered_event_log_msg)

    return ui_messages, log_messages

def _process_ai_rivals(game_state: GameState, game_configs: Any) -> Tuple[List[str], List[str]]:
    """Processes turns for all AI rivals."""
    ui_messages: List[str] = []
    log_messages: List[str] = []

    def _capture_ui_msg(msg: str): ui_messages.append(msg)
    def _capture_log_msg(msg: str): log_messages.append(msg)

    for rival_instance in game_state.ai_rivals:
        market_impact.process_rival_turn(
            rival=rival_instance, all_regions_dict=game_state.all_regions,
            current_turn_number=game_state.current_day, game_configs=game_configs,
            add_to_log_cb=_capture_log_msg, show_on_screen_cb=_capture_ui_msg,
        )
    return ui_messages, log_messages

def _handle_player_blocking_events(
    game_state: GameState, player_inventory: PlayerInventory, game_configs: Any
) -> Tuple[Optional[Dict], List[str], Optional[int]]:
    """Handles random player-affecting blocking events like mugging or informant betrayal."""
    blocking_event_data: Optional[Dict] = None
    log_messages: List[str] = []
    informant_unavailable_until: Optional[int] = game_state.informant_unavailable_until_day # Keep existing if not changed

    current_player_region = game_state.get_current_player_region()
    if not current_player_region:
        return blocking_event_data, log_messages, informant_unavailable_until

    # Mugging Event
    is_mugging_event_active = any(
        isinstance(ev, MarketEvent) and ev.event_type == EventType.MUGGING
        for ev in current_player_region.active_market_events
    )
    if not is_mugging_event_active and random.random() < game_configs.MUGGING_EVENT_CHANCE:
        cash_loss_percentage = random.uniform(
            game_configs.MUGGING_CASH_LOSS_PERCENT_MIN, game_configs.MUGGING_CASH_LOSS_PERCENT_MAX
        )
        cash_lost = player_inventory.cash * cash_loss_percentage
        cash_lost = min(cash_lost, player_inventory.cash) # Cannot lose more than you have
        player_inventory.cash -= cash_lost

        title_mug = "Mugged!"
        messages_mug = [
            f"You were ambushed by thugs in {current_player_region.name.value}!",
            f"They managed to steal ${cash_lost:,.2f} from you."
        ]
        blocking_event_data = {"title": title_mug, "messages": messages_mug, "button_text": "Damn it!"}
        log_messages.append(f"Mugging event: Lost ${cash_lost:,.2f}.")
        return blocking_event_data, log_messages, informant_unavailable_until # Exit after one blocking event

    # Informant Betrayal Event
    betrayal_chance = getattr(game_configs, "INFORMANT_BETRAYAL_CHANCE", 0.03)
    trust_threshold = getattr(game_configs, "INFORMANT_TRUST_THRESHOLD_FOR_BETRAYAL", 20)
    unavailable_days = getattr(game_configs, "INFORMANT_BETRAYAL_UNAVAILABLE_DAYS", 7)
    # Use contact_trusts dictionary for informant trust
    current_informant_trust = player_inventory.contact_trusts.get(ContactID.INFORMANT, 100)
    
    informant_already_unavailable = game_state.informant_unavailable_until_day is not None and \
                                    game_state.current_day < game_state.informant_unavailable_until_day

    is_betrayal_event_active = any(isinstance(ev, MarketEvent) and ev.event_type == EventType.INFORMANT_BETRAYAL for ev in current_player_region.active_market_events)

    if not is_betrayal_event_active and not informant_already_unavailable and \
       current_informant_trust < trust_threshold and random.random() < betrayal_chance:
        
        informant_unavailable_until = game_state.current_day + unavailable_days
        
        original_trust = current_informant_trust
        # Update informant trust in the contact_trusts dictionary
        new_trust = max(0, current_informant_trust - game_configs.INFORMANT_BETRAYAL_TRUST_LOSS)
        player_inventory.contact_trusts[ContactID.INFORMANT] = new_trust
        trust_lost = original_trust - new_trust # Use new_trust for calculating lost amount
        heat_increase_betrayal = game_configs.INFORMANT_BETRAYAL_HEAT_INCREASE
        region_name_for_log_betrayal = getattr(current_player_region.name, "value", str(current_player_region.name))
        current_player_region.modify_heat(heat_increase_betrayal)

        title_betrayal = "Informant Betrayal!"
        messages_betrayal = [
            "Your informant sold you out to the authorities!",
            f"They will be unavailable for {unavailable_days} days.",
            f"Your trust with them has decreased by {trust_lost}.",
            f"Heat in {region_name_for_log_betrayal} has increased by {heat_increase_betrayal}."
        ]
        blocking_event_data = {"title": title_betrayal, "messages": messages_betrayal, "button_text": "Damn it!"}
        log_messages.append(f"Informant betrayal: Unavailable {unavailable_days}d. Trust -{trust_lost}. Heat +{heat_increase_betrayal} in {region_name_for_log_betrayal}.")
        return blocking_event_data, log_messages, informant_unavailable_until # Exit after one blocking event

    # Forced Fire Sale Event
    active_ffs_event = None
    for event_item in current_player_region.active_market_events:
        if event_item.event_type == EventType.FORCED_FIRE_SALE: active_ffs_event = event_item; break
    
    if active_ffs_event:
        total_player_drugs_quantity = sum(qty for qualities in player_inventory.items.values() for qty in qualities.values())
        if total_player_drugs_quantity > 0:
            ffs_qty_percent = getattr(game_configs, "FORCED_FIRE_SALE_QUANTITY_PERCENT", 0.15)
            ffs_penalty_percent = getattr(game_configs, "FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT", 0.30)
            ffs_min_cash_gain = getattr(game_configs, "FORCED_FIRE_SALE_MIN_CASH_GAIN", 50.0)
            drugs_sold_details_list = []
            total_cash_gained_ffs = 0.0
            total_units_sold_ffs = 0

            player_drug_items_ffs_copy = []
            for dn_enum, q_dict in player_inventory.items.items():
                for q_enum, qty_val in q_dict.items():
                        if qty_val > 0:
                            player_drug_items_ffs_copy.append({"name_enum": dn_enum, "quality_enum": q_enum, "current_qty": qty_val})

            for drug_item_data_ffs in player_drug_items_ffs_copy:
                drug_name_val_ffs = drug_item_data_ffs["name_enum"]
                quality_val_ffs = drug_item_data_ffs["quality_enum"]
                current_qty_ffs = drug_item_data_ffs["current_qty"]
                qty_to_sell_ffs = min(math.ceil(current_qty_ffs * ffs_qty_percent), current_qty_ffs)

                if qty_to_sell_ffs > 0:
                    market_sell_price_ffs = current_player_region.get_sell_price(drug_name_val_ffs, quality_val_ffs)
                    if market_sell_price_ffs <= 0: continue

                    discounted_price_ffs = round(max(game_configs.FORCED_SALE_MIN_PRICE_PER_UNIT, market_sell_price_ffs * (1.0 - ffs_penalty_percent)), 2)
                    cash_from_sale_ffs = qty_to_sell_ffs * discounted_price_ffs
                    total_cash_gained_ffs += cash_from_sale_ffs
                    player_inventory.remove_drug(drug_name_val_ffs, quality_val_ffs, qty_to_sell_ffs)
                    total_units_sold_ffs += qty_to_sell_ffs
                    drugs_sold_details_list.append(f"{qty_to_sell_ffs} {drug_name_val_ffs.value} ({quality_val_ffs.name})")

            if total_units_sold_ffs > 0 and total_cash_gained_ffs < ffs_min_cash_gain:
                total_cash_gained_ffs = ffs_min_cash_gain
            if total_units_sold_ffs > 0:
                player_inventory.cash += total_cash_gained_ffs
                heat_increase_ffs_val = game_configs.FORCED_FIRE_SALE_HEAT_INCREASE
                region_name_log_ffs_val = getattr(current_player_region.name, "value", str(current_player_region.name))
                current_player_region.modify_heat(heat_increase_ffs_val)

                ffs_title_val = "Forced Fire Sale!"
                sold_summary_str = ", ".join(drugs_sold_details_list) if drugs_sold_details_list else "assets"
                ffs_messages_list = [
                    "Unforeseen situation forces quick liquidation!",
                    f"Sold: {sold_summary_str}.",
                    f"Total cash gained: ${total_cash_gained_ffs:,.2f}.",
                    f"Heat in {region_name_log_ffs_val} +{heat_increase_ffs_val}."
                ]
                blocking_event_data = {"title": ffs_title_val, "messages": ffs_messages_list, "button_text": "Got it."}
                log_messages.append(f"Forced Fire Sale: Sold {sold_summary_str}. Cash +${total_cash_gained_ffs:,.2f}. Heat +{heat_increase_ffs_val} in {region_name_log_ffs_val}.")
            elif total_player_drugs_quantity > 0 :
                log_messages.append("Forced Fire Sale triggered, but no applicable drugs sold (e.g., market price was too low).")
    
    return blocking_event_data, log_messages, informant_unavailable_until

def _award_skill_points(
    game_state: GameState, player_inventory: PlayerInventory, game_configs: Any
) -> Tuple[List[str], List[str], int]:
    """Awards skill points to the player if criteria are met."""
    ui_messages: List[str] = []
    log_messages: List[str] = []
    skill_points_total = player_inventory.skill_points # Return current if not awarded

    if game_state.current_day > 0 and \
       game_state.current_day % game_configs.SKILL_POINTS_PER_X_DAYS == 0:
        player_inventory.skill_points += 1
        skill_points_total = player_inventory.skill_points
        ui_messages.append(f"Daily Update: +1 Skill Point. Total: {player_inventory.skill_points}")
        log_messages.append(f"Awarded skill point (daily). Total: {player_inventory.skill_points}")
    return ui_messages, log_messages, skill_points_total

def _check_for_bankruptcy(
    player_inventory: PlayerInventory, game_configs: Any
) -> Tuple[Optional[str], List[str]]:
    """Checks if the player has gone bankrupt."""
    game_over_msg = None
    log_messages: List[str] = []
    if player_inventory.cash < game_configs.BANKRUPTCY_THRESHOLD:
        game_over_msg = "GAME OVER: You have gone bankrupt!"
        log_messages.append(f"{game_over_msg} Cash: ${player_inventory.cash:.2f}, Threshold: ${game_configs.BANKRUPTCY_THRESHOLD:.2f}")
    return game_over_msg, log_messages

# --- Main Function ---

def perform_daily_updates(
    game_state_data: GameState,
    player_inventory_data: PlayerInventory,
    game_configs_data: Any,
) -> DailyUpdateResult:
    result = DailyUpdateResult()

    # 1. Debt Payments
    debt_game_over, debt_ui_msgs, debt_log_msgs = _handle_debt_payments(
        game_state_data, player_inventory_data, game_configs_data
    )
    result.ui_messages.extend(debt_ui_msgs)
    result.log_messages.extend(debt_log_msgs)
    if debt_game_over:
        result.game_over_message = debt_game_over
        return result

    # 2. Regional Updates
    _perform_regional_updates(game_state_data, player_inventory_data, game_configs_data) # Pass all required args

    # 3. Crypto Price Updates
    _update_crypto_prices(game_state_data, game_configs_data)

    # 4. Staking Rewards
    staking_ui_msgs = _process_staking_rewards(player_inventory_data, game_configs_data)
    result.ui_messages.extend(staking_ui_msgs)

    # 5. Laundering Arrival
    launder_ui_msgs, launder_log_msgs, processed, new_sc, new_day = _process_laundering_arrival(
        game_state_data, player_inventory_data
    )
    result.ui_messages.extend(launder_ui_msgs)
    result.log_messages.extend(launder_log_msgs)
    if processed:
        result.pending_laundered_sc_processed = True # Signal to app.py that player_inventory needs persistent update
        result.new_pending_laundered_sc = new_sc
        result.new_pending_laundered_sc_arrival_day = new_day


    # 6. Random Market Event Triggering
    event_ui_msgs, event_log_msgs = _trigger_random_market_event(
        game_state_data, player_inventory_data, game_configs_data
    )
    result.ui_messages.extend(event_ui_msgs)
    result.log_messages.extend(event_log_msgs)

    # 7. AI Rival Processing
    rival_ui_msgs, rival_log_msgs = _process_ai_rivals(game_state_data, game_configs_data)
    result.ui_messages.extend(rival_ui_msgs)
    result.log_messages.extend(rival_log_msgs)

    # 8. Player-Affecting Blocking Events
    # Only process if no game over yet and no blocking event from prior steps (though none currently set them)
    if result.game_over_message is None and result.blocking_event_data is None:
        blocking_event_data, blocking_log_msgs, informant_until = _handle_player_blocking_events(
            game_state_data, player_inventory_data, game_configs_data
        )
        result.log_messages.extend(blocking_log_msgs)
        if blocking_event_data:
            result.blocking_event_data = blocking_event_data
        if informant_until is not None and informant_until != game_state_data.informant_unavailable_until_day : # check if it changed
            result.informant_unavailable_until_day = informant_until # Signal to app.py to update game_state

    # 9. Skill Point Award
    skill_ui_msgs, skill_log_msgs, total_skill_pts = _award_skill_points(
        game_state_data, player_inventory_data, game_configs_data
    )
    result.ui_messages.extend(skill_ui_msgs)
    result.log_messages.extend(skill_log_msgs)
    if total_skill_pts != player_inventory_data.skill_points: # Check if points were actually awarded this turn
         result.skill_points_awarded_player_total = total_skill_pts # Update if changed

    # 10. Bankruptcy Check
    # Only check if no game over message has been set by previous steps
    if result.game_over_message is None:
        bankruptcy_game_over, bankruptcy_log_msgs = _check_for_bankruptcy(
            player_inventory_data, game_configs_data
        )
        result.log_messages.extend(bankruptcy_log_msgs)
        if bankruptcy_game_over:
            result.game_over_message = bankruptcy_game_over
            # No return here, let it fall through so all log messages are collected
            
    # X. Seasonal Event Updates (after most other daily state changes, before final checks like bankruptcy if effects matter)
    # Check and apply/end seasonal events. This might return a message for the UI.
    seasonal_event_message = seasonal_events_manager.check_and_update_seasonal_events(game_state_data, game_configs_data)
    if seasonal_event_message:
        result.ui_messages.append(seasonal_event_message)
        result.log_messages.append(f"Seasonal Event Update: {seasonal_event_message}")

    # Y. Opportunity Event Triggering (if no other major blocking event or game over)
    if result.game_over_message is None and result.blocking_event_data is None:
        opportunity_event_data = _try_trigger_opportunity_event(game_state_data, player_inventory_data, game_configs_data)
        if opportunity_event_data:
            result.blocking_event_data = opportunity_event_data # Use existing blocking_event_data structure
            # The message from the event itself will be part of the popup data.
            result.log_messages.append(f"Opportunity Event Triggered: {opportunity_event_data.get('title', 'Unknown Opportunity')}")

    return result


def _try_trigger_opportunity_event(
    game_state: GameState, player_inventory: PlayerInventory, game_configs: Any
) -> Optional[Dict[str, Any]]:
    """
    Attempts to trigger a random opportunity event.
    If triggered, prepares and returns the event data for UI display.
    """
    if random.random() < game_configs.OPPORTUNITY_EVENT_BASE_CHANCE:
        available_events = list(game_configs.OPPORTUNITY_EVENTS_DEFINITIONS.keys())
        if not available_events:
            return None
        
        event_type_enum = random.choice(available_events)
        event_def = game_configs.OPPORTUNITY_EVENTS_DEFINITIONS[event_type_enum]
        
        # Prepare dynamic data for the description template
        # This is highly dependent on the specific event templates
        description = event_def["description_template"]
        current_player_region = game_state.get_current_player_region()
        region_name = current_player_region.name.value if current_player_region else "an unknown location"

        if event_type_enum == EventType.RIVAL_STASH_LEAKED:
            # Example: Pick a random high-tier drug and quantity
            # This needs a proper way to determine high-tier drugs and quantities
            possible_drugs = [DrugName.COKE, DrugName.HEROIN, DrugName.SPEED] # Example high-tier
            drug_name_stolen = random.choice(possible_drugs)
            quantity_stolen = random.randint(15, 40) # Example quantity
            description = description.format(drug_name=drug_name_stolen.value, quantity=quantity_stolen)
            # Store these dynamic values if outcomes need them
            event_def["runtime_params"] = {"drug_name": drug_name_stolen, "quantity": quantity_stolen, "region_name": region_name}
        
        elif event_type_enum == EventType.URGENT_DELIVERY:
            possible_drugs = [d for d in player_inventory.items if any(q > 0 for q in player_inventory.items[d].values())]
            if not possible_drugs: return None # Player has no drugs to deliver
            
            drug_to_deliver = random.choice(possible_drugs)
            # Find a quality of that drug the player has
            player_qualities = [q for q, qty in player_inventory.items[drug_to_deliver].items() if qty > 0]
            if not player_qualities: return None # Should not happen if possible_drugs is populated
            quality_to_deliver = random.choice(player_qualities)
            
            max_quantity = player_inventory.get_quantity(drug_to_deliver, quality_to_deliver)
            if max_quantity == 0: return None

            quantity_needed = random.randint(min(5, max_quantity), min(20, max_quantity)) # Deliver between 5 and 20, or max owned if less
            
            possible_regions = [r for r in game_state.all_regions.values() if r.name != current_player_region.name] if current_player_region else list(game_state.all_regions.values())
            if not possible_regions: return None # No other region to deliver to
            target_region = random.choice(possible_regions)
            
            # Calculate reward: e.g., 20-50% over current sell price (if available)
            base_sell_price = target_region.get_sell_price(drug_to_deliver, quality_to_deliver, player_inventory, game_state)
            if base_sell_price <=0: base_sell_price = game_configs.MINIMUM_DRUG_PRICE * quantity_needed * 2 # fallback if not sold there
            
            reward_premium_per_unit = base_sell_price * random.uniform(0.2, 0.5) 
            
            description = description.format(
                quantity=quantity_needed, 
                drug_name=drug_to_deliver.value, 
                target_region_name=target_region.name.value,
                reward_per_unit=reward_premium_per_unit
            )
            event_def["runtime_params"] = {
                "drug_name": drug_to_deliver, 
                "quality": quality_to_deliver,
                "quantity": quantity_needed, 
                "target_region_name": target_region.name,
                "reward_per_unit": reward_premium_per_unit,
                "total_base_value": base_sell_price * quantity_needed # For calculating final payout
            }
            # Dynamically update choice text for URGENT_DELIVERY
            for choice in event_def["choices"]:
                if choice.get("id") == "accept_delivery":
                    choice["text"] = f"Accept (Need {quantity_needed} {drug_to_deliver.value})"


        elif event_type_enum == EventType.EXPERIMENTAL_DRUG_BATCH:
            possible_drugs = [DrugName.PILLS, DrugName.SPEED] # Example
            drug_name_experimental = random.choice(possible_drugs)
            quantity_experimental = random.randint(20, 50)
            cost_experimental = quantity_experimental * random.randint(5, 20) # Low cost
            description = description.format(drug_name=drug_name_experimental.value, quantity=quantity_experimental, cost=cost_experimental)
            event_def["runtime_params"] = {"drug_name": drug_name_experimental, "quantity_base": quantity_experimental, "cost": cost_experimental}

        # Prepare data for the blocking event popup view
        # This structure should be compatible with draw_blocking_event_popup
        # OR a new view / modified view is needed. For now, try to make it compatible.
        # The view expects "title", "messages" (list of strings), and buttons are built from "choices".
        popup_data = {
            "event_type_id": event_type_enum.value, # Store the actual enum value string
            "title": event_def["name"],
            "messages": [description], # Description becomes the main message
            "choices": event_def["choices"], # Pass choices directly
            "is_opportunity_event": True, # Flag for UI to know this needs special handling
            "runtime_params": event_def.get("runtime_params", {}) # Pass dynamic params for resolution
        }
        return popup_data
    return None

[end of src/mechanics/daily_updates.py]
