from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st
try:
    import FinanceDataReader as fdr
except Exception:
    fdr = None


def normalize_stock_code_for_name(code) -> str:
    if code is None:
        return ""
    try:
        if pd.isna(code):
            return ""
    except Exception:
        pass

    text = str(code).strip()
    if not text:
        return ""

    try:
        if text.replace(".", "", 1).isdigit():
            text = str(int(float(text)))
    except Exception:
        pass

    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        return digits.zfill(6)[-6:]

    return text


@st.cache_data(show_spinner=False)
def get_krx_name_map() -> dict:
    if fdr is None:
        return {}

    try:
        listing = fdr.StockListing("KRX")
        if listing is None or listing.empty:
            return {}

        if "Code" not in listing.columns or "Name" not in listing.columns:
            return {}

        listing = listing[["Code", "Name"]].copy()
        listing["Code"] = listing["Code"].apply(normalize_stock_code_for_name)
        listing["Name"] = listing["Name"].fillna("").astype(str).str.strip()

        return dict(zip(listing["Code"], listing["Name"]))
    except Exception:
        return {}


def fill_stock_names(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    out = df.copy()

    if "종목코드" not in out.columns:
        return out

    out["종목코드"] = out["종목코드"].apply(normalize_stock_code_for_name)

    if "종목명" not in out.columns:
        out["종목명"] = ""

    name_map = get_krx_name_map()

    empty_name = (
        out["종목명"].isna()
        | out["종목명"].astype(str).str.strip().str.lower().isin(["", "nan", "none"])
    )

    if name_map:
        out.loc[empty_name, "종목명"] = out.loc[empty_name, "종목코드"].map(name_map)

    out["종목명"] = out["종목명"].fillna("").astype(str).str.strip()
    out.loc[out["종목명"].isin(["", "nan", "None", "none"]), "종목명"] = "종목명 미확인"

    return out


def show_name_mapping_status(df: pd.DataFrame):
    if df is None or df.empty or "종목명" not in df.columns:
        return

    total = len(df)
    unknown_count = int((df["종목명"] == "종목명 미확인").sum())
    success_count = total - unknown_count

    st.caption(f"종목명 매핑: {total}개 중 {success_count}개 표시 완료")

    if unknown_count > 0 and "종목코드" in df.columns:
        unknown_codes = df.loc[df["종목명"] == "종목명 미확인", "종목코드"].tolist()
        st.warning(f"종목명 미확인 종목코드: {', '.join(unknown_codes)}")

from config.constants import DISCLAIMER
from config.settings import DART_API_KEY
from modules.chart_viewer import plot_with_indicators
from modules.data_fetcher import fetch_multi_stocks, fetch_stock_price, load_uploaded_csv, normalize_ticker
from modules.disclosure_fetcher import fetch_dart_disclosures, make_dart_viewer_url, summarize_disclosures
from modules.indicators import add_bollinger_bands, add_moving_averages, add_volume_average
from modules.pattern_rules import (
    calculate_pattern_score,
    check_bullish_candle_ratio,
    check_motive_disclosure,
    check_volume_turnaround,
    classify_pattern_type,
)
from modules.preprocessor import resample_ohlcv, validate_ohlcv
from modules.ranking_report import analyze_stock_for_ranking, make_ranking_table
from modules.signal_engine import calculate_buy_signal, calculate_partial_sell_plan, calculate_rebuy_price, calculate_stop_loss, calculate_targets
from modules.support_resistance import (
    calculate_hh_l1_key_support,
    count_support_tests,
    detect_key_support_breakdown,
    find_resistance_levels,
    find_support_levels,
)
from modules.wave_analyzer import analyze_wave_position


st.set_page_config(page_title="stock_wave_dashboard", layout="wide")


def prepare_analysis(code: str, start, end, source: str, timeframe: str, uploaded_file=None, disclosures=None):
    if uploaded_file is not None:
        df = load_uploaded_csv(uploaded_file)
    else:
        df = fetch_stock_price(code, start, end, source=source)
    df = resample_ohlcv(df, timeframe)
    ok, message = validate_ohlcv(df)
    if not ok:
        raise RuntimeError(message)
    df = add_bollinger_bands(add_volume_average(add_moving_averages(df)))
    support_info = calculate_hh_l1_key_support(df)
    support_info["supports"] = find_support_levels(df)
    support_info["resistances"] = find_resistance_levels(df)
    support_info["breakdown"] = detect_key_support_breakdown(df, support_info.get("key_support_low", 0))
    support_info["support_tests"] = count_support_tests(df, support_info.get("l1_price", 0))

    bullish = check_bullish_candle_ratio(df)
    motive = check_motive_disclosure(disclosures)
    pattern_context = {
        "is_35_50_correction": False,
        "support_tests": support_info["support_tests"],
        "volume_turnaround": check_volume_turnaround(df),
        "bullish_ratio": bullish["ratio"],
        "has_motive_disclosure": motive["has_motive"],
    }
    pattern_score = calculate_pattern_score(pattern_context)
    wave_info = analyze_wave_position(df, support_info, {**pattern_context, **pattern_score})
    pattern_context["is_35_50_correction"] = 35 <= wave_info["correction_rate"] <= 50
    pattern_context["pattern_score"] = pattern_score["score"]
    pattern_context["wave3_confirmed"] = wave_info["wave3_confirmed"]
    pattern_context["overheated"] = wave_info["overheated"]
    pattern_type = classify_pattern_type(pattern_context)

    current = float(df.iloc[-1]["Close"])
    stop_loss = calculate_stop_loss(support_info, wave_info)
    targets = calculate_targets(current, wave_info["trigger_price"], support_info.get("hh_price", current), support_info.get("l1_price", current))
    partial = calculate_partial_sell_plan(current, targets)
    rebuy = calculate_rebuy_price(partial["partial_sell_price"], support_info)
    buy_signal = calculate_buy_signal(df, wave_info, support_info)
    return df, support_info, wave_info, pattern_score, pattern_type, targets, stop_loss, partial, rebuy, buy_signal


def single_stock_view():
    st.header("단일 종목 분석")
    with st.sidebar:
        st.subheader("입력")
        code = st.text_input("종목코드", value="138360")
        name = st.text_input("종목명", value="앤로보틱스")
        start = st.date_input("시작일", value=date.today() - timedelta(days=500))
        end = st.date_input("종료일", value=date.today())
        source = st.selectbox("데이터 소스", ["fdr", "auto", "yfinance"])
        timeframe = st.selectbox("봉 변환", [("일봉", "D"), ("주봉", "W"), ("월봉", "M")], format_func=lambda x: x[0])[1]

    disclosures = pd.DataFrame()
    if DART_API_KEY:
        disclosures = fetch_dart_disclosures(code, date.today() - timedelta(days=30), date.today())

    try:
        df, support, wave, pattern, pattern_type, targets, stop_loss, partial, rebuy, buy_signal = prepare_analysis(
            code, start, end, source, timeframe, disclosures=disclosures
        )
    except Exception as exc:
        st.warning(f"데이터 수집 또는 분석에 실패했습니다: {exc}")
        return

    st.subheader(f"{normalize_ticker(code)} {name}")
    st.pyplot(
        plot_with_indicators(
            df,
            supports=support.get("supports", []) + [support.get("key_support_low"), support.get("key_support_high")],
            resistances=support.get("resistances", []),
            signals={"trigger_price": wave["trigger_price"], "stop_loss": stop_loss},
        )
    )

    current = float(df.iloc[-1]["Close"])
    cols = st.columns(5)
    cols[0].metric("현재가", f"{current:,.0f}")
    cols[1].metric("파동 위치", wave["position"])
    cols[2].metric("3파 트리거", f"{wave['trigger_price']:,.0f}")
    cols[3].metric("손절라인", f"{stop_loss:,.0f}")
    cols[4].metric("패턴", pattern_type)

    st.subheader("핵심 가격")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "HH": support.get("hh_price"),
                    "L1": support.get("l1_price"),
                    "KEY_SUPPORT_LOW": support.get("key_support_low"),
                    "KEY_SUPPORT_HIGH": support.get("key_support_high"),
                    "최근 5봉 이탈": support.get("breakdown", {}).get("is_broken"),
                    "지지 테스트": support.get("support_tests"),
                }
            ]
        ),
        use_container_width=True,
    )

    st.subheader("목표가 및 분할 대응 참고값")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "30일 목표가": targets["target_30d"],
                    "60일 목표가": targets["target_60d"],
                    "90일 목표가": targets["target_90d"],
                    "120일 목표가": targets["target_120d"],
                    "30% 매도 가격": partial["partial_sell_price"],
                    "30% 매도 금액": partial["partial_sell_amount"],
                    "재매수 가격": rebuy,
                    "참고 신호": buy_signal["label"],
                    "파동강도": round(wave["wave_strength"], 1),
                    "패턴점수": pattern["score"],
                }
            ]
        ),
        use_container_width=True,
    )

    st.subheader("최근 공시 요약")
    summary = summarize_disclosures(disclosures)
    st.info(summary["summary"] if DART_API_KEY else "DART_API_KEY가 없어 공시 기능만 비활성화되었습니다.")
    if disclosures is not None and not disclosures.empty:
        st.dataframe(disclosures, use_container_width=True)

