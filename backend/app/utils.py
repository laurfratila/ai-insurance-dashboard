# backend/app/utils.py
from datetime import date
from typing import Optional, Dict, Any

def between_clause(column_name: str, start_date: Optional[date], end_date: Optional[date]) -> tuple[str, Dict[str, Any]]:
    where = []
    params: Dict[str, Any] = {}
    if start_date:
        where.append(f"{column_name} >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where.append(f"{column_name} <= :end_date")
        params["end_date"] = end_date
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    return clause, params
