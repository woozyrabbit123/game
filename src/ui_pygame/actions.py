"""
Action functions for Project Narco-Syndicate Pygame UI.
Split from app.py for modularity.
"""

import functools
import math # Added for math.ceil
import random
from typing import Any

# Third-party imports (none in this file)

# Local application imports
from .. import game_configs # Keep one import for game_configs
from ..core.enums import CryptoCoin, DrugName, DrugQuality, RegionName, SkillID
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..mechanics import event_manager, market_impact
# from .ui_components import Button  # Unused at module level
from .ui_hud import add_message_to_log, show_event_message as show_event_message_external


# All action functions will be moved here from app.py
# This file will be filled in the next step.


def set_active_prompt_message(message: str, duration_frames: int):
    from . import state

    state.active_prompt_message = message
    state.prompt_message_timer = duration_frames


# --- Action Functions ---
def action_open_main_menu():
    from . import state

    state.current_view = "main_menu"


def action_open_market():
    from . import state

    state.current_view = "market"


def action_open_inventory():
    from . import state

    state.current_view = "inventory"


def action_open_travel():
    from . import state

    state.current_view = "travel"


def action_open_tech_contact():
    from . import state

    state.current_view = "tech_contact"


def action_open_skills():
    from . import state

    state.current_view = "skills"


def action_open_upgrades():
    from . import state

    state.current_view = "upgrades"


def action_open_informant():
    from . import state

    state.current_view = "informant"


def action_cancel_transaction():
    from . import state

    # Properly update the state module's variables
    if state.current_view in ["market_buy_input", "market_sell_input"]:
        state.current_view = "market"
    elif state.current_view in ["tech_input_coin_select", "tech_input_amount"]:
        state.current_view = "tech_contact"
    state.quantity_input_string = ""
    state.tech_input_string = ""
    state.tech_transaction_in_progress = None
    state.active_prompt_message = None
    # Optionally, reset other transaction-related state if needed
    # game_state_data_cache is GameState instance, get_current_player_region() returns Region object
    from .setup_ui import (
        setup_buttons,
    )  # Import here to avoid circular if setup_ui imports actions

    setup_buttons(
        state.game_state_data_cache,
        state.player_inventory_cache,
        state.game_configs_data_cache,
        state.game_state_data_cache.get_current_player_region(),
    )


def action_confirm_transaction(
    player_inv: PlayerInventory, market_region: Region, game_state_instance: Any
):  # game_state_instance is GameState
    from . import state
    from .setup_ui import setup_buttons
    from .ui_hud import show_event_message as show_event_message_external

    if (
        not state.quantity_input_string.isdigit()
        or int(state.quantity_input_string) <= 0
    ):
        show_event_message_external("Error: Invalid quantity.")
        state.quantity_input_string = ""
        return
    quantity = int(state.quantity_input_string)
    if state.current_transaction_type == "buy":
        cost = quantity * state.price_for_transaction
        if cost > player_inv.cash:
            show_event_message_external("Error: Not enough cash.")
        elif quantity > state.available_for_transaction:
            show_event_message_external("Error: Not enough market stock.")
        elif player_inv.current_load + quantity > player_inv.max_capacity:
            show_event_message_external("Error: Not enough space.")
        else:
            drug_enum = state.drug_for_transaction
            if isinstance(drug_enum, str):  # Ensure enum type
                drug_enum = next(
                    (d for d in DrugName if d.value == state.drug_for_transaction),
                    state.drug_for_transaction,
                )
            player_inv.cash -= cost
            player_inv.add_drug(drug_enum, state.quality_for_transaction, quantity)
            market_region.update_stock_on_buy(
                drug_enum, state.quality_for_transaction, quantity
            )
            market_impact.apply_player_buy_impact(
                market_region, drug_enum.value, quantity
            )  # drug_enum.value is fine
            show_event_message_external(
                f"Bought {quantity} {drug_enum.value} ({state.quality_for_transaction.name})."
            )
            state.current_view = "market"
    elif state.current_transaction_type == "sell":
        if (
            quantity > state.available_for_transaction
        ):  # available_for_transaction is player's stock here
            show_event_message_external("Error: Not enough to sell.")
        else:
            drug_enum = state.drug_for_transaction
            if isinstance(drug_enum, str):  # Ensure enum type
                drug_enum = next(
                    (d for d in DrugName if d.value == state.drug_for_transaction),
                    state.drug_for_transaction,
                )
            player_inv.cash += quantity * state.price_for_transaction
            player_inv.remove_drug(drug_enum, state.quality_for_transaction, quantity)
            market_region.update_stock_on_sell(
                drug_enum, state.quality_for_transaction, quantity
            )
            drug_tier = market_region.drug_market_data[drug_enum].get("tier", 1)
            # Assuming game_configs_data_cache is correctly populated in state module or passed differently
            heat_per_unit = (
                state.game_configs_data_cache.HEAT_FROM_SELLING_DRUG_TIER.get(
                    drug_tier, 1
                )
            )
            total_heat = heat_per_unit * quantity

            if (
                SkillID.COMPARTMENTALIZATION.value in player_inv.unlocked_skills
            ):  # Use .value for enum comparison if unlocked_skills stores strings
                reduction = (
                    game_configs.COMPARTMENTALIZATION_HEAT_REDUCTION_PERCENT
                )
                original_heat = total_heat
                total_heat *= 1 - reduction
                total_heat = int(math.ceil(total_heat))
                add_message_to_log(
                    f"Compartmentalization skill reduced heat from {original_heat} to {total_heat}."
                )

            market_region.modify_heat(total_heat)
            market_impact.apply_player_sell_impact(
                player_inv,
                market_region,
                drug_enum,  # Pass enum directly
                quantity,
                state.game_configs_data_cache,
            )
            show_event_message_external(
                f"Sold {quantity} {drug_enum.value}. Heat +{total_heat} in {market_region.name.value}."
            )
            state.current_view = "market"
    state.quantity_input_string = ""
    # Pass market_region (Region object), game_state_instance is GameState
    setup_buttons(
        game_state_instance, player_inv, state.game_configs_data_cache, market_region
    )


