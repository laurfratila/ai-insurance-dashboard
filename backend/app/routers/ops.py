# backend/app/routers/ops.py
from fastapi import APIRouter
from datetime import date
from sqlalchemy import text
from app.db import engine
from app.models import TimeSeriesPoint, SLAItem, BreakdownItem
from app.utils import between_clause

router = APIRouter(prefix="/api/ops", tags=["operations"])

@router.get("/fnol", response_model=list[TimeSeriesPoint])
def fnol(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause('"day"', start_date, end_date)  # "day" is a reserved word sometimes
    sql = text(f"""
        SELECT "day" AS period, fnol_count AS value
        FROM marts.fnol_by_day
        {where}
        ORDER BY "day"
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [TimeSeriesPoint(**row) for row in rows]

@router.get("/sla_breaches", response_model=list[SLAItem])
def sla_breaches(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT month_start AS period,
               breaches_gt_30d,
               breaches_gt_60d,
               still_open,
               total_reported
        FROM marts.sla_breaches_simple
        {where}
        ORDER BY month_start
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [SLAItem(**row) for row in rows]

@router.get("/backlog_by_age_bucket", response_model=list[BreakdownItem])
def backlog_by_age_bucket(as_of: date | None = None):
    # When as_of omitted, return latest snapshot (single day) grouped by region
    params = {}
    where = ""
    if as_of:
        where = "WHERE as_of = :as_of"
        params["as_of"] = as_of
    else:
        where = """
        WHERE as_of = (SELECT MAX(as_of) FROM marts.backlog_by_age_bucket)
        """
    # Return total open by region (you can expand to include buckets if needed)
    sql = text(f"""
        SELECT region_key AS key,
               SUM(total_open) AS value
        FROM marts.backlog_by_age_bucket
        {where}
        GROUP BY region_key
        ORDER BY value DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [BreakdownItem(**row) for row in rows]
