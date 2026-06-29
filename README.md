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
- [ ] Expose data via a REST API (FastAPI)
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

Work in progress. FastAPI backend coming next.
