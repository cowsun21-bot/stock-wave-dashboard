"""Technical indicator calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_moving_averages(df: pd.DataFrame, windows: list[int] | None = None) -> pd.DataFrame:
    try:
        windows = windows or [5, 20, 60, 120]
        result = df.copy()
        for window in windows:
            result[f"MA{window}"] = result["Close"].rolling(window, min_periods=1).mean()
        return result
    except Exception:
        return df


def add_volume_average(df: pd.DataFrame, windows: list[int] | None = None) -> pd.DataFrame:
    try:
        windows = windows or [5, 20]
        result = df.copy()
        for window in windows:
            result[f"VMA{window}"] = result["Volume"].rolling(window, min_periods=1).mean()
        return result
    except Exception:
        return df


def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2) -> pd.DataFrame:
    try:
        result = df.copy()
        middle = result["Close"].rolling(window, min_periods=1).mean()
        std = result["Close"].rolling(window, min_periods=1).std(ddof=0).fillna(0)
        result["BB_MID"] = middle
        result["BB_UPPER"] = middle + num_std * std
        result["BB_LOWER"] = middle - num_std * std
        return result
    except Exception:
        return df


def calculate_recent_hh(df: pd.DataFrame, lookback: int = 20) -> dict:
    try:
        recent = df.tail(lookback)
        idx = recent["High"].idxmax()
        row = df.loc[idx]
        return {"price": float(row["High"]), "date": row["Date"], "index": int(idx)}
    except Exception:
        return {"price": np.nan, "date": None, "index": None}


def calculate_recent_ll(df: pd.DataFrame, lookback: int = 20) -> dict:
    try:
        recent = df.tail(lookback)
        idx = recent["Low"].idxmin()
        row = df.loc[idx]
        return {"price": float(row["Low"]), "date": row["Date"], "index": int(idx)}
    except Exception:
        return {"price": np.nan, "date": None, "index": None}


def calculate_candle_stats(df: pd.DataFrame) -> pd.DataFrame:
    try:
        result = df.copy()
        result["Body"] = (result["Close"] - result["Open"]).abs()
        result["Range"] = (result["High"] - result["Low"]).replace(0, np.nan)
        result["BodyPct"] = result["Body"] / result["Range"] * 100
        result["IsBullish"] = result["Close"] > result["Open"]
        result["UpperShadow"] = result["High"] - result[["Open", "Close"]].max(axis=1)
        result["LowerShadow"] = result[["Open", "Close"]].min(axis=1) - result["Low"]
        return result
    except Exception:
        return df
