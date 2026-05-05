"""Multi-stock ranking calculations."""

from __future__ import annotations

import pandas as pd

from modules.indicators import add_bollinger_bands, add_moving_averages, add_volume_average
from modules.pattern_rules import (
    calculate_pattern_score,
    check_bullish_candle_ratio,
    check_motive_disclosure,
    check_volume_turnaround,
)
from modules.signal_engine import calculate_partial_sell_plan, calculate_rebuy_price, calculate_stop_loss, calculate_targets
from modules.support_resistance import (
    calculate_hh_l1_key_support,
    count_support_tests,
    detect_key_support_breakdown,
    find_resistance_levels,
    find_support_levels,
)
from modules.utils import clamp, safe_pct
from modules.wave_analyzer import analyze_wave_position


def _full_analysis(df: pd.DataFrame, disclosures=None) -> dict:
    work = add_bollinger_bands(add_volume_average(add_moving_averages(df)))
    support_info = calculate_hh_l1_key_support(work)
    support_info["supports"] = find_support_levels(work)
    support_info["resistances"] = find_resistance_levels(work)
    support_info["breakdown"] = detect_key_support_breakdown(work, support_info.get("key_support_low", 0))
    support_info["support_tests"] = count_support_tests(work, support_info.get("l1_price", 0))
    bullish = check_bullish_candle_ratio(work)
    motive = check_motive_disclosure(disclosures)
    pattern_context = {
        "support_tests": support_info["support_tests"],
        "volume_turnaround": check_volume_turnaround(work),
        "bullish_ratio": bullish["ratio"],
        "has_motive_disclosure": motive["has_motive"],
    }
    pattern = calculate_pattern_score(pattern_context)
    pattern_context["pattern_score"] = pattern["score"]
    wave = analyze_wave_position(work, support_info, {**pattern_context, **pattern})
    current = float(work.iloc[-1]["Close"])
    targets = calculate_targets(current, wave["trigger_price"], support_info.get("hh_price", current), support_info.get("l1_price", current))
    stop = calculate_stop_loss(support_info, wave)
    partial = calculate_partial_sell_plan(current, targets)
    rebuy = calculate_rebuy_price(partial["partial_sell_price"], support_info)
    return {
        "df": work,
        "support_info": support_info,
        "pattern": pattern,
        "pattern_context": pattern_context,
        "wave": wave,
        "targets": targets,
        "stop_loss": stop,
        "partial": partial,
        "rebuy_price": rebuy,
        "motive_score": motive["score"],
    }


def calculate_expected_return_score(analysis: dict) -> float:
    current = analysis["df"].iloc[-1]["Close"]
    target = analysis["targets"].get("target_90d", current)
    return clamp(safe_pct(target - current, current) / 80 * 30, 0, 30)


def calculate_explosion_score(analysis: dict) -> float:
    ctx = analysis.get("pattern_context", {})
    score = 0
    score += 6 if ctx.get("volume_turnaround") else 0
    score += 6 if ctx.get("bullish_ratio", 0) >= 60 else 0
    score += 4 if analysis["wave"].get("position") in ["3파 초입", "3파 확정"] else 0
    score += 4 if ctx.get("has_motive_disclosure") else 0
    return clamp(score, 0, 20)


def calculate_three_day_spike_probability(analysis: dict) -> float:
    try:
        latest = analysis["df"].iloc[-1]
        vma20 = max(latest.get("VMA20", 1), 1)
        volume_factor = min(35, latest["Volume"] / vma20 * 15)
        wave_factor = {"3파 확정": 35, "3파 초입": 25, "2파 말": 15}.get(analysis["wave"].get("position"), 8)
        pattern_factor = min(30, analysis["pattern"].get("score", 0) * 0.3)
        return clamp(volume_factor + wave_factor + pattern_factor)
    except Exception:
        return 0.0


def analyze_stock_for_ranking(code, df, disclosures=None) -> dict:
    try:
        analysis = _full_analysis(df, disclosures)
        current = float(analysis["df"].iloc[-1]["Close"])
        expected_return_pct = safe_pct(analysis["targets"]["target_90d"] - current, current)
        expected_return_score = calculate_expected_return_score(analysis)
        wave_strength_score = clamp(analysis["wave"]["wave_strength"] / 100 * 20, 0, 20)
        explosion_score = calculate_explosion_score(analysis)
        three_day = calculate_three_day_spike_probability(analysis)
        disclosure_score = clamp(analysis.get("motive_score", 0), 0, 10)
        market_score = 3
        total = expected_return_score + wave_strength_score + explosion_score + three_day / 100 * 15 + disclosure_score + market_score
        return {
            "종목코드": str(code).zfill(6),
            "종목명": analysis["df"].iloc[-1].get("Name", ""),
            "현재가": round(current, 2),
            "파동위치": analysis["wave"]["position"],
            "3파 트리거": round(analysis["wave"]["trigger_price"], 2),
            "손절가": round(analysis["stop_loss"], 2),
            "30일 목표가": analysis["targets"]["target_30d"],
            "60일 목표가": analysis["targets"]["target_60d"],
            "90일 목표가": analysis["targets"]["target_90d"],
            "120일 목표가": analysis["targets"]["target_120d"],
            "예상상승률%": round(expected_return_pct, 2),
            "예상상승금액": round(analysis["targets"]["target_90d"] - current, 2),
            "파동강도": round(analysis["wave"]["wave_strength"], 1),
            "폭발성": round(explosion_score / 20 * 100, 1),
            "3일 급등 가능성%": round(three_day, 1),
            "30% 매도 가격": analysis["partial"]["partial_sell_price"],
            "재매수 가격": analysis["rebuy_price"],
            "종합판정": "상위 관심" if total >= 70 else "관찰" if total >= 45 else "낮음",
            "총점": round(total, 2),
        }
    except Exception:
        return {"종목코드": str(code).zfill(6), "종합판정": "분석 실패", "총점": 0}


def rank_top10(results: list[dict]) -> list[dict]:
    ranked = sorted(results, key=lambda item: item.get("총점", 0), reverse=True)[:10]
    for idx, item in enumerate(ranked, start=1):
        item["순위"] = idx
    return ranked


def make_ranking_table(results: list[dict]) -> pd.DataFrame:
    columns = [
        "순위",
        "종목코드",
        "종목명",
        "현재가",
        "파동위치",
        "3파 트리거",
        "손절가",
        "30일 목표가",
        "60일 목표가",
        "90일 목표가",
        "120일 목표가",
        "예상상승률%",
        "예상상승금액",
        "파동강도",
        "폭발성",
        "3일 급등 가능성%",
        "30% 매도 가격",
        "재매수 가격",
        "종합판정",
        "총점",
    ]
    return pd.DataFrame(rank_top10(results)).reindex(columns=columns)
