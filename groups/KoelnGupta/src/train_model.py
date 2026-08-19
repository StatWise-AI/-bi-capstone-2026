"""
train_model.py
---------------
Trains and compares four classification models (Logistic Regression,
Decision Tree, Random Forest, XGBoost) to predict Delivery_Risk_Category
(High / Medium / Low), exactly following the methodology used in the
Winter 2025 Stock Dynamics & Trends Analysis project (EDA -> feature
engineering -> preprocessing -> model training -> evaluation).

Outputs (all written automatically -- students do not need to write or
edit any of this):
    models/best_model.pkl          serialized best model (joblib)
    models/preprocessor.pkl        label encoders + scaler + feature list
    outputs/model_comparison.png
    outputs/confusion_matrix.png
    outputs/feature_importance.png
    outputs/metrics_summary.json
    outputs/Final_Predictions.xlsx

Run:
    python src/train_model.py
"""
from __future__ import annotations

import json
import os
import time

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, classification_report,
                              confusion_matrix, f1_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from data_preprocessing import PROCESSED_PATH, run_pipeline

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
TARGET = "Delivery_Risk_Category"
RANDOM_STATE = 42


def load_data() -> pd.DataFrame:
    if os.path.exists(PROCESSED_PATH):
        df = pd.read_csv(PROCESSED_PATH)
    else:
        df = run_pipeline(save=True)
    return df


def encode_features(df: pd.DataFrame):
    """Label-encode categorical columns, scale numeric columns for Logistic
    Regression. Returns X, y, and the fitted preprocessing artifacts so the
    Streamlit app can apply the exact same transforms to new data."""
    df = df.copy()
    y_raw = df.pop(TARGET)

    label_encoders: dict[str, LabelEncoder] = {}
    categorical_cols = df.select_dtypes(include=["object", "str"]).columns.tolist()
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le

    target_encoder = LabelEncoder()
    y = target_encoder.fit_transform(y_raw)

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(df), columns=df.columns, index=df.index)

    artifacts = {
        "label_encoders": label_encoders,
        "target_encoder": target_encoder,
        "scaler": scaler,
        "feature_columns": df.columns.tolist(),
        "categorical_cols": categorical_cols,
    }
    return df, X_scaled, y, artifacts


def train_all_models(X_raw, X_scaled, y):
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )
    X_train_scaled, X_test_scaled, _, _ = train_test_split(
        X_scaled, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )

    models = {
        "Logistic Regression": (LogisticRegression(max_iter=1000), True),
        "Decision Tree": (DecisionTreeClassifier(max_depth=12, random_state=RANDOM_STATE), False),
        "Random Forest": (RandomForestClassifier(n_estimators=200, max_depth=16, n_jobs=-1, random_state=RANDOM_STATE), False),
        "XGBoost": (XGBClassifier(n_estimators=300, max_depth=8, learning_rate=0.1,
                                   eval_metric="mlogloss", n_jobs=-1, random_state=RANDOM_STATE), False),
    }

    results = {}
    trained = {}
    for name, (model, needs_scaling) in models.items():
        t0 = time.time()
        Xtr = X_train_scaled if needs_scaling else X_train_raw
        Xte = X_test_scaled if needs_scaling else X_test_raw
        model.fit(Xtr, y_train)
        preds = model.predict(Xte)
        f1 = f1_score(y_test, preds, average="weighted")
        results[name] = {
            "f1_weighted": float(f1),
            "report": classification_report(y_test, preds, output_dict=True),
            "train_seconds": round(time.time() - t0, 1),
        }
        trained[name] = (model, needs_scaling, preds)
        print(f"[{name}] F1(weighted)={f1:.4f}  ({results[name]['train_seconds']}s)")

    best_name = max(results, key=lambda k: results[k]["f1_weighted"])
    return best_name, results, trained, (X_test_raw, X_test_scaled, y_test)


