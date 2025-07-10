#symptom_agent.py
import json
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI
from shared.types import HealthBotState
from dotenv import load_dotenv
from db.postgres_adapter import get_recent_messages
from langchain_core.messages import AIMessage

load_dotenv()
llm = ChatOpenAI(model="gpt-4o")

# Recall keywords
RECALL_KEYWORDS = [
    "what did i say",
    "what did i ask",
    "remind me",
    "earlier",
    "previous"
]

def symptom_extractor_agent(state: HealthBotState) -> HealthBotState:
    query = state["messages"][-1].content
    user_id = state["user_id"]

    # Recall shortcut
    if any(kw in query.lower() for kw in RECALL_KEYWORDS):
        past = get_recent_messages(user_id, limit=5)
        summary = (
            "Previously you said:\n" + "\n".join(f"- {m}" for m in past)
            if past else "I don’t see any previous interactions to recall."
        )
        state.update({
            "symptoms": [],
            "stress_level": "unknown",
            "risk_score": 0.0,
            "response_message": summary,
        })
        # Avoid appending duplicate memory replies
        if not any(m.content == summary for m in state["messages"] if m.type == "ai"):
            state["messages"].append(AIMessage(content=summary))

            state["messages"].append(AIMessage(content=summary))
            return state

    # memory prompt
    past_queries = get_recent_messages(user_id, limit=5)
    memory_prompt = "\n".join(f"- {q}" for q in past_queries)

    system_prompt = f"""
You are a helpful medical assistant.

1. Extract: symptoms, stress_level, risk_score.
2. Provide friendly advice in response_message.
3. Use memory below if user asks about past interactions.
4. pass one or two word short symptoms.

User's past messages:
{memory_prompt}

Respond ONLY in JSON format:
{{
  "symptoms": [...],
  "stress_level": "...",
  "risk_score": ..., 
  "response_message": "..."
}}
""".strip()

    result = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": query}
    ])

    # Parse JSON
    try:
        parsed = json.loads(result.content)
    except json.JSONDecodeError:
        parsed = {
            "symptoms": [],
            "stress_level": "unknown",
            "risk_score": 0.1,
            "response_message": (
                "I’m having trouble understanding. "
                "Could you please tell me more about your symptoms?"
            )
        }

    # Update state
    existing = state.get("symptoms", [])
    new = parsed.get("symptoms", [])
    combined = existing + new
    unique = []
    seen = set()
    for s in combined:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    state["symptoms"] = unique

    state["stress_level"]    = parsed.get("stress_level", "unknown")
    state["risk_score"]      = parsed.get("risk_score", 0.1)
    state["response_message"] = parsed.get(
        "response_message",
        "I'm here to help. What can I do for you today?"
    )
    
    new_ai_msg = result if isinstance(result, AIMessage) else AIMessage(content=result.content)

# Retain only last 5 messages max
    state["messages"].append(new_ai_msg)
    print("# Full message log now:", [(m.type, m.content[:30]) for m in state["messages"]])

    return state
