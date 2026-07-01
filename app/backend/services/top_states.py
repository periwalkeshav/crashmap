from __future__ import annotations

from typing import List, TypedDict

from .data_loader import load_state_year
from .utils import DataFrame, to_dict_records


class TopStateRecord(TypedDict):
    State: str
    total_accidents: int
    avg_distance: float


def get_top_states(limit: int = 10) -> List[TopStateRecord]:
    """
    Return the top-N states by total accident count, with average distance.
    
    Uses SELF-JOIN on state_year dataset to combine total accidents with average distance.
    """
    state_year = load_state_year()

    # Aggregate total accidents per state
    state_totals = state_year.groupby("State").agg({"total_accidents": "sum"})
    state_totals = state_totals.sort("total_accidents", ascending=False)
    state_totals = state_totals.head(limit)

    state_distances_data = {}
    state_distances_data["State"] = []
    state_distances_data["avg_distance"] = []
    
    unique_states = list(set(state_year.data["State"]))
    
    for state in unique_states:
        # Filter rows for this state
        state_rows = state_year.filter_by_value("State", state)
        
        if len(state_rows) == 0:
            continue
        
        # Calculate weighted average
        total_weighted = 0
        total_weight = 0
        
        for i in range(len(state_rows)):
            avg_dist = state_rows.data["avg_distance"][i]
            accidents = state_rows.data["total_accidents"][i]
            
            if avg_dist is not None and accidents is not None:
                total_weighted += avg_dist * accidents
                total_weight += accidents
        
        avg_distance = (total_weighted / total_weight) if total_weight > 0 else 0
        
        state_distances_data["State"].append(state)
        state_distances_data["avg_distance"].append(avg_distance)
    
    state_distances = DataFrame(state_distances_data)
    state_distances = state_distances.select(["State", "avg_distance"])

    result = state_totals.join(
        state_distances,
        on="State",
        how="left"
    )

    # Fill missing distance data
    result = result.fillna_column("avg_distance", 0)

    # Convert types and round
    result = result.convert_column_type("total_accidents", int)
    result = result.round_column("avg_distance", decimals=2)

    return to_dict_records(result)


