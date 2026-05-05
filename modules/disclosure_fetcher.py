"""OpenDART disclosure fetcher."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd
import requests

from config.settings import CORP_CODE_DIR, DART_API_KEY

DART_BASE = "https://opendart.fss.or.kr/api"
DART_VIEWER_BASE = "https://dart.fss.or.kr/dsaf001/main.do"


def download_corp_code(api_key: str | None = None) -> Path:
    api_key = api_key or DART_API_KEY
    if not api_key:
        raise RuntimeError("DART_API_KEY가 설정되지 않았습니다.")
    CORP_CODE_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(f"{DART_BASE}/corpCode.xml", params={"crtfc_key": api_key}, timeout=20)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(CORP_CODE_DIR)
    return CORP_CODE_DIR / "CORPCODE.xml"


def load_corp_code_table() -> pd.DataFrame:
    try:
        path = CORP_CODE_DIR / "CORPCODE.xml"
        if not path.exists():
            download_corp_code()
        root = ET.parse(path).getroot()
        rows = []
        for item in root.findall("list"):
            rows.append(
                {
                    "corp_code": item.findtext("corp_code", ""),
                    "corp_name": item.findtext("corp_name", ""),
                    "stock_code": item.findtext("stock_code", "").zfill(6),
                    "modify_date": item.findtext("modify_date", ""),
                }
            )
        df = pd.DataFrame(rows)
        return df[df["stock_code"].str.strip() != ""]
    except Exception:
        return pd.DataFrame(columns=["corp_code", "corp_name", "stock_code", "modify_date"])


def find_corp_code_by_stock_code(stock_code) -> str | None:
    try:
        table = load_corp_code_table()
        stock_code = str(stock_code).zfill(6)
        matched = table[table["stock_code"] == stock_code]
        if matched.empty:
            return None
        return str(matched.iloc[0]["corp_code"])
    except Exception:
        return None


def fetch_dart_disclosures(stock_code, start_date, end_date) -> pd.DataFrame:
    try:
        if not DART_API_KEY:
            return pd.DataFrame()
        corp_code = find_corp_code_by_stock_code(stock_code)
        if not corp_code:
            return pd.DataFrame()
        params = {
            "crtfc_key": DART_API_KEY,
            "corp_code": corp_code,
            "bgn_de": pd.to_datetime(start_date).strftime("%Y%m%d"),
            "end_de": pd.to_datetime(end_date).strftime("%Y%m%d"),
            "page_count": 100,
        }
        response = requests.get(f"{DART_BASE}/list.json", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        rows = data.get("list", [])
        result = pd.DataFrame(rows)
        if result.empty:
            return result
        classifications = result["report_nm"].apply(classify_disclosure)
        class_df = pd.DataFrame(classifications.tolist())
        return pd.concat([result.reset_index(drop=True), class_df], axis=1)
    except Exception:
        return pd.DataFrame()


def classify_disclosure(report_name: str) -> dict:
    name = str(report_name)
    positive = ["단일판매", "공급계약", "수주", "특허", "승인", "실적", "영업이익", "매출", "투자유치"]
    dilution = ["전환사채", "신주인수권", "유상증자", "교환사채", "주식매수선택권"]
    negative = ["소송", "감자", "관리종목", "상장폐지", "불성실", "횡령", "배임"]
    repeated = ["정정", "첨부정정", "기재정정"]

    if any(k in name for k in negative):
        nature, impact = "부정", "높음"
    elif any(k in name for k in positive):
        nature, impact = "긍정", "중상"
    elif any(k in name for k in dilution):
        nature, impact = "희석 가능", "중상"
    else:
        nature, impact = "중립", "보통"

    return {
        "disclosure_type": "정정/반복" if any(k in name for k in repeated) else "일반",
        "nature": nature,
        "is_repeated": any(k in name for k in repeated),
        "impact_strength": impact,
        "is_dilution": any(k in name for k in dilution),
    }


def summarize_disclosures(disclosures) -> dict:
    try:
        if disclosures is None or len(disclosures) == 0:
            return {"summary": "최근 조회 공시가 없거나 DART 키가 설정되지 않았습니다.", "motive_score": 0}
        df = disclosures if isinstance(disclosures, pd.DataFrame) else pd.DataFrame(disclosures)
        positive_count = int((df.get("nature", "") == "긍정").sum()) if "nature" in df else 0
        dilution_count = int(df.get("is_dilution", pd.Series(dtype=bool)).sum()) if "is_dilution" in df else 0
        score = max(0, min(10, positive_count * 3 - dilution_count * 2))
        return {
            "summary": f"긍정 공시 {positive_count}건, 희석 가능 공시 {dilution_count}건이 감지되었습니다.",
            "motive_score": score,
        }
    except Exception:
        return {"summary": "공시 요약 생성 실패", "motive_score": 0}


def make_dart_viewer_url(rcept_no) -> str:
    return f"{DART_VIEWER_BASE}?rcpNo={rcept_no}"
