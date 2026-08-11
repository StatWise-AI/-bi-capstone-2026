"""
EU Fuel Price Forecasting Agent — Streamlit demo.

Run with:
    pip install -r requirements.txt
    streamlit run app.py
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objects as go

from diesel_agent import DieselForecastAgent
from country_product_agent import CountryProductAgent, COUNTRY_LABELS, PRODUCT_LABELS, available_products_for
from build_powerbi_export import build_export, DEFAULT_OUT_PATH

st.set_page_config(page_title="EU Fuel Price Forecasting Agent", layout="wide")


# ----------------------------------------------------------------------
# Cached loading — the CSV read + ARIMA fit only reruns when the horizon
# actually changes, not on every widget interaction.
# ----------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading data and fitting the forecast model...")
def get_agent(horizon_weeks):
    return DieselForecastAgent(horizon_weeks=horizon_weeks)


@st.cache_resource(show_spinner="Loading precomputed country/product forecast...")
def get_country_agent(country_code, product):
    return CountryProductAgent(country_code, product)


@st.cache_data(show_spinner="Running the model backtest (this takes a few seconds)...")
def get_backtest(_agent, cache_key):
    return _agent.backtest_summary()


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
st.sidebar.title("Settings")

st.sidebar.subheader("Scope")
region_options = ["EU (aggregate)"] + [COUNTRY_LABELS[c] for c in
    ["DE", "FR", "IT", "ES", "NL", "BE", "PL", "AT", "CZ", "PT"]]
region = st.sidebar.selectbox("Region", region_options, index=0)
is_eu_aggregate = (region == "EU (aggregate)")

if is_eu_aggregate:
    horizon = st.sidebar.slider("Forecast horizon (weeks)", min_value=4, max_value=26, value=12, step=1)
    product_code = "diesel"
    country_code = "EU"
else:
    country_code = [k for k, v in COUNTRY_LABELS.items() if v == region][0]
    product_options = available_products_for(country_code)
    product_display = st.sidebar.selectbox("Product", [PRODUCT_LABELS[p] for p in product_options])
    product_code = [p for p in product_options if PRODUCT_LABELS[p] == product_display][0]
    st.sidebar.caption("Forecast horizon fixed at 12 weeks for country/product views (precomputed — see README).")
    horizon = 12

history_window = st.sidebar.selectbox(
    "History shown in chart",
    ["Last 2 years", "Last 5 years", "Full history (2005-present)"],
    index=0,
)
st.sidebar.divider()

if is_eu_aggregate:
    agent = get_agent(horizon)
else:
    agent = get_country_agent(country_code, product_code)
cache_key = (country_code, product_code, horizon)

st.sidebar.subheader("AI briefing")
use_llm = st.sidebar.toggle("Use LLM-narrated briefing", value=False)
api_key = None
if use_llm:
    api_key = st.sidebar.text_input("Anthropic API key", type="password", help="Not stored; used only for this session.")
st.sidebar.divider()

st.sidebar.subheader("Power BI export")
st.sidebar.caption(
    "Rebuilds the Power BI workbook from the current data and forecast. Power BI itself still needs "
    "Home \u2192 Refresh after this — see README for the two-click workflow."
)
if st.sidebar.button("\U0001F504 Refresh Power BI export", type="primary"):
    with st.spinner("Rebuilding Power BI workbook..."):
        out_path = build_export(agent, DEFAULT_OUT_PATH)
    st.session_state["pbi_export_path"] = out_path
    st.session_state["pbi_export_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.sidebar.success(f"Updated {os.path.basename(out_path)}")

if os.path.exists(st.session_state.get("pbi_export_path", DEFAULT_OUT_PATH)):
    export_path = st.session_state.get("pbi_export_path", DEFAULT_OUT_PATH)
    with open(export_path, "rb") as f:
        st.sidebar.download_button(
            "Download Power BI workbook", f.read(),
            file_name="EU_Diesel_PowerBI_Data_Model.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    if "pbi_export_time" in st.session_state:
        st.sidebar.caption(f"Last refreshed this session: {st.session_state['pbi_export_time']}")
    else:
        st.sidebar.caption("Showing the workbook already saved from a previous run. Click Refresh above to update it.")

st.sidebar.divider()
if is_eu_aggregate:
    st.sidebar.caption(
        "Source: European Commission Weekly Oil Bulletin (DG Energy), EU-aggregate series. "
        "Forecast model: ARIMA on the pre-tax price, tax held flat at its latest observed value."
    )
else:
    st.sidebar.caption(
        "Source: European Commission Weekly Oil Bulletin (DG Energy), country-level series, plus "
        "Brent crude (EIA via FRED) and, for non-Eurozone countries, the reported exchange rate. "
        "Forecast model: SARIMAX with exogenous regressors on the pre-tax price, tax held flat."
    )

snap = agent.current_snapshot()
combined = agent.get_combined()
combined["date"] = pd.to_datetime(combined["date"])
forecast_rows = agent.get_forecast()
meta = agent.get_meta()

# ----------------------------------------------------------------------
# Header + KPI row
# ----------------------------------------------------------------------
display_name = "EU aggregate — Diesel" if is_eu_aggregate else f"{region} — {PRODUCT_LABELS[product_code]}"

st.title(f"{display_name} price forecasting agent")
st.caption(f"Weekly price, with tax vs. market decomposition. Data as of {snap['as_of_date']}.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Current price (with tax)", f"€{snap['price_with_tax']:.0f} /1000L", f"{snap['week_over_week_change']:+.0f} WoW")
k2.metric("Tax share", f"{snap['tax_share_pct']:.0f}%", f"tax = €{snap['tax_amount']:.0f}")
k3.metric("4-week change", f"{snap['change_4w_pct']:+.1f}%")
fc_end = float(forecast_rows["price_with_tax_eur_per_1000l"].iloc[-1])
fc_change_pct = (fc_end / snap["price_with_tax"] - 1) * 100
k4.metric(f"{meta['horizon_weeks']}-week forecast", f"€{fc_end:.0f} /1000L", f"{fc_change_pct:+.1f}%")

tab_trend, tab_tax, tab_models, tab_brief = st.tabs(
    ["Trend & forecast", "Tax decomposition", "Model comparison", "AI briefing"]
)

# ----------------------------------------------------------------------
# Tab 1: Trend & forecast
# ----------------------------------------------------------------------
with tab_trend:
    if history_window == "Last 2 years":
        cutoff = combined["date"].max() - pd.Timedelta(weeks=104)
    elif history_window == "Last 5 years":
        cutoff = combined["date"].max() - pd.Timedelta(weeks=260)
    else:
        cutoff = combined["date"].min()
    plot_df = combined[combined["date"] >= cutoff].copy()

    hist = plot_df[~plot_df["is_forecast"]]
    fut = plot_df[plot_df["is_forecast"]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist["date"], y=hist["price_with_tax_eur_per_1000l"],
        mode="lines", name="Actual (with tax)", line=dict(color="#2a78d6", width=2),
    ))
    if len(fut):
        # bridge the gap so the forecast line visually connects to the last actual point
        bridge_date = hist["date"].iloc[-1]
        bridge_val = hist["price_with_tax_eur_per_1000l"].iloc[-1]
        fx = pd.concat([pd.Series([bridge_date]), fut["date"]])
        fy = pd.concat([pd.Series([bridge_val]), fut["price_with_tax_eur_per_1000l"]])
        fy_lo = pd.concat([pd.Series([bridge_val]), fut["price_with_tax_lower80"]])
        fy_hi = pd.concat([pd.Series([bridge_val]), fut["price_with_tax_upper80"]])

        fig.add_trace(go.Scatter(
            x=pd.concat([fx, fx[::-1]]), y=pd.concat([fy_hi, fy_lo[::-1]]),
            fill="toself", fillcolor="rgba(235,104,52,0.15)", line=dict(color="rgba(0,0,0,0)"),
            name="80% interval", showlegend=True, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=fx, y=fy, mode="lines", name="Forecast",
            line=dict(color="#eb6834", width=2, dash="dash"),
        ))

    fig.update_layout(
        height=440, margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="EUR per 1000 litres", legend=dict(orientation="h", y=1.05),
        hovermode="x unified",
    )
    st.plotly_chart(fig, width='stretch')

    with st.expander("Forecast values (table)"):
        show = forecast_rows[["date", "price_with_tax_eur_per_1000l", "price_with_tax_lower80",
                               "price_with_tax_upper80", "forecast_method"]].copy()
        show.columns = ["Date", "Forecast (with tax)", "Lower 80%", "Upper 80%", "Model"]
        st.dataframe(show.round(1), width='stretch', hide_index=True)

    csv_bytes = combined.to_csv(index=False).encode("utf-8")
    fname = "eu_diesel" if is_eu_aggregate else f"{country_code.lower()}_{product_code}"
    st.download_button("Download history + forecast (CSV)", csv_bytes,
                        file_name=f"{fname}_price_history_and_forecast.csv", mime="text/csv")

# ----------------------------------------------------------------------
# Tab 2: Tax decomposition
# ----------------------------------------------------------------------
with tab_tax:
    st.subheader("Market price vs. tax component")
    hist_all = combined[~combined["is_forecast"]]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=hist_all["date"], y=hist_all["price_with_tax_eur_per_1000l"],
                               name="With tax", line=dict(color="#2a78d6", width=2)))
    fig2.add_trace(go.Scatter(x=hist_all["date"], y=hist_all["price_wo_tax_eur_per_1000l"],
                               name="Without tax (market)", line=dict(color="#eb6834", width=2)))
    fig2.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10),
                        yaxis_title="EUR per 1000 litres", legend=dict(orientation="h", y=1.05),
                        hovermode="x unified")
    st.plotly_chart(fig2, width='stretch')

    st.subheader("Tax share of retail price over time")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=hist_all["date"], y=hist_all["tax_share_of_price"] * 100,
                               name="Tax share %", line=dict(color="#1baf7a", width=2), fill="tozeroy",
                               fillcolor="rgba(27,175,122,0.1)"))
    fig3.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10),
                        yaxis_title="Tax share of price (%)", hovermode="x unified")
    st.plotly_chart(fig3, width='stretch')
    st.caption(
        "Tax share falls when the market price spikes (excise duty is mostly a fixed euro amount per "
        "litre, so it matters less as the pre-tax price rises) and rises again as the market price falls."
    )

# ----------------------------------------------------------------------
# Tab 3: Model comparison
# ----------------------------------------------------------------------
with tab_models:
    st.subheader("Backtest: rolling-origin evaluation")
    if is_eu_aggregate:
        st.caption("12-week horizon. 10 fold origins spread across 2010-2026 to cover both calm periods and price shocks.")
    else:
        st.caption(
            "12-week horizon. Same fold origins for every method shown, so the comparison is apples-to-apples. "
            "Following professor feedback after the presentation, gradient-boosted trees (LightGBM) were added "
            "to this comparison for diesel and heating oil — see the model comparison document, Section 8."
        )
    bt = get_backtest(agent, cache_key)
    bt_display = bt.copy()
    bt_display["method"] = bt_display["method"].str.upper()
    bt_display = bt_display.rename(columns={"method": "Method", "mean_mae": "Mean MAE",
                                              "mean_rmse": "Mean RMSE", "n_folds": "Folds"})
    best_method = bt_display.loc[bt_display["Mean MAE"].idxmin(), "Method"]
    st.dataframe(
        bt_display.round(2).style.apply(
            lambda row: ["background-color: rgba(27,175,122,0.15)" if row["Method"] == best_method else "" for _ in row],
            axis=1,
        ),
        width='stretch', hide_index=True,
    )
    if is_eu_aggregate:
        st.caption(
            f"Lowest mean MAE: **{best_method}**. The production forecast above always uses ARIMA rather than "
            "whichever method wins on raw error, because ARIMA is the only one of the four that provides a "
            "genuine confidence interval — important for a decision-support tool, not just point accuracy."
        )
    else:
        model_used = meta.get("model_used", "sarimax")
        if model_used == "gbm":
            st.caption(
                f"Lowest mean MAE: **{best_method}**. The production forecast for this country/product uses "
                "**gradient-boosted trees (LightGBM)**, not SARIMAX — this specific combination was switched "
                f"after the backtest above showed it winning clearly. {meta.get('model_switch_reason', '')}"
            )
        else:
            st.caption(
                f"Lowest mean MAE: **{best_method}**. The production forecast for this country/product still uses "
                "**SARIMAX**: either it won this backtest, or gradient-boosted trees were tested and did not "
                "improve on it enough (or at all) to justify the loss of interpretability — see the model "
                "comparison document, Section 8, for the full country/product breakdown."
            )

# ----------------------------------------------------------------------
# Tab 4: AI briefing
# ----------------------------------------------------------------------
with tab_brief:
    st.subheader("Decision-support briefing")
    if st.button("Generate briefing", type="primary"):
        if use_llm and api_key:
            briefing = agent.generate_briefing_llm(api_key=api_key)
        else:
            briefing = agent.generate_briefing()
        st.markdown(briefing)
    else:
        st.info("Click the button to generate a fresh decision-support briefing from the current data and forecast.")

    with st.expander("How this briefing is generated"):
        st.write(
            "The rule-based briefing is fully deterministic: every sentence is built directly from the "
            "current snapshot and forecast numbers shown in the other tabs, so it can't hallucinate a "
            "figure that isn't already on screen. The optional LLM mode sends those same numbers to "
            "Claude to produce more naturally-worded prose, with the rule-based version as a fallback "
            "if no API key is provided or the call fails."
        )
