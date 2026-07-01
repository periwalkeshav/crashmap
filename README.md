# crashmap

> Interactive dashboard for exploring US road accident data (2016–2023)

## What is this?

I'm building a full-stack analytics dashboard to explore patterns in US traffic accident data — where accidents happen, when, under what weather conditions, and how severe they are.

The dataset covers ~3 million accident records across 49 states from 2016 to 2023.

## Planned stack

- **Backend** — Python, FastAPI
- **Frontend** — React, Leaflet.js
- **Data processing** — custom-built (no pandas, no numpy)

## Goals

- [x] Build a custom CSV parser that can handle multi-GB files efficiently
- [x] Implement a DataFrame-like class from scratch for filtering and aggregation
- [x] Expose data via a REST API (FastAPI)
- [ ] Build an interactive heatmap + charts on the frontend
- [ ] Correlate accidents with weather, time of day, and severity

## Project structure

crashmap/
├── app/
│   ├── backend/
│   │   ├── requirements.txt
│   │   └── functions.py
│   └── frontend/
├── data/ (file not large to upload)
├── images/
└── README.md

## Data source

Using the [US Accidents dataset](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents) from Kaggle — countrywide accident data collected from traffic APIs, law enforcement, and road sensors.

The dataset is too large for GitHub. Download the 4 CSV files from [Google Drive](#) and place them in the `data/` folder before running.

data/
├── accidents_main.csv
├── city_summary.csv
├── state_year.csv
└── weather_correlation.csv

---

## Setup & running the backend

```bash
# install dependencies
pip install -r app/backend/requirements.txt

# start the server
uvicorn app.backend.main:app --reload
```

> Note: the server loads all 4 CSVs into memory on startup — expect a 1–2 minute wait on first run.

Once running, the API is available at `http://localhost:8000`.

---

## API endpoints

| Method | Endpoint | Description |
| -------- | ---------- | ------------- |
| GET | `/severity` | Accident count by severity level (1–4) |
| GET | `/trends` | Yearly accident totals from 2016–2023 |
| GET | `/heatmap` | City-level lat, lng, and accident count |
| GET | `/weather` | Accident counts grouped by weather condition |
| GET | `/state` | State-by-year accident breakdown |

All endpoints accept an optional `severity` query param to filter results.

```bash
# example
curl http://localhost:8000/heatmap?severity=3
```

---

## Day 2 progress

Built the custom CSV parser today — two versions:

- `read_csv()` — single-threaded, handles quoted fields and auto-infers column types (int, float, string)
- `read_csv_parallel()` — splits the file into chunks and processes them across CPU cores using Python's `multiprocessing` module

The parallel version cuts load time significantly on large files. No pandas involved — just the standard library.

```python
# single-threaded
df = read_csv("data/accidents.csv")

# parallel (recommended for large files)
df = read_csv_parallel("data/accidents.csv")
```

---

## Day 3 progress

Built the core `DataFrame` class and a `GroupBy` class on top of the CSV parser today. This is the engine that the API will use to query and aggregate data.

`DataFrame` supports:

- `filter()` — filter rows by condition or dict of values
- `select()` / `drop()` — pick or remove columns
- `sort()` — sort by any column, ascending or descending
- `join()` — inner, left, right, and outer joins on arbitrary key columns
- `add_column()`, `rename()`, `fillna()`, `round()` — column-level utilities

`GroupBy` supports:

- `groupby()` — group rows by one or more columns
- `aggregate()` — compute `sum`, `mean`, `count`, `min`, `max` per group

```python
# example — accidents per state sorted by count
result = (
    df.filter({"severity": 3})
      .groupby("state")
      .aggregate({"id": "count"})
      .sort("id", ascending=False)
)
```

Everything is built on plain Python lists and dicts — no external dependencies at all.

---

## Day 4 progress

FastAPI backend is up today. All 4 CSV files are loaded into memory at startup using `read_csv_parallel()` and then queried on each request using the `DataFrame` class — no database, no ORM, just in-memory data.

Added 5 endpoints covering severity distribution, yearly trends, heatmap data, weather correlations, and state breakdowns. All of them support an optional `severity` filter param.

The `main.py` startup event looks roughly like this:

```python
@app.on_event("startup")
async def load_data():
    app.state.df = read_csv_parallel("data/accidents_main.csv")
    app.state.city_df = read_csv_parallel("data/city_summary.csv")
    app.state.state_df = read_csv_parallel("data/state_year.csv")
    app.state.weather_df = read_csv_parallel("data/weather_correlation.csv")
```

---

Work in progress. React frontend coming next.
