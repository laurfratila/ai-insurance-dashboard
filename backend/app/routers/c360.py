# backend/app/routers/c360.py
from fastapi import APIRouter
from datetime import date
from sqlalchemy import text
from app.db import engine
from app.models import TimeSeriesPoint, BreakdownItem, DemographicItem
from app.utils import between_clause

router = APIRouter(prefix="/api/c360", tags=["customer360"])

@router.get("/retention", response_model=list[TimeSeriesPoint])
def retention(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT month_start AS period, retention_rate AS value
        FROM marts.retention_by_month
        {where}
        ORDER BY month_start
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [TimeSeriesPoint(**row) for row in rows]

@router.get("/cross_sell_distribution", response_model=list[BreakdownItem])
def cross_sell_distribution():
    sql = text("""
        SELECT products_count::text AS key, customers AS value
        FROM marts.cross_sell_distribution
        ORDER BY products_count
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    return [BreakdownItem(**row) for row in rows]

@router.get("/channel_mix", response_model=list[BreakdownItem])
def channel_mix(start_date: date | None = None, end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    sql = text(f"""
        SELECT channel AS key, SUM(gwp) AS value
        FROM marts.channel_mix_by_month
        {where}
        GROUP BY channel
        ORDER BY value DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [BreakdownItem(**row) for row in rows]

@router.get("/demographics", response_model=list[DemographicItem])
def demographics():
    sql = text("""
        SELECT age_band, county_name, customers
        FROM marts.customer_demographics
        ORDER BY age_band, county_name
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    return [DemographicItem(**row) for row in rows]
