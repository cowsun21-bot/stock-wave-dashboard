import pandas as pd

from modules.indicators import add_bollinger_bands, add_moving_averages, add_volume_average
from modules.support_resistance import calculate_hh_l1_key_support, detect_key_support_breakdown
from modules.wave_analyzer import analyze_wave_position, calculate_wave_trigger


def test_wave_analysis_returns_position():
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=60),
            "Code": "000000",
            "Name": "",
            "Open": [100 + i for i in range(60)],
            "High": [105 + i for i in range(60)],
            "Low": [95 + i for i in range(60)],
            "Close": [102 + i for i in range(60)],
            "Volume": [1000 + i * 20 for i in range(60)],
        }
    )
    df = add_bollinger_bands(add_volume_average(add_moving_averages(df)))
    support = calculate_hh_l1_key_support(df)
    support["resistances"] = []
    support["breakdown"] = detect_key_support_breakdown(df, support["key_support_low"])
    trigger = calculate_wave_trigger(df, support)
    wave = analyze_wave_position(df, support, {"volume_turnaround": True, "score": 50})
    assert trigger > 0
    assert wave["position"]
