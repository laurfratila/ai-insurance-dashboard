# backend/AI/LLM/executor.py

"""
Execute parameterized SQL safely, apply PII masking, and build citations.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text # type: ignore
from sqlalchemy.engine import Connection # type: ignore

from .schema import ALLOWED_VIEWS, pii_for


# -------------------------
# PII masking
# -------------------------

MASK_REPLACEMENTS = {
    "email": "[redacted]",
    "phone": "[redacted]",
    "dob": "[redacted]",
}

def _mask_row(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in row.items():
        base_col = k.split(".")[-1]  # tolerate qualified aliases like customers.email
        out[k] = MASK_REPLACEMENTS.get(base_col, v)
    return out


# -------------------------
# Execution
# -------------------------

def run_query(db: Connection, sql: str, params: Dict[str, Any], allow_pii: bool = False) -> List[Dict[str, Any]]:
    """
    Execute a parameterized SELECT and return a list of dict rows.
    If allow_pii is False (default), mask any PII-looking fields.
    """
    result = db.execute(text(sql), params)
    rows = [dict(r._mapping) for r in result]

    if not allow_pii:
        rows = [_mask_row(r) for r in rows]

    return rows


# -------------------------
# Citations
# -------------------------

def make_citations(sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return at least two citations objects:
      1) The compiled SQL with bound-parameter names,
      2) A reference to the internal metric/table definitions.
    """
    return [
        {
            "id": "sql-compiled",
            "title": "Compiled SQL",
            "type": "sql_template",
            "detail": sql,
            "params": params,
        },
        {
            "id": "metrics-def",
            "title": "Metric & Table Definitions",
            "type": "doc",
            "detail": "See metrics.md for definitions of customers/policies/claims and common metrics.",
        },
    ]
