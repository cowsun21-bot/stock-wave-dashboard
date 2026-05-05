"""Reference-only signal and price plan calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_trigger_price(df: pd.DataFrame, support_info: dict) -> float:
    try:
        resistances = support_info.get("resistances", [])
        current = df.iloc[-1]["Close"]
        above = [r for r in resistances if r > current]
        if above:
            return float(min(above))
        return float(df["High"].tail(10).max())
    except Exception:
        return np.nan


def calculate_buy_signal(df: pd.DataFrame, wave_info: dict, support_info: dict) -> dict:
    try:
        position = wave_info.get("position", "")
        broken = support_info.get("breakdown", {}).get("is_broken", False)
        trigger = wave_info.get("trigger_price")
        close = df.iloc[-1]["Close"]
        signal = position in ["2파 말", "3파 초입", "3파 확정"] and not broken
        if position == "3파 확정":
            label = "트리거 돌파 확인"
        elif close >= trigger * 0.97:
            label = "트리거 근접 관찰"
        elif signal:
            label = "지지 방어 관찰"
        else:
            label = "관망"
        return {"has_signal": bool(signal), "label": label}
    except Exception:
        return {"has_signal": False, "label": "분석 불가"}


def calculate_stop_loss(support_info: dict, wave_info: dict) -> float:
    try:
        key_low = float(support_info.get("key_support_low"))
        l1 = float(support_info.get("l1_price"))
        return float(min(key_low, l1 * 0.97))
    except Exception:
        return np.nan


def calculate_targets(current_price: float, trigger_price: float, hh_price: float, l1_price: float) -> dict:
    try:
        base = max(float(current_price), float(trigger_price))
        hh = float(hh_price) if hh_price else base * 1.2
        risk_width = max(base - float(l1_price), base * 0.08)
        return {
            "target_30d": round(base + risk_width * 1.0, 2),
            "target_60d": round(max(hh, base + risk_width * 1.5), 2),
            "target_90d": round(max(hh * 1.15, base + risk_width * 2.2), 2),
            "target_120d": round(max(hh * 1.35, base + risk_width * 3.0), 2),
        }
    except Exception:
        return {"target_30d": np.nan, "target_60d": np.nan, "target_90d": np.nan, "target_120d": np.nan}


def calculate_partial_sell_plan(current_price: float, targets: dict, holding_qty: int | None = None) -> dict:
    try:
        sell_price = min(targets.get("target_30d", current_price * 1.3), current_price * 1.3)
        qty = int(holding_qty * 0.3) if holding_qty else None
        amount = round(sell_price * qty, 2) if qty is not None else None
        return {"partial_sell_price": round(sell_price, 2), "partial_sell_qty": qty, "partial_sell_amount": amount}
    except Exception:
        return {"partial_sell_price": np.nan, "partial_sell_qty": None, "partial_sell_amount": None}


def calculate_rebuy_price(partial_sell_price: float, support_info: dict) -> float:
    try:
        pullback_price = float(partial_sell_price) * 0.9
        key_high = float(support_info.get("key_support_high", pullback_price))
        return round(max(pullback_price, key_high), 2)
    except Exception:
        return np.nan