def action_confirm_tech_operation(
    player_inv: PlayerInventory, game_state_instance: Any, game_configs: Any
):  # game_state_instance is GameState
    from . import state
    from .setup_ui import (
        setup_buttons,
    )  # Import here to avoid circular if setup_ui imports actions
    from .ui_hud import show_event_message as show_event_message_external

    if (
        not state.tech_input_string.replace(".", "", 1).isdigit()
        or float(state.tech_input_string) <= 0
    ):
        show_event_message_external("Error: Invalid amount.")
        state.tech_input_string = ""
        return
    amount = float(state.tech_input_string)
    base_heat = (
        game_configs.HEAT_FROM_CRYPTO_TRANSACTION
    )  # Assuming game_configs is the module
    effective_heat = base_heat
    # Assuming player_inv.unlocked_skills stores SkillID enum members or their .value strings
    if (
        SkillID.DIGITAL_FOOTPRINT in player_inv.unlocked_skills
        or SkillID.DIGITAL_FOOTPRINT.value in player_inv.unlocked_skills
    ):
        effective_heat *= 1 - game_configs.DIGITAL_FOOTPRINT_HEAT_REDUCTION_PERCENT
    if player_inv.has_secure_phone:
        effective_heat *= 1 - game_configs.SECURE_PHONE_HEAT_REDUCTION_PERCENT
    effective_heat = int(round(effective_heat))

    current_player_region_obj = (
        game_state_instance.get_current_player_region()
    )  # Get Region object
    region_name_str = (
        current_player_region_obj.name.value
        if hasattr(current_player_region_obj.name, "value")
        else current_player_region_obj.name
    )

    if state.tech_transaction_in_progress == "buy_crypto":
        price = game_state_instance.current_crypto_prices.get(
            state.coin_for_tech_transaction, 0
        )
        fee = (
            amount
            * price
            * game_configs.TECH_CONTACT_SERVICES["CRYPTO_TRADE"]["fee_buy_sell"]
        )
        if price == 0:
            show_event_message_external("Error: Price unavailable.")
            return
        if player_inv.cash >= amount * price + fee:
            player_inv.cash -= amount * price + fee
            player_inv.add_crypto(state.coin_for_tech_transaction, amount)
            if effective_heat > 0 and current_player_region_obj:
                current_player_region_obj.modify_heat(effective_heat)
            show_event_message_external(
                f"Bought {amount:.4f} {state.coin_for_tech_transaction.value}. Heat +{effective_heat} in {region_name_str}."
            )
        else:
            show_event_message_external("Error: Not enough cash.")
            state.tech_input_string = ""  # Clear input only on error needing re-entry
            return
    elif state.tech_transaction_in_progress == "sell_crypto":
        price = game_state_instance.current_crypto_prices.get(
            state.coin_for_tech_transaction, 0
        )
        fee = (
            amount
            * price
            * game_configs.TECH_CONTACT_SERVICES["CRYPTO_TRADE"]["fee_buy_sell"]
        )
        if price == 0:
            show_event_message_external("Error: Price unavailable.")
            return
        if player_inv.crypto_wallet.get(state.coin_for_tech_transaction, 0) >= amount:
            player_inv.remove_crypto(state.coin_for_tech_transaction, amount)
            player_inv.cash += amount * price - fee
            if effective_heat > 0 and current_player_region_obj:
                current_player_region_obj.modify_heat(effective_heat)
            show_event_message_external(
                f"Sold {amount:.4f} {state.coin_for_tech_transaction.value}. Heat +{effective_heat} in {region_name_str}."
            )
        else:
            show_event_message_external("Error: Not enough crypto.")
            state.tech_input_string = ""
            return
    elif state.tech_transaction_in_progress == "launder_cash":
        fee = amount * game_configs.TECH_CONTACT_SERVICES["LAUNDER_CASH"]["fee"]
        launder_heat = int(amount * 0.05)  # Specific heat calculation for laundering
        if player_inv.cash >= (amount + fee):
            player_inv.cash -= amount + fee
            player_inv.pending_laundered_sc += amount
            # current_day from game_state_instance
            player_inv.pending_laundered_sc_arrival_day = (
                game_state_instance.current_day + game_configs.LAUNDERING_DELAY_DAYS
            )
            if launder_heat > 0 and current_player_region_obj:
                current_player_region_obj.modify_heat(launder_heat)
            show_event_message_external(
                f"Laundered ${amount:,.2f}. Fee ${fee:,.2f}. Arrives day {player_inv.pending_laundered_sc_arrival_day}. Heat +{launder_heat} in {region_name_str}."
            )
        else:
            show_event_message_external("Error: Not enough cash for amount + fee.")
            state.tech_input_string = ""
            return
    elif state.tech_transaction_in_progress == "stake_dc":
        if (
            state.coin_for_tech_transaction == CryptoCoin.DRUG_COIN
            and player_inv.crypto_wallet.get(CryptoCoin.DRUG_COIN, 0) >= amount
        ):
            player_inv.remove_crypto(CryptoCoin.DRUG_COIN, amount)
            # Ensure 'staked_amount' is initialized if it might not exist
            player_inv.staked_drug_coin["staked_amount"] = (
                player_inv.staked_drug_coin.get("staked_amount", 0) + amount
            )
            show_event_message_external(f"Staked {amount:.4f} DC.")
        else:
            show_event_message_external(
                f"Error: Not enough {CryptoCoin.DRUG_COIN.value} or wrong coin."
            )
            state.tech_input_string = ""
            return
    elif state.tech_transaction_in_progress == "unstake_dc":
        if (
            state.coin_for_tech_transaction == CryptoCoin.DRUG_COIN
            and player_inv.staked_drug_coin.get("staked_amount", 0) >= amount
        ):
            player_inv.staked_drug_coin["staked_amount"] -= amount
            pending = player_inv.staked_drug_coin.get("pending_rewards", 0.0)
            player_inv.add_crypto(CryptoCoin.DRUG_COIN, amount + pending)
            player_inv.staked_drug_coin["pending_rewards"] = 0.0
            show_event_message_external(
                f"Unstaked {amount:.4f} DC. Rewards collected: {pending:.4f} DC."
            )
        else:
            show_event_message_external(
                f"Error: Not enough staked {CryptoCoin.DRUG_COIN.value} or wrong coin."
            )
            state.tech_input_string = ""
            return

    state.current_view = "tech_contact"
    state.tech_input_string = ""
    state.tech_transaction_in_progress = None
    # setup_buttons expects game_state_instance, player_inv, game_configs, and a Region object
    setup_buttons(
        game_state_instance, player_inv, game_configs, current_player_region_obj
    )


