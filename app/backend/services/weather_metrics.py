from __future__ import annotations

from functools import lru_cache
from typing import List, Optional, TypedDict

from .data_loader import load_accidents_full
from .utils import DataFrame, to_dict_records


class TemperatureDistributionPoint(TypedDict):
    temperature_range: str
    count: int
    percentage: float


WEATHER_METRICS_COLUMNS = [
    "ID",
    "State",
    "Temperature(F)",
    "Visibility(mi)",
    "Wind_Speed(mph)",
    "Precipitation(in)",
]


@lru_cache(maxsize=1)
def _load_weather_metrics():
    """
    Load weather metrics data.
    
    Uses the shared data loader to avoid redundant file parsing.
    """
    df = load_accidents_full()
    
    df = df.select(WEATHER_METRICS_COLUMNS)
    
    return df


def get_state_weather_metrics(
    *,
    state: Optional[str] = None,
    limit: int = 10,
) -> List[StateWeatherMetrics]:
    """
    Return aggregated weather metrics (temperature, visibility, wind speed, precipitation) by state.
    
    Args:
        state: Optional state abbreviation to filter results.
        limit: Maximum number of states to return (ranked by total accidents).
    """
    df = _load_weather_metrics()
    
    if state:
        df = df.filter_by_value("State", state.upper())
    
    if len(df) == 0:
        return []
    
    aggregations = {}
    
    for i in range(len(df)):
        state_val = df.data["State"][i]
        if state_val is None:
            continue
        
        if state_val not in aggregations:
            aggregations[state_val] = {
                "temperatures": [],
                "visibilities": [],
                "wind_speeds": [],
                "precipitations": [],
                "count": 0,
            }
        
        agg = aggregations[state_val]
        agg["count"] += 1
        
        temp = df.data["Temperature(F)"][i]
        if temp is not None:
            agg["temperatures"].append(temp)
        
        vis = df.data["Visibility(mi)"][i]
        if vis is not None:
            agg["visibilities"].append(vis)
        
        wind = df.data["Wind_Speed(mph)"][i]
        if wind is not None:
            agg["wind_speeds"].append(wind)
        
        precip = df.data["Precipitation(in)"][i]
        if precip is not None:
            agg["precipitations"].append(precip)
    
    if not aggregations:
        return []
    
    grouped_data = {
        "State": [],
        "total_accidents": [],
        "avg_temperature": [],
        "avg_visibility": [],
        "avg_wind_speed": [],
        "avg_precipitation": [],
    }
    
    for state_val, agg in aggregations.items():
        grouped_data["State"].append(state_val)
        grouped_data["total_accidents"].append(agg["count"])
        
        avg_temp = sum(agg["temperatures"]) / len(agg["temperatures"]) if agg["temperatures"] else 0
        avg_vis = sum(agg["visibilities"]) / len(agg["visibilities"]) if agg["visibilities"] else 0
        avg_wind = sum(agg["wind_speeds"]) / len(agg["wind_speeds"]) if agg["wind_speeds"] else 0
        avg_precip = sum(agg["precipitations"]) / len(agg["precipitations"]) if agg["precipitations"] else 0
        
        grouped_data["avg_temperature"].append(avg_temp)
        grouped_data["avg_visibility"].append(avg_vis)
        grouped_data["avg_wind_speed"].append(avg_wind)
        grouped_data["avg_precipitation"].append(avg_precip)
    
    grouped = DataFrame(grouped_data)
    
    grouped = grouped.sort("total_accidents", ascending=False)
    grouped = grouped.head(limit)
    
    # Round values
    grouped = grouped.round_column("avg_temperature", decimals=1)
    grouped = grouped.round_column("avg_visibility", decimals=2)
    grouped = grouped.round_column("avg_wind_speed", decimals=2)
    grouped = grouped.round_column("avg_precipitation", decimals=3)
    
    # Convert types
    grouped = grouped.convert_column_type("total_accidents", int)
    
    # Rename columns
    grouped = grouped.rename_columns({
        "State": "state",
        "avg_temperature": "avg_temperature",
        "avg_visibility": "avg_visibility",
        "avg_wind_speed": "avg_wind_speed",
        "avg_precipitation": "avg_precipitation",
    })
    
    return to_dict_records(grouped)


def get_weather_distribution(
    *,
    metric: str = "temperature",
    state: Optional[str] = None,
    bins: int = 10,
) -> List[TemperatureDistributionPoint]:
    """
    Return distribution (histogram) for a weather metric across accidents.
    
    Args:
        metric: Which metric to analyze - "temperature", "wind_speed", "precipitation", or "visibility"
        state: Optional state abbreviation to filter results.
        bins: Number of bins/ranges to create.
    """
    df = _load_weather_metrics()
    
    if state:
        df = df.filter_by_value("State", state.upper())
    
    if len(df) == 0:
        return []
    
    # Map metric name to column name
    column_map = {
        "temperature": "Temperature(F)",
        "wind_speed": "Wind_Speed(mph)",
        "precipitation": "Precipitation(in)",
        "visibility": "Visibility(mi)",
    }
    
    if metric not in column_map:
        raise ValueError(f"Invalid metric: {metric}. Must be one of: {list(column_map.keys())}")
    
    column_name = column_map[metric]
    
    values = []
    for i in range(len(df)):
        val = df.data[column_name][i]
        if val is not None:
            values.append(val)
    
    if not values:
        return []
    
    min_val = min(values)
    max_val = max(values)
    bin_width = (max_val - min_val) / bins if max_val > min_val else 1
    
    bin_counts = [0] * bins
    for val in values:
        bin_idx = min(int((val - min_val) / bin_width), bins - 1)
        bin_counts[bin_idx] += 1
    
    total = len(values)
    
    result = []
    unit_map = {
        "temperature": "°F",
        "wind_speed": " mph",
        "precipitation": " in",
        "visibility": " mi",
    }
    unit = unit_map.get(metric, "")
    
    for i in range(bins):
        bin_start = min_val + i * bin_width
        bin_end = min_val + (i + 1) * bin_width
        count = bin_counts[i]
        percentage = (count / total * 100) if total > 0 else 0
        
        if metric == "temperature":
            range_label = f"{bin_start:.0f}°-{bin_end:.0f}°F"
        elif metric == "precipitation":
            range_label = f"{bin_start:.3f}-{bin_end:.3f} in"
        elif metric == "wind_speed":
            range_label = f"{bin_start:.1f}-{bin_end:.1f} mph"
        else:  # visibility
            range_label = f"{bin_start:.1f}-{bin_end:.1f} mi"
        
        result.append({
            "temperature_range": range_label,
            "count": count,
            "percentage": round(percentage, 1),
        })
    
    return result

