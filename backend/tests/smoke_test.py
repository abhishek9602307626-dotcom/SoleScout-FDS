"""SoleScout final backend smoke test."""
import sys
import os

# Add backend directory to sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BACKEND_DIR)

from database import init_db, get_connection
from api.routes import (
    get_health, get_products, get_brands, get_dashboard,
    get_data_quality, get_statistics_anova, get_statistics_correlation,
    get_analytics_brands, get_analytics_price_trends,
    run_collector, get_collector_status,
    download_raw_csv, download_cleaned_csv,
)
from schemas import CollectorRunRequest

init_db()
results = []
errors = []

def check(label, fn):
    try:
        result = fn()
        results.append(f"  PASS  {label}")
        return result
    except Exception as e:
        errors.append(f"  FAIL  {label}: {e}")
        return None

print("=" * 60)
print("SOLESCOUT BACKEND SMOKE TEST")
print("=" * 60)

# 1. Health
h = check("Health endpoint", get_health)
if h:
    results[-1] += f" | status={h.status}, db={h.database}"

# 2. Products
p = check("Products paginated", lambda: get_products(page=1, limit=5, include_demo=True))
if p:
    results[-1] += f" | total={p.total}, returned={len(p.items)}"

# 3. Brands
b = check("Brands list", lambda: get_brands(include_demo=True))
if b:
    results[-1] += f" | brands={b.total_brands}"

# 4. Dashboard
d = check("Dashboard", lambda: get_dashboard(include_demo=True))
if d:
    results[-1] += f" | products={d.total_products}, snapshots={d.total_snapshots}, empty={d.is_empty}"

# 5. Data Quality
dq = check("Data Quality", lambda: get_data_quality())
if dq:
    results[-1] += f" | stages={len(dq.pipeline_stages)}, removed_records={len(dq.removed_records)}"

# 6. ANOVA
a = check("ANOVA H1", lambda: get_statistics_anova(alpha=0.05, include_demo=True))
if a:
    results[-1] += f" | p={a.p_value}, decision='{a.decision[:20]}'"

# 7. Correlation
c = check("Correlation H2+H3", lambda: get_statistics_correlation(alpha=0.05, include_demo=True))
if c:
    results[-1] += f" | H2={c.price_trend_hypothesis.decision[:15]}, H3={c.price_rating_hypothesis.status}"

# 8. Brand analytics
ba = check("Brand Analytics", lambda: get_analytics_brands(include_demo=True))
if ba:
    results[-1] += f" | brands_analyzed={ba.total_brands_analyzed}"

# 9. Price trends
pt = check("Price Trends", lambda: get_analytics_price_trends(include_demo=True))
if pt:
    results[-1] += f" | days={len(pt.daily_trends)}, direction={pt.direction}"

# 10. Collector status
cs = check("Collector Status", lambda: get_collector_status())
if cs:
    results[-1] += f" | api_configured={cs['api_key_configured']}"

# 11. Collector run (no API key)
cr = check("Collector Run (no key)", lambda: run_collector(CollectorRunRequest(demo=False)))
if cr:
    results[-1] += f" | status={cr.status}"

# 12. Download endpoints
check("Download Raw CSV", lambda: download_raw_csv())
check("Download Cleaned CSV", lambda: download_cleaned_csv())

# 13. DB integrity
def check_db():
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
        uniq = conn.execute(
            "SELECT COUNT(*) FROM (SELECT DISTINCT product_id, collection_date FROM price_history)"
        ).fetchone()[0]
        assert total == uniq, f"Duplicate snapshots found: {total} rows but {uniq} unique (pid,date) pairs"
        return {"total": total, "unique": uniq}
    finally:
        conn.close()

db_check = check("DB UNIQUE(product_id, date) constraint", check_db)
if db_check:
    results[-1] += f" | snapshots={db_check['total']}"

# 14. API key not in any response
def check_no_key_leak():
    import json
    api_key = os.getenv("SOLESCOUT_API_KEY", "")
    if not api_key or api_key in ("your_api_key_here", ""):
        return "No real key configured - nothing to leak"
    # Check that key doesn't appear in dashboard JSON
    d = get_dashboard(include_demo=True)
    import pydantic
    d_json = d.model_dump_json()
    assert api_key not in d_json, "API key found in dashboard response!"
    return "Key not in responses"

check("API key not in responses", check_no_key_leak)

print()
for r in results:
    print(r)
if errors:
    print()
    print("FAILURES:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print()
    print(f"ALL {len(results)} CHECKS PASSED")
