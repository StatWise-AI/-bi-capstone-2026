"""
CountryProductAgent -- serves precomputed country/product forecasts through
the exact same interface as DieselForecastAgent (current_snapshot(),
get_history(), get_forecast(), get_combined(), backtest_summary(),
get_meta(), generate_briefing(), generate_briefing_llm()).

Why precomputed rather than live-fit like the EU-aggregate agent: with 52
country/product combinations, each requiring an order-search SARIMAX fit
plus a rolling-origin backtest, refitting on every dropdown change in the
app would mean a multi-second wait on every interaction. Instead, all 52
combinations are scored once offline (see model_pipeline.py) and the results
are served here -- a standard batch-scoring pattern for a BI dashboard.
Re-run model_pipeline.py and refresh the CSV/JSON files to update the scores
(e.g. weekly, alongside a new Oil Bulletin release).

Matching DieselForecastAgent's interface means app.py's rendering code for
the trend chart, tax decomposition, model comparison, and AI briefing tabs
does not need to change at all -- only the object constructed by the country
selector changes.
"""
import os
import json
import pandas as pd
import numpy as np

APP_DIR = os.path.dirname(os.path.abspath(__file__))
HISTFC_PATH = os.path.join(APP_DIR, "country_product_history_and_forecast.csv")
META_PATH = os.path.join(APP_DIR, "country_product_meta.json")

COUNTRY_LABELS = {
    "DE": "Germany", "FR": "France", "IT": "Italy", "ES": "Spain",
    "NL": "Netherlands", "BE": "Belgium", "PL": "Poland", "AT": "Austria",
    "CZ": "Czechia", "PT": "Portugal",
}
PRODUCT_LABELS = {
    "euro95": "Petrol (Euro-95)", "diesel": "Diesel", "heating_oil": "Heating oil",
    "fuel_oil_1": "Fuel oil (\u22641% sulphur)", "fuel_oil_2": "Fuel oil (>1% sulphur)", "lpg": "LPG",
}


def available_products_for(country_code):
    comp = pd.read_csv(os.path.join(APP_DIR, "completeness_report.csv"))
    comp["country"] = comp["country"].str.strip("_")
    sub = comp[(comp["country"] == country_code) & (comp["included"])]
    return sub["product"].tolist()


