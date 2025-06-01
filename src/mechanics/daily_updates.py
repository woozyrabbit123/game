# src/mechanics/daily_updates.py
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from ..core.enums import CryptoCoin, EventType, SkillID
from ..core.market_event import MarketEvent # Corrected import for MarketEvent
from ..core.player_inventory import PlayerInventory
from ..core.region import Region
from ..game_state import GameState
from ..mechanics import event_manager, market_impact
# from .. import game_configs as game_configs_module # Not importing directly


class DailyUpdateResult:
    def __init__(self):
        self.game_over_message: Optional[str] = None
        self.blocking_event_data: Optional[Dict] = None
        self.ui_messages: List[str] = []
        self.log_messages: List[str] = []
        self.skill_points_awarded_player_total: int = 0
        self.informant_unavailable_until_day: Optional[int] = None
        self.pending_laundered_sc_processed: bool = False
        self.new_pending_laundered_sc: float = 0.0
        self.new_pending_laundered_sc_arrival_day: Optional[int] = None

def perform_daily_updates(
    game_state_data: GameState,
    player_inventory_data: PlayerInventory,
    game_configs_data: Any,
) -> DailyUpdateResult:
    result = DailyUpdateResult()

    # --- Debt Payments ---
    if not player_inventory_data.debt_payment_1_paid and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_1_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_1_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_1_AMOUNT
            player_inventory_data.debt_payment_1_paid = True
            result.ui_messages.append("Debt Payment 1 made!")
            result.log_messages.append(f"Paid ${game_configs_data.DEBT_PAYMENT_1_AMOUNT:,.0f} (Debt 1).")
        else:
            result.game_over_message = "GAME OVER: Failed Debt Payment 1!"
            result.log_messages.append(result.game_over_message)
            return result

    if player_inventory_data.debt_payment_1_paid and not player_inventory_data.debt_payment_2_paid and \
       game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_2_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_2_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_2_AMOUNT
            player_inventory_data.debt_payment_2_paid = True
            result.ui_messages.append("Debt Payment 2 made!")
            result.log_messages.append(f"Paid ${game_configs_data.DEBT_PAYMENT_2_AMOUNT:,.0f} (Debt 2).")
        else:
            result.game_over_message = "GAME OVER: Failed Debt Payment 2!"
            result.log_messages.append(result.game_over_message)
            return result

    if player_inventory_data.debt_payment_1_paid and player_inventory_data.debt_payment_2_paid and \
       not player_inventory_data.debt_payment_3_paid and game_state_data.current_day >= game_configs_data.DEBT_PAYMENT_3_DUE_DAY:
        if player_inventory_data.cash >= game_configs_data.DEBT_PAYMENT_3_AMOUNT:
            player_inventory_data.cash -= game_configs_data.DEBT_PAYMENT_3_AMOUNT
            player_inventory_data.debt_payment_3_paid = True
            result.ui_messages.append("Final debt paid! You are free!")
            result.log_messages.append(f"Paid ${game_configs_data.DEBT_PAYMENT_3_AMOUNT:,.0f} (Final Debt). You are FREE!")
        else:
            result.game_over_message = "GAME OVER: Failed Final Debt Payment!"
            result.log_messages.append(result.game_over_message)
            return result

    # --- Regional Updates ---
    for r_name, r_obj in game_state_data.all_regions.items():
        if hasattr(r_obj, "restock_market"): r_obj.restock_market()
        market_impact.decay_regional_heat(r_obj, 1.0, player_inventory_data, game_configs_data)
        market_impact.decay_player_market_impact(r_obj)
        market_impact.decay_rival_market_impact(r_obj, game_state_data.current_day)
        event_manager.update_active_events(r_obj)

    game_state_data.update_daily_crypto_prices(game_configs_data.CRYPTO_VOLATILITY, game_configs_data.CRYPTO_MIN_PRICE)

    # --- Staking Rewards ---
    if hasattr(player_inventory_data, "staked_drug_coin") and \
       player_inventory_data.staked_drug_coin.get("staked_amount", 0.0) > 0 and \
       hasattr(game_configs_data, "DC_STAKING_DAILY_RETURN_PERCENT"):
        reward = player_inventory_data.staked_drug_coin["staked_amount"] * game_configs_data.DC_STAKING_DAILY_RETURN_PERCENT
        player_inventory_data.staked_drug_coin["pending_rewards"] = player_inventory_data.staked_drug_coin.get("pending_rewards", 0.0) + reward
        if reward > 1e-5:
            result.ui_messages.append(f"Accrued {reward:.4f} DC rewards. Collect at Tech Contact.")

    # --- Laundering Arrival ---
    if hasattr(player_inventory_data, "pending_laundered_sc_arrival_day") and \
       player_inventory_data.pending_laundered_sc_arrival_day is not None and \
       game_state_data.current_day >= player_inventory_data.pending_laundered_sc_arrival_day:
        amount_laundered = player_inventory_data.pending_laundered_sc
        stable_coin_enum = getattr(CryptoCoin, "STABLE_COIN", CryptoCoin.DRUG_COIN)
        player_inventory_data.add_crypto(stable_coin_enum, amount_laundered)
        result.ui_messages.append(f"{amount_laundered:.2f} SC (laundered) arrived.")
        result.log_messages.append(f"Laundered cash arrived: {amount_laundered:.2f} SC.")
        result.pending_laundered_sc_processed = True
        result.new_pending_laundered_sc = 0.0
        result.new_pending_laundered_sc_arrival_day = None

    # --- Event Triggering Callbacks ---
    def _capture_ui_msg(msg: str): result.ui_messages.append(msg)
    def _capture_log_msg(msg: str): result.log_messages.append(msg)

    current_player_region = game_state_data.get_current_player_region()
    if current_player_region and hasattr(event_manager, "trigger_random_market_event"):
        triggered_event_log_msg = event_manager.trigger_random_market_event(
            region=current_player_region, game_state=game_state_data,
            player_inventory=player_inventory_data, ai_rivals=game_state_data.ai_rivals,
            show_event_message_callback=_capture_ui_msg, game_configs_data=game_configs_data,
            add_to_log_callback=_capture_log_msg,
        )
        if triggered_event_log_msg: result.log_messages.append(triggered_event_log_msg)

    # --- Process AI Rivals ---
    for rival_instance in game_state_data.ai_rivals:
        market_impact.process_rival_turn(
            rival=rival_instance, all_regions_dict=game_state_data.all_regions,
            current_turn_number=game_state_data.current_day, game_configs=game_configs_data,
            add_to_log_cb=_capture_log_msg, show_on_screen_cb=_capture_ui_msg,
        )

    # --- Player-Affecting Blocking Events ---
    if current_player_region and result.game_over_message is None and result.blocking_event_data is None:
        # Mugging Event
        is_mugging_event_active = any(
            isinstance(ev, MarketEvent) and ev.event_type == EventType.MUGGING
            for ev in current_player_region.active_market_events
        )
        if not is_mugging_event_active and random.random() < game_configs_data.MUGGING_EVENT_CHANCE:
            cash_loss_percentage = random.uniform(
                game_configs_data.MUGGING_CASH_LOSS_PERCENT_MIN, game_configs_data.MUGGING_CASH_LOSS_PERCENT_MAX
            )
            cash_lost = player_inventory_data.cash * cash_loss_percentage
            cash_lost = min(cash_lost, player_inventory_data.cash)
            player_inventory_data.cash -= cash_lost

            title_mug = "Mugged!"
            messages_mug = [
                f"You were ambushed by thugs in {current_player_region.name.value}!",
                f"They managed to steal ${cash_lost:,.2f} from you."
            ]
            result.blocking_event_data = {"title": title_mug, "messages": messages_mug, "button_text": "Damn it!"}
            result.log_messages.append(f"Mugging event: Lost ${cash_lost:,.2f}.")

        # Informant Betrayal Event (only if no other blocking event has occurred this cycle)
        if result.blocking_event_data is None:
            betrayal_chance = getattr(game_configs_data, "INFORMANT_BETRAYAL_CHANCE", 0.03)
            trust_threshold = getattr(game_configs_data, "INFORMANT_TRUST_THRESHOLD_FOR_BETRAYAL", 20)
            unavailable_days = getattr(game_configs_data, "INFORMANT_BETRAYAL_UNAVAILABLE_DAYS", 7)
            current_informant_trust = getattr(player_inventory_data, "informant_trust", 100)
            informant_already_unavailable = game_state_data.informant_unavailable_until_day is not None and \
                                            game_state_data.current_day < game_state_data.informant_unavailable_until_day

            is_betrayal_event_active = any(isinstance(ev, MarketEvent) and ev.event_type == EventType.INFORMANT_BETRAYAL for ev in current_player_region.active_market_events)

            if not is_betrayal_event_active and not informant_already_unavailable and \
               current_informant_trust < trust_threshold and random.random() < betrayal_chance:

                result.informant_unavailable_until_day = game_state_data.current_day + unavailable_days
                # game_state_data.informant_unavailable_until_day = result.informant_unavailable_until_day # app.py will set this from result

                original_trust = current_informant_trust
                player_inventory_data.informant_trust = max(0, current_informant_trust - game_configs_data.INFORMANT_BETRAYAL_TRUST_LOSS)
                trust_lost = original_trust - player_inventory_data.informant_trust
                heat_increase_betrayal = game_configs_data.INFORMANT_BETRAYAL_HEAT_INCREASE
                region_name_for_log_betrayal = getattr(current_player_region.name, "value", str(current_player_region.name))
                current_player_region.modify_heat(heat_increase_betrayal)

                title_betrayal = "Informant Betrayal!"
                messages_betrayal = [
                    "Your informant sold you out to the authorities!",
                    f"They will be unavailable for {unavailable_days} days.",
                    f"Your trust with them has decreased by {trust_lost}.",
                    f"Heat in {region_name_for_log_betrayal} has increased by {heat_increase_betrayal}."
                ]
                result.blocking_event_data = {"title": title_betrayal, "messages": messages_betrayal, "button_text": "Damn it!"}
                result.log_messages.append(f"Informant betrayal: Unavailable {unavailable_days}d. Trust -{trust_lost}. Heat +{heat_increase_betrayal} in {region_name_for_log_betrayal}.")

        # Forced Fire Sale Event (only if no other blocking event has occurred this cycle)
        if result.blocking_event_data is None:
            active_ffs_event = None
            for event_item in current_player_region.active_market_events:
                if event_item.event_type == EventType.FORCED_FIRE_SALE: active_ffs_event = event_item; break

            if active_ffs_event:
                total_player_drugs_quantity = sum(qty for qualities in player_inventory_data.items.values() for qty in qualities.values())
                if total_player_drugs_quantity > 0:
                    ffs_qty_percent = getattr(game_configs_data, "FORCED_FIRE_SALE_QUANTITY_PERCENT", 0.15)
                    ffs_penalty_percent = getattr(game_configs_data, "FORCED_FIRE_SALE_PRICE_PENALTY_PERCENT", 0.30)
                    ffs_min_cash_gain = getattr(game_configs_data, "FORCED_FIRE_SALE_MIN_CASH_GAIN", 50.0)
                    drugs_sold_details_list = []
                    total_cash_gained_ffs = 0.0
                    total_units_sold_ffs = 0

                    # Create a copy of items to iterate over for modification
                    player_drug_items_ffs_copy = []
                    for dn_enum, q_dict in player_inventory_data.items.items():
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
                            if market_sell_price_ffs <= 0: continue # Should not happen with valid drugs

                            discounted_price_ffs = round(max(game_configs_data.FORCED_SALE_MIN_PRICE_PER_UNIT, market_sell_price_ffs * (1.0 - ffs_penalty_percent)), 2)
                            cash_from_sale_ffs = qty_to_sell_ffs * discounted_price_ffs
                            total_cash_gained_ffs += cash_from_sale_ffs
                            player_inventory_data.remove_drug(drug_name_val_ffs, quality_val_ffs, qty_to_sell_ffs)
                            total_units_sold_ffs += qty_to_sell_ffs
                            drugs_sold_details_list.append(f"{qty_to_sell_ffs} {drug_name_val_ffs.value} ({quality_val_ffs.name})")

                    if total_units_sold_ffs > 0 and total_cash_gained_ffs < ffs_min_cash_gain:
                        total_cash_gained_ffs = ffs_min_cash_gain
                    if total_units_sold_ffs > 0:
                        player_inventory_data.cash += total_cash_gained_ffs
                        heat_increase_ffs_val = game_configs_data.FORCED_FIRE_SALE_HEAT_INCREASE
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
                        result.blocking_event_data = {"title": ffs_title_val, "messages": ffs_messages_list, "button_text": "Got it."}
                        result.log_messages.append(f"Forced Fire Sale: Sold {sold_summary_str}. Cash +${total_cash_gained_ffs:,.2f}. Heat +{heat_increase_ffs_val} in {region_name_log_ffs_val}.")
                    elif total_player_drugs_quantity > 0 : # Had drugs, but none were applicable for FFS (e.g. price <=0)
                        result.log_messages.append("Forced Fire Sale triggered, but no applicable drugs sold (e.g., market price was too low).")


    # --- Skill Point Award ---
    if game_state_data.current_day > 0 and \
       game_state_data.current_day % game_configs_data.SKILL_POINTS_PER_X_DAYS == 0:
        player_inventory_data.skill_points += 1
        result.skill_points_awarded_player_total = player_inventory_data.skill_points
        result.ui_messages.append(f"Daily Update: +1 Skill Point. Total: {player_inventory_data.skill_points}")
        result.log_messages.append(f"Awarded skill point (daily). Total: {player_inventory_data.skill_points}")

    # --- Bankruptcy Check ---
    if player_inventory_data.cash < game_configs_data.BANKRUPTCY_THRESHOLD and result.game_over_message is None:
        result.game_over_message = "GAME OVER: You have gone bankrupt!"
        result.log_messages.append(f"{result.game_over_message} Cash: ${player_inventory_data.cash:.2f}, Threshold: ${game_configs_data.BANKRUPTCY_THRESHOLD:.2f}")

    return result
