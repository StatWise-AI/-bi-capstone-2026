"""
agent.py
--------
The AI Agent companion for the Delivery Risk Dashboard.

This agent is grounded in the ACTUAL model outputs and dataset statistics
(computed each run from outputs/metrics_summary.json and the scored
predictions) -- it is not a generic chatbot. It uses the Anthropic API with
a system prompt that injects live business context, so answers reference
real numbers from this project.

Students: you do not need to touch the model-calling logic. Your job is to
(1) put your ANTHROPIC_API_KEY in a .env file (see .env.example) or
Streamlit secrets, and (2) extend the SYSTEM_PROMPT / add new "tools"
(quick-answer functions) if your dashboard grows new KPIs.
"""
import json
import os

import anthropic
import pandas as pd

MODEL_NAME = "claude-sonnet-5"  # see https://docs.claude.com/en/docs/about-claude/models -- update if Anthropic ships a newer default


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found. Add it to a .env file (see .env.example) "
            "or to Streamlit secrets (Settings -> Secrets) before using the AI agent."
        )
    return anthropic.Anthropic(api_key=api_key)


def build_context(metrics_summary: dict, scored_df: pd.DataFrame) -> str:
    """Summarize live data into compact facts the model can ground answers in."""
    risk_counts = scored_df["Predicted_Risk"].value_counts().to_dict()
    total = len(scored_df)

    by_region = {}
    if "Order Region" in scored_df.columns:
        by_region = (
            scored_df.groupby("Order Region")["Predicted_Risk"]
            .apply(lambda s: (s == "High Risk").mean())
            .sort_values(ascending=False)
            .head(5)
            .round(3)
            .to_dict()
        )

    by_shipping_mode = {}
    if "Shipping Mode" in scored_df.columns:
        by_shipping_mode = (
            scored_df.groupby("Shipping Mode")["Predicted_Risk"]
            .apply(lambda s: (s == "High Risk").mean())
            .round(3)
            .to_dict()
        )

    context = {
        "best_model": metrics_summary.get("best_model"),
        "model_f1_scores": metrics_summary.get("all_results"),
        "top_risk_drivers": metrics_summary.get("top_features"),
        "dataset_size": metrics_summary.get("n_rows"),
        "current_view_row_count": total,
        "current_view_risk_distribution": risk_counts,
        "high_risk_rate_by_region_top5": by_region,
        "high_risk_rate_by_shipping_mode": by_shipping_mode,
    }
    return json.dumps(context, indent=2, default=str)


SYSTEM_PROMPT_TEMPLATE = """You are the Delivery Risk Assistant embedded in a supply-chain \
business intelligence dashboard for a distribution company. The dashboard predicts each \
order's delivery risk (High / Medium / Low) using a trained {model_name} classification model.

Ground every answer in the LIVE DATA CONTEXT below -- these are real numbers computed from \
the current dashboard view, not estimates. When asked for a number, quote it from the context. \
When asked for a recommendation, tie it to the specific risk drivers and action rules:
  - High Risk   -> Expedite shipment / notify customer proactively
  - Medium Risk -> Monitor closely / consider upgraded shipping mode
  - Low Risk    -> Standard processing

Be concise and business-focused (managers, not data scientists, are your audience). Use plain \
language, short paragraphs or bullet points, and always translate model output into an \
operational recommendation.

LIVE DATA CONTEXT:
{context}
"""


def chat(user_message: str, metrics_summary: dict, scored_df: pd.DataFrame,
          history: list[dict] | None = None) -> str:
    client = get_client()
    context = build_context(metrics_summary, scored_df)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        model_name=metrics_summary.get("best_model", "the trained model"),
        context=context,
    )

    messages = (history or []) + [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=800,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text
