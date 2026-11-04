# SoleScout — Project Status

> Generated: 2026-11-03 | FDS Stage 10: Final Polish Complete

---

## ✅ What Works

### Data Pipeline

| Component | Status | Notes |
|-----------|--------|-------|
| SoleScout API client | ✅ Working | `services/solescout_api.py` — credentials masked in logs |
| Raw data collector | ✅ Working | Saves timestamped JSON to `data/raw/` |
| Multi-brand collection | ✅ Working | Comma-separated `--query` in CLI |
| Multi-page support | ✅ Working | `--pages N` flag |
| Stage 4 cleaning pipeline | ✅ Working | Validation, dedup, brand normalisation, outlier flagging |
| Data Quality Report (JSON) | ✅ Working | `data/cleaned/data_quality_report_latest.json` |
| CSV export (raw + cleaned) | ✅ Working | Download via `/api/download/raw-csv` and `/api/download/cleaned-csv` |
| SQLite ingestion | ✅ Working | `UNIQUE(product_id, collection_date)` enforced |
| Historical snapshots preserved | ✅ Working | Duplicates silently ignored on re-insert |
| Demo data seeding | ✅ Working | 8 products × 4 brands × 4 dates = 32 snapshots |

### Backend API

| Endpoint | Status |
|----------|--------|
| `GET /api/health` | ✅ |
| `GET /api/products` (paginated, search, brand filter) | ✅ |
| `GET /api/products/{id}` | ✅ |
| `GET /api/brands` | ✅ |
| `GET /api/dashboard` | ✅ |
| `GET /api/price-history/{id}` | ✅ |
| `GET /api/analytics/brands` | ✅ |
| `GET /api/analytics/price-trends` | ✅ |
| `GET /api/statistics/anova` | ✅ |
| `GET /api/statistics/correlation` | ✅ |
| `GET /api/data-quality` | ✅ |
| `GET /api/download/raw-csv` | ✅ |
| `GET /api/download/cleaned-csv` | ✅ |
| `POST /api/collector/run` | ✅ |
| `POST /api/demo/seed` | ✅ |
| `POST /api/demo/clear` | ✅ |
| CORS configured for React dev server | ✅ |

### Statistical Analysis (SciPy)

| Test | Status | Result (demo data) |
|------|--------|--------------------|
| Descriptive stats (count, mean, median, std, Q1/Q3, IQR) | ✅ | Computed correctly |
| Price distribution histogram | ✅ | 8-bin histogram |
| Brand-wise price analysis | ✅ | Per-brand mean/median/IQR/std |
| **H1 — One-Way ANOVA** (brand vs price) | ✅ | p=1.4e-05 → **Reject H0** |
| **H2 — OLS Regression** (price vs date) | ✅ | Fail to reject H0 (stable trend) |
| **H3 — Pearson Correlation** (price vs rating) | ✅ | "Insufficient data" — honest, correct |
| Non-dogmatic language enforced | ✅ | Never says "H0 proven true" |
| Outliers flagged (Tukey IQR) | ✅ | `is_outlier=True`, not removed |

### Frontend

| Page | Status |
|------|--------|
| Dashboard (KPI cards, charts) | ✅ |
| Products (search, brand filter, grid/table, pagination) | ✅ |
| Product Details | ✅ |
| Compare (up to 4 products, bar charts) | ✅ |
| Price Trends (line chart, regression) | ✅ |
| Brand Analytics (bar/table) | ✅ |
| Statistical Analysis (ANOVA, Correlation, charts) | ✅ |
| Data Quality (ETL pipeline diagram, 8 KPIs, removed records table) | ✅ |
| About | ✅ |
| Sidebar navigation | ✅ |
| Demo mode toggle | ✅ |
| Loading states | ✅ |
| Error states with Retry | ✅ |
| Empty state (no data) | ✅ |
| TypeScript: 0 compile errors | ✅ |
| Vite build: ✓ 642 modules | ✅ |

### Security & Integrity

| Check | Status |
|-------|--------|
| `.env` in `.gitignore` | ✅ |
| API key never in frontend code | ✅ |
| API key never in logs or CSV exports | ✅ |
| No fake production data (demo labelled `is_demo=1`) | ✅ |
| Raw CSV export strips credential columns | ✅ |

### Tests

| Suite | Status |
|-------|--------|
| Unit tests (44 total) | ✅ All pass |
| Backend smoke test (15 checks) | ✅ All pass |

---

## ⚠️ Known Limitations

1. **Real SoleScout API requires an API key** — Demo data is available without a key via "Seed Demo Data" button or `POST /api/demo/seed`.

2. **Single-day dataset** — The collected data spans 1 day (2026-11-03), so H2 (price trend over time) cannot reject H0. Collecting data over multiple days will make trend analysis more meaningful.

