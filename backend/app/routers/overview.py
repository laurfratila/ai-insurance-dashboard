# backend/app/routers/overview.py
from fastapi import APIRouter, Query
from datetime import date
from sqlalchemy import text
from app.db import engine
from app.models import TimeSeriesPoint, RatioSeriesPoint
from app.utils import between_clause

router = APIRouter(prefix="/api/overview", tags=["overview"])

@router.get("/gwp", response_model=list[TimeSeriesPoint])
def gwp(start_date: date | None = Query(None), end_date: date | None = Query(None)):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT month_start AS period, gwp AS value
        FROM marts.gwp_by_month
        {where}
        ORDER BY month_start
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [TimeSeriesPoint(**row) for row in rows]

@router.get("/loss_ratio", response_model=list[RatioSeriesPoint])
def loss_ratio(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT month_start AS period,
               claims_paid   AS numerator,
               earned_premium AS denominator,
               loss_ratio    AS ratio
        FROM marts.loss_ratio_by_month
        {where}
        ORDER BY month_start
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [RatioSeriesPoint(**row) for row in rows]

@router.get("/claims_frequency", response_model=list[RatioSeriesPoint])
def claims_frequency(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT month_start AS period,
               claims_count AS numerator,
               policies_in_force AS denominator,
               claims_frequency AS ratio
        FROM marts.claims_frequency_by_month
        {where}
        ORDER BY month_start
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [RatioSeriesPoint(**row) for row in rows]

@router.get("/avg_settlement_days", response_model=list[TimeSeriesPoint])
def avg_settlement_days(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT month_start AS period, avg_days AS value
        FROM marts.avg_settlement_days_by_month
        {where}
        ORDER BY month_start
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [TimeSeriesPoint(**row) for row in rows]
