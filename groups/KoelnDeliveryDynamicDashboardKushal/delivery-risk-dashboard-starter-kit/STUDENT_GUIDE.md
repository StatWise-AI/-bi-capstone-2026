# Student Guide: Delivery Risk Dashboard & AI Agent

Welcome! This project already includes a **fully working, tested machine learning
pipeline and a working AI-agent dashboard**. You do not need to write, fix, or
debug any machine learning code. Your work is: run the pipeline, understand what
it did, then focus your effort on **dashboard design, business storytelling, a
Power BI companion, and pushing a clean project to GitHub**.

Follow the steps in order. Each step tells you exactly what to run and what you
should see.

---

## Step 0 — Prerequisites

- Python 3.10 or later installed (`python --version` or `python3 --version`)
- Git installed
- A GitHub account, and the empty repository URL your professor gave you
- (Optional but recommended) An Anthropic API key for the AI agent —
  get one free at https://console.anthropic.com/settings/keys
- Power BI Desktop (Windows) if your course requires a Power BI dashboard

---

## Step 1 — Get the project onto your machine

Your professor will give you a link to an **empty GitHub repository** you own.
Two ways to get this starter project into it:

**Option A — you received a zip/folder of this project:**
```bash
cd path/to/this/project
git init
git remote add origin <the-repo-url-your-professor-gave-you>
git add .
git commit -m "Initial commit: project starter kit"
git branch -M main
git push -u origin main
```

**Option B — you received a GitHub repo link directly (already has this code):**
```bash
git clone <the-repo-url>
cd <the-repo-folder>
```

---

## Step 2 — Set up your Python environment

```bash
python -m venv .venv

# Activate it:
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows (PowerShell/CMD)

pip install -r requirements.txt
```

This installs pandas, scikit-learn, xgboost, streamlit, plotly, and the Anthropic
SDK — everything the pipeline and app need.

---

## Step 3 — Download the real-world dataset

```bash
python src/download_data.py
```

