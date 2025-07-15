#physical_relief_agent.py
from shared.types import HealthBotState

def physical_relief_agent(state: HealthBotState) -> HealthBotState:
    stretches = {
        "back pain": "# Try knee-to-chest or child's pose stretch.",
        "neck pain": "# Do gentle neck tilts and shoulder rolls.",
    }

    safe_exercises = []
    for symptom in state.get("symptoms", []):
        if symptom.lower() in stretches:
            safe_exercises.append(f"{symptom}: {stretches[symptom.lower()]}")

    if safe_exercises:
        message = "# Physical Relief:\n" + "\n".join(safe_exercises)
    else:
        message = "# No safe physical activities suggested for the symptoms."

    state["response_message"] = state.get("response_message", "") + f"\n\n{message}"

     #  physical_relief output
    outputs = dict(state.get("agent_outputs", {}))
    outputs["physical_relief"] = message
    state["agent_outputs"] = outputs

    return state