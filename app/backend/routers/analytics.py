from fastapi import APIRouter, HTTPException, Query

from services.map_heatmap import get_city_heatmap
from services.time_series import get_monthly_time_series, get_time_series
from services.top_cities import get_top_cities
from services.top_states import get_top_states
from services.weather_breakdown import get_weather_breakdown
from services.weather_metrics import (
    get_weather_distribution,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-states")
def top_states(limit: int = Query(10, ge=1, le=50)):
    """
    Return the top-N states ranked by accident count.
    """
    try:
        items = get_top_states(limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"items": items}


@router.get("/time-series")
def time_series(
    state: str | None = Query(default=None, min_length=2, max_length=2),
):
    """
    Return annual accident totals (and average severity) across the dataset.
    """
    try:
        items = get_time_series(state=state)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"items": items}


@router.get("/time-series/monthly")
def monthly_time_series(
    year: int = Query(ge=2016, le=2023),
    state: str | None = Query(default=None, min_length=2, max_length=2),
):
    """
    Return monthly accident totals for a specific year.
    """
    try:
        items = get_monthly_time_series(year=year, state=state)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"items": items}


@router.get("/map/cities")
def map_cities(
    limit: int = Query(500, ge=1, le=2000),
    state: str | None = Query(default=None, min_length=2, max_length=2),
    severity_min: int = Query(1, ge=1, le=4),
    severity_max: int = Query(4, ge=1, le=4),
    sun_filter: str | None = Query(default=None, pattern="^(?i)(day|night)$"),
):
    """
    Return city-level aggregates for building a heatmap.
    """
    if severity_min > severity_max:
        raise HTTPException(
            status_code=400, detail="severity_min cannot be greater than severity_max"
        )

    normalized_sun = None
    if sun_filter:
        normalized_sun = sun_filter.title()

    try:
        items = get_city_heatmap(
            state=state,
            limit=limit,
            severity_min=severity_min,
            severity_max=severity_max,
            sun_filter=normalized_sun,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"items": items}


@router.get("/top-cities")
def top_cities(
    state: str = Query(min_length=2, max_length=2),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Return the top-N cities within a state by total accidents.
    """
    try:
        items = get_top_cities(state=state, limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"items": items}


@router.get("/weather-breakdown")
def weather_breakdown(
    limit: int = Query(5, ge=1, le=20),
    state: str | None = Query(default=None, min_length=2, max_length=2),
):
    """
    Return the dominant weather conditions by accident count.
    """
    try:
        items = get_weather_breakdown(state=state, limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"items": items}


@router.get("/weather-distribution")
def weather_distribution(
    metric: str = Query("temperature", pattern="^(temperature|wind_speed|precipitation|visibility)$"),
    state: str | None = Query(default=None, min_length=2, max_length=2),
    bins: int = Query(10, ge=5, le=20),
):
    """
    Return distribution (histogram) for a weather metric across accidents.
    
    Supported metrics: temperature, wind_speed, precipitation, visibility
    """
    try:
        items = get_weather_distribution(metric=metric, state=state, bins=bins)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400 if isinstance(exc, ValueError) else 500, detail=str(exc)) from exc

    return {"items": items}