3. **H3 (price vs rating) always returns "insufficient data"** — The SoleScout API does not return product ratings. This is correct behaviour per the project specification. Do not invent ratings.

4. **Vite dev server requires backend running** — The React app at `localhost:5173` proxies `/api` to `127.0.0.1:8000`. Both must be running simultaneously.

5. **Frontend build warning: chunk > 500 kB** — Recharts + React are bundled together. This is a performance note only, not an error. For production, add `manualChunks` to `vite.config.ts`.

6. **No authentication on the API** — This is a college demo project; the API is not production-hardened. Do not deploy publicly without adding auth middleware.

7. **Windows-only virtual environment scripts shown** — Use `venv/bin/activate` on Linux/macOS.

---

## 🚀 How to Start the Backend

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\backend"
..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- API base: `http://127.0.0.1:8000/api`
- Swagger UI: `http://127.0.0.1:8000/docs`
- HTML dashboard: `http://127.0.0.1:8000/app`

---

## 🎨 How to Start the Frontend

Open a second terminal:

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\frontend"
npm run dev
```

React app: `http://localhost:5173`

---

## 📦 How to Collect Data

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds"

# Requires SOLESCOUT_API_KEY in .env
.\venv\Scripts\python.exe scripts\collect_sneakers.py --query "Jordan 1" --limit 5 --pages 1
.\venv\Scripts\python.exe scripts\collect_sneakers.py --query "Nike" --limit 10 --pages 2
.\venv\Scripts\python.exe scripts\collect_sneakers.py --query "Adidas" --limit 10 --pages 2

# OR seed demo data (no API key needed):
.\venv\Scripts\python.exe -c "
import sys; sys.path.insert(0, 'backend')
from services.collector import seed_demo_data; print(seed_demo_data())
"
```

---

## 🧹 How to Clean Data

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds"
.\venv\Scripts\python.exe scripts\clean_data.py
```

Outputs:
- `data/cleaned/sneakers_cleaned_latest.csv`
- `data/cleaned/data_quality_report_latest.json`
- Records inserted into `data/solescout.db`

---

## 📈 How to Run Analysis

```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds"
.\venv\Scripts\python.exe scripts\run_analysis.py
```

Or access via the web dashboard: `http://localhost:5173` → Statistical Analysis.

Or call the API directly:
```powershell
# ANOVA
Invoke-WebRequest "http://127.0.0.1:8000/api/statistics/anova?alpha=0.05" | ConvertFrom-Json

# Correlation
Invoke-WebRequest "http://127.0.0.1:8000/api/statistics/correlation?alpha=0.05" | ConvertFrom-Json
```

---

## 🗄️ Database Location

```
C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\data\solescout.db
```

**Tables:**
- `sneakers` — product catalogue (SKU, name, brand, retail price, image)
- `price_history` — price snapshots with `UNIQUE(product_id, collection_date)`

**View with SQLite browser** or:
```powershell
Set-Location "C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\backend"
..\venv\Scripts\python.exe -c "
import sys; sys.path.insert(0, '.')
from database import get_connection
conn = get_connection()
print(conn.execute('SELECT COUNT(*) FROM sneakers').fetchone())
print(conn.execute('SELECT COUNT(*) FROM price_history').fetchone())
conn.close()
"
```

---

## 🔑 API Configuration

File: `C:\Users\USER\.gemini\antigravity\scratch\sole_scout_fds\.env`

```env
SOLESCOUT_API_KEY=your_actual_key_here
SOLESCOUT_BASE_URL=https://solescout.ai
APP_ENV=development
LOG_LEVEL=INFO
```

- Get a key at: [https://solescout.ai/for-ai](https://solescout.ai/for-ai)
- The `.env` file is excluded from git via `.gitignore`
- The key is **never** sent to the frontend or stored in any collected data files

---

## 🔭 Future Improvements

1. **Multi-day data collection schedule** — Use Windows Task Scheduler or `cron` to run the collector daily so price trend analysis (H2) becomes statistically meaningful.

2. **Product rating data source** — Find an alternative data source with verified ratings to enable Hypothesis 3 (H3: price vs rating Pearson correlation).

3. **Code splitting in Vite** — Split Recharts into a separate chunk to reduce the initial JS bundle from 685 kB to under 500 kB.

4. **Authentication middleware** — Add JWT or API-key auth to the FastAPI backend before any public deployment.

5. **Docker Compose** — Package backend + SQLite into a container for easier deployment.

6. **More brands and categories** — Expand data collection to cover women's, kids', and lifestyle categories.

7. **Price prediction model** — Add a simple linear regression price predictor using `scikit-learn`.

8. **Email/Slack alerts** — Alert when a tracked sneaker drops below a target price threshold.