def action_initiate_buy(drug_enum, quality_enum, buy_price, market_stock):
    """
    Initiate a buy transaction for the given drug and quality.
    Sets up transaction state and switches to the buy input view.
    """
    from . import state

    state.current_transaction_type = "buy"
    state.drug_for_transaction = drug_enum
    state.quality_for_transaction = quality_enum
    state.price_for_transaction = buy_price
    state.available_for_transaction = market_stock
    state.quantity_input_string = ""
    state.current_view = "market_buy_input"
    state.active_prompt_message = None
    state.prompt_message_timer = 0


def action_unlock_skill(
    player_inv: PlayerInventory,
    skill_id_str: str,
    skill_name_str: str,
    skill_cost: int,
    game_state_cache: Any,
    game_configs_data_cache: Any,
):
    """Action to attempt unlocking a skill."""
    from . import state  # For setup_buttons and show_event_message
    from .setup_ui import setup_buttons

    if player_inv.unlock_skill(skill_id_str, skill_cost):
        show_event_message_external(f"Skill Unlocked: {skill_name_str}!")
        add_message_to_log(
            f"Player unlocked skill: {skill_name_str} (ID: {skill_id_str}) for {skill_cost} SP. SP remaining: {player_inv.skill_points}"
        )
    else:
        show_event_message_external("Not enough skill points.")
        add_message_to_log(
            f"Player failed to unlock skill: {skill_name_str} (ID: {skill_id_str}). Needed {skill_cost} SP, has {player_inv.skill_points}"
        )

    # Refresh buttons as skill availability might change button states
    setup_buttons(
        game_state_cache,
        player_inv,
        game_configs_data_cache,
        game_state_cache.current_player_region,
    )


