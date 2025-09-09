from openai import OpenAI # type: ignore
import os

def detect_intent(question: str) -> str:
    """Returns 'smalltalk', 'data', or 'unknown'"""


    client = OpenAI(api_key=(os.getenv("OPENAI_API_KEY") or "").strip())
    resp = client.chat.completions.create(
        model=os.getenv("RAG_PLANNER_MODEL"),
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the user's message intent.\n"
                    "Reply only: 'smalltalk' (if it’s a greeting or conversational), "
                    "'data' (if it's a request for info/insights/SQL), or 'unknown'."
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
    if "data" in txt:
        return "data"
    return "unknown"
