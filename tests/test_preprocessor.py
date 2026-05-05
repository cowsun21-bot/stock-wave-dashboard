import pandas as pd

from modules.preprocessor import fill_missing_values, resample_ohlcv, sort_by_date, standardize_ohlcv, validate_ohlcv


def test_standardize_sort_fill_resample():
    df = pd.DataFrame(
        {
            "날짜": ["2025-01-03", "2025-01-02"],
            "시가": [100, None],
            "고가": [120, 110],
            "저가": [90, 95],
            "종가": [115, 105],
            "거래량": [1000, None],
        }
    )
    result = fill_missing_values(sort_by_date(standardize_ohlcv(df)))
    ok, message = validate_ohlcv(result)
    assert ok, message
    weekly = resample_ohlcv(result, "W")
    assert not weekly.empty
    assert weekly.iloc[0]["High"] == 120
