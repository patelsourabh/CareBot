#supervisor_agent.py
from shared.types import HealthBotState
from agents.home_remedy_agent import home_remedy_agent
from agents.physical_relief_agent import physical_relief_agent
from agents.info_search_agent import info_search_agent

def supervisor_node(state: HealthBotState) -> HealthBotState:
    # 1) Remedies pipeline
    state = home_remedy_agent(state)

    # 2) Physical relief
    if any(s in ["back pain","neck pain"] for s in state.get("symptoms") or []):
        state = physical_relief_agent(state)

    # 3) Info search
    state = info_search_agent.invoke(state)

    # 4) Append summary
    full_response = state.get("response_message","").strip()
    summary = "\n\n👨‍⚕️ **Supervisor Summary:**\n"
    summary += (
        "🚨 Emergency alert was triggered due to symptom severity.\n"
        if state.get("alert_sent") else "✅ No emergency alert was necessary.\n"
    )
    summary += "📝 The above response includes remedies, info, and suggestions."
    state["response_message"] = f"{full_response}\n{summary}".strip()
    state["recommended_path"] = "compiled_response"
    return state
