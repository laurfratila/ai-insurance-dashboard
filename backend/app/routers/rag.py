# backend/app/routers/rag.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException # type: ignore
from pydantic import BaseModel, Field # type: ignore
from typing import Any, Dict

from sqlalchemy.engine import Connection # type: ignore
from app.db import engine

# Our NL→Plan→SQL orchestrator
from AI.LLM.retriever import answer_question

router = APIRouter(prefix="/api/rag", tags=["rag"])


# ---------- I/O Schemas ----------

class AskReq(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class Citation(BaseModel):
    id: str | None = None
    title: str
    type: str
    detail: str | None = None
    params: Dict[str, Any] | None = None


class AskResp(BaseModel):
    answer: Dict[str, Any]
    citations: list[Citation]
    meta: Dict[str, Any]


# ---------- Routes ----------

@router.post("/ask", response_model=AskResp)
def rag_ask(req: AskReq):
    """
    Natural-language Q&A over Postgres (customers/policies/claims).
    Uses the LLM planner → safe SQL → execution pipeline.
    """
    q = req.question.strip()
    if len(q) < 3:
        raise HTTPException(status_code=400, detail="Question too short.")

    try:
        with engine.connect() as conn:  # same pattern as your other routers
            result = answer_question(conn, q, allow_pii=False, user_id="demo")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not answer the question. {e}")
