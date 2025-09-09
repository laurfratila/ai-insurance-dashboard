# backend/AI/LLM/planner.py

"""
NL → Plan (JSON) using OpenAI.

This module turns a user's natural-language question into a STRICT JSON Plan
that matches `dsl.Plan`. It *does not* execute SQL and contains no secrets
beyond reading OPENAI_API_KEY from env via the OpenAI SDK.

Returns: (plan_dict, {"llm_latency_ms": int, "token_usage": {...}})
"""

from __future__ import annotations

import json
import os
import time
from typing import Dict, Tuple, Any, List

from openai import OpenAI

from .schema import ALLOWED_VIEWS, JOIN_RULES, ALLOWED_OPERATORS, DEFAULT_LIMIT, MAX_LIMIT


# -------------------------
# Utilities
# -------------------------

def _schema_summary() -> str:
    """Generate a compact, deterministic schema+join summary for the prompt."""
    lines: List[str] = []
    lines.append("VIEWS AND COLUMNS:")
    for view, spec in ALLOWED_VIEWS.items():
        cols = ", ".join(spec["columns"])  # type: ignore[index]
        lines.append(f"- {view}({cols})")
    lines.append("")
    lines.append("ALLOWED JOINS (left.col = right.col):")
    for left, right in sorted(JOIN_RULES):
        lines.append(f"- {left} = {right}")
    lines.append("")
    ops = ", ".join(sorted(ALLOWED_OPERATORS))
    lines.append(f"ALLOWED OPERATORS: {ops}")
    lines.append(f"LIMIT: default={DEFAULT_LIMIT}, max={MAX_LIMIT}")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are a precise planner that converts user questions about an insurance
database into a STRICT JSON object called Plan. DO NOT execute SQL. DO NOT add comments.

### Goal
Produce a Plan that can be compiled into safe SQL against the allowed tables only.

### Output Format (JSON)
Return ONLY a JSON object with keys:
- view: one of ["customers","policies","claims"]
- select: array of column names (may be qualified like "policies.status")
- filters: array of { "col": <column>, "op": <operator>, "val": <value|[start,end]|[v1,...]> }
- joins: array using these shorthands ONLY: "policies->customers", "claims->policies"
- group_by: array of columns
- aggregations: array of aggregation expressions, allowed: COUNT(*), SUM(col), AVG(col), MIN(col), MAX(col). Aliases allowed via " as alias".
- order_by: array of { "col": <column>, "dir": "asc"|"desc" }
- limit: integer (<= max)

### Rules
- Use ONLY the views/columns/joins/operators provided in the SCHEMA below.
- Prefer filters over selecting PII. Include PII columns (email, phone, dob) only if explicitly asked.
- Qualify columns when needed to avoid ambiguity (e.g., status exists in multiple tables).
- Dates are strings "YYYY-MM-DD". Use BETWEEN for closed ranges.
- If the question implies grouping/aggregation (e.g., “how many”, “total”, “average”), add appropriate group_by and aggregations.
- If the question refers to a customer by name and a city, join policies->customers or claims->policies->customers accordingly.
- If the user asks for recent time windows like "last 30 days", convert to BETWEEN [today-30, today], but leave exact dates blank for the API to fill if not known.
- If the user asks broadly and no fields are specified, return a sensible narrow selection and set limit to 50.
- **If the question asks for a total (e.g., "how many customers", "total policies", "count of claims"), do NOT use GROUP BY unless the user explicitly asks for a breakdown. Just return a single COUNT or aggregate row.**


### IMPORTANT
Return ONLY the JSON. No prose, no markdown, no extra keys.
"""


# A tiny, realistic example shown to the model to anchor format.
# Keep this minimal to avoid excessive token usage.
EXAMPLE_PLAN = {
    "view": "policies",
    "select": ["policies.product_type", "policies.channel", "policies.status"],
    "filters": [
        {"col": "customers.city", "op": "ILIKE", "val": "Cluj%"},
        {"col": "policies.status", "op": "=", "val": "active"}
    ],
    "joins": ["policies->customers"],
    "group_by": ["policies.product_type", "policies.channel", "policies.status"],
    "aggregations": ["count(*) as policies", "sum(policies.gross_premium) as premium"],
    "order_by": [{"col": "premium", "dir": "desc"}],
    "limit": 50
}


# -------------------------
# Public API
# -------------------------

def build_plan_from_nl(question: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Turn a natural language question into a JSON Plan (dict) and metadata.

    Raises:
        Exception if the model output is not valid JSON or fails to parse.
    """
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    t0 = time.time()

    # Compose the dynamic schema summary once per call (cheap) to keep planner stateless.
    schema_txt = _schema_summary()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "SCHEMA:\n" + schema_txt},
        {"role": "user", "content": "EXAMPLE PLAN (for reference):\n" + json.dumps(EXAMPLE_PLAN, ensure_ascii=False)},
        {"role": "user", "content": f"QUESTION:\n{question}\n\nReturn ONLY the JSON Plan."},
    ]

    # Choose a fast, cost-effective model; adjust if you standardize elsewhere.
    # Keep temperature low for determinism.
    resp = client.chat.completions.create(
        model=os.environ.get("RAG_PLANNER_MODEL", "gpt-4o-mini"),
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},  # enforce valid JSON
    )

    txt = (resp.choices[0].message.content or "").strip()
    try:
        plan_dict = json.loads(txt)
    except json.JSONDecodeError as e:
        # Best-effort fallback: strip code fences or stray characters and retry once
        cleaned = txt.strip("` \n\r\t")
        if cleaned.startswith("{") and cleaned.endswith("}"):
            plan_dict = json.loads(cleaned)
        else:
            raise Exception(f"Planner did not return valid JSON. Raw: {txt[:200]}...") from e

    usage = getattr(resp, "usage", None)
    token_usage = {
        "prompt": getattr(usage, "prompt_tokens", None),
        "completion": getattr(usage, "completion_tokens", None),
        "total": getattr(usage, "total_tokens", None),
    }

    meta = {
        "llm_latency_ms": round((time.time() - t0) * 1000),
        "token_usage": token_usage,
        "model": os.environ.get("RAG_PLANNER_MODEL"),
    }
    return plan_dict, meta
