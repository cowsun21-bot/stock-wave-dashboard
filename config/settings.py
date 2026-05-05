"""Runtime settings."""

from pathlib import Path

from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CORP_CODE_DIR = DATA_DIR / "corp_codes"

load_dotenv(BASE_DIR / ".env")

DART_API_KEY = os.getenv("DART_API_KEY", "")
DEFAULT_START_DATE = "2023-01-01"
