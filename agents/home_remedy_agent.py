# agents/home_remedy_agent.py

from shared.types import HealthBotState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from twilio.rest import Client
from dotenv import load_dotenv
import os
from db.postgres_adapter import get_symptom_frequencies, log_symptom_interaction
from datetime import datetime

load_dotenv()

# Setup LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# Twilio config
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)
twilio_from = os.getenv("TWILIO_WHATSAPP_FROM")
emergency_to = os.getenv("EMERGENCY_CONTACT")


def home_remedy_agent(state: HealthBotState) -> HealthBotState:
    symptoms = state.get("symptoms", [])
    user_prompt = state["messages"][-1].content
    response_lines = []
    emergency_detected = False

    # Step 1: Frequency Risk Check
    freq_map = get_symptom_frequencies(state["user_id"], symptoms, days=30)
    freq_risk_symptoms = [s for s, count in freq_map.items() if count >= 3]
    if freq_risk_symptoms:
        emergency_detected = True
        response_lines.append(
            f"⚠️ Warning: Symptoms {', '.join(freq_risk_symptoms)} "
            f"occurred frequently (3+ times in last 30 days)."
        )
        state["risk_score"] = max(state.get("risk_score", 0.0), 0.9)

    # Step 2: LLM Emergency Detection
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
        response_lines.append("🚨 Emergency detected by AI analysis.")

    # Step 3: WhatsApp Alert
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
            response_lines.append("✅ WhatsApp emergency alert sent.")
        except Exception as e:
            state["alert_sent"] = False
            response_lines.append(f"❌ Failed to send WhatsApp alert: {e}")
    else:
        state["alert_sent"] = False

    # Step 4: Remedies from LLM
    remedy_system_prompt = (
        "You are a cautious medical assistant. Your task is to:\n"
        "1. Identify 1–2 suspected Disease(s) based on the user's symptoms.\n"
        "2. Provide at least 3 home remedies per major symptom.\n"
        "3. Include natural remedies and precautions.\n"
        "4. Format exactly as:\n"
        "Suspected Disease(s):\n- Disease1\n- Disease2\n\n"
        "Remedies:\n1. Remedy1\n2. Remedy2\n3. Remedy3\n\n"
        "Always include a medical disclaimer at the end."
    )
    remedy_response = llm.invoke([
        SystemMessage(content=remedy_system_prompt),
        HumanMessage(content=f"Symptoms: {', '.join(symptoms)}")
    ])
    remedies_text = remedy_response.content.strip()
    response_lines.append(remedies_text)

    # Step 5: Directly extract suspected diseases from LLM response (no regex)
    suspected_diseases = []
    lines = remedies_text.splitlines()
    in_disease_section = False

    for line in lines:
        if line.strip().lower().startswith("suspected disease"):
            in_disease_section = True
            continue
        if line.strip().lower().startswith("remedies:"):
            break
        if in_disease_section and line.strip().startswith("-"):
            suspected_diseases.append(line.strip().lstrip('-').strip())

    state["suspected_diseases"] = suspected_diseases or []

    # Final state update
    state["response_message"] = "\n\n".join(response_lines).strip()

    # Ensure timestamp
    if not state.get("timestamp"):
        state["timestamp"] = datetime.utcnow().isoformat()

    # Log to database
    log_symptom_interaction(state)

    return state
