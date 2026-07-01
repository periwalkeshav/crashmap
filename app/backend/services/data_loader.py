from __future__ import annotations

from functools import lru_cache

from .config import (
    ACCIDENTS_CLEAN_PATH,
    CITY_SUMMARY_PATH,
    STATE_YEAR_PATH,
    STATE_WEATHER_PATH,
)
from .utils import read_csv_parallel

# Global state to track data loading status
_data_loaded = False
_loading_error = None


@lru_cache(maxsize=1)
def load_accidents_full():
    """
    Load the full cleaned accidents dataset.
    
    This function is cached globally, so the file is only parsed once per server instance.
    All services should use this function to get the full dataset, then select
    the columns they need.
    
    Returns:
        DataFrame: Full accidents dataset
    """
    if not ACCIDENTS_CLEAN_PATH.exists():
        raise FileNotFoundError(
            f"Required dataset file not found at '{ACCIDENTS_CLEAN_PATH}'. "
            "Generate it via the data_cleaning notebook."
        )
    return read_csv_parallel(str(ACCIDENTS_CLEAN_PATH), skip_type_inference=False, verbose=True)


@lru_cache(maxsize=1)
def load_city_summary():
    """
    Load the city-level summary dataset.
    
    This function is cached globally, so the file is only parsed once per server instance.
    
    Returns:
        DataFrame: City summary dataset with aggregated accident statistics
    """
    if not CITY_SUMMARY_PATH.exists():
        raise FileNotFoundError(
            f"Required city summary file not found at '{CITY_SUMMARY_PATH}'. "
            "Generate it via the data_cleaning notebook."
        )
    return read_csv_parallel(str(CITY_SUMMARY_PATH), skip_type_inference=False, verbose=False)


@lru_cache(maxsize=1)
def load_state_year():
    """
    Load the pre-aggregated state/year/severity summary dataset.
    
    This function is cached globally, so the file is only parsed once per server instance.
    
    Returns:
        DataFrame: State/year summary dataset with aggregated accident statistics
    """
    if not STATE_YEAR_PATH.exists():
        raise FileNotFoundError(
            f"Required state/year summary file not found at '{STATE_YEAR_PATH}'. "
            "Generate it via the data_cleaning notebook."
        )
    return read_csv_parallel(str(STATE_YEAR_PATH), skip_type_inference=False, verbose=False)


@lru_cache(maxsize=1)
def load_state_weather():
    """
    Load the state/weather summary dataset.
    
    This function is cached globally, so the file is only parsed once per server instance.
    
    Returns:
        DataFrame: State/weather summary dataset with aggregated accident statistics
    """
    if not STATE_WEATHER_PATH.exists():
        raise FileNotFoundError(
            f"Required state/weather summary file not found at '{STATE_WEATHER_PATH}'. "
            "Generate it via the data_cleaning notebook."
        )
    return read_csv_parallel(str(STATE_WEATHER_PATH), skip_type_inference=False, verbose=False)


def initialize_all_data():
    """
    Eagerly load all datasets at server startup.
    
    This function loads all required datasets into memory so they're ready
    for immediate use when the server starts accepting requests.
    
    Raises:
        FileNotFoundError: If any required data file is missing
        Exception: If any dataset fails to load
    """
    global _data_loaded, _loading_error
    
    if _data_loaded:
        return  # Already loaded
    
    try:
        print("=" * 60)
        print("Loading all datasets at startup...")
        print("=" * 60)
        
        print("\n[1/4] Loading full accidents dataset...")
        load_accidents_full()
        print("✓ Full accidents dataset loaded")
        
        print("\n[2/4] Loading city summary dataset...")
        load_city_summary()
        print("✓ City summary dataset loaded")
        
        print("\n[3/4] Loading state/year summary dataset...")
        load_state_year()
        print("✓ State/year summary dataset loaded")
        
        print("\n[4/4] Loading state/weather summary dataset...")
        load_state_weather()
        print("✓ State/weather summary dataset loaded")
        
        _data_loaded = True
        _loading_error = None
        
        print("\n" + "=" * 60)
        print("✓ All datasets loaded successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        _loading_error = str(e)
        print(f"\n✗ Error loading datasets: {e}")
        raise


def is_data_loaded() -> bool:
    """
    Check if all datasets have been loaded.
    
    Returns:
        bool: True if all datasets are loaded, False otherwise
    """
    return _data_loaded


def get_loading_error() -> str | None:
    """
    Get the error message if data loading failed.
    
    Returns:
        str | None: Error message if loading failed, None otherwise
    """
    return _loading_error

