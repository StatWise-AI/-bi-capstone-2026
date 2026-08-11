# AI-Enabled Uber India Operations Analytics Dashboard

A locally-run, Flask-based Business Intelligence dashboard analyzing Uber India ride-hailing operations — Executive Overview, Vehicle, Revenue, Rider, and Location analytics, plus an AI Assistant page (interface built; Gemini API integration arrives in a later phase).

This app runs entirely on your own machine. No data leaves your computer, and no dataset is bundled with this package — you supply your own `uber.xlsx`.

---

## Quick Start (Windows)

1. Extract this ZIP anywhere on your computer.
2. Place your `uber.xlsx` dataset into the `data/raw/` folder (see below for the exact requirement).
3. Double-click **`run.bat`**.
4. Your browser will open automatically to the dashboard.

That's it. `run.bat` handles creating a virtual environment, installing dependencies, and starting the app for you.

---

## Where to put the dataset

Copy your Excel file to exactly this path inside the extracted project:

```
data/raw/uber.xlsx
```

The file must contain three sheets, matching the dataset used throughout this project's development:

| Sheet name | Contents |
|---|---|
| `Sheet1` | The main booking records (150,000 rows) |
| `Veh_IMG` | Vehicle Type → icon URL lookup |
| `Sheet3` | Booking Status → icon URL lookup |

**If you forget this step, the app will not crash.** It will start normally and show a clear on-screen setup page in your browser with these same instructions, telling you exactly where to place the file. Once the file is there, just restart the app (re-run `run.bat`).

---

## Folder Structure

![Folder structure](docs/folder_structure.png)

```
uber_executive_dashboard/
├── app.py
├── config.py
├── requirements.txt
├── run.bat
├── README.md
│
├── backend/
│   ├── data_loader.py       # Cleans the raw dataset (Power Query-equivalent logic)
│   ├── data_cache.py        # Loads data once at startup, caches in memory
│   ├── measures.py          # Every KPI/measure, as Python functions
│   ├── models.py            # Table schema documentation
│   ├── chart_builder.py     # Builds Plotly chart specs from real data
│   ├── view_helpers.py      # Query-string filter URL helpers
│   ├── json_utils.py        # JSON serialization helpers
│   └── routes/              # One Flask blueprint per page
│
├── templates/                # Jinja2 HTML templates (one per page + shared partials)
├── static/
│   ├── css/                  # Dashboard theme (light, black/white/grey - matches Power BI reference)
│   ├── js/                   # Navigation + AI chat interactivity
│   └── assets/                # Icons / images
│
└── data/
    ├── raw/                   # <-- place uber.xlsx HERE
    └── processed/              # Auto-generated cache (safe to delete anytime)
```

---

## Manual setup (if you prefer not to use run.bat)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python app.py
```

Requires Python 3.10 or later.

---

## What's implemented so far

| Page | Status |
|---|---|
| Home | Landing page with navigation tiles |
| Executive Overview | KPI cards, booking/revenue trend charts, revenue-by-vehicle chart, top locations, ratings |
| Vehicle Analytics | Full detail table with per-vehicle metrics and trend sparklines |
| Revenue Analytics | Revenue trend, revenue by vehicle/payment method/customer |
| Rider Analytics | Cancellation reasons, payment-method breakdown, rider segmentation, detail table |
| Location Analytics | Distance trends, busy areas, time-slot × weekday heatmap |
| AI Assistant | Full chat interface, connected to Google Gemini — answers questions, gives executive summaries, recommendations, risk analysis, and trend analysis, grounded entirely in your live dashboard data. Requires a one-time API key setup (see below) |

All charts are rendered with **Plotly**, using live data computed from your dataset — nothing is hardcoded or mocked.

Filtering (by vehicle type, date granularity, and cancellation-reason category) works via simple page reloads with query parameters — no JavaScript framework, no build step, by design (see the architecture notes in `backend/view_helpers.py` for why).

---

## Performance note

The **first** time you run the app (or any time after deleting `data/processed/`), it takes roughly 20–30 seconds to start, because it's reading and cleaning the full Excel dataset. Every run after that loads in under a second, because the cleaned data is cached in `data/processed/`. This is expected behavior, not a hang — the browser will open automatically once it's ready.

---

## Setting up the AI Assistant (Gemini)

The AI Assistant page works without any setup — it will tell you clearly if it isn't connected yet. To actually connect it to Google Gemini:

1. Get a free API key at **https://aistudio.google.com/apikey**
2. In the project root, copy `.env.example` to a new file named `.env`
3. Open `.env` and replace `your_gemini_api_key_here` with your real key:
   ```
   GEMINI_API_KEY=AIzaSy...your real key...
   ```
4. Restart the app (`run.bat`, or re-run `python app.py`).

That's it — no code changes needed. The `.env` file is never bundled, never committed, and never sent anywhere except read locally by this app.

**Important:** the AI Assistant only ever answers from the dashboard's own current data (revenue, bookings, cancellation reasons, ratings, etc.) — it's explicitly instructed not to use outside knowledge, and it will say so rather than guess if the data doesn't cover your question.

If something goes wrong (missing key, no internet, Gemini temporarily unavailable), the chat will show a clear, specific message explaining what happened — the rest of the dashboard keeps working regardless, since the AI feature is fully isolated from the core dashboard's data pipeline.

---

## Troubleshooting

**"Python was not found"** — Install Python 3.10+ from python.org, and make sure "Add Python to PATH" is checked during installation.

**Dashboard looks unstyled or shows old placeholder text** — Hard-refresh your browser (Ctrl+Shift+R) or try an incognito window. The app disables browser caching for its own files, but a stale tab from a previous run can still show old content until refreshed.

**"Dataset not found" page won't go away after adding the file** — Double check the file is named exactly `uber.xlsx` (not `uber.xlsx.xlsx` or `Uber.xlsx`), sits directly inside `data/raw/` (not a subfolder), and that you've restarted the app after placing it.
