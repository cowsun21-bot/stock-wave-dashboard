"""Shared utility helpers."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def safe_pct(numerator: float, denominator: float, default: float = 0.0) -> float:
    try:
        if not denominator:
            return default
        return float(numerator) / float(denominator) * 100
    except Exception:
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    try:
        if math.isnan(value) or math.isinf(value):
            return low
        return max(low, min(high, float(value)))
    except Exception:
        return low


def latest_row(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)
    return df.iloc[-1]


def ensure_datetime(value: Any) -> pd.Timestamp:
    return pd.to_datetime(value, errors="coerce")


def to_display_number(value: Any, digits: int = 0) -> float:
    number = safe_float(value, np.nan)
    if pd.isna(number):
        return np.nan
    return round(number, digits)
