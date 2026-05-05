"""Application constants for stock_wave_dashboard."""

OHLCV_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
STANDARD_COLUMNS = ["Date", "Code", "Name", "Open", "High", "Low", "Close", "Volume"]

DEFAULT_MA_WINDOWS = [5, 20, 60, 120]
DEFAULT_VOLUME_WINDOWS = [5, 20]

DISCLOSURE_IMPACT_SCORES = {
    "positive": 8,
    "neutral": 4,
    "negative": 2,
}

DISCLAIMER = (
    "본 화면의 결과는 투자 추천, 매수/매도 지시, 수익 보장을 의미하지 않습니다. "
    "모든 분석은 참고용이며 실제 투자 판단과 책임은 사용자에게 있습니다."
)
