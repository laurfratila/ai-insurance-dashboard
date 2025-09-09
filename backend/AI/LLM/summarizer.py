# backend/AI/LLM/summarizer.py

"""
Summarizer: generate short textual explanations for query results.

- Uses OpenAI for natural-language summarization of tabular rows.
- Keeps structured rows intact in the API response.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from openai import OpenAI # type: ignore


def summarize_rows(question: str, rows: List[Dict[str, Any]], max_rows: int = 5) -> Dict[str, Any]:
    """
    Summarize query results into a concise explanation.

    Args:
        question: the original user question (string).
        rows: list of dicts returned from the DB query.
        max_rows: maximum number of rows to include in context (default=5).

    Returns:
        {
          "summary": "Natural-language explanation",
          "llm_latency_ms": 123,
          "token_usage": {...}
        }
    """
    if not rows:
        return {"summary": "No results found.", "llm_latency_ms": 0, "token_usage": {}}

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Keep the first few rows as JSON context
    snippet = rows[:max_rows]

    system_prompt = """You are an analytics assistant.
Given a user question and some tabular results, write a short factual summary.
- Be concise (2–3 sentences).
- Use only the data provided.
- Do not hallucinate.
- If rows contain numeric aggregates, highlight the key values.
"""

    user_prompt = f"Question: {question}\nRows: {snippet}"

    t0 = time.time()
    resp = client.chat.completions.create(
        model=os.environ.get("RAG_SUMMARY_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=200,
    )
    latency_ms = round((time.time() - t0) * 1000)

    txt = resp.choices[0].message.content.strip()

    usage = getattr(resp, "usage", None)
    token_usage = {
        "prompt": getattr(usage, "prompt_tokens", None),
        "completion": getattr(usage, "completion_tokens", None),
        "total": getattr(usage, "total_tokens", None),
    }

    return {"summary": txt, "llm_latency_ms": latency_ms, "token_usage": token_usage}
