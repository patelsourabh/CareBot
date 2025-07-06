from shared.types import HealthBotState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from twilio.rest import Client
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime, timedelta

load_dotenv()

# Setup LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# Twilio config
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
twilio_from = os.getenv("TWILIO_WHATSAPP_FROM")
emergency_to = os.getenv("EMERGENCY_CONTACT")

# DB
conn = sqlite3.connect("healthbot.db", check_same_thread=False)
cursor = conn.cursor()

def get_symptom_frequencies(user_id: str, symptoms: list, days: int = 30) -> dict:
    recent_window = (datetime.utcnow() - timedelta(days=days)).isoformat()
    freq_map = {}
    for symptom in symptoms:
        cursor.execute("""
        SELECT COUNT(*) FROM symptom_logs
        WHERE user_id=? AND symptoms LIKE ? AND timestamp >= ?
        """, (user_id, f"%{symptom}%", recent_window))
        count = cursor.fetchone()[0]
        freq_map[symptom] = count
    return freq_map

def log_symptom_interaction(state: HealthBotState):
    cursor.execute("""
    INSERT INTO symptom_logs (user_id, query, symptoms, stress_level, risk_score, timestamp, final_response)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        state["user_id"],
        state["messages"][-1].content,
        ", ".join(state.get("symptoms") or []),
        state.get("stress_level"),
        state.get("risk_score"),
        state.get("timestamp") or datetime.utcnow().isoformat(),
        state.get("response_message"),
    ))
    conn.commit()

def home_remedy_agent(state: HealthBotState) -> HealthBotState:
    symptoms = state.get("symptoms", [])
    user_prompt = state["messages"][-1].content
    response_lines = []
    emergency_detected = False

    # --- Step 1: Frequency Risk Check ---
    freq_map = get_symptom_frequencies(state["user_id"], symptoms)
    freq_risk_symptoms = [s for s, count in freq_map.items() if count >= 3]

    if freq_risk_symptoms:
        emergency_detected = True
        response_lines.append(
            f"⚠️ Warning: Symptoms {', '.join(freq_risk_symptoms)} occurred frequently (3+ times in last 30 days)."
        )

    # --- Step 2: LLM Emergency Detection ---
    system_msg = (
        "You are a medical emergency classifier. Respond ONLY with 'EMERGENCY' "
        "if the message suggests any serious or urgent condition like chest pain, unconsciousness, bleeding, etc. Else say 'SAFE'."
    )
    llm_response = llm.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=user_prompt)
    ])
    llm_decision = llm_response.content.strip().lower()
    print("[DEBUG] LLM Emergency Classification:", llm_decision)

    if "emergency" in llm_decision:
        emergency_detected = True
        response_lines.append("🚨 Emergency detected by AI analysis.")

    # --- Step 3: WhatsApp Alert ---
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

    # --- Step 4: Remedies from LLM ---
    remedy_system_prompt = (
        "You are a cautious medical assistant. Your task is to:\n"
        "1. Identify 1–2 suspected diseases based on the user's symptoms.\n"
        "2. Provide at least 3 home remedies per major symptom.\n"
        "3. Include natural remedies and precautions.\n"
        "4. Format:\n"
        "Suspected Disease(s):\n- ...\n\n"
        "Remedies:\n1. ...\n2. ...\n3. ...\n\n"
        "always add medical disclaimers."
    )

    remedy_response = llm.invoke([
        SystemMessage(content=remedy_system_prompt),
        HumanMessage(content=f"Symptoms: {', '.join(symptoms)}")
    ])
    remedies_text = remedy_response.content.strip()

    # --- Step 5: Extract suspected disease (optional logic) ---
    suspected_disease = "Not identified"
    if "Suspected Disease" in remedies_text:
        suspected_disease = remedies_text.split("Suspected Disease")[1].split("Remedies")[0].strip()
    state["suspected_diseases"] = suspected_disease

    # --- Step 6: Add Disclaimer and Response ---
    #remedies_text += "\n\n⚠️ Use these remedies only after consulting a medical professional."
    response_lines.append(remedies_text)

    # --- Final state update ---
    state["response_message"] = (
        state.get("response_message", "") + "\n\n".join(response_lines)
    )

    log_symptom_interaction(state)

    return state
