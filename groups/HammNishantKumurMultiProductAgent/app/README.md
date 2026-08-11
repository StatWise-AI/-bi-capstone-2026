# EU fuel price forecasting agent — Streamlit demo

Covers the EU-aggregate diesel model (original scope) plus 10 countries ×
up to 6 products each (52 combinations), selectable from the sidebar.

## What's in this folder

**App**
- `app.py` — the Streamlit app (4 tabs: trend & forecast, tax decomposition,
  model comparison, AI briefing; sidebar has Region/Product selectors and
  the Power BI refresh button)

**Country/product path** — precomputed, fixed 12-week horizon, **hybrid model per combination**
- `country_product_agent.py` — `CountryProductAgent`: serves the precomputed
  results below through the *exact same interface* as `DieselForecastAgent`
  (`current_snapshot()`, `get_combined()`, `backtest_summary()`,
  `generate_briefing()`, etc.), so none of the tab-rendering code in `app.py`
  needed to change for the new scope
- `country_product_history_and_forecast.csv` — history + forecast for all
  52 combinations
- `country_product_meta.json` — per-combination model used (SARIMAX or GBM),
  order/backtest results, exogenous regressors used, latest tax figures
- `completeness_report.csv` — which of the 60 possible (country, product)
  combinations were included vs. excluded, and why
- `gbm_pipeline.py` — the LightGBM backtest, run on the identical fold
  structure as the SARIMAX backtest for a fair comparison
- `gbm_production.py` — generates the actual forward forecasts (with an 80%
  interval via quantile models) for the combinations where GBM won
- `gbm_vs_sarimax_comparison.csv` — the full 52-combination result behind
  the model-choice decision below

**Following professor feedback after the presentation** (see
`docs/Model_Comparison_Report.docx`, Section 8): gradient-boosted trees
(LightGBM) were actually implemented and backtested — not just discussed
qualitatively — using the exact same rolling-origin evaluation as SARIMAX.
Result: a genuine, product-specific split, not a uniform winner.

