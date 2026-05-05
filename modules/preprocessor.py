"""OHLCV preprocessing helpers."""

from __future__ import annotations

import pandas as pd

from config.constants import OHLCV_COLUMNS


COLUMN_ALIASES = {
    "date": "Date",
    "날짜": "Date",
    "datetime": "Date",
    "time": "Date",
    "code": "Code",
    "종목코드": "Code",
    "ticker": "Code",
    "name": "Name",
    "종목명": "Name",
    "open": "Open",
    "시가": "Open",
    "high": "High",
    "고가": "High",
    "low": "Low",
    "저가": "Low",
    "close": "Close",
    "종가": "Close",
    "adj close": "Close",
    "volume": "Volume",
    "거래량": "Volume",
}


def standardize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    try:
        if df is None or df.empty:
            return pd.DataFrame(columns=OHLCV_COLUMNS)

        result = df.copy()
        result = result.reset_index() if "Date" not in result.columns else result.copy()

        rename_map = {}
        for col in result.columns:
            key = str(col).strip().lower()
            rename_map[col] = COLUMN_ALIASES.get(key, str(col).strip())
        result = result.rename(columns=rename_map)

        if "Date" not in result.columns:
            date_like = [c for c in result.columns if "date" in str(c).lower()]
            if date_like:
                result = result.rename(columns={date_like[0]: "Date"})

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col not in result.columns:
                result[col] = 0
            result[col] = pd.to_numeric(result[col], errors="coerce")

        result["Date"] = pd.to_datetime(result["Date"], errors="coerce")
        if "Code" not in result.columns:
            result["Code"] = ""
        if "Name" not in result.columns:
            result["Name"] = ""

        keep_cols = ["Date", "Code", "Name", "Open", "High", "Low", "Close", "Volume"]
        return result[keep_cols].dropna(subset=["Date"])
    except Exception:
        return pd.DataFrame(columns=["Date", "Code", "Name", "Open", "High", "Low", "Close", "Volume"])


def sort_by_date(df: pd.DataFrame) -> pd.DataFrame:
    try:
        return df.sort_values("Date").reset_index(drop=True)
    except Exception:
        return df


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    try:
        result = df.copy()
        price_cols = ["Open", "High", "Low", "Close"]
        result[price_cols] = result[price_cols].ffill().bfill()
        result["Volume"] = result["Volume"].fillna(0)
        return result.dropna(subset=price_cols)
    except Exception:
        return df


def resample_ohlcv(df: pd.DataFrame, timeframe: str = "D") -> pd.DataFrame:
    try:
        result = standardize_ohlcv(df)
        result = sort_by_date(fill_missing_values(result))
        if timeframe == "D":
            return result

        rule = {"W": "W-FRI", "M": "ME"}.get(timeframe, timeframe)
        base = result.set_index("Date")
        grouped = base.resample(rule).agg(
            {
                "Code": "last",
                "Name": "last",
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        grouped = grouped.dropna(subset=["Open", "High", "Low", "Close"]).reset_index()
        return grouped
    except Exception:
        return df


def validate_ohlcv(df: pd.DataFrame) -> tuple[bool, str]:
    try:
        if df is None or df.empty:
            return False, "데이터가 비어 있습니다."
        missing = [col for col in OHLCV_COLUMNS if col not in df.columns]
        if missing:
            return False, f"필수 컬럼 누락: {', '.join(missing)}"
        if df[["Open", "High", "Low", "Close"]].isna().any().any():
            return False, "가격 컬럼에 결측치가 있습니다."
        return True, "OK"
    except Exception as exc:
        return False, str(exc)
