from shared.types import HealthBotState
from agents.home_remedy_agent import home_remedy_agent
from agents.physical_relief_agent import physical_relief_agent
from agents.info_search_agent import info_search_agent

def supervisor_node(state: HealthBotState) -> HealthBotState:
    response_parts = []

    # Only home_remedy handles emergency logic now
    state = home_remedy_agent(state)

    if "back pain" in (state.get("symptoms") or []) or "neck pain" in (state.get("symptoms") or []):
        state = physical_relief_agent(state)

    state = info_search_agent.invoke(state)


    # Compile final message
    final_message = " Supervisor Agent Summary:\n"
    if state.get("alert_sent"):
        final_message += "🚨 Emergency alert sent based on symptom severity or AI analysis.\n"
    else:
        final_message += "✅ No emergency alert needed.\n"

    final_message += "📝 Response compiled with remedies and info.\n"
    state["response_message"] = final_message + (state.get("response_message") or "")

    state["recommended_path"] = "compiled_response"
    return state