def multi_stock_view():
    st.header("여러 종목 TOP10 랭킹")

    code_text = st.text_area(
        "종목코드 리스트",
        value="138360\n308080\n066430\n131400",
        height=120,
    )

    uploaded = st.file_uploader("종목코드 CSV 업로드", type=["csv"], key="ranking_csv")
    start = st.date_input("랭킹 시작일", value=date.today() - timedelta(days=500))
    end = st.date_input("랭킹 종료일", value=date.today())

    if st.button("TOP10 분석 실행"):
        codes = [
            normalize_ticker(x)
            for x in code_text.replace(",", "\n").splitlines()
            if x.strip()
        ]

        if uploaded is not None:
            upload_df = pd.read_csv(uploaded)
            first_col = upload_df.columns[0]
            codes.extend(upload_df[first_col].dropna().astype(str).tolist())

        codes = list(dict.fromkeys(codes))

        if not codes:
            st.warning("분석할 종목코드를 입력해주세요.")
            return

        with st.spinner("여러 종목을 분석 중입니다."):
            price_map = fetch_multi_stocks(codes, start, end)
            results = []

            for code, df in price_map.items():
                if df is None or df.empty:
                    continue

                try:
                    results.append(analyze_stock_for_ranking(code, df, disclosures=[]))
                except Exception:
                    continue

        if not results:
            st.warning("분석 가능한 데이터가 없습니다.")
            return

        table = make_ranking_table(results)
        table = fill_stock_names(table)
        show_name_mapping_status(table)

        table = table.rename(
            columns={
                "30% 매도 가격": "1차매도",
                "폭발성": "폭발성점수",
            }
        )

        default_columns = {
            "공시점수": 0,
            "희석여부": "N",
            "공시성격": "미연동",
            "공시강도": "보통",
            "종합판정": "관찰",
            "총점": 0,
            "폭발성점수": 0,
        }

        for col, default_value in default_columns.items():
            if col not in table.columns:
                table[col] = default_value

        if "예상상승금액" in table.columns:
            table = table.drop(columns=["예상상승금액"])

        def display_ranking_df(df, columns):
            display_df = fill_stock_names(df.copy())

            display_df = display_df.rename(
                columns={
                    "30% 매도 가격": "1차매도",
                    "폭발성": "폭발성점수",
                }
            )

            if "예상상승금액" in display_df.columns:
                display_df = display_df.drop(columns=["예상상승금액"])

            for col, default_value in default_columns.items():
                if col not in display_df.columns:
                    display_df[col] = default_value

            existing_columns = [col for col in columns if col in display_df.columns]
            display_df = display_df[existing_columns].reset_index(drop=True)

            try:
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            except TypeError:
                st.dataframe(display_df, use_container_width=True)

        summary_cols = [
            "순위",
            "종목코드",
            "종목명",
            "현재가",
            "파동위치",
            "종합판정",
            "총점",
            "폭발성점수",
            "3일 급등 가능성%",
            "예상상승률%",
            "1차매도",
            "재매수 가격",
            "공시점수",
            "희석여부",
        ]

        return_cols = [
            "순위",
            "종목코드",
            "종목명",
            "현재가",
            "파동위치",
            "예상상승률%",
            "120일 목표가",
            "폭발성점수",
            "1차매도",
            "재매수 가격",
            "공시점수",
            "희석여부",
        ]

        surge_cols = [
            "순위",
            "종목코드",
            "종목명",
            "현재가",
            "파동위치",
            "3일 급등 가능성%",
            "폭발성점수",
            "파동강도",
            "1차매도",
            "재매수 가격",
            "공시점수",
            "희석여부",
        ]

        wave_cols = [
            "순위",
            "종목코드",
            "종목명",
            "현재가",
            "파동위치",
            "파동강도",
            "폭발성점수",
            "3파 트리거",
            "손절가",
            "종합판정",
            "공시점수",
            "희석여부",
        ]

        explosion_cols = [
            "순위",
            "종목코드",
            "종목명",
            "현재가",
            "파동위치",
            "폭발성점수",
            "3일 급등 가능성%",
            "파동강도",
            "예상상승률%",
            "공시점수",
            "희석여부",
            "종합판정",
        ]

        st.subheader("종합 TOP10")
        display_ranking_df(table.head(10), summary_cols)

        st.subheader("예상상승률 TOP10")
        display_ranking_df(
            table.sort_values("예상상승률%", ascending=False).head(10),
            return_cols,
        )

        st.subheader("3일 급등 가능성 TOP10")
        display_ranking_df(
            table.sort_values("3일 급등 가능성%", ascending=False).head(10),
            surge_cols,
        )

        st.subheader("파동강도 TOP10")
        display_ranking_df(
            table.sort_values("파동강도", ascending=False).head(10),
            wave_cols,
        )

        st.subheader("폭발성 TOP10")
        display_ranking_df(
            table.sort_values("폭발성점수", ascending=False).head(10),
            explosion_cols,
        )

        with st.expander("전체 상세 데이터 보기"):
            detail_table = table.reset_index(drop=True)
            try:
                st.dataframe(detail_table, use_container_width=True, hide_index=True)
            except TypeError:
                st.dataframe(detail_table, use_container_width=True)