This pulls the **DataCo Smart Supply Chain dataset** (180,519 real orders, ~95MB)
from its public source into `data/raw/`. It is *not* committed to git (too large,
and it's good practice to never commit large raw data) — that's why every teammate
runs this script once locally.

> If your network blocks the download, don't worry: every script automatically
> falls back to the 5,000-row sample already committed at
> `data/sample/DataCoSupplyChain_sample.csv`, so you can keep working.

---

## Step 4 — Run the ML pipeline (already written for you)

```bash
python src/data_preprocessing.py
python src/train_model.py
```

What happens:
1. `data_preprocessing.py` cleans the raw data, removes personally identifiable
   information (PII) and any column that would leak the answer, and engineers
   business features (order month, scheduled shipping days, order value, etc.).
   It saves `data/processed/model_ready_data.csv`.
2. `train_model.py` trains **four** classification models (Logistic Regression,
   Decision Tree, Random Forest, XGBoost), compares them with weighted F1 score,
   and automatically keeps the best one. It saves:
   - `models/best_model.pkl` and `models/preprocessor.pkl` (used by the app)
   - `outputs/model_comparison.png`, `outputs/confusion_matrix.png`,
     `outputs/feature_importance.png`
   - `outputs/metrics_summary.json`
   - `outputs/Final_Predictions.xlsx` — feed this into Power BI (Step 8)

This takes roughly 1–2 minutes on the full dataset. You'll see each model's F1
score printed as it trains.

**Check your results:**
```bash
python src/evaluate_model.py
```
This prints a clean summary: best model, all four F1 scores, class distribution,
and the top features driving delivery risk. Take a screenshot of this for your
report.

---

## Step 5 — Get your Anthropic API key ready

```bash
cp .env.example .env
```
Open `.env` and paste your key:
```
ANTHROPIC_API_KEY=sk-ant-your-real-key-here
```
Never commit `.env` — it's already in `.gitignore`.

---

## Step 6 — Run the dashboard locally

```bash
streamlit run app/streamlit_app.py
```

Your browser opens automatically (usually `http://localhost:8501`). You should
see:
- KPI cards (orders in view, high-risk %, prediction accuracy, model F1)
- An **Overview** tab with risk distribution and monthly trend charts
- A **Regional & Shipping** tab breaking down risk by region and shipping mode
- An **AI Agent** tab — a chat interface grounded in the live filtered data.
  Try asking: *"Which region has the highest delivery risk right now?"*

If something looks broken here, it's almost always the `.env` key (Step 5) or a
missing `pip install` (re-run Step 2) — not the ML code.

---

## Step 7 — Now make it yours (this is the actual assignment)

You are **not** expected to touch:
- `src/data_preprocessing.py`
- `src/train_model.py`
- `src/predict.py`
- The core scoring logic in `app/agent.py`

You **are** expected to work on:

1. **Dashboard design** (`app/streamlit_app.py`)
   - Restyle KPI cards, rearrange tabs, add filters relevant to your narrative
     (e.g. filter by Customer Segment, by high-value orders only)
   - Add at least one new chart answering a business question your team chose
   - Improve copy/titles so a non-technical manager understands each chart
     without needing you in the room

2. **Business storytelling** (`docs/PROJECT_BRIEF.md`)
   - Fill in Sections 7–9 (Business Impact, Conclusion, Future Work) with your
     own analysis based on what the dashboard actually shows
   - Add screenshots of your finished dashboard

3. **AI Agent extension** (optional, `app/agent.py`)
   - Add new facts to `build_context()` if you added new KPIs
   - Adjust `SYSTEM_PROMPT_TEMPLATE` if you want a different tone or focus

4. **Power BI companion** — see Step 8 below.

---

## Step 8 — Build the Power BI dashboard

Full instructions with ready-to-paste DAX measures: **[`powerbi/POWERBI_GUIDE.md`](powerbi/POWERBI_GUIDE.md)**.

Short version: open Power BI Desktop → Get Data → Excel →
`outputs/Final_Predictions.xlsx` → build KPI cards and charts using the DAX
measures provided in the guide.

---

## Step 9 — Push your work to GitHub

```bash
git add .
git commit -m "Add dashboard customization, Power BI report, and business narrative"
git push
```

Do this regularly (after each meaningful change), not just once at the end —
your commit history is part of what's being assessed.

**Never commit:**
- `.env` (already gitignored)
- `data/raw/*.csv` or `data/processed/*.csv` (already gitignored — large files)
- Anything with your API key in it

---

## Step 10 — Deploy to Streamlit Community Cloud

1. Push your repo to GitHub (Step 9) if you haven't already.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. **New app** → select your repository, branch `main`, main file path
   `app/streamlit_app.py`.
4. Before deploying, click **Advanced settings → Secrets** and add:
   ```
   ANTHROPIC_API_KEY = "sk-ant-your-real-key-here"
   ```
   (This is the cloud equivalent of your local `.env` file — the app already
   knows to read from `st.secrets` when deployed.)
5. **Deploy.** First build takes a few minutes (installing dependencies).

> Streamlit Cloud does **not** have your `data/raw/` or `models/` folders unless
> you commit them or the app generates them at startup. The simplest reliable
> option for a class deployment: commit `models/best_model.pkl`,
> `models/preprocessor.pkl`, and `data/processed/model_ready_data.csv` to the
> repo (remove them from `.gitignore` if you do this) so the deployed app has
> everything it needs without re-running training in the cloud. Discuss with
> your team which approach you prefer and note your choice in
> `docs/PROJECT_BRIEF.md`.

---

## Step 11 — Final submission checklist

- [ ] GitHub repo pushed, with a clean commit history
- [ ] `README.md` updated with your team names and a live Streamlit app link
- [ ] `docs/PROJECT_BRIEF.md` Sections 7–9 completed with your own analysis
- [ ] Dashboard screenshots included somewhere in your report
- [ ] Power BI file (`.pbix`) added to the repo or submitted separately per your
      course's instructions
- [ ] AI agent tested with at least 3 different questions, with screenshots
- [ ] CI badge/workflow passing (check the **Actions** tab on GitHub)
- [ ] `.env` and raw data **not** committed (double-check `git status`)

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError` | Virtual env not active or deps not installed | Re-run Step 2 |
| Download script fails | Network/firewall blocks GitHub raw content | Pipeline auto-falls back to the sample dataset — keep working |
| AI Agent tab shows a warning | No `ANTHROPIC_API_KEY` set | Re-check Step 5 (local) or Streamlit secrets (Step 10) |
| `FileNotFoundError: models/best_model.pkl` | You haven't run training yet | Run Step 4 |
| Streamlit Cloud app crashes on boot | `models/`, `data/processed/` not in the repo | See the note at the end of Step 10 |
| Charts look empty after filtering | Your filter combination has zero matching rows | Try "All" on one filter at a time |

Questions specific to your project's business logic (not the ML pipeline) should
go to your team first, then your professor — the pipeline itself has been tested
end-to-end and should just work.
