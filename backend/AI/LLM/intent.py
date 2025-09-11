def detect_intent(question: str) -> str:
    """Returns 'smalltalk', 'data', 'help', 'offtopic', or 'unknown'"""
    from openai import OpenAI  # type: ignore
    import os

    client = OpenAI(api_key=(os.getenv("OPENAI_API_KEY") or "").strip())
    resp = client.chat.completions.create(
        model=os.getenv("RAG_PLANNER_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the user's message intent.\n"
                    "Return ONLY ONE of the following labels:\n"
                    "- 'smalltalk': If it's a greeting or friendly message directed at the assistant.\n"
                    "- 'help': If it's asking what the assistant can do, how to use it, or general assistance.\n"
                    "- 'data': If it's asking for insurance-related info (claims, policies, customers, metrics).\n"
                    "- 'forecast': If the user is asking for a prediction, trend, or future estimate (e.g., 'predict', 'forecast', 'trend', 'estimate', 'project').\n"
                    "- 'offtopic': If it’s asking about unrelated things like weather, jokes, general trivia, etc.\n"
                    "- 'unknown': If unclear."
                )
            },
            {"role": "user", "content": f"Message: {question}"}
        ],
        temperature=0,
        max_tokens=5,
    )

    txt = (resp.choices[0].message.content or "").strip().lower()
    if "smalltalk" in txt:
        return "smalltalk"
    if "help" in txt:
        return "help"
    if "forecast" in txt:
        return "forecast"
    if "data" in txt:
        return "data"
    if "offtopic" in txt:
        return "offtopic"
    return "unknown"
