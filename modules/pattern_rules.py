"""Pattern rules inspired by the requested wave-analysis criteria."""

from __future__ import annotations

import pandas as pd

from modules.utils import clamp


def calculate_correction_rate(current_price: float, hh_price: float) -> float:
    try:
        if not hh_price:
            return 0.0
        return max(0.0, (hh_price - current_price) / hh_price * 100)
    except Exception:
        return 0.0


def check_35_50_correction(correction_rate: float) -> bool:
    return 35 <= correction_rate <= 50


def check_volume_turnaround(df: pd.DataFrame) -> bool:
    try:
        recent = df.tail(3)["Volume"]
        return len(recent) == 3 and recent.iloc[-1] > recent.iloc[-2] > recent.iloc[-3]
    except Exception:
        return False


def check_bullish_candle_ratio(df: pd.DataFrame, recent_bars: int = 10) -> dict:
    try:
        recent = df.tail(recent_bars)
        ratio = (recent["Close"] > recent["Open"]).mean() * 100
        return {"ratio": float(ratio), "is_bullish_dominant": ratio >= 55}
    except Exception:
        return {"ratio": 0.0, "is_bullish_dominant": False}


def check_motive_disclosure(disclosures) -> dict:
    try:
        if disclosures is None:
            return {"has_motive": False, "score": 0}
        if isinstance(disclosures, pd.DataFrame):
            rows = disclosures.to_dict("records")
        else:
            rows = disclosures
        keywords = ["계약", "공급", "수주", "특허", "승인", "합병", "투자", "증설", "실적", "매출"]
        negative = ["전환사채", "유상증자", "감자", "소송", "관리종목", "불성실"]
        score = 0
        for item in rows:
            name = str(item.get("report_nm", item.get("report_name", "")))
            if any(k in name for k in keywords):
                score += 3
            if any(k in name for k in negative):
                score -= 2
        return {"has_motive": score > 0, "score": clamp(score, 0, 10)}
    except Exception:
        return {"has_motive": False, "score": 0}


def calculate_pattern_score(context: dict) -> dict:
    try:
        score = 0
        reasons = []
        if context.get("is_35_50_correction"):
            score += 18
            reasons.append("HH 대비 35~50% 조정")
        if context.get("support_tests", 0) >= 2:
            score += 14
            reasons.append("KEY_SUPPORT 2회 이상 방어")
        if context.get("volume_turnaround"):
            score += 14
            reasons.append("최근 3봉 거래량 증가 전환")
        if context.get("bullish_ratio", 0) >= 55:
            score += 10
            reasons.append("최근 10봉 양봉 우세")
        if context.get("has_motive_disclosure"):
            score += 14
            reasons.append("상승 명분 공시")
        if context.get("trigger_breakout"):
            score += 15
            reasons.append("3파 트리거 돌파")
        if context.get("breakout_volume"):
            score += 15
            reasons.append("돌파봉 거래량 우위")
        return {"score": clamp(score), "reasons": reasons}
    except Exception:
        return {"score": 0, "reasons": []}


def classify_pattern_type(context: dict) -> str:
    try:
        score = context.get("pattern_score", 0)
        if context.get("overheated"):
            return "과열/분할매도 구간"
        if context.get("wave3_confirmed"):
            return "3파 확정 후보"
        if context.get("trigger_breakout") and score >= 65:
            return "3파 초입 핵심 후보"
        if score >= 55:
            return "구조형 폭등 후보"
        if score >= 40:
            return "폭등 가능성"
        return "폭등 전형 낮음"
    except Exception:
        return "폭등 전형 낮음"
