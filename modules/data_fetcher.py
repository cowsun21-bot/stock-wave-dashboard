"""Stock price data collection."""

from __future__ import annotations

import pandas as pd

from modules.preprocessor import fill_missing_values, sort_by_date, standardize_ohlcv


def normalize_ticker(code, market=None) -> str:
    code = str(code).strip()
    if code.isdigit():
        return code.zfill(6)
    return code


def _finalize_price_df(df: pd.DataFrame, code: str = "", name: str = "") -> pd.DataFrame:
    result = standardize_ohlcv(df)
    if code:
        result["Code"] = normalize_ticker(code)
    if name and "Name" in result.columns:
        result["Name"] = name
    return sort_by_date(fill_missing_values(result))


def fetch_stock_price(code, start, end, source: str = "fdr") -> pd.DataFrame:
    ticker = normalize_ticker(code)
    errors = []
    if source in ["fdr", "auto"]:
        try:
            import FinanceDataReader as fdr

            df = fdr.DataReader(ticker, start, end)
            if df is not None and not df.empty:
                return _finalize_price_df(df, ticker)
        except Exception as exc:
            errors.append(f"FinanceDataReader 실패: {exc}")

    if source in ["yfinance", "yf", "auto"] or source == "fdr":
        try:
            import yfinance as yf

            yf_ticker = ticker if "." in ticker else f"{ticker}.KS"
            df = yf.download(yf_ticker, start=start, end=end, progress=False, auto_adjust=False)
            if (df is None or df.empty) and "." not in ticker:
                df = yf.download(f"{ticker}.KQ", start=start, end=end, progress=False, auto_adjust=False)
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0] for c in df.columns]
                return _finalize_price_df(df, ticker)
        except Exception as exc:
            errors.append(f"yfinance 실패: {exc}")

    raise RuntimeError(" / ".join(errors) if errors else "데이터 수집에 실패했습니다.")


def fetch_index_price(index_code, start, end) -> pd.DataFrame:
    try:
        import FinanceDataReader as fdr

        return _finalize_price_df(fdr.DataReader(index_code, start, end), index_code)
    except Exception as exc:
        raise RuntimeError(f"지수 데이터 수집 실패: {exc}") from exc


def fetch_multi_stocks(code_list, start, end) -> dict[str, pd.DataFrame]:
    results = {}
    for code in code_list:
        try:
            results[normalize_ticker(code)] = fetch_stock_price(code, start, end, source="auto")
        except Exception:
            results[normalize_ticker(code)] = pd.DataFrame()
    return results


def load_uploaded_csv(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file)
    except UnicodeDecodeError:
        file.seek(0)
        df = pd.read_csv(file, encoding="cp949")
    return _finalize_price_df(df)
