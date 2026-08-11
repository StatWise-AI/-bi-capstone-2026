"""
Parameterized (country, product) forecasting pipeline for the upgraded,
multivariate version of the project.

For every included (country, product) combination (see completeness_report.csv):
  1. Build exogenous regressors: Brent crude (real monthly EIA/FRED data,
     forward-filled to weekly), exchange rate (only for non-Eurozone
     countries -- constant=1.0 for Eurozone gives no signal, so it's
     dropped from the regressor set for those), and calendar seasonality
     (sin/cos of month).
  2. Backtest three methods with a rolling-origin evaluation (12-week
     horizon): naive persistence, plain ARIMA (no exogenous inputs -- the
     original single-series approach), and SARIMAX with the exogenous
     regressors above. This directly tests whether adding exogenous
     variables actually improves on the original approach, rather than
     assuming it does.
  3. Refit the chosen production model (SARIMAX) on full history and
     produce a forward forecast with an 80% interval.
  4. Reconstruct the with-tax price forecast by adding the latest observed
     tax amount (price_with_tax - price_wo_tax), held flat -- identical
     assumption to the original EU-aggregate model.

Future exogenous values needed for the forecast horizon (Brent, FX) are held
at their last observed value -- a documented, explicit assumption (see
comparison document), not a prediction of where crude or FX will move.
"""
import pandas as pd
import numpy as np
import time
import json
import warnings
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings("ignore")

import os
MASTER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_country_product_weekly.csv")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
HORIZON = 12
ORDER_GRID = [(0,1,0), (1,1,0), (0,1,1), (1,1,1)]
MIN_TRAIN_WEEKS = 100
N_ORIGINS_MAX = 4


def build_exog(sub, is_eurozone):
    month = sub["date"].dt.month.values
    cols = [sub["brent_usd_per_bbl"].values, np.sin(2*np.pi*month/12), np.cos(2*np.pi*month/12)]
    names = ["brent", "month_sin", "month_cos"]
    if not is_eurozone:
        cols.append(sub["exchange_rate"].values)
        names.append("fx_rate")
    return np.column_stack(cols), names


def naive_forecast(train_y, horizon):
    return np.repeat(train_y[-1], horizon)


def fit_arima_order_search(y, horizon, exog=None, exog_future=None):
    best_aic, best_order, best_fit = np.inf, (1,1,1), None
    for order in ORDER_GRID:
        try:
            fit = SARIMAX(y, exog=exog, order=order, enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
            if fit.aic < best_aic:
                best_aic, best_order, best_fit = fit.aic, order, fit
        except Exception:
            continue
    if best_fit is None:
        return None, None, best_order
    fc = best_fit.get_forecast(horizon, exog=exog_future)
    return fc.predicted_mean, fc.conf_int(alpha=0.2), best_order


def mae(a, p):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(p))))


def rmse(a, p):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(p)) ** 2)))


