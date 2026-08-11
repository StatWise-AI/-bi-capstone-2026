"""
DieselForecastAgent — decision-support agent layer, portable version for the
Streamlit app. See forecasting.py for the underlying model logic.
"""
import os
import json
import pandas as pd

from forecasting import load_series, run_backtest, build_forecast_output, HORIZON


class DieselForecastAgent:
    def __init__(self, horizon_weeks=HORIZON):
        self.horizon_weeks = horizon_weeks
        self.df, self.s_wt, self.s_wo, self.s_tax = load_series()
        self._combined = None
        self._forward_comparison = None
        self._meta = None
        self._backtest_summary = None
        self._backtest_folds = None

    def _ensure_forecast(self):
        if self._combined is None:
            self._combined, self._forward_comparison, self._meta = build_forecast_output(
                self.df, self.s_wt, self.s_wo, self.s_tax, horizon=self.horizon_weeks
            )

    def _ensure_backtest(self):
        if self._backtest_summary is None:
            self._backtest_summary, self._backtest_folds = run_backtest(self.s_wo)

    def refresh(self):
        self._combined = None
        self._forward_comparison = None
        self._meta = None
        self._backtest_summary = None
        self._backtest_folds = None

    def get_history(self):
        self._ensure_forecast()
        return self._combined[~self._combined["is_forecast"]].copy()

    def get_forecast(self):
        self._ensure_forecast()
        return self._combined[self._combined["is_forecast"]].copy()

    def get_combined(self):
        self._ensure_forecast()
        return self._combined.copy()

    def get_meta(self):
        self._ensure_forecast()
        meta = dict(self._meta)
        meta["model_name"] = f"ARIMA{meta['arima_order']}"
        return meta

    def backtest_summary(self):
        self._ensure_backtest()
        return pd.DataFrame(self._backtest_summary).T.rename_axis("method").reset_index()

    def current_snapshot(self):
        last = self.df.iloc[-1]
        prev_4w = self.df.iloc[-5] if len(self.df) >= 5 else self.df.iloc[0]
        prev_52w = self.df.iloc[-53] if len(self.df) >= 53 else self.df.iloc[0]
        wow = self.df.iloc[-1]["price_with_tax_eur_per_1000l"] - self.df.iloc[-2]["price_with_tax_eur_per_1000l"]
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
        self._ensure_forecast()
        snap = self.current_snapshot()
        fc = self.get_forecast()
        meta = self._meta

        fc_end_price = float(fc["price_with_tax_eur_per_1000l"].iloc[-1])
        fc_change_pct = (fc_end_price / snap["price_with_tax"] - 1) * 100
        direction = "rise" if fc_change_pct > 1 else ("fall" if fc_change_pct < -1 else "stay roughly flat")

        lower_end = float(fc["price_with_tax_lower80"].iloc[-1])
        upper_end = float(fc["price_with_tax_upper80"].iloc[-1])

        lines = []
        lines.append(
            f"As of {snap['as_of_date']}, the EU-average diesel price (with tax) is "
            f"€{snap['price_with_tax']:.0f} per 1000 litres, of which €{snap['tax_amount']:.0f} "
            f"({snap['tax_share_pct']:.0f}%) is tax and duties."
        )
        lines.append(
            f"Over the last 4 weeks the price has moved {snap['change_4w_pct']:+.1f}%, "
            f"and over the last 52 weeks {snap['change_52w_pct']:+.1f}%."
        )
        lines.append(
            f"The {meta['horizon_weeks']}-week forecast ({meta['arima_order']} ARIMA model on the "
            f"pre-tax market price, tax held flat at its latest observed level) projects the price to "
            f"{direction}, reaching approximately €{fc_end_price:.0f} by {fc['date'].iloc[-1].date()} "
            f"(80% interval: €{lower_end:.0f}-€{upper_end:.0f})."
        )
        if fc_change_pct > 1:
            lines.append(
                "Recommendation: if procurement or budgeting decisions are pending, consider locking in "
                "purchase prices sooner rather than later, since the central forecast points upward."
            )
        elif fc_change_pct < -1:
            lines.append(
                "Recommendation: if there is flexibility on timing, deferring large purchases may be "
                "worthwhile, since the central forecast points downward."
            )
        else:
            lines.append(
                "Recommendation: the central forecast is close to flat, so timing purchases around the "
                "forecast alone offers little advantage — base the decision on other operational factors."
            )
        lines.append(
            "Caveat: this assumes no change in tax policy over the forecast window. A scheduled excise "
            "or VAT change in any member state would shift the with-tax figure without affecting the "
            "underlying market forecast."
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
            resp = client.messages.create(
                model=model,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(block.text for block in resp.content if block.type == "text")
            return text
        except Exception as e:
            return base_briefing + f"\n\n(LLM narration unavailable: {e})"
