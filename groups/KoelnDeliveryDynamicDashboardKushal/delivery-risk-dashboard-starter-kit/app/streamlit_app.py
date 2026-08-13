"""
streamlit_app.py
-----------------
Delivery Risk Dashboard + AI Agent
====================================
This is the deliverable app: a BI dashboard (filters, KPIs, charts) sitting
alongside a Claude-powered AI Agent chat panel that answers manager
questions grounded in the live filtered data and the trained model's
metrics.

STUDENTS: this file already works end-to-end. Your job is the dashboard
design and storytelling layer:
  - Rearrange / restyle the KPI cards and charts
  - Add filters relevant to your business narrative
  - Improve the layout, color palette, and copy
  - Extend agent.py's SYSTEM_PROMPT if you want the agent to reason about
    new KPIs you add
You are NOT expected to modify src/train_model.py or the ML logic.

Run locally:
    streamlit run app/streamlit_app.py

Deploy: push this repo to GitHub, then deploy directly from
https://share.streamlit.io (see STUDENT_GUIDE.md, Step 7).
"""
import json
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from predict import load_artifacts, predict_dataframe  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed", "model_ready_data.csv")
METRICS_PATH = os.path.join(BASE_DIR, "outputs", "metrics_summary.json")

st.set_page_config(page_title="Delivery Risk Dashboard", layout="wide", page_icon="📦")

# Streamlit Cloud: read the API key from st.secrets if present
if "ANTHROPIC_API_KEY" in st.secrets if hasattr(st, "secrets") else False:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]


@st.cache_data
def load_scored_data() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_PATH)
    X = df.drop(columns=["Delivery_Risk_Category"])
    model_bundle, preprocessor = load_artifacts()
    scored = predict_dataframe(X, model_bundle, preprocessor)
    scored["Actual_Risk"] = df["Delivery_Risk_Category"]
    return scored


@st.cache_data
def load_metrics() -> dict:
    with open(METRICS_PATH) as f:
        return json.load(f)


def kpi_card(col, label, value, help_text=None):
    col.metric(label, value, help=help_text)

