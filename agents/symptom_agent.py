#symptom_agent.py
import json
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI

from shared.types import HealthBotState
from dotenv import load_dotenv
from db.postgres_adapter import get_recent_messages
from langchain_core.messages import AIMessage
import os

load_dotenv()
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",  # You can also use "openrouter/llama3-8b"
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
)

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

    system_prompt = f"""
You are a helpful medical assistant.

1. Extract: symptoms, stress_level, risk_score.
2. Provide friendly advice in response_message.
4. pass one or two word short symptoms.

Respond ONLY in JSON format:
{{
  "symptoms": [...],
  "stress_level": "...",
  "risk_score": 0.3, 
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
    
    print(f"#### symptoms extracted: {state['symptoms']}")

    return state
