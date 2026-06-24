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
- [ ] Implement a DataFrame-like class from scratch for filtering and aggregation
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

Work in progress. DataFrame class coming next.
