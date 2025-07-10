from shared.types import HealthBotState
from db.postgres_adapter import get_recent_messages

def memory_reader_agent(state: HealthBotState) -> HealthBotState:
    
    mem = [m.content for m in state.get("messages", [])]
    state["memory_context"] = mem

    #  push to agent_outputs
    outputs = dict(state.get("agent_outputs", {}))
    outputs["memory_context"] = mem
    state["agent_outputs"] = outputs

    print("** memory_reader running, messages:", len(state.get("messages", [])))
    print("** memory_reader writes memory_context:", state["memory_context"])
    print("** agent_outputs after memory_reader:", state.get("agent_outputs", {}).keys())



    return state




