# backend/AI/LLM/retriever.py

"""
RAG-from-DB orchestrator:
NL question → Plan → SQL → DB → response (rows + citations + meta).
"""

from __future__ import annotations
import time
import hashlib
from .logging import rag_logger
from .intent import detect_intent
from typing import Any, Dict
from .summarizer import summarize_rows
from sqlalchemy.engine import Connection # type: ignore
from .dsl import Plan
from .compiler import compile_sql
from .executor import run_query, make_citations

# NOTE: Implemented in the next file (planner.py).
# It should return: (plan_dict: dict, llm_meta: {"llm_latency_ms": int, "token_usage": {...}})
from .planner import build_plan_from_nl  # type: ignore


def _hash_for_logging(value: str) -> str:
    """Hash sensitive free text for logs (avoid storing raw PII)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def answer_question(
    db: Connection,
    question: str,
    *,
    allow_pii: bool = False,
    user_id: str | None = None,
) -> Dict[str, Any]:
    """
    Main entrypoint used by the API.

    Returns:
      {
        "answer": {"rows": [...], "count": N},
        "citations": [...],
        "meta": {
          "compile_sql": "...",
          "exec_latency_ms": 42,
          "plan_latency_ms": 88,
          "llm_latency_ms": 88,
          "token_usage": {"prompt": 123, "completion": 45},
          "question_hash": "abcd1234",
          "contains_pii": false
        }
      }
    """
    t0 = time.time()

    # 🔎 Detect intent
    intent = detect_intent(question)

    if intent == "offtopic":
        return {
            "answer": {
                "type": "text",
                "rows": [],
                "count": 0,
                "summary": "I'm here to help you with insurance-related questions. Try asking me about claims, customers, or KPIs."
            },
            "citations": [],
            "meta": {
                "intent": "offtopic",
                "user_id": user_id,
                "question_hash": _hash_for_logging(question),
            }
        }

    if intent == "smalltalk":
        summary_text = (
            "I'm doing great, thanks for asking! 😊\n"
            "Would you like to explore some quick insights on your KPIs, like open claims, average premium, "
            "or ask me something else?"
        )
        rag_logger.info(
            f"RAG 🤝 Smalltalk | user_id={user_id} | question={(question[:80] + '...' if len(question) > 80 else question)}"
        )
        return {
            "answer": {
                "type": "text",
                "rows": [],
                "count": 0,
                "summary": summary_text
            },
            "citations": [],
            "meta": {
                "intent": "smalltalk",
                "user_id": user_id,
                "question_hash": _hash_for_logging(question),
            }
        }

    if intent == "help":
        summary_text = (
            "Of course! I'm here to assist you with insights from your insurance data.\n\n"
            "You can ask me questions like:\n"
            "• What is the average claim settlement time in 2024?\n"
            "• Which county had the most claims?\n"
            "• How many policies were renewed in Q2?\n\n"
            "Would you like to explore one of these topics?"
        )
        rag_logger.info(
            f"RAG 🙋 Help | user_id={user_id} | question={(question[:80] + '...' if len(question) > 80 else question)}"
        )
        return {
            "answer": {
                "type": "text",
                "rows": [],
                "count": 0,
                "summary": summary_text
            },
            "citations": [],
            "meta": {
                "intent": "help",
                "user_id": user_id,
                "question_hash": _hash_for_logging(question),
            }
        }

    if intent == "forecast":
        # Run the normal pipeline, but mark the response as a forecast for the frontend
        plan_dict, llm_meta = build_plan_from_nl(question)
        plan = Plan(**plan_dict)
        sql, params = compile_sql(plan)
        t_exec0 = time.time()
        rows = run_query(db, sql, params, allow_pii=allow_pii)
        summary_result = summarize_rows(question, rows)
        exec_ms = round((time.time() - t_exec0) * 1000)
        citations = make_citations(sql, params)
        total_ms = round((time.time() - t0) * 1000)
        meta = {
            "compile_sql": sql,
            "exec_latency_ms": exec_ms,
            "plan_latency_ms": llm_meta.get("llm_latency_ms"),
            "llm_latency_ms": llm_meta.get("llm_latency_ms"),
            "token_usage": llm_meta.get("token_usage"),
            "question_hash": _hash_for_logging(question),
            "contains_pii": plan.contains_pii,
            "user_id": user_id,
            "total_latency_ms": total_ms,
            "model": llm_meta.get("model")
        }
        summary_text = summary_result.get("summary", "[no summary]")
        rag_logger.info(
            f"RAG 📈 Forecast | user_id={user_id} | question={(question[:80] + '...' if len(question) > 80 else question)} | "
            f"rows={len(rows)} | summary={summary_text} | "
            f"model={meta.get('model')} | latency={meta.get('total_latency_ms')}ms | "
            f"tokens={llm_meta.get('token_usage', {}).get('total')} | "
            f"citations={[c['title'] for c in citations]}"
        )
        return {
            "answer": {
                "type": "forecast",
                "rows": rows,
                "count": len(rows),
                "summary": summary_result.get("summary"),
                "question": question
            },
            "citations": citations,
            "meta": meta | {
                "summary_llm_latency_ms": summary_result.get("llm_latency_ms"),
                "summary_token_usage": summary_result.get("token_usage"),
                "intent": "forecast"
            }
        }


    # 1) NL → Plan (dict) via the LLM planner
    plan_dict, llm_meta = build_plan_from_nl(question)

    # 2) Validate & normalize with Pydantic model (qualifies columns, clamps limit, flags PII)
    plan = Plan(**plan_dict)

    # 3) Plan → SQL (+ params)
    sql, params = compile_sql(plan)

    # 4) Execute
    t_exec0 = time.time()
    rows = run_query(db, sql, params, allow_pii=allow_pii)
    summary_result = summarize_rows(question, rows)

    exec_ms = round((time.time() - t_exec0) * 1000)

    # 5) Build citations (≥2)
    citations = make_citations(sql, params)

    # 6) Compose response
    total_ms = round((time.time() - t0) * 1000)
    meta = {
        "compile_sql": sql,
        "exec_latency_ms": exec_ms,
        "plan_latency_ms": llm_meta.get("llm_latency_ms"),
        "llm_latency_ms": llm_meta.get("llm_latency_ms"),
        "token_usage": llm_meta.get("token_usage"),
        "question_hash": _hash_for_logging(question),
        "contains_pii": plan.contains_pii,
        "user_id": user_id,
        "total_latency_ms": total_ms,
        "model": llm_meta.get("model")

    }
    summary_text = summary_result.get("summary", "[no summary]")
    rag_logger.info(
        f"RAG ✅ | user_id={user_id} | question={(question[:80] + '...' if len(question) > 80 else question)} | "
        f"rows={len(rows)} | summary={summary_text} | "
        f"model={meta.get('model')} | latency={meta.get('total_latency_ms')}ms | "
        f"tokens={llm_meta.get('token_usage', {}).get('total')} | "
        f"citations={[c['title'] for c in citations]}"
)
    
    return {
        "answer": {
            "rows": rows,
            "count": len(rows),
            "summary": summary_result.get("summary")
        },
        "citations": citations,
        "meta": meta | {
            "summary_llm_latency_ms": summary_result.get("llm_latency_ms"),
            "summary_token_usage": summary_result.get("token_usage"),
        }
    }

