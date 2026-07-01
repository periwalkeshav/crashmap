from __future__ import annotations

from typing import List, TypedDict

from .data_loader import load_city_summary
from .utils import to_dict_records


class TopCityRecord(TypedDict):
    city: str
    state: str
    total_accidents: int
    avg_severity: float


def get_top_cities(state: str, limit: int = 10) -> List[TopCityRecord]:
    """
    Return the top-N cities by accident count for a given state.
    """
    df = load_city_summary()
    df = df.filter_by_value("State", state.upper())

    if len(df) == 0:
        return []

    df = df.sort("total_accidents", ascending=False)
    df = df.head(limit)
    df = df.round_column("avg_severity", decimals=2)

    df = df.rename_columns({
        "City": "city",
        "State": "state",
    })
    
    df = df.select(["city", "state", "total_accidents", "avg_severity"])
    return to_dict_records(df)


