"""
evaluate_model.py
------------------
Standalone evaluation report for the saved best_model.pkl. Useful for
students to re-check performance without re-training, and used by the
Streamlit app to show live metrics on the dashboard.

Run:
    python src/evaluate_model.py
"""
import json
import os

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


def print_summary():
    summary_path = os.path.join(OUTPUTS_DIR, "metrics_summary.json")
    if not os.path.exists(summary_path):
        print("No metrics_summary.json found. Run `python src/train_model.py` first.")
        return
    with open(summary_path) as f:
        summary = json.load(f)

    print("=" * 60)
    print("MODEL EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Best model      : {summary['best_model']}")
    print(f"Rows used       : {summary['n_rows']:,}")
    print(f"Features used   : {summary['n_features']}")
    print("\nModel comparison (F1, weighted):")
    for name, res in summary["all_results"].items():
        print(f"  {name:<22} F1={res['f1_weighted']:.4f}   ({res['train_seconds']}s to train)")
    print("\nClass distribution (target):")
    for cls, pct in summary["class_distribution"].items():
        print(f"  {cls:<15} {pct*100:.1f}%")
    print("\nTop drivers of delivery risk:")
    for feat, imp in summary["top_features"].items():
        print(f"  {feat:<30} {imp:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    print_summary()
