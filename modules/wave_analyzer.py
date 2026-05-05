"""Wave position analyzer."""

from __future__ import annotations

import numpy as np
import pandas as pd

from modules.pattern_rules import calculate_correction_rate
from modules.utils import clamp


def calculate_wave_trigger(df: pd.DataFrame, support_info: dict) -> float:
    try:
        hh_index = support_info.get("hh_index")
        after_hh = df.loc[hh_index:] if hh_index is not None else df.tail(20)
        rebound_high = after_hh["High"].tail(10).max()
        resistances = [v for v in support_info.get("resistances", []) if v > df.iloc[-1]["Close"]]
        candidate = min(resistances) if resistances else rebound_high
        return float(max(candidate, df["High"].tail(5).max()))
    except Exception:
        return float(df["High"].tail(20).max()) if df is not None and not df.empty else np.nan


def is_wave3_confirmed(df: pd.DataFrame, trigger_price: float) -> bool:
    try:
        latest = df.iloc[-1]
        vma20 = latest.get("VMA20", df["Volume"].rolling(20, min_periods=1).mean().iloc[-1])
        return bool(latest["Close"] > trigger_price and latest["Volume"] >= vma20 * 1.5)
    except Exception:
        return False


def calculate_wave_strength(df: pd.DataFrame, support_info: dict, pattern_info: dict) -> float:
    try:
        latest = df.iloc[-1]
        ma20 = latest.get("MA20", df["Close"].rolling(20, min_periods=1).mean().iloc[-1])
        vma20 = latest.get("VMA20", df["Volume"].rolling(20, min_periods=1).mean().iloc[-1])
        price_score = 20 if latest["Close"] >= ma20 else 8
        volume_score = clamp((latest["Volume"] / max(vma20, 1)) * 20, 0, 30)
        pattern_score = pattern_info.get("score", 0) * 0.3
        support_score = 20 if not support_info.get("breakdown", {}).get("is_broken") else 5
        return clamp(price_score + volume_score + pattern_score + support_score)
    except Exception:
        return 0.0


def analyze_wave_position(df: pd.DataFrame, support_info: dict, pattern_info: dict) -> dict:
    try:
        latest = df.iloc[-1]
        current_price = float(latest["Close"])
        hh_price = float(support_info.get("hh_price", current_price))
        key_low = float(support_info.get("key_support_low", current_price))
        key_high = float(support_info.get("key_support_high", current_price))
        correction = calculate_correction_rate(current_price, hh_price)
        near_support = key_low <= current_price <= key_high * 1.05
        breakdown = support_info.get("breakdown", {}).get("is_broken", False)
        trigger = calculate_wave_trigger(df, support_info)
        confirmed = is_wave3_confirmed(df, trigger)
        vma20 = latest.get("VMA20", df["Volume"].rolling(20, min_periods=1).mean().iloc[-1])
        bb_upper = latest.get("BB_UPPER", np.inf)
        volume_hot = latest["Volume"] > vma20 * 2
        overheated = latest["Close"] > bb_upper and volume_hot

        if overheated:
            position = "5파 과열"
        elif confirmed:
            position = "3파 확정"
        elif current_price > trigger * 0.97 and pattern_info.get("volume_turnaround"):
            position = "3파 초입"
        elif correction >= 20 and latest["Close"] >= latest.get("MA20", latest["Close"]) and latest["Volume"] < vma20:
            position = "4파 조정"
        elif 35 <= correction <= 50 and near_support and not breakdown:
            position = "2파 말"
        elif near_support:
            position = "2파 말"
        else:
            position = "관찰 구간"

        strength = calculate_wave_strength(df, support_info, pattern_info)
        return {
            "position": position,
            "trigger_price": trigger,
            "wave3_confirmed": confirmed,
            "wave_strength": strength,
            "correction_rate": correction,
            "overheated": overheated,
        }
    except Exception:
        return {
            "position": "분석 불가",
            "trigger_price": np.nan,
            "wave3_confirmed": False,
            "wave_strength": 0,
            "correction_rate": 0,
            "overheated": False,
        }
