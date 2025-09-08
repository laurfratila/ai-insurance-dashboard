from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from datetime import date
from ..db import engine

router = APIRouter(prefix="/api/marts", tags=["marts"])

@router.get("/claims_by_month")
def claims_by_month():
    sql = text("""
        SELECT month, claims_count, paid_sum
        FROM marts.claims_by_month
        ORDER BY month
    """)
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    # Convert date to ISO for JSON
    return [
        {"month": r["month"].isoformat(), "claims_count": int(r["claims_count"]), "paid_sum": float(r["paid_sum"])}
        for r in rows
    ]


@router.get("/claims_by_county")
def claims_by_county():
    sql = text("""
        SELECT county, claims_count, paid_sum
        FROM marts.claims_by_county
        ORDER BY claims_count DESC, county
    """)
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    return [
        {"county": r["county"], "claims_count": int(r["claims_count"]), "paid_sum": float(r["paid_sum"])}
        for r in rows
    ]

