from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"

STATE_YEAR_PATH = DATA_DIR / "us_accidents_state_year.csv"
STATE_WEATHER_PATH = DATA_DIR / "us_accidents_state_weather.csv"
CITY_SUMMARY_PATH = DATA_DIR / "us_accidents_city_summary.csv"
ACCIDENTS_CLEAN_PATH = DATA_DIR / "us_accidents_clean.csv"


