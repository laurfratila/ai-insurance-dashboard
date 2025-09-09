# backend/app/routers/claims.py
from fastapi import APIRouter
from datetime import date
from sqlalchemy import text
from app.db import engine
from app.models import TwoSeriesPoint, BreakdownItem, RatioSeriesPoint
from app.utils import between_clause

router = APIRouter(prefix="/api/claims", tags=["claims"])

@router.get("/paid_vs_reserve", response_model=list[TwoSeriesPoint])
def paid_vs_reserve(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT month_start AS period,
               paid_total  AS a,
               reserve_total AS b
        FROM marts.claims_paid_vs_reserve_by_month
        {where}
        ORDER BY month_start
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [TwoSeriesPoint(**row) for row in rows]

@router.get("/severity_histogram", response_model=list[BreakdownItem])
def severity_histogram():
    sql = text("""
        SELECT severity_band AS key, claim_count AS value
        FROM marts.claim_severity_histogram
        ORDER BY value DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    return [BreakdownItem(**row) for row in rows]

@router.get("/open_vs_closed_ratio", response_model=list[RatioSeriesPoint])
def open_vs_closed_ratio(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT month_start AS period,
               closed_count AS numerator,
               opened_count AS denominator,
               closed_to_open_ratio AS ratio
        FROM marts.open_vs_closed_ratio_by_month
        {where}
        ORDER BY month_start
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [RatioSeriesPoint(**row) for row in rows]
