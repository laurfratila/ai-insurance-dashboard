from backend.AI.LLM.retriever import answer_question

class DummyConn:
    class DummyResult:
        def __init__(self, rows): self._rows = rows
        def mappings(self):
            class M:
                def __init__(self, rows): self._rows = rows
                def all(self): 
                    return [type("R", (), {"_mapping": r}) for r in self._rows]
            return M(self._rows)
    def __init__(self, rows): self._rows = rows
    def execute(self, *_args, **_kwargs): return self.DummyResult(self._rows)

def test_e2e_with_monkeypatched_planner_and_executor(monkeypatch):
    # 1) Monkeypatch planner: always return a fixed plan
    def fake_build_plan_from_nl(_q):
        plan = {
            "view": "policies",
            "select": ["policies.product_type", "policies.status"],
            "filters": [{"col": "policies.status", "op": "=", "val": "active"}],
            "joins": [],
            "group_by": ["policies.product_type", "policies.status"],
            "aggregations": ["count(*) as policies", "sum(policies.gross_premium) as premium"],
            "order_by": [{"col": "premium", "dir": "desc"}],
            "limit": 10,
        }
        meta = {"llm_latency_ms": 1, "token_usage": {"prompt": 1, "completion": 1}}
        return plan, meta

    monkeypatch.setattr("backend.AI.LLM.retriever.build_plan_from_nl", fake_build_plan_from_nl)

    # 2) Dummy DB result
    rows = [{"policies.product_type": "auto", "policies.status": "active", "policies": 3, "premium": 1000.0}]
    conn = DummyConn(rows)

    # 3) Call orchestrator
    resp = answer_question(conn, "How many active policies by product type?")
    assert "answer" in resp and "citations" in resp and "meta" in resp
    assert resp["answer"]["count"] == 1
    assert len(resp["citations"]) >= 2
    assert "compile_sql" in resp["meta"]
