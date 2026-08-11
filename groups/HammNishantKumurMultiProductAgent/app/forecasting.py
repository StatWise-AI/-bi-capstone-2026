"""
EU diesel price forecasting pipeline (portable version for the Streamlit app).

Same logic as the analysis notebook version, with one change: the data path
resolves relative to this file's own folder, so the app runs anywhere it's
copied (this sandbox, your laptop, or a deployment server) rather than only
against the original build path.

Strategy recap:
- Forecast the PRE-TAX (market) price series with ARIMA (auto-selected order
  via AIC grid search) because it behaves like a real market time series.
- Tax is policy-driven (step changes), so it's held flat at its latest
  observed value rather than forecast statistically.
- Final with-tax forecast = forecast(wo-tax) + latest tax_amount.
"""
import os
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings("ignore")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_DIR, "eu_diesel_price_weekly_2005_2026.csv")

HORIZON = 12          # weeks ahead
MIN_TRAIN_WEEKS = 260  # require at least 5 years of history before the first backtest fold


def load_series(data_path=DATA_PATH):
    df = pd.read_csv(data_path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    s_wt = df.set_index("date")["price_with_tax_eur_per_1000l"]
    s_wo = df.set_index("date")["price_wo_tax_eur_per_1000l"]
    s_tax = df.set_index("date")["tax_amount_eur_per_1000l"]
    return df, s_wt, s_wo, s_tax


def naive_forecast(train, horizon):
    last = train.iloc[-1]
    return np.repeat(last, horizon)


def ma_baseline_forecast(train, horizon, window=13):
    ma = train.rolling(window=window, min_periods=1).mean().iloc[-1]
    return np.repeat(ma, horizon)


def holt_forecast(train, horizon):
    model = ExponentialSmoothing(train.values, trend="add", damped_trend=True, seasonal=None)
    fit = model.fit(optimized=True)
    return fit.forecast(horizon)


def arima_forecast(train, horizon):
    best_aic = np.inf
    best_order = (1, 1, 1)
    for order in [(0,1,0), (1,1,0), (0,1,1), (1,1,1), (2,1,1), (1,1,2), (2,1,2), (1,0,0), (0,0,1)]:
        try:
            fit = ARIMA(train.values, order=order).fit()
            if fit.aic < best_aic:
                best_aic = fit.aic
                best_order = order
        except Exception:
            continue
    final_fit = ARIMA(train.values, order=best_order).fit()
    fc = final_fit.get_forecast(horizon)
    mean = fc.predicted_mean
    ci = fc.conf_int(alpha=0.2)  # 80% interval
    return mean, ci, best_order


def mae(actual, pred):
    return float(np.mean(np.abs(np.asarray(actual) - np.asarray(pred))))


def rmse(actual, pred):
    return float(np.sqrt(np.mean((np.asarray(actual) - np.asarray(pred)) ** 2)))


def run_backtest(s_wo, n_origins=10, horizon=HORIZON):
    n = len(s_wo)
    results = {"naive": [], "ma13": [], "holt": [], "arima": []}
    fold_details = []
    last_possible_origin = n - horizon
    origins = np.linspace(MIN_TRAIN_WEEKS, last_possible_origin, n_origins).astype(int)
    origins = sorted(set(origins.tolist()))

    for origin in origins:
        train = s_wo.iloc[:origin]
        actual = s_wo.iloc[origin:origin + horizon].values
        if len(actual) < horizon:
            continue

        pred_naive = naive_forecast(train, horizon)
        pred_ma13 = ma_baseline_forecast(train, horizon, window=13)
        pred_holt = holt_forecast(train, horizon)
        pred_arima, _, order = arima_forecast(train, horizon)

        results["naive"].append((mae(actual, pred_naive), rmse(actual, pred_naive)))
        results["ma13"].append((mae(actual, pred_ma13), rmse(actual, pred_ma13)))
        results["holt"].append((mae(actual, pred_holt), rmse(actual, pred_holt)))
        results["arima"].append((mae(actual, pred_arima), rmse(actual, pred_arima)))

        fold_details.append({"origin_date": str(s_wo.index[origin].date()), "arima_order": order})

    summary = {}
    for method, vals in results.items():
        maes = [v[0] for v in vals]
        rmses = [v[1] for v in vals]
        summary[method] = {
            "mean_mae": float(np.mean(maes)),
            "mean_rmse": float(np.mean(rmses)),
            "n_folds": len(maes),
        }
    return summary, fold_details


def build_forecast_output(df, s_wt, s_wo, s_tax, horizon=HORIZON):
    mean, ci, order = arima_forecast(s_wo, horizon)
    naive_fc = naive_forecast(s_wo, horizon)
    ma13_fc = ma_baseline_forecast(s_wo, horizon, window=13)

    last_date = s_wo.index[-1]
    freq_days = int(np.median(np.diff(s_wo.index.values).astype('timedelta64[D]').astype(int)))
    future_dates = [last_date + pd.Timedelta(days=freq_days * (i + 1)) for i in range(horizon)]

    latest_tax_amount = s_tax.iloc[-1]
    latest_tax_share = (s_wt.iloc[-1] - s_wo.iloc[-1]) / s_wt.iloc[-1]

    wo_tax_point = mean
    wo_tax_lower = ci[:, 0]
    wo_tax_upper = ci[:, 1]

    with_tax_point = wo_tax_point + latest_tax_amount
    with_tax_lower = wo_tax_lower + latest_tax_amount
    with_tax_upper = wo_tax_upper + latest_tax_amount
    with_tax_point_altshare = wo_tax_point / (1 - latest_tax_share)

    hist = pd.DataFrame({
        "date": df["date"],
        "price_with_tax_eur_per_1000l": df["price_with_tax_eur_per_1000l"],
        "price_wo_tax_eur_per_1000l": df["price_wo_tax_eur_per_1000l"],
        "tax_amount_eur_per_1000l": df["tax_amount_eur_per_1000l"],
        "tax_share_of_price": df["tax_share_of_price"],
        "is_forecast": False,
        "forecast_method": None,
        "price_with_tax_lower80": None,
        "price_with_tax_upper80": None,
    })

    fc = pd.DataFrame({
        "date": future_dates,
        "price_with_tax_eur_per_1000l": with_tax_point,
        "price_wo_tax_eur_per_1000l": wo_tax_point,
        "tax_amount_eur_per_1000l": latest_tax_amount,
        "tax_share_of_price": latest_tax_share,
        "is_forecast": True,
        "forecast_method": f"ARIMA{order}",
        "price_with_tax_lower80": with_tax_lower,
        "price_with_tax_upper80": with_tax_upper,
    })

    combined = pd.concat([hist, fc], ignore_index=True)

    forward_comparison = pd.DataFrame({
        "date": future_dates,
        "naive_wo_tax": naive_fc,
        "ma13_wo_tax": ma13_fc,
        "arima_wo_tax": wo_tax_point,
        "arima_with_tax_flat_amount": with_tax_point,
        "arima_with_tax_flat_share": with_tax_point_altshare,
    })

    meta = {
        "arima_order": order,
        "latest_tax_amount": float(latest_tax_amount),
        "latest_tax_share": float(latest_tax_share),
        "horizon_weeks": horizon,
        "last_history_date": str(last_date.date()),
    }
    return combined, forward_comparison, meta