def action_initiate_sell(drug_enum, quality_enum, sell_price, player_has_stock):
    """
    Initiate a sell transaction for the given drug and quality.
    Sets up transaction state and switches to the sell input view.
    """
    from . import state

    state.current_transaction_type = "sell"
    state.drug_for_transaction = drug_enum
    state.quality_for_transaction = quality_enum
    state.price_for_transaction = sell_price
    state.available_for_transaction = player_has_stock
    state.quantity_input_string = ""
    state.current_view = "market_sell_input"
    state.active_prompt_message = None
    state.prompt_message_timer = 0


def action_open_quality_select(drug_enum):
    """
    Opens the drug quality selection UI for the given drug.
    Sets up state and switches to the quality select view.
    """
    from . import state
    from .setup_ui import (
        setup_buttons,
    )  # Import here to avoid circular if setup_ui imports actions

    state.drug_for_transaction = drug_enum
    state.current_view = "market_quality_select"
    state.quality_for_transaction = None
    state.active_prompt_message = None
    state.prompt_message_timer = 0
    # game_state_data_cache is GameState instance, get_current_player_region() returns Region object
    setup_buttons(
        state.game_state_data_cache,
        state.player_inventory_cache,
        state.game_configs_data_cache,
        state.game_state_data_cache.get_current_player_region(),
    )


