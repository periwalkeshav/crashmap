from __future__ import annotations

from typing import List, TypedDict

from .data_loader import load_accidents_full, load_state_year
from .utils import DataFrame, to_dict_records


class MonthlyTimeSeriesPoint(TypedDict):
    month: int
    month_name: str
    total_accidents: int
    avg_severity: float


class TimeSeriesPoint(TypedDict):
    year: int
    total_accidents: int
    avg_severity: float


def get_time_series(*, state: str | None = None) -> List[TimeSeriesPoint]:
    """
    Aggregate annual accident counts and severity across the dataset.

    Args:
        state: Optional state abbreviation to filter results.
    """
    df = load_state_year()
    if state:
        df = df.filter_by_value("State", state.upper())

    if len(df) == 0:
        return []

    # Group by Year and calculate aggregations
    grouped_data = {}
    grouped_data["Year"] = []
    grouped_data["total_accidents"] = []
    grouped_data["avg_severity"] = []
    
    # Get unique years
    unique_years = sorted(set(df.data["Year"]))
    
    for year in unique_years:
        # Filter rows for this year
        year_rows = df.filter_by_value("Year", year)
        
        if len(year_rows) == 0:
            continue
        
        # Sum total accidents
        total_accidents = sum(
            acc for acc in year_rows.data["total_accidents"]
            if acc is not None
        )
        
        # Calculate weighted average severity
        weighted_severity = 0
        total_weight = 0
        
        for i in range(len(year_rows)):
            severity = year_rows.data["Severity"][i]
            accidents = year_rows.data["total_accidents"][i]
            
            if severity is not None and accidents is not None:
                weighted_severity += severity * accidents
                total_weight += accidents
        
        avg_severity = (weighted_severity / total_weight) if total_weight > 0 else 0
        
        grouped_data["Year"].append(year)
        grouped_data["total_accidents"].append(total_accidents)
        grouped_data["avg_severity"].append(avg_severity)
    
    grouped = DataFrame(grouped_data)

    grouped = grouped.convert_column_type("total_accidents", int)
    grouped = grouped.round_column("avg_severity", decimals=2)

    grouped = grouped.sort("Year")
    grouped = grouped.rename_columns({"Year": "year"})
    
    return to_dict_records(grouped)


def get_monthly_time_series(*, year: int, state: str | None = None) -> List[MonthlyTimeSeriesPoint]:
    """
    Get monthly accident data for a specific year.

    Args:
        year: Year to filter by (2016-2023).
        state: Optional state abbreviation to filter results.
    """
    df = load_accidents_full()
    
    month_aggregations = {}  # key: month, value: aggregation dict
    state_filter = state.upper() if state else None
    
    for i in range(len(df)):
        row_year = df.data["Year"][i]
        if row_year != year:
            continue
        
        if state_filter:
            row_state = df.data["State"][i]
            if row_state != state_filter:
                continue
        
        month = df.data["Month"][i]
        if month is None:
            continue
        
        if month not in month_aggregations:
            month_aggregations[month] = {
                "severities": [],
                "count": 0,
            }
        
        agg = month_aggregations[month]
        agg["count"] += 1
        
        severity = df.data["Severity"][i]
        if severity is not None:
            agg["severities"].append(severity)
    
    if not month_aggregations:
        return []
    
    grouped_data = {
        "Month": [],
        "total_accidents": [],
        "avg_severity": [],
    }
    
    for month in sorted(month_aggregations.keys()):
        agg = month_aggregations[month]
        grouped_data["Month"].append(month)
        grouped_data["total_accidents"].append(agg["count"])
        
        avg_severity = sum(agg["severities"]) / len(agg["severities"]) if agg["severities"] else 0
        grouped_data["avg_severity"].append(avg_severity)
    
    grouped = DataFrame(grouped_data)
    
    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
    }
    month_name_values = [month_names.get(month, "Unknown") for month in grouped.data["Month"]]
    grouped = grouped.add_column("month_name", month_name_values)
    
    grouped = grouped.convert_column_type("total_accidents", int)
    grouped = grouped.round_column("avg_severity", decimals=2)
    
    grouped = grouped.sort("Month")
    grouped = grouped.rename_columns({"Month": "month"})
    
    return to_dict_records(grouped)