class CountryProductAgent:
    def __init__(self, country_code, product):
        self.country_code = country_code
        self.product = product

        hist_fc = pd.read_csv(HISTFC_PATH, parse_dates=["date"])
        sub = hist_fc[(hist_fc["country"] == country_code) & (hist_fc["product"] == product)].copy()
        sub = sub.sort_values("date").reset_index(drop=True)
        sub["tax_amount_eur_per_1000l"] = sub["price_with_tax"] - sub["price_wo_tax"]
        sub["tax_share_of_price"] = sub["tax_amount_eur_per_1000l"] / sub["price_with_tax"]
        self._combined = sub.rename(columns={
            "price_with_tax": "price_with_tax_eur_per_1000l",
            "price_wo_tax": "price_wo_tax_eur_per_1000l",
        })

        with open(META_PATH) as f:
            all_meta = json.load(f)
        self._meta_raw = next(
            (m for m in all_meta if m["country"] == country_code and m["product"] == product), None
        )
        if self._meta_raw is None:
            raise ValueError(f"No precomputed results for {country_code}/{product}")

        model_used = self._meta_raw.get("model_used", "sarimax")
        if model_used == "gbm":
            order_str = "LightGBM (direct multi-horizon)"
        else:
            order_str = f"SARIMAX{tuple(self._meta_raw['sarimax_order'])}"
        self._combined["forecast_method"] = self._combined["is_forecast"].map({True: order_str, False: None})

    def get_history(self):
        return self._combined[~self._combined["is_forecast"]].copy()

    def get_forecast(self):
        return self._combined[self._combined["is_forecast"]].copy()

    def get_combined(self):
        return self._combined.copy()

    def get_meta(self):
        m = self._meta_raw
        model_used = m.get("model_used", "sarimax")
        if model_used == "gbm":
            model_name = "LightGBM (direct multi-horizon)"
        else:
            model_name = f"SARIMAX{tuple(m['sarimax_order'])}"
        return {
            "arima_order": model_name,
            "model_name": model_name,
            "model_used": model_used,
            "model_switch_reason": m.get("model_switch_reason"),
            "country": COUNTRY_LABELS.get(self.country_code, self.country_code),
            "product": PRODUCT_LABELS.get(self.product, self.product),
            "latest_tax_amount": m["latest_tax_amount"],
            "latest_tax_share": m["latest_tax_share"],
            "horizon_weeks": len(self.get_forecast()),
            "last_history_date": str(self.get_history()["date"].max().date()),
            "exog_names": m["exog_names"],
            "is_eurozone": m["is_eurozone"],
            "n_backtest_origins": m.get("n_backtest_origins"),
        }

    def backtest_summary(self):
        bt = self._meta_raw["backtest"]
        rows = []
        name_map = {"naive": "naive", "arima_noexog": "arima (no exog)", "sarimax_exog": "sarimax (+exog)", "gbm": "gradient-boosted trees"}
        for key, label in name_map.items():
            if key not in bt:
                continue
            b = bt[key]
            rows.append({"method": label, "mean_mae": b["mean_mae"], "mean_rmse": b["mean_rmse"], "n_folds": b["n_folds"]})
        return pd.DataFrame(rows)

    def current_snapshot(self):
        hist = self.get_history()
        last = hist.iloc[-1]
        prev_4w = hist.iloc[-5] if len(hist) >= 5 else hist.iloc[0]
        prev_52w = hist.iloc[-53] if len(hist) >= 53 else hist.iloc[0]
        wow = hist.iloc[-1]["price_with_tax_eur_per_1000l"] - hist.iloc[-2]["price_with_tax_eur_per_1000l"]
        change_4w_pct = (last["price_with_tax_eur_per_1000l"] / prev_4w["price_with_tax_eur_per_1000l"] - 1) * 100
        change_52w_pct = (last["price_with_tax_eur_per_1000l"] / prev_52w["price_with_tax_eur_per_1000l"] - 1) * 100
        return {
            "as_of_date": str(last["date"].date()),
            "price_with_tax": round(float(last["price_with_tax_eur_per_1000l"]), 1),
            "price_wo_tax": round(float(last["price_wo_tax_eur_per_1000l"]), 1),
            "tax_amount": round(float(last["tax_amount_eur_per_1000l"]), 1),
            "tax_share_pct": round(float(last["tax_share_of_price"]) * 100, 1),
            "week_over_week_change": round(float(wow), 1),
            "change_4w_pct": round(float(change_4w_pct), 1),
            "change_52w_pct": round(float(change_52w_pct), 1),
        }

    def generate_briefing(self):
        snap = self.current_snapshot()
        fc = self.get_forecast()
        meta = self.get_meta()
        country_label = COUNTRY_LABELS.get(self.country_code, self.country_code)
        product_label = PRODUCT_LABELS.get(self.product, self.product)

        fc_end_price = float(fc["price_with_tax_eur_per_1000l"].iloc[-1])
        fc_change_pct = (fc_end_price / snap["price_with_tax"] - 1) * 100
        direction = "rise" if fc_change_pct > 1 else ("fall" if fc_change_pct < -1 else "stay roughly flat")
        lower_end = float(fc["price_with_tax_lower80"].iloc[-1])
        upper_end = float(fc["price_with_tax_upper80"].iloc[-1])

        exog_desc = ", ".join(n for n in meta["exog_names"] if n != "month_sin" and n != "month_cos")
        exog_desc = (exog_desc + ", and calendar seasonality") if exog_desc else "calendar seasonality only"

        lines = []
        lines.append(
            f"As of {snap['as_of_date']}, the {country_label} {product_label.lower()} price (with tax) is "
            f"\u20ac{snap['price_with_tax']:.0f} per 1000 litres, of which \u20ac{snap['tax_amount']:.0f} "
            f"({snap['tax_share_pct']:.0f}%) is tax and duties."
        )
        lines.append(
            f"Over the last 4 weeks the price has moved {snap['change_4w_pct']:+.1f}%, "
            f"and over the last 52 weeks {snap['change_52w_pct']:+.1f}%."
        )
        lines.append(
            f"The {meta['horizon_weeks']}-week forecast ({meta['arima_order']}, using {exog_desc} as inputs, "
            f"tax held flat at its latest observed level) projects the price to {direction}, reaching "
            f"approximately \u20ac{fc_end_price:.0f} by {fc['date'].iloc[-1].date()} "
            f"(80% interval: \u20ac{lower_end:.0f}-\u20ac{upper_end:.0f})."
        )
        if fc_change_pct > 1:
            lines.append("Recommendation: if procurement or budgeting decisions are pending, consider locking in "
                          "purchase prices sooner rather than later, since the central forecast points upward.")
        elif fc_change_pct < -1:
            lines.append("Recommendation: if there is flexibility on timing, deferring large purchases may be "
                          "worthwhile, since the central forecast points downward.")
        else:
            lines.append("Recommendation: the central forecast is close to flat, so timing purchases around the "
                          "forecast alone offers little advantage -- base the decision on other operational factors.")
        lines.append(
            "Caveat: this assumes no change in tax policy, and holds Brent crude"
            + (" and the exchange rate" if not meta["is_eurozone"] else "")
            + " flat at their latest observed levels over the forecast window."
        )
        return "\n\n".join(lines)

    def generate_briefing_llm(self, api_key=None, model="claude-sonnet-4-5"):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        base_briefing = self.generate_briefing()
        if not key:
            return base_briefing + "\n\n(LLM narration not used: no API key provided.)"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            snap = self.current_snapshot()
            prompt = (
                "You are a fuel-procurement decision-support assistant. Given these facts, "
                "write a short (4-6 sentence) executive briefing in plain language for a "
                "logistics/procurement manager. Be concrete and avoid hedging language beyond "
                "what the numbers support.\n\n"
                f"Facts:\n{json.dumps(snap, indent=2)}\n\n"
                f"Rule-based analysis for reference:\n{base_briefing}"
            )
            resp = client.messages.create(model=model, max_tokens=400, messages=[{"role": "user", "content": prompt}])
            return "".join(block.text for block in resp.content if block.type == "text")
        except Exception as e:
            return base_briefing + f"\n\n(LLM narration unavailable: {e})"
