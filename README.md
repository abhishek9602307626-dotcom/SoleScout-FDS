# SoleScout — Sneaker Price Intelligence & Analytics

> **Fundamentals of Data Science (FDS) College Project**
> Full-stack data science platform: API collection → cleaning → statistical analysis → FastAPI backend → React dashboard.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Directory Structure](#directory-structure)
4. [Prerequisites](#prerequisites)
5. [Setup (Windows PowerShell)](#setup-windows-powershell)
6. [Running the Backend](#running-the-backend)
7. [Running the Frontend](#running-the-frontend)
8. [Collecting Data](#collecting-data)
9. [Cleaning Data](#cleaning-data)
10. [Running Statistical Analysis](#running-statistical-analysis)
11. [API Endpoints Reference](#api-endpoints-reference)
12. [Data Integrity Rules](#data-integrity-rules)
13. [Testing](#testing)

---

## Project Overview

SoleScout collects real sneaker pricing data from the SoleScout REST API, cleans and normalises it through a reproducible ETL pipeline, stores it in SQLite, and serves statistical analysis (ANOVA, OLS regression, Pearson correlation) through a FastAPI backend to a React + Recharts analytics dashboard.

**FDS Pipeline:**
```
SoleScout API → Raw JSON → Validation → Cleaning → SQLite → SciPy Analysis → FastAPI → React
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Collection | Python + `requests` |
| Data Storage | SQLite (via Python `sqlite3`) |
| Data Cleaning | Pandas, NumPy |
| Statistical Analysis | SciPy (`f_oneway`, `linregress`, `pearsonr`) |
| Backend API | FastAPI + Pydantic + Uvicorn |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS v4 + Recharts |
| Environment | `python-dotenv` |

---

## Directory Structure

```
sole_scout_fds/
├── backend/
│   ├── main.py               # FastAPI entry point
│   ├── database.py           # SQLite connection & schema
│   ├── schemas.py            # Pydantic models
│   ├── api/
│   │   └── routes.py         # All API endpoints
│   ├── services/
│   │   ├── solescout_api.py  # SoleScout API client
│   │   ├── collector.py      # Stage 3: Data collection
│   │   ├── cleaning.py       # Stage 4: Data cleaning pipeline
│   │   └── analytics.py      # Stage 5: Statistical analysis
│   ├── static/
│   │   └── app.html          # Standalone HTML dashboard (no npm needed)
│   └── tests/                # 44 unit tests
├── frontend/
│   ├── src/
│   │   ├── pages/            # React page components
│   │   ├── components/       # Reusable UI components
│   │   ├── services/api.ts   # Backend API client
│   │   └── types/index.ts    # TypeScript definitions
│   ├── package.json
│   └── vite.config.ts        # Dev proxy → backend :8000
├── scripts/
│   ├── collect_sneakers.py   # CLI: collect data
│   ├── clean_data.py         # CLI: run cleaning pipeline
│   └── run_analysis.py       # CLI: run statistical analysis
├── data/
│   ├── raw/                  # Raw API JSON files
│   ├── cleaned/              # Cleaned CSVs + quality reports
│   └── solescout.db          # SQLite database
├── .env                      # API credentials (NEVER commit)
├── .env.example              # Template
├── .gitignore                # .env and db excluded
└── requirements.txt
```

---

## Prerequisites

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/) (for React frontend only)
- **Git** (optional)

Verify installations:
```powershell
python --version
node --version
npm --version
```

---

## Setup (Windows PowerShell)

### 1. Navigate to the project

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds"
```

### 2. Create and activate Python virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> If you see an execution policy error:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure the API key

```powershell
Copy-Item .env.example .env
notepad .env
```

Edit `.env`:
```env
SOLESCOUT_API_KEY=your_actual_api_key_here
SOLESCOUT_BASE_URL=https://solescout.ai
```

> Get your API key at [solescout.ai/for-ai](https://solescout.ai/for-ai)
> The key is only used by the Python backend — **never exposed to the frontend**.

### 5. Install frontend dependencies

```powershell
Set-Location frontend
npm install
Set-Location ..
```

### 6. Seed demo data (optional — works without API key)

```powershell
Set-Location backend
..\venv\Scripts\python.exe -c "
import sys; sys.path.insert(0, '.')
from services.collector import seed_demo_data
print(seed_demo_data())
"
Set-Location ..
```

---

## Running the Backend

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\backend"
..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The backend is now live at:
- **API:** `http://127.0.0.1:8000/api/`
- **Interactive Docs:** `http://127.0.0.1:8000/docs`
- **HTML Dashboard (no npm needed):** `http://127.0.0.1:8000/app`

---

## Running the Frontend

Open a **second** PowerShell terminal:

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\frontend"
npm run dev
```

React app is now at: **`http://localhost:5173`**

The Vite dev server proxies all `/api` requests to `http://127.0.0.1:8000` automatically.

### Build for production

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\frontend"
npm run build
```

Output goes to `frontend/dist/`.

---

## Collecting Data

### Collect a small test dataset (real API)

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds"
.\venv\Scripts\python.exe scripts\collect_sneakers.py --query "Jordan 1" --limit 5 --pages 1
```

### Collect multiple brands

```powershell
.\venv\Scripts\python.exe scripts\collect_sneakers.py --query "Jordan" --limit 10 --pages 2
.\venv\Scripts\python.exe scripts\collect_sneakers.py --query "Nike" --limit 10 --pages 2
.\venv\Scripts\python.exe scripts\collect_sneakers.py --query "Adidas" --limit 10 --pages 2
```

### Via the dashboard UI

Navigate to **Data Quality** → **Run Live Collector** button.

Raw JSON files are saved to `data/raw/` with timestamps. No API credentials are stored in the files.

---

## Cleaning Data

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds"
.\venv\Scripts\python.exe scripts\clean_data.py
```

This runs the Stage 4 pipeline:
1. Loads latest raw JSON from `data/raw/`
2. Validates product IDs, names, prices, timestamps
3. Standardises brand names
4. Removes duplicates on `UNIQUE(product_id, collection_date)`
5. Flags statistical outliers (Tukey IQR) — **does not remove them**
6. Exports `data/cleaned/sneakers_cleaned_latest.csv`
7. Generates `data/cleaned/data_quality_report_latest.json`
8. Ingests clean records into `data/solescout.db`

---

## Running Statistical Analysis

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds"
.\venv\Scripts\python.exe scripts\run_analysis.py
```

Outputs:
- **Descriptive statistics** (count, mean, median, std dev, quartiles)
- **Price distribution** histogram
- **Brand-wise analysis** (mean, median, IQR per brand)
- **Hypothesis 1 — One-Way ANOVA** (brand vs price, α = 0.05)
- **Hypothesis 2 — OLS Regression** (price vs collection date)
- **Hypothesis 3 — Pearson Correlation** (price vs rating, only if rating data exists)

---

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Backend + DB health check |
| GET | `/api/products` | Paginated catalog (search, brand filter) |
| GET | `/api/products/{id}` | Single product detail |
| GET | `/api/brands` | All brands with pricing summary |
| GET | `/api/dashboard` | Executive KPIs + chart data |
| GET | `/api/price-history/{id}` | Full price snapshot timeline |
| GET | `/api/analytics/brands` | Brand-wise descriptive statistics |
| GET | `/api/analytics/price-trends` | Daily trends + OLS regression |
| GET | `/api/statistics/anova` | H1: One-Way ANOVA |
| GET | `/api/statistics/correlation` | H2 & H3: Regression + Pearson |
| GET | `/api/data-quality` | ETL audit report + pipeline stages |
| GET | `/api/download/raw-csv` | Download raw data CSV |
| GET | `/api/download/cleaned-csv` | Download cleaned data CSV |
| POST | `/api/collector/run` | Trigger collection + cleaning pipeline |
| POST | `/api/demo/seed` | Seed demo/sample data |
| POST | `/api/demo/clear` | Clear demo data |

Full interactive docs: `http://127.0.0.1:8000/docs`

---

## Data Integrity Rules

These rules are enforced throughout the codebase:

1. **No invented data** — Missing API fields are stored as `NULL`; never fabricated.
2. **Historical snapshots preserved** — `UNIQUE(product_id, collection_date)` prevents overwrites.
3. **API key never exposed** — Loaded via `python-dotenv`; never in frontend code, logs, or CSV exports.
4. **Outliers flagged, not removed** — `is_outlier=True` column set; all records kept.
5. **Demo data labelled** — All seeded records have `is_demo=1`; togglable in the UI.
6. **Non-dogmatic statistics** — Code never states "H0 is proven true"; uses "Fail to reject H0".
7. **Reproducible pipeline** — Same raw input always produces the same cleaned output.

---

## Testing

### Run all 44 unit tests

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds"
.\venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Expected: `Ran 44 tests in ~3s — OK`

### Run the backend smoke test (15 integration checks)

```powershell
.\venv\Scripts\python.exe backend\tests\smoke_test.py
```

Expected: `ALL 15 CHECKS PASSED`

### Run the statistical analysis verification

```powershell
.\venv\Scripts\python.exe scripts\verify_statistical_analysis.py
```

### TypeScript type check (no build required)

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\frontend"
npx tsc --noEmit
```

Expected: No errors.
