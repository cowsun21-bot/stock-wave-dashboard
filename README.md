# stock_wave_dashboard

Python + Streamlit 기반 한국 주식 차트, 파동, 지지/저항, 공시 분석 MVP입니다.

실제 매수/매도 주문 기능은 없으며, 분석과 시각화 및 랭킹만 제공합니다.

## 1. 설치 방법

```bash
cd stock_wave_dashboard
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. 실행 방법

```bash
streamlit run app.py
```

브라우저에서 Streamlit 주소가 열리면 단일 종목 분석, 여러 종목 TOP10 랭킹, 공시 조회, 설정 탭을 사용할 수 있습니다.

## 3. DART_API_KEY 설정 방법

`.env.example` 파일을 복사해 `.env` 파일을 만들고 OpenDART API 키를 입력합니다.

```env
DART_API_KEY=발급받은_키
```

키가 없으면 공시 기능만 비활성화됩니다. 차트, 파동, 지지/저항 분석은 계속 작동합니다.

## 4. 138360 앤로보틱스 테스트 방법

1. 앱 실행 후 `단일 종목 분석` 탭을 엽니다.
2. 종목코드에 `138360`을 입력합니다.
3. 종목명에 `앤로보틱스`를 입력합니다.
4. 데이터 소스는 `fdr` 또는 `auto`를 선택합니다.
5. 일봉/주봉/월봉 중 원하는 기준을 선택합니다.

FinanceDataReader 수집이 실패하면 `auto` 선택 시 yfinance fallback을 시도합니다.

## 5. CSV 업로드 형식

단일 종목 CSV는 아래 컬럼을 권장합니다.

```csv
Date,Open,High,Low,Close,Volume
2025-01-02,1000,1100,980,1050,100000
```

한국어 컬럼명도 일부 지원합니다.

```csv
날짜,시가,고가,저가,종가,거래량
```

여러 종목 랭킹 CSV는 첫 번째 컬럼에 종목코드를 넣으면 됩니다.

```csv
code
138360
005930
000660
```

## 6. 주요 기능 설명

- FinanceDataReader 기반 한국 종목 주가 수집
- yfinance fallback
- CSV 업로드 데이터 표준화
- 날짜 정렬, 결측치 처리, 일봉/주봉/월봉 변환
- mplfinance 캔들차트, 이동평균선, 거래량, 볼린저밴드 표시
- 최근 20봉 HH 계산
- HH 이후 거래량 상위 3일 중 최저 Low인 L1 계산
- KEY_SUPPORT_RANGE = L1 ± 2%
- 최근 5봉 KEY_SUPPORT_LOW 이탈 여부
- 지지선/저항선 계산
- 2파 말, 3파 초입, 3파 확정, 4파 조정, 5파 과열 분류
- 3파 트리거 가격, 손절라인, 30/60/90/120일 목표가 계산
- 30% 매도 가격, 매도 금액, 재매수 가격 계산
- 여러 종목 예상상승률 TOP10, 파동강도 TOP10, 폭발성 TOP10, 종합 TOP10
- OpenDART 공시 조회 및 보고서명 기반 성격/영향/희석 여부 분류

## 7. 투자 참고용 면책 문구

본 프로그램의 결과는 투자 추천, 매수/매도 지시, 수익 보장을 의미하지 않습니다. 모든 분석은 참고용이며 실제 투자 판단과 책임은 사용자에게 있습니다.
