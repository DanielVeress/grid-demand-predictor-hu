# Hungarian Electricity Demand Forecasting

Forecasting next-day national electricity load for Hungary — and scoring it against the official forecast published by the grid operator.

> **Status:** In progress. Targeting a deployed (if ugly) skeleton first, then a polished version with a live dashboard.

## The Question

Can a simple model with weather features beat the naive baseline at predicting tomorrow's national electricity demand — and how does it stack up against MAVIR's official day-ahead forecast?

## Why It Matters

Day-ahead load forecasts drive how much generating capacity and reserve margin the grid commits to. Over-forecasting wastes money on idle reserves; under-forecasting risks the system. A few percent of accuracy translates directly into MW of reserve overcommitment, which is why every TSO and energy trader cares about forecast error.

## Definition of Done

This project is done when all of the following exist:

- [ ] **Live URL** — a deployed dashboard a recruiter can click
- [ ] **Clean repo** — readable, organized, reproducible
- [ ] **Case-study README** — problem, decisions, results (this file)
- [ ] **One new CV bullet block** — the project written up for applications

**Targets:** deployed skeleton (ugly is fine) by **July 20**, polished by **July 31**.

## Data

- **Load & official forecast** — [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/): actual total load and day-ahead load forecast for Hungary (TSO: MAVIR). Free with registration, REST API. Known to have missing values and gaps, real cleanup required.
- **Weather** — [Open-Meteo](https://open-meteo.com/): free historical and forecast weather (temperature, etc.) used as predictive features.

## Approach

```
ENTSO-E + Open-Meteo  →  raw ingestion  →  dbt transforms (Postgres)
        →  model  →  dashboard: forecast vs. actual vs. TSO
```

**Models (locked, no scope creep):**
1. Naive baseline (e.g. same hour last week)
2. A single gradient boosting model with weather + calendar features

The comparison is *not* model-vs-model. It's **my model vs. the official forecast.**

## Stack

| Layer | Tool |
|-------|------|
| Ingestion | Python (ENTSO-E + Open-Meteo APIs) |
| Warehouse | Postgres |
| Transforms | dbt |
| Modeling | Python (scikit-learn / gradient boosting) |
| Dashboard | Streamlit |
| Deploy | AWS / Render free tier |

## Results

_Coming soon — RMSE / MAPE table comparing naive baseline, my model, and the official TSO forecast over a rolling evaluation window._

## Live Dashboard

_Coming soon — link to the deployed dashboard showing forecast vs. actuals vs. TSO._

## Roadmap

- [ ] ENTSO-E ingestion (load + day-ahead forecast)
- [ ] Open-Meteo weather ingestion
- [ ] dbt cleaning & feature models on Postgres
- [ ] Naive baseline + gradient boosting model
- [ ] Backtest vs. official forecast
- [ ] Streamlit dashboard
- [ ] Deploy live

## License

[MIT](LICENSE)