def plot_model_comparison(results: dict, path: str):
    names = list(results.keys())
    scores = [results[n]["f1_weighted"] for n in names]
    order = np.argsort(scores)[::-1]
    names = [names[i] for i in order]
    scores = [scores[i] for i in order]

    plt.figure(figsize=(7, 5))
    plt.bar(names, scores, color="#2563eb")
    plt.title("Model Performance Comparison")
    plt.ylabel("F1 Score (weighted)")
    plt.xticks(rotation=20)
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_confusion_matrix(y_test, preds, target_encoder, path: str):
    labels = target_encoder.classes_
    cm = confusion_matrix(y_test, preds)
    plt.figure(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap="rocket_r" if False else "Blues", values_format="d")
    plt.title("Confusion Matrix - Best Model")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_feature_importance(model, feature_names, path: str, top_n: int = 12):
    if not hasattr(model, "feature_importances_"):
        return
    importances = pd.Series(model.feature_importances_, index=feature_names)
    importances = importances.sort_values(ascending=True).tail(top_n)
    plt.figure(figsize=(7, 6))
    importances.plot(kind="barh", color="#2563eb")
    plt.title("Top Features Influencing Delivery Risk")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return importances.sort_values(ascending=False)


def build_predictions_workbook(df_original, X_test_raw, y_test, preds, target_encoder, path: str):
    action_map = {
        "High Risk": "Expedite shipment / notify customer proactively",
        "Medium Risk": "Monitor closely / consider upgraded shipping mode",
        "Low Risk": "Standard processing",
    }
    out = X_test_raw.copy()
    out["Actual_Risk"] = target_encoder.inverse_transform(y_test)
    out["Predicted_Risk"] = target_encoder.inverse_transform(preds)
    out["Correct_Prediction"] = out["Actual_Risk"] == out["Predicted_Risk"]
    out["Recommended_Action"] = out["Predicted_Risk"].map(action_map)
    out = out.reset_index(drop=True)
    out.head(2000).to_excel(path, index=False, sheet_name="Predictions")
    print(f"Saved predictions workbook: {path} ({min(len(out), 2000)} rows written)")


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    df = load_data()
    print(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns")

    X_raw, X_scaled, y, artifacts = encode_features(df)
    best_name, results, trained, (X_test_raw, X_test_scaled, y_test) = train_all_models(X_raw, X_scaled, y)

    best_model, needs_scaling, best_preds = trained[best_name]
    print(f"\nBest model: {best_name}  (F1={results[best_name]['f1_weighted']:.4f})")

    plot_model_comparison(results, os.path.join(OUTPUTS_DIR, "model_comparison.png"))
    plot_confusion_matrix(y_test, best_preds, artifacts["target_encoder"],
                           os.path.join(OUTPUTS_DIR, "confusion_matrix.png"))
    importances = plot_feature_importance(
        best_model, artifacts["feature_columns"],
        os.path.join(OUTPUTS_DIR, "feature_importance.png")
    )

    X_test_for_report = X_test_scaled if needs_scaling else X_test_raw
    build_predictions_workbook(
        df, X_test_raw.loc[X_test_for_report.index], y_test, best_preds,
        artifacts["target_encoder"], os.path.join(OUTPUTS_DIR, "Final_Predictions.xlsx")
    )

    joblib.dump(
        {"model": best_model, "model_name": best_name, "needs_scaling": needs_scaling},
        os.path.join(MODELS_DIR, "best_model.pkl"),
    )
    joblib.dump(artifacts, os.path.join(MODELS_DIR, "preprocessor.pkl"))

    summary = {
        "best_model": best_name,
        "all_results": {k: {"f1_weighted": v["f1_weighted"], "train_seconds": v["train_seconds"]}
                         for k, v in results.items()},
        "top_features": importances.head(10).to_dict() if importances is not None else {},
        "n_rows": int(df.shape[0]),
        "n_features": int(X_raw.shape[1]),
        "class_distribution": df[TARGET].value_counts(normalize=True).round(4).to_dict(),
    }
    with open(os.path.join(OUTPUTS_DIR, "metrics_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\nDone. Artifacts saved to models/ and outputs/.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
