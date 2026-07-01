"""
API-specific utility functions for DataFrame operations.
This module provides functions needed for API responses, specifically converting
DataFrames to JSON-serializable formats.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_DIR = PROJECT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from functions import DataFrame, read_csv_parallel

__all__ = [
    "DataFrame",
    "read_csv_parallel",
    "to_dict_records",
]


def to_dict_records(df: DataFrame) -> list[dict]:
    """
    Convert DataFrame to list of dictionaries (like pandas to_dict(orient="records")).
    
    This is API-specific: converts the custom DataFrame to a JSON-serializable format
    that FastAPI can return in API responses.
    
    Args:
        df: DataFrame to convert
        
    Returns:
        List of dictionaries, one per row
    """
    if len(df) == 0:
        return []
    
    records = []
    for i in range(len(df)):
        record = {col: df.data[col][i] for col in df.columns}
        records.append(record)
    
    return records

