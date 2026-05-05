import pandas as pd

from modules.support_resistance import calculate_hh_l1_key_support, count_support_tests, detect_key_support_breakdown, find_resistance_levels, find_support_levels


def test_support_info():
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=30),
            "Code": "000000",
            "Name": "",
            "Open": [100] * 30,
            "High": list(range(100, 130)),
            "Low": [90 + (i % 5) for i in range(30)],
            "Close": [100 + i for i in range(30)],
            "Volume": [1000 + i * 10 for i in range(30)],
        }
    )
    info = calculate_hh_l1_key_support(df)
    assert info["hh_price"] == 129
    assert info["key_support_low"] < info["l1_price"] < info["key_support_high"]
    assert "is_broken" in detect_key_support_breakdown(df, info["key_support_low"])
    assert isinstance(find_support_levels(df), list)
    assert isinstance(find_resistance_levels(df), list)
    assert count_support_tests(df, info["l1_price"]) >= 1
