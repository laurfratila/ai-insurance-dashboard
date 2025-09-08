# backend/app/routers/risk.py
from fastapi import APIRouter, Query
from datetime import date
from sqlalchemy import text
from app.db import engine
from app.models import BreakdownItem
from app.utils import between_clause

router = APIRouter(prefix="/api/risk", tags=["risk"])

@router.get("/claims_by_peril", response_model=list[BreakdownItem])
def claims_by_peril(start_date: date | None = None,
                    end_date: date | None = None,
                    top_n: int = Query(10, ge=1, le=100)):
    where, params = between_clause("month_start", start_date, end_date)
    # Aggregate to total per peril in range, then top N by paid_total
    sql = text(f"""
        WITH agg AS (
            SELECT peril AS key,
                   SUM(claims_count) AS value,
                   SUM(paid_total)   AS paid_total
            FROM marts.claims_by_peril_month
            {where}
            GROUP BY peril
        )
        SELECT key, value
        FROM agg
        ORDER BY paid_total DESC NULLS LAST
        LIMIT :top_n
    """)
    params["top_n"] = top_n
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [BreakdownItem(**row) for row in rows]

@router.get("/cat_exposure", response_model=list[BreakdownItem])
def cat_exposure(region: str | None = None,
                 start_date: date | None = None,
                 end_date: date | None = None):
    where, params = between_clause("month_start", start_date, end_date)
    if region:
        where += (" AND region_key = :region") if where else " WHERE region_key = :region"
        params["region"] = region
    # Return exposure (GWP proxy) by region over the range
    sql = text(f"""
        SELECT region_key AS key,
               SUM(exposure_gwp) AS value
        FROM marts.cat_exposure_by_region
        {where}
        GROUP BY region_key
        ORDER BY value DESC NULLS LAST
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [BreakdownItem(**row) for row in rows]