| Products | Model used | Why |
|---|---|---|
| Diesel (all 10 countries) | **LightGBM** | Beat SARIMAX in 10/10 countries, +46.5% average MAE improvement |
| Heating oil (8 of 10 countries) | **LightGBM** | Beat SARIMAX in 8/10 countries, +30.9% average; Germany and the Netherlands are exceptions — SARIMAX wins for those two specifically |
| Petrol, both fuel oil grades, LPG | **SARIMAX** | GBM did not improve on SARIMAX on average, and badly overfit on the thinner series (e.g. France/LPG: 258% worse than just guessing last week's price) |

The app's "Model comparison" tab shows this per selected country/product —
which model is live, and the full backtest table including GBM where it was
tested.

**EU-aggregate path (original, unchanged)** — live-fit, adjustable horizon
- `diesel_agent.py` — `DieselForecastAgent`: live ARIMA fit on the EU-wide series
- `forecasting.py` — the underlying pipeline for the EU-aggregate model
- `eu_diesel_price_weekly_2005_2026.csv` — EU-aggregate diesel series

**Keeping the data current — one command**
- `refresh_all.py` — runs the entire weekly refresh chain in order: downloads
  the latest official data, validates last week's forecasts against real
  outcomes, rebuilds the master dataset, regenerates SARIMAX forecasts for
  all 52 combinations, regenerates GBM forecasts for the 18 that use it, and
  snapshots this week's predictions for next time's validation. Run with
  `python refresh_all.py`.
- `auto_download_oil_bulletin.py` — downloads the latest workbook directly
  from the European Commission's official page, no manual browser step
- `master_country_product_weekly.csv`, `extract_master.py` — the cleaned
  weekly dataset and the script that rebuilds it from the raw Excel file
- `model_pipeline.py` — the SARIMAX backtest + forecast, run per country
- `build_history_and_forecast.py` — merges history and SARIMAX forecasts
  into `country_product_history_and_forecast.csv`
- `apply_gbm_to_production.py` — merges the GBM forecasts into that same
  combined file and flags which model is used per combination

**Forecast accuracy tracking — did we actually get it right?**
- `snapshot_forecast.py` — saves the current 12-week forecast before it gets
  overwritten by the next refresh, so it can be checked later against what
  actually happened. Deliberately keeps the *first* prediction made for each
  future week (the longest lead time), not the most recent one, so the
  accuracy check is a genuine 12-week-ahead test, not a shorter, easier one.
- `validate_forecast_accuracy.py` — once real data arrives for a
  previously-forecasted week, compares the two and reports mean absolute
  error, whether the actual price fell inside the stated 80% interval, and
  how accuracy changes by how far ahead the prediction was made
- `forecast_snapshots.csv`, `forecast_validation_detail.csv`,
  `forecast_validation_summary.csv` — the running log and its results

**Power BI**
- `build_full_powerbi_export.py` — builds `Barrl_PowerBI_Full_Dashboard_Data.xlsx`
  (in `../power_bi/`), covering **all 52 combinations in one workbook** with
  Country/Product slicers, matching the Streamlit app's full scope. This is
  the export used for the actual Power BI dashboard.
- `build_powerbi_export.py` — powers the in-app "Download Power BI workbook"
  button, which exports only whichever single country/product is currently
  selected in the sidebar. Kept separate from the full export above — the
  two serve different purposes and `app.py` imports this one by name, so it
  can't be renamed or merged with the other.
- `requirements.txt` — pinned minimum versions

**Not in this folder, submitted separately** (see `../docs/` and `../power_bi/`):
the model comparison report, the SARIMAX methodology explainer, the
deployment guide, and the Power BI dashboard build guide + workbook.

## Run it

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. Defaults to the EU-aggregate diesel view;
use the **Region** and **Product** dropdowns in the sidebar to switch to any
of the 10 countries.

## Why country/product forecasts are precomputed, not live-fit

The EU-aggregate model refits live because it's a single series. With 52
country/product combinations, each needing an order-search SARIMAX fit plus
a rolling-origin backtest, refitting on every dropdown change would mean a
multi-second wait on every interaction. Instead, all 52 combinations are
scored once offline and served from the CSV/JSON files above — a standard
batch-scoring pattern for a BI dashboard. Consequently the forecast horizon
is fixed at 12 weeks for country/product views (the EU-aggregate view keeps
its adjustable slider). Run `refresh_all.py` to update the scores.

## Keeping the Power BI workbook in sync (two clicks, not a manual export)

Power BI can't run the Python agent live, so full real-time sync isn't
possible without extra infrastructure (Power BI streaming datasets — a
bigger lift than this project needs). Instead:

1. Run `python refresh_all.py` — this regenerates
   `../power_bi/Barrl_PowerBI_Full_Dashboard_Data.xlsx` automatically as its
   last step, covering all 52 combinations.
2. In Power BI Desktop, click **Home → Refresh**. Power BI re-reads the same
   file, so it picks up the new numbers.

For a quick single-combination snapshot instead of the full dashboard, the
in-app "Download Power BI workbook" button (sidebar) works the same
two-click way, just scoped to whichever combination is currently selected.

## Notes

- **The AI briefing tab works without any API key** on both paths — it
  defaults to a rule-based, fully deterministic briefing built directly from
  the numbers on screen. Toggling "Use LLM-narrated briefing" and entering
  an Anthropic API key switches to a Claude-narrated version of the same
  facts; the key is only held in the Streamlit session, never written to disk.
- **Forecasting approach, EU-aggregate**: ARIMA on the pre-tax price
  (univariate — no exogenous inputs), tax held flat at its latest value.
- **Forecasting approach, country/product**: SARIMAX or LightGBM (see table
  above) on the pre-tax price, with exogenous regressors for SARIMAX — Brent
  crude (EIA via FRED) always; exchange rate additionally for the two
  non-Eurozone countries in scope (Poland, Czechia); calendar seasonality
  always. Tax held flat in both cases. Brent and FX are held at their latest
  observed value for the forecast horizon (a stated assumption, not a
  prediction of where they'll move) — see the model comparison document.
- **VAT/excise duty are not model inputs** — discovered during
  implementation that the workbook's VAT/Excise sheets only contain each
  country's *current* rate, not a historical series, so they can't serve as
  time-varying regressors. The realized tax gap (with-tax minus without-tax
  price, which does have full history) is used instead for the market/tax
  decomposition. See the model comparison document for the full explanation.
- **Excluded combinations**: 8 of 60 possible (country, product) pairs were
  excluded for insufficient history (mostly the >1% sulphur fuel oil grade,
  discontinued in most countries' reporting; also Austria has no LPG data)
  — see `completeness_report.csv` for the full list.
