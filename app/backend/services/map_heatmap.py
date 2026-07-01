from __future__ import annotations

from functools import lru_cache
from typing import List, Optional, TypedDict
from collections import Counter

from .data_loader import load_accidents_full
from .utils import DataFrame, to_dict_records


class CityHeatmapPoint(TypedDict):
    city: str
    state: str
    start_lat: float
    start_lng: float
    total_accidents: int
    avg_severity: float
    most_common_weather: str


ACCIDENT_COLUMNS = [
    "ID",
    "City",
    "State",
    "Start_Lat",
    "Start_Lng",
    "Severity",
    "Sunrise_Sunset",
    "Weather_Condition",
]


@lru_cache(maxsize=1)
def _load_accidents():
    """
    Load and prepare accidents data for map heatmap.
    
    Uses the shared data loader to avoid redundant file parsing.
    """
    df = load_accidents_full()
    
    df = df.select(ACCIDENT_COLUMNS)
    
    def clean_weather(val):
        if val is None or val == '':
            return "Unknown"
        val_str = str(val).strip()
        return "Unknown" if val_str == '' else val_str
    
    weather_cleaned = [clean_weather(v) for v in df.data["Weather_Condition"]]
    df.data["Weather_Condition"] = weather_cleaned
    
    def clean_sun(val):
        if val is None or val == '':
            return "Unknown"
        val_str = str(val)
        return val_str.title() if val_str else "Unknown"
    
    sun_cleaned = [clean_sun(v) for v in df.data["Sunrise_Sunset"]]
    df.data["Sunrise_Sunset"] = sun_cleaned
    
    return df


def get_city_heatmap(
    *,
    state: Optional[str] = None,
    limit: int = 500,
    severity_min: int = 1,
    severity_max: int = 4,
    sun_filter: Optional[str] = None,
) -> List[CityHeatmapPoint]:
    """
    Return aggregated accident metrics per city for map visualization.

    Args:
        state: Optional state abbreviation filter.
        limit: Maximum number of city points to return (default 500).
        severity_min: Minimum severity level to include.
        severity_max: Maximum severity level to include.
        sun_filter: Optional filter for sunrise/sunset period ("Day" or "Night").
    """
    df = _load_accidents()

    aggregations = {}  # key: (state, city), value: aggregation dict
    
    # Normalize sun_filter 
    normalized_sun = sun_filter.title() if sun_filter else None
    state_filter = state.upper() if state else None
    
    for i in range(len(df)):

        severity = df.data["Severity"][i]
        if severity is None or not (severity_min <= severity <= severity_max):
            continue
        
        if normalized_sun:
            sun_val = df.data["Sunrise_Sunset"][i]
            if sun_val != normalized_sun:
                continue
        
        state_val = df.data["State"][i]
        if state_filter and state_val != state_filter:
            continue
        
        city_val = df.data["City"][i]
        if state_val is None or city_val is None:
            continue
        
        key = (state_val, city_val)
        if key not in aggregations:
            aggregations[key] = {
                "state": state_val,
                "city": city_val,
                "severities": [],
                "lats": [],
                "lngs": [],
                "weathers": [],
                "day_count": 0,
                "night_count": 0,
            }
        
        agg = aggregations[key]
        
        if severity is not None:
            agg["severities"].append(severity)
        
        lat = df.data["Start_Lat"][i]
        lng = df.data["Start_Lng"][i]
        if lat is not None:
            agg["lats"].append(lat)
        if lng is not None:
            agg["lngs"].append(lng)
        
        weather = df.data["Weather_Condition"][i]
        if weather is not None and weather != '':
            agg["weathers"].append(weather)
        
        sun_val = df.data["Sunrise_Sunset"][i]
        if sun_val == "Day":
            agg["day_count"] += 1
        elif sun_val == "Night":
            agg["night_count"] += 1
    
    if not aggregations:
        return []
    
    grouped_data = {
        "State": [],
        "City": [],
        "total_accidents": [],
        "avg_severity": [],
        "start_lat": [],
        "start_lng": [],
        "most_common_weather": [],
        "day_accidents": [],
        "night_accidents": [],
    }
    
    for key, agg in aggregations.items():
        grouped_data["State"].append(agg["state"])
        grouped_data["City"].append(agg["city"])
        
        total_accidents = len(agg["severities"])
        grouped_data["total_accidents"].append(total_accidents)
        
        # Calculate average severity
        avg_severity = sum(agg["severities"]) / len(agg["severities"]) if agg["severities"] else 0
        grouped_data["avg_severity"].append(avg_severity)
        
        # Calculate average lat/lng
        avg_lat = sum(agg["lats"]) / len(agg["lats"]) if agg["lats"] else 0
        avg_lng = sum(agg["lngs"]) / len(agg["lngs"]) if agg["lngs"] else 0
        grouped_data["start_lat"].append(avg_lat)
        grouped_data["start_lng"].append(avg_lng)
        
        # Most common weather
        if agg["weathers"]:
            counter = Counter(agg["weathers"])
            most_common_weather = counter.most_common(1)[0][0]
        else:
            most_common_weather = "Unknown"
        grouped_data["most_common_weather"].append(most_common_weather)
        
        grouped_data["day_accidents"].append(agg["day_count"])
        grouped_data["night_accidents"].append(agg["night_count"])
    
    grouped = DataFrame(grouped_data)
    
    grouped = grouped.sort("total_accidents", ascending=False)
    grouped = grouped.head(limit)

    if len(grouped) == 0:
        return []

    grouped = grouped.round_column("avg_severity", decimals=2)

    grouped = grouped.rename_columns({
        "City": "city",
        "State": "state",
    })
    
    grouped = grouped.select([
        "city",
        "state",
        "start_lat",
        "start_lng",
        "total_accidents",
        "avg_severity",
        "most_common_weather",
        "day_accidents",
        "night_accidents",
    ])
    
    return to_dict_records(grouped)


