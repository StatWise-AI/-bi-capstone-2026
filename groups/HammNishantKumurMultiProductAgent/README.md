# Barrl — EU Fuel Price Forecasting Agent

An AI-powered forecasting agent for EU fuel prices. Forecasts are produced per country (10 EU
member states) and per product (up to 6 fuel types) rather than a single EU-wide average,
decompose the retail price into a market component and a tax component, and are served through
both an interactive Streamlit app and a Power BI dashboard.

## What's in this folder

| Folder | Contents |
|---|---|
| [`app/`](./app) | The working Streamlit application — data pipeline, forecasting models (SARIMAX + gradient-boosted trees), the AI agent, and the front end. See its own README inside for setup instructions. |
| [`powerbi/`](./powerbi) | The Power BI dashboard — `dashboard.pbix`, the underlying data workbook, and build guides. |
| [`data/`](./data) | The core datasets: cleaned weekly price history and the combined history-plus-forecast file. |

## Quick start — running the app locally

```bash
cd app
python -m venv venv
venv\Scripts\activate          # Windows; use `source venv/bin/activate` on Mac/Linux
python -m pip install -r requirements.txt
streamlit run app.py
```

Full setup and troubleshooting notes are in [`app/README.md`](./app/README.md).

## Data source

European Commission Weekly Oil Bulletin (DG Energy) — weekly consumer diesel/petrol/heating
oil/fuel oil/LPG prices, with and without tax, since 2005, across all EU member states. This is
official, publicly published government data, not synthetic or proprietary.
[Official page](https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en)

## Model

- **SARIMAX** with exogenous regressors (Brent crude oil price, exchange rate for non-Eurozone
  countries, calendar seasonality) for most country/product combinations.
- **Gradient-boosted trees (LightGBM)** for diesel (all 10 countries) and heating oil (8 of 10 —
  Germany and the Netherlands specifically keep SARIMAX), adopted after empirical backtesting
  showed a clear, product-specific improvement.

Full model comparison reasoning and backtest evidence are documented inside `app/`'s own
methodology notes and the project's companion report (submitted separately in this course's
document deliverables).

## Keeping the data current

```bash
cd app
python refresh_all.py
```

Downloads the latest official data, validates last time's forecasts against real outcomes,
regenerates forecasts, and rebuilds the Power BI workbook — all in one command.