def action_travel_to_region(
    dest_region_obj: Region, player_inv: PlayerInventory, game_state_instance: Any
):  # game_state_instance is GameState
    """
    Implements travel logic: deducts cost, moves player, triggers police stop, advances day, and updates systems.
    """
    from . import state  # UI state
    from .ui_hud import show_event_message as show_event_message_external
    from .setup_ui import (
        setup_buttons,
    )  # Import here to avoid circular if setup_ui imports actions
    from src.mechanics.event_manager import (
        check_and_trigger_police_stop,
        update_active_events,
    )

    # CRYPTO_VOLATILITY, CRYPTO_MIN_PRICE are part of game_configs, which should be available
    # via state.game_configs_data_cache or directly imported if not changing.

    travel_cost = state.game_configs_data_cache.TRAVEL_COST_CASH
    prev_region = (
        game_state_instance.get_current_player_region()
    )  # Get current region object

    if player_inv.cash < travel_cost:
        show_event_message_external("Not enough cash to travel.")
        return

    player_inv.cash -= travel_cost
    game_state_instance.set_current_player_region(
        dest_region_obj.name
    )  # Set by RegionName enum

    # Advance day and update systems
    game_state_instance.current_day += 1  # Use GameState's current_day

    # Phase progression - Assuming state.campaign_phase and state.phase_thresholds are UI-specific progression
    # If game_state_instance.difficulty_level needs to be set, it should be an attribute on GameState
    # For now, this part remains as is, if `difficulty_level` was not part of old game_state.
    for i, threshold in enumerate(
        state.phase_thresholds
    ):  # state.phase_thresholds is UI state
        if (
            game_state_instance.current_day <= threshold
        ):  # Compare with GameState's current_day
            state.campaign_phase = i + 1  # UI state campaign_phase
            break
    # game_state_instance.difficulty_level = state.campaign_phase # If difficulty_level were part of GameState

    current_player_region_obj = (
        game_state_instance.get_current_player_region()
    )  # Get new current region
    if current_player_region_obj:
        update_active_events(current_player_region_obj)  # Pass Region object

    # Call update_daily_crypto_prices on the GameState instance
    # Assuming CRYPTO_VOLATILITY and CRYPTO_MIN_PRICE are accessible from game_configs_data_cache
    game_state_instance.update_daily_crypto_prices(
        state.game_configs_data_cache.CRYPTO_VOLATILITY,
        state.game_configs_data_cache.CRYPTO_MIN_PRICE,
    )

    # Laundering arrival
    if (
        hasattr(player_inv, "pending_laundered_sc_arrival_day")
        and player_inv.pending_laundered_sc_arrival_day is not None
        and player_inv.pending_laundered_sc_arrival_day
        == game_state_instance.current_day
    ):  # Compare with GameState's current_day
        # Use a valid default coin like BITCOIN if STABLE_COIN does not exist
        default_laundered_coin = CryptoCoin.BITCOIN  # Changed default
        laundered_coin_to_use = getattr(
            player_inv, "laundered_crypto_type", default_laundered_coin
        )
        player_inv.crypto_wallet[laundered_coin_to_use] = (
            player_inv.crypto_wallet.get(laundered_coin_to_use, 0.0)
            + player_inv.pending_laundered_sc
        )
        player_inv.pending_laundered_sc = 0.0
        player_inv.pending_laundered_sc_arrival_day = None

    # Police stop event (risk based on region heat)
    if current_player_region_obj:
        police_event_triggered = check_and_trigger_police_stop(
            current_player_region_obj, player_inv, game_state_instance
        )  # Pass GameState instance
    else:
        police_event_triggered = False  # Should not happen if dest_region_obj was valid

    # Daily Heat Decay for Player
    if hasattr(player_inv, "heat"):
        base_decay = (
            state.game_configs_data_cache.BASE_DAILY_HEAT_DECAY
        )  # Use state-cached config
        effective_decay = base_decay

        if SkillID.GHOST_PROTOCOL.value in player_inv.unlocked_skills:
            boost_percent = (
                state.game_configs_data_cache.GHOST_PROTOCOL_DECAY_BOOST_PERCENT
            )  # Use state-cached config
            additional_decay = math.floor(
                base_decay * boost_percent
            )  # math.floor ensures integer decay
            effective_decay += additional_decay

        if player_inv.heat > 0:
            original_player_heat = player_inv.heat
            player_inv.heat = max(0, player_inv.heat - effective_decay)
            if (
                player_inv.heat < original_player_heat
            ):  # Log only if heat actually changed
                add_message_to_log(
                    f"Player daily heat decay: {effective_decay} (Base: {base_decay}). "
                    f"Player heat reduced from {original_player_heat} to {player_inv.heat}."
                )
        elif (
            effective_decay > 0
        ):  # If heat was already 0, but decay mechanism is active
            add_message_to_log(
                f"Player daily heat decay ran ({effective_decay} potential). Player heat remains 0."
            )

    if police_event_triggered:
        state.current_view = "blocking_event_popup"
        show_event_message_external("Police stop! Event triggered.")
    else:
        show_event_message_external(
            f"Traveled from {getattr(prev_region.name, 'value', prev_region.name)} to {getattr(dest_region_obj.name, 'value', dest_region_obj.name)}."
        )
        state.current_view = "market"
    # Use game_state_instance, and get_current_player_region() for the updated region object
    setup_buttons(
        game_state_instance,
        player_inv,
        state.game_configs_data_cache,
        game_state_instance.get_current_player_region(),
    )


def action_initiate_tech_operation(operation_type):
    """
    Placeholder for initiating a tech operation (buy/sell crypto, launder, stake, etc.).
    Sets up the transaction type and switches to the appropriate UI view.
    """
    from . import state

    state.tech_transaction_in_progress = operation_type
    if operation_type in ["buy_crypto", "sell_crypto", "stake_dc", "unstake_dc"]:
        state.current_view = "tech_input_coin_select"
    elif operation_type == "launder_cash":
        state.current_view = "tech_input_amount"
    state.tech_input_string = ""
    state.active_prompt_message = None
    state.prompt_message_timer = 0