def format_number(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return f"{value:.0f}"

def main():
    st.title("📦 Delivery Risk Dashboard")
    st.caption(
        "Predicts SKU-level delivery risk (High / Medium / Low) for the DataCo Global "
        "supply chain so operations managers can act before delays happen — instead of "
        "reacting after a shipment is already late."
    )

    metrics = load_metrics()
    df = load_scored_data()

    # ---------------------------------------------------------------- Filters
    with st.sidebar:
        st.header("Filters")
        regions = ["All"] + sorted(df["Order Region"].dropna().unique().tolist()) if "Order Region" in df else ["All"]
        region = st.selectbox("Order Region", regions)
        modes = ["All"] + sorted(df["Shipping Mode"].dropna().unique().tolist()) if "Shipping Mode" in df else ["All"]
        mode = st.selectbox("Shipping Mode", modes)
        risk_filter = st.multiselect(
            "Predicted Risk", ["High Risk", "Medium Risk", "Low Risk"],
            default=["High Risk", "Medium Risk", "Low Risk"],
        )
        st.divider()
        st.caption(f"Best model: **{metrics['best_model']}**")
        st.caption(f"Trained on {metrics['n_rows']:,} orders")

    filtered = df.copy()
    if region != "All":
        filtered = filtered[filtered["Order Region"] == region]
    if mode != "All":
        filtered = filtered[filtered["Shipping Mode"] == mode]
    filtered = filtered[filtered["Predicted_Risk"].isin(risk_filter)]

    # ---------------------------------------------------------------- KPIs
    c1, c2, c3, c4 = st.columns(4)

    # Financial KPIs
    total_sales = filtered["Sales"].sum()

    total_profit = filtered["Order Profit Per Order"].sum()

    avg_discount_rate = filtered["Discount_Rate"].mean() * 100 if len(filtered) else 0

    profit_margin = (
        (total_profit / total_sales) * 100
        if total_sales > 0 else 0
    )

    cancelled_orders = (
        filtered["Order Status"]
        .str.lower()
        .isin(["cancelled", "canceled"])
        .sum()
    )

    total_orders = len(filtered)

    cancellation_rate = (
        cancelled_orders / total_orders * 100
        if total_orders > 0 else 0
    )

    kpi_card(c1, "Total Orders", f"{len(filtered):,}")
    kpi_card(c1, "Total Sales", f"{format_number(total_sales)}")
    
    high_risk_pct = (filtered["Predicted_Risk"] == "High Risk").mean() * 100 if len(filtered) else 0
    kpi_card(c2, "High-risk orders", f"{high_risk_pct:.2f}%")
    high_risk_revenue = filtered.loc[filtered["Predicted_Risk"] == "High Risk", "Order_Value"].sum()
    kpi_card(c2, "High-risk revenue", f"{format_number(high_risk_revenue)}")

    kpi_card(c3, "Total Profit", f"{format_number(total_profit)}")
    kpi_card(c3, "Avg. Discount Rate", f"{avg_discount_rate:.2f}%")

    kpi_card(c4, "Profit Margin", f"{profit_margin:.2f}%")
    kpi_card(c4, "Cancellation Rate", f"{cancellation_rate:.2f}%")
    # accuracy = (filtered["Predicted_Risk"] == filtered["Actual_Risk"]).mean() * 100 if len(filtered) else 0
    # kpi_card(c3, "Prediction accuracy (this view)", f"{accuracy:.1f}%")
    # best_f1 = metrics["all_results"][metrics["best_model"]]["f1_weighted"]
    # kpi_card(c4, "Model F1 (weighted)", f"{best_f1:.2f}")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🌍 Regional & Shipping", "🤖 AI Agent"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            risk_counts = filtered["Predicted_Risk"].value_counts().reset_index()
            risk_counts.columns = ["Risk", "Count"]
            fig = px.bar(risk_counts, x="Risk", y="Count", color="Risk",
                         color_discrete_map={"High Risk": "#dc2626", "Medium Risk": "#f59e0b", "Low Risk": "#16a34a"},
                         title="Predicted Delivery Risk Distribution")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "Order_Month" in filtered.columns:
                monthly = filtered.groupby("Order_Month")["Predicted_Risk"].apply(
                    lambda s: (s == "High Risk").mean() * 100
                ).reset_index(name="High_Risk_Pct")
                fig2 = px.line(monthly, x="Order_Month", y="High_Risk_Pct", markers=True,
                                title="High-Risk Rate by Order Month (%)")
                st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Sample of scored orders")
        show_cols = [c for c in ["Order Region", "Shipping Mode", "Customer Segment",
                                  "Order_Value", "Predicted_Risk", "Recommended_Action"] if c in filtered.columns]
        st.dataframe(filtered[show_cols].head(200), use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            if "Order Region" in filtered.columns:
                region_risk = filtered.groupby("Order Region")["Predicted_Risk"].apply(
                    lambda s: (s == "High Risk").mean() * 100
                ).sort_values(ascending=False).reset_index(name="High_Risk_Pct")
                fig3 = px.bar(region_risk, x="Order Region", y="High_Risk_Pct",
                              title="High-Risk Rate by Region (%)")
                fig3.update_layout(xaxis_tickangle=-40)
                st.plotly_chart(fig3, use_container_width=True)
        with col2:
            if "Shipping Mode" in filtered.columns:
                mode_risk = filtered.groupby("Shipping Mode")["Predicted_Risk"].apply(
                    lambda s: (s == "High Risk").mean() * 100
                ).sort_values(ascending=False).reset_index(name="High_Risk_Pct")
                fig4 = px.bar(mode_risk, x="Shipping Mode", y="High_Risk_Pct",
                              title="High-Risk Rate by Shipping Mode (%)")
                st.plotly_chart(fig4, use_container_width=True)

        st.subheader("Top drivers of delivery risk (model feature importance)")
        top_features = pd.Series(metrics["top_features"]).sort_values(ascending=True)
        fig5 = px.bar(top_features, orientation="h", title="Feature Importance (Top 10)")
        fig5.update_layout(showlegend=False, yaxis_title="", xaxis_title="Importance")
        st.plotly_chart(fig5, use_container_width=True)

    with tab3:
        st.subheader("🤖 Ask the Delivery Risk Assistant")
        st.caption(
            "Powered by the Anthropic API (Claude). Answers are grounded in the current "
            "filtered view and the trained model's metrics -- try asking about high-risk "
            "regions, what drives risk, or what action to take for a shipment."
        )

        if not os.environ.get("ANTHROPIC_API_KEY"):
            st.warning(
                "No ANTHROPIC_API_KEY found. Add it to a local `.env` file "
                "(see `.env.example`) or to Streamlit Cloud secrets to enable the agent."
            )
        else:
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            prompt = st.chat_input("e.g. Which region has the highest delivery risk right now?")
            if prompt:
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            from agent import chat as agent_chat
                            api_history = [
                                {"role": m["role"], "content": m["content"]}
                                for m in st.session_state.chat_history[:-1]
                            ]
                            reply = agent_chat(prompt, metrics, filtered, history=api_history)
                        except Exception as exc:
                            reply = f"⚠️ Agent error: {exc}"
                        st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

            with st.expander("💡 Try asking..."):
                st.markdown(
                    "- Which region has the highest delivery risk right now?\n"
                    "- What are the top 3 drivers of delivery risk?\n"
                    "- Should we expedite orders shipped Standard Class this month?\n"
                    "- Compare model performance across the four algorithms we tested."
                )


if __name__ == "__main__":
    main()