def disclosure_view():
    st.header("공시 조회")
    if not DART_API_KEY:
        st.warning("DART_API_KEY가 없어 공시 기능만 비활성화되었습니다. .env 파일에 키를 설정하면 사용할 수 있습니다.")
        return
    code = st.text_input("공시 조회 종목코드", value="138360")
    start = st.date_input("조회 시작일", value=date.today() - timedelta(days=90))
    end = st.date_input("조회 종료일", value=date.today())
    if st.button("공시 조회"):
        df = fetch_dart_disclosures(code, start, end)
        if df.empty:
            st.warning("조회된 공시가 없습니다.")
            return
        display_cols = [c for c in ["report_nm", "flr_nm", "rcept_dt", "rm", "nature", "impact_strength", "is_dilution"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
        for _, row in df.head(20).iterrows():
            if row.get("rcept_no"):
                st.link_button(str(row.get("report_nm", "DART 원문 보기")), make_dart_viewer_url(row["rcept_no"]))
        st.info(summarize_disclosures(df)["summary"])


def settings_view():
    st.header("설정")
    st.write("DART_API_KEY 상태:", "설정됨" if DART_API_KEY else "미설정")
    st.write("데이터 소스는 FinanceDataReader 우선, 실패 시 yfinance fallback을 사용할 수 있습니다.")


def main():
    st.title("stock_wave_dashboard")
    tab1, tab2, tab3, tab4 = st.tabs(["단일 종목 분석", "여러 종목 TOP10 랭킹", "공시 조회", "설정"])
    with tab1:
        single_stock_view()
    with tab2:
        multi_stock_view()
    with tab3:
        disclosure_view()
    with tab4:
        settings_view()

    st.divider()
    st.caption(DISCLAIMER)


if __name__ == "__main__":
    main()
