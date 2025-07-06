import json
import datetime
from langchain_openai import ChatOpenAI
from shared.types import HealthBotState
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

llm = ChatOpenAI(model="gpt-4o")

def symptom_extractor_agent(state: HealthBotState) -> HealthBotState:
    query = state["messages"][-1].content

    system_prompt = """
You are a medical assistant. Extract:
- symptoms: list of symptom keywords
- stress_level: low, moderate, high
- risk_score: float between 0.0 to 1.0
- response_message: friendly health advice

Respond ONLY in JSON:
{
  "symptoms": [...],
  "stress_level": "...",
  "risk_score": ...,
  "response_message": "..."
}
"""

    result = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ])

    try:
        parsed = json.loads(result.content)
    except:
        parsed = {
            "symptoms": [],
            "stress_level": "unknown",
            "risk_score": 0.1,
            "response_message": "I couldn't understand fully, but please take care."
        }

    state["symptoms"] = parsed["symptoms"]
    state["stress_level"] = parsed["stress_level"]
    state["risk_score"] = parsed["risk_score"]
    state["response_message"] = parsed["response_message"]
    state["messages"].append(result)
    state["timestamp"] = datetime.datetime.utcnow().isoformat()

    return state
