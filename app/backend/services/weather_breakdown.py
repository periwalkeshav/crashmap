from __future__ import annotations

from typing import List, TypedDict

from .data_loader import load_state_weather
from .utils import to_dict_records


class WeatherRecord(TypedDict):
    Weather_Condition: str
    total_accidents: int
    share: float


def get_weather_breakdown(*, state: str | None = None, limit: int = 5) -> List[WeatherRecord]:
    """
    Return the leading weather conditions by accident count.
    """
    weather_df = load_state_weather()

    if state:
        weather_df = weather_df.filter_by_value("State", state.upper())

    if len(weather_df) == 0:
        return []

    # Group by Weather_Condition and sum total_accidents
    totals = weather_df.groupby("Weather_Condition").agg({"total_accidents": "sum"})

    totals = totals.sort("total_accidents", ascending=False)

    # Calculate grand total
    grand_total = sum(totals.data["total_accidents"])
    if grand_total == 0:
        return []

    # Calculate share
    share_values = [round(acc / grand_total, 4) for acc in totals.data["total_accidents"]]
    totals = totals.add_column("share", share_values)

    totals = totals.head(limit)
    totals = totals.convert_column_type("total_accidents", int)

    return to_dict_records(totals)


