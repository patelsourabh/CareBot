from shared.types import HealthBotState

def medical_escalation_agent(state: HealthBotState) -> HealthBotState:
    symptoms = ", ".join(state.get("symptoms", []))
    risk = state.get("risk_score", 0.0)

    if risk >= 0.85:
        # Simulate WhatsApp alert
        state["alert_sent"] = True
        message = f"🚨 Emergency symptoms detected ({symptoms}). WhatsApp alert sent to emergency contacts."
    else:
        state["alert_sent"] = False
        message = "Symptoms noted but not critical enough for emergency messaging."

    state["response_message"] += f"\n\n🔴 Medical Escalation:\n{message}"
    return state
