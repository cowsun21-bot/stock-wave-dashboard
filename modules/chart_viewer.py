"""Chart rendering helpers."""

from __future__ import annotations

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

from modules.indicators import add_bollinger_bands, add_moving_averages, add_volume_average


def _mpf_df(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["Date"] = pd.to_datetime(result["Date"])
    return result.set_index("Date")[["Open", "High", "Low", "Close", "Volume"]]


def plot_candlestick(df: pd.DataFrame, title: str = ""):
    try:
        fig, _ = mpf.plot(_mpf_df(df), type="candle", volume=True, style="yahoo", title=title, returnfig=True)
        return fig
    except Exception:
        fig, ax = plt.subplots()
        ax.set_title("차트 생성 실패")
        return fig


def plot_with_indicators(df: pd.DataFrame, supports=None, resistances=None, signals=None):
    try:
        supports = supports or []
        resistances = resistances or []
        signals = signals or {}
        work = add_bollinger_bands(add_volume_average(add_moving_averages(df)))
        mpf_data = _mpf_df(work)
        addplots = [
            mpf.make_addplot(work.set_index("Date")["BB_UPPER"], color="gray", width=0.7),
            mpf.make_addplot(work.set_index("Date")["BB_MID"], color="steelblue", width=0.7),
            mpf.make_addplot(work.set_index("Date")["BB_LOWER"], color="gray", width=0.7),
        ]
        hlines = []
        colors = []
        for price in supports:
            hlines.append(price)
            colors.append("green")
        for price in resistances:
            hlines.append(price)
            colors.append("red")
        for key in ["trigger_price", "stop_loss"]:
            if signals.get(key):
                hlines.append(signals[key])
                colors.append("purple" if key == "trigger_price" else "black")

        kwargs = {}
        if hlines:
            kwargs["hlines"] = dict(hlines=hlines, colors=colors, linestyle="--", linewidths=0.8)
        fig, _ = mpf.plot(
            mpf_data,
            type="candle",
            volume=True,
            mav=(5, 20, 60, 120),
            style="yahoo",
            addplot=addplots,
            returnfig=True,
            figsize=(12, 8),
            **kwargs,
        )
        return fig
    except Exception:
        return plot_candlestick(df, "차트 생성 실패")


def plot_bollinger_chart(df: pd.DataFrame):
    try:
        work = add_bollinger_bands(df)
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(work["Date"], work["Close"], label="Close")
        ax.plot(work["Date"], work["BB_UPPER"], label="Upper", color="gray")
        ax.plot(work["Date"], work["BB_MID"], label="Middle", color="steelblue")
        ax.plot(work["Date"], work["BB_LOWER"], label="Lower", color="gray")
        ax.legend()
        return fig
    except Exception:
        return plot_candlestick(df, "볼린저밴드")


def save_chart_image(df: pd.DataFrame, output_path):
    fig = plot_with_indicators(df)
    fig.savefig(output_path, bbox_inches="tight")
    return output_path