def run_pipeline_for_combo(country, product, sub):
    sub = sub.sort_values("date").reset_index(drop=True)
    is_eurozone = bool(sub["is_eurozone"].iloc[0])
    y = sub["price_wo_tax"].values
    exog_full, exog_names = build_exog(sub, is_eurozone)
    n = len(sub)

    # ---------------- Backtest: naive vs plain ARIMA (no exog) vs SARIMAX (exog) ----------------
    last_origin = n - HORIZON
    n_origins = min(N_ORIGINS_MAX, max(2, (last_origin - MIN_TRAIN_WEEKS) // 20))
    if last_origin - MIN_TRAIN_WEEKS < 20:
        n_origins = 2
    origins = sorted(set(np.linspace(MIN_TRAIN_WEEKS, last_origin, n_origins).astype(int).tolist()))

    results = {"naive": [], "arima_noexog": [], "sarimax_exog": []}
    for origin in origins:
        if origin + HORIZON > n:
            continue
        y_train, y_test = y[:origin], y[origin:origin+HORIZON]
        exog_train, exog_test = exog_full[:origin], exog_full[origin:origin+HORIZON]

        p_naive = naive_forecast(y_train, HORIZON)
        results["naive"].append((mae(y_test, p_naive), rmse(y_test, p_naive)))

        mean_ne, _, _ = fit_arima_order_search(y_train, HORIZON, exog=None, exog_future=None)
        if mean_ne is not None:
            results["arima_noexog"].append((mae(y_test, mean_ne), rmse(y_test, mean_ne)))

        mean_ex, _, _ = fit_arima_order_search(y_train, HORIZON, exog=exog_train, exog_future=exog_test)
        if mean_ex is not None:
            results["sarimax_exog"].append((mae(y_test, mean_ex), rmse(y_test, mean_ex)))

    backtest_summary = {}
    for method, vals in results.items():
        if not vals:
            backtest_summary[method] = {"mean_mae": None, "mean_rmse": None, "n_folds": 0}
            continue
        maes, rmses = zip(*vals)
        backtest_summary[method] = {"mean_mae": float(np.mean(maes)), "mean_rmse": float(np.mean(rmses)), "n_folds": len(vals)}

    # ---------------- Production forecast: SARIMAX on full history ----------------
    exog_future = np.tile(exog_full[-1], (HORIZON, 1)).astype(float)
    # let seasonal terms actually roll forward in the future exog (Brent/FX held flat, season doesn't have to be)
    last_date = sub["date"].iloc[-1]
    future_dates = pd.date_range(last_date + pd.Timedelta(days=7), periods=HORIZON, freq="7D")
    future_month = future_dates.month.values
    exog_future[:, 1] = np.sin(2*np.pi*future_month/12)
    exog_future[:, 2] = np.cos(2*np.pi*future_month/12)

    mean_fc, ci_fc, order = fit_arima_order_search(y, HORIZON, exog=exog_full, exog_future=exog_future)

    latest_tax_amount = float(sub["tax_amount"].iloc[-1])
    latest_tax_share = float(sub["tax_share"].iloc[-1])

    if mean_fc is not None:
        with_tax_fc = mean_fc + latest_tax_amount
        with_tax_lower = ci_fc[:, 0] + latest_tax_amount
        with_tax_upper = ci_fc[:, 1] + latest_tax_amount
    else:
        with_tax_fc = with_tax_lower = with_tax_upper = np.full(HORIZON, np.nan)

    forecast_df = pd.DataFrame({
        "country": country, "product": product, "date": future_dates,
        "price_wo_tax_forecast": mean_fc if mean_fc is not None else np.nan,
        "price_with_tax_forecast": with_tax_fc,
        "price_with_tax_lower80": with_tax_lower,
        "price_with_tax_upper80": with_tax_upper,
    })

    meta = {
        "country": country, "product": product,
        "n_weeks": n, "is_eurozone": is_eurozone,
        "sarimax_order": order, "exog_names": exog_names,
        "latest_tax_amount": latest_tax_amount, "latest_tax_share": latest_tax_share,
        "backtest": backtest_summary,
        "n_backtest_origins": len(origins),
    }
    return forecast_df, meta


if __name__ == "__main__":
    import sys
    import os
    country_filter = sys.argv[1] if len(sys.argv) > 1 else None

    master = pd.read_csv(MASTER_PATH, parse_dates=["date"])
    comp = pd.read_csv(f"{OUT_DIR}/completeness_report.csv")
    combos = comp[comp["included"]][["country", "product"]].values.tolist()
    if country_filter:
        combos = [c for c in combos if c[0].strip("_") == country_filter]

    fc_path = f"{OUT_DIR}/country_product_forecasts.csv"
    meta_path = f"{OUT_DIR}/country_product_meta.json"

    existing_meta = []
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            existing_meta = json.load(f)

    all_forecasts = []
    all_meta = []
    t0 = time.time()
    for i, (country, product) in enumerate(combos):
        sub = master[(master["country"] == country.strip("_")) & (master["product"] == product)]
        if sub.empty:
            continue
        fc_df, meta = run_pipeline_for_combo(country.strip("_"), product, sub)
        all_forecasts.append(fc_df)
        all_meta.append(meta)
        print(f"[{i+1}/{len(combos)}] {country.strip('_'):3s} {product:12s} "
              f"order={meta['sarimax_order']} naive_mae={meta['backtest']['naive']['mean_mae']:.1f} "
              f"noexog_mae={meta['backtest']['arima_noexog']['mean_mae']:.1f} "
              f"exog_mae={meta['backtest']['sarimax_exog']['mean_mae']:.1f} "
              f"({time.time()-t0:.0f}s elapsed)", flush=True)

    forecasts = pd.concat(all_forecasts, ignore_index=True)
    if os.path.exists(fc_path):
        forecasts.to_csv(fc_path, mode="a", header=False, index=False)
    else:
        forecasts.to_csv(fc_path, index=False)

    combined_meta = existing_meta + all_meta
    with open(meta_path, "w") as f:
        json.dump(combined_meta, f, indent=2, default=str)

    print(f"\nBatch time: {time.time()-t0:.0f}s for {len(combos)} combinations (country={country_filter})")
