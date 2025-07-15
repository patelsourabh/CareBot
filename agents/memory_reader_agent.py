from shared.types import HealthBotState
from db.postgres_adapter import get_memory_pairs  # New helper function

def memory_reader_agent(state: HealthBotState) -> HealthBotState:
    user_id = state.get("user_id", "unknown_user")

    # Fetch recent memory pairs from conversation_logs
    memory_pairs = get_memory_pairs(user_id=user_id, limit=5)  # custom helper

    # Format memory as readable chunks
    formatted_context = []
    for pair in memory_pairs:
        formatted_context.append(f"Human: {pair['user']}\nAI: {pair['ai']}")

    # Store to state
    state["memory_context"] = formatted_context

    outputs = dict(state.get("agent_outputs", {}))
    outputs["memory_context"] = formatted_context
    state["agent_outputs"] = outputs

    print(f"&&&& [Memory Reader] Loaded {len(formatted_context)} past memories.")
    return state
