# agents/emergency_alert_agent.py

from shared.types import HealthBotState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from twilio.rest import Client
from dotenv import load_dotenv
import os
from db.postgres_adapter import get_symptom_frequencies
from datetime import datetime

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)
twilio_from = os.getenv("TWILIO_WHATSAPP_FROM")
emergency_to = os.getenv("EMERGENCY_CONTACT")

def emergency_alert_agent(state: HealthBotState) -> HealthBotState:
    symptoms = state.get("symptoms", [])
    user_prompt = state["messages"][-1].content
    emergency_detected = False
    freq_map = get_symptom_frequencies(state["user_id"], symptoms, days=30)
    freq_risk_symptoms = [s for s, count in freq_map.items() if count >= 3]

    if freq_risk_symptoms:
        emergency_detected = True
        prev_score = state.get("risk_score")
        prev_score = prev_score if isinstance(prev_score, (int, float)) else 0.0
        state["risk_score"] = max(prev_score, 0.9)

        state["emergency_flags"] = [f"⚠️ Frequent symptom: {', '.join(freq_risk_symptoms)}"]

    system_msg = (
        "You are a medical emergency classifier. Respond ONLY with 'EMERGENCY' "
        "if the message suggests any serious or urgent condition like chest pain, unconsciousness, bleeding, etc. Else say 'SAFE'."
    )
    llm_response = llm.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=user_prompt)
    ])
    llm_decision = llm_response.content.strip().lower()
    if "emergency" in llm_decision:
        emergency_detected = True
        state.setdefault("emergency_flags", []).append("🚨 Emergency detected by AI")

    if emergency_detected:
        try:
            alert_msg = (
                f"🚨 Emergency Alert for user {state['user_id']}:\n"
                f"User says: \"{user_prompt}\"\n"
                f"Symptoms: {', '.join(symptoms)}\n"
                f"Frequent Symptoms: {', '.join(freq_risk_symptoms)}"
            )
            twilio_client.messages.create(
                from_=twilio_from,
                to=emergency_to,
                body=alert_msg
            )
            state["alert_sent"] = True
            state["emergency_flags"].append("✅ WhatsApp alert sent.")
        except Exception as e:
            state["alert_sent"] = False
            state["emergency_flags"].append(f"❌ Alert failed: {e}")
    else:
        state["alert_sent"] = False

    return state
