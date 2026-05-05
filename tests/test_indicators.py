import pandas as pd

from modules.indicators import add_bollinger_bands, add_moving_averages, add_volume_average, calculate_recent_hh, calculate_recent_ll


def sample_df():
    return pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=30),
            "Code": "000000",
            "Name": "",
            "Open": range(30),
            "High": range(1, 31),
            "Low": range(0, 30),
            "Close": range(1, 31),
            "Volume": range(100, 130),
        }
    )


def test_indicators():
    df = add_bollinger_bands(add_volume_average(add_moving_averages(sample_df())))
    assert "MA20" in df
    assert "VMA20" in df
    assert "BB_UPPER" in df
    assert calculate_recent_hh(df, 20)["price"] == 30
    assert calculate_recent_ll(df, 20)["price"] == 10
