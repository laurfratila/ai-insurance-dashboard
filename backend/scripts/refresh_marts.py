import os
from sqlalchemy import create_engine, text

DB = os.getenv("DATABASE_URL")
if not DB:
    raise SystemExit("DATABASE_URL is not set")

SQL = """
-- Rebuild core (idempotent) if you want this script to be the single entrypoint:
-- \\i /app/scripts/build_core.sql

-- Refresh marts (fast dashboards)
REFRESH MATERIALIZED VIEW marts.claims_by_month;
REFRESH MATERIALIZED VIEW marts.loss_ratio_by_month;
REFRESH MATERIALIZED VIEW marts.claims_by_county;
"""

def main():
    engine = create_engine(DB)
    with engine.begin() as conn:
        conn.execute(text(SQL))
    print("Refreshed marts ✅")

if __name__ == "__main__":
    main()
