"""Support and resistance calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_hh_l1_key_support(df: pd.DataFrame, lookback: int = 20, range_pct: float = 0.02) -> dict:
    try:
        if df is None or df.empty:
            return {}
        recent = df.tail(lookback)
        hh_idx = recent["High"].idxmax()
        hh_row = df.loc[hh_idx]
        after_hh = df.loc[hh_idx:].copy()
        volume_top = after_hh.sort_values("Volume", ascending=False).head(3)
        if volume_top.empty:
            l1_row = hh_row
        else:
            l1_row = volume_top.loc[volume_top["Low"].idxmin()]
        l1 = float(l1_row["Low"])
        return {
            "hh_price": float(hh_row["High"]),
            "hh_date": hh_row["Date"],
            "hh_index": int(hh_idx),
            "l1_price": l1,
            "l1_date": l1_row["Date"],
            "key_support_low": l1 * (1 - range_pct),
            "key_support_high": l1 * (1 + range_pct),
            "range_pct": range_pct,
        }
    except Exception:
        return {}


def detect_key_support_breakdown(df: pd.DataFrame, key_support_low: float, recent_bars: int = 5) -> dict:
    try:
        recent = df.tail(recent_bars)
        broken = recent[recent["Low"] < key_support_low]
        return {
            "is_broken": not broken.empty,
            "break_count": int(len(broken)),
            "latest_close_below": bool(recent.iloc[-1]["Close"] < key_support_low),
        }
    except Exception:
        return {"is_broken": False, "break_count": 0, "latest_close_below": False}


def _cluster_levels(values: list[float], tolerance: float = 0.02, max_levels: int = 5) -> list[float]:
    levels: list[float] = []
    for value in sorted([v for v in values if pd.notna(v)]):
        if not levels or abs(value - levels[-1]) / levels[-1] > tolerance:
            levels.append(float(value))
        else:
            levels[-1] = float((levels[-1] + value) / 2)
    return levels[-max_levels:]


def find_support_levels(df: pd.DataFrame) -> list[float]:
    try:
        lows = df["Low"].tail(80)
        pivot_lows = lows[(lows.shift(1) > lows) & (lows.shift(-1) > lows)].tolist()
        if not pivot_lows:
            pivot_lows = lows.nsmallest(5).tolist()
        return _cluster_levels(pivot_lows)
    except Exception:
        return []


def find_resistance_levels(df: pd.DataFrame) -> list[float]:
    try:
        highs = df["High"].tail(80)
        pivot_highs = highs[(highs.shift(1) < highs) & (highs.shift(-1) < highs)].tolist()
        if not pivot_highs:
            pivot_highs = highs.nlargest(5).tolist()
        return sorted(_cluster_levels(pivot_highs))
    except Exception:
        return []


def count_support_tests(df: pd.DataFrame, support_price: float, tolerance: float = 0.02) -> int:
    try:
        if not support_price:
            return 0
        near = df.tail(60)[
            (df.tail(60)["Low"] <= support_price * (1 + tolerance))
            & (df.tail(60)["Low"] >= support_price * (1 - tolerance))
        ]
        return int(len(near))
    except Exception:
        return 0
