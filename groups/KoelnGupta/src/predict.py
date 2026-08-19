"""
predict.py
----------
Loads the trained model + preprocessing artifacts and scores new order
records. Used by the Streamlit app (app/streamlit_app.py) so the dashboard
and the AI agent both call into the exact same scoring logic used during
training -- no duplicated preprocessing code.

Can also be run directly on the processed dataset to sanity check:
    python src/predict.py
"""
import os

import joblib
import pandas as pd

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

ACTION_MAP = {
    "High Risk": "Expedite shipment / notify customer proactively",
    "Medium Risk": "Monitor closely / consider upgraded shipping mode",
    "Low Risk": "Standard processing",
}


def load_artifacts():
    model_bundle = joblib.load(os.path.join(MODELS_DIR, "best_model.pkl"))
    preprocessor = joblib.load(os.path.join(MODELS_DIR, "preprocessor.pkl"))
    return model_bundle, preprocessor


def predict_dataframe(df: pd.DataFrame, model_bundle=None, preprocessor=None) -> pd.DataFrame:
    """Score a dataframe that has the SAME feature columns produced by
    src/data_preprocessing.py (i.e. already has Delivery_Risk_Category
    engineered/removed as needed). Returns the dataframe with two new
    columns: Predicted_Risk and Recommended_Action."""
    if model_bundle is None or preprocessor is None:
        model_bundle, preprocessor = load_artifacts()

    model = model_bundle["model"]
    needs_scaling = model_bundle["needs_scaling"]

    X = df.copy()
    for col in preprocessor["categorical_cols"]:
        le = preprocessor["label_encoders"][col]
        # unseen categories fall back to the most frequent known class
        known = set(le.classes_)
        X[col] = X[col].astype(str).apply(lambda v: v if v in known else le.classes_[0])
        X[col] = le.transform(X[col])

    X = X[preprocessor["feature_columns"]]

    if needs_scaling:
        X = pd.DataFrame(preprocessor["scaler"].transform(X), columns=X.columns, index=X.index)

    preds = model.predict(X)
    pred_labels = preprocessor["target_encoder"].inverse_transform(preds)

    out = df.copy()
    out["Predicted_Risk"] = pred_labels
    out["Recommended_Action"] = out["Predicted_Risk"].map(ACTION_MAP)
    return out


if __name__ == "__main__":
    processed_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "model_ready_data.csv")
    df = pd.read_csv(processed_path)
    sample = df.drop(columns=["Delivery_Risk_Category"]).sample(10, random_state=1)
    scored = predict_dataframe(sample)
    print(scored[["Predicted_Risk", "Recommended_Action"]])
