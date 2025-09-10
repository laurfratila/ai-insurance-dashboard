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

from openai import OpenAI # type: ignore

from .schema import ALLOWED_VIEWS, JOIN_RULES, ALLOWED_OPERATORS, DEFAULT_LIMIT, MAX_LIMIT
from .example_plans import EXAMPLE_PLAN


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
- Look at the EXAMPLE PLANS section to find similar patterns before creating the plan.

### Rules
- Use ONLY the views/columns/joins/operators provided in the SCHEMA below.
- Prefer filters over selecting PII. Include PII columns (email, phone, dob) only if explicitly asked.
- Qualify columns when needed to avoid ambiguity (e.g., status exists in multiple tables).
- The plan must always start FROM the base view that the question is focused on (e.g., claims if counting claims), and JOIN other tables as needed. Do not assume availability of a table unless it was part of the FROM clause or a JOIN.
- Dates are strings "YYYY-MM-DD". Use BETWEEN for closed ranges.
- If the plan contains aggregation functions (SUM, COUNT, AVG, etc.), and you are selecting other columns, you MUST include all non-aggregated columns in the group_by array.
- The group_by must match exactly all non-aggregated columns from the select list.
- When grouping data (e.g., to count claims per customer), only include identifying fields (e.g., customer_id, full_name, policy_id) in the group_by and select arrays. Avoid unnecessary fields like claim_id if they are not being counted individually.
- Do not select claim_id or other record-level fields unless you intend to show raw rows (which is rare when aggregating).
- Do NOT include a raw column like policies.gross_premium in the select array if you're already using it in an aggregation (e.g., avg(policies.gross_premium)).
- If the question refers to a customer by name and a city, join policies->customers or claims->policies->customers accordingly.
- If the question is about “open claims by age”, use the materialized view: marts.backlog_by_age_bucket.
    - Use columns: region_key, as_of, bucket_0_7, bucket_8_30, bucket_31_90, bucket_90_plus, total_open.
    - Do NOT use raw core.claims.
- If the user asks for a percentage of customers matching a filter (e.g., age group, city), calculate both the filtered count and the total count using COUNT() and use them to compute the percentage.
- Use a COUNT(*) FILTER (WHERE ...) as aged_group, and a second COUNT(*) as total_customers.
- If the user asks for recent time windows like "last 30 days", convert to BETWEEN [today-30, today], but leave exact dates blank for the API to fill if not known.
- If the user asks broadly and no fields are specified, return a sensible narrow selection and set limit to 50.
- **If the question asks for a total (e.g., "how many customers", "total policies", "count of claims"), do NOT use GROUP BY unless the user explicitly asks for a breakdown. Just return a single COUNT or aggregate row.**
- If the question asks “how much” or “total” about financial values (like amounts paid, reserved, premiums), use SUM() aggregations on the appropriate fields (e.g., claims.paid, claims.reserve, policies.gross_premium).
- NEVER use SELECT * in such cases. Only return necessary columns or aggregations.
- If the question asks for a comparison between two metrics (e.g., paid vs reserved), include both in the aggregation list.
- If a question is about claims or policy trends over time (e.g., per month, by region, by channel, etc.), prefer using marts views like `claims_by_month`, `channel_mix_by_month`, or `cat_exposure_by_region`.
- Only use core tables if the user is asking for detailed, raw-level information (e.g., specific customers or claims).
- Marts views should be used whenever the metrics match the question — for example:
  - avg_settlement_days_by_month → for average settlement durations
  - channel_mix_by_month → for channel splits
  - claims_by_county → for claim counts by geography, and so on.
- If using a marts view like `avg_settlement_days_by_month`, do NOT apply an extra aggregation like AVG() on top of columns like `avg_days`, `p90_days`, `p50_days`, etc. These columns are already monthly aggregates.
    - Instead, SELECT the column (e.g., avg_days) along with month_start, and ORDER BY month_start.
- For open claims older than X days, use the marts.backlog_by_age_bucket view.
- Select bucket_90_plus when asking for “older than 90 days”.
- Use region_key for grouping.
- Avoid raw joins over core.claims/policies/customers.


### IMPORTANT
Return ONLY the JSON. No prose, no markdown, no extra keys.
"""

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
        {"role": "user", "content": "EXAMPLE PLANS (for reference):\n" + "\n\n".join(json.dumps(p, ensure_ascii=False) for p in EXAMPLE_PLAN)},
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
